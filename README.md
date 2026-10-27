# Susceptibility Monitor

**Meta Global AI Developer Hackathon — Indie track**

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
literature (OpenAlex)          USDA APHIS hub (ArcGIS, no key)
        │                      wild-bird + livestock detections
        ▼                      flyways, county resolution
  agent/ ── Muse Spark mines host–pathogen evidence
        │   (living host list; bulk extraction on contributor models)
        ▼
  model/ ── PNAS three-distance RF + phylopred PU host prediction
        │   + Clay v1.5 embedding distance (new 4th signal)
        ▼
  pipeline/ ── nightly re-score → susceptibility rasters
        │   × NASS poultry inventory → supply-chain risk layer
        ▼
  api/ + app/ ── monitoring map: where to sample next,
             which production regions are exposed
```

Two parallel views of the same score: which wild mammals are likely
next hosts, and which production counties sit inside the risk zone.

## Hackathon delta

- Meta Model API integration: Muse Spark (agent + literature extraction),
  SAM 3.1 (livestock–wildlife interface segmentation), Muse Image
  (surveillance briefing figures).
- Clay v1.5 foundation-model embeddings as a fourth environmental-distance
  signal, ablated against bioclim distances.
- Living host list: agentic literature mining → provenance-tracked
  evidence → automatic model re-scoring. Real-time fit: H5N1's known
  mammal host list grew ~50% between Mar 2024 and Jul 2025.

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
