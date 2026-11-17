"""Offline checks for extraction/extract.py (no PDF needed; illustrative table).  Run:  python3 -I tests/test_extract.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "extraction"))
import extract as E  # noqa: E402

TEXT = """Table 9
Illustrative analyses (not real data)
Sample   A-1            B-2
Mineral  Garnet  Opx    Olivine
SiO2     41.5    57.9   40.8
TiO2     0.05           <0.02
MgO      20.1    35.0   n.d.
Total    99.9    100.1  99.2
Ox       12      6      4
Total    8.01    4.00   3.00
Table 10
SiO2     1.0     2.0    3.0
"""
HINTS = {"tables": [{"label": "Table 9", "page": "5", "start": "Illustrative analyses", "mineral_row": "Mineral",
                     "fields": {"note": {"2": "footnote"}}}]}


class ExtractTest(unittest.TestCase):
    def test_columns_samples_blanks_and_table_end(self):
        rows = E.extract(HINTS, TEXT)
        self.assertEqual([(r["sample_no"], r["mineral"]) for r in rows],
                         [("A-1", "Garnet"), ("A-1", "Opx"), ("B-2", "Olivine")])     # one name over two columns
        self.assertEqual([r["TiO2"] for r in rows], ["0.05", "", "<0.02"])             # blank cell placed by position
        self.assertEqual([r["Total"] for r in rows], ["99.9", "100.1", "99.2"])        # not the cation total
        self.assertEqual([r["SiO2"] for r in rows], ["41.5", "57.9", "40.8"])          # Table 10 is not read
        self.assertEqual((rows[2]["MgO"], rows[2]["note"], rows[0]["note"], rows[2]["column"]), ("n.d.", "footnote", "", 3))

    def test_compare_finds_a_changed_cell(self):
        rows = E.extract(HINTS, TEXT)
        checked = [dict(r, column=str(r["column"])) for r in rows]
        self.assertEqual(E.compare(rows, checked)[2], [])
        checked[1]["SiO2"] = "57.8"
        self.assertEqual(E.compare(rows, checked)[2], [(2, "SiO2", "57.9", "57.8")])


if __name__ == "__main__":
    unittest.main()
