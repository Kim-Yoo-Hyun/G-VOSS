# Subtypes

Last updated: 2026-04-30

## Role

This document records the support/contact subtype decision after visual inspection.

It decides whether H001 should continue with one hard support/contact rule or move to a subtype-aware verifier.

## Decision

Decision:

```text
move from one support/contact rule to a subtype-aware verifier
```

Reason:

- `h001-rules-v1` recovered many OBB/AABB failures with point/local-surface evidence.
- The remaining failures are not random. They cluster by support/contact subtype.
- Visual inspection shows that most remaining violations are visually plausible relations with rule or surface-estimation issues.

This means the next verifier should not simply tune the current threshold. It should model support/contact as a family of subtype-specific geometry constraints.

## Evidence

Fact:

`h001-rules-v1` one-scan support/contact result:

| Metric | Value |
| --- | ---: |
| support/contact edges | 32 |
| point evidence missing | 0 |
| v1 satisfied | 19 |
| v1 uncertain | 1 |
| v1 violated | 12 |
| floor support satisfied | 13 / 16 |
| v1 review queue | 13 |

Fact:

Visual inspection label summary:

| Label | Count | Meaning |
| --- | ---: | --- |
| `rule_too_strict` | 3 | Relation is visually plausible, but the threshold rule is too rigid. |
| `local_surface_estimator_issue` | 3 | Relation is visually plausible, but local support points include the wrong surface or vertical structure. |
| `segmentation_or_instance_issue` | 1 | Object geometry appears offset or incomplete; relation validity is not cleanly decidable. |

Fact:

- 6 of 7 inspected cases are visually plausible.
- 6 of 7 inspected cases need a separate rule subtype or surface estimator.
- 1 of 7 inspected cases should be treated as geometry-quality uncertainty, not as clean false relation evidence.

Primary artifacts:

```text
artifacts/one_scan/<scan-id>/visual_inspection/labels.jsonl
artifacts/one_scan/<scan-id>/visual_inspection/report.md
artifacts/one_scan/<scan-id>/visual_inspection/projections.png
```

## Subtype Set

Use this support/contact subtype set for the next verifier design.

| Subtype | Trigger | Main issue | Required evidence |
| --- | --- | --- | --- |
| `legged_floor_support` | `standing on` / support relation with object `floor` and furniture-like subject | Small true contact area is missed by robust bottom percentiles. | floor local points, subject low-percentile bottom, foot/contact-point evidence, contact fraction |
| `soft_support_contact` | `lying on` or soft/deformable subject on furniture | Negative gap can be valid because soft objects overlap or compress. | local support points, signed penetration depth, soft-object prior, bounded negative gap |
| `rigid_object_on_furniture` | rigid object `standing on` furniture such as counter/table/cabinet | Raw local support z percentiles mix horizontal surface with vertical or raised structures. | local horizontal support-plane estimate, plane residual, support footprint overlap |
| `geometry_quality_uncertain` | visually ambiguous, object appears floating, scan/instance issue likely | Geometry source may not support a reliable decision. | geometry quality flags, point density, instance completeness, visual/manual label |

These subtypes are not final ontology claims. They are verifier subtypes for the first H001 support/contact implementation.

## What Changes From v1

`h001-rules-v1`:

```text
support_contact -> one point/local-surface rule -> hard status
```

Next verifier:

```text
support_contact
  -> subtype assignment
  -> subtype-specific evidence extraction
  -> soft geometry consistency score
  -> calibrated status / confidence
```

The next verifier should produce both:

```text
consistency_score: continuous or ordinal score
status: satisfied / uncertain / violated
```

Hard filtering should be derived from score thresholds only after the score is reported.

## Subtype Logic

### Legged Floor Support

Problem:

`p05(subject_z) - p95(floor_z)` can be large even when legs touch the floor because the bottom 5 percent of all object points may still include chair/table structure above the feet.

Use:

```text
subject_z_p01
subject_z_min or robust foot candidates
floor_z_p99 under footprint
contact fraction near floor
support point count under footprint
```

Expected behavior:

- Do not mark a legged object as violated just because p05/p95 gap is high.
- If p01/p99 is near contact and support points exist, produce high or medium consistency.
- If both p01/p99 and p05/p95 remain high, return `uncertain` with geometry-quality reason before calling `violated`.

### Soft Support Contact

Problem:

`lying on` with pillows or other soft objects can have negative signed gaps. A symmetric absolute-gap rule treats valid soft contact as failure.

Use:

```text
signed local gap
penetration depth
support point count
soft subject/object category prior
local overlap footprint
```

Expected behavior:

- Allow bounded negative gap for soft objects.
- Report penetration depth separately.
- Penalize positive floating gap more strongly than negative soft penetration.

### Rigid Object On Furniture

Problem:

Furniture objects such as `kitchen counter` may include vertical faces, backs, raised structures, or multiple horizontal surfaces. Raw local support z percentiles can select the wrong surface.

Use:

```text
local horizontal plane candidate
plane normal alignment with z axis
plane residual
support footprint overlap
subject bottom to plane gap
```

Expected behavior:

- Estimate the local support plane before judging the gap.
- If no reliable horizontal plane is found, return `uncertain`.
- Do not use raw support z percentile as final evidence for counter/table support.

### Geometry Quality Uncertain

Problem:

Some cases cannot cleanly test relation correctness because object instance geometry appears incomplete, floating, or offset.

Use:

```text
point density
instance completeness proxy
manual/visual flags
large mismatch between p01 and visible support
```

Expected behavior:

- Keep these cases out of positive violation claims.
- Report them separately as geometry-source risk.

## Probabilistic Direction

The subtype-aware verifier should move toward probabilistic geometry consistency, not only new hard thresholds.

Minimum next score shape:

```text
P_geo_consistent(edge | subtype, geometry_evidence)
```

Practical smoke-test implementation can start with hand-designed score functions:

| Subtype | Candidate score signals |
| --- | --- |
| `legged_floor_support` | low-percentile gap score, floor support density, contact fraction |
| `soft_support_contact` | bounded negative penetration score, support density, overlap score |
| `rigid_object_on_furniture` | horizontal plane confidence, plane gap score, footprint overlap |
| `geometry_quality_uncertain` | geometry completeness and ambiguity flags |

Later prediction-level evaluation can calibrate this score against accepted/rejected relation edges.

## Evaluation Implication

The final paper should not only report whether the verifier removes edges.

It should report the tradeoff:

```text
standard relation recall
geometry violation rate
consistency-filtered recall
calibrated edge confidence
```

Important:

Reducing violation rate by deleting many correct edges is not sufficient. The contribution requires preserving useful predicate/triplet recall while lowering geometry inconsistency.

## Next Step

The subtype-aware verifier has been implemented and validated on the one-scan smoke test.

Result files:

```text
14_verifier_v2.md
15_calibration.md
artifacts/one_scan/<scan-id>/v2/
```

Next:

- use `16_evaluation.md` as the violation/recall evaluation protocol;
- decide the multi-scan or subset strategy;
- only then implement calibration-table export and counterfactual negative generation.
