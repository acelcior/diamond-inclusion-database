"""Portability check (D-004): load schema/*.sql into a throwaway PostgreSQL, copy every row of a fresh
SQLite build into it, and confirm all tables, views, types, CHECKs and foreign keys accept the real data.

Run from the project folder:  python3 -I scripts/check_postgres.py
Needs PostgreSQL 17 from Homebrew (brew install postgresql@17). Starts its own temporary server, stops it after;
nothing is left running and no data leaves this Mac.
"""
import csv
import graphlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_gold  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PG = Path("/opt/homebrew/opt/postgresql@17/bin")
ENV = {**os.environ, "LC_ALL": "en_US.UTF-8"}  # postgres refuses to start without a valid locale


def load_order(db):
    """Parents before children, so foreign keys are checked as rows arrive."""
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
    deps = {t: {r[2] for r in db.execute(f"PRAGMA foreign_key_list({t})")} - {t} for t in tables}
    return list(graphlib.TopologicalSorter(deps).static_order())


def main():
    db, _ = build_gold.build()  # fresh in-memory build from the source files, compilations included
    order = load_order(db)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        run = lambda *a: subprocess.run(a, env=ENV, check=True, capture_output=True, text=True)
        run(PG / "initdb", "-D", tmp / "data", "-A", "trust", "-U", "pg")
        run(PG / "pg_ctl", "-D", tmp / "data", "-o", f"-k {tmp} -c listen_addresses=''", "-l", tmp / "log", "-w", "start")
        try:
            script = ["\\set ON_ERROR_STOP 1"] + [f"\\i '{f}'" for f in sorted((ROOT / "schema").glob("*.sql"))]
            counts = {}
            for t in order:
                cur = db.execute(f"SELECT * FROM {t} ORDER BY rowid")  # rowid order: self-referencing parents first
                cols = [d[0] for d in cur.description]
                path = tmp / f"{t}.csv"
                with path.open("w", newline="") as f:
                    w = csv.writer(f, quoting=csv.QUOTE_NOTNULL)  # unquoted empty = NULL, quoted "" = empty text
                    rows = cur.fetchall()
                    w.writerows(rows)
                counts[t] = len(rows)
                script.append(f"\\copy {t} ({', '.join(cols)}) FROM '{path}' WITH (FORMAT csv)")
            script += [f"SELECT '{t}', COUNT(*) FROM {t};" for t in order]
            script += ["SELECT 'view:' || table_name, 0 FROM information_schema.views WHERE table_schema = 'public';"]
            (tmp / "load.sql").write_text("\n".join(script) + "\n")
            res = subprocess.run([PG / "psql", "-h", tmp, "-U", "pg", "-d", "postgres", "-At", "-F", "\t",
                                  "-f", tmp / "load.sql"], env=ENV, capture_output=True, text=True)
        finally:
            run(PG / "pg_ctl", "-D", tmp / "data", "-m", "fast", "stop")
    if res.returncode:
        print("FAILED — PostgreSQL rejected something:\n" + res.stderr.strip())
        return 1
    got = dict(line.split("\t") for line in res.stdout.split("\n") if "\t" in line)
    views = sorted(k[5:] for k in got if k.startswith("view:"))
    bad = {t: (n, got.get(t)) for t, n in counts.items() if str(n) != got.get(t)}
    print(f"{len(order)} tables, {sum(counts.values())} rows copied; views: {', '.join(views)}")
    for t, (n, g) in bad.items():
        print(f"  MISMATCH {t}: sqlite {n}, postgres {g}")
    print("FAILED" if bad else "OK — schema and data load into PostgreSQL unchanged")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
