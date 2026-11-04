"""Exported species_winner.csv must not contain duplicate specieskeys.

Regression test for N1 (Perognathus merriami duplicated export row
inflated meta n_species to 1148). Runs against a synthetic tmp src —
no dependency on the gitignored data/ tree.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import export_serve  # noqa: E402


def test_export_dedupes_specieskeys(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    pd.DataFrame([
        {"specieskey": 1, "species": "A", "aic": 10.0},
        {"specieskey": 2439560, "species": "B", "aic": 5.0},
        {"specieskey": 2439560, "species": "B", "aic": 7.0},
    ]).to_csv(src / "species_winner.csv", index=False)
    export_serve.main(str(src), str(dst))
    out = pd.read_csv(dst / "species_winner.csv")
    assert len(out) == out["specieskey"].nunique() == 2
    assert float(out.loc[out["specieskey"] == 2439560, "aic"].iloc[0]) == 5.0
    meta = json.loads((dst / "meta.json").read_text())
    assert meta["n_species"] == 2


def test_export_huc8_centroids(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    gj = {"type": "FeatureCollection", "features": [{
        "type": "Feature", "properties": {"huc8": "01010002"},
        "geometry": {"type": "Polygon", "coordinates": [[
            [-70.0, 45.0], [-69.0, 45.0],
            [-69.0, 46.0], [-70.0, 46.0], [-70.0, 45.0]]]}}]}
    (src / "wbd_huc8_conus.geojson").write_text(json.dumps(gj))
    import export_serve  # noqa: E402 (already imported at module top)
    export_serve.main(str(src), str(dst))
    cent = json.loads((dst / "huc8_centroids.json").read_text())
    assert cent == {"01010002": {
        "lon": -69.5, "lat": 45.5,
        "bbox": [-70.0, 45.0, -69.0, 46.0]}}


def test_export_strips_fit_catalog_filename(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "fit_catalog.csv").write_text(
        "specieskey,species,filename\n1,A,/beegfs/u/x.csv\n")
    export_serve.main(str(src), str(dst))
    header = (dst / "fit_catalog.csv").read_text().splitlines()[0]
    assert "filename" not in header.split(",")
    assert "/beegfs/" not in (dst / "fit_catalog.csv").read_text()
