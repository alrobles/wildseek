"""interaction_model — host x host parasite-sharing link prediction.

Positive pair (i,j): two universe species that share >=1 mined parasite
(interactions.parquet host names resolved to specieskeys via binomial +
common_name + GBIF vernacular maps). Negatives: pairs among the same
resolved species sharing none. Features: geographic Jaccard, env
Jaccard, patristic distance (phy_dist.csv), same-family/order/genus.

    python pipeline/interaction_model.py
    -> data/serve/interaction_pred.parquet + CV printout
"""
from itertools import combinations
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "litmine"))
from leakage_audit import norm_name  # noqa: E402


def resolve_hosts(inter, uni):
    name2key = {norm_name(s): k for k, s in uni.itertuples(index=False)}
    hl = pd.read_parquet("data/host_labels.parquet")
    c2k = {norm_name(c): k for c, k in
           hl[["common_name", "specieskey"]].dropna()
           .itertuples(index=False)}
    g2k = {}
    try:
        g = pd.read_csv("data/litmine/gbif_host_map.csv")
        g2k = {norm_name(h): k for h, k in g.itertuples(index=False)}
    except FileNotFoundError:
        pass
    k = (inter.host_norm.map(name2key)
         .fillna(inter.host_norm.map(c2k))
         .fillna(inter.host_norm.map(g2k)))
    return k.astype("float64")


def build_pairs():
    inter = pd.read_parquet("data/litmine/interactions.parquet")
    uni = pd.read_csv("data/species_winner.csv")[["specieskey", "species"]]
    inter["host_key"] = resolve_hosts(inter, uni)
    m = inter[inter.host_key.notna()].copy()
    m["host_key"] = m.host_key.astype(np.int64)
    # judge-verified edges define positives when available; unverified
    # edges only still count (they're candidate signal, weaker)
    m["v"] = (m.verified.fillna("0").astype(str).str.lower()
              .str.replace(r"\.0$", "", regex=True).isin(["true", "1"]))
    n_ver = int(m.v.sum())
    print(f"resolved edges: {len(m)} ({n_ver} judge-verified)")

    species = sorted(m.host_key.unique())
    mv = m[m.v]
    def shared_pairs(frame):
        out = set()
        for ks in frame.groupby("parasite_norm").host_key.unique():
            if 1 < len(ks) <= 60:
                out.update(combinations(sorted(ks), 2))
        return out
    pos = shared_pairs(mv) if len(shared_pairs(mv)) >= 200 else shared_pairs(m)
    print(f"positive pairs: {len(pos)} "
          f"({'verified-edges' if pos == shared_pairs(mv) else 'all-edges'})")
    all_pairs = set(combinations(species, 2))
    neg = all_pairs - pos
    rows = ([(a, b, 1) for a, b in pos] +
            [(a, b, 0) for a, b in neg])
    df = pd.DataFrame(rows, columns=["key_i", "key_j", "share"])
    print(f"resolved {m.host_key.nunique()} species | "
          f"pos {len(pos)} / neg {len(neg)}")
    return df


def attach_features(df):
    # patristic distance keyed by latin names
    phy = pd.read_csv("data/phy_dist.csv")
    uni = pd.read_csv("data/species_winner.csv")[["specieskey", "species"]]
    n2k = {s: k for k, s in uni.itertuples(index=False)}
    phy["key_i"] = phy.item1.map(n2k)
    phy["key_j"] = phy.item2.map(n2k)
    phy = phy.dropna(subset=["key_i", "key_j"])
    a = np.minimum(phy.key_i, phy.key_j).astype(np.int64)
    b = np.maximum(phy.key_i, phy.key_j).astype(np.int64)
    pdist = dict(zip(zip(a, b), phy.phylo_distance))

    geo = pd.read_parquet("data/jaccard_geo.parquet")
    env = pd.read_parquet("data/jaccard_env.parquet")
    gmap = dict(zip(zip(geo.key_i, geo.key_j), geo.j_geo))
    emap = dict(zip(zip(env.key_i, env.key_j), env.j_env))

    ki = np.minimum(df.key_i, df.key_j).values
    kj = np.maximum(df.key_i, df.key_j).values
    df["phylo_distance"] = [pdist.get((x, y), np.nan) for x, y in zip(ki, kj)]
    df["j_geo"] = [gmap.get((x, y), gmap.get((y, x), 0.0)) for x, y in zip(ki, kj)]
    df["j_env"] = [emap.get((x, y), emap.get((y, x), 0.0)) for x, y in zip(ki, kj)]

    tax = pd.read_parquet("data/taxonomy.parquet")
    tax = tax.drop_duplicates(subset="specieskey")
    tmap = tax.set_index("specieskey")[["order", "family", "genus"]]
    ti, tj = tmap.reindex(df.key_i), tmap.reindex(df.key_j)
    for col in ("order", "family", "genus"):
        df[f"same_{col}"] = (ti[col].values == tj[col].values).astype(int)
    return df


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, average_precision_score
    from sklearn.model_selection import StratifiedKFold

    df = attach_features(build_pairs())
    feats = ["phylo_distance", "j_geo", "j_env",
             "same_order", "same_family", "same_genus"]
    X = df[feats].fillna(0).values
    y = df.share.values

    skf = StratifiedKFold(5, shuffle=True, random_state=7)
    for name, clf in [("logreg", LogisticRegression(max_iter=2000,
                                                  class_weight="balanced")),
                      ("hgbt", HistGradientBoostingClassifier(
                          max_iter=300, random_state=7))]:
        aucs, aps = [], []
        for tr, te in skf.split(X, y):
            clf.fit(X[tr], y[tr])
            p = (clf.predict_proba(X[te])[:, 1]
                 if hasattr(clf, "predict_proba")
                 else clf.decision_function(X[te]))
            aucs.append(roc_auc_score(y[te], p))
            aps.append(average_precision_score(y[te], p))
        print(f"{name}: ROC-AUC {np.mean(aucs):.3f}±{np.std(aucs):.3f} | "
              f"PR-AUC {np.mean(aps):.3f}")

    best = HistGradientBoostingClassifier(max_iter=300, random_state=7)
    best.fit(X, y)
    df["p_share"] = best.predict_proba(X)[:, 1]
    out = Path("data/serve/interaction_pred.parquet")
    df.to_parquet(out, index=False)
    print(f"wrote {out}: {len(df)} host pairs "
          f"(p_share mean {df.p_share.mean():.3f})")


if __name__ == "__main__":
    main()
