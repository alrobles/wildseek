"""interactions.parquet — unified parasite<->host edge table (G2/M10).

Merges every mined edge source into one normalized schema with
provenance; name-level edges (fulltext) keep their surface names,
taxid edges keep both taxid + resolved texts. `verified` flags the
glimmer-JUDGE pass — downstream should filter verified==True for the
high-precision graph.

    python litmine/build_interactions.py
    -> data/litmine/interactions.parquet + prints pair stats
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from leakage_audit import norm_name  # noqa: E402

LIT = "data/litmine"
SOURCES = [
    ("edges_zover.csv", "zover-abstract"),
    ("edges_gold33.csv", "gold33-abstract"),
    ("edges_fulltext.csv", "gold33-fulltext"),
    ("edges_zover_full.csv", "zover-fulltext"),
]


def load(path: Path, source: str) -> pd.DataFrame:
    e = pd.read_csv(path)
    e["pmid"] = e["pmid"].astype(str).str.replace(r"\.0$", "", regex=True)
    for c in ("confidence", "parasite_taxid", "host_taxid"):
        if c in e.columns:
            e[c] = pd.to_numeric(e[c], errors="coerce")
    e["source"] = source
    # unify name fields: fulltext uses parasite/host; taxid files use
    # para_texts/host_texts (semicolon lists — first entry is canonical)
    if "parasite" not in e.columns:
        e["parasite"] = (e.get("para_texts", pd.Series([""] * len(e)))
                         .astype(str).str.split(";").str[0].str.strip())
    if "host" not in e.columns:
        e["host"] = (e.get("host_texts", pd.Series([""] * len(e)))
                     .astype(str).str.split(";").str[0].str.strip())
    e["parasite_norm"] = e["parasite"].map(norm_name)
    e["host_norm"] = e["host"].map(norm_name)
    if "verified" not in e.columns:
        e["verified"] = None
    keep = ["pmid", "parasite", "host", "parasite_norm", "host_norm",
            "relation", "confidence", "evidence_span", "verified",
            "verdict_why", "section_type", "source"]
    for c in ("parasite_taxid", "host_taxid", "geo", "date", "method",
              "known"):
        if c in e.columns:
            keep.append(c)
    return e[[c for c in keep if c in e.columns]]


def main():
    frames = []
    for fname, source in SOURCES:
        p = Path(LIT) / fname
        if p.exists():
            f = load(p, source)
            frames.append(f)
            print(f"{fname}: {len(f)} edges")
    if not frames:
        sys.exit("no edge files found")
    df = pd.concat(frames, ignore_index=True)
    df["pair"] = df["parasite_norm"] + "|" + df["host_norm"]

    out = Path(LIT) / "interactions.parquet"
    df.to_parquet(out, index=False)
    v = df.verified.fillna(False).astype(str).str.lower() == "true"
    print(f"\nwrote {out}: {len(df)} edges "
          f"({df.pair.nunique()} unique pairs, "
          f"{df.pmid.nunique()} papers)")
    print(f"verified: {int(v.sum())} | unverified: {int((~v).sum())}")
    print(df.groupby("source").size())


if __name__ == "__main__":
    main()
