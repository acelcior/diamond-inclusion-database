---
tags: [quality]
---

# Extraction confidence

Every inclusion record and every temperature/pressure estimate gets a confidence level: **high**,
**medium** or **low**. It answers one question: *how sure are we that this record matches what the
paper printed?* It does **not** say whether the science is right. Problems in the paper itself
(undefined notation such as `nd`, uncertain mineral names, a total that leaves out an oxide) are
kept as separate flags.

Levels are computed by the rules below in `scripts/build_gold.py` (`assess_confidence`) and stored
in `extraction_confidence` with the rule version, so every level can be traced and recomputed.
Related: [schema issues](schema-issues.md) · [log](log.md)

## Rules, version `conf-v4` (from 2026-11-05; v1 had no calibration step, v2 no independent-copy check, v3 no compilation rule)

1. **Start from how the values were read**:
   - spreadsheet or machine-readable supplement → *high*
   - PDF text layer, read by column position and checked against page images → *high*
   - transcribed by eye from page images → *medium*
2. **Check the analysis against its own printed total** (oxide analyses only):
   - total equals the sum of the printed oxides (within rounding) → no change
   - total differs, and the source explains why (e.g. an oxide left out) → no change, noted
   - total differs, unexplained → *low*
   - no printed total to check → one level down
3. **Calibrated image reading** (new in v2): an image-transcribed analysis whose printed total checks
   out (matches, or differs for a reason the source gives) is raised to *high*. Image-read records
   with no total to check stay *medium*: the calibration doesn't cover the errors only a total
   would catch.
4. **Independent copy** (new in v3, host-diamond records): if a compilation that cites this paper
   (an independent transcription) has the same values, the record is *high*. If it differs and the
   difference isn't explained (e.g. by a documented compiler convention), the record is *low*.
5. **Curator review**: a paper approved after a spot-check against the PDF raises a *medium*
   record whose total check passed to *high*. Review never raises a *low*.
6. Records **named but not analysed** (a phase listed in an assemblage) keep the level from rule 1.
7. **Compilation rows** (new in v4, D-013): *medium*. Our copy of the compilation is exact, but the
   compiler's copy of the paper has not been checked: in the Phillips 2004 check the compiler had
   converted V₂O₅ to V₂O₃ and rescaled totals for some analyses. A compilation row is raised only
   when the cited paper is extracted and the values agree (rule 4 applied to inclusions; not yet built).

## What the levels mean in practice

| Level | Meaning |
|---|---|
| high | Machine-read and self-consistent, or hand-read and also checked by a person. |
| medium | Probably right, but some error types can't be ruled out automatically, e.g. small values or two swapped cells in an image-read table. Check before relying on one value. |
| low | A check failed. Don't use without looking at the source. |

## Calibration

**Test 1 (2026-11-03): Gress et al. (2021) Table 3**, sulphide inclusion chemistry, p. 5.
Phillips Table 3 could not be used: its values were already known from earlier work, so it would
have tested memory, not reading. Gress Table 3 had not been seen.

- Claude transcribed the table from 220-dpi page images only and saved the result
  ([transcription](../gold/calibration/gress-2021-table3-image-transcription.csv)) before reading the
  text layer. `extraction/calibrate_gress_2021.py` then compared it with the text layer cell by cell.
- **Result: 0 mismatches in 576 cells** (416 values, 160 blanks, 36 sample labels). The script caught
  all three errors planted in a test copy, so the comparison works.
- **What it means:** for a clean, born-digital table read at high resolution, the error rate is
  probably below about **0.7 %** of values (95 % upper bound for 0 errors in 416). One table is a
  small sample, and this one had no minus signs, rotation or poor print.

**Test 2 (2026-11-03): Gress et al. (2021) Table 5**, sulphur isotopes, p. 9: unseen, with many
negative values, printed dashes, blank cells and three sub-tables. Transcribed from a 220-dpi
image ([transcription](../gold/calibration/gress-2021-table5-image-transcription.txt)), then compared by
`extraction/calibrate_gress_2021_table5.py`. **0 mismatches in 97 values and 17 labels.** A copy with
a dropped minus sign, a misread digit and a swapped pair was caught (4 cells).

**Combined: 0 errors in 513 values**, so the error rate is probably below about **0.6 %**
(95 % upper bound). That supports rule 3. Not tested: scanned (not born-digital) pages and tables
that must be read while rotated. Rotated tables are turned upright before reading, as for Kankan II.
