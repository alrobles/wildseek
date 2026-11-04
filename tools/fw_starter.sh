#!/bin/bash
# Fireworks serverless SFT on muse-glimmer-30b (free promo until
# 2026-12-01: training $0; holdout eval sampling billed per-token).
#
# Uses the fw-ai/cookbook muse_glimmer starter (clone at
# $FW_COOKBOOK, pip-installed training/ package). The account's
# managed-SFT dataset upload is disabled, so the serverless surface
# (--file, local JSONL) is the only path that works.
#
# Exact invocation used for the wildseek "all" run
# (run-id wildseek-all-20261103-233736, session ts-0512de4b658e40eab149ac01e6871c74):
#
#   tools/fw_starter.sh prepare /tmp/wildseek-night/fw_all_train_max4k.jsonl wildseek-all-20261103-233736
#   tools/fw_starter.sh launch  /tmp/wildseek-night/fw_all_train_max4k.jsonl wildseek-all-20261103-233736
#
# Rows were pre-filtered to <=4000 content tokens (chat-template
# overhead pushes ~4060-token rows past --max-seq-len 4096).
# Logs land in $FW_COOKBOOK/muse_starter_logs/<run-id>/; the tuned
# adapter promotes to accounts/alrobles/models/muse-starter-sl-<run-id>.

set -euo pipefail
FW_COOKBOOK=${FW_COOKBOOK:-/tmp/fw-cookbook/training}
CMD=${1:?prepare|launch} FILE=${2:?chat jsonl} RUN=${3:?run-id}
export FIREWORKS_API_KEY=${FIREWORKS_API_KEY:-$(cat ~/env/fireworks-token)}

cd "$FW_COOKBOOK"
exec .venv/bin/python -m examples.sft.muse_glimmer_starter "$CMD" \
  --surface serverless --file "$FILE" --run-id "$RUN" --max-seq-len 4096
