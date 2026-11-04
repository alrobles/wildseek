#!/bin/bash
# Fireworks serverless SFT on muse-glimmer-30b (free promo until
# 2026-12-01: training $0; holdout eval sampling billed per-token).
#
# Uses the fw-ai/cookbook muse_glimmer starter (clone at
# $FW_COOKBOOK, pip-installed training/ package). The account's
# managed-SFT dataset upload is disabled, so the serverless surface
# (--file, local JSONL) is the only path that works.
#
# Example invocation (run-ids/datasets are yours):
#
#   export FIREWORKS_API_KEY=<your-key>   # never commit keys
#   tools/fw_starter.sh prepare data/fw_all_train.jsonl my-run-001
#   tools/fw_starter.sh launch  data/fw_all_train.jsonl my-run-001
#
# Rows must be pre-filtered to <=4000 content tokens (chat-template
# overhead pushes ~4060-token rows past --max-seq-len 4096).
# Logs land in $FW_COOKBOOK/muse_starter_logs/<run-id>/; the tuned
# adapter promotes to your account's models/muse-starter-sl-<run-id>.

set -euo pipefail
: "${FIREWORKS_API_KEY:?set FIREWORKS_API_KEY (export it; never commit keys)}"
FW_COOKBOOK=${FW_COOKBOOK:-/tmp/fw-cookbook/training}
CMD=${1:?prepare|launch} FILE=${2:?chat jsonl} RUN=${3:?run-id}
shift 3  # remaining args (e.g. --n-eval N --seed S) pass through
export FIREWORKS_API_KEY

cd "$FW_COOKBOOK"
exec .venv/bin/python -m examples.sft.muse_glimmer_starter "$CMD" \
  --surface serverless --file "$FILE" --run-id "$RUN" --max-seq-len 4096 "$@"
