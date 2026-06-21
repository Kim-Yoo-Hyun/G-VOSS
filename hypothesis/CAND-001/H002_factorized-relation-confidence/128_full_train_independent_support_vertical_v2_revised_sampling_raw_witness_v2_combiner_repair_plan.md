# Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Combiner Repair Plan

## Purpose

`127_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis.md`
의 next TODO인 `revised_sampling_all_label_ready_raw_witness_v2_combiner_repair_plan`을 진행했다.

핵심 질문:

```text
Given that typed raw witness is positive but family_shrinkage is not the best
combiner, what should the next posterior comparison actually test?
```

이 단계는 새 모델을 학습하지 않는다. 목적은 다음 smoke의 combiner 후보, reference,
controls, success gate를 고정하는 것이다.

## Boundary

- Split: Open3DSG train-only.
- validation/test row는 사용하지 않았다.
- 새 모델을 학습하지 않았다.
- H001 artifact를 수정하지 않았다.
- 이 단계는 다음 combiner comparison protocol을 바꾸는 planning gate다.
- 결과는 hypothesis-stage plan이며 paper-level metric evidence가 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_ready
rows=134
validation_used=False
candidate_count=9
control_count=7
d_auprc_linear_vs_sg=0.1764
d_auprc_primary_vs_linear=-0.0143
next=revised_sampling_all_label_ready_raw_witness_v2_combiner_smoke
```

## Result

Status:

```text
full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_ready
```

The plan uses the following diagnosis from `127`:

- typed raw witness adds stable train-only signal over `semantic_plus_geometry`.
- raw witness controls reduce the gain.
- `family_shrinkage` is not the best combiner for grouped AUPRC/Brier.
- `linear_v2` is the strongest simple posterior so far.
- `support_contact` drives the positive signal.
- `relative_vertical` has calibration/Brier regression.
- endpoint-type ablation has nontrivial shortcut signal.

## Combiner Candidates

| ID | Role | Decision | Rationale |
| --- | --- | --- | --- |
| `C0_semantic_plus_geometry_legacy` | legacy reference | keep | pre-v2 semantic + `p_geom_valid` baseline. |
| `C1_raw_witness_only_v2` | geometry evidence reference | keep | tests typed raw witness without semantic score. |
| `C2_semantic_plus_raw_witness_v2` | direct replacement reference | keep | semantic score plus typed raw witness without extra interaction. |
| `C3_linear_v2` | current strongest simple reference | promote to next reference | best current grouped AUPRC/Brier among simple v2 posterior views. |
| `C4_calibrated_linear_v2` | calibration repair candidate | test next | keeps linear ranking signal while trying to reduce Brier/ECE. |
| `C5_constrained_monotonic_additive` | principled low-capacity candidate | test next | uses predeclared monotonic evidence directions. |
| `C6_family_gated_calibrated_mixture` | family heterogeneity repair | test next | separates support_contact and relative_vertical calibration without free endpoint shortcut. |
| `C7_limited_interaction_model` | upper-bound candidate | test after C4-C6 | only predeclared interactions, not generic high-capacity model. |
| `C8_endpoint_type_ablation_only` | shortcut probe | ablation only | endpoint type is useful but too shortcut-prone for main input. |

## Required Controls

| Control | Purpose |
| --- | --- |
| `K0_global_raw_witness_shuffle` | verifies gain follows actual pair geometry. |
| `K1_within_family_raw_witness_shuffle` | checks whether gain is only family distribution. |
| `K2_wrong_pair_raw_witness` | checks pair-specific witness dependence. |
| `K3_family_only_offset` | checks free family prior shortcut. |
| `K4_no_family_local_normalization` | checks whether local normalization helps calibration. |
| `K5_endpoint_type_only_or_ablation` | checks endpoint/object category shortcut risk. |
| `K6_family_split_support_only_vertical_only` | prevents support_contact gain from hiding vertical failure. |

## Success Gates

The next smoke uses `C3_linear_v2` as the reference, not `semantic_plus_geometry`.

Minimum gate for a new primary combiner:

```text
delta_auprc_vs_linear >= 0
delta_brier_vs_linear <= 0
delta_ece_vs_linear <= 0
new_errors_minus_fixes_vs_linear <= 0
```

Fallback gate:

```text
If a candidate ties linear within 0.01 AUPRC but improves Brier/ECE or threshold
transfer, it can be treated as a calibration/threshold repair, not as a ranking
improvement.
```

Family gates:

| Family | Gate |
| --- | --- |
| `support_contact` | dAUPRC vs `semantic_plus_geometry` >= +0.10 and dBrier <= 0. |
| `relative_vertical` | dAUPRC vs `semantic_plus_geometry` >= 0 and dBrier <= 0. |

If `relative_vertical` Brier stays positive, vertical must be separated or treated as an
unresolved calibration slice.

Shortcut gates:

- raw witness global/within-family/wrong-pair controls must remove most of the true gain.
- endpoint ablation cannot be the only source of gain for the main claim.
- family-only offset cannot explain the positive signal.

## Decision

Current decision:

```text
Proceed to train-only combiner smoke with C3_linear_v2 as the current reference.
```

The next smoke should not ask whether raw witness beats old `semantic_plus_geometry`; that is
already supported at hypothesis-stage. It should ask whether a repaired combiner can beat or
calibrate against `linear_v2` while controlling endpoint shortcut and relative_vertical
calibration regression.

Allowed claim:

```text
Typed raw witness is promising, but the posterior combiner is unsettled.
```

Blocked claims:

- `family_shrinkage` is the final combiner.
- H002 already has a paper-level posterior method result.
- support_contact-driven gain proves broad support/vertical generality.
- endpoint/object-type signal can be used as main evidence without shortcut controls.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/128_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/combiner_candidates.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/control_matrix.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/success_gates.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/next_smoke_plan.json
```

Artifact row counts:

```text
combiner_candidates.csv = 10 lines
control_matrix.csv = 8 lines
```

## Next TODO

```text
revised_sampling_all_label_ready_raw_witness_v2_combiner_smoke
```

Goal:

- implement train-only grouped combiner smoke for C0-C8.
- treat `C3_linear_v2` as the primary reference.
- report ranking, calibration, threshold transfer, family slices, and controls.
- keep endpoint type as ablation/control only.
- keep validation/test unavailable and paper-level posterior claim blocked.
