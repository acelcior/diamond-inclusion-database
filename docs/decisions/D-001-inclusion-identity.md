---
id: D-001
status: accepted
date: 2026-10-22
accepted: 2026-10-22
tags: [decision]
---

# D-001 — Inclusion identity: how a physical inclusion relates to its reports

> **In plain terms:** the same tiny mineral grain can be written about in several papers, under
> different sample numbers. Do we store it once, or once per paper? **Proposal:** once per paper
> (an *observation*), and a separate, reviewable link says "these observations are the same
> grain", with the evidence for it. Nothing is ever merged automatically.

## Context
- [Brief §2](../brief.md): one inclusion may be described in many publications; don't assume two
  descriptions are the same inclusion without evidence; don't count repeat measurements as
  separate inclusions.
- [Compilations mapping](../compilations-mapping.md): each Stachel row is one *analysis*. About
  9,519 distinct (reference, locality, sample #) keys for 10,472 rows, so rows sharing a host
  diamond exist, but nothing says which rows are the same inclusion. Sample numbers were
  sometimes altered by the compiler (zero-padding), and suffixes (`-a`, `core`, `(1)`) mark an
  inclusion or spot rather than a diamond.
- Seed cases: Phillips 2004 vs Nimis 2025 (same De Beers Pool inclusions, re-interpreted);
  Kankan I/II/III (same KK-numbered diamonds across three papers); compilation rows vs the
  original paper's rows.

## Options
1. **One canonical row per physical inclusion; papers attach to it.** Simple counting, but every
   import must decide identity up front. Wrong merges corrupt counts and are hard to undo.
2. **Observations only, no physical-inclusion entity.** Never wrong, but "how many distinct
   inclusions?" (brief §9) can't be answered, and cross-paper comparisons stay manual.
3. **Observation per report + physical inclusion as a cluster built from explicit identity links.**
   Each link records evidence (shared sample ID, explicit cross-reference in the text, same
   collection), who asserted it (author, compiler, us) and confidence. A physical inclusion is
   whatever its accepted links connect; an observation with no links is its own physical inclusion.

## Proposal
**Option 3**, with the same pattern for host diamonds:

```
publication ──< observation >── physical_inclusion ──> host_diamond
                    │                  ▲
                    └── identity_link ─┘  (evidence, asserted_by, confidence, review status)
```

- Every imported or extracted report creates one `observation`.
- `physical_inclusion` and `host_diamond` rows are created per observation at first, then joined
  via identity links when evidence exists. Joining or splitting changes links, never observation data.
- Specimen identifiers are stored as reported (original string) in an identifier table, with the
  source that used them; normalized forms (e.g. zero-padded) are a separate column.
- Compiler-proposed links (e.g. rows sharing reference + locality + sample #) are imported as
  `asserted_by = compiler-derived`, status `pending review`.
- Repeat measurements of one inclusion are *measurements* on one observation, not new observations.

## Consequences
- Counts in brief §9 come from different tables: observations, accepted physical inclusions,
  host diamonds, measurements. Distinct-inclusion counts carry a "links reviewed?" caveat.
- More tables than option 1, and a review queue for links.
- Disagreements about identity (one paper says same grain, another doesn't) are representable.

## Evidence / test cases
To verify during Phase 2: A1 ↔ A2 (do Nimis's inclusions carry Phillips's sample IDs?),
A3a ↔ A3 ↔ A4 (KK numbers), Stachel compilation rows ↔ curated Phillips rows.
