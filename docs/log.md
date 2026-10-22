---
tags: [log]
---

# Progress log

Newest first. One short entry per working session: what was done, what was decided,
what's next. Related: [roadmap](roadmap.md)

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
