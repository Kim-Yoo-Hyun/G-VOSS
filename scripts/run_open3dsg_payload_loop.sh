#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT="${REPO_ROOT:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
LIMIT="${LIMIT:-100}"
WORKERS="${WORKERS:-4}"
TIMEOUT="${TIMEOUT:-300}"
RETRIES="${RETRIES:-1}"
LOG_DIR="$REPO_ROOT/experiments/H001_geom_reliability/sources/open3dsg/payload"
LOG_FILE="$LOG_DIR/download.log"
COMPOSE_FILE="$REPO_ROOT/configs/h001/compose.yaml"
PAYLOAD_MANIFEST="$REPO_ROOT/experiments/H001_geom_reliability/sources/open3dsg/payload/manifest.json"
TRAIN_MANIFEST="$REPO_ROOT/experiments/H001_geom_reliability/sources/open3dsg/training_repro/manifest.json"

mkdir -p "$LOG_DIR"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG_FILE"
}

update_payload_summary() {
  local tmp
  tmp="$(mktemp)"
  jq --slurp '.[0].global_training_repro_summary = {
    status: .[1].status,
    official_train: .[1].official_train,
    train_dev_without_h001: .[1].train_dev_without_h001,
    train_payload: .[1].train_payload,
    train_dev_payload: .[1].train_dev_payload
  } | .[0]' "$PAYLOAD_MANIFEST" "$TRAIN_MANIFEST" > "$tmp"
  mv "$tmp" "$PAYLOAD_MANIFEST"
  chmod 644 "$PAYLOAD_MANIFEST"
}

while true; do
  ready="$(jq -r '.train_payload.open3dsg_files["mesh.refined.v2.obj"] // 0' "$TRAIN_MANIFEST")"
  expected="$(jq -r '.train_payload.expected_scans // 1178' "$TRAIN_MANIFEST")"

  if [[ "$ready" -ge "$expected" ]]; then
    log "payload complete: train Open3DSG mesh/texture readiness is $ready/$expected"
    break
  fi

  log "starting payload batch: limit=$LIMIT workers=$WORKERS current_mesh_ready=$ready/$expected"
  sg docker -c "env UID=$(id -u) GID=$(id -g) docker compose -f '$COMPOSE_FILE' run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit '$LIMIT' --workers '$WORKERS' --timeout '$TIMEOUT' --retries '$RETRIES'" 2>&1 | tee -a "$LOG_FILE"

  log "refreshing training_repro manifest"
  sg docker -c "env UID=$(id -u) GID=$(id -g) docker compose -f '$COMPOSE_FILE' run --rm open3dsg_train_root --repo-root /workspace" 2>&1 | tee -a "$LOG_FILE"

  update_payload_summary
  jq -c '{status, train_payload, train_dev_payload, target_payload}' "$TRAIN_MANIFEST" | tee -a "$LOG_FILE"
  sleep 30
done
