# H001 Paper Reviewer-Risk Register

Last updated: 2026-07-12 KST

Scope: this file tracks paper-body risks for the current AAAI manuscript under
`paper/aaai/`. The goal is not sentence polish; it is to prevent reviewer attacks
on logic, evidence, novelty, scope, and reproducibility.

## Current Verdict

GeoCalib is viable as a scoped relation-reliability paper, not as a
broad open-vocabulary 3DSSG generation paper. The strongest contribution remains:

> Existing 3DSSG relation sources can assign high source scores to
> physically inconsistent relation edges; GeoCalib contributes a calibrated
> geometry-consistency evaluation and re-ranking framework that makes this
> failure measurable, reduces violations under explicit recall tradeoffs, and
> reports controls, GT/counterfactual verifier checks, and failure analysis.

Current framing decision: GeoCalib is the calibrated geometry-consistency
framework, not one uniquely optimal formula. The Family-calibrated product
(`source score * family compatibility`) and fixed Rank-average fusion are two
soft fusion instantiations. Pooled calibration is an
ablation, RRF a strong comparator, hard filtering a diagnostic, and
calibrator-only/no-source-score ranking a control.

Factor-isolation decision: define `T_e` as predicate/family semantics, `G_e`
as raw predicate-independent same-pair geometry, `Z_e` as source relation score,
and `C_e=P(y_cal=1|T_e,G_e)`, with `Z_e notin C_e`. `y_cal` is a constructed
GT-positive/counterfactual calibration target, not direct human validity. The
legacy `p_geom_valid`-only row is calibrator-only/no-`Z`; calling it true
geometry-only would be inaccurate because the model retains `T_e` and
predicate-aligned interactions.

The main rejection risks are not that the topic is unimportant. They are:

- the method could be read as a hand-coded verifier/post-processing script;
- factor isolation is now demonstrated under the strict train-only audit, but
  the pooled interaction model fails structural controls and support/contact
  remains unsolved; compatibility claims must stay with the selected family
  model and exact counterfactual tests;
- Open3DSG is the main source but uses a reproduced selected checkpoint and a
  recovery-policy full-validation branch;
- the measured relation-family scope may look narrow if reviewers expect broad
  spatial-relation coverage;
- future `attachment_deferred` expansion could be attacked as affordance guessing
  unless the physical evidence schema is separated from class priors;
- controls and GT verifier evidence may look under-specified in the main text;
- audit wording may look non-anonymous or overfit to an internal reference;
- novelty can be blurred by recent relation-witness/calibrated-witness work.
- the previous 127-scan H001 hardened scope can still confuse reviewers unless
  it is consistently framed as historical/sensitivity evidence; the main route
  is now the full official validation split.
- the low-K table can look post-hoc unless K = `{5,10,20,50,100}` and K=1
  exclusion are described as a frozen diagnostic/reporting decision.
- Qwen-VL can dilute the contribution if presented as a new main baseline
  rather than appendix/extension evidence.
- H001_v2 fixed-`tau*` and pooled lambda-soft can dilute the main method if
  presented as replacements despite mixed source metrics; keep them as
  diagnostic candidate evidence only.
- family-conditional calibration can be attacked as a family-specific trick if
  the manuscript does not present it as a calibration design choice and does
  not keep pooled and geometry-only variants as explicit comparisons.
- the aggregate Violation reduction is not family-uniform: verifier-derived
  `support_contact` Violation increases under the calibrated product in both sources,
  including the global-top-100 family slice; claiming every-family improvement
  would be directly contradicted by the frozen decomposition.
- fixed Reciprocal Rank Fusion is a serious comparison: it lowers VL-SAT V@100
  relative to the product without a statistically resolved recall loss, even
  though the product retains a much lower Open3DSG V@100. The method should
  be framed as a source-dependent reliability tradeoff, not universal fusion
  dominance.
- Fresh SGFN confirmation passes the aggregate semantic-vs-product gate, and fixed
  rank-average fusion also passes the same recall/lower-V joint gate against the
  product at K=100 (R/V `0.9476/0.0277` vs `0.9416/0.0381`). This supports a
  two-instantiation framework claim while blocking formula superiority.
- SGFN reproduces the `support_contact` verifier-V regression (`+0.00450`, 95%
  CI `[+0.00370,+0.00532]`) while `proximity` is unchanged and
  `relative_vertical` improves. Aggregate confirmation is therefore not a
  family-uniform mechanism confirmation.
- the family calibrator predates source results, but the product was formerly
  promoted to the paper main score after those results were observed. Existing
  VL-SAT/Open3DSG comparisons are retrospective; hiding this chronology is a
  larger risk than stating it and adding prospective confirmation.
- Human V@K and human semantic calibration are not claimed in the selected
  paper route. The guide and shared mandatory-adjudication/Codex--human
  evaluators are frozen and dry-run verified, but remain non-reportable until
  two independent human sheets and third-human adjudication are complete.
- two blinded Codex LLM proxy annotation passes show high stability and zero
  binary polarity flips, but they are automatic proxy evidence rather than
  independent human annotations; presenting kappa 0.845 as inter-rater
  agreement would be invalid. They are therefore excluded from the active
  submission and retained only in `paper/paper_nonsub/`.
- a parameter-count-matched nonlinear rescorer trained with source-specific
  exact-label supervision dominates the calibrated product at low K and lowers
  SGFN K=100 violation. This blocks any best-fusion or formula-optimality
  claim; the remaining novelty must be the source-independent factor contract,
  identity controls, and joint evaluation protocol.
- target-year style, standalone checklist, supplement policy, and anonymous
  OpenReview upload ZIP are verified and built. Remaining submission risk is
  author-controlled metadata (profiles, countries, reciprocal reviewer) plus
  the final public license/post-acceptance artifact URL.

The principal non-human metric loophole is now closed: frozen sensitivity
reports decidable-only Violation, uncertainty rate, and a pessimistic bound
that treats every uncertain selected row as a violation. At K=100 the
Family-calibrated product lowers the pessimistic bound relative to the source
score for VL-SAT (`-0.04801`), Open3DSG (`-0.25264`), and SGFN (`-0.05856`),
with all paired 95% CIs below zero. Thus the aggregate Violation reductions do
not arise from moving difficult rows into an uncounted uncertain category.

The novelty boundary now explicitly distinguishes GeoCalib from SCR-SSG,
RelWitness, SGFormer++, RelGraphOV, and PUF. The defensible novelty is the
source-independent predicate--geometry compatibility calibration contract plus
joint recall/violation/uncertainty accounting and counterfactual identity
controls; it is not generic semantic--geometric fusion, a new relation
generator, or universal formula superiority.

## Orthogonal Persona Review, 2026-06-14

Persona A, skeptical 3DSSG/CV reviewer:

- Main acceptance path is credible if the paper keeps the claim narrow:
  relation-source reliability, fixed denominators, explicit caveats, and
  violation/recall tradeoff.
- Main risk is overclaiming Open3DSG or Qwen-VL as broad source generality.
  Required defense: call Open3DSG a source-output case study and Qwen an
  extension unless promoted by explicit decision.

Persona B, ML calibration/reliability reviewer:

- GeoCalib is strongest when the paper emphasizes calibration, controls, and
  counterfactual/GT verifier evidence rather than hand-coded rules.
- Low-K can improve the reliability story because top-ranked relations matter,
  but K=5/10/20 must be reported alongside K=50/100 and recall collapse checks.

Persona C, reproducibility/area-chair reviewer:

- The result package is the remaining high-risk surface. Portal checklist
  answers, artifact link/DOI, supplementary policy, and exact package contents
  must be frozen after the GeoCalib/Figure-1 source state.
- If low-K rows are in the paper, the matching point-metric artifacts must exist
  in the release bundle or be regenerated by a documented Docker command. Low-K
  bootstrap ranges should stay in artifacts unless the paper explicitly needs
  uncertainty tables.

## Mitigation Status

### P12 Independent validity, family decomposition, and provenance, 2026-07-10

- Protocol frozen: 488 unique relation items over 137 scans, balanced through
  126 nonempty source/context/family/membership/rank-band strata; raw 3D
  projection and pair PLY coverage is 488/488, RGB pair-crop coverage is
  248/488 and explicitly optional rather than a post-hoc eligibility filter.
- Blinding frozen: public sheets omit source, scores, ranks, verifier result,
  GT, stratum, inclusion probability, and design weight. Two separately locked
  Codex passes exist only in the non-submission route; a valid human route
  still requires two independent first-pass sheets plus blinded adjudication.
- Evaluation frozen: design-weighted Human Violation@K, semantic Brier/AUROC/
  AUPRC/ECE, agreement, coverage exclusions, and cluster-bootstrap CIs are
  implemented but correctly return `awaiting_independent_human_labels` with
  0/488 labels rather than generating proxy human evidence.
- Family-wise diagnostic completed: overall gains are concentrated in
  geometry-aware family/composition effects; `support_contact` verifier-V
  regresses in VL-SAT, Open3DSG, and fresh SGFN. On SGFN, `proximity` is
  unchanged and `relative_vertical` supplies the main V reduction. Main text
  must not claim uniform family improvement. The Codex audit is a proxy
  diagnostic, not a replacement human family-wise result.
- Strong fusion comparisons completed: rank-average and Reciprocal Rank Fusion
  were fixed before SGFN inference. They expose a real source-dependent
  tradeoff. Fresh SGFN rank-average passes the same recall/lower-V joint gate
  against the product, supporting framework robustness but not calibrated-
  product superiority.
- Provenance frozen: family calibrator creation predates source evaluation, but
  main-score promotion follows source results. Current source tables are
  retrospective; the physical-validity audit is prospectively confirmatory for
  validity only. Fresh SGFN target v3 was frozen before correct-checkpoint
  download and passes its aggregate exact-label Recall and verifier-V gates;
  earlier VL-SAT/Open3DSG tables remain retrospective.

Current status: fresh source confirmation, strict factor controls, the
parameter-matched nonlinear comparison, and the two-pass Codex LLM proxy audit
are complete. The submission excludes the proxy audit and must not promote
proxy agreement into Human V@K. If SGFN is reported, disclose v1/v2/v3
pre-inference errata, the 11 retained self-GT rows, family nonuniformity, and
rank-average challenge.

2026-07-10 fresh-source addendum: the official `3DSSG_full_l160` SGPN source
was frozen before checkpoint download/inference on the 157-scan official
validation annotations. Calibrated product independently passes the same
aggregate Recall/lower-verifier-V gate. Rank-average lowers V more, but its
paired dR CI lower is `-0.010053` against the strict `>-0.01` rule; the
cross-source two-formula joint gate therefore fails. Do not generalize SGFN's
two-instantiation result into a universal framework-gate claim. Factor
isolation also remains diagnostic: `M_int` performs strongly on constructed
calibration labels but fails close-by swap and vertical inverse structural
checks, while the all-candidate wrong-T aggregate is symmetry-cancelled and
uninformative. This is the official unified SceneGraphFusion-release
implementation/checkpoint of `3DSSG`, which its README distinguishes from the
original-paper implementation; use it as a fresh semantic-source case, not an
original-3DSSG reproduction or leaderboard claim.

2026-07-11 strict train-only addendum: `train_only_reestablishment_v1` rebuilds
the calibrators behind a disjoint 1,061/117/157 firewall and uses zero final-
validation rows for fit statistics or weights. The default product passes the
354-context internal-dev gate, is hash-locked, and then passes the 548-context
final gate: dR@100 `+0.007553` `[+0.004079,+0.011854]`, verifier dV@100
`-0.027901` `[-0.030347,-0.025656]`. This answers the parameter-leakage attack,
not the historical method-selection attack. The same official final target was
already observed during earlier method/score development, so label the result
`leakage-controlled reconstruction`, never untouched prospective confirmation.
Support/contact verifier V still regresses in family-wise views. A stronger
prospective claim requires a genuinely untouched target; a separate optional
human-alignment study could strengthen the Codex judge but is not active.
Rerunning or repartitioning the 157-scan validation target does not qualify.

2026-07-12 transfer-development update: ReplicaSSG/FROSS is a cross-dataset
stress test and development diagnostic, not a positive external-generalization
claim. Product has no K=100 effect and rank-average loses recall. On the
regenerated 4,293-candidate execution, an all-scene bounded fit preserves
R@100 while lowering V, but LOSO changes R/V to `.31977/.03839` and its dR CI
`[-.07548,.00000]` fails the guardrail. The 548-context cross-source check also
shows source-dependent recall costs. Keep bounded fusion in the supplement and
retain the main source-level framework claim.

Updated on 2026-06-25 KST after promoting family-conditional risk to the main
GeoCalib score and demoting pooled calibrated risk to ablation/baseline:

- P11 H001_v2 method-variant risk: resolved for the current paper route.
  Fixed-`tau*` H001_v2 is locked as diagnostic candidate evidence only. It has
  positive shuffled/wrong-pair tau controls, but VL-SAT recall collapse and
  mixed comparison to fixed paper scores block main-table promotion.
  Lambda-soft selected `lambda*=1.25` is also diagnostic-only. The main paper
  score is now `family_conditional_risk =
  semantic_score * p_geom_valid_family`; pooled
  `probabilistic_recalibrated = semantic_score * p_geom_valid` is retained as
  an ablation/baseline, not as geometry-only control.

- P10 GeoCalib/package risk: resolved for anonymous review upload on 2026-07-12.
  The current main/supplement/checklist were rebuilt in Docker and the verified
  field bundle is `release/h001_aaai27_openreview_20260712_083625/`. Its
  anonymized ZIP includes low-K compact results plus SGFN, factor/train-only,
  uncertainty sensitivity, Codex proxy, ReplicaSSG/FROSS, and Open3DSG
  provenance evidence. Remaining external
  submission risks are the target-year form/style/supplement policy and final
  artifact URL/DOI decision; low-K bootstrap ranges still should not be printed
  in the main paper.

- P0 main-text mitigation: completed. `paper/aaai/sec/6_results.tex` no longer
  names the internal reviewer id or reports private-reference matching.
- P1 main-text mitigation: completed. `paper/aaai/sec/6_results.tex` now states
  that the original control suite numbers are from the VL-SAT controlled anchor
  and adds Open3DSG control numbers for distance-only, geometry-only,
  shuffled-geometry, and wrong-pair geometry.
- P2 main-text mitigation: completed. `paper/aaai/sec/4_method.tex` now states
  that the predicate-family map, hard-rule thresholds, counterfactual
  construction, and calibrator files are fixed from train-dev calibration
  artifacts before held-out source-result reporting.
- P5 main-text mitigation: completed. `paper/aaai/sec/3_problem.tex` now
  specifies top-K grouping, violation denominator status handling, and that only
  `violated` rows count as violations.
- P4 main-text mitigation: completed. `paper/aaai/sec/2_related_work.tex` now
  explains why RelWitness is closest prior art but not a direct baseline unless
  its outputs can be mapped to the same row/denominator/violation protocol.
- P3 main-text mitigation: completed. Open3DSG wording was tightened to
  `main open-vocabulary relation-source case study` and `source-output
  reliability evidence`, avoiding broad generation or SOTA framing.
- P6 main-text mitigation: completed. Downstream claims were softened to
  motivation/future evaluation rather than measured downstream performance.
- P7 Docker bootstrap stability check: completed. `bootstrap_ci` reports 1,000 subgraph
  resamples with status `ready` and no warnings. Open3DSG family-conditional risk
  deltas remain positive for \rAt{100} and negative for \vAt{100}; VL-SAT
  recall deltas remain modest while violation reductions are stable.
- P8 appendix/provenance pass: completed. `paper/appendix.md` now records the
  calibrator/threshold provenance table, Open3DSG caveat consistency pass,
  Figure 3 final-polish boundary, and Qwen-VL third-source boundary. Docker
  `table_builder` was rebuilt and rerun so experiment Table 6 carries the
  Open3DSG caveat note.
- P8 re-check on 2026-06-05: full-validation route selected and regenerated in
  AAAI Experimental Setup, source-result table, Results prose, Limitations,
  appendix, and experiment artifact Table 6. Required current caveats are:
  selected official non-avg checkpoint provenance, filtered train/dev provenance,
  exact-label full-validation denominator, residual calibration risk, and the
  Open3DSG recovery policy (`OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus relaxed
  two-scan view regeneration). The older averaged-BLIP / covered 377/388 /
  `validation_missing_preprocessed:11` wording applies only to the historical
  127-scan sensitivity branch.
- P8 cleanup/consistency pass on 2026-06-05: stale qualitative counts and
  regeneration-needed wording were updated after local cleanup. Docker AAAI PDF
  rebuild `logs/h001_aaai_pdf_build_cleanup_consistency_20260605_111759.log`
  exited 0 with 9 US Letter pages and no targeted citation/reference/overfull or
  LaTeX/package errors.
- P8 content/claim QA and compression pass on 2026-06-06: completed. Docker
  AAAI PDF rebuild `logs/h001_aaai_pdf_build_compression_20260606_105126.log`
  exited 0; its transient historical `main.pdf` had 9 US Letter pages with
  technical content on pages 1-7, references on page 8, and the reproducibility
  checklist on page 9. That default-output duplicate is no longer retained.
  Targeted log checks found no LaTeX errors, undefined references, missing
  citations, fatal errors, or overfull hboxes. Visual/layout inspection is
  recorded in
  `archive/paper/aaai_snapshots/inspection_20260625/report.md` and found no blocking overlap or
  unreadable table/figure issue. The compression pass preserved the scoped
  relation-reliability claim: Open3DSG full-validation 548/548 recovery remains
  the main Open3DSG route; the historical 377/388 vs R2 388/388 route remains
  appendix/sensitivity evidence; Qwen-VL, `relative_horizontal`, and
  `attachment_deferred` are not promoted to the main claim.
- P9 scope-expansion track: scope audit, coordinate audit, and bucket inspection
  are complete, not metric evidence. The current paper claim remains the
  three-family scoped relation-reliability claim. `relative_horizontal` is the
  preferred expansion candidate because it adds 3,570 candidate GT rows
  (`left`, `right`, `front`, `behind`) and would expand the denominator from
  2,545 to 6,115 if validated. Docker `relative_horizontal_scope_audit`
  confirms VL-SAT has 103,664 candidate prediction rows and Open3DSG has 76,400
  candidate prediction rows, but both are currently `unsupported` by the
  verifier. Docker `relative_horizontal_coordinate_audit` is blocked for
  promotion: the best frame is `scan_left_neg_x_front_neg_y`, macro strict
  purity is 0.7725, strict eligible share is 0.6403, `left`/`right` purity is
  0.8005, `front`/`behind` purity is 0.7445, inverse-pair consistency is 1.0,
  and the wrong-frame gap is 0.1231. Docker
  `relative_horizontal_bucket_inspection` adds threshold-free diagnostics:
  `front`/`behind` strict match:contradiction is 2.9143, sign-only purity is
  0.7491, and ambiguity buckets remain large (`axis_margin_ambiguous` 230,
  `conflicting_axis_dominates` 430, `strong_projected_overlap` 44). The
  recommendation is `do_not_promote_relative_horizontal_to_main_claim`. This is
  useful appendix/limitation evidence but cannot support a broader main claim.
  Current AAAI-path decision is to stop here rather than run expanded-family
  metrics; future promotion requires resolving the `front`/`behind` ambiguity
  and completing the full verifier/calibration/metrics/control/bootstrap/audit
  path.
  Reviewer-facing wording should report the threshold-free evidence first:
  selected frame, per-label GT purity, inverse consistency, wrong-frame gap,
  match/contradiction ratio, and ambiguity buckets. The predeclared purity gate
  is a conservative non-promotion rule, not an official benchmark threshold and
  not a success claim.
  Follow-up `relative_lateral` testing is also complete and stopped for the
  current AAAI path. It split `left/right` from the full family and froze 2,264
  GT rows, selected frame `scan_left_neg_x_front_neg_y`, strict purity 0.8005,
  and distinct-left-axis wrong-frame gap 0.0998. The train/dev policy lock is
  caveated: train positive strict purity is 0.8738, but dev positive strict
  purity is 0.6975. Dev failure diagnosis shows 72 strict contradiction rows /
  36 physical pairs concentrated in two scans, 140 uncertain rows / 70 physical
  pairs, about half same-label object pairs, and mostly orthogonal-axis
  dominance. Reviewer-facing decision: keep `relative_lateral` as
  appendix/future-work boundary evidence and do not run paper-facing source
  metrics from the current strict policy.
- P10 attachment-deferred upgrade: Docker G0 scope/schema audit, G1 extractor
  contract, G1b evidence-only dry run, G1c point/surface validation, G2
  conservative verifier-policy design, G3 train-dev calibration/counterfactual
  route, G4 GT policy smoke, G4b error/visual sanity planning, G4c
  strict-only calibration-filter freeze, G5a pooled strict calibration fit, G5b
  bounded source scoring preflight, G5c full-source protocol freeze, and G5d
  full-source scoring/metrics/controls/bootstrap completed. G5d is extension
  evidence, not current main-claim evidence.
  This is the
  preferred
  future relation-family upgrade because it adds 967 GT rows and aligns with
  physical consistency better than relative-horizontal frame semantics. It is
  not part of the current AAAI claim. The audit freezes candidate denominator
  3,512 if validated, source rows VL-SAT 77,748 / Open3DSG 57,300, existing
  verification status `unsupported`, the extractor contract freezes
  evidence-only output fields, and G1c validates 36/36 point/surface-ready
  rows with no forbidden verifier/metric fields. G2 freezes 9 subtype policies
  and conservative defaults, G3 prepares 315 positive seeds plus 446
  counterfactual negative seeds with held-out overlap 0, and G4 applies the
  frozen policy to 36 smoke rows plus 761 train/dev seed rows. G4 results are
  positive nonviolated 0.9048, counterfactual nonsatisfied 0.8274, positive
  strict satisfied 0.3841, counterfactual strict violated 0.4574, and uncertain
  rate 0.4323. G4b freezes 436 review cases, a 50-row visual sanity queue, 121
  strict positive candidates, 204 strict negative candidates, 77
  false-satisfied counterfactuals, 30 false-violated positives, and 329
  uncertain rows. G5a fits pooled model
  `h001-attachment-deferred-p-geom-valid-strict-v1` with dev Brier/NLL/ECE
  0.0010/0.0077/0.0071 and dev AUROC/AUPRC 1.0/1.0 on 83 strict rows, but the
  strict subset is nearly separable and this is not source metric evidence. G5b
  scores 120 scan-diverse bounded source rows with evidence ready 120/120 and 0
  validation errors. G5c freezes 69 deterministic full-source shards for
  135,048 rows and source-specific covered denominators: VL-SAT 967/967 and
  Open3DSG 768/967. Docker G5d was added on 2026-06-06. The 1-shard smoke
  succeeded but its intermediate output/log was deleted after the full run
  completed. The full G5d run completed with exit 0 at
  `logs/h001_attachment_g5d_full_20260606_113803.log`;
  output `archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_source_g5d/`
  has 69/69 shards, 135,048 scored rows, validation errors 0, and 300 failure
  rows. Key G5d results: VL-SAT semantic_only R@100/V@100 `1.0000/0.2126`,
  probabilistic_recalibrated `0.9979/0.2210`, rule_verified_attachment_policy
  `0.9380/0.0215`; Open3DSG semantic_only `0.9297/0.3021`,
  probabilistic_recalibrated `0.6628/0.2460`, rule_verified_attachment_policy
  `0.9245/0.0842`. Required defense before promotion remains: visual/failure
  audit, connected-to caveat handling, and explicit user confirmation. Reviewer
  risk is high if
  the rule uses object class affordance as proof rather than as optional
  context; the current contract explicitly forbids that. A secondary risk is
  that the dev split has no `connected to` positive seed, so any connected-to
  family-conditional calibration claim needs pooled calibration, augmented dev
  selection, or explicit limitation.
- Historical verification logs from 2026-05-26 and 2026-05-27 exited 0 and are
  retained as completed-history records. They are superseded for current
  paper-facing status by
  `logs/h001_aaai_pdf_build_family_main_20260625_084157.log`, exit 0. Its
  transient `main.pdf` had 10 pages total, technical content pages 1-7,
  references pages 8-9, checklist page 10, with Type 1 fonts and no missing
  citations, undefined references, overfull hboxes, LaTeX errors, or AAAI
  package errors in targeted checks; superseded review PDFs are indexed under
  `archive/paper/aaai_snapshots/`.

Remaining after P0-P10:

- No P2 provenance blocker remains. Future supplement work should only expand
  details if the target venue requires a separate supplementary PDF.
- P9 is an optional claim-expansion track, not a blocker for the current paper
  claim. Its coordinate audit and bucket inspection are blocked for promotion,
  so the AAAI path freezes it as a disciplined scope-boundary defense rather
  than as a broader-coverage claim. It can strengthen the "framework can scale
  to more spatial relations" defense only if a follow-up resolves the
  `front`/`behind` frame ambiguity and then passes verifier design, calibration,
  controls, Open3DSG/VL-SAT metrics, bootstrap stability checks, and failure/audit gates.
- P10 is a future-upgrade track, not a current-paper blocker. G0 scope/schema
  audit, G1 extractor contract, G1b evidence-only dry run, G1c
  point/surface validation, G2 verifier-policy design, G3
  calibration/counterfactual route, G4 GT policy smoke, G4b error/visual
  sanity planning, G4c strict-only calibration-filter freeze, G5a pooled strict
  calibration fit, G5b bounded source scoring preflight, G5c full-source
  protocol freeze, and G5d full-source source metrics are complete. The current
  G5a-G5d result has enough strict rows for pooled calibration, a working
  source-scoring contract, and a frozen denominator/control protocol, but
  `connected to` has no dev strict rows, so a family-conditional calibration claim
  needs pooled calibration, augmented dev selection, or an explicit caveat.
  Function reasoning should remain a secondary case study until the attachment
  relation reliability result itself is established.
- P12 paper content/claim QA: current manuscript text is internally consistent
  with the narrow AAAI claim after the 2026-06-06 compression pass. Residual
  reviewer risk is now content-level rather than artifact-level: a strong
  reviewer may still read the method as a calibrated verifier/evaluator unless
  the body keeps emphasizing the row contract, frozen train-derived
  calibration, source-agnostic re-ranking interface, controls, and recall tradeoff.
  Do not widen the title, abstract, or contribution list unless additional
  source metrics and audit evidence are completed.
- P11 full official validation transition: active paper-risk mitigation with
  VL-SAT full-validation metric bundle ready and Open3DSG full-validation
  recovery metric bundle ready.
  The full official `3DSSG_subset` validation split is now the paper-facing
  primary evaluation, not the pilot-excluded 127-scan subset. This is defensible
  only with the provenance boundary that final method design, predicate-family
  mapping, hard-rule policies, counterfactual construction, and `p_geom_valid`
  calibrators are train/train-dev-derived and frozen before validation
  source-result reporting. H001-Mini should be described as
  hypothesis/feasibility evidence, not as threshold fitting, calibrator fitting,
  or primary paper metric evidence. VL-SAT full-validation raw/export,
  geometry join, metrics, GT verifier eval, and bootstrap stability artifacts now exist under
  separate output paths. Open3DSG full-validation now also has a complete
  recovery branch with 548/548 coverage, clean-exit raw dump, adapter, geometry,
  metrics, controls, bootstrap stability artifacts, failure rows, and table/caveat regeneration.
  Use the 548/548 recovery-policy branch as the primary Open3DSG
  full-denominator result and the 533-context covered branch as sensitivity /
  unmodified-source-route evidence.

### P11. Full Official Validation Transition

Reviewer attack:

> Why is the main result not evaluated on the full official `3DSSG_subset`
> validation split, and did the method overfit to a pilot subset?

Current weakness:

- Existing manuscript tables have been regenerated from the selected
  full-validation route.
- VL-SAT and Open3DSG now both have full official validation metric evidence.
  The remaining weakness is transparent wording, not missing execution or branch
  selection. The 548/548 Open3DSG branch depends on a recovery policy
  (`min_visible=2` plus relaxed view generation for two scans), while the
  unmodified covered branch keeps a 15-context denominator caveat.

Required fix:

- Move the paper-facing primary result to full official validation. Use the
  548-context Open3DSG recovery-policy branch as the main full-denominator
  Open3DSG result and report the unmodified 533-context covered branch as
  sensitivity evidence.
- To minimize tuning/hand-adjustment concerns, preserve both Open3DSG
  full-validation routes in the paper record: the 533/548 branch is the
  unmodified public-source/as-is route, and the 548/548 branch is the transparent
  recovery-policy coverage-completion variant. If the main table cannot contain
  both rows, the omitted route must be visible in the caption, appendix, or
  sensitivity paragraph.
- Keep method provenance explicit: family mapping, hard-rule policies,
  counterfactuals, and `p_geom_valid` calibrators are frozen from
  train/train-dev artifacts before validation source-result reporting.
- Treat H001-Mini as hypothesis/feasibility evidence only.
- Preserve the regenerated paper tables/prose from the selected full-validation
  branch and keep the Open3DSG recovery caveat explicit during polish.

Preflight:

- Raw 3RScan payload is present for all 157 official validation scans.
- Full scope contract has status
  `full_official_validation_scope_contract_ready_no_metric_execution`.
- Full official validation has 548 contexts, 7,720 GT-positive directed pairs,
  36,808 candidate directed pairs, 957,008 expected VL-SAT prediction rows,
  11,254 GT rows, and 3,972 H001-family GT rows.
- VL-SAT full-validation metric bundle is ready under
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/`: 957,008
  predictions, 11,254 GT rows, 3,972 H001-family GT rows, metric status
  `ready`, GT verifier AUROC `0.9772`, and bootstrap warnings 0.
- Open3DSG H001 runtime preprocess currently covers 377/548 official
  validation contexts.

Evidence / affected files:

- `results/h001_geom_reliability/full_validation_transition/scope_contract/`
- `results/h001_geom_reliability/full_validation_transition/report.md`
- `experiments/H001_geom_reliability/sources/vlsat/full_validation/`
- `TODO.md`
- `paper/aaai/sec/5_experiments.tex`
- `paper/aaai/sec/6_results.tex`
- `results/h001_geom_reliability/tables/`

## Priority Order

### P0. Remove Anonymity And Internal-Audit Wording Risk

Reviewer attack:

> The paper exposes reviewer identity or reports an internal self-check as if it
> were independent human evaluation.

Current weakness:

- Mitigated in `paper/aaai/sec/6_results.tex` on 2026-05-26. The prior draft
  mentioned `reviewer-confirmed by yhkim` and `private-reference match 1.0000`;
  those phrases were removed from the main manuscript.

Required fix:

- Remove personal identifier from the main manuscript.
- Replace the sentence with scoped wording such as:
  `A 50-row internal visual spot-check reaches a target-bucket quality-issue
  rate of 0.9333 and contradiction rate of 0.0333. We use it only as sanity and
  failure-mechanism evidence, not as a large-scale or blinded human audit.`
- Keep detailed provenance in internal notes, not in anonymous main text.

Evidence / affected files:

- `paper/aaai/sec/6_results.tex`
- `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/05_audit.md`
- `results/h001_geom_reliability/tables/table4_audit.md`

### P1. Clarify Controls Source, Denominator, And Placement

Reviewer attack:

> The controls are reported, but it is unclear whether they apply to the main
> Open3DSG result or only to VL-SAT; therefore the nontriviality defense may not
> support the main open-vocabulary case study.

Current weakness:

- Mitigated in `paper/aaai/sec/6_results.tex` and refreshed on 2026-06-25. The
  text now separates geometry-only control from pooled calibrated reranking and
  uses the full-validation controlled-anchor/control numbers under the
  3,972-row measured-family denominator, with Open3DSG control numbers retained
  for the main source-output case study. The main text still compresses
  controls into prose to preserve the AAAI page budget.

Required fix:

- State the source and denominator inline before the control numbers.
- If these controls are VL-SAT-only, say so explicitly and frame them as
  controlled-anchor nontriviality evidence.
- If Open3DSG controls exist, add one compact sentence or appendix table pointer
  for the Open3DSG control results.
- Add a supplement table for controls if page budget blocks a main table.

Evidence / affected files:

- `paper/aaai/sec/6_results.tex`
- `results/h001_geom_reliability/tables/table2_controls.md`
- `paper/outline.md`

### P2. Strengthen Calibrator / Verifier Provenance

Reviewer attack:

> This is a hand-coded rule verifier, or the rules/calibration were tuned after
> looking at held-out predictions.

Current weakness:

- Mitigated in `paper/aaai/sec/4_method.tex` on 2026-05-26. The main text now
  states that the predicate-family map, hard-rule thresholds, counterfactual
  construction, and calibrator files are fixed from train-dev calibration
  artifacts before held-out source-result reporting.
- GT/counterfactual checks may look circular unless the data split and negative
  construction are explicit; a supplement table would still strengthen this.

Required fix:

- Add one main-text sentence in Method or Experimental Setup:
  `All family mappings, hard-rule thresholds, counterfactual construction, and
  calibrator parameters are fixed from the train-dev calibration artifacts before
  held-out source-result reporting.`
- Create or reference an appendix/supplement table listing family, evidence
  fields, threshold/config source, calibrator artifact, and held-out use.
- Keep `p_geom_valid` described as a reliability score, not a correctness proof.

Evidence / affected files:

- `paper/aaai/sec/4_method.tex`
- `paper/aaai/sec/5_experiments.tex`
- `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`
- `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/04_results.md`
- `results/h001_geom_reliability/manifest.lock.json`

### P3. Defend Open3DSG Main-Source Status Without Overclaiming

Reviewer attack:

> If Open3DSG is not an exact official reproduction, why is it the main
> open-vocabulary result?

Current weakness:

- The selected paper-facing Open3DSG result is not an unmodified Open3DSG
  preprocess route: it uses the selected official non-avg checkpoint and the
  548/548 recovery branch. The 533/548 covered full-validation branch remains
  the sensitivity check.
- The risk is wording: `main open-vocabulary case study` can be interpreted as a
  broad Open3DSG/SOTA claim unless the case-study boundary and recovery-policy
  caveat stay visible.
- The completed full-validation route may tempt overclaiming as exact Open3DSG
  reproduction; it must stay framed as a source-output reliability case study.
  The 548/548 branch is stronger for denominator coverage but requires recovery
  policy disclosure, and the 533/548 branch remains the sensitivity check.

Required fix:

- Prefer `main open-vocabulary relation-source case study` or
  `Open3DSG source-output reliability case study`.
- Avoid `Open3DSG improvement` unless the sentence says improvement is within
  the reproduced selected-source output, fixed full-validation denominator, and
  H001 families.
- Keep Table 3 caption caveats visible.
- Keep experiment Table 6 caveat notes visible.
- Do not hide the full-validation recovery policy when replacing older
  averaged-BLIP/covered-scope wording.

Evidence / affected files:

- `paper/aaai/sec/0_abstract.tex`
- `paper/aaai/sec/5_experiments.tex`
- `paper/aaai/sec/6_results.tex`
- `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md`

### P4. Explain Why Closest Recent Work Is Not A Direct Baseline

Reviewer attack:

> RelWitness or other recent relation-witness/calibration work is closest; why
> not compare directly?

Current weakness:

- Related Work acknowledges RelWitness and distinguishes H001 conceptually.
- It does not yet say why RelWitness is not a direct experimental baseline under
  the current source-output reliability contract.

Required fix:

- Add one sentence after the RelWitness paragraph:
  `We therefore treat RelWitness as closest prior art for witness-based
  open-vocabulary generation, but not as a direct baseline for H001's
  post-source reliability contract unless its outputs can be mapped to the same
  row, denominator, and geometry-violation protocol.`

Evidence / affected files:

- `paper/aaai/sec/2_related_work.tex`
- `literature/2026_arxiv_relwitness/`
- `paper/outline.md`

### P5. Add Metric Definition Detail For Violation@K

Reviewer attack:

> Violation@K is not sufficiently specified: what is the ranking group, what
> happens to uncertain rows, and how is top-K formed?

Current weakness:

- `paper/aaai/sec/3_problem.tex` defines exact-label recall and Violation@K, but
  the grouping and uncertain-row handling could be clearer.

Required fix:

- Add a short metric-detail sentence:
  `Top-K is computed per evaluated subgraph/source ranking over in-scope rows;
  violated rows contribute to Violation@K, while uncertain or missing-evidence
  rows are retained with their recorded status and are not counted as violations
  unless the family rule marks them violated.`
- If this is not exactly the implementation, update the sentence to match the
  metric code before inserting it.

Evidence / affected files:

- `paper/aaai/sec/3_problem.tex`
- `experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json`
- `results/h001_geom_reliability/tables/table1_main_prediction.md`

### P6. Lower Unsupported Downstream Claims

Reviewer attack:

> The paper mentions downstream reasoning, grounding, alignment, or embodied
> decision modules, but does not test downstream tasks.

Current weakness:

- The motivation is valid, but some Results/Conclusion phrasing can sound like a
  downstream performance claim.

Required fix:

- Use `may mislead` or `motivates downstream evaluation` instead of implying
  measured downstream degradation/improvement.
- Keep downstream tasks as motivation and future work.

Evidence / affected files:

- `paper/aaai/sec/6_results.tex`
- `paper/aaai/sec/8_conclusion.tex`

### P7. Add Bootstrap Stability Check

Reviewer attack:

> VL-SAT gains are small; are they stable?

Status:

- Completed as a Docker paper experiment artifact under
  `results/h001_geom_reliability/bootstrap_ci/`.
- The check is a subgraph-level evaluation-context bootstrap, not repeated
  training variance.
- Main use: defend that the Open3DSG family-conditional risk tradeoff is not a single
  aggregate artifact; keep VL-SAT as controlled-anchor evidence because its
  recall deltas are small.
- Paper-facing decision: do not print direct bootstrap ranges in the main table
  or primary results prose. Use point estimates in the paper and keep raw
  bootstrap ranges in the experiment artifact.

Key result:

- Open3DSG full-validation recovery `family_conditional_risk` vs
  `semantic_only`: \rAt{100} delta +8.86 percentage points and \vAt{100}
  delta -9.01 points; bootstrap stability supports the same direction.
- VL-SAT full-validation `family_conditional_risk` vs `semantic_only`:
  \rAt{100} delta +0.48 points and \vAt{100} delta -1.43 points; the effect is
  smaller but favorable under the controlled-anchor route.

Evidence / affected files:

- `results/h001_geom_reliability/bootstrap_ci/summary.md`
- `results/h001_geom_reliability/bootstrap_ci/summary.json`
- `src/geocalib/bootstrap_metrics.py`
- `paper/aaai/sec/6_results.tex`

### P9. Test Scope Expansion With Relative Horizontal Relations

Reviewer attack:

> The current relation scope is too narrow. The work may be a well-engineered
> verifier for support/proximity/vertical predicates, not a framework that can
> scale to broader spatial-relation reliability.

Current decision:

- Keep the current main paper claim unchanged: scoped relation reliability for
  `support_contact`, `proximity`, and `relative_vertical`.
- Add `relative_horizontal` as a separate validation track, not as immediate
  main evidence. The first Docker scope audit is complete and records that both
  VL-SAT and Open3DSG relative-horizontal rows are currently unsupported by the
  verifier. The coordinate-frame protocol is frozen and the first Docker
  coordinate audit is complete, but it is blocked for main-claim promotion
  because macro strict purity is 0.7725 and `front`/`behind` purity is 0.7445.
- Treat success as evidence that the framework can expand to another large
  spatial family; treat failure or ambiguity as a limitation/future-work result
  rather than weakening the locked main claim.

Why this family:

- It is the largest excluded geometry-adjacent family in the fixed H001
  denominator: 3,570 GT rows, covering `left`, `right`, `front`, and `behind`.
- If validated, the geometry-checkable denominator would expand from 2,545 to
  6,115 GT rows, covering about 81% of the 7,505 held-out GT rows.
- It tests whether H001 is a framework over relation-level geometry reliability
  rather than a hand-crafted rule set for support/proximity/vertical cases.

Main risk:

- `left/right/front/behind` may depend on an annotation coordinate frame,
  room/scan frame, object-centric frame, or viewpoint convention. If the frame
  is wrong, the verifier can look wrong even when the framework is coherent.
  Therefore coordinate-frame validation must precede metric promotion.

Promotion gates before main-claim use:

1. Freeze the `relative_horizontal` label semantics and coordinate-frame
   hypothesis from dataset documentation and empirical label checks.
2. Produce a denominator/coverage audit for GT rows and source prediction rows,
   including excluded or ambiguous cases.
3. Define a deterministic geometry status policy with `satisfied`, `violated`,
   and `uncertain` handling, plus a wrong-frame/axis-flip control.
4. Build train-dev calibration and counterfactual negatives without using
   held-out prediction failures.
5. Run GT-positive/counterfactual verifier evaluation and a targeted visual
   sanity check for horizontal labels.
6. Run VL-SAT and Open3DSG source-result metrics with the expanded family
   included, preserving exact predicate-label recall.
7. Add nontriviality controls: geometry-only, distance-only if relevant,
   shuffled geometry, wrong-pair geometry, and wrong-frame/axis-flip geometry.
8. Run bootstrap stability checks and failure analysis at the same standard used for the
   current paper claim.

Pass / fail rule:

- Pass: `relative_horizontal` reaches the same evidence standard as the current
  H001 families and improves the recall/violation tradeoff under transparent
  frame and denominator caveats. It may then be promoted from appendix/track
  evidence into the main paper claim.
- Partial: it has useful metrics but unresolved frame ambiguity or weak visual
  audit. Keep it as appendix evidence that motivates broader validation.
- Fail: frame semantics are too ambiguous or controls show the result is a
  coordinate artifact. Keep the current claim unchanged and report the failure
  as a limitation/future-work boundary.

Reviewer-defense wording rule:

- Do not frame the result as "we set 0.80 and missed it" in isolation.
- Frame it as a threshold-free diagnostic: best deterministic frame is clearly
  above wrong-frame alternatives and inverse labels are perfectly consistent,
  but `front`/`behind` remains less stable than `left`/`right`.
- Use the predeclared gate only to justify not broadening the main claim
  post-hoc.

Evidence / affected files:

- `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/`
- `archive/experiments/H001_geom_reliability/sources/relative_horizontal/README.md`
- `archive/experiments/H001_geom_reliability/sources/relative_horizontal/scope_audit/`
- `archive/experiments/H001_geom_reliability/sources/relative_horizontal/coordinate_frame_protocol.md`
- `archive/experiments/H001_geom_reliability/sources/relative_horizontal/coordinate_audit/`
- future Docker artifacts under
  `archive/experiments/H001_geom_reliability/sources/relative_horizontal/`
- `paper/aaai/sec/5_experiments.tex` only if the track reaches promotion level
- `paper/aaai/sec/7_limitations.tex` if the track remains partial or failed

## Recommended Immediate Sequence

1. P9: inspect the `relative_horizontal` `front`/`behind`
   ambiguity/contradiction buckets before deciding whether a verifier policy is
   defensible. Do not change the current paper claim during this gate.
2. P0-P8: completed for the current claim; keep the manuscript wording scoped
   during any paper polish.
3. Qwen-VL: keep as a deferred third semantic-source extension until GPU
   runtime is acceptable and full Docker metric/audit promotion can run.

## What Not To Do

- Do not broaden the claim to baseline-agnostic or full open-vocabulary 3DSSG
  generation.
- Do not present Qwen-VL as evidence unless it receives full Docker metric,
  denominator, geometry join, and audit treatment.
- Do not hide Open3DSG checkpoint provenance, filtered split, exact-label
  denominator, residual calibration-risk caveats, or the full-validation
  recovery policy. If reporting the historical 127-scan branch, keep its
  averaged-BLIP and covered-scope caveats local to that branch.
- Do not describe the 50-row visual spot-check as large-scale, strictly blinded,
  or independent.
- Do not add `relative_horizontal` to the main claim until coordinate-frame
  semantics, denominator, calibration, controls, metrics, bootstrap checks, and
  failure/audit evidence reach the current H001 evidence standard.
