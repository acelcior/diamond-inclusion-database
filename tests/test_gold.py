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
        cls.db, cls.flags = build_gold.build()

    def one(self, sql):
        return self.db.execute(sql).fetchone()[0]

    def test_counts(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM measurement"), 80)          # Table 3 columns
        self.assertEqual(self.one("SELECT COUNT(*) FROM measured_value"), 80 * 14)
        self.assertEqual(self.one("SELECT COUNT(*) FROM inclusion_set"), 50)        # Table 4 rows
        self.assertEqual(self.one("SELECT COUNT(*) FROM diamond_observation"), 50)  # 36 in Table 3 + 14 only in Table 4

    def test_printed_totals_add_up(self):
        res = build_gold.checks(self.db)
        self.assertEqual(res["sum_mismatch"], [])
        self.assertEqual(res["untraceable"], 0)

    def test_every_phase_mapped(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM inclusion_observation WHERE phase_id IS NULL"), 0)

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
