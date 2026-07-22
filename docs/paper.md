# Paper Workflow

Last updated: 2026-07-22 KST

> **Submission snapshot.** RelCompat3D/H001 is the only active manuscript in
> the compact public repository, with `paper/aaai/main_teaser_aaai27.pdf`
> selected as the submission candidate. Historical H002 material is locally
> archived under `archive/local/pre_submission_20260722/` and is not an active
> paper claim. The H002 rules retained below are archival guidance only.

This document manages paper-level framing for RelCompat3D/H001 and retains
archival guidance for the former H002 compatibility-routing paper: novelty, contribution boundary,
reviewer-defense logic, and the minimum experiment evidence needed before paper
writing. It does not replace `docs/hypothesis.md` or Docker experiment artifacts.

## Ownership

- `docs/paper.md` is the authoritative paper-framing rulebook.
- `AGENTS.md` keeps only stable top-level claim guardrails and points here for detailed paper rules.
- `paper/README.md` owns the paper workspace map and file-role guide.
- Manuscript prose, figures, tables, venue-specific LaTeX source, and draft history live under `paper/`.
- Preserved hypothesis validation details are in the ignored local archive described by `archive/README.md`; executable code lives under `src/geocalib/`; Docker entry points live under `configs/`; source-specific experiment records live under `experiments/`; compact paper-facing summaries live under `results/`; reproducibility and artifact transfer details live in `docs/reproducibility.md`.
- Treat this file as a reviewer-facing writing rulebook. Live PDF build status,
  task status, long metric tables, row counts, and completion logs belong in
  `paper/README.md`, `paper/preview.md`, `TODO.md`,
  `docs/reproducibility.md`, or the closest experiment/report artifact.
  Durable claim decisions may be summarized here only when they change how the
  manuscript should be written.

## Source Note

- Checked on: 2026-05-14
- Reference: [Motivation is not Novelty](https://gisbi-kim.github.io/motivation-is-not-novelty/)
- Usage: paper-framing heuristic, not scientific evidence about 3D Scene Graphs.

Reviewer-process source:

- Checked on: 2026-06-25
- Reference: [CVPR 2026 Reviewer Training Material](https://cvpr.thecvf.com/Conferences/2026/ReviewerTrainingMaterial)
- Usage: venue-adjacent reviewer-process guidance. CVPR-specific policies are
  not copied as AAAI requirements, but the general evaluation lens is used:
  reviewers make evidence-based recommendations, assess core claims against
  support, weigh novelty/significance/technical soundness, avoid SOTA-only
  reasoning, and communicate specific strengths/weaknesses to the AC.

## Novelty Rule

Fact from the reference:

- Motivation is not novelty. "Existing methods fail under X, so we add module Y" is still a motivation-level argument unless the paper explains why the failure happens and why Y must take its proposed form.
- A top-tier pattern is: define a concrete failure mode, explain the underlying cause, derive the method from that cause, then verify the design through ablation, controls, generality checks, and failure analysis.
- Strong novelty is not merely a new component, combination, dataset use, or larger experiment. It is the insight that turns an observed failure into a necessary method design.

H001 rule:

- Do not claim novelty as "we add geometry", "we combine semantic and geometry", "we use a VLM", or "we implement a verifier".
- Claim novelty as a relation-consistent geometric re-ranking framework with
  separate predicate, geometry, and source-score factors. It targets a specific failure: semantically plausible
  3D relation predictions can be inconsistent with same-pair geometry because
  the source relation score is not a relation-level compatibility estimate.

## Reviewer-Process Writing Rule

Interpret the reviewer as someone writing a recommendation to an Area Chair,
not as someone merely checking whether a table beats SOTA. The manuscript
should make that recommendation easy to justify.

Author-side implications:

- A reviewer should be able to summarize the paper in 2-4 sentences after
  reading the abstract, introduction, Figure 1, and the main result table. If
  the intended claim cannot be summarized this way, the claim is too diffuse.
- Every central claim must point to specific evidence: a table, figure,
  ablation, control, failure taxonomy, calibration result, or source-grounded
  citation. Avoid relying on prose emphasis alone.
- Novelty must be positioned against named prior work. If the paper implies
  "done before" or "not done before", the text must cite the closest works and
  explain the relationship.
- Do not make the reviewer infer the acceptance case from SOTA numbers alone.
  Explain the experimental design, the failure mechanism, the insight, and the
  recall/violation tradeoff.
- Minor fixable issues should not be allowed to obscure the contribution, but
  fundamental soundness issues must be answered in the main text before
  submission. The paper should not depend on rebuttal-only new experiments.
- Limitations and caveats should be framed as scope discipline, not hidden
  weakness. A reviewer should be able to cite the limitation wording as evidence
  that the claim is honest and technically bounded.
- Tables and figures should support reviewer reasoning: Table captions must
  state denominator/scope/provenance; figures should show failure mechanism or
  evidence, not only static decoration.
- Reviewer-facing wording should use "the paper shows" style logic: problem,
  cause, method form, evidence, boundary. Avoid unsupported excitement,
  broad-field claims, or policy-like demands not required by the venue.

Reviewer-side checklist to simulate before submission:

- Can the reviewer identify the paper's core claim and non-claim without
  reading internal docs?
- Is there a clear reason why the method has this form rather than being a
  generic geometry filter, distance heuristic, or post-hoc verifier script?
- Are the closest novelty threats cited and distinguished without weakening the
  contribution?
- Are the main results reproducible and scoped enough that an AC can trust the
  denominator, source route, and caveats?
- Are weaknesses concrete and bounded, or do they suggest the contribution is
  under-evidenced?
- If the reviewer writes a weak-reject justification, which missing evidence or
  ambiguous claim would they point to? Address that point in prose, table,
  figure, or limitation wording before submission.

## RelCompat3D Claim Contract

Paper-facing title: `Beyond Semantic Confidence: Relation-Consistent Geometric Re-ranking for 3D Scene Graphs`. Use `RelCompat3D` as the method name in the abstract and main prose; keep `H001` for internal paths, provenance, and runbooks.

The former paper-facing name `GeoCalib` is retired because it collides with the
ECCV 2024 single-image camera-calibration method of that name. The existing
`src/geocalib/` Python namespace and frozen artifact strings remain unchanged
where renaming would break code or provenance identity.

Draft:

> Semantic relation predictors can rank plausible 3D Scene Graph relations without matching relation-level geometry; source-score-excluded geometric compatibility exposes this failure and re-ranks predictions while making recall--violation trade-offs measurable.

This is the preferred direction because it contains both cause diagnosis and method principle. Open3DSG second-source metrics are now available, so the paper wording should stay scoped to measured H001 families rather than broaden to full open-vocabulary 3DSSG generation.

Reviewer-defense rules after the independent-validity/family review:

- RelCompat3D uses the factorization `T_e` = predicate semantics, `a_e` = the
  selector for the family-specific head/procedure, `G_e` = predicate-independent
  measurements of the corresponding ordered pair, `Z_e` = source relation score, and
  `C_e = sigmoid(h_a(Phi(T_e,G_e)))`. This bounded score targets constructed
  GT-positive/counterfactual ordering; it is not a probability of physical
  validity.
- Enforce the leakage boundary `Z_e notin C_e`: neither the source relation score nor
  source identity is an input to the compatibility model. After transformation
  averaging, the ranking score is `u_e = Z_e C_e^tr` for proximity/vertical
  and `u_e = Z_e` for support/contact. Predicate-aligned quantities
  derived from geometry belong to `T_e x G_e`, not predicate-independent raw
  `G_e`.
- Current evidence supports a compatibility-based reliability framework, not a
  uniformly validated compatibility learner for every family. Factor-necessity
  wording requires the completed `T`-only, true-`G`-only, additive `T+G`, and
  interaction-aware `T x G` mechanism audit.
- The legacy `control_p_geom_valid_only` removes `Z_e` but retains the
  predicate-conditioned calibrator. Call it `calibrator-only (no Z)` or
  `validity-score-only`, never true geometry-only. Reserve `true G-only` for a
  calibrator that removes the predicate indicator and every
  predicate-aligned feature.
- Wrong-`T` and endpoint controls must respect the defined relation transformations. Wrong-`T` is
  primary for inverse-predicate vertical relations, `close by` is endpoint-swap
  invariant, and support/contact receives no blanket subject/object transform
  until an exact family rule is frozen. New factor/control results are post-hoc
  mechanism diagnostics, not part of the original prospective SGFN gate.

- RelCompat3D is a compatibility-based reliability framework, not a claim that
  one head capacity or fusion formula is uniquely optimal. Report
  `RelCompat3D-Linear` and `RelCompat3D-MLP` as two proposed compatibility
  estimators under the same factor separation, constructed targets, linked-pair
  objective, transformation averaging, product utility, and family-aware
  ranking rule. Their different Open3DSG Recall--Violation operating points are
  a capacity trade-off, not evidence that either universally dominates. The inference rule preserves
  the source family sequence, applies product ordering only among
  proximity/vertical candidates within the corresponding family positions, and
  preserves support/contact ordering. Treat the all-family product as an
  scope ablation; use rank-average and RRF as matched fusion baselines under the
  same family-aware ranking procedure;
  treat pooled product as a family-conditioning ablation and hard filtering as
  a construction comparison. If both compatibility capacities are main
  variants, apply the principal predicate/pair/geometry controls and the
  surface-based audit to both; compact results may remain supplemental when the
  seven-page technical limit prevents a readable main table.
- Keeping support/contact in source order removes the operational regression without
  establishing support/contact compatibility. Never convert exact preservation
  into a support/contact-improvement claim.
- ReplicaSSG/FROSS contains both prior target-specific development and a later
  evaluation of the final method without target-specific refitting. The latter must be
  described as a benchmark evaluation on a previously observed target, not an
  unbiased or prospective estimate. Its routed product has paired joint gains
  at K=10 and K=50 but saturates at K=100; report the full five-budget curve in
  the supplement. A family-sequence-preserving rank analysis explains score
  scale sensitivity, but must not replace the main rule based on this target.
  Keep bounded-fusion development outside the main Method and contribution
  list, and do not claim dataset-level generalization.

- Aggregate improvement does not authorize every-family wording. Family-aware
  re-ranking must preserve support/contact selection and global family composition
  exactly, and the paper must state that this family remains unsolved.
- A top-K aggregate can improve by changing family composition. Report both
  within-family top-K and the family slices inside the actual global top-K when
  composition is a plausible explanation.
- When semantic and geometry scores have source-dependent scales, include a
  fixed scale-robust fusion comparison such as rank-average or Reciprocal Rank
  Fusion. Do not claim calibrated-product superiority if a strong fusion
  baseline exposes a source-dependent tradeoff.
- Distinguish calibrator provenance from operating-point selection provenance.
  A calibrator fit before evaluation does not make a main-score choice
  confirmatory when that score was promoted after results were observed.
- Existing H001 VL-SAT/Open3DSG source metrics are retrospective evidence.
  Independent human labels collected under the frozen blinded protocol may be
  called prospective confirmation of physical validity only; a fresh
  exact-label confirmatory claim needs a genuinely untouched target.
- A strict train-only refit removes parameter leakage but does not erase
  historical method-selection leakage. The 1,061/117/157
  `train_only_reestablishment_v1` result may be described as a
  leakage-controlled reconstruction because final-validation rows do not enter
  fitting, normalization, or internal-dev acceptance. It must not be described
  as untouched prospective confirmation because the same official validation
  target informed earlier family/score framing. Prospective wording requires a
  new target or independently collected labels after the model and score hash
  are frozen.
- When the strict reconstruction is reported, state train/internal-dev/final
  split roles and the 548-context final evaluation. Internal gate mechanics and
  historical chronology belong in the artifact unless needed to interpret a
  reported number.
- On a fresh source, exact-label Recall may be called confirmatory only for the
  locked target and denominator. Verifier-derived Violation remains separate
  from independent human physical validity even when its preregistered CI gate
  passes.
- A fresh aggregate pass against semantic-only does not establish that the
  chosen fusion form is uniquely necessary. If a frozen rank-based baseline
  meets the same recall/violation gate against the calibrated product, claim
  the scoped framework benefit of geometry-aware reranking and report
  source-dependent operating points.
- Human Violation@K, semantic calibration, and inter-rater agreement must stay
  absent or explicitly pending until two independent blank-sheet first-pass
  label sets and blinded adjudication are complete. Reviewer A/B/C confirmation
  of the completed Codex reference is reviewer-verified LLM annotation, not a
  substitute for independent first-pass human labels.

## Archived H002 Compatibility Routing Claim Contract

This contract is retained only to interpret locally archived H002 artifacts.
The former paper, hypothesis, experiment, and result paths are stored under
`archive/local/pre_submission_20260722/`; they are not part of the active
public repository and must not modify the H001 manuscript unless the workflow
is explicitly reactivated.

Preferred claim:

```text
Source confidence does not guarantee predicate-geometry compatibility. We
separate semantic content, predicate-independent geometry, source confidence,
and compatibility, then validate scoped compatibility reranking on
geometry-checkable comparison relations.
```

Method boundary:

- `T_e`: predicate and endpoint semantics.
- `G_e`: predicate-independent same-pair geometry.
- `Z_e`: source confidence and rank.
- raw `C_e=f_C(T_e,G_e)`; `Z_e` is prohibited from `C_e`.
- source score is normalized per source; raw compatibility is normalized per
  source-family candidate pool.
- final score is
  `S2_source_x_Ce = normalized_source_score * normalized_C_e`.
- the logistic compatibility model is fit on internal-train rows only;
  official validation rows are evaluation-only.

Current claim boundary:

- main validated: higher/lower and bigger/smaller.
- caveated validated: left/right, with source-dependent Recall tradeoff.
- geometry-only control: close by.
- failure analysis: front/behind.
- diagnostic only: standing on, lying on, supported by.
- evaluation split: official 3DSSG validation.
- sources: VL-SAT and Open3DSG validation predictions.
- metrics: Recall@K and custom Violation@K with grouped bootstrap CI.
- Open3DSG is an open-vocabulary source, but quantitative Recall uses the
  closed-vocabulary 3DSSG mapping.

Blocked wording:

- official hidden-test, leaderboard, or SOTA result.
- solved all-relation reliable 3D Scene Graph framework.
- support/contact solved.
- learned-G_e final-score improvement.
- calibrated p_obs/p_rel solved.
- normalization-invariant improvement.
- uniform left/right improvement across sources.
- treating Violation@K as an official 3DSSG metric.

Required reviewer defense:

- model-safe `T_e+G_e`, reranking-only `Z_e`, and hidden metric views stay
  separated.
- compare source-only, geometry-only, plain concatenation, and matched
  compatibility.
- include wrong-predicate, shuffled-geometry, and wrong-pair controls.
- report Recall and Violation jointly, with K-specific grouped CI.
- disclose label-free candidate-pool normalization and sensitivity.
- keep support/contact target imbalance and construction-rule recovery in the
  limitation/failure taxonomy.
- distinguish the proposed route map from routes that are quantitatively solved.

Historical metrics and progress remain in the local archive. Current H001 state
belongs to `summary.md`, `TODO.md`, and the active H001 experiment/results
READMEs.


Current paper-facing evaluation direction:

- The primary result should use the full official `3DSSG_subset` validation
  split, not the pilot-excluded 127-scan hardened scope.
- Full-validation VL-SAT, Open3DSG, and SGFN artifacts exist. VL-SAT is the
  controlled anchor. Open3DSG's main result uses public-pipeline predictions
  from 533 contexts on the label-independent official 548-context target, with
  zero predictions in the 15 missing contexts. Public-eligible 533 and
  recovered/full-target 548 routes remain sensitivities.
- The recovered Open3DSG branch uses `min_visible=2` and relaxed two-scan view
  regeneration. It must never be described as the unmodified public route.
- The method provenance must be stated as train/train-dev-derived: final family
  mapping, hard-rule policies, counterfactual construction, and `p_geom_valid`
  calibration are frozen before validation source-result reporting.
- H001-Mini is hypothesis/feasibility evidence, not a paper metric split and
  not a calibrator/threshold fitting split.
- Source-result tables use the public/full-target route. The 533 eligible and
  recovered 548 variants show that the conclusion is not created by denominator
  restriction or recovery policy.
- Table policy is fixed: one joint Recall/Violation table uses VL-SAT,
  Open3DSG public/full target, and SGFN at K=`{5,10,20,50,100}`. Its rows are
  Source score, RelCompat3D-Linear, RelCompat3D-MLP, matched rank-average,
  matched RRF, and Product (all families). Pooled product is supplemental.
  Full K=50/100 Linear/MLP six-control tables are supplemental because a matched
  two-capacity grid is not readable within the seven-page body; hard filtering
  remains a construction comparison outside the primary table.
  Historical
  127-scan Open3DSG numbers are appendix/sensitivity evidence only, where the
  representative historical branch is the completed R2 388/388 sensitivity
  branch and the old 377/388 branch is retained as the comparison row. R2
  provenance review confirms clean-return raw files are row/predicate-score
  equivalent to the canonical R2 raw dump after excluding run metadata, but the
  process-level teardown/OOM exit-137 caveat remains visible.

2026-06-14 paper/package update:

- Low-K reporting is acceptable as a top-rank reliability diagnostic and may be
  shown in the main source-result table for K = `{5,10,20,50,100}` if matching
  metric/CI provenance is present. K=1 is excluded from paper metrics.
- Qwen-VL full official validation downstream is complete and may be discussed
  as third-source modern-VLM extension evidence. It does not replace the
  VL-SAT/Open3DSG main-source route and should not widen the main claim unless
  explicitly promoted.
- Active target-year build uses official `aaai2027` source. Outputs are
  `paper/aaai/main_aaai27.pdf` and the optional
  `paper/aaai/main_teaser_aaai27.pdf` comparison (both 9 pages with technical
  content ending on page 7), `paper/aaai/supplement_aaai27.pdf` (10 pages), and
  `paper/aaai/reproducibility_checklist_aaai27.pdf` (2 pages). Final main log:
  `logs/20260718_figure_refine_final_main.log`. The current verified
  OpenReview bundle is `release/h001_aaai27_openreview_20260720_084307/`; it
  selects the teaser main PDF and contains the promoted active-method source,
  locks, and compact results. Earlier
  source-validation PDFs, the 2026-07-12 field bundle, and compact tarballs are
  historical snapshots.

2026-06-25 H001_v2 decision, superseded in scoring role by the 2026-07-10
framework-first decision:

- H001_v2 fixed-`tau*` risk-controlled reranking and pooled lambda-soft
  reranking are diagnostic candidate evidence only. Neither should replace the
  current H001/RelCompat3D main result route or be added to the main table.
- The family-conditional calibrated product remains a soft RelCompat3D
  instantiation: `semantic_score * p_geom_valid_family`, where each relation
  family has its own calibrated geometry-risk surface. It is not the unique
  method definition or a universally dominant score.
- The pooled `semantic_score * p_geom_valid` score is now an ablation/baseline,
  not the main score. It can be explained as the pooled `lambda=1` log-linear
  risk-aware reranking instance. The calibration-selected pooled `lambda=1.25`
  source evaluation remains diagnostic because it is mixed against the fixed
  paper scores.
- Calibrator-only, distance-only, shuffled-geometry, and wrong-pair variants
  remain controls. The legacy `p_geom_valid`-only ranking is calibrator-only
  because its model includes predicate/family features; it is not the new true
  `G`-only factor baseline and is not the same as pooled calibrated reranking.

Paper workspace ownership:

- `paper/README.md` is the folder-local entry point and records the roles of the paper files, reading order, and update ownership.
- `paper/preview.md` is the current handoff snapshot for the paper claim, evidence, canonical build/release pointers, and remaining user tasks.
- `paper/progress.md` records only current completion, fixed decisions, deferred tracks, and remaining work; historical run chronology belongs in experiment reports and repository history.
- `paper/outline.md` owns the current six-section causal narrative, three contribution statements, section responsibilities, and figure/table placement. Cross-predictor results and failure analysis are empirical validation, not a separate fourth contribution.
- `paper/method.md` explains the implemented factorization, constructed supervision, objectives, relation-algebra consistency, score combination, and family-aware ranking without research-log terminology.
- `paper/experiment.md` explains the comparison contract, exact-label Recall, verifier-derived Violation, uncertainty accounting, family analysis, and paired scan-cluster inference in accessible mathematical form.
- `paper/draft.md` is a secondary prose workspace; the canonical submission text
  is the active LaTeX source under `paper/aaai/`.
- `paper/risk.md` tracks reviewer-risk attacks, mitigation status, and priority for logic/evidence/novelty/reproducibility defenses.
- `paper/review.md` consolidates the current novelty/method, experimental-validity, and writing/presentation reviews.
- `paper/appendix.md` owns appendix/supplement provenance tables, detailed Open3DSG caveat consistency checks, optional Figure 3 decisions, and Qwen-VL extension boundary notes.
- `paper/aaai/` is the current target-venue LaTeX source. It uses the official
  AAAI-27 style (`aaai2027.sty`, template version 2027.1), splits the draft
  into `main.tex` plus `sec/*.tex`, points bibliography to
  `paper/references.bib`, and builds the reproducibility checklist as a
  separate OpenReview PDF. Docker PDF build is verified with
  `h001-aaai27-tex:20260712`; the final main/supplement/checklist build log is
  `logs/h001_structured_main_final_20260713.log`.
- `archive/paper/iccv/` remains a historical/alternate ICCV-style source route.
- `paper/figures.md` is the authoritative redraw specification for Figure 1--3, including composition, flow, exact plot values and coordinates, case sources, captions, and non-claims; generated assets remain under `paper/generated/figures/`.

## H001 Fit To Top-Tier Pattern

Facts:

- H001 already has a concrete failure target: geometry-checkable relation families such as `support_contact`, `proximity`, and `relative_vertical`.
- Hypothesis-stage `VL-SAT` evidence includes semantic-only vs calibrated geometry variants, family-conditional risk evidence, evidence lock, GT-based verifier evaluation, and a reduced visual sanity check.
- The Open3DSG path is now second-source evidence: Docker checkpoint reproduction, raw-dump identity, adapter export, geometry join, metric eval, Table 6, real failure rows, qualitative case queue, and deterministic qualitative inspection are ready.
- Docker subgraph bootstrap CI is ready under `results/h001_geom_reliability/bootstrap_ci/`; it is used as evaluation-context uncertainty, not repeated-training variance.
- Open3DSG qualitative inspection shows both support and limits: 23/36 sampled cases are demoted by geometry-aware reranking, while 10/36 are rule-violated but still have `p_geom_valid > 0.9`. This must be framed as residual calibration risk, not hidden.
- The historical 127-scan Open3DSG branch has two roles. The old 377/388
  avg-BLIP branch has clean raw-dump source-process provenance via v14
  streaming same-path resume and remains a comparison row with filtered train
  split, averaged-BLIP variant, covered loadable scope, and
  `validation_missing_preprocessed:11`. The R2 covered-recovery branch reaches
  388/388 contexts and completes raw identity, adapter export, geometry join,
  metrics, bootstrap CI, and table/caveat reporting; it should be the
  representative historical sensitivity branch. Its process-level raw dump
  still exits 137 after finalization, so it is not promoted as clean
  process-level provenance.
- The paper-facing Open3DSG full-validation branch uses the selected official
  non-avg BLIP checkpoint and `recovery_relaxed_views_min2/`. Its required
  caveat is different: disclose filtered train/dev provenance, exact-label
  denominator, residual calibration risk, and the recovery policy
  (`OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus relaxed view regeneration for two
  scans). Use the 533/548 covered full-validation branch as sensitivity evidence
  for unmodified source-route behavior.
- `relative_horizontal` is the preferred relation-scope expansion track, not
  part of the current claim. Docker `relative_horizontal_scope_audit` confirms
  3,570 candidate GT rows and an expanded denominator of 6,115/7,505 if
  validated; source rows exist for VL-SAT (103,664) and Open3DSG (76,400), but
  both are currently verifier-unsupported. The coordinate-frame protocol is
  frozen under `sources/relative_horizontal/coordinate_frame_protocol.md`.
  Docker `relative_horizontal_coordinate_audit` is complete but blocked for
  promotion: selected frame `scan_left_neg_x_front_neg_y`, macro strict purity
  0.7725, strict eligible share 0.6403, `left`/`right` purity 0.8005,
  `front`/`behind` purity 0.7445, inverse consistency 1.0, wrong-frame gap
  0.1231. Docker `relative_horizontal_bucket_inspection` is also complete:
  `front`/`behind` strict match:contradiction is 2.9143, sign-only purity is
  0.7491, and ambiguity buckets remain large (`axis_margin_ambiguous` 230,
  `conflicting_axis_dominates` 430, `strong_projected_overlap` 44). The
  recommendation is `do_not_promote_relative_horizontal_to_main_claim`.
  Current AAAI-path decision is to freeze this as appendix/limitation evidence,
  not to run expanded-family metrics. Future promotion would require resolving
  this coordinate-frame/label-semantics gap plus verifier policy, calibration,
  controls, source metrics, bootstrap CI, and failure/audit evidence at the
  current H001 evidence standard. Reviewer-facing use should be threshold-free
  evidence first, with the predeclared gate treated only as a conservative
  non-promotion rule.
- `relative_lateral` was tested as a narrower left/right-only split after
  `relative_horizontal` failed full-family promotion. It is now stopped for the
  current AAAI path. Policy freeze records 2,264 GT rows and selected frame
  `scan_left_neg_x_front_neg_y`; train/dev policy lock is caveated with train
  positive strict purity 0.8738 but dev positive strict purity 0.6975. Dev
  failure diagnosis shows 72 contradiction rows / 36 physical pairs concentrated
  in two scans, 140 uncertain rows / 70 physical pairs, about half same-label
  object pairs, and mostly orthogonal-axis dominance. Treat this as
  appendix/future-work boundary evidence, not source-metric evidence.
- `attachment_deferred` is the preferred future relation-family upgrade if H001
  is expanded beyond the current AAAI claim. Its metrics are retrospective
  development diagnostics, not current main-claim evidence.
  Docker G0 scope/schema audit, G1 extractor contract, G1b evidence-only dry
  run, G1c point/surface estimator validation, G2 verifier-policy design, G3
  train-dev calibration/counterfactual route, G4 GT policy smoke, G4b
  error/visual sanity planning, G4c strict-only calibration-filter freeze, G5a
  pooled strict calibration fit, G5b bounded source scoring preflight, and G5c
  full-source protocol freeze are complete with status
  `attachment_deferred_full_source_protocol_frozen_no_metrics`:
  the denominator policy records 967 GT rows (`attached to` 808, `hanging on`
  126, `connected to` 33), candidate denominator 3,512 if validated, and
  candidate prediction rows for VL-SAT (77,748) and Open3DSG (57,300); both
  sources are currently verification-unsupported for this family. G2 covers 9
  conservative subtypes, G3 prepares 315 train/dev positive seeds plus 446
  counterfactual negative seeds, and G4 applies the frozen policy to 36 smoke
  rows plus 761 train/dev seed rows. G4 decision-schema validation passes with
  ready evidence for 761/761 seed rows, positive nonviolated 0.9048,
  counterfactual nonsatisfied 0.8274, positive strict satisfied 0.3841,
  counterfactual strict violated 0.4574, and overall uncertain rate 0.4323. At
  G4 it emitted no fitted calibration, source scoring, or source metrics. G4b
  freezes 436 review cases, a 50-row label-diverse visual sanity queue, strict
  positive candidates 121, strict negative candidates 204, false-satisfied
  counterfactuals 77, false-violated positives 30, and uncertain rows 329. G4c
  freezes 325 strict calibration rows, including 121 strict positives and 204
  strict negatives, and excludes 436 non-strict rows. G5a fits pooled model
  `h001-attachment-deferred-p-geom-valid-strict-v1`; dev Brier/NLL/ECE are
  0.0010/0.0077/0.0071 and dev AUROC/AUPRC are 1.0/1.0 on 83 strict rows.
  These numbers are calibration-readiness evidence only, because the strict
  subset is policy-selected and nearly separable. G5b scores 120 bounded,
  scan-diverse source rows with evidence ready 120/120 and validation errors 0.
  G5c freezes 69 deterministic full-source shards for 135,048 rows, metric
  conditions, control order, and source-specific exact-label denominators:
  VL-SAT covers 967/967 attachment GT rows, while Open3DSG covers 768/967 and
  has 199 missing exact-label GT rows. G5d full-source metrics are complete,
  but mixed source behavior and the verifier-derived target block promotion.
  `connected to` has no legacy dev strict rows, so pooled calibration or an
  explicit caveat is required. This
  direction is better aligned with
  the H001
  physical-consistency thesis than `relative_horizontal`, because attachment,
  hanging, and connection imply physical support/adjacency, near-surface
  contact, gravity, and object-affordance constraints. Its risk is rule
  complexity: it requires validated wall/ceiling/furniture surface evidence,
  local point contact, surface normals, hanging geometry, contradictory support
  handling, and conservative uncertain handling. Treat it as a future upgrade
  path whose next gates are subtype redesign, mechanism/observability review,
  rebuilt targets and verifier, and a new model/evaluation lock before any
  main-claim promotion.
- Attachment subtype v2 supersedes the legacy nine-subtype framing for future
  work. It separates predicate semantics, physical mechanism, and
  observability/applicability; `ambiguous_*` is no longer a physical subtype or
  automatic calibration label. Counterfactuals inherit their base-positive
  mechanism. Direct attachment/hanging may use bidirectional compatibility,
  while `connected to` remains positive-only until direct versus mediated
  ontology is resolved. No blanket endpoint swap is allowed.
- The v2 Docker migration covers 761 train/dev and 190,722 official-validation
  rows. Raw selective fusion fails. The bounded multiplier passes VL-SAT K=100
  but fails Open3DSG K=100 and VL-SAT K=50. Keep both as transparent
  development diagnostics; neither is a validated extension or paper result.
- Qwen-VL is currently a third semantic source / modern VLM extension, not a VL-SAT or Open3DSG replacement.
- The 2026-05-23 RelWitness full-PDF skim identified a stronger direct novelty threat: RelWitness uses visual-geometric relation witnesses, calibrated witness quality, witness-guided positive-unlabeled learning, and witness-consistent decoding. Its v2 numerical tables are simulated planning values, so it should sharpen H001 wording rather than replace H001's reproduced evidence.

Inference:

- The direction is aligned with the top-tier pattern if the paper is framed around failure mechanism plus calibrated geometry-consistency, not around a verifier script.
- The current evidence is stronger than a motivation-only project because it already has scoped metrics, controls, and audit artifacts.
- The top-tier risk has shifted from "single-baseline only" to claim scope and
  denominator transparency: reviewers may accept measured cross-source
  reliability evidence, but can still attack broad open-vocabulary wording,
  filtered denominator handling, selected-checkpoint provenance, and the
  full-validation recovery-policy branch.

User judgment needed:

- Whether to keep the final paper claim as a scoped reliability layer or push for broader open-vocabulary 3DSSG improvement depends on Open3DSG metric quality and failure-analysis strength.

## Reviewer Attack Surface

Likely reviewer questions:

- Is this just a hand-coded geometry verifier?
- Does geometry re-ranking improve relation prediction or only filter easy cases?
- Are gains caused by a narrow subset of relation labels?
- Does the method preserve useful recall, or does it trade recall for fewer violations?
- Does the result generalize beyond `VL-SAT` and one closed-set prediction source?
- Are the geometry rules calibrated, or manually chosen after looking at the test set?
- Are skipped Open3DSG train/eval samples changing the denominator in a way that favors H001?
- Does Qwen-VL add scientific evidence, or only a modern engineering option?
- Can the framework expand beyond the current three relation families without
  turning into an ad hoc relation-specific verifier?
- If `attachment_deferred` is the next family, are attachment and hanging rules
  physically grounded rather than class-affordance guesses?

Required defense:

- Present the method as a calibrated framework with explicit design choices, not as a script.
- Include semantic-only, calibrated product, evaluated rank-average, RRF,
  pooled calibrated ablation, rule-only diagnostic, and true control variants.
- Include wrong-pair or shuffled-geometry controls to show the geometry signal is not accidental.
- Report recall and violation metrics together.
- Keep denominator and filtered-split caveats visible in every table using Open3DSG.
- Use Open3DSG as the main open-vocabulary case study before considering any broad claims.
- Report residual calibration-risk cases separately from rule-verified results.
- Treat Qwen-VL as a third semantic-source extension unless it receives the same Docker, metric, and audit treatment.
- Treat `relative_horizontal` as a separate validation track until coordinate-frame ambiguity is resolved and the evidence reaches the same standard as the current claim. The current coordinate audit is partial/blocked, so it is not main-claim evidence.
- When discussing that track, do not rely on the operational purity threshold
  as if it were an official benchmark. Report raw diagnostics and effect sizes:
  best frame, wrong-frame gap, inverse consistency, per-label breakdown, and
  ambiguity buckets.
- Treat `attachment_deferred` as the preferred future physical-relation upgrade.
  The Docker scope/schema audit, extractor contract, schema-validated
  evidence-only dry run, point/surface estimator validation, conservative
  verifier-policy design, calibration/counterfactual route, G4 policy
  smoke/GT-counterfactual evaluation, G4b visual-sanity queue, G4c strict
  calibration-filter freeze, G5a pooled strict calibration fit, and G5b bounded
  source scoring preflight, G5c full-source protocol freeze, and G5d
  full-source scoring/metrics/controls/bootstrap are complete, but do not
  promote it from "future upgrade" to "main result" before Open3DSG denominator
  caveats, noisy `attached to` behavior, missing `connected to` dev strict rows,
  and failure/visual audit are resolved or explicitly bounded. Visual labels
  remain optional for a soft protocol, not required for the frozen strict-only
  calibration route.
  The v2 redesign is the active future route, but its raw and bounded source
  diagnostics both fail at least one primary/secondary operating point. Require
  the frozen mechanism review and rebuilt target/verifier contract before any
  new promotion attempt.
  Function-reasoning examples may be useful as a secondary case study only
  after relation reliability is established.
- Treat RelWitness-style "relation witness" and "calibrated witness quality" wording as prior-art-adjacent. H001 should claim reproduced calibrated reliability evaluation/re-ranking, source-adapter protocol, recall/violation operating points, and controls, not the mere existence of visual-geometric evidence or calibration.

## Main Paper Evidence Checklist

Minimum table/figure set before paper writing:

- Table 1: joint exact-label Recall and verifier-derived Violation across the
  three predictors and fixed `K={5,10,20,50,100}` grid; the caption owns the
  denominator and condition roles.
- Table 2: compact one-column K=50 wrong-predicate, wrong-pair,
  shuffled-geometry, label-fixed endpoint-swap, distance-only, and
  compatibility-only controls for both proposed heads. Keep the complete K=100
  control table in the supplement.
- Prose: source-specific claim boundary / non-claims, GT verifier evaluation,
  audit, visual sanity checks, and detailed family rows unless an appendix is
  added. The old claim-boundary table is demoted to prose.
- Figure 1: failure mechanism and framework overview.
- Figure 2: source-score versus RelCompat3D-product Recall--Violation
  trajectories over all five K values for each predictor.
- Figure 3: qualitative failure taxonomy with geometry-backed examples where semantic plausibility and physical consistency diverge.

## Non-Claims

Do not claim these until evidence exists:

- Broad SOTA improvement for open-vocabulary 3DSSG.
- Baseline-agnostic improvement across arbitrary relation predictors.
- Qwen-VL as a replacement main baseline.
- Geometry rules as universally correct relation semantics.
- Full open-vocabulary 3DSSG improvement beyond measured H001 families.
- `relative_horizontal` coverage as part of the main claim before its separate
  validation track passes coordinate-frame, calibration, metric, control,
  bootstrap, and audit gates.
- `relative_lateral` coverage as part of the main claim from the current
  strict policy. The train/dev gate is caveated and the dev diagnosis points to
  coordinate/frame-orientation ambiguity.
- `attachment_deferred` or functional-reasoning coverage as part of the main
  claim before the attachment-specific source metrics, controls, and audit
  gates pass. The completed G0 scope/schema audit, G1 extractor contract, G1b
  dry run, G1c point/surface validation, G2 verifier-policy design, G3 seed
  route, G4 policy smoke, G4b visual-sanity queue, G4c strict-filter freeze,
  G5a pooled strict calibration fit, G5b bounded source scoring preflight, and
  G5c full-source protocol freeze are upgrade-readiness evidence only.
- Adding any expansion family to the main AAAI claim without explicit final
  user confirmation, even if the later evidence gates pass.
- Broad Open3DSG reproduction/SOTA claims; current evidence is a selected
  full-validation source-output branch with explicit recovery-policy caveat.

## Paper-Framing Guardrails

- Claim consistency is governed by `paper/outline.md`: the title, contributions, six-section argument, and evidence placement preserve the scoped relation-reliability claim.
- Implementation-faithful method and evaluation explanations are separated into `paper/method.md` and `paper/experiment.md`; the outline should point to them rather than duplicate their equations or comparison definitions.
- The canonical title, Abstract, and section prose are maintained in
  `paper/aaai/`; `paper/draft.md` is not the submission source.
- Figure 1-3 source lock is complete in `paper/figures.md`: Figure 1 is an
  actual-failure-to-framework overview, Figure 2 connects
  Recall--Violation trajectories at K=`{5,10,20,50,100}` across VL-SAT,
  Open3DSG, and SGFN, and Figure 3 shows two geometry-backed corrections plus
  one residual support/contact case.
- Draft Figure 1-3 generation, top-tier novelty/layout review, and Figure 3 geometry-backed panel upgrade are complete under `paper/generated/figures/`; validation passed for locked values, case IDs, geometry case IDs, and SVG XML parsing.
- Recent 2025-2026 Related Work roles are decided: RelWitness is a required direct novelty-threat citation, VIZOR is a required spatial-relation/viewpoint-boundary citation, ZING-3D is a VLM/incremental 3DSG trend citation, Open-World 3DSG-RAG is a broad open-world/RAG boundary citation, and View-on-Graph is a downstream grounding-motivation citation.
- Section structure is locked to six top-level sections: Introduction, Related
  Work, Method, Experiments, Discussion and Limitations, and Conclusion.
  Problem Setup is the first Method subsection; Experimental Setup and all
  quantitative/qualitative results are subsections of Experiments.
- Section-title rule: use standard paper headings such as `Experiments`, `Experimental Setup`, `Evaluation Setup`, `Datasets`, `Evaluation Metrics`, and `Implementation Details`. Do not put `Scope` in the heading unless the target venue/template makes it necessary; H001's scope and denominator discipline should be stated in the first paragraph and tables.
- The section-title reference check supports `Experiments` as the top-level
  heading and `Experimental Setup` as its first subsection, with scope and
  denominator details stated in prose and tables rather than in a defensive
  section title.
- Target venue direction is AAAI-style main conference writing. Content stability and AAAI page/checklist compliance come before final camera-ready polish.
- `paper/draft.md` Title/Abstract/Introduction quick review is complete; front matter is about 701 words excluding title, with a 201-word abstract and 500-word Introduction before final compression.
- Paper-body gap review patch is complete: Figure 1-3 callouts, Table 4 audit/sanity prose, and Conclusion are now in `paper/draft.md`.
- Paper-body budget review is complete. The current AAAI manuscript uses two
  main tables: the five-budget cross-predictor comparison and the compact K=50
  matched-control table. The surface-based audit is quantified in Results and
  tabulated fully in the supplement; complete K=100 controls also remain there.
- AAAI-style source conversion is complete under `paper/aaai/` using the
  official AAAI-27 Author Kit preserved in the repository. The active source
  uses `aaai2027.sty`/`aaai2027.bst` and template version 2027.1.
- The `paper/aaai/` manuscript-content pass is complete: it includes fixed scope/denominator accounting, a main source-results table, a controls/diagnostics table, prose claim-boundary/verifier/audit evidence, explicit Open3DSG caveat captioning, and limitation wording.
- Figure 1--3 keep editable SVG sources and are included as 300-ppi-or-higher
  PNGs to avoid CID/Identity-H font dependencies. Figures 2 and 3 use full width so
  their K labels, ordered-pair geometry, and residual case remain legible.

## H001 Current Claim Lock, 2026-07-15

- Narrative order is failure -> structural cause -> factor-isolation
  necessity -> method -> evidence -> scope/limitations. Repeated defensive
  provenance language belongs in limitations, captions, or the supplement,
  not in the opening contribution pitch.
- Novelty is the source-score-exclusion contract `Z notin C(T,G)` for a shared
  model whose inputs also exclude predictor identity,
  identity-preserving geometry join, falsification controls, and joint
  Recall--Violation--uncertainty evaluation. Do not claim a novel or optimal
  fusion formula. The ranking construction may be described as prefix-utility
  optimal only under fixed source family counts and a fixed support/contact
  subsequence; this is not global metric or fusion optimality.
- The finalized main-claim scope is multiple semantic predictors on one shared
  3DSSG/3RScan target for relations testable from reconstructed pair geometry.
  ReplicaSSG/FROSS provides
  zero-target-fitting external diagnostic evidence for the unchanged model, but
  its previously observed target, 44.19% candidate-recall ceiling, absent
  support/contact mapping, and K=100 score saturation block a dataset-
  generalization claim.
- The main compatibility is linked-counterfactual margin fitting followed
  by exact proximity-swap / vertical-inverse transformation averaging. Paper prose
  calls it **relation-consistent compatibility**; the internal
  `orbit_pairwise_projected_product` name appears only in provenance artifacts.
  The active family-aware ranking procedure, matched comparators, controls, and
  interval analyses come from the synchronized
  `no_family_indicator_v1/evaluation/` route. The former
  `support_contact_routing_v1`, `structured_main_v1`, and
  `structured_ablation_v1` outputs are historical pre-promotion evidence.
- Visual Commonsense Driven Knowledge Refinements for Scene Graph Generation
  (Neau et al., 2026) is a required closest-work citation. It already provides
  model-agnostic post-hoc SGG refinement, mines symmetry/inverse/composition
  constraints, and reports Constraint Violation Rate. Therefore do not claim
  the first post-hoc constraints, first relation-algebra refinement, or first
  violation metric. The defensible distinction is continuous source-excluded
  3D same-pair compatibility with identity controls, linked counterfactuals,
  exact algebra projection, and recall/violation/uncertainty accounting.
- `RelCompat3D-MLP` excludes the source score and predictor identity and uses
  the same constructed training rows, targets, objective, transformation
  averaging, product utility, and family-aware ranking as `RelCompat3D-Linear`.
  Its different parameterization yields a distinct operating point rather than
  joint dominance. A separate
  SGFN exact-label nonlinear rescorer uses stronger source-specific supervision;
  its strong result must be disclosed and blocks best-rescorer claims.
- Report K=`{5,10,20,50,100}` together. Use K=50 descriptively as a mid-curve
  reference, not as a separately registered endpoint, and describe K=10--50
  behavior without an unsupported operational-use claim;
  retain K=5 and K=100 in the table and trajectory as low-/high-budget
  boundaries. At K=50, Violation decreases on all three predictors, Recall
  improves on Open3DSG and SGFN, and near-ceiling VL-SAT has no detectable
  Recall change. Never convert pointwise trends into an all-K universal
  dominance statement.
- Generalization evidence is primarily cross-predictor under a shared,
  geometry-identifiable 3DSSG target. The ReplicaSSG/FROSS supplement reports a
  retrospective transfer stress test: joint gains at K=10 and K=50, an
  inconclusive K=5 boundary, and K=100 saturation under score quantization. It
  must not be framed as established external-dataset generalization.
- Codex proxy labels, complete mandatory adjudication, and verifier--proxy
  evaluation are non-submission diagnostics under `paper/paper_nonsub/`. The
  active AAAI paper contains no Codex-derived physical-validity result;
  independent human construct validation remains open. Reviewers A/B/C have
  confirmed every completed LLM-reference row with zero revisions; this route
  is named reviewer-verified LLM annotation rather than independent human
  annotation.
- The frozen `orthogonal_geometry_audit_v1` is admissible non-human
  construct-validity evidence: it uses raw instance vertices and area-weighted
  mesh triangles, excludes OBB/model/verifier inputs from label assignment, and
  reports point, mesh, strict consensus, coverage, all K, and paired scan-cluster
  intervals. Describe it as an orthogonal raw-surface audit, not an independent
  physical-validity ground truth, because both estimators share the reconstructed
  3RScan surface and ontology.
- Docker verification is complete with `h001-aaai27-tex:20260712`: BibTeX
  uses 34 entries and targeted checks find no missing citations, undefined
  references, overfull boxes, LaTeX errors, Type 3 fonts, or AAAI package
  errors. The checklist is built separately from
  `paper/aaai/reproducibility_checklist_main.tex`; the legacy
  `sec/9_reproducibility_checklist.tex` is not included in the active paper.
- AAAI reviewer-defense main-text pass uses the public/full-target Open3DSG
  route. Recovery details and the 533/548 sensitivity are kept in the
  supplement rather than presented as the primary pipeline.
- The 2026-05-27 appendix/caveat pass is complete: `paper/appendix.md` records the calibrator/threshold provenance table and caveat consistency pass; experiment Table 6 includes `caveat_note`; Docker PDF rebuild `logs/h001_aaai_pdf_build_appendix_caveat_20260527_202734.log` exits 0 with 9 total pages and no blocking warnings.
- Draft bibliography scaffold is complete in `paper/references.bib`; citation keys used by `paper/aaai/sec/*.tex` match the bibliography entries.
- Use `paper/generated/figures/figure3_geometry_panels.svg` as the Figure 3
  source. Keep its white background, unboxed three-column evidence layout,
  embedded manuscript-compatible sans-serif font, restrained semantic colors,
  and redundant subject/object shape encodings. A rendered scene-crop upgrade
  is optional only if a deterministic crop/render path is added.
- Keep Open3DSG caveats explicit in manuscript Table 2 and experiment artifact
  Table 6; later compression must retain selected official non-avg checkpoint
  provenance, filtered-train/dev provenance, exact-label denominator, residual
  calibration risk, and the `recovery_relaxed_views_min2/` policy. If reporting
  the historical 127-scan branch, keep it outside the main source-result table
  and compare old 377/388 against R2 388/388 as appendix/sensitivity evidence;
  retain averaged-BLIP, covered loadable scope, and
  `validation_missing_preprocessed:11` only for the old comparison row.
- Source-results table and failure-analysis text are regenerated from the
  selected full-validation route rather than the older 127-scan caveat wording.
- Keep clean v14 streaming source-process provenance separate from historical exit-137 run records in reproducibility wording.
- Keep Qwen-VL as third-source extension evidence unless explicitly promoted. Full official validation downstream is complete for the extension route, including parser validation, adapter export, geometry join, metrics/controls, bootstrap CI, failure rows, and deterministic qualitative inspection, but this does not replace the VL-SAT/Open3DSG main-source route.
- Keep the `relative_horizontal` expansion track frozen as appendix/limitation
  evidence for the current AAAI path. The no-training/no-inference denominator
  audit, Docker coordinate audit, and Docker bucket inspection are complete, but
  the track is blocked for promotion; do not change the current main claim
  unless a later expansion reaches the current H001 evidence standard.
- `relative_size` is promoted only as a secondary framework-scope extension:
  one main-text scope sentence and full supplement analysis. Its learned
  product passes the frozen K=100 joint
  gate for VL-SAT, Open3DSG, and SGFN under the 1,061/117/157 firewall. Do not
  turn this into a learned-formula or best-rescorer claim: a fixed robust-point
  rule matches or improves its Violation, rank-average does not pass the global
  four-family Recall guard on every source, and the disjoint point verifier
  remains a measurement of the same segmented geometry. Keep it out of Figure
  1, the headline contribution list, and the core learned-method evidence.
- RelWitness full-PDF skim is complete for v2. Before submission, check whether a newer RelWitness version adds reproduced results, code, arbitrary-source adapters, `Violation@K`, or wrong-pair/shuffled-geometry controls.
