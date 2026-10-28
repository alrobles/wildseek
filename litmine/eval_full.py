"""D3 eval — full-text extraction vs the VIRION Ebola/Lassa gold.

Pair-level recall: a mined edge hits a gold pair when parasite AND
host match at normalized-name level (binomial or first-token for
viruses like ZEBOV/EBOV/MARV/ LASV -> genus-level approximations).

    python litmine/eval_full.py \
        --edges data/litmine/edges_fulltext.csv \
        --gold data/litmine/virion_ebola_lassa_gold.csv
"""
import argparse
import sys

import pandas as pd

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from leakage_audit import norm_name  # noqa: E402

# gold virus short codes -> accepted mined-name prefixes
VIR_ALIASES = {
    "zebov": ("ebola", "zebov", "zaire ebolavirus"),
    "ebov": ("ebola", "zebov", "zaire ebolavirus"),
    "marv": ("marburg", "marv"),
    "lasv": ("lassa", "lasv"),
    "sebv": ("sebov", "sudan"),
    "bdbv": ("bundibugyo", "bdbv"),
    "restv": ("reston", "restv"),
    "tafv": ("tai forest", "taï forest", "tafv"),
}


def vir_match(mined: str, gold_code: str) -> bool:
    m = norm_name(mined)
    g = norm_name(gold_code)
    aliases = VIR_ALIASES.get(g, (g,))
    return any(a in m for a in aliases)


def host_match(mined: str, gold_host: str) -> bool:
    m, g = norm_name(mined), norm_name(gold_host)
    if m == g or m in g or g in m:
        return True
    # genus-level fallback (gold may say 'Aves', mined 'Eidolon helvum')
    return m.split()[0] == g.split()[0] if m.split() and g.split() \
        else False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edges", default="data/litmine/edges_fulltext.csv")
    ap.add_argument("--gold",
                    default="data/litmine/virion_ebola_lassa_gold.csv")
    args = ap.parse_args()

    e = pd.read_csv(args.edges)
    g = pd.read_csv(args.gold)

    def _pmid(v):
        import re as _re
        return _re.sub(r"\D", "", str(v).lstrip("\ufeff"))

    mined_pmids = set(e.pmid.map(_pmid))
    gold_ids = g["PUBMED ID"].map(_pmid)
    gold_pmids = set(gold_ids)
    cov = mined_pmids & gold_pmids
    gold_in = g[gold_ids.isin(cov)]
    pairs = set(zip(gold_in["Virus"].map(norm_name),
                    gold_in["Host"].map(norm_name)))

    hits = set()
    for r in e.itertuples():
        for gv, gh in pairs:
            if vir_match(r.parasite, gv) and host_match(r.host, gh):
                hits.add((gv, gh))

    print(f"edges: {len(e)} from {len(mined_pmids)} papers")
    print(f"gold papers covered: {len(cov)}/{len(gold_pmids)}")
    print(f"gold unique pairs in covered papers: {len(pairs)}")
    print(f"hit: {len(hits)} ({100*len(hits)/max(len(pairs),1):.0f}%)")
    print("\nmissed gold pairs (sample):")
    for p in sorted(pairs - hits)[:15]:
        print("  ", p)


if __name__ == "__main__":
    main()
