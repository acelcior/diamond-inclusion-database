---
tags: [decisions]
---

# Design decisions

Each significant decision becomes an ADR file: `D-NNN-short-name.md`, from the
[template](_template.md). Status: **open** → **proposed** → **accepted** (or **rejected** /
**superseded by D-NNN**). Accepted ADRs are binding until superseded.

Related: [brief](../brief.md) · [roadmap](../roadmap.md)

## Decision register

| ID | Decision | Blocks | Status | Initial lean (not decided) |
|---|---|---|---|---|
| [D-001](D-001-inclusion-identity.md) | **Inclusion identity model**: how a physical inclusion relates to its reports across papers | Phase 1 | **accepted** | One record per reported inclusion; "same physical inclusion" expressed as evidence-backed identity links with confidence, never by merging rows |
| [D-002](D-002-provenance-granularity.md) | **Provenance granularity**: evidence per field vs per assertion/measurement row | Phase 1 | **accepted** | Per row (each measurement/assertion links to evidence); per field only where a row mixes sources |
| [D-003](D-003-measurement-storage.md) | **Measurement storage**: long format (one row per analyte value) vs wide tables per data type | Phase 1 | **accepted** | Long format for chemistry/isotopes, typed tables for spectra and P-T; generated flat views for users |
| [D-004](D-004-prototype-database.md) | **Prototype database**: SQLite vs DuckDB vs PostgreSQL from day one | Phase 1 | **accepted** | SQLite: one file, no server, easy to share with collaborators; [Datasette](https://datasette.io) gives a browsable web view for free. Keep SQL portable for a later move to PostgreSQL + PostGIS |
| [D-005](D-005-scope.md) | **Scope**: fibrous/coated diamonds and HDFs; synthetic diamonds (HPHT/CVD); inclusions in diamonds still in xenoliths; conference abstracts and theses | Phase 1 | **proposed**, needs professor | — needs your call |
| D-006 | **Group-level data**: storing means, ranges, n, and measurements on inclusion sets (isochrons, pooled analyses) | Phase 2 | open | `inclusion_set` entity + statistic type (single / mean / median / min / max / range) + n |
| D-007 | **Status fields**: three separate dimensions (value status, derivation, workflow) | Phase 1 | proposed | As in [brief §7](../brief.md) |
| D-008 | **Phase vocabulary basis**: IMA/RRUFF + Mindat IDs + local table for non-IMA phases, varieties, unknowns | Phase 1 | open | Local `phase` table with optional external IDs and a synonym table |
| D-009 | **Locality gazetteer**: sources (Mindat, GeoNames, literature), hierarchy, precision classes | Phase 6 | open | — |
| D-010 | **Interpretations**: separate attributed table for paragenesis, original phase, origin, P-T regime | Phase 1 | open | Separate `interpretation` table linked to subject + source + method/scheme |
| D-011 | **Database licence and excerpt policy**: public vs private; max excerpt length; redistribution of supplement data | Phase 5 | open | — needs your call |
| D-012 | **Extraction quality thresholds**: per-field precision/recall needed before scaling | Phase 3 | open | Set after first measurement on gold set |
| D-013 | **Existing CC0 compilations** (Stachel; Walter et al.; Smit et al. on Borealis, see [inputs](../inputs-needed.md)): import as a source layer, or use only as a cross-check | Phase 1 | **accepted** (J. Dasroy, 2026-11-05); Stachel major elements imported | Import as a distinct *compilation* source (each row keeps its original reference and is marked not checked against the paper), never as if extracted from the paper; literature extraction then adds per-value provenance, localities, post-2021 and non-English papers, spectroscopy, and checks disputed values |
| D-014 | **Extraction mode under a Claude Pro plan** (no API budget) | Phase 3 | open | Extraction runs paper-by-paper in Claude Code sessions, writing JSON files that code then validates; no paid batch API pipeline unless funding appears. Throughput is a few papers per week, so prioritize papers by gap (see D-013) |
| D-015 | **Literature discovery**: which tools find papers and how the master list is kept ([workflow](../literature-workflow.md)) | Phase 4 | proposed | OpenAlex citation chaining by script as the backbone, seeded with the compilations' references; Connected Papers (5 free graphs/month) and Consensus (gap questions) used by hand, their papers imported with `found_by` recorded; triage by a human, Claude may propose |
| D-016 | **Open vocabulary for extraction**: how a paper's columns become database fields | Phase 3 | proposed | No fixed template. Each printed column header is matched to an existing quantity/property (exact name, known synonym, unit); an unmatched header becomes a new vocabulary entry marked *proposed*, so its values are stored at once and nothing is dropped. A person later approves it or merges it into an existing entry (e.g. FeO\* → FeOT only if the paper says total iron). Original header always kept |
