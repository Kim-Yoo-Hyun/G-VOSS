#!/usr/bin/env bash
set -euo pipefail

parts=/workspace/local_dataset/ReplicaSSG_download
cat "$parts"/replica_v1_0.tar.gz.part?? \
  | gzip -dc \
  | tar -tvf - \
  | awk '
    $6 ~ /^(apartment_1|apartment_2|office_1|office_3|office_4|room_1|room_2|hotel_0|frl_apartment_3|frl_apartment_4|frl_apartment_5)\/habitat\// {habitat_sum += $3; habitat_count += 1}
    $6 ~ /^(apartment_1|apartment_2|office_1|office_3|office_4|room_1|room_2|hotel_0|frl_apartment_3|frl_apartment_4|frl_apartment_5)\/(mesh\.ply|textures\/)/ {render_sum += $3; render_count += 1}
    END {printf "test_habitat_files=%d\ntest_habitat_bytes=%.0f\ntest_parent_render_files=%d\ntest_parent_render_bytes=%.0f\n", habitat_count, habitat_sum, render_count, render_sum}'
