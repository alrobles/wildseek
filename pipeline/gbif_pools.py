"""GBIF occurrence pools for the HPAI susceptibility pilot.

Runs on kuhpc (login node OK, ~2 min). Reads the class-segmented
gbif_thinned_120.duckdb (1/120-deg deduplicated occurrence store on BeeGFS)
and materializes, under /beegfs/a474r867/meta-hack/:

  species_cell_counts.csv          per-species unique-cell counts both tiers
  occ_conus_{class}_1120.parquet   CONUS points, one per 1/120-deg cell
  occ_global_{class}_130.parquet   global cells, one per 1/30-deg cell
                                   (coarsened from the 1/120 grid, 4x4 blocks)
  pool_flagship.csv                species with >=100 unique CONUS cells
  pool_conus_endemic.csv           subset whose global footprint is CONUS-only

Filters: class in {Mammalia, Aves}, year 1996-2025, occurrencestatus PRESENT.
CONUS bbox: lat 24-49.5, lon -125 to -66 (lower 48 + margins).
"""

import duckdb
import time

DB = "/kuhpc/work/kbs/a474r867/gbifdata/gbif_thinned_120.duckdb"
OUT = "/beegfs/a474r867/meta-hack"
CLASSES = ["Mammalia", "Aves"]
MIN_YEAR, MAX_YEAR = 1996, 2025
CONUS = (
    "decimallatitude between 24 and 49.5 "
    "and decimallongitude between -125 and -66"
)


def base(cls: str) -> str:
    return (
        f"from occurrences where class='{cls}' "
        f"and year between {MIN_YEAR} and {MAX_YEAR} "
        "and occurrencestatus='PRESENT' and decimallatitude is not null"
    )


def main() -> None:
    con = duckdb.connect(DB, read_only=True)
    con.execute("PRAGMA threads=8; PRAGMA memory_limit='40GB'")
    t0 = time.time()

    # Per-species unique-cell counts at both tiers + CONUS-endemic flag.
    con.execute(
        f"""copy (
          with occ as (
            select species, class, decimallatitude, decimallongitude,
                   lat_120, lon_120 {base('Mammalia').replace("class='Mammalia'", "class in ('Mammalia','Aves')")}
          ),
          conus as (select * from occ where {CONUS})
          select c.species, o.class,
                 count(distinct c.lat_120 || '|' || c.lon_120) n_cells_conus,
                 count(distinct floor(o.lat_120*4)/4 || '|' ||
                               floor(o.lon_120*4)/4) n_cells_global,
                 count(distinct case when not (
                     o.decimallatitude between 24 and 49.5 and
                     o.decimallongitude between -125 and -66)
                   then floor(o.lat_120*4)/4 || '|' || floor(o.lon_120*4)/4
                 end) n_cells_outside
          from conus c join occ o using (species)
          group by 1, 2
        ) to '{OUT}/species_cell_counts.csv' (header, delimiter ',')"""
    )
    print("counts", round(time.time() - t0), "s")

    for cls in CLASSES:
        con.execute(
            f"""copy (select specieskey, species, decimallatitude lat,
                      decimallongitude lon, lat_120, lon_120, year,
                      basisofrecord
              {base(cls)} and {CONUS})
            to '{OUT}/occ_conus_{cls.lower()}_1120.parquet'
            (format parquet, compression zstd)"""
        )
        print("conus", cls, round(time.time() - t0), "s")

    for cls in CLASSES:
        con.execute(
            f"""copy (select specieskey, species,
                      floor(lat_120*4)/4 lat_30, floor(lon_120*4)/4 lon_30,
                      count(*) n120, min(year) first_yr, max(year) last_yr
              {base(cls)} group by 1,2,3,4)
            to '{OUT}/occ_global_{cls.lower()}_130.parquet'
            (format parquet, compression zstd)"""
        )
        print("global30", cls, round(time.time() - t0), "s")

    con.close()

    # Pool tables from the counts CSV.
    con2 = duckdb.connect()
    con2.execute("PRAGMA threads=8")
    counts = f"'{OUT}/species_cell_counts.csv'"
    con2.execute(
        f"""copy (select * from {counts} where n_cells_conus >= 100)
            to '{OUT}/pool_flagship.csv' (header, delimiter ',')"""
    )
    con2.execute(
        f"""copy (select * from {counts}
                where n_cells_conus >= 100 and n_cells_outside = 0)
            to '{OUT}/pool_conus_endemic.csv' (header, delimiter ',')"""
    )
    for t in ["pool_flagship", "pool_conus_endemic"]:
        print(t, con2.execute(
            f"select class, count(*) from '{OUT}/{t}.csv' group by 1"
        ).fetchall())
    con2.close()


if __name__ == "__main__":
    main()
