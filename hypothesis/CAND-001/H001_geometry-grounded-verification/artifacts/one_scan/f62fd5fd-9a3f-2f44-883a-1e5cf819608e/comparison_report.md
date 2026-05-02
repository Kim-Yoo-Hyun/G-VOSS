# Support Contact Comparison

Created at: `2026-04-30`
Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`

## Role

This report compares OBB-only support/contact verification against point/local-surface evidence.

It is a one-scan H001 smoke-test interpretation, not benchmark evidence.

## Files

| Role | File |
| --- | --- |
| Phase A edge evidence | `edges.jsonl` |
| Phase B OBB-only decisions | `decisions.jsonl` |
| Phase B manual review | `review_report.md`, `review_labels.jsonl` |
| Phase C point evidence | `point_evidence.jsonl` |
| Phase C transition table | `point_comparison.jsonl` |
| Phase C summary | `point_summary.json` |

Removed intermediate artifact:

```text
manual_inspection_queue.jsonl
```

Reason: it was a Phase A pre-verifier inspection queue and is superseded by `review_queue.jsonl`, `review_labels.jsonl`, and `review_report.md`.

## Comparison

Fact:

| Evidence | Support/contact edges | Satisfied | Uncertain | Violated |
| --- | ---: | ---: | ---: | ---: |
| OBB-only `h001-rules-v0` | 32 | 0 | 13 | 19 |
| Point/local `ply_points_v1` | 32 | 19 | 1 | 12 |

Fact:

| Transition | Count |
| --- | ---: |
| `obb_uncertain_to_point_satisfied` | 10 |
| `obb_uncertain_to_point_violated` | 3 |
| `obb_violated_to_point_satisfied` | 9 |
| `obb_violated_to_point_uncertain` | 1 |
| `obb_violated_to_point_violated` | 9 |

Fact:

- floor-support edges: 16
- floor-support recovered by point evidence: 13
- floor-support recovery rate: 0.8125
- OBB failure to `point_satisfied`: 19
- missing point object ids: 0

## Interpretation

Inference:

The OBB-only failure pattern is not strong evidence that support/contact should be removed from CAND-001.

The stronger reading is:

```text
support/contact needs relation-specific local surface evidence, not generic object-level bbox evidence.
```

Why:

- OBB-derived AABB uses object-level extents, so large planar objects such as `floor` produce misleading top/bottom geometry.
- Manual review already marked many support/contact failures as `geometry_artifact_likely` or `needs_point_geometry`.
- Point/local evidence recovered 19 OBB failures and 13 of 16 floor-support cases.

## Remaining Weakness

Fact:

Point evidence still leaves 12 edges as `point_violated` and 1 as `point_uncertain`.

Inference:

These cases should not be treated as final false-relation evidence yet. They may include true annotation inconsistencies, segmentation/object-id noise, local surface estimation failures, or threshold issues.

Current missing checks:

- no 3D visualizer inspection;
- no multi-scan replication;
- no calibrated threshold sweep;
- no floor-plane-specific estimator;
- no instance ambiguity check for same-label objects.

## Decision

Agent recommendation:

Keep `support_contact` inside H001.

Do not use the OBB-only support/contact violation rate as thesis evidence.

Revise the support/contact rule so that:

- OBB/AABB evidence is only a coarse prefilter;
- local point support evidence becomes the primary support/contact evidence;
- `point_uncertain` remains separate from hard violation;
- floor-support cases are reported separately from object-object support cases.

## Next Gate

The next CAND-001 gate should decide whether to implement a point-aware `support_contact` rule revision.

Minimal acceptance condition:

```text
The revised rule must preserve the 19 recovered cases and make the remaining 13 cases inspectable by explicit reason code.
```
