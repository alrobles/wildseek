#!/bin/bash
#SBATCH --job-name=pred_%a
#SBATCH --partition=sixhour
#SBATCH --time=06:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --output=/beegfs/a474r867/meta-hack/logs/pred_%A_%a.log
#SBATCH --error=/beegfs/a474r867/meta-hack/logs/pred_%A_%a.err
# array task: SLURM_ARRAY_TASK_ID = shard index; env N_SHARDS
if [ ! -d /beegfs/a474r867 ]; then exit 53; fi
export R_LIBS=/beegfs/a474r867/rlib_442
SIF=/home/a474r867/geospatial-rserver/xsdm_latest.sif
N_SHARDS=${N_SHARDS:-1}
apptainer exec --cleanenv --env R_LIBS="$R_LIBS" --bind /beegfs "$SIF" \
  Rscript /beegfs/a474r867/meta-hack/predict_suit.R \
  "$SLURM_ARRAY_TASK_ID" "$N_SHARDS"
