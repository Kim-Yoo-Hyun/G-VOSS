#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

BUNDLE_DIR="results/h001_geom_reliability/full_validation_transition/artifact_bundle"
SHA_FILE="${BUNDLE_DIR}/upload_payload_sha256s.txt"

if [[ ! -f "$SHA_FILE" ]]; then
  echo "missing checksum file: $SHA_FILE" >&2
  exit 2
fi

sha256sum -c "$SHA_FILE"

expect_lines() {
  local expected="$1"
  local path="$2"
  local actual
  actual="$(wc -l < "$path")"
  if [[ "$actual" != "$expected" ]]; then
    echo "row-count mismatch: $path expected=$expected actual=$actual" >&2
    exit 3
  fi
}

expect_jq() {
  local expected="$1"
  local path="$2"
  local query="${3:-.status}"
  local actual
  actual="$(jq -r "$query" "$path")"
  if [[ "$actual" != "$expected" ]]; then
    echo "status mismatch: $path query=$query expected=$expected actual=$actual" >&2
    exit 4
  fi
}

expect_lines 548 experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/raw.jsonl
expect_lines 957008 experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl
expect_lines 11254 experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl
expect_lines 957008 experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl
expect_lines 3972 experiments/H001_geom_reliability/sources/vlsat/full_validation/gt_eval/gt_positive.jsonl
expect_lines 3972 experiments/H001_geom_reliability/sources/vlsat/full_validation/gt_eval/counterfactuals.jsonl
expect_lines 59841 experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/rows.jsonl
expect_lines 36 experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/queue.jsonl

expect_lines 26746 experiments/H001_geom_reliability/sources/open3dsg/full_validation/raw_dump/raw.jsonl
expect_lines 690924 experiments/H001_geom_reliability/sources/open3dsg/full_validation/adapter/predictions.jsonl
expect_lines 690924 experiments/H001_geom_reliability/sources/open3dsg/full_validation/geometry/verification.jsonl
expect_lines 81448 experiments/H001_geom_reliability/sources/open3dsg/full_validation/failure_rows/rows.jsonl

expect_lines 26938 experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/raw_dump/raw.jsonl
expect_lines 695916 experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl
expect_lines 695916 experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl
expect_lines 82155 experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/rows.jsonl
expect_lines 36 experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/queue.jsonl

expect_jq ready experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics/metrics.json
expect_jq ready experiments/H001_geom_reliability/sources/vlsat/full_validation/bootstrap_ci/summary.json
expect_jq ready experiments/H001_geom_reliability/sources/vlsat/full_validation/gt_eval/metrics.json
expect_jq qualitative_case_inspection_ready experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/inspection.json

expect_jq ready experiments/H001_geom_reliability/sources/open3dsg/full_validation/metrics/metrics.json
expect_jq ready experiments/H001_geom_reliability/sources/open3dsg/full_validation/bootstrap_ci/summary.json
expect_jq open3dsg_full_validation_table_caveats_ready experiments/H001_geom_reliability/sources/open3dsg/full_validation/table_caveats/manifest.json

expect_jq ready experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics/metrics.json
expect_jq ready experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/bootstrap_ci/summary.json
expect_jq open3dsg_full_validation_table_caveats_ready experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/table_caveats/manifest.json
expect_jq qualitative_case_inspection_ready experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/inspection.json

echo "h001 full-validation upload bundle verification passed"
