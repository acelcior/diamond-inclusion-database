# Global Diamond Inclusion Database

A research-grade, traceable relational database of mineral inclusions in diamonds,
built from the scientific literature.

**Start here:** [docs/brief.md](docs/brief.md) (requirements) ·
[docs/roadmap.md](docs/roadmap.md) (plan and status) ·
[docs/decisions/](docs/decisions/README.md) (design decisions) ·
[docs/inputs-needed.md](docs/inputs-needed.md) (what's needed from you) ·
[docs/log.md](docs/log.md) (progress)

## Using this folder
- **Obsidian:** open this folder as a vault ("Open folder as vault"). The docs use standard
  Markdown links, so they also render on GitHub and in Claude Code.
- **Claude Code:** start a session in this folder; `CLAUDE.md` gives Claude the project
  rules automatically. Name the roadmap item you're working on.
- **Demo:** `.venv/bin/python -I scripts/build_demo_db.py`, then
  `.venv/bin/datasette demo/demo.sqlite --metadata demo/metadata.json --static assets:demo/static/ --port 8001 --setting default_facet_size 10`
  and open http://127.0.0.1:8001 (Claude can run these for you).
- **Git:** commit after each session. `papers/` (PDFs, supplements) is never committed.
