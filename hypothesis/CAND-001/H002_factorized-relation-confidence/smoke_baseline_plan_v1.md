# H002 Smoke Baseline Plan V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations`의
첫 smoke comparison을 정의한다. 목표는 모델 성능을 주장하는 것이 아니라, H002의 factor
분리가 실제로 의미 있는 신호를 만드는지 train-only prototype dataset에서 빠르게 검증하는
것이다.

Smoke에서 검증할 질문은 세 가지다.

```text
1. C_e = compatibility(T_e, G_e)가 source confidence Z_e를 복사하지 않고
   predicate-geometry compatibility를 보는가?
2. Q_e가 relation truth를 직접 결정하지 않고 abstain/selective decision에 기여하는가?
3. full factorized decision이 simple S x p_geom_valid 또는 concat MLP보다
   더 방어 가능한 failure/control profile을 보이는가?
```

이 문서는 실행 결과가 아니다. `prototype_dataset_contract_v1.md`에 맞는 materialized
dataset이 생긴 뒤, 어떤 baseline과 metric을 돌릴지 고정하는 계획이다.

## Input Contract

Required input root:

```text
artifacts/prototype_dataset_v1/
```

Required input files:

| File | Required Use |
| --- | --- |
| `prototype_rows.jsonl` | factor-separated row input |
| `counterfactual_groups.jsonl` | anchor/counterfactual grouping |
| `baseline_view.jsonl` | flattened baseline fields |
| `audit_view.jsonl` | label/control fields for analysis |
| `schema.json` | blocked-input and field-type validation |
| `summary.json` | count sanity and family/tier availability |
| `validation_errors.jsonl` | must be empty before smoke |

Smoke must stop if:

- any row is not train split;
- `validation_errors.jsonl` is non-empty;
- `compatibility_main` contains `Z_e`;
- `G_e` contains predicate/family/source fields;
- no-GT rows are used as automatic negatives;
- hidden construction fields appear in deployable model input views.

## Train-Only Evaluation Policy

All smoke runs are hypothesis-stage train-only checks.

Allowed:

- train-only internal grouped folds;
- train-only group split by scan id or scene id;
- train-only counterfactual grouping;
- train-only source/rank/family shortcut probes.

Forbidden:

- validation/test relation annotations;
- validation/test scans;
- tuning thresholds using held-out official validation/test performance;
- reporting smoke results as paper-level evidence.

Recommended smoke split:

```text
split_policy = train_internal_grouped_by_scan
fold_count = 5 if row count allows, otherwise 3
group_key = scan_id
counterfactual_group_integrity = keep all rows in a group in the same fold
```

If scan-grouped folds destroy class balance, use repeated train-only stratified group split and report
the imbalance explicitly. Do not silently switch to random row split.

## Smoke Tasks

### Task A: Compatibility

Target:

```text
compatibility_label = positive vs counterfactual_negative
```

Inputs:

- positives: P0/P1/P2/P3 as defined in `counterfactual_protocol_v1.md`;
- negatives: N1/N2/N3/N4/N5/N6 counterfactual negatives;
- excluded: `unknown`, low-observability rows unless explicitly stress-testing.

Primary question:

```text
Does C_e score the true predicate-geometry pair higher than controlled counterfactuals?
```

Primary metrics:

- AUROC;
- AUPRC;
- paired anchor-vs-counterfactual score drop;
- score drop by negative tier N1-N6;
- same-family/rank/coverage hard-negative AUPRC.

Required slices:

- relation family;
- positive tier;
- negative tier;
- source id;
- source rank band;
- observability tier;
- same-scene vs cross-scene counterfactual.

### Task B: Observability

Target:

```text
observability_label = observable / limited / insufficient
```

Primary question:

```text
Does Q_e identify cases where relation truth should be abstained rather than forced to reject?
```

Primary metrics:

- macro F1 over observability labels;
- insufficient/limited recall;
- selective coverage at fixed abstain threshold;
- error rate on low-coverage rows;
- conflict/missing-evidence detection rate.

Important constraint:

`Q_e` success is not relation correctness. It is evidence sufficiency. A high `p_obs` should mean
"we can decide", not "the relation is true".

### Task C: Reliability

Target:

```text
reliability_label = accept / reject / abstain
```

Usable rows:

- provenance-marked audit labels;
- official GT plus geometry-usable positive cases;
- valid counterfactual negatives;
- abstain/uncertain rows with explicit observability reason.

Primary question:

```text
Does the two-head decision separate accept/reject from abstain better than scalar reranking?
```

Primary metrics:

- binary AUROC/AUPRC on accept vs reject, only where `binary_usable = true`;
- multiclass macro F1 on accept/reject/abstain, only where `multiclass_usable = true`;
- selective risk vs coverage;
- Brier score and ECE if calibration target is sufficient;
- false accept rate on counterfactual negatives;
- false reject rate on audit-accepted or GT-positive rows.

Reliability task is secondary until label provenance and class mass are sufficient. If labels remain
positive-sparse or shortcut-prone, report Task C as diagnostic-only and do not promote it.

## Baseline Set

### B0: Constant And Frequency Baselines

Purpose:

```text
detect label imbalance and trivial target construction
```

Variants:

- majority class;
- family-frequency prior;
- predicate-frequency prior;
- rank-band-frequency prior.

Failure signal:

If these baselines are near the proposed method, the target is too easy or too imbalanced.

### B1: Source Confidence Only

Input:

```text
Z_e
```

Examples:

- source score;
- normalized source score;
- source rank;
- source rank band;
- source id.

Purpose:

Tests whether the target is mostly copied from the original relation source.

Expected role:

Strong on source-like labels, weak under controlled counterfactual geometry if target is valid.

### B2: Semantic Content Plus Source Confidence

Input:

```text
T_e + Z_e
```

Purpose:

Tests whether predicate/object priors plus source confidence solve the task without geometry.

Failure signal:

If B2 solves compatibility under same-family/rank/coverage hard negatives, the target likely still
contains semantic or source shortcut.

### B3: Geometry Rule Only

Input:

```text
p_geom_valid_baseline
geometry_status_baseline
```

Purpose:

H001-style geometry-only baseline and teacher reference.

Important interpretation:

This baseline can be strong for geometry-clear families such as `higher than` or support/contact. It
should not be treated as a failure of H002 by itself. H002 must beat or complement it in cases where
predicate meaning, observability, and source confidence matter.

### B4: Risk-Aware Soft Reranking

Input:

```text
source_score_normalized * p_geom_valid_baseline
```

Log-utility interpretation:

```text
utility(e) = log source_score(e) - lambda * geometry_risk(e)
geometry_risk(e) = -log p_geom_valid(e)
lambda = 1
```

Purpose:

Direct comparison to the simple semantic-geometry product. This is the strongest simple baseline
for H002 because it may already improve violation/recall tradeoffs without learned compatibility.

Expected H002 advantage:

H002 should not claim merely that it multiplies semantic and geometry. It should show better
counterfactual sensitivity, observability handling, family-specific failure behavior, or calibrated
selective decisions.

### B5: Geometry Vector Only

Input:

```text
G_e
```

Purpose:

Tests whether geometry alone solves the target because labels are geometry-status shortcuts.

Interpretation:

Geometry-only can be useful as a control, but it cannot fully define predicate-specific compatibility.
If B5 solves everything, the target may be mostly a geometry-rule target rather than a compatibility
target.

### B6: Compatibility Only

Input:

```text
C_e = compatibility(T_e, G_e)
```

Training view:

```text
T_e + G_e
Z_e excluded
```

Purpose:

Main test of predicate-geometry compatibility.

Required controls:

- source-score shuffle;
- rank-band shuffle;
- wrong-pair geometry;
- shuffled geometry;
- predicate flip;
- subject/object swap.

Expected signal:

`C_e` should drop on counterfactuals while being insensitive to source-score/rank shuffling.

### B7: Non-Factorized Concat MLP

Input:

```text
T_e + Z_e + G_e + Q_e
```

Purpose:

Tests whether factorization matters beyond giving all fields to a small model.

Required report:

- performance;
- leakage/shuffle sensitivity;
- family-wise error profile;
- calibration and selective-decision behavior.

Interpretation:

If concat MLP wins raw metrics but fails controls, H002 should prefer the factorized design. If concat
MLP wins both metrics and controls, the factorized method needs a stronger architectural reason.

### B8: Factorized Without Q

Input:

```text
Z_e + C_e + optional T_e interaction
```

No separate `p_obs`.

Purpose:

Tests whether observability is actually needed.

Expected signal:

No-Q should over-reject low-evidence or unsupported rows. Full H002 should reduce forced false
rejects by abstaining.

### B9: Full Two-Head Factorized Decision

Inputs:

```text
p_obs = f(Q_e, optional geometry-quality fields)
p_rel = f(Z_e, C_e, optional T_e interaction)
decision = abstain if p_obs low, else accept/reject by p_rel
```

Purpose:

Main H002 smoke condition.

Required ablations:

- `C_e` removed;
- `Z_e` removed from `p_rel`;
- `Q_e` removed;
- `p_geom_valid_baseline` added as teacher/ablation only;
- source/rank shuffled;
- counterfactual geometry shuffled.

## Model Complexity Rule

First smoke should use simple models before Transformer-style architectures.

Recommended initial models:

- logistic regression or calibrated linear model for scalar baselines;
- small MLP for `G_e` and concat baseline;
- small Siamese or bilinear compatibility head for `T_e + G_e`;
- small two-head MLP for `p_obs` and `p_rel`.

Blocked at this stage:

- large cross-attention Transformer;
- point-cloud encoder training from raw points;
- multi-view image encoder training;
- graph transformer;
- diffusion/denoising graph repair.

Reason:

The first smoke must answer whether the target and factor split are identifiable. Bigger architectures
can hide target shortcuts and make failure diagnosis harder.

## Shortcut And Control Suite

Every smoke run must include these controls.

### Source Controls

- source score shuffle;
- source rank shuffle;
- source id only baseline;
- rank band only baseline;
- per-source calibration sanity.

### Semantic Controls

- predicate-only baseline;
- relation-family-only baseline;
- subject/object-label-only baseline;
- predicate flip counterfactual.

### Geometry Controls

- wrong-pair geometry;
- shuffled geometry within same family/rank/coverage pool;
- subject/object swap;
- relation-specific perturbation where defined;
- geometry feature mask ablation;
- `p_geom_valid` teacher-vs-input ablation.

### Observability Controls

- no-view rows;
- low point count rows;
- missing mesh rows;
- unsupported family rows;
- evidence conflict rows.

### Hidden-Field Controls

- endpoint id probe;
- scan id probe;
- object-pair id probe;
- packet id/proxy role probe if present;
- construction group id probe if present.

Hidden-field controls are diagnostic only. They must not be deployable model inputs.

## Promotion Gates

### Gate 1: Dataset Sanity

Pass if:

- all rows are train-only;
- validation errors are zero;
- positive and counterfactual negative rows exist in at least one non-trivial family;
- unknown/no-GT rows are not used as negatives;
- source/rank/family-only probes do not trivially solve the target.

Fail action:

Return to prototype materialization or counterfactual mining. Do not run full smoke.

### Gate 2: Compatibility Signal

Pass if:

- `C_e` beats `Z_e`-only and predicate/family-only baselines on Task A controls;
- `C_e` has positive paired score drop on wrong-pair/shuffled/predicate-flip counterfactuals;
- `C_e` remains stable under source-score/rank shuffle;
- gains are visible in at least two relation families or one family with strong hard-negative controls.

Fail action:

Inspect whether positives are source-derived, negatives are too easy, or `G_e` lacks needed evidence.

### Gate 3: Observability Signal

Pass if:

- `Q_e` identifies insufficient/limited evidence better than source or predicate priors;
- no-Q factorized model over-rejects low-evidence rows relative to full two-head model;
- abstain rows are not simply copied from hidden construction fields.

Fail action:

Revise `Q_e` fields or merge unsupported/low-coverage cases into clearer observability labels.

### Gate 4: Factorized Benefit

Pass if full H002 shows at least one of:

- better counterfactual robustness than `semantic_score * p_geom_valid`;
- better selective risk/coverage than no-Q and concat MLP;
- better leakage/control profile than concat MLP at comparable performance;
- clearer family-specific error taxonomy that explains where geometry rule/product fails.

Fail action:

Do not claim factorized reliability. Either keep H002 as diagnostic, strengthen geometry evidence,
or move to a more explicit compatibility architecture only after target sanity is proven.

## Reporting Format

Recommended output root after execution:

```text
artifacts/smoke_baseline_v1/
```

Required output files:

| File | Role |
| --- | --- |
| `summary.json` | top-level pass/fail gates and metric table |
| `metrics_by_task.json` | Task A/B/C metrics |
| `metrics_by_family.json` | family and predicate slices |
| `counterfactual_score_drop.json` | paired score-drop metrics |
| `shortcut_probe_metrics.json` | source/rank/family/endpoint probes |
| `ablation_metrics.json` | no-C, no-Z, no-Q, teacher/ablation results |
| `error_cases.jsonl` | representative false accept, false reject, false abstain rows |
| `report.md` | human-readable smoke interpretation |
| `validation_errors.jsonl` | execution/schema errors |

The report should explicitly mark:

- promotable evidence;
- diagnostic-only evidence;
- target construction blocker;
- factor definition blocker;
- geometry evidence blocker.

## Expected Interpretation

The strongest early positive result is not simply:

```text
full model has best AUROC
```

The stronger H002 result is:

```text
C_e responds to predicate-geometry counterfactuals while ignoring source-score shortcuts;
Q_e separates uncertain evidence from false relation;
full two-head decision improves robustness/selectivity over source-only, geometry-only,
S x p_geom_valid, and concat MLP under controlled probes.
```

If `semantic_score * p_geom_valid` performs similarly on raw metrics, H002 can still be meaningful
only if it provides better counterfactual behavior, observability handling, transfer across relation
families, or a clearer reliability decomposition. If those are not observed, H002 should not be
promoted as a method claim.

## Next TODO

```text
prototype_dataset_materialization_v1 = completed
smoke_baseline_runner_v1 = completed
next = learned_smoke_runner_v1
```

The first deterministic smoke runner has completed under `artifacts/smoke_baseline_v1/`. The next
step should implement train-internal learned smoke with explicit shortcut controls.
