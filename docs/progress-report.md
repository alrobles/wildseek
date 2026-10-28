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

- **G1 — precision del extractor**: muestra ~30 aristas revisada a mano;
  si precision <0.8 → ajustar prompt/judge ANTES de escalar corpus.
- **G2 — full-text antes de grafo**: no construir `interactions.parquet`
  final hasta tener pase full-text; sin él el recall real queda ~16%.
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
