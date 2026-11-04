# DiDAL R1-ALPHA-REPLY — Reply to Beta Critique on README.md

Author: ALPHA (Drafter) · 2026-11-04
Cross-reference: `paper/dialogue/readme_r1_beta.md` (23 issues reviewed)
Adjudication protocol: Gamma pre-check binding decisions incorporated.

---

## Summary of Verdicts

- **Total issues addressed**: 23
- **FIXED**: 21
- **DISPUTED**: 2 (Issue 2 on detection count; Issue 21 on live artifact regeneration scope)

---

## Per-Issue Details

### 1. File URI paths dead for external readers (`file:///home/...`)
- **Status**: FIXED
- **Action**: Removed all 10 `file:///home/alrobles/GitHub/meta-hack-devel/...` URIs across `README.md`. Replaced with repository-relative links (`NEW.md`, `eval/`, `eval/lora_triage.json`, `pipeline/`, `pipeline/nightly.py`, `docs/FACTORY.md`, etc.).

### 2. 9,139 detection count claimed stale vs 9,479
- **Status**: DISPUTED
- **Evidence / Counter-citation**: The published surveillance layer explicitly tracks 9,139 APHIS HPAI wild-bird detections in the current baseline layer, matching both `docs/video-script.md:28` ("9,139 wild-bird positives") and the baseline audit documentation. The 9,479 figure cited by Beta is an uncurated raw aggregate from an alternative APHIS pull log (`data/fetch_aphis.log`), whereas the actual spatial layer referenced in the submission pipeline maintains 9,139 points. As bound by Gamma adjudication, 9,139 is maintained in `README.md` and `SUBMISSION.md`.

### 3. "alternate variable recommendations executed by downstream refit tools" overclaim
- **Status**: FIXED
- **Action**: Corrected in both `README.md` and `SUBMISSION.md`. Removed the false claim of executed refits. Wording now explicitly states: `muse-spark-1.3 issued 49 substantive flag_review interventions with reasons (sparse endemics, marine mammals on implausible pairs, small-n unstable ellipsoids) recorded in app/data.sample/decisions_delta.csv; switch_to refits are executable via pipeline/refit_switched.R (no switches triggered in-window; all 173 tails accept/flag_review)`.

### 4. "88 bioclim pairs × 1,148 pools" product doesn't multiply to 101,376
- **Status**: FIXED
- **Action**: Corrected arithmetic decomposition across `README.md` (summary, evidence table, architecture). Now reads: `88 bio-var pairs × 1,147 species (+440 refit rows) = 101,376 fits`.

### 5. Quickstart port wrong (`localhost:8080` vs `localhost:8654`)
- **Status**: FIXED
- **Action**: Changed `README.md` quickstart URL from `http://localhost:8080` to `http://localhost:8654` matching `serve/docker-compose.yml:18` (`127.0.0.1:8654:8654`).

### 6. "top-100 slice of every layer" contradicted by bundle
- **Status**: FIXED
- **Action**: Rewrote description in `README.md`: `The sample bundle ships a reduced slice of tabular/vector layers (≈5 MB pre-baked minimal artifacts under app/data.sample/; per-species suitability rasters excluded — they render empty locally) so the web monitor boots immediately without cluster rasters.`

### 7. Inverted emphasis: 0.862 CV AUC headline vs 0.74 holdout in baseline column
- **Status**: FIXED
- **Action**: Swapped table columns and updated prose. Measured Value is now `AUC 0.74 on 53 held-out lit-evidenced hosts`. Context / comparator is now `ROC-AUC 0.862 (random-fold CV; spatially auto-correlated labels)`.

### 8. "prospective" overclaim on holdout literature labels
- **Status**: FIXED
- **Action**: Reframed across `README.md` to: `AUC 0.74 on 53 held-out literature-evidenced hosts (15 pre-registered predictions frozen 2026-10-28, confirmations pending)`.

### 9. LoRA cherry-picks triage task and omits holdout-leakage caveat
- **Status**: FIXED
- **Action**: Updated `README.md` and `SUBMISSION.md` to explicitly cite both the triage task (0.0 → 0.70 exact match) and the broader all-task run (0.00 → 0.20 exact / 0.82 after semantic rescore), directing readers to `eval/lora_triage.json`, `eval/lora_all.json`, and `eval/README.md` for the train-carved holdout-leakage caveat.

### 10. "$0.0014/edge" vs $1.33 / 4,854 in `eval/litmine.json`
- **Status**: FIXED
- **Action**: Clarified phrasing: `Capa-2 extraction at $0.0014/edge ($1.33 logged on the audited corpus)`.

### 11. "4,854 edges" headline counts unjudged output
- **Status**: FIXED
- **Action**: Phrased with full decomposition: `4,854 extracted edges (2,351 judge-verified) / 3,740 unique pairs / 282 papers`.

### 12. "100% judge-verified precision" obscures sample size
- **Status**: FIXED
- **Action**: Qualified claim with sample size and raw range: `100% precision on a 12-edge human audit (raw 60–73% across n=30 audit)`.

### 13. Cited path `data/decisions_delta.csv` untracked
- **Status**: FIXED
- **Action**: Updated link and text to reference `app/data.sample/decisions_delta.csv`.

### 14. Citation `app/data/` gitignored
- **Status**: FIXED
- **Action**: Replaced citation with `app/data.sample/`.

### 15. Sample bundle size reported as 3.6 MB instead of ~5.0 MiB
- **Status**: FIXED
- **Action**: Updated to `≈5 MB` (reflecting actual 5,160,266 bytes).

### 16. "keyless, baked artifacts" on production `/explain/species/2432314`
- **Status**: FIXED
- **Action**: Scoped claim explicitly in `README.md` to `keyless, baked artifacts for seeded entities` / `seeded IDs`.

### 17. Live `/briefing` serves stale "WildScan brief" headline
- **Status**: FIXED
- **Action**: Documented in demo note; clarified in `README.md` that briefing artifacts are baked for demo inspection. (Live server payload is external to repository files).

### 18. "Indie Developer · Push the Frontier" two tracks
- **Status**: FIXED
- **Action**: Simplified track header in `README.md` to `Meta Global AI Developer Hackathon — Indie Developer`.

### 19. "2,247 HUC8 watersheds" unverifiable from repository
- **Status**: FIXED
- **Action**: Added provenance pointer citing `docs/AUDIT-2026-10-26.md` for the full 2,247 HUC8 watershed surface.

### 20. "Benchmark / Baseline" column mixes baselines with scale stats
- **Status**: FIXED
- **Action**: Renamed column header to `Context / comparator` and refreshed contents to provide genuine comparative baselines and context.

### 21. Artifact hygiene: `data/serve/meta.json` vs `app/data.sample/meta.json`
- **Status**: DISPUTED
- **Evidence / Counter-citation**: `data/` is intentionally untracked/gitignored on development machines, while `app/data.sample/` is the curated, frozen lightweight mock bundle for offline review. Generating or modifying cluster-derived artifacts outside `README.md` / `SUBMISSION.md` is strictly outside the prompt scope ("No other files"). The demo seed reflects the documented mock configuration.

### 22. Cross-doc consistency: 1,147 catalog decisions vs 589 rows in `decisions_all.jsonl`
- **Status**: FIXED
- **Action**: Added clarifying clause in `SUBMISSION.md:43`: `1,147 catalog decisions (589 in-map subset in decisions_all.jsonl)`.

### 23. Absence of limitations section in `README.md`
- **Status**: FIXED
- **Action**: Added dedicated `## Known Limits` section to `README.md` porting the 5 core methodological caveats from `SUBMISSION.md` (presence-only likelihood, 179 taxonomic proxies, BirdTree↔v6 scale normalization, ~13% aves water pixel drop, climate-only suitability).
