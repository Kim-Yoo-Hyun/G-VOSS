# Visual Inspection Artifacts

Created at: `2026-04-30T06:34:02.745561+00:00`
Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`

## Role

These files prepare and label the selected v1 review cases for manual visual inspection.
They are point-subset artifacts and qualitative labels, not benchmark evidence.

## Color Legend

| Role | Color | Meaning |
| --- | --- | --- |
| subject | red | Relation subject object points |
| object_context | blue | Relation object/support points outside the local footprint |
| local_support | yellow | Relation object/support points under the subject footprint with expansion |

## Cases

| ID | Relation | Triage | PLY | Points |
| --- | --- | --- | --- | ---: |
| `VIS-001` | `table --standing on--> floor` | `percentile_rule_too_strict_for_legged_support` | `VIS-001_table_standing_on_floor.ply` | 9850 |
| `VIS-002` | `chair --standing on--> floor` | `percentile_rule_too_strict_for_legged_support` | `VIS-002_chair_standing_on_floor.ply` | 8861 |
| `VIS-003` | `chair --standing on--> floor` | `possible_floating_or_instance_issue` | `VIS-003_chair_standing_on_floor.ply` | 8776 |
| `VIS-004` | `pillow --lying on--> sofa` | `soft_contact_borderline_penetration` | `VIS-004_pillow_lying_on_sofa.ply` | 3432 |
| `VIS-005` | `pillow --lying on--> sofa` | `soft_contact_penetration_not_handled` | `VIS-005_pillow_lying_on_sofa.ply` | 3467 |
| `VIS-006` | `plant --standing on--> kitchen counter` | `local_surface_estimator_or_instance_issue` | `VIS-006_plant_standing_on_kitchen_counter.ply` | 5800 |
| `VIS-007` | `book --standing on--> kitchen counter` | `local_surface_estimator_or_instance_issue` | `VIS-007_book_standing_on_kitchen_counter.ply` | 5700 |

## Inspection Questions

- Is the relation visually plausible?
- Is the local support surface selected correctly?
- Is there a segmentation or instance geometry issue?
- Does this relation need a separate rule subtype?

## Outputs To Fill

`labels.jsonl` contains the filled inspection labels.
`report.md` summarizes the label decisions.
`template.jsonl` is the original empty label template.
