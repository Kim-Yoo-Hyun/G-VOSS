# Open3DSG Full-Validation Table/Caveat Regeneration

Status: `open3dsg_full_validation_table_caveats_ready`
Created at: `2026-06-04T18:23:54+00:00`

## Coverage

- payload: `ready`
- views: `views_ready`
- preprocess: `preprocess_ready`
- features: `548/548` complete feature ids
- raw dump identity: `raw_dump_identity_audit_ready`
- adapter: `ready`
- geometry: `ready`
- metrics: `ready`
- bootstrap CI: `ready`
- failure rows: `82155`

## Table 6 Candidate

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.4096 | 0.5161 | 0.1386 | 0.1242 |
| probabilistic_recalibrated | 0.3975 | 0.5723 | 0.0606 | 0.0811 |
| rule_verified_point_subtype | 0.4295 | 0.5368 | 0.0000 | 0.0000 |
| family_conditional_risk | 0.4658 | 0.6047 | 0.0286 | 0.0341 |

## Caveats

- Open3DSG full-validation outputs are stored under a separate source root and do not overwrite the existing avg-BLIP or non-avg hardened branches.
- The checkpoint route is official non-averaged BLIP selected by train-dev loss before full-validation source-result reporting.
- Open3DSG remains a source-output reliability evaluation and re-ranking case study; it is not a claim of full Open3DSG paper reproduction unless stated separately.
- Exact-label recall denominator is limited to support_contact, proximity, and relative_vertical H001 families.
- Residual calibration risk remains: geometry consistency scores can demote/retain predictions but do not prove semantic correctness for every unlabeled relation.
- This recovery variant resolves the 15 missing contexts by relaxing the Open3DSG preprocess visible-object gate to min_visible=2 and regenerating relaxed views for two scans; report it as a recovery-policy variant, not as the unmodified source preprocess route.
