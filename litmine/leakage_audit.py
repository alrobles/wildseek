"""D5 — leakage audit for the prospective-validation claim.

Mined literature edges are only a valid held-out test for p_host if
the (parasite, host) pair was NOT already in the training labels.
This reconciles mined edges against host_labels.parquet at
normalized-species level and reports leakage.

    python litmine/leakage_audit.py

Writes data/litmine/leakage_audit.md (one-page table).
"""
import re
import sys
import unicodedata

import pandas as pd

LABELS = "data/host_labels.parquet"
EDGES = ["data/litmine/edges_zover.csv",
         "data/litmine/edges_gold33.csv",
         "data/litmine/edges_fulltext.csv",
         "data/litmine/edges_zover_full.csv"]
CORPUS = "data/litmine/zover_corpus.csv"
REPORT = "data/litmine/leakage_audit.md"
SPLIT_YEAR = 2020   # edges from papers >= SPLIT_YEAR = "test period"

BINOMIAL = re.compile(r"^([A-Z][a-z]+)\s+([a-z][a-z-]+)\b")


def norm_name(s: str) -> str:
    """'Anas platyrhynchos Linnaeus, 1758' -> 'anas platyrhynchos';
    common names pass through lowercase."""
    s = unicodedata.normalize("NFKD", str(s)).strip()
    s = s.replace("\ufeff", "")
    s = re.sub(r"\s+", " ", s)
    m = BINOMIAL.match(s)
    return f"{m.group(1)} {m.group(2)}".lower() if m else s.lower()


def host_keys(row) -> set[str]:
    texts = str(row.get("host_texts") or "")
    if texts in ("", "None", "nan"):
        texts = str(row.get("host") or "")
    out = set()
    for t in re.split(r"[;|]", texts):
        t = t.strip()
        if t and t.lower() not in ("nan", "none"):
            out.add(norm_name(t))
    return out


def main():
    lab = pd.read_parquet(LABELS)
    pos = lab[lab.confidence > 0]
    pos_species = {norm_name(s) for s in pos.species}
    pos_common = {norm_name(s) for s in pos.common_name}

    # pmid -> doi (zover_pmids.csv) -> paper year (zover_corpus.csv);
    # gold33 pmids resolve straight from the gold sheet's own
    # Year_Published column. edge `date` is detection date, not pub year.
    doi2year, pmid2doi, pmid2year = {}, {}, {}
    try:
        c = pd.read_csv(CORPUS)
        doi2year = {str(r.doi).strip().lower(): int(r.year)
                    for r in c.itertuples()
                    if pd.notna(r.doi) and pd.notna(r.year)}
        p = pd.read_csv("data/litmine/zover_pmids.csv")
        pmid2doi = {str(r.pmid): str(r.doi).strip().lower()
                    for r in p.itertuples()}
    except FileNotFoundError:
        pass
    try:
        g = pd.read_csv("data/litmine/virion_ebola_lassa_gold.csv")
        for pid_raw, yr in zip(g["PUBMED ID"], g["Year_Published"]):
            pid = re.sub(r"\D", "", str(pid_raw))
            if pid and pd.notna(yr):
                pmid2year[pid] = int(yr)
    except FileNotFoundError:
        pass

    rows = []
    for f in EDGES:
        try:
            e = pd.read_csv(f)
        except FileNotFoundError:
            continue
        for r in e.itertuples():
            hosts = host_keys(r._asdict())
            leaked = bool(hosts & (pos_species | pos_common))
            pid = str(r.pmid)
            year = pmid2year.get(pid) or doi2year.get(pmid2doi.get(pid, ""))
            rows.append({"pmid": str(r.pmid), "file": f,
                         "relation": r.relation,
                         "hosts": "; ".join(sorted(hosts)),
                         "leaked": leaked,
                         "year": str(year)[:4] if year else "?"})

    df = pd.DataFrame(rows)
    pairs = df.drop_duplicates(["pmid", "hosts", "relation"])

    def _year(y):
        try:
            return int(y)
        except ValueError:
            return 0

    test = pairs[pairs.year.map(_year) >= SPLIT_YEAR]
    train = pairs[(pairs.year.map(_year) < SPLIT_YEAR) &
                  (pairs.year.map(_year) > 0)]

    rep = []
    rep.append("# D5 leakage audit — mined edges vs training labels\n")
    rep.append(f"labels: {len(pos)} positive species "
               f"({len(pos_species)} binomials + "
               f"{len(pos_common)} common names)\n")
    rep.append(f"edges: {len(pairs)} unique (pmid,hosts,relation) "
               f"from {len(EDGES)} files\n")
    rep.append("| period | n pairs | host already in labels | % |\n"
               "|---|---|---|---|\n")
    for name, sub in (("pre-2020", train), ("2020+", test),
                      ("all", pairs)):
        if len(sub):
            rep.append(f"| {name} | {len(sub)} | "
                       f"{int(sub.leaked.sum())} | "
                       f"{100*sub.leaked.mean():.0f}% |\n")
    rep.append("\n**gate**: prospective claims are valid only for "
               "pairs in `2020+` with leaked=False "
               f"({int((~test.leaked).sum())} pairs).\n")
    rep.append("\nLeaked test-period pairs (host was already a "
               "training positive — NOT valid held-out evidence):\n")
    for r in test[test.leaked].itertuples():
        rep.append(f"- pmid {r.pmid} ({r.year}) {r.relation} "
                   f"hosts={r.hosts}\n")

    open(REPORT, "w").write("".join(rep))
    print("".join(rep[:8]), file=sys.stderr)
    print(f"wrote {REPORT}", file=sys.stderr)


if __name__ == "__main__":
    main()
