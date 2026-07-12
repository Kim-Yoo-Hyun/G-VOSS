# H001 Geometry Reliability Experiment

Last updated: 2026-07-12 KST

This is the Docker-based experiment root for GeoCalib/H001. Paper-facing
summaries are promoted to `results/h001_geom_reliability/`; row-level runtime
artifacts remain under this experiment tree or in an external release bundle.

Paper-facing name: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`.
`H001` remains the internal experiment identifier.

## Current Route

- Main sources: VL-SAT full official validation and Open3DSG full-validation `recovery_relaxed_views_min2/`.
- Main relation families: `support_contact`, `proximity`, `relative_vertical`.
- Soft framework instantiations: Family-calibrated product
  (`source score * family compatibility`) and fixed scale-robust Rank-average
  fusion; neither is universally dominant.
- Pooled-calibrator ablation: `source score * pooled compatibility`.
- Factor contract: `T_e` = predicate/family semantics, `G_e` = raw
  predicate-independent same-pair geometry, `Z_e` = source relation score, and
  `C_e = P(y_cal=1 | T_e,G_e)`, with `Z_e notin C_e`. Final ranking is
  `S_e = F(Z_e,C_e)`; product and rank-average are the frozen current
  instantiations.
- `y_cal` is the train/dev constructed target from GT positives and high-margin
  counterfactual negatives, not direct human physical validity.
- Legacy no-source-score control: `control_p_geom_valid_only`. Because its
  calibrator retains predicate/family and predicate-aligned features, call it
  calibrator-only/no-`Z_e`, not true `G_e`-only.
- K grid: `{5, 10, 20, 50, 100}`. K=1 is sanity-check only.
- Physical-validity proxy audit: two separately locked blinded Codex LLM passes
  cover 488 relation items / 137 scans. Agreement is 438/488 (89.75%,
  four-class kappa 0.845); all 334 jointly binary items agree. This is the
  current paper route and is not Human V@K. The frozen human evaluator remains
  dormant for an optional later alignment study.
- Fresh exact-label source: `sgfn_official_full_l160`, pre-registered before
  inference. The user-authorized v3 pipeline and final audit are complete; its
  aggregate K=100 primary gate passes, subject to verifier-V, family-wise, and
  strong-baseline caveats.
- Strict reconstruction: `train_only_reestablishment_v1/` owns the exact
  1,061/117/157 split firewall, validation-information provenance audit,
  strict train-only calibrators, pre-inference execution contract,
  internal-dev decision, final model/score hash lock, and official
  548-context evaluation. Its result passes the joint gate but is explicitly
  not an untouched prospective confirmation.
- Cross-dataset transfer development: official ReplicaSSG test plus the
  official FROSS VisualGenome source is under `sources/replicassg/`. The
  initial K=100 result fails and is now used to diagnose and develop
  source-scale-robust bounded fusion. It is a transfer stress test and
  development diagnostic, not untouched or prospective confirmation.
- Uncertainty sensitivity is complete under `uncertainty_sensitivity/frozen_v1/`.
  Across VL-SAT/Open3DSG/SGFN, the family product lowers decidable-only V,
  uncertainty rate, and pessimistic V; the reported V improvement is not an
  uncertain-denominator artifact. Docker log:
  `logs/h001_uncertainty_sensitivity_v3_20260712.log`.
- Current paper outputs: `paper/aaai/main_aaai27.pdf` (9 pages; technical
  content through page 7 and pages 8--9 references only),
  `paper/aaai/supplement_aaai27.pdf` (2 pages), and
  `paper/aaai/reproducibility_checklist_aaai27.pdf` (2 pages). Final main log:
  `logs/h001_strengthening_final_build_v2_20260712.log`; upload bundle:
  `release/h001_aaai27_openreview_20260712_083625/`.

## Source Roles

| Source | Role | Primary path |
| --- | --- | --- |
| VL-SAT | controlled reproduced anchor | `sources/vlsat/full_validation/` |
| Open3DSG | main open-vocabulary relation-source case study | `sources/open3dsg/full_validation/recovery_relaxed_views_min2/` |
| Qwen-VL | appendix/extension third semantic source | `sources/qwen_vl/` |
| SGFN full_l160 | fresh exact-label confirmation; aggregate gate passed, verifier-V caveat | `sources/sgfn/` |
| ReplicaSSG + FROSS | transfer stress test and method-development diagnostic | `sources/replicassg/` |
| attachment_deferred | extension diagnostic, not promoted | `archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_validation_g5d/` |
| Open3DSG 533/548 branch | unmodified-source sensitivity | `sources/open3dsg/full_validation/` |
| historical 127-scan branches | appendix/sensitivity/provenance only | older source subfolders and `archive/` |

## Current Full-Validation Counts

| Item | Count |
| --- | ---: |
| validation scans | 157 |
| contexts | 548 |
| directed pairs | 36,808 |
| VL-SAT prediction rows | 957,008 |
| Open3DSG recovery prediction rows | 695,916 |
| SGFN prediction rows | 957,008 |
| GT rows | 11,254 |
| in-scope H001-family GT rows | 3,972 |

## Main Metrics

VL-SAT full-validation:

| Condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| Source score | 0.9272 | 0.9635 | 0.0268 | 0.0476 |
| Family-calibrated product | 0.9288 | 0.9683 | 0.0206 | 0.0333 |
| Pooled-calibrator ablation | 0.9305 | 0.9688 | 0.0229 | 0.0404 |
| Hard geometry filter | 0.9257 | 0.9627 | 0.0000 | 0.0000 |

Open3DSG full-validation recovery:

| Condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| Source score | 0.4096 | 0.5161 | 0.1386 | 0.1242 |
| Family-calibrated product | 0.4658 | 0.6047 | 0.0286 | 0.0341 |
| Pooled-calibrator ablation | 0.3975 | 0.5723 | 0.0606 | 0.0811 |
| Hard geometry filter | 0.4295 | 0.5368 | 0.0000 | 0.0000 |

SGFN fresh confirmatory target v3:

| Condition | R@50 | R@100 | verifier V@50 | verifier V@100 |
| --- | ---: | ---: | ---: | ---: |
| Source score | 0.7402 | 0.9235 | 0.0385 | 0.0630 |
| Family-calibrated product | 0.7709 | 0.9416 | 0.0258 | 0.0381 |
| Pooled-calibrator ablation | 0.7709 | 0.9396 | 0.0293 | 0.0488 |
| Compatibility only | 0.3593 | 0.6463 | 0.0176 | 0.0224 |
| Rank-average fusion | 0.7243 | 0.9476 | 0.0218 | 0.0277 |
| Reciprocal-rank fusion | 0.7341 | 0.9192 | 0.0211 | 0.0284 |

SGFN Recall uses the frozen 3,972-row exact-label denominator. Its V columns
are frozen-verifier diagnostics, not independent human physical-validity
measurements.

ReplicaSSG/FROSS initial transfer diagnostic:

| Condition | R@20 | R@50 | R@100 | verifier V@20 | verifier V@50 | verifier V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.14535 | 0.25581 | 0.36047 | 0.11818 | 0.13100 | 0.19674 |
| `family_product` | 0.21512 | 0.31395 | 0.36047 | 0.03182 | 0.09225 | 0.19674 |
| `rank_average_family` | 0.15116 | 0.24419 | 0.33140 | 0.00455 | 0.02030 | 0.03839 |
| `rrf_c60` | 0.13953 | 0.22093 | 0.33140 | 0.00909 | 0.04428 | 0.05950 |

The initial official 11-scene exact-label denominator is 172 and the adapter preserves
4,290 actual candidates. K=100 was frozen as primary. Product dR/dV is exactly
zero, so it fails strict V improvement; rank-average dR is `-0.02907` with
paired CI `[-0.07407,+0.01333]`, so it fails the recall guardrail despite dV
`-0.15835` `[-0.19292,-0.12190]`. Do not promote the lower-K product gains or
change K after observing this result.

Current feature interpretation is family-specific. Raw center, extent,
contact, overlap, and distance features belong to `G_e`; predicate/family
one-hot belongs to `T_e`; predicate-aligned vertical deltas belong to
`T_e x G_e`. Source score and source identity are excluded from calibrator
inputs. This establishes a leakage boundary, not yet uniform factor necessity
across all three families.

The raw metric JSON may still contain legacy condition keys such as
`control_family_specific_p_geom_valid`; paper-facing tables and prose should
refer to that operating point as `family_conditional_risk`.

## Factor-Isolation Protocol, Frozen 2026-07-10

`h001_factor_isolation_protocol_v1` is frozen at
`factor_isolation_protocol/frozen_v1/` with validation errors `0`. Its models
are now fit under `factor_isolation_protocol/fitted_v1/`, and the untouched-
source execution is under `sources/3dssg_full_l160/`. The frozen artifacts
lock:

- final Docker log:
  `logs/h001_factor_isolation_protocol_freeze_final_20260710.log`, exit `0`;
- protocol self-validation: `59/59` gates pass;

- a complete feature ledger with `T`, raw `G`, `T x G`, and forbidden
  `Z/source` classes;
- the exact `y_cal` construction, row counts, and scan-disjoint train/dev
  provenance;
- `T`-only, true-`G`-only, additive `T+G`, and interaction-aware `T x G`
  conditions, with existing-score equivalence checked before new evaluation;
- wrong-`T` for inverse-predicate `relative_vertical`; endpoint-swap invariance
  for `close by`; inverse-equivariance/contradiction checks for vertical
  predicates; and no blanket support/contact swap until an exact transform is
  defined;
- fixed sources, K grid, denominators, family-wise paired CIs, Docker command,
  and the label
  `post_hoc_mechanism_diagnostic_not_original_sgfn_confirmatory_gate`.

Fresh-source result: official `3DSSG_full_l160` uses the SGPN implementation
and the 157 scans in `relationships_validation.json` (called `test_scans.txt`
inside the source release). All 548 contexts are retained, calibration overlap
is zero, and the exact-label denominator remains 3,972. At K=100, calibrated
product changes Recall by `+0.007301` (95% CI
`[+0.003483,+0.011604]`) and verifier V by `-0.027464`
(`[-0.029818,-0.025200]`), passing its joint gate. Rank-average changes Recall
by `-0.001511` with CI `[-0.010053,+0.008085]`; because the frozen lower-bound
rule is strictly `>-0.01`, it fails by `0.000053` even though dV is
`-0.040511`. Therefore this target confirms the calibrated-product
instantiation, not a two-formula cross-source claim.

The factor diagnostic is also bounded. `M_int` has the strongest calibration-
dev AUROC (`0.9822`) and its product improves fresh-source aggregate Recall/V,
but its close-by swap and vertical inverse absolute differences are large
(`0.22183`, `0.10085`). The symmetric all-candidate wrong-T aggregate cancels
to zero and is not evidence of correct predicate conditioning. Keep factor
results diagnostic and do not promote `M_int` or a structural-equivariance
claim.

The final factor artifact includes both fusion forms for every frozen
condition, direct `M_int-M_T/M_G/M_add` paired contrasts, within-family and
global-top-K family-slice outputs, simultaneous family-wise 95% bands, and
mean/median/p95 metamorphic diagnostics. The earlier point-only incomplete
artifact is preserved under `archive/experiments/` and is not authoritative.

Feature audit: the exact 29-feature model union contains `T=10` (including the
shared intercept), raw `G=17`, and `T x G=2`; all current features are
classified and no forbidden `Z/source` field occurs in the calibrator. The
fair diagnostic family uses one pooled architecture: `M_T` has 10 parameters,
true `M_G` 18 with no family route, additive `M_add` 27, and `M_int` 29. The
current family-specific score remains separate as read-only `M_existing`.

Existing-score equivalence is complete across all in-scope rows: VL-SAT
`220,848`, Open3DSG recovery `160,596`, and SGFN `220,848`. Independently
reconstructed compatibility and product scores are bit-exact, both maximum
absolute errors are `0.0`, source score-stream SHA-256 values match, and
rank-average operands/tie-breaking are unchanged.

Evaluation scope is fixed to the three sources, K=`{5,10,20,50,100}`, exact
label denominator `3,972` over 548 contexts (538 with in-scope GT), and family
denominators support/contact `1,816`, proximity `1,766`, vertical `390`. Eleven
self-`supported by` GT rows remain in the denominator. Paired uncertainty uses
1,000 fixed-seed subgraph-cluster resamples plus a simultaneous 95% max-
absolute centered bootstrap band over the three families for each
source/K/contrast/metric.

Implementation and fresh-source diagnostics are complete. Keep these results
as post-hoc mechanism evidence; no condition/source/K/denominator/CI change is
allowed after metrics.

Do not import H002 metrics or its approximate endpoint-sign-flip control into
H001. Observability/routing may be reported as applicability diagnostics only;
`p_obs`, `p_rel`, learned geometry encoders, energy/PoE claims, and
support/contact-solved wording remain outside the current route.

## Strict Train-only Reestablishment, 2026-07-11

Authoritative root:
`train_only_reestablishment_v1/`.

The firewall is 1,061 train scans / 117 internal-dev scans / 157 official
final-validation scans with pairwise overlap zero. The constructed calibration
export contains 66,454 rows. Only 60,208 train rows determine normalization,
imputation, and model weights; 6,246 internal-dev rows are diagnostic only;
final-validation fit rows are zero. Five selected scans with no in-scope
positive row remain in the split and are disclosed as exporter warnings rather
than removed from the firewall.

The exact `family_product = semantic_score * C_family_strict` default, all
comparators, K=`{5,10,20,50,100}`, paired 1,000-subgraph bootstrap, and controls
were frozen before internal-dev source inference. Internal-dev covers 354/354
contexts, 23,228/23,228 directed pairs, and 2,730/2,730 in-scope GT rows. At
K=100 it passes both acceptance gates:

| split | semantic R/V | strict family product R/V | dR (95% paired CI) | dV (95% paired CI) |
| --- | --- | --- | --- | --- |
| internal-dev | `0.988278 / 0.057431` | `0.990110 / 0.031689` | `+0.001832` `[-0.000382,+0.004345]` | `-0.025742` `[-0.028405,-0.023109]` |
| final-validation | `0.951410 / 0.062153` | `0.958963 / 0.034252` | `+0.007553` `[+0.004079,+0.011854]` | `-0.027901` `[-0.030347,-0.025656]` |

The final model SHA-256 is
`bf52a2d7c90d3f11e024f74ac6f3ba7a88f04d2865fb0df7a34a079b200f3c6f`;
the score-definition SHA-256 is
`e9186633c6514f7eb2804e0cc91d2bc0fbb089be2680bcecaa61ecaaee718fac`.
Family-specific controls behave as intended on final validation: correct-vs-
wrong-T wins on 97.44% of 390 vertical GT rows; close-by swap mean absolute
difference is `0.01542`; vertical inverse-equivariance mean absolute difference
is `0.00124`; correct-minus-wrong-pair compatibility is `+0.42341` over 3,961
recoverable GT rows. Blanket support/contact swap remains prohibited.

The limitation is material: support/contact verifier V worsens in both
within-family and global-top-K family-slice views. The experiment supports the
aggregate scoped framework, not every-family improvement. Because the same
official final-validation target had been observed during historical method
development, the authoritative classification is
`leakage_controlled_train_only_reconstruction_not_untouched_prospective_confirmation`.
ReplicaSSG/FROSS remains a transfer-development diagnostic: its initial
K=100 criterion fails, and the later bounded-fusion LOSO estimate also fails
the Recall guardrail. SGFN remains positive additional-source evidence; the
paper does not claim dataset-level generalization.

## Reviewer-Extension Gate, 2026-07-10

Docker `reviewer_extension_metrics` adds paired subgraph-bootstrap CIs,
within-family and global-top-K family slices, fixed rank-average fusion, and
fixed Reciprocal Rank Fusion. Its outputs live under
`reviewer_extension_metrics/frozen_v1/`.

The aggregate GeoCalib result remains positive, but it is not family-uniform.
At within-family K=50, `family_conditional_risk` lowers verifier-derived
Violation for `proximity` and `relative_vertical`, while `support_contact`
Violation increases on both VL-SAT and Open3DSG. The same support/contact
regression appears in the actual global-top-100 family slice. Therefore paper
wording must say overall scoped violation reduction, not improvement for every
relation family. This label-free decomposition remains verifier-derived and is
diagnostic until the independent human audit is complete.

The scale-robust fusion comparisons prevent an easy-baseline omission and
support framework-level rather than formula-level interpretation. Reciprocal
Rank Fusion has lower VL-SAT V@100 than the calibrated product with a recall
delta CI crossing zero, whereas on Open3DSG it has much higher V@100 than the
product. Fusion choice is consequently a source-dependent recall/reliability
tradeoff rather than a universally dominating rule.

The physical-validity protocol is frozen under
`physical_validity_audit/frozen_v1/`. Public annotator sheets exclude source,
scores, ranks, verifier output, and sampling strata. The evaluation runner under
`physical_validity_audit/evaluation_v1/` is intentionally in
`awaiting_independent_human_labels` state; no proxy labels are promoted as
human evidence. Once labels exist it reports raw semantic calibration and
scene-disjoint five-fold cross-fitted monotone Platt calibration alongside
design-weighted Human V@K.

The Docker evaluator additionally requires one complete, timestamped,
non-proxy reviewer ID per first-pass sheet, distinct IDs across A/B, and a
third distinct non-proxy adjudicator ID whenever adjudication is used. A
Codex/LLM/proxy label stream cannot satisfy this gate even if copied into the
human CSV schema.

The leakage-safe Codex draft under
`physical_validity_audit/codex_proxy_v1/` uses only the public queue and public
pair PLY evidence. It does not read source identity, semantic score/rank,
verifier output, private strata, or GT. Its 488 draft labels are 180 valid, 185
invalid, 120 ambiguous, and 3 unobservable. Review is available through
`review.html` or `user_review.csv`. Neither the draft nor a later user
confirmation may be represented as two independent human annotators.

A second locked Codex LLM proxy pass under
`physical_validity_audit/codex_rereview_v2/`
also read only public pair geometry and did not read pass v1 labels before its
decision lock. It labels 175 valid, 178 invalid, 132 ambiguous, and 3
unobservable. Post-lock comparison finds 438/488 agreement (89.75%, four-class
kappa 0.845). All 334 rows that both passes resolve to valid/invalid have the
same polarity; the 50 disagreements are exclusively ambiguous-boundary changes.
All 50 were visually inspected under `codex_review_comparison/`, with no label
mutation. Together these are `two blinded Codex LLM proxy annotation passes`:
a legitimate automatic-evaluator stability diagnostic, not inter-human
agreement or physical-validity ground truth.

An optional Codex-to-human alignment study uses the already frozen 488-item
queue; it is not a new score-development pass. Two genuinely independent
humans each label all 488 items using the blank, separately shuffled
`frozen_v1/annotator_a.csv` and `annotator_b.csv` sheets. They remain blinded
to source, scores, ranks, verifier, GT, Codex labels, and one another. A third
distinct human adjudicates every disagreement and every low-confidence,
ambiguous, or unobservable row. The adjudicated labels form the human reference.
The locked Codex v1/v2 labels are then compared without mutation using
four-class agreement/kappa, binary valid/invalid agreement and confusion,
coverage, confidence calibration where available, and family-stratified error.
Finally, the frozen evaluator recomputes design-weighted Human Violation@K and
paired scan-bootstrap CIs for the same semantic/product/rank-average/RRF
selections and compares their direction with verifier-derived V. Until this
workflow is complete, `evaluation_v1/summary.md` correctly remains
`awaiting_independent_human_labels` and the paper cannot claim human alignment
or Human V@K.

The pre-annotation addendum is frozen in
`physical_validity_audit/frozen_v1/annotation_guide.md`. It defines confidence,
evidence sufficiency, label-compatible reason codes, immutable fields, and the
mandatory adjudication union. Docker `human_alignment_validate` enforces every
disagreement, either low-confidence decision, and either
ambiguous/unobservable label; it writes a public-evidence-only adjudication
queue after both first passes lock. `physical_validity_audit_evaluate` imports
the same contract, so Human V@K cannot bypass the stronger gate. Docker
`codex_human_alignment_evaluate` then reports four-class agreement/kappa,
binary confusion/coverage/invalid precision-recall-F1, family-stratified error,
and accuracy by ordinal Codex confidence without treating confidence categories
as probabilities. Current dry-run status is correctly awaiting human labels;
all three evaluators report no human metric.

Post-hoc provenance and the prospective evaluation contract are frozen under
`confirmatory_evaluation/frozen_v1/`. The calibrator predates source metrics,
but the family-conditioned condition was formerly promoted to paper main after
those metrics were observed and is now the calibrated-product instantiation.
Existing source tables are therefore retrospective;
the frozen human audit can be confirmatory for physical validity. The untouched
SGFN `full_l160` target was selected and frozen before inference. Preflight then
found two protocol defects before any score existed: H001's 157 target scans
exactly match official SGFN `test_scans.txt` rather than `validation_scans.txt`,
and the v1 checkpoint URL points to a 20-object/8-relation archive rather than
the locked 160-object/26-relation model. Target v2 preserves the split erratum;
`checkpoint_audit.json` records the incompatible tensor shapes. The user then
authorized target v3 before correct-checkpoint download. V3 freezes the
official full_l160 URL; its checkpoint audit passes strict 160/26 head shapes,
the exact 157-scan preprocess is ready, and a one-scan full-directed-edge
inference smoke passes. Full inference produced 157 scans, 4,480 nodes,
160,526 directed edges, and 4,173,676 relation scores. The identity adapter and
geometry join each preserve 957,008 prediction rows. All 36,808 nonself pairs
are covered; 11 self-`supported by` GT rows receive no synthesized edge and
remain in the 3,972-row Recall denominator.

The frozen K=100 primary gate passes: Recall changes from 0.92346 to 0.94159
(dR +0.01813, 95% CI [+0.01341,+0.02325]) and verifier V changes from 0.06297
to 0.03808 (dV -0.02489, 95% CI [-0.02699,-0.02290]). This does not authorize
uniform-family or unique-score claims. `support_contact` verifier V regresses
by +0.00450, 95% CI [+0.00370,+0.00532], while the pre-specified rank-average
instantiation obtains R@100 0.94763 and verifier V@100 0.02772; versus the
calibrated product, its dR CI
crosses zero and its dV CI is strictly below zero.

## Canonical Artifacts

Paper-facing compact outputs:

- `results/h001_geom_reliability/report.md`
- `results/h001_geom_reliability/manifest.lock.json`
- `results/h001_geom_reliability/tables/`
- `results/h001_geom_reliability/bootstrap_ci/summary.md`
- `results/h001_geom_reliability/figures/figure_specs.md`
- `results/h001_geom_reliability/full_validation_transition/artifact_bundle/`

Primary source artifacts:

- `sources/vlsat/full_validation/metrics/metrics.json`
- `sources/vlsat/full_validation/metrics_k_sweep/metrics.json`
- `sources/vlsat/full_validation/bootstrap_ci/summary.md`
- `sources/vlsat/full_validation/gt_eval/metrics.json`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics/metrics.json`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/metrics.json`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/bootstrap_ci/summary.md`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/table_caveats/report.md`
- `sources/sgfn/adapter/coverage_audit.json`
- `sources/sgfn/confirmatory_metrics/summary.md`
- `sources/sgfn/confirmatory_metrics/decision.json`
- `sources/replicassg/prospective_protocol/frozen_v1/manifest.json`
- `results/h001_geom_reliability/replicassg_prospective/summary.md`

## Runbook

Use `experiments/H001_geom_reliability/commands.md` for exact commands.

Common Docker checks from the repo root:

```bash
docker compose -f configs/h001/compose.yaml config --quiet
docker compose -f configs/h001/compose.yaml run --rm table_builder
docker compose -f configs/h001/compose.yaml run --rm bootstrap_ci
docker compose -f configs/h001/compose.yaml run --rm physical_validity_audit_freeze
docker compose -f configs/h001/compose.yaml run --rm physical_validity_audit_evaluate
docker compose -f configs/h001/compose.yaml run --rm reviewer_extension_metrics
docker compose -f configs/h001/compose.yaml run --rm confirmatory_protocol_freeze
docker compose -f configs/h001/compose.yaml run --rm physical_validity_codex_proxy
docker compose -f configs/h001/compose.yaml run --rm physical_validity_codex_rereview_v2
docker compose -f configs/h001/compose.yaml run --rm physical_validity_codex_compare
docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_target_v3_freeze
docker compose -f configs/h001/compose.yaml run --rm sgfn_checkpoint_audit_v3
docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_audit
docker compose -f configs/h001/compose.yaml run --rm nonlinear_fusion_baseline
docker compose -f configs/h001/compose.yaml run --rm codex_proxy_audit_evaluate
```

Artifact bundle verification:

```bash
bash results/h001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh
```

Latest verified bundle logs:

- `logs/h001_fullval_upload_checksums_family_main_20260625_085344.log`, exit 0.
- `logs/h001_fullval_upload_verify_family_main_20260625_085354.log`, exit 0.

## Claim Boundary

Allowed:

- scoped relation reliability for geometry-checkable families;
- calibrated geometry-consistency evaluation and re-ranking;
- explicit recall/violation tradeoff reporting;
- Open3DSG as source-output reliability evidence with recovery-policy caveats.

Blocked:

- broad open-vocabulary 3DSSG SOTA claim;
- treating Open3DSG recovery as an unmodified official benchmark result;
- promoting Qwen-VL or relation-family expansions into the main claim without explicit decision and matching evidence gates.

## 2026-07-12 Reviewer-Strengthening Results

Parameter-matched nonlinear fusion:

- protocol: `nonlinear_fusion_baseline/protocol.json`
- output: `nonlinear_fusion_baseline/evaluation_v1/`
- model: 69-parameter two-hidden-unit ReLU MLP, matching the 69 coefficients
  across the three family calibrators;
- firewall: 117-scan internal-dev exact-label correctness only for fit and
  157-scan official final validation only for evaluation;
- SGFN R/V: K=10 `0.5441/0.0120`, K=50 `0.8681/0.0186`, K=100
  `0.9466/0.0279`.

This source-specific supervised rescorer has a stronger supervision contract
than GeoCalib. Its result blocks formula-optimality and best-rescorer claims;
it does not invalidate the source-independent factor contract
`Z notin C(T,G)`.

Codex proxy diagnostic:

- output: `physical_validity_audit/codex_proxy_evaluation_v1/`
- inputs: the two already locked Codex passes;
- consensus: exact pass agreement retained, disagreements set to ambiguous,
  ambiguous/unobservable excluded from binary proxy Violation;
- role: non-human, non-submission diagnostic only.

The active AAAI submission contains no Codex-derived physical-validity result.
The separate manuscript is `paper/paper_nonsub/main_nonsub.pdf`. Independent
human construct validation remains open.

## Archived Or Optional Material

Historical 127-scan outputs, non-avg branch details, failed/intermediate runs,
relative-horizontal/lateral experiments, and attachment-deferred experiments
are provenance, appendix, or future-work material. Keep their detailed logs in
their owning subfolders or `archive/`; do not copy them into current main
tables unless the claim boundary is intentionally changed.

Latest attachment-deferred full-validation extension artifact:

- protocol: `archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_validation_protocol/`
- metrics: `archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_validation_g5d/`
- scope: VL-SAT/Open3DSG full-validation attachment labels `attached to`, `hanging on`, `connected to`, K = `{5,10,20,50,100}`
- status: source metrics ready, validation errors 0, not promoted to the main GeoCalib claim
