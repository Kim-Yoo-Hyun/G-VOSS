# Open3DSG Missing-15 Preprocess Diagnosis

Date: `2026-06-05T05:41:02+00:00`
Status: `diagnosis_ready`
Diagnosed contexts: `11`

## Source Condition

- drop condition: `if len(objects_id) - len(drop) < 4: print('too few visible objects, scene missalignment possible'); return`
- meaning: the source drops a subgraph when fewer than four annotation objects have object2image view metadata
- view generation: `pixels > 12 and ((ratio > 0.3 or pixels > 80) or wall/floor pixels > 80), with R3Scan projection visibility threshold 0.20`

## Summary

- categories: `{'source_preprocess_policy_visible_object_gate': 11}`
- recoverability: `{'candidate_relax_min_visible_to_2': 5, 'candidate_relax_min_visible_to_2_low_metric_value': 5, 'not_recoverable_by_min2': 1}`
- visible annotation object counts: `{'1': 1, '2': 1, '3': 9}`
- relaxed min-2 candidates: `5`
- unrecoverable without view regeneration: `1`

## Diagnosis Table

| relationship_id | ann obj | visible obj | both-visible GT rel | category | recoverability |
| --- | ---: | ---: | ---: | --- | --- |
| 0cac7532-8d6f-2d13-8cea-1e70d5ae4856-2 | 6 | 1 | 0 | source_preprocess_policy_visible_object_gate | not_recoverable_by_min2 |
| 0cac7534-8d6f-2d13-8de7-8a915ed90050-3 | 7 | 3 | 1 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2 |
| 0cac7582-8d6f-2d13-8d4b-e4041cb166c4-1 | 9 | 3 | 1 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2 |
| 0cac7584-8d6f-2d13-8df8-c05e4307b418-5 | 9 | 2 | 0 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2_low_metric_value |
| 10b1794e-3938-2467-89a7-ebc89e84cf88-3 | 7 | 3 | 1 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2 |
| 422885b3-192d-25fc-84c9-9b80eea1752d-1 | 9 | 3 | 0 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2_low_metric_value |
| 422885b3-192d-25fc-84c9-9b80eea1752d-2 | 9 | 3 | 0 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2_low_metric_value |
| 422885c5-192d-25fc-85e6-12a3d65c8e7b-2 | 8 | 3 | 1 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2 |
| bf9a3ddf-45a5-2e80-8007-8e9e7f323e52-2 | 9 | 3 | 4 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2 |
| c7895f63-339c-2d13-81a3-0b07b1eb23b4-2 | 9 | 3 | 0 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2_low_metric_value |
| fcf66d7b-622d-291c-86b8-7db96aebcee3-3 | 5 | 3 | 0 | source_preprocess_policy_visible_object_gate | candidate_relax_min_visible_to_2_low_metric_value |

## Claim Boundary

This artifact diagnoses the source preprocessing drop. It is not a promoted paper metric. Any relaxed recovery branch must keep canonical full-validation artifacts separate and rerun feature audit, raw dump, adapter export, geometry join, metrics, bootstrap, and table generation before it can replace the current Open3DSG full-validation bundle.
