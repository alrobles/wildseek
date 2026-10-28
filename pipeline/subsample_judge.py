"""JUDGE for the niche subsampling experiment.

Joins subsampled fits to their full-n reference (same species x pair) and
scores convergence:
  d_maha    = Mahalanobis distance of mu_n from mu_full under Sigma_full
  vol_ratio = sqrt(det(S_n) / det(S_full))  (2D ellipse volume ratio)

Aggregates per bioclim variable -> convergence curves + empirical n_min
at an eps grid. Optional --catalog checks full-n refits reproduce the
campaign AIC (determinism gate).

    python3 subsample_judge.py --fits fits_subsample/ --out subsample_v1/judge
"""

import argparse
import glob
import json
import os

import numpy as np
import pandas as pd

EPS_GRID = (0.25, 0.5, 1.0)


def load_fits(path: str) -> pd.DataFrame:
    if os.path.isdir(path):
        files = sorted(glob.glob(f"{path}/fits_*.csv"))
        assert files, f"no fits_*.csv in {path}"
        return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    return pd.read_csv(path)


def score(df: pd.DataFrame) -> pd.DataFrame:
    full = df[df.is_full].set_index(["specieskey", "pair_idx"])
    sub = df[~df.is_full].copy()
    assert len(full), "no full-n reference fits"
    dm, vr = np.full(len(sub), np.nan), np.full(len(sub), np.nan)
    jittered = 0
    for i, r in enumerate(sub.itertuples()):
        f = full.loc[(r.specieskey, r.pair_idx)]
        if isinstance(f, pd.DataFrame):  # duplicate refits: keep first
            f = f.iloc[0]
        S = np.array([[f.s11, f.s12], [f.s12, f.s22]])
        try:
            Si = np.linalg.inv(S)
        except np.linalg.LinAlgError:
            S = S + np.eye(2) * 1e-8 * np.trace(S)
            Si = np.linalg.inv(S)
            jittered += 1
        d = np.array([r.mu1 - f.mu1, r.mu2 - f.mu2])
        dm[i] = float(np.sqrt(d @ Si @ d))
        vr[i] = float(np.exp(0.5 * (r.logdet - f.logdet)))
    sub["d_maha"], sub["vol_ratio"] = dm, vr
    print(f"scored {len(sub)} subsamples vs {len(full)} refs "
          f"({jittered} jittered)")
    return sub


def curves(sub: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for v in sorted(set(sub.temp) | set(sub.prec)):
        sel = sub[(sub.temp == v) | (sub.prec == v)]
        for lv, g in sel.groupby("n_level"):
            rows.append((v, lv, g.d_maha.median(),
                         g.d_maha.quantile(0.25), g.d_maha.quantile(0.75),
                         g.vol_ratio.median(), len(g)))
    return pd.DataFrame(rows, columns=["variable", "n_level", "med_dmaha",
                                       "q25_dmaha", "q75_dmaha", "med_vol",
                                       "n"])


def n_min(curves: pd.DataFrame) -> pd.DataFrame:
    out = []
    for v, g in curves.groupby("variable"):
        g = g.sort_values("n_level")
        ns, ms = g.n_level.to_numpy(), g.med_dmaha.to_numpy()
        row = {"variable": v}
        for eps in EPS_GRID:
            below = np.nonzero(ms < eps)[0]
            if not len(below):
                row[f"nmin_{eps}"] = np.nan
            elif below[0] == 0:
                row[f"nmin_{eps}"] = float(ns[0])
            else:
                i = below[0]
                n0, n1, m0, m1 = ns[i-1], ns[i], ms[i-1], ms[i]
                row[f"nmin_{eps}"] = round(float(
                    n0 + (eps - m0) * (n1 - n0) / (m1 - m0)), 1)
        out.append(row)
    return pd.DataFrame(out)


def plot(curves: pd.DataFrame, path: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib missing — skipping png")
        return
    fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    temps = sorted({v for v in curves.variable if int(v[3:]) <= 11})
    precs = sorted({v for v in curves.variable if int(v[3:]) > 11})
    for j, vs in enumerate([temps, precs]):
        for v in vs:
            g = curves[curves.variable == v].sort_values("n_level")
            ax[j].plot(g.n_level, g.med_dmaha, marker="o", ms=3, label=v)
        ax[j].set_xscale("log")
        ax[j].set_xlabel("n")
        ax[j].legend(fontsize=7, ncol=2)
    ax[0].set_ylabel("median d_maha vs full-n")
    ax[0].set_title("temperatures (bio01-11)")
    ax[1].set_title("precipitations (bio12-19)")
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    print(f"wrote {path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fits", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--catalog", default=None)
    a = ap.parse_args()

    df = load_fits(a.fits)
    sub = score(df)
    cur = curves(sub)
    nm = n_min(cur)
    os.makedirs(a.out, exist_ok=True)
    sub.to_parquet(f"{a.out}/scored.parquet", index=False)
    cur.to_csv(f"{a.out}/curves.csv", index=False)
    nm.to_csv(f"{a.out}/nmin.csv", index=False)
    plot(cur, f"{a.out}/curves.png")

    lines = [f"# Subsample judge — {len(sub)} fits, "
             f"{sub.specieskey.nunique()} species",
             "",
             "## Flag rate by level",
             sub.groupby("n_level").flag
             .apply(lambda s: f"{(s != 'accepted_global').mean():.2%} "
                              f"non-global (n={len(s)})").to_string(),
             "", "## n_min per variable (interp. median d_maha < eps)",
             nm.to_string(index=False)]
    if a.catalog:
        cat = pd.read_csv(a.catalog)
        ref = df[df.is_full].merge(
            cat, on=["specieskey", "temp", "prec"], suffixes=("", "_cat"))
        d = (ref.aic - ref.aic_cat).abs()
        lines += ["", f"## Determinism: max |dAIC| vs catalog = {d.max():.4f} "
                     f"(n={len(ref)})"]
    open(f"{a.out}/report.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
