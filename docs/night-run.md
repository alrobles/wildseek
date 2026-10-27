# Night run — prototype by morning (2026-10-26)

Goal: working "HPAI Wildlife Monitor" mounted as an ecoseek service —
wildlife susceptibility map + sub-county (watershed / 1-120deg) risk —
built agentically overnight. Every stage writes to
`/beegfs/a474r867/meta-hack/`; nothing heavy on login nodes.

## Dependency DAG

```
                 ┌── substrate (DONE)
                 │   pools / M / env cube / env_occ
                 │
        ┌────────┼─────────────────┬──────────────────┐
        ▼        ▼                 ▼                  ▼
  [A] R env   [B] BirdTree    [C] env extra      [D] mining
  xnicher     download +      CONUS normals      H5N1 host list
  install     subset pool     (verify publish)   (local, Meta)
        │        │                │                  │
        ▼        │                │                  │
  [E] xnicher campaign            │                  │
  pilot 24 → full 1160×88         │                  │
  (SLURM array)                   │                  │
        │                         │                  │
        ▼                         │                  │
  [F] suitability rasters ◄───────┘                  │
  top-K @1/120 CONUS                                 │
        │                                            │
        ▼                                            ▼
  [G] risk surface                            [H] T1 decisions
  APHIS recency × suit.                       campaign review +
  (watershed+1/120)                           briefing (muse)
        │                                            │
        └──────────────┬─────────────────────────────┘
                       ▼
                [I] serving: GeoParquet/PMTiles/COG +
                    FastAPI → ecoseek service + map
                       │
                       ▼
                [J] morning report (wonder) + spend
```

## Track detail

**[A] R env** — `xsdm_latest.sif` has R4.4.2+terra+sf+duckdb+xsdm; install
`xnicher` (CRAN) + `oneearthr` into `/beegfs/a474r867/rlib_442`,
`R_LIBS_USER` bind-mounted. Fallback if compute has no net: download
tarballs on login (net OK), install from files.

**[B] BirdTree** — VertLife phylosets (login net OK) → posterior tree
set → subset to bird pool species (match GBIF backbone names).
Fallback: skip bird PU scores; mammal tree already exists.

**[E] xnicher campaign** — per species: `env_occ` + `env_m` (live query)
→ per (temp_i, prec_j) pair: Box-Cox(prec) → z-score → `optimize_niche`
presence_only → `assess` → `compare_xnicher` AIC/BIC. Pilot array 24 sp
first; on green, array over 1,160 (e.g. 116 tasks × 10 sp).
Outputs `fit_catalog.parquet` + per-species `decision_log`.

**[F] suitability** — `predict(fit, normals stack)` for top-K species on
the CONUS grid → COG/parquet.

**[G] risk** — APHIS positives (recency-weighted, **watershed** field =
sub-county native resolution) × suitability surfaces → 1/120° risk layer
+ watershed/county aggregates. Finer than county as requested.

**[H]+[J] Meta** — T1 typed decisions over fit catalog; wonder for
flagged + morning synthesis. All via meta_client accounting.

**[I] serving** — export GeoParquet + PMTiles (ecoregions, watersheds,
detections) + top-K COG → FastAPI+DuckDB container in ecoseek stack
(pattern: ecoseek-frontend :4000/:4002, api :3000) + MapLibre map.

## Checkpoints (kill criteria)

- A fails & no local-install path → fall back to `geospatial_latest.sif`
  + install libs, else ship deterministic layers only.
- E pilot convergence <50% → tighten M / more starts, re-pilot; do NOT
  fan out a bad config to 1,160.
- BirdTree blocked → mammals-only PU demo.
- Meta API unreachable → deterministic deliverables still stand.
- Morning minimum viable: pools+M+env cube+fit catalog+risk surface+
  one map page, even if some legs are partial.
