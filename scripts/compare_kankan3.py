"""Compare the Kankan III Table 1 transcription (gold/stachel-2002-kankan3/diamonds.csv) with the Stachel
compilation's host-diamond columns (δ13C, N, %B, Type) for Kankan diamonds.

Run from the project folder (needs the local compilation):  .venv/bin/python -I scripts/compare_kankan3.py
Writes gold/stachel-2002-kankan3/compilation-check.csv.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
XLSM = ROOT / "papers" / "compilations" / "stachel-major" / "Diamond_Database_Oct-2021.xlsm"
PAPER = ROOT / "gold" / "stachel-2002-kankan3"


def num(x):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


def main():
    wb = openpyxl.load_workbook(XLSM, read_only=True, data_only=True)  # values only; macros never run
    it = wb["All diamonds"].iter_rows(values_only=True)
    hdr = next(it)
    comp = defaultdict(list)
    for r in it:
        d = dict(zip(hdr, r))
        if d["sample"] and "kankan" in str(d["sample"]).lower():
            m = re.match(r"KK-0*(\d+)", str(d["#_sample"]).strip())   # compiler pads: KK-001a = KK-1, inclusion a
            if m:
                comp[m[1]].append(d)
    out = []
    for r in csv.DictReader(open(PAPER / "diamonds.csv", encoding="utf-8")):
        key = r["sample_no"].split("-")[1]
        rows = comp.get(key, [])
        def vals(col):
            return sorted({num(c[col]) for c in rows if num(c[col]) is not None})
        # tolerance = half the printed rounding step (the compilation keeps unrounded %B)
        checks = {"d13C": (num(r["d13C"]), vals("δ13C [‰]"), 0.006), "N": (num(r["N_ppm"]), vals("N [at ppm]"), 0.5),
                  "pct_B": (num(r["pct_B"]), vals("%B"), 0.5)}
        verdict = []
        for name, (mine, theirs, tol) in checks.items():
            if not theirs:
                continue
            verdict.append(f"{name} {'ok' if any(abs(mine - t) <= tol for t in theirs) else f'DIFF {mine} vs {theirs}'}")
        out.append({"sample_no": r["sample_no"], "compilation_rows": len(rows),
                    "result": "; ".join(verdict) or "no host-diamond values in compilation"})
    with open(PAPER / "compilation-check.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    found = [o for o in out if o["compilation_rows"]]
    diffs = [o for o in out if "DIFF" in o["result"]]
    oks = sum(o["result"].count(" ok") for o in out)
    print(f"{len(out)} diamonds; {len(found)} found in compilation; {oks} values agree; {len(diffs)} diamonds differ")
    for o in diffs:
        print("  ", o)


if __name__ == "__main__":
    main()
