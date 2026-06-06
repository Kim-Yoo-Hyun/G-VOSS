# Attachment Deferred Expansion Track

Last updated: 2026-06-06 KST

Status: `attachment_deferred_g5d_full_source_metrics_ready`

This folder tracks the optional `attachment_deferred` expansion path for H001.
It is not part of the current AAAI main claim. It is the preferred next
relation-family expansion if the paper strategy pivots beyond the current
`support_contact`, `proximity`, and `relative_vertical` scope.

Consolidated relation expansion status is tracked in
`../relation_expansion_status.md`.

## Motivation

The current H001 denominator has 2,545 in-scope GT rows:

- `support_contact`: 1,199
- `proximity`: 1,128
- `relative_vertical`: 218

The `attachment_deferred` family adds 967 GT rows:

- `attached to`: 808
- `hanging on`: 126
- `connected to`: 33

If validated, the geometry-checkable denominator would expand from 2,545 to
3,512 GT rows. This is a smaller expansion than `relative_horizontal`, but it
fits H001's physical-consistency thesis better because attachment, hanging, and
connection imply contact, near-surface support, orientation, gravity, and object
affordance constraints.

Current source-row availability:

- VL-SAT prediction rows: 77,748
- Open3DSG prediction rows: 57,300

## Completed Scope Audit

Docker `attachment_deferred_scope_audit` completed on 2026-05-28 KST. This is
a no-training, no-inference planning audit, not a verifier and not source-metric
evidence.

Outputs:

- `scope_audit/manifest.json`
- `scope_audit/label_counts.json`
- `scope_audit/evidence_schema.json`
- `scope_audit/report.md`

Result summary:

- status: `attachment_deferred_scope_schema_ready_no_metric_execution`
- current H001 GT denominator: 2,545
- `attachment_deferred` GT rows: 967
- expanded candidate denominator if validated: 3,512 / 7,505
- source candidate rows: VL-SAT 77,748; Open3DSG 57,300
- existing geometry verification status: `unsupported` for both sources
- then-next gate: `G1_attachment_evidence_extractor_design` (now completed)

The scope audit freezes the first evidence-schema plan: reuse OBB
distance/overlap and segmented point evidence where available, add
attachment-specific surface/contact/normal/gravity fields before any verifier,
keep object affordance as optional context rather than proof, and preserve
exact predicate-label recall for `attached to`, `hanging on`, and
`connected to`.

## Completed G1 Extractor Contract

Docker `attachment_deferred_extractor_contract` completed on 2026-05-28 KST.
This is an extractor design and output-contract artifact only. It does not read
point clouds, assign `verification_status`, fit `p_geom_valid`, re-rank
predictions, or run metrics.

Outputs:

- `evidence_extractor/manifest.json`
- `evidence_extractor/extractor_contract.json`
- `evidence_extractor/output_schema.json`
- `evidence_extractor/field_catalog.json`
- `evidence_extractor/subtype_policy.json`
- `evidence_extractor/extraction_plan.json`
- `evidence_extractor/validation_plan.json`
- `evidence_extractor/example_row.json`
- `evidence_extractor/commands.md`
- `evidence_extractor/report.md`

Result summary:

- status: `attachment_deferred_extractor_contract_ready_no_extraction`
- required evidence groups: identity, OBB evidence, local point contact,
  surface candidates/normals, gravity cues, contradictory support cues, and
  affordance context
- forbidden extractor outputs: `verification_status`, `p_geom_valid`, recall
  credit, and reranking scores
- subsequent gate: `G1b_attachment_evidence_extractor_dry_run` (now completed)

## Completed G1b Extractor Dry Run

Docker `attachment_deferred_extractor_dry_run` completed on 2026-05-28 KST.
This is a small evidence-only dry run, not a verifier, not calibration, not
source metrics, and not current paper evidence.

Outputs:

- `extractor_dry_run/rows.jsonl`
- `extractor_dry_run/manifest.json`
- `extractor_dry_run/summary.json`
- `extractor_dry_run/validation.json`
- `extractor_dry_run/report.md`

Result summary:

- status: `attachment_deferred_extractor_dry_run_ready_no_verifier`
- input/output rows: 36 / 36
- validation errors: 0
- source rows: 9 `gt_positive`, 9 `counterfactual`, 9 `vlsat_closed_set`,
  and 9 `open3dsg_ov`
- label rows: 12 each for `attached to`, `hanging on`, and `connected to`
- extractor status: all 36 rows are `partial`
- forbidden verifier/metric fields are absent
- subsequent gate: `G1c_attachment_point_surface_estimator_validation` (now completed)

The dry run used semseg OBB and `dominantNormal` proxies only. Its `partial`
status is now superseded by G1c point/surface validation, but the G1b artifact
still cannot support verifier promotion or source metrics by itself.

## Completed G1c Point/Surface Validation

Docker `attachment_deferred_point_surface_validation` completed on 2026-05-28
KST. This is segmented-point and surface-normal estimator validation, not a
verifier, not calibration, not source metrics, and not current paper evidence.

Outputs:

- `point_surface_validation/rows.jsonl`
- `point_surface_validation/diagnostics.jsonl`
- `point_surface_validation/manifest.json`
- `point_surface_validation/summary.json`
- `point_surface_validation/validation.json`
- `point_surface_validation/report.md`

Result summary:

- status: `attachment_deferred_point_surface_validation_ready_no_verifier`
- input/output rows: 36 / 36
- validation errors: 0
- ready rows: 36
- point available rows: 36
- normal available rows: 36
- near-contact rows: 27 under the 0.05m diagnostic threshold
- surface normal classes: 14 `horizontal_up`, 21 `vertical`, 1 `slanted`
- forbidden verifier/metric fields are absent
- subsequent gate: `G2_attachment_verifier_policy_design` (now completed)

The validation uses `labels.instances.annotated.v2.ply` segmented points,
deterministic point sampling for large endpoint objects, pairwise point-distance
diagnostics, contact-patch proxy, and PCA surface-normal estimation. It still
does not emit `satisfied`, `violated`, `uncertain`, `p_geom_valid`, recall
credit, or reranking scores.

## Completed G2 Verifier Policy

Docker `attachment_deferred_verifier_policy` completed on 2026-05-28 KST. This
is a conservative verifier-policy design artifact, not a verifier run, not
calibration, not source metrics, and not current paper evidence.

Outputs:

- `verifier_policy/manifest.json`
- `verifier_policy/verifier_policy.json`
- `verifier_policy/decision_schema.json`
- `verifier_policy/threshold_plan.json`
- `verifier_policy/reason_codes.json`
- `verifier_policy/calibration_plan.json`
- `verifier_policy/commands.md`
- `verifier_policy/report.md`

Result summary:

- status: `attachment_deferred_verifier_policy_ready_no_decisions_no_metrics`
- subtypes covered: 9
- near-contact default: 0.05m
- uncertain contact band: 0.05-0.15m
- clear-far distance: 0.30m
- min near-contact points for satisfied: 3
- min contact patch score for satisfied: 0.20
- decision rows emitted: false
- calibration fitted: false
- source predictions scored: false
- metrics computed: false
- subsequent gate: `G3_attachment_calibration_counterfactual_generation` (now completed)

The policy defines future `satisfied`, `violated`, and `uncertain` logic, with
guardrails that ambiguous functional cases default to `uncertain`, class
affordance is never proof, and `violated` requires clear negative geometry.

## Completed G3 Calibration / Counterfactual Route

Docker `attachment_deferred_calibration_counterfactuals` completed on
2026-05-28 KST. This is a train-dev calibration/counterfactual route-freeze
artifact, not a verifier run, not a fitted calibrator, not source metrics, and
not current paper evidence.

Outputs:

- `calibration_counterfactuals/manifest.json`
- `calibration_counterfactuals/positive_seeds.jsonl`
- `calibration_counterfactuals/counterfactual_seeds.jsonl`
- `calibration_counterfactuals/split_plan.json`
- `calibration_counterfactuals/counterfactual_plan.json`
- `calibration_counterfactuals/policy_smoke_plan.json`
- `calibration_counterfactuals/gt_eval_inputs.json`
- `calibration_counterfactuals/threshold_freeze_protocol.json`
- `calibration_counterfactuals/commands.md`
- `calibration_counterfactuals/report.md`

Result summary:

- status:
  `attachment_deferred_calibration_counterfactual_plan_ready_no_fit_no_metrics`
- train/dev positive seeds: 315 rows
- counterfactual negative seeds: 446 rows
- positive labels: `attached to` 269, `hanging on` 40, `connected to` 6
- counterfactual strategies: `far_object_pair` 274,
  `wrong_surface_replacement` 86, `floor_support_replacement_for_hanging` 40,
  `gravity_inconsistent_hanging` 40, `wrong_pair_attachment` 6
- held-out scan overlap: 0
- warning: dev split has no `connected to` positive seed, so any future
  family-specific connected-to calibrator claim requires pooled calibration,
  augmented dev selection, or an explicit limitation
- subsequent gate: `G4_attachment_gt_verifier_evaluation_and_policy_smoke`
  (now completed as `gt_policy_smoke`)

The counterfactual rows are seeds that require geometry-margin validation before
becoming calibration negatives. They are not absent-edge negatives and cannot
be reported as source metrics.

## Completed G4 GT Policy Smoke

Docker `attachment_deferred_gt_policy_smoke` completed on 2026-05-28 KST. This
applies the frozen G2 policy to G1c smoke evidence and to G3 train/dev
positive/counterfactual seeds after point/surface evidence extraction. It is
not a fitted calibrator, not source metric evidence, not controls/bootstrap,
and not part of the current AAAI main claim.

Outputs:

- `gt_policy_smoke/manifest.json`
- `gt_policy_smoke/summary.json`
- `gt_policy_smoke/validation.json`
- `gt_policy_smoke/policy_smoke_decisions.jsonl`
- `gt_policy_smoke/gt_evidence_rows.jsonl`
- `gt_policy_smoke/gt_evidence_diagnostics.jsonl`
- `gt_policy_smoke/gt_policy_decisions.jsonl`
- `gt_policy_smoke/gt_eval_rows.jsonl`
- `gt_policy_smoke/visual_sanity_plan.json`
- `gt_policy_smoke/commands.md`
- `gt_policy_smoke/report.md`

Result summary:

- status: `attachment_deferred_gt_policy_smoke_ready_no_source_metrics`
- policy-smoke decision rows: 36/36, schema validation passed
- train/dev seed decision rows: 761/761, schema validation passed
- point/surface evidence ready rows: 761/761, scan errors 0
- positive rows: 315
- counterfactual rows: 446
- positive nonviolated rate: 0.9048
- positive strict satisfied rate: 0.3841
- counterfactual nonsatisfied rate: 0.8274
- counterfactual strict violated rate: 0.4574
- calibration-ready counterfactual negatives: 204/446
- uncertain rate across all train/dev rows: 0.4323

Interpretation:

- The policy/evidence plumbing is now functional at train/dev scale.
- The high uncertain rate and nontrivial false-violation/false-satisfaction
  rates mean this is not ready for main-claim promotion.
- No `p_geom_valid` calibrator is fitted yet, and no VL-SAT/Open3DSG source
  predictions are scored.
- Adding this family to the main AAAI claim requires explicit final user
  confirmation after the remaining evidence gates pass.

## Completed G4b Error / Visual Sanity Planning

Docker `attachment_deferred_error_visual_sanity` completed on 2026-05-28 KST.
This reads the G4 policy-smoke output, separates false-violation,
false-satisfaction, and uncertain-heavy cases, and freezes a targeted visual
sanity queue before any attachment source metrics. It is not a fitted
calibrator, not source metric evidence, not controls/bootstrap, and not part of
the current AAAI main claim.

Outputs:

- `error_visual_sanity/manifest.json`
- `error_visual_sanity/summary.json`
- `error_visual_sanity/review_cases.jsonl`
- `error_visual_sanity/visual_queue.jsonl`
- `error_visual_sanity/calibration_filter.jsonl`
- `error_visual_sanity/guide.md`
- `error_visual_sanity/commands.md`
- `error_visual_sanity/report.md`

Result summary:

- status: `attachment_deferred_error_visual_sanity_plan_ready_no_source_metrics`
- review cases: 436
- visual queue rows: 50
- calibration-filter rows: 761
- strict positive candidates: 121
- strict negative candidates: 204
- false-satisfied counterfactuals: 77
- false-violated positives: 30
- uncertain positives: 164
- uncertain counterfactuals: 165
- queue label coverage: `attached to` 38, `connected to` 6, `hanging on` 6

Interpretation:

- Source metrics remain blocked.
- False-satisfied counterfactuals should be excluded or reviewed before
  negative calibration.
- False-violated positives need visual review before changing policy
  thresholds or excluding positives.
- Uncertain rows should stay out of strict calibration unless a separate
  soft-label protocol is defined.
- Adding this family to the main AAAI claim still requires explicit final user
  confirmation after the remaining evidence gates pass.

## Completed G4c Strict Filter Freeze

Docker `attachment_deferred_strict_filter_freeze` completed on 2026-05-28 KST.
This freezes a strict-only calibration subset from the G4b calibration-filter
dispositions. It includes only GT-positive rows that the policy strictly
satisfies and counterfactual rows that the policy strictly violates. It is not a
fitted calibrator, not source metric evidence, not controls/bootstrap, and not
part of the current AAAI main claim.

Outputs:

- `strict_filter_freeze/manifest.json`
- `strict_filter_freeze/summary.json`
- `strict_filter_freeze/freeze_policy.json`
- `strict_filter_freeze/strict_calibration_rows.jsonl`
- `strict_filter_freeze/excluded_rows.jsonl`
- `strict_filter_freeze/commands.md`
- `strict_filter_freeze/report.md`

Result summary:

- status: `attachment_deferred_strict_filter_frozen_no_fit_no_source_metrics`
- strict calibration rows: 325
- strict positives: 121
- strict negatives: 204
- excluded non-strict rows: 436
- strict label counts: `attached to` 200, `hanging on` 113, `connected to` 12
- strict split counts: train 242, dev 83
- warning: `connected to` has no dev strict rows

Interpretation:

- Source metrics remain blocked.
- Pooled attachment calibration is now complete from strict rows.
- Family-specific `connected to` calibration needs pooled calibration,
  augmented dev selection, or an explicit limitation.
- Visual labels remain useful for a soft-label protocol, but are no longer
  required for the strict-only calibration route.
- Adding this family to the main AAAI claim still requires explicit final user
  confirmation after the remaining evidence gates pass.

## Completed G5a Pooled Strict Calibration Fit

Docker `attachment_deferred_calibration_fit` completed on 2026-05-28 KST. This
fits a pooled `p_geom_valid` model from the G4c strict-only calibration rows.
It is not source metric evidence, not controls/bootstrap, and not part of the
current AAAI main claim.

Outputs:

- `calibration_fit/manifest.json`
- `calibration_fit/model.json`
- `calibration_fit/metrics.json`
- `calibration_fit/scores.jsonl`
- `calibration_fit/commands.md`
- `calibration_fit/report.md`

Result summary:

- status: `attachment_deferred_calibration_fit_ready_no_source_metrics`
- model id: `h001-attachment-deferred-p-geom-valid-strict-v1`
- train rows: 242
- dev rows: 83
- train positives/negatives: 94 / 148
- dev positives/negatives: 27 / 56
- dev Brier/NLL/ECE: 0.0010 / 0.0077 / 0.0071
- dev AUROC/AUPRC: 1.0 / 1.0
- baseline dev Brier/NLL/ECE:
  - constant train prior: 0.2235 / 0.6394 / 0.0631
  - label train prior: 0.2194 / 0.6304 / 0.0325
- warnings:
  - `connected_to_dev_absent_use_pooled_or_train_only_caveat`
  - `strict_subset_nearly_separable_not_source_metric_evidence`

Interpretation:

- The pooled strict calibration path is now executable and frozen before
  source metrics.
- The near-perfect dev scores should not be used as result evidence. They are
  expected on a policy-selected strict subset and only show that the strict
  rows are separable under the frozen features.
- `connected to` remains a caveated label because no dev strict rows exist.
- Source predictions still need attachment evidence extraction, p_geom scoring,
  metrics, controls, bootstrap CI, and audit before this family can be promoted.
- Adding this family to the main AAAI claim still requires explicit final user
  confirmation after the remaining evidence gates pass.

## Completed G5b Source Scoring Preflight

Docker `attachment_deferred_source_scoring_preflight` completed on
2026-05-28 KST. This runs bounded source evidence extraction and `p_geom_valid`
scoring for VL-SAT and Open3DSG using the G5a fitted model. It is a preflight
only: it does not compute source metrics, controls, bootstrap CI, full-source
scoring, or any current AAAI main-claim update.

Outputs:

- `source_scoring_preflight/manifest.json`
- `source_scoring_preflight/summary.json`
- `source_scoring_preflight/source_rows.jsonl`
- `source_scoring_preflight/evidence_rows.jsonl`
- `source_scoring_preflight/diagnostics.jsonl`
- `source_scoring_preflight/scored_rows.jsonl`
- `source_scoring_preflight/commands.md`
- `source_scoring_preflight/report.md`

Result summary:

- status: `attachment_deferred_source_scoring_preflight_ready_no_metrics`
- selected source rows: 120
- source counts: 60 `vlsat_closed_set`, 60 `open3dsg_ov`
- label counts: `attached to` 40, `connected to` 40, `hanging on` 40
- selected unique scans: 20 for VL-SAT and 20 for Open3DSG
- evidence rows ready: 120/120
- validation errors: 0
- mean/median `p_geom_valid`: 0.3610 / 0.0580
- full source scope remains unscored: VL-SAT 77,748 rows and Open3DSG 57,300 rows

Interpretation:

- The source evidence extraction and fitted-calibrator scoring contract works
  for both reproduced sources.
- The selected rows are scan-diverse but still bounded preflight rows; they are
  not representative source-result metrics.
- Unknown model categories appear for rare source evidence values
  (`surface_type=ceiling`, `surface_type=fixture`, and
  `subtype_hint=hanging_from_overhead_or_fixture`), so the full-source protocol
  should record unknown-category handling before metrics.
- Source metrics, controls, bootstrap CI, and audit remain blocked until a
  full-source scoring/metric protocol is frozen.
- Adding this family to the main AAAI claim still requires explicit final user
  confirmation after the remaining evidence gates pass.

## Completed G5c Full-Source Protocol Freeze

Docker `attachment_deferred_full_source_protocol` completed on 2026-05-28 KST.
This freezes the full-source scoring, denominator, sharding, metric-condition,
and control-order protocol before any attachment source metric is run. It is
not source metric evidence and does not change the current AAAI main claim.

Outputs:

- `full_source_protocol/manifest.json`
- `full_source_protocol/protocol.json`
- `full_source_protocol/denominator_audit.json`
- `full_source_protocol/shards.jsonl`
- `full_source_protocol/validation.json`
- `full_source_protocol/commands.md`
- `full_source_protocol/report.md`

Result summary:

- status: `attachment_deferred_full_source_protocol_frozen_no_metrics`
- validation errors: 0
- expected full-source rows: 135,048
- deterministic shards: 69 with 2,000 rows per shard
- global attachment exact-label GT denominator: 967
- VL-SAT covered exact-label denominator: 967/967
- Open3DSG covered exact-label denominator: 768/967
- Open3DSG missing exact-label GT rows: 199 (`attached to` 159,
  `connected to` 5, `hanging on` 35)
- frozen metric conditions: `semantic_only`, `probabilistic_recalibrated`,
  `rule_verified_attachment_policy`, `control_p_geom_valid_only`,
  `control_distance_only`, `control_shuffled_geometry`, and
  `control_wrong_pair_geometry`

Interpretation:

- The attachment expansion now has a metric-free guardrail before any
  full-source result can be inspected.
- Recall must use a source-specific covered exact-label denominator while also
  reporting the global 967-row candidate denominator.
- Open3DSG attachment results, if run later, must carry the 768/967 coverage
  caveat and cannot be compared to VL-SAT without that denominator caveat.
- `connected to` still has no dev strict rows; pooled calibration is allowed
  for scoring, but a label-specific connected-to calibration claim is blocked.
- Full-source scoring, source metrics, controls, bootstrap CI, and visual/failure
  audit still do not exist.

## Why This Is Stronger Than Relative Horizontal

`relative_horizontal` has a larger denominator, but its meaning depends heavily
on coordinate-frame or annotator-viewpoint convention. The current audit found
nontrivial signal but blocked promotion because `front`/`behind` remains
ambiguous.

`attachment_deferred` is smaller but more aligned with the H001 failure
mechanism:

- a relation can be semantically plausible while physically unsupported;
- attachment should usually require object/surface adjacency or contact;
- hanging should respect gravity and near-wall/ceiling support;
- connection should have spatial adjacency and often class/part affordance.

The risk is complexity, not conceptual fit. Attachment requires richer evidence
than support/contact: wall/ceiling/furniture surface type, local point contact,
surface normals, hanging geometry, and object affordance cues.

## Claim Boundary

Allowed now:

- Treat `attachment_deferred` as the preferred next physical-relation expansion
  after the current AAAI path.
- Use it to motivate how H001 could move from pure spatial consistency toward
  simple functional precondition reasoning.
- Record denominator, source-row availability, and required gates.

Blocked now:

- Do not add `attachment_deferred` to the current AAAI main claim.
- Do not claim functional relation reasoning as solved.
- Do not promote source metrics until full-source scoring, controls, bootstrap
  CI, failure analysis, and audit gates are completed.

## Upgrade Steps

G0. Scope audit

- Freeze predicate mapping: `attached to`, `hanging on`, `connected to`.
- Confirm GT denominator, per-label counts, source prediction rows, and covered
  object-pair geometry fields for VL-SAT and Open3DSG.
- Keep exact predicate-label recall; do not collapse labels into a family-level
  recall match.
- Status: completed as Docker no-training/no-inference scope/schema audit.

G1. Attachment evidence extractor contract

- Add surface evidence: floor/wall/ceiling/furniture candidate support surface,
  local surface normal, object-to-surface distance, projected overlap, and local
  point contact.
- Add gravity/orientation evidence for `hanging on`: object above/beside support
  surface, near vertical plane or ceiling, and no contradictory floor-support
  explanation.
- Add adjacency/continuity evidence for `connected to`: very small distance,
  local overlap/contact, and optional class-pair affordance cues.
- Record `uncertain` cases explicitly when mesh/point evidence is missing or the
  relation is likely functional rather than visible physical contact.
- Status: completed as Docker design/contract artifact. No extractor
  implementation, verifier, calibration, or metric run exists yet.

G1b. Extractor dry run

- Implement an evidence-only extractor that emits rows matching
  `evidence_extractor/output_schema.json`.
- Validate row preservation and schema compliance on a small GT/counterfactual
  dry run before any verifier policy.
- Keep `verification_status`, `p_geom_valid`, recall credit, and reranking
  scores out of the extractor output.
- Status: completed as Docker evidence-only dry run. It produced only `partial`
  rows because point-contact evidence was outside G1b; G1c later added the
  point/surface validation layer.

G1c. Point/surface estimator validation

- Replace the OBB-only proxy with validated point-contact and surface-candidate
  evidence where segmented points are available.
- Validate near-contact count, contact patch proxy, surface type, and normal
  class before any `satisfied` / `violated` policy is written.
- Status: completed as Docker point/surface estimator validation. It produced
  36/36 ready evidence rows with no verifier/metric fields.

G2. Verifier policy

- Define `satisfied`, `violated`, and `uncertain` for each subtype:
  `attached_to_surface`, `hanging_from_surface`, `connected_adjacent`.
- Use conservative violation rules first. For example, mark violated only when
  the object is clearly far from any plausible support/attachment surface or the
  support surface type contradicts the predicate.
- Avoid making class affordance alone a proof of physical validity.
- Status: completed as Docker policy-design artifact. No decision rows,
  calibration, source scoring, or metrics were emitted.

G3. Calibration and counterfactuals

- Build train-dev positives and counterfactual negatives before held-out source
  metrics.
- Suggested negatives: wrong surface, far object pair, shuffled geometry,
  wrong-pair attachment, floor-support replacement for wall-hanging cases, and
  gravity-inconsistent hanging cases.
- Freeze thresholds and calibrator artifacts before held-out metrics.
- Status: completed as Docker route-freeze artifact. It produced 315 positive
  seeds and 446 counterfactual negative seeds, with no verifier application,
  calibration fit, source scoring, or metrics.

G4. GT verifier evaluation and visual sanity

- Run GT-positive/counterfactual verifier evaluation.
- Add a targeted visual sanity check for attachment/hanging cases, because
  surface contact can be visually and geometrically subtle.
- Record whether failures are due to annotation noise, missing mesh/points,
  surface-normal errors, or genuinely bad verifier policy.
- Status: policy-smoke and train/dev GT/counterfactual evaluation are complete
  as Docker `gt_policy_smoke`. Targeted visual sanity/error inspection is now
  completed as G4b planning; strict-only filter freeze is completed as G4c.

G4b. Error / visual sanity planning

- Inspect false-violated positives, false-satisfied counterfactuals, and
  uncertain-heavy subtypes.
- Generate a targeted visual sanity queue and calibration-filter disposition
  table before fitting any attachment calibrator.
- Status: completed as Docker `error_visual_sanity`. It produced 436 review
  cases, a label-diverse 50-row visual queue, and 761 calibration-filter rows.

G4c. Strict calibration-filter freeze

- Freeze a strict-only calibration subset before any source metrics.
- Include only `use_as_strict_positive` and `use_as_strict_negative` rows.
- Exclude false-satisfied counterfactuals, false-violated positives, and
  uncertain rows unless a later visual-label soft protocol is defined.
- Status: completed as Docker `strict_filter_freeze`. It produced 325 strict
  calibration rows and 436 excluded rows. `connected to` has no dev strict rows,
  so family-specific calibration needs pooled calibration, augmented dev
  selection, or an explicit caveat.

G5. Source-result metrics

- G5a status: completed as Docker `attachment_deferred_calibration_fit`. It
  fits pooled strict calibration from G4c rows and emits no source metrics.
- G5b status: completed as Docker `attachment_deferred_source_scoring_preflight`.
  It scores 120 bounded source rows and emits no source metrics.
- G5c status: completed as Docker `attachment_deferred_full_source_protocol`.
  It freezes 69 full-source shards, source-specific covered denominators, output
  schema, metric conditions, and control order while emitting no source metrics.
- G5d status: completed as Docker `attachment_deferred_full_source_g5d`.
  A 1-shard smoke run completed successfully, then its intermediate output/log
  was deleted after the full run became the source of truth. The full run
  completed with exit 0 at `logs/h001_attachment_g5d_full_20260606_113803.log`;
  output path is
  `experiments/H001_geom_reliability/sources/attachment_deferred/full_source_g5d/`.
  Full run counts: 69/69 shards, 135,048 scored source rows, validation errors
  0, and 300 failure rows.
- Report `R@K`, `Violation@K`, recall retention, exact-label denominator, and
  per-subtype family rows.
- Compare semantic-only, probabilistic calibrated, rule-verified, family-specific
  calibrated, geometry-only, distance/contact-only, shuffled-geometry, and
  wrong-pair controls.
- Do not promote `attachment_deferred` to the main AAAI claim without explicit
  final user confirmation after G5d outputs and any required failure/visual audit
  are reviewed.

G5d key source-result summary:

- VL-SAT denominator: 967/967; missing exact-label GT rows: 0.
  - `semantic_only` R@100/V@100: 1.0000 / 0.2126
  - `probabilistic_recalibrated` R@100/V@100: 0.9979 / 0.2210
  - `rule_verified_attachment_policy` R@100/V@100: 0.9380 / 0.0215
- Open3DSG denominator: 768/967; missing exact-label GT rows: 199.
  - `semantic_only` R@100/V@100: 0.9297 / 0.3021
  - `probabilistic_recalibrated` R@100/V@100: 0.6628 / 0.2460
  - `rule_verified_attachment_policy` R@100/V@100: 0.9245 / 0.0842
- Warning: `connected to` has no dev strict rows, so use pooled calibration or
  an explicit caveat; do not claim label-specific connected-to calibration.

Subrelation opportunity assessment:

- `hanging on` is the most promising future targeted relation. It is physically
  meaningful for H001 because it has gravity/orientation/contact semantics, and
  G5d preserves R@100 under `rule_verified_attachment_policy` for both VL-SAT
  126/126 and Open3DSG 91/91. Its denominator is modest, so it is better as a
  focused extension or case study than as a broad main-claim expansion by itself.
- `attached to` has the largest denominator, but it is also the noisiest
  subtype. It remains useful for future work, but the Open3DSG probabilistic
  route drops recall substantially and the policy needs stronger visual/failure
  audit before main-claim use.
- `connected to` looks clean in source recall, but the denominator is very small
  and the train/dev strict split has no dev positives. Treat it as caveated
  support evidence, not a standalone claim.

Why this is not promoted now:

- This track did not fail in the same way as `relative_horizontal` or
  `relative_lateral`; it is the most promising future physical-relation upgrade.
- It is still not current main-claim evidence because Open3DSG covers only
  768/967 exact-label GT rows, leaving 199 missing exact-label GT rows.
- `attached to` is the largest subtype but also the noisiest; Open3DSG
  probabilistic recall drops sharply for this label.
- `connected to` has no dev strict rows, so label-specific calibration would be
  under-supported without pooled calibration or an explicit caveat.
- A failure/visual audit is still needed before adding it to the AAAI main
  claim.
- Any main-claim promotion requires explicit final user confirmation.

G6. Function-reasoning pilot

- Optional after relation-level metrics pass.
- Keep it as a small case study unless a separate benchmark is introduced.
- Show simple physical precondition questions such as whether an object is
  plausibly wall-mounted, hanging, or physically connected based on the verified
  relation edge.
- Use this to motivate actionable/function-aware 3D scene graphs, not to claim
  general affordance or robotics task performance.

G7. Promotion gate

- Promote to the main claim only if the family reaches the same evidence level
  as the current H001 families: verifier policy, calibration, GT verifier
  evaluation, two source metrics, controls, bootstrap CI, and failure/audit
  evidence.
- Even after these gates pass, ask the user for explicit final confirmation
  before adding `attachment_deferred` to the main AAAI claim.

## Recommended Paper Strategy

Current AAAI path:

- Keep the main claim scoped to `support_contact`, `proximity`, and
  `relative_vertical`.
- Mention `attachment_deferred` only as the most plausible next physical-relation
  expansion, not as current metric evidence.

If upgrading H001:

1. Add `attachment_deferred` before retrying `relative_horizontal`.
2. Start from the completed scope audit, G1 extractor contract, G1b dry run,
   G1c point/surface validation, G2 verifier policy, and G3
   calibration/counterfactual route.
3. Run a GT/counterfactual verifier evaluation and policy smoke from the frozen
   G3 inputs. This is complete.
4. Inspect false violations, false satisfactions, and uncertain-heavy subtypes;
   create a targeted visual sanity queue. This is complete as G4b.
5. Label the queue or freeze a strict-only calibration filter. The strict-only
   filter is complete as G4c.
6. Fit pooled strict calibration. This is complete as G5a.
7. Run bounded source evidence extraction/scoring preflight. This is complete
   as G5b.
8. Freeze the full-source scoring/metric protocol, including sharding/runtime
   budget, denominator handling, unknown-category handling, and control order.
   This is complete as G5c.
9. Run full-source scoring plus VL-SAT/Open3DSG source metrics and controls.
   This is complete as G5d.
10. Add function-reasoning only as a secondary pilot after relation reliability
   is established.
