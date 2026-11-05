"""Checks the gold-standard build (scripts/build_gold.py) from the committed files only.

Run from the project folder:  python3 -m unittest tests/test_gold.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_gold  # noqa: E402


class GoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db, cls.papers = build_gold.build()
        cls.phillips = cls.papers["phillips-2004"]["pub"]

    def one(self, sql):
        return self.db.execute(sql).fetchone()[0]

    def test_phillips_counts(self):
        c = build_gold.checks(self.db, self.phillips)["counts"]
        self.assertEqual(c["measurement"], 80)                # Table 3 columns
        self.assertEqual(c["measured_value"], 80 * 14)
        self.assertEqual(c["inclusion_set"], 50)              # Table 4 rows
        self.assertEqual(c["diamond_observation"], 50)        # 36 in Table 3 + 14 only in Table 4

    def test_sobolev(self):
        p = self.papers["sobolev-2004"]
        c = build_gold.checks(self.db, p["pub"], p["tol"])["counts"]
        self.assertEqual(c["measurement"], 63)                # Tables 3, 4, 5, 6, 8
        # Yum-27 (olivine in Table 3, two garnets in Table 6) is one diamond; AL-1 in Tables 4 and 5 is not
        n = lambda s: self.one(f"SELECT COUNT(*) FROM specimen_identifier si JOIN diamond_observation d "
                               f"ON d.id = si.diamond_observation_id WHERE d.publication_id = {p['pub']} AND identifier = '{s}'")
        self.assertEqual((n("Yum-27"), n("AL-1")), (1, 2))
        self.assertEqual(self.one("SELECT COUNT(*) FROM measured_value WHERE original_text = '<0.03' "
                                  "AND (value_status <> 'below_detection' OR detection_limit <> 0.03)"), 0)

    def test_printed_totals_add_up(self):
        import json
        for p in self.papers.values():
            res = build_gold.checks(self.db, p["pub"], p["tol"])
            known = set(json.loads((p["dir"] / "source.json").read_text()).get("total_notes", {}))
            self.assertEqual({r[2] for r in res["sum_mismatch"]}, known)  # only mismatches already explained
            self.assertEqual(res["untraceable"], 0)

    def test_review_applied(self):
        # Phillips is approved; papers without a recorded review stay pending
        self.assertEqual(self.one(f"SELECT COUNT(*) FROM inclusion_observation WHERE publication_id = {self.phillips} "
                                  "AND workflow_status <> 'approved'"), 0)
        self.assertEqual(self.one(f"SELECT COUNT(*) FROM inclusion_observation i JOIN publication p ON p.id = i.publication_id "
                                  f"WHERE p.id <> {self.phillips} AND p.pub_type <> 'dataset' "
                                  "AND i.workflow_status <> 'pending_review'"), 0)

    def test_compilation_layer(self):
        """Stachel compilation (D-013): every row with a mineral is one report; nothing reviewed, nothing merged."""
        pub = self.one("SELECT id FROM publication WHERE doi = '10.7939/DVN/EJUE1G'")
        n = lambda sql: self.one(sql.replace("PUB", str(pub)))
        self.assertEqual(n("SELECT COUNT(*) FROM inclusion_observation WHERE publication_id = PUB"), 8634)
        self.assertEqual(n("""SELECT COUNT(*) FROM inclusion_observation WHERE publication_id = PUB
                              AND workflow_status <> 'imported_unverified'"""), 0)
        # every compiled inclusion's evidence names the compilation row and the paper the compiler cites
        self.assertEqual(n("""SELECT COUNT(*) FROM inclusion_observation i JOIN evidence e ON e.id = i.evidence_id
                              WHERE i.publication_id = PUB AND (e.source_type <> 'compilation' OR e.row_label IS NULL)"""), 0)
        # ...except 13 rows the compilation itself gives no reference for (kept and flagged, never filled in)
        self.assertEqual(n("""SELECT COUNT(*) FROM inclusion_observation i JOIN evidence e ON e.id = i.evidence_id
                              WHERE i.publication_id = PUB AND e.cited_reference_text IS NULL"""), 13)
        # no compiled diamond record is linked or merged with a directly extracted paper's record
        self.assertEqual(n("""SELECT COUNT(*) FROM diamond_identity_link l JOIN diamond_observation d
                              ON d.id IN (l.observation_a, l.observation_b) WHERE d.publication_id = PUB"""), 0)
        # notation: '<0.02' with a non-breaking space keeps its original text and its limit
        self.assertEqual(n("""SELECT COUNT(*) FROM measured_value WHERE original_text LIKE '<' || char(160) || '%'
                              AND (value_status <> 'below_detection' OR detection_limit IS NULL)"""), 0)
        self.assertGreater(n("""SELECT COUNT(*) FROM measured_value WHERE original_text LIKE '<' || char(160) || '%'"""), 0)
        # spot check, Kankan KK-001a garnet core as cited to Stachel et al. (2000): SiO2 42.425, NiO 0.0115
        self.assertEqual(n("""SELECT GROUP_CONCAT(x, ' ') FROM (SELECT v.quantity_code || '=' || v.original_text AS x FROM measured_value v
                              JOIN measurement m ON m.id = v.measurement_id JOIN inclusion_observation i ON i.id = m.inclusion_observation_id
                              JOIN evidence e ON e.id = i.evidence_id JOIN specimen_identifier s ON s.diamond_observation_id = i.diamond_observation_id
                              WHERE i.publication_id = PUB AND s.identifier = 'KK-001a' AND i.reported_phase = 'garnet (core)'
                              AND v.quantity_code IN ('SiO2', 'NiO') AND e.cited_reference_text = 'Stachel et al. (2000)'
                              ORDER BY v.quantity_code)"""), "NiO=0.0115 SiO2=42.425")

    def test_confidence(self):
        # every inclusion and estimate has exactly one level (docs/confidence.md)
        self.assertEqual(self.one("SELECT COUNT(*) FROM inclusion_observation i WHERE NOT EXISTS "
                                  "(SELECT 1 FROM extraction_confidence c WHERE c.inclusion_observation_id = i.id)"), 0)
        self.assertEqual(self.one("SELECT COUNT(*) FROM derived_parameter d WHERE NOT EXISTS "
                                  "(SELECT 1 FROM extraction_confidence c WHERE c.derived_parameter_id = d.id)"), 0)
        levels = lambda pub: {r[0] for r in self.db.execute(
            "SELECT DISTINCT c.level FROM extraction_confidence c JOIN inclusion_observation i "
            "ON i.id = c.inclusion_observation_id WHERE i.publication_id = ?", (pub,))}
        self.assertEqual(levels(self.phillips), {"high"})                                   # text layer + reviewed
        # read from images, every printed total checks out: high under conf-v2
        self.assertEqual(levels(self.papers["stachel-2000-kankan2"]["pub"]), {"high"})
        with self.assertRaises(build_gold.sqlite3.IntegrityError):
            self.db.execute("INSERT INTO extraction_confidence (level, reasons, rule_version) VALUES ('high', 'x', 'v')")

    def test_kankan3_diamonds(self):
        pub = self.papers["stachel-2002-kankan3"]["pub"]
        self.assertEqual(self.one(f"SELECT COUNT(*) FROM diamond_observation WHERE publication_id = {pub}"), 91)
        # Type II: printed N = 0 means below detection (p. 468), never a measured zero
        self.assertEqual(self.one(f"""SELECT COUNT(*) FROM measured_value v JOIN measurement m ON m.id = v.measurement_id
            JOIN diamond_observation d ON d.id = m.diamond_observation_id JOIN assertion a ON a.diamond_observation_id = d.id
            AND a.property_code = 'diamond_type' AND a.value_text = 'II'
            WHERE d.publication_id = {pub} AND v.quantity_code = 'N_content' AND v.value_status <> 'below_detection'"""), 0)
        # same KK number in Kankan II and III: 15 links, approved by the curator (gold/identity-links.json);
        # the records stay separate, and the physical-diamond count drops by one per link
        self.assertEqual(self.one("SELECT COUNT(*) FROM diamond_identity_link WHERE workflow_status = 'approved'"), 15)
        records = self.one("SELECT COUNT(*) FROM diamond_observation")
        self.assertEqual(self.one("SELECT COUNT(DISTINCT cluster_id) FROM diamond_cluster"), records - 15)

    def test_every_phase_mapped(self):
        # Phillips and Sobolev map fully; Kankan II keeps uncertain names (e.g. 'Olivine?', 'Fper-(ol)') unmapped on purpose
        self.assertEqual(self.one(f"SELECT COUNT(*) FROM inclusion_observation WHERE phase_id IS NULL AND publication_id IN "
                                  f"({self.phillips}, {self.papers['sobolev-2004']['pub']})"), 0)

    def test_table4_reuses_table3_inclusions(self):
        # DP473 has a touching and a non-touching gt + opx pair; each set must get its own pair
        rows = self.db.execute("""
            SELECT s.label, a.value_text FROM inclusion_set s
            JOIN inclusion_set_member m ON m.inclusion_set_id = s.id
            JOIN assertion a ON a.inclusion_observation_id = m.inclusion_observation_id AND a.property_code = 'touching'
            WHERE s.label LIKE 'DP473 %' ORDER BY s.label""").fetchall()
        self.assertEqual(rows, [("DP473 non-touching gt + opx", "n")] * 2 + [("DP473 touching gt + opx", "y")] * 2)


if __name__ == "__main__":
    unittest.main()
