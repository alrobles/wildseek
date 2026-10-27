"""Export monitor layers to the app's static serve dir.

Packs the DuckDB/parquet catalog into the formats app/ expects:
  data/serve/meta.json             counts + build stamp
  data/serve/species_winner.csv    catalog table
  data/serve/risk_watershed.geojson  choropleth (from risk raster, county agg)
  data/serve/detections.geojson    HPAI positive points (recent)
  data/serve/flyways.geojson       flyway polylines
  data/serve/fit_catalog.csv       full pair table (for /explain)

Runs locally against the exported artifact copies (or on cluster with
--src pointing at the beegfs dir; outputs are small).
"""

import argparse
import json
import time
from pathlib import Path

import duckdb
import pandas as pd


def main(src: str, dst: str) -> None:
    con = duckdb.connect()
    con.execute("PRAGMA threads=4")
    d = Path(dst)
    d.mkdir(parents=True, exist_ok=True)

    for name in ("fit_catalog.csv", "risk_watershed.parquet",
                 "decisions_all.jsonl", "decisions_delta.csv"):
        p = Path(src) / name
        if p.exists():
            (d / name).write_bytes(p.read_bytes())

    # species_winner.csv: merge tail-decision drops/review flag when the
    # delta exists (decide_tail writes to dst; re-export must not lose it)
    win = Path(src) / "species_winner.csv"
    if win.exists():
        w = pd.read_csv(win)
        dl = d / "decisions_delta.csv"
        if dl.exists():
            delta = pd.read_csv(dl)
            w["review"] = w["specieskey"].isin(
                delta.loc[delta["decision"] == "flag_review", "specieskey"])
            drops = set(delta.loc[delta["decision"] == "drop", "specieskey"])
            w = w[~w["specieskey"].isin(drops)]
        w.to_csv(d / "species_winner.csv", index=False)

    det = Path(src) / "aphis_wild_birds.parquet"
    if det.exists():
        rows = con.execute(
            f"""select lon, lat, state, county, watershed, date_collected
                from '{det}' where pathogenicity='High Path AI'
                  and lat is not null"""
        ).fetchall()
        feats = [{"type": "Feature",
                  "properties": {"state": r[2], "county": r[3],
                                 "watershed": r[4], "date": str(r[5])},
                  "geometry": {"type": "Point",
                               "coordinates": [r[0], r[1]]}}
                 for r in rows]
        (d / "detections.geojson").write_text(json.dumps(
            {"type": "FeatureCollection", "features": feats}))
        print("detections:", len(feats))

    fly = Path(src) / "aphis_flyways.json"
    if fly.exists():
        feats = json.loads(fly.read_text())
        gj = {"type": "FeatureCollection", "features": [
            {"type": "Feature",
             "properties": f.get("attributes", {}),
             "geometry": {"type": "MultiPolygon",
                          "coordinates": [f.get("geometry", {}).get("rings", [])]}}
            for f in feats]}
        out = d / "flyways.geojson"
        out.write_text(json.dumps(gj))
        assert out.stat().st_size > 1_000_000 and \
            all(f["geometry"]["coordinates"][0] for f in gj["features"]), \
            "flyways export produced empty geometries"

    meta = {
        "built": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "n_detections": None,
    }
    if det.exists():
        meta["n_detections"] = con.execute(
            f"select count(*) from '{det}' where pathogenicity='High Path AI'"
        ).fetchone()[0]

    for png in Path(src).glob("*.png"):
        (d / png.name).write_bytes(png.read_bytes())
        mj = Path(str(png) + ".meta.json")
        if mj.exists():
            m = json.loads(mj.read_text())
            meta[png.stem + "_png"] = png.name
            meta[png.stem + "_bbox"] = m["bbox"]

    suits = list(Path(src).glob("suit_*.png"))
    suits += list((Path(src) / "suit_png").glob("suit_*.png"))
    meta["n_species"] = len(suits) or None
    if suits:
        mj = Path(str(suits[0]) + ".meta.json")
        if mj.exists():
            meta["suit_bbox"] = json.loads(mj.read_text())["bbox"]
        for s in suits:
            (d / s.name).write_bytes(s.read_bytes())
            sm = Path(str(s) + ".meta.json")
            if sm.exists():
                (d / (s.name + ".meta.json")).write_bytes(sm.read_bytes())

    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    print("exported to", d)
    con.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--src", default="data")
    p.add_argument("--dst", default="app/data")
    a = p.parse_args()
    main(a.src, a.dst)
