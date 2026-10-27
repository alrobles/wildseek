#!/bin/bash
#SBATCH --job-name=xni_%a
#SBATCH --partition=sixhour
#SBATCH --time=06:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=/beegfs/a474r867/meta-hack/logs/xni_%A_%a.log
#SBATCH --error=/beegfs/a474r867/meta-hack/logs/xni_%A_%a.err
# array task: SLURM_ARRAY_TASK_ID = shard index
# env: CLS (mammalia|aves), N_SHARDS, N_STARTS
if [ ! -d /beegfs/a474r867 ]; then exit 53; fi
export R_LIBS=/beegfs/a474r867/rlib_442
SIF=/home/a474r867/geospatial-rserver/xsdm_latest.sif
CLS=${CLS:-mammalia}
N_SHARDS=${N_SHARDS:-1}
N_STARTS=${N_STARTS:-60}
apptainer exec --cleanenv --env R_LIBS="$R_LIBS" "$SIF" \
  Rscript /beegfs/a474r867/meta-hack/xnicher_run.R \
  "$CLS" "$SLURM_ARRAY_TASK_ID" "$N_SHARDS" "$N_STARTS"
