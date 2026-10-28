"""Internal eval tracker — sofisticado pero honesto.

Scores the project against the hackathon rubric from checkable gates,
estimates P(top-5 Indie | pass) by Monte Carlo, and persists history so
progress is a curve, not a feeling.

Usage (from repo root, with .venv):
  .venv/bin/python tools/eval_tracker.py score            # current card + P(win)
  .venv/bin/python tools/eval_tracker.py set <id> <0|0.5|1>  # update a gate
  .venv/bin/python tools/eval_tracker.py history         # trend table

State lives in tools/eval_state.json (devel-only; add to release.exclude).
Bucket means feed the Monte Carlo directly: score 8.0 in Impact means
judges score Impact ~ N(8.0, 0.6). Field scenarios are explicit unknowns.
"""

import json
import math
import os
import random
import sys
from datetime import datetime, timezone

STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "eval_state.json")

# id: (bucket, max_points, description)
CHECKS = {
    # --- survival: Stage-1 pass/fail multipliers (each miss x0.7) ---
    "S1_coldopen_pub": ("surv", 0, "cold-open declaration in PUBLIC video-script"),
    "S2_litmine_pub": ("surv", 0, "litmine/ visible in public snapshot"),
    "S3_models_grep": ("surv", 0, "all 5 Muse strings greppable in public clone"),
    "S4_disclaimer": ("surv", 0, "not-medical disclaimer UI+README+SUBMISSION+video"),
    "S5_provenance": ("surv", 0, "provenance claims verifiably true"),
    "S6_live": ("surv", 0, "live opens <3s keyless + /health 200"),
    # --- impact (30), weights sum to 10 ---
    "I1_called": ("impact", 3.0, "we-called-it card frozen w/ date"),
    "I2_confirm": ("impact", 2.0, ">=1 frozen prediction confirmed by later PMID"),
    "I3_agro": ("impact", 2.0, "poultry+dairy exposure separated, non-medical framing"),
    "I4_eggs": ("impact", 1.5, "egg-price / supply-chain narrative in demo"),
    "I5_benef": ("impact", 1.5, "beneficiary stated (agencies/producers, not patients)"),
    # --- tooling (25) ---
    "T1_cascade": ("tooling", 3.0, "4-model strip visible w/ calls+USD"),
    "T2_switch": ("tooling", 2.0, "switch_to executable shown (delta table)"),
    "T3_wonder": ("tooling", 1.5, "wonder briefing live/baked"),
    "T4_glimmer": ("tooling", 2.0, "glimmer self-hosted evidence ($10k bonus)"),
    "T5_ledger": ("tooling", 1.5, "persistent cost ledger (agent_calls.jsonl)"),
    # --- demo (25) ---
    "D1_live": ("demo", 2.5, "live fast + keyless + baked fallback"),
    "D2_video": ("demo", 2.5, "3-min video w/ cold open recorded"),
    "D3_ticker": ("demo", 2.0, "daily-loop ticker visible (papers->edges->rank)"),
    "D4_cost": ("demo", 1.5, "cost meter on screen ($/edge)"),
    "D5_backup": ("demo", 1.5, "backup recording for Nov-9 final"),
    # --- depth (20) ---
    "H1_craft": ("depth", 2.5, "craft screen: AUC+CI+cost+hand precision"),
    "H2_leak": ("depth", 2.5, "leakage audit by normalized pair"),
    "H3_prec": ("depth", 1.5, "G1: 30 edges hand-audited, prec>=0.8"),
    "H4_fail": ("depth", 2.0, "fail-closed (no silent NaN->median->p_host)"),
    "H5_phy": ("depth", 1.5, "is_patristic_real + per-class normalization"),
}

W = {"impact": 0.30, "tooling": 0.25, "demo": 0.25, "depth": 0.20}
BSD = {"impact": 0.6, "tooling": 0.6, "demo": 0.7, "depth": 0.6}

DEFAULT_STATE = {
    "S1_coldopen_pub": 0, "S2_litmine_pub": 0, "S3_models_grep": 0.5,
    "S4_disclaimer": 1, "S5_provenance": 1, "S6_live": 1,
    "I1_called": 0, "I2_confirm": 0, "I3_agro": 0.5, "I4_eggs": 0.5,
    "I5_benef": 1,
    "T1_cascade": 0, "T2_switch": 0.5, "T3_wonder": 1, "T4_glimmer": 0.5,
    "T5_ledger": 0,
    "D1_live": 1, "D2_video": 0.5, "D3_ticker": 0, "D4_cost": 0,
    "D5_backup": 0,
    "H1_craft": 0.5, "H2_leak": 0, "H3_prec": 0, "H4_fail": 0.5,
    "H5_phy": 0,
}


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            st = json.load(f)
        s = dict(DEFAULT_STATE)
        s.update(st.get("checks", {}))
        return s, st.get("log", [])
    return dict(DEFAULT_STATE), []


def save(checks, log):
    with open(STATE, "w") as f:
        json.dump({"checks": checks, "log": log[-200:]}, f, indent=1)


def buckets(checks):
    out = {}
    for b in W:
        tot = sum(pts for (bb, pts, _) in CHECKS.values() if bb == b)
        got = sum(pts * checks[cid]
                  for cid, (bb, pts, _) in CHECKS.items() if bb == b)
        out[b] = 10.0 * got / tot
    surv_miss = sum(1 for cid, (bb, _, _) in CHECKS.items()
                    if bb == "surv" and checks[cid] < 1)
    p_stage1 = 0.99 * (0.7 ** surv_miss)
    return out, p_stage1, surv_miss


def mc(scores, n_comp=150, mu=6.5, sd=1.0, trials=30000, seed=99):
    rng = random.Random(seed)
    wsum = sum(W.values())
    hit = 0
    for _ in range(trials):
        me = sum(W[k] * max(0, min(10, rng.gauss(scores[k], BSD[k])))
                 for k in W) / wsum
        better = sum(1 for _ in range(n_comp) if rng.gauss(mu, sd) > me)
        hit += better < 5
    return hit / trials


def card(checks):
    scores, p1, miss = buckets(checks)
    tot = sum(W[k] * scores[k] for k in W)
    print(f"bucket  impact={scores['impact']:.1f} tool={scores['tooling']:.1f} "
          f"demo={scores['demo']:.1f} depth={scores['depth']:.1f} "
          f"=> total={tot:.2f}/10")
    print(f"survival misses={miss}  P(stage1)={p1:.3f}")
    for n, mu in ((80, 6.0), (150, 6.5), (300, 7.0)):
        p = mc(scores, n, mu)
        print(f"  field={n:<4} rival_mu={mu}: P(top5|pass)={p:.3f} "
              f"P(prize)={p1*p:.3f}")
    print("top gaps (pts left on table):")
    gaps = sorted(
        ((CHECKS[c][1] * (1 - checks[c]) * W.get(CHECKS[c][0], 0), c,
          CHECKS[c][2])
         for c in CHECKS if CHECKS[c][0] in W and checks[c] < 1),
        reverse=True)[:5]
    for pts, c, d in gaps:
        print(f"  {c:<16} +{pts:.2f} wtd  {d}  [now {checks[c]}]")
    return scores, p1


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "score"
    checks, log = load()
    if cmd == "set" and len(sys.argv) == 4:
        cid, v = sys.argv[2], float(sys.argv[3])
        assert cid in CHECKS and v in (0, 0.5, 1), "bad id/value"
        checks[cid] = v
        scores, p1, _ = buckets(checks)
        log.append({"ts": datetime.now(timezone.utc).isoformat(),
                    "set": [cid, v], "scores": scores, "p1": p1})
        save(checks, log)
        print(f"{cid} -> {v}")
        card(checks)
    elif cmd == "history":
        for e in log[-15:]:
            s = e["scores"]
            print(f"{e['ts'][:16]} {e['set'][0]}={e['set'][1]} "
                  f"I={s['impact']:.1f} T={s['tooling']:.1f} "
                  f"D={s['demo']:.1f} H={s['depth']:.1f} P1={e['p1']:.2f}")
    else:
        scores, p1 = card(checks)
        log.append({"ts": datetime.now(timezone.utc).isoformat(),
                    "set": ["score", None], "scores": scores, "p1": p1})
        save(checks, log)


if __name__ == "__main__":
    main()
