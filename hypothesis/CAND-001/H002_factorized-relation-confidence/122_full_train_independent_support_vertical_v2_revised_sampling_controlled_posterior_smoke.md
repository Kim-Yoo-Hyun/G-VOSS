# H002 Full-Train Independent Support/Vertical V2 Revised Sampling Controlled Posterior Smoke

## Purpose

`121_full_train_independent_support_vertical_v2_revised_sampling_source_feature_join.md`의 next TODO인
`revised_sampling_all_label_ready_controlled_posterior_smoke`를 진행했다. posterior-ready strict
slice `rank_band_balanced_revised_sampling`에서 semantic-only, geometry-only, semantic+geometry,
factorized posterior를 train-only grouped smoke로 비교했다.

핵심 질문:

```text
On a target-independence-audited strict relation-reliability slice, does the
factorized reliability posterior explain relation reliability better than
simpler semantic/geometry baselines?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- active target slice는 `rank_band_balanced_revised_sampling`이다.
- review fields, hidden audit metadata, target labels, packet paths, multi-view evidence는 model input이 아니다.
- 결과는 hypothesis-stage smoke이며 paper-level metric evidence가 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_no_strong_signal
rows=134
pos=67
neg=67
metrics=40
validation_used=False
d_auprc_factorized_vs_sg=-0.0058
d_auprc_factorized_vs_sgc=-0.0058
d_auprc_factorized_vs_semantic=-0.0150
d_auprc_factorized_vs_geometry=0.0291
next=revised_sampling_all_label_ready_controlled_error_analysis
```

## Target

| Rows | Positive | Negative |
| ---: | ---: | ---: |
| 134 | 67 | 67 |

By family:

| Family | Rows |
| --- | ---: |
| `support_contact` | 99 |
| `relative_vertical` | 35 |

## Grouped Main Views

`train_internal_grouped_by_scan` 기준:

| View | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.3476 | 0.4574 | 0.3148 | 0.2310 | 0.3731 |
| `geometry_only` | 0.3587 | 0.4132 | 0.3018 | 0.2104 | 0.3955 |
| `semantic_plus_geometry` | 0.3881 | 0.4481 | 0.3098 | 0.2283 | 0.4179 |
| `semantic_geometry_coverage` | 0.3881 | 0.4481 | 0.3098 | 0.2283 | 0.4179 |
| `factorized_reliability_posterior` | 0.3858 | 0.4424 | 0.3157 | 0.1999 | 0.3881 |

## Key Deltas

`train_internal_grouped_by_scan` 기준:

| Left | Right | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | --- | ---: | ---: | ---: |
| `factorized_reliability_posterior` | `semantic_plus_geometry` | -0.0022 | -0.0058 | +0.0058 |
| `factorized_reliability_posterior` | `semantic_geometry_coverage` | -0.0022 | -0.0058 | +0.0058 |
| `factorized_reliability_posterior` | `semantic_only` | +0.0382 | -0.0150 | +0.0009 |
| `factorized_reliability_posterior` | `geometry_only` | +0.0272 | +0.0291 | +0.0139 |

## Interpretation

- strict target과 feature contract는 실행 가능하다.
- 하지만 factorized posterior가 `semantic_plus_geometry`보다 좋아지지 않았다.
- factorized는 geometry-only보다 AUPRC가 높지만, Brier는 더 나쁘고 semantic+geometry 대비
  AUROC/AUPRC/Brier가 모두 불리하다.
- coverage block은 현재 모두 같은 값에 가까워 `semantic_geometry_coverage`가
  `semantic_plus_geometry`와 동일하게 나온다.
- ECE만 보면 factorized가 가장 낮지만, ranking/calibration을 함께 보면 강한 양성 신호로
  보기 어렵다.
- 따라서 현재 H002의 다음 문제는 combiner를 더 키우는 것이 아니라, 왜 factorized residual이
  semantic+geometry를 이기지 못하는지 failure/error analysis로 확인하는 것이다.

## Decision

현재 posterior smoke는:

```text
no_strong_signal
```

Reason:

- target-independence-audited strict slice에서 실행은 성공했다.
- 그러나 grouped-by-scan 기준 factorized posterior는 semantic+geometry 대비 AUPRC `-0.0058`,
  AUROC `-0.0022`, Brier `+0.0058`이다.
- 이 상태에서 “factorized reliability posterior가 더 낫다”는 주장은 할 수 없다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/122_full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready/posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready/predictions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready/comparisons.csv
```

## Verification

Observed:

```text
posterior_rows.jsonl = 134
predictions.jsonl = 1340
metrics.csv = 41 lines
comparisons.csv = 17 lines
family_slices.csv = 21 lines
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
revised_sampling_all_label_ready_controlled_error_analysis
```

Goal:

- identify why factorized residual features do not beat semantic+geometry.
- inspect family-specific and prediction-level failure modes.
- decide whether the issue is target definition, feature definition, combiner capacity, or relation-family heterogeneity.
