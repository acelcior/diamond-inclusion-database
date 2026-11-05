"""One-time conversion: Stachel 'Diamond Inclusion Database' (CC0, local .xlsm) -> compilations/stachel-major/rows.jsonl.

Run from the project folder:  .venv/bin/python -I scripts/convert_stachel.py
Values only (macros never run). One JSON object per sheet row: {"row": Excel row number, "cells": {header: value}}.
Blank cells are omitted; everything else is kept exactly as stored (numbers as numbers, text as text, incl. spaces).
"""
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "papers" / "compilations" / "stachel-major" / "Diamond_Database_Oct-2021.xlsm"
OUT = ROOT / "compilations" / "stachel-major" / "rows.jsonl"


def main():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    it = wb["All diamonds"].iter_rows(values_only=True)
    hdr = next(it)
    n = 0
    with open(OUT, "w", encoding="utf-8") as f:
        for i, r in enumerate(it, start=2):
            cells = {h: v for h, v in zip(hdr, r) if h and v is not None}
            if cells:
                f.write(json.dumps({"row": i, "cells": cells}, ensure_ascii=False) + "\n")
                n += 1
    print(f"{n} rows -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
