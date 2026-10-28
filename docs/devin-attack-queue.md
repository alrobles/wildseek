# Devin — cola de ataque (generada del eval_tracker, ordenada por puntos ponderados)

Fuente de verdad: `tools/eval_tracker.py` + `tools/eval_state.json`.
Tras cerrar un gate, actualiza el tracker (ver prompt). Si dudas del orden,
corre `.venv/bin/python tools/eval_tracker.py score` y ataca el top gap.

FASE 0 — supervivencia (sin esto todo lo demás vale 0):
- S1/S2/S3: re-release público (incluye litmine/, cold-open, 5 strings Muse).
  Requiere humano (release.sh + push). Devin deja todo commiteado y avisa.
- S4/S5: HECHO (disclaimer + proveniencia verificada 2026-10-28).

FASE 1 — puntos gordos (en orden):
1. I1_called (+0.90): congelar HOY top-15 unlabeled por p_host con fecha en
   data/serve/we_called_it.json, endpoint /we-called-it, tarjeta UI con
   predicted_on/species/p_host/status:awaiting-confirmation.
2. T1_cascade (+0.75): tira de 4 badges (contributor/spark-1.3/wonder/glimmer)
   con calls+USD desde Spend, + tabla decisions_delta en <details>.
3. I2_confirm (+0.60): buscar 1 caso frozen-prediction confirmada por PMID
   posterior; si no existe, dejar status awaiting y decirlo en voz alta.
4. H2_leak (+0.50): reconcile TaxID->especie, normalizar
   (parasite_sp, host_sp, relation), split temporal por fecha PMID,
   tabla % pares test ya vistos en train.
5. D3_ticker (+0.50): ticker monitor diario (papers->chunks YES->edges->rank),
   filas clicables a span+PMID.
6. T5_ledger (+0.38): append JSONL por llamada LLM
   (ts, model, tokens, usd, pmid/species) desde MetaClient.chat.
7. D4_cost (+0.38): cost meter en UI ($ total, $/edge) desde el ledger.
8. D5_backup (+0.38): grabación backup del demo para la final Nov-9.

FASE 2 — resto (cualquiera suma):
D2_video (grabar video), H5_phy (is_patristic_real + normalización),
H3_prec (G1: 30 aristas a mano), I3_agro (dairy separado de poultry),
T4_glimmer (evidencia self-host), T2_switch (delta visible),
H1_craft (/metrics + tarjeta AUC+CI), I4_eggs (narrativa huevo),
H4_fail (fail-closed completo en dist_frame/suscept_model).

PROHIBIDO (bloquea release):
- Modelos no-Muse en el producto. Mercury/Inception vive solo en tools/dev.
- Lenguaje médico-personal en UI/README/SUBMISSION/video. Grep debe dar 0:
  "tu riesgo|riesgo humano|R0|diagnostico|health risk|human risk".
- Pushear a public o correr release.sh (humano). Commitear a devel sí.
- Re-ingerir VIRION como producto (solo benchmark).
- Nuevos tipos de relación o schemas sin aprobación.
