# Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Combiner Smoke

## Purpose

`128_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan.md`
의 next TODO인 `revised_sampling_all_label_ready_raw_witness_v2_combiner_smoke`를 진행했다.

핵심 질문:

```text
Can a repaired raw-witness posterior beat or calibrate against C3_linear_v2
under grouped train-only evaluation and the predeclared controls?
```

이 단계는 H002의 current simple reference를 `semantic_plus_geometry`에서 `C3_linear_v2`로
올린 뒤, calibrated linear, constrained monotonic additive, family-gated mixture,
limited interaction 후보를 비교한다.

## Boundary

- Split: Open3DSG train-only.
- validation/test row는 사용하지 않았다.
- review fields, hidden audit metadata, target labels, packet paths, multi-view evidence,
  `geometry_status`는 model input이 아니다.
- endpoint type은 main claim input이 아니라 ablation/control로만 사용했다.
- 결과는 hypothesis-stage diagnostic이며 paper-level metric evidence가 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_no_new_primary
rows=134
pos=67
neg=67
validation_used=False
best_candidate=C4_calibrated_linear_v2
best_d_auprc_vs_linear=-0.0139
primary_passes=0
fallback_passes=0
next=revised_sampling_all_label_ready_raw_witness_v2_combiner_error_analysis
```

## Result

Status:

```text
full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_no_new_primary
```

Grouped main views:

| View | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `C0_semantic_plus_geometry_legacy` | 0.3881 | 0.4481 | 0.3098 | 0.2283 | 0.4179 |
| `C1_raw_witness_only_v2` | 0.6191 | 0.6087 | 0.2990 | 0.2238 | 0.5746 |
| `C2_semantic_plus_raw_witness_v2` | 0.6115 | 0.6222 | 0.3087 | 0.2705 | 0.5597 |
| `C3_linear_v2` | 0.6293 | 0.6246 | 0.2966 | 0.2335 | 0.5821 |
| `C4_calibrated_linear_v2` | 0.5471 | 0.6107 | 0.2879 | 0.2161 | 0.5149 |
| `C5_constrained_monotonic_additive` | 0.4676 | 0.5477 | 0.3105 | 0.2697 | 0.4552 |
| `C6_family_gated_calibrated_mixture` | 0.5636 | 0.5720 | 0.3037 | 0.2234 | 0.5672 |
| `C7_limited_interaction_model` | 0.5727 | 0.5757 | 0.3112 | 0.2480 | 0.5522 |
| `C8_endpoint_type_ablation_only` | 0.8291 | 0.7935 | 0.1731 | 0.1011 | 0.7761 |

## Candidate Deltas Vs C3 Linear

| Candidate | dAUROC | dAUPRC | dBrier | dECE | dAcc | New-Fix | Primary Gate | Fallback |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `C4_calibrated_linear_v2` | -0.0822 | -0.0139 | -0.0087 | -0.0173 | -0.0672 | +9 | fail | fail |
| `C5_constrained_monotonic_additive` | -0.1617 | -0.0769 | +0.0139 | +0.0362 | -0.1269 | +17 | fail | fail |
| `C6_family_gated_calibrated_mixture` | -0.0657 | -0.0526 | +0.0071 | -0.0101 | -0.0149 | +2 | fail | fail |
| `C7_limited_interaction_model` | -0.0566 | -0.0488 | +0.0146 | +0.0146 | -0.0299 | +4 | fail | fail |

Interpretation:

- No repaired candidate beats `C3_linear_v2` under the predeclared primary gate.
- `C4_calibrated_linear_v2` improves Brier/ECE over `C3`, but loses AUPRC and adds more threshold errors.
- `C6` and `C7` improve the `relative_vertical` slice but hurt `support_contact`, so overall they do not pass.
- `C3_linear_v2` remains the current train-only reference.

## Family Tradeoff

New candidates vs `C3_linear_v2`:

| Family | Candidate | dAUPRC | dBrier | dECE |
| --- | --- | ---: | ---: | ---: |
| `support_contact` | `C4_calibrated_linear_v2` | +0.0422 | -0.0223 | -0.0325 |
| `relative_vertical` | `C4_calibrated_linear_v2` | -0.2322 | +0.0297 | +0.0384 |
| `support_contact` | `C6_family_gated_calibrated_mixture` | -0.0511 | +0.0297 | +0.0296 |
| `relative_vertical` | `C6_family_gated_calibrated_mixture` | +0.0638 | -0.0567 | -0.0744 |
| `support_contact` | `C7_limited_interaction_model` | -0.0414 | +0.0357 | +0.0285 |
| `relative_vertical` | `C7_limited_interaction_model` | +0.0363 | -0.0451 | +0.0353 |

Interpretation:

- `C4` helps `support_contact` but damages `relative_vertical`.
- `C6/C7` help `relative_vertical` calibration/ranking but damage `support_contact`.
- This confirms the previous diagnosis: a single repaired combiner is still mixing two different family regimes.

## Controls

Grouped controls:

| Control | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `K0_global_raw_witness_shuffle` | 0.4720 | 0.4898 | 0.3332 | 0.2666 | 0.4478 |
| `K1_within_family_raw_witness_shuffle` | 0.4874 | 0.4935 | 0.3299 | 0.2792 | 0.4776 |
| `K2_wrong_pair_raw_witness` | 0.3644 | 0.4395 | 0.4042 | 0.3720 | 0.3881 |
| `K3_family_only_offset` | 0.3086 | 0.3811 | 0.3179 | 0.2654 | 0.3507 |
| `K4_no_family_local_normalization` | 0.5997 | 0.6015 | 0.3119 | 0.2689 | 0.5672 |
| `K5_endpoint_type_only` | 0.9581 | 0.9369 | 0.0879 | 0.1154 | 0.8657 |

Key control result:

```text
K5_endpoint_type_only dominates every main candidate.
```

This is a strong shortcut warning. It means the current 134-row target slice is highly
explainable by endpoint/object-type metadata. Therefore endpoint type must remain a
control/audit axis, not a deployable main evidence axis, until a stricter target/control split
removes this shortcut.

Raw-witness controls still behave as expected:

- `C3_linear_v2` beats global shuffle by AUPRC `+0.1348`.
- `C3_linear_v2` beats within-family shuffle by AUPRC `+0.1310`.
- `C3_linear_v2` beats wrong-pair witness by AUPRC `+0.1851`.

So pair-specific raw witness evidence remains meaningful, but endpoint shortcut risk is now the
dominant blocker.

## Decision

Current conclusion:

```text
No repaired combiner becomes the new primary. C3_linear_v2 remains the current reference.
```

Allowed claim:

```text
Train-only combiner diagnostics show typed raw witness is useful, but the current target
slice has a strong endpoint-type shortcut and no repaired combiner beats C3_linear_v2.
```

Blocked claims:

- C4/C5/C6/C7 is a better posterior than C3.
- endpoint/object-type features can be used in the main reliability model.
- H002 has a paper-level posterior method result.
- support/vertical can be treated as solved by one shared combiner.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/129_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/combiner_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/predictions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/family_slices.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/family_deltas.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/transfer_vs_linear.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/transfer_vs_legacy.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/gate_evaluation.csv
```

Artifact row counts:

```text
combiner_rows.jsonl = 134
predictions.jsonl = 2010
metrics.csv = 46 lines
comparisons.csv = 69 lines
family_slices.csv = 31 lines
family_deltas.csv = 33 lines
transfer_vs_linear.csv = 9 lines
transfer_vs_legacy.csv = 9 lines
gate_evaluation.csv = 5 lines
```

## Next TODO

```text
revised_sampling_all_label_ready_raw_witness_v2_combiner_error_analysis
```

Goal:

- diagnose why C4 helps support but hurts vertical.
- diagnose why C6/C7 help vertical but hurt support.
- quantify endpoint-type shortcut and decide whether target construction must be revised again.
- decide whether H002 should continue with shared combiner, family-separated posterior, or target redesign.
