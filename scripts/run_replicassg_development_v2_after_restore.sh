#!/usr/bin/env bash
set -euo pipefail

data_exit=${RESTORE_DATA_EXIT:?RESTORE_DATA_EXIT is required}
weight_exit=${RESTORE_WEIGHT_EXIT:?RESTORE_WEIGHT_EXIT is required}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=${REPO_ROOT:-$(cd -- "$script_dir/.." && pwd)}

if [[ -n "${PIPELINE_EXIT_FILE:-}" ]]; then
  trap 'rc=$?; printf "%s\n" "$rc" > "$PIPELINE_EXIT_FILE"' EXIT
fi

while [[ ! -f "$data_exit" || ! -f "$weight_exit" ]]; do
  sleep 30
done

test "$(cat "$data_exit")" = "0"
test "$(cat "$weight_exit")" = "0"
exec "$repo/scripts/run_replicassg_development_v2_pipeline.sh"
