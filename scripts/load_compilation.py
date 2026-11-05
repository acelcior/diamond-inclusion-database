"""Load a literature compilation (compilations/<name>/) as its own source layer (D-013).

Called by scripts/build_gold.py. Every row becomes reports by the compilation, never by the cited paper:
evidence = (compilation, sheet, row) + the compiler's citation and DOI; workflow status 'imported_unverified'.
Nothing is merged: rows sharing (cited reference, locality, sample) are one diamond record of the compilation;
links to physical diamonds/inclusions in directly extracted papers are not made here.
Inclusion chemistry, paragenesis, assemblage, locality and craton only; host-diamond data and the compiler's
P-T columns are not imported yet.
"""
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPILATIONS = ROOT / "compilations"
CONFIDENCE = ("medium", "copied exactly from a CC0 compilation; not yet checked against the cited paper "
                        "(the Phillips 2004 check found the compiler had converted or rescaled some analyses)")
BELOW = re.compile(r"^[<≤]\s*(\d*\.?\d+)$")


def phase_matcher(phase_id):
    """Full name first, then the name before a parenthesis ('garnet (core)' -> garnet). '?' makes the match ambiguous."""
    def match(printed):
        full = phase_id(printed)
        if full:
            return full, "mapped"
        base = re.sub(r"\s*\(.*\)\s*$", "", printed).strip()
        pid = phase_id(base) if base and base != printed else None
        if pid:
            return pid, "ambiguous" if "?" in printed else "mapped"
        return None, "unmapped"
    return match


def parse(value, notation):
    """(status, number, detection_limit, original_text) for one oxide cell as stored in the sheet."""
    if isinstance(value, (int, float)):
        # Excel stores binary floats (a summed Total reads 99.86999999999999 where Excel shows 99.87);
        # 12 significant digits removes that noise without changing any value the compiler entered
        text = format(value, ".12g")
        return "reported", float(text), None, text
    text = value
    t = text.replace("\xa0", " ").strip()
    if t in notation:
        return notation[t], None, None, text
    m = BELOW.match(t)
    if m:
        return "below_detection", None, float(m[1]), text
    return "ambiguous", None, None, text   # e.g. a cell holding only spaces; flagged, never guessed


def load(db, folder, insert, phase_id, rule_version):
    src = json.loads((folder / "source.json").read_text())
    col = src["columns"]
    flags = []
    pub = insert(db, "publication", **src["publication"])
    sf = insert(db, "source_file", publication_id=pub, **src["source_file"])
    run = insert(db, "import_run", run_type="compilation_import", started_at=date.today().isoformat(),
                 tool="scripts/load_compilation.py", operator="Claude (Claude Code); values as stored in the compilation")
    match = phase_matcher(phase_id)
    diamonds = {}
    skipped_host_only = 0
    unmapped, ambiguous_cells, no_doi, no_ref = Counter(), Counter(), 0, 0

    with open(folder / src["rows"], encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            c, row = rec["cells"], rec["row"]
            mineral = str(c.get(col["mineral"], "")).strip()
            if not mineral:
                skipped_host_only += 1          # host-diamond-only row: imported in a later step
                continue
            cited = c.get(col["cited_reference"])
            doi = str(c.get(col["cited_doi"], "")).strip().lower() or None
            no_doi += doi is None and cited not in (None, "")
            no_ref += cited in (None, "")
            ev = insert(db, "evidence", publication_id=pub, source_file_id=sf, source_type="compilation",
                        sheet=src["sheet"], row_label=f"row {row}", cited_reference_text=cited, cited_doi=doi,
                        import_run_id=run)
            locality = c.get(col["locality"])
            sample = str(c[col["sample"]]).strip() if col["sample"] in c else None
            key = (cited, locality, sample) if sample else ("row", row)
            if key not in diamonds:
                d = insert(db, "diamond_observation", publication_id=pub, evidence_id=ev, reported_locality=locality,
                           workflow_status="imported_unverified", import_run_id=run)
                if sample:
                    insert(db, "specimen_identifier", diamond_observation_id=d, identifier=sample, id_type="author_sample")
                for prop, field, derivation in [("craton", "craton", "interpreted"),
                                                ("reported_assemblage", "assemblage", "reported")]:
                    if c.get(col[field]) not in (None, ""):
                        insert(db, "assertion", diamond_observation_id=d, property_code=prop, value_text=str(c[col[field]]),
                               asserted_by="compiler", value_status="reported", derivation=derivation, evidence_id=ev,
                               workflow_status="imported_unverified")
                diamonds[key] = d
            pid, status = match(mineral)
            if status == "unmapped":
                unmapped[mineral] += 1
            remark = c.get(col["remarks"])
            inc = insert(db, "inclusion_observation", publication_id=pub, evidence_id=ev, diamond_observation_id=diamonds[key],
                         reported_phase=mineral, phase_id=pid, phase_match_status=status,
                         workflow_status="imported_unverified", import_run_id=run,
                         notes=f"Compiler's remark: {remark}" if remark not in (None, "") else None)
            if c.get(col["paragenesis"]) not in (None, ""):
                insert(db, "assertion", inclusion_observation_id=inc, property_code="paragenesis",
                       value_text=str(c[col["paragenesis"]]), asserted_by="compiler", value_status="reported",
                       derivation="interpreted", evidence_id=ev, workflow_status="imported_unverified")
            insert(db, "extraction_confidence", inclusion_observation_id=inc, level=CONFIDENCE[0], reasons=CONFIDENCE[1],
                   rule_version=rule_version)
            cells = [(q, c[h]) for h, q in src["oxides"].items() if h in c]
            if not cells:
                continue
            meas = insert(db, "measurement", inclusion_observation_id=inc, evidence_id=ev, import_run_id=run,
                          workflow_status="imported_unverified",
                          notes="Method not recorded per row in the compilation")
            for quantity, value in cells:
                st, num, dl, text = parse(value, src["notation"])
                if st == "ambiguous":
                    ambiguous_cells[repr(text)] += 1
                insert(db, "measured_value", measurement_id=meas, quantity_code=quantity, original_text=text,
                       original_unit="wt%", value=num, detection_limit=dl, value_status=st, derivation="reported",
                       workflow_status="imported_unverified")

    flags.append(("host-diamond-only rows not imported yet", skipped_host_only, "next import step"))
    flags.append(("rows citing a paper without DOI", no_doi, "cited by short reference only"))
    flags.append(("rows with no reference at all", no_ref, "the compilation names no source; kept, citation unknown"))
    for text, n in ambiguous_cells.most_common():
        flags.append(("ambiguous cell", n, f"{text}: not a number or a defined notation; stored as ambiguous"))
    for name, n in unmapped.most_common():
        flags.append(("unmapped phase", n, f"'{name}' is not in vocab/ (kept as printed)"))
    flags.append(("FeO", "-", src["feo_note"]))
    return flags, pub


def load_all(db, insert, phase_id, rule_version):
    """Every compilations/<name>/source.json. Returns {name: {"dir", "pub", "flags"}}."""
    out = {}
    for s in sorted(COMPILATIONS.glob("*/source.json")):
        flags, pub = load(db, s.parent, insert, phase_id, rule_version)
        out[s.parent.name] = {"dir": s.parent, "pub": pub, "flags": flags}
    return out


def write_report(db, name, c):
    """compilations/<name>/README.md: what was imported and what was flagged."""
    pub = c["pub"]
    one = lambda sql: db.execute(sql, (pub,)).fetchone()[0]
    counts = {
        "inclusion reports": one("SELECT COUNT(*) FROM inclusion_observation WHERE publication_id = ?"),
        "with chemistry": one("""SELECT COUNT(*) FROM measurement m JOIN inclusion_observation i
                                 ON i.id = m.inclusion_observation_id WHERE i.publication_id = ?"""),
        "values": one("""SELECT COUNT(*) FROM measured_value v JOIN measurement m ON m.id = v.measurement_id
                         JOIN inclusion_observation i ON i.id = m.inclusion_observation_id WHERE i.publication_id = ?"""),
        "diamond records": one("SELECT COUNT(*) FROM diamond_observation WHERE publication_id = ?"),
        "cited references": one("SELECT COUNT(DISTINCT cited_reference_text) FROM evidence WHERE publication_id = ?"),
        "phases mapped": one("""SELECT COUNT(*) FROM inclusion_observation WHERE publication_id = ?
                                AND phase_match_status = 'mapped'"""),
    }
    status = db.execute("""SELECT v.value_status, COUNT(*) FROM measured_value v JOIN measurement m ON m.id = v.measurement_id
        JOIN inclusion_observation i ON i.id = m.inclusion_observation_id WHERE i.publication_id = ?
        GROUP BY v.value_status""", (pub,)).fetchall()
    src = json.loads((c["dir"] / "source.json").read_text())
    L = ["---", "tags: [compilation, import]", "---", "", f"# Import report: {src['publication']['short_ref']}", "",
         f"Generated by `scripts/build_gold.py` on {date.today().isoformat()}. Source: {src['publication']['citation']}", "",
         "Related: [compilations mapping](../../docs/compilations-mapping.md) · [decisions](../../docs/decisions/README.md) (D-013)", "",
         "## Imported", "", "| | Count |", "|---|---|", *[f"| {k} | {v:,} |" for k, v in counts.items()], "",
         "Value status: " + ", ".join(f"{s.replace('_', ' ')} {n:,}" for s, n in status), "",
         "Every row is stored as a report *by the compilation*, citing the paper the compiler names, with workflow "
         "status `imported_unverified` and extraction confidence medium. Rows that share cited reference, locality and "
         "sample number form one diamond record; nothing is merged with directly extracted papers.", "",
         "## Flags", "", "| Flag | Count | Detail |", "|---|---|---|",
         *[f"| {a} | {b} | {d} |" for a, b, d in c["flags"]], ""]
    (c["dir"] / "README.md").write_text("\n".join(L), encoding="utf-8")
