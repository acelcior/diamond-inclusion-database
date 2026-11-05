---
tags: [phase-4, literature, workflow]
date: 2026-11-05
---

# Literature inventory: how we find papers and keep the list current

One master list of every paper we know about, where each was found, and what we decided about
it: [`bibliography/inventory.csv`](../bibliography/inventory.csv), maintained by
`scripts/literature.py`. This page explains the tools, the evidence for choosing them, and
the routine.

Related: [roadmap](roadmap.md) (Phase 4) · [licence register](licence-register.md) ·
[inputs needed](inputs-needed.md) · [decisions](decisions/README.md) (D-015)

## In short

- **OpenAlex is the backbone.** Free, open (CC0), scriptable, and the same citation data that
  Consensus and Connected Papers are built on. Citation chaining from known papers is done by
  the script, so it is repeatable and every candidate records how it was found.
- **Connected Papers is a useful second opinion, not a source of bulk.** It finds "sibling"
  papers that share references with ours without citing them directly. Against our 11 seeds it
  added 10%, but once chaining ran from all 138 known papers it added nothing for the core
  literature. Spend the free 5 graphs a month on papers *outside* the well-connected core: new
  topics, new regions, very recent papers.
- **Consensus is for gaps, used by hand.** Plain-language questions about a mineral, method or
  locality that citation links may miss. Results go into the inventory as a list of papers;
  its AI summaries are never used as data.
- **The Stachel compilations are the strongest seed.** The 127 papers they cite are already
  known to contain inclusion data, so they start the inventory as *relevant*.

## What was tested (2026-11-05)

| Test | Result | What it means |
|---|---|---|
| OpenAlex chaining from our 11 seed papers (1 step: their references + papers citing them) | 1,193 candidates; contains **72 of the 113** compilation papers that OpenAlex knows | Chaining finds most of the known literature, but in a large pool, so a filter and triage are needed |
| Keyword filter on those candidates: "diamond" **and** "inclusion" in title/abstract | Keeps 406, but loses **34** compilation papers, 32 of them because OpenAlex has no abstract (Elsevier withholds them) | Too strict. Abstracts are often missing |
| Filter: "diamond" in title/abstract only | Keeps 772, loses only **2** of 76 | Used by the script. A paper with no abstract is read early, not dropped |
| Connected Papers graph of Phillips 2004 (40 papers) | 35 already in the OpenAlex pool; **4 new**, all relevant (e.g. Appleyard 2004 Finsch eclogitic diamonds) | ~10% extra over a small seed set (but see the full-chaining row below) |
| **Full chaining from all 138 known papers** (`literature.py chain`, first run) | **1,490 new candidates** (1,058 high priority, 432 medium); 334 published since 2022, i.e. after the compilations; new finds fell from 591 in the first 10 papers to ~10 per 10 at the end | The core literature is a fairly closed citation network: chaining reaches most of it |
| The same Connected Papers graph, against the full inventory | **All 39** of its papers already in the inventory | Connected Papers adds little in the well-connected core; its value is at the edges |
| Consensus | Needs a (free) account to search, so not tested here | Judged from its documentation (below) |

## The three tools compared

| | OpenAlex (via our script) | Connected Papers | Consensus |
|---|---|---|---|
| What it does | Lists the references of a paper and every paper citing it | A map of the ~40 papers most similar to one paper (shared references and shared citers) | AI search: answers a question with ~20 relevant papers |
| Data behind it | OpenAlex (CC0) | Semantic Scholar corpus (ODC-BY) | Semantic Scholar + OpenAlex + its own crawl |
| Cost | Free. Without a key, everyone on the network shares a small daily budget (≈1,000 list queries); a free personal key gives 10× that | Free: 5 graphs/month. Academic: US$6/month | Free: basic search, 10 AI answers, 3 deep reviews a month, light MCP use. Pro US$12/month |
| Automatable | Yes (official API) | No public API: use by hand only | Yes, through its official MCP connector for Claude (sign-in by you) |
| Repeatable | Yes: same query, same result, logged | Mostly (graph changes as the corpus grows) | No: AI ranking changes; record the question and date |
| Best for | Systematic coverage and monthly updates | Finding siblings of a key paper; spotting clusters (e.g. Yakutia, Slave craton) | Questions by topic: "Raman barometry of coesite inclusions", "inclusions in diamonds from Guaniamo" |
| Watch out for | Missing abstracts; old papers and Russian journals less complete | Academic plan is personal and non-commercial; no bulk export | Answers are AI text: never cite them; only the papers it lists count |

## Setup (once)

1. **(Recommended) free OpenAlex key.** Sign in at <https://openalex.org/settings/api>, copy
   the key, then in the project folder run `pbpaste > .openalex-key` (the file is gitignored and
   never committed). Without it the script still works but may stop for the day sooner.
2. **(Optional) Connected Papers account**, free, for the 5 graphs a month.
3. **(Optional) Consensus** free account. To let Claude search it inside these sessions, add
   its official connector (`https://mcp.consensus.app/mcp`) and sign in when asked.

## The routine

**Each week (part of a normal session; Claude runs the commands):**

1. `python3 -I scripts/literature.py status`: what is waiting.
2. **Triage** the next ~50 candidates (`literature.py next 50` lists them, high priority and
   most-linked first; `literature.py decide FILE` applies a CSV of `openalex_id,triage,note`
   and never overwrites an earlier decision). Claude reads title, journal and abstract
   (from OpenAlex) and proposes `relevant` / `maybe` / `not_relevant` with a one-line reason
   prefixed `Claude:` in `triage_note`; you or the professor spot-check and change any.
   - **relevant** = reports or re-analyses inclusions in natural diamonds (any data: chemistry,
     identification, isotopes, Raman, P-T), or is a review/compilation listing such papers.
   - **maybe** = can't tell without the full text (e.g. a kimberlite paper with a diamond section).
     Also used for papers that depend on scope decision D-005 (fibrous diamonds and fluid
     inclusions, diamonds still in xenoliths, ophiolite diamonds).
   - **not_relevant** = no inclusion data: experiments, equations of state, modelling, deposit
     geology, reviews of the host diamond only.
3. Papers newly marked `relevant` are chained on the next `chain` run: their references and
   citers enter as new candidates. This is how the list grows outward from what we trust.

**Each month (about 15 minutes):**

1. `python3 -I scripts/literature.py chain`: picks up papers published since the last run
   that cite anything relevant (forward updates are cheap).
2. Spend the 5 Connected Papers graphs on recently accepted papers from a *different* region or
   topic than before. In List view, copy the titles into a text file, then
   `python3 -I scripts/literature.py add that-file.txt --source "connected-papers:<origin paper>"`.
3. Ask Consensus 2–3 gap questions (a mineral, method or locality the inventory is thin on).
   Save the listed papers (DOIs or titles) to a file and `add` it with
   `--source "consensus:<question>"`.
4. Re-run the [licence audit](licence-register.md) for papers chosen for extraction.

**Stopping rule (when the inventory is "complete enough"):** a chaining round over all
relevant papers adds fewer than 5% new relevant papers, and the last 10 Connected Papers /
Consensus searches added none. The `found_by` column lets us measure this per tool.

## Rules

- **Nothing invented.** A DOI not in OpenAlex is kept exactly as printed, with a note (several in
  the compilation are mistyped, e.g. `10.1026/…` for `10.1016/…`); a title without an exact match
  is reported and not added.
- **Abstracts are read, never stored** (they are often publisher copyright). The inventory holds
  only citation metadata, which is CC0 from OpenAlex.
- **Every candidate records how it was found** (`found_by`: `seed:`, `compilation:`, `chain:`,
  `connected-papers:`, `consensus:`, `manual`) and when (`found_date`).
- **Triage is a human decision.** Claude may propose; the `Claude:` prefix shows which calls
  have not been checked. `priority` is only a reading order, set by a fixed rule.
- **No scraping and no shared accounts.** Connected Papers and Consensus are used through their
  own interfaces or official connector, within their terms.

## The inventory columns

| Column | Meaning |
|---|---|
| `openalex_id`, `doi`, `title`, `year`, `first_author`, `venue`, `type` | Citation metadata from OpenAlex |
| `oa_status` | Open-access status from OpenAlex (gold, green, hybrid, bronze, diamond, closed) |
| `found_by`, `found_date` | How and when it entered the list (several sources are joined with `;`) |
| `links` | How many relevant papers it cites or is cited by: a rough relevance signal, like Connected Papers' similarity |
| `priority` | Reading order: `high` = "diamond" and "inclusion" in title/abstract, or no abstract to judge; `medium` = "diamond" only |
| `triage`, `triage_note` | `candidate` → `relevant` / `maybe` / `not_relevant` / `duplicate`, with the reason |
| `chained_on` | Date its references and citers were last collected |

## Known gaps

- **Walter and Smit compilations carry no DOIs**: their ~130 reference strings still need
  matching by title (later, with `add`).
- **Russian-language literature** (e.g. *Geologiya i Geofizika*) is expected to be thin in all three
  tools (not yet measured); English translations are more likely to be indexed than originals.
- **Conference abstracts and theses** (Kimberlite Conference extended abstracts have DOIs
  under 10.29173, e.g. Sobolev 2004's abstract) depend on scope decision D-005.
- **Papers with no "diamond" in title or abstract** are not added by chaining (2 of 76 known
  papers in the test); they still enter through the compilations or the manual tools.
