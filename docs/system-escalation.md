# System-1 -> System-2 escalation plan (internal)

Goal: the fit-quality loop becomes agentic — spark triages every
species, wonder diagnoses the exceptions, actions land back in the
compute queue. Prototype status and the build order.

## What exists today

| Piece | Status |
|---|---|
| rule-based decide_tail (thresholds -> accept/flag/drop) | live — the baseline the model replaces/augments |
| fit_audit evidence export (mu/Sigma/starts/AIC landscape/M) | live — 59-sp pilot; full-winner export is a domain_build stage |
| meta_client model tiers (spark-1.2/1.3, wonder-1.0, glimmer local) | live — usage+cost accounting built in |
| explain.py typed-output pattern (JSON schema -> verdict) | live — the contract System-1 uses |
| planner.py (compute tiers + cpu-h budget gate) | live — emits run_spec.json |

## What the prototype still needs (build order)

1. **Verdict schema** — the typed contract spark fills per species:
   `{verdict: accept|refit|drop|switch, confidence: 0-1,
   action: {kind: none|more_starts|pair_switch|reconcile|review},
   reason: short str}` — same pattern as explain.py responses.
2. **`agent/fit_judge.py`** — System-1 classifier. Input: audit
   metrics per species (rel_gap, ll_spread, frac inside-95, deltaAIC
   landscape summary, n_occ, taxonomic-ambiguity flag from reconcile).
   Output: the schema above. Backends, in order:
   `MetaClient.fireworks()` (muse-spark-open — the spark model served
   on the $100 credit; it's a reasoning model so give the judge
   generous max_tokens) -> glimmer self-hosted (free) ->
   spark-1.2-contributor (paid API) as last resort.
3. **Calibration set** — ~150 species hand-verdicted (extend the 59
   pilot) -> `data/audit_labels.csv` (specieskey, human_verdict).
   Required before trusting spark's verdicts; also the benchmark for
   evaluating whether spark beats the rule baseline.
4. **Escalation policy v1** (`agent/escalate.py`) — spark -> wonder
   when any of:
   - spark confidence < 0.6
   - contradictory signals (converged + flat deltaAIC landscape;
     high p_host + bad fit; synonym flagged as lump/split)
   - species new to the pool (no prior verdict history)
   - budget cap: max ~5% of species per night, cost cap via
     meta_client usage accounting — overflow stays flagged for
     human review rather than auto-escalating.
   Wonder's output is a **diagnosis + recommended action**, not a
   verdict — it writes to the refit/audit queue and explains itself
   (that explanation is demo-worthy material).
5. **Feedback log** — `data/agent_calls.jsonl`: every call logs
   {species, tier, prompt_features_hash, model, verdict, cost,
   did_action_change_outcome}. After N nights: agreement rate
   spark-vs-rules, escalation yield (how often wonder's action
   actually changed the decision), cost/verdict. This is where the
   system-1/2 split becomes *measurable* and the thresholds learn.
6. **Closure** — nightly chain becomes: export audit -> spark triage
   -> wonder on exceptions -> decide_tail consumes verdicts ->
   planner emits next compute spec -> sbatch. The OODA loop shut.

## Sequencing with the na_ca build

- na_ca pool job running -> derive pool_all -> domain_build.sh na_ca
- audit stage already in the chain -> full-winner evidence exists
  before fit_judge is written (evidence first, judge second)
- spark fit_judge ships behind `WILDSEEK_JUDGE=1` flag — rules stay
  the default until calibration shows it beats them.

## Non-goals for now

- GPU xnicher (CPU array + tiered starts wins on cost/benefit)
- replacing suscept_model with an LLM (tabular regression stays hgbt)
- vector-borne layer — after the escalation loop is live on HPAI
