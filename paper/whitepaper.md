# WildSeek: An Autonomous Ecological Surveillance Platform and Edge Factory for Wildlife Pathogen Spillover

**Author**: WildSeek Consortium  
**Date**: November 2026  
**Artifact Repository**: `meta-hack-devel`  
**Public Snapshot**: [github.com/alrobles/meta-hack](https://github.com/alrobles/meta-hack)  
**Live Monitor**: [wildseek.ecoseek.org](https://wildseek.ecoseek.org)  
**SFT Trajectories & Eval Summaries**: [huggingface.co/datasets/alrobles/wildseek-sft](https://huggingface.co/datasets/alrobles/wildseek-sft)  

> **Operational Disclaimer**: *WildSeek provides computational ecological surveillance intelligence for wildlife biologists, state veterinarians, and agricultural biosecurity monitors. It does not provide medical diagnostics, clinical advice, or personal health recommendations.*

---

## Abstract

Avian influenza virus H5N1 clade 2.3.4.4b has crossed historical ecological boundaries, driving unprecedented mortality across wild avian taxa and spilling over into wild and domestic mammals and agricultural livestock. Conventional wildlife disease monitoring relies on opportunistic carcass discovery and post-mortem testing, leaving biosecurity officials reactive to transmission chains that have already propagated. Here we present **WildSeek**, an autonomous surveillance engine that unifies macroecological niche modeling, patristic phylogenetic distances, and structured LLM-driven literature mining into a continuous operational monitor. 

WildSeek evaluates 101,376 temperature×precipitation ellipsoid-niche fits across 1,147 North American vertebrate species (88 bioclimate pairs, plus refit/buffer rows) parameterized using `xnicher`, constrained by species-specific accessible area masks ($M$). By operationalizing the three-distance macroecological susceptibility framework (Robles-Fernández et al. 2022, *PNAS*, [doi:10.1073/pnas.2122851119](https://doi.org/10.1073/pnas.2122851119)), WildSeek models host probability $p(\text{host})$ across geographic, bioclimatic, and patristic phylogenetic axes (derived from BirdTree consensus and dated mammalian phylogenies). 

To ensure rigorous scientific calibration, we report prospective generalization on 53 literature-evidenced held-out host species, achieving a ROC-AUC of 0.738 (cited as 0.74 in `eval/susceptibility.json`; $n=53$ admits no tight confidence interval), whereas 5-fold cross-validation yields a spatially auto-correlated benchmark AUC of 0.862 ± 0.028 (PR-AUC 0.539). The platform features an autonomous literature extraction factory (`litmine`) aggregating 4,854 interaction edges (2,351 judge-verified) across 3,740 unique host-parasite pairs from 282 articles processed across multiple corpora (139 articles yielded mined edges; `eval/litmine.json`). On held-out gold benchmarks (1/65 holdout pairs post-2020; `eval/litmine.json`), full-text ingestion achieves 56% pair recall compared to 16% for abstract-only scrapers, while automated edge adjudication reaches 100% precision on a 12-edge human audit (from a raw precision of 60% strict to 70% claim-level across an $n=30$ sample; `eval/litmine.json`). Fine-tuning `muse-glimmer-30b` via LoRA parameter-efficient distillation on serverless infrastructure demonstrates exact-match triage scaling from 0.00 to 0.70 (28–0 paired win, $p \approx 7.5 \times 10^{-9}$; `eval/lora_triage.json`), alongside an all-task protocol scoring 0.20 exact-match and 0.82 author-defined semantic agreement under strict audit controls (`eval/lora_all.json`). Coupling host susceptibility with 9,139 spatiotemporally decayed USDA APHIS wild-bird detections maps continuous spillover pressure across 2,247 HUC8 hydrologic sub-basins and 3,109 contiguous United States (CONUS) counties, furnishing an auditable, self-updating early warning monitor for veterinary and ecological biosecurity.

---

## Introduction

The panzootic emergence of highly pathogenic avian influenza (HPAI) H5N1 clade 2.3.4.4b represents a critical ecological shift. Since 2021, the lineage has altered global wild bird migration dynamics and expanded into unprecedented mammalian host ranges—including terrestrial mesocarnivores (e.g., striped skunks *Mephitis mephitis*, red foxes *Vulpes vulpes*), marine pinnipeds, and commercial dairy cattle across North America. In the United States alone, agricultural consequences exceed ~82 million birds in APHIS-confirmed affected flocks across commercial production facilities, precipitating egg and poultry supply-chain volatility, regional biosecurity quarantines, and direct farmgate economic shocks.

Despite the systemic risk to both biodiversity and the agrarian supply chain, existing surveillance paradigms remain inherently lagging. Traditional biosurveillance operates as an opportunistic sink: carcass collection occurs post-die-off, diagnostic PCR or sequencing requires days to weeks for laboratory confirmation, and centralized reporting repositories (such as the USDA Animal and Plant Health Inspection Service [APHIS]) publish spatial detection registries with inherent reporting latencies. More fundamentally, testing is biased toward common sentinel species and captive agricultural flocks, leaving vast reservoirs of cryptic, migratory, or ecologically peripheral wildlife unmonitored. When a novel species is exposed at the wildlife-livestock interface, epidemiologists lack quantitative estimates of whether that species possesses the physiological and ecological competence to amplify or vector the pathogen.

To transition biosecurity from reactive carcass logging to prospective risk intelligence, surveillance platforms must resolve three foundational bottlenecks:
1. **Ecological and Evolutionary Host Competence**: Estimating susceptibility across thousands of candidate taxa in the absence of laboratory challenge experiments, incorporating environmental suitability, spatial co-occurrence, and evolutionary proximity to known hosts.
2. **Automated Synthesis of Unstructured Biomedical Literature**: The scientific literature on host-pathogen associations expands continuously. Relying on manual curation results in fragmented databases that systematically omit newly discovered host records published in regional veterinary literature.
3. **Continuous Computational Synthesis without Rubber-Stamping**: Processing continuous streams of environmental covariates, migratory bird detections, and ecological niche geometries demands an automated pipeline that does not act as a hallucinating black box, but maintains formal audit logs, deterministic rollback mechanisms, and strict separation between routine spatial aggregation and human-in-the-loop scientific refitting.

WildSeek addresses this nexus. Built during the Meta Global AI Developer Hackathon window (October 26 – November 4, 2026), the system unites macroecological modeling, phylogenetic inference, parameter-efficient open-weight language model fine-tuning, and structured literature mining into a continuous surveillance loop. Deployed live at [wildseek.ecoseek.org](https://wildseek.ecoseek.org), WildSeek computes continuous risk fields across CONUS, ranking transmission exposure across 2,247 HUC8 watersheds and 3,109 agricultural counties.

---

## Related Work

Empirical macroecology and disease biogeography demonstrate that pathogen transmission is non-random across ecological space. Pathogens require competent hosts whose environmental requirements intersect with climatic suitability and whose phylogenetic traits accommodate viral cell entry and replication.

### The Three-Distance Susceptibility Framework

The theoretical foundation of WildSeek’s host susceptibility modeling originates from the three-distance macroecological framework established by Robles-Fernández et al. (2022, *Proceedings of the National Academy of Sciences*, [doi:10.1073/pnas.2122851119](https://doi.org/10.1073/pnas.2122851119)). Rather than relying solely on taxonomic affinity or static species distribution overlap, the three-distance formulation posits that a candidate host's probability of harboring a pathogen is a joint function of its separation from confirmed hosts along three orthogonal axes:
- **Environmental Distance ($d_{\text{env}}$)**: The divergence between the candidate species' fundamental Hutchinsonian niche and the realized climatic niche of established reservoir hosts, computed across multi-dimensional bioclimatic space.
- **Geographic Distance ($d_{\text{geo}}$)**: The spatial Euclidean or dispersal-constrained barrier separating the candidate species' range from observed infection clusters or reservoir populations.
- **Phylogenetic Distance ($d_{\text{phy}}$)**: The evolutionary divergence time separating the candidate taxon from confirmed viral hosts, reflecting conserved host-cell receptor structures and innate immunological pathways.

While the original 2022 framework proved the predictive capacity of multi-distance topologies on viral and parasitic systems retrospectively, operationalizing this approach for real-time continental surveillance requires solving critical data engineering challenges: constructing species-specific accessible mobility boundaries ($M$), running high-dimensional ellipsoid optimization campaigns, reconciling conflicting phylogenetic tree topologies, and dynamically updating host labels via automated text mining.

### Macroecological Niche Estimation: Ellipsoid Optimization

Correlative species distribution modeling frequently encounters spatial over-fitting when complex algorithms (e.g., MaxEnt, Boosted Regression Trees) fit noisy presence-only collections. To enforce physiologically plausible response surfaces, WildSeek deploys the `xnicher` framework (Robles-Fernández et al., CRAN `xnicher` v1.0.0). By optimizing minimum-volume enclosing ellipsoids in bivariate bioclimatic space, `xnicher` generates convex fundamental niche boundaries that resist peripheral sampling artifacts while retaining computational tractability over continental grids.

---

## Methods

WildSeek is structured as four interconnected subsystems: (1) high-throughput niche modeling and three-distance host susceptibility scoring, (2) the three-layer `litmine` full-text literature cascade, (3) instruction-tuned open-weight model adaptation via LoRA, and (4) an autonomous nightly factory loop with QA gatekeeping.

### 1. High-Throughput Ecological Niche Modeling and the Accessible Area ($M$)

Biological species do not occupy environmental conditions simply because those conditions are physiologically tolerable; they are constrained by geographic accessibility, dispersal limitations, and historical colonization. In Soberón and Peterson’s BAM diagram framework, the accessible area ($M$) defines the spatial extent across which a species could plausibly disperse. Ignoring $M$ when extracting background training samples introduces severe environmental pseudo-absence bias.

For 1,147 North American vertebrate species (avian and mammalian candidate reservoirs), we constructed explicit $M$ polygons using the `oneearthr` package (v1.0.0, querying RESOLVE ecoregion geometries). Global occurrences were harvested from a deduped GBIF mirror thinned at 1/120° spatial resolution (~1 km grid cell). A species' accessible area $M$ was defined by intersecting its occurrence coordinates with global ecoregions, retaining the ecoregions covering $\ge 95\%$ of verified presences. 

Within each species-specific $M$, background and presence points were extracted across 19 bioclimatic variables derived from ERA5-Land reanalysis climatologies downscaled to a continuous CONUS raster grid. To model niche occupancy without distributional over-fitting, we evaluated 88 distinct bivariate temperature $\times$ precipitation feature combinations per species using `xnicher`. In total, **101,376 fit rows across 1,147 species (88 pairs, plus refit/buffer rows)** were executed and logged in the full catalog (`data/fit_catalog.csv`, 101,376 rows; reproducible via pipeline or inspected in the shipped surrogate `app/data.sample/fit_catalog.csv` of 8,888 rows). We selected the AIC-winning ellipsoid per species, producing masked CONUS suitability rasters at 1/120° resolution (~900 m, EPSG:4326 internal projection, reprojection to EPSG:3857 for web tiles).

### 2. Three-Distance Susceptibility Parameterization

For each candidate species $i \in \{1, \dots, 1147\}$, susceptibility was formalized as a supervised classification task where positive labels represent confirmed H5N1 wild hosts identified by USDA APHIS registries and verified literature records (frozen as of the training baseline):
$$\text{logit}(p(\text{host}_i)) = \beta_0 + \sum_{d \in \{\text{geo},\text{env},\text{phy}\}} \beta_d d(i) + \sum_{j \le k} \beta_{jk} d_j(i) d_k(i) + \sum \beta_m X_m(i)$$
where $\sigma(z) = (1 + e^{-z})^{-1}$, and the model is parameterized as an L2-regularized logistic regression over extended polynomial and pairwise interaction features (`model_A` in `pipeline/suscept_model.py`), incorporating mean neighbor distances (`mean_j_geo_pos5`, `mean_j_env_pos5`) alongside base features.

The distances to known infected host clusters were computed as follows:
- **Geographic Distance ($d_{\text{geo}}$)**: Euclidean and range-boundary centroid separation from species $i$ to confirmed infected populations across CONUS.
- **Environmental Distance ($d_{\text{env}}$)**: Mahalanobis distance between the optimal Hutchinsonian niche centroid of species $i$ and the joint centroid of confirmed H5N1 hosts within the standardized 19-bioclimatic environmental space.
- **Phylogenetic Distance ($d_{\text{phy}}$)**: True patristic distance along evolutionary branch lengths. Avian species were placed on the BirdTree Stage2 Ericson posterior consensus tree (1,048-tree distribution, data.vertlife.org), reconciled via the AVONET taxonomic crosswalk and manual epithet resolution (resolving 202 of 208 historically proxied avian taxa). Mammalian species were projected onto a calibrated, dated mammalian phylogeny (`v6_point.nwk`). Exactly 968 of 1,147 species were resolved with real patristic tree distances; the remaining 179 species (2 hybrids, taxa absent from published trees, and one ambiguous GBIF entity; `SUBMISSION.md`) were assigned taxonomic cophenetic distances using an explicit fallback model. Per-source normalizations and an `is_patristic_real` indicator feature were incorporated into the model matrix, ensuring fail-closed execution if fewer than two distance axes cover a candidate taxon.

Permutation feature importance confirmed the hierarchy of transmission determinants: geographic proximity proved most informative (relative importance 0.31), followed by environmental niche proximity (0.16) and phylogenetic divergence (0.12).

### 3. The `litmine` Three-Layer Literature Cascade

To maintain real-time host label currency without relying on manual database curators, WildSeek operates `litmine`, an automated text-mining factory designed to extract host-parasite relationships directly from PubMed Central (PMC) Open Access full-text articles and OpenAlex metadata.

The cascade operates across three discrete tiers:
1. **Capa 0/1 (Passage Triage)**: Full-text PMC XML documents are parsed into paragraph chunks. A high-throughput open-weight model (`muse-spark-open` hosted on Fireworks serverless) performs binary triage classifying whether each text chunk documents an empirical host-parasite association. On the primary PMC evaluation corpus, triage achieved 38% retention (303/772 chunks passing), 56% token savings, and $1.33 logged spend (`eval/litmine.json`). In a separate large-scale run across 3,165 text chunks (ZOVER corpus; `eval/litmine.json` `zover_triage`), triage retained 23% (721 YES chunks) at ~74% token savings for $1.93 in Capa-0/1 spend.
2. **Capa 2 (Structured Relation Extraction)**: Retained passages are processed by an extraction prompt enforcing strict JSON schema typing: parasite species, host taxon, interaction type (natural infection, experimental inoculation, seroprevalence), evidence span (verbatim substring), geographic location, observation date, and diagnostic methodology. Extraction operates at a compute cost of **$0.0014 per extracted edge** (`eval/litmine.json`).
3. **Capa 3 (Adjudication and Verification by JUDGE)**: LLM extractors can conflate serological antibodies with active viral shedding, or extract incidental species mentions from literature citations. The Capa-3 JUDGE (`muse-glimmer-30b` self-hosted on KU HPC during the hackathon, falling back to cloud-hosted `muse-spark-open`) acts as an adversarial auditor. The judge receives solely the extracted JSON edge and the raw `evidence_span` string, evaluating whether the text explicitly asserts viral detection in the named organism. The judge rejects serological surveys without direct viral detection and unconfirmed experimental vectors, retaining approximately 55% of raw edges (e.g., 42% retention on the ZOVER abstract benchmark; `eval/litmine.json`).

### 4. Parameter-Efficient Model Adaptation (Glimmer LoRA SFT)

To evaluate whether smaller open-weight models can replace closed commercial APIs for specialized ecological decision pipelines, we constructed supervised fine-tuning (SFT) datasets from historical triage trajectories, archiving JSONL trajectories and evaluation summaries publicly on Hugging Face (`huggingface.co/datasets/alrobles/wildseek-sft`).

Using Fireworks serverless LoRA infrastructure ($0 promotional compute tier), we trained rank-8 ($r=8$) Low-Rank Adaptations on `muse-glimmer-30b` (recipe and tooling archived in the companion repository `wildseek-lora`; deployed adapter path `accounts/alrobles/models/muse-starter-sl-wildseek-triage-20261103-215412`):
- **Triage Specialization (`wildseek-triage-20261103-215412`)**: Distilled over passage classification tasks. Across 44 training steps, holdout exact-match accuracy increased from **0.00 to 0.70** (28–0 paired win over base model, McNemar test $p = 7.45 \times 10^{-9}$; `eval/lora_triage.json`).
- **All-Task Complex Parsing (`wildseek-all-20261104-0017`)**: Distilled across joint passage triage, edge extraction, and ellipsoid niche triage. Across 120 steps, raw holdout exact-match advanced from 0.00 to 0.20 (8–0 paired win, $p = 0.0078$; `eval/lora_all.json`). 

A rigorous semantic audit of all-task outputs revealed that raw exact-match metrics were severely penalized by open-ended rationale generation: field-level accuracy reached 1.00 on `decision`, 1.00 on `switch_to`, and 1.00 on `confidence`, but was scored 0.00 on `reason` due to lexical variation. When rescored using token-F1 $\ge 0.70$ and $\ge 80\%$ gold numeric literal preservation (`tools/fw_distill.py rescore`), rationale agreement reached 1.00 (24/24 valid paraphrases preserving quantitative bounds), lifting comprehensive performance from 0.20 exact-match to **0.82 under author-defined semantic agreement** (`eval/README.md`, `eval/lora_all.json`). The residual 7 rows comprised 4 empty extraction answers, 2 truncated outputs, and 1 over-extraction (`eval/README.md`).

### 5. Detection Pressure, Continental Risk Aggregation, and Supply-Chain Exposure

To compute prospective transmission risk, host susceptibility was synthesized with empirical pathogen circulation. From USDA APHIS spatial registries, we ingested **9,139 confirmed HPAI detections in wild birds** (reconciled across GeoJSON geometries and metadata manifests; `SUBMISSION.md`). 

Each detection point was assigned an exponential temporal decay based on observation age:
$$w_j = \exp\left(-\frac{\Delta t_j}{\tau}\right)$$
where $\Delta t_j$ represents days elapsed since detection and $\tau = 90 / \ln(2) \approx 129.8$ days, corresponding to a **90-day half-life**.

Decayed detection weights were mapped onto the CONUS grid and smoothed using a continuous spatial Gaussian filter:
$$D(x, y) = \sum_{j} w_j \cdot \frac{1}{2\pi \sigma^2} \exp\left(-\frac{\|(x, y) - (x_j, y_j)\|^2}{2\sigma^2}\right)$$
parameterized with a spatial kernel bandwidth $\sigma \approx 10\text{ km}$. The resulting detection pressure surface $D(x, y)$ was normalized to the unit interval $[0, 1]$.

Continental risk was formulated as the cross-product of detection pressure and the competent reservoir community:
$$R(x, y) = D(x, y) \cdot \sum_{i \in \text{taxa}} p(\text{host}_i) \cdot S_i(x, y)$$
where $S_i(x, y) \in [0, 1]$ represents the $M$-masked climatic suitability of species $i$ at coordinates $(x, y)$.

To furnish actionable boundaries for environmental managers, continuous risk was zonal-aggregated across **2,247 HUC8 watersheds** (hydrologic sub-basins defined by the USGS Watershed Boundary Dataset). Supply-chain vulnerability was computed by intersecting these watershed transmission indices with USDA agricultural livestock census records across **3,109 CONUS counties**, mapping county-level exposure metrics against commercial poultry inventories.

### 6. The Nightly Factory Loop and QA Approver Quorum

WildSeek operationalizes an autonomous data factory (`pipeline/nightly.py`, detailed in `docs/FACTORY.md`) executing nightly at cron 03:15. The factory decouples pipeline execution into five structured phases:
1. **Ingestion (`fetch_aphis.py`)**: Pulls incremental updates from USDA APHIS ArcGIS REST endpoints, updating local Parquet stores.
2. **Planner (`agent/planner.py`)**: Computes data deltas. If new detections involve previously parameterized species, the run is flagged as *routine*. If an unmodeled taxon appears or taxonomic splits occur, the planner generates a *refit spec* that flags human operators.
3. **Builder**: Orchestrates continuous spatial re-renders. In cluster mode, Slurm batch jobs recompute raster arrays on high-performance computing (HPC) nodes; in localized standalone mode (`--casa`), vector tables, risk scores, and DuckDB indices refresh over frozen background rasters.
4. **QA Approver Quorum (`agent/qa.py`)**: Before publishing new artifacts, a four-member automated jury evaluates deployment integrity:
   - *Code Gate*: Confirms physical asset counts, probability bounds ($0 \le p \le 1$), non-empty PNG outputs, and valid GeoJSON schemas.
   - *Security Gate*: Ensures data volume monotonicity (blocking builds where detection counts drop $>5\%$ or raster coverage degrades).
   - *UX Gate*: Validates frontend metadata contracts, bounding boxes, and API route dependencies.
   - *Brain Gate*: An instruction-tuned LLM (`muse-spark-1.3`) audits the execution delta and manifest, issuing an auditable approval verdict.
   Deployments require a $\ge 3/4$ quorum. A failure in any hard gate or a cost overrun aborts deployment, generating `qa_report.json` and halting publication.
5. **Production Deployment**: Verified assets are synchronized to production hosting, serving queries via FastAPI (`api/main.py`) backed by DuckDB queries and MapLibre client-side vector visualizations.

---

## Results

Quantitative evaluations confirm the predictive utility of the three-distance susceptibility framework, the extraction efficacy of the full-text literature cascade, and the operational integrity of the agentic pipeline.

### 1. Host Susceptibility Performance and Prospective Validation

Evaluating host susceptibility across ecological networks is vulnerable to optimistic data leakage caused by spatial and phylogenetic autocorrelation. Standard stratified 5-fold cross-validation of the second-order polynomial logistic regression model yielded a cross-validated **ROC-AUC of 0.862 ± 0.028 and a PR-AUC of 0.539** across 1,147 species (159 positive hosts; `eval/susceptibility.json`). However, because spatial autocorrelation artificially inflates random-fold validation scores, we established an independent prospective evaluation set.

Mining full-text literature published outside the model's training baseline identified **53 literature-evidenced held-out host species**. When evaluated strictly against these prospectively recovered taxa, the three-distance susceptibility model attained an **ROC-AUC of 0.738** (reported transparently as **AUC 0.74** across documentation; `eval/susceptibility.json`). Due to sample size constraints, $n=53$ admits no tight confidence interval, but the score confirms discriminative signal on unobserved hosts.

To maintain strict scientific reproducibility, on **October 28, 2026**, WildSeek pre-registered and frozen-locked the top-15 unlabeled candidate species exhibiting the highest modeled $p(\text{host})$ values (`we-called-it` registry; `app/data.sample/we_called_it.json`). These 15 species—spanning both terrestrial and semi-aquatic birds and mammals—currently sit in an `awaiting-confirmation` state. While subsequent full-text mining runs have recovered empirical literature edges documenting infection for 4 of these 15 species (`SUBMISSION.md`), per the registry's strict verification rule, confirmation requires a PMID published after the October 28 freeze date naming the species as host; all 15 species remain formally awaiting-confirmation in the shipped artifact.

### 2. Literature Extraction Efficacy and Verification Auditing

The `litmine` cascade demonstrated marked improvements over traditional biomedical abstract indexing (`eval/litmine.json`):
- **Ingestion Scale**: Across 282 articles processed across multiple corpora (139 articles yielded mined edges; `eval/litmine.json`), the cascade aggregated **4,854 total interaction edges** (comprising `edges_fulltext` 740, `hpai_fulltext_edges` 2,682, `edges_zover` 217, and `edges_zover_full` 1,116) representing **3,740 unique host-parasite pairs** (with 2,172 edges and 1,547 pairs in `interactions.parquet`). The automated Capa-3 adjudication layer verified **2,351 edges** as meeting strict empirical infection criteria.
- **Full-Text vs. Abstract Recall**: Evaluated against a gold-standard validation corpus of verified filovirus (Ebola and Lassa) host associations (1/65 holdout pairs post-2020; `eval/litmine.json`), full-text passage extraction achieved **56% pair recall**, whereas abstract-only extraction achieved only **16% pair recall**—a 3.4-fold recall advantage (`eval/litmine.json`).
- **Precision and Adversarial Auditing**: An independent human audit of $n=30$ randomly sampled raw candidate edges revealed a baseline extraction precision of 70% at the general paper-claim level and 60% under strict verbatim evidence-span verification (`eval/litmine.json`). In contrast, when edges were adjudicated by the Capa-3 JUDGE (`muse-glimmer-30b`), precision reached **100% on a 12-edge human audit sample** (12/12 correct), confirming that automated adjudication filters out spurious serological mentions and taxonomic noise (`eval/litmine.json`).
- **Operational Cost**: Capa-2 relation extraction operated at an amortized cost of **$0.0014 per extracted edge**, while hosted Capa-3 edge adjudication added $0.0010 per edge (totaling $0.0024 per fully verified edge; `eval/litmine.json`), establishing literature surveillance as economically sustainable at continental scale.

### 3. Open-Weight Model Adaptation via LoRA Distillation

Fine-tuning results on `muse-glimmer-30b` demonstrated rapid convergence on structured classification:
- On the binary passage triage task, base un-tuned weights failed completely (exact-match 0.00, frequently generating runaway generation loops; 3 unterminated sequences across 40 prompts). In contrast, the adapted LoRA adapter (`wildseek-triage-20261103-215412`) achieved **0.70 exact-match accuracy** within 44 training steps (28–0 paired win over base model, $p = 7.45 \times 10^{-9}$; `eval/lora_triage.json`).
- On the comprehensive all-task run (`wildseek-all-20261104-0017`), exact-match advanced from 0.00 to **0.20** (8–0 paired win, $p = 0.0078$). Evaluating individual JSON fields revealed 100% accuracy on discrete categorization (`decision`, `switch_to`, `confidence`), while open-ended textual justification caused superficial exact-match failures. Author-defined semantic rescoring demonstrated **0.82 holdout agreement** across all fields, with a residual error composition of 7 rows (4 empty answers, 2 truncated outputs, 1 over-extraction; `eval/README.md`, `eval/lora_all.json`).

### 4. Agentic Niche Triage and Executable Deltas

A core design requirement of WildSeek is preventing autonomous language models from acting as unsupervised or unrepeatable code-mutators. During the macroecological modeling campaign, 1,147 species were evaluated across 88 bivariate niche candidates. While 974 species exhibited decisive AIC-winning fits, deterministic gates (`pipeline/decide_tail.py:44-47`) isolated an **ambiguous tail of 173 species** reaching triage thresholds: top-5 AIC spread < 15.0 (`TAIL_AIC_SPREAD = 15.0`), occurrence count < 120 (`TAIL_NOBS = 120`), marine fraction > 0.5 (`TAIL_MARINE = 0.5`), degenerate accessible areas ($n_{\text{eco}} < 3$ or $n_{\text{eco}} > 200$), or non-standard fit status (`flag != accepted_global`).

An instruction-tuned agent (`muse-spark-1.3`) conducted deep diagnostic reviews across this 173-species tail. Rather than hallucinating parameters, the agent issued **49 substantive `flag_review` interventions** complete with structured rationales (e.g., isolating unstable ellipsoid orientations in sparse desert endemics, or identifying marine mammal occurrences fitted against terrestrial precipitation rasters; logged in `app/data.sample/decisions_delta.csv`). 

Crucially, under WildSeek's operational rules:
- **Zero refits were executed in-window**: In accordance with verified submission audits, all 173 ambiguous tail species received accept or flag verdicts; zero automated model refits were triggered or executed in-window.
- **Executable Deltas Framing**: Proposed parameter adjustments and alternative ellipsoid configurations were serialized as deterministic, reproducible deltas via `pipeline/refit_switched.R`. This guarantees that all agent interventions remain fully inspectable, version-controlled, and executable by human scientists prior to altering continental risk layers.

---

## Known Limits

To ensure appropriate operational interpretation, we document several methodological constraints:
1. **Presence-Only Niche Formulations**: Continental niche parameters are optimized using presence-only occurrences within accessible areas ($M$). While `xnicher` bounds geographic over-prediction via convex minimum-volume ellipsoids, presence-only likelihoods do not explicitly model sampling effort or non-detection probabilities. An inverse-probability-weighted formulation (`ip_weighted`) has been developed for the pipeline refit path but was not activated during the baseline campaign.
2. **Taxonomic Coverage and Phylogenetic Proxies**: Of the 1,147 modeled species, 179 taxa remain on taxonomic-proxy phylogenetic distances rather than true patristic tree distances. These represent 2 inter-specific hybrids, taxa absent from published posterior consensus trees, or an ambiguous GBIF entity (`SUBMISSION.md`). Furthermore, because BirdTree consensus branch lengths and mammalian point trees (`v6_point.nwk`) operate on distinct divergence scales, distance matrices require per-source standardizations and fail-closed checks (`is_patristic_real`).
3. **Climatic Covariate Masking and Marine Boundaries**: Macroecological extraction utilizes downscaled ERA5-Land bioclimatic rasters. Because ERA5-Land excludes open ocean and large marine water bodies, approximately 13% of occurrences for coastal avian species (e.g., alcids, pelagic gulls, terns) intersect water-masked pixels and are excluded from climate fitting.
4. **Static Abiotic Environmental Dimensions**: The present suitability layer models purely abiotic climatic tolerances. Dispersal rate limits, dynamic seasonal migration corridors, and biotic exclusion (host-host competition) are not explicitly modeled in the suitability surface.
5. **LoRA Evaluation Holdout Boundaries**: As documented in `eval/README.md`, an audit of the initial multi-task distillation split revealed minor token leakage (3 of 40 holdout instances shared Jaccard similarity $\ge 0.73$ with the training pool) and training distributions biased toward negative examples (63% negative chunks), slightly skewing boundary thresholds on multi-task evaluation rows.
6. **Susceptibility Label Provenance and Holdout Cut**: Susceptibility training labels were established from USDA APHIS registries and verified literature records available up to the model freeze date, whereas prospective validation relied on 53 host taxa evidenced in mined literature. Because the temporal cut between historical positive labels and prospective literature recovery was not partitioned by an absolute publication-date firewall across all historical corpora, prospective generalization may partially reflect label recovery alongside unobserved host discovery.

---

## Reproducibility and Repository Layout

WildSeek is engineered for end-to-end auditability. The complete scientific build, evaluation suite, and serving infrastructure reside within the repository:

### Repository Layout

```
alrobles/meta-hack/
├── pipeline/             # Continental data build: GBIF ingestion, M masks,
│                         # env cube, xnicher campaigns, risk aggregation,
│                         # and executable refit scripts (refit_switched.R)
├── agent/                # Meta Model API clients, typed triage drivers,
│                         # explainers, and the 4-member QA approver quorum
├── litmine/              # Literature edge factory: PMC fetchers, passage
│                         # triage, Capa-2 parser, and Capa-3 JUDGE
├── api/                  # High-performance FastAPI monitor service (main.py)
├── app/                  # Single-file client UI (MapLibre GL vector maps)
│   └── data.sample/      # Minimal pre-baked dataset for zero-configuration boot
├── serve/                # Docker compose orchestration (container: ecoseek-wildseek)
├── eval/                 # Machine-readable evaluation manifests and proofs
│   ├── README.md         # Quantitative evidence guide and audit documentation
│   ├── susceptibility.json # ROC-AUC, PR-AUC, and prospective holdout metrics
│   ├── litmine.json      # Literature edge counts, recall, and audit logs
│   ├── lora_triage.json  # Glimmer-30B triage LoRA training and evaluation
│   └── lora_all.json     # Glimmer-30B all-task LoRA evaluation and semantic logs
├── docs/                 # Architectural specifications, factory constitution,
│                         # and historical audit records (FACTORY.md, AUDIT-2026-10-26.md)
└── paper/                # Scientific documentation and consensus dialogue
    └── whitepaper.md     # This whitepaper draft
```

### Local Demonstration and Reproduction in 60 Seconds

The repository includes a lightweight, pre-baked artifact bundle (`app/data.sample/`, $\approx 5\text{ MB}$) enabling immediate local execution of the complete API and user interface without requiring access to high-performance computing clusters or proprietary API credentials:

```bash
# 1. Seed minimal pre-baked vector and tabular artifacts
cp -r app/data.sample app/data

# 2. Configure operational environment (runs keyless for seeded entities)
cp .env.example .env

# 3. Boot the FastAPI service and MapLibre frontend
cd serve && docker compose up
```

Upon initialization, the monitor service is accessible locally at `http://localhost:8654` (mapping container `ecoseek-wildseek`). Live public endpoints are verified at:
- Web Interface: [wildseek.ecoseek.org](https://wildseek.ecoseek.org)
- System Health: [wildseek.ecoseek.org/health](https://wildseek.ecoseek.org/health)
- Operational Metrics: [wildseek.ecoseek.org/metrics](https://wildseek.ecoseek.org/metrics)
- Prospective Host Tracking: [wildseek.ecoseek.org/we-called-it](https://wildseek.ecoseek.org/we-called-it)
- Literature Edge Ticker: [wildseek.ecoseek.org/litmine](https://wildseek.ecoseek.org/litmine)
- Executable Triage Deltas: [wildseek.ecoseek.org/decisions](https://wildseek.ecoseek.org/decisions)

Training trajectories, evaluation datasets, and summary metrics are archived publicly on Hugging Face at [huggingface.co/datasets/alrobles/wildseek-sft](https://huggingface.co/datasets/alrobles/wildseek-sft). Fine-tuned adapter checkpoints are deployed on Fireworks serverless infrastructure (`accounts/alrobles/models/muse-starter-sl-wildseek-triage-20261103-215412`), with fine-tuning recipes and data conversion tools preserved in the companion repository `wildseek-lora`.

---

## Data Availability

All underlying primary datasets and foundational modeling tools are publicly accessible:
- **Global Biodiversity Information Facility (GBIF)**: Species occurrence records accessed via GBIF.org ([https://doi.org/10.15468/dd.8m3t4a](https://doi.org/10.15468/dd.8m3t4a)).
- **ERA5-Land Reanalysis**: High-resolution surface climatologies from the Copernicus Climate Change Service (ECMWF, [https://cds.climate.copernicus.eu/](https://cds.climate.copernicus.eu/)).
- **USGS Watershed Boundary Dataset (WBD)**: HUC8 hydrologic sub-basins from the U.S. Geological Survey ([https://www.usgs.gov/national-hydrography/watershed-boundary-dataset](https://www.usgs.gov/national-hydrography/watershed-boundary-dataset)).
- **PubMed Central Open Access (PMC OA) & OpenAlex**: Open-access full texts via PMC FTP service ([https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/](https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/)) and scholarly bibliometrics via OpenAlex ([https://openalex.org](https://openalex.org)).
- **Modeling Tooling**: Niche optimization library `xnicher` ([https://cran.r-project.org/package=xnicher](https://cran.r-project.org/package=xnicher)) and ecoregion boundary processor `oneearthr` ([https://github.com/alrobles/oneearthr](https://github.com/alrobles/oneearthr)).

---

## References

1. Robles-Fernández, S. D., Lira-Noriega, A., Peterson, A. T., & Reuman, D. C. (2022). Predicting potential host species of emerging pathogens using a three-distance macroecological framework. *Proceedings of the National Academy of Sciences*, 119(30), e2122851119. [doi:10.1073/pnas.2122851119](https://doi.org/10.1073/pnas.2122851119).
2. United States Department of Agriculture, Animal and Plant Health Inspection Service (USDA APHIS). (2026). Detections of Highly Pathogenic Avian Influenza in Wild Birds. Washington, D.C.
3. Jetz, W., Thomas, G. H., Joy, J. B., Hartmann, K., & Mooers, A. O. (2012). The global diversity of birds in space and time. *Nature*, 491(7424), 444–448.
4. Tobias, J. A., et al. (2022). AVONET: morphological, ecological and geographical data for all birds. *Ecology Letters*, 25(3), 581–597.
5. Upham, N. S., Esselstyn, J. A., & Jetz, W. (2019). Inferring the mammal tree of life, using phylogenetic backbones to reconcile data-dense trees. *PLOS Biology*, 17(12), e3000494.
6. Soberón, J., & Peterson, A. T. (2005). Interpretation of models of fundamental ecological niches and species' distributional areas. *Biodiversity Informatics*, 2, 1–10.
7. Dinerstein, E., et al. (2017). An ecoregion-based approach to protecting half the terrestrial realm. *BioScience*, 67(6), 534–545.
