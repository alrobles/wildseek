"""dist_frame fail-closed: a frame built on <2 distance axes must refuse
to ship (no silent NaN->median->p_host training)."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import dist_frame  # noqa: E402


def _fixture(base: Path, axes=("env",)):
    uni = pd.DataFrame({"specieskey": [1, 2, 3, 4],
                        "species": ["Sp a", "Sp b", "Sp c", "Sp d"]})
    uni.to_csv(base / "species_winner.csv", index=False)
    pd.DataFrame({"specieskey": [1, 2]}).to_parquet(
        base / "host_labels.parquet", index=False)
    if "env" in axes:
        pd.DataFrame({"key_i": [1, 2, 1], "key_j": [2, 3, 4],
                      "j_env": [0.9, 0.4, 0.3]}).to_parquet(
            base / "jaccard_env.parquet", index=False)
    if "geo" in axes:
        pd.DataFrame({"key_i": [1, 3], "key_j": [2, 4],
                      "j_geo": [0.8, 0.5]}).to_parquet(
            base / "jaccard_geo.parquet", index=False)


def test_refuses_single_axis(tmp_path):
    _fixture(tmp_path, axes=("env",))
    with pytest.raises(SystemExit, match="REFUSING"):
        dist_frame.build(tmp_path, tmp_path / "out.parquet")


def test_refuses_no_axes(tmp_path):
    _fixture(tmp_path, axes=())
    with pytest.raises(SystemExit, match="REFUSING"):
        dist_frame.build(tmp_path, tmp_path / "out.parquet")


def test_two_axes_builds(tmp_path):
    _fixture(tmp_path, axes=("env", "geo"))
    frame = dist_frame.build(tmp_path, tmp_path / "out.parquet")
    assert frame.has_env.sum() > 0 and frame.has_geo.sum() > 0
    # self-pair excluded: a positive's own key never appears as neighbor
    assert (frame.min_d_phy_pos != 0).all()
