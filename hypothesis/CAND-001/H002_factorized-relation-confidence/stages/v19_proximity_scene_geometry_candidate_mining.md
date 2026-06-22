# V19 Proximity Scene/Geometry Candidate Mining

Date: 2026-06-22 KST

## Purpose

v18 repair plan에서 고정한 contract에 따라 `close by` / proximity LH branch의
scene/geometry-aware label-ready sheet를 생성했다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v13_proximity_lh_scene_geometry_candidate_mining/
    summary.json
    report.md
    label_ready_sheet_v13.tsv
    hidden_audit_manifest_v13.jsonl
    selected_candidates_internal.jsonl
    selected_block_summary.csv
    visible_leakage_hits.jsonl
    validation_errors.jsonl
    review_cards_v13/
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_candidate_mining_ready_for_label_fill
next_todo = reliability_target_v13_proximity_lh_scene_geometry_label_fill
```

## Main Result

```text
selected_rows = 240
selected_blocks = 30
rows_per_block = 8
unique_scans = 182
unique_subgraphs = 196
raw_feature_joined_rows = 240
visible_leakage_hits = 0
validation_errors = 0
```

각 block은 visible subject-object label pair 하나를 sampling unit으로 사용한다. 각 block에서
8개 row를 뽑았고, hidden audit 기준으로 최소 다음 다양성을 확보했다.

```text
block_label_match_hidden_min_values = 2
block_rank_band_hidden_min_values = 3
block_p_geom_bin_hidden_min_values = 3
```

## What Changed From V12

v12는 object-pair text만 visible evidence로 제공해서 label이 object-pair identity로 거의
결정됐다.

v19 candidate sheet는 같은 object-pair 안에서도 scene context에 따라 label이 달라질 수
있도록 다음 visible evidence를 제공한다.

```text
scene_context_summary_v13
geometry_witness_summary_v13
nearest_neighbor_context_v13
local_density_context_v13
duplicate_or_many_alternatives_context_v13
crop_or_layout_evidence_v13
```

반면 다음 값은 hidden audit manifest에만 둔다.

```text
semantic_rank
semantic_score_norm
p_geom_valid
rank_band
label_match_status
machine_hint
target_construction_block
raw_features
```

## Claim Boundary

이 단계는 label-ready sheet 생성 단계다. 아직 label fill, ingestion, target-independence
audit이 끝나지 않았으므로 posterior evidence가 아니다.

## Next

```text
reliability_target_v13_proximity_lh_scene_geometry_label_fill
```

다음 단계에서는 visible scene/geometry evidence만 사용해 `relation_reliability_state_v13`를
채운 뒤, hidden audit manifest와 join하여 target-independence audit으로 넘어간다.
