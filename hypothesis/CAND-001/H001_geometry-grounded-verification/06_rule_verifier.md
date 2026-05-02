# Rule Verifier

Last updated: 2026-05-03

## Role

The verifier takes a candidate relation edge plus explicit geometry evidence and emits a status.

It is not a relation predictor.

```text
relation edge + geometry evidence -> verification status
```

## Status

| Status | Meaning |
| --- | --- |
| `satisfied` | Required constraints pass. |
| `violated` | Required constraints fail with enough evidence. |
| `uncertain` | Evidence is weak, sparse, ambiguous, or frame-dependent. |
| `unsupported` | Predicate is outside first-pass rule scope. |

Policy:

- preserve every input edge;
- do not count `uncertain` as false;
- do not count `unsupported` as false;
- record rule version and thresholds with outputs.

## Rule Scope

| Family | Status |
| --- | --- |
| `proximity` | primary smoke-test rule |
| `relative_vertical` | primary smoke-test rule |
| `support_contact` | primary research target, point-aware rule needed |
| `relative_horizontal` | diagnostic only |
| deferred/unsupported families | excluded from primary metrics |

## OBB Rules

`proximity`:

```text
normalized_distance_xy <= near_distance_norm_max
```

`relative_vertical`:

```text
higher than: normalized_center_delta_z >= relative_z_margin_norm
lower than:  normalized_center_delta_z <= -relative_z_margin_norm
```

OBB-only `support_contact` used:

```text
subject above object
small vertical gap
projected XY overlap
```

Finding:

```text
OBB-only support/contact is too coarse, especially for floor-support cases.
```

## Point Support Rule

`ply_points_v1` adds local support evidence:

```text
subject robust XY footprint
support points under/near subject footprint
local support surface z
local vertical gap
```

Initial point-level statuses:

| Status | Meaning |
| --- | --- |
| `point_satisfied` | Local support points and gap support the relation. |
| `point_uncertain` | Support evidence is sparse or borderline. |
| `point_violated` | Support evidence is available but inconsistent. |

Current result:

- 32 support/contact edges checked;
- 19 `point_satisfied`;
- 1 `point_uncertain`;
- 12 `point_violated`;
- 13/16 floor-support edges recovered.

## Subtype-Aware Direction

Visual inspection of representative v1 failures showed three recurring verifier issues:

| Issue | Decision |
| --- | --- |
| legged furniture on floor | use low-percentile/contact evidence instead of only p05/p95 gap |
| soft objects lying on furniture | use signed gap and allow bounded negative penetration |
| objects on counters/tables | estimate local horizontal support plane before judging gap |

The subtype-aware verifier is specified in `14_verifier_v2.md` and implemented in `tools/apply_verifier_v2.py`.

Required v2 behavior:

- assign a support/contact subtype;
- compute subtype-specific evidence;
- emit a soft consistency score;
- map the score to `satisfied`, `uncertain`, or `violated`;
- keep geometry-quality issues as `uncertain`.

## Thresholds

Current heuristic thresholds:

| Threshold | Value |
| --- | ---: |
| `near_distance_norm_max` | 1.50 |
| `relative_z_margin_norm` | 0.10 |
| `z_gap_abs_max_m` | 0.10 |
| `xy_overlap_subject_min` | 0.05 |
| `local_vertical_gap_abs_max_m` | 0.10 |
| `min_support_points_under_subject` | 10 |
| `v2_satisfied_score_min` | 0.70 |
| `v2_uncertain_score_min` | 0.40 |

Thresholds are not final claims. They are smoke-test defaults.

## Metrics

Report:

- status counts by family;
- primary denominator;
- uncertain rate;
- manual review labels;
- OBB-only to point-level transitions.
- v1 to v2 status transitions;
- support subtype status counts;
- consistency score by subtype.

Do not report one-scan results as benchmark performance.

## Next

Use `16_evaluation.md` as the prediction-level protocol, `17_subset.md` as the subset strategy, `18_baseline.md` as the baseline decision, `19_schema.md` as the prediction JSONL contract, `20_layout.md` as the layout compatibility result, `21_eval_path.md` as the faithful eval path decision, `22_prep.md` as the prep policy, and `artifacts/layout/vlsat/report.md` as the latest checker output. Select H001-Mini validation scan payloads before fitting a calibrator or reproducing a full baseline.
