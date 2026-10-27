"""Sub-county HPAI risk surface (1/120-deg CONUS raster).

risk_cell = recency-weighted detection density (Gaussian kernel over
HPAI-positive wild-bird detections) x susceptible-species suitability
sum (once the suitability stack exists). Output is continuous at
1/120 deg — strictly finer than county; county/FIPS aggregates are
derived, not primary.

Inputs:
  aphis_wild_birds.parquet  (local fetch, has lat/lon + date + result)
  env_conus_normals_1120.tif (grid definition)
  suit_stack (optional: dir of per-species suitability parquet/tif)

Runs under SLURM (grid math, not login node).
"""

import os

import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import gaussian_filter

OUT = "/beegfs/a474r867/meta-hack"
HALF_LIFE_D = 90.0          # detection recency half-life (days)
SIGMA_CELLS = 12.0          # ~10 km at 1/120 deg


def main() -> None:
    det = pd.read_parquet(f"{OUT}/aphis_wild_birds.parquet")
    det = det[det["pathogenicity"] == "High Path AI"].dropna(
        subset=["lat", "lon"])
    det["date_collected"] = pd.to_datetime(det["date_collected"])
    age = (det["date_collected"].max() - det["date_collected"]).dt.days
    det["w"] = 0.5 ** (age / HALF_LIFE_D)

    with rasterio.open(f"{OUT}/env_conus_normals_1120.tif") as r:
        tr, H, W = r.transform, r.height, r.width
        nodata_mask = ~np.isfinite(r.read(1))
    col = ((det["lon"] - tr.c) / tr.a).astype(int)
    row = ((det["lat"] - tr.f) / tr.e).astype(int)
    ok = (row >= 0) & (row < H) & (col >= 0) & (col < W)
    surf = np.zeros((H, W), np.float32)
    np.add.at(surf, (row[ok], col[ok]), det["w"].to_numpy()[ok])
    surf = gaussian_filter(surf, SIGMA_CELLS)
    surf[nodata_mask] = np.nan
    if np.nanmax(surf) > 0:
        surf = surf / np.nanmax(surf)          # 0-1 detection pressure

    np.save(f"{OUT}/risk_detect_1120.npy", surf.astype(np.float32))
    prof = dict(driver="GTiff", height=H, width=W, count=1,
                dtype="float32", crs="EPSG:4326", transform=tr,
                nodata=np.nan, compress="deflate")
    with rasterio.open(f"{OUT}/risk_detect_1120.tif", "w", **prof) as d:
        d.write(surf, 1)
    print("risk_detect_1120:", int(ok.sum()), "detections rasterized,",
          "max", float(np.nanmax(surf)))

    # Stage 2: mean suitability across Aves winners -> risk x susceptibility
    win = pd.read_csv(f"{OUT}/species_winner.csv")
    pool = pd.read_csv(f"{OUT}/pool_flagship.csv")
    aves = set(pool.loc[pool["class"] == "Aves", "specieskey"])
    wins = [k for k in win["specieskey"] if k in aves]
    acc = np.zeros((H, W), np.float64)
    n = 0
    for k in wins:
        p = f"{OUT}/suit/suit_{k}.tif"
        if not os.path.exists(p):
            continue
        with rasterio.open(p) as ds:
            a = ds.read(1)
            if a.shape != (H, W):
                continue
            acc += np.where(np.isfinite(a), a, 0)
            n += 1
    if n:
        mean_suit = (acc / n).astype(np.float32)
        risk = surf * mean_suit
        if np.nanmax(risk) > 0:
            risk = risk / np.nanmax(risk)
        np.save(f"{OUT}/mean_suit_aves_1120.npy", mean_suit)
        with rasterio.open(f"{OUT}/risk_1120.tif", "w", **prof) as d:
            d.write(risk.astype(np.float32), 1)
        print("risk_1120:", n, "aves suit layers averaged; max",
              float(np.nanmax(risk)))


if __name__ == "__main__":
    main()
