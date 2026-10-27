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

    meta = {
        "built": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "n_detections": None,
    }

    # species-level detections preferred; site-level as fallback
    det_sp = Path(src) / "aphis_wild_birds_species.parquet"
    det = Path(src) / "aphis_wild_birds.parquet"
    if det_sp.exists():
        rows = con.execute(
            f"""select lon, lat, state, county, bird_species, hpai_strain,
                       date_detected
                from '{det_sp}' where lat is not null"""
        ).fetchall()
        feats = [{"type": "Feature",
                  "properties": {"state": r[2], "county": r[3],
                                 "species": r[4], "strain": r[5],
                                 "date": str(r[6]),
                                 "year": int(str(r[6])[:4]) if r[6] else None},
                  "geometry": {"type": "Point",
                               "coordinates": [r[0], r[1]]}}
                 for r in rows]
        (d / "detections.geojson").write_text(json.dumps(
            {"type": "FeatureCollection", "features": feats}))
        meta["n_detections"] = len(feats)
    elif det.exists():
        rows = con.execute(
            f"""select lon, lat, state, county, watershed, date_collected
                from '{det}' where pathogenicity='High Path AI'
                  and lat is not null"""
        ).fetchall()
        feats = [{"type": "Feature",
                  "properties": {"state": r[2], "county": r[3],
                                 "watershed": r[4], "date": str(r[5]),
                                 "year": int(str(r[5])[:4]) if r[5] else None},
                  "geometry": {"type": "Point",
                               "coordinates": [r[0], r[1]]}}
                 for r in rows]
        (d / "detections.geojson").write_text(json.dumps(
            {"type": "FeatureCollection", "features": feats}))
        meta["n_detections"] = len(feats)

    sus = Path(src) / "susceptibility.parquet"
    if sus.exists():
        (d / "susceptibility.parquet").write_bytes(sus.read_bytes())
        meta["n_susceptibility"] = len(pd.read_parquet(sus))

    pl = Path(src) / "aphis_poultry.parquet"
    if pl.exists():
        rows = con.execute(
            f"""select lon, lat, state, county, production,
                       birds_affected, confirmed
                from '{pl}' where lat is not null"""
        ).fetchall()
        feats = [{"type": "Feature",
                  "properties": {"state": r[2], "county": r[3],
                                 "production": r[4],
                                 "birds_affected": float(r[5]),
                                 "confirmed": str(r[6])},
                  "geometry": {"type": "Point",
                               "coordinates": [r[0], r[1]]}}
                 for r in rows]
        (d / "poultry.geojson").write_text(json.dumps(
            {"type": "FeatureCollection", "features": feats}))

    ce = Path(src) / "county_exposure.geojson"
    if ce.exists():
        (d / "county_exposure.geojson").write_bytes(ce.read_bytes())
        n = len(json.loads(ce.read_text())["features"])
        meta["n_exposure_counties"] = n
        print("exposure counties:", n)

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
