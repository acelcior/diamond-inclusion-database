"""Parse Tables 3 and 4 of Phillips et al. (2004) into gold/phillips-2004/*.csv, values as printed.

Run from the project folder (needs the local PDF and poppler's pdftotext):
    python3 -I extraction/parse_phillips_2004.py

Columns are assigned by character position in `pdftotext -layout` output, which was checked
against page images of pages 160, 161 and 171. Every cell is kept as printed text; the loader
(scripts/build_gold.py) decides what each notation means.
"""
import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "papers" / "phillips-2004.pdf"
OUT = ROOT / "gold" / "phillips-2004"

OXIDES = ["SiO2", "Al2O3", "TiO2", "Cr2O3", "FeO", "MnO", "NiO", "MgO", "CaO", "Na2O", "K2O", "V2O5", "ZnO", "Total"]
BLOCK_PAGE = {1: "160", 2: "160", 3: "161", 4: "161"}  # from the page images


def tokens(line):
    """(start column, text) for each whitespace-separated token."""
    return [(m.start(), m.group()) for m in re.finditer(r"\S+", line)]


def owner(starts, col):
    """Index of the last sample header starting at or before this column.
    Headers sit up to ~3 characters right of their first column in pdftotext output, hence the slack;
    check_columns() confirms every assignment against the printed assemblage."""
    return max(i for i, s in enumerate(starts) if s <= col + 4)


def cells(line, label, starts, pattern):
    """Multi-word cells (e.g. 'Per (hz)', 'gt, opx, ol') assigned to sample headers by position."""
    out = [""] * len(starts)
    for m in re.finditer(pattern, line[len(label):]):
        k = owner(starts, m.start() + len(label))
        out[k] = (out[k] + " " + m.group()).strip()
    return out


ABBR = {"Garnet": "gt", "Opx": "opx", "Olivine": "ol", "Cpx": "cpx", "Chr": "chr", "Mag": "mag"}
# Seen in the page image of p. 161: DP473 has two garnet + opx pairs (one touching, one not).
# Every other diamond has one column per listed phase (DP392 runs on from block 2 into block 3).
CHECKED_EXCEPTIONS = {"DP473": ["gt", "opx", "gt", "opx"]}


def check_columns(rows):
    by_sample = {}
    for r in rows:
        by_sample.setdefault(r["sample_no"], []).append(r)
    for sample, cols in by_sample.items():
        got = [ABBR[c["mineral"]] for c in cols]
        listed = re.split(r",\s*", cols[0]["assemblage"].rstrip(","))
        expected = CHECKED_EXCEPTIONS.get(sample, listed)
        # a listed phase may lack a printed analysis (DP364 lists chr), but never the reverse
        assert set(got) <= set(expected) and len(got) <= len(expected), (sample, got, listed)
        if len(got) < len(expected):
            print(f"  note: {sample} lists {cols[0]['assemblage']!r} but Table 3 prints {got}")
        assert len({c["suite"] for c in cols}) == 1 and cols[0]["suite"], (sample, "suite")


def parse_table3(lines):
    start = next(i for i, l in enumerate(lines) if l.startswith("Table 3"))
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("Per: peridotitic"))
    blocks, cur, last_label = [], None, None
    for line in lines[start:end]:
        if line.startswith("Sample no."):
            cur = {"rows": {}, "assemblage_extra": []}
            blocks.append(cur)
            cur["rows"]["Sample no."] = line
            last_label = "Sample no."
            continue
        if cur is None:
            continue
        label = next((l for l in ["Mineral", "Suite", "Assemblage", "Touching"] + OXIDES
                      if re.match(re.escape(l) + r"(\s|$)", line)), None)
        if label:
            cur["rows"][label] = line
            last_label = label
        elif last_label == "Assemblage" and line.strip():
            cur["assemblage_extra"].append(line)  # wrapped assemblage text, e.g. 'chr' under 'gt, opx,'

    out, seq = [], 0
    for b, block in enumerate(blocks, 1):
        rows = block["rows"]
        samples = tokens(rows["Sample no."])[2:]           # skip 'Sample' 'no.'
        s_starts = [c for c, _ in samples]
        minerals = tokens(rows["Mineral"])[1:]
        assert len(minerals) == 20, (b, len(minerals))
        suites = cells(rows["Suite"], "Suite", s_starts, r"Per \(l?hz\)|Ecl|Web")
        assem = cells(rows["Assemblage"], "Assemblage", s_starts, r"\S+(?: \S+)*")
        for extra in block["assemblage_extra"]:
            for k, t in enumerate(cells(extra, "", s_starts, r"\S+(?: \S+)*")):
                assem[k] = (assem[k] + " " + t).strip()
        touching = [t for _, t in tokens(rows["Touching"])[1:]]
        values = {}
        for ox in OXIDES:
            vals = [t for _, t in tokens(rows[ox])[1:]]
            assert len(vals) == 20, (b, ox, len(vals))
            values[ox] = vals
        for i, (col, mineral) in enumerate(minerals):
            k = owner(s_starts, col)
            seq += 1
            out.append({
                "seq": seq, "page": BLOCK_PAGE[b], "block": b, "column": i + 1,
                "sample_no": samples[k][1], "mineral": mineral, "suite": suites[k],
                "assemblage": assem[k], "touching": touching[i],
                **{ox: values[ox][i] for ox in OXIDES},
            })
    return out


T4_COLS = ["T_gt_opx", "P_gt_opx_b", "P_gt_opx_c", "T_gt_ol", "P_gt_ol", "T_gt_cpx", "P_gt_cpx"]


def parse_table4(lines):
    start = next(i for i, l in enumerate(lines) if l.startswith("Table 4"))
    header = next(l for l in lines[start:] if "P (GPa)b" in l)
    # numeric columns start under the 'T (' and 'P (' headers
    col_starts = [m.start() for m in re.finditer(r"[TP] \(", header)]
    assert len(col_starts) == len(T4_COLS), col_starts
    out, group = [], None
    for line in lines[start:]:
        if line.startswith("Touching mineral"):
            group = "touching"
            continue
        if line.startswith("Non-touching mineral"):
            group = "non-touching"
            continue
        if group and re.match(r"\d{3}\s", line):
            break                                           # next page header: table has ended
        if not (group and line.startswith("DP")):
            continue
        parts = [(m.start(), m.group()) for m in re.finditer(r"\S+(?: \S+)*", line)]
        sample, paragenesis, assemblage = (p[1] for p in parts[:3])
        row = {"page": "171", "group": group, "sample_no": sample, "paragenesis": paragenesis,
               "assemblage": assemblage, **{c: "" for c in T4_COLS}}
        for c, t in tokens(line[parts[2][0] + len(assemblage):]):
            pos = c + parts[2][0] + len(assemblage)
            nearest = min(range(len(col_starts)), key=lambda j: abs(col_starts[j] - pos))
            assert row[T4_COLS[nearest]] == "", (sample, t)
            row[T4_COLS[nearest]] = t
        out.append(row)
    return out


def write(name, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True).stdout
    lines = text.splitlines()
    OUT.mkdir(parents=True, exist_ok=True)
    t3, t4 = parse_table3(lines), parse_table4(lines)
    check_columns(t3)
    write("table3.csv", t3)
    write("table4.csv", t4)
    print(f"Table 3: {len(t3)} inclusion columns from {len({r['sample_no'] for r in t3})} diamonds")
    print(f"Table 4: {len(t4)} rows")


if __name__ == "__main__":
    main()
