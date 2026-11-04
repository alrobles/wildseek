# DiDAL PAPER-R1-GAMMA — adjudication (judge: Muse, 2026-11-04)

Alpha: agy Gemini 3.8 Flash (draft + fix). Beta: devin SWE-2 Max
(score 0.70, 19 issues, 1 blocker).

## Verdicts per issue (all verified by direct artifact read)

- I1 ref-8 fabricated: UPHELD. Deleted (F1 verified: no Muñoz/JBI
  in draft). Anti-claim 1 neutralized on this count.
- I2 gate constants invented: UPHELD. Real 15.0/120/0.5 now quoted
  with file:line (F2 verified vs decide_tail.py:44-47).
- I3 triage conflation: UPHELD. PMC 38%/56%/$1.33 separated from
  ZOVER 23%/74%/$1.93 Capa-0/1 (F3 verified vs eval + run log).
- I4 corpus stitching: UPHELD. Four components listed, parquet
  corrected to 2,172/1,547, "282 processed (139 yielded)" (F4).
- I5 Open Weights false: UPHELD. Header → "SFT Trajectories & Eval
  Summaries"; adapter = Fireworks path + wildseek-lora (F5; HF =
  JSONL only per API listing + prior session).
- I6 4/15 validations: UPHELD. Struck; 15/15 awaiting-confirmation
  with the registry rule stated (F6 verified vs we_called_it.json).
- I7 1/100°: UPHELD. → 1/120°; FACTORY.md:48 aligned too (F7/F7b).
- I8–I19: UPHELD, all fixes F8–F19 verified by grep (affected
  flocks, poly2/model_A, 2% leakage clause, author-defined 0.82 +
  residual 4/2/1, n=53 no-tight-CI, SUBMISSION proxy breakdown,
  ≥95% rephrase, label-provenance limitation §6, cron/AUDIT,
  typos, Data Availability block).
- Gamma addition: whitepaper cited excluded-from-public
  `docs/progress-report.md`; added `zover_triage` block to
  `eval/litmine.json` (numbers traced to 2026-10-28 run log) and
  re-pointed the citation. No dangling refs remain in public set.

## Residual risks (disclosed, not blocking)

- p≈7.5e-9 assumes two-sided sign test on 28–0 (correct math,
  post-hoc framing — standard for ablations, labeled as paired).
- F13/F16 resolved by disclosure rather than computation/firewall;
  Known Limits carries both honestly.
- Beta's Wilson-lower-bound point (n=12 → ≈0.74) is not in the
  text; the "12/12 audit (raw 60–73% n=30)" phrasing already bounds
  the claim. Acceptable.

## Score: 0.88 — ACCEPT

All 19 issues closed with artifact-verified fixes; one blocker
eliminated; public-snapshot citations self-contained.
