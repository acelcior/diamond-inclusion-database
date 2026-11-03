---
tags: [schema, phase-2]
---

# Schema issues from the gold-standard papers

Phase 2 rule: every place a real paper didn't fit the schema cleanly gets recorded here. Fix them
together when revising to schema v1 (one migration), not one by one.

Related: [roadmap](roadmap.md) · [decisions](decisions/README.md) · [Phillips 2004 review](../gold/phillips-2004/README.md)

## From Phillips et al. (2004)

| # | Issue | What we did for now | Likely fix |
|---|---|---|---|
| S-1 | `derived_parameter` has no `value_status`, so a cell that should hold a result but is blank (DP497 Brey & Köhler pressure) can't be stored as "not reported". | Not stored; flagged on the review page. | Add `value_status` to `derived_parameter`, as on `measured_value`. |
| S-2 | Thermometers run at an **assumed** pressure (5.0 GPa, Table 4 note e). Only free text holds the input. | Kept in `assumptions` text with the printed value. | Structured input parameters (name, value, unit) for derived values, so P-T can be recomputed (brief §2). |
| S-3 | Each EPMA analysis is the **average of ≥3 spots** on one inclusion. There is no field for "statistic = mean, n ≥ 3". | Written in `spot_label`. | Part of D-006 (group-level data): add statistic type and n to `measurement`. |
| S-4 | A **method-level detection limit** ("typically 0.02 wt%" for Na₂O, K₂O) has no home. `detection_limit` is per value and would claim more precision than the paper gives. | Kept in `measurement.conditions`; values below it are listed on the review page. | Optional detection limit per method/session, with a "typical" qualifier. |
| S-5 | Phases **listed in an assemblage but never analysed** (DP364 chromite, all 28 inclusions of the 14 Table-4-only diamonds) become inclusion observations with no measurement. This works, but counts of "inclusions" must say whether they include these. | Created; the review page counts them separately. | Keep. Define the counting rule in the data dictionary. |
| S-6 | `Suite` combines paragenesis and subtype (`Per (hz)`) in one code. Table 4 spells out `Harzburgitic`. | Stored as printed, as `interpreted` assertions. | A paragenesis vocabulary with mappings from printed codes (`Per (hz)`, `h`, `Harzburgitic`) to one term. |
| S-7 | `locality.precision_class` is required, but it describes coordinates, and this locality has none. | Set to `region` with a note. | Allow `precision_class` to be NULL when there are no coordinates, or rename it to describe the place. |
| S-8 | The compilation's values are **rescaled to 100 % with V₂O₅ converted to V₂O₃**. They are not the printed values. | Found by [the compilation cross-check](../gold/phillips-2004/compilation-check.md). | When compilations are imported (D-013), mark their values `calculated_by_compiler` and record the transformation. |
