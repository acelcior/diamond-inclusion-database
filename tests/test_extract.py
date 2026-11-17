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

    def test_indented_rows_printed_labels_and_continued_caption(self):
        text = """   Table 7. Illustrative (not real data)
  Sample    A-1     A-2
   SiO2     40.1    41.2
  Al2 O3    0.02    na
   TFeO     7.4     7.3
    Σ       47.52   48.5
     Si     0.99    1.00
   Table 7. Cont.
  Sample    A-3
   SiO2     39.9
    Σ       39.9
   Table 8. Something else
   SiO2     1.0
"""
        hints = {"tables": [{"label": "Table 7", "page": "9", "start": "Illustrative", "mineral": "olivine",
                             "labels": {"Al2 O3": "Al2O3", "Σ": "Total", "TFeO": "TFeO"}}]}
        rows = E.extract(hints, text)
        self.assertEqual([(r["sample_no"], r["SiO2"], r.get("Al2O3", ""), r.get("TFeO", ""), r["Total"]) for r in rows],
                         [("A-1", "40.1", "0.02", "7.4", "47.52"), ("A-2", "41.2", "na", "7.3", "48.5"),
                          ("A-3", "39.9", "", "", "39.9")])
        self.assertEqual(E.totals(rows), (3, []))

    def test_continuation_page_without_row_labels_takes_them_from_the_first_page(self):
        text = """Table 7. Illustrative (not real data)
 Sample   A-1    A-2
 Grain    1      2
  SiO2    40.1   41.2
   Σ      40.1   41.2
   Si     0.99   1.00
Table 7. Cont.
 A-3
 3
 39.9
 39.9
 0.98
"""
        hints = {"tables": [{"label": "Table 7", "page": ["9", "10"], "start": "Illustrative", "mineral": "olivine",
                             "continued": "unlabelled", "rows": {"Grain": "inclusion_label"}, "labels": {"Σ": "Total"}}]}
        rows = E.extract(hints, text)
        self.assertEqual([(r["page"], r["sample_no"], r["inclusion_label"], r["SiO2"], r["Total"]) for r in rows],
                         [("9", "A-1", "1", "40.1", "40.1"), ("9", "A-2", "2", "41.2", "41.2"), ("10", "A-3", "3", "39.9", "39.9")])

    def test_rows_layout_keeps_long_names_and_blank_cells_in_place(self):
        text = """Table 2
Illustrative averages (not real data)
Sample          Zone     n     SiO2    FeO     Total
X001 cpx A      core     15    51.4    4.7     56.1
X002 gnt B      rim?     9             13.8    13.8
* a footnote with 3 numbers 1.0 2.0
"""
        hints = {"tables": [{"label": "Table 2", "page": "4", "layout": "rows", "start": "Illustrative averages", "header": "Zone",
                             "columns": ["sample_no", "zone", "n_analyses", "SiO2", "FeO", "Total"], "text": ["zone"],
                             "split": {"sample_no": r"(?P<sample_no>\S+) (?P<mineral>\S+) (?P<inclusion_label>\S+)"}}]}
        rows = E.extract(hints, text)
        self.assertEqual([(r["sample_no"], r["mineral"], r["inclusion_label"], r["zone"], r["n_analyses"], r["SiO2"],
                           r["FeO"], r["Total"], r["column"]) for r in rows],
                         [("X001", "cpx", "A", "core", "15", "51.4", "4.7", "56.1", "row 1"),
                          ("X002", "gnt", "B", "rim?", "9", "", "13.8", "13.8", "row 2")])


if __name__ == "__main__":
    unittest.main()
