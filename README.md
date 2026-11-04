# WildSeek — Autonomous Ecological Surveillance & Spillover Frontier

> **Autonomous wildlife disease intelligence anticipating pathogen spillover before detection.**  
> *Ecological surveillance for wildlife professionals — not medical advice, not for personal health decisions.*

[![Live Monitor](https://img.shields.io/badge/Live%20Monitor-wildseek.ecoseek.org-0f766e?style=for-the-badge)](https://wildseek.ecoseek.org)
[![Track](https://img.shields.io/badge/Track-T2%20Push%20the%20Frontier-0f172a?style=for-the-badge)](https://github.com/alrobles/wildseek)
[![Whitepaper](https://img.shields.io/badge/Paper-Whitepaper-b91c1c?style=for-the-badge)](paper/whitepaper.md)
[![Dataset](https://img.shields.io/badge/HuggingFace-wildseek--sft-blue?style=for-the-badge)](https://huggingface.co/datasets/alrobles/wildseek-sft)
[![Public Mirror](https://img.shields.io/badge/GitHub-alrobles%2Fwildseek-334155?style=for-the-badge)](https://github.com/alrobles/wildseek)

---

## ⚡ 5-Number Evidence Strip

| Metric | Measured Value | Context & Benchmark Baseline | Artifact Source |
|---|---|---|---|
| **Prospective Susceptibility** | **AUC 0.74** | Evaluated on **53 held-out literature-evidenced hosts** ($n=53$ admits no tight CI); random stratified 5-fold CV ×20 is 0.862 (inflated by spatial autocorrelation) | [`eval/susceptibility.json`](eval/susceptibility.json) |
| **Full-Text Literature Recall** | **56% pair recall** | vs. **16%** for abstract-only scrapers; 100% precision on 12/12 audit (raw 60% strict / 70% claim-level, $n=30$) | [`eval/litmine.json`](eval/litmine.json) |
| **Literature Extraction Scale** | **4,854 edges / 3,740 pairs** | 2,351 judge-verified edges (full ticker: 348 papers; eval corpus: 282 papers, 139 yielded); PMC triage: 38% keep / 56% tok savings / $1.33 vs ZOVER: 23% / 74% / $1.93 Capa-0/1 | [`eval/litmine.json`](eval/litmine.json) |
| **Autonomous Niche Fitting** | **101,376 fit rows** | Across 1,147 species (88 pairs, plus refit/buffer rows); 173 ambiguous tail species evaluated → 49 `flag_review` interventions; 0 refits executed in-window (executable deltas via `pipeline/refit_switched.R`) | [`app/data.sample/decisions_delta.csv`](app/data.sample/decisions_delta.csv) |
| **Domain-Adapted LoRA Distillation** | **0.00 → 0.70 exact match** | Triage task (28–0 paired win, $p \approx 7.5\times 10^{-9}$); all-task run: 0.20 exact / 0.82 semantic agreement (see holdout-leakage caveat) | [`eval/lora_triage.json`](eval/lora_triage.json) · [`eval/lora_all.json`](eval/lora_all.json) |

---

## 🧭 T2 Track: Push the Frontier

Current wildlife biosurveillance is structurally reactive: dead carcasses are discovered by chance, swabs are shipped to centralized labs, and biosecurity authorities receive alerts days to weeks after transmission chains have established.

**WildSeek pushes the biosurveillance frontier from reactive post-mortem reporting to prospective, agentic risk forecasting:**
1. **Three-Distance Macroecological Host Scoring**: Operationalizes the PNAS framework ([Robles-Fernández et al. 2022](https://doi.org/10.1073/pnas.2122851119)) combining geographic range overlap, 19-bioclim Hutchinsonian environmental niche distances, and patristic phylogenetic distances along real trees (BirdTree Stage2 consensus + dated mammal phylogeny; 968/1,147 species on real patristic tree branches).
2. **Pre-Registered Prospective Forecasting**: On October 28, 2026, WildSeek pre-registered and froze 15 unlabeled high-risk species (`we-called-it` registry). Today, **15/15 remain awaiting-confirmation** under strict post-freeze verification rules (requiring post-freeze literature confirmation; 4/15 already carry a mined host edge (`SUBMISSION.md`)).
3. **Continuous Spatial Spillover Mapping**: Fuses prospective host susceptibility with **9,139** USDA APHIS HPAI wild-bird detections (90-day exponential half-life decay, Gaussian spatial kernel) across **2,247 HUC8 watersheds** and **3,109 U.S. counties**, linking wild avian reservoirs directly to agricultural poultry supply-chain exposure (82M+ commercial birds affected, APHIS through 2024-02).
4. **Autonomous Self-Updating Edge Factory**: An end-to-end nightly loop (`ENTRADA → SPEC → REFIT → BUILDER → APPROVER → PRODUCCION`) managed by specialized LLM agents with deterministic QA quorum gatekeeping (3/4 consensus required before publishing).

---

## ⚡ 60-Second Local Run

The sample bundle ships pre-baked minimal artifacts (`≈8 MB` under `app/data.sample/`) so the full stack boots locally without requiring cluster access. It includes top-100 susceptibility/watershed tables, risk/detection/reservoir rasters, poultry exposure, and simplified flyway corridors; per-species `suit_*.png` rasters (1,141 files) are omitted (species drill-down still returns tabular data):

```bash
# 1. Clone repository
git clone https://github.com/alrobles/wildseek.git
cd wildseek

# 2. Seed pre-baked minimal sample data
cp -r app/data.sample app/data

# 3. Configure local environment (keyless demo for seeded entities)
cp .env.example .env

# 4. Launch FastAPI monitor & MapLibre interface via Docker Compose
cd serve && docker compose up
```

Open **http://localhost:8654** in your browser to explore the interactive map, HUC8 risk rankings, county exposures, and `/briefing` summaries.

---

## 🏗️ System Architecture & Autonomous Factory Loop

```
GBIF Occurrences (1/120° grid)     USDA APHIS HPAI Detections
             │                                    │
             ▼                                    ▼
       Accessible Area M                   9,139 Wild Detections
   (oneearthr ecoregions 95%)               (90d half-life decay)
             │                                    │
             ▼                                    │
      xnicher Engine                              │
  101,376 fit rows / 1,147 spp                    │
  (88 pairs, plus refit/buffer)                   │
             │                                    │
             ▼                                    │
      Agentic Triage                              │
  173 ambiguous tail species                      │
  49 flag_review interventions                    │
  (executable deltas via refit_switched.R)        │
             │                                    │
             ▼                                    │
  Three-Distance Susceptibility ◄── PMC Full-Text Litmine Factory
  (Geo + Env + Patristic Phylo)      4,854 edges / 3,740 pairs
  AUC 0.74 on 53 held-out hosts      56% recall vs 16% abstract
             │
             ▼
    Joint Continuous Risk Surface
    (2,247 HUC8 Watersheds · 3,109 Counties)
             │
             ▼
  FastAPI + MapLibre UI (wildseek.ecoseek.org)
```

The nightly factory cycle operates under strict autonomous governance:
- **`ENTRADA`**: Ingests fresh APHIS wild-bird, mammal, and flock events.
- **`SPEC`**: Agent planner generates `run_spec.json` identifying catalog deltas.
- **`REFIT`**: Re-estimates three-distance model coefficients if new host species are validated.
- **`BUILDER`**: Re-aggregates watershed risks and county exposures (HPC full recalculation or `--casa` standalone mode over frozen rasters).
- **`APPROVER`**: Autonomous QA quorum requiring 3 of 4 votes (code syntax, security policies, UX integrity, model verification) before production release.
- **`PRODUCCION`**: Atomic rsync deployment to `wildseek.ecoseek.org` followed by automatic health-check verification.

---

## 🗺️ Repository Map

```
alrobles/wildseek (public mirror) / alrobles/wildseek-devel (development repo)
├── pipeline/       Data pipeline: GBIF thinned occurrences, M-masking, xnicher campaign
│                   fits, three-distance susceptibility modeling, spatial aggregation
├── agent/          Meta model orchestration: ambiguous tail triage, nightly QA quorum,
│                   narrative /briefing generation, and structured edge adjudication
├── litmine/        Literature edge extraction: PMC full-text XML ingestion, triage filter,
│                   structured interaction extraction, and automated judge verification
├── api/            FastAPI operational backend: endpoints for /metrics, /we-called-it,
│                   /explain, /briefing, and spatial tile queries
├── app/            Zero-build MapLibre GL spatial dashboard and risk inspector
├── serve/          Docker Compose deployment spec exposing quickstart on port 8654
├── eval/           Strictly verifiable benchmark JSONs and evaluation methodologies
│   ├── susceptibility.json   Prospective AUC 0.74 & CV 0.862 baseline
│   ├── litmine.json          Full-text 56% recall, edge counts, and audit metrics
│   ├── lora_triage.json      0.00 → 0.70 exact match triage distillation
│   └── lora_all.json         0.20 exact / 0.82 semantic all-task benchmarks
├── paper/          Scientific whitepaper: architecture, methods, evaluation
│   └── whitepaper.md         Complete architecture, methods, and evaluation treatise
├── video/          Remotion programmatic video composition and presentation deck
└── tests/          Unit and integration test suite (94 passing tests)
```

---

## 🔗 Key Deliverables, Paper & Dataset Links

- **Live Production Monitor**: [https://wildseek.ecoseek.org](https://wildseek.ecoseek.org)
- **Scientific Whitepaper**: [`paper/whitepaper.md`](paper/whitepaper.md)
- **HuggingFace Dataset (SFT Trajectories & Summaries)**: [huggingface.co/datasets/alrobles/wildseek-sft](https://huggingface.co/datasets/alrobles/wildseek-sft)
- **LoRA Adapter Recipe**: Fireworks path & [wildseek-lora-adapter](https://github.com/alrobles/wildseek-lora-adapter) public recipe
- **Pre-Registered Tracking**: [wildseek.ecoseek.org/we-called-it](https://wildseek.ecoseek.org/we-called-it)
- **API Health Inspection**: [wildseek.ecoseek.org/health](https://wildseek.ecoseek.org/health)
- **Programmatic Presentation Video**: Source project in [`video/`](video/)

---

## ⚠️ Known Limits

1. **Taxonomic Resolution**: 179 of 1,147 species rely on taxonomic-proxy phylogenetic distances due to absence from published consensus trees or hybrid status.
2. **Environmental Dimensions**: Ellipsoid niches represent 19-bioclimatic variables (ERA5-Land 30-year normals); biotic interactions and microclimates remain unmodeled.
3. **Zero In-Window Executed Refits**: 49 ambiguous-tail interventions were staged as executable deltas via `pipeline/refit_switched.R`; zero refits were executed in-window.

---

*WildSeek is an open scientific research and ecological surveillance platform. Not medical advice, not for personal health decisions.*
