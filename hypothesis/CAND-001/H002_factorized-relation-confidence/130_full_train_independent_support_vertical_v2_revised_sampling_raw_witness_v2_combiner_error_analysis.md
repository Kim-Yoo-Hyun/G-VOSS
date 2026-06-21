# Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Combiner Error Analysis

## Purpose

`129_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke.md`
의 next TODO인 `revised_sampling_all_label_ready_raw_witness_v2_combiner_error_analysis`를
진행했다.

핵심 질문:

```text
Why did C4-C7 fail to replace C3_linear_v2, and is the current blocker posterior
combiner capacity or target/evidence shortcut?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test row는 사용하지 않았다.
- 새 posterior model은 학습하지 않았다.
- 129번 combiner smoke의 grouped prediction만 post-hoc으로 분석했다.
- endpoint/object-type feature는 main reliability evidence가 아니라 shortcut control로만
  분석했다.
- 결과는 hypothesis-stage diagnostic이며 paper-level metric evidence가 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_ready_endpoint_control_needed
rows=134
pos=67
neg=67
endpoint_d_auprc_vs_c3=0.3124
endpoint_new_errors_minus_fixes=-38
endpoint_shortcut_severity=severe
next=revised_sampling_all_label_ready_endpoint_controlled_resampling_plan
```

## Result

Status:

```text
full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_ready_endpoint_control_needed
```

Main diagnosis:

- `endpoint_type_shortcut_dominates_current_target_slice`
- `C4_calibrated_linear_v2_does_not_improve_ranking_over_c3`
- `C5_constrained_monotonic_additive_does_not_improve_ranking_over_c3`
- `C6_family_gated_calibrated_mixture_does_not_improve_ranking_over_c3`
- `C7_limited_interaction_model_does_not_improve_ranking_over_c3`
- `c4_calibrated_linear_helps_support_contact_but_breaks_relative_vertical`
- `C6_family_gated_calibrated_mixture_trades_support_contact_loss_for_relative_vertical_gain`
- `C7_limited_interaction_model_trades_support_contact_loss_for_relative_vertical_gain`
- `pair_specific_raw_witness_signal_survives_shuffle_and_wrong_pair_controls`
- `combiner_capacity_is_not_the_current_primary_blocker`
- `next_step_should_control_endpoint_pattern_before_family_separated_posterior`

## Endpoint Shortcut

`K5_endpoint_type_only` vs `C3_linear_v2`:

| Control | dAUROC | dAUPRC | dBrier | dECE | dAcc | Fixes C3 | Adds Error | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `K5_endpoint_type_only` | +0.3288 | +0.3124 | -0.2088 | -0.1181 | +0.2836 | 44 | 6 | -38 |

Additional shortcut indicators:

```text
endpoint_flag_rows_in_pure_groups = 100 / 134
endpoint_label_rows_in_pure_groups_min2 = 67 / 134
endpoint_shortcut_severity = severe
```

해석:

- 현재 134-row target slice는 endpoint/object-type pattern만으로도 상당 부분 설명된다.
- 이 상태에서 더 강한 combiner나 family-separated posterior를 넣으면, relation reliability가 아니라
  endpoint shortcut을 더 잘 학습할 가능성이 크다.
- 따라서 endpoint feature는 deployable main evidence가 아니라 target/control audit axis로 유지해야 한다.

## Candidate Transfer Vs C3

| Candidate | Fixes C3 | Adds Error | Both Correct | Both Wrong | New-Fix | dAUPRC | dBrier | dECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `C4_calibrated_linear_v2` | 16 | 25 | 53 | 40 | +9 | -0.0139 | -0.0087 | -0.0173 |
| `C5_constrained_monotonic_additive` | 8 | 25 | 53 | 48 | +17 | -0.0769 | +0.0139 | +0.0362 |
| `C6_family_gated_calibrated_mixture` | 8 | 10 | 68 | 48 | +2 | -0.0526 | +0.0071 | -0.0101 |
| `C7_limited_interaction_model` | 7 | 11 | 67 | 49 | +4 | -0.0488 | +0.0146 | +0.0146 |

해석:

- C4는 calibration/Brier 쪽 보정 효과가 있지만 threshold transfer에서 C3보다 error를 더 만든다.
- C6/C7은 error 추가가 작지만 ranking과 Brier 기준으로 C3를 넘지 못한다.
- C5는 단조 additive라는 원리적 장점에도 불구하고 현재 feature/target slice에서는 과도하게 약하다.

## Family Tradeoff

| Family | Candidate | Fixes C3 | Adds Error | New-Fix | dAUPRC vs C3 | dBrier vs C3 | dAUPRC vs Legacy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `relative_vertical` | `C4_calibrated_linear_v2` | 6 | 14 | +8 | -0.2322 | +0.0297 | -0.1734 |
| `relative_vertical` | `C6_family_gated_calibrated_mixture` | 4 | 1 | -3 | +0.0638 | -0.0567 | +0.1226 |
| `relative_vertical` | `C7_limited_interaction_model` | 3 | 3 | 0 | +0.0363 | -0.0451 | +0.0951 |
| `support_contact` | `C4_calibrated_linear_v2` | 10 | 11 | +1 | +0.0422 | -0.0223 | +0.2150 |
| `support_contact` | `C6_family_gated_calibrated_mixture` | 4 | 9 | +5 | -0.0511 | +0.0297 | +0.1217 |
| `support_contact` | `C7_limited_interaction_model` | 4 | 8 | +4 | -0.0414 | +0.0357 | +0.1314 |

해석:

- C4는 `support_contact`에는 도움이 되지만 `relative_vertical`을 크게 망가뜨린다.
- C6/C7은 `relative_vertical`에는 도움이 되지만 `support_contact`를 손상한다.
- 이것은 shared combiner 하나로 두 family를 동시에 해결하기 어렵다는 신호다.
- 다만 지금 당장 family-separated posterior로 가기에는 endpoint shortcut이 더 큰 blocker다.

## Decision

현재 결론:

```text
Do not pursue a higher-capacity or family-separated posterior as the immediate
next step. The current blocker is target/evidence shortcut, because endpoint-only
controls explain the current 134-row slice more strongly than the typed raw-witness
posterior.
```

따라서 다음 순서는 다음이 맞다.

1. endpoint-controlled resampling protocol을 먼저 만든다.
2. endpoint pattern이 target을 설명하는 정도를 낮춘다.
3. 그 이후에도 C3가 한계로 남는지 확인한다.
4. 그때 family-separated support/vertical posterior 또는 multi-view audit evidence를 검토한다.

Allowed claim:

```text
Train-only error analysis shows that combiner capacity is not the current primary
blocker; the immediate blocker is endpoint/object-type shortcut in the current
support/vertical target slice, while pair-specific raw witness still carries
nontrivial signal under shuffle and wrong-pair controls.
```

Blocked claims:

- C4/C5/C6/C7 is a better posterior than C3.
- endpoint/object-type features are valid deployable reliability evidence.
- family-separated posterior should be tested before endpoint-controlled target repair.
- H002 has paper-level posterior superiority evidence.
- validation/test performance can be inferred from this train-only diagnostic.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/130_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/row_diagnostics.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/candidate_transfer.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/family_tradeoff.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/endpoint_flag_groups.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/endpoint_label_groups.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/feature_target_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/representative_rows.jsonl
```

Artifact row counts:

```text
row_diagnostics.jsonl = 134
candidate_transfer.csv = 139 lines
family_tradeoff.csv = 9 lines
endpoint_flag_groups.csv = 14 lines
endpoint_label_groups.csv = 95 lines
feature_target_summary.csv = 33 lines
representative_rows.jsonl = 53
```

## Next TODO

```text
revised_sampling_all_label_ready_endpoint_controlled_resampling_plan
```

Goal:

- define endpoint-controlled positive/negative matching keys.
- reduce endpoint/object-type shortcut before further posterior claims.
- keep C3 as current reference during target repair.
- defer family-separated posterior until endpoint-controlled target slice exists.
