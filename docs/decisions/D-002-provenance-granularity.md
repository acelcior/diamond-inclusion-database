---
id: D-002
status: accepted
date: 2026-10-22
accepted: 2026-10-22
tags: [decision]
---

# D-002 — Provenance granularity: where "where did this come from?" is recorded

> **In plain terms:** every number must point back to where it was found. Do we attach that
> pointer to each individual cell, or to each group of values that came from the same place?
> **Proposal:** to each *measurement* (e.g. one EPMA analysis = one row in a paper's table), and
> to each *assertion* (e.g. one paragenesis claim), with an optional override for a single value
> that came from somewhere else.

## Context
- CLAUDE.md rule 3: every extracted value traceable to publication + location + original value
  + excerpt.
- [Compilations mapping](../compilations-mapping.md): one Stachel row mixes up to three sources:
  inclusion chemistry (column F), host isotopes/FTIR (column H), δ¹⁸O (column AM). Phillips 2004
  rows mix published and unpublished data. So provenance per *row* is too coarse.
- An EPMA table row has ~12 oxide values that share one location (paper, Table 3, row "DBP-12").
  Recording location 12 times is redundant and invites inconsistency.

## Options
1. **Per row of our source spreadsheet / per extracted record.** Too coarse (fails the mixed rows).
2. **Per individual value.** Always correct, but ~12× the evidence rows for chemistry, and
   extraction must emit a location for every number.
3. **Per measurement / assertion, with optional per-value override.** A measurement groups values
   from one analysis at one location; an assertion is one claim (identification, paragenesis,
   P-T, locality match). A value carries its own evidence only when it differs from its group
   (e.g. a footnoted correction, a value taken from a supplement).

## Proposal
**Option 3.**

```
evidence (publication, supplement file, page, table/figure, row/column label, excerpt, source_type)
   ▲             ▲                 ▲
measurement   assertion       value (override, rare)
```

- `source_type` distinguishes `paper`, `supplement`, `compilation`, `personal communication`,
  `unpublished`. A compiled value has evidence pointing at the compilation file + row, **plus** a
  `cited_reference` (the paper the compiler cited), never just the paper.
- Excerpt is short (copyright rule 8); for table values the "excerpt" is the row/column label.
- Status fields (value status, derivation, workflow) live on the value or assertion, not on evidence.

## Consequences
- Extraction JSON (Phase 3) emits location once per table row, not per number: simpler prompts.
- Queries "show me the evidence for this value" walk value → measurement → evidence.
- A rare per-value override must be supported by the validator (Phase 3).

## Evidence / test cases
Phase 2: a Phillips table row (shared location); Kankan II values that point to Kankan I's
supplement (cross-paper location); a Stachel row with F, H and AM references.
