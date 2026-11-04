"""Briefing headline must always carry the WildSeek product name."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import briefing  # noqa: E402


class _StubClient:
    def __init__(self, headline):
        self.headline = headline

    def chat(self, **kw):
        return {"content": json.dumps({
            "headline": self.headline,
            "hotspots": ["x"],
            "watchlist": ["y"],
            "methods_note": ("Ellipsoid niche models aggregate "
                             "risk to HUC8 watersheds."),
        })}


def test_wildscan_rewritten(tmp_path):
    out = briefing.briefing(client=_StubClient("WildScan brief"),
                            data_dir=tmp_path)
    assert "WildSeek" in out["headline"]
    assert "WildScan" not in out["headline"]


def test_missing_name_prefixed(tmp_path):
    out = briefing.briefing(client=_StubClient("Morning hotspots"),
                            data_dir=tmp_path)
    assert out["headline"].startswith("WildSeek")


def test_enforce_name_unit():
    assert briefing._enforce_name("WildScan brief") == "WildSeek brief"
    assert briefing._enforce_name("") == "WildSeek brief"
    assert briefing._enforce_name("WildSeek: H5N1 update").startswith(
        "WildSeek")
