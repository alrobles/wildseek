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

    card["chunks"] = card["yes_chunks"] = 0
    for tf in ("triage.parquet", "triage_zover.parquet"):
        p = f"{LIT}/{tf}"
        if not os.path.exists(p):
            continue
        t = pd.read_parquet(p)
        card["chunks"] += len(t)
        card["yes_chunks"] += int(t.relevant.sum())

    edges = []
    inter = f"{LIT}/interactions.parquet"
    if os.path.exists(inter):
        # unified table — authoritative edge count + pair stats
        e = pd.read_parquet(inter)
        card["edges"] = len(e)
        card["unique_pairs"] = int(e.pair.nunique()) \
            if "pair" in e.columns else None
    else:
        for f in ("edges_fulltext.csv", "edges_zover.csv",
                  "edges_zover_full.csv"):
            p = f"{LIT}/{f}"
            if not os.path.exists(p):
                continue
            e0 = pd.read_csv(p)
            e0["source_file"] = f
            edges.append(e0)
        e = pd.concat(edges, ignore_index=True) if edges else None
        if e is not None:
            card["edges"] = len(e)
            card["unique_pairs"] = None
    if e is not None:
        if "verified" in e.columns:
            v = e.verified.fillna(False).astype(str).str.lower()
            card["verified"] = int((v == "true").sum())
        else:
            card["verified"] = 0
        named = e[e.parasite.fillna("").astype(str).str.len() > 0]
        show = named if len(named) >= 12 else e
        keep = ["pmid", "parasite", "host", "parasite_taxid",
                "host_taxid", "relation", "evidence_span",
                "section_type", "verified"]
        cols = [c for c in keep if c in e.columns]
        recent = show[cols].tail(12).astype(object)
        card["recent"] = (recent.where(recent.notna(), "")
                          .to_dict("records"))[::-1]
    else:
        card["edges"] = card["verified"] = 0
        card["recent"] = []

    os.makedirs(SERVE, exist_ok=True)
    out = f"{SERVE}/litmine_ticker.json"
    json.dump(card, open(out, "w"), indent=1)
    print(f"wrote {out}: {card['papers']} papers / "
          f"{card['yes_chunks']} YES / {card['edges']} edges")


if __name__ == "__main__":
    main()
