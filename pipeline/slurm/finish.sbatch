#!/bin/bash
#SBATCH --job-name=finish2
#SBATCH --partition=sixhour
#SBATCH --time=03:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --exclude=r05r10n01,r05r10n02,r05r10n03
#SBATCH --output=/beegfs/a474r867/meta-hack/logs/finish_%j.log
#SBATCH --error=/beegfs/a474r867/meta-hack/logs/finish_%j.err
if [ ! -d /beegfs/a474r867 ]; then exit 53; fi
cd /beegfs/a474r867/meta-hack
mkdir -p suit_png serve_data
set -x

echo "=== RISK $(date -Is)"
python3 build_risk.py
echo "=== WATERSHED $(date -Is)"
python3 risk_watershed.py
echo "=== COUNTY EXPOSURE $(date -Is)"
python3 county_exposure.py
echo "=== RENDER 3857 $(date -Is)"
ls suit/suit_*.tif | xargs -P 8 -I{} sh -c \
  'b=$(basename {} .tif); [ -f suit_png/$b.png ] || python3 render_3857.py {} suit_png/$b.png'
echo "=== EXPORT $(date -Is)"
python3 export_serve.py --src /beegfs/a474r867/meta-hack \
  --dst /beegfs/a474r867/meta-hack/serve_data
echo "=== DONE $(date -Is)"
