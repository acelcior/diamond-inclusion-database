"""Calibration: compare an image-only transcription of Gress et al. (2021) Table 3 (p. 5) with its PDF text layer.

Run from the project folder (needs the local PDF):
    python3 -I extraction/calibrate_gress_2021.py papers/gress-2021.pdf gold/calibration/gress-2021-table3-image-transcription.csv

The transcription was written from 220-dpi page images and saved before the text layer was read.
Result on 2026-11-03: 576 cells (416 non-blank), 0 mismatches; three planted errors were all caught.
"""
import csv, re, subprocess, sys
pdf, img_csv = sys.argv[1], sys.argv[2]
text = subprocess.run(["pdftotext", "-f", "5", "-l", "5", "-layout", pdf, "-"], capture_output=True, text=True).stdout
lines = text.splitlines()
hdr = next(l for l in lines if l.strip().startswith("Inclusion") and "Fe" in l and "Pb" in l)
cols = ["Fe","Ni","Cu","Co","NiCo_Fe","Cu_metals","Ir","Ir_2s","Pt","Pt_2s","Zn","Zn_2s","Mo","Mo_2s","Pb","Pb_2s"]
starts = [m.start() for m in re.finditer(r"\S+(?: \S+)*", hdr)][1:]
assert len(starts) == 16, (len(starts), hdr)
ref = {}
for l in lines:
    m = re.match(r"\s*((?:JW|DM|LK|OR)\d+ [A-D])\s", l)
    if not m: continue
    row = {c: "" for c in cols}
    for t in re.finditer(r"\S+", l[m.end():]):
        pos = t.start() + m.end()
        j = min(range(16), key=lambda k: abs(starts[k] - pos))
        assert not row[cols[j]], (m[1], t.group(), cols[j])
        row[cols[j]] = t.group()
    ref[m[1]] = row
img = {r["Inclusion"]: r for r in csv.DictReader(open(img_csv))}
print("rows: reference", len(ref), "image", len(img), "missing", set(ref) ^ set(img))
cells = filled = 0; errors = []
for k, r in ref.items():
    for c in cols:
        cells += 1; filled += bool(r[c])
        a, b = img[k][c].strip(), r[c].strip()
        if a != b: errors.append((k, c, "image:" + (a or "blank"), "text:" + (b or "blank")))
print(f"cells {cells}, non-blank {filled}, mismatches {len(errors)}")
for e in errors: print("  ", *e)
