"""Brain reviewer: strict JSON verdict, fence-tolerant, one retry.

N2: the live brain abstained on an empty model reply
("Expecting value: line 1 column 1"). Stub clients only — no network.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import qa  # noqa: E402


class _Stub:
    def __init__(self, *contents):
        self.contents = list(contents)
        self.calls = 0

    def chat(self, *a, **k):
        self.calls += 1
        # api.meta.ai returns empty content with response_format set,
        # so the brain must NOT request it (verified 2026-11-04).
        assert "response_format" not in k, k.keys()
        assert "exactamente un objeto JSON" in a[0][0]["content"]
        return {"content": self.contents.pop(0)}


def test_fenced_verdict_ok():
    c = _Stub('```json\n{"verdict": "approve", "reason": "routine"}\n```')
    out = qa._brain({"run": "x"}, client=c)
    assert out == [{"name": "brain review", "ok": True, "value": "routine"}]
    assert c.calls == 1


def test_garbage_abstains_after_retry():
    c = _Stub("not json {{", "")
    out = qa._brain({"run": "x"}, client=c)
    assert c.calls == 2  # initial + one retry
    assert out[0]["ok"] is False
    assert out[0]["value"].startswith("abstain: unparseable")


def test_reject_verdict():
    c = _Stub('{"verdict": "reject", "reason": "data collapse"}')
    out = qa._brain({"run": "x"}, client=c)
    assert out[0]["ok"] is False
    assert out[0]["value"] == "data collapse"


def test_legacy_approve_shape():
    c = _Stub('{"approve": true, "reason": "ok"}')
    out = qa._brain({"run": "x"}, client=c)
    assert out[0]["ok"] is True


def test_no_manifest():
    out = qa._brain(None, client=_Stub('{"verdict":"approve"}'))
    assert out[0]["value"] == "abstain: no manifest"
