# WildSeek + litmine — Devin Brief (consolidado)

Fecha: 2026-10-28. Repo: meta-hack-devel. Track: Indie. Theme: Build for Your World.
Demo live: wildseek.ecoseek.org. Deadline: Nov 4, 9:00 PM ET. Final: Nov 9.

Este documento consolida tres outputs del consejo cientifico para consumo
del agente Devin. Es la especificacion de estrategia + diseno + tareas.
Regla madre del hackathon (producto): stack Muse-only en el demo.
Modelos locales / Fireworks = tooling interno y pre-filtro, no cara del producto.

---

## 1. TESIS CENTRAL (una sola frase)

phy + env + geo predice quien comparte parasitos, validado
prospectivamente con literatura que el modelo nunca vio.

Todo lo que no fortalezca esa tesis es ruido. No vender "otro VIRION con LLM".
Lo defendible: benchmark vivo con validacion prospectiva continua.

---

## 2. RUBRICA OFICIAL Y REPARTO DE ESFUERZO

Stage 1 (pass/fail): fit al tema + uso razonable de Meta Model API y/o
open-weights. Si un filtro AI no encuentra strings de modelos Meta en repo,
video y producto, se reprueba aunque la ciencia sea buena.

Stage 2:
- Impact 30%: potencial real, quien se beneficia, fit al problem statement.
- Use of Meta AI tooling 25%: uso creativo mas alla de integracion basica.
- Demo 25%: demo funcional que aguanta en vivo + video 3 min que valga ver.
- Technical depth 20%: ingenieria solida y refinada, con craft real.

Reparto de horas sugerido: 40% tarjeta we-called-it + video, 30% cascada
de modelos visible, 20% live rapido sin key, 10% numeros de profundidad.

Bonus cazables con lo existente:
- $10k open-weights: Glimmer corriendo en hardware propio (MI210/Q6000),
  con log + endpoint local en codigo. El partner infra lo verifica.
- $5k agentic: factory ENTRADA>SPEC>BUILDER>JUDGE>APPROVER + self-heal
  flagueado + quorum 3/4 + run manifest real.
- $5k creative: briefing Wonder bien escrito + figura.
- $20k viral + $10k community vote: post en X con we-called-it + mapa.

---

## 3. REGLA CRITICA: EVITAR CONSEJO MEDICO (RISK DE DESCALIFICACION)

La guia prohibe "AI que genera y da consejo medico" (anti-projects).
Un dashboard de "riesgo zoonotico personalizado" puede caer en ese bote
y morir en Stage 1.

Lenguaje PROHIBIDO en UI, video, README, SUBMISSION:
- "tu riesgo", "riesgo para tu salud", "que hacer si vives en X",
  "probabilidad de contagio humano", "recomendacion sanitaria",
  "R0", "diagnostico", "prevencion personal".

Lenguaje OBLIGATORIO (wildlife / ecologico / vigilancia):
- "ecological surveillance for researchers, not medical advice"
- "wildlife susceptibility", "surveillance priority",
  "supply-chain exposure (poultry/dairy, county-level)",
  "detection pressure", "reservoir community".
- Exposure humana: presentarla SOLO como "ecological overlap /
  surveillance proxy", nunca como riesgo personal. Declarar el proxy.

Disclaimer visible en web + README + video (1 linea):
"WildSeek is an ecological surveillance research tool for wildlife
professionals. Not medical advice, not for personal health decisions."

Enfoque wildlife, NO zoonosis humana, NO medicina:
- El paper fuerte es parasitos generalistas (pool na_ca ~2.5k spp),
  no clinica humana.
- H5N1 en demo = spillover en mamiferos + exposicion de supply chain
  (watershed/county), no enfermedad humana.
- No construir: recomendaciones sanitarias, mapas de riesgo personal,
  estimadores de R0, triaje clinico, nada que un filtro lea como
  "medical advice".

---

## 4. DISENO FULL-TEXT PMC GENERAL (4 capas, barato)

Principio: nunca pasar un paper completo de ~8k tokens al modelo caro.
90% del texto es descartable por reglas gratis; 5-10% llega a Muse.

Capa 0 — Ingesta local, costo cero:
- Por PMCID: bajar XML BioC desde PMC OA API (o crawl.ecoseek.org para no-OA).
- Parsear por secciones con reglas. Guardar: Methods, Results, Tables,
  Figure legends, Supplementary mention. Descartar: Intro, Discussion,
  References, Acknowledgements.
- Por que: los misses del gold33 son "especies en tablas", que viven en
  Results/Tables/Legends. Intro/Discussion solo mete ruido y tokens.
- Implementacion: script pmc_fetch.py sobre dump PubMed 166G + FTS para
  resolver PMCID desde PMID/DOI (reusar DoiDict). Guardar sections.parquet
  por PMCID. Sin LLM. Cache en disco, nunca re-fetch.

Capa 1 — Triaje local gratis (glimmer / spark-open Fireworks):
- Clasificador binario barato por chunk ~500 tokens:
  "contiene posible par host-parasito concreto o no_detection?"
- Solo chunks YES pasan a Capa 2. Un paper tipico: 15-20 chunks, 2-3 YES.
  Recorte 80-85% de tokens caros.
- Prompt de ~10 lineas, temperature 0, salida YES/NO + nombres.
- Backend: glimmer MI210 local o muse-spark-open Fireworks ($100 credito
  intacto). MetaClient.local / backend fireworks ya cableados en
  litmine/extract.py; agregar --stage triage.

Capa 2 — Extraccion tipada Muse contributor (cara del producto):
- Solo chunks YES entran a muse-spark-1.2/1.3-contributor
  ($0.10 in / $0.20 out). Mismo schema de extract.py + campo nuevo
  obligatorio: source_section (abstract/table/results/legend) + table_id.
- Tablas como texto linealizado:
  "Table 2 row: host=X, n=12, positive=3, tissue=spleen".
  No parsear XML perfecto; texto plano + LLM basta.
- Costo: ~3 chunks x 700 tokens x $0.10/M = ~$0.0002/paper. 10k papers ~$2.
- Regla hackathon: todo edge del demo debe salir de Muse (producto
  Muse-only). Lo local es pre-filtro interno.

Capa 3 — Dedupe + reconcile (local, sin LLM):
- Normalizar TaxID a especie aceptada (rank species NCBI), colapsar
  duplicados por (parasite_sp, host_sp, relation) guardando lista de
  PMIDs + mejor span. Guardar cepa original en columna.
- Por que: PubTator devuelve TaxIDs a nivel cepa/serotipo; sin esto se
  inflan edges 2-3x y el leakage audit mata el claim prospectivo.
- Extender name_reconcile.py (ya usado para GBIF-BirdTree). Publicar la
  regla de colapso en Methods.

Optimizaciones obligatorias:
1. Cache PubTator3 por PMID + cache PMC XML por PMCID (resume ya existe
   en edges; extender a secciones).
2. Batch PubTator 100 PMIDs + batch PMC OA 50.
3. Tablas primero: si ya salieron 5+ edges de tablas, saltar Discussion.
4. Skip list: reviews/editoriales sin datos primarios (YES=0) gastan cero.
5. Ledger de costo por paper en agent_calls.jsonl (patron factory).
   Cada edge muestra su costo ("full sweep $0.00" en demo).

Orden de construccion (no invertir):
G1 precision abstract (30 edges a mano) -> Capa 0 sobre gold33 (medir
cuantas misses se vuelven recuperables) -> Capa 1 triaje sobre esos 33
-> Capa 2 full sobre 165 PMIDs ZOVER -> comparar recall abstract vs full.
Luz verde si recall sube de 16% a >50% con costo <$1.

---

## 5. IDEAS CIENTIFICAS PRIORIZADAS (que + por que + como)

Prioridad P0 (48h): leakage audit + ablacion negativos + we-called-it.
Sin leakage audit los numeros son papel mojado.

1. [P0] Leakage audit por par normalizado.
   Que: para cada edge test, buscar par host-parasito (TaxID a especie)
   en todo el training sin importar PMID.
   Por que: invalida/confirma el claim prospectivo de un plumazo.
   Como: cruzar 217 edges ZOVER + gold 283 contra corpus training.
   Reportar % pares realmente nuevos vs re-publicaciones.

2. [P0] Ablacion negativos reales vs pseudo-absences.
   Que: modelo A con no_detection reales ZOVER vs modelo B con
   pseudo-absences aleatorias del pool na_ca.
   Por que: GMPD/HP3 sufren falsos negativos; xplus + negativos reales
   es superioridad metodologica. Es Figura 2 del paper.
   Como: comparar calibracion (reliability) y AUC en VIRION gold 283.

3. [P0] Tarjeta "we called it" (demo + Figura 4 del paper).
   Que: prediccion congelada a fecha T + PMID posterior que la confirma.
   Por que: unico demo que un juez entiende en 10s; Figura 4 del paper.
   Como: buscar en 217 edges el mejor caso retrospectivo, congelar fecha,
   bakear a JSON estatico (patron explain/briefing ya existente).

4. [P1] Validacion prospectiva mensual (tesis del paper).
   Congelar dist_frame + p_host a fecha T (ej. pre-2024), evaluar
   AUC/recall contra edges con PMID >= T. Repetir mensual, curva AUC vs
   tiempo. Titulo candidato: "Phylogeny, environment and accessibility
   predict cross-species parasite sharing: prospective validation from
   living literature mining".

5. [P1] M-mask anti-artefacto.
   Jaccard env con vs sin M-mask en 50 pares que comparten parasito.
   Mostrar inflacion 2-3x sin mask. Activo: env_cube + 844 ecoregiones.

6. [P1] Separar competence vs exposure (2 scores, nunca mezclar).
   p_host (phy+env intrinseco) vs riesgo (p_host x deteccion x overlap).
   Matriz 2x2 con ZOVER 5.9k: alta p_host + baja exposicion (vigilar)
   vs baja p_host + alta exposicion (ruido de muestreo).

7. [P1] Host-switching: distancia patristica host-host vs distancia
   genomica viral (8 FASTA bat/rodent/mosquito/tick -> mafft -> TN93).
   Scatter x=patristic, y=viral distance, color=grupo. Prediccion:
   generalistas = arbol viral plano vs arbol hospedero profundo.

8. [P1] Tissue tropism como filtro.
   Re-etiquetar 217 edges con tissue_class (sistemica vs pasaje) desde
   BioSample. p_host debe predecir mejor las sistemicas. Delta >0.05 AUC
   = metodo publicable. VIRION no distingue.

9. [P1] Vector-bridged pairs (mosquito/tick como conectores).
   Grafo vertebrado <-> vector <-> virus. Prediccion: pares conectados
   solo via vector tienen menor env-overlap que transmision directa.

10. [P1] reservoir_of vs parasite_of como tasks jerarquicas.
    Dos cabezas xplus: reservoir_of ~ phy-cercania, parasite_of ~
    geo-overlap. Testeable con corpus 10k + scores PU.

11. [P1] Sesgo de literatura (revisor hostil #1).
    effort = n pubs por hospedero (FTS PubMed) vs p_host. Re-correr con
    effort como covariado; si phy+env sobreviven, el ataque cae.
    GBIF duckdb 41GB + env_cube ya disponibles.

12. [P2] Recall 16% -> two-stage (no esconder el numero).
    Precision abstract alta y barata; recall se recupera con full-text PMC
    solo en candidatos alta p_host. Probar en 10 PMIDs gold con misses,
    medir delta recall/costo. Vender eficiencia, no recall bruto.

13. [P2] Flag is_patristic_real en dist_frame.
    Repetir AUC solo con patristic real vs mixto con proxy taxonomico
    (179 spp). Reportar main solo con real si el mixto infla.

14. [P2] Monitor diario como ticker vivo (demo).
    Delta diario PubMed -> S0 -> extract -> dedupe -> store por fecha ->
    brief. Pre-registrar p_host antes de ver el abstract. Tabla visible.

15. [P2] Cost meter honesto en UI ("217 edges $0.00, 119 calls").
    Loguear tokens desde meta_client.py (cost_usd ya existe).

---

## 6. FEATURES DEMO QUE VENDEN (orden de impacto)

1. We-called-it card (sec 5, idea 3). Estatica, cero inferencia live.
2. Evidence chain click-through: score -> desglose phy/env/geo ->
   arista -> span resaltado -> PMID -> metodo + tejido + geo/fecha.
   Anti-blackbox que los jueces premian.
3. Ticker monitor diario (sec 5, idea 14). Prueba "living" vs VIRION static.
4. Cost meter (sec 5, idea 15). Eficiencia sobre Meta API.
5. Desglose por eje en /explain existente + suitability PNG con M-mask.

Requisitos live: abrir <3s, funcionar sin key (baked JSON), /health vivo,
video grabado como backup para la final Nov 9.

---

## 7. QUE NO CONSTRUIR (aunque haya presupuesto)

1. No full-text sobre todo PubMed 166G. Solo corpus filtrado
   (score PU alto + ZOVER + gold). El resto es quemar dinero en ceros.
2. No filogenia viral propia ni reloj molecular. Con 8 FASTA solo
   distancias crudas; un dated viral es overclaim mortal.
3. No mezclar H5N1-clade con ZOVER en el mismo paper. H5N1 = demo
   producto; parasitos generalistas = paper. Mezclarlos confunde.
4. No agregar tipos de relacion ni modelos nuevos. Congelar schema
   (parasite_of/reservoir_of/vector_of/no_detection + 3 raros
   existentes). Cada tipo nuevo divide 217 edges y destruye power.
5. No RAG generico ni chatbot educativo (anti-projects = descalificacion
   funcional por puntaje cero en tooling).
6. No re-ingerir VIRION como producto. Solo benchmark interno
   (terminos heredados LGPL/agregados turbios). Edges propios con
   provenance primaria.

---

## 8. TAREAS PARA DEVIN (contrato)

D1. pmc_fetch.py (Capa 0): PMID/DOI -> PMCID -> secciones -> sections.parquet.
    Cache disco + resume. Probar sobre gold33: reportar % misses abstract
    recuperables desde Results/Tables/Legends.
D2. Triaje local (Capa 1): --stage triage en extract.py, chunks 500 tok,
    YES/NO. Medir % tokens ahorrados en gold33.
D3. Extraccion full-text (Capa 2): chunks YES -> contributor tipado +
    source_section + table_id. Salida al mismo schema edges.csv.
D4. Reconcile + dedupe (Capa 3): TaxID -> species rank, colapso
    (parasite_sp, host_sp, relation), lista PMIDs. Regla documentada.
D5. Leakage audit (P0): pares test vs training normalizados. Tabla %.
D6. Ablacion negativos (P0): A reales vs B pseudo-absences. AUC + reliability.
D7. We-called-it cards x3 (P0): JSON estatico + UI + links PMID.
D8. Disclaimer medico + renombre "health risk" -> "surveillance priority"
    en UI, README, SUBMISSION, video script. Grep de palabras prohibidas
    (sec 3) debe dar cero antes del release.
D9. Verificar strings Meta grepeables en snapshot publico
    (muse-spark-1.3, contributor, wonder, glimmer, spark-open) + /health.
D10. Video script 3 min (estructura sec 2/stage + linea pre-existente vs
    construido en 0:00). Ver docs/video-script.md existente y actualizar.

Gates: no corpus grande (D3 a escala) sin D1+D5. No claims prospectivos
sin D5. No release sin D8+D9 (grep prohibidas = 0, grep modelos > 0).

---

## 9. ANGULO PAPER (4 figuras max)

Titulo: "Phylogeny, environment and accessibility predict cross-species
parasite sharing: prospective validation from living literature mining".
Estructura IMRaD alrededor de hipotesis falsables, no "presentamos software".
Fig1: dos fabricas acopladas (WildSeek scores -> litmine valida -> loop).
Fig2: ablacion tres distancias + negativos reales (barras AUC + CI bootstrap).
Fig3: scatter host-phy vs viral-genetic O curva AUC prospectiva mensual
  (una a main, otra a supplement).
Fig4: caso we-called-it (prediccion pre-fecha + PMID confirmatorio).
Demo H5N1 + monitor diario van a Methods/Supplement. No application note.
