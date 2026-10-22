---
tags: [log]
---

# Progress log

Newest first. One short entry per working session: what was done, what was decided,
what's next. Related: [roadmap](roadmap.md)

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
