"""Materialize APHIS HPAI layers to parquet for the risk surface.

Pulls the full wild-bird surveillance table (174k records, incl.
Watershed field = sub-county resolution) + livestock events +
flyways into data/ as parquet. API fetch — runs locally, not on HPC.
"""

import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import aphis  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    import pandas as pd

    OUT.mkdir(exist_ok=True)

    birds = [dataclasses.asdict(d)
                 for d in aphis.wild_bird_detections(hpai_only=False)]
    df = pd.DataFrame(birds)
    df.to_parquet(OUT / "aphis_wild_birds.parquet", index=False)
    print("wild_birds:", len(df),
          "| hpai:", int(df["pathogenicity"].eq("High Path AI").sum()))

    stock = [dataclasses.asdict(e) for e in aphis.livestock_events()]
    df2 = pd.DataFrame(stock)
    df2.to_parquet(OUT / "aphis_livestock.parquet", index=False)
    print("livestock:", len(df2))

    fly = aphis.flyways()
    (OUT / "aphis_flyways.json").write_text(json.dumps(fly))
    print("flyways:", len(fly))


if __name__ == "__main__":
    main()
