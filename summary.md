# GeoCalib / H001 Research Summary

Last updated: 2026-07-12 KST

Paper-facing name: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`.
Use `GeoCalib` in manuscript-facing prose. Keep `H001` only for internal
experiment paths and archived hypothesis records.

## Parallel H002 Route

H002 is a separate scoped paper branch and does not modify H001 artifacts.

- Title: `Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations`
- Claim: source confidence does not guarantee predicate-geometry compatibility;
  H002 separates `T_e`, predicate-independent `G_e`, source confidence
  `Z_e`, and `C_e=f_C(T_e,G_e)`.
- Leakage boundary: `Z_e` is excluded from `C_e` and enters only final
  reranking.
- Implementation: a logistic `C_e` model is fit on 4,868 internal-train rows.
  Source score is normalized per source, raw compatibility per source-family,
  and the primary score is
  `S2_source_x_Ce = normalized_source_score * normalized_C_e`.
- Evaluation: VL-SAT and Open3DSG predictions on the official 3DSSG validation
  split; Recall@K, custom Violation@K, and 1,000 grouped bootstrap replicates.
- Main validated routes: relative vertical (higher/lower) and relative size
  (bigger/smaller).
- Caveated route: left/right. It consistently lowers Violation, but VL-SAT has
  a bounded Recall tradeoff.
- Controls/failures: close by is geometry-only; front/behind is a
  reference-frame/depth failure; support/contact is diagnostic because its
  repaired target is positive-sparse and exactly reconstructed by its
  construction rule.
- Main comparison deltas for S2 versus source-only:
  K=10 dRecall +0.0420 [0.0232, 0.0621], dViolation -0.2299
  [-0.2397, -0.2202]; K=20 dRecall +0.0816 [0.0481, 0.1180],
  dViolation -0.2431 [-0.2519, -0.2351]; K=50 dRecall +0.1032
  [0.0689, 0.1407], dViolation -0.2592 [-0.2662, -0.2524].
- Boundary: validation-level custom evaluation only. H002 does not claim hidden
  test, SOTA, all-relation reliability, solved support/contact, learned-G_e
  improvement, calibrated p_obs/p_rel, or normalization invariance.
- Package status: compact tables, CI, sensitivity, controls, qualitative cases,
  and support/contact diagnostic freeze are complete. The verified AAAI package
  is main/supplement/checklist 7/3/2 pages.
- Current action: no automatic experiment is open. External release/submission
  or a broader route requires an explicit decision and a frozen protocol.

Authoritative owners:

- hypothesis state: `hypothesis/CAND-001/H002_factorized-relation-confidence/README.md`
- claim and method: `hypothesis/CAND-001/H002_factorized-relation-confidence/paper_claim_core.md`, `hypothesis/CAND-001/H002_factorized-relation-confidence/method_contract_v1.md`
- consolidated evidence: `hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0706.md`
- runtime: `experiments/H002_compatibility_routing/`
- manuscript: `paper/h002_compatibility_routing/aaai2027/`


## Current Status

- Current paper route: AAAI-style manuscript under `paper/aaai/`.
- Active AAAI-27 outputs: `paper/aaai/main_aaai27.pdf` (9 US-Letter pages;
  technical content through page 7, references only on pages 8--9),
  `paper/aaai/supplement_aaai27.pdf` (1 page), and
  `paper/aaai/reproducibility_checklist_aaai27.pdf` (2 pages). Final main log:
  `logs/h001_aaai27_main_build_20260712.log`; triplet verification log:
  `logs/h001_aaai27_final_triplet_build_20260712.log`. All three have
  zero Type 3 fonts and no unresolved citations/references or blocking
  LaTeX/overfull errors.
- Active OpenReview upload set:
  `release/h001_aaai27_openreview_20260712_083625/`. Older factorized,
  LLM-proxy, Replica-disclosure, and reference-expansion PDFs remain historical
  provenance snapshots rather than upload candidates.
- Main sources: VL-SAT full official validation and Open3DSG full-validation `recovery_relaxed_views_min2/`.
- Framework instantiations: calibrated product
  (`family_conditional_risk = semantic_score * p_geom_valid_family`) and fixed
  scale-robust rank-average fusion. Neither is claimed universally dominant.
- Pooled ablation: `probabilistic_recalibrated = semantic_score * p_geom_valid`.
- Factorization: `T_e` is predicate/family semantics, `G_e` is
  predicate-independent same-pair geometry, `Z_e` is source confidence, and
  `C_e = P(y_cal=1 | T_e,G_e)` is calibrated compatibility for the constructed
  train/dev target. The leakage boundary is `Z_e notin C_e`; final ranking is
  `S_e = F(Z_e,C_e)`.
- Legacy `control_p_geom_valid_only`: calibrator-only/no-`Z_e` control. It is
  not true `G_e`-only because the calibrator includes predicate/family and
  predicate-aligned interaction features.
- Main K grid: `{5, 10, 20, 50, 100}`. K=1 is sanity-check only.
- Qwen-VL is complete as a third-source / modern VLM extension, but it is not part of the main claim unless explicitly promoted.
- Strict train-only reestablishment is complete under
  `experiments/H001_geom_reliability/train_only_reestablishment_v1/`. It uses
  an exact 1,061/117/157 train/internal-dev/final firewall, zero final rows in
  fitting, a pre-source-inference execution contract, and a post-internal-dev
  model/score hash lock. It passes the final aggregate joint gate, but its
  classification is leakage-controlled reconstruction rather than untouched
  prospective confirmation.

## Claim Boundary

Allowed claim:

```text
For geometry-checkable 3D Scene Graph relation families, GeoCalib exposes and
reduces semantically plausible but geometrically inconsistent relation
predictions by applying a calibrated geometry-consistency reliability layer
while reporting recall tradeoffs.
```

Current scope:

- `support_contact`
- `proximity`
- `relative_vertical`

Not claimed:

- Broad open-vocabulary 3D Scene Graph generation improvement.
- Baseline-agnostic or SOTA 3DSSG improvement.
- Guaranteed physical correctness of every retained relation.
- Promotion of `relative_horizontal`, `relative_lateral`, or `attachment_deferred` into the main AAAI claim.

## Method

GeoCalib is a calibrated geometry-consistency evaluation and re-ranking
framework over existing relation-source outputs.

Factor contract:

| Factor | Definition | Boundary |
| --- | --- | --- |
| `T_e` | predicate label and relation-family semantics | may condition compatibility |
| `G_e` | raw, predicate-independent geometry of the same ordered object pair | excludes predicate-aligned transforms |
| `Z_e` | source relation confidence | excluded from `C_e` |
| `C_e` | `P(y_cal=1 | T_e,G_e)` | constructed-target calibrated compatibility |
| `S_e` | `F(Z_e,C_e)` | product and rank-average are frozen instantiations |

`y_cal` is built from train/dev GT-positive rows and high-margin
counterfactual negatives. It must not be described as direct human physical
validity. Predicate-aligned center-delta features are interaction terms
`T_e x G_e`, while raw center/extent/contact/distance quantities belong to
`G_e`. Existing artifacts exclude the source score, but factor necessity is
not yet established uniformly across families.

Core steps:

1. Standardize relation predictions into identity-preserving rows.
2. Join subject/object 3D geometry evidence for the same object pair.
3. Evaluate relation-family-specific geometric consistency.
4. Calibrate geometry validity as `p_geom_valid` or `p_geom_valid_family`.
5. Re-rank relation predictions with semantic confidence and calibrated geometry risk.
6. Report `R@K` and `Violation@K` together.

Main scoring conditions:

| Condition | Role |
| --- | --- |
| `semantic_only` | source ranking baseline |
| `family_conditional_risk` | calibrated-product instantiation |
| `rank_average_fusion` | pre-specified scale-robust instantiation |
| `probabilistic_recalibrated` | pooled calibrated-risk ablation |
| `rule_verified_point_subtype` | hard-rule diagnostic |
| `control_p_geom_valid_only` | calibrator-only/no-source-score control; not true `G`-only |
| `control_distance_only` | distance-only control |
| `control_shuffled_geometry` | geometry distribution control |
| `control_wrong_pair_geometry` | object-pair identity control |

## Current Evidence

Full official validation scope:

| Item | Count |
| --- | ---: |
| validation scans | 157 |
| contexts | 548 |
| directed pairs | 36,808 |
| VL-SAT prediction rows | 957,008 |
| Open3DSG recovery prediction rows | 695,916 |
| GT rows | 11,254 |
| in-scope H001-family GT rows | 3,972 |

VL-SAT full-validation source result:

| Condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9272 | 0.9635 | 0.0268 | 0.0476 |
| `family_conditional_risk` | 0.9288 | 0.9683 | 0.0206 | 0.0333 |
| `probabilistic_recalibrated` | 0.9305 | 0.9688 | 0.0229 | 0.0404 |
| `rule_verified_point_subtype` | 0.9257 | 0.9627 | 0.0000 | 0.0000 |

Open3DSG full-validation recovery source result:

| Condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.4096 | 0.5161 | 0.1386 | 0.1242 |
| `family_conditional_risk` | 0.4658 | 0.6047 | 0.0286 | 0.0341 |
| `probabilistic_recalibrated` | 0.3975 | 0.5723 | 0.0606 | 0.0811 |
| `rule_verified_point_subtype` | 0.4295 | 0.5368 | 0.0000 | 0.0000 |

Bootstrap CI summary:

- Open3DSG `family_conditional_risk` vs `semantic_only`: R@100 delta `+8.86 pp`, 95% CI `[+6.69, +10.96]`; Violation@100 delta `-9.01 pp`, 95% CI `[-9.49, -8.53]`.
- VL-SAT `family_conditional_risk` vs `semantic_only`: R@100 delta `+0.48 pp`, 95% CI `[+0.11, +0.93]`; Violation@100 delta `-1.43 pp`, 95% CI `[-1.60, -1.28]`.

Strict train-only reconstruction, frozen 2026-07-11:

- Split firewall: 1,061 train scans / 117 internal-dev scans / 157 final-
  validation scans; overlap zero. The strict table has 66,454 rows. Fit uses
  60,208 train rows; 6,246 internal-dev rows are diagnostic only; final-
  validation fit rows are zero.
- Internal-dev K=100: semantic R/V `0.988278/0.057431`; strict family product
  `0.990110/0.031689`; dR `+0.001832`
  `[-0.000382,+0.004345]`; dV `-0.025742`
  `[-0.028405,-0.023109]`. Both frozen gates pass.
- Hash lock before final evaluation: model
  `bf52a2d7c90d3f11e024f74ac6f3ba7a88f04d2865fb0df7a34a079b200f3c6f`;
  score definition
  `e9186633c6514f7eb2804e0cc91d2bc0fbb089be2680bcecaa61ecaaee718fac`.
- Final-validation K=100: semantic R/V `0.951410/0.062153`; strict family
  product `0.958963/0.034252`; dR `+0.007553`
  `[+0.004079,+0.011854]`; dV `-0.027901`
  `[-0.030347,-0.025656]`. The full 548 contexts, 3,972 GT rows, and actual
  candidate counts are retained.
- Final default controls: GT vertical correct-T win rate `0.97436`, close-by
  swap mean absolute error `0.01542`, vertical inverse mean absolute error
  `0.00124`, and correct-minus-wrong-pair compatibility `+0.42341` over 3,961
  recoverable GT rows. Support/contact endpoint swap remains prohibited.
- Boundary: support/contact verifier V still regresses in family-wise views;
  V is verifier-derived; and the official final-validation target had already
  informed historical method/score provenance. This result is not prospective
  confirmation and does not authorize family-uniform or support/contact-solved
  claims.

Reviewer-extension result, frozen 2026-07-10:

- The aggregate result reproduces the locked point estimates exactly and adds
  family-wise/global-family-slice paired CIs plus fixed rank-average and
  Reciprocal Rank Fusion baselines.
- The verifier-derived improvement is not family-uniform. At within-family
  K=50, `support_contact` V increases from `0.0433` to `0.0518` on VL-SAT and
  from `0.0475` to `0.0520` on Open3DSG; paired 95% delta CIs are strictly
  positive. The global-top-100 family slice shows the same direction. Overall
  V reduction is driven by `proximity`, `relative_vertical`, and ranking
  composition, so claims are limited to overall scoped reliability rather than
  every-family improvement.
- Reciprocal Rank Fusion at K=100 has VL-SAT R/V `0.9698/0.0251` versus product
  `0.9683/0.0333`; its recall delta CI versus product crosses zero and its V delta
  CI is strictly negative. On Open3DSG it has R/V `0.6196/0.0789` versus product
  `0.6047/0.0341`; product has much lower V while the RRF recall-delta CI narrowly
  crosses zero. This is a source-dependent recall/reliability tradeoff, not a
  universal dominance result.
- Independent physical-validity audit protocol is frozen with 488 unique items,
  137 scans, 126 nonempty probability-sampling strata, and 488/488 raw 3D
  evidence coverage. Two blinded annotator sheets and adjudication are empty by
  design; Human V@K and semantic-calibration metrics remain pending rather than
  replaced with proxy labels.
- Two blinded Codex LLM proxy annotation passes are locked as separate runs of
  the same agent family. Pass v1 counts
  valid/invalid/ambiguous/unobservable `180/185/120/3`; pass v2 counts
  `175/178/132/3`. Post-lock agreement is `438/488` (`89.75%`, four-class
  kappa `0.845`). All `334/334` rows resolved to binary by both passes have the
  same polarity; all 50 disagreements involve `ambiguous`. This is
  automatic-evaluator stability evidence only, not independent human
  agreement. Paper-facing naming is `LLM-based physical-validity proxy audit`;
  model identity, prompt/rubric, visible evidence scope, and same-agent-family
  dependence must remain disclosed.
- Provenance audit finds the family calibrator predates source metrics, but the
  family-conditioned operating point was formerly promoted to paper main after
  the source results were observed. It is now the calibrated-product
  instantiation. Existing VL-SAT/Open3DSG source tables are
  retrospective. The human-audit protocol remains frozen but is not active in
  the current route. The completed 488-row two-pass Codex audit is reported as
  an LLM-based physical-validity proxy diagnostic, not independent human
  evidence.
- `sgfn_official_full_l160` was selected as the untouched exact-label source
  before inference and before any SGFN score existed. V2 corrected the source
  split identity to the exactly matching official 157-scan test list; the user
  authorized v3 before correct-checkpoint download to replace the mistaken l20
  URL with official full_l160. Correct checkpoint 160/26 tensor audit, 157-scan
  preprocess, full inference, identity adapter, geometry join, 1,000-resample
  paired bootstrap, and final execution audit all pass.
- SGFN frozen primary K=100 confirms the calibrated-product instantiation
  against semantic:
  exact-label R rises `0.9235 -> 0.9416`, delta `+0.0181`, 95% CI
  `[+0.0134,+0.0233]`; verifier V falls `0.0630 -> 0.0381`, delta `-0.0249`,
  95% CI `[-0.0270,-0.0229]`. Both preregistered gates pass on the unchanged
  3,972-row denominator. Coverage is 548/548 contexts and 36,808/36,808
  nonself directed pairs; 11 self-`supported by` GT rows are retained in the
  denominator with no synthesized predictions.
- The fresh result strengthens the framework rather than a single formula.
  `support_contact` verifier V again regresses by `+0.00450`
  (95% CI `[+0.00370,+0.00532]`), `proximity` is unchanged at within-family
  K=100, and `relative_vertical` drives the gain. Fixed rank-average fusion
  reaches R/V `0.9476/0.0277` and passes the same recall/lower-V joint gate
  against the calibrated product. The prospective result therefore supports
  calibrated geometry-consistency integration across two pre-specified soft
  fusion forms, not family-uniform improvement or formula dominance.
- A stronger dataset-and-source prospective test was then frozen before any
  source prediction on the official 11-scene ReplicaSSG test split with the
  official VisualGenome-trained FROSS source. Validation scenes were never
  used; all 24 final provenance/firewall checks pass. Exact mappings are only
  `near/above/under`, yielding 172 GT rows and 4,290 candidates.
- The ReplicaSSG/FROSS K=100 primary gate fails. The calibrated product matches
  semantic-only exactly at R/V `0.36047/0.19674`; rank-average reaches
  `0.33140/0.03839`, with dR `-0.02907`
  `[-0.07407,+0.01333]` and dV `-0.15835`
  `[-0.19292,-0.12190]`. Product gains at K=20/50 are positive diagnostics,
  but cannot replace the frozen K=100 endpoint. This is honest external
  failure evidence, not dataset-level confirmation of the joint gate.

Verifier evidence:

- GT positives: 3,972.
- Counterfactual negatives: 3,972.
- Positive nonviolated rate: 0.9965.
- Counterfactual nonsatisfied rate: 0.9673.
- AUROC/AUPRC: 0.9772 / 0.9729.
- Brier: 0.0543.

## Source Roles

| Source | Current role |
| --- | --- |
| VL-SAT | controlled reproduced anchor |
| Open3DSG | main open-vocabulary relation-source case study |
| Qwen-VL | appendix/extension third semantic source |
| SGFN full_l160 | fresh exact-label confirmation; aggregate gate passed with verifier-V and baseline caveats |
| ReplicaSSG + FROSS | untouched dataset/source prospective test; provenance passed, frozen K=100 framework gate failed |
| `relative_horizontal` | stopped appendix/limitation scope-expansion evidence |
| `relative_lateral` | stopped appendix/future-work boundary evidence |
| `attachment_deferred` | preferred future family expansion, not current main claim |

Open3DSG caveats to keep visible:

- selected official non-avg checkpoint;
- filtered train/dev provenance;
- 548/548 recovery branch with `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`;
- relaxed two-scan view regeneration;
- 533/548 unmodified-source sensitivity branch;
- appendix-only historical 127-scan / R2 sensitivity;
- residual calibration risk.

## Artifact And Reproducibility State

Primary current locations:

- `paper/aaai/`: active manuscript source.
- `results/h001_geom_reliability/report.md`: compact paper-facing result report.
- `results/h001_geom_reliability/manifest.lock.json`: locked current result manifest.
- `results/h001_geom_reliability/tables/`: compact table artifacts.
- `results/h001_geom_reliability/bootstrap_ci/`: compact bootstrap mirror.
- `experiments/H001_geom_reliability/sources/vlsat/full_validation/`: VL-SAT full-validation runtime results.
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`: selected Open3DSG full-validation recovery route.
- `experiments/H001_geom_reliability/sources/sgfn/`: fresh SGFN v3 raw,
  adapter, geometry, coverage, and confirmatory-metric artifacts.
- `experiments/H001_geom_reliability/train_only_reestablishment_v1/`: strict
  split firewall, provenance audit, train-only models, execution contract,
  internal-dev metrics, final hash lock, and official final-validation metrics.
- `results/h001_geom_reliability/full_validation_transition/artifact_bundle/`: external upload payload list, checksums, and verification script.

Latest bundle verification:

- checksum generation log: `logs/h001_fullval_upload_checksums_family_main_20260625_085344.log`, exit 0.
- verification log: `logs/h001_fullval_upload_verify_family_main_20260625_085354.log`, exit 0.
- payload files: 211.
- checksum records: 211.
- row-count snapshot records: 18.

Large datasets, checkpoints, model caches, feature caches, raw dumps, and
row-level JSONL are not Git artifacts. Use `docs/reproducibility.md` before any
transfer, cleanup, or full rerun.

## Paper State

Current paper-facing files:

- `paper/README.md`: paper workspace map.
- `paper/preview.md`: current handoff snapshot.
- `paper/progress.md`: progress rationale.
- `paper/risk.md`: reviewer-risk register.
- `paper/review.md`: orthogonal persona review.
- `paper/appendix.md`: appendix/supplement plan.
- `paper/figures.md`: figure plan and source lock.
- `paper/aaai/README.md`: active venue-source runbook.

Current figures:

- Figure 1: failure mechanism and GeoCalib framework.
- Figure 2: recall-violation tradeoff.
- Figure 3: Open3DSG qualitative geometry-backed failure cases.

## Remaining TODO

Method-strengthening sequence:

1. Completed: froze `h001_factor_isolation_protocol_v1` with validation errors
   `0` and `59/59` passing self-validation gates before computing factor
   metrics. Final Docker log:
   `logs/h001_factor_isolation_protocol_freeze_final_20260710.log`.
2. Completed: classified the 29-feature union as `T=10`, raw `G=17`, and
   `T x G=2` with no forbidden `Z/source` hits; independently reproduced the
   existing compatibility/product scores bit-exactly on 602,292 in-scope rows
   across VL-SAT, Open3DSG, and SGFN.
3. Completed: fit `M_T/M_G/M_add/M_int` on the 4,616 calibration-train rows
   only and report the 1,193-row dev diagnostics without selection. Dev AUROC
   is `0.6124/0.8809/0.9193/0.9822`, respectively.
4. Completed: freeze a previously unseen official `3DSSG_full_l160` (SGPN)
   semantic source before checkpoint download/inference and evaluate all 548
   official-validation contexts. The calibrated product passes the frozen
   K=100 joint gate: dR `+0.00730` `[+0.00348,+0.01160]`, verifier dV
   `-0.02746` `[-0.02982,-0.02520]`. Rank-average lowers V more but misses the
   Recall guardrail by `0.000053` at its CI lower bound, so the two-score joint
   framework gate fails exactly as pre-registered.
5. Completed: factor metrics and controls. `product_M_int` improves aggregate
   dR by `+0.00780` and dV by `-0.01215`, but large close-by swap and vertical
   inverse errors (`0.22183`, `0.10085`) prevent promotion to a structurally
   valid compatibility claim. The all-candidate wrong-T stream is symmetric
   and therefore uninformative; do not cite its zero mean as positive evidence.
   The final artifact also contains the pre-registered direct contrasts,
   global-top-K family slices, simultaneous family-wise bands, and control
   median/p95 values; the first incomplete output is archived.
6. Completed: strict train-only reestablishment, internal-dev acceptance,
   model/score hash freeze, and locked 548-context final evaluation. Next
   scientific action is a genuinely untouched prospective target. The current
   audit route uses two blinded Codex LLM proxy passes; a human-alignment study
   is optional and not active. Do not reuse the observed official validation
   target as prospective evidence.
7. Completed: entirely untouched ReplicaSSG/FROSS prospective evaluation. All
   hash, split, timestamp, source, and validation firewalls pass, but the
   product has no K=100 effect and rank-average trades too much aggregate
   recall for its large V reduction. Preserve this as a negative external
   diagnostic; do not strengthen the manuscript to a dataset-level joint-gate
   claim.

Submission/package hygiene:

1. Completed: verified the live AAAI-27/OpenReview form, official target-year
   style, deadlines, page limits, separate checklist, and supplement policy.
2. Completed: built and verified the field bundle at
   `release/h001_aaai27_openreview_20260712_083625/`.
3. Author action: enter author order/profiles, countries, conflicts, and the
   qualified reciprocal reviewer.
4. Author decision: final public code license and post-acceptance artifact URL.
5. Optional scientific decision: activate the frozen independent-human
   alignment study; otherwise retain the explicit Codex-proxy-only claim.

No new main-source metric experiment is required to preserve the current
GeoCalib claim. SGFN remains source-level prospective confirmation on the
known 3DSSG target. ReplicaSSG/FROSS is a valid untouched dataset/source test
whose primary gate failed; another prospective target must not be launched
automatically to chase a passing result.
