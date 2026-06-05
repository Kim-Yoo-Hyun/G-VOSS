#!/usr/bin/env bash
set -u

RAW_EXIT="${RAW_EXIT:-logs/open3dsg_eval_h001_gt_objects_nonavg_stream_20260604_182423.exit}"
EXITF="${EXITF:-logs/open3dsg_nonavg_downstream.exit}"
WAIT_MINUTES="${WAIT_MINUTES:-360}"
COMPOSE_FILE="${COMPOSE_FILE:-experiments/H001_geom_reliability/compose.yaml}"

services=(
  open3dsg_raw_dump_identity_nonavg
  open3dsg_adapter_raw_dump_nonavg
  open3dsg_geometry_join_nonavg
  open3dsg_metric_eval_nonavg
  bootstrap_ci_nonavg
  open3dsg_non_avg_table6_caveats
)

echo "launched_at=$(date -Is)"
echo "workdir=$(pwd)"
echo "waiting_for_raw_exit=${RAW_EXIT}"
echo "exit_file=${EXITF}"
echo "compose_file=${COMPOSE_FILE}"

for _ in $(seq 1 "${WAIT_MINUTES}"); do
  if [ -f "${RAW_EXIT}" ]; then
    break
  fi
  sleep 60
done

if [ ! -f "${RAW_EXIT}" ]; then
  echo "raw_exit_timeout_after_minutes=${WAIT_MINUTES}"
  printf "%s\n" 124 > "${EXITF}"
  exit 124
fi

raw_rc_raw="$(tail -n 1 "${RAW_EXIT}")"
raw_rc="$(printf "%s" "${raw_rc_raw}" | tr -cd "0-9")"
echo "raw_exit_code=${raw_rc}"
echo "raw_exit_code_raw=${raw_rc_raw}"
if [ -z "${raw_rc}" ]; then
  echo "raw_exit_code_parse_failed"
  printf "%s\n" 125 > "${EXITF}"
  exit 125
fi
if [ "${raw_rc}" != "0" ]; then
  printf "%s\n" "${raw_rc}" > "${EXITF}"
  exit "${raw_rc}"
fi

for svc in "${services[@]}"; do
  echo "running_service=${svc} started_at=$(date -Is)"
  env UID="$(id -u)" GID="$(id -g)" docker compose -f "${COMPOSE_FILE}" run --rm "${svc}"
  rc="$?"
  echo "service=${svc} exit_code=${rc} finished_at=$(date -Is)"
  if [ "${rc}" != "0" ]; then
    printf "%s\n" "${rc}" > "${EXITF}"
    exit "${rc}"
  fi
done

printf "%s\n" 0 > "${EXITF}"
echo "finished_at=$(date -Is)"
