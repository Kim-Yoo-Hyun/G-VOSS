#!/usr/bin/env bash
set -euo pipefail

repo=${REPO_ROOT:-/home/yoohyun/research}
compose="$repo/configs/fross/compose.yaml"
output="$repo/experiments/H001_geom_reliability/sources/replicassg/development_v2/evaluation"

if [[ -n "${PIPELINE_EXIT_FILE:-}" ]]; then
  trap 'rc=$?; printf "%s\n" "$rc" > "$PIPELINE_EXIT_FILE"' EXIT
fi

cd "$repo"
test "$(find local_dataset/ReplicaSSG_download -maxdepth 1 -name 'replica_v1_0.tar.gz.part??' | wc -l)" -eq 17
test "$(sha256sum local_dataset/FROSS_weights/VG.zip | cut -d' ' -f1)" = "03dc86a1a0f40321a2caa0e35ec2739f458837365455017b5a830a0f5349467c"
docker compose -f "$compose" config --quiet
env UID=$(id -u) GID=$(id -g) docker compose -f "$compose" run --rm weight_extract
env UID=$(id -u) GID=$(id -g) docker compose -f "$compose" run --rm engine_export
env UID=$(id -u) GID=$(id -g) docker compose -f "$compose" run --rm replicassg_extract_test_habitat
env UID=$(id -u) GID=$(id -g) docker compose -f "$compose" run --rm instance_ply
PATH="$repo/scripts/no_stdin_bin:$PATH" env UID=$(id -u) GID=$(id -g) \
  bash scripts/run_replicassg_fross_development_streaming.sh
env UID=$(id -u) GID=$(id -g) docker compose -f "$compose" run --rm replicassg_development_v2_adapter
env UID=$(id -u) GID=$(id -g) docker compose -f "$compose" run --rm replicassg_development_v2_geometry
test ! -e "$output"
env UID=$(id -u) GID=$(id -g) docker compose -f "$compose" run --rm replicassg_development_v2
env UID=$(id -u) GID=$(id -g) docker compose -f "$repo/configs/h001/compose.yaml" run --rm bounded_fusion_cross_source
