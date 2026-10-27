# Hackathon rules — respuestas del bot de Discord (organizadores)

> Anotado 2026-10-27. Respuestas oficiales del bot/organizadores en Discord.

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
  ya cumple "standalone extract, sin historia de devel".
- Etiquetar como pre-existente en video + SUBMISSION:
  - framework de tres distancias (Robles-Fernández et al. 2022, PNAS —
    DOI en README)
  - árbol de mamíferos `v6_point.nwk` (phyloseek-devel, trabajo previo
    del lab — no es dataset público; declararlo)
  - BirdTree/VertLife, Ecoregions2017, GBIF, APHIS, ERA5 (datasets
    públicos — citar)
- Todo el código de WildSeek se escribió durante la semana del evento —
  declarar eso también en la línea de apertura del video.
- Track: Indie (sin entidad legal registrada).
