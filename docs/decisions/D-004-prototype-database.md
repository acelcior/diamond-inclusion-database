---
id: D-004
status: accepted
date: 2026-10-22
accepted: 2026-10-22
tags: [decision]
---

# D-004 — Prototype database: SQLite, DuckDB or PostgreSQL

> **In plain terms:** which database program holds the data while we test the design?
> **Proposal:** SQLite: the whole database is one file, there's nothing to install or run, and
> a free tool (Datasette) turns it into a website collaborators can browse and filter. Move to
> PostgreSQL + PostGIS later, when maps and multiple editors make it worth it.

## Context
- [Inputs](../inputs-needed.md): very little command-line experience; 2–3 h/week; shared with
  collaborators; no budget for hosting.
- [Brief §3](../brief.md): PostgreSQL + PostGIS is the long-term target; an accessible prototype first.
- Prototype size is small: ~12,000 compiled analyses plus 10 curated papers.

## Options
| | SQLite | DuckDB | PostgreSQL (+PostGIS) |
|---|---|---|---|
| Setup | none (built into Python, already on this Mac) | `pip install` | install + run a server (Postgres.app) |
| Sharing | send one file | send one file | collaborators need a server or a dump |
| Browse in a browser | Datasette: filters, facets, CSV export, no code | limited | needs a separate app |
| Foreign keys, constraints | yes (must be switched on per connection) | partial | full |
| Spatial | SpatiaLite extension, or plain lat/long columns | spatial extension | PostGIS, best |
| Multi-user editing | no | no | yes |

## Proposal
**SQLite + Datasette for Phases 1–5**, with portability rules so the move to PostgreSQL is
mechanical:
- Plain SQL types only (`TEXT`, `INTEGER`, `REAL`); `CHECK` constraints for controlled values
  instead of database-specific enums; controlled vocabularies as tables.
- Coordinates as latitude/longitude columns + CRS + precision class; no spatial extension until
  PostGIS.
- `PRAGMA foreign_keys = ON` set by every script that writes (SQLite default is off).
- The database file is **rebuilt from source files** (schema SQL + vocab CSVs + curated JSON +
  compilation imports) by one script, so it's never the only copy and never edited by hand.
  The `.sqlite` file stays out of git (already in `.gitignore`); sources are in git.

Revisit when any of these happen: more than one person needs to edit at once, the map view
(Phase 6–7) needs real spatial queries, or the data outgrows one file.

## Consequences
- Zero setup for you; Claude runs the build script.
- Collaborators get either the `.sqlite` file, CSV exports, or a Datasette view (local now;
  hosted later if wanted).
- Some PostgreSQL features (arrays, JSONB, PostGIS) are off-limits until migration.

## Evidence / test cases
Phase 1 exit gate: schema loads in SQLite; an illustrative record round-trips; the same DDL loads
in PostgreSQL unchanged (or with a documented, scripted diff).
