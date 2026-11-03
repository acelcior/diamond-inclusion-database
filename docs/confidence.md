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

## Rules, version `conf-v1`

1. **Start from how the values were read**:
   - spreadsheet or machine-readable supplement → *high*
   - PDF text layer, read by column position and checked against page images → *high*
   - transcribed by eye from page images → *medium*
2. **Check the analysis against its own printed total** (oxide analyses only):
   - total equals the sum of the printed oxides (within rounding) → no change
   - total differs, and the source explains why (e.g. an oxide left out) → no change, noted
   - total differs, unexplained → *low*
   - no printed total to check → one level down
3. **Curator review**: a paper approved after a spot-check against the PDF raises a *medium*
   record whose total check passed to *high*. Review never raises a *low*.
4. Records **named but not analysed** (a phase listed in an assemblage) keep the level from rule 1.

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

**Rule 1 is unchanged for now** (image transcription starts at *medium*). Raising it needs a second
test on a harder table: rotated, older, with negative numbers (for example δ¹³C).
