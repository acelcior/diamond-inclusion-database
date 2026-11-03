"""Calibration test 2: Gress et al. (2021) Table 5 (p. 9; negative values, dashes, blanks) read from images vs its text layer.

Run from the project folder (needs the local PDF):
    python3 -I extraction/calibrate_gress_2021_table5.py papers/gress-2021.pdf gold/calibration/gress-2021-table5-image-transcription.txt

Result on 2026-11-03: 97 values, 0 mismatches; a planted sign error, misread and swap were all caught.
"""
import re, subprocess, sys
pdf, img = sys.argv[1], sys.argv[2]
# text layer of the table area only (left column of p. 9, 72-dpi units)
text = subprocess.run(["pdftotext", "-f", "9", "-l", "9", "-x", "30", "-y", "80", "-W", "275", "-H", "225",
                       "-layout", pdf, "-"], capture_output=True, text=True).stdout
norm = lambda t: t.replace("−", "-")
labels = re.compile(r"^\s*((?:LK|OR)\d+ [A-Z]\d|Galena-ED \(PbS\)|Galena-ET \(PbS\)|Py-Emerald \(FeS2\)|Mif-Po \(FeS\))\s")
ref, section = [], ""
for line in text.splitlines():
    if "True composition" in line: section = "true "
    if "Measured composition" in line: section = "measured "
    m = labels.match(line.replace("FeS₂", "FeS2"))
    if m:
        ref.append((section + m[1] if section else m[1], norm(line.replace("FeS₂", "FeS2")[m.end():]).split()))
mine = [(l.split("|")[0].strip(), l.split("|")[1].split()) for l in open(img, encoding="utf-8") if "|" in l and not l.startswith("#")]
print("rows: text layer", len(ref), "image", len(mine))
values = errors = 0
for (rl, rv), (il, iv) in zip(ref, mine):
    values += len(rv)
    if rl != il: print("  label:", il, "vs", rl); errors += 1
    if rv != iv:
        print("  ", rl, "| image:", " ".join(iv), "| text:", " ".join(rv))
        errors += sum(a != b for a, b in zip(rv, iv)) + abs(len(rv) - len(iv))
print(f"values {values}, mismatching cells {errors}")
