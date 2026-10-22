---
tags: [phase-1, compilations, schema]
date: 2026-10-22
---

# Dataset 0: what the compilations contain and how they map to our schema

Phase 1 roadmap item: *read the Dataset 0 data dictionaries; map their columns to our schema
and note what they can't represent.* The entities below are the **planned** ones from
[brief §3](brief.md); no tables exist yet. Findings here feed the blocking decisions in
[decisions](decisions/README.md).

Related: [inputs needed](inputs-needed.md) · [roadmap](roadmap.md)

## 1. What's in each compilation (measured, not estimated)

| Compilation | Sheets | Rows | References | Identifiers |
|---|---|---|---|---|
| **Stachel major elements** (`Diamond_Database_Oct-2021.xlsm`) | `All diamonds` + per-mineral sheets (Garnet 2944, Cpx 1378, Olivine 1499, Spinel 1046, Opx 533, Sulfide 676, Pericl-wust 270, Si-pvks 104) | 10,472 in `All diamonds` | 146 distinct short references; full list in the PDF dictionary | DOI on 8,361 rows; 13 rows have no reference |
| **Stachel trace elements** (`Diamond_Traces_Oct-2021.xlsm`) | `All` + per-mineral sheets | 949 in `All` | (shares the major-element reference list) | DOI column present |
| **Walter et al. sublithospheric** (`RiMG Chapter11_Walter_Tables.xlsm`) | 11 tables: major and trace elements for majorite, CaSiO₃, MgSiO₃, ferropericlase, olivine, cpx; partition coefficients | ~900 across tables | 115 distinct reference *strings* | **No DOIs**; header is on row 2 |
| **Smit et al. radiogenic isotopes** (`Chapter11_supplementary data.xlsm`) | Re-Os sulfides (311), Sm-Nd silicates (154), isochron initial ratios, U-Th-He, reference values | ~530 | 17 studies in Re-Os alone | **No DOIs** |

All four are CC0. The Stachel dictionaries are thorough; Walter and Smit have none, so their
columns are interpreted from headers only.

### Overlap with our seed papers

| Seed | In which compilation | Notes |
|---|---|---|
| A1 Phillips 2004 | Stachel major: 653 rows | Cited as **"unpubl and Phillips et al. (2004)"**: unpublished and published data are mixed under one reference. The gold-standard curation of A1 will show which rows are actually in the paper. |
| A3/A3a Kankan | Stachel major: 159 rows; Walter: several | Every row cites **Kankan I's DOI** (10.1007/s004100000173), even for phases described in Kankan II. Confirms Kankan I's supplement is the data source. |
| B2 Gress 2021 | Smit: 25 Re-Os rows, 127 Sm-Nd rows | The Sm-Nd rows may come from a different Gress 2021 paper: to check, since "Gress et al. 2021" carries no DOI. |
| B5 Sobolev 2004 | Stachel major: 63 rows | |
| B1 Meyer & Boyd 1972 | Stachel major: 3 rows (Sierra Leone) | Far fewer than the paper reports, so worth checking which inclusions were included. |
| A2, A5, B3, B4 | not found by reference search | Nimis 2025, Genzel 2023 postdate or fall outside the compilations; De Hoog 2019 and Anzolini 2016 may sit under other reference strings. |

## 2. What one row means

In Stachel `All diamonds`, **one row is one analysis of one inclusion phase, with its host
diamond's data repeated on the same row.** 10,472 rows collapse to about 9,519 distinct
(reference, locality, sample number) combinations, so roughly a tenth of rows share a host
diamond. A further **2,049 rows have no inclusion chemistry at all**: they are host-diamond
records (δ¹³C, nitrogen, FTIR) with the mineral blank.

So a single row splits into several of our entities:

```
one Stachel row ──► host_diamond      (locality, sample #, size, shape, colour, δ13C, N, FTIR)
                ├─► inclusion          (phase, position extensions like core/rim, (1)/(2))
                ├─► observation        (the report of that inclusion in a reference)
                ├─► measurement + values (oxides wt%, Cl, F, δ18O)
                ├─► derived_parameter  (T and P estimates, N-residence temperatures)
                └─► interpretation     (paragenesis, garnet class)
```

## 3. Column mapping: Stachel major elements, `All diamonds`

Planned entity · column(s) · derivation (see [brief §7](brief.md)) · notes.

| Planned entity / field | Stachel column(s) | Derivation | Notes |
|---|---|---|---|
| **locality** (reported name) | A `sample` | reported | Pipe, prospect or alluvial district "typically as given in the publication": 156 distinct values. No coordinates. |
| locality → geological unit | E `craton` | interpreted by compiler | 31 values; some are not cratons but headless alluvial deposits (NSW, Borneo). |
| — (drop) | B–D `kcode/jcode/lcode` | — | Igpet plotting codes; derivable from craton and paragenesis. |
| **publication** (inclusion data) | F `EPMA reference (or both)`, G `EPMA DOI` | — | "or both" means the same paper also supplied isotope/FTIR data. Short-ref strings need matching to full references. |
| **publication** (isotope/FTIR data) | H, I | — | A second source for the host-diamond fields on the same row. |
| **phase** (as reported) | J `mineral` | reported | **262 distinct spellings**, e.g. `garnet (maj)`, `garnet (majorite)`, `SiO2 (coesite)`, `chromite (average)`, `?`. Map to the phase vocabulary while keeping the original string. |
| **specimen identifier** | K `#_sample` | reported, *modified* | Compiler zero-padded some numbers (X-1 → X-001). Suffixes `-a`, `core`/`rim`, `(1)`/`(2)` identify the inclusion or spot, not the diamond. |
| **interpretation**: paragenesis | L `paragenesis` | interpreted | Compact codes (`e`, `p`, `h`, `l`, `l.m.`, `wb`, `deep-e`, `wb/l (transitional)`, `?`) that also encode alteration (`altered`, `epigenetic`) and depth (`deep`, `TZ`). Split these into separate fields. |
| **interpretation**: garnet class | M `garnet class` | calculated by compiler | Grütter et al. (2004) scheme. Recomputable from oxides. |
| **assemblage** | N `assemblage` | reported | List of all phases observed in that diamond, as text. Implies inclusions we have no row for. |
| **host_diamond**: size | O `size` | reported | Mixed notations: DTC sieve classes (`-11+9`, `-11 +9`), mm, μm, mg. Excel may have turned sieve classes into numbers (`-2`). Store original text; never parse into a number without a rule. |
| host_diamond: shape, colour, deformation | P, Q, R | reported | Coded abbreviations; vocabularies in the dictionary. |
| **isotope measurement** on host | S `δ13C`, T `δ15N` | reported | Mostly bulk on ~1 mg fragments; SIMS values are averages of spots. Reference frames: VPDB, air N₂. |
| **measurement**: N content | U `N[SIMS]` (at ppm) | reported | Same spot/fragment as the isotopes. |
| **spectroscopy (FTIR)** | V `Type`, W `N [at ppm]`, X `%B`, Y `IB'`, Z `B'pos`, AA `3107 cm⁻¹` | reported / calculated | **%B detection-limit substitutions are marked only by bold red font** (dictionary, column X). A values-only import loses this; read cell formatting or treat 2 and 99.5 %B as flagged. |
| **derived_parameter**: N-residence temperature | AB–AE `T[Nitrogen, 3/1/0.5/0.1 Ga]` | calculated by compiler | Assumes residence time; recomputable. |
| **derived_parameter**: thermobarometry | AF–AK (Krogh, O'Neill, Harley/BKN, NTcpx) | calculated by compiler | Some at a **preset 50 kbar**. Store calibration + inputs, not just the number ([brief §2](brief.md), recomputable P-T). |
| **isotope measurement** on inclusion | AL `δ18O`, AM, AN | reported | Has its own reference and DOI. |
| **composition values** | AO–BH oxides wt%, `Total`; BI–BJ Cl, F wt% | reported | Long format: one value per analyte. Blanks usually mean *not analysed*. See §5 for notation. |
| free text | BK `Remarks` | — | Needs reading; may hold inclusion context (touching, altered). |

**Per-mineral sheets** add compiler calculations: cations per formula unit, Mg#, Cr#, Ca#,
garnet Ca-intercept, Mg# Ca-corrected, eclogitic-garnet class (Aulbach & Jacob 2016), majorite
barometer (Beyer & Frost 2017), and **spinel Fe³⁺ recalculated after Droop (1987)**. These are
all `calculated by compiler`: we import them as such, or recompute with versioned rules.

## 4. Other compilations

**Stachel trace elements:** the same leading columns as above, plus cations and ratios
(calculated), then trace elements in **wt ppm** "usually either SIMS or LA-ICP-MS"; the method
per row is not recorded. Chondrite-normalized ratios and Eu anomalies are calculated.

**Walter et al. sublithospheric:** per table, `Reference | Location | Craton | Sample # |
Diamond Type | Inclusion phases | X'll Structure | Reported Co-occurring | d13C | oxides |
cations`. Two columns matter for our design:
- `Inclusion phases` vs `X'll Structure`: an **observed vs inferred-phase** distinction already
  present in the source.
- `Reported Co-occurring`: assemblage, as text.

Table 3 holds mineral/melt partition coefficients, which are not inclusion data. Table 6
(MgSiO₃) has 278 columns and a different layout; to inspect before any import.

**Smit et al. radiogenic:** one row per inclusion analysis (Re, Os ppb; ¹⁸⁷Re/¹⁸⁸Os,
¹⁸⁷Os/¹⁸⁸Os with uncertainties; Sm, Nd ppm, ¹⁴⁷Sm/¹⁴⁴Nd, ¹⁴³Nd/¹⁴⁴Nd with 2σ), plus
**isochron age repeated on every row of the isochron**, model ages (TRD, TMA, TDM, TCHUR,
calculated), and separate sheets for isochron initial ratios and the reference values used
(PUM, chondrite). The repeated isochron age is a measurement on a *set* of inclusions, not on
each one.

## 5. Value notation found in the data

Counted across the oxide and Total columns of Stachel `All diamonds`:

| Notation | Count | Meaning | Our handling |
|---|---|---|---|
| `b.d.`, `bdl` | 355 | below detection, limit not given | value status `below detection`, no number |
| `<0.02`, `<0.01`, `<0.06` … | ~470 | below a stated detection limit | value status `below detection`, detection limit stored |
| `≤0.03`, `≤0.04` … | ~57 | as above, written with ≤ | same; keep the original symbol |
| `< 0.02` with a non-breaking space | 13 | same as `<0.02` | normalize whitespace before parsing |
| empty string | 218 | ambiguous | `ambiguous`; distinct from a blank cell (*not analysed*) |
| blank | most | usually *not analysed* (per dictionary) | `not measured`, but flagged, since "usually" ≠ always |

Also: `FeO` is total iron except where spinel Fe³⁺ was recalculated; `size` has inconsistent
spacing in the same notation (`-11+9` and `-11 +9`).

## 6. What the compilations can't represent

1. **Location in the source.** References are per row, but no page, table or supplement. Every
   compiled value is traceable to a paper, not to a spot in it (CLAUDE.md rule 3).
2. **Who reported what, where several sources mix.** `unpubl and Phillips et al. (2004)`;
   host data from reference H next to inclusion data from reference F on one row.
3. **Physical-inclusion identity across papers.** Each row is one analysis; there is no link
   saying two rows (or a row and a later paper) are the same inclusion.
4. **Inclusion context.** Touching/non-touching, in situ vs released, protogenetic/syngenetic:
   absent, except where buried in `Remarks` or `paragenesis` (`epigenetic`).
5. **Analytical conditions and uncertainty for chemistry.** No method per row for trace elements
   (SIMS or LA-ICP-MS), no oxide uncertainties, no detection limits except where written in a cell.
6. **Coordinates and locality hierarchy.** Names only; craton is a separate interpretation.
7. **Disagreement.** One paragenesis per row; competing interpretations aren't stored.
8. **Post-2021 and some older literature.** Snapshot of October 2021 (Stachel); A2 and A5 are
   newer. Meyer & Boyd 1972 contributes only 3 rows.
9. **Spectroscopy beyond FTIR nitrogen.** No Raman, PL or CL data.
10. **Formatting-encoded information.** The bold-red %B substitutions.

## 7. Implications for the blocking decisions

| Decision | What the compilations tell us |
|---|---|
| D-001 inclusion identity | Rows can't be merged into physical inclusions automatically. Import each row as one *observation*; host-diamond grouping by (reference, locality, sample #) is a **candidate** link, flagged for review, not a merge. |
| D-002 provenance granularity | Two sources per row (F and H) means provenance must sit at least at the measurement level, not the row. |
| D-003 measurement storage | 60+ oxide and 50+ trace-element columns, mostly empty per row: long format confirmed. |
| D-006 group-level data | Smit's repeated isochron age and `chromite (average)` rows need an *inclusion set* or *statistic type*. |
| D-008 phase vocabulary | 262 spellings to map; Walter's `Inclusion phases` vs `X'll Structure` supports storing observed and inferred phases separately. |
| D-010 interpretations | Paragenesis, garnet class, craton are interpretations with a scheme; the paragenesis code also needs splitting into suite, alteration and depth fields. |
| D-013 build on compilations | Strong case for importing them as a **compilation source layer**: ~12,000 analyses with references already attached. Our curation then adds what §6 lists. Still the professor's call. |

**Suggested import rule (for D-013, not yet decided):** every compiled value gets provenance
`source = compilation (Stachel 2021, row n)` *and* `cited_reference = F/H/AM column`, with
workflow status `imported, unverified`. When we curate the original paper, the curated
observation is linked to the compiled one instead of replacing it.

## Not yet checked

- Whether host-diamond fields agree across rows that share (reference, locality, sample #).
- Stachel per-mineral sheets column by column (only the `All` sheets were profiled).
- Walter Table 6 layout, and the `Remarks` column contents.
- Whether De Hoog 2019 and Anzolini 2016 appear under other reference strings.
