"""General table extractor: tables in a text-layer PDF -> analyses.csv, driven by per-paper hints, not per-paper code.

    python3 -I extraction/extract.py HINTS.json [--out analyses.csv] [--compare checked.csv]

HINTS.json is a paper's source.json (hints under "extract") or a file holding only the hints:
  {"pdf": "papers/x.pdf", "tables": [{"label": "Table 3", "page": "231", "start": "text that opens the table", ...}]}
Per table (all but label, page, start optional):
  end          text that closes the table (default: the next "Table N" caption, at most 150 lines after start)
  cut          ignore text right of this character column (body text beside a narrow table)
  sample_row   label of the row of sample names (default "Sample");  samples: the names, when the text layer garbles them
  mineral_row  label of the row of mineral names;                    mineral: one name, or one per column
  rows         {"printed row label": "csv field"} for other header rows (suite, assemblage, touching); give
               {"field": "csv field", "pattern": "regex of one cell"} when neighbouring cells are one space apart
  fields       {"csv field": value | [per column] | {"column index": value}} for facts from footnotes
  page         one printed page, or one per block when a table continues over pages

Handles tables printed with one analysis per column (oxides down the side), in one or several blocks. A row label must
be a quantity code in vocab/quantity.csv or "Total"; the printed label becomes the CSV column and the loader maps it.
Every cell is kept as printed. Values are placed by count, or by position when a row has blank cells.
shortcut: tables with one analysis per row and spreadsheet supplements are not handled; add when a paper needs them.
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALUE = re.compile(r"[<≤]\s*\d*\.?\d+|\d+\.?\d*(?:\s*\(\d+\))?\*?|n\.d\.|n\.a\.|b\.d\.l?\.?|\b(?:na|nd|bdl)\b|[—–-](?=\s|$)")
WORD, CHUNK = re.compile(r"\S+"), re.compile(r"\S+(?: \S+)*")
STOP = ["Ox", "Oxygen", "Oxygens", "Cations"]  # rows of calculated cations follow: recomputable, not extracted
SKIP_IN_COMPARE = {"column", "seq", "block"}
STANDARD = ["table", "page", "column", "sample_no", "mineral", "touching", "n_analyses", "cited_source", "note",
            "phase_hint"]  # the columns scripts/build_gold.py load_simple expects in every analyses.csv


def quantity_labels():
    with open(ROOT / "vocab" / "quantity.csv", encoding="utf-8") as f:
        return [r["code"] for r in csv.DictReader(f)] + ["Total"]


def toks(line, skip, pattern=WORD):
    """(character column, text) of each cell right of the row label."""
    return [(m.start() + skip, re.sub(r"\s+", " ", m.group()).replace("< ", "<")) for m in pattern.finditer(line[skip:])]


def owner(starts, col):
    """Index of the last header starting at or before this column (headers sit up to ~4 characters right)."""
    return max((i for i, s in enumerate(starts) if s <= col + 4), default=0)


def pick(spec, i, default=""):
    """A hint that is one value for every column, a list per column, or {column index: value}."""
    if isinstance(spec, list):
        return spec[i]
    if isinstance(spec, dict):
        return spec.get(str(i), default)
    return default if spec is None else spec


def blocks_of(lines, t, qlabels):
    sample_row, extra = t.get("sample_row", "Sample"), t.get("rows", {})
    meta = [x for x in [sample_row, t.get("mineral_row"), *extra] if x]
    labels = sorted(meta + qlabels + STOP, key=len, reverse=True)
    start = next(i for i, l in enumerate(lines) if t["start"] in l)
    is_end = (lambda l: t["end"] in l) if t.get("end") else (lambda l: re.match(r"Table \d", l))  # next table's caption
    end = next((i for i in range(start + 1, min(start + 150, len(lines))) if is_end(lines[i])), start + 150)
    blocks, cur, last = [], None, None
    for line in lines[start:end]:
        line = line[:t.get("cut", 10_000)]
        label = next((x for x in labels if line.startswith(x) and not line[len(x):len(x) + 1].strip()), None)
        if label is None:
            if cur and last in extra and not cur["q"] and line.strip():
                cur["more"].setdefault(last, []).append(line)   # a wrapped header cell, e.g. 'chr' under 'gt, opx,'
            continue
        if label == "Total" and cur and "Total" in cur["q"]:
            continue                                            # the total of the calculated cations
        new = label in meta or (label in qlabels and cur and label in cur["q"])  # a header after values, or an oxide again
        if cur is None or (new and cur["q"]):
            cur = {"meta": {}, "more": {}, "q": {}, "closed": False}
            blocks.append(cur)
        if label in STOP:
            cur["closed"] = True
        elif label in meta:
            cur["meta"].setdefault(label, line)
        elif not cur["closed"]:
            cur["q"][label] = toks(line, len(label), VALUE)
            cur["closed"] = label == "Total"
        last = label
    return [b for b in blocks if b["q"]]


def parse_table(lines, t, qlabels):
    sample_row, extra = t.get("sample_row", "Sample"), t.get("rows", {})
    out, done = [], 0
    for b, blk in enumerate(blocks_of(lines, t, qlabels)):
        if t.get("samples") and done >= len(t["samples"]):
            break                                               # every listed sample is read: what follows is another table
        n = max(len(v) for v in blk["q"].values())
        full = [v for v in blk["q"].values() if len(v) == n]
        starts = [sorted(v[i][0] for v in full)[len(full) // 2] for i in range(n)]   # median position of each column
        where = f"{t['label']} block {b + 1}"

        def place(cells_, what):
            if len(cells_) == n:
                return [x for _, x in cells_]
            assert len(cells_) < n, f"{where}: {what} has {len(cells_)} cells for {n} columns"
            out_ = [""] * n
            for pos, x in cells_:                                # blank cells: nearest column by position
                k = min(range(n), key=lambda j: abs(starts[j] - pos))
                assert not out_[k], f"{where}: two cells of {what} fall in column {k + 1}"
                out_[k] = x
            return out_

        hdr = toks(blk["meta"][sample_row], len(sample_row)) if sample_row in blk["meta"] else []
        if t.get("samples"):
            samples, s_starts = t["samples"][done:done + n], starts
        elif len(hdr) == n:
            samples, s_starts = [x for _, x in hdr], starts
        else:                                                    # one sample name over several analysis columns
            assert hdr, f"{where}: no '{sample_row}' row found; list the samples in the hints"
            s_starts = [p for p, _ in hdr]
            samples = [hdr[owner(s_starts, c)][1] for c in starts]
        assert len(samples) == n, f"{where}: {len(samples)} sample names for {n} columns"
        if "mineral" in t:
            minerals = [pick(t["mineral"], done + i) for i in range(n)]
        else:
            got = toks(blk["meta"].get(t.get("mineral_row"), ""), len(t.get("mineral_row") or ""))
            assert len(got) == n, f"{where}: {len(got)} mineral names for {n} columns; list them in the hints"
            minerals = [x for _, x in got]
        heads = {}
        for label, spec in extra.items():
            field, cell = (spec, CHUNK) if isinstance(spec, str) else (spec["field"], re.compile(spec["pattern"]))
            line = blk["meta"].get(label, "")
            if len(toks(line, len(label))) == n and len(toks(line, len(label), cell)) != len(s_starts):
                heads[field] = place(toks(line, len(label)), label)             # one cell per analysis column
                continue
            per_sample = [""] * len(s_starts)                                    # one cell per sample, by position
            for src, skip in [(line, len(label))] + [(x, 0) for x in blk["more"].get(label, [])]:
                for pos, x in toks(src, skip, cell):
                    k = owner(s_starts, pos)
                    per_sample[k] = (per_sample[k] + " " + x).strip()
            heads[field] = [per_sample[owner(s_starts, c)] for c in starts]
        values = {q: place(v, q) for q, v in blk["q"].items()}
        for i in range(n):
            out.append({"table": t["label"], "page": pick(t["page"], b), "column": done + i + 1, "sample_no": samples[i],
                        "mineral": minerals[i], **{f: pick(spec, done + i) for f, spec in t.get("fields", {}).items()},
                        **{f: v[i] for f, v in heads.items()}, **{q: v[i] for q, v in values.items()}})
        done += n
    return out


def extract(hints, text):
    qlabels, lines = quantity_labels(), text.splitlines()
    return [r for t in hints["tables"] for r in parse_table(lines, t, qlabels)]


def compare(rows, checked):
    """Cell-by-cell agreement with a checked CSV, row by row in order, over the columns both files have."""
    assert len(rows) == len(checked), f"{len(rows)} rows extracted, {len(checked)} in the checked file"
    cols = [c for c in checked[0] if c not in SKIP_IN_COMPARE and any(c in r for r in rows)]
    bad = [(i + 1, c, r.get(c, ""), g[c]) for i, (r, g) in enumerate(zip(rows, checked)) for c in cols if r.get(c, "") != g[c]]
    return len(rows) * len(cols), sum(bool(g[c]) for g in checked for c in cols), bad


def main(argv):
    if not argv:
        sys.exit(__doc__)
    hints = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    hints = hints.get("extract", hints)
    text = subprocess.run(["pdftotext", "-layout", str(ROOT / hints["pdf"]), "-"],
                          capture_output=True, text=True, check=True).stdout
    rows = extract(hints, text)
    fields = list(dict.fromkeys(STANDARD + [k for r in rows for k in r]))
    if "--out" in argv:
        with open(argv[argv.index("--out") + 1], "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, restval="")
            w.writeheader()
            w.writerows(rows)
    for t in hints["tables"]:
        got = [r for r in rows if r["table"] == t["label"]]
        print(f"{t['label']}: {len(got)} analyses; filled: {[k for k in fields if any(r.get(k) for r in got)][5:]}")
    if "--compare" in argv:
        with open(argv[argv.index("--compare") + 1], encoding="utf-8") as f:
            cells, filled, bad = compare(rows, list(csv.DictReader(f)))
        print(f"compared {cells} cells ({filled} not blank) with the checked file: {cells - len(bad)} agree, {len(bad)} differ")
        for row, col, got, want in bad[:20]:
            print(f"  row {row} {col}: extracted {got!r}, checked {want!r}")


if __name__ == "__main__":
    main(sys.argv[1:])
