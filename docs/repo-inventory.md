# Inventario verificado del repo — meta-hack-devel

Auditoría a mano (2026-10-28): qué existe realmente en `data/` vs lo
reclamado. Regla para Devin: si no está aquí listado, NO asumir ruta —
confirmar antes de usar.

## 1. ZOVER muestras — `data/zover/` ✓

- bat_samples.csv 1489 · mosquito_samples.csv 1093 · rodent_samples.csv
  333 · tick_samples.csv 2972 → **5887 muestras reales**
- Schema: SampleName, Host, CollectionDate, Country, Province, City,
  SampleDetails, BioProject, BioSample — metadatos, NO secuencias
- **GAP**: los 8 FASTA del repertorio viral NO están en el repo —
  viven en `/beegfs/a474r867/zover/` (descargados allí)

## 2. litmine corpus y edges — `data/litmine/` ✓

- zover_corpus.csv 380 rows (id, doi, title, abstract, year, source)
- zover_pmids.csv 119 · doi_pmid_map.csv 165 (dict DOI↔PMID↔PMCID)
- edges_zover.csv 217 aristas, $0.00 en 119 calls
- edges_gold33.csv 99 aristas (recall unique-pair 16% vs gold)
- edges_smoke.csv (prueba 2 PMIDs)
- virion_ebola_lassa_gold.csv — gold 283 aristas, SOLO benchmark
- sections.parquet — Capa 0: **ahora ~792 passages / 33 pmids**
  (este inventario se escribió con 272 — ya creció con la ingesta PDF)
- pmc_cache/: 7 JSON — funciona
- **GAP**: corpus etiquetado ~10k abstracts + score PU + negativos
  NO está en el repo — vive en abstractsHostParasites/data-raw
  (otro árbol). No asumir.

## 3. WildSeek modelo — `data/` ✓

- dist_frame.parquet 1147×12 (species, label, j_env, j_geo, d_phy…)
- susceptibility.parquet (serve/) 1147×7 — el score vivo de la web
- host_labels.parquet 219×7 (labels APHIS)
- jaccard_env.parquet 23.2M rows (157MB) · jaccard_geo 13.0M (46MB)
- phy_dist.csv 20.9MB · m_summary.parquet 16330 spp · taxonomy 1148
- species_winner.csv (88 pares) · fit_catalog.csv 101k fits ·
  species_cell_counts.csv
- **GAP**: pool na_ca ~2.5k NO materializado — solo el builder
  `pipeline/gbif_pools.py`; CONUS 1147 es lo corrido

## 4. APHIS + agro — `data/` ✓

- aphis_wild_birds.parquet 174581 rows (iav/h5/h7, county, watershed)
- aphis_poultry.parquet 1109 (county_fips, birds_affected) — base
  seguridad alimentaria · aphis_livestock.parquet 64 (dairy state)
- aphis_flyways.json 18MB · host_list*.jsonl

## 5. Filogenias — mixto

- v6_point.nwk = **SYMLINK** a phyloseek-devel/results/dating_v6/ —
  no viaja al público (gitignored, nunca asumirlo en snapshot)
- data/birdtree/: BLIOCPhyloMasterTax + avonet1.xlsx + e2/ —
  consensus local existe
- bird_syn_map.csv + mammal_syn_map.csv (crosswalks)

## 6. Geo base — `data/` ✓

wbd_huc8_conus.geojson · cb_county/ shapefiles · app/data + data/serve
(detecciones, county_exposure, risk_watershed, flyways, decisions,
briefing, qa_report, meta) — lo que sirve la web bakeada.

## 7. Auditorías/runs — `data/` ✓

decisions_all.jsonl · decisions_tail · delta.csv (49 flag_review) ·
data/audit + audit_export (61 spp dirs) · data/runs (2 nightly JSON)

## 8. Externo NO VERIFICADO desde esta máquina

(beegfs/kuhpc no montados en sesión local — marcar, no asumir):

- Dump PubMed 2026 166G + FTS index (`/kuhpc/.../pubmed`)
- GBIF duckdb 41GB + env_cube + era5_bioclim
- Corpus 10k + scores PU (GAP #2) · 8 FASTA (están en
  `/beegfs/a474r867/zover/`, verificado por ssh kuhpc)
- Pool na_ca CSV
