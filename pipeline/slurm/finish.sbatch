#!/bin/bash
#SBATCH --job-name=finish
#SBATCH --partition=sixhour
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --output=/beegfs/a474r867/meta-hack/logs/finish_%j.log
#SBATCH --error=/beegfs/a474r867/meta-hack/logs/finish_%j.err
if [ ! -d /beegfs/a474r867 ]; then exit 53; fi
cd /beegfs/a474r867/meta-hack
set -e

echo "== build_risk (detect + det x mean aves suit) =="
python3 build_risk.py

echo "== risk_watershed =="
python3 risk_watershed.py

echo "== render risk png =="
python3 render_png.py risk_1120.tif risk.png --cmap turbo --vmax 1
python3 render_png.py risk_detect_1120.tif risk_detect.png --cmap turbo --vmax 1

echo "== render suit pngs (parallel, skip-existing) =="
mkdir -p suit_png
ls suit/suit_*.tif | sed 's/.*suit_\(.*\)\.tif/\1/' | \
  xargs -P 8 -I {} sh -c '[ -f suit_png/suit_{}.png ] || \
  python3 render_png.py suit/suit_{}.tif suit_png/suit_{}.png --cmap viridis --vmax 1'
echo "pngs: $(ls suit_png/*.png | wc -l)"

echo "== export serve_data =="
python3 export_serve.py /beegfs/a474r867/meta-hack /beegfs/a474r867/meta-hack/serve_data
echo DONE
