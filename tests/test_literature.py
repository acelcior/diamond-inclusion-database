"""Offline checks for scripts/literature.py (no network).  Run:  python3 -m unittest tests/test_literature.py"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import literature as L  # noqa: E402


def work(i, title, doi="", abstract=None, year=2004):
    return {"id": f"https://openalex.org/W{i}", "doi": f"https://doi.org/{doi}" if doi else None, "title": title,
            "publication_year": year, "abstract_inverted_index": {w: [n] for n, w in enumerate(abstract.split())}
            if abstract else None}


class LiteratureTest(unittest.TestCase):
    def test_parse_list(self):
        dois, titles = L.parse_list("@article{x,\n doi = {10.1016/j.lithos.2004.04.005},\n title = {Ignored field}\n}\n"
                                    "Rare and unusual mineral inclusions in diamonds from Mwadui, Tanzania | 1998\n"
                                    "https://doi.org/10.1007/S004100000173.\n")
        self.assertEqual(dois, ["10.1016/j.lithos.2004.04.005", "10.1007/s004100000173"])
        self.assertEqual(titles, ["Rare and unusual mineral inclusions in diamonds from Mwadui, Tanzania"])

    def test_priority(self):
        self.assertEqual(L.priority(work(1, "Garnet inclusions in diamonds")), "high")
        self.assertEqual(L.priority(work(2, "Diamonds from Wawa", abstract="carbon isotopes of diamond")), "medium")
        self.assertEqual(L.priority(work(3, "Diamonds from Wawa")), "high")  # no abstract: cannot tell, read early
        self.assertIsNone(L.priority(work(4, "Kimberlite emplacement", abstract="pipes and dykes")))

    def test_dedup_by_id_doi_and_title(self):
        inv = L.Inventory(Path(tempfile.mkdtemp()) / "inv.csv")
        inv.add(work(1, "Same Paper", doi="10.1/abc"), "seed:A1", triage="relevant")
        _, new_doi = inv.add(work(9, "Same paper", doi="10.1/ABC".lower()), "connected-papers:x")
        _, new_title = inv.add(work(8, "Same  paper!"), "consensus:q", link=True)
        self.assertEqual((new_doi, new_title, len(inv.rows)), (False, False, 1))
        r = inv.rows[0]
        self.assertEqual((r["found_by"], r["links"], r["triage"]), ("seed:A1; connected-papers:x; consensus:q", 1, "relevant"))
        inv.save()
        self.assertEqual(len(L.Inventory(inv.path).rows), 1)

    def test_decide_never_overwrites(self):
        d = Path(tempfile.mkdtemp())
        inv = L.Inventory(d / "inv.csv")
        inv.add(work(1, "A paper"), "chain:x")
        inv.add(work(2, "Seed paper"), "seed:A1", triage="relevant")
        (d / "dec.csv").write_text("openalex_id,triage,note\nW1,maybe,Claude: x\nW2,not_relevant,y\nW1,bogus,z\n")
        L.cmd_decide(inv, d / "dec.csv")
        self.assertEqual([(r["triage"], r["triage_note"]) for r in inv.rows], [("maybe", "Claude: x"), ("relevant", "")])


if __name__ == "__main__":
    unittest.main()
