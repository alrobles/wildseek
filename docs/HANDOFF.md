# WildSeek handoff — 2026-10-27

Continuar el desarrollo desde **reumanlab-terminal** mientras la laptop está
apagada. Todo el estado está en cluster (beegfs) + este repo; la laptop no es
necesaria salvo indicado.

## Estado actual

- **Deploy público**: `ecoseek-wildseek` en terminal `:8654` →
  `https://wildseek.ecoseek.org` (túnel cloudflared `~/.cloudflared/wildseek.yml`,
  corre con nohup — pierde el proceso si terminal reinicia; relanzar:
  `cloudflared tunnel --config ~/.cloudflared/wildseek.yml run`)
- **Repo**: `~/GitHub/meta-hack-devel` (privado, origin) → releases curados a
  `meta-hack` (remote `public`) vía `scripts/release.sh` (gate muse-spark).
- **Job corriendo**: `finish2` = `32354212` — cadena completa post-M:
  build_risk → risk_watershed → county_exposure → render_3857 (1132 PNGs) →
  export a `serve_data`. Verificar:
  `ssh kuhpc 'sacct -j 32354212 --format=State; tail -20 /beegfs/a474r867/meta-hack/logs/finish_32354212.log'`

## Qué cambió desde el deploy actual

1. **Suitability enmascarado a M** — los 1132 tifs en `beegfs:.../suit/` están
   cortados a las ecorregiones con 95% de presencias de cada especie
   (`predict_suit.R` + `eco_conus_1120.tif`). Los PNGs en producción son
   viejos (sin máscara, CRS 4326) — re-render 3857 corre en finish2.
2. **Modelo de susceptibilidad PNAS** (`pipeline/`):
   `env_geo_jaccard.py` → `jaccard_{env,geo}.parquet`;
   `phy_dist.R` → `data/phy_dist.csv` (mamíferos reales, árbol v6 phyloseek);
   `species_labels.py` → 159 positivos (143 aves + 16 mamíferos, capas
   `hpai_wildbirds_usa` + `hpai_mammals_usa` del mirror OSU);
   `dist_frame.py` → `data/dist_frame.parquet`;
   `suscept_model.py` → `data/serve/susceptibility.parquet`
   **logreg_poly2 ext ganó: ROC-AUC 0.876** (importancias geo>env>phy).
   Aves = phy `taxa_proxy` hasta tener BirdTree/VertLife.
3. **Detecciones a nivel especie** — `aphis_wild_birds_species.parquet`
   (9,070) + `aphis_mammals_species.parquet` (208) exportan a
   `detections.geojson` con `species`+`strain`+`year`.
4. API: `/susceptibility` + `p_host` join en `/species`; app: badges
   P(host)/known-host/flag_review, popup de detección por especie.

## Tras completar finish2 (32354212)

```bash
ssh -J reumanlab-terminal kuhpc   # o directo si ya estás en mesh
B=/beegfs/a474r867/meta-hack

# 1. verificar PNG enmascarado: océano alpha=0 Y bordes de M
python3 - <<'PY'
import rasterio
# spot-check un PNG 3857 + su .meta.json
PY

# 2. serve_data debe incluir susceptibility.parquet + species detections
ls $B/serve_data/ | grep -c suit_   # esperado ~1132
python3 -c "import pandas as pd; print(pd.read_parquet('$B/serve_data/susceptibility.parquet').head())"

# 3. sync a terminal (datos en el host, volumen ro)
rsync -a $B/serve_data/ terminal:/home/alrobles/wildseek/data/

# 4. rebuild + restart
ssh alrobles@<terminal>  # o el alias del mesh
cd /home/alrobles/wildseek && docker compose up -d --build
curl -s localhost:8654/health | python3 -m json.tool
curl -s localhost:8654/susceptibility?top=5 | python3 -m json.tool
curl -s https://wildseek.ecoseek.org/health

# 5. re-hornear agente (briefing ahora incluye susceptibilidad)
#    MODEL_API_KEY: export MODEL_API_KEY=$(cat ~/env/meta-key) en la laptop;
#    en terminal verificar si existe el archivo o usar muse-glimmer local:
#    http://127.0.0.1:20007/v1 (MetaClient.local() en agent/)
python3 pipeline/precompute_agent.py   # DATA=app/data
```

## Reglas duras

- Nada de compute en el login node de kuhpc — todo vía `sbatch`/`srun`,
  partición `sixhour` (≤6h), **siempre `--exclude='r05r10n0[1-3]'`**
  (esos chasis matan jobs al arrancar, exit 0:53).
- SSH a kuhpc desde esta máquina va con `-J reumanlab-terminal`.
- `data/` y `app/data/` están gitignored — nunca commitear.
- No leer `~/env` salvo `meta-key` por nombre exacto; no pegar secretos.
- Commits al `origin` (devel) libremente; al `public` solo vía
  `scripts/release.sh` (corre review de muse-spark-1.3 antes del push).

## Pendiente después

- **Árbol de aves**: birdtree.org (request form) o VertLife — sustituye el
  `taxa_proxy` de 881 aves en `phy_dist.R` + re-corre dist_frame/modelo.
- **phylopred PU scores** como capa extra (solo si sobra tiempo).
- Docs: actualizar README/SUBMISSION con el modelo de susceptibilidad.
- Video 3min (guion en `docs/video-script.md`).

## Verificación rápida

```bash
squeue -u a474r867                    # jobs vivos
ls $B/suit_png/*.png | wc -l          # 1132 esperado
curl -s https://wildseek.ecoseek.org/meta.json | python3 -c \
  "import json,sys; m=json.load(sys.stdin); print(m.get('n_susceptibility'), m.get('n_detections'))"
# esperado: 1147, 9278 (9070 aves + 208 mamíferos)
```
