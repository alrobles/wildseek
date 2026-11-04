"""SPEC + JUDGE math for the subsampling experiment (synthetic, no R)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import subsample_spec as spec
import subsample_judge as judge


def test_seeds_deterministic_and_small():
    a = spec.occ_seed(2432314, 5, 2, 3)
    assert a == spec.occ_seed(2432314, 5, 2, 3)
    assert 0 <= a < 2**31
    assert spec.occ_seed(2432314, 5, 2, 4) != a
    assert spec.opt_seed(2432314, 0) == (2432314 % 1000000) * 89 + 1


def test_select_top_per_class():
    pool = pd.DataFrame({"specieskey": [1, 2, 3, 4],
                         "species": list("abcd"),
                         "class_": ["Aves", "Aves", "Mammalia", "Mammalia"]})
    counts = pd.DataFrame({"specieskey": [1, 2, 3, 4],
                           "n_cells_global": [50, 500, 300, 90]})
    sel = spec.select(pool, counts, per_class=1, min_n=100, max_level=100)
    assert set(sel.specieskey) == {2, 3}


def test_build_tasks_shape():
    sp = pd.DataFrame({"specieskey": [7], "species": ["x"],
                       "class_": ["Aves"]})
    t = spec.build_tasks(sp, levels=[10, 20], reps=2)
    assert len(t) == 88 * (1 + 2 * 2)
    assert t.is_full.sum() == 88
    # one full row per pair, opt_seed == campaign scheme
    full = t[t.is_full].sort_values("pair_idx")
    assert list(full.seed) == [spec.opt_seed(7, i) for i in range(88)]


def test_score_known_geometry():
    df = pd.DataFrame([
        {"specieskey": 1, "pair_idx": 0, "is_full": True, "mu1": 0.0,
         "mu2": 0.0, "s11": 1.0, "s12": 0.0, "s22": 1.0, "logdet": 0.0,
         "flag": "accepted_global", "n_level": 0, "temp": "bio01",
         "prec": "bio12"},
        {"specieskey": 1, "pair_idx": 0, "is_full": False, "mu1": 3.0,
         "mu2": 4.0, "s11": 4.0, "s12": 0.0, "s22": 4.0,
         "logdet": float(np.log(16.0)), "flag": "accepted_global",
         "n_level": 30, "temp": "bio01", "prec": "bio12"},
    ])
    sub = judge.score(df)
    assert abs(sub.d_maha.iloc[0] - 5.0) < 1e-9
    assert abs(sub.vol_ratio.iloc[0] - 4.0) < 1e-9


def test_n_min_interpolation():
    cur = pd.DataFrame({
        "variable": ["bio01"] * 3, "n_level": [10, 20, 40],
        "med_dmaha": [2.0, 1.0, 0.2], "q25_dmaha": [1.5, 0.8, 0.1],
        "q75_dmaha": [2.5, 1.2, 0.3], "med_vol": [1.0, 1.0, 1.0],
        "n": [5, 5, 5]})
    nm = judge.n_min(cur)
    # eps=0.5: between (20,1.0) and (40,0.2) -> 20 + .5*20/.8 = 32.5
    assert abs(nm["nmin_0.5"].iloc[0] - 32.5) < 1e-9
    assert nm["nmin_1.0"].iloc[0] == 20.0  # 1.0 not < 1.0 -> interp. to 20
