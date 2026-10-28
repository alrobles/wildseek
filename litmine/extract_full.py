"""litmine Capa 2 — typed edge extraction over triage-YES chunks.

Same output schema as extract.py but the input is raw full-text
passages (sections.parquet), which carry NO PubTator entity
annotations — the model names species textually and a post-pass
can resolve names->TaxIDs when needed.

    python litmine/extract_full.py \
        --triage data/litmine/triage.parquet \
        --sections data/litmine/sections.parquet \
        --out data/litmine/edges_fulltext.csv --jobs 4

Resume: (pmid, section_type, offset) already in --out are skipped.
"""
import argparse
import csv
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from meta_client import MetaClient  # noqa: E402

RELATIONS = ("parasite_of", "host_of", "vector_of", "reservoir_of",
             "intermediate_host_of", "dead_end", "no_detection")

SYS = """You extract parasite/pathogen<->host relations from a text
chunk of a scientific paper. For EVERY pathogen-host relation the
text states, output one JSON object in a list:
{"parasite": name as written, "host": name as written,
 "relation": one of parasite_of|host_of|vector_of|reservoir_of|
   intermediate_host_of|dead_end|no_detection,
 "evidence_span": exact quote <=30 words, "confidence": 0-1,
 "geo": str|null, "date": str|null, "method": str|null}
Rules: primary findings only. Specific taxa (species/genus named),
not vague groups ("mammals", "wildlife"). parasite must differ from
host. no_detection = host sampled and pathogen NOT found. If the
chunk states none, output []. Output ONLY the JSON list."""

FIELDS = ["pmid", "pmcid", "section_type", "offset",
          "parasite", "host", "relation", "confidence",
          "evidence_span", "geo", "date", "method"]


def extract_chunk(client, model, text, retries=3):
    for att in range(retries):
        try:
            r = client.chat(
                model=model, temperature=0, max_tokens=2048,
                messages=[{"role": "system", "content": SYS},
                          {"role": "user", "content": text}])
            break
        except Exception:
            if att == retries - 1:
                raise
            import time
            time.sleep(5 * (att + 1))
    m = re.search(r"\[.*\]", r["content"], re.S)
    try:
        items = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        items = []
    out = []
    for e in items:
        try:
            p, h, rel = str(e["parasite"]).strip(), \
                str(e["host"]).strip(), e["relation"]
        except (KeyError, TypeError):
            continue
        if not p or not h or p.lower() == h.lower() or \
                rel not in RELATIONS:
            continue
        out.append(e | {"parasite": p, "host": h, "relation": rel})
    return out, r["usage"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--triage", default="data/litmine/triage.parquet")
    ap.add_argument("--sections", default="data/litmine/sections.parquet")
    ap.add_argument("--out", default="data/litmine/edges_fulltext.csv")
    ap.add_argument("--backend", default="fireworks",
                    choices=["fireworks", "local", "meta"])
    ap.add_argument("--model")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    import pandas as pd
    tr = pd.read_parquet(args.triage)
    yes = tr[tr.relevant == True][  # noqa: E712
        ["key", "pmid", "pmcid", "section_type", "offset"]]
    sec = pd.read_parquet(args.sections)
    sec["key"] = (sec.pmid.astype(str) + "|" + sec.section_type + "|" +
                  sec.offset.astype(str))
    chunks = sec.merge(yes[["key"]].drop_duplicates(), on="key")
    if args.limit:
        chunks = chunks.head(args.limit)
    print(f"YES chunks: {len(yes)} | to extract: {len(chunks)}",
          file=sys.stderr)

    client = {"fireworks": MetaClient.fireworks,
              "local": MetaClient.local,
              "meta": MetaClient}[args.backend]()
    model = args.model or ("accounts/fireworks/models/muse-spark-open"
                           if args.backend == "fireworks"
                           else "muse-spark-1.3")

    lock = threading.Lock()
    n_done = [0]
    mode = "a" if os.path.exists(args.out) else "w"
    with open(args.out, mode, newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if mode == "w":
            w.writeheader()

        def work(r):
            try:
                client.ledger_ctx.update({"pmid": str(r.pmid)})
                es, _ = extract_chunk(client, model, r.text)
                return r, es, None
            except Exception as e:
                return r, [], str(e)[:80]

        with ThreadPoolExecutor(args.jobs) as pool:
            futs = [pool.submit(work, r) for r in chunks.itertuples()]
            for fu in as_completed(futs):
                r, es, err = fu.result()
                if err is not None:
                    print(f"  {r.key}: FAIL {err}", file=sys.stderr)
                    continue
                for e in es:
                    e.update({"pmid": r.pmid, "pmcid": r.pmcid,
                              "section_type": r.section_type,
                              "offset": r.offset})
                with lock:
                    w.writerows(es)
                    f.flush()
                n_done[0] += 1
                if n_done[0] % 25 == 0:
                    print(f"  {n_done[0]}/{len(chunks)}",
                          file=sys.stderr)

    n_edges = sum(1 for _ in open(args.out)) - 1
    print(f"\nwrote {args.out}: {n_edges} edges from "
          f"{len(chunks)} chunks", file=sys.stderr)
    print(client.spend.report(), file=sys.stderr)


if __name__ == "__main__":
    main()
