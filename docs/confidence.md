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

## Not yet calibrated
These rules are a first version. Planned calibration: transcribe Phillips (2004) Table 3 from images
only and compare it cell by cell with the verified text-layer values, to measure the real error
rate of image reading. Then revisit rule 1.
