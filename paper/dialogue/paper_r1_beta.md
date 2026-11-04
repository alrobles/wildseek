# DiDAL PAPER-R1-BETA — rival review of `paper/whitepaper.md`

Reviewer: BETA (SWE-2 Max) · 2026-11-04
Artifact under review: `paper/whitepaper.md` (252 lines), cross-checked
against `SUBMISSION.md`, `NEW.md`, `README.md`, `eval/README.md`,
`eval/*.json`, `docs/eval-model-report.md`, `docs/FACTORY.md`,
`docs/plan.md`, `docs/progress-report.md`, `docs/hackathon-rules.md`,
`pipeline/decide_tail.py`, `pipeline/predict_suit.R`,
`pipeline/nightly.py`, `data/fit_catalog.csv`, `data/aphis_poultry.parquet`,
`app/data.sample/{we_called_it.json,detections.geojson,meta.json,
decisions_delta.csv,fit_catalog.csv}`, the HF API listing of
`alrobles/wildseek-sft`, and `paper/dialogue/*r1*` precedent.

## 0. Binding-rules compliance check

| Rule | Status |
|---|---|
| switch_to: zero refits; "executable deltas" only | PASS — "Zero refits were executed in-window" (:169), 49 flag_review, deltas via `refit_switched.R`. Verified: 173 rows in shipped `decisions_delta.csv`, 49 `flag_review` (verified count by direct read). |
| Holdout AUC 0.74 (53 hosts) leads; CV 0.862 caveated | PASS — abstract and Results lead with 0.738/53; CV labeled "spatially auto-correlated". |
| LoRA dual: 0.70 AND 0.20/0.82 + leakage caveat | PASS — both reported; leakage caveat in Known Limits §5. |
| Litmine 100% = 12/12 audit; raw 60–73% n=30 | PASS — "100% on a 12-edge human audit sample (12/12)", raw 70%/60% n=30 disclosed. |
| No unprovenanced precision ("440") | PASS — "(88 pairs, plus refit/buffer rows)" avoids the bare 440. |
| No file://, ~/env, hostnames | PASS — grep clean (localhost:8654 in quickstart is expected). |
| Claims cited to artifacts | PARTIAL — most numbers carry `eval/*.json` pointers, but at least one cited artifact contradicts the claim (issue 3) and several numbers are invented (issues 1–2). |

## 1. Per-section verdicts

| Section | Verdict | Driver |
|---|---|---|
| Header / metadata | **FLAG** | "Open Weights & SFT Data" overclaims — the HF dataset repo ships JSONL trajectories + one summary JSON, zero weight files (issue 5). |
| Abstract | **FLAG (minor)** | Numbers check against artifacts, but "cited as 0.74 in `eval/susceptibility.json`" misattributes a rounding (json says 0.738); "from 282 articles" vs `papers_mined: 139`; "an continuous" typo. |
| Introduction | **HOLD (1 nit)** | "82 million commercial poultry culled" — artifact says `birds_affected` = 82,017,090 (affected ≠ culled). |
| Related Work | **HOLD** | Framework attribution to PNAS three-distance paper is correct and properly hedged. |
| Methods §1 (M, niches) | **FLAG** | 1/100° raster claim contradicts SUBMISSION + pipeline header (1/120°); `data/fit_catalog.parquet` is a `.csv` in a gitignored dir; "≥95%" phrasing ambiguous. |
| Methods §2 (three-distance) | **FLAG (minor)** | Displayed model omits the poly2 terms the Results prose claims; "domestic breeds" invented; label sources ("verified literature records") blur the holdout boundary. |
| Methods §3 (litmine) | **REWRITE** | 23%/74%/$1.93 are ZOVER-run numbers attributed to the PMC run and cited to a contradicting artifact; "end-to-end ingestion costs" scope error (issue 3). |
| Methods §4 (LoRA) | **HOLD** | r8, steps, wins, p-values all verify. |
| Methods §5 (detection/risk) | **HOLD** | 9,139 detections, τ=129.8 d (90-d half-life), σ≈10 km, R=D·Σp·S — all match SUBMISSION. |
| Methods §6 (factory/QA) | **HOLD** | Gate names, ≥3/4 quorum, cost veto, qa_report.json verified against `docs/FACTORY.md`. |
| Results §1 (susceptibility) | **FLAG** | No CI on the n=53 headline; "validating forward-looking predictive capacity" overclaims — shipped `we_called_it.json` shows 15/15 `awaiting-confirmation` (issues 6, 15). |
| Results §2 (litmine) | **REWRITE** | "772 chunks → 4,854 edges" conflates ≥4 corpora; `interactions.parquet` attribution contradicts the artifact's own note; omits 2% holdout leakage (issues 4, 11). |
| Results §3 (LoRA) | **FLAG (minor)** | Numbers verify, but 0.82 is a self-defined post-hoc rescore rubric; residual-error composition omitted. |
| Results §4 (agentic deltas) | **REWRITE** | 173/49/zero-refit verified, but the deterministic-gate constants (ΔAIC<2.0, n<25, >40%) are fabricated — code uses 15.0/120/0.5 (issue 2). |
| Known Limits | **HOLD** | All five entries trace to SUBMISSION/eval sources; LoRA leakage honestly stated. |
| Reproducibility | **FLAG** | `.parquet` vs `.csv`, `AUDIT.md` filename, unverifiable "adapter checkpoints on HF", unprovenanced "UTC". |
| References | **REWRITE** | Reference 8 is fabricated (blocker); load-bearing data sources (GBIF, ERA5-Land, WBD, OpenAlex, PMC) uncited. |

## 2. Issues (numbered; exact quote → correction source)

1. **`whitepaper.md:252` — Reference 8 is fabricated.** Severity: **blocker.**
   > "Muñoz, G., et al. (2024). Open-access biomedical text mining and automated relation extraction. *Journal of Biomedical Informatics*, 148, 104542."
   *J. Biomed. Inform.* vol. 148 art. 104542 is Katyan, Saha & Foysal, "Explainable XGBoost for Clinician-Acceptable Disease Risk Prediction using Clinical Notes" (2024); `doi:10.1016/j.jbi.2023.104542` 404s. An invented author/title on a real volume/article number — in a paper whose entire pitch is auditability.
   Fix: cite the real source for the text-mining claim or delete the reference.

2. **`whitepaper.md:164` — Deterministic-gate constants are invented.** Severity: **major.**
   > "AIC ties (ΔAIC < 2.0), sparse occurrence counts (n < 25), high marine fraction (>40%), or degenerate accessible areas (M)"
   `pipeline/decide_tail.py:44–47,92–96`: `TAIL_AIC_SPREAD = 15.0` (top-5 AIC spread < 15), `TAIL_NOBS = 120`, `TAIL_MARINE = 0.5`, `n_eco < 3 or > 200`, plus `flag != accepted_global`. All three stated thresholds are wrong.
   Fix: quote the real constants from `decide_tail.py`.

3. **`whitepaper.md:88` — Triage stats conflate two runs; cited artifact contradicts.** Severity: **major.**
   > "Triage retains 23% of candidate chunks (303/772 chunks passing on initial benchmarks; `eval/litmine.json`), achieving a 74% token reduction and reducing end-to-end ingestion costs to $1.93 per 3,000-chunk corpus ($1.33 logged on the primary evaluation corpus)"
   `eval/litmine.json` for the 303/772 corpus: `yes_rate 0.38`, `tok_savings 0.56`, `cost_usd 1.33`. The 23%/74%/$1.93 triple is the **ZOVER** triage run (`docs/progress-report.md:58`: "3,165 chunks → 721 YES (23%), ~74%, $1.93 spark-open") — and $1.93 is Capa-0/1 triage spend, not "end-to-end ingestion". 303/772 = 39%, not 23%.
   Fix: separate the corpora — e.g. "38% retained (303/772; `eval/litmine.json`), 56% token savings, $1.33 logged; a second 3,165-chunk run retained 23% at ~74% token savings for $1.93".

4. **`whitepaper.md:151` — "772 chunks → 4,854 edges" corpus conflation; wrong parquet attribution.** Severity: **major.**
   > "Across 282 open-access PMC papers, the cascade processed 772 text chunks, extracting 4,854 total interaction edges representing 3,740 unique host-parasite pairs (`interactions.parquet`)"
   The 4,854 edges aggregate ≥4 corpora in the same artifact (`edges_fulltext 740` + `hpai_fulltext_edges 2682` + `edges_zover 217` + `edges_zover_full 1116`), not the 772-chunk PMC run (≈6.3 edges/chunk is implausible). The json's own note: "2,172 edges/1,547 pairs in interactions.parquet". Also `papers: 282` vs `papers_mined: 139`, and the ZOVER corpora are not PMC.
   Fix: attribute counts per corpus; drop or correct the `interactions.parquet` parenthetical; say "282 papers processed (139 yielded edges)".

5. **`whitepaper.md:8,239` — "Open Weights"/"adapter checkpoints on Hugging Face" is false.** Severity: **major.**
   > "Training trajectories, evaluation datasets, and model weight adapter checkpoints for `muse-glimmer-30b` are archived publicly on Hugging Face"
   HF API for `alrobles/wildseek-sft` (fetched 2026-11-04): siblings are JSONL splits + `lora_triage_summary.json` — **no weight/checkpoint files**. The adapter lives on Fireworks (`accounts/alrobles/models/muse-starter-sl-wildseek-triage-20261103-215412`); recipe in the `wildseek-lora` companion repo.
   Fix: drop "Open Weights"/"adapter checkpoints"; say trajectories + eval summaries; cite the Fireworks adapter path and `wildseek-lora`.

6. **`whitepaper.md:146` — "validating the platform's forward-looking predictive capacity" overclaims.** Severity: **major.**
   > "subsequent full-text mining runs have already recovered empirical literature edges documenting natural or experimental infection for 4 of these 15 pre-registered species"
   Shipped `app/data.sample/we_called_it.json` (frozen 2026-10-28): all 15 still `awaiting-confirmation`, and the artifact's own note defines confirmation as "a literature edge **published after** predicted_on names the species as host". A mined edge (undated here) is not a confirmation; 4/15 edges ≠ 4/15 validations.
   Fix: "carry mined host edges (per SUBMISSION.md); per the registry's rule, confirmation requires a post-freeze PMID — all 15 remain awaiting-confirmation as of the shipped artifact."

7. **`whitepaper.md:68` — Suitability raster resolution contradicts binding source + pipeline.** Severity: **major.**
   > "producing masked CONUS suitability rasters at 1/100° resolution (~1 km, EPSG:4326 internal projection, reprojection to EPSG:3857 for web tiles)"
   `SUBMISSION.md:29` "at 1/120° (~1 km)"; `docs/plan.md:44` CONUS fine layer 1/120° (~900 m); `pipeline/predict_suit.R:1` "CONUS 1/120-deg". Only `docs/FACTORY.md:48` says 1/100° — repo sources themselves conflict; the whitepaper picked the minority number and contradicts the binding doc.
   Fix: reconcile to the pipeline truth (1/120° for suitability rasters) and align `FACTORY.md`.

8. **`whitepaper.md:68` — `data/fit_catalog.parquet`: wrong filename, unshipped path.** Severity: **minor–major.**
   The artifact is `data/fit_catalog.csv` (101,376 rows) and `data/` is gitignored — absent from the public snapshot; shipped surrogate is `app/data.sample/fit_catalog.csv` (8,888 rows). Same class as README-round issue 13.
   Fix: cite `app/data.sample/fit_catalog.csv` or state the catalog is regenerated by the pipeline.

9. **`whitepaper.md:26` — "82 million commercial poultry culled" escalates the data.** Severity: **minor.**
   `data/aphis_poultry.parquet`: `birds_affected` sums 82,017,090 — APHIS "birds affected" = flock size on confirmed premises, not culled birds.
   Fix: "~82 million birds in APHIS-confirmed affected flocks" (matches README's "82M+ poultry affected").

10. **`whitepaper.md:73,142` — Equation omits the polynomial terms the prose claims.** Severity: **minor.**
    Prose: "second-order polynomial logistic regression"; `eval/susceptibility.json`: `logreg_poly2 [ext]`. Displayed logit is linear in the three distances plus a catch-all ΣβkXk.
    Fix: show the quadratic/interaction terms or describe the model as "logistic regression over extended polynomial features" and point at `pipeline/suscept_model.py`.

11. **`whitepaper.md:152` — Gold-holdout recall omits the 2% leakage disclosure.** Severity: **minor.**
    `eval/litmine.json`: `leakage_2020plus: "1/65 pairs (2%)"`, `heldout_pairs_clean: 64`. Paper says "gold-standard validation corpus" with no caveat.
    Fix: one clause — "(1/65 holdout pairs post-2020; `eval/litmine.json`)".

12. **`whitepaper.md:100,160` — 0.82 semantic rescore is a bespoke post-hoc rubric; residual composition omitted.** Severity: **minor.**
    Token-F1 ≥ 0.70 + ≥80% gold-numeric-literal thresholds were defined by the authors after exact-match failed; `eval/README.md` also records the residual 7 rows (4 empty, 2 truncated, 1 over-extraction). Paper presents 0.82 beside external metrics without flagging it as self-scored.
    Fix: label it "author-defined semantic agreement" and give the residual breakdown.

13. **`whitepaper.md:144` — Headline holdout AUC carries no uncertainty.** Severity: **minor.**
    0.862 is reported ±0.028 but the n=53 headline 0.738 has no CI (a bootstrap CI on 53 species is wide — which is exactly why it must be shown).
    Fix: add a bootstrap CI or state n is too small for a tight interval.

14. **`whitepaper.md:79` — "domestic breeds" invented category.** Severity: **minor.**
    Sources: "2 hybrids, taxa absent from the trees, one ambiguous GBIF entity" (`SUBMISSION.md`). No domestic-breed category exists in the ledger.
    Fix: mirror the source breakdown.

15. **`whitepaper.md:66` — "≥95% of verified presences" ambiguity.** Severity: **minor.**
    "retaining all ecoregions containing ≥95% of verified presences" reads as per-ecoregion; actual semantics = the ecoregion set covering ≥95% of presences (README: "M, 95% of presences").
    Fix: "retaining the ecoregions covering ≥95% of verified presences".

16. **`whitepaper.md:72` — Label provenance blurs the holdout boundary.** Severity: **minor.**
    Positives = "confirmed H5N1 wild hosts identified by USDA APHIS registries **and verified literature records**", while the holdout is "literature-evidenced" hosts. The temporal/provenance cut between label construction and holdout mining is undefined — a methods reviewer will ask whether any holdout species' literature evidence predates label freezing.
    Fix: state the boundary explicitly (which literature-derived positives were in, and the date cut).

17. **`whitepaper.md:122,211` — Small factual drift.** Severity: **minor.**
    "03:15 UTC" — `SUBMISSION.md` says "cron 03:15" with no timezone. "(`FACTORY.md`, `AUDIT.md`)" — actual file is `docs/AUDIT-2026-10-26.md`.
    Fix: drop "UTC" or verify the crontab TZ; correct the filename.

18. **`whitepaper.md:16,68` — Typos/grammar.** Severity: **trivial.**
    "an continuous operational monitor"; "Model selection selected the optimal AIC-winning ellipsoid".
    Fix: "a continuous…", "We selected the AIC-winning ellipsoid per species".

19. **References — missing load-bearing data citations.** Severity: **minor.**
    GBIF, ERA5-Land, USGS WBD, OpenAlex, PMC OA — all used, none cited; `xnicher`/`oneearthr` named in prose with no ref entry. For a paper centered on auditability, cite datasets as first-class artifacts.
    Fix: add data citations (or a Data Availability block).

## 3. Anti-claims (strongest attacks on the paper)

1. **Fabricated citation undermines the paper's core selling point.** WildSeek's
   thesis is "an auditable, self-updating monitor" — yet reference 8 is an
   invented paper grafted onto a real JBI article number, and the Methods
   fabricate the deterministic gate's constants (issue 2). If the reference
   list and the tail thresholds were hallucinated, a reviewer must distrust
   every uncited numeric in the manuscript by the paper's own standard.

2. **The flagship mining numbers are corpus-stitched.** Sentences in Methods
   and Results fuse the ZOVER triage run (23%/74%/$1.93/3,165 chunks) with
   the PMC run (38%/56%/$1.33/772 chunks) and then attribute an aggregate
   4,854 edges — spanning ≥4 corpora per the artifact itself — to a single
   772-chunk run and to a parquet file the same artifact says holds 2,172.
   The cited artifact contradicts the claim in the same sentence that cites
   it.

3. **Headline evidence is statistically thin where it matters most.**
   AUC 0.738 on n=53 with no CI; "100% precision" on n=12 (Wilson lower
   bound ≈ 0.74); pre-registration shows 15/15 `awaiting-confirmation` in
   the shipped artifact while the text claims 4/15 "validations"; and the
   0.82 LoRA "semantic agreement" is an author-defined post-hoc rescore
   applied after exact-match failed (all-task exact match remains 0.20 on
   a holdout with 3/40 near-duplicates of train).

4. **"Open Weights" is not delivered.** The header advertises open weights
   and the reproducibility section claims adapter checkpoints on Hugging
   Face; the dataset repo contains only JSONL trajectories and a summary.
   The actual adapter is a Fireworks account artifact, and the training
   recipe lives in a companion repo the paper never names — the weights
   claim is aspirational, not shipped.

5. **Holdout provenance is potentially circular.** Susceptibility positives
   include "verified literature records" and the holdout is
   "literature-evidenced hosts" — with no stated date/provenance cut between
   the two, "prospective generalization" may partly measure label-recall
   overlap rather than prediction of unobserved hosts.

## 4. Scores

| Criterion | Score | Rationale |
|---|---|---|
| Accuracy | 0.62 | Headline numbers verify, but fabricated gate constants, a fabricated reference, corpus conflation, and the 1/100°/1/120° conflict are all one-grep falsifiable. |
| Clarity | 0.84 | Professional structure and prose; a few typos; equation under-specifies the claimed model. |
| Evidence | 0.60 | eval/ citations are diligent, but one cited artifact contradicts its sentence, `interactions.parquet` is misattributed, HF "checkpoints" don't exist, cited `.parquet` path is wrong/unshipped. |
| Contrast | 0.75 | Honest CV-vs-holdout framing and real before/after deltas; 0.82 self-rescore sits beside external metrics unlabeled. |
| Depth | 0.85 | Genuine methodological substance: M masks, patristic reconciliation, fail-closed design, QA quorum, decay/kernel, Known Limits incl. leakage. |
| Structure | 0.90 | Clean sections, reproducibility block, repo map, references. |

**Mean ≈ 0.76.**

**Overall paper score: 0.70** — real results undermined by fabricated
specifics: one invented citation and invented method constants violate the
paper's own auditability thesis; REWRITE required on Methods §3 /
Results §2,§4 / References before submission.
