# WildSeek — wildlife susceptibility monitor

**Meta Global AI Developer Hackathon — Indie track** · live demo: `wildseek.ecoseek.org`

A living host-susceptibility + supply-chain risk monitoring system.
Extends the three-distance ML framework from
[Robles-Fernández et al. 2022, PNAS](papers/robles-fernández-et-al-2022-wildlife-susceptibility-to-infectious-diseases-at-global-scales.pdf)
— geographic, environmental, and phylogenetic distances — into a
continuously-updated surveillance tool.

Flagship system: **HPAI H5N1 (clade 2.3.4.4b)** — mammal spillover
(74 species infected and growing ~50%/year) × U.S. poultry/dairy
supply-chain exposure, county-level.

## Architecture

```
GBIF occurrences (1/120° grid)   USDA APHIS hub (ArcGIS, no key)
        │                        wild-bird + livestock detections
        ▼                        flyway polygons
  pipeline/ ── species pools + ecoregion accessible area (M)
        │   + ERA5 30-year normals → env_occ / env_m
        ▼
  xnicher campaign ── 88 bio-var pairs × 1,148 species
        │   = 101,376 fits, all accepted; AIC winners
        ▼
  agent/ ── Muse Spark typed triage over fit diagnostics
        │   ambiguous tail (AIC-tied, sparse, marine) →
        │   accept / flag_review / drop / switch_family,
        │   then a real refit runner honours switch_to
        ▼
  pipeline/ ── per-species suitability rasters (CONUS 1/120°)
        │   × recency-weighted detection kernel → risk_1120
        │   → HUC8 watershed ranking (sub-county, named)
        ▼
  api/ + app/ ── wildseek.ecoseek.org: monitoring map,
             /explain + /briefing with cached agent outputs
```

Two parallel views of the same score: which wild vertebrates are
climatically suitable hosts where, and which watersheds sit inside
the risk zone.

## Hackathon delta

- Meta Model API throughout: muse-spark-1.3 for typed triage and
  /explain, muse-wonder-1.0 for the narrative /briefing,
  muse-spark-1.2-contributor for bulk extraction; muse-glimmer
  self-hosted for free offload.
- Agentic decision layer with real teeth: an ambiguous-tail selector
  surfaces only suspicious fits; the agent's `switch_to` verdicts are
  executed by `pipeline/refit_switched.R` and both AICs land in
  `decisions_delta.csv`.
- Living host list: agentic literature mining → provenance-tracked
  evidence (OpenAlex → typed JSON).

Pre-hackathon baseline is tagged `pre-hackathon` in upstream repos;
work submitted here was built during Oct 26 – Nov 4, 2026.

## Layout

| Dir | What |
|---|---|
| `model/` | R wrapper over `alrobles/PNAS-...` + `phylopred` + `pam` |
| `agent/` | Python — Meta Model API client, extraction prompts, APHIS hub client |
| `api/` | FastAPI monitor service |
| `app/` | Map frontend (geoseek pattern) |
| `pipeline/` | Scheduled re-score loop |
| `data/` | Local artifacts (gitignored) |
| `papers/` | Reference papers |
| `docs/` | `meta-api.md` (API facts/pricing), `data-sources.md` (endpoints) |
