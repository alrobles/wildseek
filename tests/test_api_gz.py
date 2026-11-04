"""Precompressed statics: <file>.gz serves when the client accepts gzip.

The GZip middleware must pass the encoded variant through untouched —
a double-compressed body would corrupt every opt-in fetch.
"""
import gzip

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.gzip import GZipMiddleware

import api.main as m

RAW = b'{"type":"FeatureCollection","features":[]}'


def _client(tmp_path):
    (tmp_path / "big.geojson").write_bytes(RAW)
    (tmp_path / "big.geojson.gz").write_bytes(
        gzip.compress(RAW, compresslevel=9, mtime=0))
    (tmp_path / "small.json").write_bytes(b"{}")
    app = FastAPI()
    app.add_middleware(GZipMiddleware, minimum_size=1)
    app.mount("/", m._Precompressed(directory=tmp_path, html=True))
    return TestClient(app)


def test_gz_served_encoded(tmp_path):
    r = _client(tmp_path).get("/big.geojson")
    assert r.status_code == 200
    assert r.headers["content-encoding"] == "gzip"
    assert "Accept-Encoding" in r.headers["vary"]
    assert r.headers["content-type"].startswith("application/geo+json")
    assert r.content == RAW  # httpx decodes once: body is the raw json


def test_identity_gets_raw_file(tmp_path):
    r = _client(tmp_path).get(
        "/big.geojson", headers={"accept-encoding": "identity"})
    assert r.status_code == 200
    assert "content-encoding" not in r.headers
    assert r.content == RAW


def test_no_sibling_falls_back(tmp_path):
    r = _client(tmp_path).get("/small.json")
    assert r.status_code == 200
    assert r.content == b"{}"


def test_post_still_405(tmp_path):
    assert _client(tmp_path).post("/big.geojson").status_code == 405
