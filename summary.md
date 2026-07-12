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
  is main/supplement/checklist 6/3/2 pages. Figure 1 is a claim-safe five-stage
  pipeline, and Method is consolidated into two module-aligned subsections.
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
  `paper/aaai/supplement_aaai27.pdf` (3 pages), and
  `paper/aaai/reproducibility_checklist_aaai27.pdf` (2 pages). Final main log:
  `logs/h001_claim_lock_main_final_20260712.log`. All three have
  zero Type 3 fonts and no unresolved citations/references or blocking
  LaTeX/overfull errors.
- Active OpenReview upload set:
  `release/h001_aaai27_openreview_20260712_083625/`. Older factorized,
  LLM-proxy, Replica-disclosure, and reference-expansion PDFs remain historical
  provenance snapshots rather than upload candidates.
- Main sources: VL-SAT full official validation and Open3DSG full-validation `recovery_relaxed_views_min2/`.
- Framework instantiations: family-calibrated product and fixed scale-robust
  rank-average fusion. Neither is claimed universally dominant.
- Pooled compatibility product is an ablation. Exact internal condition keys
  remain in experiment manifests rather than manuscript-facing prose.
- Factorization: `T_e` is predicate/family semantics, `G_e` is
  predicate-independent same-pair geometry, `Z_e` is the source relation score, and
  `C_e = P(y_cal=1 | T_e,G_e)` is calibrated compatibility for the constructed
  train/dev target. The leakage boundary is `Z_e notin C_e`; final ranking is
  `S_e = F(Z_e,C_e)`.
- The compatibility-only control removes `Z_e`. It is
  not true `G_e`-only because the calibrator includes predicate/family and
  predicate-aligned interaction features.
- Main K grid: `{5, 10, 20, 50, 100}`. K=1 is sanity-check only.
- Frozen uncertainty sensitivity is complete for VL-SAT/Open3DSG/SGFN. The
  family product lowers decidable-only V, uncertainty rate, and pessimistic V
  on all three sources, ruling out uncertainty promotion as the explanation for
  the aggregate verifier-V reduction.
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
5. Re-rank relation predictions with the source relation score and calibrated compatibility.
6. Report `R@K` and `Violation@K` together.

Main scoring conditions:

| Condition | Role |
| --- | --- |
| Source score | source ranking baseline |
| Family-calibrated product | calibrated-product instantiation |
| Rank-average fusion | fixed scale-robust instantiation |
| Pooled-calibrator ablation | family-conditioning ablation |
| Hard geometry filter | rule-supported diagnostic |
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
| Source score | 0.9272 | 0.9635 | 0.0268 | 0.0476 |
| Family-calibrated product | 0.9288 | 0.9683 | 0.0206 | 0.0333 |
| Pooled-calibrator ablation | 0.9305 | 0.9688 | 0.0229 | 0.0404 |
| Hard geometry filter | 0.9257 | 0.9627 | 0.0000 | 0.0000 |

Open3DSG full-validation recovery source result:

| Condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| Source score | 0.4096 | 0.5161 | 0.1386 | 0.1242 |
| Family-calibrated product | 0.4658 | 0.6047 | 0.0286 | 0.0341 |
| Pooled-calibrator ablation | 0.3975 | 0.5723 | 0.0606 | 0.0811 |
| Hard geometry filter | 0.4295 | 0.5368 | 0.0000 | 0.0000 |

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
- The pre-annotation human-alignment contract is implementation-complete:
  confidence/evidence-sufficiency guidance, label-compatible reason codes,
  mandatory adjudication of disagreements/low-confidence/ambiguous/
  unobservable rows, and a Codex--human alignment evaluator are available as
  Docker services. Empty-sheet dry runs correctly return awaiting states with
  zero human metrics; the remaining input is two independent 488-row human
  sheets and a third-human adjudication of the generated mandatory queue.
- Two blinded Codex LLM proxy annotation passes are locked as separate runs of
  the same agent family. Pass v1 counts
  valid/invalid/ambiguous/unobservable `180/185/120/3`; pass v2 counts
  `175/178/132/3`. Post-lock agreement is `438/488` (`89.75%`, four-class
  kappa `0.845`). All `334/334` rows resolved to binary by both passes have the
  same polarity; all 50 disagreements involve `ambiguous`. This is
  automatic-evaluator stability evidence only, not independent human
  agreement. In the non-submission analysis, naming is `LLM-based physical-
  validity proxy audit`; model identity, prompt/rubric, visible evidence scope,
  and same-agent-family dependence remain disclosed there.
- The active AAAI submission no longer reports Codex-derived validity results.
  The locked passes and a deterministic consensus evaluation are isolated in
  `paper/paper_nonsub/` as non-submission, non-human analysis. Exact-pass
  agreements are retained, every disagreement becomes `ambiguous`, and
  ambiguous/unobservable rows are excluded from binary proxy Violation. This
  diagnostic cannot replace an independent human reference.
- A 69-parameter nonlinear fusion baseline matches the combined parameter
  count of the three family calibrators and is fit only on disjoint internal-dev
  exact-label correctness. On SGFN it obtains R/V `0.5441/0.0120` at K=10,
  `0.8681/0.0186` at K=50, and `0.9466/0.0279` at K=100. It dominates the
  calibrated product at lower budgets and reduces K=100 verifier violation;
  therefore H001 does not claim formula optimality. The framework distinction
  is instead that GeoCalib learns source-independent predicate--geometry
  compatibility without source confidence or source-specific exact-label
  supervision, whereas this reviewer-requested rescorer uses both.
- Provenance audit finds the family calibrator predates source metrics, but the
  family-conditioned operating point was formerly promoted to paper main after
  the source results were observed. It is now the calibrated-product
  instantiation. Existing VL-SAT/Open3DSG source tables are
  retrospective. The human-audit protocol remains frozen but is not active in
  the current route. The completed 488-row two-pass Codex audit is reported as
  an LLM-based physical-validity proxy diagnostic, not independent human
  evidence.
- `sgfn_official_full_l160` provides an additional source evaluation on the
  official 157-scan test list. The correct checkpoint 160/26 tensor audit,
  preprocess, full inference, identity adapter, geometry join, 1,000-resample
  paired bootstrap, and execution audit all pass.
- At the primary SGFN K=100 endpoint, the calibrated-product instantiation
  improves over the source score:
  exact-label R rises `0.9235 -> 0.9416`, delta `+0.0181`, 95% CI
  `[+0.0134,+0.0233]`; verifier V falls `0.0630 -> 0.0381`, delta `-0.0249`,
  95% CI `[-0.0270,-0.0229]`. Both joint criteria pass on the unchanged
  3,972-row denominator. Coverage is 548/548 contexts and 36,808/36,808
  nonself directed pairs; 11 self-`supported by` GT rows are retained in the
  denominator with no synthesized predictions.
- The additional-source result strengthens the framework rather than a single formula.
  `support_contact` verifier V again regresses by `+0.00450`
  (95% CI `[+0.00370,+0.00532]`), `proximity` is unchanged at within-family
  K=100, and `relative_vertical` drives the gain. Fixed rank-average fusion
  reaches R/V `0.9476/0.0277` and satisfies the same recall/lower-V criterion
  against the calibrated product. The result supports calibrated
  geometry-consistency integration across two evaluated soft
  fusion forms, not family-uniform improvement or formula dominance.
- The official 11-scene ReplicaSSG test split with the VisualGenome-trained
  FROSS source supplies a cross-dataset transfer stress test. Its initial run
  passes all 24 source/mapping/artifact checks and contains 172 exact
  `near/above/under` GT rows over 4,290 candidates. The observed result now
  informs method development and is not treated as an external confirmation.
- The ReplicaSSG/FROSS K=100 primary gate fails. The calibrated product matches
  semantic-only exactly at R/V `0.36047/0.19674`; rank-average reaches
  `0.33140/0.03839`, with dR `-0.02907`
  `[-0.07407,+0.01333]` and dV `-0.15835`
  `[-0.19292,-0.12190]`. Product gains at K=20/50 are positive diagnostics,
  but do not repair the primary K=100 result. This is a development diagnostic
  for score-scale, displacement, geometry-domain, and ontology shift.
- Development v2 evaluates 355 source-normalized/bounded configurations on a
  regenerated 4,293-candidate FROSS execution. The all-scene choice preserves
  R@100 `.35465` and lowers V `.19674 -> .03935`, but the LOSO estimate changes
  R/V to `.31977/.03839`; its paired dR CI `[-.07548,.00000]` fails the Recall
  guardrail. Applying that Replica-developed rule on all 548 3DSSG contexts
  lowers V but sacrifices VL-SAT recall and is weaker than the existing family
  product on the main Open3DSG/SGFN tradeoff. It remains supplement-only
  development evidence.

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
| SGFN full_l160 | additional exact-label source evaluation; aggregate gate passed with verifier-V and baseline caveats |
| ReplicaSSG + FROSS | cross-dataset transfer stress test and bounded-fusion development diagnostic |
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

- Figure 1: an actual inconsistent Open3DSG relation, its structural cause,
  factor isolation, compatibility scoring, and joint evaluation; no
  review-checklist artifact appears in the figure.
- Figure 2: three-source Recall--Violation trajectories at
  K=`{5,10,20,50,100}`, with K=100 primary, K=50 secondary, and K=10
  operational.
- Figure 3: two large geometry-backed correction examples and one residual
  top-10 failure.

Current reviewer-risk verdict:

1. Circularity is mitigated but not resolved: wrong-predicate, wrong-pair, and
   transformation controls test falsifiability, while the compatibility target
   and verifier still share engineered geometric primitives. Codex proxy
   disagreement reinforces rather than closes the need for independent human
   construct validation.
2. The engineered-calibration novelty threat is partially resolved by the
   factor contract, leakage boundary, identity-preserving join, and joint
   evaluation protocol. The strong nonlinear baseline prevents a best-rescorer
   or best-formula claim, so novelty remains framework/protocol level.
3. Dataset-level generalization is unresolved: source-level generalization is
   supported under a fixed geometry-identifiable 3DSSG target, while the
   initial ReplicaSSG/FROSS K=100 transfer fails. ReplicaSSG now supports
   method diagnosis and bounded-fusion development, not an unbiased external
   estimate.

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
6. Completed: strict train-only reestablishment, internal-dev selection,
   model/score hash lock, and 548-context final benchmark evaluation. The
   current audit route uses two blinded Codex LLM proxy passes; a human-
   alignment study is optional and not active. Report split use and any
   test-specific tuning directly rather than assigning a prospective label.
7. Completed: reclassified ReplicaSSG/FROSS as a transfer-development
   diagnostic and evaluated context quantiles, bounded monotone penalties, and
   exact rank-displacement constraints. The optimistic all-scene result is not
   promoted because LOSO fails the Recall guardrail; the main claim is unchanged.

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
GeoCalib claim. SGFN remains an additional source evaluation on the known
3DSSG target. ReplicaSSG/FROSS is now used for transfer diagnosis and method
development; any selected configuration is reported with test-specific tuning.
