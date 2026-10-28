# WildSeek + litmine — Design Draft + Master Plan para Devin

Fecha: 2026-10-28. Deadline: Nov 4, 9PM ET. Track: Indie. Tema: Build for Your World.
Ignora el video de software factory; este es el plan del producto hackathon.

## Goal

Dejar WildSeek (monitor de susceptibilidad wildlife + riesgo supply-chain) + litmine
(extractor zero-shot parásito-hospedero) listos para submit: repo público elegible,
demo viva sin llave, video 3 min, y claims técnicos respaldados. Maximizar rúbrica:
Impact 30 / Meta tooling 25 / Demo 25 / Tech depth 20.

## Success Criteria

1. Repo público `alrobles/meta-hack`: snapshot huérfano, incluye `litmine/`,
   video-script abre con línea pre-existente vs construido, strings
   `muse-spark-1.3`, `muse-spark-1.2-contributor`, `muse-wonder-1.0`,
   `muse-glimmer`, `muse-spark-open` grepeables en código + README + SUBMISSION.
2. Cero strings prohibidos (`tu riesgo`, `riesgo humano`, `R0`, `diagnostico`,
   `prevencion personal`, `health risk`) en UI, README, SUBMISSION, video;
   disclaimer "Not medical advice" visible en los cuatro.
3. Demo viva: abre <3s sin llave (baked JSON), `/health` ok, muestra cascada de
   4 modelos con costo, tarjeta we-called-it, tarjeta métricas
   (AUC + CI + costo/arista + precisión manual).
4. Video 3 min grabado con estructura 0:00 / 0:30 / 1:30 / 2:30 y backup local.
5. Claims con evidencia: AUC + bootstrap CI, precisión manual ≥30 aristas,
   leakage audit por par normalizado, costo por arista desde ledger.

## Approach — Design Draft

Dos sistemas acoplados, no uno:

- **WildSeek (scores)**: GBIF pools → M por especie (ecorregiones 95%) →
  env cube → campaña xnicher 88 pares → winners AIC → suit con M-mask →
  `dist_frame` (env/geo/phy vs positivos, auto-exclusión) → `suscept_model`
  (logreg-poly2 vs HGB, repeated CV, bootstrap) → `susceptibility.parquet` →
  risk = detección × reservoir → HUC8/county → serve bakeado.
- **litmine (valida)**: PMIDs → PubTator3 NER→TaxID (el LLM nunca hace NER) →
  Capa 1 triage YES/NO → Capa 2 relación tipada (contributor/spark-open) →
  `edges.csv` → reconcile + dedupe a rango especie → validación de p_host +
  we-called-it. Full-text PMC solo en candidatos (Capa 0 secciones, nunca
  papers completos al modelo caro).
- **Capa agente (Meta)**: `MetaClient` con 4 roles: contributor = bulk S1,
  spark-1.3 = juez/decisiones, wonder = briefing S2, glimmer = offload local.
  `decide_tail` solo ve cola ambigua → `switch_to` ejecutable vía
  `refit_queue.csv` → `refit_switched.R` → `decisions_delta.csv`.
  `qa.py` quorum 3/4 → `nightly.py` conveyor → `release.sh` gate SHIP.

Contratos congelados (no cambiar sin actualizar este doc):

- `edges.csv`: pmid, parasite_taxid, host_taxid, relation, confidence,
  evidence_span, geo, date, method, host_texts, para_texts, known.
- relations enum (7, cerrado): parasite_of, host_of, vector_of, reservoir_of,
  intermediate_host_of, dead_end, no_detection.
- `decisions_delta.csv`: species, decision, switch_to, why, changed,
  old/new AIC. `qa_report.json`: pass, verdict, quorum, reviews.
- Serve bakeado: meta.json, susceptibility.parquet, risk_watershed.parquet,
  briefing.json, explain_*.json, suit_*.png + meta, decisions_delta.csv.

Invariantes (un juez técnico las va a probar):

1. Todo píxel de suitability vive dentro de M; fuera = NA.
2. `dist_frame` excluye auto-pares; un positivo solitario da NaN.
3. Demo corre sin llave: baked JSON primero, live call solo fallback.
4. Toda llamada Meta loguea modelo + tokens + USD en ledger append-only.
5. `data/` gitignored siempre; público = snapshot huérfano filtrado.
6. Cero consejo médico en superficies juzgadas (ver criterio 2).

Alternativas rechazadas: full-text sobre todo PubMed (costo, quemar ceros);
filogenia viral datada con 8 FASTA (overclaim); RAG genérico/chatbot (anti-project);
nuevos tipos de relación (dividen 217 edges, destruyen power); re-ingerir VIRION
como producto (LGPL/agregados turbios — solo benchmark).

Supuestos: Devin trabaja en `meta-hack-devel` (origin), nunca pushea directo a
`public` (solo vía `release.sh` con SHIP); cluster kuhpc + beegfs disponibles para
compute pesado; llaves solo por env (`MODEL_API_KEY`, `FIREWORKS_API_KEY`,
`NCBI_API_KEY`), nunca en código.

## Steps

Fase 0 — Elegibilidad (día 1, bloquea todo lo demás):

- 0.1 Re-release público: correr `scripts/release.sh`, verificar en clon fresco
  que `public/main` liste `litmine/`, `tools/`, video-script con cold open y los
  5 strings de modelo. Agregar `muse-spark-open` a README + SUBMISSION antes.
- 0.2 Disclaimer 1-línea en `app/index.html` (footer panel), README, SUBMISSION,
  video-script Act 1. Renombrar "risk" UI → "surveillance priority" donde sea
  etiqueta de cara al usuario. Grep prohibidas = 0.
- 0.3 Proveniencia: crear/pushear tag `pre-hackathon` en upstreams
  (xnicher, oneearthr, phyloseek-devel, geoseek-devel) en commit pre-26-oct, o
  borrar el claim de README.md:70-71 y citar hashes fechados.
- 0.4 Ventana Oct 26 vs 27: preguntar en Discord #office-hours cuál rige;
  ajustar NEW.md/README a lo respondido.
- 0.5 Higiene pública: `pipeline/gbif_pools.py` default `""` + assert con mensaje
  (quitar `/kuhpc/...`); `phy_dist.R` + `name_reconcile.py` fallan con mensaje
  accionable si falta el árbol; borrar symlink `data/v6_point.nwk`; mover backend
  Inception/mercury de `agent/meta_client.py` a `tools/dev/` + exclude del snapshot.

Fase 1 — Demo visible (días 2-3, puntos de rúbrica más baratos):

- 1.1 Tira de 4 modelos en UI: badges contributor/spark-1.3/wonder/glimmer con
  calls + USD (desde Spend/ledger) + tabla `decisions_delta` en `<details>`
  (species, verdict, why, AIC old→new).
- 1.2 `/metrics` + tarjeta: `metrics.json` bakeado (auc, auc_ci, n_boot,
  precision_hand_n, cost_usd_total, cost_per_edge, n_edges) y tarjeta en panel.
- 1.3 We-called-it: congelar HOY top-15 unlabeled por p_host con fecha en
  `data/serve/we_called_it.json`, endpoint `/we-called-it`, tarjeta con
  predicted_on/species/p_host/status. Status inicial `awaiting-confirmation`.
- 1.4 Precisión manual G1: auditar 30 aristas a mano, registrar
  correct/total + criterios; si <0.8, ajustar prompt/judge antes de escalar.
- 1.5 `pipeline/seed_demo.py`: genera `app/data` mínimo (meta, top-100 risk/
  susceptibilidad, briefing ejemplo marcado sample, 20 suit o placeholders) +
  documentar `seed_demo.py && docker compose up` en README.
- 1.6 Bakeo: precomputar explains top-50 watersheds + top-20 especies;
  filas sin baked se deshabilitan en UI.

Fase 2 — Profundidad técnica (días 3-5, protege Tech depth + Impact):

- 2.1 Leakage audit (P0): reconcile TaxID→especie, normalizar par
  (parasite_sp, host_sp, relation), split temporal por fecha PMID, tabla %
  pares test ya vistos en train. Sin esto, ningún claim prospectivo.
- 2.2 Ablación negativos (P0): modelo A con `no_detection` reales vs B con
  pseudo-ausencias; comparar AUC + reliability. Documentar supuesto "unlabeled
  = negativo" en SUBMISSION Known limits sí o sí.
- 2.3 Escala filo: flag `is_patristic_real` en dist_frame, normalización
  intra-clase antes de mezclar BirdTree/v6/proxy, `is_patristic_real` como
  feature; re-correr modelo y reportar delta AUC.
- 2.4 Ledger: append JSONL por llamada en `MetaClient.chat`
  (ts, model, prompt_tok, compl_tok, usd, pmid/species) a `data/agent_calls.jsonl`.
- 2.5 Fail-closed: `dist_frame` aborta si faltan ≥2 ejes o coverage <50%;
  persistir `n_imputed` por fila en susceptibility; log de PMID + respuesta
  cruda en cada JSONDecodeError de litmine.
- 2.6 Test M-mask: 1 suit PNG + eco raster, cero píxeles válidos fuera de M.

Fase 3 — litmine full-text (con gates, días 4-6):

- 3.1 Verificar D1/D2 ya hechos (commits pmc_fetch, triage): correr sobre
  gold33 y reportar % misses abstract recuperables + % tokens ahorrados.
- 3.2 D4 reconcile + dedupe con regla documentada. Gate: sin D4 no hay D5.
- 3.3 D3 piloto 10 PMIDs gold con misses: delta recall/costo full-text.
  Gate: escalar a 165 PMIDs ZOVER solo si recall 16%→>50% con costo <$1.
- 3.4 Ticker monitor diario (idea 14): delta PubMed→S0→extract→dedupe→store
  por fecha→brief; p_host pre-registrado antes de ver abstract.

Fase 4 — Video + submit (días 6-7):

- 4.1 Actualizar `docs/video-script.md` a estructura 0:00/0:30/1:30/2:30,
  grabar, backup local para final Nov 9.
- 4.2 Release final a público + checklist: clon fresco, compose up con seed,
  grep modelos >0, grep prohibidas = 0, /health, grabar evidencia.
- 4.3 Submit en Cerebral Valley (repo + video + miembros) + post X con
  we-called-it + mapa. No después del Nov 4 12:00 ET (margen).

## Validation Plan

- Cada fase: `python -m pytest -q tests/` en verde antes de pasar a la siguiente.
- Gates release (siempre): `grep -rE 'tu riesgo|riesgo humano|R0|diagnostico|prevencion personal|health risk' app/ api/ README.md SUBMISSION.md docs/video-script.md` vacío;
  `grep -r 'muse-spark-1.3\|muse-spark-1.2-contributor\|muse-wonder-1.0\|muse-glimmer\|muse-spark-open'` con hits en código + README + SUBMISSION del clon público.
- Demo E2E: `curl /health` → ok; `/briefing` sin `MODEL_API_KEY` → baked real;
  `/species?limit=1` con p_host; clon fresco + `seed_demo.py` + compose → health ok.
- Paso de mayor riesgo: 2.1 leakage audit — si el % de overlap es alto, los
  claims prospectivos y la tarjeta we-called-it deben reescribirse antes del video.

## Risks / Open Questions

- R1 Ventana de elegibilidad Oct 26 vs Oct 27 (guía dice 27, kickoff fue 26
  12PM). Mitigación: paso 0.4.
- R2 Recall litmine 16% a nivel abstract. Mitigación: vender precisión +
  eficiencia two-stage (idea 12), no recall bruto; no esconder el número.
- R3 `mercury`/`fireworks` en cliente si se publica antes de 0.5. Mitigación: 0.5.
- R4 BirdTree↔v6 escalas distintas (conocido, SUBMISSION lo admite). Mitigación: 2.3.
- Q1 (abierta): ¿guide "Oct 27" es errata o ventana estricta? Solo la responde
  #office-hours en Discord. Revisé el repo: ningún archivo la resuelve.
