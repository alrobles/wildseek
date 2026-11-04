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
  tools/fw_distill.py lint    <run_dir> | <train.jsonl> <holdout.jsonl>
                                                      # pre-launch dataset audit
  tools/fw_distill.py rebuild <traj_train> <traj_val> <out_dir>
                                                      # launch-ready v2 dataset
"""

import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
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

# lint thresholds — learned on the wildseek-all-20261104-0017 autopsy:
# the starter carved its 40-row holdout out of the train pool (all 40 rows
# verbatim in fw_all_train_max4k, near-dup siblings left behind), triage
# train ran 63% relevant:false, one paper (pmid 19785757) held 63 near-dup
# caption chunks, and the only 2 truncated eval rows had gold > 1600 chars
# vs 473 for the longest clean row.
LEAK_J = 0.7      # holdout-vs-train token-Jaccard = cross-split leak
DUP_J = 0.7       # train-vs-train Jaccard = paper-level over-representation
MINOR_FLOOR = 0.4  # binary task minority share below this = skewed prior
LONG_GOLD = 1200   # assistant gold chars = eval truncation risk


def _task(row: dict) -> str:
    try:
        g = json.loads(row["messages"][-1]["content"])
    except (KeyError, IndexError, json.JSONDecodeError, TypeError):
        return "other"
    if isinstance(g, list):
        return "relations"
    if not isinstance(g, dict):
        return "other"
    if "hosts" in g:
        return "chunk_pos" if g.get("relevant") else "chunk_neg"
    if "decision" in g:
        return "triage"
    return "other"


def _tokset(row: dict) -> frozenset:
    try:
        u = row["messages"][1]["content"]
    except (KeyError, IndexError, TypeError):
        return frozenset()
    return frozenset(re.findall(r"[a-z0-9]+", u.lower()))


def _user_text(row: dict) -> str:
    try:
        return " ".join(row["messages"][1]["content"].split())
    except (KeyError, IndexError, TypeError, AttributeError):
        return ""


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _near_pairs(small: list[tuple[int, frozenset]],
                big: list[tuple[int, frozenset]],
                thresh: float) -> list[tuple[int, int, float]]:
    """(small_idx, big_idx, j) for every pair scoring >= thresh.

    Size-ratio prefilter: jaccard <= min(|a|,|b|)/max(|a|,|b|), so pairs
    whose sizes can't reach thresh are skipped before the set algebra.
    """
    out = []
    for i, a in small:
        for j, b in big:
            if min(len(a), len(b)) < thresh * max(len(a), len(b)):
                continue
            s = _jaccard(a, b)
            if s >= thresh:
                out.append((i, j, round(s, 3)))
    return out


def _jsonl(path: Path) -> list[dict]:
    # split on "\n" only: str.splitlines() also breaks on U+2028/\x85/\v,
    # which are legal raw chars inside a JSON string (traj_all_*.jsonl
    # carries 16 U+2028) and would corrupt the row count.
    return [json.loads(x) for x in path.read_text().split("\n") if x.strip()]


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


def _base(task: str) -> str:
    return "chunk" if task.startswith("chunk_") else task


def lint(train: list[dict], hold: list[dict]) -> dict:
    """Pre-launch audit of a train/holdout pair — facts + warnings.

    Catches the wildseek-all failure modes: holdout carved from the train
    pool (exact + near-dup leak), duplicate rows inside train, binary-task
    class skew, paper-level near-dup concentration, and gold outputs long
    enough to truncate under the eval sampling budget.
    """
    ttask = [_task(r) for r in train]
    htask = [_task(r) for r in hold]
    warn: list[str] = []

    counts = {"train": dict(Counter(ttask)), "holdout": dict(Counter(htask))}

    # binary-task class balance: minority share of the +/- split
    for split, tasks in (("train", ttask), ("holdout", htask)):
        pos = tasks.count("chunk_pos")
        n = pos + tasks.count("chunk_neg")
        if n and min(pos, n - pos) / n < MINOR_FLOOR:
            warn.append(f"{split} chunk minority share "
                        f"{min(pos, n - pos) / n:.2f} ({pos}/{n} pos) "
                        f"< {MINOR_FLOOR} — skewed label prior")

    # exact duplicate rows inside train (normalized user+assistant)
    seen: dict[tuple, int] = {}
    dups = []
    for i, r in enumerate(train):
        try:
            key = (_user_text(r), " ".join(
                r["messages"][-1]["content"].split()))
        except (KeyError, IndexError, TypeError, AttributeError):
            continue
        if key in seen:
            dups.append((seen[key], i))
        else:
            seen[key] = i
    if dups:
        warn.append(f"{len(dups)} exact-duplicate rows inside train "
                    f"(first copies at {[d[0] for d in dups[:5]]})")

    # cross-split leak: holdout user text vs same-task train rows
    tsets: dict[str, list[tuple[int, frozenset]]] = {}
    for i, r in enumerate(train):
        tsets.setdefault(_base(ttask[i]), []).append((i, _tokset(r)))
    leak = []
    for h, r in enumerate(hold):
        cand = tsets.get(_base(htask[h]), [])
        u = _user_text(r)
        exact = [i for i, _ in cand
                 if _user_text(train[i]) == u] if u else []
        near = _near_pairs([(h, _tokset(r))], cand, LEAK_J)
        near = [(i, j) for _, i, j in near if i not in exact]
        if exact:
            leak.append({"holdout": h, "train": exact, "exact": True})
            warn.append(f"holdout {h} verbatim in train {exact} — "
                        f"cross-split leak")
        if near:
            leak.append({"holdout": h, "train": [i for i, _ in near],
                         "j": max(j for _, j in near), "exact": False})
            warn.append(f"holdout {h} near-dup of train {[i for i, _ in near]} "
                        f"(J={max(j for _, j in near):.2f})")

    # intra-train near-dup concentration per task (paper-level prior proxy)
    clusters = {}
    for b, cand in tsets.items():
        if len(cand) < 2:
            continue
        pairs = [p for p in _near_pairs(cand, cand, DUP_J) if p[0] < p[1]]
        if pairs:
            rows = {i for p in pairs for i in p[:2]}
            clusters[b] = {"rows": len(rows), "pairs": len(pairs)}
            warn.append(f"train {b}: {len(rows)} rows in {len(pairs)} "
                        f"near-dup pairs (J>={DUP_J}) — paper-level "
                        f"over-representation")

    # gold outputs long enough to truncate under the eval sampling budget
    long_gold = []
    for split, rows in (("train", train), ("holdout", hold)):
        for i, r in enumerate(rows):
            try:
                n = len(r["messages"][-1]["content"])
            except (KeyError, IndexError, TypeError):
                continue
            if n > LONG_GOLD:
                long_gold.append({"split": split, "index": i, "chars": n})
    if long_gold:
        hg = [g["index"] for g in long_gold if g["split"] == "holdout"]
        if hg:
            warn.append(f"holdout gold >{LONG_GOLD} chars at {hg} — "
                        f"eval truncation risk")

    return {"counts": counts, "train_dups": dups, "leaks": leak,
            "train_clusters": clusters, "long_gold": long_gold,
            "warnings": warn}


def cmd_lint(args: list[str]) -> int:
    if len(args) == 1 and Path(args[0]).is_dir():
        run = Path(args[0])
        train = _jsonl(run / "train.jsonl")
        hold = _jsonl(run / "holdout.jsonl")
    elif len(args) == 2:
        train, hold = _jsonl(Path(args[0])), _jsonl(Path(args[1]))
    else:
        sys.exit(__doc__)
    r = lint(train, hold)
    for split, c in r["counts"].items():
        print(f"{split}: "
              + "  ".join(f"{k}={v}" for k, v in sorted(c.items())))
    for w in r["warnings"]:
        print("WARN:", w)
    print(f"{len(r['warnings'])} warnings")
    return 1 if r["warnings"] else 0


# ----------------------------------------------------------------- rebuild
# Launch-dataset rebuild from wildseek-lora traj_*_{train,val}.jsonl —
# fixes every failure mode the wildseek-all autopsy (and lint above) named:
#  * holdout must be the pmid/key-GROUPED val split, never re-carved from
#    train. The starter carves --file with a seeded shuffle and takes the
#    first n_eval rows, so rebuild pre-places the val rows at exactly the
#    file positions that shuffle sends to the front: the carve then returns
#    the grouped val verbatim, zero leak by construction.
#  * exact-duplicate train rows dropped (normalized user+assistant).
#  * binary task rebalanced: per-group positives capped at POS_CAP, then a
#    single per-group negative cap solved so kept negs ~= kept pos.
#  * non-binary tasks capped at GROUP_CAP rows per pmid/key (singletons
#    today; guards regrowth).
#  * eval rows with gold > MAX_GOLD chars dropped (observed truncation
#    risk), plus a paranoid verbatim-vs-train drop.
#  * both sides filtered to <=TOK_LIMIT content tokens (chat-template
#    overhead pushes ~4060-tok rows past --max-seq-len 4096).
POS_CAP = 20
GROUP_CAP = 40
TOK_LIMIT = 4000
TOK_MODEL = "meta-models/Muse-Glimmer-30B"


def _traj_to_chat(r: dict) -> dict | None:
    """traj {system,instruction,input,output} -> {"messages": [...]}.
    Mirrors wildseek-lora scripts/fw_convert.convert_row."""
    out = (r.get("output") or "").strip()
    if not out:
        return None
    user = "\n\n".join(p for p in ((r.get("instruction") or "").strip(),
                                   (r.get("input") or "").strip()) if p)
    if not user:
        return None
    msgs = []
    if (r.get("system") or "").strip():
        msgs.append({"role": "system", "content": r["system"].strip()})
    msgs += [{"role": "user", "content": user},
             {"role": "assistant", "content": out}]
    return {"messages": msgs}


def _group(r: dict) -> str:
    p = r.get("provenance") or {}
    return str(p.get("pmid") or p.get("key") or "")


def _label(r: dict) -> bool | None:
    try:
        v = json.loads(r["output"]).get("relevant")
    except (json.JSONDecodeError, TypeError, AttributeError):
        return None
    return v if isinstance(v, bool) else None


def _norm_dup(chat: dict) -> tuple:
    return (_user_text(chat),
            " ".join(chat["messages"][-1]["content"].split()))


def _default_tok():
    """(counter, mode) — real Glimmer tokenizer when the cookbook venv is
    importable (FW_COOKBOOK or /tmp/fw-cookbook/training), else chars//3
    (conservative; --max-seq-len still trims stragglers server-side)."""
    try:
        sys.path.insert(0, os.environ.get("FW_COOKBOOK",
                                        "/tmp/fw-cookbook/training"))
        from training.renderer.tokenizer import get_tokenizer
        t = get_tokenizer(TOK_MODEL)
        return (lambda s: len(t.encode(s))), "glimmer"
    except Exception:
        return (lambda s: len(s) // 3), "est3"


def _neg_cap(counts: dict, target: int) -> int:
    """Per-group negative cap whose total kept lands closest to target."""
    best = (1, None)
    for k in range(1, max(counts.values(), default=1) + 1):
        d = abs(sum(min(n, k) for n in counts.values()) - target)
        if best[1] is None or d < best[1]:
            best = (k, d)
    return best[0]


def _cap_task(rows: list, pos_cap: int, group_cap: int,
              drops: Counter) -> list:
    """Cap one task's (traj, chat) pairs. Binary tasks (output carries a
    bool 'relevant') get per-group pos cap + a globally-solved neg cap."""
    labels = [_label(r) for r, _ in rows]
    if not any(lb is not None for lb in labels):
        groups = defaultdict(list)
        for p in rows:
            groups[_group(p[0])].append(p)
        kept = []
        for glist in groups.values():
            kept += glist[:group_cap]
            drops["group_cap"] += max(0, len(glist) - group_cap)
        return kept
    pos_g, neg_g, other = defaultdict(list), defaultdict(list), []
    for p, lb in zip(rows, labels):
        (pos_g[_group(p[0])] if lb else
         neg_g[_group(p[0])] if lb is False else other).append(p)
    kept = []
    for glist in pos_g.values():
        kept += glist[:pos_cap]
        drops["pos_cap"] += max(0, len(glist) - pos_cap)
    k = _neg_cap({g: len(v) for g, v in neg_g.items()}, len(kept))
    for glist in neg_g.values():
        kept += glist[:k]
        drops["neg_cap"] += max(0, len(glist) - k)
    return kept + other


def rebuild(traj_train: list, traj_val: list, seed: int = 7,
            pos_cap: int = POS_CAP, group_cap: int = GROUP_CAP,
            tok_limit: int = TOK_LIMIT, max_gold: int = LONG_GOLD,
            tok=None) -> tuple:
    """(train, eval, file_rows, manifest). file_rows interleaves eval at
    the seeded-shuffle front slots so the starter's carve returns the
    grouped val verbatim."""
    drops: Counter = Counter()
    tok_fn, tok_mode = ((tok, "injected") if callable(tok)
                        else tok or _default_tok())

    def convert(rows, tag):
        out = []
        for r in rows:
            c = _traj_to_chat(r)
            if c is None:
                drops[f"empty_{tag}"] += 1
            else:
                out.append((r, c))
        return out

    def dedup(pairs, tag):
        seen, out = set(), []
        for r, c in pairs:
            k = _norm_dup(c)
            if k in seen:
                drops[f"dup_{tag}"] += 1
            else:
                seen.add(k)
                out.append((r, c))
        return out

    # train: convert -> dedup -> per-task caps -> tok filter
    by_task = defaultdict(list)
    for p in dedup(convert(traj_train, "train"), "train"):
        by_task[(p[0].get("provenance") or {}).get("task", "?")].append(p)
    pairs = []
    for task, rows in sorted(by_task.items()):
        pairs += _cap_task(rows, pos_cap, group_cap, drops)
    kept = []
    for r, c in pairs:
        if sum(tok_fn(m["content"]) for m in c["messages"]) <= tok_limit:
            kept.append((r, c))
        else:
            drops["over_tok_train"] += 1
    train = [c for _, c in kept]
    tusers = {_user_text(c) for _, c in kept}

    # eval: grouped val, verbatim order — long gold and any accidental
    # train-verbatim are the only drops (rebalancing eval would game it)
    eval_rows = []
    for r, c in dedup(convert(traj_val, "val"), "val"):
        if len(c["messages"][-1]["content"]) > max_gold:
            drops["long_gold_val"] += 1
        elif _user_text(c) in tusers:
            drops["val_leak"] += 1
        elif sum(tok_fn(m["content"]) for m in c["messages"]) > tok_limit:
            drops["over_tok_val"] += 1
        else:
            eval_rows.append(c)

    # seeded placement: starter does rows <- shuffle(rows); eval <- rows[:n]
    perm = list(range(len(train) + len(eval_rows)))
    random.Random(seed).shuffle(perm)
    file_rows = [None] * len(perm)
    for slot, c in zip(perm[:len(eval_rows)], eval_rows):
        file_rows[slot] = c
    for slot, c in zip(perm[len(eval_rows):], train):
        file_rows[slot] = c
    chk = list(range(len(perm)))
    random.Random(seed).shuffle(chk)
    assert [file_rows[chk[j]] for j in range(len(eval_rows))] == eval_rows

    man = {
        "seed": seed, "n_eval": len(eval_rows), "train_rows": len(train),
        "file_rows": len(file_rows), "tok_mode": tok_mode,
        "tok_limit": tok_limit, "pos_cap": pos_cap, "group_cap": group_cap,
        "max_gold": max_gold, "drops": dict(drops),
        "train_tasks": dict(Counter(
            (r.get("provenance") or {}).get("task", "?")
            for r, _ in kept)),
        "eval_tasks": dict(Counter(_task(c) for c in eval_rows)),
        "lint": lint(train, eval_rows),
    }
    return train, eval_rows, file_rows, man


def cmd_rebuild(args: list) -> int:
    pos = [a for a in args if not a.startswith("--")]
    opts = {a.split("=")[0][2:]: a.split("=")[1]
            for a in args if a.startswith("--") and "=" in a}
    if len(pos) != 3:
        sys.exit(__doc__)
    src_tr, src_va, out_dir = Path(pos[0]), Path(pos[1]), Path(pos[2])
    m = re.match(r"traj_(.+?)_train", src_tr.name)
    tag = m.group(1) if m else "v2"
    train, eval_rows, file_rows, man = rebuild(
        _jsonl(src_tr), _jsonl(src_va), seed=int(opts.get("seed", 7)),
        pos_cap=int(opts.get("pos-cap", POS_CAP)),
        group_cap=int(opts.get("group-cap", GROUP_CAP)),
        tok_limit=int(opts.get("tok-limit", TOK_LIMIT)),
        max_gold=int(opts.get("max-gold", LONG_GOLD)))
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"fw_{tag}_v2"
    for name, rows in (("train", train), ("eval", eval_rows),
                       ("file", file_rows)):
        # ensure_ascii=True: raw U+2028/\x85 inside strings would be split
        # by the starter's own splitlines() reader — escaped they can't.
        (out_dir / f"{stem}_{name}.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows))
    man["launch"] = (f"tools/fw_starter.sh launch "
                     f"{out_dir}/{stem}_file.jsonl wildseek-{tag}v2-<ts> "
                     f"--n-eval {man['n_eval']} --seed {man['seed']}")
    (out_dir / f"{stem}_manifest.json").write_text(
        json.dumps(man, indent=1) + "\n")
    print(f"{tag}: train {man['train_rows']} eval {man['n_eval']} "
          f"file {man['file_rows']} drops {man['drops']} tok {man['tok_mode']}")
    hard = [w for w in man["lint"]["warnings"]
            if "verbatim" in w or "exact-duplicate" in w]
    for w in man["lint"]["warnings"]:
        print(("HARD" if w in hard else "WARN") + ":", w)
    return 1 if hard else 0


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
    if len(sys.argv) < 3 or sys.argv[1] not in ("check", "install",
                                               "rescore", "lint",
                                               "rebuild"):
        sys.exit(__doc__)
    if sys.argv[1] == "rescore":
        sys.exit(cmd_rescore(Path(sys.argv[2])))
    if sys.argv[1] == "lint":
        sys.exit(cmd_lint(sys.argv[2:]))
    if sys.argv[1] == "rebuild":
        sys.exit(cmd_rebuild(sys.argv[2:]))
    sys.exit(cmd_check(Path(sys.argv[2])) if sys.argv[1] == "check"
             else cmd_install(Path(sys.argv[2]), sys.argv[3]))
