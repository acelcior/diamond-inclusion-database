"""Build demo/demo.sqlite: the Stachel CC0 compilations, with readable column names, for a browsable demo.

Raw compilation rows, NOT curated into schema/001_core.sql yet (that is Phase 2 / D-013).
Values are unchanged; only column names, column order and an added full-text index differ.
Run: .venv/bin/python -I scripts/build_demo_db.py
"""
import sqlite3, warnings
from pathlib import Path
from openpyxl import load_workbook  # reads cached values only; never runs the workbook's macros

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    ("major_elements", ROOT / "papers/compilations/stachel-major/Diamond_Database_Oct-2021.xlsm", "All diamonds"),
    ("trace_elements", ROOT / "papers/compilations/stachel-traces/Diamond_Traces_Oct-2021.xlsm", "All"),
]
DROP = {"kcode", "jcode", "lcode"}  # Igpet plotting codes
# Original header (whitespace-normalized) -> readable name. Both workbooks' spellings are listed.
RENAME = {
    "sample": "Locality", "craton": "Craton / terrane", "mineral": "Inclusion mineral",
    "#_sample": "Sample ID", "paragenesis": "Paragenesis (code)", "garnet class": "Garnet class",
    "assemblage": "Assemblage in diamond",
    "EPMA reference (or both)": "Inclusion data reference", "Mineral Chemistry Reference (or both)": "Inclusion data reference",
    "EPMA DOI": "Inclusion data DOI", "Mineral Chemistry DOI": "Inclusion data DOI",
    "isoptope analysis reference": "Diamond isotope/FTIR reference", "Stable Isotope Reference": "Diamond isotope/FTIR reference",
    "isotope DOI": "Diamond isotope/FTIR DOI", "Isotope DOI": "Diamond isotope/FTIR DOI",
    "size": "Diamond size", "shape": "Diamond shape", "colour": "Diamond colour", "deformation": "Plastic deformation",
    "δ13C [‰]": "Diamond δ13C (‰)", "δ13C[‰]": "Diamond δ13C (‰)",
    "δ15N [‰]": "Diamond δ15N (‰)", "δ15N[‰]": "Diamond δ15N (‰)",
    "N [SIMS, at ppm]": "Diamond N, SIMS (at.ppm)", "N[SIMS,atppm]": "Diamond N, SIMS (at.ppm)",
    "Type": "Diamond type (FTIR)", "N [at ppm]": "Diamond N, FTIR (at.ppm)", "N[atppm]": "Diamond N, FTIR (at.ppm)",
    "%B": "N in B centres (%)", "IB'[cm-2]": "Platelet peak area (cm-2)", "B'pos[cm-1]": "Platelet peak position (cm-1)",
    "3107cm-1[cm-2]": "3107 cm-1 peak area (cm-2)",
    "T[Nitrogen,3Ga]": "T N-residence 3 Ga (°C)", "T[Nitrogen,1Ga]": "T N-residence 1 Ga (°C)",
    "T[Nitrogen,0.5Ga]": "T N-residence 0.5 Ga (°C)", "T[Nitrogen,0.1Ga]": "T N-residence 0.1 Ga (°C)",
    "T[Krogh 88; 50 kbar]": "T gt-cpx Krogh, at 50 kbar (°C)", "T[O'Neill 79; 50 kbar]": "T gt-ol O'Neill, at 50 kbar (°C)",
    "T[Harley/BKN]": "T gt-opx Harley (°C)", "P[BKN/Harley]": "P Al-in-opx BKN (kbar)", "p[BKN/Harley]": "P Al-in-opx BKN (kbar)",
    "T[NTcpx]": "T single-cpx Nimis-Taylor (°C)", "P[NTcpx]": "P single-cpx Nimis-Taylor (kbar)", "p[NTcpx]": "P single-cpx Nimis-Taylor (kbar)",
    "δ18O [mineral]": "Inclusion δ18O (‰)", "δ18O[mineral]": "Inclusion δ18O (‰)",
    "δ18O reference": "Inclusion δ18O reference", "δ18O DOI": "Inclusion δ18O DOI",
    "Total": "Oxide total (wt%)", "Cl": "Cl (wt%)", "F": "F (wt%)",
}
OXIDES = {"P2O5", "Nb2O5", "SiO2", "TiO2", "ZrO2", "Al2O3", "Cr2O3", "V2O3", "FeO", "MnO", "NiO", "MgO",
          "CaO", "CoO", "ZnO", "SrO", "BaO", "Na2O", "K2O"}
FIRST = ["Locality", "Craton / terrane", "Inclusion mineral", "Sample ID", "Paragenesis", "Paragenesis (code)",
         "Garnet class", "Assemblage in diamond", "Inclusion data reference", "Inclusion data DOI"]
# Exact codes only, from the Stachel data dictionary; combined or uncertain codes stay as code only.
PARAGENESIS = {"e": "eclogitic", "p": "peridotitic", "h": "harzburgitic", "l": "lherzolitic", "wb": "websteritic",
               "wehr": "wehrlitic", "l.m.": "lower mantle", "deep-e": "sublithospheric eclogitic",
               "deep-h": "sublithospheric harzburgitic", "deep-l": "sublithospheric lherzolitic", "?": "unknown"}
SEARCHABLE = ["Locality", "Craton / terrane", "Inclusion mineral", "Sample ID", "Paragenesis (code)",
              "Assemblage in diamond", "Inclusion data reference", "Diamond isotope/FTIR reference", "Remarks"]


def readable(headers):
    """Readable names; trace-element ppm columns sit between Ca_int and the first REE ratio."""
    names, in_traces = [], False
    for h in headers:
        if h == "La[N]/Yb[N]":
            in_traces = False
        if h in RENAME:
            n = RENAME[h]
        elif h in OXIDES:
            n = f"{h} (wt%)"
        elif in_traces:
            n = f"{h} (ppm)"
        elif h.endswith("+") and h[:-2].isalpha():  # cations per formula unit, e.g. Si4+
            n = f"{h} (cpfu)"
        else:
            n = h
        names.append(n)
        if h == "Ca_int":
            in_traces = True
    return names


out = ROOT / "demo/demo.sqlite"
out.unlink(missing_ok=True)
db = sqlite3.connect(out)
q = lambda n: '"' + n.replace('"', '""') + '"'
for table, path, sheet in SOURCES:
    rows = load_workbook(path, read_only=True, data_only=True)[sheet].iter_rows(values_only=True)
    header = [" ".join(str(h).split()) if h is not None else None for h in next(rows)]
    keep = [i for i, h in enumerate(header) if h is not None and h not in DROP]
    names = readable([header[i] for i in keep])
    assert len(set(n.lower() for n in names)) == len(names), "duplicate column names"
    data = []
    for r in rows:
        if any(c is not None for c in r):
            rec = dict(zip(names, (r[i] for i in keep)))
            rec["Paragenesis"] = PARAGENESIS.get(str(rec.get("Paragenesis (code)") or "").strip())
            data.append(rec)
    cols = [c for c in FIRST if c in data[0]] + [n for n in names if n not in FIRST]
    db.execute(f"CREATE TABLE {table} ({', '.join(q(c) for c in cols)})")
    db.executemany(f"INSERT INTO {table} VALUES ({','.join('?' * len(cols))})", [tuple(d.get(c) for c in cols) for d in data])
    fts = [c for c in SEARCHABLE if c in cols]
    db.execute(f"CREATE VIRTUAL TABLE {table}_fts USING fts5({', '.join(q(c) for c in fts)}, content={q(table)}, content_rowid='rowid')")
    db.execute(f"INSERT INTO {table}_fts ({table}_fts) VALUES ('rebuild')")
    print(table, len(data), "rows,", len(cols), "columns; unrenamed:", [n for n in names if n == RENAME.get(n, n) and n in header][:12])
db.commit()
