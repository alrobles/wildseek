"""Literature-mining driver: OpenAlex -> Muse Spark extraction -> host list.

    cd meta-hack
    export MODEL_API_KEY="$(cat ~/env/meta-key)"
    python -m agent.run_mine --query '"Cochliomyia hominivorax" host' --limit 25
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .meta_client import MetaClient, MODEL_EXTRACTION
from .lit_search import search
from .extract import extract_batch
from .host_list import HostList
from .resolve import resolve_host_list

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "host_list.jsonl"

PARASITE = "Cochliomyia hominivorax"
PARASITE_COMMON = "New World screwworm, screwworm, gusano barrenado"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", default=f'"{PARASITE}" host OR "screwworm" mammal')
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--min-year", type=int, default=None)
    ap.add_argument("--model", default=MODEL_EXTRACTION)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--rpm", type=int, default=120)
    ap.add_argument("--no-resolve", action="store_true",
                    help="skip GBIF taxonomic resolution")
    args = ap.parse_args(argv)

    print(f"Searching OpenAlex: {args.query!r} (limit {args.limit})")
    works = search(args.query, limit=args.limit, min_year=args.min_year)
    n_abs = sum(1 for w in works if w.abstract)
    print(f"  {len(works)} works, {n_abs} with abstracts")

    client = MetaClient()
    ev = extract_batch(
        client, works, PARASITE, PARASITE_COMMON,
        model=args.model, rpm=args.rpm,
    )
    print(f"Extracted {len(ev)} evidence records")

    hosts = HostList.load(args.out)
    before = len(hosts.entries)
    new, added = hosts.merge_many(ev)
    if not args.no_resolve and hosts.entries:
        print("Resolving host names via GBIF...")
        print(f"  {resolve_host_list(hosts)}")
    hosts.save(args.out)
    print(f"Host list: {before} -> {len(hosts.entries)} entries "
          f"({new} new hosts, {added} new evidence) -> {args.out}")
    print("\nSpend:")
    print(client.spend.report())
    return 0


if __name__ == "__main__":
    sys.exit(main())
