"""Unvalidated limit/top must not reach SQL (negative/huge -> 500).

Contract: limit/top accept 1..2000 (FastAPI 422 outside), so DuckDB
never sees a negative LIMIT or an unbounded scan dump. The species
drill-down needs the full 1,147 catalog in one page (limit=1200).
"""
from fastapi.testclient import TestClient

from api.main import app

c = TestClient(app)


def test_species_negative_limit_no_500():
    r = c.get("/species?limit=-1")
    assert r.status_code in (200, 422)


def test_species_huge_limit_capped():
    r = c.get("/species?limit=1000000")
    assert r.status_code == 422


def test_species_drilldown_page(tmp_path, monkeypatch):
    import pandas as pd

    import api.main as mm
    pd.DataFrame({"specieskey": range(1147),
                  "species": [f"Sp {i}" for i in range(1147)],
                  "aic": range(1147)}).to_csv(
        tmp_path / "species_winner.csv", index=False)
    monkeypatch.setattr(mm, "DATA", tmp_path)
    r = TestClient(app).get("/species?limit=1200")
    assert r.status_code == 200
    assert len(r.json()) == 1147


def test_susceptibility_huge_top_no_500():
    r = c.get("/susceptibility?top=1000000")
    assert r.status_code in (200, 422)
