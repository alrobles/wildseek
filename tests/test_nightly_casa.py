"""Casa mode: the nightly factory runs without the HPC cluster.

No ssh/sbatch/sacct anywhere in the casa stage set; text/vector layers
refresh locally while rasters stay frozen.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import nightly  # noqa: E402


def test_plan_hpc_unchanged():
    assert nightly.plan_stages({"refit": False}, casa=False,
                               dry=False) == [
        "entrada", "spec", "builder", "approver", "produccion",
        "briefing", "brain"]
    assert nightly.plan_stages({"refit": True}, casa=False,
                               dry=False) == [
        "entrada", "spec", "refit", "builder", "approver",
        "produccion", "briefing", "brain"]


def test_plan_casa_swaps_hpc_stages():
    assert nightly.plan_stages({"refit": False}, casa=True,
                               dry=False) == [
        "entrada", "spec", "builder_casa", "approver_casa",
        "produccion", "briefing", "brain_casa"]
    assert nightly.plan_stages({"refit": True}, casa=True,
                               dry=False) == [
        "entrada", "spec", "refit_casa", "builder_casa",
        "approver_casa", "produccion", "briefing", "brain_casa"]


def test_refit_casa_no_ssh(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(nightly, "ROOT", tmp_path)
    monkeypatch.setattr(nightly, "sh",
                        lambda cmd, **kw: calls.append(cmd) or "")
    man = {"casa": True, "stages": {}}
    nightly.STAGE_FNS["refit_casa"](man)
    assert calls, "refit_casa ran nothing"
    assert all("ssh " not in c and "scp " not in c and "sbatch" not in c
               for c in calls)
    assert any("species_labels" in c for c in calls)
    assert any("dist_frame" in c for c in calls)
    assert any("suscept_model" in c for c in calls)


def test_plan_dry():
    assert nightly.plan_stages({}, casa=False, dry=True) == [
        "entrada", "spec", "brain"]
    assert nightly.plan_stages({}, casa=True, dry=True) == [
        "entrada", "spec", "brain_casa"]


def test_builder_casa_needs_seed(tmp_path, monkeypatch):
    monkeypatch.setattr(nightly, "ROOT", tmp_path)  # no app/data seed
    man = {"casa": True, "stages": {}}
    try:
        nightly.STAGE_FNS["builder_casa"](man)
    except RuntimeError as ex:
        assert "seed" in str(ex).lower()
    else:
        raise AssertionError("builder_casa ran without a seed snapshot")


def test_builder_casa_no_ssh(tmp_path, monkeypatch):
    seed = tmp_path / "app" / "data"
    seed.mkdir(parents=True)
    (seed / "meta.json").write_text("{}")
    calls = []
    monkeypatch.setattr(nightly, "ROOT", tmp_path)
    monkeypatch.setattr(nightly, "sh",
                        lambda cmd, **kw: calls.append(cmd) or "")
    man = {"casa": True, "stages": {}}
    nightly.STAGE_FNS["builder_casa"](man)
    assert calls, "builder_casa ran nothing"
    assert all("ssh " not in c and "sbatch" not in c and "sacct" not in c
               for c in calls)
    assert any("export_serve" in c for c in calls)
    assert any("metrics_providers" in c for c in calls)
