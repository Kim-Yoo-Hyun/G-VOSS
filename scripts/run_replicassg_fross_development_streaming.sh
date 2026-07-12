#!/usr/bin/env bash
set -euo pipefail

repo=/home/yoohyun/research
compose="$repo/configs/fross/compose.yaml"
runtime="$repo/local_dataset/ReplicaSSG_runtime"
frozen_scans="$repo/experiments/H001_geom_reliability/sources/replicassg/prospective_protocol/frozen_v1/test_scans.txt"
runtime_scans="$runtime/ReplicaSSG/test_scans.txt"
development="$repo/experiments/H001_geom_reliability/sources/replicassg/development_v2/runtime"
current="$repo/experiments/H001_geom_reliability/sources/replicassg/fross_raw/replica/predictions_gaussian_obj0.7_rel10_hell0.85_kfnone_test_gtpose.pkl"
shards="$development/fross_raw/shards"
cleanup_log="$development/fross_raw/transient_sequence_cleanup.jsonl"

test -f "$frozen_scans"
test -d "$runtime/ReplicaSSG"
mkdir -p "$shards" "$(dirname "$current")"

restore_split() {
  cp "$frozen_scans" "$runtime_scans"
}
trap restore_split EXIT

while IFS= read -r scene; do
  test -n "$scene" || continue
  shard="$shards/$scene.pkl"
  container_shard="/workspace/${shard#"$repo/"}"
  if [[ -f "$shard" ]]; then
    REPLICASSG_EXPECTED_SCENE="$scene" REPLICASSG_SHARD="$container_shard" \
      docker compose -f "$compose" run --rm replicassg_validate_shard
    rm -rf "$runtime/data/$scene/sequence" "$runtime/data/$scene/textures"
    continue
  fi

  printf '%s\n' "$scene" > "$runtime_scans"
  rm -rf "$runtime/data/$scene/sequence"
  REPLICASSG_SCENE="$scene" docker compose -f "$compose" run --rm replicassg_extract_scene_textures
  REPLICASSG_SCENE="$scene" docker compose -f "$compose" run --rm replicassg_render_scene
  docker compose -f "$compose" run --rm inference_test
  test -f "$current"
  mv "$current" "$shard"
  REPLICASSG_EXPECTED_SCENE="$scene" REPLICASSG_SHARD="$container_shard" \
    docker compose -f "$compose" run --rm replicassg_validate_shard

  sequence="$runtime/data/$scene/sequence"
  test -f "$sequence/_info.txt"
  files=$(find "$sequence" -type f | wc -l)
  bytes=$(du -sb "$sequence" | cut -f1)
  texture_files=$(find "$runtime/data/$scene/textures" -type f | wc -l)
  texture_bytes=$(du -sb "$runtime/data/$scene/textures" | cut -f1)
  shard_sha=$(sha256sum "$shard" | cut -d' ' -f1)
  printf '{"scene":"%s","verified_shard_sha256":"%s","deleted_sequence_files":%s,"deleted_sequence_bytes":%s,"deleted_texture_files":%s,"deleted_texture_bytes":%s}\n' \
    "$scene" "$shard_sha" "$files" "$bytes" "$texture_files" "$texture_bytes" >> "$cleanup_log"
  rm -rf "$sequence" "$runtime/data/$scene/textures"
done < "$frozen_scans"

restore_split
docker compose -f "$compose" run --rm replicassg_development_v2_merge_shards
