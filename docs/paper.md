# Paper Workflow

Last updated: 2026-06-05

This document manages paper-level framing for H001/CAND-001: novelty, contribution boundary, reviewer-defense logic, and the minimum experiment evidence needed before paper writing. It does not replace `docs/hypothesis.md`, `07_experiment_spec.md`, or Docker experiment artifacts.

## Ownership

- `docs/paper.md` is the authoritative paper-framing rulebook.
- `AGENTS.md` keeps only stable top-level claim guardrails and points here for detailed paper rules.
- `paper/README.md` owns the paper workspace map and file-role guide.
- Manuscript prose, figures, tables, venue-specific LaTeX source, and draft history live under `paper/`.
- Hypothesis validation details live under `hypothesis/`; executable paper experiment details live under `experiments/`; reproducibility and artifact transfer details live in `docs/reproducibility.md`.

## Source Note

- Checked on: 2026-05-14
- Reference: [Motivation is not Novelty](https://gisbi-kim.github.io/motivation-is-not-novelty/)
- Usage: paper-framing heuristic, not scientific evidence about 3D Scene Graphs.

## Novelty Rule

Fact from the reference:

- Motivation is not novelty. "Existing methods fail under X, so we add module Y" is still a motivation-level argument unless the paper explains why the failure happens and why Y must take its proposed form.
- A top-tier pattern is: define a concrete failure mode, explain the underlying cause, derive the method from that cause, then verify the design through ablation, controls, generality checks, and failure analysis.
- Strong novelty is not merely a new component, combination, dataset use, or larger experiment. It is the insight that turns an observed failure into a necessary method design.

H001 rule:

- Do not claim novelty as "we add geometry", "we combine semantic and geometry", "we use a VLM", or "we implement a verifier".
- Claim novelty as a calibrated geometry-consistency evaluation/re-ranking framework that targets a specific failure: semantically plausible 3D relation predictions can be physically inconsistent because semantic confidence is not calibrated to relation-level geometry.

## Current One-Liner

Draft:

> Semantic relation predictors can rank plausible 3D Scene Graph relations without calibrating them to relation-level physical consistency; calibrated geometry-consistency scoring exposes this failure mode and re-ranks predictions to reduce geometric violations while making recall tradeoffs measurable.

This is the preferred direction because it contains both cause diagnosis and method principle. Open3DSG second-source metrics are now available, so the paper wording should stay scoped to measured H001 families rather than broaden to full open-vocabulary 3DSSG generation.

2026-06-05 paper-facing evaluation direction:

- The primary result should use the full official `3DSSG_subset` validation
  split, not the pilot-excluded 127-scan hardened scope.
- Full-validation VL-SAT and Open3DSG artifacts now exist. VL-SAT is the
  controlled-anchor full-validation metric bundle. Open3DSG uses the 548/548
  recovery-policy variant as the primary full-denominator branch; the original
  533/548 covered branch remains a sensitivity / unmodified-source-route check.
- The Open3DSG recovery branch uses `min_visible=2` and relaxed two-scan view
  regeneration. This must be disclosed wherever the Open3DSG full-validation
  result is used.
- The method provenance must be stated as train/train-dev-derived: final family
  mapping, hard-rule policies, counterfactual construction, and `p_geom_valid`
  calibration are frozen before validation source-result reporting.
- H001-Mini is hypothesis/feasibility evidence, not a paper metric split and
  not a calibrator/threshold fitting split.
- Source-result tables and claims should now be regenerated from the selected
  full-validation route. Do not silently present the recovery branch as the
  unmodified Open3DSG preprocess route; use the 533/548 covered branch as a
  sensitivity check to show the conclusion is not created by the recovery
  policy.

Current paper workspace:

- `paper/README.md` is the folder-local entry point and records the roles of the paper files, reading order, and update ownership.
- `paper/preview.md` summarizes current evidence, caveats, reviewer-defense map, optional extension boundary, and recovery files.
- `paper/progress.md` records why each hypothesis/experiment stage was run, why the next stage was needed, and how the key results should be interpreted.
- `paper/outline.md` provides the English/Korean paper skeleton, recommended title, title alternatives, three contribution statements, abstract skeleton, section-level evidence placement, Open3DSG caveat placement, reviewer-defense plan, and table/figure plan. Cross-source results and failure analysis are treated as empirical validation, not a separate fourth contribution.
- `paper/draft.md` provides first-pass manuscript prose for Title, Abstract, Introduction, Related Work, Problem Formulation, Method, Experimental Setup, Results/Discussion, Limitations, and Conclusion. It has passed claim-scope/evidence-link review and now uses BibTeX-style citation keys in Related Work.
- `paper/risk.md` tracks reviewer-risk attacks, mitigation status, and priority for logic/evidence/novelty/reproducibility defenses.
- `paper/appendix.md` owns appendix/supplement provenance tables, detailed Open3DSG caveat consistency checks, optional Figure 3 decisions, and Qwen-VL extension boundary notes.
- `paper/aaai/` is the current target-venue LaTeX source. It now uses the official AAAI-26 Author Kit style files checked on 2026-05-27 KST, splits the draft into `main.tex` plus `sec/*.tex`, points bibliography to `paper/references.bib`, and includes the AAAI reproducibility checklist after references. Docker PDF build is verified with `h001-aaai-tex:20260526`.
- `paper/iccv/` remains a historical/alternate ICCV-style source route.
- `paper/figures.md` locks Figure 1-3 source claims, exact values, case IDs, artifacts, and caption constraints; draft SVGs are generated, verified, and layout-reviewed under `paper/generated/figures/`.

## H001 Fit To Top-Tier Pattern

Facts:

- H001 already has a concrete failure target: geometry-checkable relation families such as `support_contact`, `proximity`, and `relative_vertical`.
- Hypothesis-stage `VL-SAT` evidence includes semantic-only vs calibrated geometry variants, family-specific controls, evidence lock, GT-based verifier evaluation, and a reduced visual sanity check.
- The Open3DSG path is now second-source evidence: Docker checkpoint reproduction, raw-dump identity, adapter export, geometry join, metric eval, Table 6, real failure rows, qualitative case queue, and deterministic qualitative inspection are ready.
- Docker subgraph bootstrap CI is ready under `experiments/H001_geom_reliability/bootstrap_ci/`; it is used as evaluation-context uncertainty, not repeated-training variance.
- Open3DSG qualitative inspection shows both support and limits: 23/36 sampled cases are demoted by geometry-aware reranking, while 10/36 are rule-violated but still have `p_geom_valid > 0.9`. This must be framed as residual calibration risk, not hidden.
- The historical 127-scan Open3DSG branch has clean raw-dump source-process
  provenance via v14 streaming same-path resume and remains caveated by filtered
  train split, averaged-BLIP variant, covered loadable scope, and
  `validation_missing_preprocessed:11`; earlier exit-137 attempts are historical
  run records, not final raw-dump provenance caveats.
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
- `attachment_deferred` is the preferred future relation-family upgrade if H001
  is expanded beyond the current AAAI claim. It is not current metric evidence.
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
  has 199 missing exact-label GT rows. This is still contract evidence only
  because full-source scoring and metrics do not exist. `connected to` has no
  dev strict rows, so pooled calibration or an explicit caveat is required. This
  direction is better aligned with
  the H001
  physical-consistency thesis than `relative_horizontal`, because attachment,
  hanging, and connection imply physical support/adjacency, near-surface
  contact, gravity, and object-affordance constraints. Its risk is rule
  complexity: it requires validated wall/ceiling/furniture surface evidence,
  local point contact, surface normals, hanging geometry, contradictory support
  handling, and conservative uncertain handling. Treat it as a future upgrade
  path whose next gates are full-source scoring, two-source metrics, controls,
  bootstrap CI, and audit before any main-claim
  promotion.
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
- Include semantic-only, rule-only, calibrated, and family-specific variants.
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
  source scoring preflight are complete, but do not promote it from "future
  upgrade" to "main result" before it has full-source metrics, controls,
  bootstrap CI, and audit. Visual labels remain optional for a soft protocol,
  not required for the frozen strict-only calibration route.
  Function-reasoning examples may be useful as a secondary case study only
  after relation reliability is established.
- Treat RelWitness-style "relation witness" and "calibrated witness quality" wording as prior-art-adjacent. H001 should claim reproduced calibrated reliability evaluation/re-ranking, source-adapter protocol, recall/violation operating points, and controls, not the mere existence of visual-geometric evidence or calibration.

## Main Paper Evidence Checklist

Minimum table/figure set before paper writing:

- Table 1: dataset/split/scope and denominator audit.
- Table 2: source-specific claim boundary and blocked extensions.
- Table 3: Open3DSG-first main source results with VL-SAT as the controlled anchor.
- Prose: controls, GT verifier evaluation, audit, and visual sanity checks unless an appendix is added.
- Figure 1: failure mechanism and framework overview.
- Figure 2: recall-violation tradeoff across semantic-only, probabilistic calibrated, rule-verified, and family-specific operating points.
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

## Next Paper-Framing Step

- Claim-consistency review is complete in `paper/outline.md`: title, contribution statements, abstract, Introduction, Figure 1-3 captions, and Table 1-6 captions preserve the scoped relation-reliability claim.
- Paper-body content blocks are secured in `paper/outline.md`: related-work positioning, problem/method formalization, re-ranking algorithm skeleton, Results/controls/Open3DSG prose skeleton, failure-analysis prose skeleton, limitation prose, Figure 1-3 asset plan, and table/appendix placement.
- First-pass manuscript prose is drafted and claim-scope/evidence-link reviewed in `paper/draft.md`; Title, quantitative Abstract, and Introduction are now filled before Related Work.
- Figure 1-3 source lock is complete in `paper/figures.md`: Figure 1 method framework, Figure 2 two-panel R@100/Violation@100 tradeoff, and Figure 3 Open3DSG qualitative case panels.
- Draft Figure 1-3 generation, top-tier novelty/layout review, and Figure 3 geometry-backed panel upgrade are complete under `paper/generated/figures/`; validation passed for locked values, case IDs, geometry case IDs, and SVG XML parsing.
- Recent 2025-2026 Related Work roles are decided: RelWitness is a required direct novelty-threat citation, VIZOR is a required spatial-relation/viewpoint-boundary citation, ZING-3D is a VLM/incremental 3DSG trend citation, Open-World 3DSG-RAG is a broad open-world/RAG boundary citation, and View-on-Graph is a downstream grounding-motivation citation.
- Section structure is locked: keep Section 5 as a short standalone `Experimental Setup` section. Do not merge it into Results because denominator, filtered-split, covered-scope, Open3DSG variant, and Docker-result boundaries are part of the reviewer defense.
- Section-title rule: use standard paper headings such as `Experiments`, `Experimental Setup`, `Evaluation Setup`, `Datasets`, `Evaluation Metrics`, and `Implementation Details`. Do not put `Scope` in the heading unless the target venue/template makes it necessary; H001's scope and denominator discipline should be stated in the first paragraph and tables.
- Section-title reference check, 2026-05-23: Open3DSG uses `4 Experiments` / `4.1 Experimental Setup`; OpenFunGraph uses `6 Experiments` / `6.1 Experimental Setup`; FROSS uses `4 Experimental Results` / `4.1 Evaluation Setup` with dataset/metric/implementation subsections; VIZOR uses `4 Experiments` / `4.1 Datasets` and separates `5 Failure Analysis`. This supports the H001 decision to use the standard heading `Experimental Setup` while keeping scope/caveat details in text and tables.
- Target venue direction is AAAI-style main conference writing. Content stability and AAAI page/checklist compliance come before final camera-ready polish.
- `paper/draft.md` Title/Abstract/Introduction quick review is complete; front matter is about 701 words excluding title, with a 201-word abstract and 500-word Introduction before final compression.
- Paper-body gap review patch is complete: Figure 1-3 callouts, Table 4 audit/sanity prose, and Conclusion are now in `paper/draft.md`.
- Paper-body budget review is complete: Title-through-Conclusion prose is about 3,507 words. The current AAAI manuscript uses three main tables: fixed scope/denominator, source-specific claim boundary, and Open3DSG-first source results with `VL-SAT` as controlled anchor. Controls, GT verifier, audit, and detailed family rows stay as prose-backed evidence unless an appendix is added.
- AAAI-style source conversion is complete under `paper/aaai/` using the official AAAI-26 Author Kit. The 2026-05-27 check confirms `aaai2026.sty` was replaced from `AuthorKit26/AnonymousSubmission/LaTeX/aaai2026.sty`, `aaai2026.bst` already matched the official kit, and no official AAAI-27 author kit was confirmed.
- The `paper/aaai/` manuscript-content pass is complete: it includes fixed scope/denominator accounting, a source-specific claim-boundary table, an Open3DSG-first main source-results table, prose controls/verifier/audit evidence, explicit Open3DSG caveat captioning, and limitation wording.
- Figure 1-3 PNG build assets are ready and `paper/aaai/sec/6_results.tex` points to them. Figure 2 and Figure 3 are single-column in the AAAI source to keep technical content before references.
- Docker build verification is complete: `paper/aaai/main.pdf` builds with `h001-aaai-tex:20260526`, BibTeX uses 19 entries, and there are no missing citations, undefined refs, overfull hboxes, LaTeX errors, or AAAI package errors. Latest full-validation rebuild log: `logs/h001_aaai_pdf_build_full_validation_20260605_100108.log`.
- AAAI reproducibility checklist insertion is complete: `paper/aaai/sec/9_reproducibility_checklist.tex` is included after references. Docker rebuild `logs/h001_aaai_pdf_build_full_validation_20260605_100108.log` exits 0; the PDF has 9 total pages, technical content on pages 1-7, references on page 8, checklist on page 9, and no missing citations, undefined refs, overfull hboxes, LaTeX errors, or AAAI package errors.
- AAAI reviewer-defense main-text pass is updated for the selected
  full-validation route: Introduction, Method, Experimental Setup, Results, and
  Limitations directly answer the high-risk attacks, including hand-coded
  verifier, geometry-only/distance heuristic, recall-for-violation tradeoff,
  Open3DSG recovery-policy provenance, family selection, AAAI relevance, and
  small-delta uncertainty.
- The 2026-05-27 appendix/caveat pass is complete: `paper/appendix.md` records the calibrator/threshold provenance table and caveat consistency pass; experiment Table 6 includes `caveat_note`; Docker PDF rebuild `logs/h001_aaai_pdf_build_appendix_caveat_20260527_202734.log` exits 0 with 9 total pages and no blocking warnings.
- Draft bibliography scaffold is complete in `paper/references.bib`; citation keys used by `paper/aaai/sec/*.tex` match the bibliography entries.
- Use `paper/generated/figures/figure3_geometry_panels.svg` as the preferred Figure 3 draft; keep `figure3_failure_cases.svg` as the traceable row-card fallback. A rendered scene-crop upgrade is optional only if a deterministic crop/render path is added.
- Keep Open3DSG caveats explicit in manuscript Table 3 and experiment artifact
  Table 6; later compression must retain selected official non-avg checkpoint
  provenance, filtered-train/dev provenance, exact-label denominator, residual
  calibration risk, and the `recovery_relaxed_views_min2/` policy. If reporting
  the historical 127-scan branch, retain averaged-BLIP, covered loadable scope,
  and `validation_missing_preprocessed:11` there only as historical/sensitivity
  caveats.
- Source-results table and failure-analysis text are regenerated from the
  selected full-validation route rather than the older 127-scan caveat wording.
- Keep clean v14 streaming source-process provenance separate from historical exit-137 run records in reproducibility wording.
- Keep Qwen-VL as third-source extension evidence unless it receives the same Docker, metric, and audit treatment. Current Qwen promotion status is protocol-frozen but non-metric: tiny runtime smoke passed, full-source plan frozen, shards 0000-0013 completed with 3,500 parsed rows, and clean resume starts from shard 0014 after GPU guard is acceptable. No full prediction/geometry/metric/audit path is complete yet.
- Keep the `relative_horizontal` expansion track frozen as appendix/limitation
  evidence for the current AAAI path. The no-training/no-inference denominator
  audit, Docker coordinate audit, and Docker bucket inspection are complete, but
  the track is blocked for promotion; do not change the current main claim
  unless a later expansion reaches the current H001 evidence standard.
- RelWitness full-PDF skim is complete for v2. Before submission, check whether a newer RelWitness version adds reproduced results, code, arbitrary-source adapters, `Violation@K`, or wrong-pair/shuffled-geometry controls.
