#!/usr/bin/env bash
set -euo pipefail

repo=/workspace
parts="$repo/local_dataset/ReplicaSSG_download"
habitat_configs="$parts/additional_habitat_configs.zip"
runtime="$repo/local_dataset/ReplicaSSG_runtime"
annotations="$repo/local_dataset/ReplicaSSG_code/files"
scans="$repo/experiments/H001_geom_reliability/sources/replicassg/prospective_protocol/frozen_v1/test_scans.txt"

test -f "$parts/replica_v1_0.tar.gz.partaa"
test "$(find "$parts" -maxdepth 1 -name 'replica_v1_0.tar.gz.part??' | wc -l)" -eq 17
for suffix in {a..p}; do
  test "$(stat -c %s "$parts/replica_v1_0.tar.gz.parta$suffix")" -eq 2000000000
done
test "$(stat -c %s "$parts/replica_v1_0.tar.gz.partaq")" -eq 1859047808
test "$(stat -c %s "$habitat_configs")" -eq 40793904

mkdir -p "$runtime/data" "$runtime/ReplicaSSG"
cp "$annotations"/* "$runtime/ReplicaSSG/"
cp "$annotations/replica.scene_dataset_config.json" "$runtime/data/replica.scene_dataset_config.json"

patterns=()
while IFS= read -r scene; do
  test -n "$scene" || continue
  patterns+=("$scene/habitat/*")
  patterns+=("$scene/mesh.ply")
done < "$scans"

missing_mesh=0
while IFS= read -r scene; do
  test -n "$scene" || continue
  if [ ! -f "$runtime/data/$scene/habitat/mesh_semantic.ply" ] \
    || [ ! -f "$runtime/data/$scene/mesh.ply" ]; then
    missing_mesh=1
  fi
done < "$scans"

if [ "$missing_mesh" -eq 1 ]; then
  cat "$parts"/replica_v1_0.tar.gz.part?? \
    | tee >(sha256sum > "$runtime/replica_v1_0.combined.sha256") \
    | gzip -dc \
    | tar -x -C "$runtime/data" --wildcards "${patterns[@]}"
else
  test -s "$runtime/replica_v1_0.combined.sha256"
fi

python - "$habitat_configs" "$runtime/data" "$scans" <<'PY'
import pathlib
import sys
import zipfile

archive, destination, scans_path = map(pathlib.Path, sys.argv[1:])
scans = {line.strip() for line in scans_path.read_text().splitlines() if line.strip()}
with zipfile.ZipFile(archive) as handle:
    for info in handle.infolist():
        if info.filename.split("/", 1)[0] in scans:
            handle.extract(info, destination)
PY

while IFS= read -r scene; do
  test -n "$scene" || continue
  test -f "$runtime/data/$scene/habitat/mesh_semantic.ply"
  test -f "$runtime/data/$scene/mesh.ply"
  test -f "$runtime/data/$scene/habitat/info_semantic.json"
  test -f "$runtime/data/$scene/habitat/replica_stage.stage_config.json"
  test -f "$runtime/data/$scene/habitat/sorted_faces.bin"
done < "$scans"

find "$runtime/data" \( -path '*/mesh.ply' -o -path '*/habitat/mesh_semantic.ply' -o -path '*/habitat/info_semantic.json' \
  -o -path '*/habitat/replica_stage.stage_config.json' -o -path '*/habitat/sorted_faces.bin' \) \
  | sort | xargs sha256sum > "$runtime/test_habitat_checksums.sha256"
