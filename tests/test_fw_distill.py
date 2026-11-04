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
