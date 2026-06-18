# H002 Posterior Path Decision

Last updated: 2026-06-14

## Purpose

`50_label_policy_audit.md` 이후 H002는 중요한 decision point에 도달했다.

현재까지 확인된 것은 다음이다.

```text
semantic score != geometry validity != relation reliability
```

이 problem framing은 여전히 유효하다. 그러나 현재 bootstrap target에서는
`factorized reliability posterior`가 `semantic_plus_geometry`를 안정적으로 이긴다는
증거가 없다.

이번 문서의 목적:

- posterior를 H002의 method candidate로 계속 유지할지 결정한다.
- posterior 결합 방식 변경으로 개선 가능성이 있는지 판단한다.
- posterior claim을 살리기 위한 최소 label/protocol 조건을 고정한다.
- near-term H002 framing을 정한다.

## Current Evidence

현재 핵심 결과:

| Gate | Status | Interpretation |
| --- | --- | --- |
| `41_grouped_control_smoke.md` | weak conditional support | codex target에서 일부 gain, but rank proxy stronger |
| `42_rank_proxy_debias.md` | rank_proxy_not_debiased | non-rank factorized evidence가 rank proxy를 못 이김 |
| `45_target_independence_audit.md` | target_independence_not_established | codex target이 construction signal과 독립적이지 않음 |
| `49_independent_combiner_smoke.md` | independent_combiner_no_strong_signal | factorized/residual/gated가 `semantic_plus_geometry`를 못 이김 |
| `50_label_policy_audit.md` | label_policy_entangled | bootstrap label이 family/predicate policy로 많이 설명됨 |

가장 최근 결과:

```text
factorized - semantic_plus_geometry:
  grouped AUPRC = -0.0013
  grouped Brier = +0.0016

residual - semantic_plus_geometry:
  grouped AUPRC = -0.1010

gated - semantic_plus_geometry:
  grouped AUPRC = -0.0969

predicate majority accuracy = 0.7067
family majority accuracy = 0.7067
```

따라서 현재 evidence가 직접 반박하는 것은 다음이다.

```text
The current global linear/logistic factorized posterior, trained on current
bootstrap labels, is a strong method contribution.
```

반대로, 아직 반박하지 않은 것은 다음이다.

```text
A better-controlled posterior formulation may help once labels are independent,
balanced, and human-confirmed.
```

## Answer: Can A Different Posterior Combination Improve?

짧게 답하면:

```text
Yes, but the improvement path is conditional.
```

결합 방식을 바꾸면 개선 여지는 있다. 현재 실패는 모든 posterior formulation의 실패가
아니라, 다음 조합의 실패에 가깝다.

```text
current bootstrap labels
+ family/predicate-entangled label policy
+ small N
+ mostly global linear logistic combination
+ semantic_plus_geometry as a strong baseline
```

즉, posterior 자체의 가능성은 남아 있다. 그러나 지금 당장 결합 방식만 바꿔서 성능이
오르더라도 reviewer 관점에서는 다음처럼 보일 위험이 크다.

```text
label-policy shortcut + model-capacity increase
```

따라서 결합 방식 개선은 다음 순서에서만 의미가 있다.

1. predicate/family-controlled label을 먼저 만든다.
2. target이 semantic/rank/family/predicate shortcut과 충분히 독립적인지 확인한다.
3. 그 다음 더 나은 posterior combiner를 비교한다.

## Current Combiner Limitation

현재 H002에서 주로 사용한 combiner는 다음 계열이다.

```text
logistic P(R=1 | feature block)
```

특징:

- feature block을 한꺼번에 넣는 global discriminative model이다.
- family-specific geometry semantics를 충분히 분리하지 않는다.
- coverage/uncertainty를 structural gate로 강하게 쓰지 않는다.
- label policy가 family/predicate와 얽히면 쉽게 그 shortcut을 학습한다.
- small-N에서 feature 수가 늘면 calibration보다 overfitting 위험이 커진다.

현재 residual/gated view도 엄밀한 구조모델이라기보다 feature engineering된 logistic
view에 가깝다.

## Better Posterior Candidates

### 1. Semantic-Prior Residual Posterior

Form:

```text
logit P(R=1) = logit P_sem(R=1 | S_e) + Delta(G_e, C_e, U_e)
```

Purpose:

```text
semantic evidence로 설명되는 부분을 먼저 빼고, geometry/coverage/uncertainty가
남은 reliability residual을 설명하는지 본다.
```

Why promising:

- H002의 핵심 질문인 "semantic score와 geometry validity가 분리되는가"에 가장 직접적이다.
- semantic-only를 더 강한 baseline으로 두기 때문에 reviewer defense가 쉽다.

Risk:

- 현재 bootstrap label에서는 residual이 label policy와 얽혀 있어 signal이 약했다.

Status:

```text
defer until predicate/family-controlled human labels exist
```

### 2. Family-Specific Hierarchical Posterior

Form:

```text
P(R=1 | S,G,C,U,family)
  = family-specific calibration + shared global prior
```

Example:

```text
logit P_f(R=1) =
  alpha_f + beta_S,f S + beta_G,f G + beta_U,f U
```

with partial pooling across families.

Why promising:

- `support_contact`, `proximity`, `relative_vertical`은 geometry evidence의 의미가 다르다.
- 하나의 global combiner가 모든 family를 같은 방식으로 결합하는 것은 약하다.

Risk:

- 현재 label에서 family가 target을 직접 설명하므로, hierarchical model은 오히려 shortcut을
  강화할 수 있다.

Required control:

```text
within-family positive/negative balance
within-predicate or same-predicate pairs
family held-out or family-balanced evaluation
```

### 3. Coverage-Gated Geometry Model

Form:

```text
P(R=1) = sigmoid(
  f_S(S_e)
  + gate(C_e, U_e) * f_G(G_e)
  + f_U(U_e)
)
```

Why promising:

- geometry evidence는 항상 같은 신뢰도를 갖지 않는다.
- `unsupported`, `uncertain`, low-visibility cases에서는 geometry score를 강하게 쓰면 안 된다.

Risk:

- 현재 pilot의 target은 대부분 geometry-checkable and satisfied 쪽이라 gate가 차별화할
  여지가 작다.

Best use:

```text
coverage/uncertainty-rich target
```

### 4. Pairwise Rank-Matched Reliability Ranking

Form:

```text
score(e_positive) > score(e_negative)
```

within:

```text
same family
same predicate if possible
same rank band
similar semantic score
same geometry_status
```

Why promising:

- small-N binary calibration보다 더 안정적일 수 있다.
- H002의 reviewer question인 "semantic score를 넘어서는가?"를 직접 검증한다.

Risk:

- current pairs가 너무 적다.
- pair construction이 다시 shortcut이 될 수 있다.

### 5. Debiased / Orthogonalized Factor Posterior

Form:

```text
G_res = G - E[G | predicate, family, rank_band, semantic_score]
U_res = U - E[U | predicate, family, rank_band, semantic_score]
P(R=1 | S, G_res, U_res, C)
```

Why promising:

- label-policy/family/rank shortcut을 먼저 제거한다.
- "geometry evidence가 independent information인가?"를 가장 엄격하게 본다.

Risk:

- data가 적으면 residualization 자체가 불안정하다.

### 6. Selective / Abstention-Aware Reliability

Form:

```text
P(reliable), P(unreliable), P(abstain)
```

or:

```text
P(R=1 | not abstain), P(abstain | C,U)
```

Why promising:

- H002에는 `uncertain`, `unsupported`, `abstain_uncertain`,
  `visibility_or_geometry_artifact`가 자연스럽게 존재한다.
- binary reliable/unreliable로 강제하면 coverage uncertainty가 손실된다.

Risk:

- multiclass label이 더 많이 필요하다.

### 7. Constrained Monotonic Calibrator

Form:

```text
P(R=1) = calibrated monotonic function of semantic prior, geometry validity,
coverage, and uncertainty
```

Constraints:

- reliability should not decrease as semantic prior improves, all else equal.
- reliability should not decrease as geometry validity improves, all else equal.
- reliability should decrease or abstain as uncertainty increases.

Why promising:

- relation reliability는 black-box MLP보다 calibrated/monotonic model이 방어하기 쉽다.
- small data setting에서 overfitting 위험이 작다.

Risk:

- 현재 target이 biased이면 monotonic constraint만으로는 해결되지 않는다.

## Decision

Current decision:

```text
posterior_path_deferred
```

Meaning:

```text
Keep posterior as a conditional method candidate, but do not use it as the
near-term H002 main contribution.
```

Near-term H002 main direction:

```text
RGA benchmark / diagnostic framework / failure taxonomy
```

Secondary or future method direction:

```text
policy-controlled reliability posterior
```

This is not a retreat from H002. It is a narrowing of the claim to the evidence
that is currently defensible.

## How feasibility_check.md Is Used

`feasibility_check.md`에서 정리한 방법은 폐기하지 않는다. 다만 현재 결과가
보여준 blocker 때문에 적용 위치를 분리한다.

Use now:

- RGA audit/confirmation evidence로 multi-view, contact sheet, mesh/point-cloud
  context를 사용한다.
- `true_underconfidence`, `dense_relation_noise`, `annotation_sparsity`,
  `ontology_mismatch`, `uncertain_needs_visual_or_mesh`를 구분하는 label protocol에
  사용한다.
- relation family 확장 우선순위는 feasibility check의 순서를 따른다:
  `support_contact -> attachment_deferred -> relative_vertical`.
- posterior를 revive할 때는 feasibility check의 combiner 후보를 사용한다:
  residual, gated, pairwise rank-matched, debiased/orthogonalized,
  product-of-experts, family-specific mixture/hierarchical, monotonic calibrated
  posterior.

Do not use now:

- `V_mv_e`를 deployable model input으로 바로 넣지 않는다.
- point cloud + multi-view를 더 강한 relation predictor로 framing하지 않는다.
- multi-view posterior 성능 향상을 H002의 현재 method claim으로 쓰지 않는다.

Reason:

```text
current blocker = target independence / label policy bias
not = lack of visual feature capacity
```

Therefore:

```text
feasibility_check.md is the execution map for RGA audit and future posterior
revival, not a license to add V_mv_e before the independent-target gate passes.
```

## Why Not Just Try A Stronger Combiner Now?

Because current labels are not strong enough to distinguish:

```text
better reliability model
```

from:

```text
better exploitation of predicate/family bootstrap rules
```

Evidence:

- `predicate_label` majority rule accuracy is `0.7067`.
- `support_contact` is `23/25` positive.
- `standing on` is `15/15` positive.
- `predicate_only` reached grouped AUPRC `0.8650` in the original target.
- policy-balanced variants did not recover meaningful factorized/gated AUPRC.

So model search now would mostly test:

```text
Can a model exploit biased bootstrap labels?
```

not:

```text
Does factorized relation reliability explain real edge trustworthiness?
```

## Minimum Evidence To Revive Posterior Claim

Posterior can return as a method candidate only if these gates pass.

### Label Gate

Minimum:

```text
human-confirmed or independently reviewed labels
binary usable rows >= 150
positive rows >= 50
negative rows >= 50
at least 2 relation families with both classes
per-family minority class >= 15
```

Preferred:

```text
same-predicate or same-family matched pairs
balanced predicate/family distribution
2 reviewers or adjudicated labels
explicit abstain labels preserved
```

### Shortcut Gate

Must show:

```text
predicate_only < semantic_plus_geometry
family_only < semantic_plus_geometry
rank_only < semantic_plus_geometry
negative_rank_only < factorized/residual/gated
```

or at least:

```text
posterior gain remains after controlling predicate/family/rank.
```

### Performance Gate

Under train-only hypothesis-stage grouped CV:

```text
factorized/residual/gated - semantic_plus_geometry:
  AUPRC >= +0.03
  or Brier <= -0.02
  with AUROC drop <= 0.02
```

Under final paper experiment:

```text
same criterion must hold on locked validation/test after protocol freeze.
```

### Calibration Gate

Because H002 is a reliability problem:

```text
Brier and ECE must improve or at least not degrade.
```

Pure AUPRC gain is not enough if calibration worsens.

## Recommended Posterior Revival Order

If posterior is revived, do it in this order:

1. `pairwise_rank_matched_posterior`
   - same family/predicate, similar semantic score, similar rank band.
   - evaluates whether non-semantic evidence ranks trusted edges higher.

2. `semantic_prior_residual_posterior`
   - learns residual over semantic prior.
   - strongest conceptual alignment with H002.

3. `coverage_gated_geometry_posterior`
   - uses coverage/uncertainty as gate.
   - only meaningful after uncertainty-rich labels.

4. `family_specific_hierarchical_posterior`
   - partial pooling by relation family.
   - only after family-balanced labels.

5. `selective_abstention_posterior`
   - models reliable/unreliable/abstain.
   - useful if multi-view audit produces more uncertainty labels.

## Paper Framing Implication

Near-term paper claim should not be:

```text
We propose a superior posterior rescoring model.
```

Near-term paper claim should be:

```text
Existing 3D scene graph relation confidence conflates semantic plausibility,
geometric satisfiability, coverage, and annotation policy. RGA exposes and
quantifies these mismatches, including both high-semantic/low-geometry and
low-semantic/high-geometry cases.
```

Potential method contribution:

```text
RGA-based reliability auditing and failure taxonomy.
```

Deferred method contribution:

```text
policy-controlled calibrated reliability posterior.
```

## Direct Answer To The User Question

Question:

```text
posterior 결합 방식을 변화하면 개선의 여지도 존재하지 않아?
```

Answer:

```text
존재한다. 특히 global logistic combiner보다 residual, hierarchical, gated,
pairwise, selective-abstention 방식이 원리적으로 더 맞다.
```

But:

```text
현재 evidence에서는 결합 방식보다 label-policy bias가 더 큰 blocker다.
```

Therefore:

```text
결합 방식 개선은 다음 실험 후보로 남기되, 지금 H002의 main claim으로 올리면
방어가 어렵다. 먼저 predicate/family-controlled human label이 필요하다.
```

## Next TODO

Next document:

```text
52_rga_main_framing.md
```

Goal:

- H002 near-term claim을 RGA benchmark/failure taxonomy 중심으로 재정리한다.
- posterior를 optional/future method candidate로 낮춘다.
- `feasibility_check.md`의 즉시 활용 항목을 RGA audit protocol에 연결한다:
  multi-view는 label/audit evidence, family priority는
  `support_contact -> attachment_deferred -> relative_vertical`, posterior combiner
  후보는 revival path로 유지한다.
- paper-level contribution 후보를 `metric/framework`, `failure taxonomy`,
  `controlled audit protocol` 중심으로 다시 정리한다.
- validation/test는 계속 사용하지 않는다.
