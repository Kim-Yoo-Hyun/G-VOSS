#!/usr/bin/env bash
set -euo pipefail

repo=/workspace
parts="$repo/local_dataset/ReplicaSSG_download"
runtime="$repo/local_dataset/ReplicaSSG_runtime"
scans="$repo/experiments/H001_geom_reliability/sources/replicassg/prospective_protocol/frozen_v1/test_scans.txt"
scene=${REPLICASSG_SCENE:?REPLICASSG_SCENE is required}

test "$(grep -Fxc "$scene" "$scans")" -eq 1
test -s "$runtime/replica_v1_0.combined.sha256"
test "$(find "$parts" -maxdepth 1 -name 'replica_v1_0.tar.gz.part??' | wc -l)" -eq 17

if [ ! -d "$runtime/data/$scene/textures" ]; then
  cat "$parts"/replica_v1_0.tar.gz.part?? \
    | gzip -dc \
    | tar -x -C "$runtime/data" --wildcards "$scene/textures/*"
fi

test -d "$runtime/data/$scene/textures"
test "$(find "$runtime/data/$scene/textures" -type f | wc -l)" -gt 0
