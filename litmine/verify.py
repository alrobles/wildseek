"""litmine JUDGE — verify extracted edges against their evidence_span.

For each edge, a judge model answers whether the span supports the
claimed parasite<->host relation. Rows get verified / verdict_why
columns; unverified edges stay but are flagged (verified=False) so
downstream can filter. Backend is CLI-selectable (cloud default —
the local glimmer tunnel died with the cluster).

    python litmine/verify.py --edges data/litmine/edges_fulltext.csv \
        --jobs 4

Resume: rows already having verified!=NA in --out are skipped.
"""
import argparse
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from meta_client import (MODEL_AGENT, MODEL_BASETEN, MODEL_FW_JUDGE,  # noqa: E402
                         MODEL_LOCAL, MetaClient)

BACKENDS = {"local": MetaClient.local,
            "local_mi210": MetaClient.local_mi210,
            "fireworks": MetaClient.fireworks,
            "baseten": MetaClient.baseten,
            "meta": MetaClient}

_DEFAULT_MODEL = {"local": MODEL_LOCAL, "local_mi210": MODEL_LOCAL,
                  "fireworks": MODEL_FW_JUDGE, "baseten": MODEL_BASETEN,
                  "meta": MODEL_AGENT}


def default_model(backend: str, override: str | None) -> str:
    return override or _DEFAULT_MODEL[backend]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edges", required=True)
    ap.add_argument("--out")
    ap.add_argument("--backend", default="fireworks",
                    choices=sorted(BACKENDS))
    ap.add_argument("--model")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--limit", type=int)
    return ap

SYS = """You verify parasite-host edges against their evidence span.
Reply ONLY JSON: {"ok": true|false, "why": <=12 words}
ok=true only if the span states the pathogen was detected IN / isolated
FROM / infecting the host. A species name without the detection link,
or a vaccine/serology-only mention, is ok=false."""


def judge(client, model, e):
    q = json.dumps({"parasite": e.get("parasite") or e.get("para_texts"),
                    "host": e.get("host") or e.get("host_texts"),
                    "rel": e.get("relation"),
                    "span": str(e.get("evidence_span", ""))[:300]})
    for _ in range(2):
        r = client.chat(model=model, temperature=0, max_tokens=800,
                        messages=[{"role": "system", "content": SYS},
                                  {"role": "user", "content": q}])
        m = re.search(r"\{[^{}]*\}", r["content"] or "")
        try:
            d = json.loads(m.group(0)) if m else {}
        except json.JSONDecodeError:
            d = {}
        if "ok" in d:
            return d.get("ok"), str(d.get("why", ""))[:80]
    return None, "no-json"


def main():
    args = build_parser().parse_args()

    import pandas as pd
    df = pd.read_csv(args.edges)
    out = args.out or args.edges
    if "verified" not in df.columns:
        df["verified"] = None
        df["verdict_why"] = ""
    todo = df[df.verified.isna()]
    if args.limit:
        todo = todo.head(args.limit)
    print(f"edges {len(df)} | to verify {len(todo)}", file=sys.stderr)

    client = BACKENDS[args.backend]()
    model = default_model(args.backend, args.model)

    lock = threading.Lock()
    done_ct = [0]

    def work(i, r):
        try:
            rd = r.to_dict() if hasattr(r, "to_dict") else r._asdict()
            client.ledger_ctx.update({"pmid": str(rd.get("pmid"))})
            ok, why = judge(client, model, rd)
            return i, ok, why
        except Exception as e:
            return i, None, f"err:{str(e)[:40]}"

    idx = list(todo.index)
    with ThreadPoolExecutor(args.jobs) as pool:
        futs = {pool.submit(work, i, df.loc[i]): i for i in idx}
        for fu in as_completed(futs):
            i, ok, why = fu.result()
            with lock:
                df.at[i, "verified"] = ok
                df.at[i, "verdict_why"] = why
                done_ct[0] += 1
                if done_ct[0] % 25 == 0:
                    df.to_csv(out, index=False)
                    print(f"  {done_ct[0]}/{len(idx)}", file=sys.stderr)

    df.to_csv(out, index=False)
    ok = df.verified.sum()
    print(f"wrote {out}: verified {int(ok)}/{int(df.verified.notna().sum())}"
          f" ({100*ok/max(df.verified.notna().sum(),1):.0f}%)",
          file=sys.stderr)
    print(client.spend.report(), file=sys.stderr)


if __name__ == "__main__":
    main()
