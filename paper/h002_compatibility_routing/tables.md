# H002 Table Plan

## Frozen Table Placement

Status:

```text
h002_relation_aware_framework_claim_hierarchy_and_route_protocol_ready = true
```

The table plan follows the frozen claim hierarchy:

- Main quantitative table: validated predicate-geometry compatibility route
  only, using `relative_vertical` and `size_relative`.
- Main/near-main ablation table: `S2_current_source_x_Ce` against
  source-only, route-aware geometry-only, no-route geometry-only, plain
  `T_e/G_e` concat, shuffled `C_e`, and wrong-T controls.
- Route-readiness table: framework/taxonomy evidence, not a solved-route result
  table.
- Appendix diagnostics: full family-wise CI, normalization sensitivity,
  support/contact failure taxonomy, p_obs/p_rel diagnostics, and route-specific
  failure cases.
- Candidate-only result: `I4_calibrated_route_aware_source_x_Ce` may appear as
  a secondary ablation/improvement-path row, not as the promoted main score.

## Caption-Ready Claim Sync

Use these captions unless later paper editing changes wording without changing
the claim boundary.

Main result caption:

```text
Validation-level source reranking on the official 3DSSG validation split for
geometry-checkable comparison relations. S0 ranks VL-SAT/Open3DSG predictions
by source confidence, while S2 reranks with source confidence multiplied by
predicate-geometry compatibility C_e. Open3DSG is an open-vocabulary relation
source, but Recall@K is evaluated after closed-vocabulary 3DSSG mapping.
Violation@K is a custom geometry-consistency metric. This table validates the
comparison route only and is not an official test, SOTA, or all-relation
benchmark.
```

Ablation/control caption:

```text
Ablations for the validated comparison route. Geometry-only and no-route
geometry-only controls test whether gains are explained by geometry alone;
plain T_e/G_e concatenation tests whether the factorized compatibility head is
needed; shuffled-C_e and wrong-T controls test whether the score depends on the
matched predicate-geometry pairing. I4 is reported only as a candidate
improvement-path ablation and is not the promoted main score.
```

Route-readiness caption:

```text
Route-readiness analysis for relation-aware evidence routing. The table maps
relation families to the evidence route needed to judge reliability. It is a
framework and boundary table, not a performance table over solved relation
families.
```

## Main Table: Scoped Validation Source Reranking

Source artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/
```

Caption boundary:

```text
Validation-level source-reranking result on the official 3DSSG validation split
for geometry-checkable comparison relations. We compare source-score ranking
with H002 compatibility-aware reranking on VL-SAT and Open3DSG validation
predictions. Open3DSG is used as an open-vocabulary source, while quantitative
Recall@K is computed after mapping to closed-vocabulary 3DSSG labels.
Violation@K is our custom geometry-consistency metric. This table is not an
official test, SOTA, or all-relation benchmark.
```

Main rows:

| K | S0 Recall@K | H002 Recall@K | Delta Recall@K | S0 Violation@K | H002 Violation@K | Delta Violation@K |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 0.344671 | 0.352608 | 0.007937 | 0.295181 | 0.054491 | -0.240690 |
| 10 | 0.471655 | 0.513605 | 0.041950 | 0.302201 | 0.072342 | -0.229859 |
| 20 | 0.642857 | 0.724490 | 0.081633 | 0.343578 | 0.100487 | -0.243091 |
| 50 | 0.849206 | 0.952381 | 0.103175 | 0.425197 | 0.165998 | -0.259199 |
| 100 | 0.995465 | 1.000000 | 0.004535 | 0.484792 | 0.341919 | -0.142873 |

Claim boundary: this table supports the validated mechanism claim for the
comparison-compatibility route (`relative_vertical + size_relative`). It is not
the whole relation-aware framework result, an all-relation reliability
benchmark, or a completed general reliable 3D relation framework result.

## Analysis Table: Route Readiness

This table should appear near the experiment setup or limitation section to
avoid overclaiming generality.

| Route | Relation Types | Paper Status | Required Next Evidence |
| --- | --- | --- | --- |
| comparison compatibility | `higher/lower`, `bigger/smaller` | locked main quantitative success | complete A1/A2/sensitivity caveats in caption |
| geometry-only compatibility | `close by`, proximity | control / generality route | source-level proximity reranking or route-control table |
| frame-aware directional | `left/right/front/behind` | candidate route | reference-frame robustness and source-level violation control |
| support/contact | `standing on`, `lying on`, `supported by` | hard-route failure taxonomy | richer contact/pose/mesh `G_e`; class-pair controlled target |
| attachment/containment/occlusion | `attached to`, `hanging on`, `inside`, `cover` | future observability route | real visual/mesh `Q_e` labels and p_obs route evaluation |
| semantic/structural | `part of`, `belonging to`, identity/symmetry | abstain or separate structural route | semantic/identity/symmetry-specific evidence |

Caption boundary: this is a route-assignment and claim-boundary table. It must
not be captioned as performance over all route types.

## Main/Appendix Table: Bootstrap CI

Source artifact:

```text
experiments/H002_compatibility_routing/source_reranking_ci/latest/
```

Use CI to avoid overstating K = 5 and K = 100 recall effects.

## Appendix Table: Controls

Source artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/control_table_compact.csv
```

Controls:

- C_e only
- source x shuffled C_e
- source x wrong-T C_e
- geometry-only diagnostic

Completed table fixes:

- absolute Recall@K / Violation@K for controls and ablations are available
- `source x geometry-only` and `source x T+G concat` are implemented
- family-wise CI is available as appendix-required caveat material
- no-route G-only and normalization sensitivity are available as
  appendix/ablation support

Latest freeze artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update/
```

Frozen additional score IDs:

| Score ID | Role |
| --- | --- |
| `A1_source_x_G_only` | tests whether the gain is just geometry-only reranking |
| `A2_source_x_TG_concat` | tests whether the gain is explainable by plain `T_e/G_e` concatenation |

The broader route-aware framework can be described as a design and route map,
but not as a completed all-route quantitative result.

`I4_calibrated_route_aware_source_x_Ce` placement: candidate/secondary
ablation only. It should not replace `S2_current_source_x_Ce` in the main
validation table unless a later family-wise review resolves the Open3DSG
`relative_vertical` regression cells.

Implementation status:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/
```

The implementation generated absolute metrics and bootstrap CI with validation
errors `0`. Result review, remaining-gap review, and normalization/no-route
geometry sensitivity are complete. Paper wording is allowed only under the
scoped comparison-route boundary.

Key primary weighted absolute rows:

| Score | K=20 Recall@K | K=20 Violation@K | Role |
| --- | ---: | ---: | --- |
| `S0_source_score` | 0.642857 | 0.343578 | source baseline |
| `A1_source_x_G_only` | 0.646259 | 0.327534 | geometry-only ablation |
| `A2_source_x_TG_concat` | 0.629252 | 0.330770 | plain concat ablation |
| `S2_source_x_Ce` | 0.724490 | 0.100487 | H002 primary score |

Selected CI deltas at K=20:

| Comparison | Delta Recall@20 95% CI | Delta Violation@20 95% CI |
| --- | --- | --- |
| `S2 - A1` | [0.047499, 0.110305] | [-0.234776, -0.219345] |
| `S2 - A2` | [0.064715, 0.131210] | [-0.238861, -0.222207] |

Experiment-stage placement decision:

- Compact ablation table: main or near-main candidate under the scoped
  comparison-route claim.
- Full ablation/control table: appendix required.
- Family-wise caveat table: appendix required with main-text caveat because
  Violation reduction is stable but Recall gains are not uniformly significant
  in every source/family/K cell.

## Analysis Table: p_obs / p_rel

Source artifacts:

```text
experiments/H002_compatibility_routing/pobs_prel_evaluation/latest/
experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest/
```

Paper role:

- include as selective-decision framework evidence
- do not claim calibrated quantitative p_obs/p_rel reliability is solved

Current key numbers:

| Metric | Value | Claim Use |
| --- | ---: | --- |
| p_rel AUROC | 0.723800 | discrimination remains useful |
| p_rel raw ECE@10 | 0.171030 | calibration not sufficient |
| p_rel calibrated ECE@10 | 0.223458 | calibrated claim blocked |
| decision macro-F1 | 0.778072 | stress-test support |
| missing-control abstain rate | 1.000000 | selective stress-test support |

## Analysis Table: Support/Contact Failure Taxonomy

Source artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review/support_contact_failure_taxonomy.csv
```

Paper role: failure analysis, not success evidence.

## Appendix Table: Normalization And No-Route Sensitivity

Source artifact:

```text
experiments/H002_compatibility_routing/source_reranking_sensitivity/latest/
```

Paper role:

- defend that S2 is not explained by route-family one-hot geometry-only
  features
- show raw `source_score*C_e` preserves the improvement direction
- disclose that rank-percentile normalization reduces Violation@K but loses
  low-K Recall@K

Caption boundary: this table supports the selected minmax risk-utility score
with sensitivity evidence. It must not be used to claim normalization-invariant
improvement.
