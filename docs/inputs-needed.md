---
tags: [inputs]
---

# Inputs needed from you

Claude can't guess these, and they shape the design. Fill in the answers directly in this file.

Related: [roadmap](roadmap.md) · [brief](brief.md)

## Constraints

| Question | Your answer |
|---|---|
| Solo or team? Who will review extracted records? | Team effort, I will review the records.|
| Comfort with Python / SQL / command line (none / some / fluent) | very little|
| Time available per week | 2-3 hours|
| Budget for model API calls (extraction at scale is the main running cost) | one claude pro plan|
| Institutional journal access? Text-and-data-mining (TDM) rights? | binghamton access, idk about rights|
| Will the database be public, shared with collaborators, or private? | shared with collaborators|
| Intended licence for the data (e.g. CC BY, CC0, undecided) | undecided|
| Any existing data you already hold (spreadsheets, compilations, your own analyses)? | no|
| Primary research questions you personally care about most | n/a, on contract for professor |

## Seed papers (5–10)

Pick papers you can legally access, chosen to **stress the schema**, not to be easy.
Aim to cover as many of these styles as possible:

- [ ] Individual inclusions with full electron-microprobe (EPMA) oxide tables
- [ ] A paper reporting only ranges, means or bulk results for groups
- [ ] Data mainly in supplementary spreadsheets (e.g. LA-ICP-MS trace elements)
- [ ] Isotopes or ages (e.g. sulfide Re-Os, garnet Sm-Nd, isochrons)
- [ ] Raman / elastic barometry or spectroscopy-led identification
- [ ] Superdeep / sublithospheric inclusions (observed vs inferred original phase)
- [ ] An old paper with historical locality names or old mineral terminology
- [ ] A paper re-analysing specimens published earlier (tests cross-paper identity)
- [ ] Alluvial / unknown-provenance diamonds

### Proposed seed set (found by Claude, 2026-10-21)

Every citation and DOI below was checked against OpenAlex/Crossref. **Styles** are what each
paper is *expected* to test, based on its title and abstract; confirm them once you've read it.
**Access:** OA = free to download; *library* = use Binghamton access.
Save PDFs into `papers/` named `firstauthor-year.pdf` (e.g. `phillips-2004.pdf`), and any
supplements as `phillips-2004-supp1.xlsx`, etc. Tick the last two columns as you go.

**Batch A — start here (5 papers, deliberately arranged in pairs that share specimens):**

| # | Citation | DOI | Styles it should test | Access | PDF? | Supp? |
|---|---|---|---|---|---|---|
| A1 | Phillips, Harris & Viljoen (2004) Mineral chemistry and thermobarometry of inclusions from De Beers Pool diamonds, Kimberley, South Africa. *Lithos* 77, 155–179 | [10.1016/j.lithos.2004.04.005](https://doi.org/10.1016/j.lithos.2004.04.005) | Individual EPMA tables; thermobarometry; touching vs non-touching | library | [x] `phillips-2004.pdf` | none mentioned in the paper |
| A2 | Nimis, Grütter & Nestola (2025) Multistage diamond formation, mantle uplift and changing geothermal regimes recorded by inclusions in Kimberley diamonds. *Mineralogy and Petrology* 119, 413–432 | [10.1007/s00710-025-00908-2](https://doi.org/10.1007/s00710-025-00908-2) | **Re-interprets the A1 inclusions**: cross-paper identity, conflicting P-T interpretation, elastic modelling | OA | [x] `nimis-2025.pdf` | [ ] **needed**: Supplementary Table S1, from the article page |
| A3a | Stachel, Brey & Harris (2000) Kankan diamonds (Guinea) I: from the lithosphere down to the transition zone. *Contrib. Mineral. Petrol.* 140, 1–15 | [10.1007/s004100000173](https://doi.org/10.1007/s004100000173) | **Added 2026-10-22**: A3 says its full EPMA dataset is "Table 1 of electronic supplementary material, Stachel et al., this issue", i.e. this paper's supplement | library | [ ] | [ ] **needed**: electronic supplementary material, Table 1 |
| A3 | Stachel, Harris, Brey & Joswig (2000) Kankan diamonds (Guinea) II: lower mantle inclusion parageneses. *Contrib. Mineral. Petrol.* 140, 16–27 | [10.1007/s004100000174](https://doi.org/10.1007/s004100000174) | Superdeep; observed vs inferred original phase; alluvial source; printed tables show *selected* inclusions only; bulk analysis of a symplectite (KK-83) | library | [x] `stachel-2000-kankan2.pdf` | uses A3a's supplement |
| A4 | Stachel, Harris, Aulbach & Deines (2002) Kankan diamonds (Guinea) III: δ¹³C and nitrogen characteristics of deep diamonds. *Contrib. Mineral. Petrol.* 142, 465–475 | [10.1007/s004100100297](https://doi.org/10.1007/s004100100297) | **Host diamonds from the same Kankan series as A3**: cross-paper specimen identity; FTIR nitrogen; δ¹³C | library | [x] `stachel-2002-kankan3.pdf` | none mentioned in the paper |
| A5 | Genzel et al. (2023) Geobarometric evidence for a LM/TZ origin of CaSiO₃ in a sublithospheric diamond. *Geochem. Perspect. Lett.* 25, 41–45 | [10.7185/geochemlet.2313](https://doi.org/10.7185/geochemlet.2313) | XRD residual pressure; uses the name **breyite** (= CaSiO₃-walstromite in B4): synonym test; short paper | OA | [x] `genzel-2023.pdf` (publisher's "noSI" version) | [ ] supplementary information is separate |

**PDF quality notes (2026-10-22):** A1 and A2 have clean text layers. A3 and A4 (Springer,
2000–2002) have an encoded text layer: it decodes, but spaces and ligatures are lost, so
tables in them will need to be read from page images rather than from extracted text.

**Batch B — after the schema survives Batch A:**

| # | Citation | DOI | Styles it should test | Access | PDF? | Supp? |
|---|---|---|---|---|---|---|
| B1 | Meyer & Boyd (1972) Composition and origin of crystalline inclusions in natural diamonds. *Geochim. Cosmochim. Acta* 36, 1255–1273 | [10.1016/0016-7037(72)90048-8](https://doi.org/10.1016/0016-7037(72)90048-8) | Old terminology and locality names; early EPMA; likely scanned (OCR) | library | [ ] | [ ] |
| B2 | Gress et al. (2021) Mesozoic to Paleoproterozoic diamond growth beneath Botswana recorded by Re-Os ages from individual eclogitic and websteritic inclusions. *Lithos* 388–389, 106058 | [10.1016/j.lithos.2021.106058](https://doi.org/10.1016/j.lithos.2021.106058) | Re-Os isotopes; isochron = measurement on an inclusion set; growth zones | OA | [x] `gress-2021.pdf` | [ ] check article page |
| B3 | De Hoog, Stachel & Harris (2019) Trace-element geochemistry of diamond-hosted olivine inclusions from the Akwatia Mine, West African Craton. *Contrib. Mineral. Petrol.* 174 | [10.1007/s00410-019-1634-y](https://doi.org/10.1007/s00410-019-1634-y) | Trace elements, probably in supplementary tables; derived classification (harzburgitic/lherzolitic) | OA | [x] `dehoog-2019.pdf` | [ ] check article page |
| B4 | Anzolini et al. (2016) Depth of formation of CaSiO₃-walstromite included in super-deep diamonds. *Lithos* 265, 138–147 | [10.1016/j.lithos.2016.09.025](https://doi.org/10.1016/j.lithos.2016.09.025) | Elastic barometry; residual vs entrapment pressure; walstromite/breyite naming | OA (author copy) | [x] `anzolini-2016.pdf` | [ ] check article page |
| B5 | Sobolev et al. (2004) Mineral inclusions in microdiamonds and macrodiamonds from kimberlites of Yakutia: a comparative study. *Lithos* 77, 225–242 | [10.1016/j.lithos.2004.04.001](https://doi.org/10.1016/j.lithos.2004.04.001) | Russian research tradition; group comparisons (may report means/ranges); a conference-abstract version also exists ([10.29173/ikc3082](https://doi.org/10.29173/ikc3082)), which tests publication dedup | library | [x] `sobolev-2004.pdf` | [ ] check article page |

Still missing: a paper with data *mainly* in supplementary spreadsheets (B3 may cover it),
and one that reports *only* ranges or means (B5 may cover it). We'll fill these gaps after
reading Batch B.

### Dataset 0 — existing open compilations (download these too)

Published literature compilations on Borealis, all **CC0** (public domain). They change the
strategy: see D-013 in [decisions](decisions/README.md). Files are `.xlsm` (Excel with macros):
**open them with macros disabled**. Save into `papers/compilations/`.

**Received 2026-10-22:** all four, in `papers/compilations/{stachel-major, stachel-traces,
walter-sublithospheric, smit-radiogenic}/`. Every file matches the MD5 checksum Borealis publishes.

| Dataset | Author(s) | DOI | Files |
|---|---|---|---|
| Diamond Inclusion Database (major elements + host-diamond physical, IR and stable-isotope data), Oct 2021 | Stachel | [10.7939/DVN/EJUE1G](https://doi.org/10.7939/DVN/EJUE1G) | `Diamond_Database_Oct-2021.xlsm` (8.6 MB) + PDF data dictionary |
| Trace element data for inclusions in diamond, Oct 2021 | Stachel | [10.7939/DVN/581P99](https://doi.org/10.7939/DVN/581P99) | `Diamond_Traces_Oct-2021.xlsm` (2.3 MB) + PDF data dictionary |
| Major and trace element composition of sublithospheric inclusions in diamond | Walter, Thomson & Smith | [10.5683/SP3/LIVK1K](https://doi.org/10.5683/SP3/LIVK1K) | `RiMG Chapter11_Walter_Tables.xlsm` (8.9 MB) |
| Radiogenic isotope compositions of inclusions in diamond (Re-Os, Sm-Nd) | Smit, Milne, Richardson & Timmerman | [10.7939/DVN/DRAJGT](https://doi.org/10.7939/DVN/DRAJGT) | `Chapter11_supplementary data.xlsm` (0.2 MB) |

Related review: Stachel, Aulbach & Harris (2022) Mineral inclusions in lithospheric diamonds.
*Rev. Mineral. Geochem.* 88, 307–391, [10.2138/rmg.2022.88.06](https://doi.org/10.2138/rmg.2022.88.06).
The chapter says it rests on a database of almost 5000 inclusion analyses.

## Questions for the professor

The project is on contract, so the research priorities are theirs. Worth asking early:
1. What are the top 3 questions the database should answer for you?
2. Do you know the Stachel / Walter / Smit compilations above? Should we **build on them**
   (import them, then add per-value provenance, localities, newer and non-English literature,
   spectroscopy) or build **independently** and use them only as a cross-check?
3. Who are the collaborators, and how will they access the data (spreadsheet exports, a
   shared web view, or the database file itself)?
4. Is there a deadline or a first deliverable they expect?

## Existing compilations and references to check

Verify these before relying on them; Claude will help locate and assess them:
- Published inclusion compilations behind the major review papers (e.g. Stachel & Harris;
  the 2022 *Reviews in Mineralogy & Geochemistry* volume on diamond)
- GEOROC / EarthChem data models and any diamond-inclusion holdings
- IMA mineral list (RRUFF), Mindat (mineral and locality IDs), GeoNames, IGSN for samples
