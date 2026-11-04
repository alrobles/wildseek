"""HPAI Wildlife Monitor API — FastAPI + DuckDB over the parquet catalog.

Serves the ecoseek-style monitor: species susceptibility catalog,
per-species fit + suitability links, sub-county risk (watershed), and
the /explain endpoint (muse-spark narrative, System-1 typed).

Run:  DATA_DIR=/srv/hpai uvicorn api.main:app --port 8100
DATA_DIR holds the exported artifacts (GeoParquet / CSV / COG / PMTiles)
synced from the cluster staging dir ($WILDSEEK_BEEG on the HPC side).
"""

import json
import os
import re
import stat
import sys
from mimetypes import guess_type
from pathlib import Path

import anyio
import duckdb
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import Headers
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import FileResponse

DATA = Path(os.environ.get("DATA_DIR", "app/data"))

app = FastAPI(title="WildSeek", version="0.1.0")


class _NoPathsend:
    # Uvicorn's httptools impl negotiates http.response.pathsend (sendfile);
    # those bodies bypass response middleware entirely, so the 18 MB
    # flyways.geojson would stay uncompressed on prod. Strip the extension
    # and FileResponse falls back to chunked sends, which gzip sees.
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            scope.get("extensions", {}).pop("http.response.pathsend", None)
        await self.app(scope, receive, send)


app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=6)
app.add_middleware(_NoPathsend)


class _Precompressed(StaticFiles):
    # export_serve writes <file>.gz siblings for the heavy text
    # artifacts; serving them verbatim moves the compress cost off the
    # request path (a compresslevel=6 scan over 18 MB per hit). The
    # GZip middleware passes responses that already carry
    # Content-Encoding straight through.
    async def get_response(self, path, scope):
        if scope["method"] in ("GET", "HEAD") and \
                "gzip" in Headers(scope=scope).get("accept-encoding", ""):
            try:
                full, st = await anyio.to_thread.run_sync(
                    self.lookup_path, path + ".gz")
            except (OSError, ValueError):
                st = None
            if st is not None and stat.S_ISREG(st.st_mode):
                return FileResponse(
                    full, stat_result=st, media_type=guess_type(path)[0],
                    headers={"content-encoding": "gzip",
                             "vary": "Accept-Encoding"})
        return await super().get_response(path, scope)


_BAKED: dict[Path, tuple[tuple[int, int], object]] = {}
_MISSING = object()


def _baked(f: Path, load):
    """Cached load of a baked export artifact keyed on (mtime_ns, size).

    Export rewrites these files in place per data drop, so the stat key
    invalidates itself; stat-before-load can at worst cache bytes under
    a pre-write stamp, which the next stat already misses. Returns
    _MISSING when the file isn't there — callers keep their own
    503/fallback semantics.
    """
    try:
        st = f.stat()
    except OSError:
        return _MISSING
    key = (st.st_mtime_ns, st.st_size)
    hit = _BAKED.get(f)
    if hit is None or hit[0] != key:
        try:
            obj = load(f)
        except OSError:
            return _MISSING
        hit = (key, obj)
        _BAKED[f] = hit
    return hit[1]


def _json_file(f: Path):
    return json.loads(f.read_text())


def q(sql: str) -> list[dict]:
    # fresh connection per query: DuckDB connections are not thread-safe
    # and FastAPI runs sync endpoints on a threadpool
    c = duckdb.connect()
    c.execute("PRAGMA threads=4")
    try:
        return c.execute(sql).fetchdf().to_dict("records")
    except Exception as ex:
        print(f"catalog query failed: {ex!r}", file=sys.stderr)
        raise HTTPException(503, "catalog query failed")
    finally:
        c.close()


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
def species(limit: int = Query(200, ge=1, le=2000),
            cls: str | None = None) -> list[dict]:
    f = DATA / "species_winner.csv"
    if not f.exists():
        raise HTTPException(503, "catalog not exported yet")
    sus = DATA / "susceptibility.parquet"
    esc = cls.lower().replace("'", "''") if cls else ""
    w = f"and lower(species) like '%{esc}%'" if esc else ""
    where = f"where 1=1 {w}" if w else ""
    if sus.exists():
        return q(f"select w.*, s.p_host, s.p05, s.p95, s.label as host_label "
                 f"from '{f}' w left join '{sus}' s "
                 f"on w.specieskey=s.specieskey {where} "
                 f"order by aic limit {limit}")
    return q(f"select * from '{f}' {where} order by aic limit {limit}")


@app.get("/susceptibility")
def susceptibility(top: int = Query(100, ge=1, le=1000)) -> list[dict]:
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
def risk_watershed(top: int = Query(100, ge=1, le=1000)) -> list[dict]:
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
    # ident feeds both SQL filters and the baked-file path — whitelist it.
    # The regex allows dots/spaces, so reject ".." segments explicitly.
    if not re.fullmatch(r"[A-Za-z0-9_ .-]+", ident) or ".." in ident:
        raise HTTPException(400, "bad ident")
    obj = _baked(DATA / f"explain_{kind}_{ident}.json", _json_file)
    if obj is not _MISSING:
        return JSONResponse(obj)
    return JSONResponse(do_explain(kind, ident, data_dir=DATA))


@app.get("/litmine")
def litmine() -> JSONResponse:
    """Litmine loop ticker: papers -> chunks -> YES -> edges."""
    obj = _baked(DATA / "litmine_ticker.json", _json_file)
    if obj is _MISSING:
        raise HTTPException(503, "litmine ticker not exported yet")
    return JSONResponse(obj)


@app.get("/metrics")
def metrics() -> JSONResponse:
    """Baked run metrics: CV AUC, edge counts, model-cascade cost."""
    obj = _baked(DATA / "metrics.json", _json_file)
    if obj is _MISSING:
        raise HTTPException(503, "metrics not exported yet")
    return JSONResponse(obj)


@app.get("/we-called-it")
def we_called_it() -> JSONResponse:
    """Frozen prospective predictions: top unlabeled species by p_host,
    dated; confirmed when a post-freeze PMID names the species."""
    obj = _baked(DATA / "we_called_it.json", _json_file)
    if obj is _MISSING:
        raise HTTPException(503, "predictions not frozen yet")
    return JSONResponse(obj)


def _decisions_payload(f: Path) -> dict:
    import pandas as pd
    d = pd.read_csv(f).astype(object).where(pd.notna, None)
    return {"rows": d.to_dict("records"),
            "counts": d["decision"].value_counts().to_dict(),
            "switches": int((d["switch_to"].fillna("none") != "none").sum()),
            "refit_queue": "data/refit_queue.csv"}


@app.get("/decisions")
def decisions() -> JSONResponse:
    """Campaign decision delta: per-species accept/flag_review/drop +
    the executable switch_to column (drives the refit queue)."""
    obj = _baked(DATA / "decisions_delta.csv", _decisions_payload)
    if obj is _MISSING:
        raise HTTPException(503, "decision delta not exported yet")
    return JSONResponse(obj)


@app.get("/briefing")
def briefing() -> JSONResponse:
    """System-2 nightly digest via muse-wonder (see agent/briefing.py)."""
    obj = _baked(DATA / "briefing.json", _json_file)
    if obj is not _MISSING:
        return JSONResponse(obj)
    from agent.briefing import briefing as do_brief

    return JSONResponse(do_brief(data_dir=DATA))


STATIC = Path(os.environ.get("STATIC_DIR",
                             Path(__file__).resolve().parent.parent / "app"))
if STATIC.exists():
    app.mount("/", _Precompressed(directory=STATIC, html=True), name="app")
