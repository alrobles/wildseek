"""CONUS 30-yr bioclim normals at 1/120 deg from publish/_YYYY_split.

Reads the per-var global 1/120-deg GeoTIFFs windowed to the lower-48
bbox, accumulates 1996-2025 means per cell, writes:
  env_conus_normals_1120.tif    19-band float32 GeoTIFF (predict input)
  env_conus_normals_1120.parquet  cell-level table (DuckDB joins)

Grid: 0.0083333 deg, x from -180.0001 (global product) — CONUS window
lon [-125,-66], lat [24,49.5] => ~7080x3060 px. NaN stays NaN.
Runs under SLURM.
"""

import glob
import os
import numpy as np
import rasterio
from rasterio.windows import from_bounds

SRC = "/beegfs/a474r867/era5_bioclim/publish/_{y}_split/bio{v:02d}_{y}.tif"
OUT = "/beegfs/a474r867/meta-hack"
YEARS = range(1996, 2026)
LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = -125.0, -66.0, 24.0, 49.5


def window_for(ref_path: str):
    with rasterio.open(ref_path) as r:
        w = from_bounds(LON_MIN, LAT_MIN, LON_MAX, LAT_MAX, r.transform)
        w = w.round_offsets().round_lengths()
        tr = r.window_transform(w)
        return w, tr, r.height, r.width


def main() -> None:
    acc = None
    win = tr = None
    for y in YEARS:
        for v in range(1, 20):
            f = SRC.format(y=y, v=v)
            if not os.path.exists(f):
                continue
            if win is None:
                win, tr, H, W = window_for(f)
                acc = np.zeros((19, win.height, win.width), np.float64)
                cnt = np.zeros((win.height, win.width), np.int32)
            with rasterio.open(f) as r:
                arr = r.read(1, window=win)
            ok = np.isfinite(arr)
            acc[v - 1][ok] += arr[ok]
            cnt[ok] += 1
        print("year", y, "done", flush=True)
    with np.errstate(invalid="ignore"):
        mean = (acc / cnt[None]).astype(np.float32)
    profile = dict(
        driver="GTiff", height=win.height, width=win.width, count=19,
        dtype="float32", crs="EPSG:4326", transform=tr,
        nodata=np.nan, compress="deflate",
    )
    tif = f"{OUT}/env_conus_normals_1120.tif"
    with rasterio.open(tif, "w", **profile) as dst:
        dst.write(mean)
        dst.descriptions = tuple(f"bio{i:02d}" for i in range(1, 20))
    print("wrote", tif, mean.shape)


if __name__ == "__main__":
    main()
