# H002 Prototype Dataset Contract V1

Date: 2026-06-25 KST

## Purpose

이 문서는 새 H002 방향인 `Semantic-Geometry Compatibility Learning for Reliable 3D Scene
Graph Relations`를 검증하기 위한 train-only prototype dataset의 row schema, label axes,
file layout, baseline-ready fields를 고정한다.

핵심 목적은 다음과 같다.

```text
source relation candidate를 그대로 positive로 쓰지 않는다.
no-GT relation candidate를 그대로 negative로 쓰지 않는다.
semantic content, source confidence, geometry evidence, observability, label axes를 분리한다.
```

이 contract는 실제 smoke 성능을 주장하는 문서가 아니다. 다음 단계의 baseline smoke가
shortcut이나 label leakage 없이 실행될 수 있는 최소 데이터 형식을 정의한다.

## Scope

Prototype dataset은 train-side evidence만 사용한다.

Allowed sources:

- train official relation GT;
- train-side relation candidates from Open3DSG/VL-SAT-style relation sources;
- train-side object geometry, OBB, point/mesh features, and existing geometry joins;
- train-side audit labels already produced under H002;
- train-side counterfactual corruptions defined in `counterfactual_protocol_v1.md`.

Forbidden sources:

- validation/test relation annotations for target construction;
- validation/test scans for threshold selection;
- held-out performance used to select positives, negatives, or thresholds;
- hidden construction fields as model inputs.

## Prototype Output Root

Recommended output root:

```text
artifacts/prototype_dataset_v1/
```

Required files:

| File | Role |
| --- | --- |
| `source_candidates.jsonl` | original train-side relation candidates before counterfactual expansion |
| `prototype_rows.jsonl` | model-ready rows with separated `T_e`, `Z_e`, `G_e`, `Q_e`, and label axes |
| `counterfactual_groups.jsonl` | anchor-counterfactual grouping for compatibility learning |
| `baseline_view.jsonl` | flattened fields for simple baselines and shortcut probes |
| `audit_view.jsonl` | label-only and control fields for analysis, not model input |
| `split_manifest.json` | train-only split and source provenance manifest |
| `schema.json` | field names, types, allowed values, and blocked-input declarations |
| `summary.json` | row counts, family counts, label counts, tier counts, and validation result |
| `validation_errors.jsonl` | schema, leakage, split, and target construction errors |
| `report.md` | human-readable summary of the materialized prototype |

No file in this output root is a paper-level result until a separate smoke/baseline report validates
shortcut controls and failure cases.

## Row Identity Fields

Every row in `prototype_rows.jsonl` must contain stable identity fields.

```json
{
  "row_id": "h002_proto_v1_00000001",
  "group_id": "h002_proto_v1_group_000001",
  "row_role": "anchor_positive | counterfactual_negative | source_unknown | observability_probe",
  "split": "train",
  "source_dataset": "Open3DSG_train | VL-SAT_train | mixed_train",
  "relation_source": "open3dsg | vlsat | gt | audit | counterfactual",
  "scan_id": "...",
  "scene_id": "...",
  "subject_instance_id": "...",
  "object_instance_id": "...",
  "directed_pair_id": "...",
  "candidate_relation_text": "chair close by table"
}
```

`scan_id`, `scene_id`, `directed_pair_id`, and endpoint ids are control/provenance fields. They are
allowed in audit/control views but must not be used as model inputs unless the experiment is explicitly
named as a leakage probe.

## Factor Field Blocks

### `T_e`: Semantic Content

`T_e` stores what relation is being claimed.

Required fields:

```json
{
  "T_e": {
    "predicate_label": "close by",
    "predicate_text": "close by",
    "relation_family": "proximity",
    "subject_label": "chair",
    "object_label": "table",
    "subject_object_text": "chair [REL] table",
    "predicate_embedding_id": "optional",
    "subject_class_embedding_id": "optional",
    "object_class_embedding_id": "optional"
  }
}
```

Blocked from `T_e`:

- source score;
- source rank;
- source id;
- official GT match status;
- audit label;
- RGA state;
- counterfactual tier;
- construction proxy role.

### `Z_e`: Source Confidence

`Z_e` stores how strongly the original relation source believed the candidate.

Required fields:

```json
{
  "Z_e": {
    "source_id": "open3dsg",
    "source_score_raw": 0.83,
    "source_score_normalized": 0.71,
    "source_rank": 12,
    "source_rank_band": "top_20",
    "source_score_available": true
  }
}
```

For GT-only positives without a source prediction, use:

```json
{
  "source_id": "official_gt",
  "source_score_available": false,
  "source_score_raw": null,
  "source_score_normalized": null,
  "source_rank": null,
  "source_rank_band": "not_applicable"
}
```

`Z_e` must not enter `C_e`. It is used only by source baselines and final `p_rel`.

### `G_e`: Predicate-Independent Geometry Evidence

`G_e` stores object-pair geometry before knowing the predicate.

Required top-level fields:

```json
{
  "G_e": {
    "geometry_features": {},
    "geometry_feature_mask": {},
    "geometry_feature_units": {},
    "geometry_normalization": "object_scale_and_scene_scale",
    "geometry_source": "obb | point | mesh | mixed"
  }
}
```

Minimum feature groups:

- object geometry: OBB center/size, height, volume, point count;
- pair geometry: center distance, boundary distance, XY distance, `delta_z`, vertical gap,
  projected overlap, 3D overlap, containment ratios;
- contact/support proxy: nearest gap, contact candidate count, support overlap proxy when available;
- generic context: floor/wall proximity, pair direction vector, geometry artifact flags.

Blocked from `G_e`:

- predicate label/text;
- relation family;
- source score/rank/source id;
- official GT or audit label;
- counterfactual construction key.

H001 `p_geom_valid` may be included only as a separated baseline/teacher field:

```json
{
  "p_geom_valid_baseline": 0.92,
  "geometry_status_baseline": "satisfied | violated | uncertain | unsupported | missing"
}
```

These fields are excluded from the main `G_e` input unless the run is explicitly named
`geometry_rule_teacher` or `p_geom_valid_ablation`.

### `Q_e`: Evidence Quality / Observability

`Q_e` stores whether the available evidence is sufficient to decide.

Required fields:

```json
{
  "Q_e": {
    "subject_point_count": 1240,
    "object_point_count": 980,
    "pair_point_count": 3210,
    "mesh_available": true,
    "normal_available": true,
    "same_frame_visible": true,
    "multi_view_count": 4,
    "subject_crop_available": true,
    "object_crop_available": true,
    "pair_crop_available": true,
    "low_coverage_flag": false,
    "missing_geometry_flag": false,
    "unsupported_family_flag": false,
    "evidence_conflict_flag": false,
    "asset_tier": "geometry_only | individual_view_plus_mesh | same_frame_visible"
  }
}
```

`Q_e` supervises or supports `p_obs`. It must not directly decide relation truth.

## Label Axes

Prototype rows use separate label axes. A row may have some labels missing.

### Official GT Axis

```json
{
  "official_gt_axis": {
    "gt_match_status": "exact_match | family_match | pair_has_other_predicate | no_gt_for_pair | unavailable",
    "gt_predicates_for_pair": ["supported by"],
    "gt_family_for_pair": ["support_contact"],
    "gt_source": "official_train_annotation",
    "gt_used_as_model_input": false
  }
}
```

Interpretation:

- `exact_match` can support P0 positive if geometry is usable;
- `family_match` is analysis-only unless the predicate normalization is explicitly defined;
- `no_gt_for_pair` means unknown, not negative;
- GT fields are label/control axes, not model inputs.

### Audit Axis

```json
{
  "audit_axis": {
    "audit_label": "accept_reliable | reject_unreliable | abstain_uncertain | not_audited",
    "geometry_support_label": "supports | contradicts | ambiguous | not_audited",
    "audit_evidence_tier": "same_frame_visible | individual_view_plus_mesh | geometry_only | not_available",
    "audit_provenance": "user_confirmed | codex_visible_packet | codex_diagnostic | official_gt_only | none",
    "audit_hidden_fields_exposed": false
  }
}
```

Interpretation:

- `accept_reliable` can support P1 positive if hidden construction fields were not exposed;
- `reject_unreliable` is evaluation/calibration evidence, but not automatically a compatibility
  negative unless it is tied to a valid counterfactual or contradiction;
- `abstain_uncertain` should supervise or evaluate `p_obs`, not force reject.

### Counterfactual Axis

```json
{
  "counterfactual_axis": {
    "compatibility_label": "positive | counterfactual_negative | unknown",
    "positive_tier": "P0 | P1 | P2 | P3 | none",
    "negative_tier": "N1 | N2 | N3 | N4 | N5 | N6 | none",
    "counterfactual_type": "none | wrong_pair_geometry | shuffled_geometry | predicate_flip | subject_object_swap | relation_specific_perturbation | same_family_rank_coverage_hard_negative",
    "anchor_row_id": "h002_proto_v1_00000001",
    "matching_fields": ["relation_family", "source_id", "source_rank_band", "asset_tier"],
    "relaxed_matching_fields": []
  }
}
```

This is the primary label axis for `C_e`.

Rules:

- positives must come from P0/P1/P2/P3;
- counterfactual negatives must come from N1-N6;
- no-GT source rows remain `unknown` unless a valid positive or counterfactual rule applies;
- low-observability rows should be `observability_probe`, not negative.

### Observability Axis

```json
{
  "observability_axis": {
    "observability_label": "observable | limited | insufficient",
    "observability_reason": "enough_geometry | limited_view | missing_mesh | unsupported_family | evidence_conflict",
    "p_obs_target_usable": true
  }
}
```

This axis trains/evaluates selective decision. It is separated from relation truth.

### Reliability Evaluation Axis

```json
{
  "reliability_eval_axis": {
    "reliability_label": "accept | reject | abstain | unavailable",
    "label_source": "audit | official_gt_plus_geometry | counterfactual | unavailable",
    "binary_usable": true,
    "multiclass_usable": true
  }
}
```

This axis is optional and should be used only for evaluation/calibration. It must be provenance-marked.

## Model Views

The same row must support multiple controlled views.

| View | Inputs | Purpose |
| --- | --- | --- |
| `compatibility_main` | `T_e + G_e` | train/evaluate `C_e`; `Z_e` excluded |
| `source_only` | `Z_e` | source confidence baseline |
| `semantic_source` | `T_e + Z_e` | semantic/source baseline |
| `geometry_rule` | `p_geom_valid_baseline` | H001-style geometry-only baseline |
| `semantic_x_geometry_rule` | `source_score_normalized * p_geom_valid_baseline` | risk-aware soft reranking baseline |
| `concat_mlp` | `T_e + Z_e + G_e + Q_e` | non-factorized neural baseline |
| `obs_head` | `Q_e` plus optional geometry-quality fields | train/evaluate `p_obs` |
| `full_factorized` | `Z_e + C_e + Q_e + optional T_e interaction` | final two-head reliability decision |

Blocked:

- `compatibility_main` cannot use `Z_e`;
- `G_e` cannot include predicate/family/source fields;
- hidden construction fields cannot be used by any deployable model view;
- `official_gt_axis` and `audit_axis` cannot be used as inputs.

## Prototype Sampling Contract

Initial relation families:

| Family | Predicates | Status |
| --- | --- | --- |
| `proximity` | `close by` | include for generality and LH mismatch coverage |
| `relative_vertical` | `higher than`, `lower than` | include as geometry-clear family |
| `support_contact` | `standing on`, `lying on`, `supported by` | include as contact/support family |
| `attachment_deferred` | `attached to`, `hanging on` | include only when mesh/multi-view or strong geometry evidence exists |
| `attachment_deferred` | `connected to` | diagnostic-only until physical connection schema is defined |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | deferred; reference-frame ambiguity must be solved first |
| `containment` | `inside`, `surrounding` | deferred; add after containment schema is frozen |

Recommended prototype target:

```text
families = proximity, relative_vertical, support_contact, attachment_deferred
positive_tiers = P0, P1, P2
optional_positive_tier = P3
negative_tiers = N1, N2, N3, N4, N6
negative_per_positive = 2 to 4
low_observability_rows = separate p_obs subset
connected_to = diagnostic only
```

Do not force equal counts if a family lacks high-precision positives. A family with insufficient
P0/P1/P2 positives should be retained as diagnostic rather than filled with source-only positives.

## Counterfactual Group Contract

Each compatibility group should contain:

```json
{
  "group_id": "h002_proto_v1_group_000001",
  "anchor_row_id": "h002_proto_v1_00000001",
  "anchor_positive_tier": "P0",
  "counterfactual_row_ids": [
    "h002_proto_v1_00000002",
    "h002_proto_v1_00000003"
  ],
  "negative_tiers_present": ["N1", "N3"],
  "matching_fields": {
    "split": "train",
    "relation_family": "support_contact",
    "source_id": "open3dsg",
    "source_rank_band": "top_20",
    "asset_tier": "same_frame_visible"
  },
  "relaxed_matching_fields": []
}
```

Minimum controls:

- same split;
- same relation family;
- same or similar source/rank band when possible;
- same or similar observability tier;
- same scene when possible for N1/N2;
- no trivial endpoint/object-class mismatch unless the row is marked as an easy-negative diagnostic.

## Baseline-Ready Labels

`baseline_view.jsonl` should flatten the following fields.

```json
{
  "row_id": "...",
  "family": "support_contact",
  "predicate_label": "standing on",
  "source_score_normalized": 0.71,
  "source_rank_band": "top_20",
  "p_geom_valid_baseline": 0.92,
  "geometry_status_baseline": "satisfied",
  "compatibility_label": "positive",
  "observability_label": "observable",
  "reliability_label": "accept",
  "binary_usable": true,
  "multiclass_usable": true,
  "hidden_control_available": true
}
```

Baseline tasks:

1. Compatibility task:
   - target: `compatibility_label`;
   - usable rows: `positive` vs `counterfactual_negative`;
   - excluded rows: `unknown`, low-observability rows unless explicitly stress-testing.

2. Observability task:
   - target: `observability_label`;
   - usable rows: `observable`, `limited`, `insufficient`;
   - purpose: check whether `Q_e` can support abstain decisions.

3. Reliability task:
   - target: `reliability_label`;
   - usable rows: provenance-marked audit/GT/counterfactual rows;
   - purpose: evaluate the two-head decision, not train `C_e` directly.

4. RGA diagnostic:
   - target: semantic-geometry agreement bucket;
   - purpose: analyze mismatch, not train the main method.

## Leakage And Shortcut Validation

Materialization must fail if any of the following occurs:

- non-train rows appear;
- validation/test annotations appear in target construction;
- hidden construction fields are present in model input views;
- `Z_e` appears in `compatibility_main`;
- predicate or relation family appears inside `G_e`;
- no-GT rows are labeled negative without a valid counterfactual or audit contradiction;
- source-only or rank-only baseline nearly solves the compatibility target;
- endpoint id, scan id, object-pair id, packet id, or proxy role predicts the label in shortcut probes.

Required post-materialization audits:

- row count by family, predicate, source, rank band, and observability tier;
- label count by `compatibility_label`, `positive_tier`, `negative_tier`;
- source/rank balance inside positive-negative groups;
- hidden-field leakage scan over model views;
- source-only and rank-only diagnostic probe;
- family-only and predicate-only diagnostic probe;
- endpoint-pair memorization probe where enough repeated pairs exist.

## Success Criteria For Proceeding To Smoke

Proceed to `smoke_baseline_plan_v1` only if:

- `prototype_rows.jsonl`, `counterfactual_groups.jsonl`, `baseline_view.jsonl`, and `audit_view.jsonl`
  are defined by this schema;
- all rows are train-only;
- `C_e` has at least one non-trivial positive/counterfactual-negative subset;
- `Q_e` has observable and insufficient/limited examples;
- source-only and rank-only labels are explicitly available for shortcut probing;
- unknown/no-GT rows are not used as automatic negatives.

If a family has too few positives, the correct action is:

```text
mark family diagnostic-only, not source-positive filling
```

## Non-Goals

This contract does not:

- claim model performance;
- promote any result to paper evidence;
- make validation/test targets;
- define a final AAAI table;
- replace human/audit or official GT provenance;
- make `p_geom_valid` the final H002 score.

## Next TODO

```text
smoke_baseline_plan_v1 = completed
prototype_dataset_materialization_v1 = completed
next = smoke_baseline_runner_v1
```

The materialized dataset now lives under `artifacts/prototype_dataset_v1/` with validation errors `0`.
The next step should implement or specify the smoke runner.
