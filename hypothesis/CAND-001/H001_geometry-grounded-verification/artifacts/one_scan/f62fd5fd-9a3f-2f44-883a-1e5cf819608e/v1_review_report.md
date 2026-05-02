# Rules v1 Review

Created at: `2026-04-30`
Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`

## Role

This report triages the 13 remaining support/contact cases in `v1_review_queue.jsonl`.

This is evidence-level triage only. It does not use a 3D visualizer and does not make benchmark claims.

## Inputs

```text
v1_review_queue.jsonl
v1_comparison.jsonl
point_evidence.jsonl
review_labels.jsonl
```

Output labels:

```text
v1_review_labels.jsonl
```

## Summary

Fact:

| Group | Count | Interpretation |
| --- | ---: | --- |
| floor support with legged objects | 3 | Local contact may be represented by a small fraction of object points, so p05/p95 gap is too strict. |
| pillow lying on sofa | 8 | Soft/deformable support creates negative local gaps; symmetric absolute gap is too strict. |
| object on kitchen counter | 2 | Local counter surface may be ambiguous or instance/segmentation needs checking. |

Fact:

- v1 review queue size: 13
- floor-support remaining cases: 3
- object-object support remaining cases: 10
- v1 `uncertain`: 1
- v1 `violated`: 12

## Triage Labels

| Triage label | Count | Meaning |
| --- | ---: | --- |
| `percentile_rule_too_strict_for_legged_support` | 2 | Contact exists at low percentiles, but object p05 misses leg contact. |
| `possible_floating_or_instance_issue` | 1 | Both p01 and p05 gaps remain high; stronger visual-inspection candidate. |
| `soft_contact_penetration_not_handled` | 7 | Negative gap likely reflects soft-object penetration or overlap. |
| `soft_contact_borderline_penetration` | 1 | Negative gap is in relaxed band; keep uncertain. |
| `local_surface_estimator_or_instance_issue` | 2 | Counter support surface or instance geometry likely needs visual check. |

## Interpretation

Inference:

The remaining 13 cases do not invalidate the point-aware direction.

They show that support/contact is not one uniform geometric relation. It has at least three subtypes:

```text
floor support for legged rigid objects
soft/deformable lying-on support
rigid object-on-furniture support with local surface ambiguity
```

This is useful for H001 because the contribution is becoming sharper:

```text
3D scene graph relation verification needs relation-family and relation-subtype geometry evidence.
```

## Group Notes

### Floor Support

Cases:

- `table --standing on--> floor`
- `chair --standing on--> floor`
- `chair --standing on--> floor`

Interpretation:

- Two cases have p01/p99 gaps close to contact but p05/p95 gaps above threshold.
- This suggests leg contact is too small a fraction of object points for a p05 bottom statistic.
- One chair case has both p01/p99 and p05/p95 gaps above threshold and is the strongest visual-inspection candidate in the floor group.

Inference:

Floor support for legged objects may need a foot/contact-point statistic, not a robust bottom percentile alone.

### Pillow On Sofa

Cases:

- eight `pillow --lying on--> sofa` edges

Interpretation:

- The queue is dominated by repeated pillow/sofa negative local gaps.
- Negative gaps are expected for soft/deformable or interpenetrating point evidence.
- Treating `abs(local_vertical_gap)` symmetrically makes v1 too strict for soft `lying on` relations.

Inference:

`lying on` with soft objects should not share the same rigid support rule as `standing on`.

Possible next rule direction:

```text
soft_support_contact:
  allow bounded negative penetration
  report penetration depth separately
  require local support point presence
```

### Kitchen Counter Support

Cases:

- `plant --standing on--> kitchen counter`
- `book --standing on--> kitchen counter`

Interpretation:

- Both cases have many local support points but large negative gaps.
- This can happen if the counter point group includes local vertical faces, raised structures, or instance geometry that is not the actual support plane.
- These are not safe to call real relation violations without visualization.

Inference:

Rigid object-on-furniture support may need a local horizontal support-plane estimator rather than raw support z percentiles.

## Decision

Decision:

```text
visual inspection is needed before multi-scan replication
```

Reason:

- The queue is small enough to inspect manually.
- The remaining failures are subtype-specific, not random.
- Running multi-scan now would multiply ambiguous labels without first fixing the interpretation scheme.

Do not start multi-scan replication yet.

## Next Action

Prepare a minimal visual inspection pass for representative v1 review cases:

```text
floor support: 3 cases
soft pillow/sofa support: 2 representative cases
counter support: 2 cases
```

The visual inspection pass should answer:

- Is the relation visually plausible?
- Is the local point evidence selecting the right support surface?
- Is the failure caused by segmentation/instance geometry?
- Should this relation subtype get a separate rule?
