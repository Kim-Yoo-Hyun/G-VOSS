# Compatibility Dataset V3 Paper Table Skeleton After Claim Boundary Lock

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock/
status = h002_compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock_ready
selected_path = paper_table_skeleton_ready_select_table_review
validation_errors = 0
next_todo = compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock
```

## Purpose

Claim-boundary lock 이후 bounded paper-table skeleton을 만들었다. 이 단계는 최종
paper result promotion이 아니라, 논문 표에 올릴 수 있는 row 구조와 caveat를
사전에 고정하는 draft 단계다.

## Main Table Skeleton

| Block | Scope | Method | AUROC | AUPRC | Balanced Acc. | Role |
| --- | --- | --- | ---: | ---: | ---: | --- |
| primary mechanism macro | `relative_vertical + size_relative` | `T_e only` | 0.500000 | 0.499505 | 0.500000 | baseline |
| primary mechanism macro | `relative_vertical + size_relative` | `G_e only` | 0.500000 | 0.507762 | 0.500000 | baseline |
| primary mechanism macro | `relative_vertical + size_relative` | `T_e + G_e concat` | 0.498994 | 0.527248 | 0.509615 | baseline |
| primary mechanism macro | `relative_vertical + size_relative` | `C_e compatibility` | 0.995453 | 0.995505 | 0.972964 | proposed mechanism |
| caveated row | `relative_horizontal` | `C_e compatibility` | 0.719568 | 0.444788 | 0.701522 | frame-aware only |
| diagnostic row | `support_contact` | `C_e compatibility` | 0.631712 | 0.643417 | 0.566394 | diagnostic only |

## Control Skeleton

Primary signed-comparison macro 기준에서 `C_e compatibility`는 semantic-only,
geometry-only, plain concat, wrong-`T`, shuffled-`G`, subject/object swap, sign flip
control보다 높다.

Important caveats:

- `relative_horizontal` frame-swap delta is modest: AUROC delta `0.104163`.
- `support_contact` is not solved: wrong-`T` across-route control is stronger than
  M4 and shuffled-`G` within-family delta is weak.

## Draft Caption Boundary

Official-validation mechanism evaluation for H002 `C_e = compatibility(T_e, G_e)`.
The primary block reports only the locked signed-comparison routes
(`relative_vertical` and `size_relative`). `relative_horizontal` is reported as
frame-aware caveated evidence, and `support_contact` is diagnostic. The table does
not use official test data and does not evaluate source reranking, calibrated
`p_rel`/`p_obs`, or all-relation 3DSSG performance.

## Decision

The paper table skeleton is ready for review. It is still not a final paper result.
The next step should review whether this table shape is strong enough for a paper
claim or whether it should remain a hypothesis/report artifact.

## Next

```text
compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock
```
