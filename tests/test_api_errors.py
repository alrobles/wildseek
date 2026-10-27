"""DB/IO failures must degrade to 503, never raw 500 tracebacks."""
from fastapi.testclient import TestClient

import api.main as m
from api.main import app


def test_species_corrupt_parquet_503(tmp_path, monkeypatch):
    (tmp_path / "species_winner.csv").write_text(
        "specieskey,species,aic\n1,sp_a,10.0\n")
    (tmp_path / "susceptibility.parquet").write_bytes(b"not a parquet")
    monkeypatch.setattr(m, "DATA", tmp_path)
    r = TestClient(app).get("/species")
    assert r.status_code == 503
