"""SPEC for the niche subsampling experiment (Q1 of niche-factory).

Selects ground-truth species (n >= --min-n) and emits the full task table:
species x 88 pairs x n-levels x reps + one full-n refit per species x pair.

Seed discipline: opt_seed is fixed per (species, pair) — the exact campaign
seed — so the only varying factor across levels/reps is the occurrence
sample. Full-n refits must reproduce the campaign AIC (determinism check).
occ_seed varies per (level, rep) and drives the subsample draw.

    python3 subsample_spec.py --pool $B/pool_flagship.csv \
        --counts data/species_cell_counts.csv --out $B/subsample_v1
"""

import argparse
import datetime
import json
import os
import subprocess

import pandas as pd

TEMPS = [f"bio{i:02d}" for i in range(1, 12)]
PRECS = [f"bio{i:02d}" for i in range(12, 20)]
PAIRS = [(t, p) for t in TEMPS for p in PRECS]
MOD = 2147483627  # 2^31-1, fits R integers


def occ_seed(sp: int, pair_idx: int, level_idx: int, rep: int) -> int:
    """Deterministic integer seed (no hash() — stable across runs)."""
    return ((sp * 73856093) ^ (pair_idx * 19349663)
            ^ (level_idx * 83492791) ^ (rep * 2971215073)) % MOD


def opt_seed(sp: int, pair_idx: int) -> int:
    """Campaign seed scheme: (sp %% 1e6) * 89 + pi, pi 1-based."""
    return (sp % 1000000) * 89 + pair_idx + 1


def git_sha(path: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", path, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True).stdout.strip()
    except OSError:
        return "unknown"


def select(pool: pd.DataFrame, counts: pd.DataFrame, per_class: int,
           min_n: int, max_level: int) -> pd.DataFrame:
    for df in (pool, counts):  # specieskey may parse float (blank cells)
        df["specieskey"] = pd.to_numeric(df.specieskey,
                                         errors="coerce").astype("Int64")
    pool, counts = pool.dropna(subset=["specieskey"]), counts.dropna(
        subset=["specieskey"])
    need = max(min_n, max_level)
    c = counts[counts.n_cells_global >= need]
    m = pool.merge(c[["specieskey", "n_cells_global"]], on="specieskey")
    m = m.sort_values("n_cells_global", ascending=False)
    return m.groupby("class_", group_keys=False).head(per_class)


def build_tasks(species: pd.DataFrame, levels: list[int],
                reps: int) -> pd.DataFrame:
    rows = []
    tid = 0
    for r in species.itertuples():
        sp = int(r.specieskey)
        for pi, (tv, pv) in enumerate(PAIRS):
            rows.append((tid, sp, r.species, r.class_, tv, pv,
                         pi, 0, 0, 0, opt_seed(sp, pi), True))
            tid += 1
            for li, lv in enumerate(levels):
                for rep in range(reps):
                    rows.append((tid, sp, r.species, r.class_, tv,
                                 pv, pi, lv, li, rep,
                                 occ_seed(sp, pi, li, rep), False))
                    tid += 1
    cols = ["task_id", "specieskey", "species", "class", "temp", "prec",
            "pair_idx", "n_level", "level_idx", "rep", "seed", "is_full"]
    return pd.DataFrame(rows, columns=cols)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True)
    ap.add_argument("--counts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-class", type=int, default=15)
    ap.add_argument("--min-n", type=int, default=100)
    ap.add_argument("--levels", default="10,20,30,50,75,100")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--starts", type=int, default=60)
    a = ap.parse_args()

    levels = [int(x) for x in a.levels.split(",")]
    pool = pd.read_csv(a.pool)
    pool = pool.rename(columns={"class": "class_"})
    counts = pd.read_csv(a.counts)
    species = select(pool, counts, a.per_class, a.min_n, max(levels))
    assert len(species), "empty selection — loosen --per-class/--min-n"
    tasks = build_tasks(species, levels, a.reps)

    os.makedirs(a.out, exist_ok=True)
    tasks.to_parquet(f"{a.out}/tasks.parquet", index=False)
    spec = {
        "created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "levels": levels, "reps": a.reps, "starts": a.starts,
        "per_class": a.per_class, "min_n": a.min_n,
        "n_species": len(species),
        "n_tasks": len(tasks),
        "git_meta_hack": git_sha("."),
        "pool": a.pool, "counts": a.counts,
    }
    json.dump(spec, open(f"{a.out}/spec.json", "w"), indent=1)
    print(f"species {len(species)} | tasks {len(tasks)} -> {a.out}")


if __name__ == "__main__":
    main()
