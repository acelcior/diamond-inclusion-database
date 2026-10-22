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
| D-001 | **Inclusion identity model**: how a physical inclusion relates to its reports across papers | Phase 1 | open | One record per reported inclusion; "same physical inclusion" expressed as evidence-backed identity links with confidence, never by merging rows |
| D-002 | **Provenance granularity**: evidence per field vs per assertion/measurement row | Phase 1 | open | Per row (each measurement/assertion links to evidence); per field only where a row mixes sources |
| D-003 | **Measurement storage**: long format (one row per analyte value) vs wide tables per data type | Phase 1 | open | Long format for chemistry/isotopes, typed tables for spectra and P-T; generated flat views for users |
| D-004 | **Prototype database**: SQLite vs DuckDB vs PostgreSQL from day one | Phase 1 | open | Consider PostgreSQL from the start (Postgres.app on macOS is simple) to avoid a dialect migration; SQLite if zero setup matters more |
| D-005 | **Scope**: fibrous/coated diamonds and HDFs; synthetic diamonds (HPHT/CVD); inclusions in diamonds still in xenoliths; conference abstracts and theses | Phase 1 | open | — needs your call |
| D-006 | **Group-level data**: storing means, ranges, n, and measurements on inclusion sets (isochrons, pooled analyses) | Phase 2 | open | `inclusion_set` entity + statistic type (single / mean / median / min / max / range) + n |
| D-007 | **Status fields**: three separate dimensions (value status, derivation, workflow) | Phase 1 | proposed | As in [brief §7](../brief.md) |
| D-008 | **Phase vocabulary basis**: IMA/RRUFF + Mindat IDs + local table for non-IMA phases, varieties, unknowns | Phase 1 | open | Local `phase` table with optional external IDs and a synonym table |
| D-009 | **Locality gazetteer**: sources (Mindat, GeoNames, literature), hierarchy, precision classes | Phase 6 | open | — |
| D-010 | **Interpretations**: separate attributed table for paragenesis, original phase, origin, P-T regime | Phase 1 | open | Separate `interpretation` table linked to subject + source + method/scheme |
| D-011 | **Database licence and excerpt policy**: public vs private; max excerpt length; redistribution of supplement data | Phase 5 | open | — needs your call |
| D-012 | **Extraction quality thresholds**: per-field precision/recall needed before scaling | Phase 3 | open | Set after first measurement on gold set |
