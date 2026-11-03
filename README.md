# Global Diamond Inclusion Database

A research-grade, traceable relational database of mineral inclusions in diamonds,
built from the scientific literature.

**Start here:** [docs/brief.md](docs/brief.md) (requirements) ·
[docs/roadmap.md](docs/roadmap.md) (plan and status) ·
[docs/decisions/](docs/decisions/README.md) (design decisions) ·
[docs/inputs-needed.md](docs/inputs-needed.md) (what's needed from you) ·
[docs/log.md](docs/log.md) (progress)

**Website:** https://diamond-inclusion-database.vercel.app is the searchable database
(served from `site/`). After a data change, run `python3 -I scripts/export_site.py`, then push;
Vercel redeploys on every push to `main`. Project docs live here on GitHub, not on the website.

## Using this folder
- **Obsidian:** open this folder as a vault ("Open folder as vault"). The docs use standard
  Markdown links, so they also render on GitHub and in Claude Code.
- **Claude Code:** start a session in this folder; `CLAUDE.md` gives Claude the project
  rules automatically. Name the roadmap item you're working on.
- **Git:** commit after each session. `papers/` (PDFs, supplements) is never committed.
