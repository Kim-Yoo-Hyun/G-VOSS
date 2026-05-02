# Stage Log

Last updated: 2026-04-30

## Role

This file consolidates the execution path and stage summaries that were previously split across separate Phase A/B/C and v1 decision documents.

Merged files:

```text
07_execution_path.md
08_evidence_export.md
09_rule_application.md
10_point_support_evidence.md
11_rule_revision_decision.md
12_rules_v1_contract.md
```

Detailed artifacts remain in:

```text
artifacts/one_scan/<scan-id>/
```

## Scan

Validated sample scan:

```text
f62fd5fd-9a3f-2f44-883a-1e5cf819608e
```

Input payload:

```text
labels.instances.annotated.v2.ply
semseg.v2.json
mesh.refined.0.010000.segs.v2.json
```

Dataset join check:

- 60 3DSSG objects join to 60 `semseg.v2.json` objects.
- 772 relation tuples are available.
- PLY vertex count matches `segIndices`: 72,017.

## Phase A

Goal:

```text
export relation-level geometry evidence
```

Script:

```text
tools/export_evidence.py
```

Outputs:

```text
edges.jsonl
export_summary.json
export_report.md
thresholds.json
```

Result:

- 772 edges exported.
- Validation passed.
- Missing object/semseg joins: 0.

Interpretation:

- OBB-derived evidence is enough for proximity and vertical smoke checks.
- OBB/AABB evidence is too coarse for support/contact surfaces.

## Phase B

Goal:

```text
apply h001-rules-v0 to exported edges
```

Script:

```text
tools/apply_rules_v0.py
```

Outputs:

```text
decisions.jsonl
rules_summary.json
rules_report.md
review_queue.jsonl
review_labels.jsonl
review_report.md
```

Result:

- 772 decisions.
- Validation passed.
- Primary metric denominator: 129.
- `proximity`: 68 satisfied.
- `relative_vertical`: 40 satisfied, 6 uncertain, 2 violated.
- `support_contact`: 32 edges, all required point/local evidence review.

Interpretation:

- `proximity` and `relative_vertical` are usable as first smoke-test families.
- `relative_horizontal` remains diagnostic because coordinate-frame assumptions are unresolved.
- `support_contact` should not rely on OBB/AABB evidence alone.

## Phase C

Goal:

```text
add PLY point-level local support evidence for support/contact
```

Script:

```text
tools/export_point_support.py
```

Outputs:

```text
point_evidence.jsonl
point_comparison.jsonl
point_summary.json
point_report.md
comparison_report.md
```

Result:

| Metric | Value |
| --- | ---: |
| support/contact records | 32 |
| point evidence missing | 0 |
| point satisfied | 19 |
| point uncertain | 1 |
| point violated | 12 |
| floor support recovered | 13 / 16 |

Interpretation:

Point/local support evidence recovers many OBB-only support/contact failures, so support/contact remains a valid H001 target.

## Rules v1

Decision:

```text
go: revise support/contact from OBB/AABB evidence to point/local-surface evidence
```

Script:

```text
tools/apply_rules_v1.py
```

Outputs:

```text
v1_decisions.jsonl
v1_comparison.jsonl
v1_summary.json
v1_report.md
v1_review_queue.jsonl
v1_review_labels.jsonl
v1_review_report.md
```

Result:

| Metric | Value |
| --- | ---: |
| all edges preserved | 772 |
| support/contact edges | 32 |
| v1 satisfied | 19 |
| v1 uncertain | 1 |
| v1 violated | 12 |
| v1 review queue | 13 |

Transition summary:

| Transition | Count |
| --- | ---: |
| v0 uncertain -> v1 satisfied | 10 |
| v0 uncertain -> v1 violated | 3 |
| v0 violated -> v1 satisfied | 9 |
| v0 violated -> v1 uncertain | 1 |
| v0 violated -> v1 violated | 9 |

Interpretation:

`h001-rules-v1` validates the point-evidence direction but still behaves like one hard support/contact rule.

## Visual Inspection

Artifacts:

```text
visual_inspection/labels.jsonl
visual_inspection/report.md
visual_inspection/projections.png
```

Label summary:

| Label | Count |
| --- | ---: |
| `rule_too_strict` | 3 |
| `local_surface_estimator_issue` | 3 |
| `segmentation_or_instance_issue` | 1 |

Interpretation:

- 6 of 7 inspected cases are visually plausible.
- Most remaining v1 failures are verifier/evidence interpretation issues.
- Multi-scan replication should wait until subtype-aware support/contact logic is specified.

## Verifier v2

Goal:

```text
apply subtype-aware support/contact verification
```

Script:

```text
tools/apply_verifier_v2.py
```

Outputs:

```text
v2/decisions.jsonl
v2/support.jsonl
v2/transitions.jsonl
v2/review.jsonl
v2/summary.json
v2/report.md
```

Result:

| Metric | Value |
| --- | ---: |
| all edges preserved | 772 |
| support/contact edges | 32 |
| v2 satisfied | 31 |
| v2 uncertain | 1 |
| v2 violated | 0 |
| v2 review queue | 1 |
| visually plausible v2 violations | 0 |

Subtype summary:

| Subtype | Count |
| --- | ---: |
| `legged_floor_support` | 15 |
| `soft_support_contact` | 11 |
| `rigid_object_on_furniture` | 5 |
| `geometry_quality_uncertain` | 1 |

Transition summary:

| Transition | Count |
| --- | ---: |
| v1 satisfied -> v2 satisfied | 19 |
| v1 uncertain -> v2 satisfied | 1 |
| v1 violated -> v2 satisfied | 11 |
| v1 violated -> v2 uncertain | 1 |

Interpretation:

- The subtype-aware verifier removes the visually plausible false violations found in v1.
- The remaining review case is a visual `segmentation_or_instance_issue`, so `uncertain` is the correct smoke-test outcome.
- This validates the H001 smoke-test direction, but it is still not benchmark evidence or a calibrated probability model.

## Current Decision

Use `13_subtypes.md` as the decision record for subtype-aware support/contact verification.

Use `14_verifier_v2.md` as the implementation contract and `v2/report.md` / `v2/summary.json` as the one-scan result record.

Use `15_calibration.md` as the calibration design record. The v2 `consistency_score` is not a calibrated probability.

Use `16_evaluation.md` as the prediction-level violation/recall evaluation protocol.

Use `17_subset.md` as the official `3DSSG_subset`-based multi-scan/subset strategy decision.

Use `18_baseline.md` as the prediction-level baseline decision.

Use `19_schema.md` as the `vlsat_closed_set` prediction schema.

Use `20_layout.md` as the local `VL-SAT` layout compatibility record.

Use `21_eval_path.md` as the faithful eval path decision.

Use `22_prep.md` as the faithful staged layout prep policy.

Next gate:

```text
H001-Mini validation scan payload selection
```

Do not treat these one-scan results as benchmark evidence.
