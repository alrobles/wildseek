# Plan — HPAI Susceptibility Monitor

> 2026-11-04: plan original de construcción (campaña HPC oct-2026).
> Operación actual: modo casa — ver `docs/FACTORY.md`. El cluster
> (kuhpc/beegfs) está fuera de alcance hasta que KUIT cierre la
> investigación; stages SLURM suspendidos, rasters congelados.

Decisions locked 2026-10-26. Flagship: **HPAI H5N1 (clade 2.3.4.4b)**,
dual track: wildlife susceptibility (global) + U.S. supply-chain
exposure (county). All compute on **kuhpc SLURM**; all data on
`/beegfs/a474r867` unless noted.

## Verified assets

| Asset | Location | Notes |
|---|---|---|
| GBIF mirror | `beegfs/gbifdata` (~289G) | Parquet + backbone; `gbifdb::gbif_local` pattern |
| era5_bioclim | `beegfs/era5_bioclim/v1` | **global** 3600×1801 @0.1°, 19 vars, yearly 1950–2025 |
| Mammal tree | `beegfs/phylogenyAI/results/dating_v6` | 10k posterior dated trees, 7,901/9,507 tips, MCCs |
| APHIS hub | `agent/aphis.py` | 174k wild-bird samples + livestock events + flyways. **No species field → circulation surface, not labels** |
| xnicher | `alrobles/xnicher` (CRAN) | Ellipsoidal ENM, presence-only + IPW, `habitat_suitability()` |
| phylopred | `alrobles/phylopred` | PU phylogenetic host prediction (PNAS 3rd distance) |
| geoseek | `alrobles/geoseek-devel` | Frozen EO embeddings — 4th signal (replaces Clay) |
| xbioclim/fastbioclim | `alrobles/*` | Fast bioclim computation |
| Agent miner | `agent/` this repo | OpenAlex → Muse Spark → host_list JSONL (pattern from `cochliomyia_hominivorax`, no shared artifacts) |

## Constraints / policies

- **No Chinese AI** (KB POLICY) — muse-* compliant; Ollama: Llama/Mistral/Gemma only.
- **IUCN shapefiles**: governance-restricted → validation only, never shipped. Our xnicher SDMs replace them.
- SLURM: `sixhour` ≤6h (self-chaining pattern in KB), `kbs` 60d, `bigjay_20nodemax_10+`; Apptainer, no Docker; some nodes lack BeeGFS (0:53 → exclude list).
- **NO compute on login nodes** (rule, 2026-10-26): anything beyond
  file listing / squeue / sbatch goes through `sbatch`. Interactive
  debugging only via `srun`.
- Bird tree: **VertLife/BirdTree posterior set** (public; download, subset to candidate pool).

## Species universe — LOCKED (2026-10-26)

**Two-resolution design** (user decision):

| Tier | Extent | Dedup grid | Role |
|---|---|---|---|
| Global | world | **1/30°** (~3.7 km) | full occurrence envelope per species → `env_occ` for xnicher (niche is global — CONUS-only records would truncate the ellipse) |
| CONUS | lower-48 | **1/120°** (~900 m) | fine focal layer where suitability rasters, APHIS detections, and NASS risk align |

Bonus: **endemism becomes computable** — a species is CONUS-endemic
iff its global 1/30° footprint ⊆ CONUS bbox. No IUCN needed.

**Grid source**: xbioclim CONUS **1/120°** collection — served at
`data.xbioclim.org` (per-year bio01–19 GeoTIFFs, 1986–2025) and on
cluster (`era5_bioclim/publish/_YYYY_split/bio*_YYYY.tif`; verify
whether splits are 0.1° global or the 1/120° CONUS product).

**Occurrences**: GBIF mirror, **1996–2025 only**, deduplicated one
point per cell — same `distinct`-after-rounding pattern as
`gbif_effort` stage-1, at both resolutions.

**Climatology**: 30-year normals 1996–2025 (mean over yearly
1/120° bio files for CONUS; global env extraction may use the 0.1°
`v1/era5land_bioclim_YYYY.tif` stack or a 1/30°-matched grid).

**Pools**: species split by unique-cell count at each resolution:
- >100 unique 1/120° CONUS cells → flagship high-res pool
- species with global 1/30° footprint ⊆ CONUS → "CONUS endemic" flag
- thinner sets can still take phylo (T0) scores
- Pilot: **birds + mammals** (bird↔mammal jump = the HPAI story)

## Environmental design — LOCKED (2026-10-26)

- Variable space: all **(temp_i, prec_j)** pairs — 11 temperature
  (bio01–11) × 8 precipitation (bio12–19) = **88 candidate pairs**.
- Transform: precipitation → **Box-Cox** first; then **z-score**
  all model inputs.
- **M hypothesis**: per species, `env_m` = ecoregions covering the
  top-95% of its presence points. `oneearthr`
  (`alrobles/oneearthr`) ships the One Earth / RESOLVE 2017 layers
  offline — 847 ecoregions via `oe_layer("ecoregions")`.
  Operationalization: point-in-polygon per species → rank
  ecoregions by occupancy share → cumulative ≥95% → union = M
  polygon → `env_m` = env cells inside M. Edge cases: small-n
  species (95% unstable → containing ecoregions + buffer
  fallback); dominant-ecoregion species get a tight M by
  construction.
- Model: **xnicher** ellipsoid in the 2-D pair space per species.
- Selection: **AIC + BIC via `compare_xnicher()`** + Akaike weights;
  `assess()$flag` must be `"accepted_global"` or the fit is out.
  Idiom per the workflow vignette (alrobles.github.io/xnicher):
  `optimize_niche(env_occ, env_m, likelihood, num_starts, seed)` →
  `assess()` → `compare_xnicher(...)` → `predict(fit, stack)`.
- Cheap by construction: 2-D fit per combo is trivial → 88 × N spp
  still SLURM-array friendly.

Open technical notes: bio14/bio17 can be 0 → Box-Cox needs ε or
Yeo-Johnson; AIC across pairs is valid variable-selection (same
nobs, same likelihood family — keep `likelihood` fixed per
comparison set, e.g. all 88 presence_only, then re-check top pair
under ip_weighted).

## Agentic modeling orchestrator — DESIGN SPACE

Concept (per user): the ellipsoidal scan is cheap enough to brute-force,
so the AI isn't there to *run* fits — it's a **typed decision layer**
over fit diagnostics. jev-pattern (TypeSafe System One, see
`alrobles/PU-jev-devel`): one structured call → decision vector →
deterministic machinery executes.

Mapping onto Meta API (System-1/System-2):

| Tier | Model | Role in pipeline |
|---|---|---|
| T0 deterministic | — | dedup, transforms, 88 `optimize_niche` fits, AIC/BIC table |
| T1 typed calls | `muse-spark-1.2-contributor` (bulk) / `muse-spark-1.3` | per-species decision via strict JSON schema: `{accept, refit_more_starts, switch_family(skew_t/ip_weighted), flag_review, drop}` — driven by diagnostics (convergence flags, AIC spread, eccentricity, n) |
| T2 deep | `muse-wonder-1.0` | flagged species, family-switch rationale, campaign synthesis + demo narrative |

What the typed call decides (not what it computes):
- **likelihood-family switch**: asymmetric env_occ → skew_normal/skew_t;
  high sampling bias → ip_weighted; heavy tails → skew_t
- **convergence triage**: non-`accepted_global` → more starts /
  narrower M / drop species
- **niche sanity**: centroid outside convex hull, degenerate
  eccentricity → flag
- **pool moves**: n too small → suggest genus-level pooling

Deliverable framing: every species carries a machine-readable
decision log (why accepted/rejected/refit) — auditability IS the
hackathon story ("the agent runs the modeling campaign").

Rubric fit: uses structured output + tool calling + background
responses — the "beyond basic integration" features in
`docs/meta-api.md`.

## Serving stack — LOCKED (2026-10-26)

No database server in the prototype — serverless-geo, static files:

| Layer | Format | Why |
|---|---|---|
| Analytical tables (pools, M, county risk) | GeoParquet | already our materialization format |
| Map vectors (counties, ecoregions, flyways, detections) | PMTiles | one file per layer, HTTP range requests, MapLibre-native — no tile server |
| Suitability rasters | COG / PNG (top-K species only) | same range-request pattern; full catalog stays parquet on beegfs, rasterized on demand |
| Query engine | FastAPI + DuckDB (single process), optional DuckDB-WASM in browser | the "API" can be static files |

Upgrade path: PostGIS only if multi-writer production ever needs it.
Volume note: 1/120° CONUS ≈ 30M cells/sp × 1,160 sp — serve top-K
(~50) rasters in the demo; raw catalog stays on beegfs.

## Meta-model instrumentation map — LOCKED (2026-10-26)

Where each Meta model plugs in (and where it does NOT):

| Stage | Deterministic work | Meta model | Instrumented role |
|---|---|---|---|
| Literature mining | OpenAlex search, dedup | `muse-spark-1.2-contributor` | host–pathogen extraction, strict JSON (BUILT) |
| Query planning | — | `muse-spark-1.3` | next-query proposals for the mining loop |
| Evidence QC | GBIF resolve + flags | `muse-spark-1.3` (typed) | review `search_fuzzy` matches (the "domestic animal"→*Equus* failure mode): `{accept, reject, requery}` verdicts — high real value, known failure class |
| GBIF pools / M | dedup, rasterized-ecoregion join, 95% rank | — | none — pure SQL |
| M edge cases | marine-ish flag, n_eco_m outliers | `muse-spark-1.3` (typed) | `{accept, buffer_M, drop, flag}` per flagged species |
| Env extraction | overlay, Box-Cox, z-score | — | none |
| xnicher 88-pair | `optimize_niche`, `assess`, `compare_xnicher` | `muse-spark-1.2-contributor` (bulk typed) | per-species decision vector `{accept, refit_more_starts, switch_family, flag_review, drop}` |
| Flagged species | — | `muse-wonder-1.0` | family-switch rationale, degenerate ellipsoids, marine no-env cases |
| Susceptibility score | phylopred PU + distances + combine | — | none — scoring stays deterministic |
| Top-K narrative | — | `muse-wonder-1.0` | per-species susceptibility synthesis (phylo + niche + known hosts) → demo cards |
| County risk layer | recency-weighted APHIS × suitability × NASS | — | none |
| Surveillance briefings | — | `muse-spark-1.3` typed → `muse-wonder` polish | per-county structured briefing: `{top_species, drivers, sampling_rec}` then narrative |
| Nightly delta | new detections/literature diff | `muse-wonder-1.0` | digest narrative — the "living monitor" story |
| API `/explain` | score lookups | `muse-spark-1.3` | on-demand county/species explanation |
| Facility geolocation | aerial tiles fetch | **`sam-3.1`** | segment poultry barns / CAFO / dairy barns / wetlands around detection counties → point-level facilities, upgrades NASS county aggregates. $2.50/1K img @3k RPM ≈ free. The legitimate Meta geospatial-AI leg |

EO embeddings role: **geoseek** (own frozen EO embeddings) — covers
what Clay v1.5 would give; no external FM needed. muse-spark/wonder
multimodal input unverified — probe `image_url` once; if yes, cheap
map-chip QA joins T1.

Not instrumented (honest exclusions): `muse-image-1.0`,
`muse-voice-transcribe-1.0` — no legitimate role; demo garnish.

Cost shape: T1 bulk ≈ 1,160 species × ~1 KB prompt ≈ cents on
contributor; wonder reserved for flagged species + briefings + digest.
All calls through `meta_client` usage/spend accounting.

## Phases

0. ✅ agent (OpenAlex→extract→host_list→GBIF resolve) + `aphis.py`
1. **Universe + occurrences** — mostly DONE (2026-10-26):
   - ✅ `gbif_thinned_120.duckdb` reused (186M rows, already 1/120°-deduped
     globally, segmented by class)
   - ✅ `/beegfs/a474r867/meta-hack/`: `species_cell_counts.csv` (16,906 sp),
     `occ_conus_{aves,mammalia}_1120.parquet`, `occ_global_*_130.parquet`,
     `pool_flagship.csv` (1,160 sp ≥100 CONUS cells), `pool_conus_endemic.csv` (71 sp)
   - ✅ **M built**: `eco_raster_130.csv.gz` (19.2M cells, 844/847 ecoregions
     rasterized at 1/30°) → `species_eco_counts_*.parquet` →
     `m_ecoregions.parquet` + `m_summary.parquet` (16,330 sp; median 7
     ecoregions/sp; 1,777 marine-ish flagged). Scripts:
     `pipeline/gbif_pools.py`, `pipeline/rasterize_ecoregions.R`,
     `pipeline/build_m.py` (shardable: `--shard i/N`)
   - ✅ **env cube built** (`pipeline/build_env_cube.py`):
     `env_cube/year=*/` (66.4M rows: 2.21M land cells × 30 yr × 19 bio,
     eco_id pre-joined), `env_cell_map.parquet` (pixel→ecoregion/realm/
     biome dictionary; 95.5% of cells matched), `env_normals_96_25.parquet`
     (30-yr means per cell). Extract-by-ecoregion = one WHERE clause;
     `env_m` for any species = `eco_id in (species' M)`. Build cost ≈
     5 min login-node + ~9 GB. Notes: env grid is 0.1° offset +0.05°
     (centers at X.X5); `eco_id=-1` = outside ecoregions; a DuckDB
     19-aggregate groupby OOM'd → numpy accumulator instead.
   - ⬜ BirdTree download; CONUS 1/120° normals (verify `publish/` product)
2. **SDM array**: `xnicher` per-species SLURM array (88 pairs, fixed
   likelihood, `compare_xnicher` AIC/BIC) → suitability stack (top-K COGs).
3. **Susceptibility**: `phylopred` PU scores (mammal tree + BirdTree) + env distance (xbioclim) + geographic + geoseek embeddings → combined score per species.
4. **Risk layer**: APHIS detection surface (recency-weighted) × suitability stack × NASS poultry inventory + **sam-3.1 facility segmentation** → county/facility risk.
5. **Demo loop**: `run_mine` on H5N1 → re-score → static geo stack (PMTiles/COG/GeoParquet) + FastAPI+DuckDB + Muse briefing.

## Open items

- era5_bioclim `publish/_YYYY_split` — check if spatial tiles already exist for chunked reading.
- `nicherbayes_birds` on beegfs — may already have bird-occurrence extraction machinery.
- NASS QuickStats key needed (free api.data.gov).
- APHIS mammals page = HTML table — scrape for cross-check (state-level).
