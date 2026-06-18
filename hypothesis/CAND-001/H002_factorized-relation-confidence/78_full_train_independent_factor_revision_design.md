# H002 Full-Train Independent Factor Revision Design

## Purpose

이 문서는 77번 path decision 이후, 다음 smoke 전에 어떤 factor를 실제 deployable
feature block으로 재설계할지 고정한다.

핵심 질문:

```text
현재 posterior/combiner가 실패한 원인이 단순 결합기 capacity 부족이 아니라면,
어떤 relation-family-specific factor를 먼저 고쳐야 하는가?
```

## Boundary

- Split: Open3DSG train-only.
- Input: 77번 path decision, 76번 error analysis, full-train `match_rows.jsonl`.
- 새 모델은 학습하지 않는다.
- validation/test는 사용하지 않는다.
- hidden audit metadata는 model input으로 사용하지 않는다.
- multi-view는 아직 audit evidence로만 둔다.
- `geometry_status`의 satisfied/unsatisfied를 main score shortcut으로 쓰지 않는다.
- paper-level posterior performance claim은 여전히 불가하다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_factor_revision_design.py
```

Observed:

```text
status=full_train_independent_factor_revision_design_ready
factors=5
families=6
validation_used=False
posterior_claim_allowed=False
next=full_train_independent_revised_factor_dataset
```

## Why This Step Was Needed

이전 upgraded combiner 결과는 다음처럼 해석된다.

- `C2_family_gated_residual`은 ranking signal을 만들지만 calibration-safe하지 않다.
- `C2`는 특히 `support_contact`에서 new threshold mistakes를 만든다.
- `C3_uncertainty_gated_geometry`는 threshold/Brier에는 유리하지만 support_contact
  ranking을 손상시킨다.
- `C3`는 `relative_vertical`과 high-semantic/low-geometry slice에서는 유망하다.

따라서 바로 SOTA급 high-capacity combiner로 가기보다, `p_geom_valid` 하나에 접힌
geometry evidence를 relation family별 continuous witness factor로 다시 펼치는 것이
현재 failure mechanism에 더 가깝다.

## Full-Train Geometry Availability

`match_rows.jsonl` 전체를 train-only로 스트리밍 집계했다.

| Family | Rows | Raw Feature Rows | Raw Coverage | Satisfied | Unsatisfied | Uncertain | Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | 556,038 | 556,038 | 1.0000 | 178,968 | 15,472 | 361,598 | 0 |
| `relative_vertical` | 370,692 | 370,692 | 1.0000 | 124,604 | 124,604 | 121,484 | 0 |
| `proximity` | 185,346 | 185,346 | 1.0000 | 171,326 | 6,692 | 7,328 | 0 |
| `attachment_deferred` | 556,038 | 0 | 0.0000 | 0 | 0 | 0 | 556,038 |
| `relative_horizontal` | 741,384 | 0 | 0.0000 | 0 | 0 | 0 | 741,384 |
| `unsupported_first_pass` | 2,409,498 | 0 | 0.0000 | 0 | 0 | 0 | 2,409,498 |

현재 바로 사용할 수 있는 raw geometry fields:

```text
center_delta_z
distance_3d
distance_xy
normalized_center_delta_z
normalized_distance_3d
normalized_distance_xy
object_bottom_z
object_top_z
projected_iou_xy
projected_object_overlap_ratio
projected_subject_overlap_ratio
subject_bottom_z
subject_top_z
vertical_gap_subject_on_object
```

중요한 해석:

- `support_contact`, `relative_vertical`, `proximity`는 raw witness feature가 이미 있다.
- `attachment_deferred`, `relative_horizontal`, `unsupported_first_pass`는 현재 train RGA에서
  unsupported라 posterior factor input으로 확장하지 않는다.
- 따라서 다음 단계는 새 family를 늘리는 것이 아니라, 이미 raw feature가 있는 세 family
  안에서 factor를 재구성하는 것이다.

## Factor Contracts

### FR1 Support-Contact Witness Split

목표:

```text
support_contact를 하나의 p_geom_valid로 보지 않고, 접촉/지지 witness를 분해한다.
```

사용 가능한 deployable evidence:

- `vertical_gap_subject_on_object`
- `normalized_distance_xy`
- `projected_subject_overlap_ratio`
- `projected_object_overlap_ratio`
- subject/object labels
- predicate label/family

만들 factor:

- `contact_gap_abs`
- `penetration_proxy`
- `xy_support_overlap`
- `floor_like_support_flag`
- `object_object_support_flag`
- `weak_contact_flag`

성공 조건:

```text
support_contact slice가 new mistakes를 지배하지 않아야 하며,
Brier가 semantic_plus_geometry보다 나빠지면 안 된다.
```

### FR2 Relative-Vertical Order Residual

목표:

```text
higher/lower relation을 p_geom_valid 하나가 아니라 vertical sign/margin residual로 표현한다.
```

사용 가능한 deployable evidence:

- `center_delta_z`
- `normalized_center_delta_z`
- `subject_bottom_z`, `subject_top_z`
- `object_bottom_z`, `object_top_z`
- `vertical_gap_subject_on_object`
- `projected_iou_xy`

만들 factor:

- `predicate_expected_z_sign`
- `vertical_sign_agreement`
- `vertical_margin_abs`
- `vertical_clearance`
- `xy_overlap_context`

성공 조건:

```text
relative_vertical과 semantic_high_geometry_low에서 보인 C3의 이득이 유지되면서,
support_contact 성능을 망가뜨리지 않아야 한다.
```

### FR3 Coverage-Uncertainty Gate

목표:

```text
geometry contradiction과 evidence absence를 분리한다.
```

사용 가능한 deployable evidence:

- `geometry_available`
- `geometry_checkable`
- `raw_feature_present`
- `consistency_score`
- semantic score/rank
- semantic-geometry disagreement

만들 factor:

- `coverage_flag`
- `unsupported_family_flag`
- `raw_geometry_missing_flag`
- `near_boundary_uncertainty`
- `disagreement_uncertainty`

주의:

```text
multi-view는 아직 model input이 아니라 audit evidence로만 둔다.
```

### FR4 Family-Shrinkage Residual

목표:

```text
family gate를 쓰되, family별 자유도를 제한한다.
```

구성:

```text
logit P(R=1) = logit P_sg
             + global_residual(S, G_raw, C, U)
             + shrink(family) * family_residual_delta
```

금지:

- 현재 label 수에서 per-predicate free model은 쓰지 않는다.
- generic high-capacity combiner는 아직 쓰지 않는다.

### FR5 Target Confirmation Gate

목표:

```text
positive smoke가 나오더라도 Codex bootstrap label만으로 paper claim을 만들지 않는다.
```

역할:

- model input이 아니라 evidence gate다.
- posterior 성능 claim은 human-confirmed 또는 더 강한 independent label 전까지 blocked다.

## Forbidden Or Deferred Inputs

다음은 다음 smoke model input으로 쓰지 않는다.

- `label_match_status`
- `proposed_audit_role`
- `queue_kind`
- `rank_band_hidden`
- labeler confidence
- validation/test row
- multi-view feature
- `geometry_status` satisfied/unsatisfied를 main reliability shortcut으로 쓰는 방식

`geometry_status`는 analysis/coverage stratification에는 쓸 수 있지만, posterior가
배우는 주 신호는 continuous raw geometry evidence여야 한다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/design.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/factor_contracts.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/feature_blocks.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/feature_spec.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/smoke_plan.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/availability_by_family.csv
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_factor_revision_design.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_factor_revision_design.py
```

Observed:

```text
validation_used=False
posterior_claim_allowed=False
families=6
factors=5
```

## Next TODO

Completed next action:

```text
full_train_independent_revised_factor_dataset
```

Result:

```text
full_train_independent_revised_factor_dataset_ready
```

Implication:

- 158-row controlled slice에 raw geometry witness를 join한다.
- FR1-FR4 factor block을 `baseline_inputs`에 materialize한다.
- hidden audit metadata와 target-construction metadata가 feature에 들어오지 않는지 검사한다.
- 이후 revised factor smoke를 돌릴 수 있는 row artifact를 만든다.

Next action:

```text
full_train_independent_revised_factor_smoke
```
