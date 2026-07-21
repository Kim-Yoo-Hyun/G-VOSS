# RelCompat3D / H001 Research Summary

Last updated: 2026-07-20 KST

Paper-facing name: `Beyond Semantic Confidence: Relation-Consistent Geometric Re-ranking for 3D Scene Graphs`.
Use `RelCompat3D` in manuscript-facing prose. Keep `H001` only for internal
experiment paths and archived hypothesis records.
The legacy `src/geocalib/` namespace is retained for executable compatibility;
it is not the current paper-facing method name.

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
- Active organization: six top-level sections. Problem Setup is the first
  Method subsection; Experimental Setup and quantitative/qualitative results
  are grouped under Experiments; broad interpretation and claim boundaries are
  consolidated in Discussion and Limitations.
- Active AAAI-27 outputs: `paper/aaai/main_aaai27.pdf` and the separate
  `paper/aaai/main_teaser_aaai27.pdf` comparison (both 9 US-Letter pages and
  both ending technical content on page 7), `paper/aaai/supplement_aaai27.pdf`
  (10 pages), and `paper/aaai/reproducibility_checklist_aaai27.pdf` (2 pages).
  Main/teaser/supplement SHA256 prefixes are `111b9f3c...`, `423ba83c...`, and
  `b9dc44ce...`. All have zero Type 3 or CID/Identity-H fonts and no unresolved
  citations/references or blocking LaTeX/overfull errors.
- The revised Figure 1 is a three-panel figure with a measured ordered-pair
  point cloud, separate predicate/pair-geometry/source-score paths,
  family-aware re-ranking, rank 19 to 178, and joint Recall--Violation
  evaluation. Figures 1--3 use Helvetica-compatible TeX Gyre Heros source
  typography, 2,400-pixel manuscript assets, white backgrounds,
  thin neutral separators, and restrained colorblind-safe accents. Figure 3
  removes card-style containers and redundantly encodes subject/object identity
  by point shape and box line style for grayscale printing. Relative size is intentionally absent from the submission and
  remains artifact-only secondary evidence.
- The paper reports two proposed compatibility capacities under one fixed
  framework: `RelCompat3D-Linear` and `RelCompat3D-MLP`. They share training
  rows, constructed targets, linked-pair loss, transformation averaging,
  product utility, the official 548-context universe, family sequence, and
  support/contact source order, while differing in compatibility
  parameterization. At Open3DSG K=50, Linear gives R/V `.4418/.0342` and MLP
  `.4670/.0413`; neither dominates the joint trade-off. Rank-average and RRF
  remain matched fusion baselines rather than proposed compatibility heads.
- Matched structural controls for RelCompat3D-MLP and a separate point/mesh surface audit are
  complete under `no_family_indicator_v1/evaluation/mlp_ablation/` and
  `no_family_indicator_v1/evaluation/mlp_surface_audit/`. All route, denominator,
  family-composition, support-order, and hash validations pass. At K=50, MLP
  consensus surface-V changes versus Source are `-.0238`, `-.3712`, and
  `-.0393` for VL-SAT, Open3DSG, and SGFN, with scan-cluster intervals below
  zero. The K=50 matched Linear/MLP controls are retained in the one-column
  main Table 2; the complete K=100 controls are supplemental.
- Train-only counterfactual-policy sensitivity is complete under
  `no_family_indicator_v1/evaluation/counterfactual_sensitivity/`. Nine
  one-factor refits vary the proximity
  threshold, vertical margin, negative cap, and pairwise-loss weight. The
  default model reproduces the main model exactly; internal-development ordering
  accuracy is 1.000 in every variant. Relative to the default, the maximum
  absolute change is `.0020` Recall / `.0011` V at K=50 and `.0035` Recall /
  `.0020` V at K=100. Every variant retains point-estimate gains over source
  scoring on both metrics for all three predictors at both budgets. This is a
  threshold-robustness result, not an independent physical-validity reference.
- Paired scan-cluster intervals now cover all K=`{5,10,20,50,100}`. Recall
  support is predictor- and budget-dependent, while Violation intervals are
  strictly negative except the tied SGFN K=5 point and the SGFN K=10 interval
  that reaches zero. A bounded single-process CPU benchmark reports
  3.391--4.476 ms per nonempty context after relation rows and pair geometry
  are preloaded; it is not an end-to-end source-pipeline latency claim. The
  stored heads have 66 parameters, with 43 used by the primary path.
- A frozen raw-surface construct audit is complete under
  `orthogonal_geometry_audit_v1/`. Point vertices and area-weighted mesh
  triangles define training-only audit thresholds without OBB inputs, source or
  compatibility scores, or existing verifier labels. At K=50, strict-consensus
  dV is `-.0210`, `-.4113`, and `-.0343` for VL-SAT, Open3DSG, and SGFN; all
  paired scan-cluster intervals are below zero and method coverage is
  95.5--98.2%. Strict binary-decision coverage is 71.0--83.7% at K=50 because
  point/mesh disagreement remains uncertain. K=100 is also negative on all
  three. Frozen compatibility is
  monotone under all 1,024 synthetic interventions, while raw-surface response
  is 94.7--100% monotone. This materially reduces exact OBB-rule circularity,
  but point and mesh still share the reconstructed 3RScan surface and are not
  human or cross-sensor physical ground truth.
- The main paper reports the K=50 strict-consensus surface result numerically in
  Results; the full point/mesh/consensus audit is supplemental. The
  optional first-page teaser shows a same-context Top-50 exchange: one violated
  vertical relation leaves and one exact-label proximity relation enters. The
  compact image places the full-width method overview on page 2 without changing
  the claim. Its dense gray scene projections are embedded at 621 ppi, while
  titles, relation labels, axes, object annotations, lines, and ranks are vector
  outlines.
- Related Work now includes the official CVPR-Findings 2026 GEODE boundary:
  GEODE injects geometry inside discrete-diffusion predicate generation,
  whereas RelCompat3D evaluates and re-ranks fixed candidate outputs. It also
  distinguishes RelWitness, RelGraphOV, TAD, SCR-SSG, and PUF from the fixed-candidate
  predicate--geometry compatibility setting.
- The current verified OpenReview field bundle is
  `release/h001_aaai27_openreview_20260720_084307/`. It selects the teaser main
  PDF, contains 215 internally checksummed source/evidence files, and passes
  extracted-source Docker rebuild, archive integrity, anonymity/path, JSON,
  compose, font, and canonical-PDF checks. Older factorized,
  LLM-proxy, Replica-disclosure, and reference-expansion PDFs remain historical
  provenance snapshots rather than upload candidates.
- Docker retention audit: `h001-geom-reliability:latest`,
  `h001-sgfn-confirmatory:cu128`, and `h001-aaai27-tex:20260712` are the
  protected active/full-reproduction images. The AAAI-26 image, non-main
  proposal image, and ReplicaSSG/FROSS runtime/render images are removable for
  current paper/package preservation. Exact conditional roles are owned by
  `docs/reproducibility.md`; no image was deleted during the audit.
- Main sources: VL-SAT and SGFN on all 548 official contexts, plus Open3DSG
  public-pipeline predictions evaluated on the same full 548-context target;
  the 15 public preprocessing drops receive no predictions.
- Main method: the promoted strict training-only
  `no_family_indicator_v1` transformation-consistent compatibility
  model with family-aware re-ranking. Proximity and vertical candidates use the
  product within their respective family positions;
  support/contact retains source selection exactly. Unrestricted product,
  rank-average, and RRF are comparisons, not universally dominant formulas.
- Pooled compatibility product is an ablation. Exact internal condition keys
  remain in experiment manifests rather than manuscript-facing prose.
- Factorization: `T_e` is predicate semantics, `a_e` selects the family head,
  training statistics, transformations, and ranking scope, `G_e` contains
  predicate-independent pair-geometry measurements, `Z_e` is the source relation score, and
  `C_e = sigmoid(h_a(Phi(T_e,G_e)))` is a bounded score for the constructed
  positive/counterfactual target, not a physical-validity probability. The
  leakage boundary is `Z_e notin C_e`; after transformation averaging, primary
  ranking uses `u_e = Z_e C_e^tr` for proximity/vertical and `u_e = Z_e` for
  support/contact.
- The reported evaluation scope is support/contact, proximity, and vertical
  order; the re-ranking scope is proximity and vertical order. For the latter,
  candidates are ordered by the product utility with exact-identity tie
  handling. The support/contact ordered list is defined directly as the
  corresponding source subsequence. The manuscript also discloses that
  counterfactual construction and the primary verifier share some OBB-derived
  measurements, so Violation@K is not presented as independent
  physical-validity ground truth.
- The compatibility-only control removes `Z_e`. It is
  not true `G_e`-only because the calibrator includes predicate and
  predicate-aligned interaction features.
- Main K grid: `{5, 10, 20, 50, 100}`. K=1 is sanity-check only.
- The main paper uses one joint five-budget Recall/Violation table placed before
  its quantitative interpretation and a one-column K=50 matched-control table.
  Wrong-predicate, wrong-pair, shuffled-geometry, label-fixed endpoint swap,
  distance-only, and compatibility-only results for both Linear and MLP remain
  visible in the main paper at K=50; the complete K=100 table is supplemental.
  All fixed-model,
  context, family-order, donor, denominator, and equivalence validations pass.
- Uncertainty sensitivity is complete for VL-SAT/Open3DSG/SGFN. Routed
  decidable-only and pessimistic V decrease on every source; uncertainty moves
  slightly in either direction, so the aggregate reduction is not explained by
  uniformly reclassifying failures as uncertain.
- Scan-cluster resampling is the primary interval analysis over 157 scans and
  548 contexts; context resampling is a sensitivity. At K=100, all
  routed-minus-source Recall intervals are strictly positive and all
  Violation intervals strictly negative.
- Qwen-VL is complete as a third-source / modern VLM extension, but it is not part of the main claim unless explicitly promoted.
- The optional `relative_size` family (`bigger than` / `smaller than`) has now
  completed the same 1,061/117/157 split firewall and a three-source
  K=`{5,10,20,50,100}` Docker evaluation. The learned product passes the frozen
  within-size and global four-family K=100 gates for VL-SAT, Open3DSG, and SGFN.
  This supports a possible framework-scope expansion, not a learned-formula
  superiority claim: the fixed robust-point rule matches or improves
  Violation, and rank-average does not pass the global four-family Recall guard
  on every source. The active manuscript now includes relative size only as a
  secondary scope sentence and a full supplement analysis; the headline
  learned-method evidence and main source tables remain the original three
  families.
- Strict train-only reestablishment is complete under
  `experiments/H001_geom_reliability/train_only_reestablishment_v1/`. It uses
  an exact 1,061/117/157 train/internal-dev/final firewall, zero final rows in
  fitting, a recorded execution contract, and a post-internal-dev model/score
  hash lock. It satisfies the aggregate Recall--Violation criterion. The
  manuscript reports the split roles and benchmark result directly rather than
  assigning an untouched or prospective label.
- Novelty-mechanism development was completed under
  `experiments/H001_geom_reliability/relation_algebra_v1/`. Six structured
  candidates were evaluated behind a pre-run gate. Only linked-counterfactual
  margin fitting followed by exact transformation averaging passes:
  proximity swap and vertical inverse errors are exactly zero, linked-positive
  win rate improves from .991752 to .992321, and K=100 Recall continuity holds
  on VL-SAT, Open3DSG, and SGFN. Its R/V is .9688/.0325, .6055/.0339, and
  .9418/.0372. Its `no_family_indicator_v1` strict train-only refit is now the
  active model: it removes only the constant family input, stores 66 rather
  than 69 parameters, and changes the main grid by at most 0.076 Recall and
  0.004 Violation percentage points. Every current comparator, uncertainty
  analysis, figure, and table reads from that promoted root. This strengthens
  implementation parsimony but is not a best-score result.
- The same SGFN-supervised 69-parameter nonlinear rescorer parameters were also
  used on VL-SAT and Open3DSG. The model significantly loses Recall on VL-SAT at
  K=100 and on both sources at smaller K, so it remains a source-adapted upper
  bound rather than a predictor-agnostic replacement. Outputs are under
  `experiments/H001_geom_reliability/nonlinear_transfer_v1/`.
- A supervision-matched 69-parameter nonlinear compatibility estimator is
  complete and is now reported as `RelCompat3D-MLP`. It uses the same constructed target,
  training rows, underlying predicate/pair-geometry measurements, and
  source-score exclusion as the linear model, while adding a shared-family
  indicator and an overlap-sum interaction appropriate to its shared head; the
  same fitted parameters are used for all predictors. It does not dominate the joint
  objective: on complete-coverage Open3DSG it changes product Recall by
  `+.0360` `[+.0252,+.0475]` but worsens V by `+.0096`
  `[+.0079,+.0113]`; VL-SAT/SGFN differences are small. These differing Pareto
  points motivate capacity-robust framework wording rather than head superiority.
- Transformation averaging is formalized by one exact invariance proposition;
  family-sequence and support/contact prefix preservation are stated as direct
  consequences of the ordered-list construction. For every prefix, the rule is
  utility-optimal among rankings with the same family counts and fixed
  support/contact subsequence; the supplement gives the exchange proof. A
  strict train-only three-condition primitive holdout is
  complete under `held_out_primitive_v1/`: exact-scalar removal preserves
  nearly the full result; broader primitive removal retains a strong Open3DSG
  effect but attenuates K=50 V gains on VL-SAT and SGFN.
- Reviewers A/B/C confirmed every row of the completed 488-item Codex proxy
  reference without revision. The Docker validator reports 488 resolved rows,
  three distinct reviewer IDs, and zero errors. This remains reviewer-verified
  LLM annotation in `paper/paper_nonsub/`, not Human V@K or independent blank
  first-pass human labeling.
- A no-target-tuning evaluation of the active method is complete on
  ReplicaSSG/FROSS under
  `no_family_indicator_v1/evaluation/external_transfer/`. The
  target was observed in earlier development, so this is external benchmark
  evidence rather than untouched confirmation. The routed product has paired
  joint improvements at K=10 and K=50; K=20 is positive with its Recall
  interval touching zero, K=5 is inconclusive, and the K=100 product gate fails
  because dV is `-.00096` with CI `[-.00288,.00000]`.
  The pre-frozen family-sequence-preserving rank analysis reaches R/V
  `.38372/.04223` from `.35465/.19674`; its dR CI `[-.00476,.06714]` clears
  the fixed recall guardrail and dV CI `[-.19182,-.11015]` is below zero.
  The main paper emphasizes the routed product's K=10--50 behavior and
  reports the full curve in the supplement; the rank diagnostic remains an
  artifact-level mechanism analysis. All model, data, score, and execution
  checks pass; the untouched-confirmation check is intentionally false because
  the target was previously observed. This partially mitigates the
  single-dataset concern but does not establish dataset-level generalization.

## Claim Boundary

Allowed claim:

```text
For geometry-checkable 3D Scene Graph relation families, RelCompat3D exposes and
reduces semantically plausible but geometrically inconsistent relation
predictions by applying a source-score-excluded geometric compatibility layer
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
- Dataset-level generalization beyond 3DSSG/3RScan.

## Method

RelCompat3D is a predicate-conditioned geometric compatibility and re-ranking
framework over existing relation-source outputs.

Factor contract:

| Factor | Definition | Boundary |
| --- | --- | --- |
| `T_e` | predicate label | conditions compatibility |
| `a_e` | relation-family selector | selects head, training statistics, transformations, and ranking scope; not a head input |
| `G_e` | raw, predicate-independent geometry of the same ordered object pair | excludes predicate-aligned transforms |
| `Z_e` | source relation confidence | excluded from `C_e` |
| `C_e` | `sigmoid(h_a(Phi(T_e,G_e)))` | bounded constructed-target compatibility; not physical-validity probability |
| `S_e` | `F(Z_e,C_e)` | product and rank-average are evaluated instantiations |

`y_cal` is built from training-split GT-positive rows and high-margin
counterfactual negatives. It must not be described as direct human physical
validity. Predicate-aligned center-delta features are interaction terms
`T_e x G_e`, while raw center/extent/contact/distance quantities belong to
`G_e`. The active family-specific heads contain no family indicator and exclude
the source score; factor necessity is not established uniformly across families.

Core steps:

1. Represent each relation candidate with its ordered object-pair identity.
2. Associate each candidate with 3D measurements from the same object pair.
3. Fit source-score-excluded predicate--geometry compatibility with linked
   counterfactual margins on the 1,061 training scans.
4. Average proximity and vertical scores over their valid swap/inverse
   transformations; support/contact uses only the identity transformation.
5. Preserve the source family sequence; use product ordering within
   proximity/vertical ordered lists and source-score ordering for support/contact.
6. Report exact-label `R@K` and verifier-derived `Violation@K` together.

Transformation averaging is formally invariant under each declared finite
endpoint/predicate transformation group. Family-aware re-ranking preserves the
complete family sequence and support/contact subsequence at every prefix by
construction, and selects the highest-utility candidates within each re-ranked
family subject to those constraints. The invariance appears as one proposition; the
supplement proves it and gives the constrained prefix-utility exchange proof.

Main scoring conditions:

| Condition | Role |
| --- | --- |
| Source score | source ranking baseline |
| RelCompat3D | main method; product within proximity/vertical relations, support/contact kept in source order |
| Product (all families) | compatibility product applied to every family |
| Rank-average fusion | scale-robust framework instantiation |
| RRF (`c=60`) | strong rank-fusion comparator |
| Pooled-calibrator ablation | family-conditioning ablation |
| Hard geometry filter | rule-supported diagnostic |
| Compatibility-only | no-source-score control; not true `G`-only |
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
| Open3DSG public-route prediction rows | 690,924 |
| GT rows | 11,254 |
| in-scope H001-family GT rows | 3,972 |

Primary K=50/100 source result:

| Source | Condition | R@50 | R@100 | V@50 | V@100 |
| --- | --- | ---: | ---: | ---: | ---: |
| VL-SAT | Source score | 0.9272 | 0.9635 | 0.0268 | 0.0476 |
| VL-SAT | RelCompat3D | 0.9277 | 0.9658 | 0.0197 | 0.0295 |
| Open3DSG public/full-target | Source score | 0.4043 | 0.5111 | 0.1387 | 0.1242 |
| Open3DSG public/full-target | RelCompat3D | 0.4418 | 0.5685 | 0.0342 | 0.0324 |
| SGFN | Source score | 0.7402 | 0.9235 | 0.0385 | 0.0630 |
| SGFN | RelCompat3D | 0.7450 | 0.9303 | 0.0263 | 0.0350 |

Routed K=100 paired scan-cluster deltas are Recall/Violation
`+.00227 [+.00048,+.00492] / -.01816 [-.01994,-.01656]` for VL-SAT,
`+.05740 [+.04628,+.06856] / -.09176 [-.09631,-.08727]` for the
conservative Open3DSG route, and
`+.00680 [+.00431,+.00980] / -.02797 [-.03043,-.02568]` for SGFN.
Context-bootstrap sensitivity preserves all six directions. Support/contact
selection and family composition are bit-exact with source ranking at every
reported K.

Open3DSG coverage sensitivity at K=100 is stable: public eligible 533 gives
source/method R/V `.5206/.1242` and `.5791/.0324`; public/full-target 548 gives
`.5111/.1242` and `.5685/.0324`; recovered/full-target 548 gives
`.5161/.1242` and `.5735/.0332`.

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
- Boundary: unrestricted product regresses on support/contact. The primary
  family-aware re-ranking prevents that regression by preserving source selection,
  but does not improve the family. V remains verifier-derived, so neither
  family-uniform nor support/contact-solved wording is authorized.

Historical reviewer-extension continuity result, frozen 2026-07-10:

The promoted structured-main model and current numbers are reported above.
The bullets below preserve the pre-promotion comparator audit and human-audit
boundary; they are not the active main-score table.

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
  The locked passes and complete proxy adjudication are isolated in
  `paper/paper_nonsub/` as non-submission, non-human analysis. All 154 rows
  triggered by disagreement, low confidence, ambiguity, or unobservability
  were reviewed from the blinded projection sheets. The 50 disagreements were
  resolved and 22 agreed low-confidence ambiguous labels with visible
  contradictions were revised; final valid/invalid/ambiguous/unobservable
  counts are `178/212/95/3`. Of 390 binary proxy rows, the verifier is decisive
  on 282; design-weighted agreement is `.7306` with scan-bootstrap 95% CI
  `[.6133,.8583]`, weighted kappa `.4665`, verifier-invalid precision `1.000`,
  and recall `.4713`. This supports a conservative-verifier interpretation but
  cannot replace an independent human reference.
- Three completed external verification sheets and a strict majority validator
  are ready. A synthetic all-confirm dry run produces 488/488 majority rows
  with zero errors; the real status is correctly
  `awaiting_external_reviewer_verification`. The eventual terminology is
  `reviewer-verified LLM annotation`, not independent human annotation.
- A 69-parameter nonlinear fusion baseline matches the combined parameter
  count of the three family calibrators and is fit only on disjoint internal-dev
  exact-label correctness. On SGFN it obtains R/V `0.5441/0.0120` at K=10,
  `0.8681/0.0186` at K=50, and `0.9466/0.0279` at K=100. It dominates the
  compatibility product at lower budgets and reduces K=100 verifier violation;
  therefore H001 does not claim formula optimality. The framework distinction
  is instead that RelCompat3D learns predictor-agnostic predicate--geometry
  compatibility without the source relation score or predictor-specific exact-label
  supervision, whereas this reviewer-requested rescorer uses both.
- Cross-source application makes that distinction empirical. With its SGFN
  parameters and normalization unchanged, the nonlinear rescorer changes
  VL-SAT R/V@100 from the strict family product .9690/.0327 to .9625/.0311;
  the Recall delta is -.00655 with 95% CI [-.01251,-.00185]. On Open3DSG it
  is competitive at K=100 but loses Recall by -.09718/-.17271/-.24673/-.10272
  at K=5/10/20/50. The source-specific exact-label upper bound therefore does
  not supply a stable cross-source ranking rule.
- Relation-algebra development tests six ways to give compatibility a stronger
  structure than generic feature calibration. Transformation averaging alone obtains
  exact symmetry/inverse behavior but does not improve linked-pair ordering;
  pairwise training improves ordering but remains structurally inconsistent;
  an algebra basis loses too much Open3DSG Recall. Only the combined pairwise
  model plus exact transformation averaging passes all frozen gates. It is now the main
  compatibility model after a coordinated strict-model rerun of all paper
  baselines, uncertainty metrics, figures, and tables.
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
- ReplicaSSG/FROSS now contributes a locked-final-method external benchmark in
  addition to archived development. It shows that family-aware re-ranking prevents
  the global rank-fusion Recall loss, while raw product is neutralized by 86.28%
  zero source scores. Candidate support caps Recall at .44186, 19.20% of
  external feature cells exceed three train-standardized deviations, and
  compatibility aligns verifier satisfaction (AUC .9460) more strongly than
  exact labels (AUC .6686). The result remains outside the finalized main claim
  because the target was previously observed and support/contact is unmapped.

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
| SGFN full_l160 | additional exact-label source evaluation; aggregate criterion satisfied with Violation and baseline caveats |
| ReplicaSSG + FROSS | locked-final-method external benchmark plus earlier development; positive routed-rank diagnostic, failed primary product gate, previously observed target, no dataset-generalization claim |
| `relative_size` | promoted secondary scope extension; one main-text sentence plus full supplement, not core learned-method evidence |
| `relative_horizontal` | stopped appendix/limitation scope-expansion evidence |
| `relative_lateral` | stopped appendix/future-work boundary evidence |
| `attachment_deferred` | subtype-v2 redesign/development diagnostic; not current main claim |

The latest attachment redesign replaces the legacy nine-subtype ontology with
separate predicate, physical-mechanism, and observability/applicability axes.
Its 761-row migration yields 311 candidate strict rows, while the 190,722-row
official-validation audit routes 74,433 rows to bidirectional compatibility,
19,287 to positive-only evidence, and 97,002 to abstention. A raw selective
product fails both source K=100 gates. A parameter-free bounded multiplier
passes VL-SAT K=100 but fails Open3DSG K=100 and VL-SAT K=50. This is
retrospective method-development evidence only; it does not expand the main
relation-family scope.

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
- `experiments/H001_geom_reliability/sources/sgfn/`: SGFN v3 raw source,
  adapter, geometry, coverage, and exact-label metric artifacts. Historical
  subdirectory names are retained for artifact identity.
- `experiments/H001_geom_reliability/train_only_reestablishment_v1/`: strict
  split firewall, provenance audit, train-only models, execution contract,
  internal-dev metrics, final hash lock, and official final-validation metrics.
- `experiments/H001_geom_reliability/relative_size_v1/`: frozen protocol,
  train-only size compatibility, pre-evaluation hashes, three-source five-K
  metrics, family-wise paired CIs, composition, and construct audit.
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
- `paper/outline.md`: current six-section argument and evidence placement.
- `paper/method.md`: accessible method definition and equations.
- `paper/experiment.md`: comparison, metric, and statistical contract.
- `paper/progress.md`: current completion, deferred tracks, and remaining work.
- `paper/risk.md`: reviewer-risk register.
- `paper/review.md`: consolidated three-persona review.
- `paper/appendix.md`: appendix/supplement plan.
- `paper/figures.md`: figure plan and source lock.
- `paper/aaai/README.md`: active venue-source runbook.

Current figures:

- Figure 1: an actual inconsistent Open3DSG relation, its structural cause,
  factor isolation, compatibility scoring, and joint evaluation; no
  review-checklist artifact appears in the figure.
- Figure 2: three-source Recall--Violation trajectories at
  K=`{5,10,20,50,100}` on percentage axes, with every K labeled and no selected
  operating point.
- Figure 3: an ordered-pair--evidence--outcome grid containing one proximity
  correction, one relative-vertical correction, and one residual
  support/contact case.

Current reviewer-risk verdict:

1. Exact OBB-rule circularity is substantially mitigated: wrong-predicate,
   wrong-pair, and transformation controls are now complemented by a frozen
   point/mesh audit whose labels exclude OBB inputs and existing verifier
   outputs. Separate point, mesh, and strict-consensus results agree on the
   K=50/100 direction across all predictors. Residual construct dependence
   remains because both audits use the same reconstructed PLY surface and
   dataset ontology; this is not independent physical ground truth.
2. The engineered-calibration novelty threat is materially reduced, but not
   eliminated. Factor isolation is now complemented by linked-counterfactual
   margin fitting and exact relation-algebra projection, which supply a hard
   structural property that a generic MLP rescorer does not guarantee. The
   strong nonlinear baseline still blocks best-rescorer or best-formula claims,
   and recent post-hoc constraint-refinement work blocks any claim that
   relation constraints alone are new.
3. Dataset-level generalization is explicitly out of scope. The paper is
   finalized around cross-predictor evidence across VL-SAT, Open3DSG, and SGFN
   on one 3DSSG/3RScan target; this is a scope limit rather than an unresolved
   claimed contribution.

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
8. Completed: froze and executed six relation-algebra compatibility variants.
   The combined linked-pair margin model plus exact transformation averaging is the
   only condition to pass structural, all-source joint, Recall-continuity, and
   counterfactual-ordering gates.
9. Completed: applied the unchanged SGFN-supervised nonlinear rescorer to
   VL-SAT and Open3DSG. Significant low-K Recall losses, plus a significant
   VL-SAT K=100 loss, establish that its strong SGFN result is source-adapted.
10. Completed: promoted the structurally projected candidate and regenerated
    every main comparator, uncertainty metric, family-wise paired interval,
    figure, and table on the same strict train-only model route. The
    unprojected family product remains an ablation.
11. Completed: froze and ran the current final model on ReplicaSSG without
    target-specific fitting or hyperparameter selection. All 20 validations pass. The
    routed product has paired joint gains at K=10 and K=50 but remains
    scale-limited at K=100. The supplement reports all five budgets and the
    quantization/candidate-ceiling analysis; a family-sequence-preserving rank
    diagnostic remains mechanism evidence only. The previously observed target
    prevents prospective wording.

Submission/package hygiene:

1. Completed: verified the live AAAI-27/OpenReview form, official target-year
   style, deadlines, page limits, separate checklist, and supplement policy.
2. Completed: the active-method 2026-07-20 field bundle at
   `release/h001_aaai27_openreview_20260720_084307/` passed outer/inner
   checksums, archive integrity, identity/path scans, JSON/compose validation,
   and extracted-source Docker rebuild. It supersedes the earlier field
   bundles.
3. Author action: enter author order/profiles, countries, conflicts, and the
   qualified reciprocal reviewer.
4. Author decision: final public code license and post-acceptance artifact URL.
5. Optional scientific decision: activate the frozen independent-human
   alignment study; otherwise retain the explicit Codex-proxy-only claim.
6. Completed: keep `relative_size` as an artifact-only secondary analysis. It
   is excluded from the submitted main paper, supplement, and release ZIP
   because the fixed point-rule baseline is as strong as the learned score.

No new main-source metric experiment is required to preserve the current
RelCompat3D claim. The coordinated structured-main rerun and ReplicaSSG
final-method benchmark are complete. SGFN remains an additional predictor on
the known 3DSSG target; ReplicaSSG is external diagnostic evidence rather than
an active dataset-generalization claim.
