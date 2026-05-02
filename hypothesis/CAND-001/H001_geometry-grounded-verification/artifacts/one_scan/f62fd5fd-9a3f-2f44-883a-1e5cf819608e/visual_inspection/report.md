# Inspection Report

Created at: `2026-04-30`
Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`

## Role

This report records qualitative labels for the 7 representative support/contact cases in `visual_inspection_queue.jsonl`.

Evidence source:

```text
colored PLY point subsets
projections.png
point evidence statistics
```

This is still smoke-test evidence. It is not a final benchmark result.

## Summary

Fact:

| Label | Count | Interpretation |
| --- | ---: | --- |
| `rule_too_strict` | 3 | The relation is visually plausible, but the current threshold rule is too rigid. |
| `local_surface_estimator_issue` | 3 | The relation is visually plausible, but local support points include the wrong surface or vertical structure. |
| `segmentation_or_instance_issue` | 1 | The relation cannot be cleanly judged because object geometry appears offset or incomplete. |

Fact:

- visually plausible: 6
- visually uncertain: 1
- local support surface correct: 4
- local support surface incorrect: 3
- rule subtype needed: 6

## Case Labels

| ID | Relation | Label | Visual judgment |
| --- | --- | --- | --- |
| `VIS-001` | `table --standing on--> floor` | `rule_too_strict` | Leg contact is visible; p05/p95 misses sparse support. |
| `VIS-002` | `chair --standing on--> floor` | `rule_too_strict` | Sparse floor contact is plausible for chair legs. |
| `VIS-003` | `chair --standing on--> floor` | `segmentation_or_instance_issue` | Chair appears above local floor support; not a clean rule failure. |
| `VIS-004` | `pillow --lying on--> sofa` | `rule_too_strict` | Soft support makes negative gap acceptable. |
| `VIS-005` | `pillow --lying on--> sofa` | `local_surface_estimator_issue` | Sofa back/side structure contaminates local support surface. |
| `VIS-006` | `plant --standing on--> kitchen counter` | `local_surface_estimator_issue` | Counter support needs horizontal local plane estimation. |
| `VIS-007` | `book --standing on--> kitchen counter` | `local_surface_estimator_issue` | Same counter surface ambiguity as `VIS-006`. |

## Interpretation

Inference:

The visual pass supports the broader direction but weakens a single hard-threshold verifier.

The next verifier should not only tune thresholds. It should separate at least three support/contact subtypes:

```text
legged_floor_support
soft_support_contact
rigid_object_on_furniture
```

Each subtype should expose evidence and produce a soft consistency score before any hard filtering.

## Decision

Decision:

```text
do not start multi-scan replication before subtype-aware rule decision
```

Reason:

- 6 of 7 inspected cases appear visually plausible or likely plausible.
- Most remaining v1 failures are verifier/evidence interpretation issues, not clear false relations.
- Multi-scan replication with the current hard rule would likely amplify known rule bias.

## Next

Write a support/contact subtype decision that connects:

```text
probabilistic geometry consistency calibration
relation-subtype-aware verifier
evaluation protocol with violation/recall tradeoff
```
