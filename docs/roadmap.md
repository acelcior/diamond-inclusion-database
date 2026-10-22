---
tags: [roadmap]
---

# Roadmap

Phases are sequential unless marked *parallel*. Each phase ends at an **exit gate**:
don't start the next one until the gate is met (or an ADR records why it was skipped).

Related: [brief](brief.md) · [decisions](decisions/README.md) · [inputs needed](inputs-needed.md) · [log](log.md)

## Constraints that shape this plan
From [inputs needed](inputs-needed.md): about 2–3 hours a week; very little Python, so Claude runs
the commands and explains them; a Claude Pro plan with no API budget; shared with collaborators;
on contract for a professor, who sets the research priorities.

What follows from that:
- **Build on the open CC0 compilations** (D-013) instead of re-extracting thousands of papers.
- **Extraction happens in Claude Code sessions** (D-014): a few papers a week, chosen by gap.
- **Zero-setup prototype** (D-004 lean: SQLite + Datasette) before any server or custom UI.
- Phases 5–8 are long-horizon; their timing depends on the professor's priorities.

---

## Phase 0 — Setup and inputs
- [x] Project folder as git repo + Obsidian vault + `CLAUDE.md`
- [x] Revised [brief](brief.md)
- [x] Fill in [inputs needed](inputs-needed.md): constraints, access, budget, licence intent
- [x] First commit
- [x] Seed papers proposed and citations verified (Batch A, Batch B, Dataset 0 in [inputs needed](inputs-needed.md))
- [ ] Download the Batch A PDFs and the Dataset 0 compilations into `papers/`
- [ ] Ask the professor the questions in [inputs needed](inputs-needed.md), especially D-013

**Exit gate:** Batch A available locally; professor's view on D-013 known (or a provisional choice recorded).

## Phase 1 — Core schema v0 (Tier 1)
- [ ] Entity-relationship overview (inclusion ↔ host ↔ observation ↔ measurement ↔ publication ↔ locality)
- [x] Decide the blocking ADRs: D-001 – D-004 accepted; D-005 proposed, awaiting the professor ([decisions](decisions/README.md))
- [ ] `schema/001_core.sql` — portable DDL (SQLite/DuckDB now, Postgres-compatible)
- [ ] Seed vocabularies in `vocab/`: phases + synonyms, paragenesis, methods, units, status enums
- [ ] Tier 1 data dictionary (`docs/data-dictionary.md`)
- [x] Read the Dataset 0 data dictionaries; map their columns to our schema and note what they can't represent → [compilations mapping](compilations-mapping.md)
- [ ] Tests: schema loads; constraints reject obviously bad rows

**Exit gate:** schema loads; an illustrative (clearly labelled) record round-trips.

## Phase 2 — Gold standard from real papers
- [ ] Hand-curate seed paper 1 into the schema (Claude drafts, you verify every value)
- [ ] Record every awkward fit as a schema issue → revise schema
- [ ] Curate seed papers 2–5, covering different reporting styles
- [ ] Freeze gold set in `gold/` (versioned)

**Exit gate:** all seed papers representable without loss or forced certainty; schema v1 tagged.

## Phase 3 — Extraction spec and validator
- [ ] `extraction/schema.json` — JSON Schema for paper → records
- [ ] Extraction prompt (structured output, evidence excerpt per value)
- [ ] PDF/table/supplement parsing for seed papers (text layer first, OCR fallback)
- [ ] `validate.py` — units, oxide totals, stoichiometry, vocab, coordinates, duplicates, references
- [ ] Importer: validated JSON → DB, with extraction-run and review-status records
- [ ] Measure per-field precision/recall vs gold; set thresholds (ADR)

**Exit gate:** automated extraction on seed papers meets agreed thresholds for Tier 1 fields.

## Phase 4 — Bibliography and discovery *(parallel with Phase 2–3)*
- [ ] OpenAlex + Crossref harvesting scripts; search-term list incl. synonyms and historical terms
- [ ] Citation chaining from key reviews/compilations
- [ ] Master bibliography table + publication dedup (DOI, title/author/year fuzzy, preprint ↔ published)
- [ ] Access-status tracking (open / institutional / unavailable) — no circumvention

**Exit gate:** master bibliography of candidate papers with access status and relevance triage.

## Phase 5 — Scaled extraction and review
- [ ] Batch extraction with cost tracking per paper
- [ ] Review queue: flagged/ambiguous records, reviewer decisions, revision history
- [ ] Physical-inclusion and specimen reconciliation across papers (evidence-based links only)
- [ ] Per-publication processing tracker (which tables/supplements done)

**Exit gate:** first N papers (you choose N) approved and imported; review throughput known.

## Phase 6 — PostgreSQL + PostGIS and localities
- [ ] Migrate schema; reproducible import from source files
- [ ] Locality gazetteer: standardized names, aliases, hierarchy, coordinates + precision + source
- [ ] Backups

## Phase 7 — Explorer and map
- [ ] Inclusion explorer: filters, selectable columns, saved views, CSV export
- [ ] Map with honest precision display; list view of unknown/approximate localities
- [ ] Record detail view with evidence

## Phase 8 — Analysis and research landscape
- [ ] Co-occurrence, compositional comparisons by locality/paragenesis, technique coverage
- [ ] Landscape dashboard with separated counts (publications / observations / inclusions / diamonds / measurements)
- [ ] Gap and bias analyses

---

## How to run a working session with Claude

1. Open Claude Code in this folder (`CLAUDE.md` loads automatically).
2. Say which roadmap item you're on, e.g. *"Phase 1: draft schema/001_core.sql"*.
3. One roadmap item per session where possible; long sessions drift.
4. Claude ends the session by updating [log](log.md) and ticking the roadmap; you commit.
5. Decisions that come up go into `docs/decisions/` as ADRs.
