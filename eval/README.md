# eval/ — quantitative evidence behind the submission claims

Each file is a baked artifact produced during the event window
(Oct 26 – Nov 4, 2026); repro pointers included.

| File | Claim it backs | Reproduce |
|---|---|---|
| `susceptibility.json` | p(host) logreg ROC-AUC 0.862±0.028, PR 0.539; prospective AUC 0.738 on 53 lit-evidenced held-out hosts | `pipeline/suscept_model.py` + `freeze_predictions.py` over `data/serve` |
| `litmine.json` | 4,854 edges / 3,740 pairs / 282 papers; full-text pair-recall 56% vs 16% abstract-only; judge-verified precision 100% (12/12 audit) | `litmine/` pipeline + `eval_full.py` on the gold set |
| `lora_triage.json` | Glimmer-30B LoRA r8 (Fireworks serverless, $0 promo): hold-out exact-match 0.0 → 0.70 (28-0 paired, p≈7e-9) | `wildseek-lora` companion repo (`fw_convert.py` + Fireworks glimmer starter, run `wildseek-triage-20261103-215412`) |
| `lora_all.json` | Glimmer-30B LoRA r8 (Fireworks serverless, $0 promo): hold-out exact-match 0.00 -> 0.20 (8-0 paired, p=0.0078); tuned field acc: relevant 0.71, hosts 0.57, parasites 0.57, decision 1.00, switch_to 1.00, reason 0.00, confidence 1.00. Semantic rescore (`tools/fw_distill.py rescore`: token-F1 ≥ 0.7 + ≥80% gold numeric literals @1% rtol) — reason 0.00 → 1.00 (24/24 paraphrases, core stats preserved), exact 0.20 → 0.82; residual 7 rows = 4 empty extraction answers, 2 truncated, 1 over-extraction | wildseek-lora repo, run `wildseek-all-20261104-0017` |

Unit/integration coverage lives in `tests/` (71 tests, CI-green);
`docs/eval-model-report.md` narrates the modeling decisions.
SFT trajectories + LoRA summary are also public at
https://huggingface.co/datasets/alrobles/wildseek-sft.
