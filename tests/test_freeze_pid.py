"""freeze --check must match float-formatted PMIDs (e.g. "12345.0")
against digit-normalized pubdate keys — else status never confirms.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import freeze_predictions as fp  # noqa: E402


def test_check_confirms_float_pmid(tmp_path, monkeypatch):
    edges = tmp_path / "edges.csv"
    pd.DataFrame([{"host": "Phalaropus tricolor", "pmid": "12345.0"}]) \
        .to_csv(edges, index=False)
    monkeypatch.setattr(fp, "_pmid_pubdate",
                        lambda: {"12345": "2026-10-29"})
    card = {"predicted_on": "2026-10-28", "predictions": [
        {"species": "Phalaropus tricolor", "status": "awaiting-confirmation"},
    ]}
    out = fp.check(card, str(edges))
    assert out["predictions"][0]["status"] == "confirmed"


def test_check_ignores_pre_freeze(tmp_path, monkeypatch):
    edges = tmp_path / "edges.csv"
    pd.DataFrame([{"host": "Phalaropus tricolor", "pmid": 12345}]) \
        .to_csv(edges, index=False)
    monkeypatch.setattr(fp, "_pmid_pubdate",
                        lambda: {"12345": "2026-10-20"})
    card = {"predicted_on": "2026-10-28", "predictions": [
        {"species": "Phalaropus tricolor", "status": "awaiting-confirmation"},
    ]}
    out = fp.check(card, str(edges))
    assert out["predictions"][0]["status"] == "awaiting-confirmation"
