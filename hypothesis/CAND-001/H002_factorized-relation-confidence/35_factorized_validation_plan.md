# H002 Factorized Validation Plan

Last updated: 2026-06-13

## Purpose

H002의 다음 검증 gate를 고정한다.

Current posterior under validation:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

Future posterior is deferred:

```text
P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)
```

이 문서의 핵심 결정:

```text
Validate the current factorized posterior before adding V_mv_e.
```

즉, multi-view는 아직 model input이 아니다. 현재 단계에서 multi-view는 label
confirmation/audit evidence로만 사용한다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factorized_validation_plan.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factorized_validation_plan.py
```

Status:

```text
ready_validation_plan_vmv_deferred
```

Boundary:

```text
split = train_only
validation usage = false
test usage = false
paper result = false
V_mv_e model input allowed = false
posterior claim allowed = false
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/report.md
```

## Current Smoke Reference

The current `(codex_ver)` smoke is only a reference. It is not a method result.

Train-internal 5-fold:

| Baseline | Inputs | AUROC | AUPRC | Brier | ECE-5 |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_only` | `S_e` | 0.6080 | 0.7431 | 0.2381 | 0.2620 |
| `geometry_only` | `G_e` | 0.8523 | 0.8986 | 0.1828 | 0.0300 |
| `semantic_plus_geometry` | `S_e + G_e` | 0.8864 | 0.9217 | 0.1420 | 0.0960 |
| `factorized_reliability_posterior` | `S_e + G_e + C_e + U_e` | 0.8864 | 0.9339 | 0.1434 | 0.1376 |

Reading:

- `semantic_plus_geometry` is already strong.
- `factorized` has slightly higher AUPRC but worse Brier/ECE in this smoke.
- Because labels are `(codex_ver)` and `N=27`, this is only plumbing evidence.
- H002 cannot claim posterior advantage from this result.

## Label Target Requirement

The next target must be independent enough that model performance is not just
recovering how the target was constructed.

### Hypothesis-Stage Minimum

This permits train-only hypothesis validation only.

| Requirement | Value |
| --- | --- |
| label source | human-confirmed or independent audit labels |
| `codex_ver` sufficient? | no |
| usable binary rows | at least 60 |
| per-class rows | at least 20 |
| reviewers | at least 1 |
| preferred reviewers | 2 |
| target form | same-family, same-geometry-status, same-rank-band reliability labels |
| allowed use | train-only hypothesis validation |

### Paper-Prep Minimum

This still does not replace later held-out evaluation.

| Requirement | Value |
| --- | --- |
| label source | two reviewers or adjudicated conflicts |
| usable binary rows | at least 100 |
| per-class rows | at least 40 |
| agreement | `>=0.75` exact final-label agreement or adjudicated disagreements |
| later required | held-out validation/test only after target and feature policy freeze |

## Primary Target Design

The immediate target should not be cross-family pooled.

Primary controlled target:

```text
predicate_family = fixed
geometry_status = fixed
rank_band = stratified or fixed
label = relation reliability / informativeness
```

Best current candidate:

```text
proximity / close by
geometry_status = satisfied
label = reliable_promote vs unreliable_dense_noise
```

Why:

- Current strict target already has this shape.
- It directly tests `geometry validity != relation reliability`.
- It controls the satisfied-vs-unsatisfied shortcut.

Current blocker:

```text
current usable rows = 27
positive = 16
negative = 11
```

This is below the hypothesis-stage minimum. The next target task must expand
human-confirmable controlled labels, especially negative `unreliable_dense_noise`
rows, without using validation/test data.

## Secondary Target Design

`support_contact` is promising but not ready as a balanced target.

Current audit candidate count:

```text
support_contact rows = 26
standing on = 15
supported by = 11
working labels = true_underconfidence 21, annotation_sparsity 5
```

Issue:

- Current support-contact queue lacks reliable negative labels.
- It is useful for future relation-family expansion.
- It should not replace the primary controlled target until balanced positives
  and negatives exist.

## Required Controls

| Control | Purpose | Required |
| --- | --- | --- |
| same-family | avoid family/source shortcut | yes |
| same-geometry-status | avoid satisfied vs unsatisfied shortcut | yes |
| same-rank-band | avoid top-K vs tail semantic shortcut | yes |
| same-source | avoid source/domain shortcut in current pilot | yes |
| no visual input | keep `V_mv_e` deferred | yes |

Operational meaning:

- Same-family: report primary result within one predicate family first.
- Same-geometry-status: primary reliability comparison should happen inside
  `geometry_status=satisfied`.
- Same-rank-band: positives and negatives must be sampled or stratified within
  comparable semantic rank bands.
- Same-source: current train pilot uses Open3DSG only; cross-source evidence is
  later.
- No visual input: visual/multi-view fields may influence audit labels but must
  not enter model features.

## Feature Policy

Allowed now:

- semantic score/rank features under same-rank-band control.
- continuous geometry evidence.
- `p_geom_valid`.
- coverage/checkability features.
- uncertainty/abstain features.

Excluded from claim view:

- `working_label`.
- `final_human_label`.
- `(codex_ver)` label.
- reviewer id or audit metadata.
- visual audit decision.
- `V_mv_e` deployable visual features.
- direct RGA bucket identity such as `top100_and_unsatisfied`.
- target construction flags such as `tail_gt100_and_satisfied`.
- predicate family/label when not controlled by stratification.

Diagnostic-only:

- full factorized view with direct identity features.
- pooled cross-family result before per-family controls.
- `(codex_ver)` label smoke.

## Baseline Set

Required comparison:

| Baseline | Inputs | Role |
| --- | --- | --- |
| `semantic_only` | `S_e` | source-score baseline |
| `geometry_only` | `G_e` | geometry-only reliability baseline |
| `semantic_plus_geometry` | `S_e + G_e` | strong simple baseline |
| `factorized_reliability_posterior` | `S_e + G_e + C_e + U_e` | H002 current method candidate |

Important:

```text
semantic_plus_geometry is the main baseline to beat.
```

If `factorized` cannot beat `semantic_plus_geometry` under controlled labels,
then H002 still supports the RGA diagnostic framing but not a posterior method
contribution.

## Acceptance Rule

### Hypothesis Support Signal

Factorized posterior can be said to support the H002 hypothesis only if all are
true:

- labels pass the hypothesis-stage minimum.
- same-family, same-geometry-status, same-rank-band controls pass structurally.
- `factorized_reliability_posterior` beats `semantic_plus_geometry` by either:
  - AUPRC `>= +0.03`, or
  - Brier `<= -0.02`.
- AUROC does not drop by more than `0.02`.
- the gain remains after direct identity/RGA-bucket features are removed.
- the gain is not concentrated in one obvious artifact stratum.

### Strong Support Signal

Strong support requires:

- two-reviewer or adjudicated labels.
- pair/bootstrap confidence interval positive for AUPRC delta or negative for
  Brier delta.
- coverage/uncertainty ablation shows `C_e`/`U_e` add signal beyond `S_e + G_e`.

### Stop Or Reframe

Stop or reframe H002 if:

- `factorized` is indistinguishable from `semantic_plus_geometry`.
- gains disappear under same-family/status/rank controls.
- label target remains `(codex_ver)` or machine-assisted only.
- performance is explained by predicate family, rank bucket, or geometry status
  identity.

## V_mv_e Gate

`V_mv_e` can be promoted to model input only after the current gate passes.

Promotion rule:

```text
V_mv_e must not become a deployable model input before
S_e + G_e + C_e + U_e passes the independent-target validation gate.
```

Until then:

- multi-view can support label confirmation.
- multi-view cannot be used as model input.
- multi-view cannot be used to claim visual-geometric reliability improvement.

## Current Decision

Established:

- current posterior validation plan is fixed.
- required baselines are fixed.
- target minimum is fixed.
- controls are fixed.
- `V_mv_e` is deferred.
- no validation/test rows were used.

Not established:

- independent controlled labels.
- factorized advantage over `semantic_plus_geometry`.
- paper-level result.
- visual evidence as deployable factor.

## Next TODO

Next document:

```text
36_controlled_label_target.md
```

Required next work:

- design how to expand the current strict target from 27 rows to at least 60
  usable human-confirmable rows.
- keep predicate family, geometry status, and rank band controlled.
- decide whether to mine more proximity dense-noise negatives or introduce a
  second controlled family only as a separate stratum.
- produce the next review queue without using validation/test rows.
