# H002 Full-Train Independent Revised Factor Smoke

## Purpose

이 문서는 79번에서 만든 revised factor dataset을 사용해 D1-D4 revised factor views를
train-only scan-grouped fold로 비교한 결과를 기록한다.

핵심 질문:

```text
raw geometry witness 기반 revised factor views가 semantic_plus_geometry보다
안전하게 좋아지는가?
```

## Boundary

- Split: Open3DSG train-only.
- Active target: `proposed_role_balanced_codex_ver`.
- Rows: 158.
- Positive/negative: 79/79.
- Revised views는 `semantic_plus_geometry` 위의 offset residual로 학습한다.
- 새 combiner는 train-only fold 내부에서만 학습한다.
- validation/test는 사용하지 않는다.
- hidden audit metadata는 model input이 아니다.
- `geometry_status`는 model input이 아니다.
- multi-view는 model input이 아니다.
- label은 `(codex_ver_full_train_independent)` bootstrap label이다.
- paper-level performance claim은 불가하다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_smoke.py
```

Observed:

```text
status=full_train_independent_revised_factor_smoke_positive
rows=158
validation_used=False
best_revised=D4_coverage_uncertainty_shrinkage
d_auprc_vs_sg=+0.1241
d_brier_vs_sg=-0.0462
progress_views=D1_revised_residual_base,D2_support_contact_split_residual,D3_relative_vertical_order_residual,D4_coverage_uncertainty_shrinkage
next=full_train_independent_revised_factor_error_analysis
```

## Tested Views

Baselines:

```text
semantic_only
geometry_only
semantic_plus_geometry
current_factorized_reliability_posterior
residual_reliability_model
```

Revised offset views:

```text
D1_revised_residual_base
D2_support_contact_split_residual
D3_relative_vertical_order_residual
D4_coverage_uncertainty_shrinkage
```

## Grouped Main Result

Scan-grouped train-only folds:

| View | Kind | AUROC | AUPRC | Brier | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_only` | baseline | 0.6623 | 0.6291 | 0.2360 | 0.6076 |
| `geometry_only` | baseline | 0.4575 | 0.5098 | 0.2559 | 0.4810 |
| `semantic_plus_geometry` | baseline | 0.6640 | 0.6300 | 0.2341 | 0.6392 |
| `current_factorized_reliability_posterior` | baseline | 0.6531 | 0.6253 | 0.2363 | 0.5823 |
| `residual_reliability_model` | baseline | 0.6558 | 0.6255 | 0.2358 | 0.6203 |
| `D1_revised_residual_base` | revised_offset | 0.7782 | 0.7116 | 0.1905 | 0.7468 |
| `D2_support_contact_split_residual` | revised_offset | 0.7846 | 0.7193 | 0.1901 | 0.7215 |
| `D3_relative_vertical_order_residual` | revised_offset | 0.7895 | 0.7382 | 0.1870 | 0.7342 |
| `D4_coverage_uncertainty_shrinkage` | revised_offset | 0.7879 | 0.7541 | 0.1879 | 0.7342 |

## Delta vs Semantic+Geometry

| View | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | ---: | ---: | ---: |
| `current_factorized_reliability_posterior` | -0.0109 | -0.0047 | +0.0021 |
| `residual_reliability_model` | -0.0082 | -0.0045 | +0.0017 |
| `D1_revised_residual_base` | +0.1142 | +0.0816 | -0.0437 |
| `D2_support_contact_split_residual` | +0.1207 | +0.0893 | -0.0441 |
| `D3_relative_vertical_order_residual` | +0.1255 | +0.1082 | -0.0471 |
| `D4_coverage_uncertainty_shrinkage` | +0.1239 | +0.1241 | -0.0462 |

Interpretation:

- 기존 `current_factorized_reliability_posterior`와 `residual_reliability_model`은 여전히
  `semantic_plus_geometry`보다 약하다.
- raw geometry witness를 materialize한 D1-D4는 모두 train-only grouped fold에서
  `semantic_plus_geometry`를 크게 넘는다.
- D4가 AUPRC 기준 best revised view이고, D3가 Brier 기준 best revised view다.

## Threshold Transfer

Reference: `semantic_plus_geometry`.

| View | Fixes | New Mistakes | Both Correct | Both Wrong | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: |
| `current_factorized_reliability_posterior` | 1 | 10 | 91 | 56 | +9 |
| `residual_reliability_model` | 1 | 4 | 97 | 56 | +3 |
| `D1_revised_residual_base` | 26 | 9 | 92 | 31 | -17 |
| `D2_support_contact_split_residual` | 21 | 8 | 93 | 36 | -13 |
| `D3_relative_vertical_order_residual` | 24 | 9 | 92 | 33 | -15 |
| `D4_coverage_uncertainty_shrinkage` | 21 | 6 | 95 | 36 | -15 |

Interpretation:

```text
D1-D4는 모두 semantic_plus_geometry 대비 new mistakes보다 fixes가 많다.
```

이는 이전 C1-C3와 가장 다른 점이다. 이전 C2는 AUPRC를 올렸지만 threshold transfer가
안전하지 않았고, C3는 threshold는 안전했지만 AUPRC가 낮았다. 이번 D1-D4는 둘을 동시에
개선했다.

## Slice Clues

D4 vs `semantic_plus_geometry`:

| Slice | Rows | SG AUPRC | D4 AUPRC | SG Brier | D4 Brier |
| --- | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | 72 | 0.7121 | 0.8566 | 0.2233 | 0.1607 |
| `relative_vertical` | 55 | 0.6729 | 0.7922 | 0.2200 | 0.1793 |
| `proximity` | 31 | 0.3960 | 0.3407 | 0.2843 | 0.2665 |
| `semantic_high_geometry_low` | 16 | 0.6983 | 0.9583 | 0.2391 | 0.1328 |
| `semantic_low_geometry_high` | 97 | 0.5903 | 0.7271 | 0.2379 | 0.1872 |
| `semantic_geometry_close` | 45 | 0.7013 | 0.7597 | 0.2243 | 0.2091 |

Interpretation:

- `support_contact`와 `relative_vertical`에서 revised factor design의 의도와 맞는 gain이
  보인다.
- `semantic_high_geometry_low`와 `semantic_low_geometry_high` 양방향 mismatch 모두에서
  gain이 보인다.
- `proximity`는 Brier는 좋아지지만 AUPRC는 낮아진다. 다음 error analysis에서 반드시
  확인해야 한다.

## What This Means

현재 결과는 H002에 유리한 첫 positive smoke다.

다만 아직 강한 claim은 불가하다.

이유:

- label은 여전히 Codex bootstrap label이다.
- rows는 158개 controlled slice다.
- validation/test는 사용하지 않았다.
- raw geometry witness가 target construction과 우연히 맞는 shortcut인지 확인해야 한다.
- D4가 `predicate_family` categorical feature를 포함하므로 family shortcut 여부를 확인해야
  한다.

따라서 이 결과는 다음 claim만 허용한다.

```text
Revised raw-witness factorization is a promising hypothesis-stage direction.
```

다음 claim은 아직 blocked다.

```text
factorized reliability posterior improves relation reliability at paper level.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/threshold_transfer.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/slice_metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/predictions.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_smoke.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_smoke.py
```

Observed:

```text
validation_used=False
geometry_status_as_model_input=False
hidden_metadata_as_model_input=False
multi_view_as_model_input=False
```

## Next TODO

Completed next action:

```text
full_train_independent_revised_factor_error_analysis
```

Result:

```text
full_train_independent_revised_factor_error_analysis_ready
```

Implication:

- D1-D4의 gain이 어떤 rows/families에서 생기는지 확인한다.
- `proximity` AUPRC drop을 분석한다.
- D4의 family categorical feature가 shortcut인지 확인한다.
- raw geometry witness가 target construction shortcut으로 작동하는지 점검한다.
- positive smoke를 paper claim으로 승격할 수 있는 조건과 아직 막는 조건을 분리한다.

Next action:

```text
full_train_independent_revised_factor_shortcut_controls
```
