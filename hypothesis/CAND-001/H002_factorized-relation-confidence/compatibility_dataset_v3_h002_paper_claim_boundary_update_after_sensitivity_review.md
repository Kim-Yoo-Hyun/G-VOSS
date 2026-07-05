# H002 Paper Claim Boundary Update After Sensitivity Review

## Purpose

This stage locks the paper-facing H002 claim after the normalization and
no-route geometry sensitivity review. The goal is to prevent the paper from
overstating a partially validated route-aware framework as a completed general
reliable 3D relation framework.

## Decision

```text
status = h002_paper_claim_boundary_update_after_sensitivity_review_ready
locked_claim = validation_level_comparison_route_source_reranking
comparison_route_main_claim_allowed = true
relation_aware_framework_partially_validated = true
general_reliable_framework_completed_result = false
pobs_prel_solved_claim_allowed = false
normalization_invariant_claim_allowed = false
validation_errors = 0
next_todo = h002_general_framework_gap_experiment_plan_after_claim_boundary_lock
```

## Allowed Wording

H002 can claim that factor-isolated predicate-geometry compatibility improves
validation-level source reranking for geometry-checkable comparison relations.

The paper can describe relation-aware evidence routing as a principled
framework and route map:

```text
some relations are geometry-decidable,
some require predicate-geometry compatibility,
some require observability-aware abstention,
and some require semantic/structural reasoning.
```

## Blocked Wording

Do not claim:

- official 3DSSG test benchmark result
- SOTA or leaderboard result
- unconstrained open-set GT evaluation
- uniform improvement across all source/family/K cells
- support/contact solved
- calibrated `p_obs/p_rel` reliability solved
- normalization-invariant improvement
- completed general reliable 3D relation framework

## Updated Files

- `paper/h002_compatibility_routing/README.md`
- `paper/h002_compatibility_routing/tables.md`
- `paper/h002_compatibility_routing/route_framework.md`
- `paper/h002_compatibility_routing/risk.md`
- `paper/h002_compatibility_routing/outline.md`
- `paper/h002_compatibility_routing/draft.md`
- `hypothesis/CAND-001/H002_factorized-relation-confidence/README.md`
- `hypothesis/CAND-001/H002_factorized-relation-confidence/paper_claim_core.md`
- `hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0705.md`
