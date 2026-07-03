# Main Validation Claim Table Lock After Path Decision

## Purpose

H002 main claim을 official 3DSSG validation split에서 진행하기로 결정했기 때문에, main
validation benchmark table의 caption, baseline comparison wording, Open3DSG caveat, blocked
claim, required caveat를 고정한다. 이 단계는 새 metric을 실행하지 않는다.

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision/
status = h002_main_validation_claim_table_lock_after_path_decision_ready
selected_path = main_validation_table_claim_locked_keep_official_test_blocked
validation_errors = 0
main_table = official_3DSSG_validation_split
official_test_benchmark = false
next_todo = compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock
```

## Locked Main Table

Recommended caption:

```text
Main validation benchmark on the official 3DSSG validation split. We compare
source-score ranking with H002 compatibility-aware reranking on VL-SAT and
Open3DSG validation predictions. Open3DSG is used as an open-vocabulary source,
while quantitative Recall@K is computed after mapping to closed-vocabulary 3DSSG
labels. Violation@K is our geometry-consistency metric.
```

## Locked Claim Boundary

- Main split: official 3DSSG validation split.
- Sources: VL-SAT and Open3DSG validation predictions.
- Baseline: `S0_source_score`.
- Primary H002 score: `S2_source_x_Ce`.
- Metrics: `Recall@K`, `Violation@K`.
- Method role: factorized reliability/reranking layer, not a new relation predictor.
- Open3DSG role: open-vocabulary source with closed-vocabulary 3DSSG evaluation.

## Required Caveats

- No official 3DSSG test result is used.
- `Violation@K` is an H002 custom geometry-consistency metric.
- Some source/family/K cells can have small Recall@K regressions; do not claim uniform
  improvement.
- `support_contact` remains diagnostic/failure taxonomy, not solved relation family.
- H003 embedding is future/optional unless a prototype beats explicit `C_e` on hard
  negatives, transfer, calibration, or family generalization.
