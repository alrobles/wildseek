"""Aggregate MetaClient ledger spend by provider into metrics.json.

Usage:
    .venv/bin/python tools/metrics_providers.py [metrics.json ...]

Adds/refreshes the `provider_usage` block from data/agent_calls.jsonl,
mapping model ids to providers via the price tables in
agent/meta_client.py (PRICES=meta, FW_PRICES=fireworks,
BASETEN_PRICES=baseten, muse-glimmer=local). Rows without a backend
field (pre-2026-11-04) are mapped by model id; rows with one use it.

Scope note: the ledger is cumulative (pipeline + ops/audit traffic
through MetaClient), so the block is labeled as such. Honest
provider proof for /metrics, not a per-run invoice.
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent.meta_client import (  # noqa: E402
    BASETEN_PRICES,
    FW_PRICES,
    PRICES,
)

MODEL_PROVIDER = {m: "meta" for m in PRICES}
MODEL_PROVIDER.update({m: "fireworks" for m in FW_PRICES})
MODEL_PROVIDER.update({m: "baseten" for m in BASETEN_PRICES})
MODEL_PROVIDER["muse-glimmer"] = "local-glimmer"


def aggregate(ledger: Path) -> dict:
    agg: dict[str, list] = defaultdict(lambda: [0, 0.0, set()])
    n = 0
    with open(ledger) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            n += 1
            prov = r.get("backend") or MODEL_PROVIDER.get(
                r.get("model", ""), "other")
            a = agg[prov]
            a[0] += 1
            a[1] += r.get("usd") or 0.0
            a[2].add(r.get("model", "?"))
    return {
        prov: {"calls": c, "usd": round(u, 4),
               "models": sorted(m)}
        for prov, (c, u, m) in sorted(agg.items())
    }, n


def main(paths: list[str]) -> None:
    by_prov, n = aggregate(ROOT / "data/agent_calls.jsonl")
    block = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "ledger_rows": n,
        "scope": ("cumulative MetaClient ledger "
                  "(pipeline + ops/audit traffic)"),
        "by_provider": by_prov,
    }
    for p in paths:
        mp = Path(p)
        d = json.loads(mp.read_text())
        d["provider_usage"] = block
        mp.write_text(json.dumps(d, indent=1) + "\n")
        print(f"{mp}: provider_usage from {n} ledger rows")


if __name__ == "__main__":
    args = sys.argv[1:] or ["data/serve/metrics.json",
                            "app/data.sample/metrics.json"]
    main(args)
