# V18 Proximity Scene/Geometry Repair Plan

Date: 2026-06-22 KST

## Purpose

v17에서 선택한 `scene/geometry-aware target repair` 경로를 실제 candidate mining으로
넘길 수 있는지 확인하고, v13 repair plan의 evidence contract와 target schema를 고정했다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v13_proximity_lh_scene_geometry_repair_plan/
    summary.json
    report.md
    repair_plan.json
    evidence_contract.json
    target_schema_v13.json
    candidate_mining_contract.json
    repair_group_inventory.csv
    top_repair_groups.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_repair_plan_ready
next_todo = reliability_target_v13_proximity_lh_scene_geometry_candidate_mining
```

## Main Finding

```text
repair_pool_rows = 50966
visible_pair_groups = 5122
v13_block_candidate_groups = 1510
strong_v13_block_candidate_groups = 778
candidate_capacity_cap8 = 11520
candidate_group_goal_pass = true
candidate_capacity_goal_pass = true
```

즉, `close by` proximity LH branch는 수량 부족으로 막힌 상태가 아니다. 현재 blocker는
v12처럼 object-pair text만 보고 label을 채우면 target이 object-pair identity로 풀린다는 점이다.

## Repair Principle

v13은 posterior 결합 방식을 바꾸는 단계가 아니다. 바뀌는 것은 label evidence surface다.

```text
v12: visible object-pair text -> proxy label
v13: local scene/geometry evidence -> relation reliability label
```

목표는 같은 visible subject-object label pair 안에서도 scene context에 따라 reliable /
unreliable `close by`가 갈릴 수 있는 candidate block을 만드는 것이다.

## Evidence Contract

Reviewer-visible evidence:

```text
scene_context_summary_v13
geometry_witness_summary_v13
nearest_neighbor_context_v13
local_density_context_v13
duplicate_or_many_alternatives_context_v13
crop_or_layout_evidence_v13
```

Reviewer-hidden audit fields:

```text
semantic_rank
semantic_score_norm
p_geom_valid
rank_band
label_match_status
machine_hint
subject_object_label_pair
target_construction_block
```

금지되는 visible evidence:

```text
source semantic rank / score
machine_hint
label_match_status
GT matched predicate names
target construction bucket
posterior score
raw p_geom_valid numeric value
```

## Target Schema

```text
relation_reliability_state_v13:
  accept_reliable_close_by
  reject_dense_relation_noise
  reject_trivial_or_context_only
  abstain_uncertain
```

Binary mapping:

```text
accept_reliable_close_by -> 1
reject_dense_relation_noise -> 0
reject_trivial_or_context_only -> 0
abstain_uncertain -> excluded from binary target
```

## Next

```text
reliability_target_v13_proximity_lh_scene_geometry_candidate_mining
```

Candidate mining should select about `240` train-only rows from about `30` visible object-pair
blocks, with `6-8` rows per block. Posterior smoke remains blocked until the repaired target
passes target-independence audit.
