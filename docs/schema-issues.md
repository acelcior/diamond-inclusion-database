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

## From Sobolev et al. (2004) and Kankan II (Stachel et al. 2000b)

| # | Issue | What we did for now | Likely fix |
|---|---|---|---|
| S-9 | One physical inclusion analysed as several phases plus a **bulk** analysis (KK-83a symplectite: cpx, olivine, "garnet", bulk mix). Each became its own inclusion observation with the same label. | Same `reported_label`; bulk mapped to `polyphase inclusion (bulk)`. | A parent–child link: phase analyses belong to one polyphase inclusion. |
| S-10 | Uncertain phase names (`Olivine?`, `"Garnet"`, `Fper-(ol)`, `MgSiO3-(ol)`) have no honest standard phase. | Left unmapped (`phase_match_status = unmapped`), name kept as printed. | Use `phase_match_status = ambiguous` with candidate phases. |
| S-11 | The same label in different tables (Sobolev AL-1: chromite in Table 4, eclogitic garnet in Table 5) may or may not be one diamond. | Kept as separate diamonds unless the text links them (Yum-27). | Record a `pending_review` identity link when labels repeat, so a curator decides. |
| S-12 | A printed Total can leave out an oxide the row reports (Kankan II KK-66a, KK-87a omit SrO). | Recorded in `source.json` `total_notes`; values unchanged. | Optional note on the `oxide_total` value saying which oxides it sums. |
| S-13 | Whether `FeO` means total iron is often unstated. | `FeO` kept as its own quantity; `FeOT` only where the source says total iron. | Keep; add a conversion rule only when a source states Fe³⁺ handling. |

## From Kankan III (Stachel et al. 2002)

| # | Issue | What we did for now | Likely fix |
|---|---|---|---|
| S-14 | A printed `0` can mean "below detection" (Type II nitrogen) or a real zero (%B = 0 for IaA). Only the paper's definitions say which. | Type II: N `0` → `below_detection`, %B `0` → `not_applicable`, with the p. 468 evidence. | Keep; record the rule per paper in `source.json`. |
| S-15 | Inclusion lists per diamond (`2 Fe-per, MgSiO3, siderite`; `cpx-opx` = touching pair) are stored as text only, not as inclusion records. | `reported_assemblage` assertion; shown on the Diamonds tab. | Parse into named-only inclusion observations with counts, once a rule for `altered`, `Ca-silicates` and `?` is agreed. |
| S-16 | Analytical methods for δ¹³C and nitrogen are not in Table 1, and the text layer can't be read. | `method_code` NULL with a note. | Read the methods section from the page images. |
