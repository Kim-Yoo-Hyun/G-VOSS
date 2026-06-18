# H002 Full-Train Independent Combiner Path Decision

## Purpose

이 문서는 full-train independent combiner upgrade 결과 이후 H002의 다음 경로를
결정한다.

핵심 질문:

```text
현재 posterior/combiner 성능 결과를 negative boundary로 멈출 것인가,
아니면 relation-family-specific factor를 먼저 수정한 뒤 다시 train-only smoke를
진행할 것인가?
```

## Boundary

- Split: Open3DSG train-only.
- Input: 75번 combiner upgrade smoke와 76번 error analysis.
- 새 모델은 학습하지 않는다.
- validation/test는 사용하지 않는다.
- hidden audit metadata는 사용하지 않는다.
- multi-view는 model input으로 사용하지 않는다.
- label은 `(codex_ver_full_train_independent)` bootstrap label이다.
- paper-level posterior performance claim은 불가하다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_path_decision.py
```

Observed:

```text
status=full_train_independent_combiner_path_decision_factor_revision_first
selected_path=B_factor_revision_first
validation_used=False
posterior_claim_allowed=False
next=full_train_independent_factor_revision_design
```

## Input Evidence

Combiner upgrade smoke의 핵심 결과:

```text
status = full_train_independent_combiner_upgrade_no_safe_gain
best_upgraded = C2_family_gated_residual
C2 delta AUPRC vs semantic_plus_geometry = +0.0070
C2 delta Brier vs semantic_plus_geometry = +0.0062
C3 delta AUROC vs semantic_plus_geometry = +0.0064
C3 delta AUPRC vs semantic_plus_geometry = -0.0052
C3 delta Brier vs semantic_plus_geometry = -0.0012
progress_views = none
```

Error analysis의 핵심 진단:

```text
C2_ranking_gain_is_not_calibrated_safe
C3_threshold_transfer_is_safer_than_C2
C3_calibration_gain_trades_off_ranking
C2_family_gate_overcorrects_support_contact
C3_is_promising_for_relative_vertical_not_global
```

해석:

- `C2_family_gated_residual`은 ranking signal을 만들지만 calibration과 threshold
  decision이 안전하지 않다.
- `C3_uncertainty_gated_geometry`는 threshold/Brier 관점에서는 더 안전하지만
  support_contact ranking을 망가뜨린다.
- 따라서 병목은 단순 combiner capacity 부족이 아니라 relation family별 evidence
  factor 설계 문제다.

## Decision

선택한 경로:

```text
B_factor_revision_first
```

의미:

```text
H002는 계속 진행한다. 다만 현재 posterior performance 결과는 negative/partial
boundary로 고정하고, generic high-capacity combiner를 바로 추가하지 않는다.
다음 단계는 relation-family-specific deployable factor revision이다.
```

## Why Not The Other Paths

### Option A: Negative Boundary Only

선택하지 않았다.

이유:

- 가장 보수적이지만, `C2`와 `C3`가 structured partial signal을 보였다.
- 특히 `C3`는 `relative_vertical`과 high-semantic/low-geometry slice에서 유망하다.
- 따라서 posterior path를 완전히 닫기보다는 factor 설계를 먼저 고치는 것이 낫다.

### Option C: Target Revision First

primary next step으로 선택하지 않았다.

이유:

- target risk는 여전히 실제 위험이다.
- 하지만 현재 관찰된 failure는 support_contact, relative_vertical, mismatch direction별
  factor behavior에서 더 직접적으로 나타난다.
- target confirmation은 paper claim 전 필수 gate로 유지하되, 바로 다음 설계 단계는
  factor revision이 더 원인에 가깝다.

### Option D: High-Capacity Combiner Now

현재는 거부한다.

이유:

- 158-row bootstrap target에서 overfit 위험이 크다.
- 성능이 좋아져도 “왜 이 method 형태가 필요한가”를 설명하기 어렵다.
- 먼저 factor가 failure mechanism을 직접 반영해야 한다.

## Factor Revision Plan

우선순위:

| Priority | Factor | Problem | Revision |
| ---: | --- | --- | --- |
| 1 | `support_contact_factor_split` | C2/C3가 support_contact를 과보정한다. | floor/support contact, object-object support, weak contact/no-contact evidence를 분리한다. |
| 2 | `relative_vertical_order_residual` | C3 signal이 global gate에 섞여 있다. | vertical ordering residual, clearance, overlap proxy, direction-consistent sign을 분리한다. |
| 3 | `coverage_uncertainty_factor` | uncertainty gate가 explicit coverage 없이 약한 proxy에 의존한다. | missingness/coverage factor를 deployable feature로 정리하고, multi-view는 audit evidence로 유지한다. |
| 4 | `family_shrinkage_gate` | family gate가 일부 slice에서는 유용하지만 다른 slice에서는 과보정한다. | family-specific residual scale을 shrinkage로 제한한다. |
| 5 | `target_confirmation_gate` | 현재 label은 Codex bootstrap label이다. | paper claim 전 human-confirmed 또는 더 강한 independent label을 요구한다. |

## Claim Boundary

Allowed:

```text
RGA는 semantic/geometric mismatch를 드러내며, 현재 posterior/combiner는
train-only controlled target에서 relation-family-specific failure mode를 보인다.
```

Blocked:

```text
factorized reliability posterior가 semantic_plus_geometry보다 relation reliability를
개선한다.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_path_decision_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_path_decision_codex_ver/decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_path_decision_codex_ver/decision_options.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_path_decision_codex_ver/factor_revision_plan.csv
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_path_decision.py
```

Observed:

```text
validation_used=False
posterior_claim_allowed=False
selected_path=B_factor_revision_first
```

## Next TODO

Completed next action:

```text
full_train_independent_factor_revision_design
```

Result:

```text
full_train_independent_factor_revision_design_ready
```

Implication:

- support_contact와 relative_vertical의 factor를 먼저 분리한다.
- coverage/uncertainty를 deployable factor로 정리한다.
- family gate는 free high-capacity model이 아니라 shrinkage/gating 형태로 제한한다.
- 이후 train-only smoke에서 다시 `semantic_only`, `geometry_only`,
  `semantic_plus_geometry`, revised factorized posterior를 비교한다.

Next action:

```text
full_train_independent_revised_factor_dataset
```
