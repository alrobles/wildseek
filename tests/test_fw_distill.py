"""fw_distill must pass a self-consistent run dir and fail closed when
summary.json disagrees with the raw predictions (a half-written or
corrupt summary must not reach eval/)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import fw_distill as fd  # noqa: E402


def _row(i, exact, fields, truncated=False):
    return {"index": i, "gold": "{}", "exact": exact,
            "fields": fields, "truncated": truncated, "answer_text": "{}"}


def _run(tmp_path, tuned_exact=3, summary=None):
    base = [_row(i, False, {"relevant": True, "hosts": False},
                 truncated=(i == 0)) for i in range(4)]
    tuned = [_row(i, i < tuned_exact, {"relevant": True, "hosts": i < tuned_exact})
             for i in range(4)]
    (tmp_path / "predictions_base.jsonl").write_text(
        "\n".join(json.dumps(r) for r in base))
    (tmp_path / "predictions_tuned.jsonl").write_text(
        "\n".join(json.dumps(r) for r in tuned))
    (tmp_path / "holdout.jsonl").write_text("\n".join("{}" for _ in base))
    (tmp_path / "metrics.jsonl").write_text(
        '\n'.join(f'{{"step": {i}}}' for i in range(1, 5)))
    if summary is None:
        summary = {
            "steps": 4,
            "base": {"label": "base", "exact_match": 0.0, "unterminated": 1,
                     "prompt_tokens": 1, "sampled_tokens": 1,
                     "field_accuracy": {"relevant": 1.0, "hosts": 0.0}},
            "tuned": {"label": "tuned", "exact_match": tuned_exact / 4,
                      "unterminated": 0, "prompt_tokens": 1, "sampled_tokens": 1,
                      "field_accuracy": {"relevant": 1.0,
                                         "hosts": tuned_exact / 4}},
            "exact_match_delta": tuned_exact / 4,
            "paired": {"only_tuned_correct": tuned_exact,
                       "only_base_correct": 0,
                       "p_value": fd.mcnemar_p(0, tuned_exact)},
            "session": "ts-x", "log": "muse_starter_logs/test",
        }
    (tmp_path / "summary.json").write_text(json.dumps(summary))
    return tmp_path


def test_check_clean_run(tmp_path):
    assert fd.check(_run(tmp_path)) == []


def test_check_flags_corrupt_summary(tmp_path):
    run = _run(tmp_path)
    summ = json.loads((run / "summary.json").read_text())
    summ["tuned"]["exact_match"] = 0.25
    (run / "summary.json").write_text(json.dumps(summ))
    errs = fd.check(run)
    assert any("tuned.exact_match" in e for e in errs)
    assert any("exact_match_delta" in e for e in errs)


def test_check_flags_wrong_paired(tmp_path):
    run = _run(tmp_path)
    summ = json.loads((run / "summary.json").read_text())
    summ["paired"]["only_tuned_correct"] = 2
    (run / "summary.json").write_text(json.dumps(summ))
    errs = fd.check(run)
    assert any("paired" in e for e in errs)


def test_field_accuracy_per_key_denominator(tmp_path):
    # variable-schema holdout ("all" orchestrator): a field's accuracy is
    # over rows whose gold carried the key, not all rows — mirrors the
    # wildseek-all run where relevant x/14 and decision x/24 coexist.
    base = [_row(0, False, {"relevant": False}),
            _row(1, False, {"relevant": True}),
            _row(2, False, {"decision": False}),
            _row(3, False, {"decision": False})]
    tuned = [_row(i, True, f) for i, f in enumerate(
        [{"relevant": True}, {"relevant": True},
         {"decision": True}, {"decision": True}])]
    for name, rows in (("base", base), ("tuned", tuned)):
        (tmp_path / f"predictions_{name}.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows))
    (tmp_path / "holdout.jsonl").write_text("\n".join("{}" for _ in base))
    (tmp_path / "metrics.jsonl").write_text('{"step": 1}')
    summary = {
        "steps": 1,
        "base": {"label": "base", "exact_match": 0.0, "unterminated": 0,
                 "prompt_tokens": 1, "sampled_tokens": 1,
                 "field_accuracy": {"relevant": 0.5, "decision": 0.0}},
        "tuned": {"label": "tuned", "exact_match": 1.0, "unterminated": 0,
                  "prompt_tokens": 1, "sampled_tokens": 1,
                  "field_accuracy": {"relevant": 1.0, "decision": 1.0}},
        "exact_match_delta": 1.0,
        "paired": {"only_tuned_correct": 4, "only_base_correct": 0,
                   "p_value": fd.mcnemar_p(0, 4)},
        "session": "ts-x", "log": "muse_starter_logs/test",
    }
    (tmp_path / "summary.json").write_text(json.dumps(summary))
    assert fd.check(tmp_path) == []
    # an n-denominator summary (relevant 1/4) must fail closed
    summary["base"]["field_accuracy"]["relevant"] = 0.25
    (tmp_path / "summary.json").write_text(json.dumps(summary))
    assert any("relevant" in e for e in fd.check(tmp_path))


def test_mcnemar_matches_triage_reference():
    # triage run: 28-0 discordant -> 2 * (1/2)^28 = 7.45e-9
    assert fd.mcnemar_p(0, 28) == 7.450580596923828e-09
    assert fd.mcnemar_p(0, 0) == 1.0


def _pred(i, gold, ans, exact=False, fields=None, truncated=False):
    if fields is None:
        fields = {k: False for k in json.loads(gold)} if _isjson(gold) else {}
    return {"index": i, "gold": gold, "exact": exact, "fields": fields,
            "truncated": truncated, "answer_text": ans}


def _isjson(s):
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False


def test_rescore_paraphrase_reason_rescues_row():
    # mirrors wildseek-all decision rows: same stats, reworded -> PARAPHRASE
    gold = ('{"decision": "rank", "reason": "88/88 accepted_global, n=33 '
            'adequate, top5 AIC spread 11.64 shows clear winner."}')
    ans = ('{"decision": "rank", "reason": "88/88 accepted_global, n=33, '
           'top5 AIC spread 11.64 shows clear winner; proceed."}')
    r = fd.rescore([_pred(0, gold, ans,
                          fields={"decision": True, "reason": False})])
    assert r["exact_match"] == 0.0
    assert r["exact_match_semantic"] == 1.0
    assert r["field_accuracy_semantic"]["reason"] == 1.0
    assert r["field_accuracy"]["reason"] == 0.0
    assert r["rescued"] == [0]


def test_rescore_real_errors_stay_errors():
    # empty extraction answer (idx 0/21/27/30 pattern) must NOT be rescued
    gold = ('{"relevant": true, "hosts": "monkeys; domestic pigs; Bats", '
            '"parasites": "RESTV; Marburgvirus"}')
    ans = '{"relevant": false, "hosts": "", "parasites": ""}'
    r = fd.rescore([_pred(0, gold, ans)])
    assert r["exact_match_semantic"] == 0.0
    assert r["field_accuracy_semantic"]["hosts"] == 0.0
    # over-extraction superset (idx 25 pattern): low F1 stays an error
    gold2 = '{"hosts": "chimpanzee"}'
    ans2 = '{"hosts": "chimpanzee; chimpanzee community; gorillas; monkeys; bush pigs"}'
    r2 = fd.rescore([_pred(1, gold2, ans2)])
    assert r2["field_accuracy_semantic"]["hosts"] == 0.0


def test_rescore_num_cov_rounding_and_missing():
    # gold "spread 1713.9" vs answer "spread 1713" -> covered at 1% rtol
    assert fd._num_cov("spread 1713.9, n=6621", "spread 1713, n=6621") == 1.0
    # one optional literal dropped (5/6 = .833 >= SEM_NUM) still passes
    assert fd._num_cov("n=104 spread 31.37 best 59.92 a 1 b 2 c 3",
                       "n=104 spread 31.37 a 1 b 2 c 3") == 5 / 6
    # no gold numbers -> coverage vacuous 1.0
    assert fd._num_cov("no digits", "none either") == 1.0


def test_rescore_fails_closed_on_truncated_and_structural():
    # truncated + unparseable answer: never rescued
    gold = '{"decision": "rank", "reason": "n=33 adequate, spread 11.6 clear"}'
    ans = '{"decision": "rank", "reason": "n=33 adequate, spread 11.6 cle'
    r = fd.rescore([_pred(0, gold, ans, truncated=True)])
    assert r["exact_match_semantic"] == 0.0
    # exact=False with empty fields (structural mismatch) fails closed
    r2 = fd.rescore([_pred(1, gold, gold, fields={})])
    assert r2["exact_match_semantic"] == 0.0
    # unparseable gold fails closed too
    r3 = fd.rescore([_pred(2, '{"a": "x', '{"a": "x', fields={"a": False})])
    assert r3["exact_match_semantic"] == 0.0


def test_rescore_bool_field_not_semantic():
    # non-string fields (relevant: bool) can only pass strict
    gold = '{"relevant": true}'
    ans = '{"relevant": false}'
    r = fd.rescore([_pred(0, gold, ans)])
    assert r["field_accuracy_semantic"]["relevant"] == 0.0
    assert r["exact_match_semantic"] == 0.0


def _chat(user, assistant, sysp="sys"):
    return {"messages": [{"role": "system", "content": sysp},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}]}


def _chunk(user, relevant=True):
    return _chat(user, json.dumps({"relevant": relevant, "hosts": "bats",
                                   "parasites": "ZEBOV"}))


def test_lint_clean_pair_no_warnings():
    vocab = ["alpha beta gamma", "delta epsilon zeta", "eta theta iota",
             "kappa lambda mu", "nu xi omicron", "pi rho sigma",
             "tau upsilon phi", "chi psi omega", "lorem ipsum dolor",
             "sit amet consectetur"]
    train = [_chunk(f"distinct narrative {v} number {i}",
                    relevant=bool(i % 2)) for i, v in enumerate(vocab)]
    hold = [_chunk("unseen vocabulary quartz jasper onyx", relevant=False),
            _chunk("fresh terms ruby emerald sapphire", relevant=True)]
    assert fd.lint(train, hold)["warnings"] == []


def test_lint_verbatim_and_neardup_leak():
    leak_text = "serological status of bats captured 2003 according to site"
    train = [_chunk(leak_text), _chunk("other narrative " + "w " * 40)]
    hold = [_chunk(leak_text),
            _chunk(leak_text.replace("site", "demographic parameters"))]
    r = fd.lint(train, hold)
    assert any("verbatim" in w for w in r["warnings"])
    assert any("near-dup" in w for w in r["warnings"])
    assert r["leaks"][0]["exact"] is True
    assert r["leaks"][1]["exact"] is False


def test_lint_class_skew_and_dups():
    # 70% negative chunk rows -> minority 0.30 < MINOR_FLOOR; plus a
    # verbatim duplicate row inside train (mirrors max4k pool: 14 dups)
    train = ([_chunk(f"neg chunk {i} filler words {i}", relevant=False)
              for i in range(7)]
             + [_chunk(f"pos chunk {i} different terms {i}") for i in range(3)]
             + [_chunk("neg chunk 0 filler words 0", relevant=False)])
    r = fd.lint(train, [])
    assert any("minority share" in w for w in r["warnings"])
    assert any("exact-duplicate" in w for w in r["warnings"])
    assert r["train_dups"] == [(0, 10)]


def test_lint_long_gold_and_cluster_flag():
    long_rel = _chat("abstract", json.dumps(
        [{"parasite_taxid": str(i), "host_taxid": "1"} for i in range(200)]))
    train = [long_rel] + [_chunk(f"shared boilerplate caption text {i % 2}")
                          for i in range(4)]
    hold = [long_rel]
    r = fd.lint(train, hold)
    assert any("truncation risk" in w for w in r["warnings"])
    assert r["long_gold"][0]["index"] == 0
    # 4 near-identical caption rows form a chunk cluster
    assert r["train_clusters"]["chunk"]["rows"] >= 4


def test_task_classifier():
    assert fd._task(_chat("u", '[{"a": 1}]')) == "relations"
    assert fd._task(_chunk("u", True)) == "chunk_pos"
    assert fd._task(_chunk("u", False)) == "chunk_neg"
    assert fd._task(_chat("u", '{"decision": "rank"}')) == "triage"
    assert fd._task(_chat("u", "not json")) == "other"
