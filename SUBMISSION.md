# WildSeek — submission notes

Live demo: **wildseek.ecoseek.org** (ecoseek stack, container
`ecoseek-wildseek` on `127.0.0.1:8654`).
Public repo: **github.com/alrobles/meta-hack** (curated snapshot
releases; development lives in a separate private repo).

## What it is

Ecological surveillance for wildlife professionals — not medical advice.

Wildlife HPAI susceptibility + U.S. supply-chain risk monitor —
the first disease on an agentic wildlife-risk platform designed
to generalize to further pathogens. Ecological surveillance for
wildlife professionals — not medical advice, not for personal
health decisions.

Three layers, all computed during the event window:

1. **Susceptibility** — 1,147 vertebrate species scored with the
   three-distance framework (Robles-Fernández et al. 2022, PNAS):
   environmental + geographic distance to confirmed hosts, plus
   **phylogenetic distance on real trees** — BirdTree Stage2
   Ericson posterior consensus for birds, dated mammal tree for
   mammals. 968/1,147 species on patristic distances, the rest on
   a taxonomic fallback. Per-species CONUS suitability comes from
   88 temperature×precipitation ellipsoid-niche pairs each
   (`xnicher`; 101,376 fits, 100% `accepted_global`, AIC winners)
   masked to each species' own occupied ecoregions (M), at 1/120°
   (~1 km). GBIF↔tree name reconciliation via AVONET crosswalk +
   epithet/manual rules: 202/208 formerly-proxied species resolved.
2. **Detection pressure** — 9,139 HPAI-positive wild-bird records
   (USDA APHIS), recency-weighted (90-day half-life),
   Gaussian-smoothed (~10 km kernel), normalized 0–1.
3. **Risk** — detection pressure × reservoir community
   (`sum_i p_host_i · suit_i`, plus strongest-host and
   at-least-one-reservoir layers) → continuous sub-county risk
   surface, aggregated to named HUC8 watersheds for the ranked
   table; county exposure for 3,109 counties.

## The agentic layer (Meta models, not a rubber stamp)

- `muse-spark-1.3` — typed triage: 1,147 catalog decisions, then a
  **second pass over only the ambiguous tail** (173 species selected
  by AIC-tie / sparse-n / marine-fraction / degenerate-M heuristics).
  Result: **49 flag_review with substantive reasons** — sparse
  endemics, marine mammals on implausible pairs, small-n unstable
  ellipsoids — written to `decisions_delta.csv`.
  `switch_to` verdicts are executable by `pipeline/refit_switched.R`.
- The same model is the **release gate**: `scripts/release.sh`
  publishes to the public repo only after a Muse review of the
  exact diff returns an explicit SHIP; NO-SHIP, review failure or a
  missing verdict aborts the push.
- `muse-wonder-1.0` — `/briefing` narrative over the night's
  artifacts (baked to JSON, demo runs keyless).
- `muse-spark-1.2-contributor` — bulk OpenAlex literature extraction.
- `muse-glimmer` (self-hosted, KU HPC) — free offload path; also the
  litmine JUDGE (see below).

## litmine — the literature edge factory

Second product: a live loop mining parasite↔host edges from
full-text papers, with per-edge provenance (PMID + evidence span):

- **Capa 0/1**: PMC Open-Access full text → chunked passages →
  `muse-spark-open` (Fireworks) YES/NO triage — keeps 23% of chunks,
  ~74% token savings ($1.93 per 3k-chunk corpus).
- **Capa 2**: typed edge extraction (parasite, host, relation,
  evidence_span, geo/date/method) at **$0.0014 per edge**.
- **Capa 3 (JUDGE)**: self-hosted `muse-glimmer` re-verifies every
  edge against its span — rejects serology-only and species-without-
  detection mentions (42% pass on the ZOVER abstracts run). On a
  30-edge audit, raw precision 73% → **100% on judge-verified edges**.
- **Numbers**: 1,451 mined edges / 1,059 unique pairs / 129 papers
  (`interactions.parquet`). On the held-out Ebola/Lassa gold,
  full-text pair-recall **56% vs 16% abstract-only** (3.4×).
- **Prospective validation**: `we-called-it` card froze the top-15
  unlabeled species by p_host on **2026-10-28**; a post-freeze PMID
  naming one as host flips it to confirmed — statuses shown live.
- Endpoints: `/litmine` (ticker), `/metrics`, `/we-called-it`,
  `/decisions` (executable switch_to delta).

## Nightly loop

`pipeline/nightly.py` (cron 03:15): fetch APHIS → spec detects
whether refit is warranted (run spec carries an explicit
`criticality`: routine ships direct, refit flags a human) → Slurm
build on KU HPC (submit + `sacct` polling, no blind timeout) → QA
approver (hard gates + 3/4 reviewer quorum + **cost veto** on the
call ledger) → rsync to production → re-baked briefing.
Optional self-heal (`WILDSEEK_SELFHEAL=1`) lets a Muse agent
attempt bounded repairs; off by default.

## Audit-criteria status (docs/AUDIT-2026-10-26.md)

| Criterion | Status |
|---|---|
| Repo public | done — curated snapshot, orphan commits |
| NEW.md provenance | done |
| Tail delta with changed=true | done — 49 rows |
| /risk/watershed ≥1,000 rows | 2,247 HUC8 exported |
| ≥20 suit PNGs + flyways | 1,132 PNGs; flyways as polygons |
| Docker-serving /explain | baked JSON fallback + live |
| Cached briefing/explain | precomputed JSON in image |

## Known limits

- Presence-only likelihood for all campaign fits; `ip_weighted`
  exists in refit path for queued species.
- 179 species remain on taxonomic-proxy phylo distance (2 hybrids,
  taxa absent from the trees, one ambiguous GBIF entity).
- BirdTree↔v6 distance scales differ; handled by per-source
  normalization plus an `is_patristic_real` indicator feature
  (dist_frame fail-closed if fewer than two distance axes cover).
- ~13% of aves occurrence cells fall on era5land water pixels and
  are dropped from env extraction.
- Suitability is climate-only; biotic/dispersal axes are future work
  (phylopred PU layer is staged but not shipped).

## Roadmap — the agentic monitor

WildSeek generalizes from HPAI to a multi-disease agentic
surveillance system: a disease registry declares pathogen,
host taxa and evidence feeds; the same pipeline (M-masked niche
campaigns, three-distance susceptibility, detection-pressure ×
reservoir risk) instantiates per disease, and the agent layer
gains scheduling and hypothesis tools — proposing which
data/model to refresh next under a compute budget.
