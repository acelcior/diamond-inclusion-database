---
tags: [log]
---

# Progress log

Newest first. One short entry per working session: what was done, what was decided,
what's next. Related: [roadmap](roadmap.md)

## 2026-11-17 — Zhao (2022), Fuxian No. 50 pipe, China
- **Zhao (2022)**, Minerals 12, 844 (CC BY): Tables 2-5, 66 inclusions (42 olivine, 14 chromite, 6 garnet,
  4 orthopyroxene) in 36 diamonds, 726 values → [review page](../extracted/zhao-2022/README.md). All 66 printed
  totals equal the oxide sum within 0.05 wt%. Tables checked against page images of pp. 14-19. `pending_review`.
- **Extractor:** new hint `"continued": "unlabelled"` for continuation pages printed without row labels
  (Table 2, pp. 15-16): each line takes the label of the same line on the first page. Confirmed on the page
  images that the printed pages really have no labels. Test added.
- **Loader:** a table's `identity_note` in `source.json` now shows as a flag "inclusion count unclear"; the
  "same label, kept apart" flag is no longer raised when a paper's sample label is its diamond key.
- **Judgements to check at review:**
  - Table 3 lists four chromite grains for LN50D07 (Sp 1-4) while the text and Figure 3 (p. 7) describe three
    chromite inclusions. Stored as four, as the table's "Grain" row labels them; flagged, not resolved.
  - Chromite grain labels (Sp2 ... Sp 2) are listed by hand from the page image: the text layer puts two of
    them under one column.
  - `TFeO` is stored as total iron as FeO (`FeOT`).
  - This PDF's hidden text is offset on some pages (p. 8 carries text printed on p. 7), so page numbers of
    quoted statements were taken from page images.
- **Left out, with reasons:** columns of Tables 4 and 5 taken from Harris et al., Wang & Guo and Meyer et al.
  (repeat reports; to be read from the original papers); the authors' recalculated Fe2O3/FeO and second total
  (calculated, not measured); Table 6 sulfides (element wt% not in the vocabulary; several columns may be phases
  of one inclusion); Tables 7-8 unknown phases (water by difference; six analyses of one inclusion).
- Website data regenerated: 8 papers, 8,970 inclusion reports, 99,011 values. Not committed or pushed.
- **Next:** Thomson et al. 2014 (`eimf-2014.pdf`) and the 2015 São Luiz paper; then supplements. Zhao's
  sulfides need a decision on element quantities (D-016).

## 2026-11-17 — Third paper, and what the remaining downloads need
- **Wiggers de Vries et al. (2011)**, Udachnaya, Yakutia (CC BY-NC): Table 1, 7 chromite, olivine and phlogopite
  inclusions in one diamond (#3615), 84 values, with each inclusion's position (core, core/intermediate, rim) →
  [review page](../extracted/wiggers-de-vries-2011/README.md). All totals add up; checked against the page image.
  `n.a.` = not analysed (defined). Not extracted: trace elements with ± and Zn-thermometry temperatures in the
  same table.
- Set aside, each for a stated reason:
  - **Westerlund & Gurney 2004**: a scan; its text layer is OCR and misreads characters, so it needs the image
    route. Its major elements are already in the Stachel compilation.
  - **Kaminsky et al. 2023** (Minerals 13, 1217; listed in the inventory under its preprint DOI): the table's text
    layer is scrambled, so it needs the image route. Several of its analyses are the same grains as in Kaminsky &
    Kostitsyn 2025 (same sample labels and values), so loading it also needs identity links between the two papers.
  - **Zhao et al. 2022**: eight tables; continuation pages without row labels, sample names spanning columns,
    two totals per analysis (before and after the authors' Fe2O3 recalculation), and columns that may come from
    other studies. Worth a session of its own.
- Website data regenerated: 7 papers, 8,904 inclusion reports. Not pushed.
- **Next:** Zhao 2022 in its own session; Thomson et al. 2014 (Juina-5; filed as `eimf-2014.pdf` because OpenAlex
  lists a facility as first author) and the 2015 São Luiz paper; then supplements.

## 2026-11-17 — First two papers through the general extractor
- **Gress et al. (2018)**, Jwaneng, Botswana (CC BY): Table 2, 46 clinopyroxene and garnet inclusions in 16
  diamonds, 552 values → [review page](../extracted/gress-2018/README.md). All totals agree within the rounding
  of the printed averages (tolerance 0.35 wt%, largest difference 0.17). Flags: `–` in two Cr₂O₃ cells is not
  defined in the table, so it is stored as ambiguous. Printed totals are low (91.8-100.4): unpolished grains.
- **Kaminsky & Kostitsyn (2025)**, Rio Sorriso placer, Juina, Brazil (CC BY): Table 1, 8 CaSiO₃, Ca(Si,Ti)O₃ and
  ferropericlase inclusions in 3 diamonds, 96 values → [review page](../extracted/kaminsky-2025/README.md).
  All totals add up. `bdl` is defined by the paper (below detection, no limits given). Flags: `Ca(Si,Ti)O3` is
  not in the mineral vocabulary and is kept as printed. Grain `2.2.1-2` is assigned to diamond 2.2.2 on the
  table's grouping and the text's Mg# statement (noted on the record).
- Both tables were checked against an image of the printed page before loading. Both are `pending_review`,
  confidence high by rule 1 (text layer, checked against page images) and rule 2 (totals).
- Not extracted from these papers: host-diamond δ13C and nitrogen, trace elements, isotopes, authors' depth
  interpretations (listed in each paper's notes).
- Loader: new column `zone` → assertion `position_in_host` (new vocabulary property; Gress Table 2 gives core /
  int / rim, with `?` kept as printed). Vocabulary: `gnt` = garnet. Website: Botswana and Brazil country names;
  licence shown from `bibliography/downloads.csv` when a paper is not in the licence register.
- Website data regenerated: 6 papers, 8,897 inclusion reports. Not pushed.
- Tried and set aside: Curtolo 2023 (a review, and the copy is a preprint), Zhao 2022 (continuation pages have
  no row labels in the text layer), Smith 2016 (accepted manuscript, table text scrambled).
- **Next:** you spot-check the two review pages; then the remaining downloaded papers with main-text tables
  (Westerlund 2004, De Vries 2010, Kaminsky 2022), label-less continued tables (Zhao 2022), then supplements.

## 2026-11-17 — Extractor: tables with oxides across the top
- `extract.py` now reads both layouts. `"layout": "rows"` puts each cell under the header cell it sits below,
  keeps long names in their own column, splits a combined cell such as `JW030 cpx A` by a stated pattern, and
  lists any line it did not read as a row. Also new: indented rows, differently printed labels (`Al2 O3`, `Σ`),
  `Table N. Cont.` blocks, and `--totals` (each analysis against its own printed total).
- **Gress 2021 Table 3: 612 of 612 cells** agree with the checked image transcription. Phillips and Sobolev still
  agree in every cell; website data files unchanged; all four test files pass.
- Two unseen papers, checked by their printed totals only: Gress 2018 Table 2 (46 analyses; 42 totals within
  0.15 wt%, 4 off by at most 0.17, the table prints rounded averages) and Zhao 2022 Table 2 (first 13 analyses,
  all totals add up). Zhao's continuation pages print no row labels in the text layer: the extractor now reports
  those 48 rows as not read instead of passing over them. Hints for both saved in `extraction/hints/`.
- **Correction:** the earlier count of "10 papers with oxides across the top" was wrong (the search counted
  sentences that list oxides). A stricter search finds about 10 of the 50 PDFs with an oxide table in the main
  text: 9 down the side, 1 across the top. D-017 is corrected.
- Still no paper loaded into the database from the new extractor: each needs its `source.json` (method,
  localities with page and excerpt, notation) and a spot-check.
- **Next:** extract Gress 2018 end to end into `extracted/` as the first new paper (needs sulphide/trace
  quantities added to the vocabulary for its other tables); then spreadsheet supplements.

## 2026-11-17 — General table extractor (D-017)
- Decided by J. Dasroy to build one general extractor before the Phase 2 gate; recorded as
  [D-017](decisions/D-017-general-extractor.md).
- New `extraction/extract.py`: reads tables with one analysis per column from a text-layer PDF, guided by
  per-paper hints (no per-paper code), and writes the `analyses.csv` the loader already reads. Against the two
  approved text-layer papers: **Phillips Table 3: 1,600 of 1,600 cells; Sobolev Tables 3-6 and 8: 1,386 of 1,386.**
  Loading its Sobolev output gives records identical to the gold load. Hints in `extraction/hints/`.
- Loader (`load_simple`): reads every value column that is a known quantity, takes the unit from the vocabulary,
  and stops on an unknown column. `build_gold.py` also loads `extracted/<paper>/`. Website data files are
  byte-for-byte unchanged; all four test files pass (new `tests/test_extract.py`).
- **Coverage is the limit.** Of the 50 downloaded PDFs, 16 print an oxide table in the main text: 6 with oxides
  down the side (handled), 10 only across the top (not handled). The other 34 keep their data in supplements or
  report other kinds of data.
- Not tested on Kankan II/III (no usable text layer). No new paper has been extracted yet.
- **Next:** add tables with oxides across the top, using Gress 2021 Table 3 as the test (its checked transcription
  is in `gold/calibration/`); then spreadsheet supplements; then extract the first new paper end to end.

## 2026-11-17 — Open-access downloads and Consensus searches
- Asked to download and extract all relevant papers. Downloading is done as far as a script legally can; bulk
  extraction is **not started**: it means building the Phase 3 extractor ahead of the Phase 2 gate, which needs a
  recorded decision first (see Next).
- New `literature.py fetch`: downloads open-access PDFs of queued papers into `papers/oa/` and logs each in
  `bibliography/downloads.csv`. Of the 135 open-access papers in the queue: **50 downloaded** (139 MB; 36 published
  versions, 3 accepted manuscripts, 11 preprints; 27 CC BY), 35 refused the script (publisher sites answer 403 or a
  web page), 50 have no direct PDF link. Nothing closed-access was touched.
- `bibliography/manual-downloads.md` lists the 377 papers still to get by hand, as DOI links in queue order:
  85 free to read, 16 closed 2022+, 162 closed older, 114 closed older whose major elements are already compiled.
- A quick scan of the 50 PDFs: 49 have a text layer, 30 mention supplementary data, 13 print no numbered table.
- Consensus connected. Three searches (297 results): 84% already in the inventory; 38 new papers added with
  `found_by = consensus:…` and a proposed triage (1 relevant, 24 maybe, 13 not relevant; judged from titles only) in
  `bibliography/triage/2026-11-17-claude-consensus.csv`. Queue is now 431 relevant papers.
- Seeds Genzel 2023 and Nimis 2025 were downloaded again into `papers/oa/` (they already sit in `papers/`).
- **Next:** decide how to extract at scale (a general extractor tested against the four gold papers, versus one
  parser per paper as now); download closed papers through the library into `papers/inbox/`.

## 2026-11-17 — Website quick fixes
- The live site still showed Sobolev 2004 as "not yet reviewed": its data files had not been regenerated after
  the approval. Re-ran `scripts/export_site.py`; Sobolev now shows as approved.
- The table now scrolls inside its own box (Tabulator `fitData`), so the page no longer scrolls sideways and
  the Diamond ID column stays pinned. The sources list starts collapsed, so the table is on the first screen.
- Added `.claude/launch.json` so Claude can preview `site/` locally before a push.
- `tests/test_gold.py` had been failing since the Sobolev approval (it assumed only Phillips was approved); it now
  checks each paper against the review recorded in its own `source.json`. All three test files pass.
- Ideas not built yet: headline count split into extracted vs compilation rows, shareable filter links,
  a "last updated" date and data version, one simple plot of the filtered rows.
- **Next:** review Kankan II and Kankan III; ask the professor about D-005.

## 2026-11-05 — Extraction queue
- Asked to import all 265 newly relevant papers into the database. Declined as asked: importing means extracting
  each paper's tables from a legally held full text, one session per paper (D-014); registering empty publication
  rows would inflate the database's counts. Instead `literature.py queue` ranks every relevant paper for
  extraction by a fixed rule (tier by gap and access, reviews last, then links and year) into
  `bibliography/extraction-queue.csv`: 61 in tier A (2022+, readable), 16 in B, 74 in C, 275 in D, 4 already done.
- **Next:** take the top tier-A papers one or two a week; check each one's licence before downloading.

## 2026-11-05 — Bulk triage of the literature inventory
- Claude proposed a label for every one of the 1,440 untriaged candidates from title, venue and OpenAlex
  abstract (no abstract for roughly a third; those were judged from the title alone): 265 relevant,
  308 maybe, 867 not relevant. Each note starts with `Claude:` and nobody has spot-checked them yet.
  Decisions file: `bibliography/triage/2026-11-05-claude-batch2.csv`.
- Most "maybe" calls are papers that depend on scope decision D-005 (diamonds in xenoliths, fibrous and
  fluid-inclusion diamonds, polycrystalline diamonds, ophiolite and metamorphic diamonds, conference
  abstracts and theses). Once D-005 is decided, that pile can be split by rule rather than reread.
- Found and fixed: a triage note containing a comma was cut short by `decide` (the CSV was unquoted).
  The 365 affected notes were patched in the inventory and the workflow doc now says to quote.
- Citation chaining from the newly relevant papers: 246 of 288 chained (815 new candidates, 469 high priority)
  before the OpenAlex daily budget ran out; 42 remain. `python3 -I scripts/literature.py chain` tomorrow
  finishes them. Without a key the shared budget ran out in one session: the free personal key
  (see [literature workflow](literature-workflow.md), Setup) would avoid this.
- **Next:** you or the professor spot-check the `Claude:` labels (start with the 430 relevant); decide D-005
  to resolve the maybe pile; then triage the new candidates from this chaining round.

## 2026-11-05 — PostgreSQL portability check
- Decided not to switch databases yet: the database is rebuilt from source files, so more papers don't make
  the later move harder; the risk is SQLite-only SQL creeping in. D-004 revisit triggers not yet met.
- Installed PostgreSQL 17 (Homebrew; no background service). New `scripts/check_postgres.py`: schema + all
  174,142 rows load into PostgreSQL unchanged. Phase 1's "loads in PostgreSQL" gate is now met.
- Known Phase 6 diff recorded in the roadmap: auto-numbered ids and the sqlite3 Python API.
- **Next:** rerun the check whenever `schema/` changes.

## 2026-11-05 — Stachel compilation imported (D-013)
- D-013 accepted by J. Dasroy: compilations are imported as their own source layer. Proposed D-016 (open
  vocabulary: match a paper's columns to existing fields, add unmatched ones as *proposed*, never drop data).
- Stachel major-element compilation (CC0) converted to `compilations/stachel-major/rows.jsonl` (all 10,472 rows,
  values as stored; MD5 of the .xlsm matches) and loaded by new `scripts/load_compilation.py`: 8,634 inclusion
  reports, 95,096 values, 139 cited references, 98% of mineral names mapped (vocab extended with the dictionary's
  phases; 176 rows with rare or uncertain names kept as printed and flagged). Every row: evidence = compilation row +
  the compiler's citation and DOI; status `imported_unverified`; confidence medium (new rule 7, `conf-v4`).
- Schema migration `003_compilation_import.sql`: `evidence.cited_doi` + indexes.
- Not merged with extracted papers. The website flags compilation rows that repeat a paper extracted here (same
  cited DOI, sample number and phase; Kankan II declared as cited under Kankan I's DOI): Phillips 191, Sobolev 52,
  Kankan 38. Shown by default (Phillips' "unpubl and" rows hold extra analyses), hideable with a checkbox.
- Website: 8,843 inclusion reports (stats now say *reports*), craton filled, source type and cited paper columns,
  the 139 cited papers listed under the compilation, Cl and F columns. Data files trimmed (inclusions.json 7.7 MB,
  ~0.5 MB compressed).
- Found in the source: 13 rows with no reference; 222 cells holding only spaces; FeO not stated as total iron.
- **Next:** host-diamond fields and P-T columns of the same sheet; then trace elements, Walter, Smit.

## 2026-11-05 — Literature triage, batch 1
- Added `next` and `decide` commands to `scripts/literature.py`; triage rules written into the
  [literature workflow](literature-workflow.md).
- Claude triaged the 50 most-linked high-priority candidates: 27 relevant, 17 maybe, 6 not
  relevant (all notes start `Claude:`, not yet checked by a person). Many are reviews (RiMG 2022
  chapters, Stachel & Harris 2008, Kaminsky 2011), marked relevant so chaining reaches their references.
- Found the likely source of the Smit compilation's "Gress et al. 2021" Sm-Nd rows: Gress et al.
  2021, CMP, Orapa cluster (W3175333777); to confirm against the compilation.
- 5 of the 17 "maybe" depend on scope decision D-005 (fibrous diamonds, xenolith diamonds, ophiolite diamonds).
- **Next:** a person spot-checks batch 1; `chain` the 27 new relevant papers; next batch of 50.

## 2026-11-05 — Literature discovery workflow
- Compared Consensus and Connected Papers with OpenAlex for finding papers (details and
  evidence in [literature workflow](literature-workflow.md)). Both are built on Semantic Scholar
  / OpenAlex data. Connected Papers has no API (5 free graphs/month, by hand); Consensus has an
  official MCP connector but needs an account (not tested).
- Tests: OpenAlex chaining from the 11 seeds reached 72 of 113 compilation papers; a
  "diamond AND inclusion" filter would lose 34 known papers (missing abstracts), so the filter
  is "diamond" only. A Connected Papers graph of Phillips 2004 added 4 of 39 over the seeds, but
  none once chaining ran from all known papers.
- New `scripts/literature.py` (seed / chain / add / status) and `bibliography/inventory.csv`:
  138 known-relevant papers (seeds + Stachel-compilation DOIs) and 1,490 candidates from the
  first chaining run. 16 compilation DOIs are not in OpenAlex (several mistyped); kept as printed.
- OpenAlex now meters its API: no key = a small shared daily budget; a free personal key gives
  $1/day. The script stops and resumes when the budget runs out; a key is optional.
- New decision D-015 (proposed). Tests: `tests/test_literature.py` (offline).
- **Next:** triage the 1,058 high-priority candidates (~50 per session, Claude proposes, human
  checks); optionally get a free OpenAlex key; Walter/Smit references (no DOIs) to match by title.

## 2026-11-05 — Licence and access audit
- `scripts/licence_audit.py` looks up each source in OpenAlex (open access), Crossref (publisher and
  text-mining licences) and DataCite/Borealis (datasets); writes [licence register](licence-register.md)
  and `docs/licence-register.csv`. No personal details sent.
- Result for 15 seed sources: 7 open licence (Nimis 2025, Gress 2021, De Hoog 2019 CC BY; the four
  Borealis compilations CC0), 2 open non-commercial (Genzel 2023; Anzolini 2016's author manuscript,
  CC BY-NC-ND), 6 subscription with a publisher text-mining licence (Phillips, Sobolev, Meyer & Boyd
  via Elsevier; Kankan I–III via Springer). None unknown.
- Policy recorded: show values + citation + page/table only; never PDFs, figures or text; private
  quotes ≤ 200 characters. Schema excerpt limit lowered 500 → 200 (all stored quotes ≤ 111).
- Website: each source shows its licence; note that the site shows values and citations only.

## 2026-11-03 — Requested columns added to the website
- Renamed: Sample → Diamond ID (+ Inclusion ID where a label is printed, e.g. KK-16a), Mineral →
  Mineral name, Shape → Diamond morphology, Colour → Color, Type → Diamond type.
- New, filled only where a paper states it (with page and quote): country, region (Kimberley,
  Yakutia, Arkhangelsk), host rock (kimberlite), formation depth domain + basis (Kankan "l.m." →
  lower mantle; Kankan III majoritic → asthenosphere or transition zone, p. 468), identification
  method (EPMA where the phase is named from its analysis), notes.
- Inclusions inherit diamond-level values from another paper's record of the same diamond only
  through an approved identity link, labelled with that paper (e.g. KK-16a type `II [Stachel et al. (2002)]`).
- Empty, marked *: craton, weight_carat, transparency, resorption/surface features, fracture
  features, growth structure, relative timing, timing basis (not reported in any extracted paper).
- New `apply_setting` step in `scripts/build_gold.py`; properties region, host_rock,
  formation_depth_domain in `vocab/property.csv`.

## 2026-11-03 — Kankan II–III diamond links approved
- User compared both papers' inclusion lists for the 15 shared KK numbers and approved all 15
  links; recorded in `gold/identity-links.json` (read by `link_shared_samples`). Records stay
  separate; the `diamond_cluster` view now counts 201 physical diamonds from 216 records.
- Differences kept as each paper's own statement, noted on the links: KK-45 (names: MgSiO3 +
  microcline vs opx + K-fsp/hollandite?), KK-66 (1 vs 2 CaSiO3), KK-84 (l.m.(?) vs Unknown).
- Website: header counts physical diamonds; "Also reported in" no longer says pending.

## 2026-11-03 — Kankan III extracted; Diamonds tab
- Kankan III Table 1 (91 diamonds: shape, colour, deformation, δ13C, type, N, %B, paragenesis,
  inclusion list) transcribed from 220-dpi page images. Checks: matches every statistic the text
  gives (majoritic δ13C −3.13 to +0.89, mean −1.29; 36 lower-mantle diamonds, all Type II; N ranges),
  and **268 of 270 values match the Stachel compilation** (`scripts/compare_kankan3.py`); the two
  differences are the compiler's documented %B = 2 substitution. KK-47 (IaA with %B = 100) is a
  source inconsistency.
- New `load_diamonds`; Type II N `0` stored as below detection. 15 pending-review identity links to
  Kankan II diamonds with the same KK number. Confidence rules `conf-v3` (independent-copy check):
  90 diamonds high, KK-41 medium (not in the compilation).
- Website: new Diamonds tab (one row per diamond per paper, decoded shape/colour codes, δ13C/N/%B,
  inclusion list, Also reported in).

## 2026-11-03 — Calibration test 2; confidence rules v2
- Gress 2021 Table 5 (unseen; negative values, dashes, blanks) transcribed from images:
  **0 errors in 97 values**; planted sign/misread/swap errors caught. Combined with test 1:
  0 errors in 513 values (rate likely < 0.6 %).
- Rules `conf-v2`: image-read analyses whose printed total checks out are now *high*; image-read
  records without a total stay *medium*. Kankan II's 37 analyses move from medium to high.
- Still untested: scanned pages. Kankan III (no totals) will be *medium* under these rules.

## 2026-11-03 — Image-reading calibration, test 1
- Phillips Table 3 was unusable for a blind test (values already seen), so used Gress 2021 Table 3
  (unseen, born-digital): transcribed from 220-dpi images only, saved, then compared with the text
  layer by `extraction/calibrate_gress_2021.py`. **0 errors in 576 cells** (416 values); a planted-
  error copy was caught 3/3. Error rate likely < 0.7 % for clean tables. Rules kept at `conf-v1`;
  a harder second test (rotated, negative numbers) is needed before raising image-read confidence.

## 2026-11-03 — Extraction confidence for every record
- New table `extraction_confidence` (`schema/002_extraction_confidence.sql`) and rules `conf-v1` in
  [confidence](confidence.md): start from how values were read (text layer high, page images medium),
  drop to low if a printed total fails unexplained, one level down if there is no total to check,
  curator review lifts a passing medium to high. Ambiguities in the source stay separate flags.
- Applied backwards: Phillips 231 records high, Sobolev 63 high, Kankan II 37 medium.
- Website: Confidence column (hover for reasons), quick filter, "Why this confidence" column.
- **Next:** calibrate rule 1 by transcribing Phillips Table 3 from images and measuring the error rate.

## 2026-11-03 — Kankan II extracted (not yet reviewed)
- Kankan II Tables 2–4 (37 analyses, 485 values; ferropericlase, CaSiO3, MgSiO3, siderite, microcline,
  Mg-hornblende, and the KK-83a symplectite with its bulk analysis) transcribed by Claude from page
  images: the PDF's text layer is unreadable. Diamonds grouped by number (KK-16a/c/d = diamond KK-16).
- 35 of 37 printed totals match the oxide sums within 0.06 wt%. KK-66a and KK-87a totals leave out SrO
  (source inconsistency, recorded, values unchanged). `≤x` is undefined in the tables: stored as an
  upper limit and flagged. Eight uncertain names (`Olivine?`, `"Garnet"`, `Fper-(ol)`…) kept unmapped.
- Loader fix: FeO is total iron only where the source says so (Phillips); Sobolev and Kankan FeO stay
  `FeO` as printed. Website shows both columns.
- Not done: Kankan III Table 1 (host-diamond data for ~140 diamonds) needs a Diamonds tab and ~1,400
  cells transcribed from images.

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
