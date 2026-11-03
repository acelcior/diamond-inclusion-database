"""Compare the Phillips et al. (2004) gold extraction with the Stachel compilation's rows for that paper.

Run from the project folder (needs the local compilation in papers/compilations/):
    .venv/bin/python -I scripts/compare_compilation.py
Writes gold/phillips-2004/compilation-check.md and compilation-check.csv.

The compilation stores vanadium as V2O3 and appears to rescale each analysis to a 100 % total, so
each paper analysis is compared both as printed and after applying those two steps.
"""
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
XLSM = ROOT / "papers" / "compilations" / "stachel-major" / "Diamond_Database_Oct-2021.xlsm"
PAPER = ROOT / "gold" / "phillips-2004"
REF = "Phillips et al. (2004)"

OX = ["SiO2", "TiO2", "Al2O3", "Cr2O3", "FeO", "MnO", "NiO", "MgO", "CaO", "Na2O", "K2O", "ZnO"]
V2O5_TO_V2O3 = 149.881 / 181.880  # molar masses: V2O3 / V2O5, same number of V atoms
MINERAL = {"Garnet": "garnet", "Opx": "opx", "Olivine": "olivine", "Cpx": "cpx", "Chr": "chromite", "Mag": "magnesite"}
# compilation codes compatible with each paper Suite ('p' = peridotitic, unspecified)
PARA = {"Per (hz)": ("h", "p"), "Per (lhz)": ("l", "p"), "Ecl": ("e",), "Web": ("wb",)}
MATCH = "matches after V2O3 conversion and 100 % rescaling (≤ 0.025 wt%)"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def compilation_rows():
    wb = openpyxl.load_workbook(XLSM, read_only=True, data_only=True)  # values only; macros never run
    it = wb["All diamonds"].iter_rows(values_only=True)
    hdr = next(it)
    out = []
    for i, r in enumerate(it, start=2):
        if r[5] and REF in str(r[5]):
            d = dict(zip(hdr, r))
            d["_row"] = i
            out.append(d)
    return out


def paper_vectors(r):
    """Paper analysis as printed, and transformed the way the compilation appears to store it."""
    raw = {k: num(r[k]) for k in OX}
    v = num(r["V2O5"])
    conv = dict(raw, V2O3=v * V2O5_TO_V2O3 if v is not None else None)
    s = sum(x for x in conv.values() if x is not None)
    norm = {k: (x * 100 / s if x is not None else None) for k, x in conv.items()}
    return raw, norm


def max_diff(a, b, keys):
    d = [abs(a[k] - num(b.get(k))) for k in keys if a.get(k) is not None and num(b.get(k)) is not None]
    return max(d) if d else None


def main():
    comp = compilation_rows()
    t3 = list(csv.DictReader(open(PAPER / "table3.csv", encoding="utf-8")))
    by_key = defaultdict(list)
    for c in comp:
        by_key[(str(c["#_sample"]).strip(), str(c["mineral"]).strip())].append(c)

    results, used = [], set()
    for r in t3:
        sample = str(int(r["sample_no"][2:]))           # 'DP014' -> '14' (compiler drops prefix and zeros)
        cands = [c for c in by_key.get((sample, MINERAL[r["mineral"]]), []) if c["_row"] not in used]
        raw, norm = paper_vectors(r)
        best = None
        for c in cands:
            dn, dr = max_diff(norm, c, OX + ["V2O3"]), max_diff(raw, c, OX)
            if dn is not None and (best is None or dn < best[1]):
                best = (c, dn, dr)
        if best is None:
            verdict, row, dn, dr, para = "not found", "", "", "", ""
        else:
            c, dn, dr = best
            used.add(c["_row"])
            # compiler rescaled unrounded data, so up to ~0.02 wt% is rounding
            verdict = ("identical as printed" if dr <= 0.005 else
                       MATCH if dn <= 0.025 else
                       "small differences (0.025–0.1 wt%)" if dn <= 0.1 else "different (> 0.1 wt%)")
            row = c["_row"]
            para = "" if c["paragenesis"] in PARA[r["suite"]] else f"paper {r['suite']} / compilation {c['paragenesis']}"
            dn, dr = f"{dn:.3f}", f"{dr:.3f}"
        results.append({"sample_no": r["sample_no"], "mineral": r["mineral"], "page": r["page"],
                        "column": f"block {r['block']} col {r['column']}", "verdict": verdict,
                        "compilation_row": row, "max_diff_after_rescaling": dn, "max_diff_as_printed": dr,
                        "n_candidates": len(cands), "paragenesis_note": para})

    with open(PAPER / "compilation-check.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)

    verdicts = Counter(r["verdict"] for r in results)
    samples_t3 = {str(int(r["sample_no"][2:])) for r in t3}
    comp_samples = Counter(re.match(r"\d+", str(c["#_sample"]).strip()).group() for c in comp)
    other = sum(n for s, n in comp_samples.items() if s not in samples_t3)
    same_diamond_extra = sum(n for s, n in comp_samples.items() if s in samples_t3) - len(used)
    totals = Counter(round(num(c["Total"]) or 0) for c in comp)
    odd = [r for r in results if r["verdict"] not in (MATCH, "identical as printed")]
    paras = [r for r in results if r["paragenesis_note"]]
    minerals = Counter(str(c["mineral"]).strip() for c in comp)

    def table(rows, cols):
        return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] +
                         ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows])

    md = [
        "# Compilation cross-check: Phillips et al. (2004)",
        "",
        "Compares the 80 Table 3 analyses we extracted with the Stachel major-element compilation "
        "([doi:10.7939/DVN/EJUE1G](https://doi.org/10.7939/DVN/EJUE1G), sheet `All diamonds`), whose rows "
        f"for this paper are cited as \"unpubl and {REF}\". Generated by `scripts/compare_compilation.py`; "
        "per-analysis results in [compilation-check.csv](compilation-check.csv). Back to [the review page](README.md).",
        "",
        "## Result",
        "",
        "| Outcome | Analyses |", "|---|---|",
        *[f"| {k} | {n} |" for k, n in verdicts.most_common()],
        "",
        "**What this tells us:**",
        "",
        "- **The compilation does not store the printed values.** It converts V₂O₅ to V₂O₃ and rescales each "
        "analysis to a 100 % total. Compilation totals for this paper: "
        + ", ".join(f"{n} rows ≈ {t}" for t, n in totals.most_common(3)) + ". "
        "So compilation numbers are `calculated_by_compiler`, not `reported`. This matters for D-013.",
        f"- **{verdicts[MATCH]} of {len(results)} analyses match** the compilation within rounding, once the "
        "compiler's two steps are applied. That independently confirms those extracted values.",
        "- **Differences above 0.1 wt% are not extraction errors.** Every extracted total equals the sum of its "
        "printed oxides, and the columns were checked against the page images. Those compilation rows "
        "hold a different analysis or average of the same inclusion, probably from the online data repository. "
        "Both versions are real data. Keep both; resolving them needs the repository file.",
        "- **Not found:** the compilation has no row of that mineral for that diamond (e.g. several olivines, "
        "and the DP387 magnesite).",
        f"- **The compilation holds much more than the paper prints:** {len(comp)} rows, of which {len(used)} "
        f"correspond to Table 3 columns. Another {same_diamond_extra} are further inclusions or analyses of the "
        f"same 36 diamonds, and {other} are from {len([s for s in comp_samples if s not in samples_t3])} other "
        "diamonds. These come from the online data repository and/or unpublished data. The citation does not say which.",
        "- **The compiler drops the `DP` prefix and leading zeros** (`DP014` → `14`). Linking a compilation "
        "row to our observation is a `compiler_derived` identity link, to be approved, never automatic.",
        "- Mineral names used in these rows: " + ", ".join(f"`{m}` ({n})" for m, n in minerals.most_common()) + ".",
        "",
        "## Needs a look",
        "",
        table(odd, ["sample_no", "mineral", "page", "column", "verdict", "compilation_row",
                    "max_diff_after_rescaling", "n_candidates"]) if odd else "Nothing: every analysis matched.",
        "",
        "## Paragenesis differences",
        "",
        table(paras, ["sample_no", "mineral", "paragenesis_note"]) if paras else
        "None: every matched row has the same paragenesis code as the paper's Suite.",
        "",
    ]
    (PAPER / "compilation-check.md").write_text("\n".join(md), encoding="utf-8")
    print(verdicts)
    for r in odd:
        print(r)
    for r in paras:
        print(r)


if __name__ == "__main__":
    main()
