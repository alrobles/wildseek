#!/bin/bash
#SBATCH --job-name=risk
#SBATCH --partition=sixhour
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --output=/beegfs/a474r867/meta-hack/logs/risk_%j.log
if [ ! -d /beegfs/a474r867 ]; then exit 53; fi
cd /beegfs/a474r867/meta-hack
python3 build_risk.py
