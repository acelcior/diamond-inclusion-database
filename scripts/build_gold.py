"""Build gold/gold.sqlite from schema + vocab/ + every gold/<paper>/, run the checks, write each review page.

Run from the project folder:  python3 -I scripts/build_gold.py
Output: gold/gold.sqlite (not committed) and gold/<paper>/README.md (one review page per paper).
Papers with a Table 4 (Phillips 2004) use load_phillips; the rest use load_simple (one row per analysis).
"""
import csv
import json
import random
import re
import sqlite3
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "001_core.sql"
VOCAB = ROOT / "vocab"
GOLD = ROOT / "gold"
PAPER = GOLD / "phillips-2004"
DB_PATH = ROOT / "gold" / "gold.sqlite"

OXIDES = ["SiO2", "Al2O3", "TiO2", "Cr2O3", "FeO", "MnO", "NiO", "MgO", "CaO", "Na2O", "K2O", "V2O5", "ZnO", "Total"]
OXIDE_COLUMNS = ["P2O5", *OXIDES, "SrO"]  # analyses.csv columns load_simple reads
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
        parent = r.pop("parent", "")
        insert(db, "phase", **{k: (v or None) for k, v in r.items()},
               parent_phase_id=db.execute("SELECT id FROM phase WHERE name = ?", (parent,)).fetchone()[0] if parent else None)
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
def load_phillips(db, folder=PAPER):
    src = json.loads((folder / "source.json").read_text())
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
    return flags, pub


def apply_review(db, folder, pub):
    """Set every record of the paper to the curator's recorded review outcome (source.json "review")."""
    review = json.loads((folder / "source.json").read_text()).get("review")
    if not review:
        return
    ev = f"SELECT id FROM evidence WHERE publication_id = {int(pub)}"
    for t in ["diamond_observation", "inclusion_observation", "measurement", "derived_parameter", "assertion"]:
        db.execute(f"UPDATE {t} SET workflow_status = ? WHERE evidence_id IN ({ev})", (review["workflow_status"],))
    db.execute(f"UPDATE measured_value SET workflow_status = ? WHERE measurement_id IN "
               f"(SELECT id FROM measurement WHERE evidence_id IN ({ev}))", (review["workflow_status"],))


NUM = re.compile(r"^(?P<v>\d+\.?\d*)(?:\s*\((?P<u>\d+)\))?(?P<star>\*?)$")


def load_simple(db, folder):
    """Papers whose analyses are one CSV row each (gold/<paper>/analyses.csv), values as printed."""
    src = json.loads((folder / "source.json").read_text())
    phase_id = phase_lookup(db)
    flags = []
    pub = insert(db, "publication", **src["publication"])
    sf = insert(db, "source_file", publication_id=pub, **src["source_file"])
    run = insert(db, "import_run", run_type="claude_extraction", started_at=date.today().isoformat(),
                 tool=src.get("tool"), operator="Claude (Claude Code); values to be verified by a curator")

    def evidence(**kw):
        return insert(db, "evidence", publication_id=pub, source_file_id=sf, source_type="paper", import_run_id=run, **kw)

    prefix_to_loc = {}
    for loc in src.get("localities", []):
        ev = evidence(page=loc["page"], excerpt=loc["excerpt"])
        lid = insert(db, "locality", name=loc["name"], locality_type=loc["locality_type"],
                     country_code=src.get("country_code"), precision_class="approximate",
                     notes=loc.get("notes", "No coordinates entered yet (Phase 6 gazetteer)."))
        for p in loc["prefixes"]:
            prefix_to_loc[p] = (loc["name"], lid, ev)

    same = {k: evidence(**v) for k, v in src.get("same_diamond", {}).items()}
    diamonds, tables_of = {}, {}
    for r in rows(folder / src["analyses"]):
        cfg = src["tables"][r["table"]]
        where = f"{r['table']}, p. {r['page']}, {r['sample_no']} {r['mineral']} (column {r['column']})"
        tables_of.setdefault(r["sample_no"], set()).add(r["table"])
        ev = evidence(page=r["page"], table_label=r["table"], row_label=r["sample_no"],
                      column_label=f"{r['mineral']} (column {r['column']})",
                      excerpt=f"Sample {r['sample_no']}; {r['mineral']}" +
                              (f"; {r['n_analyses']} analyses" if r["n_analyses"] else ""),
                      cited_reference_text=r["cited_source"] or None)
        key = (r.get("diamond_no") if src.get("diamond_key") == "diamond_no" else
               r["sample_no"] if r["sample_no"] in same or src.get("diamond_key") == "sample" else (r["table"], r["sample_no"]))
        if key not in diamonds:
            m = re.match(r"[A-Za-z]+", r["sample_no"])
            loc = prefix_to_loc.get(m.group() if m else "")
            d = insert(db, "diamond_observation", publication_id=pub, evidence_id=same.get(r["sample_no"], ev),
                       reported_locality=loc[0] if loc else None, import_run_id=run,
                       notes="Same diamond in several tables (see evidence)" if r["sample_no"] in same else None)
            insert(db, "specimen_identifier", diamond_observation_id=d, identifier=r.get("diamond_no") or r["sample_no"],
                   id_type="author_sample")
            if r.get("assemblage"):
                insert(db, "assertion", diamond_observation_id=d, property_code="reported_assemblage",
                       value_text=r["assemblage"], asserted_by="authors", value_status="reported", derivation="reported",
                       evidence_id=ev)
            if loc:
                insert(db, "assertion", diamond_observation_id=d, property_code="collection_locality", value_text=loc[0],
                       value_locality_id=loc[1], asserted_by="authors", value_status="reported", derivation="reported",
                       evidence_id=loc[2])
            else:
                flags.append(("no locality", where, "sample prefix not in the paper's locality key"))
            diamonds[key] = d
        pid = phase_id(r.get("phase_hint") or r["mineral"])
        inc = insert(db, "inclusion_observation", publication_id=pub, evidence_id=ev, diamond_observation_id=diamonds[key],
                     reported_label=r.get("inclusion_label") or None,
                     reported_phase=r["mineral"], phase_id=pid, phase_match_status="mapped" if pid else "unmapped",
                     import_run_id=run, notes="; ".join(x for x in [where, r["note"]] if x))
        if pid is None:
            flags.append(("unmapped phase", where, f"'{r['mineral']}' is not in vocab/"))
        if r.get("paragenesis"):
            insert(db, "assertion", inclusion_observation_id=inc, property_code="paragenesis", value_text=r["paragenesis"],
                   asserted_by="authors", value_status="reported", derivation="interpreted", evidence_id=ev)
        if r["touching"]:
            insert(db, "assertion", inclusion_observation_id=inc, property_code="touching", value_text=r["touching"],
                   asserted_by="authors", value_status="reported", derivation="reported", evidence_id=ev,
                   notes=r["note"] or None)
        meas = insert(db, "measurement", inclusion_observation_id=inc, method_code=src["method"]["code"],
                      spot_label=f"mean of {r['n_analyses']} analyses" if r["n_analyses"] else "number of analyses not stated",
                      conditions=src["method"]["conditions"], evidence_id=ev, import_run_id=run,
                      notes=f"Analytical conditions: p. {src['method']['page']}")
        for col in OXIDE_COLUMNS:
            text = r.get(col, "")
            if not text:
                continue                                  # oxide not printed for this table
            value = dl = unc = None
            m = NUM.match(text)
            if text in cfg["notation"]:
                status = cfg["notation"][text]
                if status == "ambiguous":
                    flags.append(("ambiguous notation", where, f"{col} = '{text}': {cfg.get('footnote', 'not defined')}"))
            elif text[0] in "<≤":                        # '≤x' read as an upper limit; flagged per table
                status, dl = "below_detection", float(text[1:])
            elif m:
                status, value = "reported", float(m["v"])
                if m["u"] and cfg.get("uncertainty"):
                    decimals = len(m["v"].split(".")[1]) if "." in m["v"] else 0
                    unc = int(m["u"]) * 10 ** -decimals
            else:
                sys.exit(f"Unrecognised notation {text!r} at {where}, {col}")
            quantity = {"Total": "oxide_total", **src.get("column_quantity", {})}.get(col, col)
            insert(db, "measured_value", measurement_id=meas, quantity_code=quantity, original_text=text,
                   original_unit="wt%", value=value, detection_limit=dl, uncertainty=unc,
                   uncertainty_type=cfg.get("uncertainty") if unc is not None else None, value_status=status,
                   derivation="calculated_by_authors" if col == "Total" else "reported")
    for t, cfg in src["tables"].items():
        for k in ["uncertainty_note", "notation_note"]:
            if cfg.get(k):
                flags.append(("undefined notation", t, cfg[k]))
    for sample, note in src.get("total_notes", {}).items():
        flags.append(("total excludes an oxide", sample, note))
    for sample, ts in tables_of.items():
        if len(ts) > 1 and sample not in same:
            flags.append(("same label, kept apart", sample, f"appears in {', '.join(sorted(ts))}; the paper does not "
                          "say these are the same diamond, so they are separate records"))
    return flags, pub


def write_simple_review(db, paper, res):
    folder, pub, flags = paper["dir"], paper["pub"], paper["flags"]
    src = json.loads((folder / "source.json").read_text())
    c, review = res["counts"], src.get("review")
    status = (f"**Status: {review['workflow_status']}** by {review['reviewer']} on {review['date']}." if review else
              "**Status: extracted, not yet reviewed** (every record is `pending_review`).")
    L = [f"# Extraction: {src['publication']['short_ref']}", "",
         f"> {src['publication']['citation']} [doi:{src['publication']['doi']}](https://doi.org/{src['publication']['doi']}). "
         f"{status}", "",
         f"Generated by `scripts/build_gold.py` from [{src['analyses']}]({src['analyses']}) and "
         "[source.json](source.json); do not edit by hand.", "",
         "## What was extracted", "",
         md_table(["Records", "Count"], [["Host diamonds", c["diamond_observation"]],
                                         ["Inclusion analyses", c["measurement"]], ["Values", c["measured_value"]]]), "",
         f"{src['publication'].get('notes', '')}", "",
         "## Automatic checks", "",
         f"- **Traceability:** {c['measured_value'] - res['untraceable']} of {c['measured_value']} values have page, "
         "table, column and original text.",
         (f"- **Totals add up:** for every analysis the printed Total equals the sum of the printed oxides within "
          f"{res['tol']} wt% (rounding)." if not res["sum_mismatch"] else
          f"- **Totals differ by more than {res['tol']} wt%** for: " +
          ", ".join(f"{r[2]} {r[3]} (printed {r[4]}, sum {r[6]:.2f})" for r in res["sum_mismatch"])),
         "- **Value status:** " + ", ".join(f"{n} {s}" for s, n in res["status_counts"]) + ".", "",
         "**Flagged:**", "", md_table(["Kind", "Where", "What"], flags or [["—", "—", "none"]]), "",
         "## Spot-check list", "",
         "Open the PDF at each page and check the printed cell, then tell Claude the result.", "",
         md_table(["✓", "Page", "Table", "Row / column", "Quantity", "Printed"],
                  [["☑" if review else "☐", *r] for r in spot_checks(db, pub)]), ""]
    (folder / "README.md").write_text("\n".join(L), encoding="utf-8")


RULES = "conf-v3"  # docs/confidence.md (v3 adds the independent-copy check for host-diamond records)
BASE = {"spreadsheet": ("high", "read from a spreadsheet"),
        "text_layer": ("high", "read from the PDF text layer by column position, checked against page images"),
        "image_transcription": ("medium", "transcribed by eye from page images")}
DOWN = {"high": "medium", "medium": "low", "low": "low"}


def assess_confidence(db, papers):
    """Store an extraction-confidence level for every inclusion and derived value (rules in docs/confidence.md)."""
    for p in papers.values():
        src = json.loads((p["dir"] / "source.json").read_text())
        base, why = BASE[src["extraction_method"]]
        approved = (src.get("review") or {}).get("workflow_status") == "approved"
        explained = set(src.get("total_notes", {}))
        res = checks(db, p["pub"], p["tol"]) if "diamonds" not in src else {"sums": [], "sum_mismatch": []}
        state = {}
        for mid, _, row, *_ in res["sums"]:
            state[mid] = "match"
        for mid, _, row, *_ in res["sum_mismatch"]:
            state[mid] = "explained" if row in explained else "mismatch"
        for iid, mid in db.execute("""SELECT i.id, m.id FROM inclusion_observation i
                LEFT JOIN measurement m ON m.inclusion_observation_id = i.id WHERE i.publication_id = ?""", (p["pub"],)):
            level, reasons = base, [why]
            if mid is None:
                reasons.append("named in the paper, no analysis printed")
            elif state.get(mid) is None:
                level = DOWN[level]
                reasons.append("no printed total to check against")
            elif state[mid] == "mismatch":
                level = "low"
                reasons.append("printed total does not match the sum of the oxides")
            else:
                reasons.append("printed total matches the oxide sum" if state[mid] == "match" else
                               "printed total differs, explained by the source (see flags)")
            passed = state.get(mid) in ("match", "explained")
            if level == "medium" and passed and src["extraction_method"] == "image_transcription":
                level = "high"  # conf-v2: image reading calibrated, 0 errors in 513 values
                reasons.append("image reading calibrated (docs/confidence.md)")
            if approved:
                reasons.append("paper spot-checked against the PDF by a curator")
                if level == "medium" and passed:
                    level = "high"
            insert(db, "extraction_confidence", inclusion_observation_id=iid, level=level,
                   reasons="; ".join(reasons), rule_version=RULES)
        comp = {r["sample_no"]: r["result"] for r in rows(p["dir"] / "compilation-check.csv")} \
            if (p["dir"] / "compilation-check.csv").exists() and "diamonds" in src else {}
        explained_comp = src.get("compilation_explained", {})
        for dia, sample, n_meas in db.execute("""SELECT d.id, s.identifier, (SELECT COUNT(*) FROM measurement m
                WHERE m.diamond_observation_id = d.id) FROM diamond_observation d
                JOIN specimen_identifier s ON s.diamond_observation_id = d.id WHERE d.publication_id = ?""",
                                              (p["pub"],)).fetchall():
            level, reasons = base, [why]
            if n_meas:
                result = comp.get(sample, "")
                if (" ok" in result and "DIFF" not in result) or sample in explained_comp:
                    level = "high"  # conf-v3: two independent transcriptions agree
                    reasons.append("values match the Stachel compilation, an independent transcription citing this paper"
                                   + (" (one difference explained by the compiler's conventions)" if sample in explained_comp else ""))
                elif "DIFF" in result:
                    level = "low"
                    reasons.append("values differ from the Stachel compilation: " + result)
                else:
                    reasons.append("no printed total or independent copy to check against")
            if approved:
                reasons.append("paper spot-checked against the PDF by a curator")
            insert(db, "extraction_confidence", diamond_observation_id=dia, level=level,
                   reasons="; ".join(reasons), rule_version=RULES)
        for (did,) in db.execute("""SELECT d.id FROM derived_parameter d JOIN evidence e ON e.id = d.evidence_id
                                    WHERE e.publication_id = ?""", (p["pub"],)).fetchall():
            reasons = [why, "no printed check value for estimates"]
            level = DOWN[base]
            if approved:
                reasons.append("paper spot-checked against the PDF by a curator")
                level = base
            insert(db, "extraction_confidence", derived_parameter_id=did, level=level,
                   reasons="; ".join(reasons), rule_version=RULES)


def load_diamonds(db, folder):
    """Host-diamond tables (gold/<paper>/diamonds.csv): one row per diamond, values as printed."""
    src = json.loads((folder / "source.json").read_text())
    flags = []
    pub = insert(db, "publication", **src["publication"])
    sf = insert(db, "source_file", publication_id=pub, **src["source_file"])
    run = insert(db, "import_run", run_type="claude_extraction", started_at=date.today().isoformat(),
                 tool=src.get("tool"), operator="Claude (Claude Code); values to be verified by a curator")

    def evidence(**kw):
        return insert(db, "evidence", publication_id=pub, source_file_id=sf, source_type="paper", import_run_id=run, **kw)

    loc = src["locality"]
    loc_ev = evidence(page=loc["page"], excerpt=loc["excerpt"])
    loc_id = insert(db, "locality", name=loc["name"], locality_type="district", country_code="GN",
                    precision_class="approximate", notes="No coordinates entered yet (Phase 6 gazetteer).")
    unit_ev = evidence(**{k: src["units"]["N_ppm"][k] for k in ("page", "excerpt")})
    type2_ev = evidence(**src["type_II_rule"])
    for r in rows(folder / src["diamonds"]):
        where = f"{r['table']}, p. {r['page']}, {r['sample_no']}"
        ev = evidence(page=r["page"], table_label=r["table"], row_label=r["sample_no"],
                      excerpt=" ".join(r[c] for c in ["sample_no", "shape", "colour", "plastic_deformation", "d13C",
                                                     "type", "N_ppm", "pct_B", "paragenesis", "inclusions"] if r[c]))
        d = insert(db, "diamond_observation", publication_id=pub, evidence_id=ev, reported_locality=loc["reported"],
                   import_run_id=run, notes=src.get("notes_per_sample", {}).get(r["sample_no"]))
        insert(db, "specimen_identifier", diamond_observation_id=d, identifier=r["sample_no"], id_type="author_sample")
        a = lambda prop, text, derivation="reported", e=ev: insert(
            db, "assertion", diamond_observation_id=d, property_code=prop, value_text=text, asserted_by="authors",
            value_status="reported", derivation=derivation, evidence_id=e)
        a("collection_locality", loc["reported"], e=loc_ev)
        db.execute("UPDATE assertion SET value_locality_id = ? WHERE id = (SELECT MAX(id) FROM assertion)", (loc_id,))
        for prop in ["shape", "colour", "plastic_deformation"]:
            a(prop, r[prop])
        a("diamond_type", r["type"], "interpreted")
        a("paragenesis", r["paragenesis"], "interpreted")
        if r["inclusions"]:
            a("reported_assemblage", r["inclusions"])
        m = insert(db, "measurement", diamond_observation_id=d, evidence_id=ev, import_run_id=run,
                   notes="δ13C; method not recorded here (text layer unreadable)")
        insert(db, "measured_value", measurement_id=m, quantity_code="d13C", original_text=r["d13C"], original_unit="‰",
               value=float(r["d13C"]), value_status="reported", derivation="reported")
        m = insert(db, "measurement", diamond_observation_id=d, evidence_id=ev, import_run_id=run,
                   notes="Nitrogen content and aggregation; method not recorded here (text layer unreadable)")
        type2 = r["type"] == "II"
        n_status = "below_detection" if type2 and r["N_ppm"] == "0" else "reported"
        insert(db, "measured_value", measurement_id=m, quantity_code="N_content", original_text=r["N_ppm"],
               original_unit="ppm (atomic, p. 468)", value=None if n_status != "reported" else float(r["N_ppm"].replace(",", "")),
               value_status=n_status, derivation="reported", evidence_id=type2_ev if type2 else unit_ev)
        b_status = "not_applicable" if type2 and r["pct_B"] == "0" else "reported"
        insert(db, "measured_value", measurement_id=m, quantity_code="N_pct_B", original_text=r["pct_B"], original_unit="%B",
               value=None if b_status != "reported" else float(r["pct_B"]), value_status=b_status, derivation="reported",
               evidence_id=type2_ev if type2 else None)
        if r["sample_no"] in src.get("notes_per_sample", {}):
            flags.append(("source inconsistency", where, src["notes_per_sample"][r["sample_no"]]))
    flags.append(("interpretation", "Type II rows", "Printed N = 0 stored as below detection and %B = 0 as not "
                  "applicable, because the paper defines Type II as nitrogen below detection (p. 468)."))
    return flags, pub


def link_shared_samples(db, papers):
    """Identity links between diamonds that two papers of one series report under the same number
    (gold/identity-links.json). Links stay pending_review until a recorded curator review approves them."""
    cfg = json.loads((GOLD / "identity-links.json").read_text())
    for link in cfg["series_links"]:
        (a, b), why = link["papers"], link["why"]
        status = (link.get("review") or {}).get("workflow_status", "pending_review")
        if a not in papers or b not in papers:
            continue
        for da, db_, sample in db.execute("""SELECT da.id, dbb.id, sa.identifier FROM diamond_observation da
                JOIN specimen_identifier sa ON sa.diamond_observation_id = da.id
                JOIN specimen_identifier sb ON sb.identifier = sa.identifier
                JOIN diamond_observation dbb ON dbb.id = sb.diamond_observation_id
                WHERE da.publication_id = ? AND dbb.publication_id = ?""", (papers[a]["pub"], papers[b]["pub"])).fetchall():
            lo, hi = sorted((da, db_))
            insert(db, "diamond_identity_link", observation_a=lo, observation_b=hi, basis=link["basis"],
                   asserted_by="curator", confidence="high", workflow_status=status,
                   notes="; ".join(x for x in [why, link.get("notes", {}).get(sample)] if x))


def apply_setting(db, papers):
    """Region, host rock and depth domain, only where a paper states them (source.json "setting"), with evidence."""
    for p in papers.values():
        src = json.loads((p["dir"] / "source.json").read_text())
        cfg, pub = src.get("setting", {}), p["pub"]
        ev_cache = {}

        def ev(spec):
            key = (spec["page"], spec["excerpt"])
            if key not in ev_cache:
                ev_cache[key] = insert(db, "evidence", publication_id=pub, source_type="paper", page=spec["page"],
                                       excerpt=spec["excerpt"])
            return ev_cache[key]

        for did, loc in db.execute("SELECT id, (SELECT l.name FROM assertion a JOIN locality l ON l.id = a.value_locality_id "
                                   "WHERE a.diamond_observation_id = d.id LIMIT 1) FROM diamond_observation d "
                                   "WHERE publication_id = ?", (pub,)).fetchall():
            for prop in ["region", "host_rock"]:
                if prop in cfg:
                    spec = cfg[prop].get("by_locality", {}).get(loc, cfg[prop])
                    insert(db, "assertion", diamond_observation_id=did, property_code=prop, value_text=spec["value"],
                           asserted_by="authors", value_status="reported", derivation="reported", evidence_id=ev(spec))
        dd = cfg.get("depth_domain")
        if dd:
            for col, sid, text in db.execute("""SELECT CASE WHEN inclusion_observation_id IS NOT NULL THEN 'inclusion_observation_id'
                    ELSE 'diamond_observation_id' END, COALESCE(inclusion_observation_id, diamond_observation_id), value_text
                    FROM assertion a JOIN evidence e ON e.id = a.evidence_id
                    WHERE a.property_code = 'paragenesis' AND e.publication_id = ?
                    AND (inclusion_observation_id IS NOT NULL OR diamond_observation_id IS NOT NULL)""", (pub,)).fetchall():
                if text in dd["map"]:
                    insert(db, "assertion", **{col: sid}, property_code="formation_depth_domain", value_text=dd["map"][text],
                           asserted_by="authors", value_status="reported", derivation="interpreted", evidence_id=ev(dd),
                           notes=dd["basis"])


def build(path=":memory:"):
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA.read_text())
    db.executescript((ROOT / "schema" / "002_extraction_confidence.sql").read_text())
    load_vocab(db)
    papers = {}
    for src in sorted(GOLD.glob("*/source.json")):
        folder = src.parent
        kind = json.loads(src.read_text())
        loader = (load_phillips if (folder / "table4.csv").exists() else load_diamonds if "diamonds" in kind
                  else load_simple)
        flags, pub = loader(db, folder)
        apply_review(db, folder, pub)
        papers[folder.name] = {"dir": folder, "pub": pub, "flags": flags,
                               "tol": json.loads(src.read_text()).get("total_tolerance", 0.05)}
    apply_setting(db, papers)
    link_shared_samples(db, papers)
    assess_confidence(db, papers)
    db.commit()
    return db, papers


# ---------------- checks ----------------

def checks(db, pub, tol=0.05):
    out = {}
    P = f"e.publication_id = {int(pub)}"
    # analytical totals: printed Total vs sum of the printed oxides
    sums = db.execute("""
        SELECT m.id, e.page, e.row_label, e.column_label, t.original_text, t.value,
               ROUND(SUM(CASE WHEN v.quantity_code <> 'oxide_total' THEN v.value END), 2)
        FROM measurement m JOIN evidence e ON e.id = m.evidence_id
        JOIN measured_value v ON v.measurement_id = m.id
        JOIN measured_value t ON t.measurement_id = m.id AND t.quantity_code = 'oxide_total'
        WHERE """ + P + """ GROUP BY m.id ORDER BY m.id""").fetchall()
    sums = [s for s in sums if s[5] is not None and s[6] is not None]
    out["sums"] = sums
    out["sum_mismatch"] = [s for s in sums if abs(s[6] - s[5]) > tol]
    out["tol"] = tol
    out["max_sum_diff"] = max((abs(s[6] - s[5]) for s in sums), default=0)
    out["total_range"] = [s for s in sums if not 98.0 <= s[5] <= 101.5]
    V = "FROM measured_value v JOIN measurement m ON m.id = v.measurement_id JOIN evidence e ON e.id = m.evidence_id"
    out["below_dl"] = db.execute(f"""SELECT quantity_code, COUNT(*) {V}
        WHERE {P} AND quantity_code IN ('Na2O', 'K2O') AND value < 0.02 GROUP BY quantity_code""").fetchall()
    out["status_counts"] = db.execute(f"""SELECT value_status, COUNT(*) {V}
        WHERE {P} GROUP BY value_status ORDER BY 2 DESC""").fetchall()
    out["untraceable"] = db.execute("""SELECT COUNT(*) FROM measured_value v
        JOIN measurement m ON m.id = v.measurement_id JOIN evidence e ON e.id = m.evidence_id
        WHERE """ + P + """ AND (e.page IS NULL OR e.table_label IS NULL OR v.original_text IS NULL)""").fetchone()[0]
    count = lambda sql: db.execute(sql).fetchone()[0]
    out["counts"] = {
        "diamond_observation": count(f"SELECT COUNT(*) FROM diamond_observation WHERE publication_id = {int(pub)}"),
        "inclusion_observation": count(f"SELECT COUNT(*) FROM inclusion_observation WHERE publication_id = {int(pub)}"),
        "measurement": count(f"SELECT COUNT(*) FROM measurement m JOIN evidence e ON e.id = m.evidence_id WHERE {P}"),
        "measured_value": count(f"SELECT COUNT(*) {V} WHERE {P}"),
        "inclusion_set": count(f"SELECT COUNT(*) FROM inclusion_set WHERE publication_id = {int(pub)}"),
        "derived_parameter": count(f"SELECT COUNT(*) FROM derived_parameter d JOIN evidence e ON e.id = d.evidence_id WHERE {P}"),
        "assertion": count(f"SELECT COUNT(*) FROM assertion a JOIN evidence e ON e.id = a.evidence_id WHERE {P}"),
        "evidence": count(f"SELECT COUNT(*) FROM evidence e WHERE {P}"),
    }
    out["unanalysed"] = count(f"""SELECT COUNT(*) FROM inclusion_observation i WHERE publication_id = {int(pub)}
        AND NOT EXISTS (SELECT 1 FROM measurement m WHERE m.inclusion_observation_id = i.id)""")
    return out


# ---------------- review page ----------------

def md_table(header, body):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in body]
    return "\n".join(lines)


def spot_checks(db, pub, n_values=20, n_derived=5):
    rng = random.Random(2004)  # fixed seed: the same list every build
    vals = db.execute("""SELECT e.page, e.table_label, e.row_label, e.column_label, v.quantity_code, v.original_text
        FROM measured_value v JOIN measurement m ON m.id = v.measurement_id JOIN evidence e ON e.id = m.evidence_id
        WHERE e.publication_id = ? ORDER BY v.id""", (pub,)).fetchall()
    der = db.execute("""SELECT e.page, e.table_label, e.row_label, d.method, d.original_text, d.original_unit
        FROM derived_parameter d JOIN evidence e ON e.id = d.evidence_id WHERE e.publication_id = ? ORDER BY d.id""",
                     (pub,)).fetchall()
    picks = [(p, t, f"{r} {c}", q, x) for p, t, r, c, q, x in rng.sample(vals, min(n_values, len(vals)))]
    picks += [(p, t, r, m, f"{x} {u}") for p, t, r, m, x, u in rng.sample(der, min(n_derived, len(der)))]
    return sorted(picks, key=lambda x: (x[0], x[1], x[2]))


def write_review(db, flags, res, pub):
    c = res["counts"]
    q = lambda sql: db.execute(sql).fetchall()
    data = q("""SELECT e.page, e.row_label, i.reported_phase, a.value_text, t.value_text,
        """ + ", ".join(f"MAX(CASE WHEN v.quantity_code = '{k}' THEN v.original_text END)" for k in
                        ["SiO2", "TiO2", "Al2O3", "Cr2O3", "FeOT", "MnO", "NiO", "MgO", "CaO", "Na2O", "K2O", "V2O5", "ZnO", "oxide_total"]) + """
        FROM inclusion_observation i JOIN measurement m ON m.inclusion_observation_id = i.id
        JOIN evidence e ON e.id = m.evidence_id JOIN measured_value v ON v.measurement_id = m.id
        JOIN assertion a ON a.inclusion_observation_id = i.id AND a.property_code = 'paragenesis'
        JOIN assertion t ON t.inclusion_observation_id = i.id AND t.property_code = 'touching'
        WHERE i.publication_id = """ + str(int(pub)) + """ GROUP BY i.id ORDER BY i.id""")
    pt = q("""SELECT s.label, d.method, d.original_text || ' ' || d.original_unit, COALESCE(d.assumptions, '')
        FROM derived_parameter d JOIN inclusion_set s ON s.id = d.inclusion_set_id
        WHERE s.publication_id = """ + str(int(pub)) + """ ORDER BY d.id""")
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
                 [["☑" if review else "☐", *r] for r in spot_checks(db, pub)]),
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
    db, papers = build(str(DB_PATH))
    for name, p in papers.items():
        res = checks(db, p["pub"], p["tol"])
        if (p["dir"] / "diamonds.csv").exists():
            print(f"{name}: {res['counts']['diamond_observation']} diamonds, {len(p['flags'])} flags")
            for f in p["flags"]:
                print("   ", *f)
            continue
        if p["dir"] == PAPER:
            write_review(db, p["flags"], res, p["pub"])
        else:
            write_simple_review(db, p, res)
        print(f"{name}: {res['counts']['measurement']} analyses, {res['counts']['measured_value']} values; "
              f"{len(res['sum_mismatch'])} sum mismatches (tol {p['tol']}); {len(p['flags'])} flags; "
              f"{res['untraceable']} untraceable")
        for f in p["flags"]:
            print("   ", *f)


if __name__ == "__main__":
    main()
