# Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Posterior Smoke

## Purpose

`125_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2.md`
의 next TODO인 `revised_sampling_all_label_ready_raw_witness_v2_posterior_smoke`를 진행했다.

핵심 질문:

```text
Does typed relation-specific raw witness evidence explain train-only relation
reliability better than the legacy p_geom_valid scalar and semantic+geometry baseline?
```

이 단계는 combiner novelty를 확정하는 것이 아니라, H002에서 이전 smoke가 실패한 원인이
`semantic + p_geom_valid` 수준의 과도한 geometry compression이었는지 검증하는
train-only hypothesis-stage smoke다.

## Boundary

- Split: Open3DSG train-only.
- validation/test row는 사용하지 않았다.
- H001 artifact를 수정하지 않았다.
- active target slice는 `rank_band_balanced_revised_sampling`이다.
- review fields, hidden audit metadata, target labels, packet paths, multi-view evidence,
  `geometry_status`, free predicate/family categorical shortcut은 model input이 아니다.
- typed raw witness는 v2 feature contract에서 허용된 geometry evidence로만 사용했다.
- 결과는 hypothesis-stage diagnostic이며 paper-level metric evidence가 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_positive_smoke
rows=134
pos=67
neg=67
metrics=55
validation_used=False
d_auprc_shrinkage_vs_sg=0.1622
d_brier_shrinkage_vs_sg=-0.0115
d_auprc_sem_raw_vs_sg=0.1740
d_auprc_raw_vs_legacy=0.1955
d_auprc_shrinkage_vs_shuffle=0.1205
d_auprc_shrinkage_vs_wrong_pair=0.1708
next=revised_sampling_all_label_ready_raw_witness_v2_error_analysis
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
| `legacy_geometry_only` | 0.3587 | 0.4132 | 0.3018 | 0.2104 | 0.3955 |
| `semantic_plus_geometry` | 0.3881 | 0.4481 | 0.3098 | 0.2283 | 0.4179 |
| `raw_witness_only_v2` | 0.6191 | 0.6087 | 0.2990 | 0.2238 | 0.5746 |
| `semantic_plus_raw_witness_v2` | 0.6115 | 0.6222 | 0.3087 | 0.2705 | 0.5597 |
| `factorized_reliability_posterior_v2_linear` | 0.6293 | 0.6246 | 0.2966 | 0.2335 | 0.5821 |
| `factorized_reliability_posterior_v2_family_shrinkage` | 0.6231 | 0.6103 | 0.2983 | 0.2212 | 0.6269 |

## Key Deltas

`train_internal_grouped_by_scan` 기준:

| Left | Right | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | --- | ---: | ---: | ---: |
| `factorized_reliability_posterior_v2_family_shrinkage` | `semantic_plus_geometry` | +0.2350 | +0.1622 | -0.0115 |
| `factorized_reliability_posterior_v2_linear` | `semantic_plus_geometry` | +0.2413 | +0.1764 | -0.0132 |
| `semantic_plus_raw_witness_v2` | `semantic_plus_geometry` | +0.2234 | +0.1740 | -0.0011 |
| `raw_witness_only_v2` | `legacy_geometry_only` | +0.2604 | +0.1955 | -0.0028 |
| `factorized_reliability_posterior_v2_family_shrinkage` | `raw_witness_shuffle_global` | +0.1510 | +0.1205 | -0.0349 |
| `factorized_reliability_posterior_v2_family_shrinkage` | `raw_witness_shuffle_within_family` | +0.1357 | +0.1168 | -0.0316 |
| `factorized_reliability_posterior_v2_family_shrinkage` | `wrong_pair_raw_witness` | +0.2586 | +0.1708 | -0.1059 |
| `factorized_reliability_posterior_v2_family_shrinkage` | `factorized_reliability_posterior_v2_linear` | -0.0062 | -0.0143 | +0.0017 |

## Family Deltas

`semantic_plus_geometry` 대비:

| Family | View | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | --- | ---: | ---: | ---: |
| `support_contact` | `factorized_reliability_posterior_v2_family_shrinkage` | +0.2902 | +0.1659 | -0.0282 |
| `relative_vertical` | `factorized_reliability_posterior_v2_family_shrinkage` | +0.0261 | +0.0270 | +0.0357 |
| `support_contact` | `semantic_plus_raw_witness_v2` | +0.2710 | +0.1724 | -0.0131 |
| `relative_vertical` | `semantic_plus_raw_witness_v2` | +0.0131 | +0.0412 | +0.0329 |

## Interpretation

이번 smoke는 이전 `semantic + p_geom_valid` posterior 실패 원인이 combiner capacity만의
문제가 아니라 geometry evidence definition 문제였다는 쪽을 지지한다.

중요한 점:

- `raw_witness_only_v2`가 `legacy_geometry_only`보다 AUROC/AUPRC를 크게 개선했다.
- `semantic_plus_raw_witness_v2`와 두 factorized v2 posterior가 모두
  `semantic_plus_geometry`보다 좋아졌다.
- global shuffle, within-family shuffle, wrong-pair control에서 gain이 크게 줄어들어,
  단순 row count/family shortcut만으로 설명되지는 않는다.
- 하지만 `factorized_reliability_posterior_v2_family_shrinkage`가
  `factorized_reliability_posterior_v2_linear`보다 AUPRC/Brier에서 약간 불리하다.
  따라서 현재 결과는 "typed raw witness evidence가 필요하다"는 신호이지,
  "family shrinkage combiner가 최선이다"는 증거는 아니다.
- family-wise로는 `support_contact`가 주된 positive signal이다.
  `relative_vertical`은 AUPRC가 소폭 좋아지지만 Brier가 악화되어 calibration/threshold
  관점의 error analysis가 필요하다.

## Decision

현재 posterior smoke는:

```text
positive_smoke
```

Reason:

- train-only grouped-by-scan 기준 raw witness v2가 legacy `p_geom_valid` geometry보다 강하다.
- `factorized_reliability_posterior_v2_family_shrinkage`는 `semantic_plus_geometry` 대비
  AUPRC `+0.1622`, AUROC `+0.2350`, Brier `-0.0115`다.
- required raw-witness controls는 true raw witness view보다 낮게 나온다.

Claim boundary:

- H002 posterior method claim은 아직 확정하지 않는다.
- 현재 허용되는 주장은 "typed relation-specific raw witness evidence가 H002의 posterior
  evidence axis로 필요해 보인다"는 train-only diagnostic claim이다.
- 다음 단계에서 row-level/family-level error analysis, threshold transfer, control failure
  case를 확인해야 한다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/126_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/predictions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/family_slices.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/family_deltas.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/matched_pairs.jsonl
```

## Verification

Observed:

```text
posterior_rows.jsonl = 134
predictions.jsonl = 1876
matched_pairs.jsonl = 66
metrics.csv = 56 lines
comparisons.csv = 25 lines
family_slices.csv = 29 lines
family_deltas.csv = 7 lines
validation_errors = 0
validation_used = False
test_used = False
```

## Next TODO

Current next action:

```text
revised_sampling_all_label_ready_raw_witness_v2_error_analysis
```

Goal:

- inspect why linear beats family shrinkage in AUPRC/Brier.
- separate support_contact gains from relative_vertical calibration failures.
- identify whether remaining errors come from raw witness definition, target ambiguity, endpoint/object type shortcut, or combiner form.
- decide whether the next combiner should be linear, calibrated monotonic additive, family-gated mixture, or a constrained interaction model.
