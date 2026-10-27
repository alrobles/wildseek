"""Nightly digest — muse-wonder (System-2) briefing over the catalog.

Reads the exported artifacts (species_winner, risk_watershed, decisions)
and asks wonder for a structured situation briefing: headline, hotspots,
watchlist, caveats. Runs locally or inside the container on demand.
"""

import json
import os
from pathlib import Path

from .meta_client import MetaClient, MODEL_SHOWCASE

BRIEF_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "wildseek_brief",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "headline": {"type": "string"},
                "hotspots": {"type": "array", "items": {"type": "string"},
                             "maxItems": 5},
                "watchlist": {"type": "array", "items": {"type": "string"},
                              "maxItems": 5},
                "methods_note": {"type": "string"},
            },
            "required": ["headline", "hotspots", "watchlist", "methods_note"],
            "additionalProperties": False,
        },
    },
}

PROMPT = """You are the WildSeek situation analyst. Given these JSON facts from
tonight's avian-influenza wildlife susceptibility run (xnicher ellipsoid
models over ERA5 bioclim normals, M = 95% ecoregions, APHIS wild-bird
detections rasterized to 1/120-degree recency kernel and aggregated to
HUC8 watersheds), write a briefing. Hotspots: name the top watersheds with
state codes. Watchlist: species or pipeline caveats worth flagging.
Keep each field under 40 words. Facts:
{facts}"""


def briefing(client: MetaClient | None = None,
             data_dir: Path | str = "data/serve",
             model: str = MODEL_SHOWCASE) -> dict:
    import duckdb

    client = client or MetaClient()
    data = Path(os.environ.get("DATA_DIR", data_dir))
    con = duckdb.connect()
    facts: dict = {}

    w = data / "species_winner.csv"
    if w.exists():
        facts["catalog"] = con.execute(
            f"""select count(*) n, min(aic) best_aic
                from '{w}'""").fetchone()
        facts["top_pairs"] = con.execute(
            f"""select best_temp||' x '||best_prec pair, count(*) n
                from '{w}' group by 1 order by 2 desc limit 5""").fetchall()

    r = data / "risk_watershed.parquet"
    if r.exists():
        facts["top_watersheds"] = con.execute(
            f"""select name, states, round(risk,3) risk, n_det
                from '{r}' order by risk desc limit 8""").fetchall()

    dec = data / "decisions_all.jsonl"
    if dec.exists():
        decs = [json.loads(l) for l in dec.read_text().splitlines()]
        from collections import Counter
        facts["t1_decisions"] = dict(Counter(d["decision"] for d in decs))
        flagged = [d["species"] for d in decs
                   if d["decision"] != "accept"][:10]
        facts["flagged_species"] = flagged
    con.close()

    r = client.chat(
        model=model,
        messages=[{"role": "user",
                   "content": PROMPT.format(facts=json.dumps(facts)[:6000])}],
        response_format=BRIEF_SCHEMA,
    )
    out = json.loads(r["choices"][0]["message"]["content"])
    out["facts"] = facts
    out["model"] = model
    return out
