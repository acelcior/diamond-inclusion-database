"""Build gold/gold.sqlite from schema + vocab/ + gold/phillips-2004/, run the checks, write the review page.

Run from the project folder:  python3 -I scripts/build_gold.py
Output: gold/gold.sqlite (not committed) and gold/phillips-2004/README.md (the review page).
"""
import csv
import json
import random
import sqlite3
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "001_core.sql"
VOCAB = ROOT / "vocab"
PAPER = ROOT / "gold" / "phillips-2004"
DB_PATH = ROOT / "gold" / "gold.sqlite"

OXIDES = ["SiO2", "Al2O3", "TiO2", "Cr2O3", "FeO", "MnO", "NiO", "MgO", "CaO", "Na2O", "K2O", "V2O5", "ZnO", "Total"]
SUITE_TO_T4 = {"Per (hz)": "Harzburgitic", "Per (lhz)": "Lherzolitic", "Ecl": "Eclogitic", "Web": "Websteritic"}


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def insert(db, table, **cols):
    cols = {k: v for k, v in cols.items() if v is not None}
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    return db.execute(sql, list(cols.values())).lastrowid


def load_vocab(db):
    for name in ["unit", "method", "quantity", "property"]:
        for r in rows(VOCAB / f"{name}.csv"):
            insert(db, name, **{k: (v or None) for k, v in r.items()})
    for r in rows(VOCAB / "phase.csv"):
        insert(db, "phase", **{k: (v or None) for k, v in r.items()})
    ids = dict(db.execute("SELECT name, id FROM phase"))
    for r in rows(VOCAB / "phase_name_variant.csv"):
        insert(db, "phase_name_variant", phase_id=ids[r["phase"]], variant=r["variant"],
               variant_type=r["variant_type"], notes=r["notes"] or None)


def phase_lookup(db):
    names = {n.lower(): i for n, i in db.execute("SELECT name, id FROM phase")}
    names.update({v.lower(): i for v, i in db.execute("SELECT variant, phase_id FROM phase_name_variant")})
    return lambda printed: names.get(printed.strip().lower())


# shortcut: this loader knows the layout of Phillips et al. (2004) Tables 3 and 4; generalise it
# (or move to extraction/schema.json, Phase 3) once the second seed paper shows what varies.
def load_phillips(db):
    src = json.loads((PAPER / "source.json").read_text())
    t3, t4 = rows(PAPER / "table3.csv"), rows(PAPER / "table4.csv")
    phase_id = phase_lookup(db)
    flags = []  # (kind, where, message) for the review page

    pub = insert(db, "publication", **src["publication"])
    sf = insert(db, "source_file", publication_id=pub, **src["source_file"])
    run = insert(db, "import_run", run_type="claude_extraction", started_at=date.today().isoformat(),
                 tool="extraction/parse_phillips_2004.py (pdftotext -layout) + scripts/build_gold.py",
                 operator="Claude (Claude Code); values to be verified by a curator")

    def evidence(**kw):
        return insert(db, "evidence", publication_id=pub, source_file_id=sf, source_type="paper",
                      import_run_id=run, **kw)

    loc = src["locality"]
    loc_ev = evidence(**loc["evidence"])
    loc_id = insert(db, "locality", name=loc["name"], locality_type=loc["locality_type"],
                    country_code=loc["country_code"], precision_class=loc["precision_class"], notes=loc["notes"])

    diamonds = {}

    def diamond(sample, ev):
        if sample not in diamonds:
            d = insert(db, "diamond_observation", publication_id=pub, evidence_id=ev,
                       reported_locality=loc["reported"], import_run_id=run)
            insert(db, "specimen_identifier", diamond_observation_id=d, identifier=sample, id_type="author_sample")
            insert(db, "assertion", diamond_observation_id=d, property_code="collection_locality",
                   value_text=loc["reported"], value_locality_id=loc_id, asserted_by="authors",
                   value_status="reported", derivation="reported", evidence_id=loc_ev)
            diamonds[sample] = d
        return diamonds[sample]

    def inclusion(d, printed, ev, notes, touching=None):
        pid = phase_id(printed)
        i = insert(db, "inclusion_observation", publication_id=pub, evidence_id=ev, diamond_observation_id=d,
                   reported_phase=printed, phase_id=pid, phase_match_status="mapped" if pid else "unmapped",
                   import_run_id=run, notes=notes)
        if pid is None:
            flags.append(("unmapped phase", notes, f"'{printed}' is not in vocab/"))
        if touching:
            insert(db, "assertion", inclusion_observation_id=i, property_code="touching", value_text=touching,
                   asserted_by="authors", value_status="reported", derivation="reported", evidence_id=ev)
        return i

    # ---- Table 3: one inclusion observation + one EPMA measurement per printed column ----
    t3_cfg = src["table3"]
    printed = {}      # sample -> [(inclusion id, phase id, touching)]
    listed_only = {}  # sample -> [(inclusion id, phase id)] phases in the assemblage with no printed column
    epma = src["epma"]
    for r in t3:
        where = f"Table 3, p. {r['page']}, {r['sample_no']} {r['mineral']} (block {r['block']}, column {r['column']})"
        ev = evidence(page=r["page"], table_label=t3_cfg["label"], row_label=r["sample_no"],
                      column_label=f"{r['mineral']} (block {r['block']}, column {r['column']})",
                      excerpt=f"Sample no. {r['sample_no']}; Mineral {r['mineral']}; Suite {r['suite']}; "
                              f"Assemblage {r['assemblage']}; Touching {r['touching']}")
        first = r["sample_no"] not in diamonds
        d = diamond(r["sample_no"], ev)
        if first:
            insert(db, "assertion", diamond_observation_id=d, property_code="reported_assemblage",
                   value_text=r["assemblage"], asserted_by="authors", value_status="reported",
                   derivation="reported", evidence_id=ev)
        inc = inclusion(d, r["mineral"], ev, where, touching=r["touching"])
        printed.setdefault(r["sample_no"], []).append((inc, phase_id(r["mineral"]), r["touching"]))
        insert(db, "assertion", inclusion_observation_id=inc, property_code="paragenesis", value_text=r["suite"],
               asserted_by="authors", value_status="reported", derivation="interpreted", evidence_id=ev)
        m = insert(db, "measurement", inclusion_observation_id=inc, method_code="EPMA", spot_label=epma["spot_label"],
                   conditions=epma["conditions"], evidence_id=ev, import_run_id=run,
                   notes=f"Analytical conditions: p. {epma['evidence']['page']}")
        for col in OXIDES:
            text = r[col]
            status = t3_cfg["notation"].get(text)
            if status is None:
                try:
                    value, status = float(text), "reported"
                except ValueError:
                    sys.exit(f"Unrecognised notation {text!r} at {where}, {col}: add it to source.json")
            else:
                value = None
            if status == "ambiguous":
                flags.append(("ambiguous notation", where, f"{col} = '{text}': {t3_cfg['notation_notes'][text]}"))
            insert(db, "measured_value", measurement_id=m, quantity_code=t3_cfg["column_quantity"].get(col, col),
                   original_text=text, original_unit="wt%", value=value, value_status=status,
                   derivation="calculated_by_authors" if col == "Total" else "reported")

    for sample, cols in printed.items():
        assemblage = db.execute("SELECT value_text FROM assertion WHERE property_code = 'reported_assemblage' "
                                "AND diamond_observation_id = ?", (diamonds[sample],)).fetchone()[0]
        listed = [p.strip() for p in assemblage.split(",") if p.strip()]
        remaining = [c[1] for c in cols]
        for p in listed:
            pid = phase_id(p)
            if pid in remaining:
                remaining.remove(pid)
            else:  # listed in the assemblage, no analysis printed
                ev = db.execute("SELECT evidence_id FROM inclusion_observation WHERE id = ?", (cols[0][0],)).fetchone()[0]
                inc = inclusion(diamonds[sample], p, ev, f"Table 3, {sample}: listed in the assemblage, no analysis printed")
                listed_only.setdefault(sample, []).append((inc, pid))

    # ---- Table 4: thermobarometry on co-existing assemblages, stored on inclusion sets ----
    t4_cfg = src["table4"]
    for r in t4:
        where = f"Table 4, p. {r['page']}, {r['sample_no']} ({r['group']})"
        shown = [r[c] for c in ["T_gt_opx", "P_gt_opx_b", "P_gt_opx_c", "T_gt_ol", "P_gt_ol", "T_gt_cpx", "P_gt_cpx"]]
        ev = evidence(page=r["page"], table_label=t4_cfg["label"], row_label=f"{r['sample_no']} ({r['group']})",
                      excerpt=" ".join([r["sample_no"], r["paragenesis"], r["assemblage"]] + [v for v in shown if v]))
        d = diamond(r["sample_no"], ev)
        want_touch = "y" if r["group"] == "touching" else "n"
        pool = [c for c in printed.get(r["sample_no"], []) if c[2] == want_touch]
        spare = list(listed_only.get(r["sample_no"], []))
        members = []
        for p in [p.strip() for p in r["assemblage"].split("+")]:
            pid = phase_id(p)
            hit = next((c for c in pool if c[1] == pid), None)
            if hit:
                pool.remove(hit)
                members.append(hit[0])
                continue
            hit = next((c for c in spare if c[1] == pid), None)
            if hit:  # e.g. DP364 chromite: listed in Table 3, touching status given only here
                spare.remove(hit)
                members.append(hit[0])
                insert(db, "assertion", inclusion_observation_id=hit[0], property_code="touching", value_text=want_touch,
                       asserted_by="authors", value_status="reported", derivation="reported", evidence_id=ev)
                continue
            if r["sample_no"] in printed:
                flags.append(("Table 3/4 mismatch", where, f"no Table 3 {p} with touching = {want_touch}; added from Table 4"))
            members.append(inclusion(d, p, ev, f"{where}: from the co-existing assemblage, no analysis printed",
                                     touching=want_touch))
        s = insert(db, "inclusion_set", publication_id=pub, evidence_id=ev,
                   label=f"{r['sample_no']} {r['group']} {r['assemblage']}",
                   description="Co-existing inclusion assemblage used for thermobarometry (Table 4)")
        for i in members:
            insert(db, "inclusion_set_member", inclusion_set_id=s, inclusion_observation_id=i)
        t3_suite = {db.execute("SELECT value_text FROM assertion WHERE property_code = 'paragenesis' "
                               "AND inclusion_observation_id = ?", (i,)).fetchone() for i in members} - {None}
        for (suite,) in t3_suite:
            if SUITE_TO_T4.get(suite) != r["paragenesis"]:
                flags.append(("paragenesis differs", where, f"Table 3 says '{suite}', Table 4 says '{r['paragenesis']}'"))
        insert(db, "assertion", inclusion_set_id=s, property_code="paragenesis", value_text=r["paragenesis"],
               asserted_by="authors", value_status="reported", derivation="interpreted", evidence_id=ev)
        for col, spec in t4_cfg["columns"].items():
            if not r[col]:
                continue
            assumptions = None
            if "pressure_column" in spec:
                p = r[spec["pressure_column"]]
                assumptions = f"{t4_cfg['assumed_pressure_note']}; printed P = {p} GPa"
                if p != "5.0":
                    flags.append(("assumed pressure", where, f"P printed as '{p}', note e says 5.0 GPa"))
            insert(db, "derived_parameter", inclusion_set_id=s, quantity_code=spec["quantity"], original_text=r[col],
                   original_unit=spec["unit"], value=float(r[col]), method=spec["method"], assumptions=assumptions,
                   derivation="calculated_by_authors", evidence_id=ev)
        if r["T_gt_opx"] and not r["P_gt_opx_b"]:
            flags.append(("blank cell", where, f"Brey & Köhler P is blank while T = {r['T_gt_opx']} and MacGregor "
                          f"P = {r['P_gt_opx_c'] or 'blank'}; the text quotes 7.6 GPa for DP497. Not filled."))
    return flags


def apply_review(db):
    """Set every record of the paper to the curator's recorded review outcome (source.json "review")."""
    review = json.loads((PAPER / "source.json").read_text()).get("review")
    if not review:
        return
    ev = "SELECT id FROM evidence"  # shortcut: one paper in the db; filter by publication_id when there are more
    for t in ["diamond_observation", "inclusion_observation", "measurement", "derived_parameter", "assertion"]:
        db.execute(f"UPDATE {t} SET workflow_status = ? WHERE evidence_id IN ({ev})", (review["workflow_status"],))
    db.execute(f"UPDATE measured_value SET workflow_status = ? WHERE measurement_id IN "
               f"(SELECT id FROM measurement WHERE evidence_id IN ({ev}))", (review["workflow_status"],))


def build(path=":memory:"):
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA.read_text())
    load_vocab(db)
    flags = load_phillips(db)
    apply_review(db)
    db.commit()
    return db, flags


# ---------------- checks ----------------

def checks(db):
    out = {}
    # analytical totals: printed Total vs sum of the printed oxides
    sums = db.execute("""
        SELECT m.id, e.page, e.row_label, e.column_label, t.original_text, t.value,
               ROUND(SUM(CASE WHEN v.quantity_code <> 'oxide_total' THEN v.value END), 2)
        FROM measurement m JOIN evidence e ON e.id = m.evidence_id
        JOIN measured_value v ON v.measurement_id = m.id
        JOIN measured_value t ON t.measurement_id = m.id AND t.quantity_code = 'oxide_total'
        GROUP BY m.id ORDER BY m.id""").fetchall()
    out["sum_mismatch"] = [s for s in sums if abs(s[6] - s[5]) > 0.05]
    out["max_sum_diff"] = max(abs(s[6] - s[5]) for s in sums)
    out["total_range"] = [s for s in sums if not 98.0 <= s[5] <= 101.5]
    out["below_dl"] = db.execute("""SELECT quantity_code, COUNT(*) FROM measured_value
        WHERE quantity_code IN ('Na2O', 'K2O') AND value < 0.02 GROUP BY quantity_code""").fetchall()
    out["status_counts"] = db.execute("""SELECT value_status, COUNT(*) FROM measured_value
        GROUP BY value_status ORDER BY 2 DESC""").fetchall()
    out["untraceable"] = db.execute("""SELECT COUNT(*) FROM measured_value v
        JOIN measurement m ON m.id = v.measurement_id JOIN evidence e ON e.id = m.evidence_id
        WHERE e.page IS NULL OR e.table_label IS NULL OR v.original_text IS NULL""").fetchone()[0]
    out["counts"] = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in
                     ["diamond_observation", "inclusion_observation", "measurement", "measured_value",
                      "inclusion_set", "derived_parameter", "assertion", "evidence"]}
    out["unanalysed"] = db.execute("""SELECT COUNT(*) FROM inclusion_observation i
        WHERE NOT EXISTS (SELECT 1 FROM measurement m WHERE m.inclusion_observation_id = i.id)""").fetchone()[0]
    return out


# ---------------- review page ----------------

def md_table(header, body):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in body]
    return "\n".join(lines)


def spot_checks(db, n_values=20, n_derived=5):
    rng = random.Random(2004)  # fixed seed: the same list every build
    vals = db.execute("""SELECT e.page, e.table_label, e.row_label, e.column_label, v.quantity_code, v.original_text
        FROM measured_value v JOIN measurement m ON m.id = v.measurement_id JOIN evidence e ON e.id = m.evidence_id
        ORDER BY v.id""").fetchall()
    der = db.execute("""SELECT e.page, e.table_label, e.row_label, d.method, d.original_text, d.original_unit
        FROM derived_parameter d JOIN evidence e ON e.id = d.evidence_id ORDER BY d.id""").fetchall()
    picks = [(p, t, f"{r} {c}", q, x) for p, t, r, c, q, x in rng.sample(vals, n_values)]
    picks += [(p, t, r, m, f"{x} {u}") for p, t, r, m, x, u in rng.sample(der, n_derived)]
    return sorted(picks, key=lambda x: (x[0], x[1], x[2]))


def write_review(db, flags, res):
    c = res["counts"]
    q = lambda sql: db.execute(sql).fetchall()
    data = q("""SELECT e.page, e.row_label, i.reported_phase, a.value_text, t.value_text,
        """ + ", ".join(f"MAX(CASE WHEN v.quantity_code = '{k}' THEN v.original_text END)" for k in
                        ["SiO2", "TiO2", "Al2O3", "Cr2O3", "FeOT", "MnO", "NiO", "MgO", "CaO", "Na2O", "K2O", "V2O5", "ZnO", "oxide_total"]) + """
        FROM inclusion_observation i JOIN measurement m ON m.inclusion_observation_id = i.id
        JOIN evidence e ON e.id = m.evidence_id JOIN measured_value v ON v.measurement_id = m.id
        JOIN assertion a ON a.inclusion_observation_id = i.id AND a.property_code = 'paragenesis'
        JOIN assertion t ON t.inclusion_observation_id = i.id AND t.property_code = 'touching'
        GROUP BY i.id ORDER BY i.id""")
    pt = q("""SELECT s.label, d.method, d.original_text || ' ' || d.original_unit, COALESCE(d.assumptions, '')
        FROM derived_parameter d JOIN inclusion_set s ON s.id = d.inclusion_set_id ORDER BY d.id""")
    review = json.loads((PAPER / "source.json").read_text()).get("review")
    decide = lambda where: next((d for k, d in (review or {}).get("decisions", {}).items() if k in where), "open")
    comp_rows = rows(PAPER / "compilation-check.csv") if (PAPER / "compilation-check.csv").exists() else []
    flags = flags + [("compilation disagrees", f"Table 3, p. {r['page']}, {r['sample_no']} {r['mineral']}",
                      f"paragenesis: {r['paragenesis_note']} (compilation row {r['compilation_row']})")
                     for r in comp_rows if r["paragenesis_note"]]

    L = [
        "# Gold standard: Phillips et al. (2004)",
        "",
        "> Phillips, Harris & Viljoen (2004), *Lithos* 77, 155–179, "
        "[doi:10.1016/j.lithos.2004.04.005](https://doi.org/10.1016/j.lithos.2004.04.005). "
        "First seed paper (A1). " + (f"**Status: {review['workflow_status']}** by {review['reviewer']} on "
                                      f"{review['date']}. {review['method']}" if review else
                                      "**Status: extracted, awaiting your review** (every record is `pending_review`)."),
        "",
        "Generated by `scripts/build_gold.py` from [table3.csv](table3.csv), [table4.csv](table4.csv) and "
        "[source.json](source.json); do not edit by hand. Values below are read back out of the database.",
        "",
        "## What was extracted",
        "",
        md_table(["Records", "Count"], [
            ["Host diamonds (one per sample no.)", c["diamond_observation"]],
            ["Inclusion observations", c["inclusion_observation"]],
            ["  of which analysed in Table 3", c["measurement"]],
            ["  of which named only (Table 4 assemblage or Table 3 assemblage list)", res["unanalysed"]],
            ["EPMA values (one per oxide per inclusion)", c["measured_value"]],
            ["Thermobarometry assemblages (inclusion sets)", c["inclusion_set"]],
            ["Temperatures and pressures", c["derived_parameter"]],
            ["Assertions (paragenesis, touching, assemblage, locality)", c["assertion"]],
        ]),
        "",
        "- **Table 3** (pp. 160–161): 80 averaged EPMA analyses from 36 diamonds, with suite, touching status "
        "and assemblage. `FeO` is stored as total iron (`FeOT`), as the table footnote says.",
        "- **Table 4** (p. 171): temperatures and pressures for 50 co-existing assemblages, each stored on the set of "
        "inclusions it was calculated from, with the calibration. Pressures printed as 5.0 GPa for garnet–olivine "
        "and garnet–clinopyroxene are the authors' *assumed* pressure (note e), stored as an assumption, not a result. "
        "Table 4 inclusions were matched to Table 3 columns by sample number, mineral and touching status.",
        "- **Locality:** every diamond is `De Beers Pool` (pooled production of four Kimberley mines, p. 158); "
        "the mine of a single diamond is not reported, and no coordinates are entered.",
        "",
        "**Not extracted, and why:**",
        "- Table 1 summarises *earlier* studies of other collections, so it is not this paper's observation.",
        "- Table 2 gives counts of assemblages (group-level data; waits for D-006).",
        "- The complete dataset is in the *Lithos* online data repository (p. 159). We don't have it. "
        "Table 3 is described as representative analyses only.",
        "- Figures and text-only values (e.g. Mg-number ranges) were not extracted.",
        "",
        "## Automatic checks",
        "",
        f"- **Traceability:** {c['measured_value'] - res['untraceable']} of {c['measured_value']} values have "
        "page, table, column and original text.",
        (f"- **Totals add up:** for all {c['measurement']} analyses the printed Total equals the sum of the printed "
         "oxides (to 0.01 wt%). A value read into the wrong cell would break this." if not res["sum_mismatch"] else
         "- **Totals do not add up** for: " + ", ".join(f"{r[2]} {r[3]} (printed {r[4]}, sum {r[6]:.2f})"
                                                       for r in res["sum_mismatch"]) + "."),
        "- **Totals outside 98–101.5 wt%:** "
        + ", ".join(f"{r[2]} {r[3].split(' (')[0]} {r[4]}" for r in res["total_range"])
        + ". The magnesite total of 50.52 is expected: CO₂ is not analysed by EPMA. "
        "The others are as printed.",
        "- **Value status:** " + ", ".join(f"{n} {s}" for s, n in res["status_counts"]) + ". "
        "`na` (not analysed, per footnote) = `not_measured`; `nd` (not defined in this table) = `ambiguous`.",
        "- **Below typical detection limit:** " + ", ".join(f"{n} {k} values" for k, n in res["below_dl"])
        + " are printed below the stated typical 0.02 wt% limit for Na₂O and K₂O. They are kept as printed (`reported`).",
        "",
        "**Flagged items and the decision taken:**" if review else "**Flagged for your decision:**",
        "",
        md_table(["Kind", "Where", "What", "Decision"],
                 [(*f, decide(f[1])) for f in flags] or [["—", "—", "none", ""]]),
        "",
        "## Compilation cross-check",
        "",
        (f"Of {len(comp_rows)} analyses: " + ", ".join(f"{n} {k}" for k, n in Counter(r["verdict"] for r in comp_rows).most_common())
         + ". Details and what it means: [compilation-check.md](compilation-check.md).") if comp_rows else "Not run yet.",
        "",
        "## Spot-check list",
        "",
        ("Checked against the PDF: all matched. " if review else
         "Open the PDF at each page and check the printed cell. Tick when it matches; note any that don't. ")
        + "(Random sample with a fixed seed, so the list stays the same each build.)",
        "",
        md_table(["✓", "Page", "Table", "Row / column", "Quantity", "Printed"],
                 [["☑" if review else "☐", *r] for r in spot_checks(db)]),
        "",
        "## Table 3 as stored",
        "",
        md_table(["p.", "Sample", "Mineral", "Suite", "Touch.", "SiO₂", "TiO₂", "Al₂O₃", "Cr₂O₃", "FeOT", "MnO", "NiO",
                  "MgO", "CaO", "Na₂O", "K₂O", "V₂O₅", "ZnO", "Total"], data),
        "",
        "## Table 4 as stored",
        "",
        md_table(["Assemblage (inclusion set)", "Method", "Value", "Assumption"], pt),
        "",
    ]
    (PAPER / "README.md").write_text("\n".join(L), encoding="utf-8")


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    db, flags = build(str(DB_PATH))
    res = checks(db)
    write_review(db, flags, res)
    print(json.dumps(res["counts"], indent=1))
    print(f"max total diff {res['max_sum_diff']:.3f}; {len(res['sum_mismatch'])} sum mismatches; "
          f"{len(res['total_range'])} totals out of range; {len(flags)} flags; {res['untraceable']} untraceable")
    for f in flags:
        print(" ", *f)


if __name__ == "__main__":
    main()
