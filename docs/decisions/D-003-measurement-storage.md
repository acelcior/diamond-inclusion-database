---
id: D-003
status: accepted
date: 2026-10-22
accepted: 2026-10-22
tags: [decision]
---

# D-003 — Measurement storage: one column per element, or one row per value?

> **In plain terms:** a spreadsheet with a column for every possible element (SiO₂, TiO₂, … 60
> trace elements) is mostly empty and needs a new column whenever a paper reports something new.
> **Proposal:** store each value as its own row ("SiO₂ = 41.2 wt% in analysis 17"), and generate
> familiar wide tables automatically for people who want them.

## Context
- [Brief §3](../brief.md): no giant sparse spreadsheet; support variable analytical data; still
  let users build simple tables.
- [Compilations mapping](../compilations-mapping.md): Stachel major has 22 oxide/halogen columns,
  traces add ~50 elements; most are blank on any row. Values need per-value status (`b.d.`,
  `<0.02`, blank-vs-empty), detection limits, original text.
- Some data types don't fit "analyte = number": spectra (peak lists, files), P-T estimates (need
  calibration + inputs), isotope ratios with their own uncertainty conventions.

## Options
1. **Wide tables per data type** (one column per oxide, per element). Familiar and fast to query,
   but sparse, schema change for every new analyte, and no room for per-value status/limits.
2. **Fully generic key-value (EAV) for everything**, including P-T and spectra. Flexible but
   hard to validate and to query; meaning hides in strings.
3. **Long format for chemistry and isotopes; typed tables for the rest; generated wide views.**

## Proposal
**Option 3.**

| Data | Storage |
|---|---|
| Major/trace elements, halogens, isotope values, N content | `measured_value`: measurement_id, analyte (from vocabulary: SiO2, La, δ13C, ¹⁸⁷Os/¹⁸⁸Os…), original text, original unit, numeric value, uncertainty (+ type: 1σ, 2σ, SE), detection limit, value status, derivation, normalized value + unit + conversion rule id |
| Spectroscopy (FTIR, Raman, PL, CL) | `spectral_observation` (method, conditions) + `spectral_feature` (peak position, area, assignment) + optional link to a raw file; FTIR-derived N and %B as `measured_value`s |
| P-T, depth, residence temperature, ages | `derived_parameter`: parameter, value, uncertainty, method/calibration, input measurements (links), assumed values (e.g. "P fixed at 50 kbar"), who calculated it |
| Isochron ages and other set-level results | `derived_parameter` attached to an `inclusion_set` (see D-006) |

- `measurement` holds method, instrument, conditions, analytical session; values hang off it.
- Wide "simple tables" (e.g. one row per inclusion, one column per oxide) are SQL views, so
  collaborators can still export a familiar spreadsheet.

## Consequences
- New analytes need a vocabulary entry, not a schema change.
- Validation can check per analyte (units allowed, plausible ranges, oxide totals per measurement).
- Queries need a pivot for wide output: hidden behind views and Datasette (D-004).

## Evidence / test cases
Phase 2: Phillips oxide table (wide → long); Kankan III FTIR (spectral + N values); Phillips
thermobarometry (derived with inputs); Gress Re-Os isochron (set-level).
