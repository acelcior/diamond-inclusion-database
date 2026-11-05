"""Checks that schema/001_core.sql loads, round-trips a record, and rejects bad rows.

Run from the project folder:  python3 -m unittest tests/test_schema.py

All data here is ILLUSTRATIVE (CLAUDE.md rule 9): invented values, not real observations.
"""
import sqlite3
import unittest
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "001_core.sql"


def new_db():
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA.read_text())
    db.executescript("""
        INSERT INTO unit (code, dimension) VALUES ('wt%', 'mass_fraction'), ('degC', 'temperature');
        INSERT INTO method (code, name) VALUES ('EPMA', 'Electron probe microanalysis');
        INSERT INTO quantity (code, kind, default_unit) VALUES
            ('SiO2', 'oxide', 'wt%'), ('TiO2', 'oxide', 'wt%'), ('T_equilibration', 'derived', 'degC');
        INSERT INTO property (code, applies_to) VALUES ('paragenesis', 'inclusion');
        INSERT INTO phase (id, name, phase_kind) VALUES (1, 'garnet', 'mineral_species');
        INSERT INTO publication (id, citation, pub_type)
            VALUES (1, 'ILLUSTRATIVE EXAMPLE - not a real publication', 'other');
        INSERT INTO evidence (id, publication_id, source_type, table_label, row_label)
            VALUES (1, 1, 'paper', 'Table 1', 'X-1');
    """)
    return db


def add_inclusion(db, obs_id):
    """Illustrative diamond + inclusion observation pair sharing obs_id."""
    db.execute("INSERT INTO diamond_observation (id, publication_id, evidence_id) VALUES (?, 1, 1)", (obs_id,))
    db.execute("""INSERT INTO inclusion_observation
                  (id, publication_id, evidence_id, diamond_observation_id, reported_phase, phase_id, phase_match_status)
                  VALUES (?, 1, 1, ?, 'gt', 1, 'mapped')""", (obs_id, obs_id))


class SchemaTest(unittest.TestCase):
    def setUp(self):
        self.db = new_db()

    def rejects(self, sql, params=()):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(sql, params)

    def test_record_round_trips(self):
        add_inclusion(self.db, 1)
        db = self.db
        db.execute("INSERT INTO specimen_identifier (diamond_observation_id, identifier, id_type) VALUES (1, 'X-1', 'author_sample')")
        db.execute("INSERT INTO measurement (id, inclusion_observation_id, method_code, evidence_id) VALUES (1, 1, 'EPMA', 1)")
        db.execute("""INSERT INTO measured_value (measurement_id, quantity_code, original_text, original_unit,
                      value, value_status, derivation) VALUES (1, 'SiO2', '41.2', 'wt%', 41.2, 'reported', 'reported')""")
        db.execute("""INSERT INTO measured_value (measurement_id, quantity_code, original_text, detection_limit,
                      value_status, derivation) VALUES (1, 'TiO2', '<0.02', 0.02, 'below_detection', 'reported')""")
        db.execute("""INSERT INTO assertion (inclusion_observation_id, property_code, value_text, asserted_by,
                      value_status, derivation, evidence_id) VALUES (1, 'paragenesis', 'h', 'authors', 'reported', 'interpreted', 1)""")
        db.execute("""INSERT INTO derived_parameter (id, inclusion_observation_id, quantity_code, original_text, value,
                      method, assumptions, derivation, evidence_id)
                      VALUES (1, 1, 'T_equilibration', '1100', 1100, 'illustrative thermometer', 'P fixed at 50 kbar',
                              'calculated_by_authors', 1)""")
        db.execute("INSERT INTO derived_parameter_input VALUES (1, 1)")

        rows = db.execute("""
            SELECT io.reported_phase, p.name, mv.quantity_code, mv.original_text, mv.value, mv.value_status, e.table_label
            FROM inclusion_observation io
            JOIN phase p ON p.id = io.phase_id
            JOIN measurement m ON m.inclusion_observation_id = io.id
            JOIN measured_value mv ON mv.measurement_id = m.id
            JOIN evidence e ON e.id = m.evidence_id
            ORDER BY mv.quantity_code""").fetchall()
        self.assertEqual(rows, [
            ("gt", "garnet", "SiO2", "41.2", 41.2, "reported", "Table 1"),
            ("gt", "garnet", "TiO2", "<0.02", None, "below_detection", "Table 1"),
        ])

    def test_value_status_must_match_value(self):
        add_inclusion(self.db, 1)
        self.db.execute("INSERT INTO measurement (id, inclusion_observation_id, evidence_id) VALUES (1, 1, 1)")
        insert = """INSERT INTO measured_value (measurement_id, quantity_code, original_text, value, value_status, derivation)
                    VALUES (1, 'SiO2', ?, ?, ?, 'reported')"""
        self.rejects(insert, ("41.2", None, "reported"))       # reported but no number
        self.rejects(insert, ("b.d.", 0.0, "below_detection"))  # below detection but a number

    def test_bad_rows_rejected(self):
        add_inclusion(self.db, 1)
        self.rejects("INSERT INTO inclusion_observation (publication_id, evidence_id, reported_phase, phase_id) VALUES (1, 1, 'x', 999)")  # unknown phase
        self.rejects("INSERT INTO inclusion_observation (publication_id, evidence_id, reported_phase, phase_match_status) VALUES (1, 1, 'x', 'mapped')")  # mapped, no phase
        self.rejects("INSERT INTO measurement (inclusion_observation_id, diamond_observation_id, evidence_id) VALUES (1, 1, 1)")  # two subjects
        self.rejects("INSERT INTO measurement (evidence_id) VALUES (1)")  # no subject
        self.rejects("INSERT INTO evidence (publication_id, source_type, excerpt) VALUES (1, 'paper', ?)", ("x" * 201,))
        self.rejects("INSERT INTO publication (citation, pub_type) VALUES ('x', 'blog')")
        self.rejects("""INSERT INTO assertion (inclusion_observation_id, property_code, value_text, asserted_by, value_status,
                        derivation, evidence_id) VALUES (1, 'paragenesis', 'h', 'authors', 'reported', 'guessed', 1)""")

    def test_locality_honesty(self):
        insert = """INSERT INTO locality (name, locality_type, latitude, longitude, crs, precision_class, coordinate_evidence_id)
                    VALUES ('illustrative', 'region', ?, ?, ?, ?, ?)"""
        self.rejects(insert, (95, 10, "EPSG:4326", "exact", 1))       # latitude out of range
        self.rejects(insert, (10, 10, None, "exact", 1))              # coordinates without CRS
        self.rejects(insert, (10, 10, "EPSG:4326", "exact", None))    # coordinates without a source
        self.rejects(insert, (10, 10, "EPSG:4326", "unknown", 1))     # unknown place with coordinates
        self.db.execute(insert, (None, None, None, "unknown", None))  # unknown locality is still storable

    def test_identity_clusters(self):
        for i in (1, 2, 3, 4):
            add_inclusion(self.db, i)
        link = """INSERT INTO inclusion_identity_link (observation_a, observation_b, basis, asserted_by, confidence, workflow_status)
                  VALUES (?, ?, 'shared_sample_id', 'curator', 'high', ?)"""
        self.db.execute(link, (1, 2, "approved"))
        self.db.execute(link, (2, 3, "approved"))
        self.db.execute(link, (3, 4, "pending_review"))  # not counted until approved
        self.rejects(link, (2, 1, "approved"))           # pairs stored once, a < b
        clusters = dict(self.db.execute("SELECT inclusion_observation_id, cluster_id FROM inclusion_cluster"))
        self.assertEqual(clusters, {1: 1, 2: 1, 3: 1, 4: 4})
        self.assertEqual(len(set(clusters.values())), 2)  # 4 observations, 2 physical inclusions


if __name__ == "__main__":
    unittest.main()
