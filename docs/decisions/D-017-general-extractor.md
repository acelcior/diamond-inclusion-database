---
id: D-017
status: accepted   # by J. Dasroy, 2026-11-17; the professor has not been asked
date: 2026-11-17
tags: [decision, phase-3]
---

# D-017 — One general table extractor, started before the Phase 2 gate

**In plain words:** instead of writing a new program for every paper, one program reads tables from any
text-layer PDF, guided by a short per-paper note of hints. It was built before the checked ("gold") set
was frozen, which the roadmap says not to do, so this page records why.

## Context
431 papers are marked relevant. Each of the first four needed its own parser and about one session,
which would take years. The roadmap gate says not to automate until the gold set is frozen and schema
v1 is tagged; two of the four gold papers (Kankan II and III) are still waiting for review.

## Options
1. **Keep one parser per paper** until the gate is met. Safe, and too slow to reach the literature.
2. **One general extractor now**, accepted only if it reproduces the reviewed gold papers cell for cell,
   writing the same files the loader already reads. New papers enter as not yet reviewed.
3. **Claude types every table by hand** into the standard file. No code, but every number is a
   transcription; kept only for pages with no usable text layer (the calibrated image route).

## Decision
Option 2. `extraction/extract.py` reads tables printed with one analysis per column (oxides down the
side) from `pdftotext -layout` output. Per-paper knowledge is data, not code: the `extract` hints
(table title, page, sample and mineral names where the text layer garbles them, facts from footnotes).
It writes `analyses.csv` in the format `scripts/build_gold.py` (`load_simple`) already loads, so the
existing checks, flags, confidence rules and review page apply unchanged. New papers go in
`extracted/<paper>/` with a `source.json`, not in `gold/`, which stays the benchmark.

The loader now reads every value column whose header is a quantity in `vocab/quantity.csv` (or mapped
in `column_quantity`) and stops on a header it does not know, so a printed column is never dropped
silently. Adding the quantity to the vocabulary is still a deliberate step (D-016 is not decided).

## Consequences
- Skips the Phase 2 exit gate. Risk: the schema may still change after Kankan II/III review; the
  standard file is the loader's own input, so a schema change is absorbed by the loader, not the files.
- D-014 (a few papers a week) is no longer the ceiling for text-layer tables; real throughput is not
  measured yet.
- **Not covered yet:** tables with one analysis per row (oxides across the top), spreadsheet
  supplements, P-T and isotope tables, and image-only pages. A scan of the 50 downloaded open-access
  PDFs found oxide tables in 16: 6 with oxides down the side, 10 only across the top. 34 print no oxide
  table in the main text (data in supplements, or other kinds of data).
- Every extracted paper still needs its `source.json` (citation, method, localities with page and
  excerpt, notation per table) and a human spot-check before approval.

## Evidence / test cases
- **Phillips et al. (2004) Table 3** (approved): 1,600 of 1,600 cells agree with `gold/phillips-2004/table3.csv`
  (80 analyses in four blocks; sample names spanning several columns; wrapped header cells).
- **Sobolev et al. (2004) Tables 3-6 and 8** (approved): 1,386 of 1,386 cells agree with
  `gold/sobolev-2004/analyses.csv` (63 analyses; `<0.03`, `n.d.`, `41.7 (2)` notation; a narrow table
  beside body text). Loading the extractor's output gives records identical to the gold load
  (63 analyses, 579 values, same flags).
- Hints used: `extraction/hints/phillips-2004.json`, `extraction/hints/sobolev-2004.json`. Rerun with
  `python3 -I extraction/extract.py extraction/hints/sobolev-2004.json --compare gold/sobolev-2004/analyses.csv`.
- **Not tested:** Kankan II and III (no usable text layer; read from page images, rule 3 in
  [confidence](../confidence.md)). The hints for the two tested papers were taken from their existing
  parsers, so this shows the general code is equivalent to them, not that an unseen paper works first time.
- Offline test with an illustrative table: `tests/test_extract.py`.
