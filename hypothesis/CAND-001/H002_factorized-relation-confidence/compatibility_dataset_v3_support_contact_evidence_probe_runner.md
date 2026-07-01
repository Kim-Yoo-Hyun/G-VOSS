# Compatibility Dataset V3 Support/Contact Evidence Probe Runner

## Status

```text
status = h002_compatibility_dataset_v3_support_contact_evidence_probe_runner_blocks_numeric_support_smoke
selected_path = route_to_visual_mesh_or_role_orientation_evidence
next = compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan
validation_errors = 0
```

## Purpose

이 단계는 `support_contact`를 바로 learned smoke로 넘기지 않고, 현재 train-side numeric
artifact만으로 predicate-conditioned compatibility `C_e`를 검증할 수 있는지 확인하기 위한
evidence probe다. 특히 `standing on`, `lying on`, `supported by`가 단순 거리/overlap/gap
perturbation으로 맞춰지는지, 아니면 predicate별로 다른 geometry evidence가 필요한지를 먼저
검사한다.

## Inputs

```text
plan = artifacts/compatibility_dataset_v3_support_contact_evidence_probe_plan/
rga_queue = artifacts/train_rga_full/open3dsg_train_full/rga/
v2_schema = artifacts/compatibility_dataset_v2_schema_shortcut_audit/
v2_candidates = artifacts/compatibility_dataset_v2_candidate_materialization/
v2_failure = artifacts/compatibility_dataset_v2_failure_analysis/
```

The runner intentionally does not scan the full 17GB `match_rows.jsonl`. It only uses the
train-side HL/LH queue files and existing v2 diagnostic artifacts.

## Outputs

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_evidence_probe_runner/
summary.json
path_decision.json
source_inventory.json
source_inventory.csv
same_or_near_geometry_capacity.csv
exact_pair_preview.jsonl
evidence_axis_inventory.csv
negative_policy_audit.csv
shortcut_precheck.csv
report.md
validation_errors.jsonl
```

## Key Results

```text
support_queue_rows = 161498
distinct_directed_pairs = 75763
distinct_visible_pairs = 4109
distinct_scans = 1157
exact multi-predicate mixed-geometry groups = 75
non-hard-surface exact candidate groups = 4
support_contact_materialization_allowed = false
visual_mesh_or_role_orientation_required = true
diagnostic_only = true
```

현재 수량 자체는 충분해 보이지만, clean support/contact target으로 쓸 수 있는 후보는 크게
줄어든다. 특히 exact directed pair 안에서 mixed geometry status를 보이는 group은 75개뿐이고,
floor/wall/ceiling 같은 hard-surface shortcut을 제외한 non-hard-surface exact candidate group은
4개뿐이다. 이 수량은 reportable support/contact compatibility smoke를 만들기에는 부족하다.

## Evidence Axis Diagnosis

Available or partial:

- distance, 3D/XY separation, projected overlap/IoU;
- vertical gap and object top/bottom z;
- support-order proxy from OBB z ranges.

Missing required axes:

- `role_orientation_pose`;
- `contact_direction_surface_normal`;
- `mesh_visual_multiview`.

Interpretation:

`standing on`, `lying on`, `supported by`는 모두 접촉/지지 계열이지만, 필요한 evidence가 서로
다르다. 거리와 overlap만 있으면 "가까운가/겹치는가"는 볼 수 있어도, 사람이 서 있는지 누워
있는지, 접촉 방향이 지지면과 맞는지, surface normal이 실제 support를 설명하는지는 분리하기
어렵다. 따라서 현재 numeric-only `G_e`는 support/contact family의 `C_e`를 검증하기 위한 주
evidence로 쓰기 어렵다.

## Shortcut Diagnosis

High-risk probes:

```text
hidden_counterfactual_type = 1.000
hidden_row_role = 1.000
hidden_geometry_status_baseline = 1.000
```

These are hidden/provenance probes, not allowed model features. The result still matters because
it confirms that v2 support/contact rows were construction-route dependent. Direct learned smoke
over those rows would likely repeat the previous failure: the model could learn generated
geometry perturbation rather than predicate-conditioned semantic-geometry compatibility.

## Decision

```text
support_contact_materialization_allowed = false
selected_path = route_to_visual_mesh_or_role_orientation_evidence
next = compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan
```

H002 should not proceed to a numeric-only support/contact learned smoke from the current v2/v3
artifacts. The next step is to plan an evidence extension that can expose role/orientation,
contact direction, surface normal, mesh, visual, or multi-view information while keeping source
score and construction proxy fields out of the model input.

## Boundary

- Train-only evidence probe.
- No learned smoke.
- No validation/test usage.
- No paper-level evidence promotion.
- No H001 artifact modification.
