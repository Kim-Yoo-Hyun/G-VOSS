# Full-Train Independent Support/Vertical V2 Revised Sampling Controlled Error Analysis

## Purpose

`122_full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke.md`
에서 factorized posterior가 `semantic_plus_geometry`를 이기지 못한 원인을
prediction-level, family-level, quadrant-level로 분해한다.

핵심 질문은 다음이다.

- 실패 원인이 target definition 문제인가?
- feature definition 문제인가?
- combiner capacity 문제인가?
- relation family heterogeneity 문제인가?

## Boundary

- Train-only post-hoc diagnostic이다.
- Validation/test row는 사용하지 않았다.
- 새 모델을 학습하지 않고, grouped-by-scan posterior smoke prediction만 분석했다.
- review fields, target labels, hidden audit metadata, packet paths, multi-view evidence는 model input이 아니다.
- 결과는 hypothesis-stage 진단이며 paper-level metric이 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis.py
```

Console summary:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis_ready_feature_family_misalignment
rows=134
validation_used=False
d_auprc_factorized_vs_sg=-0.0058
d_brier_factorized_vs_sg=0.0058
new_errors_minus_fixes=4
diagnoses=6
next=revised_sampling_all_label_ready_factor_definition_repair_plan
```

## Result

Status:

```text
full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis_ready_feature_family_misalignment
```

Global grouped-by-scan delta:

| Comparison | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | ---: | ---: | ---: |
| `factorized_reliability_posterior` - `semantic_plus_geometry` | -0.0022 | -0.0058 | +0.0058 |

Threshold transfer against `semantic_plus_geometry`:

| View | Fixes SG Errors | Adds Errors | Both Correct | Both Wrong | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: |
| `factorized_reliability_posterior` | 5 | 9 | 47 | 73 | +4 |

Family slices:

| Family | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | 99 | 50 | 49 | +0.0023 | +0.0044 | +2 |
| `relative_vertical` | 35 | 17 | 18 | -0.0813 | +0.0100 | +2 |

Quadrant slices:

| Quadrant | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `LH_low_semantic_high_geometry` | 84 | 45 | 39 | -0.0201 | -0.0005 | +5 |
| `HH_high_semantic_high_geometry` | 22 | 12 | 10 | -0.0024 | +0.0060 | +1 |
| `LL_low_semantic_low_geometry` | 20 | 5 | 15 | -0.0001 | +0.0536 | 0 |
| `HL_high_semantic_low_geometry` | 8 | 5 | 3 | -0.0300 | -0.0477 | -2 |

## Diagnosis

Observed diagnostic flags:

- `factorized_does_not_add_stable_signal_over_semantic_plus_geometry`
- `coverage_factor_is_constant_or_noninformative_in_all_label_ready_slice`
- `factorized_threshold_adds_more_errors_than_it_fixes`
- `relative_vertical_loses_ranking_signal_after_factorization`
- `support_contact_has_weak_ranking_gain_but_worse_calibration`
- `family_effects_have_opposite_directions`

Interpretation:

- 현재 문제는 posterior 결합 방식만의 문제가 아니다.
- `semantic_plus_geometry`보다 더 많은 factor를 넣었지만 grouped-by-scan에서는 안정적 이득이 없다.
- `support_contact`는 ranking gain이 거의 없고 calibration이 나빠진다.
- `relative_vertical`은 factorized feature가 `semantic_plus_geometry`의 기존 신호를 크게 손상한다.
- coverage factor는 all-label-ready slice에서 거의 상수처럼 동작하므로 현재 posterior 개선 요인이 아니다.
- 따라서 SOTA급 high-capacity combiner를 바로 도입하면 feature/target misalignment를 가린 채 overfit할 위험이 크다.

## Decision

현재 blocker는 `combiner capacity`보다 `feature/family alignment`로 본다.
다음 단계는 factorized posterior를 더 복잡하게 만드는 것이 아니라,
typed geometry factor와 family-specific normalization을 먼저 수리하는 것이다.

Allowed claim:

```text
Train-only diagnostics show that semantic score, p_geom_valid, and simple
interaction terms are not yet sufficient to form a stable relation reliability
posterior on the revised all-label-ready slice.
```

Blocked claim:

```text
The current factorized posterior improves relation reliability over
semantic+geometry.
```

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/row_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/slice_deltas.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/transfer_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/feature_label_summary.csv
```

Artifact row counts:

```text
row_errors.jsonl = 134
slice_deltas.csv = 166 lines
transfer_summary.csv = 6 lines
feature_label_summary.csv = 7 lines
```

## Next TODO

```text
revised_sampling_all_label_ready_factor_definition_repair_plan
```

Goal:

- `support_contact`와 `relative_vertical`을 같은 residual vector로 밀어 넣지 않는다.
- `p_geom_valid`를 family-local calibrated evidence로 재정의할 수 있는지 검토한다.
- `consistency_score`, `absolute_disagreement`, `underconfidence_score`, `overconfidence_score`가 family별로 반대 방향 의미를 갖는지 점검한다.
- high-capacity combiner는 feature repair 이후로 미룬다.
