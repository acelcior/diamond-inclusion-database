"""Export the gold database to site/data/*.json for the website (site/index.html).

Run from the project folder after any data change:  python3 -I scripts/export_site.py
Reads only the database (built by scripts/build_gold.py), so new papers appear without changes here.
"""
import csv
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
    db, papers = build_gold.build()  # all papers in gold/
    codes_by_pub = {pp["pub"]: json.loads((pp["dir"] / "source.json").read_text()).get("codes", {}) for pp in papers.values()}
    q = lambda sql, *a: db.execute(sql, a).fetchall()

    # oxide columns in vocab order, only those that hold data
    present = {c for (c,) in q("SELECT DISTINCT quantity_code FROM measured_value")}
    oxides = [c for (c,) in q("SELECT code FROM quantity WHERE kind = 'oxide' OR code = 'oxide_total' ORDER BY rowid")
              if c in present]

    def assertion(col, subject_id, prop):
        r = q(f"SELECT value_text FROM assertion WHERE {col} = ? AND property_code = ? ORDER BY id DESC", subject_id, prop)
        return r[0][0] if r else None

    conf = {("i", i): (lvl, why) for i, lvl, why in q("""SELECT inclusion_observation_id, level, reasons
              FROM extraction_confidence WHERE inclusion_observation_id IS NOT NULL""")}
    conf.update({("d", d): (lvl, why) for d, lvl, why in q("""SELECT derived_parameter_id, level, reasons
              FROM extraction_confidence WHERE derived_parameter_id IS NOT NULL""")})

    def decode(pub, prop, code):
        legend = codes_by_pub.get(pub, {}).get(prop, {})
        if not code or not legend:
            return code
        return "/".join(legend.get(c, c) for c in code.split("/")) + f" ({code})"

    COUNTRY = {"ZA": "South Africa", "RU": "Russia", "GN": "Guinea"}
    short_of = dict(q("SELECT id, short_ref FROM publication"))
    pub_of_dia = dict(q("SELECT id, publication_id FROM diamond_observation"))
    cluster = dict(q("SELECT diamond_observation_id, cluster_id FROM diamond_cluster"))
    members = {}
    for d, c in cluster.items():
        members.setdefault(c, []).append(d)

    def dia_prop(did, prop, decoded=True):
        """A diamond-level value from this record, else from a linked record of the same diamond (named)."""
        if did is None:
            return None
        for other in [did] + [x for x in members.get(cluster.get(did), []) if x != did]:
            v = assertion("diamond_observation_id", other, prop)
            if v:
                pub = pub_of_dia[other]
                v = decode(pub, prop, v) if decoded else v
                return v if other == did else f"{v} [{short_of[pub]}]"
        return None

    def country(did):
        r = q("""SELECT l.country_code FROM assertion a JOIN locality l ON l.id = a.value_locality_id
                 WHERE a.diamond_observation_id = ? AND a.property_code = 'collection_locality'""", did) if did else []
        return COUNTRY.get(r[0][0], r[0][0]) if r and r[0][0] else None

    def depth(col, sid):
        r = q(f"""SELECT value_text, notes FROM assertion WHERE {col} = ? AND property_code = 'formation_depth_domain'""", sid)
        return r[0] if r else (None, None)

    def clean_notes(n):
        # inclusion notes start with where it was printed (shown elsewhere); keep only what follows
        if not n:
            return None
        n = n.split("; ", 1)[1] if n.startswith("Table") and "; " in n else (None if n.startswith("Table") else n)
        return n or None

    inclusions = []
    for (iid, pub, short, sample, loc, phase, printed, status, did, page, table, row, col, inc_label, notes) in q("""
            SELECT i.id, p.id, p.short_ref, s.identifier, d.reported_locality,
                   ph.name, i.reported_phase,
                   i.workflow_status, d.id, e.page, e.table_label, e.row_label, e.column_label, i.reported_label, i.notes
            FROM inclusion_observation i JOIN publication p ON p.id = i.publication_id
            LEFT JOIN diamond_observation d ON d.id = i.diamond_observation_id
            LEFT JOIN specimen_identifier s ON s.diamond_observation_id = d.id
            LEFT JOIN phase ph ON ph.id = i.phase_id
            JOIN evidence e ON e.id = i.evidence_id ORDER BY i.id"""):
        dd, basis = depth("inclusion_observation_id", iid)
        if dd is None:
            dd, basis = depth("diamond_observation_id", did) if did else (None, None)
        r = {"id": iid, "source_id": pub, "source": short, "diamond_id": sample,
             "inclusion_id": f"{sample}{inc_label}" if inc_label else None, "locality": loc, "mineral": phase,
             "country": country(did), "region": dia_prop(did, "region"), "host_rock": dia_prop(did, "host_rock"),
             "diamond_type": dia_prop(did, "diamond_type"), "diamond_morphology": dia_prop(did, "shape"),
             "color": dia_prop(did, "colour"), "formation_depth_domain": dd, "depth_interpretation_basis": basis,
             "notes": clean_notes(notes),
             "mineral_printed": printed, "paragenesis": assertion("inclusion_observation_id", iid, "paragenesis"),
             "touching": {"y": "yes", "n": "no"}.get(assertion("inclusion_observation_id", iid, "touching")),
             "assemblage": assertion("diamond_observation_id", did, "reported_assemblage"),
             "status": status_label(status), "where": ref(page, table, row, col), "_txt": {}, "_st": {},
             "confidence": conf[("i", iid)][0], "confidence_why": conf[("i", iid)][1]}
        m = q("SELECT id, method_code FROM measurement WHERE inclusion_observation_id = ?", iid)
        r["method"] = m[0][1] if m else None
        r["identification_method"] = f"{m[0][1]} (phase named from its analysis)" if m and m[0][1] else None
        r["analysed"] = "yes" if m else "no"
        for code, text, value, vstatus in (q("""SELECT quantity_code, original_text, value, value_status
                                               FROM measured_value WHERE measurement_id = ?""", m[0][0]) if m else []):
            r[code] = value
            r["_txt"][code] = text
            if vstatus != "reported":
                r["_st"][code] = vstatus.replace("_", " ")
        inclusions.append(r)

    estimates = []
    for (sid, pub, short, page, table, row, qcode, text, value, unit, method, assumptions, dstatus, did) in q("""
            SELECT s.id, p.id, p.short_ref, e.page, e.table_label, e.row_label, d.quantity_code, d.original_text,
                   d.value, d.original_unit, d.method, d.assumptions, d.workflow_status, d.id
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
            "assumption": assumptions, "status": status_label(dstatus), "where": ref(page, table, row, None),
            "confidence": conf[("d", did)][0], "confidence_why": conf[("d", did)][1]})

    conf.update({("dia", d): (lvl, why) for d, lvl, why in q("""SELECT diamond_observation_id, level, reasons
              FROM extraction_confidence WHERE diamond_observation_id IS NOT NULL""")})

    diamonds = []
    for did, pub, short, sample, loc, status, page, table, row in q("""
            SELECT d.id, p.id, p.short_ref, s.identifier, d.reported_locality, d.workflow_status,
                   e.page, e.table_label, e.row_label
            FROM diamond_observation d JOIN publication p ON p.id = d.publication_id
            LEFT JOIN specimen_identifier s ON s.diamond_observation_id = d.id
            JOIN evidence e ON e.id = d.evidence_id ORDER BY d.id"""):
        get = lambda prop: assertion("diamond_observation_id", did, prop)
        dd, basis = depth("diamond_observation_id", did)
        dnotes = q("SELECT notes FROM diamond_observation WHERE id = ?", did)[0][0]
        r = {"id": did, "source_id": pub, "source": short, "sample": sample, "locality": loc,
             "country": country(did), "region": get("region"), "host_rock": get("host_rock"),
             "formation_depth_domain": dd, "depth_interpretation_basis": basis, "notes": dnotes,
             "diamond_morphology_d": decode(pub, "shape", get("shape")), "color_d": decode(pub, "colour", get("colour")),
             "plastic_deformation": decode(pub, "plastic_deformation", get("plastic_deformation")),
             "type": get("diamond_type"), "paragenesis": get("paragenesis"), "inclusions": get("reported_assemblage"),
             "inclusions_in_db": q("SELECT COUNT(*) FROM inclusion_observation WHERE diamond_observation_id = ?", did)[0][0],
             "also_in": ", ".join(f"{x} (link pending review)" if st != "approved" else x for x, st in q("""
                 SELECT p2.short_ref, l.workflow_status FROM diamond_identity_link l
                 JOIN diamond_observation d2 ON d2.id = CASE WHEN l.observation_a = ? THEN l.observation_b ELSE l.observation_a END
                 JOIN publication p2 ON p2.id = d2.publication_id WHERE ? IN (l.observation_a, l.observation_b)""", did, did)) or None,
             "status": status_label(status), "where": ref(page, table, row, None),
             "confidence": conf[("dia", did)][0], "confidence_why": conf[("dia", did)][1], "_txt": {}, "_st": {}}
        for code, text, value, vstatus in q("""SELECT v.quantity_code, v.original_text, v.value, v.value_status
                FROM measured_value v JOIN measurement m ON m.id = v.measurement_id WHERE m.diamond_observation_id = ?""", did):
            r[code], r["_txt"][code] = value, text
            if vstatus != "reported":
                r["_st"][code] = vstatus.replace("_", " ")
        r["has_data"] = "yes" if r["_txt"] or r["diamond_morphology_d"] else "no"
        diamonds.append(r)

    sources = []
    reg = Path(__file__).resolve().parent.parent / "docs" / "licence-register.csv"  # from scripts/licence_audit.py
    licence = {r["doi"].lower(): r["what_we_may_do"].split(";")[0].split(":")[0] for r in csv.DictReader(open(reg, encoding="utf-8"))} \
        if reg.exists() else {}
    for (pid, doi, citation, short, notes) in q("SELECT id, doi, citation, short_ref, notes FROM publication ORDER BY year, short_ref"):
        n = lambda sql: q(sql, pid)[0][0]
        sources.append({
            "id": pid, "doi": doi, "citation": citation, "short": short, "notes": notes,
            "licence": licence.get((doi or "").lower(), "not checked"),
            "diamonds": n("SELECT COUNT(*) FROM diamond_observation WHERE publication_id = ?"),
            "inclusions": n("SELECT COUNT(*) FROM inclusion_observation WHERE publication_id = ?"),
            "analyses": n("""SELECT COUNT(*) FROM measurement m JOIN inclusion_observation i
                             ON i.id = m.inclusion_observation_id WHERE i.publication_id = ?"""),
            "estimates": n("""SELECT COUNT(*) FROM derived_parameter d JOIN evidence e ON e.id = d.evidence_id
                              WHERE e.publication_id = ?"""),
            "diamond_data": n("""SELECT COUNT(DISTINCT m.diamond_observation_id) FROM measurement m
                                 JOIN diamond_observation d ON d.id = m.diamond_observation_id WHERE d.publication_id = ?"""),
            "status": sorted({status_label(s) for (s,) in q(
                """SELECT workflow_status FROM inclusion_observation WHERE publication_id = ?
                   UNION SELECT workflow_status FROM diamond_observation WHERE publication_id = ?""", pid, pid)}),
        })

    meta = {"oxides": [{"code": c, "label": label(c)} for c in oxides],
            "counts": {"papers": len(sources), "diamonds": sum(s["diamonds"] for s in sources),
                       "physical_diamonds": q("SELECT COUNT(DISTINCT cluster_id) FROM diamond_cluster")[0][0],
                       "inclusions": len(inclusions), "analysed": sum(r["analysed"] == "yes" for r in inclusions),
                       "values": q("SELECT COUNT(*) FROM measured_value")[0][0], "estimates": len(estimates)}}

    OUT.mkdir(parents=True, exist_ok=True)
    for name, obj in [("inclusions", inclusions), ("estimates", estimates), ("diamonds", diamonds),
                      ("sources", sources), ("meta", meta)]:
        (OUT / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(meta["counts"], [o["code"] for o in meta["oxides"]])


if __name__ == "__main__":
    main()
