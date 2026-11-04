"""Judge backends must default to cloud — the local glimmer tunnel
died with the cluster. Pure: no keys, no network, no clients built.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "litmine"))

import verify  # noqa: E402


def test_backends_cover_cloud():
    assert set(verify.BACKENDS) >= {"fireworks", "baseten", "meta"}


def test_default_model_matches_backend():
    assert verify.default_model("fireworks", None) == \
        "accounts/fireworks/models/muse-spark-open"
    assert verify.default_model("baseten", None) == \
        "meta-models/muse-spark-open-1026"
    assert verify.default_model("meta", None) == "muse-spark-1.3"
    assert verify.default_model("local", None) == "muse-glimmer"
    assert verify.default_model("fireworks", "custom") == "custom"


def test_verify_cli_defaults_to_cloud():
    ap = verify.build_parser()
    assert ap.parse_args(["--edges", "e.csv"]).backend == "fireworks"


def test_monitor_judge_defaults_to_cloud():
    import monitor  # noqa: E402
    ap = monitor.build_parser()
    assert ap.parse_args(["run"]).judge_backend == "fireworks"
