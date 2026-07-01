# H002 Counterfactual Protocol V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `C_e = compatibility(T_e, G_e)`를 학습하고 평가하기 위한 positive/negative
구성 규칙을 고정한다. 목표는 compatibility head가 기존 source score, predicate prior,
object-pair identity shortcut을 복사하지 않고, predicate meaning과 object-pair geometry
evidence의 정합성을 보도록 만드는 것이다.

Core rule:

```text
source candidate != positive
no-GT candidate != negative
```

H002의 compatibility learning은 source relation predictor를 재학습하는 것이 아니라,
relation predicate가 요구하는 geometry evidence와 실제 object-pair geometry가 맞는지
학습한다.

## Scope

This protocol applies to:

```text
C_e = compatibility(T_e, G_e)
```

It does not define final reliability labels by itself. Final reliability uses:

```text
p_obs = P(evidence is sufficient to decide)
p_rel = P(relation is reliable | evidence is observable)
```

## Train-Only Policy

Hypothesis-stage construction uses train-side data only.

Forbidden:

- validation/test relation annotations for target construction;
- validation/test scans for threshold selection;
- selecting positives/negatives after looking at held-out performance.

Allowed:

- train official GT relation annotations;
- train candidate predictions from VL-SAT/Open3DSG-style sources;
- train geometry features;
- train human/audit labels generated from train artifacts;
- train counterfactual corruptions.

## Positive Tiers

Compatibility positives must be high precision. A row can be positive only if it belongs
to one of the following tiers.

### P0: Official GT + Geometry-Usable

Requirements:

- exact official GT predicate for the directed subject-object pair;
- geometry evidence available for the relation family;
- `Q_e` not low enough to force abstain;
- no known geometry contradiction from rule-derived diagnostic.

Use:

- primary positive tier for closed-set relation families.

Caveat:

If an official GT edge is geometry-contradicted, it is not a compatibility positive. It becomes
an RGA diagnostic case such as `GT+ / G-`.

### P1: Human/Audit Accepted

Requirements:

- train-side audit label is `accept_reliable`;
- audit was created without exposing hidden construction fields;
- evidence is sufficient enough for `p_obs` positive supervision;
- audit provenance is recorded.

Use:

- primary positive tier for hard families such as `attached to`, `hanging on`, and
  multi-view/mesh-confirmed cases.

### P2: High-Precision Geometry-Verified

Requirements:

- relation family has a frozen high-precision geometry rule;
- geometry evidence strongly supports the relation;
- threshold is fixed from train/dev calibration or predeclared rule, not tuned on validation/test;
- no low-observability flag.

Examples:

- `close by` with very small normalized boundary distance;
- `higher than` with large positive vertical margin;
- `standing on` with near-contact plus projected support overlap.

Use:

- auxiliary compatibility positives;
- teacher/baseline comparison against H001 `p_geom_valid`.

Caveat:

This tier must be reported as geometry-verified proxy, not human reliability GT.

### P3: Cross-Source Agreement + Geometry Support

Requirements:

- two or more independent relation sources predict the same predicate or same normalized predicate family;
- geometry evidence supports the predicate;
- source agreement is not used as `C_e` input;
- source ids and scores remain audit/control fields or `Z_e`, not compatibility input.

Use:

- optional positive tier for open-vocabulary source transfer.

## Positive Exclusions

The following are not valid positives for `C_e` training by themselves:

- any arbitrary Open3DSG/VL-SAT predicted relation;
- high source score without geometry support;
- no-GT row with plausible text but no audit/geometry confirmation;
- low-observability row;
- unsupported relation family;
- row selected only because of hidden proxy role or construction metadata.

## Negative Tiers

Compatibility negatives should be hard enough that predicate/object priors alone do not solve the task.

### N1: Wrong-Pair Geometry

Construction:

```text
keep T_e
replace G_e with another object-pair geometry
```

Matching constraints:

- same split: train only;
- same relation family;
- same scene where possible;
- same or similar source rank band where possible;
- same or similar `Q_e` / observability tier;
- avoid trivial object-class mismatch when possible.

Purpose:

Tests whether compatibility uses object-pair geometry rather than predicate prior.

### N2: Shuffled Geometry

Construction:

```text
keep T_e
shuffle G_e within a controlled pool
```

Matching constraints:

- same family;
- same source;
- same rank band;
- same coverage tier;
- same scan or same scene type when possible.

Purpose:

Tests whether geometry alignment matters beyond marginal geometry distribution.

### N3: Predicate Flip

Construction:

```text
keep G_e
replace T_e with incompatible predicate
```

Safe flips:

- `higher than` <-> `lower than`;
- `inside` <-> `surrounding` when containment direction is known;
- `standing on` / `lying on` to incompatible support predicate only when geometry no longer supports the flipped predicate;
- attachment predicate flip only when a family-specific contradiction rule exists.

Blocked flips:

- flipping to a vague or ontology-ambiguous predicate;
- flipping `attached to` / `connected to` without explicit physical-connection schema;
- flipping `close by` to an unsupported `far from` label unless the ontology includes it.

Purpose:

Tests whether `T_e` changes the interpretation of the same geometry.

### N4: Subject/Object Swap

Construction:

```text
swap subject and object roles
```

Use when relation is directional:

- `higher than`, `lower than`;
- `standing on`, `supported by`;
- `inside`;
- directional attachment if schema supports direction.

Blocked:

- symmetric or near-symmetric relations unless direction matters;
- cases where swap creates another valid relation.

Purpose:

Tests whether the model understands directed geometry, not just unordered pair layout.

### N5: Relation-Specific Perturbation

Construction examples:

- support/contact: remove or perturb contact/support overlap;
- vertical: invert or reduce vertical margin;
- proximity: increase normalized distance;
- containment: move object outside containment boundary;
- attachment: break near-contact or anchor geometry when mesh/point evidence supports it.

Purpose:

Creates hard negatives tied to the geometry evidence actually required by the predicate.

### N6: Same-Family / Same-Rank / Same-Coverage Hard Negative

Construction:

```text
negative row is matched to positive row on family, rank band, and observability tier
```

Required matching fields:

- predicate family;
- source id;
- rank band or score band;
- `Q_e` tier;
- scene or scan when possible;
- object class family when possible.

Purpose:

Prevents the task from becoming source-rank, coverage, predicate-family, or object-class classification.

## No-GT Handling

No-GT is unknown by default.

```text
no_gt_for_pair -> unlabeled / candidate for audit
```

No-GT can become negative only if one of the following is true:

- generated counterfactual corruption with known invalid construction;
- human/audit reject label;
- high-precision geometry contradiction under sufficient observability;
- official GT has mutually exclusive opposite predicate for the same directed pair and the ontology supports exclusivity.

No-GT can become positive only if one of the following is true:

- human/audit accept label;
- high-precision geometry-verified positive tier;
- cross-source agreement plus geometry support, if enabled.

## Observability Rules

Low-observability rows should not be forced into positive or negative compatibility labels.

Use:

```text
low Q_e -> p_obs supervision / abstain stress test
```

Not:

```text
low Q_e -> negative relation label
```

Examples routed to observability:

- missing point cloud or mesh;
- limited view only;
- no same-frame visibility for attachment relation;
- unsupported family;
- strong conflict between mesh and view evidence.

## Source-Score Leakage Controls

Because `Z_e` is separated from `C_e`, the protocol must verify that compatibility does not copy
source confidence.

Required controls:

- train `C_e` without `Z_e`;
- shuffle source score/rank during compatibility evaluation;
- match positives and negatives by source id and rank band when possible;
- report rank-band-only and source-score-only baselines;
- inspect whether `C_e` performance remains after source score/rank shuffle.

Pass condition:

```text
C_e should remain sensitive to geometry corruption after source score/rank shuffle.
```

Fail condition:

```text
C_e drops to source-rank shortcut behavior or counterfactual drop disappears.
```

## Matching Priority

Hard negative matching follows this priority order.

1. same split;
2. same relation family;
3. same source id;
4. same rank band or score band;
5. same `Q_e` tier;
6. same scan;
7. same object class family;
8. same endpoint type, if available;
9. same geometry feature bucket, when it does not destroy the counterfactual.

If strict matching yields too few rows, relax from the bottom upward and record the relaxation.

## Prototype Sampling Contract

For first smoke, use a small but balanced train-only prototype.

Recommended target:

```text
families = proximity, relative_vertical, support_contact, attachment_deferred
positive tiers = P0/P1/P2 only
negative tiers = N1/N2/N3/N4/N6
min positive per family = 50 if available
negative per positive = 2 to 4
low-observability rows = separate p_obs subset
```

Attachment-specific caveat:

`attached to`, `hanging on`, and `connected to` should not rely on generic OBB distance alone.
Use them only when mesh/multi-view/point evidence can support either a positive tier or a controlled
counterfactual. `connected to` remains diagnostic unless a physical-connection schema exists.

## Labels Produced

The protocol produces separate labels.

```text
compatibility_label: positive / counterfactual_negative / unknown
positive_tier: P0 / P1 / P2 / P3 / none
negative_tier: N1 / N2 / N3 / N4 / N5 / N6 / none
observability_label: observable / limited / insufficient
source_label: original source candidate metadata, not compatibility target
```

It does not directly produce final relation reliability labels.

## Evaluation Rows

Each counterfactual group should preserve:

```text
group_id
anchor_row_id
counterfactual_type
positive_tier
negative_tier
matching_fields
relaxed_matching_fields
T_e fields
G_e fields
Q_e fields
Z_e fields, held out from C_e
official_gt_axis
audit_axis, if available
```

## Required Smoke Metrics

- `C_e` real-vs-counterfactual AUROC;
- counterfactual score drop by negative tier;
- source-score/rank shuffle sensitivity;
- same-family hard-negative AUPRC;
- per-family score-drop distribution;
- low-observability abstain rate under `p_obs`;
- false negative audit rate on no-GT but geometry-supported rows.

## Failure Criteria

The protocol is not successful if:

- positives are dominated by unverified source predictions;
- negatives are mostly easy random pairs;
- no-GT rows are treated as negative without audit or counterfactual construction;
- `C_e` performance disappears under source-score/rank shuffle;
- hard negatives are separable by predicate family, rank band, endpoint id, or coverage tier alone;
- low-observability rows are forced into reject rather than abstain.

## Current Follow-Up

```text
prototype_dataset_contract_v1 = completed
smoke_baseline_plan_v1 = completed
prototype_dataset_materialization_v1 = completed
next = smoke_baseline_runner_v1
```

The next step should run or specify controlled smoke baselines over the materialized counterfactual
groups.
