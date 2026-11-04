"""Fireworks SFT launch — wildseek-lora orchestrator on muse-glimmer-30b.

Worktree copy of wildseek-lora/scripts/fw_sft.py, reworked for direct
upload: gs/s3 billing is unavailable, so datasets are created as
userUploaded and the jsonl is POSTed to datasets/{id}:upload
(<=150MB). State lands next to this file (tools/fw_sft_state.json,
committed to night-shift); the source jsonl dir is passed explicitly
(read-only on the lora repo).

Usage:
    export FIREWORKS_API_KEY=$(cat ~/env/fireworks-token)
    python tools/fw_sft.py upload --data-dir /path/to/wildseek-lora/data
    python tools/fw_sft.py launch [--epochs 2] [--lora-rank 16]
    python tools/fw_sft.py status
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import httpx

ACCT = "alrobles"
BASE = f"https://api.fireworks.ai/v1/accounts/{ACCT}"
MODEL_BASE = "accounts/fireworks/models/muse-glimmer-30b"
OUT_MODEL = f"accounts/{ACCT}/models/wildseek-orch-v1"
DATASETS = {"wildseek-orch-train": "fw_all_train.jsonl",
            "wildseek-orch-val": "fw_all_val.jsonl"}
STATE = os.path.join(os.path.dirname(__file__), "fw_sft_state.json")


def h():
    return {"Authorization": f"Bearer {os.environ['FIREWORKS_API_KEY']}"}


def save(patch: dict) -> None:
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    st.update(patch)
    json.dump(st, open(STATE, "w"), indent=1)


def cmd_upload(data_dir: str) -> None:
    for ds_id, fname in DATASETS.items():
        path = os.path.join(data_dir, fname)
        n = sum(1 for _ in open(path))
        # recreate empty dataset entry, then upload the file content
        httpx.delete(f"{BASE}/datasets/{ds_id}", headers=h(), timeout=30)
        r = httpx.post(f"{BASE}/datasets", timeout=30,
                       headers={**h(), "Content-Type": "application/json"},
                       json={"datasetId": ds_id,
                             "dataset": {"userUploaded": {},
                                         "exampleCount": n,
                                         "format": "CHAT"}})
        print("create", ds_id, r.status_code, r.text[:160])
        if r.status_code != 200:
            continue
        with open(path, "rb") as fh:
            u = httpx.post(f"{BASE}/datasets/{ds_id}:upload", timeout=300,
                           headers=h(), files={"file": (fname, fh)})
        print("upload", ds_id, u.status_code, u.text[:160])


def cmd_launch(epochs: int, lora_rank: int) -> None:
    body = {"dataset": f"{BASE}/datasets/wildseek-orch-train",
            "evaluationDataset": f"{BASE}/datasets/wildseek-orch-val",
            "baseModel": MODEL_BASE,
            "outputModel": OUT_MODEL,
            "displayName": "wildseek-orch-v1",
            "loraRank": lora_rank,
            "epochs": epochs,
            "earlyStop": True,
            "maxContextLength": 4096}
    r = httpx.post(f"{BASE}/supervisedFineTuningJobs", timeout=60,
                   headers={**h(), "Content-Type": "application/json"},
                   json=body)
    print(r.status_code, r.text[:400])
    if r.status_code == 200:
        save({"job": r.json().get("name")})


def cmd_status() -> None:
    for ds_id in DATASETS:
        r = httpx.get(f"{BASE}/datasets/{ds_id}", headers=h(), timeout=30)
        if r.status_code == 200:
            d = r.json()
            print(ds_id, d.get("state"), d.get("exampleCount"))
        else:
            print(ds_id, r.status_code, r.text[:120])
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    job = st.get("job")
    if job:
        r = httpx.get(f"https://api.fireworks.ai/v1/{job}",
                      headers=h(), timeout=30)
        if r.status_code == 200:
            j = r.json()
            print("job:", j.get("state"), j.get("jobProgress"))
            for k in ("billedTokens", "cost", "estimatedCost"):
                if k in j:
                    print(f"{k}: {j[k]}")
        else:
            print("job get:", r.status_code, r.text[:150])


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("upload")
    d.add_argument("--data-dir", default="data",
                   help="local dir holding the jsonl")
    l = sub.add_parser("launch")
    l.add_argument("--epochs", type=int, default=2)
    l.add_argument("--lora-rank", type=int, default=16)
    sub.add_parser("status")
    a = ap.parse_args()
    {"upload": lambda: cmd_upload(a.data_dir),
     "launch": lambda: cmd_launch(a.epochs, a.lora_rank),
     "status": cmd_status}[a.cmd]()


if __name__ == "__main__":
    main()
