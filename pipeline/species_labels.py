"""Resolve APHIS wild-bird species names -> GBIF specieskeys -> labels.

    python3 species_labels.py

Writes data/serve/host_labels.parquet:
  specieskey, species (gbif canonical), common_name, n_detections, class
Only rows that join onto the fitted-species universe count as positives.
"""
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

API = "https://api.gbif.org/v1/species/match"


def match(name):
    try:
        j = requests.get(API, params={
            "name": name, "rank": "species", "kingdom": "Animalia",
            "strict": "false"}, timeout=15).json()
        return {
            "common_name": name,
            "specieskey": j.get("usageKey"),
            "species": j.get("scientificName"),
            "class": j.get("class"),
            "confidence": j.get("confidence"),
            "match_type": j.get("matchType"),
        }
    except Exception:
        return {"common_name": name, "match_type": "ERR"}


def main():
    det = pd.read_parquet("data/aphis_wild_birds_species.parquet")
    names = det.bird_species.value_counts()
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(match, names.index))
    lab = pd.DataFrame(rows)
    lab["n_detections"] = lab.common_name.map(names)
    # keep confident species-level vertebrate matches
    lab = lab[(lab.confidence.fillna(0) >= 90)
              & (lab.match_type.isin(["EXACT", "FUZZY"]))]
    print("resolved:", lab.specieskey.notna().sum(), "/", len(lab))
    print("classes:", lab["class"].value_counts().to_dict())
    lab.to_parquet("data/host_labels.parquet", index=False)
    win = pd.read_csv("data/species_winner.csv")
    hit = lab[lab.specieskey.isin(win.specieskey)]
    print("positives inside fitted universe:", len(hit))


if __name__ == "__main__":
    main()
