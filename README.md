# Susceptibility Monitor

**Meta Global AI Developer Hackathon — Indie track**

A living wildlife-disease susceptibility monitoring system. Extends the
three-distance ML framework from
[Robles-Fernández et al. 2022, PNAS](papers/robles-fernández-et-al-2022-wildlife-susceptibility-to-infectious-diseases-at-global-scales.pdf)
— geographic, environmental, and phylogenetic distances — into a
continuously-updated surveillance tool.

Flagship system: *Cochliomyia hominivorax* (New World screwworm) →
susceptible wild-mammal hosts across the Americas, as the parasite
re-invades northward.

## Architecture

```
literature (OpenAlex/PubTator)
        │
        ▼
  agent/ ── Muse Spark mines host–pathogen evidence
        │   (living host list; bulk extraction on open-weight models)
        ▼
  model/ ── PNAS three-distance RF + phylopred PU host prediction
        │   + Clay v1.5 embedding distance (new 4th signal)
        ▼
  pipeline/ ── nightly re-score → susceptibility rasters
        │
        ▼
  api/ + app/ ── monitoring map: where to sample next
```

## Hackathon delta

- Meta Model API integration: Muse Spark (agent + literature extraction),
  SAM 3.1 (livestock–wildlife interface segmentation), Muse Image
  (surveillance briefing figures).
- Clay v1.5 foundation-model embeddings as a fourth environmental-distance
  signal, ablated against bioclim distances.
- Living host list: agentic literature mining → provenance-tracked
  evidence → automatic model re-scoring.

Pre-hackathon baseline is tagged `pre-hackathon` in upstream repos;
work submitted here was built during Oct 26 – Nov 4, 2026.

## Layout

| Dir | What |
|---|---|
| `model/` | R wrapper over `alrobles/PNAS-...` + `phylopred` + `pam` |
| `agent/` | Python — Meta Model API client, extraction prompts |
| `api/` | FastAPI monitor service |
| `app/` | Map frontend (geoseek pattern) |
| `pipeline/` | Scheduled re-score loop |
| `data/` | Local artifacts (gitignored) |
| `papers/` | Reference papers |
