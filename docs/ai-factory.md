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

## Instancia 2: litmine — parásito↔hospedero (diseño)

Mejora sobre cochliomyia_hominivorax v5 (hoy: listas de nombres
extraídas por PubTator3 -> CSV). El salto: de **entidades** a
**relaciones con evidencia**.

```
ENTRADA  PubMed/PMC query -> PubTator3 API
         (entities ya linkeadas: species->NCBI TaxID, diseases->MESH
         — la normalización de sinónimos viene gratis, no regex)
SPEC     cola de papers por staleness/cobertura de query;
         budget diario de tokens
BUILDER  por paper: abstract + anotaciones -> LLM tipado:
         {parasite_taxid, host_taxid,
          relation: parasite_of|host_of|vector_of|reservoir_of,
          evidence_span, confidence}
         — el LLM no hace NER, hace RELACIÓN sobre entidades ya
         anotadas: más barato y auditable (el span está anclado)
JUDGE    S1 re-lee la evidencia contra el span (self-consistency);
         dedupe por (para_taxid, host_taxid, pmid)
ESCALATE confianza baja | taxón fuera de backbone | relación que
         contradice arista existente -> S2 wonder
PRODUC   interactions.parquet (parasite_taxid, host_taxid, relation,
         pmid, evidence, confidence, run_id)
BRAIN    ledger: papers procesados, pares nuevos, precision en
         muestra revisada
```

## La integración que vale el proyecto

`interactions.parquet` es un **EvidenceFeed más de WildSeek**:

- aristas parásito↔hospedero -> `species_labels` por enfermedad
  (los labels del suscept_model dejan de depender solo de APHIS —
  literatura minada etiqueta hospederos en Canadá/Centroamérica
  donde NO hay vigilancia: resuelve el caveat del dominio na_ca)
- vector relations (vector_of) -> la capa trófica para WNV
- aristas nuevas por run -> hypothesis queue del planner

## Orden de construcción

1. `litmine/` extractor: PubTator3 annotate -> typed relation LLM
   (schema primero, igual que fit_judge)
2. calibration set ~100 oraciones etiquetadas -> precision/recall real
3. judge S1 + escalate S2 con caps de budget
4. interactions.parquet -> adapter a `species_labels`
5. ledger + primera corrida full sobre el corpus cochliomyia

Non-goal: re-anotar lo que PubTator3 ya linkea (usar sus TaxIDs,
no inventar nombres); no construir el grafo completo hasta que la
precision del extractor esté medida.
