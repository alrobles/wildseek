# Reporte de avances — WildSeek AI Factory + litmine

**Fecha:** 2026-10-27 · **Repo:** meta-hack-devel · **Doc:** interno

## 1. Objetivos

Convertir WildSeek (susceptibilidad eco-epidemiológica CONUS) en un
sistema escalable de priorización parásito↔hospedero con tres ejes:

1. **Escala geográfica/taxonómica** — Canadá→Panamá (`na_ca`), ~2.5k
   especies ave+mamífero, cómputo SLURM automatizado.
2. **Fábrica agéntica** — System-1 (triaje barato masivo) → System-2
   (diagnóstico excepcional) con ledger medible, sobre Muse/Fireworks.
3. **litmine "system-zero"** — extractor zero-shot de aristas
   parásito↔hospedero desde literatura (PubTator3 NER → LLM relación),
   con provenance primaria, monitor diario de papers nuevos, y
   alimentación de `species_labels` para validar `p_host`.

## 2. Avances y trazas

### WildSeek (fábrica 1)

- Dominio `na_ca` parametrizado (−170..−52, 7..84); CONUS intacto.
- `pool_all_na_ca.csv` vía `WILDSEEK_MIN_CELLS_ALL` (~2.5k spp ≥30 celdas).
- M-masking ecorregional ya en `predict_suit.R` — predicción acotada al
  rango accesible por especie.
- `domain_build.sh`: pool→normals→xnicher arrays→collect→phy_dist→
  suscept_model→predict→audit, con deps SLURM y exclusión de nodos
  sin beegfs (`WILDSEEK_EXCLUDE`).
- `planner` → `run_spec.json` (tiers screen/refine/audit/refit).
- `nightly.py` robusto: env-parametrizado, self-heal detrás de flag.
- Release gate curado → público `main` pusheado limpio (docs internos
  excluidos vía `release.exclude`).
- **2026-10-28**: `dist_frame` normaliza `min_d_phy_pos` por fuente
  (patristic vs taxa_proxy) + indicador `is_patristic_real`; re-run
  suscept_model (5-fold ×20): logreg ROC **0.850±0.031** → métricas
  bakeadas en `metrics.json`. We-called-it: **15 predicciones
  congeladas 2026-10-28** (`we_called_it.json`, `/we-called-it`);
  `--check` solo confirma con PMID **post-freeze** (bug corregido:
  antes flipeaba con cualquier arista). `/decisions` + tarjeta delta
  (switch_to ejecutable visible). Exposure: poultry (county) y
  dairy herds (state) **separados** — toggle en UI. Supply chain:
  60.1M egg-layer birds (73% del total APHIS).

### litmine (fábrica 2) — trazas verificables

| Traza | Resultado |
|---|---|
| `extract.py` v1 | PubTator3→S1 tipado; `--resume`, `--jobs N`, retry+backoff, escritura incremental por doc |
| `doidict.py` | dict persistente DOI↔PMID (idconv batch); `doi2pmid` = wrapper |
| Smoke 2 PMIDs | 7 aristas, aristas centrales recuperadas — `ffbeeba` |
| Gold run 33 PMIDs | 100 aristas; **16% unique-pair recall a nivel abstract**; misses = especies en tablas full-text → diseño de 2 capas — `0e723da` |
| Barrido corpus ZOVER | 348 DOIs → 165 PMIDs → 119 papers anotados → **217 aristas, $0.0000, 119 llamadas** |
| Distribución relaciones | parasite_of 182 · reservoir_of 29 · no_detection 3 · host_of 2 · intermediate_host_of 1 |
| Backends LLM | Fireworks `muse-spark-open` verificado (crédito $100, reasoning model); glimmer/MI210 self-host; spark API pago — cascada ya cableada en `MetaClient` |
| **2026-10-28 (noche autónoma)** | |
| PMC full-text ZOVER | 83/119 papers OA → **3,165 pasajes** (`sections_zover`) |
| Triage zover | 3,165 chunks → **721 YES (23%)**, ahorro tokens ~74%, **$1.93 spark-open** |
| Extracción Capa 2 gold | 303 YES → **740 aristas, $0.51** — `extract_full.py` name-level |
| Eval full-text gold | **56% pair-recall (64/115)** vs 16% abstracts — **3.4×** — `eval_full.py` |
| Auditoría 30 aristas (glimmer) | precisión cruda **73%**; subconjunto judge-verified **100%** (12/12) — el JUDGE capturó los 8 falsos positivos |
| `verify.py` JUDGE | glimmer self-host, verdict+reason por arista; zover-abstract **88/212 (42%)**, gold33-fulltext **183/734 (25%)**; rechazos: 273 mención-sin-detección, 86 solo-serología, ~190 números/contexto |
| Leakage audit v2 | 720 pares únicos, **0% leakage 2020+** (22 pares limpios); 1 par pre-2020 filtrado — `leakage_audit.md` |
| Costo/edge | **$0.0014** (ledger JSONL por llamada — `agent_calls.jsonl`) |
| Fail-closed | `dist_frame` rechaza <2 ejes con cobertura; test `test_dist_frame.py` |
| Capa de datos | ZOVER 5.9k muestras (geo+tejido+BioSample), VIRION gold 283 aristas/33 PMIDs (benchmark, licencia respetada), corpus etiquetado + `score` PU precomputado, `df_abstracts_random` negativos |
| Infra corpus | `/kuhpc/.../pubmed` baseline 2026 completo (166G + FTS index); `crawl.ecoseek.org` para fuentes JS-walled |
| Motor PU formal | `xplus` (alrobles/xplus-devel) como slot swappable del suscept_model — automatización+finetuning en desarrollo paralelo |

## 3. Planeación (docs vivos)

- `docs/ai-factory.md` — patrón ENTRADA→SPEC→BUILDER→JUDGE→ESCALATE→
  APPROVER→PRODUC→BRAIN; capa de datos; **litmine-monitor** (delta
  diario PubMed → S0 → extract → dedupe → store por fecha → brief);
  **protocolo de validación** (edges minados = test-set held-out de
  `p_host`, con advertencias de independencia parcial y ruido).
- `docs/system-escalation.md` — cascada S1→S2: schema de veredicto
  → `fit_judge` → calibración ~150 spp → `escalate` con cap ~5%/noche
  → `agent_calls.jsonl` → cierre OODA.

## 4. Milestones

| # | Milestone | Estado |
|---|---|---|
| M1 | Expansión na_ca + M-mask + automatización SLURM | ✅ hecho (pool job en cómputo) |
| M2 | Release público curado con gate | ✅ SHIP → push limpio |
| M3 | Backends LLM verificados (fireworks + locales) | ✅ |
| M4 | Extractor v1 + robustez (resume/jobs/retry) | ✅ |
| M5 | Benchmark gold 33 PMIDs | ✅ 16% abstract-level (diagnóstico: gap = tablas full-text) |
| M6 | Primer barrido corpus (ZOVER) | ✅ 217 aristas / $0 |
| M7 | QC de precision sobre muestra de aristas | ⏳ siguiente |
| M8 | Full-text pass (PMC local) para especies-en-tablas | ⏳ |
| M9 | Corpus grande (`df_abstracts.score`-filtrado, ~miles) | ⏳ |
| M10 | Monitor diario + `interactions.parquet` por run | ⏳ |
| M11 | `fit_judge` S1 + calibración 150 spp | ⏳ |
| M12 | xplus integrado como motor PU | ⏳ (en desarrollo paralelo) |
| M13 | Validación prospectiva p_host vs edges minados | 🔮 tesis del paper |

## 5. Puertas (gates)

- **G1 — precision del extractor**: auditoría de 30 aristas (glimmer):
  precisión cruda 73% <0.8 → **el JUDGE stage ya existía y lo resuelve**:
  subconjunto verificado = 100% (12/12). Pendiente: confirmación humana
  (muestra manual) para cerrar formalmente.
- **G2 — full-text antes de grafo**: ✅ RESUELTA — `extract_full.py`
  sobre chunks YES: 56% recall vs 16% abstract (3.4×). Grafo puede
  construirse sobre aristas verificadas.
- **G3 — calibración antes de S2**: `fit_judge` debe superar baseline
  de reglas (`decide_tail`) sobre ~150 spp etiquetadas antes de
  escalar a wonder.
- **G4 — budget caps**: S2 con cap ~5% casos/noche + ledger de costo;
  fireworks = bulk S1, spark-API solo fallback.
- **G5 — VIRION**: solo benchmark/cobertura interna; jamás re-ingerido
  como producto (términos heredados). Edges propios con provenance.

## 6. Hoja de ruta

```
ahora ──► QC precision (G1) ──► full-text pass PMC (G2)
        ──► barrido corpus grande + interactions.parquet (G5)
        ──► monitor diario (cron junto a nightly.py)
        ──► adapter edges → species_labels
en paralelo: fit_judge + calibración (G3) | xplus tuning (M12)
        ──► validación prospectiva p_host×edges → paper
```

**Riesgo principal manejado**: pérdida de trabajo por timeouts →
resuelto (resume/incremental/jobs). **Activo diferenciador**: grafo
vivo con provenance primaria + monitor diario — lo que ninguna DB
curada anualmente ofrece. Crédito Fireworks: ~$0.00 gastado,
margen enorme para barrido a escala.
