"""Parse the major-element Tables 3, 4, 5, 6 and 8 of Sobolev et al. (2004) into gold/sobolev-2004/analyses.csv.

Run from the project folder (needs the local PDF and poppler's pdftotext):
    python3 -I extraction/parse_sobolev_2004.py

Column headers are listed here by hand from the page images (pp. 231, 232, 235, 236, 239), because
the text layer misplaces some (Table 5's Syt-1 has two columns). Values are read from the text layer
and must match the header count. Every cell is kept as printed. Cation, Mg#, Fo and Cr/(Cr+Al) rows
are calculated by the authors and are not extracted (recomputable from the oxides).
"""
import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "papers" / "sobolev-2004.pdf"
OUT = ROOT / "gold" / "sobolev-2004" / "analyses.csv"

OXIDES = ["P2O5", "SiO2", "TiO2", "Al2O3", "Cr2O3", "FeO", "MnO", "MgO", "CaO", "Na2O", "K2O", "NiO", "Total"]
VALUE = re.compile(r"<\s*\d*\.?\d+|\d+\.?\d*(?:\s*\(\d+\))?\*?|n\.d\.")

T5 = ["Syt-1", "Syt-1", "Im-10", "Im-21", "Yub-212", "Yub-322", "Yum-150", "AL-8", "AL-9", "Km-42/35", "Km-64/23",
      "Km-68/23", "Km-69/23", "Km-71/49", "Im-3", "STI-203/98", "ST-203/00", "AL-1", "AL-2", "Yum-31", "Km-94/49"]
TABLES = [
    # label, page, title prefix in text, mineral per column (or one for all), samples (None = read header), cut column
    {"label": "Table 3", "page": "231", "start": "Major-element compositions of selected olivine", "mineral": "olivine"},
    {"label": "Table 4", "page": "232", "start": "Selected compositions of chrome spinels", "mineral": "chrome spinel"},
    {"label": "Table 5", "page": "235", "start": "Selected compositions of garnets", "mineral": "garnet", "samples": T5,
     "n": {9: "10", 10: "15", 11: "10", 12: "10", 13: "12", 20: "8"}},
    {"label": "Table 6", "page": "236", "start": "Chemical composition of majoritic and normal garnets", "cut": 72,
     "samples": ["Yum-27", "Yum-27", "Km-88/23", "Kr-119/13", "Po-99"],
     "mineral": ["Majorite", "Normal", "Majorite", "Majorite", "Majorite"], "n": dict(enumerate(["8", "10", "5", "17", "17"])),
     # 'Gt type' labels; the title says "majoritic and normal garnets"
     "phase_hint": ["majoritic garnet", "garnet", "majoritic garnet", "majoritic garnet", "majoritic garnet"]},
    {"label": "Table 8", "page": "239", "start": "Selected compositions of pyroxenes", "cut": 66,
     "samples": ["Kmsm-6", "Kmsm-7", "Kmsm-21", "UD-2", "STI-33", "Yum-20"],
     "mineral": ["Cr-Di", "Cr-Di", "En", "Omph", "Omph", "Omph"]},
]
NOTES = {  # per (table, sample): from table footnotes
    ("Table 3", "Yum-10"): ("Sobolev et al. (2000)", ""), ("Table 3", "Yub-317"): ("Sobolev et al. (2000)", ""),
    ("Table 3", "Yub-13"): ("Sobolev et al. (2000)", ""),
    ("Table 8", "UD-2"): ("", "Printed as UD-2*: associated (touching) with coesite (Table 8 footnote)"),
}


def parse(lines, t):
    start = next(i for i, l in enumerate(lines) if t["start"] in l)
    rows, header = {}, None
    for line in lines[start:start + 120]:
        line = line[:t.get("cut", 10_000)]
        if line.startswith("Sample") and header is None:
            header = line.split()[1:]
        label = next((o for o in OXIDES if re.match(re.escape(o) + r"\s", line)), None)
        if label and label not in rows:
            rows[label] = [re.sub(r"\s+", " ", m.group()).replace("< ", "<") for m in VALUE.finditer(line[len(label):])]
        if re.match(r"(Ox|Oxygen)\s", line):
            break                                   # cation rows follow: not extracted
    samples = t.get("samples") or header
    out = []
    for i, sample in enumerate(samples):
        mineral = t["mineral"][i] if isinstance(t["mineral"], list) else t["mineral"]
        cited, note = NOTES.get((t["label"], sample), ("", ""))
        r = {"table": t["label"], "page": t["page"], "column": i + 1, "sample_no": sample, "mineral": mineral,
             "touching": "y" if note.startswith("Printed as UD-2*") else "", "n_analyses": t.get("n", {}).get(i, ""),
             "cited_source": cited, "note": note, "phase_hint": t["phase_hint"][i] if "phase_hint" in t else ""}
        for ox in OXIDES:
            vals = rows.get(ox)
            if vals is not None:
                assert len(vals) == len(samples), (t["label"], ox, len(vals), len(samples), vals)
            r[ox] = vals[i] if vals else ""
        out.append(r)
    return out


def main():
    text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True).stdout
    lines = text.splitlines()
    rows = [r for t in TABLES for r in parse(lines, t)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for t in TABLES:
        n = [r for r in rows if r["table"] == t["label"]]
        print(t["label"], len(n), "analyses; oxides:", [o for o in OXIDES if any(r[o] for r in n)])


if __name__ == "__main__":
    main()
