# Manual Review

Created at: 2026-04-29

Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`

Input queue:

```text
review_queue.jsonl
```

Review output:

```text
review_labels.jsonl
```

## Scope

This is an evidence-level manual review of the Phase B verifier queue. It does not use a 3D visualizer yet, so labels are based on the exported geometry evidence, relation labels, verifier status, and reason codes.

Reviewed queue size:

| Family | Count |
| --- | ---: |
| `support_contact` | 10 |
| `proximity` | 10 |
| `relative_vertical` | 5 |
| `relative_horizontal` | 5 |

## Review Labels

| Review label | Count | Meaning |
| --- | ---: | --- |
| `geometry_artifact_likely` | 6 | Current OBB/AABB geometry likely causes the verifier issue. |
| `needs_point_geometry` | 3 | OBB/AABB is insufficient; point-level evidence is needed before deciding. |
| `candidate_real_violation_or_geometry_mismatch` | 1 | The edge is a stronger violation candidate, but point-level evidence is still needed. |
| `rule_correct_likely` | 7 | The rule behavior looks plausible from current evidence. |
| `threshold_too_loose_candidate` | 5 | The edge passes, but the proximity threshold may be too permissive. |
| `candidate_annotation_or_instance_issue` | 2 | The edge may be a real inconsistency or an instance-label ambiguity. |
| `rule_correct_uncertain` | 1 | The verifier correctly avoids a hard decision. |
| `coordinate_frame_issue` | 5 | Raw scene x/y horizontal rules cannot be trusted yet. |

## Support / Contact

Reviewed edges: 10

Status distribution:

- `uncertain`: 6
- `violated`: 4

Review interpretation:

- Six `standing on floor` examples have subject-above and projected overlap, but very large negative `vertical_gap_subject_on_object`.
- This pattern is not good evidence that the relation is false.
- It is stronger evidence that floor OBB-derived AABB is not a valid support surface model.
- Three floor-support violated cases have zero projected AABB overlap. These need point-level footprint evidence before being called real violations.
- The non-floor edge `lamp --standing on--> cabinet` is the strongest candidate for a real support/contact inconsistency, but it still needs point-level contact evidence.

Decision:

- Keep `support_contact` as part of the H001 contribution.
- Do not use OBB-only support/contact violation rate as primary thesis evidence.
- Add `ply_points_v1` or floor-plane-specific local support evidence before multi-scan support/contact evaluation.

Recommended support/contact evidence:

```text
subject_bottom_z_p05
support_object_local_top_z_p95
local_vertical_gap
subject_xy_footprint_overlap_with_support_points
support_points_under_subject_count
support_plane_or_local_surface_confidence
```

## Proximity

Reviewed edges: 10

Status distribution:

- `satisfied`: 10

Review interpretation:

- High-score table/chair and blinds/curtain examples look plausible from normalized XY distance.
- Low-score cabinet/cabinet, item/item, and kitchen-cabinet/stool examples still pass under `near_distance_norm_max = 1.50`.
- This suggests the first proximity rule is useful for smoke testing but may be too permissive for final reporting.

Decision:

- Keep `proximity` in the primary smoke-test metric.
- Treat proximity score as a ranking signal, not just a binary threshold.
- Calibrate `near_distance_norm_max` only after more scans or manual labels are available.

Recommended proximity refinement:

```text
near_distance_norm_max_candidate_grid = [0.75, 1.00, 1.25, 1.50]
report proximity score quantiles
inspect low-score satisfied edges before threshold changes
```

## Relative Vertical

Reviewed edges: 5

Status distribution:

- `satisfied`: 2
- `violated`: 2
- `uncertain`: 1

Review interpretation:

- The two satisfied examples have clear signed vertical deltas and look consistent with the rule.
- The two violated examples have predicate direction opposite to signed vertical center delta. These are useful candidate inconsistency examples, though same-label cabinet instances may be ambiguous without visualization.
- The pillow/pillow uncertain example has a vertical margin below threshold, so `uncertain` is the right behavior.

Decision:

- Keep `relative_vertical` in the primary smoke-test metric.
- Use its violated examples as the first qualitative examples of geometry-inconsistent relation labels.
- Add visual or object-id context before treating same-label instance pairs as final evidence.

## Relative Horizontal

Reviewed edges: 5

Status distribution:

- `uncertain`: 5

Review interpretation:

- All five are diagnostic conflicts under raw scene x/y assumptions.
- Chair reciprocal relations suggest the raw x/y convention may be reversed, viewpoint-relative, or object-centric.
- These conflicts should not be counted as relation failures.

Decision:

- Keep `relative_horizontal` diagnostic only.
- Do not include it in primary violation-rate metrics until coordinate-frame convention is validated.
- If horizontal relations are needed later, design a separate coordinate-frame validation pass.

Recommended horizontal validation:

```text
collect reciprocal pairs: left/right, front/behind
test x-axis sign, y-axis sign, and swapped-axis hypotheses
compare consistency under each frame hypothesis
only promote horizontal relations if one frame explains most reciprocal pairs
```

## Overall Conclusion

The manual review supports this split:

| Relation family | Current status | Next action |
| --- | --- | --- |
| `proximity` | usable smoke-test signal | calibrate threshold later |
| `relative_vertical` | usable smoke-test signal | keep in primary metric |
| `support_contact` | important but under-modeled | add point/local support evidence |
| `relative_horizontal` | coordinate-frame dependent | keep diagnostic only |

Most important conclusion:

```text
support_contact should stay in the research contribution, but it needs relation-specific geometry evidence beyond semseg_obb_v0.
```

This strengthens the CAND-001 direction: geometry-grounded relation verification is not just adding generic bbox features. Different relation families need different geometry evidence.

## Next Action

Plan a small `ply_points_v1` support/contact smoke test inside the H001 hypothesis folder.

Do not create `experiments/`, `paper/`, or `decisions/` yet.
