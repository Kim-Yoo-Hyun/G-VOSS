# H002 Relation-Aware Route Framework

## Goal

The upgraded H002 goal is not to force every 3D Scene Graph relation through one
fixed score. The goal is a relation-aware reliable 3D relation framework:

```text
relation candidate
-> route classification
-> route-specific evidence schema
-> compatibility / observability / abstention decision
-> reranking, accept/reject, relabel, or abstain
```

This makes H002 broader than the current comparison-route result while keeping
the paper claim honest about what has been empirically validated.

## Route Map

| Route | Relation Types | Main Evidence Needed | Current Status |
| --- | --- | --- | --- |
| comparison compatibility | `higher than`, `lower than`, `bigger than`, `smaller than` | predicate-independent signed geometry plus predicate compatibility | main quantitative success |
| geometry-only compatibility | `close by`, `near` | distance / proximity evidence | control and generality route |
| frame-aware directional | `left`, `right`, `front`, `behind` | reference frame, axis sign, object pair geometry | candidate route; frame risk remains |
| support/contact | `standing on`, `lying on`, `supported by` | contact patch, support surface, pose/orientation, mesh quality | hard-route failure taxonomy |
| attachment / connection | `attached to`, `hanging on`, `connected to` | local contact, attachment point, multi-view/mesh evidence, observability | future observability-heavy route |
| containment / occupancy | `inside`, `standing in`, `lying in`, `hanging in` | containment ratio, occlusion, view/mesh completeness | future observability-heavy route |
| occlusion / coverage | `cover` | visibility, occlusion, coverage evidence | future route |
| semantic / structural | `part of`, `belonging to`, identity/symmetry labels | semantic/structural or identity/symmetry evidence | not geometry-only; abstain or separate route |

## Current Paper Position

Selected framework claim:

```text
Reliable 3D relation reasoning should be route-aware: some relations are
geometry-decidable, some require predicate-geometry compatibility, some require
observability-aware abstention, and some should not be judged by geometry alone.
```

Validated mechanism claim:

```text
Factorized predicate-geometry compatibility improves validation-level source
reranking for geometry-checkable comparison relations.
```

Boundary after sensitivity review:

```text
comparison_route_main_claim_allowed = true
relation_aware_framework_partially_validated = true
general_reliable_framework_completed_result = false
```

The paper should present the route-aware framework as a principled design that
explains why different families need different evidence routes. Only the
comparison route is currently validated as the main quantitative success.

Protocol freeze status:

```text
status = h002_relation_aware_framework_claim_hierarchy_and_route_protocol_ready
date = 2026-07-06
```

This protocol freezes:

- claim hierarchy: framework claim, validated mechanism claim, route-taxonomy
  claim, and boundary/future claim
- route-assignment protocol: geometry-decidable, predicate-conditioned,
  observability-heavy, superordinate/decomposition, semantic/structural
- route-wise table placement and metric role
- blocked wording, including all-relation solved, support/contact solved,
  calibrated p_obs/p_rel solved, and I4-as-main-score wording

## Frozen Claim Hierarchy

The paper must keep four claim levels separate.

| Level | Claim | Evidence Status | Paper Role |
| --- | --- | --- | --- |
| L1 framework | Reliable 3D relation estimation requires relation-aware evidence routing rather than one fixed semantic-geometry fusion. | supported by route analyses, failures, and controls | problem/method framing |
| L2 validated mechanism | `C_e = compatibility(T_e, G_e)` improves validation-level source reranking for comparison relations. | quantitatively validated on `relative_vertical` and `size_relative` | main result |
| L3 route taxonomy | Relation families fall into geometry-only, compatibility, observability-heavy, superordinate/decomposition, or semantic/structural routes. | partially validated plus diagnostic/future routes | analysis table and framework figure |
| L4 boundary | H002 does not solve every 3DSSG relation family. | explicit blocked gates | limitations and reviewer defense |

The paper can use L1 as the organizing framework, but L2 is the only current
quantitative success claim. L3 explains generality without overclaiming. L4
prevents the framework from being read as a completed all-relation benchmark.

## Route Assignment Protocol

Route assignment is based on the evidence needed to decide the relation, not on
which route currently gives the best score.

| Criterion | Question | Route |
| --- | --- | --- |
| geometry-decidable | Can predicate validity be decided from predicate-independent metric geometry alone? | geometry-only |
| predicate-conditioned geometry | Does the same geometry support one predicate but contradict another? | predicate-geometry compatibility |
| frame-conditioned geometry | Does the relation require a reference frame or direction convention? | frame-aware compatibility |
| observability-dependent | Is the needed physical evidence hidden, view-dependent, or mesh-quality dependent? | observability-aware |
| superordinate label | Is the predicate too broad and better treated as subtype, relabel, or abstain? | superordinate/decomposition |
| semantic/structural | Is relation validity mainly identity, part-whole, ontology, or symmetry reasoning? | semantic/structural |

Route assignment must not use validation labels, GT match, source score,
source rank, or post-hoc metric outcomes. These fields are allowed only for
evaluation or final reranking after the route and score protocol are fixed.

## Route-Wise Metric And Table Placement

| Route | Primary Metric Role | Main Paper Placement | Appendix / Diagnostic Placement |
| --- | --- | --- | --- |
| comparison compatibility | Recall@K, Violation@K, bootstrap CI, controls | main quantitative table | family-wise caveat and full controls |
| geometry-only | route-control evidence and violation diagnostic | route-readiness table | source-level proximity extension if added |
| frame-aware directional | candidate route with frame-risk caveat | route-readiness table only | frame controls and failure examples |
| support/contact | failure taxonomy, not success metric | limitation / failure analysis | hard-route AUROC and class-pair capacity diagnostics |
| observability-heavy | `Q_e` / p_obs protocol, missing-evidence controls | framework figure only | p_obs/p_rel diagnostics; no solved claim |
| superordinate/decomposition | relabel/abstain target design | route-readiness table | supported-by decomposition diagnostics |
| semantic/structural | boundary or separate task | limitation / future work | optional route definition only |

The main validation result table must stay scoped to the comparison route.
Route-readiness and failure-taxonomy tables explain the broader framework.
They do not convert diagnostic routes into solved quantitative claims.

## Score Promotion Policy

The promoted main score remains:

```text
S2_current_source_x_Ce
```

`I4_calibrated_route_aware_source_x_Ce` is allowed only as:

- secondary/candidate ablation
- improvement-path diagnostic
- motivation for future calibrated or route-gated `C_e`

It is not the main score because the CI/family review found family-wise
regression cells, especially Open3DSG `relative_vertical`.

Do not claim:

- all relation families are solved
- support/contact is solved
- calibrated `p_obs/p_rel` reliability is solved
- official test or SOTA benchmark
- `I4` is the promoted main score

Section sync after this freeze:

```text
status = h002_route_aware_paper_section_sync_after_protocol_freeze_ready
```

The frozen hierarchy is now synced into the outline, draft text, table
captions, figure captions, and risk wording without changing metrics.

Next step:

```text
h002_route_aware_full_draft_plan_after_section_sync
```

## Required Experiments To Grow Into A General Framework

The scoped paper claim no longer requires these experiments, but a general
reliable 3D relation framework claim does.

1. Repair or redesign support/contact with richer predicate-independent
   evidence: contact patch, support surface, pose/orientation, surface normals,
   local point density, mesh gap/intersection.
2. Build an observability-heavy route for attachment/containment using
   multi-view/mesh evidence as `Q_e` before using it as model input.
3. Keep semantic/structural relations as route-specific abstain or separate
   structural reasoning, not geometry-only failures.
4. Promote `p_obs/p_rel` only after real observability labels, calibration, and
   missing-evidence controls support the quantitative claim.
5. Re-run route-specific source-level evaluation before claiming route
   generality beyond comparison relations.

Latest planning gate:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update/
```

This gate passed with validation errors `0`; it is a contract for the next
implementation step, not a new result table.

Latest implementation gate:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/
```

This implementation also passed with validation errors `0` and produced
positive primary-route CI against both geometry-only and plain concat
ablations. The result review is complete; paper wording is now locked to the
scoped comparison-route boundary.

Latest result-review gate:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation/
```

The review fixes the interpretation: aggregate primary-route evidence supports
S2 over A1/A2, family-wise Violation is stable, family-wise Recall is mixed, and
all-relation wording remains blocked.

Latest experiment-stage gap review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_experiment_stage_remaining_gap_review_after_ablation_result_review/
```

The global review confirms that the paper claim is possible only if scoped to
validation-level comparison-route source reranking. It also identifies two
remaining sensitivities before final paper wording: candidate-pool score
normalization and the route-aware nature of the geometry-only ablation.

Latest normalization/no-route geometry sensitivity review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_experiment_stage_normalization_and_no_route_geometry_sensitivity_after_gap_review/
```

This review resolves the route-family one-hot concern for the current primary
route: no-route G-only sensitivity remains weaker than S2. Raw
`source_score*C_e` preserves the improvement direction over S0 at K `{10,20,50}`;
rank-percentile normalization loses low-K recall, so normalization-invariant
wording stays blocked.

Framework status after this review:

```text
relation_aware_evidence_routing_framework = constructed_as_framework_and_partially_validated
general_reliable_3d_relation_framework = not_yet_validated
```

Latest claim-boundary lock:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_paper_claim_boundary_update_after_sensitivity_review/
```

Decision:

```text
locked_claim = validation_level_comparison_route_source_reranking
allowed_framework_wording = relation-aware evidence routing is constructed and partially validated
blocked_framework_wording = completed general reliable 3D relation framework
```
