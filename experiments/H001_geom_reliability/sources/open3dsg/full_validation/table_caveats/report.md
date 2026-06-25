# Open3DSG Full-Validation Table/Caveat Regeneration

Status: `open3dsg_full_validation_table_caveats_ready`
Created at: `2026-06-04T14:24:07+00:00`

## Coverage

- payload: `ready`
- views: `views_ready`
- preprocess: `preprocess_partial_ready`
- features: `533/533` complete feature ids
- raw dump identity: `raw_dump_identity_audit_ready`
- adapter: `ready`
- geometry: `ready`
- metrics: `ready`
- bootstrap CI: `ready`
- failure rows: `81448`

## Table 6 Candidate

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.4043 | 0.5111 | 0.1387 | 0.1242 |
| probabilistic_recalibrated | 0.3943 | 0.5685 | 0.0590 | 0.0807 |
| rule_verified_point_subtype | 0.4242 | 0.5320 | 0.0000 | 0.0000 |
| family_conditional_risk | 0.4612 | 0.5999 | 0.0265 | 0.0332 |

## Caveats

- Open3DSG full-validation outputs are stored under a separate source root and do not overwrite the existing avg-BLIP or non-avg hardened branches.
- The checkpoint route is official non-averaged BLIP selected by train-dev loss before full-validation source-result reporting.
- Open3DSG remains a source-output reliability evaluation and re-ranking case study; it is not a claim of full Open3DSG paper reproduction unless stated separately.
- Exact-label recall denominator is limited to support_contact, proximity, and relative_vertical H001 families.
- Residual calibration risk remains: geometry consistency scores can demote/retain predictions but do not prove semantic correctness for every unlabeled relation.
- Open3DSG full-validation feature coverage excludes 15 contexts without loadable preprocessed pickles; report this as a covered-context denominator caveat.
- Open3DSG preprocessing produced 15 missing contexts after recovery attempts; these are treated as explicit source-runtime caveats.
