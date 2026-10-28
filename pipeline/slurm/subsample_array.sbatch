#!/bin/bash
#SBATCH --job-name=sub_%a
#SBATCH --partition=sixhour
#SBATCH --time=06:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=logs/sub_%A_%a.log
#SBATCH --error=logs/sub_%A_%a.err
# array task: SLURM_ARRAY_TASK_ID = shard index
# env: N_SHARDS, N_STARTS (SPEC run dir must exist: $B/subsample_v1/)
B="${WILDSEEK_BEEG:?set WILDSEEK_BEEG to the staging dir}"
[ -d "$B" ] || exit 53
[ -f "$B/subsample_v1/tasks.parquet" ] || exit 54
export R_LIBS="${WILDSEEK_RLIBS:-$(dirname "$B")/rlib_442}"
SIF="${WILDSEEK_SIF:-$HOME/geospatial-rserver/xsdm_latest.sif}"
N_SHARDS=${N_SHARDS:-1}
N_STARTS=${N_STARTS:-60}
apptainer exec --cleanenv --env R_LIBS="$R_LIBS" \
  --env WILDSEEK_BEEG="$B" \
  --env WILDSEEK_DOMAIN="${WILDSEEK_DOMAIN:-conus}" \
  --bind "$(dirname "$(dirname "$B")")" "$SIF" \
  Rscript "$B/subsample_run.R" \
  "$B/subsample_v1/tasks.parquet" "$SLURM_ARRAY_TASK_ID" "$N_SHARDS" "$N_STARTS"
