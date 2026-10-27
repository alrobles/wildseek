# WildSeek — submission notes

Live demo: **wildseek.ecoseek.org** (ecoseek stack, container
`ecoseek-wildseek` on `127.0.0.1:8654`).

## What it is

Wildlife HPAI susceptibility + U.S. supply-chain risk monitor.
Three layers, all computed during the event window:

1. **Susceptibility** — 1,148 vertebrate species × 88
   temperature×precipitation ellipsoid-niche pairs (`xnicher`) =
   101,376 fits, 100% `accepted_global`, AIC-selected winners
   projected to CONUS suitability rasters at 1/120° (~1 km).
2. **Detection pressure** — 9,479 HPAI-positive wild-bird records
   (USDA APHIS), recency-weighted (90-day half-life), Gaussian-smoothed
   (~10 km kernel), normalized 0–1.
3. **Risk** — detection pressure × mean Aves suitability →
   continuous sub-county risk surface, aggregated to 2,247 named
   HUC8 watersheds for the ranked table.

## The agentic layer (Meta models, not a rubber stamp)

- `muse-spark-1.3` — typed triage: 1,147 catalog decisions, then a
  **second pass over only the ambiguous tail** (173 species selected
  by AIC-tie / sparse-n / marine-fraction / degenerate-M heuristics).
  Result: **49 flag_review with substantive reasons** — sparse
  endemics, marine mammals on implausible pairs, small-n unstable
  ellipsoids — written to `decisions_delta.csv` (49 changed rows).
  `switch_to` verdicts are executable by `pipeline/refit_switched.R`.
- `muse-wonder-1.0` — `/briefing` narrative over tonight's artifacts.
- `muse-spark-1.2-contributor` — bulk OpenAlex literature extraction.
- `muse-glimmer` (self-hosted, KU HPC) — free offload path.

## Audit-criteria status (docs/AUDIT-2026-10-26.md)

| Criterion | Status |
|---|---|
| Repo public | pending (owner action) |
| NEW.md provenance | done |
| Tail delta with changed=true | done — 49 rows |
| /risk/watershed ≥1,000 rows | 2,247 HUC8 exported |
| ≥20 suit PNGs + flyways | 1,147 PNGs; flyways as polygons |
| Docker-serving /explain | baked JSON fallback + live |
| Cached briefing/explain | precomputed JSON in image |

## Known limits

- Presence-only likelihood for all campaign fits; `ip_weighted`
  exists in refit path for queued species.
- ~13% of aves occurrence cells fall on era5land water pixels and
  are dropped from env extraction.
- Suitability is climate-only; biotic/dispersal axes are future work
  (phylopred PU layer is staged but not shipped).
