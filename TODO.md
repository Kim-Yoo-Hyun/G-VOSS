# TODO

Last updated: 2026-07-14 KST

이 파일은 에이전트가 다음 작업 계획과 진행 상태를 관리하는 루트 작업판이다. 자세한 문헌 조사 내용은 `literature/`에 기록하고, 자세한 hypothesis 근거는 `archive/hypothesis_records/hypothesis/`에 기록한다.

## Current Snapshot, 2026-07-14 KST

- Paper-facing name is now `Beyond Semantic Confidence: Relation-Algebra-Constrained Geometric Compatibility for 3D Scene Graph Relations`; keep `H001` as an internal hypothesis/experiment identifier only.
- The active manuscript now uses `RelCompat3D` as its method name and six
  top-level sections: Introduction, Related Work, Method, Experiments,
  Discussion and Limitations, and Conclusion. Problem Setup is inside Method;
  Experimental Setup and results are grouped under Experiments.
- Repository structure is now release-oriented: core Python in `src/geocalib/`, shell wrappers in `scripts/`, Docker/compose files in `configs/`, compact outputs in `results/`, preserved hypothesis records in `archive/hypothesis_records/hypothesis/`, and superseded/optional material in `archive/`.
- Main claim remains scoped relation reliability for `support_contact`,
  `proximity`, and `relative_vertical`, with VL-SAT as the controlled
  reproduced anchor, Open3DSG 548/548 recovery as the main open-vocabulary
  case study, and SGFN as the additional exact-label source on the same target.
- The optional `relative_size` extension is complete under
  `experiments/H001_geom_reliability/relative_size_v1/`. It keeps the
  1,061/117/157 firewall, all 548 evaluation contexts, K=`{5,10,20,50,100}`,
  paired family-wise CIs, and global-top-K composition. The learned product
  passes the frozen within-size and four-family K=100 gates for VL-SAT,
  Open3DSG, and SGFN. It does not strictly outperform the point-rule baseline,
  and four-family rank-average does not pass on every source. The user has now
  approved a bounded promotion: one main-text scope sentence plus full
  supplement results, without using relative size as core learned-method
  evidence or changing the headline three-family result tables.
- `attachment_deferred` subtype-v2 redesign is complete as development
  evidence only. The new predicate/mechanism/observability taxonomy, 761-row
  migration, 190,722-row source-route audit, controls, and 100-row review queue
  are under `archive/experiments/H001_geom_reliability/sources/attachment_deferred/subtype_redesign_v2/`.
  The raw selective product fails; the bounded multiplier passes VL-SAT K=100
  but fails Open3DSG K=100 and VL-SAT K=50. It is not promoted to the main
  RelCompat3D claim.
- Low-K result reporting decision is to expose K = `{5, 10, 20, 50, 100}` in the main source-result table. K=1 stays out of paper metrics. Docker-regenerated point-metric artifacts now live under `sources/vlsat/full_validation/metrics_k_sweep/` and `sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/`; K=50/100 matches the locked `metrics/metrics.json` point estimates.
- Figure 2 and one joint main table report Recall/Violation at
  K=`{5,10,20,50,100}` for VL-SAT, Open3DSG, and SGFN. K=100 is the primary
  endpoint; smaller budgets are reported without internal protocol labels. A
  second table reports six fixed-model controls at K=50/100.
- Qwen-VL full official validation downstream is complete as a third-source / modern VLM extension: 157 scans / 548 contexts / 110,424 query rows / 46,506 inferable input rows / 35,131 exported predictions / 32,236 in-scope predictions / 3,972 H001-family GT rows, plus metrics/controls/bootstrap/failure rows/36 deterministic qualitative cases. It remains appendix/extension evidence unless explicitly promoted.
- Historical source-validation build
  `archive/paper/aaai_snapshots/20260625_reference_expansion.pdf`
  remains preserved. It is provenance only and must not be used as the active
  manuscript or upload package.
- Latest H001 submission manuscript is `paper/aaai/main_aaai27.pdf`, SHA256
  `49459774de4bd244af34de48a06a867b0b14694215ff29fd35e17c8a5e64106f`. The active
  outputs are main/supplement/checklist 8/2/2 US-Letter pages; technical content
  continues through page 7 and references occupy pages 7--8. Type 3 fonts, unresolved
  citations/references, LaTeX errors, and overfull boxes are zero. Superseded
  framework-first, factorized, and Replica-disclosure builds remain archived.
- The current main/supplement PDFs include the source-backed three-panel vector Figure 1,
  scan-cluster sensitivity, and compact relative-size appendix. The synchronized,
  upload-ready bundle is `release/h001_aaai27_openreview_20260714_170829/`; its outer/inner checksums,
  structured manifest, archive integrity, and author-path scans pass.
- H001-only cleanup completed after compact-result verification: removed
  Replica/FROSS raw archives, mesh/runtime, weights, cloned source repositories,
  regenerated source shards, the duplicate merged pickle, Python caches, and
  the superseded submission bundle. Available disk increased from 63GB to 100GB.
- Docker retention audit is current: no listed H001/H002 image is attached to
  a local container. The old AAAI-26 image, non-main proposal image, redundant
  FROSS tag, and de-scoped Replica/FROSS runtime/render images are removable;
  the active RelCompat3D metric, SGFN full-reproduction, and AAAI-27 TeX images
  remain protected. Exact conditions are owned by `docs/reproducibility.md`.
- The prose now follows failure -> structural cause -> factor-isolation
  necessity -> method -> evidence -> scope/limitations. Figure 1 starts from an
  actual geometry-inconsistent prediction and contains no reviewer-checklist
  band; Figure 2 is the three-source K trajectory; Figure 3 contains two large
  corrected point-cloud examples and one residual top-10 failure. The three
  LaTeX inclusions use vector PDFs, and Table 2 is a single-column K=50/100
  ablation table.
- H001 method direction is now factor-isolated: `T_e` denotes predicate/family
  semantics, `G_e` predicate-independent same-pair geometry, `Z_e` source
  confidence, and `C_e = sigmoid(h_a(Phi(T_e,G_e)))` the bounded compatibility
  score for a constructed positive/counterfactual target, not a probability of
  physical validity. The leakage boundary is `Z_e notin C_e`; the source relation score is
  used only by final fusion `S_e = F(Z_e,C_e)`. Existing product/rank-average
  results remain unchanged framework instantiations.
- The strict train-only `orbit_pairwise_projected_product` candidate is now
  promoted as the paper-facing **relation-algebra-constrained compatibility
  product**. The coordinated `structured_main_v1` Docker run regenerated
  source score, structured product, rank-average, RRF, pooled product,
  hard-rule filtering, compatibility-only, family-wise paired CIs, and
  uncertainty sensitivity for all three sources and K=`{5,10,20,50,100}`.
  The locked model SHA256 is
  `62d251f3ce60e2db54eb1748c277350e3b9e2c7c9d2be0312cf2fb323b761410`;
  every manifest validation passes.
- A Docker scan-cluster sensitivity resamples 157 scans and carries all 548
  relation contexts with their scan. At K=100, all verifier-V intervals remain
  below zero; Recall intervals exclude zero for Open3DSG/SGFN and meet zero at
  the VL-SAT lower bound. Scores, rankings, and point estimates are unchanged.
- `h001_factor_isolation_protocol_v1` is frozen under
  `factor_isolation_protocol/frozen_v1/`, and its Docker implementation is
  complete. Train-only fitted models are under `fitted_v1/`; a fresh official
  `3DSSG_full_l160` (SGPN) semantic-source evaluation is under
  `sources/3dssg_full_l160/`. The calibrated product passes its frozen joint
  gate, while rank-average misses the Recall CI guardrail by `0.000053` at the
  lower bound. No condition is promoted from this target.
- `train_only_reestablishment_v1` is complete under
  `experiments/H001_geom_reliability/train_only_reestablishment_v1/`. The
  1,061/117/157 scan firewall is exact and disjoint; strict fit uses 60,208
  train rows, internal-dev uses 6,246 rows only for diagnostics/acceptance, and
  final-validation contributes zero fit rows. After the default score met
  its 354-context internal-dev acceptance criterion, model and score hashes were locked
  before the 548-context run. Final K=100 dR is `+0.007553`
  `[+0.004079,+0.011854]` and verifier dV is `-0.027901`
  `[-0.030347,-0.025656]`. The manuscript now reports the train/internal-dev/
  final-validation split roles directly and does not attach a prospective
  label to this benchmark evaluation.
- The initial ReplicaSSG/FROSS cross-dataset transfer diagnostic is complete on
  11 official test scenes, 4,290 candidates, and 172 exact-label GT rows. All
  24 source/mapping/artifact validations pass, but the K=100 criterion fails:
  the family product is identical to semantic-only
  (dR/dV `0/0`), while rank-average lowers V by `-0.15835` but has dR
  `-0.02907` with CI `[-0.07407,+0.01333]`. This blocks the stronger
  dataset-level generalization claim; lower-K product gains remain diagnostic.
- ReplicaSSG development v2 is complete on a regenerated 4,293-candidate
  execution. The all-scene bounded fit reaches R/V@100 `.3547/.0393`, while
  LOSO reaches `.3198/.0384` and fails the Recall guardrail. Its corrected
  cross-source evaluation includes all 548 contexts and ten GT-free contexts;
  bounded fusion remains supplement-only and does not change the main claim.
- Non-human reviewer strengthening is complete. The main paper now gives the
  exact Recall/Violation denominators, the train-only family-logistic
  compatibility objective and optimizer, six cross-source comparison methods,
  factor/counterfactual controls, and explicit family-nonuniform limitations.
  A frozen Docker sensitivity additionally reports decidable-only Violation,
  uncertainty rate, and a pessimistic bound that counts every uncertain row as
  a violation; the structured product lowers all three at K=100 for
  VL-SAT/Open3DSG/SGFN. Recent closest-work boundaries for SCR-SSG, RelWitness,
  SGFormer++, RelGraphOV, and PUF are explicit in the paper/supplement.
- A parameter-count-matched nonlinear fusion baseline is complete under
  `nonlinear_fusion_baseline/evaluation_v1/`. Its 69 parameters equal the 69
  family-calibrator coefficients, and it is trained only on the disjoint
  117-scan internal-dev exact-label target before evaluation on the 157-scan
  official final validation. On SGFN it reaches R/V
  `0.5441/0.0120`, `0.8681/0.0186`, and `0.9466/0.0279` at K=10/50/100. It
  outperforms the product at low K and lowers K=100 violation, so formula-level
  optimality is explicitly blocked; its source-specific exact-label
  supervision is also disclosed as stronger than RelCompat3D's predictor-agnostic
  compatibility supervision.
- 3DSSG-only novelty-mechanism development is complete under
  `relation_algebra_v1/`. Six structured candidates were run behind a frozen
  gate. Only linked-counterfactual margin fitting plus exact relation-algebra
  orbit projection passes all gates, with zero proximity-swap and
  vertical-inverse error and preserved K=100 Recall on VL-SAT, Open3DSG, and
  SGFN. This mechanism is now the main compatibility model; it remains a
  structural contribution rather than a best-score or best-rescorer claim.
- The unchanged SGFN-supervised nonlinear rescorer was applied to VL-SAT and
  Open3DSG under `nonlinear_transfer_v1/`. It loses Recall significantly on
  VL-SAT at K=100 and on both sources at smaller K, confirming that its strong
  SGFN result is source-adapted rather than a predictor-agnostic replacement.
- H001 is now finalized as a 3DSSG/3RScan-only source-generalization paper.
  Dataset-level generalization is out of scope; ReplicaSSG/FROSS is archived
  development provenance and must not appear in the active submission claim.
- The two locked Codex passes have been evaluated only in the separate
  non-submission workspace `paper/paper_nonsub/`. The active AAAI submission
  contains no Codex-derived validity result. Codex consensus is a non-human
  diagnostic and does not close independent construct-validity or Human V@K.
- H002 is a separate scoped compatibility-routing branch. Its canonical state is owned by `hypothesis/CAND-001/H002_factorized-relation-confidence/README.md` and `paper_claim_core.md`; runtime and manuscript owners are `experiments/H002_compatibility_routing/` and `paper/h002_compatibility_routing/aaai2027/`. The implemented score is `S2_source_x_Ce = normalized_source_score * normalized_C_e`, with raw `C_e=f_C(T_e,G_e)` fit on 4,868 internal-train rows and `Z_e` excluded from compatibility. Main validated routes are `higher/lower` and `bigger/smaller`; `left/right` is caveated, `close by` is a geometry-only control, and `front/behind` plus support/contact are failure/diagnostic routes. The compact table, grouped CI, sensitivity, qualitative package, support/contact diagnostic freeze, and AAAI package are complete. The verified package is main/supplement/checklist 6/3/2 pages; Figure 1 and the two-subsection Method structure are synchronized with the scoped claim. No additional H002 experiment is automatically open; external release/submission or broader-route work requires an explicit decision and frozen protocol.
- H001_v2 under `hypothesis/CAND-001/H001_v2_risk_controlled_reranking/` now serves two roles: fixed-`tau*`/lambda-soft diagnostic evidence and method framing for RelCompat3D risk-aware reranking. Protocol skeleton, read-only source inventory, schema probe, calibration threshold dry run, source-eval contract, source-eval runner, fixed-`tau*` source point metrics, tau corruption controls, source-result path decision, risk-aware soft reranking reframing, paper prose pass, lambda-soft source evaluation, family-conditional risk formalization, and paper-facing naming pass are complete. Fixed-`tau*` remains diagnostic only: `tau*=0.20`, equivalent `p_geom_valid >= 0.80`. Lambda-soft selected `lambda*=1.25` from calibration dev rows and generated VL-SAT/Open3DSG K={5,10,20,50,100} metrics, but it is mixed against current fixed `lambda=1` calibrated scores and remains diagnostic-only. The 2026-06-25 product promotion is preserved as provenance; the current paper framing treats calibrated product and evaluated rank-average as soft framework instantiations. Pooled calibration remains an ablation and geometry-only ranking remains a control.
- H001 top-tier reviewer extension is frozen: independent physical-validity
  audit 488 items / 137 scans / raw 3D evidence 488/488, two empty blinded
  annotator sheets, label-ready Human V@K and semantic-calibration evaluator,
  family-wise paired CIs, fixed rank-average/RRF baselines, and post-hoc
  main-score provenance. The label-free decomposition shows significant
  `support_contact` verifier-V regressions in both sources, so every-family
  improvement wording is blocked. Existing source metrics are retrospective;
  two leakage-safe Codex passes are locked but are not human evidence. They
  agree on 438/488 rows (89.75%, four-class kappa 0.845); all 334 rows resolved
  as binary in both passes have identical polarity, and all 50 disagreements
  involve `ambiguous`. The user authorized SGFN target v3 before correct
  checkpoint download. Full_l160 checkpoint, 157-scan preprocess, and
  one-scan full-edge inference smoke pass. Full inference, identity adapter,
  geometry join, frozen six-condition metrics, and confirmatory audit are now
  complete. The aggregate K=100 gate passes, but fixed rank-average fusion
  improves verifier V over the locked main score without a significant recall
  loss, and `support_contact` verifier V significantly regresses.

## Current Phase

Parallel candidate tracking.

CAND-001 / H001 is in paper/package hygiene plus independent-validity closure,
not automatic new main-source metric generation. Existing source evidence is
complete for the scoped `support_contact`, `proximity`, and
`relative_vertical` aggregate claim, but human validity confirmation remains
open:

- VL-SAT full official validation is the controlled reproduced anchor.
- Open3DSG full-validation `recovery_relaxed_views_min2/` is the main open-vocabulary relation-source case study.
- RelCompat3D is framework-first: the relation-algebra-constrained product is
  the main score, while rank-average is a scale-robust framework instantiation;
  neither is claimed universally dominant.
- Pooled-calibrator product is an ablation/baseline; its raw key remains only
  in reproducibility artifacts.
- geometry-only ranking is a separate control.
- `relative_size` is a promoted secondary scope extension: one main-text scope
  sentence and full supplement evidence only. Qwen-VL, `relative_horizontal`,
  `relative_lateral`, and `attachment_deferred` remain appendix/extension/
  future-work evidence unless explicitly promoted.

Current H001 owners:

- research summary: `summary.md`
- experiment runbook: `experiments/H001_geom_reliability/README.md`
- exact commands: `experiments/H001_geom_reliability/commands.md`
- frozen method/model: `experiments/H001_geom_reliability/relation_algebra_v1/`
- promoted evaluation: `experiments/H001_geom_reliability/structured_main_v1/evaluation/`
- fixed-model ablations: `experiments/H001_geom_reliability/structured_ablation_v1/evaluation/`
- compact results: `results/h001_geom_reliability/report.md`
- reproducibility and bundle transfer: `docs/reproducibility.md`
- paper source: `paper/aaai/`
- verified upload bundle: `release/h001_aaai27_openreview_20260714_170829/`

Current H001 immediate work:

1. Enter the complete author order and link all OpenReview profiles. Every
   profile must have the full publication name, current position,
   institution-affiliated email, and DBLP URL; select all institutional
   countries and confirm the profile-policy checkbox.
2. Nominate by July 21 AoE one eligible coauthor who is not SPC/AC/organizer
   and has at least two first-author or five coauthored related archival papers
   (workshops excluded), or explicitly declare that no author qualifies. The
   nominee accepts up to six reviews. Add optional profile-based conflicts.
3. Verify title, TL;DR, abstract, primary topic, and up to five secondary
   topics; then upload the prepared paper/checklist/supplement/code files by
   their respective deadlines.
4. Decide the final public code license and post-acceptance artifact URL. The
   anonymous review ZIP is already generated and does not depend on an
   external repository link.
5. Optional scientific extension: human-alignment tooling is frozen and dry-run
   verified. If activated, collect two independent 488-row first passes and
   third-human adjudication of every disagreement/low-confidence/ambiguous/
   unobservable row. Human V@K remains unclaimed until the shared validator
   reports `ready`.

Completed package hygiene: Open3DSG `25da9...` non-avg versus historical
`2a23...` avg provenance is reconciled; and the active verified OpenReview set
is `release/h001_aaai27_openreview_20260714_170829/`. Earlier bundles are
retained only as superseded handoff snapshots. The current bundle contains the
structured-main PDFs and focused anonymous supplement and passes outer/inner
checksum, ZIP integrity, and author-path verification.

Completed paper-folder hygiene: `paper/aaai/` now contains only active
AAAI-27 source/templates and the three canonical `*_aaai27.pdf` outputs.
Superseded PDFs, AAAI-26 style files, the legacy appended checklist, and old
inspection notes moved to `archive/paper/aaai_snapshots/`; LaTeX sidecars and
byte-identical default-output duplicates were deleted.

Research target rule: goal and direction are judged against AI, ML, CV, and Robotics top-tier journal/conference standards.

CAND-003 is the literature-survey track. Its next step remains user judgment on whether to promote a survey result into a hypothesis workflow.

## Active Objective

- CAND-001 / H001: main-source metrics, the SGFN additional exact-label source
  comparison, factor implementation, and official SGPN-source evaluation are
  complete. The projected pairwise compatibility eliminates the previously
  blocking proximity/vertical algebra errors, passes its frozen three-source
  gate, and has replaced the continuity product in the coordinated main tables,
  uncertainty analysis, and Figures 1--3. The
  submission excludes the completed two-pass Codex proxy audit and does not
  claim Human V@K; the proxy analysis is isolated in `paper/paper_nonsub/`.
  Independent-human alignment remains an optional stronger validation path,
  not an active collection task. The strict train-only benchmark evaluation is
  complete and satisfies its internal-dev and final-validation criteria.
- CAND-001 / H001 extensions: `relative_size` is now included as a secondary
  scope sentence plus full supplement analysis, not core learned-method
  evidence; Qwen-VL, lateral/horizontal, and attachment-deferred remain
  appendix/future-work evidence unless explicitly promoted.
- CAND-003: decide whether to promote the survey output into a hypothesis workflow.

## Now

### CAND-001 / H001 reviewer extension

- [x] Add `relative_size` as an isolated family with predicate sign `T`, robust
      point-derived `G`, signed `T x G`, and no source-score/rank/class input.
      Freeze and run the 1,061/117/157 Docker route, wrong-T/inverse/common-
      scale/wrong-pair/shuffled controls, point/OBB baselines, three sources,
      five K values, paired family-wise CIs, and global composition. The learned
      product passes every K=100 scope gate, but does not beat the point-rule
      baseline; exact results are in `relative_size_v1/README.md`.

- [x] Redesign `attachment_deferred` subtypes by separating predicate
      semantics, physical mechanism, and observability/applicability. Freeze
      counterfactual mechanism inheritance, positive-only `connected to`, no
      blanket endpoint swap, 311 candidate strict rows, 62 review-required
      rows, and a 100-row blinded mechanism queue. Docker audits cover 761
      train/dev and 190,722 official-validation rows with validation errors 0.
      Preserve both diagnostics: raw selective fusion increases K=100
      Violation in both sources; bounded fusion passes VL-SAT K=100 but fails
      Open3DSG K=100 and VL-SAT K=50. Keep attachment outside the paper claim.

- [x] Reclassify ReplicaSSG/FROSS from prospective confirmation to a
      cross-dataset transfer stress test and development diagnostic, implement
      source-scale-normalized bounded fusion, and regenerate its row-level
      Docker evaluation. Official Replica archive restoration and exact part-
      size validation completed with exit 0; the FROSS VG weight matches the
      expected SHA256. The extraction/inference/evaluation pipeline completed;
      its logs are
      `logs/h001_replicassg_restore_download_20260712_201552.log` and
      `logs/h001_replicassg_development_v2_20260712.log`. Development v2
      completed on 4,293 regenerated candidates: all-scene bounded R/V@100 is
      `.3547/.0393`, but LOSO is `.3198/.0384` and fails the Recall guardrail.
      The 548-context cross-source diagnostic also completed; it does not
      promote bounded fusion or dataset-level generalization to the main claim.
- [x] Rewrite the submission narrative in the order observed failure,
      structural cause, factor-isolation necessity, method, results, and only
      then scope/limitations. Reframe novelty as a predictor-agnostic,
      factor-isolated physical-reliability framework rather than a new fusion
      formula.
- [x] Add the 69-parameter nonlinear fusion baseline using only internal-dev
      exact labels and report its SGFN K=10/50/100 results. Treat its strong
      performance as a formula-optimality blocker, not as evidence to suppress.
- [x] Freeze and execute six 3DSSG-only relation-algebra compatibility
      candidates. Only `orbit_pairwise_projected_product` passes exact
      structural validity, all-source joint performance, Recall continuity,
      and linked-counterfactual ordering gates.
- [x] Apply the unchanged SGFN-supervised nonlinear rescorer to VL-SAT and
      Open3DSG. Report all K values and paired CIs; the observed low-K Recall
      collapse blocks a predictor-agnostic nonlinear-replacement claim.
- [x] Promote the projected pairwise candidate as the paper-facing
      relation-algebra-constrained compatibility method. Regenerate
      rank-average, RRF, pooled, hard-filter, compatibility-only, uncertainty,
      family-wise CIs, Figures 1--3, and all main tables through one coordinated
      strict train-only Docker route. The release bundle is regenerated only
      from these synchronized artifacts.
- [x] Run the frozen K=50/100 fixed-model ablation for wrong predicate,
      wrong-pair geometry, shuffled geometry, label-fixed endpoint swap,
      distance-only, and compatibility-only rankings. Add one joint
      Recall/Violation main table and a dedicated six-control ablation table;
      move hard filtering out of the primary comparison table.
- [x] Replace Figure 1 with an actual failure-grounded four-stage framework,
      Figure 2 with K=5/10/20/50/100 Recall--Violation trajectories over three
      sources, and Figure 3 with two corrected geometry examples plus one
      residual failure. Figure validation status is `passed`.
- [x] Isolate both locked Codex proxy passes and their consensus evaluation in
      `paper/paper_nonsub/`; keep them out of the submission manuscript and do
      not call them human evidence.
- [x] Freeze independent physical-validity audit protocol and materialize 488
      blinded items with 488/488 raw 3D evidence coverage.
- [x] Implement Docker Human V@K, agreement, coverage, and semantic-calibration
      evaluation; current status correctly awaits 488 labels from each of two
      independent annotators.
- [x] Freeze the pre-annotation field guide for `high/medium/low` confidence,
      evidence sufficiency, label-compatible reason codes, immutable fields,
      and distinct human provenance. The 488-item sample and estimands are
      unchanged.
- [x] Implement a shared Docker validator that forces adjudication of the union
      of disagreements, either low-confidence decision, and either
      ambiguous/unobservable label. The Human V evaluator imports the same
      contract, preventing a disagreement-only bypass.
- [x] Implement the locked Codex--human alignment evaluator for four-class
      agreement/kappa, binary confusion/coverage/invalid precision-recall-F1,
      family-stratified errors, and ordinal confidence diagnostics. Empty-sheet
      dry runs correctly remain non-reportable.
- [x] Harden the evaluator provenance gate: two complete first-pass sheets must
      carry distinct non-proxy reviewer IDs and timestamps; any adjudication
      must use a third distinct non-proxy reviewer. Codex/LLM/proxy IDs cannot
      be promoted as human evidence.
- [x] Add family-wise/global-family-slice paired CIs and fixed rank-average/RRF
      fusion baselines. Aggregate improvement is not family-uniform;
      `support_contact` verifier-V regression is now an explicit claim blocker.
- [x] Freeze main-score chronology and prospective confirmatory protocol.
      Existing source metrics are retrospective and the human audit is
      confirmatory only for physical validity.
- [x] Select the current LLM-proxy route instead of collecting two independent
      human annotators. Keep the blank human sheets and evaluator frozen for a
      possible later alignment study; do not relabel Codex output as human.
- [x] Generate a leakage-safe Codex-blinded proxy draft for all 488 items and a
      blank user-review sheet/UI. Proxy counts are valid 180, invalid 185,
      ambiguous 120, unobservable 3; this is not independent human evidence.
- [x] Lock a second public-evidence-only Codex blinded pass before comparing it
      with pass v1. Pass v2 counts are valid 175, invalid 178, ambiguous 132,
      unobservable 3. Agreement is 438/488, kappa 0.845; 334/334 jointly binary
      rows agree and there are zero valid/invalid polarity flips. All 50
      disagreement rows were visually inspected without mutating either pass.
- [x] Formalize the two runs as `two blinded Codex LLM proxy annotation
      passes` and survey LLM-annotation/LLM-as-a-judge precedent. PNAS 2023,
      G-Eval, MT-Bench, AnnoLLM, CHI 2024 crowd-pipeline work, MEGAnno+, and
      CVPR 2024 GPT-4V text-to-3D evaluation support LLM-based automatic
      annotation/evaluation when human alignment, bias, and provenance are
      measured. H001 therefore reports the Codex passes as automatic proxy
      diagnostics, not human ground truth.
- [x] Preserve the historical Codex-disclosure draft only as an archived
      snapshot, remove Codex-derived validity results from the active AAAI
      submission, and create `paper/paper_nonsub/main_nonsub.pdf` for the
      explicitly non-human proxy analysis. The two runs are never represented
      as independent human annotators.
- [x] Select and pre-register untouched `sgfn_official_full_l160` before source
      inference. Split preflight found H001's 157 scans exactly equal official
      SGFN `test_scans.txt`, not its 117-scan validation list; target v2 freezes
      that pre-inference correction.
- [x] User authorized target-v3 pre-inference erratum. Freeze v3 before correct
      checkpoint download, download/audit `SGFN_full_l160.zip`, and validate
      strict 160-object/26-relation checkpoint compatibility.
- [x] Stage official SGFN source/data and preprocess the exact 157-scan test
      target: 4,480 nodes and 27,712 source relationship rows. One-scan
      inference smoke passes strict checkpoint, full directed-edge, RGB
      alignment, and PyG compatibility gates.
- [x] Complete frozen SGFN v3 full inference, identity adapter, geometry join,
      six-condition metrics, 1,000-resample paired bootstrap, and confirmatory
      gate audit. The K=100 aggregate main-vs-semantic gate passes: dR
      `+0.01813`, 95% CI `[+0.01341,+0.02325]`; verifier dV `-0.02489`, 95% CI
      `[-0.02699,-0.02290]`. Retain all 3,972 GT rows, including 11 self
      `supported by` rows without synthesized edges. `support_contact` dV is
      `+0.00450` `[+0.00370,+0.00532]`, and fixed rank-average beats the main
      score on verifier V with recall-difference CI crossing zero, so neither
      family-uniform improvement nor unique-score dominance is authorized.
- [x] Adopt framework-level manuscript framing: calibrated product and
      evaluated rank-average are two soft RelCompat3D instantiations; SGFN is an
      additional exact-label source comparison satisfying the aggregate
      criterion, while source-dependent tradeoffs and verifier/human boundaries
      remain explicit.
- [x] Adopt the H002-derived factor separation without importing H002 results:
      define `T_e`, predicate-independent raw `G_e`, source relation score `Z_e`,
      and constructed-target compatibility `C_e`; freeze `Z_e notin C_e`; keep
      `S_e = F(Z_e,C_e)` with product/rank-average as existing instantiations.
      Reclassify `control_p_geom_valid_only` as calibrator-only/no-`Z`, not
      true `G`-only.
- [x] Freeze `h001_factor_isolation_protocol_v1` before any new factor metric.
      The artifact classifies the 29-feature union as `T=10`, raw `G=17`, and
      `T x G=2`, with zero forbidden `Z/source` hits; locks pooled `M_T/M_G/
      M_add/M_int`, exact metamorphic controls, three sources, K grid,
      3,972-row denominator, and simultaneous family-wise paired bootstrap CI.
      It is labeled
      `post_hoc_mechanism_diagnostic_not_original_sgfn_confirmatory_gate`.
      Final Docker freeze log:
      `logs/h001_factor_isolation_protocol_freeze_final_20260710.log`, exit 0;
      all `59/59` validation gates pass.
- [x] Prove the existing-score no-change boundary before implementation. An
      independent factor-ledger scorer is bit-exact against the canonical
      family scorer for VL-SAT `220,848`, Open3DSG `160,596`, and SGFN
      `220,848` in-scope rows: compatibility/product max absolute error `0.0`,
      identical score-stream SHA-256, and unchanged rank-average operands.
- [x] Implement the frozen `M_T/M_G/M_add/M_int`, wrong-`T`, close-by exact
      swap, and vertical inverse-equivariance diagnostics in Docker. Models use
      only 4,616 calibration-train rows; 1,193 dev rows are diagnostic only.
      On fresh `3DSSG_full_l160`, `product_M_int` gives dR@100 `+0.00780` and
      verifier dV@100 `-0.01215`, but its close-by swap and vertical inverse
      errors (`0.22183`, `0.10085`) block a structural-compatibility claim.
- [x] Freeze and evaluate the previously unseen official
      `3DSSG_full_l160`/SGPN semantic source on all 548 contexts from the
      official 157-scan validation annotations. The target is disjoint from all
      32 calibration scans, keeps the 3,972 exact-label denominator, and uses
      no source-specific tuning. Calibrated product passes; rank-average has
      dR CI lower `-0.010053` against a strict `>-0.01` guardrail and therefore
      fails the pre-registered joint framework gate despite lower verifier V.
- [x] Complete `train_only_reestablishment_v1`: freeze the protocol, create the
      exact 1,061 train / 117 internal-dev / 157 final-validation firewall,
      audit validation-information provenance, export 66,454 constructed-label
      rows, and fit strict calibrators using train-only statistics and weights.
      The fit contains 60,208 train rows, 6,246 diagnostic-only internal-dev
      rows, and zero final-validation rows.
- [x] Freeze the exact default product, comparator, K, denominator, bootstrap,
      and metamorphic-control implementation before internal-dev source
      inference. The 117-scan official internal-dev source covers 354/354
      contexts, 23,228/23,228 directed pairs, and 2,730/2,730 in-scope GT rows.
- [x] Accept and hash-lock the default family product on internal-dev. At
      K=100, dR is `+0.001832` with paired 95% CI
      `[-0.000382,+0.004345]`, and verifier dV is `-0.025742`
      `[-0.028405,-0.023109]`; both frozen gates pass. Final model SHA-256 is
      `bf52a2d7c90d3f11e024f74ac6f3ba7a88f04d2865fb0df7a34a079b200f3c6f`
      and score-definition SHA-256 is
      `e9186633c6514f7eb2804e0cc91d2bc0fbb089be2680bcecaa61ecaaee718fac`.
- [x] Run the locked official 548-context final-validation evaluation with no
      post-result repair. Semantic vs strict family product at K=100 is
      R `0.951410 -> 0.958963`, dR `+0.007553`
      `[+0.004079,+0.011854]`; verifier V `0.062153 -> 0.034252`, dV
      `-0.027901` `[-0.030347,-0.025656]`. All 3,972 GT rows and all actual
      candidate counts are retained. Support/contact V still regresses in the
      family analyses, so no family-uniform or support/contact-solved claim is
      allowed. Classification remains
      `leakage_controlled_train_only_reconstruction_not_untouched_prospective_confirmation`.
- [x] Complete the untouched dataset/source confirmation on official
      ReplicaSSG test + FROSS. The 11-scene / 172 exact-label denominator,
      strict train-only model, four primary scores, factor diagnostics,
      controls, paired scene bootstrap, weight SHA-256, and Docker
      implementation hashes were frozen before source prediction under
      `sources/replicassg/prospective_protocol/frozen_v1/`. All 11 full official
      trajectories, FROSS inference, shard validation/merge, adapter, geometry,
      and 1,000-resample evaluation completed in Docker. All prospective
      validations pass. The K=100 product is unchanged from semantic and
      rank-average violates the recall guardrail, so both the framework and
      formula-robust gates fail. Compact result:
      `results/h001_geom_reliability/replicassg_prospective/`.

### CAND-001 / H001_v2

- No active H001_v2 source-metric rerun task. Fixed-`tau*` H001_v2 is locked as
  diagnostic candidate evidence only, pooled lambda-soft H001_v2 is also
  diagnostic-only, and family-conditional calibrated risk is the product
  instantiation inside the current framework-first paper framing.
- [x] H001_v2 `paper_facing_family_conditional_naming_pass`: reported the
      frozen family-calibrator artifact as `family_conditional_risk` in
      paper-facing summaries, tables, figure inputs, and AAAI prose. Raw metric
      JSON may still expose the legacy key
      `control_family_specific_p_geom_valid`; treat it as an implementation
      key for the same paper-facing condition.
- [x] H001_v2 `family_conditional_risk_formalization`: promoted the existing
      frozen family-conditional geometry-risk artifact from a control-like
      interpretation to the RelCompat3D main family-conditional calibrated
      geometry-risk score; wrote `11_family_conditional_risk_result.md`.
      Open3DSG improves over pooled risk across K in both recall and violation;
      VL-SAT lowers violation with near-flat recall. Pooled
      `probabilistic_recalibrated` is retained as an ablation/baseline.
- [x] H001_v2 `lambda_soft_protocol_and_source_eval`: selected `lambda*=1.25` from calibration dev rows only using NLL over `p_geom_valid^lambda`, generated VL-SAT/Open3DSG K={5,10,20,50,100} metrics under `artifacts/source_eval_lambda/`, and wrote `10_lambda_soft_reranking_result.md`; result is mixed against current `lambda=1` RelCompat3D and remains diagnostic-only.
- [x] H001_v2 `paper_prose_pass`: updated `paper/aaai/sec/4_method.tex` and `paper/draft.md` so RelCompat3D's `semantic_score * p_geom_valid` score is presented as the `lambda=1` risk-aware soft re-ranking objective; locked metrics and result tables unchanged.
- [x] H001_v2 `source_result_path_decision`: selected diagnostic-only stop for fixed-`tau*` H001_v2. Do not promote it to the current main table or run fixed-`tau*` bootstrap unless appendix/supplement diagnostic uncertainty is explicitly needed.
- [x] H001_v2 `risk_aware_soft_reranking_reframing`: updated the branch so current RelCompat3D `semantic_score * p_geom_valid` is framed as the `lambda=1` risk-aware soft reranking objective. Fixed-`tau*` remains diagnostic and locked metrics are unchanged.
- [x] H001_v2 `tau_corruption_controls`: added fixed-threshold shuffled-geometry and wrong-pair-geometry tau controls to `evaluate_h001_v2_source.py`, regenerated VL-SAT/Open3DSG source-eval artifacts, and updated `08_source_eval_result.md`. Controls are worse than H001_v2 on both sources, supporting geometry-specific signal but not resolving the promotion blocker.
- [x] H001_v2 `evaluate_h001_v2_source_runner`: implemented/validated the hypothesis-stage source-eval runner following `07_source_eval_contract.md`, generated VL-SAT and Open3DSG recovery point metrics under the H001_v2 artifact root, and wrote `08_source_eval_result.md`. Result: mixed, not promotable yet.
- [x] H001_v2 `source_eval_contract`: wrote `07_source_eval_contract.md`; fixed input roots, output roots, condition semantics, K grid, selected-count reporting, no-overwrite guard roots, proposed VL-SAT/Open3DSG commands, and decided the first implementation should be a hypothesis runner rather than Docker.
- [x] H001_v2 `threshold_selector_dry_run`: added `src/geocalib/select_h001_v2_threshold.py`, ran the calibration-only selector on `p_geom_valid_smoke/scores.jsonl` with `role == "dev"`, and wrote `artifacts/calibration_threshold_selection/`; result `tau*=0.20`, `p_geom_valid >= 0.80`, 423 selected rows, 13 violations, empirical 0.0307, CP upper 0.0484.
- [x] H001_v2 `calibration_schema_probe`: completed `06_schema_probe.md`; calibration `table.jsonl` has labels but no deployable `p_geom_valid` or semantic ranks, `p_geom_valid_smoke/scores.jsonl` has 1,193 held-out dev rows for threshold selection, and both source geometry JSONLs have complete in-scope semantic/risk/status fields for fixed-threshold top-K evaluation.
- [x] H001_v2 `source_inventory`: created `05_source_inventory.md` with read-only H001 input paths, row counts, observed schema fields, derived output root, and no-overwrite guard roots.
- [x] H001_v2 `protocol_skeleton`: created the branch under `hypothesis/CAND-001/H001_v2_risk_controlled_reranking/` with fixed K grid `{5,10,20,50,100}`, primary `alpha=0.05`, `delta=0.05`, candidate `tau_grid`, baseline list, source scope, and claim boundary.

### CAND-001 / H002

- [x] Freeze the scoped factor contract: raw `C_e=f_C(T_e,G_e)`, `Z_e not in C_e`, and final `S2_source_x_Ce = normalized_source_score * normalized_C_e`.
- [x] Complete the Docker validation pipeline for VL-SAT and Open3DSG on the official 3DSSG validation split.
- [x] Lock main validated routes: relative vertical and relative size.
- [x] Lock route boundaries: caveated left/right, close-by control, front/behind failure, support/contact diagnostic only.
- [x] Produce compact main/appendix tables, 1,000-replicate grouped CI, normalization sensitivity, controls, and qualitative cases.
- [x] Freeze the support/contact independent-target repair as diagnostic: 35 accept / 347 reject, majority baseline 0.908, and exact construction-rule recovery.
- [x] Build and verify the scoped AAAI package: main/supplement/checklist 7/3/2 pages, US Letter, Type 3 font 0, citation/reference/LaTeX/overfull errors 0.
- [x] Consolidate H002 hypothesis, experiment, result, and paper files; remove discarded learned-G_e, p_obs/p_rel, repeated repair, and transition branches.
- [ ] No active automatic H002 experiment. On explicit request, decide one of: external artifact/release preparation, submission portal policy, or a preregistered broader-route experiment.


### CAND-001

Data-dependent:

- [x] OpenReview/AAAI-27 live form and target-year policy verified on 2026-07-12 KST; migrated to official `aaai2027` source, separate checklist upload, and live field-size/anonymity rules.
- [ ] Artifact/code-release URL 또는 DOI 결정: GitHub/source bundle, external row-level artifact bundle, and checksum/verification command must be fixed before final checklist answers.
- [x] Supplementary/code-data route fixed: two-page provenance/negative-transfer technical supplement plus anonymized code/data ZIP, with no media supplement and no external repository pointer used for review.
- [x] Standalone AAAI-27 checklist updated and built; partial answers remain explicit where public licensing/final public URL are not yet decided.
- [x] Low-K result provenance sync: Docker-regenerated `K={5,10,20,50,100}` point-metric artifacts in the current checkout without overwriting locked `metrics/`. VL-SAT output is `experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics_k_sweep/`; Open3DSG recovery output is `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/`. K=50/100 values match each source's locked `metrics/metrics.json`. Low-K bootstrap CI is not currently claimed; generate it only if the manuscript adds CI statements for low-K deltas.
- [x] Full official validation transition metric-bundle generation: build Docker-reproducible full
      `3DSSG_subset` validation scope artifacts and rerun the complete source
      pipeline before promoting it to the main paper claim. Target scope is 157
      scans / 548 subgraphs / 11,254 GT rows / 3,972 in-scope H001-family GT
      rows. Raw 3RScan payload is 157/157 ready and the full-validation scope
      contract is frozen under
      `results/h001_geom_reliability/full_validation_transition/scope_contract/`
      with status
      `full_official_validation_scope_contract_ready_no_metric_execution`.
      VL-SAT full-validation Docker staging/runtime record/raw preflight are
      now ready under
      `experiments/H001_geom_reliability/sources/vlsat/full_validation/`:
      157/157 faithful staged scans, runtime image
      `h001-open3dsg-repro:cu128`, 16/16 checkpoint files, raw preflight
      status `ready_to_run`, 0 errors, and 1 expected legacy import-shim
      warning. VL-SAT full-validation metric bundle is ready under
      `experiments/H001_geom_reliability/sources/vlsat/full_validation/`:
      raw dump/export, ground-truth JSONL, geometry join, metrics, controls,
      GT verifier check, and VL-SAT-only bootstrap CI completed under the same
      157-scan scope. Key full-validation VL-SAT low-K metrics from
      `metrics_k_sweep/metrics.json`, ordered as K=`5/10/20/50/100`:
      semantic_only R `0.4194/0.6322/0.8074/0.9272/0.9635`, V
      `0.0029/0.0082/0.0142/0.0268/0.0476`; probabilistic_recalibrated R
      `0.4154/0.6322/0.8107/0.9305/0.9688`, V
      `0.0015/0.0071/0.0120/0.0229/0.0404`;
      rule_verified_point_subtype R `0.4197/0.6317/0.8074/0.9257/0.9627`,
      V `0.0/0.0/0.0/0.0/0.0`; family_conditional_risk R
      `0.4162/0.6309/0.8087/0.9288/0.9683`, V
      `0.0011/0.0051/0.0109/0.0206/0.0333`.
      Open3DSG full-validation metric bundle is also ready under
      `experiments/H001_geom_reliability/sources/open3dsg/full_validation/`
      after Docker payload/views/preprocess audit, recovery attempt, feature
      seed/audit, selected-checkpoint raw dump, adapter export, raw identity,
      geometry join, metrics/controls, bootstrap CI, failure rows, and
      Table 6/caveat regeneration. Coverage: views 157/157, preprocess
      533/548 with 15 missing contexts after recovery, covered-scope features
      533/533, raw stream 26,746 rows / 533 completed batches, adapter
      690,924 prediction rows, geometry 690,924 rows, metrics `ready`,
      bootstrap `ready`, failure rows 81,448, and table/caveat report
      `open3dsg_full_validation_table_caveats_ready`. Key Open3DSG
      full-validation metrics: semantic_only R@50/R@100 `0.4043/0.5111`,
      V@50/@100 `0.1387/0.1242`; probabilistic_recalibrated R@50/R@100
      `0.3943/0.5685`, V@50/@100 `0.0590/0.0807`;
      rule_verified_point_subtype R@50/R@100 `0.4242/0.5320`, V@50/@100
      `0.0/0.0`; family_conditional_risk R@50/R@100 `0.4612/0.5999`,
      V@50/@100 `0.0265/0.0332`. Caveats: Open3DSG uses the selected official
      non-avg BLIP checkpoint for this separate full-validation branch, the
      raw process exited `137` after stream finalization, and the 15 missing
      preprocess contexts remain an explicit source-runtime denominator caveat.
      User direction on 2026-06-04: full validation should be the main route
      if the caveats are transparently handled. Retried the 15 missing contexts
      in Docker under `full_validation/preprocess_retry2/`; result stayed
      identical at 32 regenerated / 15 missing with the same Open3DSG
      `too few visible objects, scene missalignment possible` source messages,
      so this was initially treated as a persistent loadability caveat. On
      2026-06-05 KST a separate missing-15 recovery branch was started under
      `full_validation/preprocess_missing15_diagnosis/` and
      `full_validation/preprocess_recovery_relaxed_views_min2/`. Diagnosis
      found the source drop condition exactly: Open3DSG
      `preprocess_3rscan.py` returns when fewer than 4 annotation objects have
      `object2image` view metadata. Recovery with `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`
      generated 13/15 missing contexts; relaxed view-generation thresholds for
      the remaining 2 scans then yielded a full preprocess audit of 548/548
      ready contexts. The recovery variant is now complete under
      `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`.
      Docker feature audit reached 548/548, raw dump completed with clean exit
      `0`, stream manifest `raw_dump_stream_complete`, 548/548 batches,
      26,938 raw rows, dropped/invalid partial rows `0/0`, adapter export
      695,916 prediction rows, geometry join 695,916 rows with 160,596
      H001-family geometry-checkable rows, metrics/controls `ready`, bootstrap
      CI `ready`, failure rows 82,155, and Table 6/caveat report
      `open3dsg_full_validation_table_caveats_ready`. Recovery low-K Table 6
      candidate from `metrics_k_sweep/metrics.json`, ordered as
      K=`5/10/20/50/100`: semantic_only R
      `0.0368/0.1002/0.1991/0.4096/0.5161`, V
      `0.5131/0.3255/0.2088/0.1386/0.1242`;
      probabilistic_recalibrated R `0.0826/0.1581/0.2603/0.3975/0.5723`, V
      `0.0628/0.0699/0.0654/0.0606/0.0811`;
      rule_verified_point_subtype R `0.0707/0.1314/0.2422/0.4295/0.5368`,
      V `0.0/0.0/0.0/0.0/0.0`; family_conditional_risk R
      `0.0984/0.1921/0.3291/0.4658/0.6047`, V
      `0.0420/0.0482/0.0441/0.0286/0.0341`. Caveat: report this as a
      recovery-policy variant, not the unmodified Open3DSG source preprocess
      route, because it relaxes the visible-object gate to `min_visible=2` and
      regenerates relaxed views for two scans. Docker
      `open3dsg_full_validation_raw_clean_exit_review` reviewed the older
      533/548 unmodified-source clean-exit retry/equivalence state and wrote
      `sources/open3dsg/full_validation/raw_clean_exit_review/`: the canonical
      unmodified branch remains complete at 26,746 rows but exited `137`; the
      expected retry root `raw_dump_exit0_retry_20260605_000241/` is no longer
      present after cleanup, so the unmodified branch's clean-exit caveat
      cannot be reduced. This does not affect the selected 548/548 recovery
      branch, whose raw stream exited `0`.
      Decision: promote full official validation to the AAAI main route. Use
      VL-SAT full-validation as the controlled-anchor result and Open3DSG
      `recovery_relaxed_views_min2/` as the primary full-denominator Open3DSG
      result. Keep the original 533/548 Open3DSG covered branch as a
      sensitivity / unmodified-source-route check, not the main result.
- [x] Full-validation failure taxonomy / qualitative reviewer-defense refresh:
      Docker regenerated the source-agnostic H001 failure-analysis schema,
      VL-SAT full-validation failure rows, and Open3DSG recovery failure rows;
      then sampled and inspected deterministic 36-case qualitative queues for
      both full-validation sources. VL-SAT outputs are under
      `sources/vlsat/full_validation/{failure_rows,failure_cases}/`: 59,841
      diagnostic rows, 2,897 visual-audit queue rows, 36 selected qualitative
      cases, validation errors 0. Open3DSG recovery outputs are under
      `sources/open3dsg/full_validation/recovery_relaxed_views_min2/{failure_rows,failure_cases}/`:
      82,155 diagnostic rows, 8,821 visual-audit queue rows, 36 selected
      qualitative cases, validation errors 0. These are deterministic
      failure-mechanism artifacts, not representative human-audit metrics.
- [x] Full-validation reproducibility bundle plan refresh: update
      `docs/reproducibility.md` so the default paper-facing bundle is the
      full-validation bundle: selected official non-avg Open3DSG checkpoint,
      VL-SAT full-validation row JSONL/metrics/bootstrap/GT verifier/failure
      artifacts, Open3DSG recovery row JSONL/metrics/bootstrap/failure
      artifacts, table outputs, and manifest locks. Added lightweight bundle
      manifest/runbook under
      `results/h001_geom_reliability/full_validation_transition/artifact_bundle/`;
      no large tar archive was created. The existing
      `release/h001_core_results_20260526_160957.tar.zst` is now explicitly
      historical 127-scan/sensitivity evidence.
- [x] R1 Open3DSG exact non-averaged BLIP route retry completed and checkpoint selection/downstream refresh are complete: Docker/tmux job `h001_open3dsg_train_full_nonavg_retry_20260601_071908` exited `0`, selected official non-avg checkpoint `epoch=13-step=13104.ckpt` from run `25da9c4c00214f3b880cedbb2a124177`, train-dev `val/loss=0.5724539160728455`, and separate non-avg raw/export/geometry/metrics/bootstrap/Table 6-caveat artifacts are ready. Do not overwrite historical avg-BLIP artifacts; current paper-facing Open3DSG evidence uses the full-validation 548/548 recovery branch.
- [x] Open3DSG dual-route retention policy locked: keep both the unmodified
      Open3DSG source-route full-validation branch and the recovery branch. The
      `sources/open3dsg/full_validation/` branch is public-source/as-is evidence
      with 533/548 loadable contexts and should not be discarded; it shows the
      Open3DSG source-runtime preprocess visibility drop. The
      `sources/open3dsg/full_validation/recovery_relaxed_views_min2/` branch is
      the 548/548 coverage-completion recovery variant and must keep its
      `min_visible=2` plus relaxed two-scan view caveat. Use both to reduce
      tuning/hand-adjustment concerns: the conclusion should not depend on
      hiding either the source-runtime drop or the recovery-policy intervention.
- [x] Optional R2 H001 covered-loadable context retry toward `388/388`:
      downstream sensitivity branch complete; same-route clean-exit retries
      exhausted.
      Docker diagnosis found the
      same Open3DSG visible-object gate pattern as the full-validation recovery
      branch: default route stayed 377/388, default view regeneration made
      10/10 missing scans readable, `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` recovered
      10/11 missing contexts, and one final relaxed-view recovery for
      `0cac7532-8d6f-2d13-8cea-1e70d5ae4856` completed preprocessing. Full
      preprocess audit now reports 388/388 ready contexts under
      `sources/open3dsg/h001_covered_recovery/preprocess_audit_388/`.
      Feature audit after preprocess initially reported 377/388 complete
      feature ids with 11 missing ids. Docker/tmux
      `h001_open3dsg_h001_r2_feature_388_retry` completed with exit `0`,
      filled the missing 11 feature ids, and
      `h001_covered_recovery/features_388/` now reports 388/388 complete
      feature ids and 1,164 `.pt` files. Branch-local raw stream artifacts are
      complete: `h001_covered_recovery/raw_dump/`,
      `raw_dump_clean_return_20260606_003130/`, and
      `raw_dump_clean_return_retry2_20260606_021154/` all reached 388/388
      batches and 19,224 rows with dropped/invalid partial rows `0/0`; however
      the two patched clean-return reruns still ended with Docker exit `137`
      and Docker `container oom` after finalization. Treat this as a complete
      artifact plus process-level teardown/OOM caveat. Docker downstream
      refresh is complete under `h001_covered_recovery/`: raw identity
      `raw_dump_identity_audit_ready`, adapter `ready` with 498,212 prediction
      rows, geometry `ready` with 498,212 preserved rows and 114,972 H001-family
      geometry rows, metrics `ready`, bootstrap CI `ready`, and
      `table_caveats/` status
      `open3dsg_h001_covered_recovery_sensitivity_ready`. R2 changes the old
      avg-BLIP 377/388 point estimates only slightly: R@100 is +0.28 pp across
      main conditions and Violation@100 changes by +0.00 to +0.13 pp. Wording
      value: appendix robustness/sensitivity that the old missing 11 contexts
      did not drive the Open3DSG trend. Do not repeat the same Lightning/DDP
      raw-dump route. A raw-dump-only runner is optional and should be built
      only if this R2 sensitivity branch needs process-level exit-0 provenance.
      Docker `open3dsg_h001_covered_recovery_provenance_review` then confirmed
      both clean-return raw files are row/predicate-score equivalent to the
      canonical branch raw dump after excluding run-metadata fields; byte SHA
      differs only because `baseline_run_id` / `model_source_stage` differ.
- [x] Optional H001 upgrade path G5d completed: full-source attachment VL-SAT/Open3DSG scoring, source metrics, controls, and bootstrap CI completed with exit 0. Log `logs/h001_attachment_g5d_full_20260606_113803.log`; output `archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_source_g5d/`; 69/69 shards, 135,048 scored rows, validation errors 0.

Non-data:

- [x] Preserved hypothesis records moved out of active `docs/` into
      `archive/hypothesis_records/hypothesis/`. H001 canonical files, H001
      smoke/evaluation artifacts, and H002 diagnostic/audit artifacts are
      preserved there. Active docs, code constants, compose paths, compact
      result manifests, and paper references now point to the archive location.
- [x] `src/geocalib` path cleanup completed: added shared path constants in
      `src/geocalib/paths.py`, replaced repeated H001 hypothesis-root constants
      in runnable scripts, and added `src/geocalib/README.md` to separate the
      current VL-SAT/Open3DSG claim path from Qwen-VL and relation-family
      extension code. Verification passed with `py_compile`, table generation,
      all compose config checks, and `git diff --check`.
- [x] `docs/reproducibility.md` fresh-machine path updated: added reproduction
      tiers for Git-only checkout, external result-bundle reproduction, and
      full raw-dataset rerun; expanded required local dataset roots/readiness
      checks; clarified that missing datasets are setup blockers; and replaced
      stale Qwen shard-resume wording with the current completed
      full-validation extension boundary.
- [x] Cleanup and full-validation caveat consistency pass 완료: user-approved cleanup
      paths were deleted, including failed/superseded Open3DSG full-validation
      retry artifacts, generated Python cache, targeted failed/intermediate logs,
      and the historical 127-scan release tar/checksum copy. Primary
      full-validation artifacts, Qwen resume files, datasets, selected
      checkpoints, feature caches, and sensitivity branches were not deleted.
      2026-06-06 cleanup additionally removed the superseded attachment G5d
      smoke output/log, selected stale relative-lateral interim logs, the
      Open3DSG raw-provenance build log, and generated `__pycache__/` folders;
      retained source-of-truth artifacts include `attachment_deferred/full_source_g5d/`,
      Open3DSG `raw_clean_exit_review/`, and Open3DSG
      `h001_covered_recovery/provenance_review/`.
      AAAI Results qualitative counts and stale risk/appendix/progress wording
      were updated for the selected full-validation recovery branch. Docker PDF
      rebuild `logs/h001_aaai_pdf_build_cleanup_consistency_20260605_111759.log`
      exited 0; later table-policy rebuild
      `logs/h001_aaai_pdf_build_table_policy_20260606_094543.log` also exited
      0 but expanded to 10 pages. Compression/layout polish then shortened
      Related Work, Experimental Setup, Results, Limitations, and Conclusion
      without changing the source-result policy. Docker rebuild
      `logs/h001_aaai_pdf_build_compression_20260606_105126.log` exited 0; this
      was later superseded by the low-K table build and then by the
      family-main build
      `logs/h001_aaai_pdf_build_family_main_20260625_084157.log`, which remains
      the latest transient `main.pdf` check before the later archived
      `archive/paper/aaai_snapshots/20260625_top_tier_review.pdf` and
      `archive/paper/aaai_snapshots/20260625_reference_expansion.pdf`
      source-validation builds. That removed default output had 10 total pages with
      technical content on pages 1-7, references on pages 8-9, and checklist on
      page 10. Targeted grep found no missing citations, undefined references,
      overfull hboxes, LaTeX errors, Type 3 fonts, or AAAI package errors.
- [x] Latest AAAI PDF visual/layout inspection after compression: inspect
      pages, table/figure placement, caption readability, and whether the
      full-validation main table plus appendix/sensitivity policy remains
      visible after compression. Result recorded in
      that inspection build: 10 total pages, technical content pages 1-7,
      references pages 8-9, checklist page 10, Open3DSG-main framing preserved,
      full-validation main table policy preserved, and no blocking build issue.
- [x] AAAI paper content/claim QA for the full-validation route completed on
      2026-06-11 KST. Checked main text, appendix/checklist wording, source
      result captions, and paper-facing experiment table artifacts for
      consistency on: full official validation as primary route, Open3DSG
      548/548 recovery branch, exact-label denominator 3,972, and residual
      calibration risk. Patched stale historical values in Table 1/2/3 markdown
      artifacts and updated Table 5 boundary wording. QA record:
      `archive/paper/aaai_snapshots/inspection_20260625/claim_qa_20260611.md`. Docker PDF rebuild
      `logs/h001_aaai_pdf_build_claim_qa_20260611_000409.log` exited 0.
- [x] Reproducibility upload artifact bundle finalized for Google Drive/Zenodo/HF
      style external release. Fixed payload list has 211 files and includes the
      selected official non-avg Open3DSG checkpoint, full-validation VL-SAT
      artifacts, Open3DSG unmodified-source sensitivity artifacts, Open3DSG
      548/548 recovery artifacts, scope contract, tables, manifests, metrics,
      bootstrap summaries, failure rows, and checkpoint-selection provenance.
      Per-file checksum manifest and row-count snapshot were generated under
      `results/h001_geom_reliability/full_validation_transition/artifact_bundle/`.
      Verification script
      `results/h001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh`
      passed with log `logs/h001_fullval_upload_verify_20260611_002319.log`.
- [x] Keep full `relative_horizontal` frozen as appendix/limitation evidence for the current AAAI path, while splitting `left/right` into a narrower `relative_lateral` candidate track.
- [x] Freeze `relative_lateral` family, denominator, geometry policy, and threshold provenance without source metrics. Docker build/run logs: `logs/h001_relative_lateral_policy_freeze_rebuild_20260606_163240.log`, `logs/h001_relative_lateral_policy_freeze_rerun_20260606_163240.log`; output `archive/experiments/H001_geom_reliability/sources/relative_lateral/policy_freeze/`.
- [x] Run `relative_lateral` train/dev policy lock or calibration gate before held-out source metrics. Docker final build/run logs: `logs/h001_relative_lateral_train_dev_lock_final_build_20260606_165717.log`, `logs/h001_relative_lateral_train_dev_lock_final_run_20260606_165717.log`; output `archive/experiments/H001_geom_reliability/sources/relative_lateral/train_dev_policy_lock/`. Status is caveated because dev strict purity gates failed.
- [x] Diagnose `relative_lateral` dev strict contradictions and uncertain rows without changing validation policy. Docker final build/run logs: `logs/h001_relative_lateral_dev_diagnosis_rebuild_20260606_170406.log`, `logs/h001_relative_lateral_dev_diagnosis_rerun_20260606_170406.log`; output `archive/experiments/H001_geom_reliability/sources/relative_lateral/dev_failure_diagnosis/`. Result: strict contradictions are pair-symmetric, concentrated in two dev scans, and about half same-label object pairs; uncertain rows are mostly orthogonal-axis dominance.
- [x] Stop `relative_lateral` for the current AAAI path and record why attempted expansion relations did not promote. Updated `archive/experiments/H001_geom_reliability/sources/relation_expansion_status.md`, `relative_lateral/README.md`, `relative_horizontal/README.md`, `attachment_deferred/README.md`, paper appendix/preview/progress, docs, and TODO. Current decision: no paper-facing lateral source metrics from the current strict policy.
- [x] Qwen-VL full official validation downstream completed as appendix/extension
      evidence: parser validation, adapter export, geometry join,
      metrics/controls, bootstrap CI, failure rows, and deterministic
      qualitative inspection are ready. It remains outside the main claim unless
      explicitly promoted.

### CAND-003

- No active task.

## Next

- [x] Promote `orbit_pairwise_projected_product` as the paper-facing
      relation-algebra-constrained compatibility and regenerate every
      comparator, uncertainty definition, family-wise CI, figure, and table
      from one strict train-only route.

- [x] Regenerate and verify the OpenReview field bundle at
      `release/h001_aaai27_openreview_20260714_170829/`. It contains the current
      8/2/2-page PDFs and a 1.83 MB focused anonymous code/data ZIP; outer and
      internal checksums, archive extraction, and identity-path scans pass.

- [x] Promote the completed `relative_size` evidence only as one main-text scope
      sentence and a full supplement section. Keep the point-rule baseline,
      residual construct-circularity caveat, and no universal two-fusion or
      best-rescorer claim; exclude the family from Figure 1 and the headline
      learned-method evidence.

- [ ] Optional attachment-v2 continuation: complete the frozen 100-row
      mechanism/observability queue, rebuild calibration targets and a verifier
      that do not inherit the legacy `ambiguous_*` policy labels, verify
      train/internal-dev support for every retained mechanism, then lock a new
      model and score before any further source evaluation. Do not tune another
      fusion on the current official-validation diagnostics.

### Archived External-Transfer Route

- [x] ReplicaSSG/FROSS transfer development is complete and de-scoped. It is
      retained as internal provenance only; the active paper is 3DSSG-only and
      makes no dataset-level generalization claim.
- [ ] Optional, not active: if LLM proxy evidence must be promoted beyond a
      diagnostic, collect a human-alignment subset or independent first-pass
      sheets and run the frozen Human V@K evaluator. The current selected route
      does not initiate this collection.

### CAND-001 Data-Dependent Order

- [x] Freeze Open3DSG caveat-reduction retry order and downstream rerun requirements before running heavy jobs.
- [x] Freeze the full official validation scope contract and commands: official
      validation source `local_dataset/3DSSG_subset/relationships_validation.json`,
      157 scans, 548 contexts, 7,720 GT-positive directed pairs, 11,254 GT
      rows, and 3,972 exact-label H001-family GT rows. Record H001-Mini as
      non-metric hypothesis/feasibility evidence and final method provenance as
      train/train-dev-derived. Docker
      `full_validation_scope_contract` generated
      `full_validation_transition/scope_contract/{manifest.json,scope_contract.json,scans.txt,contexts.jsonl,commands.md,report.md}`.
      Additional contract counts: 36,808 candidate directed pairs and 957,008
      expected VL-SAT prediction rows under the all-non-`none` export policy.
- [x] Complete the Open3DSG non-avg downstream branch under
      `sources/open3dsg/non_avg/`: raw stream complete 19,162 rows / 377
      batches; process exit `137` after stream finalization; manual downstream
      services completed raw-dump identity, adapter export, geometry join,
      metric eval, bootstrap CI, and `open3dsg_non_avg_table6_caveats`. Status
      `open3dsg_non_avg_branch_ready`. Do not promote over avg-BLIP without
      explicit user confirmation.
- [x] Regenerate VL-SAT full official validation staging, raw dump/export,
      ground-truth JSONL, geometry join, metrics, controls, GT verifier check,
      bootstrap CI, and table/report artifacts under separate full-validation
      output paths. Completed subgate: Docker `vlsat_full_validation_stage`,
      `vlsat_full_validation_runtime_record`, and
      `vlsat_full_validation_raw_preflight` are ready with 157/157 staged
      scans and `ready_to_run` raw preflight. Completed full route:
      `vlsat_full_validation_raw_dump`,
      `vlsat_full_validation_adapter_export`,
      `vlsat_full_validation_geometry_join`,
      `vlsat_full_validation_metric_eval`,
      `vlsat_full_validation_gt_verifier_eval`, and
      `bootstrap_ci_full_validation_vlsat`. Status
      `vlsat_full_validation_metric_bundle_ready`.
- [x] Regenerate Open3DSG full official validation preprocessing/features/raw
      dump/adapter/geometry/metrics/bootstrap/failure rows under separate
      full-validation output paths. Completed under
      `sources/open3dsg/full_validation/`: payload/views ready; preprocess
      533/548 with 15 missing contexts after recovery; feature seed/audit
      covered-scope 533/533; raw stream 26,746 rows / 533 batches; raw-dump
      identity, adapter, geometry, metrics/controls, bootstrap CI, failure
      rows, and Table 6/caveat report ready. This branch uses the selected
      official non-avg BLIP checkpoint and must not overwrite the existing
      avg-BLIP or non-avg hardened branches. This original 533/548 covered
      branch is retained as an unmodified-source-route sensitivity check after
      the 548/548 recovery branch was selected as main.
- [x] Complete Open3DSG full-validation missing-15 recovery downstream under
      `sources/open3dsg/full_validation/recovery_relaxed_views_min2/`: feature
      audit 548/548, clean-exit raw dump 26,938 rows / 548 batches, raw-dump
      identity, adapter export, geometry join, metrics/controls, bootstrap CI,
      failure rows, and Table 6/caveat regeneration are ready. This is a
      recovery-policy variant because it uses `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`
      and relaxed two-scan view regeneration; do not silently treat it as the
      unmodified Open3DSG preprocessing route.
- [x] Promote the full official validation metric bundles to the AAAI main paper
      route. Decision: VL-SAT full-validation is the controlled-anchor primary
      result; Open3DSG `recovery_relaxed_views_min2/` is the primary
      full-denominator Open3DSG result; original 533/548 covered Open3DSG branch
      is retained as sensitivity/unmodified-source-route evidence.
- [x] Regenerate AAAI paper source-results table / experiment Table 6 wording, appendix
      caveat/provenance, `paper/preview.md`, `paper/progress.md`, and root
      summaries from the selected full-validation route. Required caveat:
      Open3DSG 548/548 is a recovery-policy branch using
      `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus relaxed two-scan view regeneration,
      not the unmodified Open3DSG preprocess route. Completed with full-validation
      AAAI source regeneration, Figure 2 regeneration, Table 6 artifact update,
      appendix/source-summary updates, and Docker PDF build
      `logs/h001_aaai_pdf_build_full_validation_20260605_100108.log` exit 0.
- [x] Verify Open3DSG full-validation raw clean-exit retry/equivalence:
      Docker `open3dsg_full_validation_raw_clean_exit_review` completed with
      exit `0`; outputs live under
      `sources/open3dsg/full_validation/raw_clean_exit_review/`. Result:
      canonical unmodified 533/548 raw stream remains complete at 26,746 rows
      but process exit `137`; the expected retry root
      `raw_dump_exit0_retry_20260605_000241/` is no longer present after prior
      cleanup, so row equivalence cannot be evaluated and the unmodified branch
      cannot be promoted to clean-exit provenance. Keep it as a
      sensitivity/unmodified-source branch with exit-137 caveat. The selected
      548/548 recovery branch remains unaffected and already has raw stream
      exit `0`.
- [x] First, verify the exact non-averaged BLIP route retry and rerun Docker checkpoint selection. Result: R1 completed exit `0`, selected official non-avg checkpoint exists, and separate non-avg downstream H001 raw stream/identity/export/geometry/metrics/bootstrap/Table 6-caveat artifacts are complete under `sources/open3dsg/non_avg/`. Train-dev loss remains worse than avg-BLIP for the historical 127-scan route, while the paper-facing Open3DSG primary route is now the full-validation 548/548 recovery branch.
- [x] Second, optional H001 covered-loadable context retry toward `388/388`:
      dependent H001 eval feature/raw dump, adapter export, geometry join,
      metrics, bootstrap CI, Table 6/caveat wording, and provenance review are
      complete under `sources/open3dsg/h001_covered_recovery/`. Docker
      `open3dsg_h001_covered_recovery_provenance_review` confirms the
      clean-return raw files are row-equivalent to the canonical R2 raw dump
      after excluding run-metadata fields. Use this as appendix sensitivity
      evidence only.
- [x] Verify `attachment_deferred` G5d full-source job: exit file appeared with exit 0; JSON validation passed for manifest/summary/metrics/bootstrap/validation; 69/69 shards, 135,048 scored rows, validation errors 0, source metric status ready, controls/bootstrap ready, 300 failure rows, and Open3DSG 199 missing exact-label GT caveat preserved.

### CAND-001 Non-Data Order

- [x] Build and run Docker `relative_horizontal_scope_audit` to freeze the no-training/no-inference denominator and current unsupported-status audit
- [x] Design the `relative_horizontal` coordinate-frame validation protocol: scan/world frame, room frame, viewpoint frame, axis-flip/wrong-frame control, and ambiguity policy
- [x] Implement Docker `relative_horizontal_coordinate_audit` for GT sign-purity, inverse-pair consistency, wrong-frame controls, and ambiguity buckets
- [x] Inspect `relative_horizontal` `front`/`behind` ambiguity/contradiction buckets from `coordinate_audit/records.jsonl`, emphasizing raw diagnostics rather than the operational threshold, and decide whether to attempt policy refinement or stop as scope-boundary evidence
- [x] Current AAAI-path decision: stop `relative_horizontal` as appendix/limitation evidence, because bucket inspection is meaningful but not strong enough for a broader main claim
- [x] Split `left/right` into `relative_lateral` and freeze policy-only artifact: `left/right` denominator 2,264, `front/behind` deferred denominator 1,306, selected frame `scan_left_neg_x_front_neg_y`, strict purity 0.8005, strict eligible share 0.6466, distinct-left-axis wrong-frame gap 0.0998, train/dev lateral rows 1,538/378, no source metrics.
- [x] Run `relative_lateral` train/dev policy lock/calibration before any held-out VL-SAT/Open3DSG source metrics: completed with 3,832 decision rows and train-only calibrator, but dev strict gate failed (`0.6975` strict purity) while lenient dev signal remains `0.8095`.
- [x] Diagnose dev strict contradictions and uncertain rows without changing held-out validation policy; conclusion is caveated boundary evidence, not a clean promotion route.
- [x] Decide `relative_lateral` current-path action: stop as appendix/future-work boundary; do not run paper-facing lateral source metrics from the current strict policy.
- [ ] Optional only if explicitly continuing this expansion later: run a targeted `front`/`behind` visual/frame-metadata check to test whether the contradiction buckets are annotation-frame artifacts or real geometry-policy failures
- [ ] If coordinate-frame validation becomes defensible after that check, specify the `relative_horizontal` geometry status policy and train-dev calibration/counterfactual generation route
- [ ] Only after those gates, run expanded-family VL-SAT/Open3DSG metric path, controls, bootstrap CI, and failure/audit evidence before changing any main paper claim
- [x] Resume Qwen-VL remaining full-source inference from
      `qwen_full_source_shard_0014`: launched tmux
      `h001_qwen_vl_infer_remaining_resume_20260611_000531`, run id
      `20260611_000531`, log
      `logs/qwen_vl_full_source_infer_remaining_20260611_000531.log`, status
      TSV `logs/qwen_vl_full_source_infer_remaining_20260611_000531.status.tsv`.
      Previous loop `20260527_023111` stopped with exit 1 due to transient GPU
      utilization guard, not OOM or parser failure.
- [x] Re-check official AAAI-27 author kit/live portal: completed 2026-07-12;
      active source uses `aaai2027`, template version 2027.1, separate
      checklist upload, and the verified OpenReview field bundle.
- [ ] Optional final Figure 3 polish: replace geometry panels with rendered scene crops only if a deterministic crop/render path is added for the same locked case IDs
- [x] Keep Open3DSG caveats explicit in the manuscript source-results table and experiment artifact Table 6; 2026-06-06 update fixes the required table policy: the main source-result table uses VL-SAT full-validation plus Open3DSG full-validation 548/548 recovery, while appendix/sensitivity uses Open3DSG historical old 377/388 versus R2 388/388. Main caveats are selected official non-avg checkpoint provenance, filtered train/dev provenance, full-validation exact-label denominator, 548/548 recovery policy, 533/548 full-validation sensitivity branch, appendix historical 377/388 vs R2 388/388 sensitivity, and residual calibration risk. Older averaged-BLIP / 377/388 / `validation_missing_preprocessed:11` wording is historical old-branch wording only.
- [ ] After the Qwen-VL remaining shard loop completes, verify exit/file counts, run full-source parser validation, prediction aggregation/export, geometry join, metrics, controls, bootstrap CI, and audit; keep it as a third semantic source, not a VL-SAT/Open3DSG replacement
- [ ] Optional reduced checkpoint smoke only if the official route is intentionally paused or declared too slow: `dump_features_3rscan_pilot` -> `feature_audit_pilot` -> `train_pilot_reduced`; do not promote to paper-result evidence
- [ ] Optional SceneFun3D/FunGraph3D expansion only if paper scope pivots to robotics/functionality: separate verifier contract, denominator, metrics, and claim boundary
- [x] Optional H001 upgrade path G0: run Docker `attachment_deferred_scope_audit` and freeze no-training/no-inference denominator plus evidence-schema plan before any source metrics
- [x] Optional H001 upgrade path G1: design `attachment_deferred` evidence extractor and output contract before verifier/calibration implementation
- [x] Optional H001 upgrade path G1b: implement a schema-validated evidence-only extractor dry run before verifier/calibration implementation
- [x] Optional H001 upgrade path G1c: validate point-contact and surface-candidate estimators before verifier/calibration implementation
- [x] Optional H001 upgrade path G2: design attachment verifier policy before calibration/counterfactual generation
- [x] Optional H001 upgrade path G3: generate train-dev calibration/counterfactual route before source metrics
- [x] Optional H001 upgrade path G4: run GT verifier evaluation and policy smoke from frozen G3 seeds before source metrics
- [x] Optional H001 upgrade path G4b: inspect attachment false violations, false satisfactions, and uncertain-heavy subtypes; generate targeted visual sanity queue before source metrics
- [x] Optional H001 upgrade path G4c: freeze a strict-only calibration filter that excludes false-satisfied counterfactuals, false-violated positives, and uncertain rows
- [x] Optional H001 upgrade path G5a: fit pooled attachment train-dev calibration from the G4c strict filter
- [x] Optional H001 upgrade path G5b: implement/run bounded attachment VL-SAT/Open3DSG source evidence extraction and p_geom scoring preflight
- [x] Optional H001 upgrade path G5c: freeze full-source scoring/metric protocol, including sharding/runtime budget, output contract, denominator handling, and control order
- [x] Optional H001 upgrade path G5d: full-source attachment VL-SAT/Open3DSG scoring, source metrics, controls, and bootstrap CI completed; do not promote to main claim without explicit final user confirmation
- [ ] Optional function-reasoning pilot only after attachment relation reliability passes GT/counterfactual and source-result gates; keep it as a secondary case study, not a primary claim
- [x] Acquire and execute the official FROSS runtime through the separate
      ReplicaSSG prospective route; the older ScanNet20 adapter idea is
      superseded for current H001 scope.
- [x] Implement the ReplicaSSG/FROSS identity/object-matching adapter and frozen
      evaluation; do not reopen the older `fross_scannet20` path automatically.
- [ ] Relative horizontal coordinate-frame validation is currently blocked for promotion; current paper claim remains unchanged unless ambiguity/policy/metrics/controls/bootstrap/audit reach current H001 evidence level

### CAND-003

- [ ] CAND-003 hypothesis workflow 승격 여부 사용자 판단 대기

## Recently Completed

Historical note for H001: entries below this line are provenance logs from
earlier paper/experiment passes. For current H001 decisions, use `Current
Snapshot`, `Current Phase`, `summary.md`,
`experiments/H001_geom_reliability/README.md`, and
`paper/aaai/README.md`. Older AAAI or ICCV build notes are historical; the
canonical manuscript and upload set are the structured-main build and
`release/h001_aaai27_openreview_20260714_170829/`.

- [x] H001 canonical path and Docker-retention audit completed: active
      method/evaluation/PDF/release owners were reconciled across the root,
      experiment, config, command, and recovery runbooks. The duplicate FROSS
      tags were confirmed to share one image ID; active and conditional image
      roles were documented without deleting any image or external artifact.

- [x] H001 submission-prose precision pass completed: compatibility is now a
      bounded constructed-target score rather than a physical-validity
      probability; source-independence claims are replaced by
      predictor-agnostic/cross-predictor wording; vertical orbit augmentation,
      product log interpretation, and bootstrap units are exact. Figure 1 no
      longer nests a debug screenshot, Figure 2 drops internal K labels, all
      five K values remain in separate Recall and verifier-V tables, and a
      157-scan Docker cluster-bootstrap sensitivity is included. The rebuilt
      main/supplement/checklist are 9/2/2 pages, and the 20260714 upload bundle
      passes outer and 125-file internal manifests plus extracted-source build.

- [x] H001 non-human top-tier strengthening completed: exact metric and
      uncertainty definitions, train-only family-logistic model details,
      six-method cross-source comparisons, factor/family controls, closest-work
      novelty boundaries, and a frozen three-source uncertainty sensitivity
      are reflected in the main paper and three-page supplement. The final
      Docker-built 9/2/2-page PDFs and refreshed anonymous code/data ZIP pass
      font, citation, archive, checksum, and identity-path verification.
- [x] H001 low-K bootstrap CI regenerated from `metrics_k_sweep/metrics.json`:
      Docker `bootstrap_metrics.py` ran with K=`{5,10,20,50,100}`,
      1,000 subgraph resamples, seed `20260526`, and output
      `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/bootstrap_ci_k_sweep/`.
      Status `ready`, warnings `none`; point-estimate mismatch against
      `metrics_k_sweep/metrics.json` is `0`, and K=50/100 point estimates
      exactly match the previous locked bootstrap summary for VL-SAT and
      Open3DSG across reported conditions.
- [x] Open3DSG baseline paper reproduction clean route started: created
      `local_dataset/Open3DSG_staged/baseline_repro` with public Open3DSG
      commit `a568358d6bb718929aa9ff67b2dfdecc4a4c3261`, unfiltered 3DSSG
      train/validation metadata `3852/160`, 160-object and 27-relation
      paper-style label roots, `configs/open3dsg/Dockerfile.legacy`, and
      baseline compose services. Legacy build/CUDA smoke launched in tmux
      `open3dsg_legacy_build_20260705_213816`; log
      `logs/open3dsg_legacy_build_env_20260705_213816.log`.
- [x] H001 Open3DSG paper-table reproduction debug: patched the local
      public-source reproduction copy for BLIP dtype compatibility,
      current-Transformers `max_new_tokens` generation compatibility, and
      3DSSG 160-class object-label namespace alignment; Docker eval completed
      with exit `0`; Object R@5/R@10 recovered from the collapsed
      `0.02120/0.04656` compatibility run to `0.45856/0.56743`; authoritative
      report:
      `experiments/H001_geom_reliability/sources/open3dsg/paper_table_reproduction/report.md`.
- [x] H001 paper `reference_expansion_survey`: checked additional top-tier and adjacent primary sources for claim/contribution support, expanded `paper/references.bib` from 19 to 34 used entries, rewrote AAAI Related Work into role-separated groups, documented the promotion decision in `literature/geocalib_reference_expansion_20260625.md`, and built the snapshot now archived as `archive/paper/aaai_snapshots/20260625_reference_expansion.pdf` with log `logs/h001_aaai_pdf_build_reference_expansion_20260625_130811.log`.
- [x] H001 paper `reviewer_process_and_docs_hygiene_pass`: interpreted CVPR 2026 reviewer training for paper-writing rules in `docs/paper.md`, clarified `docs/` as navigation/workflow-rule/runbook space rather than a progress dashboard, updated `docs/README.md`, `docs/index.md`, `docs/literature.md`, `docs/hypothesis.md`, and promoted the documentation ownership rule to `AGENTS.md`.
- [x] H002 historical stage logs and discarded branches were consolidated into
      the canonical README, claim/method contracts, `report/report_0706.md`, and
      compact Docker artifacts; deleted stage paths are no longer authoritative.

- [x] Open3DSG full-validation missing-15 recovery downstream 완료:
      `sources/open3dsg/full_validation/recovery_relaxed_views_min2/` now has
      feature audit 548/548, clean-exit raw stream 26,938 rows / 548 batches,
      raw-dump identity, adapter export 695,916 prediction rows, geometry join
      695,916 rows with 160,596 H001-family geometry-checkable rows,
      metrics/controls, bootstrap CI, 82,155 failure rows, and Table 6/caveat
      regeneration ready. Low-K metrics are ready in `metrics_k_sweep/` for
      K=`{5,10,20,50,100}` and K=50/100 matches locked `metrics/`. Key
      Open3DSG pattern: semantic_only R@5/R@10 `0.0368/0.1002`, V@5/V@10
      `0.5131/0.3255`; family_conditional_risk R@5/R@10
      `0.0984/0.1921`, V@5/V@10 `0.0420/0.0482`. Caveat:
      this is a recovery-policy variant using `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`
      and relaxed view regeneration for two scans, not the unmodified Open3DSG
      preprocess route.
- [x] Full-validation failure-analysis/qualitative artifact refresh 완료:
      source-agnostic H001 failure schema allows Open3DSG and VL-SAT rows;
      VL-SAT full-validation has 59,841 failure rows and 36 inspected
      qualitative cases; Open3DSG recovery full-validation has 82,155 failure
      rows and a new 36-case recovery inspection. Updated local README files
      and reproducibility bundle plan to make full-validation the artifact
      default.
- [x] VL-SAT full-validation metric bundle 완료: tmux raw dump `h001_vlsat_full_validation_raw_20260604_204428` completed with log `logs/vlsat_full_validation_raw_20260604_204428.log`, raw status `raw_dump_ready`, 548 raw subgraph rows, 36,808 directed pairs, and errors 0. Docker downstream services completed adapter export, geometry join, metric eval, GT verifier eval, and VL-SAT-only bootstrap CI under `experiments/H001_geom_reliability/sources/vlsat/full_validation/`. Outputs: 957,008 predictions, 11,254 GT rows, 3,972 H001-family GT rows, metrics status `ready`, GT verifier AUROC `0.9772`, bootstrap warnings 0. Key metric pattern: probabilistic recalibration improves R@100 `0.9635 -> 0.9688` while reducing V@100 `0.0476 -> 0.0404`; rule filtering gives V@100 `0.0` with R@100 `0.9627`; `family_conditional_risk` gives R@100 `0.9683` and V@100 `0.0333`.
- [x] Open3DSG full-validation 1-8 route 완료: Docker full-validation payload/views/preprocess coverage audit, recovery attempt, feature seed/audit, selected-checkpoint raw dump, adapter export, raw-dump identity, geometry join, metrics/controls, bootstrap CI, failure rows, and Table 6/caveat regeneration completed under `experiments/H001_geom_reliability/sources/open3dsg/full_validation/`. Views 157/157, preprocess 533/548 with 15 missing contexts after recovery, covered-scope features 533/533, raw stream 26,746 rows / 533 completed batches, adapter 690,924 predictions, geometry 690,924 rows, metrics status `ready`, bootstrap status `ready`, failure rows 81,448, and table/caveat status `open3dsg_full_validation_table_caveats_ready`. Key metrics: semantic_only R@50/R@100 `0.4043/0.5111`, V@50/@100 `0.1387/0.1242`; probabilistic_recalibrated R@50/R@100 `0.3943/0.5685`, V@50/@100 `0.0590/0.0807`; rule_verified_point_subtype R@50/R@100 `0.4242/0.5320`, V@50/@100 `0.0/0.0`; `family_conditional_risk` R@50/R@100 `0.4612/0.5999`, V@50/@100 `0.0265/0.0332`. Caveats: selected official non-avg BLIP checkpoint route, raw process exit `137` after stream finalization, and 15 missing preprocessed contexts.
- [x] Open3DSG official non-avg downstream 완료: raw stream wrote 19,162 rows and 377/377 completed batches under `sources/open3dsg/non_avg/raw_dump/`, then process exited `137` after stream finalization. Manual downstream services completed raw-dump identity, adapter export, geometry join, metric eval, bootstrap CI, and Table 6/caveat report. Status `open3dsg_non_avg_branch_ready`. Non-avg metrics: semantic_only R@50/R@100 `0.4310/0.5320`, V@50/@100 `0.1395/0.1256`; probabilistic_recalibrated R@50/R@100 `0.3945/0.5639`, V@50/@100 `0.0570/0.0782`; rule_verified_point_subtype R@50/R@100 `0.4507/0.5481`, V@50/@100 `0.0/0.0`; `family_conditional_risk` R@50/R@100 `0.4750/0.6047`, V@50/@100 `0.0243/0.0310`. For the historical 127-scan route, avg-BLIP remains stronger on train-dev loss; main paper Open3DSG evidence now comes from the full-validation recovery branch.
- [x] Open3DSG non-avg downstream branch setup/preflight 완료: `compose.open3dsg.yaml` and experiment `compose.yaml` now include separate non-avg services/output roots, H001 eval feature tensor compatibility was checked for the non-avg projector route, Docker `feature_audit_h001_eval_nonavg` ran with only known `validation_missing_preprocessed:11`, Docker `eval_preflight_nonavg` reported `ready`, Docker `open3dsg_raw_dump_identity_nonavg` produced a checklist with raw dump missing, Docker `open3dsg_non_avg_table6_caveats` is blocked only by missing non-avg metrics, and tmux raw dump `h001_open3dsg_eval_nonavg_stream_20260604_182423` was launched under `sources/open3dsg/non_avg/raw_dump/`.
- [x] Open3DSG non-avg downstream continuation launch 완료: host-side runner `scripts/run_open3dsg_nonavg_downstream_after_raw.sh` and run record `experiments/H001_geom_reliability/sources/open3dsg/non_avg/downstream_after_raw_20260604_183622.md` were added. The continuation stopped because raw process exit was `137` after stream finalization; it was superseded by manual downstream completion.
- [x] Open3DSG R1 exact non-avg BLIP closeout 완료: background job `h001_open3dsg_train_full_nonavg_retry_20260601_071908` exited `0` at `2026-06-04T17:01:07+09:00`; final training reached epoch 99 / global step 93600. Docker `open3dsg_checkpoint_selection` was rebuilt/rerun and generated `sources/open3dsg/checkpoint_selection/{manifest.json,report.md}` with status `checkpoint_selection_ready_official_non_avg_blip`; selected checkpoint `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt`, sha256 `ca86d429b19e846aec2bfff014256bf36f6f90da07e566b90c461d6eca8d76bb`, train-dev `val/loss=0.5724539160728455` at step 13103. Docker `open3dsg_caveat_reduction_plan` and `open3dsg_paper_caveats` were rebuilt/rerun before the full-validation promotion; the later non-avg downstream branch and full-validation `recovery_relaxed_views_min2/` branch are now complete. Final route judgment: the historical 127-scan route keeps avg-BLIP as stronger by train-dev loss, while the current paper-facing Open3DSG evidence uses the selected official non-avg checkpoint on the full-validation recovery-policy branch with explicit caveat wording.
- [x] Docker `open3dsg_caveat_reduction_plan` 완료: initial stale-image run log `logs/h001_open3dsg_caveat_reduction_plan_20260528_170347.log` exited 2 because the new script was not yet copied into the existing image; image rebuild log `logs/h001_open3dsg_caveat_reduction_plan_build_20260528_170356.log` exited 0, and final Docker service run log `logs/h001_open3dsg_caveat_reduction_plan_20260528_170410.log` exited 0. Outputs `experiments/H001_geom_reliability/sources/open3dsg/caveat_reduction_plan/{manifest.json,retry_plan.json,commands.md,report.md}`. Status `open3dsg_caveat_reduction_plan_frozen_no_execution`; validation errors 0. Frozen order: R1 exact non-averaged BLIP retry, R2 H001 covered-loadable context retry toward `388/388`, R3 attachment G5d only after Open3DSG decisions. Current decomposition: attachment Open3DSG missing exact-label GT rows 199 total, 23 from missing preprocessed H001 contexts and 176 from absent Open3DSG candidate pairs. This is no-execution planning evidence only and does not change current AAAI claim wording.
- [x] Docker `attachment_deferred_full_source_protocol` 완료: final Docker image rebuild log `logs/h001_attachment_deferred_full_source_protocol_build_20260528_161447.log` exit 0, final Docker service run log `logs/h001_attachment_deferred_full_source_protocol_run_20260528_161447.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_source_protocol/{manifest.json,protocol.json,denominator_audit.json,shards.jsonl,validation.json,commands.md,report.md}`. Status `attachment_deferred_full_source_protocol_frozen_no_metrics`; validation errors 0; expected full-source rows 135,048; deterministic shards 69 with rows-per-shard 2,000; global attachment exact-label GT denominator 967; VL-SAT covered denominator 967/967; Open3DSG covered denominator 768/967 with 199 missing exact-label GT rows. Frozen metric conditions are `semantic_only`, `probabilistic_recalibrated`, `rule_verified_attachment_policy`, `control_p_geom_valid_only`, `control_distance_only`, `control_shuffled_geometry`, and `control_wrong_pair_geometry`. This is protocol evidence only: no full-source scoring, source metrics, controls, bootstrap CI, failure/audit, or main AAAI claim update.
- [x] Docker `attachment_deferred_source_scoring_preflight` 완료: final Docker image rebuild log `logs/h001_attachment_deferred_source_scoring_preflight_build_20260528_155705.log` exit 0, final Docker service run log `logs/h001_attachment_deferred_source_scoring_preflight_run_20260528_155725.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/source_scoring_preflight/{manifest.json,summary.json,source_rows.jsonl,evidence_rows.jsonl,diagnostics.jsonl,scored_rows.jsonl,commands.md,report.md}`. Status `attachment_deferred_source_scoring_preflight_ready_no_metrics`; selected/scored source rows 120; source counts Open3DSG 60 and VL-SAT 60; label counts `attached to` 40, `connected to` 40, `hanging on` 40; selected unique scans 20 per source; evidence rows ready 120/120; validation errors 0; mean/median p_geom_valid `0.36097181955688334` / `0.057955692988128193`; full source rows remain VL-SAT 77,748 and Open3DSG 57,300. This is bounded preflight only: no R@K, Violation@K, controls, bootstrap CI, full-source scoring, or main AAAI claim update.
- [x] Docker `attachment_deferred_calibration_fit` 완료: final Docker image rebuild log `logs/h001_attachment_deferred_calibration_fit_build_20260528_152626.log` exit 0, final Docker service run log `logs/h001_attachment_deferred_calibration_fit_run_20260528_152639.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/calibration_fit/{manifest.json,model.json,metrics.json,scores.jsonl,commands.md,report.md}`. Status `attachment_deferred_calibration_fit_ready_no_source_metrics`; model id `h001-attachment-deferred-p-geom-valid-strict-v1`; train/dev rows 242/83; dev positives/negatives 27/56; dev Brier/NLL/ECE `0.0010268071750410028` / `0.0077383149722480785` / `0.007145890189565561`; dev AUROC/AUPRC `1.0/1.0`. Warnings: `connected_to_dev_absent_use_pooled_or_train_only_caveat` and `strict_subset_nearly_separable_not_source_metric_evidence`. This is fitted calibration only; it does not score source predictions, compute source metrics, run controls/bootstrap, or change the current AAAI main claim.
- [x] Docker `attachment_deferred_strict_filter_freeze` 완료: final Docker image rebuild log `logs/h001_attachment_deferred_strict_filter_freeze_build_20260528_151133.log` exit 0, final Docker service run log `logs/h001_attachment_deferred_strict_filter_freeze_run_20260528_151144.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/strict_filter_freeze/{manifest.json,summary.json,freeze_policy.json,strict_calibration_rows.jsonl,excluded_rows.jsonl,commands.md,report.md}`. Status `attachment_deferred_strict_filter_frozen_no_fit_no_source_metrics`; strict calibration rows 325, strict positives 121, strict negatives 204, excluded rows 436. Strict label counts: `attached to` 200, `hanging on` 113, `connected to` 12. Split counts: train 242, dev 83. Warning: `connected to` has no dev strict rows, so future connected-to family-specific calibration requires pooled calibration, augmented dev selection, or explicit limitation. This does not fit calibration, score source predictions, compute source metrics, run bootstrap/audit, or change the current AAAI main claim.
- [x] Docker `attachment_deferred_error_visual_sanity` 완료: final Docker image rebuild log `logs/h001_attachment_deferred_error_visual_sanity_build_20260528_145040.log` exit 0, final Docker service run log `logs/h001_attachment_deferred_error_visual_sanity_run_20260528_145040.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/error_visual_sanity/{manifest.json,summary.json,review_cases.jsonl,visual_queue.jsonl,calibration_filter.jsonl,guide.md,commands.md,report.md}`. Status `attachment_deferred_error_visual_sanity_plan_ready_no_source_metrics`; review cases 436, visual queue 50, calibration filter rows 761. Case distribution: strict positives 121, strict negatives 204, false-satisfied counterfactuals 77, false-violated positives 30, uncertain positives 164, uncertain counterfactuals 165. Queue is label-diverse: `attached to` 38, `connected to` 6, `hanging on` 6. Calibration guidance: exclude/review false-satisfied counterfactuals, visually check false-violated positives before relaxing policy, and keep uncertain rows out of strict calibration unless a soft-label protocol is defined. This does not fit calibration, score source predictions, compute source metrics, run bootstrap/audit, or change the current AAAI main claim.
- [x] Docker `attachment_deferred_gt_policy_smoke` 완료: final Docker image rebuild log `logs/h001_attachment_deferred_gt_policy_smoke_build_20260528_143827.log` exit 0, final Docker service run log `logs/h001_attachment_deferred_gt_policy_smoke_run_20260528_143827.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/gt_policy_smoke/{manifest.json,summary.json,validation.json,policy_smoke_decisions.jsonl,gt_evidence_rows.jsonl,gt_evidence_diagnostics.jsonl,gt_policy_decisions.jsonl,gt_eval_rows.jsonl,visual_sanity_plan.json,commands.md,report.md}`. Status `attachment_deferred_gt_policy_smoke_ready_no_source_metrics`; 36/36 policy-smoke decision rows and 761/761 train-dev seed decision rows pass schema validation with scan errors 0 and ready evidence rows 761/761. GT/counterfactual policy evaluation: positive nonviolated 0.9048, positive strict satisfied 0.3841, counterfactual nonsatisfied 0.8274, counterfactual strict violated 0.4574, calibration-ready counterfactual negatives 204/446, uncertain rate 0.4323. This does not fit `p_geom_valid`, score VL-SAT/Open3DSG, compute source metrics, run controls/bootstrap, run visual audit, or change the current AAAI main claim. Main-claim promotion requires explicit final user confirmation.
- [x] Docker `attachment_deferred_calibration_counterfactuals` 완료: final Docker image rebuild log `logs/h001_attachment_deferred_calibration_counterfactuals_build_20260528_141402.log` exit 0, final Docker service run log `logs/h001_attachment_deferred_calibration_counterfactuals_run_20260528_141402.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/calibration_counterfactuals/{manifest.json,positive_seeds.jsonl,counterfactual_seeds.jsonl,split_plan.json,counterfactual_plan.json,policy_smoke_plan.json,gt_eval_inputs.json,threshold_freeze_protocol.json,commands.md,report.md}`. Status `attachment_deferred_calibration_counterfactual_plan_ready_no_fit_no_metrics`; 315 train/dev positive seeds and 446 counterfactual negative seeds are ready, held-out scan overlap is 0, and source metrics remain blocked. Warning: dev split has no `connected to` positive seed, so future connected-to family-specific calibration needs pooled calibration, augmented dev selection, or explicit limitation. This emits no decision rows, fits no calibration, scores no source predictions, and computes no metrics; subsequent G4 policy smoke is now complete.
- [x] Docker `attachment_deferred_verifier_policy` 완료: direct Docker image rebuild log `logs/h001_attachment_deferred_verifier_policy_build_20260528_095223.log` exit 0, Docker service run log `logs/h001_attachment_deferred_verifier_policy_run_20260528_095223.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/verifier_policy/{manifest.json,verifier_policy.json,decision_schema.json,threshold_plan.json,reason_codes.json,calibration_plan.json,commands.md,report.md}`. Status `attachment_deferred_verifier_policy_ready_no_decisions_no_metrics`; 9 subtype rules are covered, conservative defaults are near-contact 0.05m, uncertain contact band 0.05-0.15m, clear-far distance 0.30m, min near-contact points 3, and min contact patch score 0.20. This emits no decision rows, fits no calibration, scores no source predictions, and computes no metrics; subsequent gate `G3_attachment_calibration_counterfactual_generation` is now complete.
- [x] Docker `attachment_deferred_point_surface_validation` 완료: direct Docker image rebuild log `logs/h001_attachment_deferred_point_surface_validation_build_20260528_015503.log` exit 0, Docker service run log `logs/h001_attachment_deferred_point_surface_validation_run_20260528_015503.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/point_surface_validation/{rows.jsonl,diagnostics.jsonl,manifest.json,summary.json,validation.json,report.md}`. Status `attachment_deferred_point_surface_validation_ready_no_verifier`; 36 input rows -> 36 output rows, validation errors 0, ready rows 36, point available rows 36, normal available rows 36, near-contact rows 27, surface normal classes horizontal_up 14 / vertical 21 / slanted 1, and forbidden verifier/metric fields are absent. This is still evidence-only validation, not source metric evidence; next gate is `G2_attachment_verifier_policy_design`.
- [x] Docker `attachment_deferred_extractor_dry_run` 완료: direct Docker image rebuild log `logs/h001_attachment_deferred_extractor_dry_run_build_20260528_013413.log` exit 0, Docker service run log `logs/h001_attachment_deferred_extractor_dry_run_run_20260528_013413.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/extractor_dry_run/{rows.jsonl,manifest.json,summary.json,validation.json,report.md}`. Status `attachment_deferred_extractor_dry_run_ready_no_verifier`; 36 input rows -> 36 output rows, validation errors 0, source rows 9 each for `gt_positive`, `counterfactual`, `vlsat_closed_set`, and `open3dsg_ov`, labels 12 each for `attached to`, `hanging on`, and `connected to`. Forbidden verifier/metric fields are absent. All rows were `partial` because the dry run used semseg OBB and `dominantNormal` proxies only; subsequent G1c validation is now complete.
- [x] Docker `attachment_deferred_extractor_contract` 완료: direct Docker image rebuild log `logs/h001_attachment_deferred_extractor_contract_build_20260528_011439.log` exit 0, Docker service run log `logs/h001_attachment_deferred_extractor_contract_run_20260528_011439.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/evidence_extractor/{manifest.json,extractor_contract.json,output_schema.json,field_catalog.json,subtype_policy.json,extraction_plan.json,validation_plan.json,example_row.json,commands.md,report.md}`. Status `attachment_deferred_extractor_contract_ready_no_extraction`; it freezes identity/OBB/point-contact/surface-normal/gravity/contradictory-support/affordance-context fields and explicitly forbids verifier/metric outputs. This was superseded by the completed G1b dry run; current AAAI main claim remains unchanged.
- [x] Docker `attachment_deferred_scope_audit` 완료: direct Docker image rebuild log `logs/h001_attachment_deferred_scope_build_20260528_010443.log` exit 0, Docker service run log `logs/h001_attachment_deferred_scope_run_20260528_010443.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/attachment_deferred/scope_audit/{manifest.json,label_counts.json,evidence_schema.json,report.md}`. Status `attachment_deferred_scope_schema_ready_no_metric_execution`; current H001 GT denominator 2,545, attachment GT rows 967, expanded candidate denominator 3,512/7,505, VL-SAT candidate rows 77,748, Open3DSG candidate rows 57,300, and existing verification status `unsupported` for both sources. Next gate is `G1_attachment_evidence_extractor_design`; current AAAI main claim remains unchanged.
- [x] `attachment_deferred` future expansion strategy frozen: `archive/experiments/H001_geom_reliability/sources/attachment_deferred/README.md` records why this is the preferred relation-family upgrade over `relative_horizontal`, current counts (967 GT rows, VL-SAT 77,748 prediction rows, Open3DSG 57,300 prediction rows), required evidence schema, verifier/calibration gates, source metric path, and optional function-reasoning pilot boundary. Current AAAI main claim remains unchanged.
- [x] AAAI manuscript future-work wording updated for `attachment_deferred`: `paper/aaai/sec/7_limitations.tex` and `sec/8_conclusion.tex` now frame attachment-style physical relations as the nearest family upgrade before broader functional reasoning. Docker PDF rebuild `logs/h001_aaai_pdf_build_attachment_strategy_20260528_004342.log` exit 0; `paper/aaai/main.pdf` remains 9 pages / US Letter with no missing citations, undefined references, overfull hboxes, LaTeX errors, or AAAI package errors.
- [x] `relative_horizontal` AAAI-path decision 고정: scope audit / coordinate audit / bucket inspection 결과는 threshold-free scope-boundary evidence로 보존하되, current paper claim에는 추가하지 않는다. Rationale: selected frame and wrong-frame gap show non-random signal, but `front`/`behind` ambiguity and contradiction buckets are too large for a defensible broader main claim. Any future promotion requires targeted visual/frame-metadata check first, then the full verifier/calibration/metrics/control/bootstrap/audit path.
- [x] Docker `relative_horizontal_bucket_inspection` 완료: direct Docker image rebuild log `logs/h001_relative_horizontal_bucket_inspection_build_20260527_234744.log` exit 0, Docker service run log `logs/h001_relative_horizontal_bucket_inspection_run_20260527_234755.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/relative_horizontal/bucket_inspection/{manifest.json,summary.json,examples.jsonl,report.md}`. Status `relative_horizontal_bucket_inspection_ready_no_metric_execution`; selected frame `scan_left_neg_x_front_neg_y`, inverse consistency 1.0, wrong-frame gap 0.1231, `front`/`behind` strict match:contradiction 2.9143, `front`/`behind` strict purity 0.7445, sign-only purity 0.7491, `left`/`right` strict purity 0.8005. `front`/`behind` ambiguity flags are `axis_margin_ambiguous` 230, `conflicting_axis_dominates` 430, and `strong_projected_overlap` 44. Recommendation is `do_not_promote_relative_horizontal_to_main_claim`; do not run expanded-family metrics unless a targeted visual/frame-metadata check resolves the `front`/`behind` issue.

- [x] Docker `relative_horizontal_coordinate_audit` 완료: direct Docker image rebuild log `logs/h001_relative_horizontal_coordinate_audit_build_20260527_212831.log` exit 0, Docker service run log `logs/h001_relative_horizontal_coordinate_audit_run_20260527_212845.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/relative_horizontal/coordinate_audit/{manifest.json,frame_metrics.json,records.jsonl,ambiguity_buckets.json,report.md}`. Status `relative_horizontal_coordinate_audit_blocked_no_metric_execution`; 3,570 GT rows across 125 scans and 16 frame variants were audited. Best candidate is `scan_left_neg_x_front_neg_y` with macro strict purity 0.7725, strict eligible share 0.6403, macro sign-only purity 0.7626, `left`/`right` strict purity 0.8005, `front`/`behind` strict purity 0.7445, inverse consistency 3,570/3,570 = 1.0, and wrong-frame gap 0.1231. This is not metric evidence and does not change the current paper claim; follow-up bucket inspection is now complete and also blocks promotion.
- [x] `relative_horizontal` coordinate-frame protocol 고정 완료: `archive/experiments/H001_geom_reliability/sources/relative_horizontal/coordinate_frame_protocol.md`를 추가했다. H0 scan/world XY, H1 axis-flip/swap, H2 room-layout principal frame, H3 viewpoint/annotator frame, H4 object-centric frame을 가설로 두고, GT sign-purity, directed inverse-pair consistency, wrong-frame/axis-flip control, ambiguity bucket, visual sanity check를 promotion gate로 고정했다. Provisional promotion thresholds는 macro sign-purity >= 0.80, per-label >= 0.75 unless uncertain, inverse consistency >= 0.85, visual contradiction <= 0.10이다. 아직 metric evidence가 아니며 current paper claim은 변경하지 않는다.
- [x] Docker `relative_horizontal_scope_audit` 완료: direct Docker image rebuild log `logs/h001_relative_horizontal_scope_audit_direct_build_20260527_211130.log` exit 0, Docker service run log `logs/h001_relative_horizontal_scope_audit_run_20260527_211142.log` exit 0. Outputs `archive/experiments/H001_geom_reliability/sources/relative_horizontal/scope_audit/{manifest.json,label_counts.json,report.md}`. Status `relative_horizontal_scope_audit_ready_no_metric_execution`; current H001 denominator 2,545, `relative_horizontal` 3,570 GT rows, expanded candidate denominator 6,115/7,505 = 0.8148, labels `left/right/front/behind` = 1,132/1,132/653/653, source rows VL-SAT 103,664 and Open3DSG 76,400, current verification status unsupported for both sources. Next blocker is coordinate-frame semantics, not data availability.
- [x] `relative_horizontal` expansion track planning 시작: current paper claim은 `support_contact` / `proximity` / `relative_vertical` scoped reliability로 유지하고, `relative_horizontal`은 framework 확장 가능성을 검증하는 별도 트랙으로 분리했다. `paper/risk.md`, `docs/paper.md`, `experiments/H001_geom_reliability/README.md`, and `archive/experiments/H001_geom_reliability/sources/relative_horizontal/README.md`에 promotion gate를 기록했다. 핵심 조건은 coordinate-frame semantics, denominator, verifier policy, calibration, GT verifier evaluation, VL-SAT/Open3DSG metrics, controls, bootstrap CI, and failure/audit evidence가 current H001 evidence level에 도달해야 main claim 승격이 가능하다는 것이다.
- [x] Paper appendix/provenance and Open3DSG caveat-consistency pass 완료: `AGENTS.md` Reading Protocol을 `AGENTS.md` first -> `README.md`/`TODO.md`/`docs/index.md` 순서로 맞췄다. `paper/appendix.md`를 생성해 calibrator/threshold provenance table, Open3DSG caveat consistency pass, Figure 3 optionality, and Qwen-VL third-source boundary를 기록했다. `paper/aaai/sec/6_results.tex` source-results table caption에 residual calibration-risk wording을 추가했고, `src/geocalib/build_tables.py`를 수정한 뒤 Docker image rebuild + `table_builder` rerun으로 experiment Table 6에 `caveat_note`를 추가했다. AAAI PDF rebuild도 exit 0이며 9 pages / US Letter / no blocking LaTeX or AAAI warnings이다. Logs: `logs/h001_geom_image_rebuild_table6_caveat_20260527_202425.log`, `logs/h001_table_builder_caveat_consistency_20260527_202425.log`, `logs/h001_aaai_pdf_build_appendix_caveat_20260527_202734.log`.
- [x] `paper/README.md` 생성 완료: `preview.md`를 README로 rename하지 않고, `paper/README.md`를 folder-local entry point로 추가했다. `preview.md`, `progress.md`, `outline.md`, `draft.md`, `figures.md`, `risk.md`, `references.bib`, `aaai/`, `iccv/`, `generated/figures/`, and `scripts/`의 역할과 paper reading/update rules를 명시했다. Root/docs/summary/reproducibility pointers도 `paper/README.md`와 `paper/risk.md`를 포함하도록 갱신했다.
- [x] Hypothesis README 중복 정리 완료: `hypothesis/CAND-001/README.md` 내용을 `archive/hypothesis_records/hypothesis/README.md`로 병합하고 candidate README를 삭제했다. 앞으로 CAND-001처럼 active hypothesis가 하나인 경우 root hypothesis index가 candidate summary도 함께 소유하고, candidate-level README는 여러 active hypotheses가 생길 때만 만든다.
- [x] `docs/literature.md`, `docs/hypothesis.md`, `docs/paper.md`, `docs/index.md` ownership 업데이트 완료: literature workflow는 `docs/literature.md`가 authoritative owner이고 `AGENTS.md`에는 중복 workflow를 두지 않도록 정리했다. Hypothesis/Paper docs도 workflow-specific rulebook 역할과 실제 상태/산출물 owner를 명시했다.
- [x] `AGENTS.md`와 `docs/index.md` 문서 책임 구조 보강 완료: `AGENTS.md = 상위 project instruction / 파일 책임 / stable rules`, `docs/*.md`와 각 폴더 `README.md = workflow-specific rule / runbook / current state` 구조를 명시했고, `docs/index.md`에 `Docs Directory Usage`를 추가해 `docs/literature.md`, `docs/hypothesis.md`, `docs/paper.md`, `docs/reproducibility.md`의 사용 역할을 정리했다.
- [x] `AGENTS.md` / `docs/reproducibility.md` 운영 규칙 업데이트 완료: `AGENTS.md`는 세부 artifact list가 아니라 file-role map, reading protocol, documentation ownership rules, H001 scoped claim boundary, Open3DSG/Qwen policy, background-loop handling, and artifact handoff/cleanup rules를 담는 상위 운영 문서로 재정리했다. H001 resume/verification/upload/delete의 상세 파일 목록과 명령은 `docs/reproducibility.md`, `paper/preview.md`, and relevant experiment/source README가 소유한다.
- [x] Qwen-VL remaining loop status check 완료: tmux `h001_qwen_vl_infer_remaining` is inactive and exit file `logs/qwen_vl_full_source_infer_remaining_20260527_023111.exit` contains `1`. Status TSV shows shards `qwen_full_source_shard_0001`-`0013` finished with exit 0, then `qwen_full_source_shard_0014` finished with exit 1 at 2026-05-27 03:18:36 KST. Runtime manifests show 14 complete shards including shard 0000, 3,500 completed rows total, and shard 0014 status `blocked_full_source_inference_shard`. The blocker is `gpu_busy_or_unavailable:memory_used_mb=4349,utilization=36`, just above the 35% guard threshold. No shard 0014 prediction/raw/progress rows were written, so resume should start cleanly from shard 0014.
- [x] `paper/aaai/aaai2026.*` official AAAI-26 Author Kit verification/replacement 완료: official page `https://aaai.org/authorkit26-1/` redirects to `https://aaai.org/wp-content/uploads/2025/07/AuthorKit26-1.zip`, zip SHA256 `d2844ec68a4a9396d749fcca5b5784809617b670863e8d4fecbfb00e444fc3af`, check log `logs/aaai_author_kit_check_20260527_024724.log`. `aaai2026.sty` differed from the previous mirror copy and was replaced from `AuthorKit26/AnonymousSubmission/LaTeX/aaai2026.sty`; `aaai2026.bst` already matched the official kit. Official-kit Docker PDF rebuild `logs/h001_aaai_pdf_build_official_kit_20260527_024752.log` exit 0; `paper/aaai/main.pdf` remains 9 pages, US Letter, with no missing citations, undefined refs, overfull hboxes, LaTeX errors, or AAAI package errors. `https://aaai.org/conference/aaai/aaai-27/submission-instructions/` redirected to an older AAAI-25 page, so no official AAAI-27 kit is confirmed.
- [x] Qwen-VL remaining full-source inference shard loop launched as a sequential resumable background job: tmux `h001_qwen_vl_infer_remaining`, run id `20260527_023111`, log `logs/qwen_vl_full_source_infer_remaining_20260527_023111.log`, status TSV `logs/qwen_vl_full_source_infer_remaining_20260527_023111.status.tsv`, exit file `logs/qwen_vl_full_source_infer_remaining_20260527_023111.exit`, command `QWEN_VL_LOOP_RUN_ID=20260527_023111 QWEN_VL_LOOP_START_SUFFIX=0001 QWEN_VL_LOOP_END_SUFFIX=0133 bash scripts/run_qwen_vl_full_source_shard_loop.sh`. Scope is `qwen_full_source_shard_0001` through `qwen_full_source_shard_0133`, 133 shards, 33,134 expected rows. Pre-launch GPU guard was acceptable (`memory.used=4349MB`, `utilization=23%` at 2026-05-27 02:31 KST). Lightweight post-launch check showed tmux active, no exit file yet, shard 0001 finished with exit 0 and shard 0002 started. This remains non-metric runtime generation, not paper evidence.
- [x] Qwen-VL full-source inference shard 0000 완료 및 contract validation 통과: tmux `h001_qwen_vl_infer_qwen_full_source_shard_0000` ended with exit `0`, log `logs/qwen_vl_full_source_infer_qwen_full_source_shard_0000_20260527_021706.log`, exit file `logs/qwen_vl_full_source_infer_qwen_full_source_shard_0000_20260527_021706.exit`. Runtime manifest `full_source_runtime/manifests/qwen_full_source_shard_0000.json` reports `full_source_inference_shard_complete`, 250 prediction rows, 250 raw-response rows, 250 completed rows, parser status `parsed:250`, row status `ok:250`. Docker contract validation log `logs/qwen_vl_full_source_shard0000_contract_validate_20260527_022224.log` exit 0 produced `full_source_runtime/validation/qwen_full_source_shard_0000/{manifest.json,parsed.jsonl,parser_contract.json,report.md}` with 33,384 input rows checked, 250 parsed rows, 0 input errors, 0 output errors, 0 warnings. This remains non-metric third-source evidence until all shards and downstream geometry/metric/audit stages complete.
- [x] Qwen-VL full-source inference shard 0000 background launch 완료: pre-launch GPU guard was acceptable (`memory.used=4349MB`, `utilization=25%` at 2026-05-27 02:16:50 KST). Launched tmux `h001_qwen_vl_infer_qwen_full_source_shard_0000` at 2026-05-27 02:17:06 KST with log `logs/qwen_vl_full_source_infer_qwen_full_source_shard_0000_20260527_021706.log` and exit file `logs/qwen_vl_full_source_infer_qwen_full_source_shard_0000_20260527_021706.exit`. Expected shard rows: 250. This launch is not paper metric evidence; parser validation, adapter export, geometry join, metrics, controls, bootstrap, and audit remain required.
- [x] Qwen-VL full-source sharded inference runner plan 완료: added `run_qwen_vl_full_source_inference.py`, `plan_qwen_vl_full_source_inference.py`, Docker service `qwen_vl_full_source_inference_plan`, and Qwen runtime services `qwen_vl_full_source_infer_dry_run` / `qwen_vl_full_source_infer_shard`. Rebuilt `h001-geom-reliability:latest` with log `logs/h001_geom_image_rebuild_qwen_inference_plan_20260527_020239.log` exit 0 and `h001-qwen-vl-runtime:cu128` with log `logs/qwen_vl_runtime_image_rebuild_full_source_runner_20260527_020253.log` exit 0. Docker plan log `logs/qwen_vl_full_source_inference_plan_20260527_020314.log` exit 0 generated `full_source_inference_plan/{manifest.json,runner_contract.json,shards.jsonl,commands.md,report.md}` with status `full_source_inference_runner_frozen_no_inference`, 33,384 planned rows, 134 shards, and 11,128 verified unique pair crops. Docker dry-run log `logs/qwen_vl_full_source_infer_dry_run_shard0000_20260527_020324.log` exit 0 generated `full_source_runtime/dry_runs/qwen_full_source_shard_0000.json` with status `full_source_inference_shard_dry_run_ready`, 250 rows, 84 unique pair crops, and 0 blockers. No Qwen model load or inference was run.
- [x] Qwen-VL full-source crop render/preflight 완료: added Docker services `qwen_vl_full_source_crop_render` and `qwen_vl_full_source_crop_preflight` plus script `render_qwen_vl_full_source_crops.py`. Rebuilt `h001-geom-reliability:latest` with log `logs/qwen_vl_full_source_crop_render_build_20260527_012748.log` exit 0. Shard smoke `qwen_full_source_shard_0000` rendered/preflighted with logs `logs/qwen_vl_full_source_crop_render_shard0000_20260527_012801.log` and `logs/qwen_vl_full_source_crop_preflight_shard0000_20260527_012813.log`, exit 0/0; result 250 input rows, 84 unique pair crops, 84 verified crops, 0 errors. All-scope crop rendering log `logs/qwen_vl_full_source_crop_render_all_20260527_012856.log` exit 0 and all-scope preflight log `logs/qwen_vl_full_source_crop_preflight_all_20260527_013235.log` exit 0; final result 33,384 input rows, 11,128 unique pair crops, 11,128 verified crops, 0 errors under `experiments/H001_geom_reliability/sources/qwen_vl/full_source_crops/all/`. Docker table builder regenerated report with log `logs/h001_table_builder_qwen_crops_20260527_013204.log` exit 0. No Qwen model load or inference was run.
- [x] Qwen-VL full-source input builder 완료: Docker service `qwen_vl_full_source_input` and script `build_qwen_vl_full_source_input.py` added. First run with training-repro view root produced 0 input rows and exposed wrong view-root routing (`logs/qwen_vl_full_source_input_20260527_005643.log`, `logs/qwen_vl_full_source_input_20260527_005756.log`, exit 1). Fixed views dir to `local_dataset/Open3DSG_staged/h001_runtime/output/datasets/OpenSG_3RScan/views` and added numpy pickle compatibility for `numpy._core.numeric` view pickles; rebuilt with `logs/qwen_vl_full_source_input_build_20260527_005922.log` exit 0 and reran `logs/qwen_vl_full_source_input_20260527_005933.log` exit 0. Outputs under `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/`: `universe.jsonl` 77,748 rows, `input.jsonl` 33,384 inferable rows, `missing.jsonl` 44,364 rows, `shards.jsonl` 134 shards, `manifest.json`, `coverage.json`, `report.md`. Contract validation log `logs/qwen_vl_full_source_input_validate_20260527_010011.log` exit 0: 33,384 input rows, 0 input errors, 0 output errors, 0 warnings. This remains no-model/no-inference third-source preparation, not paper metric evidence.
- [x] Qwen-VL third-source full-source promotion plan freeze 완료: Qwen role을 third semantic source / modern VLM extension으로 고정했고, Docker service `qwen_vl_full_source_plan`을 추가했다. Initial run failed because the existing `h001-geom-reliability:latest` image did not include the new script (`logs/qwen_vl_full_source_plan_20260527_003327.log`, exit 2); rebuilt image with `logs/qwen_vl_full_source_plan_build_20260527_003340.log` exit 0, reran with `logs/qwen_vl_full_source_plan_20260527_003349.log` exit 0. Outputs: `experiments/H001_geom_reliability/sources/qwen_vl/full_source_plan/{manifest.json,protocol.json,commands.md,report.md}`. Status `full_source_promotion_plan_frozen_no_metric_run`; scope 127 scans / 388 contexts / 25,916 directed pairs / max 77,748 all-pairs x family query rows / 2,545 in-scope GT rows. `results/h001_geom_reliability/report.md` regenerated via Docker table builder log `logs/h001_table_builder_qwen_third_source_20260527_003525.log` exit 0.
- [x] Qwen-VL runtime preflight and tiny inference smoke 완료: Docker `qwen_vl_runtime_preflight` log `logs/qwen_vl_runtime_preflight_20260527_002150.log` exit 0, status `runtime_preflight_passed`, model class `Qwen3VLForConditionalGeneration`, processor class `Qwen3VLProcessor`. Docker `qwen_vl_tiny_inference_smoke` initially hit Python 3.9 compatibility issue `zip(strict=True)`; patched `run_qwen_vl_runtime_smoke.py`, rebuilt `h001-qwen-vl-runtime:cu128` with log `logs/qwen_vl_runtime_image_rebuild_20260527_002307.log`, then reran tiny inference with log `logs/qwen_vl_tiny_inference_smoke_20260527_002330.log` exit 0. Status `tiny_inference_smoke_passed`, attempted rows 3, output rows 3, parser status counts `{'parsed': 3}`. Runtime raw-response contract validation log `logs/qwen_vl_tiny_inference_contract_validate_20260527_002427.log` exit 0. This remains non-metric modern-VLM semantic-source extension evidence, not a replacement for Open3DSG or VL-SAT.
- [x] H001 Docker subgraph bootstrap CI 완료: compose service `bootstrap_ci`와 `src/geocalib/bootstrap_metrics.py`를 추가하고 Docker 실행 `logs/h001_bootstrap_ci_20260526_182034.log` exit 0으로 `bootstrap_ci/{manifest.json,summary.json,summary.md}`를 생성했다. Status `ready`, sources `vlsat_closed_set` and `open3dsg_ov`, 1,000 subgraph resamples, warnings none. Main result: Open3DSG `family_conditional_risk` vs `semantic_only` R@100 delta `+10.22 pp` with 95% CI `[+7.94,+12.54]`, Violation@100 delta `-8.84 pp` with CI `[-9.41,-8.28]`; VL-SAT recall deltas are modest while violation reductions remain negative. `paper/aaai/sec/6_results.tex`, `paper/risk.md`, `experiments/H001_geom_reliability/README.md`, and `commands.md` were updated. Docker PDF rebuild `logs/h001_aaai_pdf_build_20260526_182458.log` exit 0; `paper/aaai/main.pdf` remains 9 pages and no missing citations, undefined refs, overfull hboxes, LaTeX errors, or AAAI package errors found.
- [x] H001 AAAI reviewer-risk P5/P4/P3/P6 main-text mitigation 완료: `paper/aaai/sec/3_problem.tex`에 `Violation@K` top-K grouping and status-denominator handling을 보강했고, `paper/aaai/sec/2_related_work.tex`에 RelWitness가 closest prior art지만 동일 row/denominator/violation protocol로 mapping되기 전에는 direct baseline이 아니라는 문장을 추가했다. `paper/aaai/sec/0_abstract.tex`, `sec/5_experiments.tex`, `sec/6_results.tex`, and `sec/8_conclusion.tex`에서 Open3DSG를 `main open-vocabulary relation-source case study` / source-output reliability evidence로 좁히고 downstream wording을 future-evaluation 수준으로 낮췄다. Docker rebuild `logs/h001_aaai_pdf_build_20260526_173136.log` exit 0; `paper/aaai/main.pdf` remains 9 pages and no missing citations, undefined refs, overfull hboxes, LaTeX errors, or AAAI package errors found.
- [x] H001 AAAI reviewer-risk P0-P2 main-text mitigation 완료: `paper/aaai/sec/6_results.tex`에서 anonymous submission에 위험한 `yhkim`/private-reference wording을 제거했고, controls 문단에 VL-SAT controlled-anchor source/2,545 denominator와 Open3DSG control numbers를 명시했다. `paper/aaai/sec/4_method.tex`에는 predicate-family map, hard-rule thresholds, counterfactual construction, and calibrator files가 train-dev calibration artifacts에서 held-out source-result reporting 전에 freeze된다는 문장을 추가했다. Docker rebuild `logs/h001_aaai_pdf_build_20260526_170736.log` exit 0; `paper/aaai/main.pdf` remains 9 pages and no missing citations, undefined refs, overfull hboxes, LaTeX errors, or AAAI package errors found.
- [x] H001 core result artifact bundle 생성 및 검증 완료: background `tmux` job `h001_core_bundle_20260526_160957` exited `0`; output `release/h001_core_results_20260526_160957.tar.zst` is 423 MB, checksum file `release/h001_core_results_20260526_160957.sha256` verifies OK, archive entry count is 89. Row-count verification: raw dump 19,162, Open3DSG predictions 496,600, verification 496,600, failure rows 57,736, qualitative queue 36, total 1,070,134; metric status is `ready`. `.gitignore` now ignores `release/` and `*.tar.zst`.
- [x] H001 reproducibility artifact bundle plan 완료: `docs/reproducibility.md`에 GitHub-tracked source, core H001 result bundle, optional large feature-cache bundle, and external-only dataset/model dependency tiers를 추가했다. Core bundle paths, current sizes/counts, row counts, tar/zstd creation template, checksum command, and post-download verification commands를 기록했다. Current checked row counts: raw dump 19,162, Open3DSG predictions 496,600, verification 496,600, failure rows 57,736, qualitative queue 36; selected Open3DSG checkpoint size 401 MB, train/dev features 131 GB, H001 eval features 13 GB, Qwen cache 8.3 GB.
- [x] Qwen-VL runtime preflight retry recorded as blocked: Docker `qwen_vl_runtime_preflight` was run twice with logs `logs/qwen_vl_runtime_preflight_20260526_160048.log` and `logs/qwen_vl_runtime_preflight_20260526_160125.log`; both wrote `blocked_runtime_preflight` because GPU guard observed utilization 63-65%. `nvidia-smi`/`docker top` traced active GPU use to unrelated `AST_mujoco` process `python scripts/rollout_plot_ee_trajectories_depth.py`, so no Qwen tiny inference was launched.
- [x] H001 AAAI reviewer-defense main-text pass 완료: `paper/aaai/sec/1_intro.tex`, `sec/4_method.tex`, `sec/5_experiments.tex`, `sec/6_results.tex`, and `sec/7_limitations.tex`에 hand-coded verifier, geometry-only/distance heuristic, recall-only tradeoff, averaged-BLIP Open3DSG caveat, family selection, and AAAI reader relevance 공격에 대한 직접 답변을 보강했다. Docker rebuild `logs/h001_aaai_pdf_build_20260526_143440.log` exit 0; `paper/aaai/main.pdf`는 9 pages, technical content pages 1-7, references page 8, checklist page 9이며 missing citations, undefined refs, overfull hboxes, LaTeX errors, or AAAI package errors 없음.
- [x] H001 AAAI reproducibility checklist 추가 완료: official AAAI-26 reproducibility checklist page를 확인하고 `paper/aaai/sec/9_reproducibility_checklist.tex`를 추가한 뒤 `paper/aaai/main.tex`에서 references 뒤에 연결했다. Docker rebuild `logs/h001_aaai_pdf_build_20260526_102601.log` exit 0; `paper/aaai/main.pdf`는 9 pages, technical content pages 1-7, references page 8, checklist page 9이며 missing citations, undefined refs, overfull hboxes, LaTeX errors, or AAAI package errors 없음.
- [x] H001 AAAI-style source conversion 완료: `paper/aaai/`에 AAAI-style `main.tex`, `preamble.tex`, `sec/*.tex`, `aaai2026.sty`, `aaai2026.bst`, `Dockerfile.tex`, `.gitignore`, `README.md`, and `inspection/report.md`를 생성했다. Official AAAI-26 submission page를 확인했고 최신 공개 AAAI-26 style route를 사용했다. Docker image `h001-aaai-tex:20260526` build 성공, `paper/aaai/main.pdf` build 성공. Initial PDF log `logs/h001_aaai_pdf_build_20260526_015812.log`: 8 total pages, technical content pages 1-7, references start page 8, no missing citations, undefined refs, overfull hboxes, or AAAI package errors. This was later superseded by the checklist-included rebuild above.
- [x] H001 Open3DSG-first ICCV float/table ordering polish 완료: `archive/paper/iccv/sec/0_abstract.tex`, `sec/1_intro.tex`, `sec/5_experiments.tex`, `sec/6_results.tex`, `sec/7_limitations.tex`, and `sec/8_conclusion.tex`를 Open3DSG-main framing으로 갱신했다. Manuscript에서는 Open3DSG를 main open-vocabulary relation-source case study로 두고 VL-SAT를 controlled reproduced anchor로 둔다. Standalone Open3DSG/VL-SAT/audit tables를 `Table 3 Main source results`와 prose evidence로 압축해 9-page build를 유지했다. Docker rebuild `logs/h001_iccv_pdf_build_20260526_013847.log` exit 0; no missing citations, undefined refs, or overfull hboxes.
- [x] H001 PDF visual/layout inspection 완료: `archive/paper/iccv/inspection/report.md`에 page-level inspection을 기록했다. Latest `archive/paper/iccv/main.pdf`는 9 pages이며 no missing citations, no undefined refs, no overfull hbox warnings 상태다. Body/Conclusion은 page 8 안에서 끝나고 References는 page 8에서 시작해 page 9로 이어진다. 이후 Open3DSG-first float/table ordering polish로 standalone Open3DSG/VL-SAT/audit tables를 `Table 3 Main source results`와 prose evidence로 압축했다.
- [x] H001 ICCV-style compression/layout pass 완료: Related Work / Results / Table 6 wording을 압축하고 `sec/3_problem.tex` family equation과 Open3DSG table을 줄여 overfull hbox 2개를 제거했다. Docker `latexmk` rebuild 성공, `archive/paper/iccv/main.pdf`는 9 pages이며 본문/Conclusion은 page 8 안에서 끝나고 References는 page 8 right column에서 시작해 page 9로 이어진다. Latest build log: `logs/h001_iccv_pdf_build_20260526_001215.log`.
- [x] H001 `archive/paper/iccv/` Docker PDF build 검증 완료: `archive/paper/iccv/Dockerfile.tex`로 `h001-iccv-tex:20260525` image를 만들고 Docker `latexmk` build를 실행했다. Initial `archive/paper/iccv/main.pdf` 생성 성공, 9 pages, letter size, BibTeX 19 entries used, missing citations/undefined refs 없음. Initial build warnings were overfull hbox 2개(`sec/3_problem.tex` line 23, `sec/6_results.tex` lines 157-167), later resolved by the compression/layout pass. Build logs: `logs/h001_iccv_tex_image_build_20260525_235416.log`, `logs/h001_iccv_pdf_build_20260525_235643.log`.
- [x] H001 Figure 1-3 ICCV build asset 변환 완료: Chrome headless screenshot으로 `figure1_framework.png` 1280x650, `figure2_tradeoff.png` 1280x620, `figure3_geometry_panels.png` 1280x910을 생성했고 `archive/paper/iccv/sec/6_results.tex`의 `\figmaybe{...}` paths를 PNG로 전환했다. PDF build는 아직 실행하지 않았다.
- [x] H001 `archive/paper/iccv/` manuscript-content pass 완료: PDF build 전에 필요한 main-section prose, fixed scope/denominator table, source-specific claim-boundary table, figure/table callouts, audit/sanity table, Open3DSG caveat-heavy Table caption, and limitation wording을 scoped H001 claim에 맞게 보강했다. Build는 아직 실행하지 않았다.
- [x] H001 ICCV-style manuscript source conversion 완료: official ICCV/CVF author-kit route를 선택하고 `archive/paper/iccv/`에 `iccv.sty`, `ieeenat_fullname.bst`, `main.tex`, `preamble.tex`, `sec/*.tex`, and figure placeholder route를 생성했다. Citation keys used by the LaTeX source match `paper/references.bib`; `git diff --check` passes. Build는 현재 host에 TeX engine / figure converter가 없어 아직 검증하지 못했다.
- [x] H001 paper content-first pass 진행: `paper/draft.md`에 scoped title, quantitative abstract, and Section 1 Introduction을 추가했다. 이후 body gap patch까지 반영되어 draft는 Title/Abstract/Introduction/Related Work/Problem/Method/Experimental Setup/Results/Limitations/Conclusion까지 이어지는 ICCV-style paper body를 가진다. Template/build 검증은 내용 안정화 이후로 미룬다.
- [x] H001 front matter ICCV-style quick review 완료: `paper/draft.md`의 Title/Abstract/Introduction을 claim sharpness와 page economy 기준으로 확인했다. 현재 front matter는 title 제외 약 701 words, abstract 201 words, Introduction 500 words로 final compression 전 content draft로 수용 가능하다.
- [x] H001 full paper-body gap review patch 완료: `paper/draft.md`에 Figure 1-3 본문 callout, Table 4 audit/sanity prose, and Conclusion section을 추가했다. 이제 draft는 Title부터 Conclusion까지 이어지며 template 변환 전 큰 paper-body hole은 제거했다.
- [x] H001 paper-body word budget and table placement review 완료: `paper/draft.md`의 Title-through-Conclusion prose는 약 3,507 words이고, front matter는 약 707 words이다. Main-paper recommendation은 Figure 1-3, Table 1, compact Table 2, compact Table 3 if space allows, and Table 6; Table 4 and full Table 5는 appendix/prose fallback으로 고정했다.
- [x] H001 experiment progress rationale 작성 완료: `paper/progress.md`를 생성해 hypothesis smoke부터 hardened VL-SAT, controls, GT verifier, audit, Docker experiment transition, Open3DSG second-source, failure analysis, optional Qwen/FROSS branches까지 각 실험의 실행 이유, 다음 단계로 넘어간 이유, 결과 해석, claim boundary를 정리했다.
- [x] H001 draft bibliography scaffold 및 Section 5 title standardization 완료: `paper/references.bib`를 생성해 `paper/draft.md`의 19개 BibTeX-style citation key를 모두 채웠고, top-tier CV paper section 관행을 확인해 Section 5 제목을 표준 `Experimental Setup`으로 바꿨다. Scope/denominator/filtered-split/Docker-result caveat는 제목이 아니라 Section 5 본문과 tables에서 유지한다.
- [x] H001 Qwen-VL runtime preflight resource check 완료: 2026-05-23 현재 GPU는 약 10,034 MiB 사용 중이며 `qwen_vl_runtime_preflight` guard 기준 `max-gpu-memory-used-mb=8192`를 초과한다. Docker preflight/inference는 실행하지 않았고, GPU/RAM pressure가 해소된 뒤 `qwen_vl_runtime_preflight`부터 진행한다.
- [x] H001 paper draft section-structure decision 완료: `paper/draft.md` Section 5는 Results에 병합하지 않고 짧은 standalone experiment setup section으로 유지한다. 이유는 denominator, filtered split, covered scope, Open3DSG averaged-BLIP variant, Docker-result boundary, and non-claim caveats가 Results 안에 묻히면 reviewer-defense가 약해지기 때문이다. 이후 제목은 표준 `Experimental Setup`으로 정리했다.
- [x] H001 recent 2025-2026 final Related Work role decision 완료: RelWitness는 required direct novelty-threat citation, VIZOR는 required spatial-relation/viewpoint-boundary citation, ZING-3D는 VLM/incremental 3DSG trend citation, Open-World 3DSG-RAG는 broad open-world/RAG boundary citation, View-on-Graph는 downstream grounding-motivation citation으로 유지한다. 이들은 final Related Work에 남기되 H001의 direct baseline/metric evidence로 쓰지 않는다.
- [x] H001 RelWitness full-PDF novelty-difference matrix 완료: arXiv v2 PDF를 full-PDF skim으로 확인했고, RelWitness가 relation witnesses, calibrated witness quality `Q`, witness-guided positive-unlabeled learning, and witness-consistent decoding을 포함한다는 점을 기록했다. H001 distinction은 reproduced calibrated geometry-consistency evaluation/re-ranking over existing relation-source outputs, identity-preserving joins, `Violation@K`, controls, and denominator discipline으로 고정했다. Updated `literature/2026_arxiv_relwitness/`, `literature/PAPER.md`, `literature/README.md`, `paper/draft.md`, `docs/paper.md`, `docs/index.md`, `README.md`, and `summary.md`.
- [x] H001 literature novelty-threat expansion pass 완료: primary sources checked for RelWitness, ZING-3D, Open-World 3DSG-RAG, View-on-Graph, and VIZOR; `literature/2026_arxiv_relwitness/` paper folder added; `literature/PAPER.md`, `literature/README.md`, `paper/draft.md`, `docs/paper.md`, and `summary.md` updated to distinguish relation-witness prior art from H001's calibrated geometry-consistency evaluation/re-ranking claim.
- [x] H001 Related Work citation placeholder 교체 완료: `paper/draft.md`의 `[3DSSG]`, `[VL-SAT]`, `[Open3DSG]` 등 약어 placeholder를 BibTeX-style `\cite{...}` keys로 교체하고, draft 상단에 shorthand-to-key map을 기록했다. Later bibliography work was advanced into `paper/references.bib`; remaining work is final ICCV-style build verification after content stability.
- [x] H001 Figure 3 geometry-backed panel upgrade 완료: Docker `h001-open3dsg-repro:cu128`에서 `paper/scripts/render_figure3_geometry_panels.py`를 실행해 locked Open3DSG cases `open3dsg_case_001`, `005`, `010`, `007`에 대한 preprocessed object point-cloud geometry SVG, case measurement JSON, manifest, and report를 생성했다. Outputs: `paper/generated/figures/figure3_geometry_panels.svg`, `figure3_geometry_cases.json`, `figure3_geometry_manifest.json`, `figure3_geometry_report.md`; SVG XML parse passed.
- [x] H001 generated Figure 1-3 top-tier novelty/layout review 완료: Figure 1 was revised to foreground failure mechanism -> cause -> design necessity; Figure 2 kept as strongest recall/violation evidence; Figure 3 row-card draft was accepted as a traceable placeholder, then superseded by the geometry-backed panel upgrade above. Review record: `paper/generated/figures/layout_review.md`.
- [x] H001 draft Figure 1-3 생성 및 검증 완료: `paper/scripts/generate_draft_figures.py` generated `paper/generated/figures/figure1_framework.svg`, `figure2_tradeoff.svg`, `figure3_failure_cases.svg`, `figure2_data.json`, `figure3_cases.json`, `manifest.json`, `validation.json`, and `report.md`; validation status `passed`, SVG XML parse passed, Figure 2 locked values and Figure 3 case IDs match `paper/figures.md`.
- [x] H001 Figure 1-3 source lock 완료: `paper/figures.md`를 생성해 Figure 1 method pipeline, Figure 2 two-panel R@100/Violation@100 tradeoff with VL-SAT and caveated Open3DSG, and Figure 3 Open3DSG qualitative case panels를 source artifacts, exact values, case IDs, and caption constraints와 함께 고정했다.
- [x] H001 first-pass draft claim/evidence review 완료: `paper/draft.md` status를 `first_pass_reviewed_source_lock_next`로 갱신하고 claim-scope pass, citation placeholder follow-up, table/evidence links, Open3DSG caveat pass, and Figure 1-3 source-lock follow-up을 기록했다. Results prose now points to Table 1/2/3/5/6 and source artifacts; citation-key follow-up was later resolved.
- [x] H001 first-pass manuscript prose draft 완료: `paper/draft.md`에 Related Work, Problem Formulation, Method, Experimental Setup, Results/Discussion, Limitations의 1차 prose를 작성했다. Citation placeholder, Figure 1-3 generation, Table 6 caveat compression은 draft review 이후 처리한다.
- [x] H001 Open3DSG feature `.pt` regeneration route 문서화 완료: `docs/reproducibility.md`에 train/dev official BLIP TopK5/scales3 feature cache와 H001 eval feature cache 재생성 전제조건, tmux/resume/shard 명령, audit 명령, expected ids, output paths, and high-cost warning을 추가했다. 결론: 재생성 가능하지만 train/dev 131GB + multi-day급, H001 eval 13GB + shard-loop급 비용이 크다.
- [x] H001 reproducibility runbook 및 `.gitignore` portability audit 업데이트 완료: `docs/reproducibility.md`에 2026-05-21 상태, paper planning handoff, runtime pressure check rule, GitHub에 올릴 수 있는 재현 파일, 의도적으로 ignored 되는 대형 데이터/checkpoint/raw JSONL/model cache, and other-computer transfer/rebuild requirement를 정리했다. `.gitignore` 자체는 수정하지 않았다.
- [x] H001 paper-body content blocks 확보 완료: `paper/outline.md`에 related-work positioning map, formal problem/method notation, re-ranking algorithm skeleton, Results/controls/Open3DSG prose skeleton, failure-analysis prose skeleton, limitation prose skeleton, Figure 1-3 asset plan, and table/main-vs-appendix placement을 추가했다.
- [x] H001 paper-writing priority reset 완료: camera-ready caption compression은 현재 단계에서 너무 이르므로, 다음 우선순위를 paper-body content completeness로 변경했다. `paper/outline.md`에 paper content coverage checklist를 추가하고 secured content와 missing blocks를 구분했다.
- [x] H001 paper claim-consistency review 완료: `paper/outline.md`에서 title, contribution, abstract, Introduction, Figure 1-3 captions, Table 1-6 captions를 scoped relation-reliability claim 기준으로 점검했고, broad open-vocabulary/SOTA, baseline-agnostic, verifier-script, Qwen-main-evidence, exact non-averaged Open3DSG reproduction overclaim을 금지 표현으로 고정했다. 다음 priority는 문장 polish가 아니라 paper-body content completeness다.
- [x] H001 table/figure manuscript-ready caption draft 완료: `paper/outline.md`에 Figure 1-3 caption drafts, Table 1-6 caption drafts, reviewer-defense role, Korean caption notes를 추가했다.
- [x] H001 Introduction section logic 확장 완료: `paper/outline.md`에 영어/한국어 6문단 Introduction flow, draft paragraph skeleton, 금지 표현, 필수 inclusion checklist를 추가했다.
- [x] H001 abstract skeleton 작성 완료: `paper/outline.md`에 full/short English abstract skeleton, 한국어 초록 skeleton, optional quantitative abstract numbers, and abstract wording constraints를 추가했다.
- [x] H001 contribution statements 3개 구성으로 정리 완료: `paper/outline.md`에서 cross-source evidence/failure analysis를 4번째 contribution이 아니라 Results/Failure Analysis의 empirical validation으로 이동하고, contribution은 failure mechanism / method framework / evaluation protocol 3개로 고정했다.
- [x] H001 title candidates and contribution statements 작성 완료: `paper/outline.md`에 recommended primary title, 8개 대안 title, 피해야 할 title pattern, 3개 contribution statements, Introduction용 compact contribution version, and 한국어 병기 contribution wording을 추가했다.
- [x] H001 paper outline 한국어 병기 완료: `paper/outline.md`에 기존 영어 outline을 유지하면서 한국어 작성 지침, section별 역할, reviewer-defense, Open3DSG caveat, figure/table plan을 추가했다.
- [x] H001 paper outline 생성 완료: `paper/outline.md`에 paper skeleton, section별 evidence placement, Open3DSG caveat placement, reviewer-defense map, figure/table plan, and next drafting tasks를 정리했다.
- [x] H001 paper preview handoff 생성 완료: `paper/preview.md`에 현재까지의 `VL-SAT` / Open3DSG metric evidence, controls, GT verifier, audit, failure analysis, Open3DSG caveats, reviewer-defense map, optional extension boundary, and 새 컴퓨터/데이터셋 손실 시 반드시 읽을 파일 목록을 정리했다.
- [x] H001 Open3DSG paper caveat wording 완료: Docker `open3dsg_paper_caveats` generated `sources/open3dsg/paper_caveats/{manifest.json,report.md}` with status `open3dsg_paper_caveats_ready`; fixed wording covers filtered-train `3744/3852`, train-dev validation `156/160`, H001 covered loadable scope `377/388`, `validation_missing_preprocessed:11`, averaged-BLIP variant, exact-label 2,545-row H001-family denominator, and residual calibration risk.
- [x] H001 Open3DSG qualitative failure-case inspection 완료: Docker `open3dsg_failure_case_inspection` generated `sources/open3dsg/failure_cases/{inspection.json,inspection.md}` with status `qualitative_case_inspection_ready`; 36 cases inspected, 23/36 demoted by geometry-aware reranking, 13/36 promoted or retained, 10/36 rule-violated cases with `p_geom_valid > 0.9`, no taxonomy change, and explicit non-visual-audit claim boundary.
- [x] H001 Open3DSG clean v14 streaming raw-dump provenance promoted to canonical wording/table notes: same-path resume exited `0`, stream manifest status `raw_dump_stream_complete`, completed batches `377/377`, rows `19162`, dropped/invalid partial rows `0/0`, and SHA256 matched canonical `raw_dump/raw.jsonl`.
- [x] H001 최신 md/runbook 업데이트 완료: `docs/reproducibility.md`를 추가해 데이터 위치/다운로드, checkpoint 위치/다운로드 방법, 환경 설치, Docker 실행, 실험 재현 명령, 검증 명령, artifact/evaluation 요약을 한 곳에 정리했고, `README.md`, `docs/index.md`, `docs/paper.md`, `summary.md`, hypothesis README, experiment README, Open3DSG README를 Open3DSG/Qwen runtime 상태로 갱신했다.
- [x] H001 Open3DSG v14 streaming raw dump retry checked: tmux `h001_open3dsg_eval_stream_raw_dump_retry_20260519_092628` ended with exit `137` after `294/377` test items; stream output `raw_stream_retry_20260519_092628.jsonl` has `15010` rows and completed-batch file has `294` records, so same-path resume is now useful. No CUDA OOM string was logged; current evidence points to SIGKILL under host/container memory pressure rather than confirmed GPU OOM.
- [x] H001 Open3DSG v14 streaming raw dump same-path resume launched: tmux `h001_open3dsg_eval_stream_raw_dump_resume_20260519_103227`, log `logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_resume_20260519_103227.log`, exit file `logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_resume_20260519_103227.exit`; it resumes `raw_stream_retry_20260519_092628.jsonl` / `.completed.jsonl` from `294` completed batches. Pre-launch GPU memory was about `330 MB` and swap was `0 B`; eval preflight/source patch passed.
- [x] H001 Open3DSG v14 streaming raw dump same-path resume completed: exit `0`, manifest status `raw_dump_stream_complete`, completed batches `377/377`, rows `19162`, dropped/invalid partial rows `0/0`, and SHA256 matches existing `raw_dump/raw.jsonl` exactly (`7072c77939a84f8739671025534cf09d5b834c507efad22fec3e3172e46ed2c2`).
- [x] H001 Open3DSG v14 streaming raw dump checked: tmux ended, exit file `logs/open3dsg_eval_h001_gt_objects_stream_raw_dump_20260518_204538.exit` contains `137`, log reached `LOCAL_RANK: 0` after checkpoint loading but did not enter `Testing DataLoader`, and no `raw_stream_20260518_204538.jsonl` / `.completed.jsonl` / manifest was written.
- [x] H001 Open3DSG per-batch streaming raw dump patch and rerun launched: source patch schema `h001_open3dsg_source_patch_v14` adds `OPEN3DSG_RAW_DUMP_STREAM_BATCHES=1`, resumable `.completed.jsonl`, partial-row repair, and no `test_step_outputs` accumulation in streaming mode. tmux `h001_open3dsg_eval_stream_raw_dump` launched with output `raw_dump/raw_stream_20260518_204538.jsonl`.
- [x] H001 Open3DSG v13 clean raw-dump-only rerun checked: tmux ended, exit file `logs/open3dsg_eval_h001_gt_objects_clean_raw_dump_20260518_194818.exit` contains `137`, the log reached only `Testing DataLoader 0` about `228/377`, and no `raw_clean_exit_20260518_194818.jsonl` was written. The v13 guard did not fire because raw export still occurs at epoch end.
- [x] H001 Open3DSG clean raw-dump-only source eval rerun launched: source patch schema `h001_open3dsg_source_patch_v13` adds `OPEN3DSG_RAW_DUMP_EXIT_AFTER_WRITE=1`; tmux `h001_open3dsg_eval_clean_raw_dump` writes separate raw output `raw_dump/raw_clean_exit_20260518_194818.jsonl` and should exit immediately after raw dump writing.
- [x] H001 Open3DSG qualitative failure-case sampler 완료: Docker `open3dsg_failure_case_sampler` generated `sources/open3dsg/failure_cases/{queue.jsonl,manifest.json,report.md}` with status `failure_case_sample_ready`, 36 selected high-severity visual-audit candidates from 6,162 candidate rows, balanced across geometry_contradiction / semantic_and_geometry_failure and support_contact / proximity / relative_vertical.
- [x] H001 Open3DSG H001 eval feature shard loop completed: tmux ended, exit file `logs/open3dsg_dump_features_h001_eval_shard_loop_20260518_103948.exit` contains `0`, covered loadable feature ids reached `377/377`, total `.pt` files `1131`, and final event reported `h001_eval_feature_shard_loop_complete complete_ids=377 target_loadable_ids=377`.
- [x] H001 Open3DSG Docker `feature_audit_h001_eval` rerun after shard loop: missing complete feature ids `0`; audit status remains `blocked` only because of the known `validation_missing_preprocessed:11` caveat.
- [x] H001 Open3DSG feature-ready raw dump run failed after full eval loop: test loop reached `388/388`, then failed with Docker shared-memory / DataLoader worker errors before `raw_dump/raw.jsonl` was written; exit file `logs/open3dsg_eval_h001_gt_objects_avg_blip_feature_ready_20260518_170149.exit` contains `1`.
- [x] H001 Open3DSG raw dump SHM guard added and retry launched: compose now sets `shm_size: 16gb`, `eval_h001_gt_objects` defaults to `OPEN3DSG_EVAL_WORKERS=0`, and tmux `h001_open3dsg_eval_avg_blip_retry_shm` is running with log `logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_shm_20260518_170639.log`.
- [x] H001 Open3DSG raw dump SHM retry failed on avg-BLIP dtype mismatch: exit file `logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_shm_20260518_170639.exit` contains `1`; failure was `RuntimeError: mat1 and mat2 must have the same dtype, but got Float and BFloat16`; no `raw_dump/raw.jsonl`.
- [x] H001 Open3DSG source patch v11 and dtype retry launched: `patch_open3dsg_source.py` schema `h001_open3dsg_source_patch_v11` aligns relationship image embeddings to BLIP model dtype before `BLIP.generate_caption`; tmux `h001_open3dsg_eval_avg_blip_retry_dtype` launched with `OPEN3DSG_EVAL_WORKERS=0` and `OPEN3DSG_SHM_SIZE=16gb`.
- [x] H001 Open3DSG raw dump dtype retry failed on legacy BLIP generation length: exit file `logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_dtype_20260518_171351.exit` contains `1`; failure was current Transformers rejecting Open3DSG's legacy `max_length=20` generation call; no `raw_dump/raw.jsonl`.
- [x] H001 Open3DSG source patch v12 and generation retry launched: `patch_open3dsg_source.py` schema `h001_open3dsg_source_patch_v12` switches BLIP relationship generation to `max_new_tokens`, Docker compose exposes `OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS`, and tmux `h001_open3dsg_eval_avg_blip_retry_generate` is running.
- [x] H001 Open3DSG v12 raw dump retry wrote identity-audited raw dump: `raw_dump/raw.jsonl` has `19162` rows; source eval exit file contains `137` after raw dump writing; Docker `open3dsg_raw_dump_identity` reports `raw_dump_identity_audit_ready` with no blockers.
- [x] H001 Open3DSG adapter export 완료: Docker `open3dsg_adapter_raw_dump` generated `adapter/predictions.jsonl` with status `ready`, `496600` prediction rows from `19162` raw rows, and `62` raw rows filtered outside the fixed H001 object context; adapter version is `v1`.
- [x] H001 Open3DSG geometry join 완료: Docker `open3dsg_geometry_join` generated `geometry/verification.jsonl` with status `ready`, row preservation `496600/496600`, geometry/calibration scored rows `114600`, and G2 variants `obb_only`, `point_subtype`, `point_subtype_no_soft_support`.
- [x] H001 Open3DSG metric eval 완료: Docker `open3dsg_metric_eval` generated `metrics/metrics.json` status `ready` with no blockers. Key metrics: semantic_only R@50/R@100 `0.3945/0.4963`, Violation@50/@100 `0.1326/0.1195`; probabilistic_recalibrated R@50/R@100 `0.3843/0.5580`, Violation@50/@100 `0.0575/0.0803`; rule_verified_point_subtype R@50/R@100 `0.4149/0.5238`, Violation@50/@100 `0.0/0.0`; family_conditional_risk R@50/R@100 `0.4530/0.5984`, Violation@50/@100 `0.0228/0.0311`.
- [x] H001 Open3DSG Table 6 재생성 완료: Docker `table_builder` now reads `sources/open3dsg/metrics/metrics.json`; `sources/open3dsg/table6_hook.json` and `tables/table6_cross_source_status.*` report Open3DSG status `ready` with no blockers.
- [x] H001 Open3DSG real failure-analysis rows 완료: Docker `open3dsg_failure_generator_real` generated `sources/open3dsg/failure_rows/{rows.jsonl,summary.json,manifest.json,report.md}` with status `failure_analysis_real_ready`, 57,736 rows from semantic top-100 or geometry-reranked top-100 union per subgraph, validation errors 0, and visual-audit queue rows 6,162.
- [x] H001 Open3DSG H001 eval feature dump lower-memory chunk1 resume completed partially: tmux ended, exit file `logs/open3dsg_dump_features_h001_eval_resume_chunk1_20260518_091944.exit` contains `137`; settings `OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1`, `OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1`, `OPEN3DSG_FEATURE_SKIP_EXISTING=1`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64`; complete feature ids advanced from 194/377 to 195/377, newly writing `10b1794e-3938-2467-89a7-ebc89e84cf88-2`; next first missing loadable id is `10b17940-3938-2467-8a7a-958300ba83d3-1`.
- [x] H001 Open3DSG remaining-id shard patch and command added: source patch schema `h001_open3dsg_source_patch_v10` adds feature-cache shard filtering, lazy eval dataset loading, bounded `OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS`, and feature-dump relation-mapper skip; Docker compose exposes the shard env vars and command docs include the tmux shard command.
- [x] H001 Open3DSG H001 eval feature dump shard launched: tmux `h001_open3dsg_dump_features_h001_eval_shard`, log `logs/open3dsg_dump_features_h001_eval_shard_20260518_100159.log`, exit file `logs/open3dsg_dump_features_h001_eval_shard_20260518_100159.exit`; shard filter selected 5 missing loadable ids from original 388 contexts, with 195 complete, 182 missing, and 11 skipped missing-preprocessed contexts.
- [x] H001 Open3DSG H001 eval feature dump shard completed: exit code `0`, DataLoader `5/5`, complete feature ids advanced from 195/377 to 200/377, total `.pt` files 600; next first missing loadable id `4fbad31e-465b-2a5d-84b7-c0ddea978db4-1`.
- [x] H001 Open3DSG H001 eval feature shard loop launched: tmux `h001_open3dsg_dump_features_h001_eval_shard_loop`, log `logs/open3dsg_dump_features_h001_eval_shard_loop_20260518_103948.log`, exit file `logs/open3dsg_dump_features_h001_eval_shard_loop_20260518_103948.exit`; iteration 1 started from 200/377 and selected 5 missing loadable ids.
- [x] H001 Open3DSG H001 eval feature dump v9 resume launched: payload retry exited 137 after 194/377 complete feature ids; source patch schema `h001_open3dsg_source_patch_v9` adds test-step pre-forward skip-existing, tmux `h001_open3dsg_dump_features_h001_eval`, log `logs/open3dsg_dump_features_h001_eval_resume_v9_skip_20260518_084946.log`, exit file `logs/open3dsg_dump_features_h001_eval_resume_v9_skip_20260518_084946.exit`.
- [x] H001 Open3DSG H001 eval feature dump payload retry ended partially: exit code 137 at 2026-05-18 07:16 KST, complete feature ids 194/377, total `.pt` files 582; audit/raw dump remain blocked until the resume completes.
- [x] H001 Open3DSG H001 eval payload staging completed: Docker `h001_eval_payload` created/verified 127/127 held-out scan symlinks under `h001_runtime/data/3RScan`, sequence-ready scans 127/127, blockers none; artifacts `sources/open3dsg/h001_eval_payload/{manifest.json,records.jsonl,report.md}`.
- [x] H001 Open3DSG H001 eval feature dump payload retry launched: previous `dump_features_h001_eval` attempt failed before feature writing because H001 runtime sequence symlinks were missing; launched tmux `h001_open3dsg_dump_features_h001_eval`, log `logs/open3dsg_dump_features_h001_eval_retry_payload_20260518_014442.log`, exit file `logs/open3dsg_dump_features_h001_eval_retry_payload_20260518_014442.exit`, target `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3`.
- [x] H001 Open3DSG raw dump NumPy retry failed on missing H001 eval features: retry `h001_open3dsg_eval_avg_blip_retry_numpy` exited 1 after recovering the validation preload, because `OPEN3DSG_FEATURE_LOAD_DIR` pointed to the official `training_repro` feature dump and did not contain H001 held-out eval ids such as `ab835faa-54c6-29a1-9b55-1a5217fcba19-1.pt`.
- [x] H001 Open3DSG H001 eval feature dump route added and launched: compose services `dump_features_h001_eval` and `feature_audit_h001_eval` added; source patch schema `h001_open3dsg_source_patch_v8` prevents test-mode feature dumping from falling through into metric evaluation; tmux `h001_open3dsg_dump_features_h001_eval`, log `logs/open3dsg_dump_features_h001_eval_20260518_013909.log`, exit file `logs/open3dsg_dump_features_h001_eval_20260518_013909.exit`, target `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3`.
- [x] H001 Open3DSG raw dump false-positive diagnosed and compatibility fixed: first raw dump run `h001_open3dsg_eval_avg_blip` exited 0 but produced no `raw.jsonl` because `numpy._core` unpickle errors collapsed the test DataLoader to length 0. Source patch schema `h001_open3dsg_source_patch_v7` now installs a NumPy pickle compatibility alias in `open_dataset.py`; Docker sanity recovered 377/388 H001 eval contexts, with 11 remaining as the known missing-preprocess caveat.
- [x] H001 Open3DSG raw dump retry launched after NumPy compatibility fix: tmux `h001_open3dsg_eval_avg_blip_retry_numpy`, log `logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_numpy_20260518_013208.log`, exit file `logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_numpy_20260518_013208.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/raw_dump/eval_avg_blip_retry_numpy_20260518_013208.md`; immediate check showed tmux active and no exit file yet.
- [x] H001 Open3DSG checkpoint selection/eval preflight refreshed after full avg-BLIP training: Docker `open3dsg_checkpoint_selection` rebuilt to schema `h001_open3dsg_checkpoint_selection_v3`, selected `epoch=13-step=13104.ckpt` as an explicitly labeled averaged-BLIP Open3DSG variant using only train-dev val/loss 0.32881081104278564 at step 13103; blockers none, claim limitations record that this is not the exact non-averaged BLIP route. Docker `eval_preflight` passed with the selected checkpoint and raw-dump contract `contract_ready_raw_dump_missing`.
- [x] H001 Open3DSG raw-dump exporter added and launch recorded: source patch schema `h001_open3dsg_source_patch_v6` exports H001 identity-preserving raw prediction JSONL during Open3DSG test; `eval_h001_gt_objects` command now sets `OPEN3DSG_RAW_DUMP_JSONL`, `OPEN3DSG_BASELINE_RUN_ID`, `OPEN3DSG_MODEL_SOURCE_STAGE`, `--avg_blip_emb`, and `--load_features`.
- [x] H001 Open3DSG raw dump inference launched: tmux `h001_open3dsg_eval_avg_blip`, log `logs/open3dsg_eval_h001_gt_objects_avg_blip_20260518_012214.log`, exit file `logs/open3dsg_eval_h001_gt_objects_avg_blip_20260518_012214.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/raw_dump/eval_avg_blip_20260518_012214.md`; immediate check showed tmux active and no exit file yet.
- [x] H001 Open3DSG full avg-BLIP training completed: tmux `h001_open3dsg_train_full_avg_blip` ended, exit file `logs/open3dsg_train_full_avg_blip_20260515_172644.exit` contains `0`, log reports `Trainer.fit stopped: max_epochs=100 reached` and `finished_at=2026-05-18T00:47:56+09:00`; `last.ckpt` updated at 2026-05-18 00:47 KST, with top-k checkpoint files for epochs 9, 13, 14, 15, and 19.
- [x] H001 Open3DSG avg-BLIP pilot completed and checkpoint provenance refreshed: pilot exit code 0, global step 936, val/loss 0.37145, checkpoints `epoch=0-step=936.ckpt` and `last.ckpt`; Docker `open3dsg_checkpoint_selection` rebuilt/reran with schema `h001_open3dsg_checkpoint_selection_v2`, candidate_count 2, both `avg_blip_pilot`, paper-result eligible candidates 0.
- [x] H001 Open3DSG full avg-BLIP training launched: tmux `h001_open3dsg_train_full_avg_blip`, Docker container `open3dsg-train_full_avg_blip-run-b642ae11a484`, log `logs/open3dsg_train_full_avg_blip_20260515_172644.log`, exit file `logs/open3dsg_train_full_avg_blip_20260515_172644.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/train_pilot/full_avg_blip_20260515_172644.md`; preflight passed and training loop entered at epoch 0.
- [x] H001 Open3DSG training preflight GPU free-memory gate 추가: `open3dsg_training_preflight.py` schema `h001_open3dsg_training_preflight_v6` records GPU free/total memory and blocks `train_pilot`/`train_full` when `OPEN3DSG_MIN_GPU_FREE_MB` is not met; Docker preflight passed at 2026-05-15 13:49 KST with 30019/32100 MB free and threshold 18000 MB.
- [x] H001 Open3DSG checkpoint pilot retry2 launched: tmux `h001_open3dsg_train_pilot_retry2`, Docker container `open3dsg-train_pilot-run-755150572fe2`, log `logs/open3dsg_train_pilot_retry2_20260515_135125.log`, exit file `logs/open3dsg_train_pilot_retry2_20260515_135125.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/train_pilot/retry2_20260515_135125.md`; preflight passed and training loop entered with `OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1`.
- [x] H001 Open3DSG checkpoint pilot retry2 failed: exit code 1, CUDA OOM at epoch 0 step 699/3744 in chunked BLIP projector path even with `OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1`; no `.ckpt` found, so checkpoint provenance/selection was not refreshed.
- [x] H001 Open3DSG lower-memory avg-BLIP route selected and launched: Docker services `train_pilot_avg_blip` and `train_full_avg_blip` added; route record `experiments/H001_geom_reliability/sources/open3dsg/train_pilot/avg_blip_route_20260515_161344.md`; pilot tmux `h001_open3dsg_train_pilot_avg_blip`, Docker container `open3dsg-train_pilot_avg_blip-run-ad64be0a3ee8`, log `logs/open3dsg_train_pilot_avg_blip_20260515_161344.log`, exit file `logs/open3dsg_train_pilot_avg_blip_20260515_161344.exit`; training loop entered with `avg_blip_emb=True`, 34.9M trainable params, and about 7.1GB GPU usage.
- [x] H001 Open3DSG first checkpoint pilot retry failed: source patch schema `h001_open3dsg_source_patch_v5` chunks BLIP projector forward; tmux `h001_open3dsg_train_pilot_retry`, Docker container `open3dsg-train_pilot-run-545850558ca8`, log `logs/open3dsg_train_pilot_retry_20260515_134359.log`, exit file `logs/open3dsg_train_pilot_retry_20260515_134359.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/train_pilot/retry_20260515_134359.md`; exit code 1, CUDA OOM at epoch 0 step 235/3744 in the chunked BLIP projector path, no `.ckpt` found.
- [x] H001 Open3DSG first checkpoint pilot failed: tmux `h001_open3dsg_train_pilot`, Docker container `open3dsg-train_pilot-run-d03f45d49049`, log `logs/open3dsg_train_pilot_20260515_131857.log`, exit file `logs/open3dsg_train_pilot_20260515_131857.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/train_pilot/run_20260515_131857.md`; exit code 1, CUDA OOM at epoch 0 step 1419/3744 during BLIP projector forward, no `.ckpt` found.
- [x] H001 Open3DSG Docker `feature_audit` 완료: official BLIP TopK5/scales3 run status `ready`, blockers none, complete ids 3900/3900, train 3744/3744, validation 156/156, missing complete 0, missing preprocessed 0; artifacts `experiments/H001_geom_reliability/sources/open3dsg/dump_features/{manifest.json,report.md}`.
- [x] H001 Open3DSG official feature dump fifth resume launched: previous fourth resume stopped before completion with 3883/3900 complete feature ids and no exit file; launched tmux `h001_open3dsg_dump_features` from 3883/3900 complete ids, log `logs/open3dsg_dump_features_resume_20260515_105521.log`, exit file `logs/open3dsg_dump_features_resume_20260515_105521.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/dump_features/resume_20260515_105521.md`.
- [x] Root `summary.md` 최신 진행 상황 업데이트 완료: Open3DSG feature dump 3548/3900 status, baseline selection policy, `VL-SAT` / Open3DSG / optional SGFormer baseline order, pre-trained re-eval and Docker retraining rule, source checks를 2026-05-15 기준으로 반영했다.
- [x] Paper novelty standard 반영 완료: `AGENTS.md`에 motivation-vs-novelty 기준, H001 paper claim pattern, reviewer-defense rule을 추가했고, `docs/paper.md`에 H001 one-liner, top-tier fit 판단, reviewer attack surface, main evidence checklist, non-claims를 정리했다.
- [x] H001 Open3DSG official feature dump fourth resume launched: added chunked BLIP embedding patch schema `h001_open3dsg_source_patch_v4`, launched tmux `h001_open3dsg_dump_features` from 3329/3900 complete feature ids with `OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=2`, log `logs/open3dsg_dump_features_resume_20260514_142104.log`, exit file `logs/open3dsg_dump_features_resume_20260514_142104.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/dump_features/resume_20260514_142104.md`.
- [x] H001 Open3DSG official feature dump third resume status 확인: tmux ended, exit code 1, CUDA OOM during BLIP vision forward, complete feature ids remain 3329/3900 across all three feature role dirs.
- [x] H001 Open3DSG official feature dump third resume launched: tmux `h001_open3dsg_dump_features` active from 3329/3900 complete feature ids, log `logs/open3dsg_dump_features_resume_20260514_105206.log`, exit file `logs/open3dsg_dump_features_resume_20260514_105206.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/dump_features/resume_20260514_105206.md`.
- [x] H001 Open3DSG official feature dump second resume completed partially: tmux `h001_open3dsg_dump_features` ended with exit code 137 at 2026-05-13 10:18 KST, log `logs/open3dsg_dump_features_resume_20260512_005606.log`, exit file `logs/open3dsg_dump_features_resume_20260512_005606.exit`; progress advanced from 2412/3900 to 3329/3900 complete feature ids before stopping.
- [x] H001 Qwen-VL model cache download/cache verification completed: locked `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`, exit code 0, 14 top-level files, cache size 8.3G; Docker `qwen_vl_cache_verify` wrote `runtime_smoke/cache/{manifest.json,report.md}` with status `model_cache_ready`.
- [x] H001 Qwen-VL guarded runtime preflight attempted without model load: Docker `qwen_vl_runtime_preflight` wrote `runtime_smoke/preflight/{manifest.json,report.md}` with status `blocked_runtime_preflight` because GPU was busy with Open3DSG feature dump; tiny inference smoke was not started.
- [x] H001 Qwen-VL runtime smoke infrastructure and model-cache background job launched: added `configs/qwen_vl/Dockerfile.qwen`, `configs/qwen_vl/compose.qwen.yaml`, `scripts/run_qwen_vl_runtime_smoke.py`; launched tmux `h001_qwen_vl_model_download` for locked `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`, log `logs/qwen_vl_model_download_20260512_082830.log`, exit file `logs/qwen_vl_model_download_20260512_082830.exit`; GPU inference smoke not started.
- [x] H001 Open3DSG official feature dump second resume launched: tmux `h001_open3dsg_dump_features` active from 2412/3900 complete feature ids, log `logs/open3dsg_dump_features_resume_20260512_005606.log`, exit file `logs/open3dsg_dump_features_resume_20260512_005606.exit`, run record `experiments/H001_geom_reliability/sources/open3dsg/dump_features/resume_20260512_005606.md`.
- [x] H001 Open3DSG official feature dump resume attempt completed partially: tmux `h001_open3dsg_dump_features` ended with exit code 137, log `logs/open3dsg_dump_features_resume_20260511_172022.log`, exit file `logs/open3dsg_dump_features_resume_20260511_172022.exit`; progress advanced from 2347/3900 to 2412/3900 complete feature ids before stopping.
- [x] Root `summary.md` H001 연구 전체 요약 업데이트 완료: problem definition, research necessity, hypothesis, method contribution, fixed experiment setting, metrics, comparison groups, current evidence, required tables/figures, main baselines, implementation direction, reviewer-risk defense를 한 문서로 정리했다.
- [x] Root `summary.md` main-baseline reproducibility summary 작성 완료: current H001 main baselines를 `VL-SAT` and Open3DSG로 정의하고, official code, pre-trained baseline checkpoint/component-weight availability, re-training feasibility, current H001 decision, and non-main baseline boundaries for CCL-3DSGG/SGGpoint/SMKA/FROSS/Qwen-VL을 정리했다.
- [x] Literature PAPER.md SGAligner / SG-PGM positioning 업데이트 완료: SGAligner ICCV 2023 and SG-PGM CVPR 2024를 3D scene graph downstream alignment / semantic-geometric fusion 근거로 registry, CAND-001 evidence view, reading queue에 추가했다. H001 direct baseline이 아니라 relation reliability motivation / optional downstream sanity-check 근거로 경계를 기록했다.
- [x] H001 reviewer-risk defense checklist report 반영 완료: Docker `table_builder` report template and regenerated `results/h001_geom_reliability/report.md` now record likely reviewer attacks, required defenses, metric-scope denominator transparency, exact-label recall caveat, and the fact that background Open3DSG feature dump only strengthens defense after downstream audit/checkpoint/raw-dump/adapter/metric/failure-analysis gates complete.
- [x] H001 Open3DSG predicate-family mapping / denominator policy 완료: Docker `open3dsg_metric_scope` generated `sources/open3dsg/metric_scope/{predicate_mapping.json,denominator_policy.json,manifest.json,commands.md,report.md}` with status `metric_scope_policy_ready_no_metric_execution`; in-scope GT denominator 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218; recall matching remains predicate-label exact; filtered-train and covered-scope caveats are frozen before Open3DSG metric execution. Docker `table_builder` now requires this metric-scope policy for Open3DSG Table 6 promotion.
- [x] H001 Open3DSG raw-dump identity checklist 완료: Docker `open3dsg_raw_dump_identity` generated `sources/open3dsg/raw_dump_identity/{checklist.json,manifest.json,commands.md,report.md}` with status `raw_dump_identity_checklist_ready_raw_dump_missing`; fixed identity scope is 127 scans / 388 contexts / 25,916 directed pairs, and current blocker is missing real raw dump `raw_dump/raw.jsonl`. No Open3DSG eval, adapter conversion, metric computation, or failure inspection was run.
- [x] H001 Open3DSG checkpoint provenance/selection template 완료: Docker `open3dsg_checkpoint_selection` generated `sources/open3dsg/checkpoint_selection/{selection_policy.json,record_template.json,manifest.json,commands.md,report.md}` with status `checkpoint_selection_template_ready_checkpoint_missing`; current blockers are `no_checkpoint_candidates` and `official_feature_audit_not_ready:blocked`. The policy freezes route priority and forbids choosing a primary checkpoint using H001 held-out R@K, violation rate, failure-analysis distribution, or held-out visual inspection.
- [x] H001 Open3DSG Table 6 blocked hook 완료: initial Docker `table_builder` wrote `sources/open3dsg/table6_hook.json` and blocked Table 6 until real metrics existed; this was later superseded by the ready Table 6 regeneration from `sources/open3dsg/metrics/metrics.json`.
- [x] H001 Open3DSG metric/join runner contract skeleton 완료: Docker `open3dsg_metric_join_contract` generated `sources/open3dsg/metric_join_contract/{input_contract.json,output_contract.json,metrics.json,manifest.json,commands.md,report.md}` as the input/output contract; this was later rerun with all required inputs present and superseded by real metric eval under `sources/open3dsg/metrics/`.
- [x] H001 Open3DSG post-dump handoff gate 고정 완료: Docker `open3dsg_post_dump_handoff` initially generated `sources/open3dsg/post_dump_handoff/{manifest.json,commands.md,report.md}` while waiting for feature completion; this artifact has since been superseded by completed feature audit, avg-BLIP checkpoint, raw dump identity, adapter, geometry, metrics, Table 6, and failure-row outputs.
- [x] H001 Open3DSG failure-analysis row generator skeleton 완료: Docker `open3dsg_failure_generator_smoke` generated `sources/open3dsg/failure_analysis_generator_smoke/{rows.jsonl,summary.json,manifest.json,report.md}` with 6 synthetic rows, 6 primary categories, locked schema/taxonomy validation errors 0, and status `failure_analysis_generator_smoke_ready_no_metric_inspection`; no Open3DSG metric/failure inspection was performed.
- [x] H001 Open3DSG failure-analysis schema 설계 완료: Docker `open3dsg_failure_schema` generated `sources/open3dsg/failure_analysis/{schema.json,taxonomy.json,aggregation_plan.json,example.jsonl,manifest.json,report.md}` with status `failure_analysis_schema_ready_no_metric_run`; taxonomy has 14 fixed primary categories and 6 aggregation table specs, and no Open3DSG metric/failure inspection was performed.
- [x] H001 Qwen-VL tiny pilot pair-crop rendering 완료: Docker `qwen_vl_tiny_pilot_scope` now filters for shared subject/object views, Docker `qwen_vl_pair_crop_render` generated `sources/qwen_vl/crops/{records.jsonl,manifest.json,report.md}` plus 30 ignored PNG crops under `local_dataset/qwen_vl_crops/tiny_pilot/`; prompt template records red=subject and blue=object box convention; Docker `qwen_vl_tiny_pilot_validator` parsed 30/30 rows with 0 errors/warnings, and rerun `qwen_vl_runtime_plan` reports pair crops 30/30. No model download/inference was started.
- [x] H001 Qwen-VL crop-rendering preflight/model-lock plan 완료: Docker `qwen_vl_runtime_plan` generated `sources/qwen_vl/runtime_plan/{crop_plan.jsonl,model_recommendation.json,commands.md,manifest.json,report.md}` with status `runtime_plan_ready_no_model_download_no_inference`; context frames/object2image metadata are 30/30 and the recommended primary model is `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17` under `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`.
- [x] H001 Qwen-VL tiny pilot scope 선택 완료: Docker `qwen_vl_tiny_pilot_scope` selected 30 non-held-out pilot input rows from filtered train split, balanced as support_contact/proximity/relative_vertical 10/10/10 across 12 scans and 18 subgraphs; held-out overlap 0, pair crops reserved but not rendered, model download/inference not started. Docker `qwen_vl_tiny_pilot_validator` parsed 30/30 synthetic template rows with 0 errors/warnings.
- [x] H001 Qwen-VL contract-only validator/parser skeleton 완료: Docker `qwen_vl_contract_validator` generated `sources/qwen_vl/validation/{input_smoke.jsonl,parsed.jsonl,parser_contract.json,manifest.json,report.md}` with status `validator_parser_skeleton_ready_no_model_runtime`; model download/inference was not started.
- [x] H001 Qwen-VL input/output contract freeze 완료: Docker `qwen_vl_adapter_contract` regenerated frozen `input_schema.json`, `input_schema_example.json`, `output_schema.json`, `output_jsonl_contract.md`, `prediction_schema_example.json`, and status `io_contract_frozen_model_runtime_not_started`; model download/inference was not started.
- [x] Research target rule 추가: 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다.
- [x] H001 experiment spec에 Qwen2.5-VL/Qwen3-VL modern-VLM semantic-source extension 추가: Qwen-VL은 Open3DSG reproduction anchor의 대체가 아니라 trend-aligned optional track이며, Docker/model id/prompt/parser/prediction JSONL/geometry join/metric gate를 요구한다.
- [x] Qwen-VL adapter contract 생성 완료: Docker `qwen_vl_adapter_contract` generated `sources/qwen_vl/{adapter_contract.json,model_candidates.json,prediction_schema_example.json,prompt_templates.md,commands.qwen_vl.md,report.md}` with 2B/3B/4B small-model ladder.
- [x] H001 experiment spec에 layered paper strategy 추가: 3DSSG/VL-SAT main anchor, Open3DSG reproduction anchor, Qwen-VL modern semantic-source extension, SceneFun3D/FunGraph3D robotics/functionality expansion을 분리했다.
- [x] AGENTS long-running/background task policy 추가: long-running I/O jobs는 `tmux`/background로 실행, `logs/` timestamp log, resumable command, exact command/verification record, targeted log inspection, completion verification, TODO/hypothesis status update를 요구한다.
- [x] H001 Open3DSG hardened official dump restart 확인: tmux `h001_open3dsg_dump_features` restarted; preflight/patch ready, `epochs=1` active, existing 5 feature ids skipped in ~16s, and additional official TopK5/scales3 feature ids are being written.
- [x] H001 Open3DSG partial feature audit 완료: Docker `feature_audit` now records official run coverage as blocked with 5/3900 complete feature ids, train 5/3744, validation 0/156, missing preprocessed 0.
- [x] H001 Open3DSG feature dump runtime policy hardening 완료: previous official run was interrupted after confirming feature writing because the command needed stronger runtime policy; `dump_features_3rscan` now has explicit `--epochs 1`, pre-forward skip-existing resume, deterministic no-shuffle dump iteration, stable official run dir, corrected training `--load_features` path, and a clearly marked reduced TopK1/scales1 pilot route for checkpoint smoke only.
- [x] H001 Open3DSG validation coverage guard 완료: validation views 30/30, validation preprocess 156/160 ready after retry/filter, runtime validation split 30 scans / 156 subgraphs / 3,696 relations.
- [x] H001 Open3DSG `dump_features_3rscan` hardening 진행: process-pool crash는 `OPEN3DSG_DATASET_LOAD_WORKERS=1`로 우회, preload OOM은 `OPEN3DSG_LAZY_DATASET=1` lazy dataset patch로 우회, DataLoader shm bus error는 `workers=0`으로 우회, dump-time CUDA OOM은 `dump_features` no-grad patch와 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`로 우회했다. Current run reaches feature writing but official BLIP TopK5/scales3 throughput is slow.
- [x] H001 Open3DSG missing preprocess recoverability audit 완료: `train_preprocess/full.log`의 `too few visible objects, scene missalignment possible` count가 108이고 manifest의 108개 `missing_output` ID와 일치한다. Docker representative retry는 sample missing targets를 회복하지 못했으며, 단순 재시도/fix 대상이 아니라 source-level visibility filter drop으로 판단했다.
- [x] H001 Open3DSG explicit train preprocess filter 적용 완료: runtime `relationships_train.json`/`train_scans.txt`를 preprocessed-ready split으로 갱신하고 `.unfiltered` backup을 남겼다. Runtime train split은 1178 scans / 3852 subgraphs / 81,190 relations에서 1158 scans / 3744 subgraphs / 79,704 relations로 줄었고, 108 missing subgraphs / 1,486 relations / 20 removed-only scans는 `train_preprocess_filter/`에 기록했다. Docker `train_preprocess_filter` service로 같은 count를 재현했고, protected `dump_features_3rscan` preflight now reports `ready`.
- [x] H001 Open3DSG cu128 env/cache + guarded dump rerun 완료: `env_check` passes with CUDA visible, device count 1, torch `2.8.0+cu128`, RTX 5090 `sm_120` supported; `cache_preflight` status is `ready_with_cache_warnings` with only `torch_hub` cache warning; the initial protected `dump_features_3rscan` rerun correctly stopped before Open3DSG execution at runtime coverage blockers `train_views:2/1178` and `train_preprocessed:7/3852`.
- [x] H001 Open3DSG train view/preprocess Docker staging smoke 완료: `train_views_audit`, `train_views_smoke`, and corrected `train_preprocess_smoke` services added; smoke generated/confirmed train views for 2 scans total and preprocessed 7 subgraphs for one scan, with no preprocess blockers in the smoke artifact.
- [x] H001 Open3DSG `train_views_full` 완료: detached tmux run exited 0; `train_views/full.log` and `train_views/manifest.json` report 1178/1178 ready scan view pickles, actions `generated` 1176 and `already_ready` 2.
- [x] H001 Open3DSG `train_preprocess_full` 완료: detached tmux run exited 0; `train_preprocess/manifest.json` status is `preprocess_partial_ready`, 3744/3852 ready subgraphs, 108 missing outputs across 101 scans, actions `generated` 3737 and `already_ready` 7. This initially blocked protected `dump_features_3rscan` at `train_preprocessed:3744/3852`; the later explicit filter item records the current resolution.
- [x] H001 Open3DSG full train payload staging 완료: `training_repro` status is `training_repro_staged_root_ready_for_view_preprocess`; official train payload is 1178/1178 for scan dirs, raw files, Open3DSG mesh/texture, and sequence files; train-dev payload is 30/30. Background tmux downloader session has ended, and `open3dsg_train_handoff` now reports `ready_for_open3dsg_env_check`.
- [x] H001 Open3DSG eval checkpoint/path guard 완료: Docker `eval_preflight` service and `eval_h001_gt_objects` inline guard added; it checks `OPEN3DSG_CHECKPOINT`, H001 runtime paths, model files, selected 127 scans / 388 contexts, Docker imports/CUDA, and raw-dump JSONL contract. Current protected eval smoke stops before `pip install -e .` and Open3DSG execution because checkpoint env/file is missing.
- [x] H001 Open3DSG adapter smoke-test 완료: `export_open3dsg_predictions.py --smoke-test` and Docker `open3dsg_adapter_smoke` service added; synthetic identity-preserving raw JSONL converts to H001 prediction JSONL with 388 contexts, 1 raw row, 2 prediction rows, zero errors/warnings. Contract-only adapter remains `adapter_contract_ready_raw_dump_missing` until reproduced checkpoint raw dump exists.
- [x] H001 Open3DSG model/cache preflight 완료: Docker `cache_preflight` service added for persistent `HOME`/`XDG_CACHE_HOME`, HF/torch/CLIP cache dirs, 300GB disk budget, OpenSeg/BLIP/PointNet local checkpoint files, and model import checks; current cu128 rerun passes required files/imports/disk and leaves only a non-blocking `torch_hub` cache warning.
- [x] H001 Open3DSG training preflight hardening 완료: `open3dsg_training_preflight.py` now checks full train payload, runtime train view/preprocess coverage, writable runtime/cache dirs, Open3DSG source entrypoint, Docker imports (`torch`, `pytorch_lightning`, `tensorflow`, `open3d`, `transformers`), and CUDA visibility; protected `dump_features_3rscan`, `train_pilot`, and `train_full` stop before Open3DSG execution until coverage/features are ready.
- [x] H001 Open3DSG Docker env image build/import check 완료: `h001-open3dsg-repro:cu128` build/import path passes with CUDA visible (`torch.cuda.is_available=True`, device count 1, torch `2.8.0+cu128`, RTX 5090 `sm_120` supported). 기록: `experiments/H001_geom_reliability/sources/open3dsg/env_check.md`.
- [x] H001 Open3DSG Docker training preflight guard 완료: `open3dsg_training_preflight.py` added and wired before `dump_features_3rscan`, `train_pilot`, and `train_full`; protected compose commands now stop before Open3DSG execution while payload is incomplete. Current guard artifacts are under `experiments/H001_geom_reliability/sources/open3dsg/training_preflight/`.
- [x] H001 Open3DSG training handoff + prediction adapter skeleton 완료: Docker `open3dsg_train_handoff` service generated `sources/open3dsg/training_handoff/{manifest.json,commands.md,report.md}` with current status `blocked_payload_incomplete`; Docker `open3dsg_adapter_contract` service generated `sources/open3dsg/adapter/{manifest.json,raw_schema_example.json,report.md}` with status `adapter_contract_ready_raw_dump_missing` and 388 H001 contexts.
- [x] H001 Open3DSG 3RScan payload batch route/progress 완료: Docker `open3dsg_payload` service added; audit pass, pilot batches, and resumable background `--limit 100` loop worked with no file/sequence failures in the recorded route; final synced `training_repro` readiness is train scan dirs 1178/1178, train mesh/texture 1178/1178, train sequence extracted 1178/1178.
- [x] H001 Open3DSG `training_repro` metadata/split staging 완료: Docker `open3dsg_train_root` service generated `sources/open3dsg/training_repro/{manifest.json,records.jsonl,missing_train_scans.txt,missing_train_dev_scans.txt,report.md}` and local staged root `local_dataset/Open3DSG_staged/training_repro/`; official train metadata 1178 scans / 3852 subgraphs / 81,190 relations, train-dev without H001 held-out 30 scans / 160 subgraphs / 3,749 relations, H001 held-out overlap train/train-dev 0/0; status `training_repro_staged_root_ready_for_view_preprocess`.
- [x] H001 Dockerized Open3DSG checkpoint reproduction plan 완료: Docker `open3dsg_plan` service generated `checkpoint_plan.{json,md}`, `Dockerfile.repro`, `compose.open3dsg.yaml`, `commands.open3dsg.md`, and status `checkpoint_reproduction_plan_ready_training_not_started`; split fixed to official train 1178 scans / 3852 subgraphs / 81,190 relations and H001 eval 127 scans / 388 subgraphs / 7,505 relations, with dependency pins, dataset/cache mounts, training commands, and failure budget recorded.
- [x] H001 Docker table/report reproduction 재실행 완료: `sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml build && env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm table_builder'`, status `ready`, predictions 673,816 / GT 7,505 / verification 673,816 row count 재확인
- [x] H001 hypothesis markdown consolidation 완료: H001 root markdown files reduced to 7 canonical files, with duplicated stage content merged and current dashboards updated.
- [x] H001 Docker experiment workflow entry 완료: `experiments/H001_geom_reliability/` 생성, Dockerfile/compose/commands/manifest/script 작성, `sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm table_builder'`로 Table 1-6, `manifest.lock.json`, `report.md`, `figure_specs.*`, source status files 생성; manifest status `ready`.
- [x] H001 top-tier direction update 완료: method contribution을 calibrated geometry-consistency evaluation/re-ranking framework로 정리하고, Open3DSG checkpoint를 Docker로 직접 재현해 second-source adapter result를 확보하는 방향을 선택; single-baseline reliability-layer justification은 fallback으로 유지.
- [x] H001 scoped main experiment implementation spec 완료: `07_experiment_spec.md`, status `hypothesis_stage_complete_for_geom_reliability_experiment`; fixed inputs, metrics, tables, figures, acceptance criteria, and proposed `experiments/H001_geom_reliability/` workflow root 고정.
- [x] Paper experiment Docker rule 고정: 논문 본문용 실제 experiment 구현은 Docker 기반으로만 진행하며, host-only output은 paper experiment 결과로 승격하지 않음.
- [x] H001 GT-based verifier evaluation 완료: GT positives 2,545, GT-derived negatives 2,545, positive nonviolated 0.9972, negative nonsatisfied 0.9694, `p_geom_valid` AUROC/AUPRC 0.9779/0.9737.
- [x] H001 reduced visual spot-check label fill/summary 완료: reviewer id `yhkim`, status `ready_sanity_pass`, labels 50/50, target quality-issue rate 0.9333, contradiction rate 0.0333.
- [x] H001 final scoped evidence lock 완료: status `scoped_hypothesis_evidence_locked_with_reduced_visual_sanity_check`; scoped main experiment implementation spec으로 진행 가능.
- [x] H001 Open3DSG second-source path decision 업데이트: official checkpoint 대기 대신 Dockerized checkpoint reproduction을 선택; raw dump/JSONL/join/metric은 reproduced checkpoint 이후 진행.
- [x] H001 Open3DSG runtime staging 완료: staged metadata/root, mesh/texture, view pickles, source-visible preprocessed pickles, BLIP2/OpenSeg/PointNet/PointNet2 ready/partial-ready; trained checkpoint missing.
- [x] H001 FROSS source/runtime feasibility 완료: FROSS is support/contact-only for H001 and blocked by missing runtime artifacts.
- [x] H001 G3/G4/G5/G6 hardening completed: family-specific calibration control, structured audit, baseline feasibility, and reportability gate recorded.
- [x] H001 hardened `VL-SAT` raw/export/join/metrics completed: 127 scans, 388 subgraphs, 673,816 prediction rows, 7,505 ground-truth rows.
- [x] H001 calibration track completed: calibration data contract, train/dev split/export, `p_geom_valid` smoke, family-conditional calibrated risk, and held-out application.
- [x] CAND-003 literature survey pass completed through P1 paper intake.

## Pending / Blocked

- [ ] Do not treat hardened `VL-SAT` alone as baseline-agnostic or broad open-vocabulary final evidence; Open3DSG second-source metrics now support only measured H001-family cross-source reliability claims.
- [x] FROSS runtime/adapter blocking issue is resolved through official
      ReplicaSSG full-trajectory inference and a 4,290-row adapter output.
- [x] ReplicaSSG provides exact `near/above/under` mappings for proximity and
      relative-vertical only. Support/contact remains excluded, and the failed
      K=100 gate prevents broad/full-family evidence wording.
- [x] Open3DSG second-source metrics exist. Current full-validation wording must report selected-checkpoint provenance, filtered train/dev provenance, exact-label denominator, 548/548 recovery policy, 533/548 sensitivity branch, and residual calibration risk. Historical 127-scan averaged-BLIP / covered-scope / `validation_missing_preprocessed:11` caveats stay local to that branch.
- [ ] Do not choose or change the primary Open3DSG checkpoint using H001 held-out metrics, failure-analysis distribution, or held-out visual inspection.
- [x] Open3DSG raw dump conversion and metric run occurred only after Docker `open3dsg_raw_dump_identity` reported `raw_dump_identity_audit_ready`.
- [ ] Do not promote Open3DSG metric/Table 6 results unless `metric_scope` status is ready, predicate recall remains exact-label matched, and selected-checkpoint / filtered-train-dev / recovery-policy / sensitivity-branch caveats are reported.
- [ ] Do not overstate the reduced 50-row visual sanity check as a large-scale or strictly blinded human audit; provenance is `yhkim` reference-aligned labels transcribed by Codex.
- [ ] Keep `paper/` limited to paper-writing handoff/draft artifacts for now; do not create `decisions/` yet. `experiments/H001_geom_reliability/` remains the active Docker experiment root.
- [ ] Do not promote host-only outputs to paper experiment results; final paper tables/reports must be reproducible from documented Docker commands.
- [ ] Do not promote H001 to final paper claim without explicitly recording remaining limitations and next validation requirements.

## Rules

- 작업을 시작할 때 이 파일을 먼저 확인한다.
- 작업 중 새 task가 생기면 이 파일에 추가한다.
- 완료한 task는 체크하고, 필요한 상세 내용은 `literature/` 또는 해당 workflow 문서에 기록한다.
- 이 파일은 긴 설명을 담지 않는다. 계획, 상태, 다음 행동만 관리한다.
