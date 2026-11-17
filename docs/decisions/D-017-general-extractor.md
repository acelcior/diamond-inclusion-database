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
Option 2. `extraction/extract.py` reads tables from `pdftotext -layout` output in both common layouts: one
analysis per column (oxides down the side) and, with `"layout": "rows"`, one analysis per row (oxides across
the top). Per-paper knowledge is data, not code: the `extract` hints
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
- **Not covered yet:** spreadsheet supplements, P-T and isotope tables, element (non-oxide) tables such as
  sulfides, PDFs whose text layer scrambles
  the table (e.g. the accepted manuscript of Smith 2016), and image-only pages.
- **Coverage (approximate, by text search of the 50 downloaded open-access PDFs):** about 10 print an oxide
  table in the main text, 9 with oxides down the side and 1 across the top. The other 40 keep their data
  in supplements or report other kinds of data. A first, cruder search that reported 10 across-the-top
  tables was wrong: it counted sentences and reference lists that name several oxides.
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
- **Gress et al. (2021) Table 3** (across the top, many blank cells): 612 of 612 cells agree with the
  transcription made independently from page images (`gold/calibration/`); hints in
  `extraction/hints/gress-2021-table3.json`.
- **Two papers never seen before**, checked against their own printed totals (`--totals`), not by a person:
  Gress et al. (2018) Table 2, across the top: 46 analyses, 42 totals within 0.15 wt% and 4 off by at most
  0.17 (the table prints rounded averages). Zhao et al. (2022) Table 2, down the side, indented, labels printed
  as `Al2 O3`, `TFeO`, `Σ`: the first 13 analyses read and all 13 totals add up; the 48 number rows on its two
  continuation pages carry no labels in the text layer and were reported as not read.
- **Zhao (2022) Tables 2-5**, loaded: 66 analyses, all 66 totals within 0.05 wt%. Continuation pages printed
  without row labels are read with `"continued": "unlabelled"` (labels taken from the first page in order; without
  the hint such rows are still reported as unread, never guessed). Columns cited from other papers are cut off.
- **Not tested:** Kankan II and III (no usable text layer; read from page images, rule 3 in
  [confidence](../confidence.md)). The hints for the two tested papers were taken from their existing
  parsers, so this shows the general code is equivalent to them, not that an unseen paper works first time.
- Offline test with an illustrative table: `tests/test_extract.py`.
