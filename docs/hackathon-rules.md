# Hackathon rules — reglas oficiales + Q&A del bot (organizadores)

> Anotado 2026-10-27.

## Reglas oficiales (Meta Global AI Developer Hackathon)

- **New work only.** Todo lo presentado debe construirse durante el
  hackathon: **Oct 26 – Nov 4**.
- **Identify your contributions.** El demo solo puede mostrar features/
  código/funcionalidad construidas durante el evento; los jueces deben
  poder distinguir qué es nuevo. Si no pueden → descalificado.
- **Public repo** — obligatorio.
- **Teams**: máx 4, solo permitido. Un track: **Indie Developer** o
  **Startup** (Startup requiere entidad legal registrada). Una persona
  hace submit por el equipo.
- **Demo video**: 3 min, requerido en el submission — de lo que más
  puntúan los jueces.
- **Banned**: proyectos que violen políticas legales/éticas/de plataforma
  o usen código/datos/assets **sin derechos**. Evitar genéricos (RAG
  básico, chatbots edu, analizadores de imagen simples, etc.).
- **Theme** — uno de dos problemas:
  - *Build for Your World* — modelos Meta en un dominio propio.
  - *Push the Frontier* — Muse Spark, Glimmer, SAM 3 u otros modelos Meta
    en problemas duros de software/robótica/manufactura/energía/ciencia.
- **Submit**: mié **Nov 4, 9:00 PM ET** —
  https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit
  (repo público + link del video + todos los miembros agregados).
- Waiver: 18+, edad legal local; no staff Meta/CV ni afiliados a gobierno.

## Respuestas del bot de Discord (organizadores)

## Cambiar la idea
Sí. Se puede cambiar de idea o tema en cualquier momento. No hay que
actualizar nada en la plataforma — se fija al hacer submit.

## Construir sobre trabajo existente
Se prefiere empezar de cero. Si se construye sobre trabajo existente,
el repo entregado debe ser un **extracto standalone**: repo público
nuevo con SOLO trabajo hecho durante el evento; el codebase existente
se queda fuera. **No pushear código pre-hackathon ni su git history**
al repo del hackathon. Scaffolding escrito antes del kickoff debe
reescribirse después del kickoff.

El **video de 3 min debe abrir con una línea** declarando qué era
pre-existente y qué se construyó esta semana. Dependencias open-source
y datasets públicos pre-existentes están bien **si se etiquetan**.
Si AgriFlow Copilot específicamente es compatible es decisión de los
organizadores.

## Registro y track
Nada que actualizar ahora. El track se elige en el formulario de
submission. Startup track requiere entidad legal (empresa
constituida); si no está registrada → **Indie track**.

## Pendiente
El usuario preguntó al resto a los organizadores; responderán en Discord.

---

## Implicaciones para WildSeek

- El release snapshot-huérfano (`release.sh`, commit raíz sin historial)
  ya cumple "standalone extract, sin historia de devel". El repo público
  contiene **solo código escrito Oct 26-27** (dentro de la ventana
  oficial) — `data/` es gitignored, así que el árbol v6 ni BirdTree
  viajan al repo. El framework PNAS es solo cita DOI.
- Purga del PDF PNAS = exactamente lo que pide la regla de assets sin
  derechos. Ya hecho.
- **Video**: abrir con la línea pre-existente vs construido, y asegurar
  que el demo solo muestre trabajo del evento.
- Etiquetar como pre-existente en video + SUBMISSION:
  - framework de tres distancias (Robles-Fernández et al. 2022, PNAS —
    DOI en README)
  - árbol de mamíferos `v6_point.nwk` (phyloseek-devel, trabajo previo
    del lab — no es dataset público; declararlo)
  - BirdTree/VertLife, Ecoregions2017, GBIF, APHIS, ERA5 (datasets
    públicos — citar)
- Track: **Indie** (sin entidad legal registrada).
- Theme: calza ambos; **Build for Your World** es el fit natural
  (vigilancia de susceptibilidad wildlife = dominio del PI, usando
  Muse/Glimmer de Meta); Push the Frontier también defensible (ciencia).
- Deadline: Nov 4 9PM ET.
