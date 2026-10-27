"""HPAI Wildlife Monitor API — FastAPI + DuckDB over the parquet catalog.

Serves the ecoseek-style monitor: species susceptibility catalog,
per-species fit + suitability links, sub-county risk (watershed), and
the /explain endpoint (muse-spark narrative, System-1 typed).

Run:  DATA_DIR=/srv/hpai uvicorn api.main:app --port 8100
DATA_DIR holds the exported artifacts (GeoParquet / CSV / COG / PMTiles)
synced from /beegfs/a474r867/meta-hack on kuhpc.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

import duckdb
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

DATA = Path(os.environ.get("DATA_DIR", "data/serve"))

app = FastAPI(title="WildSeek", version="0.1.0")


@lru_cache
def con() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect()
    c.execute("PRAGMA threads=4")
    return c


def q(sql: str) -> list[dict]:
    return con().execute(sql).fetchdf().to_dict("records")


def _stamp() -> str | None:
    m = DATA / "meta.json"
    if m.exists():
        try:
            return json.loads(m.read_text()).get("built")
        except Exception:
            return None
    return None


@app.get("/health")
def health() -> dict:
    ok = (DATA / "fit_catalog.csv").exists()
    return {"status": "ok" if ok else "empty",
            "data_dir": str(DATA), "built": _stamp()}


@app.get("/species")
def species(limit: int = 200, cls: str | None = None) -> list[dict]:
    f = DATA / "species_winner.csv"
    if not f.exists():
        raise HTTPException(503, "catalog not exported yet")
    sus = DATA / "susceptibility.parquet"
    w = f"and lower(species) like '%{cls.lower()}%'" if cls else ""
    where = f"where 1=1 {w}" if w else ""
    if sus.exists():
        return q(f"select w.*, s.p_host, s.p05, s.p95, s.label as host_label "
                 f"from '{f}' w left join '{sus}' s "
                 f"on w.specieskey=s.specieskey {where} "
                 f"order by aic limit {limit}")
    return q(f"select * from '{f}' {where} order by aic limit {limit}")


@app.get("/susceptibility")
def susceptibility(top: int = 100) -> list[dict]:
    """PNAS-style P(host|env,geo,phy proximity to known H5N1 hosts)."""
    f = DATA / "susceptibility.parquet"
    if not f.exists():
        raise HTTPException(503, "susceptibility model not exported yet")
    return q(f"select * from '{f}' order by p_host desc limit {top}")


@app.get("/species/{key}/fit")
def species_fit(key: int) -> dict:
    f = DATA / "species_winner.csv"
    if not f.exists():
        raise HTTPException(503, "catalog not exported yet")
    rows = q(f"select * from '{f}' where specieskey={key}")
    if not rows:
        raise HTTPException(404, "species not in catalog")
    return rows[0]


@app.get("/risk/watershed")
def risk_watershed(top: int = 100) -> list[dict]:
    f = DATA / "risk_watershed.parquet"
    if not f.exists():
        raise HTTPException(503, "risk layer not exported yet")
    return q(f"select * from '{f}' order by risk desc limit {top}")


@app.get("/explain/{kind}/{ident}")
def explain(kind: str, ident: str) -> JSONResponse:
    """System-1 typed explanation via muse-spark (see agent/explain.py)."""
    from agent.explain import explain as do_explain  # agent pkg, not data

    if kind not in ("county", "watershed", "species"):
        raise HTTPException(400, "kind must be county|watershed|species")
    baked = DATA / f"explain_{kind}_{ident}.json"
    if baked.exists():
        return JSONResponse(json.loads(baked.read_text()))
    return JSONResponse(do_explain(kind, ident, data_dir=DATA))


@app.get("/briefing")
def briefing() -> JSONResponse:
    """System-2 nightly digest via muse-wonder (see agent/briefing.py)."""
    baked = DATA / "briefing.json"
    if baked.exists():
        return JSONResponse(json.loads(baked.read_text()))
    from agent.briefing import briefing as do_brief

    return JSONResponse(do_brief(data_dir=DATA))


STATIC = Path(os.environ.get("STATIC_DIR",
                             Path(__file__).resolve().parent.parent / "app"))
if STATIC.exists():
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="app")
