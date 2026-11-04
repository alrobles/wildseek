# DiDAL R1-BETA — cold-judge critique of README.md

Reviewer: BETA (SWE-2 Max) · 2026-11-04
Artifact under review: `README.md` (163 lines), cross-checked against
`SUBMISSION.md`, `NEW.md`, `eval/*.json`, `data/`, `app/data.sample/`,
`serve/docker-compose.yml`, `pipeline/`, `api/main.py`, and live probes of
`https://wildseek.ecoseek.org` (`/`, `/health`, `/metrics`, `/briefing`,
`/risk/watershed`, `/explain/{kind}/{ident}`, `/decisions`, `/litmine`,
`/we-called-it`, `/openapi.json` — all 200; `/risk/county` does not exist).

## 1. Verdict per DiDAL criterion (0.0–1.0)

| Criterion | Score | Rationale |
|---|---|---|
| Accuracy | 0.62 | Most headline numbers verify against shipped artifacts, but a stale detection count (9,139 vs actual 9,479), a fit-count product that doesn't multiply, a false "refits executed" claim, a wrong quickstart port, and a "top-100 slice of every layer" claim contradicted by the bundle itself. |
| Clarity | 0.80 | Tight, scannable, judge-oriented prose; the "Benchmark / Baseline" column mislabels the prospective number and mixes baselines with scale stats. |
| Evidence | 0.55 | `eval/*.json` are real and mostly back the claims, but every in-repo citation is a `file:///<home>/...` URI dead to any external reader; `litmine.json` is internally inconsistent (cost/edge, papers, interactions.parquet note); LoRA section cherry-picks the strong task and omits the holdout-leakage caveat sitting in the same directory. |
| Contrast | 0.70 | Real before/after contrasts exist (16→56% recall, 0.0→0.70 exact match, CV vs holdout AUC), but the table inverts emphasis — the honest prospective number is filed under "Baseline" while the leakage-prone CV number is the "Measured Value". |
| Depth | 0.80 | Genuine pipeline depth (M-masked niche campaign, three-distance susceptibility, nightly factory with QA quorum + cost veto, LoRA SFT, judge-verified mining). README omits SUBMISSION's "Known limits" entirely, which undercuts reviewer trust once found. |
| Structure | 0.85 | Clean sectioning: summary → evidence table → architecture → quickstart → factory → repo map. Evidence table is a strong idea executed with broken links. |

**Mean: 0.72 → ACCEPT** (barely clears 0.7; the numbers are real, the
packaging is what a judge trips on).

## 2. Issues

1. **`README.md:9,34,40,44–50,109` — every in-repo citation is a
   `file:///<home>/GitHub/wildseek-devel/...` URI.**
   Severity: **blocker.** Dead for every reader except the author's own
   machine; rendered on GitHub they are unclickable, and they point at the
   `-devel` repo while the README claims to be `alrobles/wildseek`. The
   sentence "All figures are strictly verifiable against eval/…" is followed
   by links no judge can open.
   Fix: repo-relative links — `[NEW.md](NEW.md)`,
   `[eval/lora_triage.json](eval/lora_triage.json)`,
   `[eval/](eval/)`, `[`pipeline/`](pipeline/)`,
   `[pipeline/nightly.py](pipeline/nightly.py)`,
   `[docs/FACTORY.md](docs/FACTORY.md)`.

2. **`README.md:28,49` — "9,139 APHIS HPAI wild-bird detections" is stale.**
   Severity: **major.** `data/fetch_aphis.log` reports `hpai: 9479`;
   `data/serve/detections.geojson` ships 9,479 features;
   `data/serve/meta.json` has `n_detections: 9479`; `docs/AUDIT-2026-10-26.md`
   says "9,479 HPAI points". `SUBMISSION.md` carries the same stale figure.
   Fix: `9,479 APHIS HPAI wild-bird detections` (both occurrences).

3. **`README.md:32` — "alternate variable recommendations executed by
   downstream refit tools" is false.** Severity: **major.** In
   `data/serve/decisions_delta.csv` (= `app/data.sample/decisions_delta.csv`)
   all 49 `flag_review` rows have `switch_to='none'` and empty `aic_new`;
   `decisions_all.jsonl` shows `switch_to='none'` for all 589 rows. Zero
   alternate-variable recommendations exist and zero refits ran; the 49 is
   real but it is *flags with reasons*, not executed interventions.
   Fix: `…issued 49 substantive flag_review interventions with reasons
   (sparse endemics, marine mammals on implausible pairs, small-n unstable
   ellipsoids) — written to decisions_delta.csv; switch_to refits are
   executable via pipeline/refit_switched.R` — or drop the clause.

4. **`README.md:47,64` — "88 bioclim pairs × 1,148 pools" does not produce
   101,376.** Severity: **major.** 88 × 1,148 = 101,024. The catalog has
   1,147 distinct `specieskey` values × 88 pairs = 100,936, plus 440 refit
   rows (5 species re-run at 176 rows each) = 101,376. The "1,148" comes from
   `species_winner.csv` row count, which double-counts specieskey `2439560`
   (1,148 rows / 1,147 distinct keys). A judge can multiply.
   Fix: `88 bio-var pairs × 1,147 species (+440 refit rows) = 101,376 fits`.

5. **`README.md:103` — wrong port.** Severity: **major.** Quickstart says
   `http://localhost:8080`; `serve/docker-compose.yml` maps
   `127.0.0.1:8654:8654` (its own header comment says
   `http://localhost:8654`). A judge running the 60-second path verbatim hits
   nothing. Fix: `Open http://localhost:8654`.

6. **`README.md:90` — "top-100 slice of every layer" is contradicted by the
   bundle.** Severity: **major.** `app/data.sample/NO_SUIT_PNGS.txt`:
   "suit_*.png … too large for the demo seed … map layer will be empty";
   sample detections = 2,000 features, fit_catalog = 8,888 rows, county
   exposure = full 3,109. Neither "top-100" nor "every layer".
   Fix: `ships a reduced slice of the tabular/vector layers (per-species
   suitability rasters excluded — they render empty locally); boots the
   monitor without cluster rasters`.

7. **`README.md:30,44,76` — the 0.862 CV AUC is the inflated number; the
   table files the honest one as "Baseline".** Severity: **major (methods).**
   Labels are APHIS-confirmed hosts and features include geographic distance
   to confirmed hosts; random 5-fold CV does not control spatial
   autocorrelation/label-leakage, so 0.862 overstates skill. The 0.74 on 53
   held-out literature-evidenced hosts is the defensible headline, yet it
   sits in the "Benchmark / Baseline" column.
   Fix: swap columns — Measured = `AUC 0.74 on 53 held-out lit-evidenced
   hosts`; Benchmark = `ROC-AUC 0.862 (random-fold CV; spatially
   auto-correlated labels)`.

8. **`README.md:30,44,76` — "prospective" overclaims.** Severity: **major.**
   The 0.74/53 figure is a literature-label holdout. The genuinely
   prospective artifact is the 15 frozen predictions
   (`we_called_it.json`, frozen 2026-10-28) — live endpoint shows all 15
   still `awaiting-confirmation`; zero have confirmed yet.
   Fix: `held-out literature-evidenced hosts (AUC 0.74, n=53); 15
   pre-registered predictions frozen 2026-10-28, confirmations pending`.

9. **`README.md:34,50` — LoRA claim cherry-picks the triage task.**
   Severity: **major.** Same directory's `eval/lora_all.json` shows the
   all-task run at exact-match 0.0 → 0.20 (8-0 paired, p=0.0078), and
   `eval/README.md` discloses that the starter holdout "was carved from the
   train pool (3/40 rows near-dup of train, J≥0.73)". A judge opening `eval/`
   reads the caveat the README dropped.
   Fix: add `…(triage task; the broader all-task run reached 0.20 exact /
   0.82 after semantic rescore — see eval/lora_all.json and eval/README for
   the holdout-leakage caveat)`.

10. **`README.md:33,46` — "$0.0014/edge" does not reconcile with the cited
    artifact.** Severity: **minor.** `litmine.json` logs `cost_usd: 1.33`
    over `edges: 4854` → $2.7e-4/edge; the 0.0014 unit cost comes from the
    Capa-2 stage on a different corpus.
    Fix: `Capa-2 extraction at $0.0014/edge ($1.33 logged on the audited
    corpus)` or reconcile the artifact.

11. **`README.md:33,46` — "4,854 edges" headline counts unjudged output.**
    Severity: **minor.** Artifact: `verified_edges: 2351` (48%),
    `judge_edge_retention: 0.55`, and its own note says "2,172 edges/1,547
    pairs in interactions.parquet"; `papers: 282` vs `papers_mined: 139`.
    Fix: `4,854 extracted edges (2,351 judge-verified) / 3,740 unique pairs
    / 282 papers`.

12. **`README.md:33` — "100% judge-verified precision" hides n=12.**
    Severity: **minor.** Artifact note: 100% (12/12) on human audit; raw
    audit 70% (60% strict-span), audit n=30.
    Fix: `100% on a 12-edge human audit (raw 60–73%)`.

13. **`README.md:48` — cited path `data/decisions_delta.csv` does not exist
    in the repo.** Severity: **minor.** `data/` is entirely untracked
    (`git ls-files data/` = 0); the committed copy is
    `app/data.sample/decisions_delta.csv`. Fix: cite that path.

14. **`README.md:49` — `[`app/data/`]` is gitignored** (`.gitignore:8`) —
    nothing exists at that path in the published repo; only `app/data.sample`
    ships. Severity: **minor.** Fix: point at `app/data.sample/`.

15. **`README.md:93` — "3.6 MB" is wrong.** Severity: **minor.** The sample
    bundle is 5,160,266 bytes (~5.0 MiB). Fix: `≈5 MB`.

16. **`README.md:17,83` — "keyless, baked artifacts" / "baked agent outputs"
    is only partially true live.** Severity: **minor.**
    `GET /explain/species/2432314` on production returns `brief: null` +
    `"note":"MODEL_API_KEY unset"` even though the repo ships
    `app/data.sample/explain_species_2432314.json` with a full baked brief —
    the deploy data dir is missing the baked explain files.
    Fix: rsync `explain_*.json` into the production data dir, or scope the
    claim to the seeded IDs.

17. **Live `/briefing` serves `"headline":"WildScan brief"`** — stale product
    name on the endpoint the README advertises. Severity: **minor.**
    Fix: regenerate `briefing.json` with the WildSeek headline.

18. **`README.md:5` — "Indie Developer · Push the Frontier" presents two
    tracks.** Severity: **minor.** `docs/hackathon-rules.md` says one track
    is chosen at submission and records Indie (no legal entity). Fix: keep
    one track label; frame Push-the-Frontier as bonus positioning only if
    accurate.

19. **`README.md:29,49` — "2,247 HUC8 watersheds" is not verifiable from the
    repo.** Severity: **minor.** `risk_watershed.parquet` is not shipped
    (lives in the gitignored deploy dir); `/risk/watershed` caps at
    `top≤1000` per call. The audit doc asserts 2,247. Fix: ship the parquet
    or a top-N CSV under `app/data.sample/`, or cite the audit line.

20. **`README.md:42–50` — the "Benchmark / Baseline" column mixes real
    baselines with scale stats** ("9,139 wild detections", "82M+ poultry",
    "Executable switch_to AIC refits" — none of which are baselines, and one
    is stale + one describes non-existent verdicts). Severity: **minor.**
    Fix: rename column to `Context / comparator` and de-stale its contents.

21. **Artifact hygiene: `data/serve/meta.json` vs `app/data.sample/meta.json`
    disagree** (`n_detections` 9479 vs `null`; `n_species` `null` vs `1148`
    vs susceptibility's 1,147). Feeds the 1,147/1,148 confusion behind
    issue 4. Severity: **minor.** Fix: regenerate both from one export run.

22. **Cross-doc consistency:** `SUBMISSION.md:43` claims "1,147 catalog
    decisions" but the shipped `decisions_all.jsonl` has 589 rows (in-map
    subset). README doesn't repeat the number, but judges cross-reading the
    two files will trip. Severity: **minor.** Fix: add one clause explaining
    the subset.

23. **README has no limitations section** — `SUBMISSION.md` "Known limits"
    (presence-only likelihood, 179 taxonomic-proxy species, ~13% aves cells
    on water pixels dropped, climate-only suitability) is exactly what a
    methods reviewer looks for and its absence reads as concealment once
    discovered. Severity: **minor.** Fix: port 3–4 bullets.

## 3. Top-3 must-fix for Alpha's reply round

1. **Repair the verification path end-to-end.** Replace all
   `file:///<home>/...` URIs with repo-relative links (issue 1),
   correct `localhost:8080` → `localhost:8654` (issue 5), and point the
   decisions citation at `app/data.sample/decisions_delta.csv` (issue 13).
   This is the difference between "strictly verifiable" and "unverifiable".

2. **Fix every number a judge can recompute or contradict in one click.**
   9,139 → 9,479 (issue 2); "88 pairs × 1,148 pools" → "1,147 species × 88
   pairs + 440 refit rows = 101,376" (issue 4); delete "alternate variable
   recommendations executed" — all 49 `switch_to` are `'none'`, zero refits
   ran (issue 3); "top-100 slice of every layer" → note suitability PNGs are
   excluded (issue 6).

3. **Re-frame the evidence honestly before a methods reviewer does it for
   you.** Headline the 0.74 held-out AUC and demote 0.862 to a CV caveat
   (distance-to-confirmed-host features under random folds — issue 7);
   rename "prospective" → "held-out literature-evidenced" and show the
   15 frozen predictions as pending (issue 8); disclose that LoRA 0.70 is
   the triage task and that the all-task run + holdout-leakage caveat live
   in `eval/` (issue 9); qualify the 100%-precision claim with n=12 and the
   2,351/4,854 verified-edge count (issues 11–12).
