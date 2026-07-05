# GeoCalib / H001 Research Summary

Last updated: 2026-07-05 KST

Paper-facing name: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`.
Use `GeoCalib` in manuscript-facing prose. Keep `H001` only for internal
experiment paths and archived hypothesis records.

Parallel H002 paper route:

- Workspace: `paper/h002_compatibility_routing/`
- Title: `Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations`
- Role: standalone validation-level paper candidate, separate from the active
  H001/GeoCalib manuscript.
- Updated goal: route-aware reliable 3D relation framework.
- Current main quantitative success route: comparison compatibility
  (`relative_vertical`, `size_relative`).
- Claim boundary: source reranking with `S2_source_x_Ce` on VL-SAT/Open3DSG
  validation predictions; no official-test/SOTA claim; no completed
  all-relation framework claim; calibrated p_obs/p_rel solved claim remains
  blocked.
- Latest H002 ablation status: `A1_source_x_G_only` and
  `A2_source_x_TG_concat` are implemented and reviewed in the Docker
  source-reranking path. Aggregate primary comparison-route evidence supports
  `S2_source_x_Ce` over both ablations; family-wise Violation reduction is
  stable, but Recall improvement is mixed in saturated/low-denominator cells.
- Latest H002 global review: the experiment-stage remaining-gap review is
  complete with validation errors `0`. H002 is paper-possible only as a scoped
  validation-level comparison-route reranking claim. Broad all-relation
  reliability, support/contact solved, official-test/SOTA, and calibrated
  p_obs/p_rel solved claims remain blocked. Before final paper wording, resolve
  or explicitly caveat two sensitivities: validation candidate-pool
  normalization and the fact that the G-only ablation is route-aware because
  `G_e` includes a `route_family` one-hot.
- Latest H002 sensitivity status: normalization/no-route geometry sensitivity is
  complete with validation errors `0`. No-route G-only passed, so the S2 gain is
  not explained by route-family one-hot geometry features. Raw
  `source_score*C_e` preserves the improvement direction over S0 at K
  `{10,20,50}`; rank-percentile normalization reduces violations but loses
  low-K recall. Current method is natural and principled for the scoped
  comparison-route problem. Relation-aware evidence routing is constructed and
  partially validated, but a completed general reliable 3D relation framework is
  not yet validated.
- Latest H002 paper boundary status: claim-boundary update after sensitivity
  review is complete, and the selected paper direction is now relation-aware
  evidence routing. The framework claim is broad: reliable 3D relation
  estimation requires route-specific evidence rather than one fixed
  semantic-geometry fusion. The validated quantitative mechanism remains
  narrower: validation-level comparison-route source reranking with
  factor-isolated predicate-geometry compatibility.
- Next H002 work stays in the experiment stage before further paper
  strengthening. The current focus is no longer calibrated `p_obs/p_rel`; it is
  improving and reviewing `C_e = compatibility(T_e, G_e)` as the core signal.
- Latest H002 experiment-stage synthesis: Docker service
  `h002-general-framework-gap` produced
  `experiments/H002_compatibility_routing/general_framework_gap/latest/` with
  validation errors `0`. The general framework claim remains blocked:
  support/contact solved, calibrated `p_obs/p_rel` solved,
  normalization-invariant improvement, and route-aware source-wide
  generalization all failed current promotion gates. Next experiment-stage step
  was `support_contact_generalization_repair`.
- Latest H002 support/contact repair status: Docker service
  `h002-support-contact-generalization-repair` produced
  `experiments/H002_compatibility_routing/support_contact_generalization_repair/latest/`
  with validation errors `0`. Current support/contact failure is not missing
  current feature coverage (`43/43` current `G_e` features available on
  `3178/3178` rows); it is a pose-subtype/observability target problem. Hard
  official M4 AUROC remains `0.077539`, so support/contact solved wording is
  blocked. Next experiment-stage step is
  `support_contact_generalization_repair_materialization`.
- Latest H002 support/contact repair materialization: Docker service
  `h002-support-contact-repair-materialize` produced
  `experiments/H002_compatibility_routing/support_contact_repair_materialization/latest/`
  with validation errors `0` and gate failures `1`. After enforcing
  mixed-class-pair control, only `40` binary rows over `4` class-pairs remain;
  `3138` rows are abstain/diagnostic. Metric rerun is blocked because the
  capacity is too small. Next experiment-stage step is
  `support_contact_generalization_repair_capacity_decision`.
- Latest H002 support/contact capacity decision: Docker service
  `h002-support-contact-capacity-decision` produced
  `experiments/H002_compatibility_routing/support_contact_capacity_decision/latest/`
  with validation errors `0`. Support/contact is frozen as
  diagnostic/failure-taxonomy evidence for the current H002 path; metric rerun
  and solved-route wording are blocked. Reopening requires independent
  pose/observability labels with at least `200` binary rows and `10` mixed
  class-pairs after shortcut control. Next experiment-stage step is
  `pobs_prel_observability_repair`.
- Latest H002 p_obs/p_rel observability repair and label ingestion: Docker service
  `h002-pobs-prel-observability-repair` produced
  `experiments/H002_compatibility_routing/pobs_prel_observability_repair/latest/`
  with validation errors `0`. Current real asset-observability labels remain
  single-class (`observable:23062`), synthetic missing-evidence controls remain
  controls rather than GT, and calibrated `p_rel` ECE@10 is `0.223458`. A
  `265`-row visual/mesh audit queue was created. Codex label fill, ingestion,
  and schema audit have now completed with validation errors `0`: labels are
  `observable_clear:135`, `ambiguous_evidence:126`, and
  `unobservable_missing_evidence:4`; blocked model-safe field hits are `0`.
  The user confirmed these Codex-filled labels for a diagnostic rerun, so the
  metric gate opened and Docker service
  `h002-pobs-prel-observability-metric-runner` evaluated the `265`-row subset
  with validation errors `0`. Result: `p_obs` AUROC `0.500000`, ECE@10
  `0.446174`, `p_rel` AUROC `0.774704`, ECE@10 `0.083819`, decision macro-F1
  `0.331637`. The rerun shows useful `p_rel` signal but `p_obs` failure on
  ambiguous/missing-evidence rows. The result review completed with validation
  errors `0` and identified the cause as `Q_e` feature/label mismatch:
  `ambiguous_evidence` `126/126` rows and `unobservable_missing_evidence` `4/4`
  rows are still marked as Q_e-sufficient in the model-safe view. Calibrated
  p_obs/p_rel solved-claim wording remains blocked. The Q_e repair plan is now
  complete with validation errors `0`: it freezes Q_e v2 blocks for asset
  availability, visual coverage, geometry quality, ambiguity, and Q_e state v2.
  The repaired Q_e v2 materialization is also complete with validation errors
  `0` and blocked field hits `0`: train rows are balanced at `4868` each for
  observable/ambiguous/missing, and the 265-row diagnostic eval view maps
  `observable_clear` to sufficient (`135`), `ambiguous_evidence` to ambiguous
  (`126`), and `unobservable_missing_evidence` to missing (`4`). It is still
  audit-proxy diagnostic material, not paper-level calibrated p_obs/p_rel
  solved evidence. The Q_e v2 schema audit also completed with validation
  errors `0`: blocked field hits `0`, row alignment passed, required Q_e blocks
  are present, train labels are balanced, and ambiguous/missing eval rows are not
  sufficient. The p_obs-only diagnostic smoke test is now complete with
  validation errors `0`: AUROC `1.000000`, ECE@10 `0.049266`, abstain recall
  `1.000000`, and observable false-abstain rate `0.000000`, while the legacy
  all-sufficient baseline has AUROC `0.500000` and abstain recall `0.000000`.
  The p_obs metric review also completed with validation errors `0`: proxy
  shortcut risk is `high` because direct `Q_e state_code` reaches the same
  AUROC `1.000000`, eval `Q_e v2` is audit-proxy material, and the
  missing-evidence slice has only `4` rows. Therefore `p_obs` is not required
  for the current H002 core claim and is demoted to optional diagnostic/future
  evidence; full p_obs/p_rel selective-decision rerun is not justified now.
- Latest H002 C_e improvement path: Docker service
  `h002-ce-improvement-path` produced
  `experiments/H002_compatibility_routing/ce_improvement_path/latest/` with
  validation errors `0` over `762888` source rows. The run evaluated
  hard-negative + structured C_e, route-aware C_e, richer-G_e hard-route
  feasibility, and calibrated C_e. Best primary-route candidate is
  `I4_calibrated_route_aware_source_x_Ce`: compared with current
  `S2_source_x_Ce`, it improves Recall@K by `+0.015873/+0.021542/+0.007937`
  and reduces Violation@K by `-0.008769/-0.010512/-0.014035` at K
  `{10,20,50}`. Internal heldout calibration improves Brier/NLL
  (`0.045925` / `0.139495`) but family-wise caveats remain, especially
  Open3DSG `relative_vertical` Violation. Therefore I4 is a promising
  candidate, not the promoted main score.
- Latest H002 C_e candidate CI/family review: Docker service
  `h002-ce-candidate-ci-family-review` produced
  `experiments/H002_compatibility_routing/ce_candidate_ci_family_review/latest/`
  with validation errors `0` and `1000` bootstrap samples. K=5 point result is
  `S2_current_source_x_Ce` Recall/Violation `0.352608/0.054491` versus
  `I4_calibrated_route_aware_source_x_Ce` `0.358277/0.047554`. Aggregate
  primary-route deltas at K `{5,10,20,50}` are positive for Recall and negative
  for Violation, but K=5 and K=50 Recall CIs include zero, and family-wise
  review finds `5` violation-regression cells plus `1` double-regression cell
  concentrated in Open3DSG `relative_vertical`. Therefore I4 stays a candidate
  ablation/secondary result, and the current main score remains
  `S2_current_source_x_Ce`.
- Latest H002 route-framework protocol: `h002_relation_aware_framework_claim_hierarchy_and_route_protocol`
  is complete. The frozen hierarchy is: relation-aware evidence routing as the
  framework claim, predicate-geometry compatibility as the validated mechanism
  claim, route taxonomy as analysis/diagnostic evidence, and explicit boundary
  wording for unsolved routes. The route-assignment protocol is based on
  evidence requirements, not metric outcomes. The main result table remains
  comparison-route only; route-readiness, support/contact, p_obs/p_rel, and
  semantic/structural routes remain diagnostic/future unless separately
  validated.
- Latest H002 paper-section sync: `h002_route_aware_paper_section_sync_after_protocol_freeze`
  is complete. The frozen hierarchy is now reflected in the H002 paper
  workspace's draft, outline, table captions, figure captions, and risk
  register. The sync adds section-ready introduction/method/experiment/boundary
  text and caption-ready wording without changing metrics, score promotion, or
  route status.
- Latest H002 report: `hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0706.md`.
  Next step is `h002_route_aware_full_draft_plan_after_section_sync`: plan the
  full H002 manuscript expansion from the synced paper workspace.

## Current Status

- Current paper route: AAAI-style manuscript under `paper/aaai/`.
- Latest source-validation build: `logs/h001_aaai_pdf_build_reference_expansion_20260625_130811.log`, exit 0, output `paper/aaai/main_reference_expansion.pdf`.
- PDF status: 9 total pages, references start on page 7, reproducibility checklist page 9. The original `paper/aaai/main.pdf` is preserved.
- Main sources: VL-SAT full official validation and Open3DSG full-validation `recovery_relaxed_views_min2/`.
- Main score: `family_conditional_risk = semantic_score * p_geom_valid_family`.
- Pooled ablation: `probabilistic_recalibrated = semantic_score * p_geom_valid`.
- Geometry-only control: rank by `p_geom_valid` without semantic score.
- Main K grid: `{5, 10, 20, 50, 100}`. K=1 is sanity-check only.
- Qwen-VL is complete as a third-source / modern VLM extension, but it is not part of the main claim unless explicitly promoted.

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
| `family_conditional_risk` | GeoCalib main score |
| `probabilistic_recalibrated` | pooled calibrated-risk ablation |
| `rule_verified_point_subtype` | hard-rule diagnostic |
| `control_p_geom_valid_only` | geometry-only control |
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

Submission/package hygiene:

1. Confirm final OpenReview/AAAI portal form and exact target-year style constraints.
2. Decide artifact/code-release URL or DOI.
3. Decide supplementary/code-data upload policy.
4. Recheck partial/no reproducibility checklist answers.
5. Regenerate any flattened release package created before the low-K and family-main table/prose update.
6. Run final PDF/source sanity checks from the current checkout.

No new main-source metric experiment is required for the current GeoCalib claim.
