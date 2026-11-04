"""edges -> species_labels adapter (M13): literature-mined host edges
as prospective validation labels for p_host.

Maps each interaction's normalized host name to a universe specieskey
(binomial match first, then host_labels common_name for vernaculars),
then reports whether p_host ranks literature-evidenced
species above the rest — the prospective claim in numbers.

    python litmine/edges_to_labels.py
    -> data/litmine/species_labels.parquet + eval printout
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from leakage_audit import norm_name  # noqa: E402

LIT = "data/litmine"


def main():
    inter = pd.read_parquet(f"{LIT}/interactions.parquet")
    uni = pd.read_csv("data/species_winner.csv")[["specieskey", "species"]]
    sus = pd.read_parquet("data/serve/susceptibility.parquet")

    name2key = {norm_name(s): k for k, s in
                uni.itertuples(index=False)}
    # vernacular names resolve through host_labels' common_name map
    try:
        hl = pd.read_parquet("data/host_labels.parquet")
        common2key = {norm_name(c): k for c, k in
                      hl[["common_name", "specieskey"]]
                      .dropna().itertuples(index=False)}
    except Exception:
        common2key = {}
    # vernaculars not in host_labels resolve through the cached GBIF
    # vernacular->binomial map (litmine/gbif_host_map.csv)
    gbif2key = {}
    try:
        g = pd.read_csv(f"{LIT}/gbif_host_map.csv")
        gbif2key = {norm_name(h): k for h, k in
                    g[["host_norm", "specieskey"]]
                    .itertuples(index=False)}
    except Exception:
        pass
    k1 = inter["host_norm"].map(name2key)
    k2 = inter["host_norm"].map(common2key).fillna(
        inter["host_norm"].map(gbif2key))
    inter["host_key"] = k1.astype("float64").fillna(k2)
    matched = inter[inter.host_key.notna()].copy()
    matched["host_key"] = matched.host_key.astype(np.int64)

    # verified edges only count double: label strength = has a
    # judge-verified edge vs any edge
    v = (matched.verified.fillna("0").astype(str).str.lower()
         .str.replace(r"\.0$", "", regex=True).isin(["true", "1"]))
    lab = (matched.groupby("host_key")
           .agg(n_edges=("pair", "size"),
                n_verified=("pair", lambda s: int(
                    v.loc[s.index].sum())),
                parasites=("parasite_norm",
                           lambda s: "; ".join(sorted(set(s))[:6])),
                pmids=("pmid", lambda s: ";".join(sorted(set(s))[:6])))
           .reset_index()
           .rename(columns={"host_key": "specieskey"}))
    lab["lit_host"] = True

    out = Path(LIT) / "species_labels.parquet"
    lab.to_parquet(out, index=False)
    print(f"wrote {out}: {len(lab)} species with literature host edges "
          f"({int((lab.n_verified > 0).sum())} with verified edges)")

    # prospective eval: p_host should rank lit-evidenced hosts high
    ev = sus.merge(lab[["specieskey", "lit_host"]], on="specieskey",
                   how="left") if len(lab) else sus.assign(lit_host=False)
    ev["lit_host"] = ev.lit_host.fillna(False).astype(bool)
    # training positives are excluded from the claim — this measures
    # prediction on species the model never saw as labels
    held = ev[ev.label != 1]
    pos = held[held.lit_host].p_host
    neg = held[~held.lit_host].p_host
    print(f"\nheld-out species (label!=1): {len(held)}")
    print(f"lit-evidenced hosts: {len(pos)} | p_host "
          f"mean {pos.mean():.3f} vs rest {neg.mean():.3f}")
    if len(pos) >= 5:
        from sklearn.metrics import roc_auc_score
        y = held.lit_host.astype(int)
        auc = roc_auc_score(y, held.p_host)
        print(f"p_host AUC on literature labels: {auc:.3f} "
              f"({len(pos)} pos / {len(neg)} neg)")
        top = held.nlargest(15, "p_host")
        hit = int(top.lit_host.sum())
        print(f"top-15 p_host unlabeled: {hit}/15 carry a mined "
              f"host edge")


if __name__ == "__main__":
    main()
