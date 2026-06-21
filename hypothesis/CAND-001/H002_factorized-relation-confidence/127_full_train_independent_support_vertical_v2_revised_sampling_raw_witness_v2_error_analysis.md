# Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Error Analysis

## Purpose

`126_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke.md`
의 next TODO인 `revised_sampling_all_label_ready_raw_witness_v2_error_analysis`를 진행했다.

핵심 질문:

```text
The raw-witness v2 smoke is positive, but where does the gain come from and
what still blocks a defensible posterior method claim?
```

이 단계는 새 모델을 학습하지 않는다. `126`의 grouped-by-scan prediction을
row-level, family-level, feature-slice-level로 분해해 다음 combiner repair 방향을 정한다.

## Boundary

- Split: Open3DSG train-only.
- validation/test row는 사용하지 않았다.
- 새 모델을 학습하지 않았다.
- H001 artifact를 수정하지 않았다.
- review fields, hidden audit metadata, target labels, packet paths, multi-view evidence는
  model input이 아니다.
- 결과는 hypothesis-stage diagnostic이며 paper-level metric evidence가 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_ready_support_driven_linear_gap
rows=134
validation_used=False
d_auprc_primary_vs_sg=0.1622
d_brier_primary_vs_sg=-0.0115
d_auprc_linear_vs_sg=0.1764
d_auprc_primary_vs_linear=-0.0143
diagnoses=9
next=revised_sampling_all_label_ready_raw_witness_v2_combiner_repair_plan
```

## Result

Status:

```text
full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_ready_support_driven_linear_gap
```

Primary comparison:

| Comparison | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | ---: | ---: | ---: |
| `family_shrinkage` - `semantic_plus_geometry` | +0.2350 | +0.1622 | -0.0115 |
| `linear_v2` - `semantic_plus_geometry` | +0.2413 | +0.1764 | -0.0132 |
| `family_shrinkage` - `linear_v2` | -0.0062 | -0.0143 | +0.0017 |

## Transfer Against Semantic+Geometry

Threshold transfer against `semantic_plus_geometry`:

| View | Fixes SG Errors | Adds Errors | Both Correct | Both Wrong | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: |
| `raw_witness_only_v2` | 39 | 18 | 38 | 39 | -21 |
| `semantic_plus_raw_witness_v2` | 38 | 19 | 37 | 40 | -19 |
| `factorized_reliability_posterior_v2_linear` | 42 | 20 | 36 | 36 | -22 |
| `factorized_reliability_posterior_v2_family_shrinkage` | 42 | 14 | 42 | 36 | -28 |
| `no_family_local_normalization` | 40 | 20 | 36 | 38 | -20 |
| `endpoint_type_ablation` | 55 | 7 | 49 | 23 | -48 |

Interpretation:

- `raw_witness_only_v2`만으로도 `semantic_plus_geometry` error를 많이 고친다.
- `family_shrinkage`는 threshold 기준에서 error 추가가 가장 적다.
- 하지만 `endpoint_type_ablation`이 매우 강한 transfer를 보이므로 endpoint/object-type shortcut
  가능성을 별도 control로 다뤄야 한다.

## Linear Vs Family Shrinkage

`family_shrinkage`를 reference로 봤을 때:

| View | Fixes Primary Errors | Adds Errors | Both Correct | Both Wrong | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: |
| `factorized_reliability_posterior_v2_linear` | 0 | 6 | 78 | 50 | +6 |
| `semantic_plus_raw_witness_v2` | 0 | 9 | 75 | 50 | +9 |
| `raw_witness_only_v2` | 4 | 11 | 73 | 46 | +7 |

Interpretation:

- threshold accuracy 관점에서는 `family_shrinkage`가 `linear_v2`보다 보수적이고 좋다.
- 그러나 AUPRC/Brier에서는 `linear_v2`가 더 좋다.
- 따라서 다음 combiner는 단순히 `family_shrinkage`를 유지하거나 SOTA 고용량 모델을 넣는 것이 아니라,
  ranking/calibration/threshold tradeoff를 명시적으로 분리해야 한다.

## Family Slices

`semantic_plus_geometry` 대비:

| Family | View | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | `raw_witness_only_v2` | 99 | 50 | 49 | +0.1611 | -0.0320 | -18 |
| `support_contact` | `semantic_plus_raw_witness_v2` | 99 | 50 | 49 | +0.1724 | -0.0131 | -15 |
| `support_contact` | `linear_v2` | 99 | 50 | 49 | +0.1728 | -0.0253 | -18 |
| `support_contact` | `family_shrinkage` | 99 | 50 | 49 | +0.1659 | -0.0282 | -23 |
| `relative_vertical` | `raw_witness_only_v2` | 35 | 17 | 18 | +0.0243 | +0.0490 | -3 |
| `relative_vertical` | `semantic_plus_raw_witness_v2` | 35 | 17 | 18 | +0.0412 | +0.0329 | -4 |
| `relative_vertical` | `linear_v2` | 35 | 17 | 18 | +0.0588 | +0.0211 | -4 |
| `relative_vertical` | `family_shrinkage` | 35 | 17 | 18 | +0.0270 | +0.0357 | -5 |

`linear_v2` 대비 `family_shrinkage`:

| Family | Comparison | dAUPRC | dBrier | New-Fix |
| --- | --- | ---: | ---: | ---: |
| `support_contact` | `linear_v2` - `family_shrinkage` | +0.0069 | +0.0029 | +5 |
| `relative_vertical` | `linear_v2` - `family_shrinkage` | +0.0318 | -0.0146 | +1 |

Interpretation:

- positive smoke의 핵심 신호는 `support_contact`에서 나온다.
- `relative_vertical`은 ranking이 개선되지만 Brier가 악화된다.
- `relative_vertical`에서는 오히려 `linear_v2`가 `family_shrinkage`보다 Brier를 낮춘다.
- 그러므로 family별 calibration/normalization을 분리하지 않으면 raw witness gain이 논문 claim으로
  방어되기 어렵다.

## Diagnosis

Observed diagnostic flags:

- `typed_raw_witness_v2_adds_stable_signal_over_semantic_plus_geometry`
- `raw_witness_controls_reduce_gain`
- `family_shrinkage_not_best_combiner_for_ranking_or_brier`
- `linear_v2_is_current_strongest_simple_posterior`
- `family_local_normalization_mainly_improves_calibration_not_ranking`
- `support_contact_drives_positive_signal`
- `relative_vertical_has_calibration_regression`
- `family_effect_is_heterogeneous`
- `endpoint_type_ablation_has_nontrivial_signal_and_needs_shortcut_control`

## Decision

현재 결론:

```text
typed raw witness evidence is necessary, but the final posterior combiner is not settled.
```

Allowed claim:

```text
Train-only diagnostics support typed raw witness as a stronger geometry evidence axis than legacy p_geom_valid.
```

Blocked claim:

```text
The family-shrinkage posterior is the final or paper-level superior combiner.
```

다음 단계는 SOTA급 high-capacity combiner를 바로 넣는 것이 아니다. 먼저 다음을 고정해야 한다.

- `linear_v2`를 current simple reference로 둔다.
- `family_shrinkage`는 threshold/ECE 장점은 있지만 ranking/Brier 약점이 있음을 기록한다.
- `relative_vertical` calibration을 별도로 수리한다.
- endpoint/object-type shortcut을 별도 control 또는 ablation-only feature로 유지한다.
- 이후 constrained monotonic additive, family-gated mixture, calibrated linear, small interaction model을
  같은 train-only protocol로 비교한다.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/127_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/row_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/slice_deltas.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/transfer_vs_semantic_plus_geometry.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/transfer_vs_primary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/feature_label_summary.csv
```

Artifact row counts:

```text
row_errors.jsonl = 134
slice_deltas.csv = 1093 lines
transfer_vs_semantic_plus_geometry.csv = 9 lines
transfer_vs_primary.csv = 4 lines
feature_label_summary.csv = 7 lines
top_primary_losses_vs_sg.jsonl = 25
top_primary_wins_vs_sg.jsonl = 25
top_linear_wins_vs_primary.jsonl = 25
top_linear_losses_vs_primary.jsonl = 25
```

## Next TODO

```text
revised_sampling_all_label_ready_raw_witness_v2_combiner_repair_plan
```

Goal:

- define the next combiner candidates without hiding the current failure modes.
- keep `linear_v2` as the current strongest simple posterior reference.
- design constrained alternatives for ranking/calibration/threshold tradeoff.
- add endpoint shortcut control to the next smoke plan.
- keep validation/test unavailable and paper-level posterior claim blocked.
