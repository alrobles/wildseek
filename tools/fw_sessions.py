#!/usr/bin/env python3
"""List or expire Fireworks TrainingSessions on this account.

Serverless LoRA allows ONE concurrent run per base model
(muse-glimmer-30b). A launcher that dies between session-create and
session-close leaves an orphan ts-* holding the slot; the next launch
429s on models.create ("in use 1, limit 1") until the orphan's TTL
expires. This tool lists sessions (state + createTime) and can DELETE
a session by id to free the slot immediately.

Only delete sessions that are (a) state!=EXPIRED and (b) known-orphaned
(no local launcher alive, no promotable work). A promoted model
survives session deletion; session-only checkpoints do not.

Usage:
  tools/fw_sessions.py list
  tools/fw_sessions.py delete ts-<id> [<id>...]
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://api.fireworks.ai"
ACCOUNT = os.environ.get("FIREWORKS_ACCOUNT", "alrobles")


def _key() -> str:
    key = os.environ.get("FIREWORKS_API_KEY")
    if key:
        return key
    with open(os.path.expanduser("~/env/fireworks-token")) as f:
        return f.read().strip()


def _req(method: str, path: str):
    req = urllib.request.Request(
        BASE + path, method=method, headers={"Authorization": f"Bearer {_key()}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read()[:300].decode()}


def cmd_list() -> int:
    code, body = _req("GET", f"/v1/accounts/{ACCOUNT}/trainingSessions?pageSize=50")
    if code != 200:
        print(code, body)
        return 1
    for s in body.get("trainingSessions", []):
        print(f"{s.get('name')}  {s.get('state')}  {s.get('createTime')}")
    return 0


def cmd_delete(ids: list[str]) -> int:
    rc = 0
    for sid in ids:
        name = sid if sid.startswith("accounts/") else f"accounts/{ACCOUNT}/trainingSessions/{sid}"
        code, body = _req("DELETE", "/v1/" + name)
        print("DELETE", name, "->", code, body if code != 200 else "")
        rc |= code != 200
    return rc


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "delete"):
        sys.exit(__doc__)
    sys.exit(cmd_list() if sys.argv[1] == "list" else cmd_delete(sys.argv[2:]))
