#!/bin/bash
#SBATCH --job-name=ws-nightly
#SBATCH --partition=sixhour
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --exclude=r05r10n01,r05r10n02,r05r10n03
#SBATCH --output=/beegfs/a474r867/meta-hack/logs/nightly_%j.log
if [ ! -d /beegfs/a474r867 ]; then exit 53; fi
cd /beegfs/a474r867/meta-hack
set -x
python3 build_risk.py && \
python3 risk_watershed.py && \
python3 county_exposure.py && \
python3 render_3857.py risk_1120.tif risk.png --cmap turbo --vmax 1 && \
python3 export_serve.py --src /beegfs/a474r867/meta-hack \
  --dst /beegfs/a474r867/meta-hack/serve_data
