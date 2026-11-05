# Global Diamond Inclusion Database — Claude Code context

Read this first in every session. Full requirements: [docs/brief.md](docs/brief.md).
Current plan and status: [docs/roadmap.md](docs/roadmap.md). Recent work: [docs/log.md](docs/log.md).

## What this project is
A research-grade relational database of mineral inclusions in diamonds, built from the
scientific literature. The unit of interest is the **physical inclusion and its
observations/measurements**, not the paper.

## Non-negotiable rules
1. **Never invent** data, citations, DOIs, coordinates, specimen identities, or mineral IDs.
   If something is not in the source, record it as not reported / unknown — never fill it.
2. **Physical inclusion ≠ observation ≠ measurement.** Never count repeat measurements or
   repeat reports as separate inclusions. Never merge two reports into one physical
   inclusion without explicit evidence (shared sample ID, explicit cross-reference).
3. **Every extracted value is traceable**: source publication + location (page/table/figure/
   supplement) + original value/term/units + short evidence excerpt.
4. **Original and normalized are stored separately.** Original values, units and terms are
   never overwritten; normalization uses explicit, versioned conversion rules.
5. **Author interpretation is attributed and separate** from measured observations
   (e.g. paragenesis, "former bridgmanite", P-T, origin). Disagreements are kept, not resolved.
6. **Status dimensions are separate fields**, never one combined enum:
   value status (reported / not reported / not measured / not applicable / unknown / ambiguous),
   derivation (reported / calculated / inferred / interpreted),
   workflow (not attempted / extracted / failed / pending review / approved / rejected).
7. **Geographic honesty**: no centroid coordinates presented as exact. Coordinates carry
   precision class and source. Unknown locality must never block storing a record.
8. **Copyright**: only legally accessible full texts; store short excerpts only; respect API
   and publisher TDM terms.
9. **Illustrative examples are labelled** as illustrative and kept out of real data tables/files.

## Working with this user
- Very little Python/SQL/command-line experience: Claude runs commands itself, explains
  results in plain language, and avoids asking the user to edit code by hand.
- Roughly 2–3 hours a week; plan sessions as small, finishable roadmap items.
- Claude Pro plan, no API budget: no paid batch API pipelines (see D-014).
- On contract for a professor, who owns the research priorities; the database is shared
  with collaborators.

## Working conventions
- Work incrementally: schema → validate on real papers → automate. No full UI before the
  schema has survived the seed papers.
- Design decisions are recorded as ADRs in `docs/decisions/` (template there). If a change
  contradicts an accepted ADR, stop and raise it rather than silently diverging.
- At the end of each working session, append a short entry to `docs/log.md` and tick items
  in `docs/roadmap.md`.
- Docs use standard relative Markdown links (they work in Obsidian, GitHub and here).
- Python for pipeline/validation; SQLite/DuckDB acceptable for prototype, PostgreSQL+PostGIS
  is the long-term target — keep SQL portable unless an ADR says otherwise.
- Ambiguous table notation (`n.d.`, `—`, `bdl`, blank, FeO vs FeOtotal) is flagged, never guessed.
- Every inclusion and derived value gets an **extraction confidence** (high/medium/low) computed by the
  versioned rules in [docs/confidence.md](docs/confidence.md); set `extraction_method` in each paper's
  `source.json`. Never assign a level by hand.

## Layout (grows over time)
```
docs/          brief, roadmap, decisions (ADRs), inputs, log — the Obsidian vault content
schema/        SQL DDL and migrations            (Phase 1)
vocab/         controlled vocabularies (CSV)     (Phase 1)
extraction/    JSON Schema, prompts, scripts     (Phase 3)
gold/          hand-curated gold-standard records (Phase 2)
compilations/  CC0 compilations converted to text (rows.jsonl) + source.json; a separate source layer (D-013)
bibliography/  literature inventory (inventory.csv), see docs/literature-workflow.md (Phase 4)
papers/        local PDFs/supplements — gitignored, never committed
```
