#!/bin/bash
#SBATCH --job-name=env_occ
#SBATCH --partition=sixhour
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=36G
#SBATCH --output=/beegfs/a474r867/meta-hack/logs/env_occ_%j.log
#SBATCH --error=/beegfs/a474r867/meta-hack/logs/env_occ_%j.err

# meta-hack env_occ extraction — runs on a compute node, never login.
# BeeGFS sanity: some nodes lack the mount (KB: exit 0:53) — check first.
if [ ! -d /beegfs/a474r867 ]; then
  echo "BeeGFS not mounted on $SLURMD_NODENAME" >&2
  exit 53
fi

PY=/beegfs/a474r867/miniconda3/envs/genoml-phylo/bin/python3
cd /beegfs/a474r867/meta-hack
"$PY" env_occ.py mammalia aves
