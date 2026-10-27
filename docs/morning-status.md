# WildSeek — estado al despertar (2026-10-27 ~08:00 UTC)

## LIVE: https://wildseek.ecoseek.org

Contenedor `ecoseek-wildseek` (compose `wildseek`) en terminal,
`127.0.0.1:8654`, volumen ro `~/wildseek/app/data`. Túnel cloudflared
dedicado `34ab0a08-722e-48a8-b907-9e24817d16a0` corriendo vía nohup
(`~/.cloudflared/wildseek.yml`, log `/tmp/wildseek-tunnel.log`) —
**pendiente persistirlo** como el resto (watchdog/systemd o donde
vivan los otros; muere si terminal reinicia).

## Lo que se hizo esta noche

1. **Bug crítico corregido**: `conus_normals.py` compartía `cnt`
   entre las 19 bandas → normales = media/19 → todas las
   suitability ≈ 0. Recomputado (job 32353577), validado:
   bio01 p50 10.17°C, ocean NaN 31% restaurado.
2. **Re-predict completo**: 1,147 rasters suit_*.tif sobre normales
   correctas (job 32353596). Verificado: p50 0.23, p90 0.76, max 1.0.
3. **Risk de 2 etapas** (job 32353667): detecciones con half-life
   90d + kernel ~10km, × media de suitability de aves →
   `risk_1120.tif` → agregado a **2,247 HUC8 con nombre**
   (Piscataqua-Salmon Falls #1). 1,147 PNGs renderizados.
4. **Capa agentic real**: `decide_tail.py` corrió las 173 especies
   ambiguas (AIC-tie, n<60, marine>0.4, M degenerado) por
   muse-spark-1.3 → **49 flag_review** con razones sustantivas en
   `decisions_delta.csv` (changed=true). Ningún drop ni switch_to —
   el agente juzgó que los casos son de datos, no de familia.
5. **Artefactos horneados**: briefing (muse-wonder) + 16 explains
   (spark) en app/data — el demo corre sin MODEL_API_KEY. Costo
   total de la noche en API Meta: ~$1.20 (T1 completo) + $0.5 (tail)
   + $0.06 (precompute+script).
6. **Auditoría respondida**: D1 flyways→MultiPolygon (fill), D2
   requests, D3 retry limpio, D4 methods_note sustantivo, D5 imports
   + health stamp. NEW.md + SUBMISSION.md + video-script pulido por
   wonder.

## Pendiente deliberado / para ti

- **Repo público**: acción del owner (auditoría la exige).
- **suit PNGs a terminal**: stream beegfs→local en curso cuando se
  hizo este doc (~1500/2300); segundo rsync local→terminal corre
  en paralelo; si quedara alguno, `rsync -a app/data/
  reumanlab-terminal:wildseek/app/data/` lo cierra.
- **Persistir el túnel**: ver arriba (ahora es nohup).
- **Video**: guion en `docs/video-script.md` listo para grabar.
- **Spend limit + créditos Meta**: paso manual del audit.
- phylopred PU layer quedó fuera (documentado en SUBMISSION.md).

## Cómo verificar rápido

```
curl https://wildseek.ecoseek.org/health
curl https://wildseek.ecoseek.org/briefing
curl https://wildseek.ecoseek.org/risk/watershed?limit=5
ssh reumanlab-terminal "docker ps | grep wildseek"
```
