---
tags: [brief]
status: living document
---

# Project brief — Global Diamond Inclusion Database

> The authoritative statement of requirements. Revised from the original project prompt,
> with additions for diamond-specific problems, separate status fields, inputs, tiers and
> success criteria. Change it deliberately; record major changes in [log](log.md).

Related: [roadmap](roadmap.md) · [decisions](decisions/README.md) · [inputs needed](inputs-needed.md)

---

## 1. Objective

Build a structured, traceable database of mineral inclusions in diamonds reported in the
scientific literature worldwide. The unit of interest is the **inclusion and its
observations**, not the paper. Not wanted: paper summaries, abstracts, conclusions.

Capture, as the literature provides:
- Mineral/phase identity and assemblages (as observed **and** as interpreted).
- Host diamond characteristics.
- Geographic locality and geological setting.
- Major- and trace-element chemistry.
- Isotopic measurements and ages.
- Raman, FTIR, PL, CL and other spectroscopic data.
- Analytical techniques and conditions.
- Physical characteristics: morphology, size, texture, position in host.
- Pressure, temperature, depth, age and other derived geological parameters.
- Relationships between inclusions, host diamonds, minerals, localities and samples.
- Original values, units, uncertainty and supporting evidence for each record.

No predetermined short list of mineral species or techniques.

### Capture tiers (to keep the first pass finishable)

| Tier | Content | When |
|---|---|---|
| **1 — Core** | Phase (observed + reported name), host diamond link, locality, paragenesis (attributed), major-element oxides, provenance | Phases 1–4 |
| **2 — Extended** | Trace elements, isotopes, ages, P-T estimates, inclusion context (touching, in situ, position), host N/δ¹³C | After Tier 1 is stable |
| **3 — Full** | Spectra (peak lists, raw files), imaging, analytical conditions in full detail, everything else | Later |

The schema must *accommodate* all tiers from the start; extraction *prioritizes* by tier.

## 2. Fundamental scientific requirements

- One diamond can host multiple inclusions of different phases.
- One phase occurs in inclusions from many diamonds and localities.
- One inclusion can have many measurements and appear in many publications.
- Papers report individual inclusions, groups, aggregates, ranges or bulk analyses.
- **Some measurements belong to a set of inclusions** (isochron ages, pooled/bulk analyses,
  composite inclusion sets) — model this explicitly, not as one inclusion.
- Host diamond, locality or analytical data may be unknown or incomplete.
- Locality names may be historical, ambiguous, or at different geographic scales.
- Publications may disagree about identification, composition, origin or interpretation.
- The same specimen/inclusion may appear in several papers, sometimes under different IDs.

Never force uncertain information into a definitive record. Distinguish the physical
inclusion from a published observation from an analytical measurement. Do not merge
reports into one physical inclusion without sufficient evidence.

### Diamond-specific issues the model must handle

- **Observed vs inferred original phase.** E.g. CaSiO₃-walstromite interpreted as
  retrogressed CaSiO₃-perovskite; polyphase inclusions interpreted as an unmixed single
  phase; "former bridgmanite". Store both, with the interpretation attributed.
- **Non-IMA phase names.** "Majoritic garnet", "ferropericlase", "TAPP", undifferentiated
  "sulfide", "Cr-pyrope", "omphacite" in loose usage. The vocabulary must allow phases,
  varieties, solid solutions and unknown phases, not just IMA species.
- **Derived classifications are interpretations.** Paragenesis (peridotitic / eclogitic /
  websteritic / sublithospheric), lherzolitic vs harzburgitic, garnet G-classes — store
  with source and method/scheme.
- **Inclusion context.** Touching vs non-touching (visible cracks to surface), analysed
  in situ vs released by breaking, position (core/rim, CL growth zone), syngenetic /
  protogenetic / epigenetic status (as asserted, with source).
- **Host diamond.** Nitrogen content and aggregation (Type; %B / IaAB), δ¹³C, δ¹⁵N,
  CL zoning, morphology, colour, size/weight, sample ID(s), collection/museum ID.
- **Fibrous/coated diamonds and high-density fluids (HDF).** Scope decision — see
  [decisions](decisions/README.md).
- **Recomputable P-T.** Store the thermobarometer/calibration and the input analyses,
  not only the result. Elastic (Raman) barometry: keep measured residual pressure separate
  from derived entrapment pressure, with the EoS/model used.
- **Ages.** Model age vs isochron age; which inclusions were pooled; decay constants /
  reference values where reported.
- **Ambiguous table notation.** `n.d.` (not detected *or* not determined), `—`, `bdl`,
  `<x`, blank cells, FeO vs FeOtotal vs recalculated Fe³⁺. Flag, never guess.

## 3. Normalized relational database

PostgreSQL + PostGIS long term; a portable prototype (SQLite or DuckDB) first. Linked
tables for at least:

1. Publications and supplementary files
2. Host diamonds and specimens (incl. specimen identifiers across papers)
3. Physical inclusions
4. Reported inclusion observations
5. Phases / mineral species and taxonomy
6. Assemblages and phase relationships
7. Localities (with gazetteer)
8. Analytical methods and measurement sessions
9. Chemical compositions and trace elements
10. Spectroscopic observations and spectral data
11. Isotopic measurements and ages
12. Geological context, P-T and other derived parameters
13. Evidence/citations for individual values or claims
14. Extraction runs, validation, review and revision history

Additional tables when justified (e.g. inclusion sets, interpretations/assertions,
sample identifier crosswalk). Define PKs, FKs, M:N links, types, controlled vocabularies
and validation rules. No giant sparse spreadsheet; support variable analytical data
while allowing simple flat views to be generated.

**Open question (not mandated):** whether provenance lives at the level of each field or
at the level of each assertion/measurement row. See [decisions](decisions/README.md).

## 4. Provenance

Every observation and measurement traceable to source. Capture where available:
- DOI and full bibliographic data.
- Page, table, figure, caption, supplementary file (and sheet/cell for spreadsheets).
- Original terminology and value as printed.
- Short supporting excerpt or evidence reference.
- Original units, normalized units, uncertainty (type and level: 1σ/2σ/SE/SD), detection limits.
- Analytical method and conditions.
- Status fields (see §7), reviewer, confidence.
- Derivation: directly reported / calculated (by us or by authors) / inferred / interpreted.

Author interpretations are separate attributed fields. Never invent data, citations,
coordinates, specimen identities or identifications.

## 5. Localities

Capture: original name, standardized name, aliases, mine, pipe, deposit, field, region,
country, coordinates, CRS, geographic precision class, and the **source of every match and
coordinate** (gazetteer reference, not the paper, unless the paper gives them).

- Distinguish exact / approximate / region-level / ambiguous / unknown.
- Unknown localities never prevent storage or search.
- No country/region centroid represented as an exact locality.
- Distinguish **reported collection locality** (mine/pipe/alluvial source) from
  **inferred geological origin** (craton, mantle domain, depth regime).
- Alluvial/secondary deposits and "provenance unknown, purchased in X" are first-class cases.
- Use external identifiers where possible (Mindat locality IDs, GeoNames).

## 6. Literature discovery and extraction pipeline

Workflows to:
1. Discover publications broadly and iteratively (Crossref, OpenAlex, citation chaining,
   existing review compilations, synonym/historical-term searches).
2. Maintain a master bibliography.
3. Deduplicate publications and versions (preprint/published, conference abstract/paper).
4. Obtain legally accessible full texts and supplements.
5. Parse PDFs, tables, captions, supplementary spreadsheets.
6. OCR scanned documents.
7. Extract structured inclusion-level data with Claude, against a JSON Schema.
8. Validate extracted records in code.
9. Flag ambiguous records for human review.
10. Import approved records.
11. Track per-publication processing status (which tables/sections/supplements done).

Don't rely on abstracts or keywords alone. Look for less obvious observations, historical
terminology, synonyms, and data buried in supplements. Respect copyright, publisher access
restrictions and API/TDM terms.

## 7. Standardization and data quality

- Mineral vocabulary: standardized names, synonyms, historical terms, identifiers
  (IMA/RRUFF, Mindat), and non-IMA phase names (see §2).
- Original terminology preserved alongside standardized terms.
- Original values/units preserved; normalized values separate; explicit versioned
  conversion rules.

**Three separate status dimensions** (not one enum):

| Dimension | Values |
|---|---|
| Value status | reported · not reported · not measured · not applicable · unknown · ambiguous · below detection |
| Derivation | directly reported · calculated by authors · calculated by us · inferred · interpreted |
| Workflow | not attempted · extracted · extraction failed · pending review · approved · rejected · superseded |

Validation rules for: units, oxide totals and stoichiometry, mineral names, coordinate
ranges, missing required fields, duplicated observations, inconsistent source references.

Never silently resolve scientific disagreements; keep competing reports and a transparent
reconciliation process.

## 8. User interface (later — informs schema now, not designed yet)

A. Inclusion explorer: search, filters, sort, selectable columns, saved views, CSV export.
B. Interactive map with filters (phase, locality, method, date, …).
C. Record view: everything about an inclusion, host, measurements, evidence, related inclusions.
D. Analysis workspace: compare chemistry, spectra, isotopes, assemblages, geography.
E. Research-landscape dashboard: trends, coverage, methods, gaps, missing data.

Users choose their own columns. Unknown/approximate localities visible in non-map views.

## 9. Research landscape analyses (later)

Questions the database should answer: most-reported phases and assemblages; represented
regions/deposits/settings; co-occurrence within the same diamond; compositional variation
by locality; techniques per mineral; change over time; poorly characterized minerals or
localities; rarely reported data categories; geographic and analytical gaps; which patterns
are robust vs sampling artefacts.

Keep **publication, observation, distinct physical inclusion, host-diamond and measurement
counts separate**. Published counts are not geological abundance.

## 10. Technical approach

Consider: Claude Code (development, extraction orchestration), Claude API with structured
output, Python, JSON Schema validation, SQLite/DuckDB prototype → PostgreSQL + PostGIS,
web UI with customizable tables/maps/plots, automated tests, git, backups, reproducible
imports. Explain build order, what can be automated, what needs human review, and costs.

## 11. Success criteria

- **Gold standard:** 3–5 seed papers hand-curated into the schema before any automated
  extraction.
- **Extraction quality:** per-field precision and recall against the gold standard;
  target thresholds set in an ADR after the first measurement.
- **Schema fitness:** every seed paper representable without loss or forced certainty;
  every workaround recorded as a schema issue.
- **Traceability:** 100% of stored values have source location + original value.
- **Recall check:** compare coverage against existing published compilations.

## 12. How we work

- Incremental; functioning system over elaborate theory.
- Validate the design against real papers before building the application.
- When processing a publication, return structured records, not summaries.
- When uncertain, preserve evidence and flag rather than guess.
- Illustrative examples clearly labelled; never presented as real observations.
- Deliverables are files in this repo, version-controlled.
