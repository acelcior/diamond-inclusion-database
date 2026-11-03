"""Export the gold database to site/data/*.json for the website (site/index.html).

Run from the project folder after any data change:  python3 -I scripts/export_site.py
Reads only the database (built by scripts/build_gold.py), so new papers appear without changes here.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_gold  # noqa: E402

OUT = ROOT / "site" / "data"
SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
LABEL = {"FeOT": "FeO (total Fe)", "oxide_total": "Total"}


def status_label(s):
    return {"pending_review": "not yet reviewed"}.get(s, s.replace("_", " "))


def label(code):
    return LABEL.get(code, code.translate(SUB))


def ref(page, table, row, col):
    return ", ".join(x for x in [f"p. {page}" if page else None, table, " ".join(filter(None, [row, col]))] if x)


def main():
    db, _ = build_gold.build()  # all papers in gold/
    q = lambda sql, *a: db.execute(sql, a).fetchall()

    # oxide columns in vocab order, only those that hold data
    present = {c for (c,) in q("SELECT DISTINCT quantity_code FROM measured_value")}
    oxides = [c for (c,) in q("SELECT code FROM quantity WHERE kind = 'oxide' OR code = 'oxide_total' ORDER BY rowid")
              if c in present]

    def assertion(col, subject_id, prop):
        r = q(f"SELECT value_text FROM assertion WHERE {col} = ? AND property_code = ? ORDER BY id DESC", subject_id, prop)
        return r[0][0] if r else None

    inclusions = []
    for (iid, pub, short, sample, loc, phase, printed, status, did, page, table, row, col) in q("""
            SELECT i.id, p.id, p.short_ref, s.identifier || COALESCE(i.reported_label, ''), d.reported_locality,
                   ph.name, i.reported_phase,
                   i.workflow_status, d.id, e.page, e.table_label, e.row_label, e.column_label
            FROM inclusion_observation i JOIN publication p ON p.id = i.publication_id
            LEFT JOIN diamond_observation d ON d.id = i.diamond_observation_id
            LEFT JOIN specimen_identifier s ON s.diamond_observation_id = d.id
            LEFT JOIN phase ph ON ph.id = i.phase_id
            JOIN evidence e ON e.id = i.evidence_id ORDER BY i.id"""):
        r = {"id": iid, "source_id": pub, "source": short, "sample": sample, "locality": loc, "mineral": phase,
             "mineral_printed": printed, "paragenesis": assertion("inclusion_observation_id", iid, "paragenesis"),
             "touching": {"y": "yes", "n": "no"}.get(assertion("inclusion_observation_id", iid, "touching")),
             "assemblage": assertion("diamond_observation_id", did, "reported_assemblage"),
             "status": status_label(status), "where": ref(page, table, row, col), "_txt": {}, "_st": {}}
        m = q("SELECT id, method_code FROM measurement WHERE inclusion_observation_id = ?", iid)
        r["method"] = m[0][1] if m else None
        r["analysed"] = "yes" if m else "no"
        for code, text, value, vstatus in (q("""SELECT quantity_code, original_text, value, value_status
                                               FROM measured_value WHERE measurement_id = ?""", m[0][0]) if m else []):
            r[code] = value
            r["_txt"][code] = text
            if vstatus != "reported":
                r["_st"][code] = vstatus.replace("_", " ")
        inclusions.append(r)

    estimates = []
    for (sid, pub, short, page, table, row, qcode, text, value, unit, method, assumptions, dstatus) in q("""
            SELECT s.id, p.id, p.short_ref, e.page, e.table_label, e.row_label, d.quantity_code, d.original_text,
                   d.value, d.original_unit, d.method, d.assumptions, d.workflow_status
            FROM derived_parameter d JOIN inclusion_set s ON s.id = d.inclusion_set_id
            JOIN publication p ON p.id = s.publication_id JOIN evidence e ON e.id = d.evidence_id ORDER BY d.id"""):
        members = q("""SELECT ph.name, i.diamond_observation_id,
                              (SELECT value_text FROM assertion a WHERE a.inclusion_observation_id = i.id
                               AND a.property_code = 'touching' ORDER BY a.id DESC LIMIT 1)
                       FROM inclusion_set_member m JOIN inclusion_observation i ON i.id = m.inclusion_observation_id
                       LEFT JOIN phase ph ON ph.id = i.phase_id WHERE m.inclusion_set_id = ? ORDER BY i.id""", sid)
        touch = {t for _, _, t in members}
        samples = q("SELECT identifier FROM specimen_identifier WHERE diamond_observation_id = ?", members[0][1])
        estimates.append({
            "source_id": pub, "source": short, "sample": samples[0][0] if samples else None,
            "assemblage": " + ".join(n for n, _, _ in members),
            "touching": "yes" if touch == {"y"} else "no" if touch == {"n"} else "mixed",
            "paragenesis": assertion("inclusion_set_id", sid, "paragenesis"),
            "estimate": {"T_equilibration": "Temperature", "P_equilibration": "Pressure"}.get(qcode, qcode),
            "value": value, "value_text": text, "unit": {"degC": "°C"}.get(unit, unit), "method": method,
            "assumption": assumptions, "status": status_label(dstatus), "where": ref(page, table, row, None)})

    sources = []
    for (pid, doi, citation, short, notes) in q("SELECT id, doi, citation, short_ref, notes FROM publication ORDER BY year, short_ref"):
        n = lambda sql: q(sql, pid)[0][0]
        sources.append({
            "id": pid, "doi": doi, "citation": citation, "short": short, "notes": notes,
            "diamonds": n("SELECT COUNT(*) FROM diamond_observation WHERE publication_id = ?"),
            "inclusions": n("SELECT COUNT(*) FROM inclusion_observation WHERE publication_id = ?"),
            "analyses": n("""SELECT COUNT(*) FROM measurement m JOIN inclusion_observation i
                             ON i.id = m.inclusion_observation_id WHERE i.publication_id = ?"""),
            "estimates": n("""SELECT COUNT(*) FROM derived_parameter d JOIN evidence e ON e.id = d.evidence_id
                              WHERE e.publication_id = ?"""),
            "status": sorted({status_label(s) for (s,) in q(
                "SELECT DISTINCT workflow_status FROM inclusion_observation WHERE publication_id = ?", pid)}),
        })

    meta = {"oxides": [{"code": c, "label": label(c)} for c in oxides],
            "counts": {"papers": len(sources), "diamonds": sum(s["diamonds"] for s in sources),
                       "inclusions": len(inclusions), "analysed": sum(r["analysed"] == "yes" for r in inclusions),
                       "values": q("SELECT COUNT(*) FROM measured_value")[0][0], "estimates": len(estimates)}}

    OUT.mkdir(parents=True, exist_ok=True)
    for name, obj in [("inclusions", inclusions), ("estimates", estimates), ("sources", sources), ("meta", meta)]:
        (OUT / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(meta["counts"], [o["code"] for o in meta["oxides"]])


if __name__ == "__main__":
    main()
