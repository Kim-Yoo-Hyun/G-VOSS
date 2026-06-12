#!/usr/bin/env bash
set -u

REPO_ROOT="${REPO_ROOT:-/home/yoohyun/research}"
RUN_ID="${QWEN_VL_LOOP_RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
START_SUFFIX="${QWEN_VL_LOOP_START_SUFFIX:-0001}"
END_SUFFIX="${QWEN_VL_LOOP_END_SUFFIX:-0133}"
SHARDS_JSONL="${QWEN_VL_LOOP_SHARDS_JSONL:-experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/shards.jsonl}"
RUNTIME_ROOT="${QWEN_VL_LOOP_RUNTIME_ROOT:-experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime}"
COMPOSE_FILE="${QWEN_VL_LOOP_COMPOSE_FILE:-experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml}"
SERVICE="${QWEN_VL_LOOP_SERVICE:-qwen_vl_full_source_infer_shard}"
SHARD_ENV_VAR="${QWEN_VL_LOOP_SHARD_ENV_VAR:-QWEN_VL_FULL_SOURCE_SHARD_ID}"
STATUS_PREFIX="${QWEN_VL_LOOP_STATUS_PREFIX:-qwen_vl_full_source_infer_remaining}"
LOG_DIR="${REPO_ROOT}/logs"
STATUS_TSV="${LOG_DIR}/${STATUS_PREFIX}_${RUN_ID}.status.tsv"
EXIT_FILE="${LOG_DIR}/${STATUS_PREFIX}_${RUN_ID}.exit"

mkdir -p "${LOG_DIR}"
cd "${REPO_ROOT}" || exit 2

printf "run_id\tshard_id\tevent\ttimestamp\texit_code\n" > "${STATUS_TSV}"

mapfile -t SHARDS < <(
  python - "${SHARDS_JSONL}" "${START_SUFFIX}" "${END_SUFFIX}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
start = sys.argv[2]
end = sys.argv[3]
for line in path.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    shard_id = str(json.loads(line)["shard_id"])
    suffix = shard_id.rsplit("_", 1)[-1]
    if start <= suffix <= end:
        print(shard_id)
PY
)

is_complete() {
  local manifest="$1"
  python - "${manifest}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    sys.exit(1)
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    sys.exit(1)
counts = payload.get("counts") or {}
runtime = payload.get("runtime_result") or {}
expected = int(counts.get("selected_rows") or 0)
completed = int(runtime.get("completed_rows") or 0)
status = payload.get("status")
sys.exit(0 if status == "full_source_inference_shard_complete" and expected > 0 and completed >= expected else 1)
PY
}

if [ "${#SHARDS[@]}" -eq 0 ]; then
  printf "%s\t-\tno_shards\t%s\t2\n" "${RUN_ID}" "$(date -Is)" >> "${STATUS_TSV}"
  printf "2\n" > "${EXIT_FILE}"
  exit 2
fi

for shard in "${SHARDS[@]}"; do
  manifest="${RUNTIME_ROOT}/manifests/${shard}.json"
  if is_complete "${manifest}"; then
    printf "%s\t%s\tskipped_complete\t%s\t0\n" "${RUN_ID}" "${shard}" "$(date -Is)" >> "${STATUS_TSV}"
    continue
  fi

  printf "%s\t%s\tstarted\t%s\t\n" "${RUN_ID}" "${shard}" "$(date -Is)" >> "${STATUS_TSV}"
  echo "started_at=$(date -Is) shard=${shard}"
  sg docker -c "env UID=$(id -u) GID=$(id -g) ${SHARD_ENV_VAR}=${shard} docker compose -f ${COMPOSE_FILE} run --rm ${SERVICE}"
  rc=$?
  echo "finished_at=$(date -Is) shard=${shard} exit=${rc}"
  printf "%s\t%s\tfinished\t%s\t%s\n" "${RUN_ID}" "${shard}" "$(date -Is)" "${rc}" >> "${STATUS_TSV}"
  if [ "${rc}" -ne 0 ]; then
    printf "%s\n" "${rc}" > "${EXIT_FILE}"
    exit "${rc}"
  fi
done

printf "0\n" > "${EXIT_FILE}"
exit 0
