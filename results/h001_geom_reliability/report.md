# H001 / RelCompat3D Geometry Reliability Report

Last updated: 2026-07-20 KST

This is the compact paper-facing full-validation report for RelCompat3D. The
current main result uses the strict training-only transformation-consistent
compatibility model and family-aware re-ranking across VL-SAT,
Open3DSG, and SGFN on the same 548-context 3DSSG target. Historical 127-scan outputs
and optional family-expansion artifacts are not main evidence unless explicitly
promoted.

## Metric Scope

Main evaluated families:

| family | predicate labels | GT denominator |
| --- | --- | ---: |
| `proximity` | `close by` | 1,766 |
| `relative_vertical` | `higher than`, `lower than` | 390 |
| `support_contact` | `lying on`, `standing on`, `supported by` | 1,816 |
| total | main H001 geometry-checkable scope | 3,972 |

Metric definitions:

- `R@K`: exact-label relation recall over the 3,972 in-scope GT relations.
- `Violation@K` / `V@K`: fraction of selected top-K predictions whose
  associated geometry verifier status is `violated`; the primary denominator
  includes satisfied, uncertain, and violated predictions.
- Uncertainty sensitivity additionally reports decidable-only V, uncertainty
  rate, pessimistic V that counts uncertainty as violation, and status coverage.
- `dR` and `dV`: absolute point-estimate deltas against Source score.
  Bootstrap artifacts are retained as stability checks, but direct
  interval notation is not used in the paper-facing summary.
- Top-K grid: `K = {5, 10, 20, 50, 100}`. `K=1` is not a paper metric.
- Relation-wise tables below report recall. The current main metrics artifact
  materializes violation rate at source/condition/top-K level, not by predicate
  label; do not read the relation-wise recall tables as relation-wise violation
  tables.

## Scoring Conditions

| condition | formula / rule | paper role |
| --- | --- | --- |
| Source score | source model relation score | source baseline |
| RelCompat3D-Linear | family-specific linear compatibility product within proximity/vertical; source order for support/contact | proposed linear capacity |
| RelCompat3D-MLP | shared compact nonlinear compatibility product under the same family-aware ranking | proposed nonlinear capacity |
| Product (all families) | `source_score * transformation-consistent compatibility` applied to every family | all-family ablation |
| Rank-average | mean of within-context source-score and compatibility percentile ranks within proximity/vertical families | scale-robust comparator |
| Reciprocal-rank fusion | reciprocal-rank fusion with fixed constant 60 within proximity/vertical families | strong comparator |
| Pooled-calibrator ablation | `source_score * pooled_compatibility` | family-conditioning ablation |
| Hard geometry filter | keep/rank rule-supported point-subtype evidence | zero-violation diagnostic, not default |
| Compatibility-only | projected compatibility only | no-source-score control; not true `G`-only |
| Distance-only | inverse 3D distance only, without source score | distance-only control |
| Wrong predicate | product after a fixed predicate substitution | predicate--geometry interaction control |
| Wrong-pair geometry | product with a deterministic within-context same-predicate donor | object-pair identity control |
| Shuffled geometry | product with a deterministic source/predicate-stream donor | geometry identity control |
| Endpoint swap, label fixed | product after the applicable proximity/vertical geometry swap while retaining the label | directional/symmetry falsification control |

For reproducibility, the matched-procedure comparator keys are `routed_product`,
`routed_rank_average`, `routed_rrf`, and `routed_matched_mlp` under
`routed_comparators_v1/`. Unrestricted keys remain `structured_product`,
`structured_rank_average`, `structured_rrf_c60`, `pooled_product`, and
`hard_rule_filter`. The legacy condition names below are historical
implementation identifiers, not current manuscript terminology. No fusion
formula is universally dominant.

## Primary Family-Aware Result

The active Docker evaluation is
`experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/`. The
primary `routed_comparators/` result preserves the source family sequence and
support/contact selection exactly at every K, while ordering
proximity/vertical candidates by the transformation-consistent product.
Sibling directories own all-family comparisons, controls, intervals,
uncertainty, surface audit, and runtime. The structured model SHA256 is
`08cd309bbacead29dd9f76cd3845e3625de72423e45c242e33114ca686e2c01c`;
the strict model SHA256 is
`5b6423d0825395990b00663fc0004799268d87c9480493895d01d1c3ef9c3218`.

| Source | Source | routed product | routed MLP | routed rank-average | routed RRF | unrestricted product | pooled product |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VL-SAT | .9635/.0476 | .9658/.0295 | .9650/.0296 | .9700/.0225 | .9710/.0247 | .9688/.0325 | .9690/.0387 |
| Open3DSG public/full target | .5111/.1242 | .5685/.0324 | .5989/.0371 | .5400/.0549 | .5468/.0780 | .6005/.0331 | .6402/.0743 |
| SGFN | .9235/.0630 | .9303/.0350 | .9288/.0350 | .9280/.0259 | .8774/.0302 | .9418/.0372 | .9413/.0464 |

The routed K=100 Recall/Violation deltas versus Source score are
`+.00227/-.01816`, `+.05740/-.09176`, and `+.00680/-.02796` for
VL-SAT, Open3DSG, and SGFN. Their paired 95% intervals are respectively
`[+.00048,+.00492]/[-.01994,-.01656]`,
`[+.04628,+.06856]/[-.09631,-.08727]`, and
`[+.00431,+.00980]/[-.03043,-.02566]`. All K=`{5,10,20,50,100}` rows
are in the routing and synchronized comparator artifacts.

Factor interpretation: `T_e` is predicate semantics, `a_e` selects the family
head/procedure, `G_e` contains predicate-independent same-pair geometry
measurements, `Z_e` is the source relation score, and
`C_e=sigmoid(h_a(Phi(T_e,G_e)))` a bounded score for the constructed
GT-positive/counterfactual target. It is not a probability of physical
validity. Current compatibility models exclude `Z_e` and predictor identity,
but include `T_e` and predicate-aligned `T_e x G_e` features. The active heads
do not include a constant family indicator. Hence
the legacy `control_p_geom_valid_only` isolates removal of `Z_e`; it is not a
predicate-independent geometry-only calibrator.

Dependence sensitivity resamples the 157 scans, carrying every one of the 548
contexts from each sampled scan together. At K=100, routed-minus-source
Recall/Violation intervals are `+.0023 [.0005,.0049] / -.0182
[-.0199,-.0166]` for VL-SAT, `+.0574 [.0463,.0686] / -.0918
[-.0963,-.0873]` for Open3DSG, and `+.0068 [.0043,.0098] / -.0280
[-.0304,-.0257]` for SGFN. Rankings and point estimates are unchanged.

## Two RelCompat3D Compatibility Capacities

`experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/routed_comparators/`
applies `RelCompat3D-Linear`, `RelCompat3D-MLP`, rank-average, and RRF through
the identical public/full family-aware ranking procedure. The two proposed
capacities share constructed targets, linked-pair supervision, transformation
averaging, product utility, family composition, support/contact selections,
official contexts, and scan-cluster indices. At K=50:

| Predictor | RelCompat3D-Linear R/V | RelCompat3D-MLP R/V |
| --- | ---: | ---: |
| VL-SAT | .9277/.0197 | .9272/.0189 |
| Open3DSG | .4418/.0342 | .4670/.0413 |
| SGFN | .7450/.0263 | .7457/.0258 |

The nonlinear capacity does not jointly dominate: its Open3DSG Recall gain
relative to Linear accompanies a Violation increase. Both capacities weakly
improve Source point estimates in all reported predictor--budget cells. A
separate SGFN-specific
exact-label nonlinear rescorer uses stronger source-specific supervision and is
reported as such; it is not a supervision-matched replacement.

The MLP matched-control summary is
`no_family_indicator_v1/evaluation/mlp_ablation/summary.json` (SHA256
`83e85bbb9c940644ece4d0322db6ea2f7c98dccfbd11a62ff1efbf47295484ce`).
Wrong-predicate, wrong-pair, shuffled-geometry, fixed-label swap, distance-only,
and compatibility-only conditions are reported at K=50/100 beside their Linear
counterparts in the supplement. The MLP point/mesh/consensus audit is
`no_family_indicator_v1/evaluation/mlp_surface_audit/summary.json` (SHA256
`c77c94024fe9de09afbe9ad418f97945a114087cb0199a00079b77df83c3bd55`);
its K=50 consensus changes versus Source are `-.0238`, `-.3712`, and `-.0393`
for VL-SAT, Open3DSG, and SGFN, and all paired scan-cluster intervals exclude
zero.

## Counterfactual-Policy Sensitivity

`experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/counterfactual_sensitivity/`
contains nine one-factor-at-a-time train-only refits: the default; proximity
threshold 2.0/3.0 versus 2.5; vertical absolute margin 0.20/0.30 m versus
0.25 m; negative cap 1/4 versus 2; and pairwise-loss weight .125/.5 versus
.25. Every condition recomputes targets and normalization using only the
1,061 training scans, uses the 117-scan internal-development split for ordering
diagnostics, and excludes all 157 final-validation scans from fitting.

The default model and all three-source K=50/100 points are bit-exact to the
main result. Linked-positive ordering accuracy is 1.000 for every variant.
Across conditions, maximum absolute changes from default are `.0020` Recall
and `.0011` V at K=50, and `.0035` Recall and `.0020` V at K=100. Every variant
preserves positive Recall and negative V point deltas versus source scoring for
VL-SAT, Open3DSG, and SGFN at both budgets. These results reduce dependence on
one engineered threshold/cap/weight setting; they do not constitute an
independent physical-validity reference.

## Open3DSG Coverage Sensitivity

The public preprocessing path produces predictions for 533 contexts because 15
official contexts fail its object-to-image visibility gate. The main Open3DSG
route evaluates those public predictions on the label-independent official
548-context universe and assigns no predictions to missing contexts. The
K=100 sensitivity is:

| Route | Contexts | Source R/V | Routed R/V |
| --- | ---: | ---: | ---: |
| public eligible | 533 | .5206/.1242 | .5791/.0324 |
| public/full target | 548 | .5111/.1242 | .5685/.0324 |
| recovered/full target | 548 | .5161/.1242 | .5735/.0332 |

The conclusion is stable across routes. The recovered route is a coverage
sensitivity, not the unmodified public pipeline.

## Fixed-Model Ablations and Falsification Controls

The Docker-frozen evaluation is
`experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/routed_ablation/`.
It uses the same locked structured-model SHA256
`08cd309bbacead29dd9f76cd3845e3625de72423e45c242e33114ca686e2c01c`,
the public/full 548-context target and 3,972-relation denominator, and the same
family-aware ranking procedure as the primary method. Every input, context,
primary-point, family-composition, support/contact-order, donor, and
source-exclusion validation passes.

| Source | Condition | R@50 | V@50 | R@100 | V@100 |
| --- | --- | ---: | ---: | ---: | ---: |
| Open3DSG | RelCompat3D | .4418 | .0342 | .5685 | .0324 |
| Open3DSG | Wrong predicate | .4265 | .2200 | .5342 | .2098 |
| Open3DSG | Wrong-pair geometry | .3852 | .0848 | .4927 | .0835 |
| Open3DSG | Shuffled geometry | .3844 | .1293 | .4864 | .1243 |
| Open3DSG | Endpoint swap, label fixed | .4267 | .2200 | .5368 | .2098 |
| Open3DSG | Distance-only | .5116 | .0824 | .6322 | .0955 |
| Open3DSG | Compatibility-only in routed families | .4207 | .0342 | .5672 | .0324 |
| VL-SAT | RelCompat3D | .9277 | .0197 | .9658 | .0295 |
| VL-SAT | Wrong predicate | .9043 | .0498 | .9481 | .0796 |
| VL-SAT | Wrong-pair geometry | .9053 | .0261 | .9494 | .0473 |
| VL-SAT | Shuffled geometry | .8917 | .0306 | .9411 | .0560 |
| VL-SAT | Endpoint swap, label fixed | .9043 | .0498 | .9481 | .0796 |
| VL-SAT | Distance-only | .8190 | .0534 | .8980 | .0809 |
| VL-SAT | Compatibility-only in routed families | .6765 | .0161 | .8409 | .0203 |
| SGFN | RelCompat3D | .7450 | .0263 | .9303 | .0350 |
| SGFN | Wrong predicate | .7158 | .0942 | .8993 | .1299 |
| SGFN | Wrong-pair geometry | .7155 | .0399 | .8807 | .0665 |
| SGFN | Shuffled geometry | .7059 | .0473 | .8683 | .0836 |
| SGFN | Endpoint swap, label fixed | .7158 | .0942 | .9003 | .1298 |
| SGFN | Distance-only | .6319 | .1000 | .8406 | .1266 |
| SGFN | Compatibility-only in routed families | .5279 | .0232 | .7064 | .0230 |

The geometry corruptions break the joint operating point. Removing the source
relation score from the re-ranked families usually lowers Violation further but
loses substantial Recall, so compatibility cannot replace the source relation
score.
Distance-only can increase Recall by aggressively reordering proximity rows,
but its substantially higher Violation rejects a simple distance heuristic as
the explanation. Support/contact order and selection are unchanged in every
condition. The earlier unrestricted/recovered result under `evaluation/` is
retained only as a supplemental mechanism and coverage sensitivity.

## Source Artifacts

| source | role | predictions | metric artifact |
| --- | --- | ---: | --- |
| VL-SAT | controlled closed-set anchor | 957,008 | `experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics_k_sweep/metrics.json` |
| Open3DSG | public-pipeline/full-target relation-source case study | 690,924 | `experiments/H001_geom_reliability/open3dsg_official_route_v1/evaluation/` |
| SGFN full_l160 | additional exact-label source evaluation | 957,008 | `experiments/H001_geom_reliability/sources/sgfn/confirmatory_metrics/summary.json` |

## Historical Framework-Level K=100 Comparison (Pre-Promotion)

This table preserves the 2026-07-10 continuity comparison. It is superseded
for current paper numbers by **Promoted Structured Main Result** above.

| source | condition | R@100 | verifier V@100 | role |
| --- | --- | ---: | ---: | --- |
| VL-SAT | semantic | 0.9635 | 0.0476 | source baseline |
| VL-SAT | calibrated product | 0.9683 | 0.0333 | soft instantiation |
| VL-SAT | rank-average | 0.9597 | 0.0259 | scale-robust instantiation |
| VL-SAT | RRF | 0.9698 | 0.0251 | strong comparator |
| Open3DSG | semantic | 0.5161 | 0.1242 | source baseline |
| Open3DSG | calibrated product | 0.6047 | 0.0341 | soft instantiation |
| Open3DSG | rank-average | 0.6052 | 0.0532 | scale-robust instantiation |
| Open3DSG | RRF | 0.6196 | 0.0789 | strong comparator |
| SGFN | semantic | 0.9235 | 0.0630 | fresh source baseline |
| SGFN | calibrated product | 0.9416 | 0.0381 | soft instantiation; joint criterion satisfied |
| SGFN | rank-average | 0.9476 | 0.0277 | soft instantiation; joint criterion satisfied vs product |
| SGFN | RRF | 0.9192 | 0.0284 | lower V but fails recall guardrail vs product |

The SGFN result supports the framework-level claim that incorporating calibrated
same-pair geometry can improve the aggregate recall/violation operating point
under more than one evaluated fusion form. It does not establish formula
dominance, family-uniform improvement, or independent human physical validity.

Bootstrap stability artifacts for the same K grid are available at
`experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/bootstrap_ci_k_sweep/summary.md`.

## External-Dataset Transfer Boundary

The current final RelCompat3D model and family-aware ranking rule were evaluated without
ReplicaSSG fit rows or target-specific hyperparameters on the regenerated
4,293-candidate FROSS execution. The official test target was already inspected
in earlier transfer development, so this is a cross-dataset benchmark
evaluation rather than untouched confirmation.

| K | Source R/V | Routed product R/V | dR | dV |
| ---: | ---: | ---: | ---: | ---: |
| 5 | .04651/.05455 | .06977/.01818 | +.02326 | -.03636 |
| 10 | .07558/.08182 | .14535/.02727 | +.06977 | -.05455 |
| 20 | .14535/.12727 | .22093/.03636 | +.07558 | -.09091 |
| 50 | .26163/.13284 | .31395/.09041 | +.05233 | -.04244 |
| 100 | .35465/.19674 | .35465/.19578 | .00000 | -.00096 |

Paired scene-bootstrap intervals support joint routed-product improvement at
K=10 and K=50. K=20 is positive with its Recall interval touching zero, K=5 is
inconclusive, and the K=100 product gate fails because its dV CI is
`[-.00288,.00000]`. Applying the same fixed guardrail to the pre-frozen routed
rank diagnostic at K=100 gives
dR CI `[-.00476,.06714]` and dV CI `[-.19182,-.11015]`; the global version
instead loses Recall through cross-family displacement. This is positive
framework behavior on an external dataset, but not an unbiased dataset-level
generalization estimate or a promotion of rank-average to the primary method.

The failure decomposition is concrete: 86.28% of source scores are zero;
19.20% of external feature cells exceed three train-standardized deviations;
only 76/172 GT relations have candidate support; support/contact has no exact
mapping; and compatibility aligns external verifier satisfaction (AUC .9460)
more strongly than exact labels (AUC .6686). All model, input, score, and
execution checks pass; the untouched-confirmation check is intentionally false
because the target was previously observed.

Canonical active-method compact artifacts:

- `experiments/H001_geom_reliability/no_family_indicator_v1/protocols/external_transfer.json`
- `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/external_transfer/summary.json`
- `experiments/H001_geom_reliability/sources/replicassg/development_v2/evaluation/summary.json`
- `experiments/H001_geom_reliability/sources/replicassg/development_v2/cross_source_evaluation/summary.json`

## Historical Uncertainty Sensitivity (Pre-Promotion)

The Docker-frozen diagnostic at
`experiments/H001_geom_reliability/uncertainty_sensitivity/frozen_v1/` keeps
every score, rank, family, and verifier status unchanged. At K=100, the family
product changes decidable-only V by `-0.0244`, `-0.1671`, and `-0.0428` on
VL-SAT, Open3DSG, and SGFN. It also lowers uncertainty rate on all three
sources. Pessimistic V changes by `-0.0480`, `-0.2526`, and `-0.0586`; all
paired 95% CIs exclude zero. The primary V improvement therefore does not rely
on promoting uncertain rows.

## Non-Submission LLM Proxy Diagnostic

The separate non-submission workspace includes two locked blinded Codex LLM passes over
the same 488-item public-evidence queue. Both passes exclude source identity,
semantic scores/ranks, verifier outputs, GT, and private sampling strata.
Pass 1 labels valid/invalid/ambiguous/unobservable as `180/185/120/3`; Pass 2
labels them `175/178/132/3`. They agree on `438/488` rows (`89.75%`), with
four-class kappa `0.845`; all `334/334` jointly binary rows have the same
polarity and all 50 disagreements involve the ambiguous boundary.

Paper-facing naming is `two blinded Codex LLM proxy annotation passes` or
`LLM-based physical-validity proxy audit`. This is automatic-evaluator
stability evidence, not two human annotators, independent-human agreement, or
physical-validity ground truth. The protocol exposes raw evidence paths,
rubric, confidence, reason codes, model identity, and disagreement sheets.

This use has clear precedent: LLM labels and judges are used in
[PNAS 2023 text annotation](https://doi.org/10.1073/pnas.2305016120),
[G-Eval/EMNLP 2023](https://aclanthology.org/2023.emnlp-main.153/),
[MT-Bench](https://arxiv.org/abs/2306.05685),
[AnnoLLM/NAACL 2024](https://aclanthology.org/2024.naacl-industry.15/), and the
closest multimodal example,
[GPT-4V evaluation of text-to-3D generation at CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Wu_GPT-4Vision_is_a_Human-Aligned_Evaluator_for_Text-to-3D_Generation_CVPR_2024_paper.html).
Those studies validate LLM judgments against trained/crowd/expert labels or
human preferences. Accordingly, H001 keeps the Codex audit diagnostic until a
human-alignment subset or independent human audit is available.

Before human collection, the frozen annotation addendum now defines
`high/medium/low` confidence and makes `evidence_sufficient=false` equivalent
to an `unobservable` evidence failure. A shared Docker validator requires
adjudication for the union of label disagreements, either low-confidence row,
and either ambiguous/unobservable label. The Human V evaluator uses this same
gate. A separate locked Codex--human evaluator will compare each unchanged
Codex pass against the final adjudicated human reference using four-class,
binary, family-wise, coverage, and ordinal-confidence diagnostics. Empty-sheet
dry runs correctly remain non-reportable and produce no human result.

## Historical Continuity Results (Pre-Promotion)

The detailed source-local tables below use the former family-calibrated model
and legacy condition keys. They remain useful for provenance and predicate-level
diagnostics but are not the promoted structured-main result.

### VL-SAT

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Source score | 0.4194 | 0.6322 | 0.8074 | 0.9272 | 0.9635 | 0.0029 | 0.0082 | 0.0142 | 0.0268 | 0.0476 |
| Family-calibrated product | 0.4162 | 0.6309 | 0.8087 | 0.9288 | 0.9683 | 0.0011 | 0.0051 | 0.0109 | 0.0206 | 0.0333 |
| Pooled-calibrator ablation | 0.4154 | 0.6322 | 0.8107 | 0.9305 | 0.9688 | 0.0015 | 0.0071 | 0.0120 | 0.0229 | 0.0404 |
| Hard geometry filter | 0.4197 | 0.6317 | 0.8074 | 0.9257 | 0.9627 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Interpretation: VL-SAT is already near ceiling at K=50/100, so the recall
change is small. The main effect is reliability: Family-calibrated product
reduces V@100 from 0.0476 to 0.0333 while slightly improving R@100 from 0.9635
to 0.9683. At low K, R@5/R@10 is essentially flat to slightly lower, while
V@5/V@10 decreases.

### Open3DSG

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Source score | 0.0368 | 0.1002 | 0.1991 | 0.4096 | 0.5161 | 0.5131 | 0.3255 | 0.2088 | 0.1386 | 0.1242 |
| Family-calibrated product | 0.0984 | 0.1921 | 0.3291 | 0.4658 | 0.6047 | 0.0420 | 0.0482 | 0.0441 | 0.0286 | 0.0341 |
| Pooled-calibrator ablation | 0.0826 | 0.1581 | 0.2603 | 0.3975 | 0.5723 | 0.0628 | 0.0699 | 0.0654 | 0.0606 | 0.0811 |
| Hard geometry filter | 0.0707 | 0.1314 | 0.2422 | 0.4295 | 0.5368 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Interpretation: Open3DSG has much larger semantic-geometry inconsistency in
the source ranking. Family-calibrated product improves recall at every K and
substantially reduces violations, especially at low K. The largest practical
effect is top-rank reliability: V@5 drops from 0.5131 to 0.0420 while R@5
increases from 0.0368 to 0.0984.

Open3DSG selected predictions are slightly below `548 * K` for K=20/50/100
because some validation contexts have fewer available in-scope predictions
after the recovery/filtering route. The metrics use the actual selected-row
denominator recorded in the JSON.

## Bootstrap Stability Check

Bootstrap uses 1,000 subgraph-resampling samples with seed `20260526`. The raw
bootstrap summaries stay in the experiment artifact. The paper-facing summary
reports only point-estimate deltas and uses bootstrap as a stability check.

### `family_conditional_risk` vs `semantic_only`

| source | K | dR pp | dV pp | paper-facing reading |
| --- | ---: | ---: | ---: | --- |
| VL-SAT | 5 | -0.33 | -0.18 | low-K recall is essentially flat; violations decrease. |
| VL-SAT | 10 | -0.13 | -0.31 | low-K recall is essentially flat; violations decrease. |
| VL-SAT | 20 | +0.13 | -0.34 | small recall shift; violations decrease. |
| VL-SAT | 50 | +0.15 | -0.61 | small positive recall shift; violations decrease. |
| VL-SAT | 100 | +0.48 | -1.43 | controlled-anchor improvement is small but favorable. |
| Open3DSG | 5 | +6.17 | -47.12 | strong top-rank reliability gain. |
| Open3DSG | 10 | +9.19 | -27.74 | strong low-K reliability gain. |
| Open3DSG | 20 | +12.99 | -16.47 | strongest recall gain with large violation reduction. |
| Open3DSG | 50 | +5.61 | -11.00 | positive recall shift with lower violations. |
| Open3DSG | 100 | +8.86 | -9.01 | positive recall shift with lower violations. |

Interpretation: Open3DSG shows a strong effect across all K. VL-SAT is already
near ceiling, so the recall deltas are small; the more relevant signal is the
consistent violation reduction from K=10 upward. Direct bootstrap ranges are
kept out of the paper-facing table to match the closest 3DSSG reporting style.

## Relation-Family Recall

### VL-SAT

| family | GT denom | condition | R@5 | R@10 | R@20 | R@50 | R@100 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `proximity` | 1766 | `semantic_only` | 0.6104 | 0.8143 | 0.9145 | 0.9773 | 1.0000 |
| `proximity` | 1766 | `family_conditional_risk` | 0.6110 | 0.8171 | 0.9196 | 0.9790 | 1.0000 |
| `relative_vertical` | 390 | `semantic_only` | 0.5308 | 0.6872 | 0.8795 | 0.9897 | 1.0000 |
| `relative_vertical` | 390 | `family_conditional_risk` | 0.5282 | 0.6846 | 0.8821 | 0.9897 | 1.0000 |
| `support_contact` | 1816 | `semantic_only` | 0.7291 | 0.8805 | 0.9317 | 0.9769 | 0.9879 |
| `support_contact` | 1816 | `family_conditional_risk` | 0.7252 | 0.8860 | 0.9444 | 0.9807 | 0.9928 |

### Open3DSG

| family | GT denom | condition | R@5 | R@10 | R@20 | R@50 | R@100 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `proximity` | 1766 | `semantic_only` | 0.1127 | 0.2022 | 0.3635 | 0.6359 | 0.8154 |
| `proximity` | 1766 | `family_conditional_risk` | 0.1971 | 0.3097 | 0.4530 | 0.7905 | 0.8154 |
| `relative_vertical` | 390 | `semantic_only` | 0.0051 | 0.0128 | 0.0923 | 0.3590 | 0.5667 |
| `relative_vertical` | 390 | `family_conditional_risk` | 0.0385 | 0.0923 | 0.2487 | 0.5026 | 0.5744 |
| `support_contact` | 1816 | `semantic_only` | 0.2621 | 0.3888 | 0.5716 | 0.7137 | 0.7830 |
| `support_contact` | 1816 | `family_conditional_risk` | 0.2996 | 0.4460 | 0.5887 | 0.7555 | 0.8315 |

Interpretation: VL-SAT relation-family recall is already saturated by K=50/100,
with the clearest family-level improvement in `support_contact`. Open3DSG shows
meaningful gains across all three families. The largest relative changes are in
`relative_vertical` at low/mid K and `proximity` at K=50.

## Predicate-Label Recall

### VL-SAT

| relation label | GT denom | condition | R@5 | R@10 | R@20 | R@50 | R@100 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `close by` | 1766 | `semantic_only` | 0.6104 | 0.8143 | 0.9145 | 0.9773 | 1.0000 |
| `close by` | 1766 | `family_conditional_risk` | 0.6110 | 0.8171 | 0.9196 | 0.9790 | 1.0000 |
| `higher than` | 195 | `semantic_only` | 0.7077 | 0.8923 | 0.9692 | 1.0000 | 1.0000 |
| `higher than` | 195 | `family_conditional_risk` | 0.7026 | 0.8923 | 0.9744 | 1.0000 | 1.0000 |
| `lower than` | 195 | `semantic_only` | 0.6872 | 0.8872 | 0.9795 | 1.0000 | 1.0000 |
| `lower than` | 195 | `family_conditional_risk` | 0.6923 | 0.8872 | 0.9795 | 1.0000 | 1.0000 |
| `lying on` | 232 | `semantic_only` | 0.9741 | 0.9914 | 1.0000 | 1.0000 | 1.0000 |
| `lying on` | 232 | `family_conditional_risk` | 0.9741 | 0.9957 | 1.0000 | 1.0000 | 1.0000 |
| `standing on` | 1357 | `semantic_only` | 0.9005 | 0.9867 | 0.9956 | 1.0000 | 1.0000 |
| `standing on` | 1357 | `family_conditional_risk` | 0.9064 | 0.9882 | 0.9971 | 1.0000 | 1.0000 |
| `supported by` | 227 | `semantic_only` | 0.5242 | 0.7004 | 0.8502 | 0.9339 | 0.9515 |
| `supported by` | 227 | `family_conditional_risk` | 0.5771 | 0.7269 | 0.8590 | 0.9515 | 0.9515 |

### Open3DSG

| relation label | GT denom | condition | R@5 | R@10 | R@20 | R@50 | R@100 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `close by` | 1766 | `semantic_only` | 0.1127 | 0.2022 | 0.3635 | 0.6359 | 0.8154 |
| `close by` | 1766 | `family_conditional_risk` | 0.1971 | 0.3097 | 0.4530 | 0.7905 | 0.8154 |
| `higher than` | 195 | `semantic_only` | 0.0154 | 0.0410 | 0.2000 | 0.5538 | 0.5744 |
| `higher than` | 195 | `family_conditional_risk` | 0.1385 | 0.2872 | 0.5436 | 0.5744 | 0.5744 |
| `lower than` | 195 | `semantic_only` | 0.0462 | 0.1282 | 0.2974 | 0.5744 | 0.5744 |
| `lower than` | 195 | `family_conditional_risk` | 0.0410 | 0.2513 | 0.4410 | 0.5744 | 0.5744 |
| `lying on` | 232 | `semantic_only` | 0.1983 | 0.4310 | 0.6853 | 0.8405 | 0.8448 |
| `lying on` | 232 | `family_conditional_risk` | 0.4914 | 0.7112 | 0.8017 | 0.8448 | 0.8448 |
| `standing on` | 1357 | `semantic_only` | 0.4171 | 0.6382 | 0.7708 | 0.8394 | 0.8578 |
| `standing on` | 1357 | `family_conditional_risk` | 0.4812 | 0.6831 | 0.8165 | 0.8578 | 0.8578 |
| `supported by` | 227 | `semantic_only` | 0.0749 | 0.1498 | 0.3260 | 0.5815 | 0.7093 |
| `supported by` | 227 | `family_conditional_risk` | 0.1938 | 0.3172 | 0.5463 | 0.7004 | 0.7093 |

Interpretation: predicate-label recall supports the same source-level story.
VL-SAT is near saturation for most labels, but `supported by` improves at
K=5/10/20/50. Open3DSG benefits most where semantic-only ranking is unreliable:
`higher than`, `lying on`, `supported by`, and `close by` show clear low/mid-K
gains.

## Controls

### VL-SAT K=100 Control Summary

| condition | R@100 | V@100 | role |
| --- | ---: | ---: | --- |
| `semantic_only` | 0.9635 | 0.0476 | source baseline |
| `family_conditional_risk` | 0.9683 | 0.0333 | calibrated-product instantiation |
| `control_p_geom_valid_only` | 0.5184 | 0.0711 | calibrator-only/no-`Z` control |
| `control_distance_only` | 0.5554 | 0.0981 | distance-only control |
| `control_shuffled_geometry` | 0.9494 | 0.0588 | geometry identity corruption |
| `control_wrong_pair_geometry` | 0.9529 | 0.0601 | wrong-pair geometry corruption |

### Open3DSG K=100 Control Summary

| condition | R@100 | V@100 | role |
| --- | ---: | ---: | --- |
| `semantic_only` | 0.5161 | 0.1242 | source baseline |
| `family_conditional_risk` | 0.6047 | 0.0341 | calibrated-product instantiation |
| `control_p_geom_valid_only` | 0.5116 | 0.0865 | calibrator-only/no-`Z` control |
| `control_distance_only` | 0.5038 | 0.1071 | distance-only control |
| `control_shuffled_geometry` | 0.2543 | 0.1998 | geometry identity corruption |
| `control_wrong_pair_geometry` | 0.2331 | 0.1985 | wrong-pair geometry corruption |

Control interpretation: calibrator-only and distance-only controls do not
explain the main result because they lose too much recall or retain high violation.
Shuffled and wrong-pair geometry controls are worse than the identity-preserving
RelCompat3D score, supporting the claim that the method depends on the correct
object-pair geometry join rather than a generic family prior. A frozen true
`G`-only factor baseline is now available in the separate fresh-source factor
diagnostic below; it is not retroactively part of these main VL-SAT/Open3DSG
results.

## Strict Train-only Reconstruction On Official 3DSSG/SGPN

`train_only_reestablishment_v1` rebuilds RelCompat3D behind an exact
1,061-train / 117-internal-dev / 157-final-validation firewall. All
normalization, imputation, counterfactual construction, and weights come from
train rows only. Internal-dev may only accept or reject the pre-frozen default;
it cannot change the formula, family set, K grid, denominator, or controls.
After the internal-dev acceptance criterion was met, model and score hashes were frozen
before final evaluation.

| split | condition | R@100 | dR vs semantic (95% paired CI) | verifier V@100 | dV vs semantic (95% paired CI) |
| --- | --- | ---: | --- | ---: | --- |
| internal-dev, 354 contexts / 2,730 GT | `semantic_only` | 0.988278 | -- | 0.057431 | -- |
| internal-dev, 354 contexts / 2,730 GT | strict `family_product` | 0.990110 | +0.001832 `[-0.000382,+0.004345]` | 0.031689 | -0.025742 `[-0.028405,-0.023109]` |
| final-validation, 548 contexts / 3,972 GT | `semantic_only` | 0.951410 | -- | 0.062153 | -- |
| final-validation, 548 contexts / 3,972 GT | strict `family_product` | 0.958963 | +0.007553 `[+0.004079,+0.011854]` | 0.034252 | -0.027901 `[-0.030347,-0.025656]` |

Both frozen gates pass on both splits. The final model SHA-256 is
`bf52a2d7c90d3f11e024f74ac6f3ba7a88f04d2865fb0df7a34a079b200f3c6f` and
the score-definition SHA-256 is
`e9186633c6514f7eb2804e0cc91d2bc0fbb089be2680bcecaa61ecaaee718fac`.
The factor controls now use GT-only wrong-T rows and exact endpoint algebra:
the final vertical correct-T win rate is 97.44%, vertical inverse error is
0.00124, and correct-minus-wrong-pair compatibility is +0.42341.

This strengthens the leakage-control evidence. The paper reports it as a
benchmark evaluation with explicit train/internal-dev/final-validation roles;
it does not assign an untouched-target label. Verifier-derived V remains
distinct from independent human physical validity. Moreover,
support/contact V regresses in family-wise analyses, so neither every-family
improvement nor support/contact-solved wording is permitted.

Authoritative artifact:
`experiments/H001_geom_reliability/train_only_reestablishment_v1/final_validation/evaluation/summary.json`.

## Earlier Fresh Official 3DSSG/SGPN Factor Diagnostic

The official `3DSSG_full_l160` SGPN checkpoint was frozen as an unseen
semantic source before download/inference. Evaluation uses all 548 contexts in
the 157-scan official validation annotations, preserves the 3,972-row exact-
label denominator, and shares 1,000 paired subgraph bootstrap indices. This is
the official SceneGraphFusion release's unified implementation, not a claim to
reproduce the original 3DSSG paper implementation or its leaderboard result.

| condition | R@100 | dR vs semantic (95% CI) | verifier V@100 | dV vs semantic (95% CI) | frozen gate |
| --- | ---: | --- | ---: | --- | --- |
| `semantic_only` | 0.951410 | -- | 0.062153 | -- | reference |
| `family_conditional_risk` | 0.958711 | +0.007301 `[+0.003483,+0.011604]` | 0.034690 | -0.027464 `[-0.029818,-0.025200]` | pass |
| `rank_average_fusion` | 0.949899 | -0.001511 `[-0.010053,+0.008085]` | 0.021642 | -0.040511 `[-0.043540,-0.037426]` | fail: dR CI lower is not `>-0.01` |

The miss is `0.000053` at the pre-registered lower-bound guardrail and is not
rounded into a pass. Thus the new source confirms calibrated product, while
the stronger claim that both framework instantiations always pass is blocked.

The train-only factor diagnostic reports `product_M_G`, `product_M_add`, and
`product_M_int`; `product_M_int` reaches R@100 `0.959215` and V@100 `0.050000`.
However, `M_int` has mean absolute close-by swap error `0.22183` and vertical
inverse-equivariance error `0.10085`. These controls block promotion of the
pooled interaction model as a structurally valid compatibility mechanism.

## Transformation-Consistency Development

A frozen 3DSSG-only development protocol compares six structured alternatives
to the strict training-only family product. The alternatives cover inference-time
transformation averaging, transformation-consistent augmentation, linked-counterfactual margin
fitting, their combination, and an algebra-constrained feature basis. All use
the 1,061/117/157 firewall and exclude source score, source identity, rank, and
source-specific exact-label supervision from compatibility.

Only the combined linked-pair model with exact transformation averaging passes all
pre-run gates:

| Source | strict family R/V@100 | projected pairwise R/V@100 | dR vs family (95% CI) | dV vs family (95% CI) |
| --- | --- | --- | --- | --- |
| VL-SAT | .9690/.0327 | .9688/.0325 | -.00025 [-.00080,.00000] | -.00018 [-.00036,.00000] |
| Open3DSG | .6085/.0338 | .6055/.0339 | -.00302 [-.00571,-.00074] | +.00008 [-.00017,.00032] |
| SGFN | .9416/.0376 | .9418/.0372 | +.00025 [.00000,.00079] | -.00042 [-.00062,-.00024] |

The candidate has zero close-by swap and vertical inverse-equivariance error
over 2,106 and 566 internal-development rows. Its linked-positive win rate is
.992321 versus .991752 for the strict family model over 3,516 pairs. Every
source also passes the frozen K=100 joint gate against source-score ranking.
This is structural evidence, not a material accuracy gain or a best-formula
result. The artifact is
`experiments/H001_geom_reliability/relation_algebra_v1/evaluation/summary.json`.

The same fitted SGFN-supervised 69-parameter nonlinear comparator was then used
on VL-SAT and Open3DSG. At K=100 it loses VL-SAT Recall versus the
strict family product by -.00655 (95% CI [-.01251,-.00185]); at smaller K it
loses Recall significantly on both sources, including -.24673
[-.27444,-.21903] on Open3DSG at K=20. This shows that the strong SGFN
comparator is source-adapted rather than a uniform predictor-agnostic
replacement. The artifacts are under
`experiments/H001_geom_reliability/nonlinear_transfer_v1/`.

The structured candidate is promoted as the main compatibility model. The
coordinated replacement regenerated rank fusion, pooled, hard-filter,
compatibility-only, figures, and uncertainty comparisons under one consistent
strict route. The previous family product remains a labeled continuity
reference only; the mechanism is still not presented as a best-formula result.

## Held-out Verifier-Primitive Diagnostic

`experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/held_out_primitive/` refits
three source-score-excluded compatibility models on the same 1,061 training
scans, with the same pairwise objective, exact transformation averaging, and
family-aware ranking procedure. The conditions remove the exact verifier scalar, remove its
entire reconstructible measurement family, or retain only alternative
overlap/horizontal-context evidence. All 14 integrity validations pass,
including the official 548-context/157-scan universe and exact reproduction of
the promoted main-route points.

| Source | Condition | R/V@50 | R/V@100 |
| --- | --- | --- | --- |
| VL-SAT | exact scalar held out | .9280/.0199 | .9660/.0300 |
| VL-SAT | primitive family held out | .9275/.0268 | .9653/.0468 |
| VL-SAT | alternative evidence only | .9280/.0268 | .9642/.0471 |
| Open3DSG | exact scalar held out | .4381/.0342 | .5687/.0325 |
| Open3DSG | primitive family held out | .4119/.0954 | .5264/.0955 |
| Open3DSG | alternative evidence only | .4104/.1194 | .5327/.1188 |
| SGFN | exact scalar held out | .7465/.0268 | .9300/.0358 |
| SGFN | primitive family held out | .7467/.0388 | .9298/.0616 |
| SGFN | alternative evidence only | .7462/.0386 | .9277/.0625 |

Exact-scalar removal preserves nearly the full result, so the method is not a
literal readout of the single verifier input. Broader primitive removal
materially attenuates K=50 V reduction on VL-SAT and SGFN, while Open3DSG
retains a joint improvement. At K=100 every held-out condition improves both
point metrics on all three predictors. This reduces, but does not resolve, the
construct-validity risk because correlated geometry and constructed labels
remain shared.

## Orthogonal Raw-Surface Audit

`experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/surface_audit/`
contains the active automatic construct-validity audit. Its frozen protocol
was fixed before evaluation. Its point estimator uses
instance vertices; its mesh estimator uses area-weighted triangle centroids.
Neither estimator reads the OBB center, axes, distance, overlap, or gap features
used by the compatibility model and main verifier, nor does it read source
scores, compatibility scores, or existing verifier labels. Proximity and
relative vertical are the only primary audit families. All percentile and
minimum-surface-support rules are fitted on the 1,061-scan training split.

The consensus status is decided only when point and mesh give the same binary
status; all other supported disagreements are uncertain. Scan-cluster paired
intervals use shared resampling indices across both ranking methods, all K, all
audits, and all three predictors.

| Source | K | Source consensus V | RelCompat3D consensus V | dV [paired scan CI] | Source / method coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| VL-SAT | 50 | .1643 | .1434 | -.0209 [-.0241,-.0180] | .9543/.9551 |
| VL-SAT | 100 | .2600 | .2150 | -.0451 [-.0490,-.0417] | .9505/.9523 |
| Open3DSG | 50 | .4596 | .0490 | -.4106 [-.4275,-.3928] | .9777/.9823 |
| Open3DSG | 100 | .4087 | .0865 | -.3222 [-.3361,-.3074] | .9779/.9807 |
| SGFN | 50 | .1156 | .0813 | -.0343 [-.0392,-.0300] | .9570/.9576 |
| SGFN | 100 | .2155 | .1598 | -.0557 [-.0603,-.0512] | .9559/.9575 |

Point and mesh audits separately agree on the K=50/100 direction for every
predictor. Across the full K grid, their paired intervals are below zero except
for the exact SGFN K=5 tie and the point-only SGFN K=10 interval, which includes
zero; mesh and strict consensus are negative at SGFN K=10. Exact-label Recall
matches the primary public/full 548-context artifact bit-for-bit.

At K=50, RelCompat3D strict-consensus coverage (including uncertain rows) is
`.9551/.9823/.9576` for VL-SAT/Open3DSG/SGFN, while decidable coverage is
`.7099/.8375/.7992` and uncertainty among supported rows is
`.2567/.1475/.1654`. At K=100 the corresponding decidable coverage is
`.7377/.8251/.7765`. The Violation denominator follows the frozen all-status
contract and retains uncertain rows rather than dropping them.

The synthetic test translates proximity pairs apart and vertical pairs in the
predicate-consistent direction over 0, 0.5, 1, and 2 pair-scale units. Frozen
compatibility is monotone in all 512 cases per family. Point/mesh response is
96.3%/94.7% monotone for proximity and 100%/100% for vertical. This provides an
orthogonal measurement-level mechanism check, while the shared reconstructed
PLY surface and training ontology remain residual construct dependencies.

## Optional Expansion Status

`relative_size` (`bigger than` / `smaller than`) has completed the frozen
1,061/117/157 Docker route under
`experiments/H001_geom_reliability/relative_size_v1/`. At K=100, the learned
product passes the within-size and global four-family Recall--Violation gates
for VL-SAT, Open3DSG, and SGFN. The four-family changes are respectively
`(+0.00483,-0.02393)`, `(+0.06977,-0.10402)`, and
`(+0.02559,-0.03590)` for `(dR,dV)`, with all paired CI gates passing.

This is framework-scope evidence, not formula superiority. The learned product
does not strictly beat the fixed point-rule baseline on Violation, and
four-family rank-average fails the global Recall guard for VL-SAT and SGFN.
Disjoint point views remove exact verifier-rule reuse, but agreement with the
point and OBB rules is `1.0` on decidable final GT, so residual construct
circularity remains. The active paper therefore includes relative size only as
one scope sentence and full supplement evidence, not in Figure 1, the headline
contribution list, or the core three-family result table.

`attachment_deferred` source metrics exist under
`archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_validation_g5d/`,
covering `attached to`, `hanging on`, and `connected to` for VL-SAT and
Open3DSG. This artifact is not promoted to the main RelCompat3D claim because it
uses an attachment-specific G5d policy and does not yet have the same
paper-facing bootstrap/audit gate as the main three families.

`relative_horizontal` / lateral relations remain outside the main claim. The
archived policy gate did not pass the dev strict-purity requirement and no
VL-SAT/Open3DSG source metric result is promoted for that family.

## Claim Boundary

Allowed:

- scoped relation-reliability evidence for geometry-checkable 3D Scene Graph
  relation families;
- calibrated geometry-consistency evaluation and re-ranking;
- explicit recall/violation tradeoff reporting over K={5,10,20,50,100};
- Open3DSG as source-output reliability evidence with recovery-policy caveats.

Blocked:

- broad open-vocabulary 3DSSG generation improvement;
- Open3DSG leaderboard/SOTA reproduction;
- arbitrary-source generality;
- dataset-level generalization beyond 3DSSG/3RScan;
- downstream task improvement;
- promotion of `attachment_deferred`, `relative_horizontal`, or Qwen-VL into
  the main claim without separate final approval and matching evidence gates.

Open3DSG caveats to preserve: selected official non-averaged checkpoint,
filtered train/dev provenance, exact-label denominator, 548/548 recovery-policy
branch, 533/548 covered branch as sensitivity evidence, and residual
calibration risk.
