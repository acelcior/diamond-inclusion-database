"""Literature inventory: find candidate papers and keep one master list (bibliography/inventory.csv).

Workflow and reasons: docs/literature-workflow.md. Run from the project folder:

  .venv/bin/python -I scripts/literature.py seed      # seed papers + every DOI the Stachel compilations cite
  python3 -I scripts/literature.py chain              # citation chaining (OpenAlex) from every paper triaged 'relevant'
  python3 -I scripts/literature.py add FILE --source "connected-papers:Phillips 2004"
                                                      # DOIs or titles from Connected Papers / Consensus / Zotero / a list
  python3 -I scripts/literature.py next 50            # the next candidates to triage, with abstracts (not stored)
  python3 -I scripts/literature.py decide FILE        # apply a CSV of openalex_id,triage,note decisions
  python3 -I scripts/literature.py status             # counts
  python3 -I scripts/literature.py queue              # ranked extraction queue of relevant papers -> bibliography/extraction-queue.csv
  python3 -I scripts/literature.py fetch [--dry-run] [--max N]
                                                      # download the open-access PDFs of queued papers -> papers/oa/

Metadata comes from OpenAlex (CC0). Abstracts are read to set a priority but never stored.
An OpenAlex key is optional: put it in the file .openalex-key (gitignored) or OPENALEX_API_KEY.
Nothing is guessed: a title that does not match exactly is reported, not added.
"""
import csv
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "bibliography" / "inventory.csv"
FIELDS = ["openalex_id", "doi", "title", "year", "first_author", "venue", "type", "oa_status",
          "found_by", "found_date", "links", "priority", "triage", "triage_note", "chained_on"]
TRIAGE = ["relevant", "maybe", "candidate", "not_relevant", "duplicate"]
SELECT = "id,doi,title,publication_year,authorships,primary_location,type,open_access,abstract_inverted_index"
UA = {"User-Agent": "diamond-inclusion-database literature inventory (research project)"}  # no personal details
KEY_FILE = ROOT / ".openalex-key"
BUDGET_FLOOR_USD = 0.005  # stop and save before OpenAlex's daily budget runs out; the next run resumes


class BudgetUsed(Exception):
    pass


def api_key():
    return os.environ.get("OPENALEX_API_KEY") or (KEY_FILE.read_text().strip() if KEY_FILE.exists() else "")


def get(path, **params):
    if api_key():
        params["api_key"] = api_key()
    url = "https://api.openalex.org/" + path + "?" + urllib.parse.urlencode(params, safe=":|/,")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                left = r.headers.get("X-RateLimit-Remaining-USD")
                data = json.load(r)
            if left is not None and float(left) < BUDGET_FLOOR_USD:
                raise BudgetUsed(left)
            time.sleep(0.15)
            return data
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 429) and b"budget" in e.read().lower():
                raise BudgetUsed("0")
            if e.code == 404 or attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def short_id(w):
    return (w.get("id") or "").rsplit("/", 1)[-1]


def abstract(w):
    inv = w.get("abstract_inverted_index") or {}
    return " ".join(word for word, _ in sorted(((k, p) for k, ps in inv.items() for p in ps), key=lambda x: x[1]))


def priority(w):
    """A reading order, not a relevance decision (that is the triage column)."""
    text = (w.get("title") or "") + " " + abstract(w)
    if not re.search(r"diamond", text, re.I):
        return None
    if re.search(r"inclusion", text, re.I):
        return "high"
    # many publishers withhold abstracts from OpenAlex; without one we cannot tell, so read it early
    return "high" if not w.get("abstract_inverted_index") else "medium"


def row_from(w, found_by):
    loc = (w.get("primary_location") or {}).get("source") or {}
    auth = (w.get("authorships") or [{}])
    return {"openalex_id": short_id(w), "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower(),
            "title": w.get("title") or "", "year": w.get("publication_year") or "",
            "first_author": ((auth[0] if auth else {}).get("author") or {}).get("display_name", ""),
            "venue": loc.get("display_name", ""), "type": w.get("type") or "",
            "oa_status": (w.get("open_access") or {}).get("oa_status", ""),
            "found_by": found_by, "found_date": date.today().isoformat(), "links": 0,
            "priority": priority(w) or "low", "triage": "candidate", "triage_note": "", "chained_on": ""}


class Inventory:
    def __init__(self, path=INVENTORY):
        self.path = path
        self.rows = []
        if path.exists():
            with open(path, encoding="utf-8", newline="") as f:
                self.rows = list(csv.DictReader(f))
        self.index = {}
        for r in self.rows:
            self._index(r)

    def _index(self, r):
        for k in (r["openalex_id"], r["doi"], norm_title(r["title"]) + str(r["year"])):
            if k and k != str(r["year"]):
                self.index[k] = r

    def find(self, w):
        doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        for k in (short_id(w), doi, norm_title(w.get("title")) + str(w.get("publication_year") or "")):
            if k and k in self.index:
                return self.index[k]

    def add(self, w, found_by, triage=None, link=False):
        """Add a work (or note another source for one already listed). Returns (row, is_new)."""
        r = self.find(w)
        new = r is None
        if new:
            r = row_from(w, found_by)
            self.rows.append(r)
            self._index(r)
        elif found_by.split(":")[0] not in r["found_by"]:
            r["found_by"] += "; " + found_by
        if triage and r["triage"] in ("candidate", ""):
            r["triage"] = triage
        if link:
            r["links"] = int(r["links"] or 0) + 1
        return r, new

    def save(self):
        self.path.parent.mkdir(exist_ok=True)
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(self.rows)


def works(filter_, select=SELECT):
    """All works matching an OpenAlex filter (page= paging: works without a key, unlike cursor=)."""
    out, page = [], 1
    while True:
        d = get("works", filter=filter_, select=select, **{"per-page": 200, "page": page})
        out += d["results"]
        if not d["results"] or len(out) >= d["meta"]["count"]:
            return out
        page += 1


def by_ids(ids, key="ids.openalex", select=SELECT):
    out = []
    for i in range(0, len(ids), 50):
        out += works(f"{key}:" + "|".join(ids[i:i + 50]), select)
    return out


# ---------- commands ----------

def compilation_dois():
    """DOIs cited by the Stachel compilations (local CC0 files; Walter and Smit carry no DOIs)."""
    import openpyxl  # in .venv only
    found = {}
    for name, sheet in [("stachel-major/Diamond_Database_Oct-2021.xlsm", "All diamonds"),
                        ("stachel-traces/Diamond_Traces_Oct-2021.xlsm", "All")]:
        f = ROOT / "papers" / "compilations" / name
        if not f.exists():
            print("missing (skipped):", f)
            continue
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)  # values only; macros never run
        it = wb[sheet].iter_rows(values_only=True)
        hdr = next(it)
        cols = [i for i, h in enumerate(hdr) if h and "doi" in str(h).lower()]
        for row in it:
            for i in cols:
                for m in re.findall(r"10\.\d{4,9}/[^\s,;]+", str(row[i] or "")):
                    found.setdefault(m.rstrip(".").lower(), "compilation:" + name.split("/")[0])
    return found


def cmd_seed(inv):
    sys.path.insert(0, str(ROOT / "scripts"))
    from licence_audit import sources  # same seed list as the licence register
    dois = {doi.lower(): "seed:" + key for key, doi, _ in sources() if not doi.startswith(("10.7939", "10.5683"))}
    dois.update({d: s for d, s in compilation_dois().items() if d not in dois})
    ws = by_ids(list(dois), key="doi")
    seen = set()
    for w in ws:
        d = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        seen.add(d)
        inv.add(w, dois.get(d, "seed"), triage="relevant")
    for d in sorted(set(dois) - seen):
        try:  # single lookups are free and resolve DOI aliases (e.g. 10.2113/gsecongeo.96.1.0159)
            w = get("works/doi:" + urllib.parse.quote(d, safe="/()"), select=SELECT)
            r, _ = inv.add(w, dois[d], triage="relevant")
            r["triage_note"] = f"source cites it as DOI {d}"
        except urllib.error.HTTPError:  # not in OpenAlex: keep the DOI as printed, invent nothing
            r, new = inv.add({"doi": d, "title": ""}, dois[d], triage="relevant")
            if new:
                r["triage_note"] = "DOI as printed in the source, not found in OpenAlex (may be mistyped or truncated)"
    print(f"seeded {len(dois)} DOIs ({len(ws)} found in OpenAlex)")


def cmd_chain(inv, limit=None):
    """Backward (references) + forward (citing) chaining from each 'relevant' paper.
    First run: everything. Later runs: only papers citing it published since the last run."""
    todo = [r for r in inv.rows if r["triage"] == "relevant" and r["openalex_id"]
            and r["chained_on"] != date.today().isoformat()]
    added = 0
    try:
        for n, r in enumerate(todo[:limit] if limit else todo, 1):
            src = f"chain:{r['first_author'].split(' ')[-1]} {r['year']}"
            cands = []
            if not r["chained_on"]:
                me = works(f"ids.openalex:{r['openalex_id']}")
                refs = [x.rsplit("/", 1)[-1] for x in (me[0].get("referenced_works") if me else []) or []]
                cands += by_ids(refs) if refs else []
                cands += works(f"cites:{r['openalex_id']}")
            else:
                cands += works(f"cites:{r['openalex_id']},from_created_date:{r['chained_on']}")
            for w in cands:
                if inv.find(w) or priority(w):  # shortcut: drops papers with no 'diamond' in title/abstract (2 of 76 compilation papers in the test); compilations and manual tools are the safety net
                    _, new = inv.add(w, src, link=True)
                    added += new
            r["chained_on"] = date.today().isoformat()
            if n % 10 == 0:
                inv.save()
                print(f"  {n}/{len(todo)} chained, {added} new candidates so far")
    except BudgetUsed:
        print("OpenAlex daily budget nearly used: progress saved, run 'chain' again tomorrow to continue.")
    print(f"chained {sum(r['chained_on'] == date.today().isoformat() for r in todo)} papers; {added} new candidates")


def parse_list(text):
    """DOIs anywhere in the text (BibTeX, RIS, CSV, a pasted list); lines without a DOI are treated as titles."""
    dois, titles = [], []
    for line in text.splitlines():
        found = re.findall(r"10\.\d{4,9}/[^\s\"'<>{},;]+", line)
        if found:
            dois += [d.rstrip(".").lower() for d in found]
        elif len(line.strip()) > 20 and not re.match(r"\s*(@|[A-Z]{2}  -|\w+\s*=)", line):  # skip BibTeX/RIS field lines
            titles.append(line.strip().split(" | ")[0])
    return list(dict.fromkeys(dois)), titles


def cmd_add(inv, file, source):
    dois, titles = parse_list(Path(file).read_text(encoding="utf-8", errors="replace"))
    new = 0
    for w in by_ids(dois, key="doi") if dois else []:
        new += inv.add(w, source)[1]
    unmatched = []
    for t in titles:
        hits = get("works", filter="title.search:" + re.sub(r"[,|:]", " ", t), select=SELECT, **{"per-page": 5})["results"]
        exact = [w for w in hits if norm_title(w.get("title")) == norm_title(t)]
        if len(exact) >= 1:
            new += inv.add(exact[0], source)[1]
        else:
            unmatched.append(t)
    print(f"{len(dois)} DOIs + {len(titles) - len(unmatched)} titles matched; {new} new to the inventory")
    for t in unmatched:
        print("  no exact title match (not added):", t[:100])


def cmd_next(inv, n):
    """Untriaged candidates, high priority first, most-linked first; abstract shown for reading only."""
    order = {"high": 0, "medium": 1, "low": 2}
    todo = sorted((r for r in inv.rows if r["triage"] == "candidate" and r["openalex_id"]),
                  key=lambda r: (order.get(r["priority"], 3), -int(r["links"] or 0)))[:n]
    ws = {short_id(w): w for w in by_ids([r["openalex_id"] for r in todo])}
    for r in todo:
        w = ws.get(r["openalex_id"], {})
        print(f"\n{r['openalex_id']} | {r['year']} | {r['first_author']} | {r['venue']} | {r['type']} | links {r['links']}")
        print("  " + r["title"])
        print("  " + (abstract(w)[:700] or "(no abstract in OpenAlex)"))


def cmd_decide(inv, file):
    """CSV with columns openalex_id,triage,note. Only candidates change; earlier decisions are never overwritten."""
    with open(file, encoding="utf-8", newline="") as f:
        decisions = list(csv.DictReader(f))
    by_id = {r["openalex_id"]: r for r in inv.rows}
    done = 0
    for d in decisions:
        r = by_id.get(d["openalex_id"].strip())
        if d["triage"] not in TRIAGE or r is None or r["triage"] != "candidate":
            print("  skipped:", d["openalex_id"], d["triage"], "(unknown id, bad value, or already triaged)")
            continue
        r["triage"], r["triage_note"] = d["triage"], d["note"].strip()
        done += 1
    print(f"applied {done} of {len(decisions)} decisions")


QUEUE = ROOT / "bibliography" / "extraction-queue.csv"
OA_READABLE = {"gold", "hybrid", "diamond", "green", "bronze"}  # a copy can be read; licence for mining differs
TIERS = {  # (post-compilation, readable) -> tier letter and the reason, fixed rule so the order is reproducible
    (True, True): ("A", "published after the Stachel compilation (2022+) and a readable copy is online"),
    (True, False): ("B", "published after the Stachel compilation (2022+), closed access"),
    (False, True): ("C", "pre-2022, readable copy online"),
    (False, False): ("D", "pre-2022, closed access"),
}


def cmd_queue(inv):
    """Rank every 'relevant' paper for extraction. Tier by gap (new papers first) and access; within a tier by
    links then year. Papers already extracted (DOI in gold/*/source.json) go last. Compiled = cited by the Stachel
    compilation, so its major-element data is already in the database and only the rest is new."""
    gold_dois = set()
    for f in [*(ROOT / "gold").glob("*/source.json"), *(ROOT / "extracted").glob("*/source.json")]:
        gold_dois.add(json.loads(f.read_text()).get("publication", {}).get("doi", "").lower())
    rows = []
    for r in inv.rows:
        if r["triage"] != "relevant":
            continue
        post = bool(r["year"]) and int(r["year"]) >= 2022
        tier, why = TIERS[(post, r["oa_status"] in OA_READABLE)]
        extracted = r["doi"].lower() in gold_dois if r["doi"] else False
        rows.append({"tier": "done" if extracted else tier, "why": "already extracted into gold/" if extracted else why,
                     "compiled": "yes" if "compilation:" in r["found_by"] else "",
                     "seed": "yes" if "seed:" in r["found_by"] else "",
                     **{k: r[k] for k in ("openalex_id", "doi", "year", "first_author", "title", "venue", "oa_status",
                                           "links", "triage_note")}})
    # reviews and compilations last within a tier: they rarely print primary tables (judged from the triage note)
    rows.sort(key=lambda x: (x["tier"] == "done", x["tier"], "review" in x["triage_note"].lower(),
                             -int(x["links"] or 0), -int(x["year"] or 0)))
    with open(QUEUE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rank"] + list(rows[0]))
        w.writeheader()
        for n, x in enumerate(rows, 1):
            w.writerow({"rank": n, **x})
    from collections import Counter
    print(f"{len(rows)} relevant papers ranked -> {QUEUE.relative_to(ROOT)}; tiers:", dict(Counter(x["tier"] for x in rows)))


DOWNLOADS = ROOT / "bibliography" / "downloads.csv"   # what was fetched, from where, under which licence
OA_DIR = ROOT / "papers" / "oa"                       # gitignored with the rest of papers/
DL_FIELDS = ["openalex_id", "doi", "file", "status", "url", "host", "licence", "version", "bytes", "date"]
MAX_PDF = 80 * 2**20
VERSION_RANK = {"publishedVersion": 0, "acceptedVersion": 1}  # anything else (preprints) last: tables may differ


def pdf_name(r, taken):
    """firstauthor-year.pdf as elsewhere in papers/; the OpenAlex id is added only when two papers would share a name."""
    last = (r["first_author"].split() or ["unknown"])[-1]
    family = re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", last).lower()) or "unknown"
    name = f"{family}-{r['year']}.pdf"
    return name if name not in taken else f"{family}-{r['year']}-{r['openalex_id'].lower()}.pdf"


def oa_copies(w):
    """Open copies OpenAlex lists with a direct PDF link: published version first, then accepted, then preprints."""
    seen, out = set(), []
    for loc in [w.get("best_oa_location")] + (w.get("locations") or []):
        url = (loc or {}).get("pdf_url") or ""
        if loc and loc.get("is_oa") and url.startswith("https://") and url not in seen:
            seen.add(url)
            out.append(loc)
    return sorted(out, key=lambda loc: VERSION_RANK.get(loc.get("version"), 2))


def fetch_pdf(url, dest):
    """Save url to dest only if it really is a PDF (publishers often answer a script with a login or landing page)."""
    req = urllib.request.Request(url, headers={**UA, "Accept": "application/pdf"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read(MAX_PDF + 1)
    if not data.startswith(b"%PDF"):
        raise ValueError("not a PDF")
    if len(data) > MAX_PDF:
        raise ValueError("over the size limit")
    dest.write_bytes(data)
    return len(data)


def cmd_fetch(dry_run=False, limit=None):
    """Download open-access PDFs for queued papers, in queue order. Only copies OpenAlex marks as open are used;
    closed papers are never touched (they come from the library, by hand). Reruns skip what is already there."""
    from collections import Counter
    queue = [r for r in csv.DictReader(open(QUEUE, encoding="utf-8"))
             if r["tier"] != "done" and r["oa_status"] in OA_READABLE]
    log = {r["openalex_id"]: r for r in csv.DictReader(open(DOWNLOADS, encoding="utf-8"))} if DOWNLOADS.exists() else {}
    have = lambda i: log.get(i, {}).get("status") == "downloaded" and (OA_DIR / log[i]["file"]).exists()
    todo = [r for r in queue if not have(r["openalex_id"])][:limit]
    meta = {short_id(w): w for w in by_ids([r["openalex_id"] for r in todo], select="id,best_oa_location,locations")}
    taken = {x["file"] for i, x in log.items() if have(i)} | {p.name for p in OA_DIR.glob("*.pdf")}
    OA_DIR.mkdir(parents=True, exist_ok=True)
    for r in todo:
        copies = oa_copies(meta.get(r["openalex_id"], {}))
        row = {"openalex_id": r["openalex_id"], "doi": r["doi"], "file": "", "status": "no direct PDF link", "url": "",
               "host": "", "licence": "", "version": "", "bytes": "", "date": date.today().isoformat()}
        for loc in copies:
            row.update(url=loc["pdf_url"], host=urllib.parse.urlparse(loc["pdf_url"]).netloc,
                       licence=loc.get("license") or "none stated", version=loc.get("version") or "")
            if dry_run:
                row["status"] = "would download"
                break
            name = pdf_name(r, taken)
            try:
                row.update(bytes=fetch_pdf(loc["pdf_url"], OA_DIR / name), file=name, status="downloaded")
                taken.add(name)
                break
            except (urllib.error.URLError, ValueError, TimeoutError, OSError) as e:
                row["status"] = f"failed: {getattr(e, 'code', None) or getattr(e, 'reason', None) or e}"
            finally:
                time.sleep(1)  # be polite to publishers and repositories
        log[r["openalex_id"]] = row
        print(f"{row['status']:<22} {r['first_author'][:22]:<22} {r['year']}  {row['host']}")
    if not dry_run:
        with open(DOWNLOADS, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=DL_FIELDS)
            w.writeheader()
            w.writerows(log.values())
    print(dict(Counter(log[r["openalex_id"]]["status"].split(":")[0] for r in todo)),
          "| already downloaded:", len(queue) - len([r for r in queue if not have(r["openalex_id"])]) if dry_run else
          sum(have(r["openalex_id"]) for r in queue), "of", len(queue), "open-access papers in the queue")
    if not dry_run:
        write_manual_list()


MANUAL = ROOT / "bibliography" / "manual-downloads.md"


def write_manual_list():
    """The queued papers a script cannot or may not fetch, as clickable DOI links in queue order."""
    log = {r["openalex_id"]: r for r in csv.DictReader(open(DOWNLOADS, encoding="utf-8"))} if DOWNLOADS.exists() else {}
    groups = {"Free to read, but the script could not get the PDF": [], "Closed access, 2022 or later": [],
              "Closed access, older, not in the Stachel compilation": [],
              "Closed access, older, major elements already in the Stachel compilation": []}
    for r in csv.DictReader(open(QUEUE, encoding="utf-8")):
        if r["tier"] == "done" or log.get(r["openalex_id"], {}).get("status") == "downloaded":
            continue
        key = list(groups)[0 if r["oa_status"] in OA_READABLE else 1 if r["tier"] == "B" else 3 if r["compiled"] else 2]
        link = f"https://doi.org/{r['doi']}" if r["doi"] else f"https://openalex.org/{r['openalex_id']}"
        groups[key].append(f"- [{r['first_author']} ({r['year']}) {r['title'][:90]}]({link}), {r['venue'] or 'venue not listed'}")
    out = ["# Papers to download by hand", "",
           "Written by `scripts/literature.py fetch`; do not edit. Open a link (through the library for closed papers),",
           "save the PDF and any data supplement into `papers/inbox/` under any name. Best queue rank first.", ""]
    for title, lines in groups.items():
        out += [f"## {title} ({len(lines)})", "", *lines, ""]
    MANUAL.write_text("\n".join(out), encoding="utf-8")
    print({k: len(v) for k, v in groups.items()}, "->", MANUAL.relative_to(ROOT))


def cmd_status(inv):
    from collections import Counter
    print(f"{len(inv.rows)} papers in {INVENTORY.relative_to(ROOT)}")
    print("triage:  ", dict(Counter(r["triage"] for r in inv.rows)))
    cand = [r for r in inv.rows if r["triage"] == "candidate"]
    print("to triage by priority:", dict(Counter(r["priority"] for r in cand)))
    print("found by:", dict(Counter(s.strip().split(":")[0] for r in inv.rows for s in r["found_by"].split(";"))))


def main(argv):
    if not argv or argv[0] not in ("seed", "chain", "add", "next", "decide", "status", "queue", "fetch"):
        print(__doc__)
        return
    if argv[0] == "fetch":
        return cmd_fetch("--dry-run" in argv, int(argv[argv.index("--max") + 1]) if "--max" in argv else None)
    inv = Inventory()
    if argv[0] == "next":
        return cmd_next(inv, int(argv[1]) if len(argv) > 1 else 50)
    if argv[0] == "queue":
        return cmd_queue(inv)
    if argv[0] == "seed":
        cmd_seed(inv)
    elif argv[0] == "chain":
        cmd_chain(inv, int(argv[argv.index("--max") + 1]) if "--max" in argv else None)
    elif argv[0] == "add":
        cmd_add(inv, argv[1], argv[argv.index("--source") + 1] if "--source" in argv else "manual")
    elif argv[0] == "decide":
        cmd_decide(inv, argv[1])
    if argv[0] != "status":
        inv.save()
    cmd_status(inv)


if __name__ == "__main__":
    main(sys.argv[1:])
