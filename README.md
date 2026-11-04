# WildSeek — wildlife susceptibility monitor

Ecological surveillance for wildlife professionals — not medical advice.

**Meta Global AI Developer Hackathon — Indie Developer** · Live demo: [wildseek.ecoseek.org](https://wildseek.ecoseek.org)

## Submission Overview

- **Provenance (Oct 26 – Nov 4, 2026)**: Everything in this snapshot was built during the event window (pre-existing deps ledger in [NEW.md](NEW.md); development history intentionally excluded).
- **Meta models** ([Meta Model API](https://dev.meta.ai)):
  - `muse-spark-1.3`: Pipeline orchestration, typed triage over the ambiguous tail, and `/explain`.
  - `muse-spark-open` (Fireworks/Baseten open weights): Bulk extraction and edge judge.
  - `muse-spark-1.2-contributor`: High-throughput literature mining.
  - `muse-wonder-1.0`: Nightly narrative `/briefing`.
  - `muse-glimmer-30b` + LoRA: Domain-adapted triage SFT on Fireworks serverless.
- **Bonus targets**: Best Build on Meta Open Weight Models ($10k) · Best Agentic Use-Case.
- **Demo**: [wildseek.ecoseek.org](https://wildseek.ecoseek.org) (keyless, baked artifacts for seeded entities) · [API Health Check](https://wildseek.ecoseek.org/health).
- **Open data & models**: SFT trajectories + LoRA eval at [huggingface.co/datasets/alrobles/wildseek-sft](https://huggingface.co/datasets/alrobles/wildseek-sft).

---

## 60-Second Summary

WildSeek transforms wildlife disease surveillance from static reports into an autonomous risk-intelligence system. Its flagship deployment targets **HPAI H5N1 (clade 2.3.4.4b)** across the contiguous United States (CONUS).

1. **What it does**: Computes three continuous ecological surveillance layers across CONUS:
   - **Susceptibility**: Scores 1,147 vertebrate species using the three-distance ecological framework ([Robles-Fernández et al. 2022, PNAS](https://doi.org/10.1073/pnas.2122851119)) across geographic overlap, 19-bioclim environmental niches, and patristic phylogenetic distances (dated mammal trees + BirdTree consensus).
   - **Detection Pressure**: 9,139 APHIS HPAI wild-bird detections with a 90-day half-life decay and Gaussian spatial kernel.
   - **Supply-Chain Exposure**: Joint continuous risk surface aggregated to 2,247 HUC8 watersheds (per `docs/AUDIT-2026-10-26.md`) and mapped across 3,109 U.S. counties against agricultural exposure (82M+ poultry affected).
2. **Why it matters**: Spillover into novel mammalian and avian hosts outpaces field testing. WildSeek predicts prospective host suitability *before* detection, achieving **AUC 0.74 on 53 held-out literature-evidenced hosts** (15 pre-registered predictions frozen 2026-10-28, confirmations pending).
3. **Built with Meta models (Oct 26 – Nov 4, 2026)**:
   - **Agentic Niche Triage**: Evaluated 101,376 ellipsoid fits across 1,147 species (88 bio-var pairs, plus refit/buffer rows). Filtered down to an ambiguous tail of 173 species, where `muse-spark-1.3` issued 49 substantive `flag_review` interventions with reasons (sparse endemics, marine mammals on implausible pairs, small-n unstable ellipsoids) recorded in `app/data.sample/decisions_delta.csv`; `switch_to` refits are executable via `pipeline/refit_switched.R` (no switches triggered in-window).
   - **Full-Text Literature Mining**: Extracted 4,854 edges (2,351 judge-verified / 3,740 unique pairs) from 282 PMC open-access papers, boosting gold pair recall from 16% (abstract-only) to 56% (full-text) with 100% precision on a 12-edge human audit (raw 60–73% across n=30 audit; Capa-2 extraction at $0.0014/edge, $1.33 logged on the audited corpus).
   - **Task-Specialized Open Weights (LoRA)**: Fine-tuned `muse-glimmer-30b` with LoRA r8 on Fireworks serverless ($0 promo), taking holdout exact-match accuracy from 0.0 to 0.70 on the triage task (28-0 paired win, p ≈ 7e-9; broader all-task run reached 0.20 exact / 0.82 after semantic rescore — see [eval/lora_triage.json](eval/lora_triage.json), [eval/lora_all.json](eval/lora_all.json), and [eval/README.md](eval/README.md) for holdout-leakage caveat).

---

## Verified Quantitative Evidence

All figures are strictly verifiable against [eval/](eval/), [`/metrics`](https://wildseek.ecoseek.org/metrics), and repository manifests:

| Metric | Measured Value | Context / comparator | Source File |
|---|---|---|---|
| **Host Susceptibility** | AUC 0.74 on 53 held-out lit-evidenced hosts | ROC-AUC 0.862 (random-fold CV; spatially auto-correlated labels) | [eval/susceptibility.json](eval/susceptibility.json) |
| **Literature Recall** | 56% pair recall (full-text) | 16% pair recall (abstract-only) | [eval/litmine.json](eval/litmine.json) |
| **Literature Scale** | 4,854 extracted edges (2,351 judge-verified) / 3,740 pairs / 282 papers | Capa-2 extraction at $0.0014/edge ($1.33 logged on audited corpus) | [eval/litmine.json](eval/litmine.json) |
| **Niche Fitting Scale** | 101,376 fits / 1,147 species | 88 bio-var pairs, plus refit/buffer rows | [pipeline/](pipeline/) |
| **Triage Interventions** | 49 `flag_review` interventions (0 refits triggered in-window) | 173 ambiguous tail species triaged; switch_to refits executable via `pipeline/refit_switched.R` | [app/data.sample/decisions_delta.csv](app/data.sample/decisions_delta.csv) |
| **Spatial Aggregation** | 2,247 HUC8 watersheds / 3,109 counties | 9,139 wild detections (82M+ poultry affected) | [app/data.sample/](app/data.sample/) |
| **LoRA SFT Exact Match** | 0.0 → 0.70 exact match (triage task) | 0.20 exact / 0.82 semantic rescore (all-task; see holdout caveat) | [eval/lora_triage.json](eval/lora_triage.json) |

---

## Architecture

```
GBIF occurrences (1/120° grid)   USDA APHIS hub (ArcGIS, no key)
        │                        wild-bird + mammal detections
        ▼                        (species-level) + flock events +
  pipeline/ ── species pools +   flyway polygons
        │   ecoregion accessible area (M, 95% of presences)
        │   + ERA5 30-year normals → env_occ / env_m
        ▼
  xnicher campaign ── 88 bio-var pairs × 1,147 species (+440 refit rows)
        │   = 101,376 fits, all accepted; AIC winners
        ▼
  agent/ ── Muse Spark typed triage over fit diagnostics
        │   ambiguous tail (173 spp) → 49 flag_review w/ substantive reasons
        │   (recorded in decisions_delta.csv; switch_to executable via refit_switched.R)
        ▼
  pipeline/ ── suitability rasters MASKED to each species' M
        │   (EPSG:3857 PNGs; strictly within accessible areas)
        ▼
  susceptibility model (PNAS three-axis: env + geo + patristic phy):
        │   labels = 159 APHIS-confirmed H5N1 host species
        │   model = logistic regression with polynomial interactions
        │   ROC-AUC 0.862 (CV), AUC 0.74 on 53 held-out lit hosts (15 frozen pending)
        ▼
  risk = detection kernel × mean aves suitability → 2,247 HUC8 watersheds
        → county exposure across 3,109 counties (flocks × birds affected)
        ▼
  api/ + app/ ── wildseek.ecoseek.org: risk-first monitor,
             click→watershed/county/detection cards,
             /explain + /briefing with baked agent outputs for seeded entities
```

---

## Quickstart (Run Locally in 60s)

The sample bundle ships a reduced slice of tabular/vector layers (`≈5 MB` pre-baked artifacts under `app/data.sample/`; per-species suitability rasters excluded — they render empty locally) so the web monitor boots immediately without cluster rasters.

```bash
# 1. Seed demo data (≈5 MB pre-baked minimal artifacts)
cp -r app/data.sample app/data

# 2. Configure environment (optional: MODEL_API_KEY for live agent runs; demo runs keyless for seeded IDs)
cp .env.example .env

# 3. Boot FastAPI backend + MapLibre frontend
cd serve && docker compose up
```

Open [http://localhost:8654](http://localhost:8654) to inspect the live interface.

---

## The Factory (Nightly Autonomous Loop)

WildSeek runs as an automated surveillance pipeline ([pipeline/nightly.py](pipeline/nightly.py), specification in [docs/FACTORY.md](docs/FACTORY.md)):

```
ENTRADA    fetch_aphis -> fresh APHIS detections/species/flocks
SPEC       agent/planner.py -> run_spec.json (delta: new species -> refit)
REFIT      (conditional) labels -> dist_frame -> suscept_model
BUILDER    HPC: risk -> watershed -> exposure -> render -> export
           (casa: local export, rasters frozen)
APPROVER   agent/qa.py: quorum 3/4 (code / security / UX / brain=spark)
PRODUCCION rsync -> serve host -> wildseek.ecoseek.org + /health verify
BRAIN      run manifest + shift log (glimmer local on HPC, cloud in casa)
SELF-HEAL  stage failure -> `muse exec` patches -> one retry
```

- **HPC mode**: Full cluster recalculation of spatial rasters and ellipsoid niches.
- **Casa mode** (`--casa` / `WILDSEEK_CASA=1`): Automated conveyor operating without cluster access; preserves frozen rasters, updates vector/tabular data, executes QA quorum, and verifies production health.
- Routine updates deploy automatically; susceptibility refits flag `needs_human_release` via PR gate before pushing to production.

---

## Known Limits

- **Likelihood formulation**: Presence-only likelihood for all campaign fits; `ip_weighted` exists in the refit path for queued species.
- **Taxonomic coverage**: 179 species remain on taxonomic-proxy phylo distance (2 hybrids, taxa absent from trees, one ambiguous GBIF entity).
- **Scale reconciliation**: BirdTree↔v6 distance scales differ; handled by per-source normalization plus an `is_patristic_real` indicator feature (dist_frame fail-closed if fewer than two distance axes cover).
- **Water pixel masks**: ~13% of aves occurrence cells fall on era5land water pixels and are dropped from env extraction.
- **Environmental dimensions**: Suitability is climate-only; biotic/dispersal axes are future work (phylopred PU layer staged but not shipped).

---

## Repository Map

```
alrobles/meta-hack  (THIS REPO — everything built Oct 26 – Nov 4, 2026)
├── pipeline/   data build: GBIF pools → M masks → env cube →
│               101k-fit campaign → risk (HUC8 + county) → serve export
├── agent/      Meta Model API layer: typed triage, 49-verdict delta,
│               QA quorum 3/4 + cost veto, briefing, extraction
├── litmine/    literature edge factory: PMC full text → triage →
│               typed edges → judge-verified ($0.0014/edge)
├── api/        FastAPI monitor service
├── app/        MapLibre frontend (single file)
├── serve/      docker compose — one-command demo (data.sample incl.)
└── eval/       quantitative benchmark artifacts (ROC, litmine, LoRA)

pre-existing dependencies (released/lab infra — full ledger in NEW.md)
├── xnicher v1.0.0 (CRAN, 2026-09-06)      niche-fitting engine
├── oneearthr v1.0.0 (2026-09-16)          RESOLVE ecoregions → M
├── phyloseek-devel (lab, unversioned)     dated mammal tree v6
├── ecoseek / geoseek stack (ecoseek.org)  serving platform
└── xsdm_pipeline .sif (HPC)               R/terra/duckdb container

public data (cited, external)
├── GBIF mirror (1/120° dedup) · ERA5 bioclim normals
├── USDA APHIS hub (HPAI detections, flock events)
├── BirdTree Stage2 Ericson + AVONET crosswalk
└── PMC Open Access + OpenAlex (literature corpus)

companion repository (event work, outside this snapshot)
└── wildseek-lora — SFT trajectories for Glimmer orchestrator
```

---

> *WildSeek is an ecological surveillance research tool for wildlife professionals. Not medical advice, not for personal health decisions.*
