---
id: D-005
status: proposed (needs the professor's view)
date: 2026-10-22
tags: [decision]
---

# D-005 — Scope: which diamonds, inclusions and sources are in

> **In plain terms:** some borderline material could be in or out: fluid inclusions in fibrous
> diamonds, lab-grown diamonds, diamonds still inside their host rock, and theses or conference
> abstracts. **Proposal:** design the schema so all of them *fit*, but only *collect* the core
> set now. The professor should confirm, because this sets what the database claims to cover.

## Context
- [Brief §2](../brief.md) lists fibrous/coated diamonds and high-density fluids (HDFs) as a
  scope decision. [Compilations mapping](../compilations-mapping.md): the Stachel reference list
  includes MSc/PhD theses and conference volumes; Smit includes U-Th-He ages on fluid-bearing
  fibrous diamonds; Walter includes partition coefficients (not inclusion data).
- Limited time (2–3 h/week): every in-scope category costs curation time.

## Proposal (by category)

| Category | Schema supports it? | Collect now? | Why |
|---|---|---|---|
| Mineral inclusions in natural diamonds (lithospheric and sublithospheric) | yes | **yes** | Core of the project |
| Polyphase / composite inclusions, unknown phases | yes | **yes** | Common; handled as observed vs inferred phase |
| Host-diamond-only data (δ¹³C, N) with no inclusion data | yes | **yes, when it belongs to a diamond with inclusions** | 2,049 compilation rows are like this; needed for host context |
| Fluid / melt inclusions and HDFs in fibrous or coated diamonds | yes (phase type = fluid; bulk composition) | **later** | Different analytical world (bulk microinclusion analyses); add after Tier 1 |
| Microdiamonds | yes | **yes** | Sobolev 2004 (B5) compares micro and macro |
| Inclusions in diamonds still in xenoliths | yes (host diamond has a host-rock context) | **yes, flagged** | Rare; context matters for interpretation |
| Synthetic diamonds (HPHT/CVD), metal-flux inclusions | could be represented | **no** | Not mantle samples; would distort analyses |
| Impact / metamorphic (UHP) microdiamonds in crustal rocks | could be represented | **no for now** | Different geology; revisit if the professor wants it |
| Mineral inclusions in other mantle minerals | no | **no** | Out of project scope |
| Peer-reviewed papers + their supplements | — | **yes** | |
| Theses, conference abstracts (e.g. IKC extended abstracts) | yes (publication type) | **yes, as sources, flagged** | Some data exists only there; abstracts also duplicate papers (dedup test, B5) |
| Compilations (Dataset 0) | yes (source type = compilation, see D-002) | **yes**, if D-013 agrees | |
| Experimental / partition-coefficient data (e.g. Walter Table 3) | no | **no** | Not observations of natural inclusions |

## Consequences
- The schema carries a few extra fields (phase type, host-rock context, publication type) from
  the start, so widening scope later needs no redesign.
- Coverage statements (brief §9) must say what was collected, e.g. "excludes fluid inclusions".

## Questions for the professor
1. Are fluid/melt inclusions and HDFs in fibrous diamonds wanted, and how soon?
2. Should theses and conference abstracts count as sources?
3. Any category above you'd move in or out?
