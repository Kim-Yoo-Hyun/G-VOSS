# H002 Compatibility Routing Paper Workspace

This workspace owns the standalone H002 paper draft track:

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

It is separate from the active H001/GeoCalib manuscript. H001 paper files under
`paper/aaai/` are not edited by this workspace.

## Current Status

```text
status = promoted_from_hypothesis_to_paper_workspace_goal_updated_to_route_aware_framework
source_split = official_3DSSG_validation_split
sources = VL-SAT validation predictions, Open3DSG validation predictions
primary_score = S2_source_x_Ce
baseline = S0_source_score
metrics = Recall@K, Violation@K
ultimate_goal = relation_aware_reliable_3d_relation_framework
current_main_success_route = geometry_checkable_comparison_relations
current_hard_route = support_contact
official_test_used = false
sota_or_leaderboard_claim_allowed = false
pobs_prel_framework_component_allowed = true
pobs_prel_calibrated_quantitative_claim_allowed = false
support_contact_solved_claim_allowed = false
source_reranking_ablation_expansion_plan_ready = true
source_reranking_ablation_expansion_implementation_ready = true
source_reranking_ablation_expansion_primary_ci_pass = true
source_reranking_ablation_expansion_result_review_ready = true
source_reranking_ablation_expansion_familywise_caveat = violation_stable_recall_mixed
experiment_stage_remaining_gap_review_ready = true
normalization_no_route_geometry_sensitivity_ready = true
paper_claim_strength = moderate_to_good_if_scoped
method_principle = natural_and_principled_for_scoped_problem
relation_aware_evidence_routing_framework = constructed_as_framework_and_partially_validated
general_reliable_3d_relation_framework = not_yet_validated
paper_claim_boundary_locked_after_sensitivity = true
selected_paper_direction = relation_aware_evidence_routing
framework_claim_role = broad_problem_and_design_framework
validated_mechanism_claim = predicate_geometry_compatibility_route
validated_mechanism_relations = relative_vertical,size_relative
validated_main_score = S2_current_source_x_Ce
i4_position = secondary_candidate_ablation_not_main_score
claim_hierarchy_and_route_protocol_ready = true
paper_section_sync_after_protocol_freeze_ready = true
current_paper_claim = relation_aware_framework_with_validated_comparison_route
general_framework_claim_role = design_framework_and_route_map_not_completed_result
next_step = h002_route_aware_full_draft_plan_after_section_sync
```

## Locked Core Claim

H002 is not a single universal relation scorer. The selected paper direction is
relation-aware evidence routing:

```text
Reliable 3D relation estimation requires route-specific evidence rather than
one fixed source confidence or semantic-geometry fusion.
```

The validated mechanism inside this framework remains narrower:

```text
Factor-isolated predicate-geometry compatibility improves validation-level
source reranking for geometry-checkable comparison relations.
```

The route-aware framework is therefore the paper's problem/method framing and
route map. Each relation family should use the evidence route that is meaningful
for that family, and abstain when the needed evidence is unavailable. It is not
yet a completed general reliable 3D relation framework result.

3D Scene Graph relation reliability should not be inferred from source
confidence alone or from a fixed semantic-geometry fusion. H002 separates:

```text
T_e = predicate / relation-family semantic content
G_e = predicate-independent geometry evidence
Z_e = source confidence, score, rank
C_e = compatibility(T_e, G_e)
Q_e = observability / evidence quality
```

The main validation score is:

```text
S2(e) = normalized_source_score(Z_e) * C_e
```

`C_e` is estimated from `T_e` and `G_e` before source score is used for final
reranking. This separation is the central leakage and design boundary.

Current experiment evidence supports the locked paper claim on
geometry-checkable comparison relations:

```text
relative_vertical = higher than / lower than
size_relative = bigger than / smaller than
```

Other relation families are kept in the framework as explicit routes rather
than forced into the same success claim:

| Route | Relation Types | Current Paper Role |
| --- | --- | --- |
| comparison compatibility | `higher/lower`, `bigger/smaller` | main quantitative success |
| geometry-only compatibility | `close by` / proximity | control or generality route |
| frame-aware directional | `left/right/front/behind` | candidate route; needs frame-risk handling |
| support/contact | `standing on`, `lying on`, `supported by` | hard-route failure taxonomy |
| observability-heavy | `attached to`, `hanging on`, `connected to`, `inside`, `cover` | future route requiring visual/mesh evidence and `p_obs` |
| semantic/structural | `part of`, `belonging to`, identity/symmetry labels | semantic/structural or abstain route |

## Allowed Claims

- H002 reranks VL-SAT/Open3DSG validation predictions with `S2_source_x_Ce`.
- Main quantitative evidence is on the official 3DSSG validation split.
- The framework claim is relation-aware evidence routing; the validated
  quantitative success claim is limited to geometry-checkable comparison
  relations.
- Open3DSG can be described as an open-vocabulary relation source, while
  quantitative Recall@K is computed after closed-vocabulary 3DSSG mapping.
- `Violation@K` is a custom H002 geometry-consistency metric.
- `p_obs/p_rel` is part of the framework as a selective-decision layer and
  stress-test result.
- `A1_source_x_G_only`, `A2_source_x_TG_concat`, the remaining
  experiment-stage gap review, and the
  normalization/no-route geometry sensitivity review are complete. No-route
  G-only sensitivity passed, and raw `source_score*C_e` preserves the
  improvement direction over S0 at K `{10,20,50}`. Rank-percentile
  normalization loses low-K recall, so normalization-invariant wording remains
  blocked.
- H002 is now judged natural and principled for the scoped comparison-route
  problem. Relation-aware evidence routing is constructed and partially
  validated, but a completed general reliable 3D relation framework remains
  blocked.
- The paper can describe the route-aware framework as a principled design and
  route taxonomy, but only the comparison route should be treated as the main
  quantitative success.
- `I4_calibrated_route_aware_source_x_Ce` can be reported as a
  secondary/candidate ablation; it is not the main score while family-wise
  regressions remain unresolved.

## Blocked Claims

- official 3DSSG test result
- SOTA or leaderboard result
- unconstrained open-set GT evaluation
- uniform improvement across every source/family/K cell
- all-relation reliable 3D relation framework as a completed result
- completed general reliable 3D relation framework
- normalization-invariant improvement
- support/contact solved as a success route
- calibrated `p_obs/p_rel` reliability is solved

## File Roles

| File | Role |
| --- | --- |
| `README.md` | workspace status, claim boundary, and source pointers |
| `outline.md` | section-level paper plan |
| `draft.md` | initial manuscript prose skeleton |
| `tables.md` | main/appendix table plan and exact artifact sources |
| `figures.md` | figure plan and source artifacts |
| `risk.md` | reviewer-risk register and mitigation plan |
| `route_framework.md` | relation-family route map, current evidence status, and expansion plan |

## Source Artifacts

Canonical H002 branch:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/
```

Main validation table:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/
```

Gap-resolution pack:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review/
```

p_obs / p_rel calibration-upgrade review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner/
```

Route-aware workspace sync:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_paper_workspace_initial_draft_and_figure_table_sync/
```

Source-reranking ablation expansion plan:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update/
```

Source-reranking ablation expansion implementation:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/
```

Source-reranking ablation result review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation/
```

Experiment-stage remaining-gap review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_experiment_stage_remaining_gap_review_after_ablation_result_review/
```

Normalization/no-route geometry sensitivity review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_experiment_stage_normalization_and_no_route_geometry_sensitivity_after_gap_review/
```

Paper claim-boundary lock:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_paper_claim_boundary_update_after_sensitivity_review/
```

Runtime code:

```text
experiments/H002_compatibility_routing/scripts/
```

Runtime metrics:

```text
experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
experiments/H002_compatibility_routing/source_reranking_ci/latest/
experiments/H002_compatibility_routing/source_reranking_sensitivity/latest/
```
