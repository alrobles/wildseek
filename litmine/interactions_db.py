"""interactions.db — the live parasite<->host edge store (sqlite).

Replaces append-to-CSV as the write path: dedupe is a UNIQUE index,
resume is the `papers` work queue, provenance is `run_id` per batch.
Exports to parquet for the API/UI read path.

    python litmine/interactions_db.py migrate   # one-time: CSVs -> db
    python litmine/interactions_db.py export    # db -> interactions.parquet
    python litmine/interactions_db.py stats

DB lives at $LITMINE_DB or data/litmine/interactions.db
(canonical: reumanlab-terminal:/mnt/lenovo/litmine/db/interactions.db).
"""
import argparse
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from leakage_audit import norm_name  # noqa: E402

LIT = Path("data/litmine")
DB = Path(os.environ.get("LITMINE_DB", LIT / "interactions.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS edges(
  edge_id INTEGER PRIMARY KEY,
  pmid TEXT NOT NULL,
  pmcid TEXT,
  section_type TEXT NOT NULL DEFAULT '',
  offset INTEGER NOT NULL DEFAULT -1,
  parasite TEXT, host TEXT,
  parasite_norm TEXT, host_norm TEXT,
  parasite_taxid INTEGER, host_taxid INTEGER,
  relation TEXT,
  evidence_span TEXT,
  geo TEXT, date TEXT, method TEXT,
  confidence REAL,
  verified INTEGER, verdict_why TEXT,
  source TEXT,
  model_extract TEXT, model_judge TEXT,
  run_id TEXT, scope_id TEXT,
  UNIQUE(pmid, parasite_norm, host_norm, relation,
         section_type, offset)
);
CREATE INDEX IF NOT EXISTS ix_edges_pair
  ON edges(parasite_norm, host_norm);
CREATE INDEX IF NOT EXISTS ix_edges_pmid ON edges(pmid);
CREATE INDEX IF NOT EXISTS ix_edges_host ON edges(host_norm);

CREATE TABLE IF NOT EXISTS papers(
  pmid TEXT NOT NULL, corpus TEXT NOT NULL,
  fetched INTEGER DEFAULT 0, triaged INTEGER DEFAULT 0,
  yes INTEGER DEFAULT 0, extracted INTEGER DEFAULT 0,
  run_id TEXT, status TEXT,
  PRIMARY KEY(pmid, corpus)
);
"""

SOURCES = [
    ("edges_gold33.csv", "gold33-abstract"),
    ("edges_fulltext.csv", "gold33-fulltext"),
    ("edges_zover.csv", "zover-abstract"),
    ("edges_zover_full.csv", "zover-fulltext"),
    ("edges_hpai.csv", "hpai-fulltext"),
]


def connect(db=DB):
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA)
    return conn


def _ins(conn, e):
    conn.execute(
        """INSERT OR IGNORE INTO edges
        (pmid,pmcid,section_type,offset,parasite,host,
         parasite_norm,host_norm,parasite_taxid,host_taxid,
         relation,evidence_span,geo,date,method,confidence,
         verified,verdict_why,source,model_extract,model_judge,
         run_id,scope_id)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (str(e.get("pmid")), e.get("pmcid"),
         e.get("section_type") or "", 
         int(e["offset"]) if e.get("offset") not in (None, "") else -1,
         e.get("parasite"), e.get("host"),
         e.get("parasite_norm") or norm_name(e.get("parasite", "")),
         e.get("host_norm") or norm_name(e.get("host", "")),
         e.get("parasite_taxid"), e.get("host_taxid"),
         e.get("relation"), e.get("evidence_span"),
         e.get("geo"), e.get("date"), e.get("method"),
         e.get("confidence"),
         None if e.get("verified") in (None, "", "nan") else
         int(str(e["verified"]).lower() == "true"),
         e.get("verdict_why"), e.get("source"),
         e.get("model_extract"), e.get("model_judge"),
         e.get("run_id"), e.get("scope_id")))


def migrate(conn):
    import pandas as pd
    for fname, source in SOURCES:
        p = LIT / fname
        if not p.exists():
            continue
        df = pd.read_csv(p)
        # unify taxid sources -> parasite/host name columns
        if "parasite" not in df.columns and "para_texts" in df.columns:
            df["parasite"] = (df.para_texts.astype(str)
                              .str.split(";").str[0].str.strip())
        if "host" not in df.columns and "host_texts" in df.columns:
            df["host"] = (df.host_texts.astype(str)
                          .str.split(";").str[0].str.strip())
        df["source"] = source
        df["run_id"] = f"migrate-{source}"
        before = conn.total_changes
        for e in df.to_dict("records"):
            e = {k: (None if pd.isna(v) else v) for k, v in e.items()}
            _ins(conn, e)
        conn.commit()
        got = conn.execute(
            "SELECT count(*) FROM edges WHERE source=?", (source,)
        ).fetchone()[0]
        print(f"{fname}: +{conn.total_changes - before} new "
              f"({got} total {source})")


def export(conn, out=None):
    import pandas as pd
    df = pd.read_sql("SELECT * FROM edges", conn)
    for c in ("confidence", "parasite_taxid", "host_taxid"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["pair"] = df.parasite_norm + "|" + df.host_norm
    out = out or (LIT / "interactions.parquet")
    df.to_parquet(out, index=False)
    print(f"wrote {out}: {len(df)} edges "
          f"({df.pair.nunique()} pairs, {df.pmid.nunique()} papers)")


def stats(conn):
    n = conn.execute("SELECT count(*) FROM edges").fetchone()[0]
    v = conn.execute("SELECT count(*) FROM edges WHERE verified=1"
                     ).fetchone()[0]
    src = conn.execute(
        "SELECT source,count(*) FROM edges GROUP BY source").fetchall()
    print(f"edges {n} | verified {v}")
    for s, c in src:
        print(f"  {s}: {c}")
    pq = conn.execute("SELECT count(*) FROM papers").fetchone()[0]
    print(f"papers queued: {pq}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["migrate", "export", "stats"])
    ap.add_argument("--out")
    a = ap.parse_args()
    conn = connect()
    {"migrate": migrate, "export": export, "stats": stats}[a.cmd](conn)
