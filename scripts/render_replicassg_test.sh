#!/usr/bin/env bash
set -euo pipefail

repo=/workspace
runtime="$repo/local_dataset/ReplicaSSG_runtime"
code="$repo/local_dataset/ReplicaSSG_code"
scans="$repo/experiments/H001_geom_reliability/sources/replicassg/prospective_protocol/frozen_v1/test_scans.txt"

while IFS= read -r scene; do
  test -n "$scene" || continue
  python "$code/extract_path.py" \
    --replica_path "$runtime/data" \
    --scene "$scene" \
    --replica_to_vg_path "$runtime/ReplicaSSG/replica_to_visual_genome.json" \
    --trajectory_json "$runtime/ReplicaSSG/trajectories.json" \
    --output_dir "$runtime/data"
done < "$scans"
