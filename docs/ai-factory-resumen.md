# AI Factory — resumen del diseño v2

Diagrama: `ai-factory-diagrama.svg` (abrir en navegador).

## Flujo

1. **Entrada** — petición (voz, GitHub, doc).
2. **Spec writer (Opus)** — escribe la spec; sin spec no hay build.
3. **Builder (Opus, TDD)** — implementa por tareas con test-rojo/código-verde.
4. **4 revisores en paralelo** — Seguridad (Sol), UX (Sol), UI (Astra), Código (Sonnet).
5. **Approver (spark-1.3)** — lee los 4 veredictos y emite juicio final: approve / reject / nota. El quorum aritmético es pre-filtro, no el veredicto.
6. **¿Humano?** — la tabla de criticidad del Brain decide: refit de modelo → PR, cambio de datos >5% → PR, solo refresh → directo a Main.
7. **Producción** — cada corrida deja `qa_report.json` + manifest.

## Reglas duras

- **Quorum**: código + seguridad deben aprobar siempre, y ≥3/4 en total. Seguridad nunca puede ser outvoteada.
- **Retry acotado**: el loop Approver→Builder reintenta 1 vez, luego escala a humano.
- **Gate de costo con veto**: spend acumulado vs presupuesto por corrida; si excede, bloquea aunque el resto apruebe.
- **Brain = constitución**: arquitectura, forma de revisar, estilo de código y tabla de criticidad viven en un solo lugar y gobiernan a todos los agentes.

## Propiedades garantizadas

Auditable (qa_report + manifest por corrida), seguible (spec→tareas→veredictos trazables), arreglable (retry + escala humana), con brain (criterio central, sin drift).

## Brechas v1 → v2 (de la revisión)

| # | Brecha | Fix aplicado en v2 |
|---|--------|-------------------|
| 1 | 3 revisores eran asserts sobre los mismos archivos (1 voto real) | Documentar "3 gates + 1 juez"; dar fuentes independientes a seguridad (diff vs run N-1) |
| 2 | Approver era un AND aritmético, sin juicio | Approver LLM que razona sobre los 4 veredictos |
| 3 | Criterio humano/PR no escrito | Tabla de criticidad en el Brain |
| 4 | Sin límite de gasto en loops autónomos | Gate de costo con veto |
| 5 | TDD prometido en diagrama, ausente en código | Smoke test por stage o quitar del diagrama |

## Estado

Implementado (~70%): `agent/qa.py` (quorum + 4 checks + brain), `pipeline/nightly.py` (conveyor + `needs_human_release`), `scripts/release.sh` (gate de release a público).
Pendiente: approver con juicio (#2), gate de costo (#4), tabla de criticidad explícita (#3), TDD por stage (#5).
