"""powerlaw_eval — thesis ch.4 network validation, Python port.

poweRcpp (R, Clauset-Shalizi-Newman MLE) equivalents implemented here:
alpha via MLE on integer degrees, x_min by KS minimization, KS as the
goodness-of-fit statistic.

Hypothesis (dissertation ch.4): adding predicted edges to the observed
host-parasite-sharing network should IMPROVE the power-law fit — the
degree distribution of the "true" network is closer to power-law than
the under-sampled observed one.

    python litmine/powerlaw_eval.py
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
from interaction_model import resolve_hosts  # noqa: E402


def powerlaw_fit(deg, x_min_grid=range(1, 6)):
    """Clauset MLE for discrete power law. deg: int array >=1.
    Returns (x_min, alpha, ks) for best x_min by KS."""
    deg = np.asarray(deg, dtype=int)
    deg = deg[deg >= 1]
    best = None
    for xm in x_min_grid:
        d = deg[deg >= xm]
        if len(d) < 10:
            continue
        alpha = 1 + len(d) / np.sum(np.log(d / (xm - 0.5)))
        # empirical CDF vs power-law CDF on sorted data
        d_sorted = np.sort(d)
        emp = np.arange(1, len(d) + 1) / len(d)
        zeta = sum(x ** -alpha for x in range(xm, d.max() + 1))
        cdf = np.array([sum(x ** -alpha
                            for x in range(xm, int(v) + 1)) / zeta
                        for v in d_sorted])
        ks = np.max(np.abs(emp - cdf))
        if best is None or ks < best[2]:
            best = (xm, alpha, ks)
    return best


def host_degrees(edges_keyed):
    """edges with resolved host_key + parasite_norm ->
    host degree (# distinct parasites each host shares-links...).
    Here degree = number of partner hosts sharing >=1 parasite,
    i.e. degree in the host-sharing network."""
    pairs = set()
    for ks in edges_keyed.groupby("parasite_norm").host_key.unique():
        ks = sorted(ks)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                pairs.add((ks[i], ks[j]))
    deg = {}
    for a, b in pairs:
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
    return deg, pairs


def main():
    inter = pd.read_parquet("data/litmine/interactions.parquet")
    uni = pd.read_csv("data/species_winner.csv")[["specieskey", "species"]]
    inter["host_key"] = resolve_hosts(inter, uni)
    m = inter[inter.host_key.notna()].copy()
    m["host_key"] = m.host_key.astype(np.int64)
    m["v"] = (m.verified.fillna("0").astype(str).str.lower()
              .str.replace(r"\.0$", "", regex=True).isin(["true", "1"]))

    obs_deg, obs_pairs = host_degrees(m[m.v])
    print(f"observed (verified edges): {len(obs_deg)} hosts, "
          f"{len(obs_pairs)} sharing pairs")
    fit_obs = powerlaw_fit(list(obs_deg.values()))
    print(f"  power-law fit: x_min={fit_obs[0]} alpha={fit_obs[1]:.2f} "
          f"KS={fit_obs[2]:.3f}")

    pred = pd.read_parquet("data/serve/interaction_pred.parquet")
    pos_pred = (pred[pred.share == 0]
                .nlargest(100, "p_share"))
    print(f"top predicted pairs p_share "
          f"[{pos_pred.p_share.min():.3f}-{pos_pred.p_share.max():.3f}]")
    aug_deg = dict(obs_deg)
    for a, b in pos_pred[["key_i", "key_j"]].itertuples(index=False):
        if (a, b) in obs_pairs or (b, a) in obs_pairs:
            continue
        aug_deg[a] = aug_deg.get(a, 0) + 1
        aug_deg[b] = aug_deg.get(b, 0) + 1
    print(f"augmented (+{len(pos_pred)} predicted pairs): "
          f"{len(aug_deg)} hosts")
    fit_aug = powerlaw_fit(list(aug_deg.values()))
    print(f"  power-law fit: x_min={fit_aug[0]} alpha={fit_aug[1]:.2f} "
          f"KS={fit_aug[2]:.3f}")
    delta = fit_obs[2] - fit_aug[2]
    print(f"\nDelta KS (obs-aug): {delta:+.3f} "
          f"({'predictions IMPROVE power-law fit' if delta > 0 else 'predictions degrade fit'})")


if __name__ == "__main__":
    main()
