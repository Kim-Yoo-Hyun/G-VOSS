#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=${REPO_ROOT:-$(cd -- "$script_dir/.." && pwd)}
mode=${1:-all}

if [[ -n "${RESTORE_EXIT_FILE:-}" ]]; then
  trap 'rc=$?; printf "%s\n" "$rc" > "$RESTORE_EXIT_FILE"' EXIT
fi

download_dataset() {
  local destination="$repo/local_dataset/ReplicaSSG_download"
  mkdir -p "$destination"
  cd "$destination"
  for suffix in {a..q}; do
    printf '%s\n' "https://github.com/facebookresearch/Replica-Dataset/releases/download/v1.0/replica_v1_0.tar.gz.parta${suffix}"
  done | xargs -n 1 -P 8 wget -c
  wget -c "http://dl.fbaipublicfiles.com/habitat/Replica/additional_habitat_configs.zip"
  for suffix in {a..p}; do
    test "$(stat -c %s "replica_v1_0.tar.gz.parta${suffix}")" -eq 2000000000
  done
  test "$(stat -c %s replica_v1_0.tar.gz.partaq)" -eq 1859047808
  test -s additional_habitat_configs.zip
}

download_weight() {
  mkdir -p "$repo/local_dataset/FROSS_weights"
  docker run --rm \
    -v "$repo:/workspace" \
    -w /workspace \
    python:3.11-slim-bookworm \
    sh -lc 'pip install --no-cache-dir gdown==5.2.0 && gdown --continue --id 1glMkDC1UPQbd8JfjQa6VzNQRwMDAnOsI -O /workspace/local_dataset/FROSS_weights/VG.zip'
}

case "$mode" in
  dataset) download_dataset ;;
  weight) download_weight ;;
  all)
    download_dataset
    download_weight
    ;;
  *)
    echo "usage: $0 [dataset|weight|all]" >&2
    exit 2
    ;;
esac
