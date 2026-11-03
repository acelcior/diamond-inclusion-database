---
tags: [log]
---

# Progress log

Newest first. One short entry per working session: what was done, what was decided,
what's next. Related: [roadmap](roadmap.md)

## 2026-11-03 — Sobolev 2004 extracted (not yet reviewed)
- `extraction/parse_sobolev_2004.py`: Tables 3, 4, 5, 6, 8 (63 analyses, 579 values: olivine, chrome
  spinel, garnet, majoritic garnet, pyroxenes) from the text layer; column headers listed by hand
  from the page images (Table 5's Syt-1 has two columns). Table 7 (SIMS traces) not extracted.
- `scripts/build_gold.py` now loads every `gold/<paper>/`: `load_phillips` for Phillips, new
  `load_simple` for one-row-per-analysis papers. Handles `<0.03` (below detection, with limit),
  `41.7 (2)` (1σ in the last digit where the table defines it), sample-prefix → mine from the
  footnotes, and keeps same-label samples in different tables apart unless the text links them
  (Yum-27 linked; AL-1 kept apart). Checks and review status are per paper.
- All printed totals match the oxide sums within 0.07 wt%. Flags: two undefined `n.d.` (Table 6),
  undefined `( )` in Table 5, AL-1 label reuse. Shown on the website as "not yet reviewed".

## 2026-11-03 — Website is now the database explorer
- `site/index.html` (Tabulator 6.3.1 from jsDelivr) shows two tables: inclusions & chemistry, and
  temperature & pressure. Search, quick filters, number filters (`>40`, `40-45`), a column chooser
  with presets, "hide columns with no values", CSV export of the current view, row details with
  provenance, and a Sources list with citations and DOIs at the top.
- Data comes from `scripts/export_site.py`, which writes `site/data/*.json` from the database only,
  so new papers show up without changes to the page. Vercel's root directory is now `site/`, so
  docs no longer appear on the website; they stay on GitHub.

## 2026-11-03 — Phillips 2004 approved
- User checked the 25-value spot-check list and the stored tables against the PDF: all matched.
  Recorded in `gold/phillips-2004/source.json` (`review`); the build now marks every record `approved`.
- Flag decisions (Claude's recommendations, accepted): DP209 `nd` stays `ambiguous`; DP497 Brey &
  Köhler pressure left blank; DP539 paragenesis kept as two attributed views (paper Web, compilation e).
- **Next:** seed paper 2 (Nimis 2025: needs Supplementary Table S1) or another Batch A/B paper.

## 2026-11-03 — Phase 2: Phillips 2004 extracted (awaiting review)
- `extraction/parse_phillips_2004.py` reads Tables 3 and 4 from the PDF's text layer by column
  position; checked against page images of pp. 160, 161, 171. Output, as printed:
  `gold/phillips-2004/table3.csv` (80 EPMA analyses, 36 diamonds), `table4.csv` (50 P-T rows).
- `scripts/build_gold.py` loads schema + `vocab/` (new, minimal) + the CSVs into `gold/gold.sqlite`:
  50 diamonds, 109 inclusion observations, 1120 values, 122 temperatures/pressures on 50 inclusion
  sets, each traceable to page/table/column. Writes the review page `gold/phillips-2004/README.md`.
- Checks: every printed Total equals the sum of its printed oxides; flags `nd` (DP209 chromite SiO2)
  and the blank DP497 Brey & Köhler pressure. Nothing guessed.
- `scripts/compare_compilation.py`: 57/80 analyses match Stachel's compilation within rounding
  once its V2O5→V2O3 conversion and 100 % rescaling are applied; 10 differ by >0.1 wt% (different
  analyses, likely from the paper's online data repository); DP539 paragenesis differs (Web vs e).
- 8 schema issues recorded in [schema issues](schema-issues.md). Tests: 9 pass.
- **Next:** you work through the spot-check list; then mark records approved. Getting the paper's
  online data repository file would let us add all ~650 analyses.

## 2026-11-03 — Docs website on Vercel
- `index.html` renders the repo's Markdown docs and schema in the browser (no build step), so the
  site always shows the committed docs. Hosted on Vercel (team linked to GitHub `acelcior`),
  public at https://diamond-inclusion-database.vercel.app; every push to `main` redeploys.
  Preview links need a Vercel login. No data pages yet.
- Repo commit email set to acelcior's GitHub noreply address (repo-only setting), so Vercel
  accepts pushes; commits with the Mac's default email were blocked.

## 2026-11-03 — Demo tables removed
- Removed the compilation-table demo (`scripts/build_demo_db.py`, `demo/`): its data came only
  from the Stachel spreadsheets, not from papers. Recoverable from commit 11e4ed0.
- The next demo should show data curated from the seed papers into `schema/001_core.sql`.

## 2026-10-22 — Browsable demo
- `scripts/build_demo_db.py` builds `demo/demo.sqlite` (gitignored) from the two Stachel
  compilations as-is: readable column names with units, key columns first, plotting codes dropped,
  paragenesis decoded for simple codes only, full-text search index. Values unchanged.
- Datasette view with `demo/metadata.json` (titles, licence/source, facets, column notes, quick
  links, two summary queries) and `demo/static/style.css` (sticky header, compact notes).
- This is raw compilation data, not the project schema; the real explorer is Phase 7.

## 2026-10-22 — Phase 1: core schema v0
- Wrote `schema/001_core.sql`: 25 tables + 2 views, from D-001 – D-004. Observations are what a
  source reported; physical diamonds/inclusions are clusters of observations joined by approved
  identity links (views `inclusion_cluster`, `diamond_cluster`). Values in long format with
  original text, value status and derivation; evidence per measurement/assertion.
- `tests/test_schema.py` (stdlib only; illustrative data): schema loads, a record round-trips,
  bad rows are rejected, clusters count correctly. 5/5 pass on SQLite 3.54.1; a deliberately
  removed constraint makes a test fail, so the tests bite.
- Added `calculated_by_compiler` and `imported_unverified` to the status lists (brief §7).
- Not done: PostgreSQL load test (not installed), vocabularies in `vocab/`, Tier 1 data dictionary.
- **Next:** seed vocabularies, then the data dictionary; Phase 1 exit gate is met for SQLite.

## 2026-10-22 — Phase 1: blocking decisions drafted
- Drafted D-001 – D-005 as **proposed** (not accepted), each with a plain-language summary:
  observations + reviewable identity links (D-001); provenance per measurement/assertion (D-002);
  long-format values + typed tables + generated wide views (D-003); SQLite + Datasette with
  portability rules (D-004); scope table with questions for the professor (D-005).
- User accepted D-001 – D-004 as drafted; D-005 stays proposed until the professor answers.
- **Next:** draft `schema/001_core.sql` (Phase 1).

## 2026-10-22 — Phase 1: compilations mapped
- Read both Stachel PDF dictionaries and profiled all four workbooks (read-only, macros
  never run; added `openpyxl` to `.venv/`). Wrote [compilations mapping](compilations-mapping.md).
- Key facts: Stachel `All diamonds` = 10,472 rows, one inclusion analysis per row with host
  data repeated; 2,049 host-only rows; 146 references; 262 mineral spellings; ~900 non-numeric
  oxide entries (`b.d.`, `<0.02`, `≤0.03`…). Walter and Smit have no DOIs.
- Seed overlap: Phillips 2004 = 653 rows cited as "unpubl and Phillips et al. (2004)";
  all Kankan rows cite Kankan I's DOI (so A3a really is the data source); Gress 2021 in Smit.
- Findings recorded against D-001, D-002, D-003, D-006, D-008, D-010, D-013 (none decided).
- **Next:** decide the blocking ADRs D-001 – D-005, then draft `schema/001_core.sql`.

## 2026-10-22 — Batch B and Dataset 0 received
- Received B2–B5 (Gress 2021, De Hoog 2019, Anzolini 2016, Sobolev 2004); identified from
  page 1 and renamed. Still missing: B1 (Meyer & Boyd 1972), and A3a
  (Kankan I, added after the user's first download, so it was never on their list).
- Dataset 0: all four compilations unpacked into `papers/compilations/`; every file
  matches Borealis's published MD5 checksum.
- Claude downloaded A5 (Genzel 2023, open access) from the publisher as `genzel-2023.pdf`.
- No supplement files yet (Nimis Table S1 and Kankan I's supplement are both needed).

## 2026-10-22 — First papers received
- 4 of 5 Batch A PDFs in `papers/`, renamed to `firstauthor-year.pdf`; all match their
  verified citations. Still missing: A5 (Genzel 2023) and the Dataset 0 compilations.
- Kankan II prints only *selected* inclusions; the full EPMA dataset is in Kankan I's
  electronic supplement, so Kankan I (10.1007/s004100000173, verified) was added as A3a.
  Nimis 2025 has a Supplementary Table S1.
- Kankan II/III PDFs have an encoded text layer (decodable, but spaces are lost); their
  tables need to be read from page images. Created `.venv/` with `pypdf`; installed
  poppler (Homebrew), and page images of the Kankan PDFs now read cleanly.
- **Next:** user downloads A3a + its supplement, Nimis S1, A5, Dataset 0; then Phase 1.

## 2026-10-21 — Seed papers found
- User filled in constraints: team project on contract for a professor; ~2–3 h/week; very
  little Python; Claude Pro plan only; Binghamton library access; shared with collaborators.
- Proposed seed papers in [inputs needed](inputs-needed.md): Batch A (5, arranged as
  specimen-sharing pairs) and Batch B (5). All citations/DOIs verified against OpenAlex/Crossref.
  One remembered DOI (Meyer & Boyd 1972) was wrong and was corrected by the lookup.
- Found four CC0 literature compilations on Borealis (Stachel major-element and trace-element
  databases; Walter et al. sublithospheric; Smit et al. radiogenic isotopes): "Dataset 0".
- New decisions D-013 (build on the compilations?) and D-014 (extraction under Pro plan);
  D-004 lean changed to SQLite + Datasette. Roadmap gained a constraints section.
- **Next:** user downloads Batch A + Dataset 0 into `papers/`; asks the professor the
  questions in inputs-needed; then Phase 1.

## 2026-10-21 — Project setup
- Created project structure: `CLAUDE.md`, revised [brief](brief.md), [roadmap](roadmap.md),
  [decision register](decisions/README.md), [inputs needed](inputs-needed.md).
- Brief revised from the original prompt: diamond-specific issues (observed vs inferred
  phase, inclusion context, group-level measurements, recomputable P-T, ambiguous table
  notation), three separate status dimensions, capture tiers, success criteria.
- **Next:** fill in [inputs needed](inputs-needed.md); choose seed papers; then Phase 1
  (blocking ADRs D-001 – D-005, schema v0).
