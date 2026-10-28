"""Freeze the we-called-it card: top-N UNLABELED species by p_host.

The card is the prospective-validation artifact: predictions frozen
with a date; a future literature edge (PMID published after
predicted_on) that names one of these species as a host flips its
status to confirmed. Without a frozen date there is no claim.

    python pipeline/freeze_predictions.py          # write JSON
    python pipeline/freeze_predictions.py --check data/litmine/edges_zover.csv

--check: scan mined edges for host species matches and mark
status=confirmed when the edge's PMID postdates the freeze.
"""
import argparse
import json
import os
import sys
import time

OUT = os.environ.get("WILDSEEK_BEEG", ".")
SERVE = os.environ.get("WILDSEEK_SERVE", "data/serve")
CARD = f"{SERVE}/we_called_it.json"
TOP_N = 15


def freeze() -> dict:
    import pandas as pd
    s = pd.read_parquet(f"{SERVE}/susceptibility.parquet")
    top = (s[s.label != 1].nlargest(TOP_N, "p_host")
           [["specieskey", "species", "p_host", "p05", "p95"]])
    card = {
        "predicted_on": time.strftime("%Y-%m-%d"),
        "model": "xplus susceptibility (phy+env+geo)",
        "note": "unlabeled species ranked by p_host; confirmed when a "
                "literature edge published after predicted_on names "
                "the species as host",
        "predictions": [
            {"specieskey": int(r.specieskey), "species": r.species,
             "p_host": round(float(r.p_host), 3),
             "ci": [round(float(r.p05), 3), round(float(r.p95), 3)],
             "status": "awaiting-confirmation"}
            for r in top.itertuples()],
    }
    return card


def _pmid_pubdate() -> dict:
    """pmid -> publication date (YYYY-MM-DD best effort) so an edge can
    only confirm a prediction when the paper POSTDATES the freeze."""
    import re
    import pandas as pd
    out = {}
    try:
        c = pd.read_csv("data/litmine/zover_corpus.csv")
        doi2date = {str(r.doi).strip().lower(): str(r.date)
                    for r in c.itertuples() if pd.notna(r.doi)}
        p = pd.read_csv("data/litmine/zover_pmids.csv")
        for r in p.itertuples():
            d = doi2date.get(str(r.doi).strip().lower())
            if d:
                out[re.sub(r"\D", "", str(r.pmid))] = d[:10]
    except FileNotFoundError:
        pass
    try:
        g = pd.read_csv("data/litmine/virion_ebola_lassa_gold.csv")
        for pid_raw, yr in zip(g["PUBMED ID"], g["Year_Published"]):
            pid = re.sub(r"\D", "", str(pid_raw))
            if pid and pd.notna(yr) and pid not in out:
                out[pid] = f"{int(yr)}-01-01"   # year-only -> Jan 1
    except FileNotFoundError:
        pass
    return out


def check(card: dict, edges_csv: str) -> dict:
    """Mark predictions confirmed by a mined literature edge — only
    when the edge's PMID was published AFTER predicted_on."""
    import pandas as pd
    edges = pd.read_csv(edges_csv)
    host = {c for c in edges.columns
            if c.lower() in ("host", "host_texts", "host_name")}
    if not host:
        print("no host column in edges csv", file=sys.stderr)
        return card
    col = sorted(host)[0]
    frozen_on = card["predicted_on"]
    pubdate = _pmid_pubdate()
    pred_species = {p["species"].lower(): p for p in card["predictions"]}
    for r in edges.itertuples():
        h = getattr(r, col, None)
        if pd.isna(h):
            continue
        hit = None
        for name in str(h).replace(";", "|").split("|"):
            key = name.strip().lower()
            if key in pred_species:
                hit = pred_species[key]
        if hit is None or hit["status"] != "awaiting-confirmation":
            continue
        pid = str(getattr(r, "pmid", ""))
        d = pubdate.get(pid)
        if d is None:
            continue          # undated paper cannot confirm a dated claim
        if d > frozen_on:
            hit["status"] = "confirmed"
            hit["confirmed_by"] = f"pmid {pid} ({d})"
    return card


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", metavar="EDGES_CSV")
    args = ap.parse_args()
    if args.check:
        if not os.path.exists(CARD):
            sys.exit(f"{CARD} missing — run without --check first")
        card = check(json.load(open(CARD)), args.check)
    else:
        card = freeze()
    os.makedirs(SERVE, exist_ok=True)
    json.dump(card, open(CARD, "w"), indent=1)
    n_conf = sum(p["status"] == "confirmed" for p in card["predictions"])
    print(f"{CARD}: {len(card['predictions'])} predictions, "
          f"{n_conf} confirmed", file=sys.stderr)


if __name__ == "__main__":
    main()
