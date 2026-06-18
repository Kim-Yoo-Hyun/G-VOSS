# H002 RGA Main Framing

Last updated: 2026-06-14

## Purpose

`51_posterior_path_decision.md` 이후 H002의 near-term 방향을 다시 고정한다.

사용자 결정:

```text
pilot train에서 posterior signal이 약하더라도, 전체 train으로 확장해서
train-only hypothesis gate를 먼저 검증한다.
```

이 문서의 목적:

- H002의 main framing을 RGA benchmark / diagnostic framework / failure taxonomy로
  정리한다.
- posterior를 폐기하지 않고 full-train evidence gate 이후 revive할 method candidate로
  둔다.
- validation/test를 열지 않는 이유와 full-train 확장 이유를 명확히 한다.
- `feasibility_check.md`의 방법을 RGA audit과 posterior revival path에 연결한다.

## Core Position

H002의 핵심 문제는 다음 분리에서 출발한다.

```text
semantic score != geometry validity != relation reliability
```

RGA는 이 분리를 relation edge 단위로 측정하는 framework다.

```text
RGA(e) = {
  semantic_axis(e),
  geometry_axis(e),
  label_axis(e),
  coverage_axis(e),
  uncertainty_axis(e),
  disagreement_score(e)
}
```

Near-term H002 claim:

```text
Existing 3D scene graph relation confidence conflates semantic plausibility,
geometric satisfiability, coverage, uncertainty, and annotation policy. RGA
separates these axes and exposes bidirectional mismatch states.
```

Bidirectional mismatch:

| Bucket | Meaning |
| --- | --- |
| high semantic + low geometry | semantic overconfidence / unsafe relation |
| low semantic + high geometry | semantic underconfidence / missed or under-ranked relation candidate |
| high semantic + uncertain geometry | confident semantic relation with insufficient physical evidence |
| low semantic + uncertain geometry | low-ranked relation with unresolved evidence |

## Why Full Train Expansion Is Still Necessary

현재 pilot 결과는 posterior를 최종 반박하지 않는다.

현재 결과가 말하는 것:

```text
On the current Open3DSG train pilot with codex/bootstrap labels and 75 binary
targets, factorized/residual/gated posterior does not reliably beat the
semantic_plus_geometry baseline.
```

현재 결과가 말하지 않는 것:

```text
Factorized relation reliability cannot work on the full train distribution.
```

Full train 확장이 필요한 이유:

- pilot `N=75` binary target은 너무 작다.
- `support_contact`가 positive-heavy라 family/predicate shortcut이 강하다.
- `proximity`, `relative_vertical`, `support_contact` 사이의 label policy가 충분히
  균형 잡혀 있지 않다.
- full train에서는 relation family별 positive/negative 후보를 더 많이 mine할 수 있다.
- train-only grouped CV로 validation leakage 없이 posterior signal이 scale에서
  살아나는지 볼 수 있다.

따라서 H002의 다음 과학적 질문은 다음이다.

```text
After scaling to the full train split and controlling family/predicate/rank
shortcuts, does non-semantic evidence explain relation reliability beyond
semantic score and geometry-only validity?
```

## Why Validation Is Not Used Yet

Validation에서 잘 될 가능성은 원리적으로 있다. 그러나 지금 validation을 열면 다음
문제가 생긴다.

```text
target definition, family selection, posterior combiner, and audit policy are
still being designed.
```

따라서 validation을 지금 보면 validation은 held-out evaluation이 아니라 development
feedback이 된다. H002는 다음 순서를 지킨다.

1. full train에서 source/geometry/RGA row를 확장한다.
2. train-only controlled label target을 만든다.
3. train-only grouped CV와 shortcut controls를 통과한다.
4. feature schema, target definition, metrics, baselines, combiner를 freeze한다.
5. 그 뒤에만 validation/test를 확인한다.

Important rule:

```text
No validation/test rows are used for H002 hypothesis-stage target design,
posterior selection, threshold selection, or family selection.
```

## RGA Contribution Candidate

H002의 near-term contribution은 posterior 성능 claim이 아니라 RGA framework다.

Contribution candidate:

```text
Relation-Geometric Agreement (RGA): a relation-level diagnostic framework that
separates semantic plausibility, geometric satisfiability, coverage,
uncertainty, and annotation/audit evidence for 3D scene graph relations.
```

RGA가 기존 metric과 다른 점:

- relation recall/mAP는 label match를 보지만 geometry satisfiability를 분리하지 않는다.
- geometry-only verifier는 physical status를 보지만 semantic underconfidence,
  annotation sparsity, ontology mismatch를 분리하지 않는다.
- RGA는 `high-semantic/low-geometry`와 `low-semantic/high-geometry`를 모두 측정한다.
- RGA는 missing/unsupported/uncertain을 invalid relation으로 뭉개지 않는다.

Main RGA outputs:

| Output | Purpose |
| --- | --- |
| `RGA-HL@K` | high-ranked semantic relation의 geometry contradiction rate |
| `RGA-LH-tail@K` | low-ranked but geometry-satisfied relation candidate rate |
| `coverage_rate` | verifier가 실제로 평가 가능한 relation share |
| `uncertainty_rate` | physical evidence가 부족하거나 모호한 share |
| `family_bucket_table` | relation family별 mismatch 구조 |
| `audit_taxonomy` | underconfidence, dense noise, annotation sparsity, ontology mismatch 분리 |

## Posterior Position

Posterior는 폐기하지 않는다. 다만 현재 main claim이 아니다.

Current posterior:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

Future multi-view extension:

```text
P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)
```

현재 H002에서 posterior의 위치:

```text
RGA rows -> controlled audit labels -> factor blocks -> train-only posterior
smoke -> shortcut controls -> protocol freeze -> validation/test
```

Posterior revive condition:

```text
full-train controlled labels and proxy controls must show that non-semantic
evidence adds reliable signal beyond semantic_plus_geometry.
```

## Full Train Expansion Protocol

### Step 1. Full Train Source Scope

Full train scope를 먼저 고정한다.

Required:

- train split source list.
- scan/subgraph/object-pair identity.
- prediction-row identity.
- source semantic score/rank.
- relation predicate and family.
- geometry verifier joinability.
- no validation/test rows.

Output should be a source contract, not a metric result.

### Step 2. Full Train RGA Rows

Create full train RGA rows with the same axes as the pilot.

Required row fields:

```text
source_id
scan_id
subgraph_id
subject_id
object_id
predicate_label
predicate_family
semantic_rank_in_subgraph
semantic_score_raw
semantic_score_norm
geometry_status
p_geom_valid
coverage_state
uncertainty_state
label_match_status
provenance
```

Primary family set:

```text
support_contact
proximity
relative_vertical
```

No full-train posterior training starts until this row contract is complete.

### Step 3. Full Train RGA Distribution

Measure mismatch distributions before training any posterior.

Required tables:

- bucket counts by `predicate_family`.
- `RGA-HL@K` for K = 50 and 100.
- `RGA-LH-tail@K` for K = 50 and 100.
- coverage/uncertainty/missing/unsupported rates.
- exact-label / family-label / no-pair label states.
- scan-grouped distribution to avoid one scan dominating the conclusion.

Purpose:

```text
Decide whether H002 has enough full-train relation-level mismatch mass to
support a controlled audit and posterior revival.
```

### Step 4. Controlled Label Target Mining

Full train should be used to mine better label targets, not to fit a larger model
first.

Minimum mining goal:

```text
binary usable rows >= 150
positive rows >= 50
negative rows >= 50
at least 2 families with both classes
per-family minority class >= 15
```

Preferred target design:

- same-family balanced.
- same-predicate pairs where possible.
- same-rank-band or close semantic score.
- same-geometry-status comparisons when testing informativeness.
- abstain/uncertain preserved rather than forced into positive/negative.

Forbidden shortcut:

```text
Do not define target labels directly from semantic rank, p_geom_valid threshold,
or predicate-family majority policy.
```

### Step 5. Audit With Feasibility-Check Evidence

`feasibility_check.md` is used immediately as audit support.

Use now:

- contact sheets.
- mesh or point-cloud context.
- multi-view visibility/crop evidence if available.
- object-pair co-visibility.
- occlusion and view coverage.

Audit labels to separate:

```text
true_underconfidence
dense_relation_noise
annotation_sparsity
ontology_mismatch
uncertain_needs_visual_or_mesh
invalid_relation
valid_but_trivial_dense
```

Important:

```text
V_mv_e is audit evidence at this stage, not deployable model input.
```

### Step 6. Train-Only Posterior Smoke

After controlled labels are ready, run train-only grouped CV.

Main baselines:

| Baseline | Input |
| --- | --- |
| `semantic_only` | `S_e` |
| `geometry_only` | `G_e` or `p_geom_valid` |
| `semantic_plus_geometry` | `S_e + G_e` |
| `factorized_reliability_posterior` | `S_e + G_e + C_e + U_e` |

Required proxy controls:

| Control | Purpose |
| --- | --- |
| `rank_only` | tests semantic rank shortcut |
| `negative_rank_only` | tests rank-direction inversion artifact |
| `predicate_only` | tests predicate label shortcut |
| `family_only` | tests relation family shortcut |
| `geometry_status_only` | tests discrete status shortcut |

Posterior candidates, in order:

1. `semantic_prior_residual_posterior`
2. `coverage_gated_geometry_posterior`
3. `pairwise_rank_matched_posterior`
4. `debiased_orthogonalized_factor_posterior`
5. `product_of_experts_calibrated_posterior`
6. `family_specific_hierarchical_posterior`
7. `monotonic_calibrated_posterior`

### Step 7. Full Train Gate

Posterior can be revived only if:

```text
factorized/residual/gated - semantic_plus_geometry:
  AUPRC >= +0.03
  or Brier <= -0.02
  with AUROC drop <= 0.02
```

and:

```text
predicate_only, family_only, rank_only, geometry_status_only do not explain the
target as well as the proposed posterior.
```

Calibration requirement:

```text
Brier and ECE must improve or at least not degrade materially.
```

If the gate fails:

```text
H002 remains an RGA benchmark / failure taxonomy / audit protocol paper idea.
Posterior remains future work.
```

If the gate passes:

```text
freeze target, feature schema, combiner, baselines, controls, and metrics before
opening validation/test.
```

## Relation Family Priority

Full train starts with the current H002 families:

```text
support_contact
proximity
relative_vertical
```

Expansion priority from `feasibility_check.md`:

```text
1. support_contact
2. attachment_deferred
3. relative_vertical
```

Interpretation:

- `support_contact`: best first family for visual-geometric audit.
- `attachment_deferred`: strongest novelty extension, but needs dedicated schema.
- `relative_vertical`: useful control family because 3D geometry already explains
  much of the relation.
- `proximity`: useful for dense/noisy relation debugging, but not the best final
  multi-view payoff family.

## Paper-Level Claim Boundary

Allowed after full-train RGA rows:

```text
RGA exposes bidirectional semantic-geometric mismatch on train data and provides
a controlled audit protocol for relation reliability.
```

Allowed after full-train controlled labels:

```text
H002 has or lacks evidence that non-semantic factors explain relation
reliability beyond semantic score and geometry-only validity under train-only
controls.
```

Blocked until protocol freeze and validation/test:

- posterior improves generalization.
- H002 improves downstream 3DSSG prediction.
- multi-view factor improves relation reliability.
- validation/test results.
- broad open-vocabulary 3DSG SOTA claim.

## Decision

Current decision:

```text
full_train_expansion_before_validation
```

Meaning:

```text
Expand H002 from Open3DSG train pilot to full train, keep validation/test closed,
use RGA as the main framework, and use full train to mine controlled labels and
test whether posterior signal survives shortcut controls.
```

## Next TODO

Next document:

```text
53_full_train_scope_contract.md
```

Goal:

- define the full-train source scope, expected row identity, artifact paths, and
  execution boundary.
- decide whether the first full-train expansion can reuse existing train-pilot
  scripts or needs a new train-full runner.
- keep validation/test unavailable.
- prepare a run checklist for full-train RGA row generation before any posterior
  model training.
