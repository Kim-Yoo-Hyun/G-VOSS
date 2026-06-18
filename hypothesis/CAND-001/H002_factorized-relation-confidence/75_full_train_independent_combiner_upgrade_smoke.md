# H002 Full-Train Independent Combiner Upgrade Smoke

## Purpose

이 문서는 74번 설계에서 고정한 upgraded combiner 3개를 train-only controlled slice에서
실제로 비교한 결과를 기록한다.

검증 질문:

```text
failure analysis에 맞춘 residual/family-gated/uncertainty-gated combiner가
semantic_plus_geometry를 안전하게 이길 수 있는가?
```

## Boundary

- Split: Open3DSG train-only.
- Active target: `proposed_role_balanced_codex_ver`.
- Rows: 158.
- Positive/negative: 79/79.
- 새 combiner는 train-only fold 내부에서만 학습한다.
- validation/test는 사용하지 않는다.
- hidden audit metadata는 model input이 아니다.
- multi-view는 model input이 아니다.
- label은 `(codex_ver_full_train_independent)` bootstrap label이다.
- paper-level performance claim은 불가하다.

## Tested Views

Baselines:

```text
semantic_only
geometry_only
semantic_plus_geometry
current_factorized_reliability_posterior
residual_reliability_model
```

Upgraded combiners:

```text
C1_residual_logit_calibrator
C2_family_gated_residual
C3_uncertainty_gated_geometry
```

All upgraded combiners are offset/residual models over `semantic_plus_geometry`.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_smoke.py
```

Observed:

```text
status=full_train_independent_combiner_upgrade_no_safe_gain
rows=158
validation_used=False
best_upgraded=C2_family_gated_residual
d_auprc_vs_sg=+0.0070
d_brier_vs_sg=+0.0062
progress_views=none
next=full_train_independent_combiner_upgrade_error_analysis
```

## Grouped Main Result

Scan-grouped train-only folds:

| View | Kind | AUROC | AUPRC | Brier | ECE-5 | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | baseline | 0.6623 | 0.6291 | 0.2360 | 0.0671 | 0.6076 |
| `geometry_only` | baseline | 0.4575 | 0.5098 | 0.2559 | 0.0230 | 0.4810 |
| `semantic_plus_geometry` | baseline | 0.6640 | 0.6300 | 0.2341 | 0.0418 | 0.6392 |
| `current_factorized_reliability_posterior` | baseline | 0.6531 | 0.6253 | 0.2363 | 0.0758 | 0.5823 |
| `residual_reliability_model` | baseline | 0.6558 | 0.6255 | 0.2358 | 0.0755 | 0.6203 |
| `C1_residual_logit_calibrator` | upgraded | 0.6581 | 0.6271 | 0.2356 | 0.0468 | 0.6139 |
| `C2_family_gated_residual` | upgraded | 0.6520 | 0.6370 | 0.2404 | 0.0833 | 0.6139 |
| `C3_uncertainty_gated_geometry` | upgraded | 0.6704 | 0.6247 | 0.2329 | 0.0714 | 0.6456 |

## Delta vs Semantic+Geometry

| View | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | ---: | ---: | ---: |
| `current_factorized_reliability_posterior` | -0.0109 | -0.0047 | +0.0021 |
| `residual_reliability_model` | -0.0082 | -0.0045 | +0.0017 |
| `C1_residual_logit_calibrator` | -0.0059 | -0.0028 | +0.0015 |
| `C2_family_gated_residual` | -0.0120 | +0.0070 | +0.0062 |
| `C3_uncertainty_gated_geometry` | +0.0064 | -0.0052 | -0.0012 |

Interpretation:

- `C1`은 current factorized보다 안정적이지만 `semantic_plus_geometry`를 넘지 못한다.
- `C2`는 AUPRC를 가장 많이 올리지만 threshold와 calibration 손해가 크다.
- `C3`는 AUROC, Brier, threshold transfer는 개선하지만 AUPRC가 내려간다.
- progression threshold를 만족한 upgraded view는 없다.

## Threshold Transfer

Reference: `semantic_plus_geometry`.

| View | Fixes | New Mistakes | Both Correct | Both Wrong | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: |
| `current_factorized_reliability_posterior` | 1 | 10 | 91 | 56 | +9 |
| `residual_reliability_model` | 1 | 4 | 97 | 56 | +3 |
| `C1_residual_logit_calibrator` | 1 | 5 | 96 | 56 | +4 |
| `C2_family_gated_residual` | 4 | 8 | 93 | 53 | +4 |
| `C3_uncertainty_gated_geometry` | 4 | 3 | 98 | 53 | -1 |

Interpretation:

```text
C3 is the only upgraded combiner that fixes more threshold decisions than it
breaks, but it does not improve AUPRC enough and its Brier improvement is small.
```

## Slice-Level Clues

Family slices:

- `relative_vertical`: upgraded combiners help, especially `C3`
  (`AUPRC=0.6984`, `Brier=0.2122`) versus `semantic_plus_geometry`
  (`AUPRC=0.6729`, `Brier=0.2200`).
- `support_contact`: upgraded combiners mostly hurt calibration/ranking.
  `C2` is particularly bad here (`AUPRC=0.6959`, `Brier=0.2442`) versus
  `semantic_plus_geometry` (`AUPRC=0.7121`, `Brier=0.2233`).
- `proximity`: small gains are visible but the slice is only 31 rows.

Direction slices:

- `semantic_high_geometry_low`: `C3` improves both ranking/calibration
  (`AUPRC=0.7553`, `Brier=0.2217`) versus `semantic_plus_geometry`
  (`AUPRC=0.6983`, `Brier=0.2391`).
- `semantic_geometry_close`: `C2` improves AUPRC strongly
  (`AUPRC=0.8124`) but does not make the global result safe.
- `semantic_low_geometry_high`: `C2` improves AUPRC but worsens Brier.

## Decision

Status:

```text
full_train_independent_combiner_upgrade_no_safe_gain
```

Reason:

```text
No upgraded combiner satisfies the pre-defined progression rule:
Delta AUPRC vs semantic_plus_geometry >= +0.01
or Delta Brier vs semantic_plus_geometry <= -0.005,
with threshold mistakes not exceeding fixes.
```

This is not a failure of the H002 question itself. It says the current controlled
bootstrap target and current deployable factors are not yet enough to claim that
the upgraded posterior is better than `semantic_plus_geometry`.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/slice_metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/threshold_transfer.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/predictions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/combiner_rows.jsonl
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `combiner_rows.jsonl` | 158 |
| `predictions.jsonl` | 1,264 |
| `metrics.csv` | 24 + header |
| `comparisons.csv` | 24 + header |
| `slice_metrics.csv` | 48 + header |
| `threshold_transfer.csv` | 8 + header |

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_smoke.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_smoke.py
```

Observed:

```text
validation_used=False
hidden_metadata_as_model_input=False
multi_view_as_model_input=False
trains_new_combiner=True
```

## Next TODO

Completed next action:

```text
full_train_independent_combiner_upgrade_error_analysis
```

Result:

```text
full_train_independent_combiner_upgrade_error_analysis_ready_for_decision
```

The error analysis shows that C2 is a ranking-oriented family gate with
calibration damage, while C3 is a safer threshold/calibration gate that loses
global ranking.

The next action is:

```text
full_train_independent_combiner_path_decision
```
