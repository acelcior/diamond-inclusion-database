"""General table extractor: tables in a text-layer PDF -> analyses.csv, driven by per-paper hints, not per-paper code.

    python3 -I extraction/extract.py HINTS.json [--out analyses.csv] [--compare checked.csv] [--totals]

--totals checks each analysis against its own printed Total (the same check the loader repeats after import).

HINTS.json is a paper's source.json (hints under "extract") or a file holding only the hints:
  {"pdf": "papers/x.pdf", "tables": [{"label": "Table 3", "page": "231", "start": "text that opens the table", ...}]}
Per table (all but label, page, start optional):
  end          text that closes the table (default: the caption of the next table, so "Table 2. Cont." blocks are
               read as part of Table 2; at most 150 lines after start unless "max_lines" says otherwise)
  labels       {"printed row label": "csv column"} for labels printed differently from the vocabulary, e.g.
               {"Al2 O3": "Al2O3", "Σ": "Total", "TFeO": "TFeO"}; a column that is not a quantity must then be mapped
               in source.json "column_quantity" before it loads, so its meaning is stated, not assumed
  cut          ignore text right of this character column (body text beside a narrow table)
  sample_row   label of the row of sample names (default "Sample");  samples: the names, when the text layer garbles them
  mineral_row  label of the row of mineral names;                    mineral: one name, or one per column
  rows         {"printed row label": "csv field"} for other header rows (suite, assemblage, touching); give
               {"field": "csv field", "pattern": "regex of one cell"} when neighbouring cells are one space apart
  fields       {"csv field": value | [per column] | {"column index": value}} for facts from footnotes
  page         one printed page, or one per block when a table continues over pages
  continued    "unlabelled" when the pages after "Table N. Cont." print the rows without their labels: each line
               then takes the label of the same line on the first page (check the result with --totals)

Default layout, one analysis per column (oxides down the side), in one or several blocks: a row label must be a
quantity code in vocab/quantity.csv, "Total", or listed in "labels". Rows may be indented.
Values are placed by count, or by position when a row has blank cells.

"layout": "rows", one analysis per row (oxides across the top): each cell goes to the header cell it sits under.
  header   text found in the header line (default: the first line with four or more quantity labels)
  columns  CSV column names for the header cells, in order (default: "sample_no", then the printed labels)
  text     names of further columns that hold words, not values (e.g. ["zone"])
  row      regex a data row starts with; without it a line counts as a row when its value cells all look like values,
           and other lines with three or more cells are listed as not read, so nothing is skipped unseen
  align    "right" when numbers line up with the right edge of their header (default: left edge)
  split    {"column": "regex with named groups"} to split one printed cell into fields, e.g. a cell 'JW030 cpx A'
           with "(?P<sample_no>\\S+) (?P<mineral>\\S+) (?P<inclusion_label>\\S+)"

Every cell is kept as printed.
shortcut: spreadsheet supplements are not handled; add when a paper needs them.
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
ROWTOK = re.compile(r"[<≤>]\s*\S+|\S+")
CELL = re.compile(r"[<≤>]?\s*[-−–]?\d[\d,]*\.?\d*(?:\s*\(\d+\))?\*?|n\.d\.|n\.a\.|b\.d\.l?\.?|na|nd|bdl|[—–-]")
TEXT_COLUMNS = {"sample_no", "diamond_no", "inclusion_label", "mineral", "paragenesis", "assemblage", "touching", "note",
                "suite", "n_analyses", "cited_source", "phase_hint"}
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


def span(lines, t):
    start = next(i for i, l in enumerate(lines) if t["start"] in l)
    own = re.sub(r"\D", "", t["label"])                         # 'Table 2' -> '2': its own 'Table 2. Cont.' is not an end

    def is_end(line):
        if t.get("end"):
            return t["end"] in line
        m = re.match(r"\s*Table (\d+)", line)
        return bool(m) and m[1] != own
    last = min(start + t.get("max_lines", 150), len(lines))
    return start, next((i for i in range(start + 1, last) if is_end(lines[i])), last)


def parse_rows(lines, t, qlabels):
    """One analysis per row: a cell belongs to the last header cell starting at or before it (or, right-aligned,
    the first header cell ending at or after it), so a long name stays in its own column."""
    start, end = span(lines, t)
    cut = t.get("cut", 10_000)
    is_header = ((lambda l: t["header"] in l) if t.get("header") else
                 (lambda l: sum(x in qlabels for _, x in toks(l, 0, CHUNK)) >= 4))
    h = next(i for i in range(start, end) if is_header(lines[i][:cut]))
    head = toks(lines[h][:cut], 0, CHUNK)
    names = t.get("columns") or ["sample_no"] + [x for _, x in head[1:]]
    assert len(names) == len(head), f"{t['label']}: {len(names)} column names for {len(head)} header cells"
    right = t.get("align") == "right"
    starts, ends = [p for p, _ in head], [p + len(x) for p, x in head]
    text_cols = {0} | {i for i, name in enumerate(names) if name in TEXT_COLUMNS or name in t.get("text", [])}
    row_re = re.compile(t["row"]) if t.get("row") else None
    out, unread = [], []
    for line in lines[h + 1:end]:
        line = line[:cut]
        if not line.strip() or (row_re and not row_re.match(line.strip())):
            continue
        got, clash = [""] * len(names), None
        for pos, x in toks(line, 0, ROWTOK):
            k = (next((j for j, e in enumerate(ends) if e >= pos + len(x) - 4), len(names) - 1) if right
                 else owner(starts, pos))
            if got[k] and k not in text_cols and not re.fullmatch(r"\(\d+\)\*?", x):
                clash = f"{t['label']}: two cells fall under '{names[k]}' in: {line.strip()[:80]}"
            got[k] = (got[k] + " " + x).strip()
        values = [got[k] for k in range(len(names)) if k not in text_cols and got[k]]
        if row_re:
            assert not clash, clash
        elif clash or not got[0] or len(values) < 2 or not all(CELL.fullmatch(v) for v in values):
            if len(line.split()) >= 3:
                unread.append(line.strip()[:90])
            continue
        for x in unread:                     # only lines before or between rows: text after the last row is not table
            print(f"  {t['label']}: not read as a row: {x}", file=sys.stderr)
        unread, i = [], len(out)
        cells_ = dict(zip(names, got))
        for col, pattern in t.get("split", {}).items():
            m = re.fullmatch(pattern, cells_[col])
            assert m, f"{t['label']} row {i + 1}: '{cells_[col]}' does not fit the split pattern for {col}"
            cells_.update(m.groupdict())
        out.append({"table": t["label"], "page": pick(t["page"], 0), "column": f"row {i + 1}",
                    **({"mineral": pick(t["mineral"], i)} if "mineral" in t else {}),
                    **{f: pick(spec, i) for f, spec in t.get("fields", {}).items()}, **cells_})
    return out


def blocks_of(lines, t, qlabels):
    sample_row, extra = t.get("sample_row", "Sample"), t.get("rows", {})
    meta = [x for x in [sample_row, t.get("mineral_row"), *extra] if x]
    printed = t.get("labels", {})
    labels = sorted(meta + qlabels + STOP + list(printed), key=len, reverse=True)
    start, end = span(lines, t)
    blocks, cur, last, bare = [], None, None, 0
    # "continued": "unlabelled" = pages after "Table N. Cont." print no row labels: their lines take the first
    # block's labels (None for a line without one) in the same order
    # shortcut: a continuation page whose header row is wholly blank shifts the labels (totals then fail); list rows by hand if met
    cont = re.compile(rf"\s*{re.escape(t['label'])}\. Cont") if t.get("continued") == "unlabelled" else None
    template, queue = [], []
    for line in lines[start:end]:
        line = line[:t.get("cut", 10_000)]
        body = line.lstrip()
        if cont and cont.match(line):
            queue = list(template)
            continue
        if queue and body:
            label, skip = queue.pop(0), 0
        else:
            label = next((x for x in labels if body.startswith(x) and not body[len(x):len(x) + 1].strip()), None)
            skip = len(line) - len(body) + len(label or "")
            if cont and body and (label in meta and cur is None or len(blocks) == 1 and not cur["closed"]):
                template.append(label)                          # from the first header row to the Total row
        if label is None:
            bare += not cont and bool(re.match(r"\d+\.\d+(\s+\d+\.\d+){3}", body))   # a row of numbers with no label in front
            if cur and last in extra and not cur["q"] and line.strip():
                cur["more"].setdefault(last, []).append(line)   # a wrapped header cell, e.g. 'chr' under 'gt, opx,'
            continue
        name = printed.get(label, label)                        # the CSV column this row goes to
        if name == "Total" and cur and "Total" in cur["q"]:
            continue                                            # the total of the calculated cations
        new = label in meta or (label not in STOP and cur and name in cur["q"])  # a header after values, or an oxide again
        if cur is None or (new and cur["q"]):
            cur = {"meta": {}, "more": {}, "q": {}, "closed": False}
            blocks.append(cur)
        if label in STOP:
            cur["closed"] = True
        elif label in meta:
            cur["meta"].setdefault(label, (line, skip))
        elif not cur["closed"]:
            cur["q"][name] = toks(line, skip, VALUE)
            cur["closed"] = name == "Total"
        last = label
    if bare:
        print(f"  {t['label']}: {bare} rows of numbers have no row label and were NOT read "
              "(a continued table whose labels are missing from the text layer?)", file=sys.stderr)
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

        hdr = toks(*blk["meta"][sample_row]) if sample_row in blk["meta"] else []
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
            got = toks(*blk["meta"].get(t.get("mineral_row"), ("", 0)))
            assert len(got) == n, f"{where}: {len(got)} mineral names for {n} columns; list them in the hints"
            minerals = [x for _, x in got]
        heads = {}
        for label, spec in extra.items():
            field, cell = (spec, CHUNK) if isinstance(spec, str) else (spec["field"], re.compile(spec["pattern"]))
            line, skip = blk["meta"].get(label, ("", 0))
            if len(toks(line, skip)) == n and len(toks(line, skip, cell)) != len(s_starts):
                heads[field] = place(toks(line, skip), label)                    # one cell per analysis column
                continue
            per_sample = [""] * len(s_starts)                                    # one cell per sample, by position
            for src, skip in [(line, skip)] + [(x, 0) for x in blk["more"].get(label, [])]:
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
    return [r for t in hints["tables"]
            for r in (parse_rows if t.get("layout") == "rows" else parse_table)(lines, t, qlabels)]


def compare(rows, checked):
    """Cell-by-cell agreement with a checked CSV, row by row in order, over the columns both files have."""
    assert len(rows) == len(checked), f"{len(rows)} rows extracted, {len(checked)} in the checked file"
    cols = [c for c in checked[0] if c not in SKIP_IN_COMPARE and any(c in r for r in rows)]
    bad = [(i + 1, c, r.get(c, ""), g[c]) for i, (r, g) in enumerate(zip(rows, checked)) for c in cols if r.get(c, "") != g[c]]
    return len(rows) * len(cols), sum(bool(g[c]) for g in checked for c in cols), bad


def totals(rows, tol=0.15):
    """(analyses with a printed Total, those whose oxides do not add up to it within tol): a misplaced cell shows here."""
    num = lambda x: float(re.match(r"\d+\.?\d*", x).group()) if re.match(r"\d", x or "") else None
    oxides = list(dict.fromkeys(k for r in rows for k in r if k not in STANDARD and k not in TEXT_COLUMNS and k != "Total"))
    have = [(r, num(r["Total"]), sum(num(r.get(q)) or 0 for q in oxides)) for r in rows if num(r.get("Total")) is not None]
    return len(have), [(r["table"], r["column"], r["sample_no"], r["Total"], round(s, 2)) for r, t, s in have if abs(t - s) > tol]


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
    if "--totals" in argv:
        n, off = totals(rows)
        print(f"printed totals: {n - len(off)} of {n} analyses add up within 0.15 wt%")
        for x in off:
            print("  does not add up:", *x)
    if "--compare" in argv:
        with open(argv[argv.index("--compare") + 1], encoding="utf-8") as f:
            cells, filled, bad = compare(rows, list(csv.DictReader(f)))
        print(f"compared {cells} cells ({filled} not blank) with the checked file: {cells - len(bad)} agree, {len(bad)} differ")
        for row, col, got, want in bad[:20]:
            print(f"  row {row} {col}: extracted {got!r}, checked {want!r}")


if __name__ == "__main__":
    main(sys.argv[1:])
