# H002 Full-Train Independent Combiner Upgrade Design

## Purpose

이 문서는 controlled error analysis 이후 H002의 다음 결합 방식을 정의한다.

핵심 질문은 다음이다.

```text
결합 방식을 더 강하게 바꾸면 성능이 좋아질 수 있는가?
그렇다면 어떤 SOTA-style combiner를 먼저 검증해야 하는가?
```

결론부터 말하면, 결합 방식 개선은 필요하다. 다만 현재 158-row controlled bootstrap
target에서는 고용량 generic classifier를 바로 넣는 것보다, failure 분석에 맞춘
calibrated residual / family-gated / uncertainty-gated combiner를 먼저 검증하는 것이
더 방어 가능하다.

## Boundary

- Split: Open3DSG train-only.
- 새 모델 학습은 이 단계에서 하지 않는다.
- validation/test는 사용하지 않는다.
- multi-view는 아직 model input이 아니라 audit evidence로만 둔다.
- hidden audit metadata는 post-hoc diagnostic 전용이다.
- 아래 combiner 후보는 `(codex_ver_full_train_independent)` bootstrap target용
  hypothesis-stage 설계다.
- paper-level performance claim은 아직 불가하다.

## Input Evidence

직전 controlled error analysis:

```text
status = full_train_independent_controlled_error_analysis_ready_for_combiner_design
rows = 158
factorized_wrong_sg_correct = 10
factorized_correct_sg_wrong = 1
mean_brier_delta_factorized_minus_sg = +0.0021
```

이 결과는 현재 `factorized_reliability_posterior`가 단순히 약간 낮은 정도가 아니라,
`semantic_plus_geometry`가 맞춘 decision을 더 많이 망가뜨린다는 것을 의미한다.

## Why Not Directly Use A Generic SOTA Combiner?

고용량 SOTA급 tabular combiner를 바로 넣는 방향은 성능이 좋아질 가능성은 있다.
하지만 지금 단계에서는 위험하다.

1. 현재 target은 158-row bootstrap target이다.
2. family가 3개뿐이고 slice별 row 수가 작다.
3. hidden metadata leakage를 이미 한 번 경험했다.
4. 성능 하락 원인이 random nonlinearity가 아니라 family/direction별 구조적 차이로
   보인다.
5. 고용량 모델이 좋아져도 reviewer 관점에서는 `feature engineering + powerful classifier`
   로 보일 수 있다.

따라서 지금 필요한 것은 무작정 강한 모델이 아니라, 다음 design necessity를 반영한
combiner다.

```text
semantic_plus_geometry를 대체하지 말고 보정한다.
relation family별 geometry 의미 차이를 반영한다.
HL/LH/close-agreement direction을 같은 방식으로 처리하지 않는다.
calibration과 threshold error transfer를 AUPRC만큼 중요하게 본다.
```

## Design Requirements

| ID | Evidence | Design Consequence |
| --- | --- | --- |
| `R1_do_not_replace_strong_base` | `semantic_plus_geometry`가 current factorized보다 grouped AUPRC/Brier에서 강함 | `semantic_plus_geometry` 위에 residual correction을 얹는다 |
| `R2_family_conditioning` | family별 F-SG delta가 다름 | global geometry weight 하나로 처리하지 않는다 |
| `R3_direction_conditioning` | `semantic_high_geometry_low`는 손해, `semantic_geometry_close`는 이득 | HL/LH/close regime별 interaction을 둔다 |
| `R4_calibration_guard` | factorized가 SG-correct row 10개를 망가뜨리고 1개만 고침 | Brier와 threshold transfer를 주요 기준으로 둔다 |
| `R5_no_hidden_metadata` | original target에서 hidden metadata correlation 발견 | queue/status/role은 input 금지 |

## Candidate Combiners

### C1: Residual Logit Calibrator

가장 먼저 검증할 후보.

```text
logit P(R=1) = logit P_sg + delta(S, G, D, U)
```

여기서:

- `P_sg`: `semantic_plus_geometry` base posterior.
- `S`: semantic score/rank.
- `G`: `p_geom_valid`, consistency.
- `D`: absolute disagreement, underconfidence, overconfidence.
- `U`: deployable uncertainty proxy.

장점:

- 현재 가장 강한 simple baseline을 버리지 않는다.
- combiner가 배워야 할 일을 “전체 prediction”이 아니라 “보정량”으로 줄인다.
- 작은 N에서 가장 안정적이다.

위험:

- residual도 158 rows에서는 overfit 가능하다.

대응:

- strong L2.
- scan-grouped folds.
- `semantic_plus_geometry` 대비 delta 중심 보고.

### C2: Family-Gated Residual

두 번째 우선 후보.

```text
logit P(R=1) = logit P_sg + delta_global(S,G,D,U)
             + shrink(family) * delta_family(S,G,D,U)
```

핵심은 relation family를 deployable gate로 쓰되, family별 모델을 완전히 독립시키지 않는
것이다.

장점:

- `support_contact`, `relative_vertical`, `proximity`가 다른 geometry behavior를 보인다는
  error analysis 결과와 직접 연결된다.
- H002의 “relation-level reliability” 주장과 잘 맞는다.

위험:

- family rows가 작아서 family-specific weight가 slice artifact를 외울 수 있다.

대응:

- family-specific term은 shrinkage를 걸어 global residual로 수축한다.
- per-predicate free model은 현재 단계에서 금지한다.

### C3: Uncertainty-Gated Geometry

세 번째 후보.

```text
P = gate(e) * P_geometry_adjusted + (1 - gate(e)) * P_sg
```

여기서 `gate(e)`는 deployable uncertainty proxy로 계산한다.

가능한 gate input:

- semantic confidence entropy/proximity-to-0.5.
- semantic rank.
- `p_geom_valid`.
- consistency.
- absolute disagreement.
- feature missing flag.

장점:

- geometry-only가 global하게 약하지만 특정 regime에서는 도움이 된다는 관찰을 반영한다.
- HL에서 geometry penalty를 항상 강하게 주는 문제를 줄일 수 있다.

위험:

- 현재 feature export에는 명시적 coverage factor가 충분하지 않다.

대응:

- 현재 smoke에서는 consistency를 proxy로 사용한다.
- coverage가 없다는 사실을 artifact에 명시한다.

### Deferred: Monotonic GBDT Calibrator

SOTA-style nonlinear tabular combiner 후보이지만 지금은 보류한다.

이유:

- 158-row target에서는 고용량 nonlinear model이 쉽게 overfit된다.
- 좋아져도 method necessity보다 classifier capacity로 해석될 수 있다.
- human-confirmed label 또는 더 큰 independent target이 생긴 뒤 비교하는 것이 맞다.

### Deferred: Graph Factor Rescoring

H002의 장기 방향과는 맞지만, 현재 edge-local reliability가 아직 충분히 검증되지 않았다.
따라서 edge-local combiner가 simple baselines를 이긴 뒤 graph-level factor로 확장한다.

## Next Smoke Comparison

다음 smoke에서 비교할 baseline:

```text
semantic_only
geometry_only
semantic_plus_geometry
current_factorized_reliability_posterior
residual_reliability_model
```

다음 smoke에서 추가할 upgraded views:

```text
C1_residual_logit_calibrator
C2_family_gated_residual
C3_uncertainty_gated_geometry
```

필수 control:

- scan-grouped folds.
- same controlled slice.
- same train-only provenance.
- no hidden audit metadata as input.
- no validation/test tuning.
- `semantic_plus_geometry`를 main baseline으로 둔다.
- family/direction slice를 다시 보고한다.
- threshold error transfer를 보고한다.

## Progression Threshold

다음 smoke에서 hypothesis-stage progress로 볼 수 있는 최소 조건:

```text
Delta AUPRC vs semantic_plus_geometry >= +0.01
or
Delta Brier vs semantic_plus_geometry <= -0.005
```

추가 조건:

```text
new mistakes should not exceed fixed mistakes
```

즉, AUPRC가 약간 좋아져도 `semantic_plus_geometry`가 맞춘 row를 대량으로 망가뜨리면
좋은 combiner로 보지 않는다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_design_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_design_codex_ver/design.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_design_codex_ver/candidate_matrix.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_design_codex_ver/design_requirements.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_design_codex_ver/smoke_plan.json
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_design.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_design.py
```

Observed:

```text
status=full_train_independent_combiner_upgrade_design_ready_for_smoke
candidates=5
validation_used=False
trains_new_model=False
next=full_train_independent_combiner_upgrade_smoke
```

## Decision

다음 단계에서는 generic high-capacity combiner가 아니라 다음 3개를 먼저 smoke한다.

1. `C1_residual_logit_calibrator`
2. `C2_family_gated_residual`
3. `C3_uncertainty_gated_geometry`

이 순서는 현재 failure analysis에 의해 정당화된다.

## Next TODO

Completed next action:

```text
full_train_independent_combiner_upgrade_smoke
```

Result:

```text
full_train_independent_combiner_upgrade_no_safe_gain
```

The upgraded smoke tested `C1_residual_logit_calibrator`,
`C2_family_gated_residual`, and `C3_uncertainty_gated_geometry`. None satisfied
the pre-defined safe progression threshold against `semantic_plus_geometry`.

The next action is:

```text
full_train_independent_combiner_upgrade_error_analysis
```
