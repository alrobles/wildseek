#!/usr/bin/env python3
"""Distill a muse-glimmer SFT run's summary.json into eval/ — verified.

The starter writes run artifacts under $FW_COOKBOOK/muse_starter_logs/<run>/:
predictions_base.jsonl / predictions_tuned.jsonl (one row per holdout
prompt: index, gold, exact, fields{...}, truncated), metrics.jsonl
({"step":N} lines + {"eval":...} summaries), and on success summary.json
(base/tuned exact-match, field accuracy, paired McNemar, cost).

eval/lora_*.json is byte-identical to summary.json (see lora_triage), so
install = verify the summary against the raw predictions, copy, and emit
the eval/README.md table row. Any mismatch fails closed — a half-written
summary must not become a submission claim.

Usage:
  tools/fw_distill.py check   <run_dir>
  tools/fw_distill.py install <run_dir> <eval_name>   # eval/<eval_name>.json
  tools/fw_distill.py rescore <run_dir>               # semantic rescore of
                                                      # string-field misses
"""

import json
import re
import sys
from collections import Counter
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOL = 1e-9

# rescore thresholds — a string field missed by exact equality still counts
# when it is a faithful paraphrase: bag-of-words F1 >= SEM_F1 AND >= SEM_NUM
# of the gold's numeric literals present in the answer (rel tol NUM_RTOL,
# absorbs gold "1713.9" vs answer "1713"). The wildseek-all misses split
# cleanly: paraphrases 0.74-0.94 F1, real errors <= 0.40 or empty.
SEM_F1 = 0.7
SEM_NUM = 0.8
NUM_RTOL = 0.01


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def mcnemar_p(only_a: int, only_b: int) -> float:
    """Exact two-sided McNemar: discordant pairs ~ Binomial(n, 0.5)."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    k = min(only_a, only_b)
    return min(1.0, 2.0 * sum(comb(n, i) for i in range(k + 1)) / 2**n)


def recompute(preds: list[dict]) -> dict:
    # _score keys each row's fields by gold keys, so a field's denominator
    # is the rows whose gold carried it — not all rows (variable-schema
    # holdouts like the "all" orchestrator set depend on this).
    seen: dict[str, int] = {}
    hits: dict[str, int] = {}
    for p in preds:
        for k, v in p["fields"].items():
            seen[k] = seen.get(k, 0) + 1
            hits[k] = hits.get(k, 0) + int(bool(v))
    n = len(preds)
    return {
        "exact_match": sum(p["exact"] for p in preds) / n,
        "unterminated": sum(p["truncated"] for p in preds),
        "field_accuracy": {k: hits[k] / seen[k] for k in seen},
    }


def check(run: Path) -> list[str]:
    """Return list of mismatch strings; empty = summary verified."""
    sp = run / "summary.json"
    if not sp.exists():
        return ["summary.json absent — run still in flight "
                "(or launcher died before tuned eval)"]
    summ = json.loads(sp.read_text())
    base = _jsonl(run / "predictions_base.jsonl")
    tuned = _jsonl(run / "predictions_tuned.jsonl")
    errs: list[str] = []

    holdout = run / "holdout.jsonl"
    if holdout.exists():
        n = sum(1 for x in holdout.read_text().splitlines() if x.strip())
        if len(base) != n or len(tuned) != n:
            errs.append(f"holdout {n} rows vs base {len(base)} tuned {len(tuned)}")

    for label, preds in (("base", base), ("tuned", tuned)):
        got = recompute(preds)
        want = summ[label]
        for key in ("exact_match", "unterminated"):
            if abs(got[key] - want[key]) > TOL:
                errs.append(f"{label}.{key}: summary {want[key]} != recomputed {got[key]}")
        if set(got["field_accuracy"]) != set(want["field_accuracy"]):
            errs.append(f"{label}.field_accuracy keys: {sorted(want['field_accuracy'])} "
                        f"!= {sorted(got['field_accuracy'])}")
        for k, v in got["field_accuracy"].items():
            if abs(v - want["field_accuracy"].get(k, -1)) > TOL:
                errs.append(f"{label}.field_accuracy.{k}: summary "
                            f"{want['field_accuracy'].get(k)} != recomputed {v}")

    b = [p["exact"] for p in base]
    t = [p["exact"] for p in tuned]
    only_t = sum(1 for x, y in zip(b, t) if not x and y)
    only_b = sum(1 for x, y in zip(b, t) if x and not y)
    p_val = mcnemar_p(only_b, only_t)
    paired = summ["paired"]
    if paired["only_tuned_correct"] != only_t or paired["only_base_correct"] != only_b:
        errs.append(f"paired: summary {paired} != recomputed ({only_b}, {only_t})")
    if abs(paired["p_value"] - p_val) > max(TOL, 1e-6 * p_val):
        errs.append(f"paired.p_value: summary {paired['p_value']} != recomputed {p_val}")
    if abs(summ["exact_match_delta"] - (summ["tuned"]["exact_match"]
                                      - summ["base"]["exact_match"])) > TOL:
        errs.append("exact_match_delta != tuned-base")

    metrics = run / "metrics.jsonl"
    if metrics.exists():
        steps = sum(1 for x in metrics.read_text().splitlines() if '"step"' in x)
        if summ["steps"] != steps:
            errs.append(f"steps: summary {summ['steps']} != {steps} step lines")
    return errs


def _tok_f1(gold: str, ans: str) -> float:
    g = Counter(re.findall(r"[a-z0-9]+", gold.lower()))
    a = Counter(re.findall(r"[a-z0-9]+", ans.lower()))
    if not g and not a:
        return 1.0
    ov = sum((g & a).values())
    return 2 * ov / (sum(g.values()) + sum(a.values()))


def _num_cov(gold: str, ans: str) -> float:
    """Fraction of gold numeric literals found in ans within NUM_RTOL."""
    gv: list[float] = []
    for x in re.findall(r"-?\d+\.?\d*", gold):
        try:
            gv.append(float(x))
        except ValueError:
            pass
    if not gv:
        return 1.0
    av = [float(x) for x in re.findall(r"-?\d+\.?\d*", ans)
          if re.fullmatch(r"-?\d+\.?\d*", x)]
    hit = sum(any(abs(v - g) <= NUM_RTOL * max(1.0, abs(g)) for v in av)
              for g in gv)
    return hit / len(gv)


def _loads(s: str) -> dict | None:
    try:
        d = json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return None
    return d if isinstance(d, dict) else None


def rescore(preds: list[dict]) -> dict:
    """Re-judge failed string fields as paraphrase vs error.

    A missed field counts semantically when it is a string on both sides,
    _tok_f1 >= SEM_F1 and _num_cov >= SEM_NUM. Unparseable gold/answer and
    truncated rows fail closed. Returns strict + semantic field accuracy
    and row-level exact-match under both judges.
    """
    seen: dict[str, int] = {}
    strict: dict[str, int] = {}
    sem: dict[str, int] = {}
    row_strict = row_sem = 0
    detail: list[dict] = []
    for p in preds:
        gold = _loads(p["gold"])
        ans = _loads(p["answer_text"])
        ok_sem = not p["truncated"] and gold is not None
        for k, hit in p["fields"].items():
            seen[k] = seen.get(k, 0) + 1
            strict[k] = strict.get(k, 0) + int(bool(hit))
            pass_sem = bool(hit)
            if not hit and gold is not None and ans is not None:
                g, a = gold.get(k), ans.get(k)
                if isinstance(g, str) and isinstance(a, str):
                    f1, nc = _tok_f1(g, a), _num_cov(g, a)
                    pass_sem = f1 >= SEM_F1 and nc >= SEM_NUM
                    detail.append({"index": p["index"], "field": k,
                                   "f1": round(f1, 3), "num_cov": round(nc, 3),
                                   "semantic": pass_sem})
            sem[k] = sem.get(k, 0) + int(pass_sem)
            ok_sem &= pass_sem
        row_strict += int(bool(p["exact"]))
        # fail closed: exact=False with no scored fields means the mismatch
        # was structural (key set/JSON shape), not a field paraphrase
        row_sem += int(ok_sem and (p["exact"] or bool(p["fields"])))
    n = len(preds)
    return {
        "n": n,
        "exact_match": row_strict / n,
        "exact_match_semantic": row_sem / n,
        "field_accuracy": {k: strict[k] / seen[k] for k in seen},
        "field_accuracy_semantic": {k: sem[k] / seen[k] for k in seen},
        "rescued": sorted({d["index"] for d in detail if d["semantic"]}),
        "detail": detail,
    }


def cmd_rescore(run: Path) -> int:
    tuned = _jsonl(run / "predictions_tuned.jsonl")
    r = rescore(tuned)
    print(f"{run.name}: rows {r['n']}  exact {r['exact_match']:.2f} -> "
          f"semantic {r['exact_match_semantic']:.2f} "
          f"(rescued rows {r['rescued']})")
    for k, v in r["field_accuracy_semantic"].items():
        print(f"  {k:10s} strict {r['field_accuracy'][k]:.2f}  semantic {v:.2f}")
    for d in r["detail"]:
        print(f"  idx {d['index']:>3} {d['field']:10s} f1={d['f1']:.2f} "
              f"num_cov={d['num_cov']:.2f} {'PARAPHRASE' if d['semantic'] else 'ERROR'}")
    return 0


def readme_row(summ: dict, name: str) -> str:
    b, t = summ["base"], summ["tuned"]
    pair = summ["paired"]
    fields = ", ".join(f"{k} {v:.2f}" for k, v in t["field_accuracy"].items())
    return (f"| `{name}.json` | Glimmer-30B LoRA r8 (Fireworks serverless, $0 promo): "
            f"hold-out exact-match {b['exact_match']:.2f} -> {t['exact_match']:.2f} "
            f"({pair['only_tuned_correct']}-{pair['only_base_correct']} paired, "
            f"p={pair['p_value']:.2g}); tuned field acc: {fields} | "
            f"wildseek-lora repo, run `{summ['log'].split('/')[-1]}` |")


def cmd_check(run: Path) -> int:
    errs = check(run)
    for e in errs:
        print("MISMATCH:", e)
    print(f"{run.name}: {'OK' if not errs else f'{len(errs)} mismatches'}")
    return 1 if errs else 0


def cmd_install(run: Path, name: str) -> int:
    errs = check(run)
    if errs:
        for e in errs:
            print("MISMATCH:", e)
        return 1
    summ = json.loads((run / "summary.json").read_text())
    out = ROOT / "eval" / f"{name}.json"
    out.write_text(json.dumps(summ, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    print(readme_row(summ, name))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("check", "install", "rescore"):
        sys.exit(__doc__)
    if sys.argv[1] == "rescore":
        sys.exit(cmd_rescore(Path(sys.argv[2])))
    sys.exit(cmd_check(Path(sys.argv[2])) if sys.argv[1] == "check"
             else cmd_install(Path(sys.argv[2]), sys.argv[3]))
