"""litmine-monitor — daily delta loop (the differentiator).

ESearch on PMC for papers published in the last N days within a scope,
then the same factory: BioC sections -> spark-open triage -> typed
extraction -> dedupe into interactions.db (run_id=date) -> brief.

    python litmine/monitor.py run --days 2 --term "avian influenza"
    python litmine/monitor.py run --days 2 --dry-run   # no LLM calls
"""
import argparse
import datetime as dt
import json
import sys
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
import pmc_fetch  # noqa: E402
import interactions_db  # noqa: E402
from meta_client import MetaClient  # noqa: E402
from triage import triage_chunk  # noqa: E402
from extract_full import extract_chunk  # noqa: E402
from verify import BACKENDS, default_model, judge  # noqa: E402

LIT = Path("data/litmine")
ESEARCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
           "esearch.fcgi?db=pmc&retmode=json&retmax=500&"
           "datetype=pdat&term={term}&mindate={d0}&maxdate={d1}")
ESEARCH_PM = ESEARCH.replace("db=pmc", "db=pubmed")
EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
          "efetch.fcgi?db=pubmed&rettype=abstract&retmode=text&id={pmids}")
MODEL_TRIAGE = "accounts/fireworks/models/muse-spark-open"
MODEL_EXTRACT = "accounts/fireworks/models/muse-spark-open"


def delta_pmids(term, days):
    """New PMIDs via PubMed esearch (abstracts always available —
    recent papers are rarely OA-BioC, which the PMC route misses)."""
    d1 = dt.date.today()
    d0 = d1 - dt.timedelta(days=days)
    url = ESEARCH_PM.format(term=urllib.parse.quote(term),
                          d0=d0.strftime("%Y/%m/%d"),
                          d1=d1.strftime("%Y/%m/%d"))
    d = json.loads(pmc_fetch._get(url))
    return d.get("esearchresult", {}).get("idlist", [])


def fetch_abstracts(pmids, batch=100):
    """pmid list -> {pmid: abstract text} via efetch."""
    out = {}
    for i in range(0, len(pmids), batch):
        raw = pmc_fetch._get(EFETCH.format(pmids=",".join(pmids[i:i + batch])))
        text = raw.decode("utf-8", "replace")
        # efetch text format: records separated by blank lines, each
        # starts with 'N. J ...' header; PMID line ends each record
        for rec in text.split("\n\n\n"):
            m = rec.rfind("PMID:")
            if m == -1:
                continue
            pmid = rec[m + 5:].split()[0].strip()
            abs_txt = rec[:m].strip()
            if abs_txt:
                out[pmid] = abs_txt
        time.sleep(0.12)
    return out


def delta_pmcs(term, days):
    d1 = dt.date.today()
    d0 = d1 - dt.timedelta(days=days)
    url = ESEARCH.format(term=urllib.parse.quote(term),
                         d0=d0.strftime("%Y/%m/%d"),
                         d1=d1.strftime("%Y/%m/%d"))
    d = json.loads(pmc_fetch._get(url))
    return d.get("esearchresult", {}).get("idlist", [])


def run(args):
    run_id = dt.date.today().isoformat()
    conn = interactions_db.connect()
    pmids = delta_pmids(args.term, args.days)
    print(f"[monitor] {args.term!r} last {args.days}d -> "
          f"{len(pmids)} PMIDs", file=sys.stderr)
    if not pmids:
        return
    pmids = pmids[: args.max_papers]

    # hybrid fetch: OA papers -> BioC sections; the rest -> abstract
    p2c = pmc_fetch.resolve_pmcids(pmids)
    secs, oa, need_abs = [], set(), []
    for pmid in pmids:
        pmcid = p2c.get(pmid)
        doc = (pmc_fetch.fetch_bioc(pmcid, LIT / "pmc_cache_monitor")
               if pmcid else None)
        if doc:
            oa.add(pmid)
            for r in pmc_fetch.passages(doc):
                r["pmid"] = pmid
                r["pmcid"] = pmcid
                secs.append(r)
            time.sleep(0.12)
        else:
            need_abs.append(pmid)
    for pmid, txt in fetch_abstracts(need_abs).items():
        secs.append({"pmid": pmid, "pmcid": p2c.get(pmid, ""),
                     "section_type": "abstract", "offset": 0,
                     "text": txt, "pass_type": "abstract"})
    print(f"[monitor] {len(secs)} passages | OA fulltext {len(oa)}"
          f" | abstracts {len(need_abs)}", file=sys.stderr)
    brief = {"run_id": run_id, "term": args.term, "days": args.days,
             "pmids": len(pmids), "oa": len(oa),
             "passages": len(secs),
             "yes": 0, "edges": 0, "edges_new": 0, "verified": 0}
    if args.dry_run:
        return _brief(conn, brief, dry=True)

    fw = MetaClient.fireworks()
    judge_client = BACKENDS[args.judge_backend]()
    judge_model = default_model(args.judge_backend, args.judge_model)

    # triage
    yes_rows, tlock = [], threading.Lock()

    def _triage(r):
        try:
            d, _ = triage_chunk(fw, MODEL_TRIAGE, r["text"])
            return r, bool(d.get("relevant"))
        except Exception as e:
            print("  triage err:", e, file=sys.stderr)
            return r, False

    with ThreadPoolExecutor(args.jobs) as pool:
        for r, ok in pool.map(lambda rr: _triage(rr), secs):
            if ok:
                yes_rows.append(r)
    brief["yes"] = len(yes_rows)
    print(f"[monitor] triage YES {len(yes_rows)}/{len(secs)}",
          file=sys.stderr)

    # extract + judge + store (dedupe by UNIQUE key)
    wlock = threading.Lock()
    n_new = [0]

    def _edge(r):
        try:
            items, _ = extract_chunk(fw, MODEL_EXTRACT, r["text"])
        except Exception as e:
            print("  extract err:", e, file=sys.stderr)
            return r, []
        out = []
        for e in items:
            try:
                out.append((e, *judge(judge_client, judge_model, e)))
            except Exception as ex:
                out.append((e, None, f"err:{str(ex)[:40]}"))
        return r, out

    def _store(r, items):
        brief["edges"] += len(items)
        for e, ok, why in items:
            with wlock:
                before = conn.total_changes
                interactions_db._ins(conn, {
                    "pmid": r["pmid"], "pmcid": r["pmcid"],
                    "section_type": r["section_type"],
                    "offset": r["offset"], "parasite": e["parasite"],
                    "host": e["host"], "relation": e["relation"],
                    "evidence_span": e.get("evidence_span"),
                    "geo": e.get("geo"), "date": e.get("date"),
                    "method": e.get("method"),
                    "confidence": e.get("confidence"),
                    "verified": ok, "verdict_why": why,
                    "source": f"monitor:{args.term}",
                    "model_extract": MODEL_EXTRACT,
                    "model_judge": "muse-glimmer",
                    "run_id": run_id, "scope_id": args.term})
                if conn.total_changes > before:
                    n_new[0] += 1
                    brief["verified"] += int(bool(ok))
                conn.commit()

    with ThreadPoolExecutor(args.jobs) as pool:
        futs = [pool.submit(_edge, r) for r in yes_rows]
        for fu in as_completed(futs):
            r, items = fu.result()
            _store(r, items)
    brief["edges_new"] = n_new[0]
    print(f"[monitor] {brief['edges']} edges extracted, "
          f"{n_new[0]} NEW (dedup), {brief['verified']} verified",
          file=sys.stderr)
    _brief(conn, brief)
    print(fw.spend.report(), file=sys.stderr)


def _brief(conn, brief, dry=False):
    brief["dry_run"] = dry
    js = LIT / f"monitor_brief_{brief['run_id']}.json"
    json.dump(brief, open(js, "w"), indent=2)
    md = LIT / "monitor_brief.md"
    md.write_text(
        f"# litmine-monitor {brief['run_id']}\n\n"
        f"- scope: `{brief['term']}` last {brief['days']}d\n"
        f"- papers: {brief['pmids']} (OA: {brief.get('oa', 0)})"
        f" | passages: {brief['passages']}"
        f" | YES: {brief.get('yes', 0)}\n"
        f"- edges: {brief.get('edges', 0)} | NEW after dedupe: "
        f"{brief.get('edges_new', 0)} | verified: "
        f"{brief.get('verified', 0)}\n")
    print(f"[monitor] brief -> {md}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--term", default="avian influenza OR HPAI")
    r.add_argument("--days", type=int, default=2)
    r.add_argument("--max-papers", type=int, default=100)
    r.add_argument("--jobs", type=int, default=4)
    r.add_argument("--judge-backend", default="fireworks",
                   choices=sorted(BACKENDS))
    r.add_argument("--judge-model", default=None)
    r.add_argument("--dry-run", action="store_true")
    return ap


def main():
    a = build_parser().parse_args()
    if a.cmd == "run":
        run(a)


if __name__ == "__main__":
    main()
