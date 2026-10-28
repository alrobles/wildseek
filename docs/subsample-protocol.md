# Subsampling experiment — protocol v1 (Q1 niche-factory)

Ground-truth species (n >= 100) refit at full n plus subsampled levels.
Measures per-variable convergence of the ellipsoid centroid (and volume)
to derive empirical n_min per bioclim variable. No changes to the
campaign pipeline — new files only, same likelihood/transform/optimizer.

## Files

| File | Role |
|---|---|
| `pipeline/subsample_spec.py` | SPEC: select species, emit task table + spec.json |
| `pipeline/subsample_run.R` | BUILDER: fit tasks (shard slice), record mu/Sigma |
| `pipeline/subsample_judge.py` | JUDGE: d_maha/vol_ratio, curves, n_min, report |
| `pipeline/slurm/subsample_array.sbatch` | SLURM array over shards |
| `tests/test_subsample.py` | unit tests (synthetic, no R) |

## Design

- Transform is n-independent (Box-Cox lambda + z-moments from env_m), so
  subsampled and full-n centroids live in the same z-space and are
  directly comparable.
- opt_seed fixed per (species, pair) = campaign seed: the only varying
  factor is the occurrence sample. Full-n refits must reproduce the
  catalog AIC (determinism gate in JUDGE via `--catalog`).
- Metrics: d_maha of mu_n vs mu_full under Sigma_full; volume ratio
  sqrt(det_n/det_full). Per-variable medians over species x pairs x reps.
- n_min(v, eps): interpolated n where median d_maha < eps, eps in
  (0.25, 0.5, 1.0).

## Budget (default SPEC: 15/class, 6 levels, 5 reps)

30 spp x 88 pairs x (1 + 6x5) = 81,840 fits ≈ one campaign. Fits are
cheaper than campaign (fewer occ points, same M cap).

## Run (kuhpc)

```bash
B=/beegfs/a474r867/meta-hack
python3 pipeline/subsample_spec.py --pool $B/pool_flagship.csv \
  --counts data/species_cell_counts.csv --out $B/subsample_v1
cp pipeline/subsample_run.R $B/
sbatch --array=0-39 pipeline/slurm/subsample_array.sbatch  # N_SHARDS=40
# after completion:
python3 pipeline/subsample_judge.py --fits $B/subsample_v1/fits/ \
  --out $B/subsample_v1/judge --catalog data/fit_catalog.csv
```

## Deferred stages

- Q2 combo redundancy: Python-only clustering of variable correlations
  on an env-cube sample (needs beegfs; no fits).
- Q3 ranking preservation: needs the ellipsoid->j_env interface decision
  (current j_env is model-free footprint Jaccard); Q3a fallback =
  footprint-Jaccard stability under occurrence subsampling, no fits.
- Q4 concentration bounds: analysis on top of Q1 curves (n_min vs
  O(k log k) and vs cube marginal moments).
