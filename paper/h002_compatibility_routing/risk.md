# H002 Reviewer Risk Register

## R1. Validation Is Not Official Test

Risk: reviewer may reject the result as validation-only.

Mitigation:

- state that main result uses official 3DSSG validation split
- do not claim official test, SOTA, or leaderboard
- explain that VL-SAT/Open3DSG comparisons are validation-level source
  reranking comparisons

## R2. Is This Just Geometry Filtering?

Risk: reviewer may read H002 as a post-hoc geometry rule.

Mitigation:

- emphasize `C_e = compatibility(T_e, G_e)`
- show `Z_e` is excluded from `C_e`
- include wrong-T and shuffled-C_e controls
- add `A1_source_x_G_only` to test whether the gain is just geometry-only
  reranking
- add `A2_source_x_TG_concat` to test whether the gain is explainable by plain
  `T_e/G_e` concatenation
- show leakage boundary figure

Status: `A1_source_x_G_only` and `A2_source_x_TG_concat` have now been
implemented in the Docker source-reranking path and passed the primary-route CI
gate. The remaining risk is paper wording: this supports the comparison route,
not all relation families.

Result review status: aggregate primary-route evidence supports S2 over A1/A2,
but family-wise Recall is mixed. Use this as a scoped mechanism result with
family-wise caveat, not as a completed framework result.

## R3. Open3DSG Open-Vocabulary Wording

Risk: open-vocabulary source may be confused with open-set GT evaluation.

Mitigation:

- wording: Open3DSG is an open-vocabulary source
- quantitative Recall@K uses closed-vocabulary 3DSSG mapping
- do not claim unconstrained open-set GT evaluation

## R4. Support/Contact Is Not Solved

Risk: support/contact hard route can weaken the broad reliability claim.

Mitigation:

- use support/contact as failure taxonomy
- do not put it as a success row
- frame it as evidence that hard routes require richer pose/contact/mesh and
  observability evidence

## R5. p_obs / p_rel Calibration Does Not Pass

Risk: framework includes p_obs/p_rel but calibration-upgrade result blocks a
solved reliability claim.

Mitigation:

- include p_obs/p_rel as selective-decision framework component
- present stress-test controls only
- explicitly state calibrated quantitative p_obs/p_rel is not claimed as solved
- keep calibrated ECE failure visible

## R6. Controls Look Too Strong Or Unnatural

Risk: wrong-T or shuffled controls may be seen as artificial.

Mitigation:

- use controls as mechanism checks, not standalone benchmark claims
- pair them with source reranking and CI
- explain each control's purpose: source copying, arbitrary geometry, predicate
  mismatch, and hidden-label leakage

## R7. Relation-Family Generality

Risk: gains may concentrate in relative comparison families.

Mitigation:

- state the claim as relation-family-aware compatibility routing
- explicitly say the current main success route is comparison compatibility
- include a route-readiness table
- keep support/contact as hard-route limitation
- avoid completed all-relation framework wording

Status: claim boundary is now locked to comparison-route source reranking.
Route-aware evidence routing may be described as the framework and route map,
but not as a completed general reliable 3D relation result.

## R8. Route-Aware Framework Looks Like Future Work

Risk: reviewer may say the general framework is mostly a roadmap because current
main success is limited to comparison relations.

Mitigation:

- separate two claims:
  current evidence claim = comparison-route reranking works;
  framework claim = relation families require different evidence routes
- use support/contact failure and p_obs/p_rel calibration boundary as evidence
  that fixed fusion is insufficient
- do not claim the future routes are solved
- list concrete route-specific experiments required for generalization

Status: partially mitigated. The framework is no longer used as a completed
result claim; it is used to justify the method form and to organize the
comparison success, geometry-only control, support/contact failure taxonomy,
and p_obs/p_rel selective-decision boundary.

Protocol freeze: `h002_relation_aware_framework_claim_hierarchy_and_route_protocol`
sets the route-aware framework as the paper's problem/method framing, while the
main quantitative evidence remains the validated comparison route. The paper
must not imply that diagnostic/future routes are solved.

Section sync status: `h002_route_aware_paper_section_sync_after_protocol_freeze`
is complete. The draft, outline, table captions, and figure captions now carry
the same hierarchy: framework claim first, validated comparison-route mechanism
second, route taxonomy as analysis, and unsolved routes as boundary/future
evidence.

## R9. Geometry-Only Ablation Is Route-Aware

Risk: reviewer may challenge the phrase "predicate-independent geometry" because
the current `G_e` implementation excludes predicate label and source score, but
`common_g_features` includes a `route_family` one-hot.

Mitigation:

- call `A1_source_x_G_only` a route-aware geometry-only ablation
- avoid saying it is a universal predicate-agnostic geometry encoder
- optionally add a no-route G-only sensitivity before final wording
- emphasize that S2 still beats this stronger route-aware geometry-only
  baseline on aggregate primary comparison-route metrics

Status: no-route G-only sensitivity has now run. Removing the route-family
one-hot does not explain the S2 gain on the current primary comparison route.
Keep the sensitivity in appendix/ablation support, and avoid overclaiming the
result beyond comparison relations.

## R10. Candidate-Pool Normalization

Risk: per-source and per-source-family minmax normalization is label-free but
uses the validation candidate score distribution, which can look transductive or
dataset-specific.

Mitigation:

- state that normalization is frozen and label-free
- do not tune thresholds, lambda, feature schema, or family scope on validation
  labels
- add sensitivity with train/dev bounds, rank-percentile normalization, or raw
  log-utility scoring before final paper promotion

Status: raw `source_score*C_e` preserves the improvement direction over S0 at K
`{10,20,50}`, but rank-percentile normalization loses low-K recall while
reducing violations. The main minmax score is still allowed as a selected
risk-utility score, but normalization-invariant wording is blocked.

## R11. General Framework Overclaim

Risk: the paper may overstate H002 as a completed general reliable 3D relation
framework.

Mitigation:

- state that relation-aware evidence routing is constructed and partially
  validated
- use comparison route as the main quantitative claim
- keep support/contact as failure taxonomy
- keep p_obs/p_rel as framework component unless calibrated result evidence
  passes
- use "toward" or "framework candidate" language for the general route-aware
  framework

Status: locked. Current paper wording must say the general reliable 3D relation
framework is not yet validated. The allowed claim is validation-level
comparison-route source reranking with a partially validated route-aware
framework.

Updated wording rule: say "relation-aware evidence routing framework with a
validated predicate-geometry compatibility route." Do not say "general reliable
3D relation framework is solved."

Section sync rule: captions and section prose must name `relative_vertical` and
`size_relative` as the validated quantitative scope whenever Recall@K or
Violation@K results are discussed.

## R12. Normalization Sensitivity Misread

Risk: reviewer may read the selected minmax score as tuned to the validation
candidate pool or as evidence of normalization-invariant improvement.

Mitigation:

- state that the selected score is label-free but candidate-pool normalized
- include raw-product sensitivity showing the improvement direction persists
- disclose rank-percentile low-K recall loss
- do not claim normalization-invariant improvement

Status: sensitivity review complete. Minmax main scoring is allowed with raw
product support and rank-percentile caveat.
