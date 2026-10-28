"""Bake the litmine loop ticker for the UI: papers -> chunks -> YES ->
edges -> rank, with clickable recent edges (PMID + evidence span).

    python pipeline/litmine_status.py        # writes
    data/serve/litmine_ticker.json (copied to app/data by export_serve)
"""
import json
import os
import time

import pandas as pd

LIT = "data/litmine"
SERVE = os.environ.get("WILDSEEK_SERVE", "data/serve")


def main():
    card = {"updated": time.strftime("%Y-%m-%d %H:%M"),
            "pipeline": "papers -> chunks -> YES triage -> typed "
                        "edges -> rank"}

    try:
        c = pd.read_csv(f"{LIT}/zover_corpus.csv")
        card["papers"] = len(c)
    except FileNotFoundError:
        card["papers"] = 0

    try:
        t = pd.read_parquet(f"{LIT}/triage.parquet")
        card["chunks"] = len(t)
        card["yes_chunks"] = int(t.relevant.sum())
    except FileNotFoundError:
        card["chunks"] = card["yes_chunks"] = 0

    edges = []
    for f in ("edges_fulltext.csv", "edges_zover.csv"):
        p = f"{LIT}/{f}"
        if not os.path.exists(p):
            continue
        e = pd.read_csv(p)
        e["source_file"] = f
        edges.append(e)
    if edges:
        e = pd.concat(edges, ignore_index=True)
        card["edges"] = len(e)
        keep = ["pmid", "parasite", "host", "parasite_taxid",
                "host_taxid", "relation", "evidence_span",
                "section_type"]
        cols = [c for c in keep if c in e.columns]
        card["recent"] = (e[cols].tail(12)
                          .fillna("").to_dict("records"))[::-1]
    else:
        card["edges"] = 0
        card["recent"] = []

    os.makedirs(SERVE, exist_ok=True)
    out = f"{SERVE}/litmine_ticker.json"
    json.dump(card, open(out, "w"), indent=1)
    print(f"wrote {out}: {card['papers']} papers / "
          f"{card['yes_chunks']} YES / {card['edges']} edges")


if __name__ == "__main__":
    main()
