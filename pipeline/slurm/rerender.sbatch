#!/bin/bash
#SBATCH --job-name=rerender
#SBATCH --partition=sixhour
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --output=/beegfs/a474r867/meta-hack/logs/rerender_%j.log
#SBATCH --error=/beegfs/a474r867/meta-hack/logs/rerender_%j.err
if [ ! -d /beegfs/a474r867 ]; then exit 53; fi
cd /beegfs/a474r867/meta-hack
set -e
python3 render_3857.py risk_1120.tif risk.png --cmap turbo --vmax 1
python3 render_3857.py risk_detect_1120.tif risk_detect.png --cmap turbo --vmax 1
ls suit/suit_*.tif | sed 's/.*suit_\(.*\)\.tif/\1/' | \
  xargs -P 8 -I {} python3 render_3857.py suit/suit_{}.tif suit_png/suit_{}.png --cmap viridis --vmax 1
echo "pngs: $(ls suit_png/*.png | wc -l)"
python3 export_serve.py --src /beegfs/a474r867/meta-hack --dst /beegfs/a474r867/meta-hack/serve_data
echo DONE
