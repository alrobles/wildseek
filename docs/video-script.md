# WildSeek — 3-minute demo script (v2, 2026-11-03)

On-screen footer throughout: "Ecological surveillance for wildlife
professionals — not medical advice." Badge "built during the event"
fixed under the video for its whole duration.

VO budget: ~420 palabras a ~140 wpm. Números finales del submission
(2026-11-03): 101,376 fits / 1,147 species / 4,854 edges / 3,740 pairs /
282 papers / $0.0014 por edge / recall 56% vs 16% / p_host AUC 0.74 en
53 held-out / we-called-it 4/15 / 2,247 HUC8 / 3,109 counties /
9,139 APHIS detections.

## Cold open — required declaration (0:00–0:15)

- Screen: slate fija, dos columnas: "pre-existing" (xnicher,
  oneearthr, the PNAS 2022 three-distance framework, phyloseek
  mammal tree, BirdTree/VertLife, GBIF/APHIS/ERA5 data, ecoseek
  stack) vs "built this week" (everything else shown here).
- VO: "Rule check first: the niche-fitting engine, the phylogenies
  and the surveillance data predate this event — everything else was
  built this week. And what we built fitted 101,376 climate niche
  models, scored 1,147 species for H5N1 susceptibility — and froze
  its predictions in public. The literature is already confirming
  them."

## Act 1 — stakes (0:15–0:30)

- Screen: map with HPAI detections layer on. 9,139 wild-bird positives.
- VO: "H5N1 has already jumped to 74 mammal species and put the virus
  inside dairy herds — the same supply chain behind egg prices.
  Detections tell you where it *was*. We built where it can go next."

## Act 2 — the build (0:30–1:15)

- Screen: species picker → suitability layer fades in on a bird
  species. Switch species a couple of times; the map repaints.
- VO: "101,376 ellipsoid niche fits — 88 candidates per species —
  against 30-year ERA5 normals, each masked to that species' own
  occupied ecoregions. Every fit AIC-scored, all accepted — the
  winner predicts this layer. Below it: phylogenetic distance on
  real trees — BirdTree for birds, a dated mammal tree — reconciled
  to GBIF names."

## Act 3 — agentic teeth (1:15–2:00)

- Screen: decisions delta card → litmine ticker → we-called-it card.
- VO: "An agent watches the campaign — but only the ambiguous tail
  reaches it: 173 suspect fits, 49 back as `flag_review` with reasons,
  every verdict an executable refit in an auditable delta. A second
  loop reads the literature itself: 4,854 typed parasite–host edges
  at $0.0014 each, judge-verified — and full text beats abstracts
  three to one on held-out recall. Then we froze the top-15
  unlabelled hosts publicly — four already carry a freshly-mined
  host edge. Every number on screen came from the pipeline — the
  models audit and narrate; they never invent one."

## Act 4 — product answer + living system (2:00–2:45)

- Screen: risk layer = detection recency × host-weighted reservoir
  community, aggregated to HUC8 — named watersheds ranked; cut to
  county exposure (dairy herds / egg-layer fields).
- VO: "Recency-weighted detections times the host-weighted reservoir
  community — risk at one kilometre, ranked across 2,247 named
  watersheds and exposure for 3,109 counties, dairy and egg-layer
  country included. And it isn't a frozen demo — every night it
  re-fetches APHIS, decides whether to re-fit, gates the deploy on
  a three-of-four quorum with a cost veto, and ships."

## End card (2:45–3:00)

- Screen: wildseek.ecoseek.org live → /we-called-it card.
- VO: "WildSeek — live now. The frozen predictions are on
  /we-called-it — watch the literature catch up."

## Visual split for the "new work" rule

- Bottom-corner badge during acts 2–4: "built during the event" vs a
  short "pre-existing" slate listing xnicher/oneearthr/GBIF
  mirror/ERA5 collection/ecoseek (per NEW.md).

## Capture checklist

- [ ] Slate pre-existing vs built (regla: la línea abre el video)
- [ ] Mapa con capa de detecciones APHIS (9,139)
- [ ] Species picker → repaint por especie ×2-3
- [ ] decisions_delta.csv / card con razones de los 49 flag_review
- [ ] Litmine ticker (/litmine) + metrics ($0.0014/edge)
- [ ] we-called-it card (freeze 2026-10-28, 4/15)
- [ ] Risk layer → tabla HUC8 rankeada → county exposure
- [ ] /briefing o nightly manifest para el beat "corre cada noche"
- [ ] End card: URL + /we-called-it
