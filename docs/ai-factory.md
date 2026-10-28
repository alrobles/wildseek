# AI Factory — diseño generalizado (internal)

Patrón de producción que ya corre WildSeek (FACTORY.md = su
constitución). Este doc lo abstrae para que el segundo producto —
**minería de interacciones parásito↔hospedero desde literatura
(PubTator3)** — sea otra instancia de la misma fábrica, compartiendo
sustrato de modelos y verificación.

## El patrón (invariante)

```
ENTRADA   feeds -> raw immutables
SPEC      planner decide qué computar, con qué profundidad, bajo budget
BUILDER   trabajos embarazosamente paralelos (sbatch / api batch)
JUDGE     System-1 tipado verifica cada unidad de trabajo
ESCALATE  confianza baja / señales contradictorias -> System-2
APPROVER  quorum / reglas + juicio -> ¿ship?
PRODUC    artefactos versionados + verificación en destino
BRAIN     manifest por run + ledger de decisiones (se aprende de esto)
```

Sustrato compartido: `MetaClient` (spark-1.3 = S1 pago,
muse-spark-open@fireworks = S1 bulk con crédito, glimmer = S1 gratis
self-host, wonder-1.0 = S2), manifest JSON por run, quorum de review,
release gate curado.

## Instancia 1: WildSeek (existe)

ENTRADA = APHIS/GBIF/ERA5; JUDGE = fit_judge (S1 sobre audit metrics);
S2 = wonder diagnosticando fits patológicos. Ver system-escalation.md.

## Instancia 2: litmine "system zero" — extractor general parásito↔hospedero

Producto: un **extractor zero-shot** de pares parásito-hospedero —
cualquier taxón, cualquier paper, sin código por especie.
cochliomyia_hominivorax (el pipeline del gusano barrenador, que hoy
solo extrae listas de nombres por PubTator3) queda como **corpus de
validación**, no como el producto. La generalidad la da PubTator3:
su NER linkea cualquier taxón mencionado a NCBI TaxID — el extractor
no necesita saber qué especies existen.

```
ENTRADA  scope configurable: (parasite_taxa?, host_taxa?, query) ->
         PubMed/PMC ids -> PubTator3 annotations API
         (entities linkeadas: species->TaxID, diseases->MESH)
S0       filtro de relevancia PRE-LLM sobre el corpus:
         el modelo PU-learning ya entrenado (abstractsHostParasites
         repo, pu_learning_model_*.rds) + corpora etiquetados
         zover_gmpd/lacs/df_parasites (class) como train;
         solo abstracts relevantes pagan tokens de relación
SPEC     cola de papers por staleness; budget diario de tokens;
         dedupe por pmid+span antes de llamar al LLM
BUILDER  por paper: abstract + anotaciones -> LLM tipado, prompt
         agnóstico de taxón:
         {parasite_taxid, host_taxid,
          relation: parasite_of|host_of|vector_of|reservoir_of|
                    intermediate_host_of|dead_end|no_detection,
          evidence_span, confidence,
          geo?, date?, method?, tissue?}
         — Lindsley et al. 2026 (PLOS NTD, VIRION eval): las DBs
         existentes PIERDEN resultados negativos y resolución
         espacio-temporal — nuestro schema los captura
         (no_detection es arista de primera clase; geo/date/
         method/tissue del span, como los samples ZOVER)
         — el LLM no hace NER, hace RELACIÓN sobre entidades ya
         anotadas: más barato y auditable (el span está anclado)
JUDGE    S1 re-lee evidencia contra el span (self-consistency);
         verifica que ambos TaxIDs existen y que parasite!=host
ESCALATE confianza baja | TaxID fuera de backbone | arista que
         contradice el grafo existente -> S2 wonder
PRODUC   interactions.parquet — grafo general, no por-organismo:
         (parasite_taxid, host_taxid, relation, pmid, evidence,
          confidence, run_id, scope_id)
BRAIN    ledger por scope: papers, pares nuevos, precision en
         muestra revisada — el grafo crece por runs incrementales
```

## Capa de datos

| Fuente | Rol en la fábrica |
|---|---|
| PubTator3 API | NER linkeado (TaxID/MESH) — generalidad del extractor |
| crawl.ecoseek.org | crawler propio — fuentes detrás de JS-walls (ZOVER howto/api), PMC full-text no-OA, publisher pages |
| ZOVER (mgc.ac.cn) | aristas curadas virus/huésped/vector zoonótico — semilla del grafo + eval. Export ~5.9k muestras (bat/rodent/mosquito/tick.xlsx): Host species + geo + tejido + BioSample → lado hospedero de la arista; el virus se resuelve vía BioSample/BioProject (o implícito por export). **Nota QA: los nombres de archivo están rotados respecto a su contenido** (bat.xlsx=roedores, rodent.xlsx=mosquitos, mosquito.xlsx=garrapatas, tick.xlsx=murciélagos) — nombrar por contenido al ingerir, nunca por filename |
| **VIRION** (viralemergence/virion) | la mayor DB hospedero↔virus (CLOVER + GenBank diario). **Términos: código LGPL-3.0; los DATOS heredan términos de las DBs componentes (EID2/HP3/Shaw) — el equipo es celoso de la atribución.** Uso nuestro: benchmark interno + chequeo de cobertura, NUNCA re-ingestado como producto. ZeroShot produce aristas propias con procedencia primaria (PMID+span) — más limpio legal y científicamente que re-empaquetar VIRION |
| VIRION S1 (Lindsley 2026 supp) | `data/litmine/virion_ebola_lassa_gold.csv` — 283 aristas virus-hospedero curadas por expertos (complejo Ebola) sobre 33 PMIDs, con geo/fecha/método: **gold standard del extractor** — correr litmine sobre esos PMIDs y medir precision/recall contra curación humana |
| GMPD | aristas mamífero-parásito — semilla del grafo |
| abstractsHostParasites repo (data-raw/) | corpus curado del proyecto abandonado — **salvaje**: etiquetados `df_parasites` (1.9k), `zover_gmpd` (2.2k), `lacs` (6.5k), `db_abstracts`, `df_abstracts_sample`, `df_abstracts_random` (negativos = oro de calibración); corpus por DB `zover_doi` (380), `gmpd_doi` (1.8MB), `parasiteAbstracts` (2.1MB); **`df_abstracts.csv` (9.7MB) lleva columna `score` = output PU ya computado** — el filtro S0 sobre el corpus grande ya existe, no hay que cargar el .rds |
| pu_learning_model (rds, 57MB) | alternativa al score: re-aplicar S0 a corpus nuevo |

## Referencia de arquitectura (sci-litrev / sciev)

El sistema `sci-litrev` (repo privado, litrev.ecoseek.org) ya corre el
mismo patrón sobre otro dominio — referencia de diseño, no dependencia:

| su pieza | equivalente litmine |
|---|---|
| `table.py` seed→extract(ollama JSON)→verify→pivot | BUILDER + JUDGE: PubTator3→LLM tipado→self-consistency |
| `pu.py`/`pu_noul` (PU expansion + scorer) | S0 relevancia (aquí: PU score ya materializado en df_abstracts) |
| `pairs.py` typed pair records | edges.csv con provenance pmid+span |
| sciev noul verify | SystemOne (muse-spark) — el swap que ya planeamos |

Corpus: `/kuhpc/work/kbs/a474r867/pubmed` — baseline completo
`pubmed26n*.xml.gz` (2,669 archivos, dump 2026, 166G) + `parsed/` por
década + `index/pubmed_fts.db` (FTS sobre todo PubMed). La cola de
papers se construye por query FTS in-cluster, no por API externa.

## litmine-monitor — vigilancia continua (el diferenciador)

Las DBs competidoras son snapshots: ZOVER se curó una vez, VIRION
actualiza semanal desde GenBank pero su curación experta es anual.
Un extractor zero-shot corriendo **diario** detecta "nuevo hospedero
reportado" el día que sale el paper — alerta temprana que ninguna
DB curada puede ofrecer. Mismo loop OODA que `nightly.py`:

```
delta:   PubMed ESearch mindate/maxdate (ultimas 24-48h) o los
         updatefiles NCBI del dump local -> PMIDs nuevos del scope
S0:      PU score / query taxa -> solo relevantes pagan tokens
extract: pubtator3 annotate -> S1 relacion (lo que ya corre)
dedupe:  (pmid, parasite_taxid, host_taxid, relation) vs store
store:   interactions.parquet particionado por run_id=fecha
brief:   reporte diario — N papers, M aristas nuevas, taxa nuevos
         (misma superficie BRIEFING que nightly WildSeek)
feed:    aristas nuevas -> species_labels WildSeek -> el siguiente
         fit ya incorpora la evidencia
```

Costo: ~50-200 papers/día en el scope zoonosis/parasitología ->
$0.00-0.05/día en fireworks. El grafo se vuelve **vivo** — eso es lo
que se vende: "literature surveillance as a service" para nuestro
propio modelo y como artefacto publicable por separado.

## Protocolo de validación — la tesis medible

Dos fábricas, un experimento:

```
train:    labels conocidos (ZOVER/GMPD/corpus curado)
          -> suscept_model: phy-dist + env + geo -> p_host
predict:  p_host para especies sin label
validate: edges minados por litmine que NO estaban en training
          -> AUC / PR de p_host contra el test-set minado
```

La tesis: "la distancia filogenética+ambiental+geográfica predice
qué hospederos comparten un parásito". Y el monitor la hace
**prospectiva**: cada paper nuevo valida predicciones ya emitidas.

Advertencias del diseño:
- Independencia parcial: DBs curadas salieron de la misma
  literatura — validar por FAMILIA de evidencia (PMIDs que ningún
  label de training citó = validación fuerte; mismos PMIDs =
  consistencia, no validación)
- Ruido del extractor entra al denominador — validar solo edges
  judge-verificados con confidence >= umbral
- `no_detection` minado = negativos reales que ninguna DB trae ->
  permite medir ESPECIFICIDAD, no solo recall

## La integración que vale el proyecto

`interactions.parquet` es un **EvidenceFeed más de WildSeek**:

- aristas parásito↔hospedero -> `species_labels` por enfermedad
  (los labels del suscept_model dejan de depender solo de APHIS —
  literatura minada etiqueta hospederos en Canadá/Centroamérica
  donde NO hay vigilancia: resuelve el caveat del dominio na_ca)
- vector relations (vector_of) -> la capa trófica para WNV
- aristas nuevas por run -> hypothesis queue del planner

## Orden de construcción

1. `litmine/` extractor general: scope->PMIDs->PubTator3 annotate
   -> typed relation LLM (schema primero, igual que fit_judge)
2. calibration set ~100 oraciones del corpus cochliomyia
   (primer benchmark del extractor general) -> precision/recall real
3. judge S1 + escalate S2 con caps de budget
4. interactions.parquet -> adapter a `species_labels`
5. ledger + primera corrida full (corpus cochliomyia como validación;
   luego scopes amplios: helmintos, protozoos, ectoparásitos)

Non-goal: re-anotar lo que PubTator3 ya linkea (usar sus TaxIDs,
no inventar nombres); no construir el grafo completo hasta que la
precision del extractor esté medida; nada de lógica por-especie —
si un caso necesita código específico de taxón, va al calibration
set, no al extractor.
