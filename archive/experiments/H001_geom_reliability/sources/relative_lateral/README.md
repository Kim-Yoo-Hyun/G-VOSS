# Relative Lateral

This folder tracks the optional H001 relation-family expansion that separates
`left` and `right` from the broader `relative_horizontal` audit.

## Status

- status: `relative_lateral_stopped_as_appendix_future_work_boundary_no_source_metrics`
- labels: `left`, `right`
- GT denominator: 2,264 rows (`left` 1,132 + `right` 1,132)
- current AAAI main claim: unchanged
- source metrics: not run
- promotion: stopped for the current AAAI path

`front` and `behind` are not included here. They are deferred as
`relative_depth_deferred` because the earlier coordinate audit found lower
strict purity and larger ambiguity/contradiction buckets for those labels.

## Frozen Artifact

The policy freeze artifact lives under `policy_freeze/`:

- `manifest.json`: complete status, inputs, family split, denominator, policy,
  provenance, and blockers
- `family_split.json`: `relative_lateral` vs `relative_depth_deferred`
- `denominator.json`: held-out GT denominator and source-row universe counts
- `geometry_policy.json`: selected coordinate frame and row-status rules
- `threshold_provenance.json`: why the thresholds are operational gates, not
  tuned result thresholds
- `calibration_plan.json`: train/dev calibration or policy-lock route before
  any paper-facing source metrics
- `report.md`: human-readable summary

The train/dev policy-lock artifact lives under `train_dev_policy_lock/`:

- `manifest.json`: train/dev scope, gate result, blockers, and claim boundary
- `policy_lock.json`: GT-positive and label-flip counterfactual policy summary
- `calibration_model.json`: train-only univariate logistic calibrator over
  signed lateral margin
- `metrics.json`: train/dev calibration metrics
- `rows.jsonl`: row-level positive/counterfactual decisions
- `report.md`: human-readable summary

The dev failure diagnosis artifact lives under `dev_failure_diagnosis/`:

- `manifest.json`: diagnosis status, inputs, claim boundary, and output map
- `summary.json`: contradiction/uncertain bucket counts and pair-level summary
- `focus_cases.jsonl`: all dev contradiction/uncertain rows and counterfactual mirrors
- `examples.jsonl`: capped representative examples per bucket
- `report.md`: human-readable diagnosis

## Current Interpretation

The lateral-only evidence is stronger than the full `relative_horizontal`
family: the selected frame is `scan_left_neg_x_front_neg_y`, strict purity is
0.8005, strict eligible share is 0.6466, inverse consistency is inherited as
1.0, and the distinct-left-axis wrong-frame gap is 0.0998. This is enough to
freeze a candidate policy, but not enough to update the main AAAI claim.

Current decision: stop this track as appendix/future-work boundary evidence.
Do not run paper-facing VL-SAT/Open3DSG lateral source metrics from the current
strict policy. Any future revival requires a separate predeclared
frame/annotation study rather than tuning the frozen validation policy.

## Train/Dev Policy Lock

Docker `relative_lateral_train_dev_policy_lock` completed on 2026-06-06 KST.
It uses only train/dev GT annotations and left/right label-flip
counterfactuals. It does not read VL-SAT/Open3DSG predictions and does not
change the paper claim.

Result:

- status: `relative_lateral_train_dev_policy_lock_ready_with_caveats_no_source_metrics`
- decision rows: 3,832 = 1,916 GT positives + 1,916 label-flip counterfactuals
- train positives: 1,538 rows; strict purity 0.8738; lenient nonviolated rate 0.9168
- dev positives: 378 rows; strict purity 0.6975; lenient nonviolated rate 0.8095
- dev counterfactuals: 378 rows; strict negative purity 0.6975; lenient nonsatisfied rate 0.8095
- train-only calibrator: fit on 3,076 rows; train AUROC 0.8913; dev AUROC 0.7401
- gate: failed the dev strict-purity checks

Interpretation:

- The train side supports the frozen lateral policy, and the dev side still has
  nontrivial signal under lenient treatment of uncertain rows.
- The dev strict gate does not pass, so this family is not ready for
  paper-facing VL-SAT/Open3DSG lateral source metrics unless it is explicitly
  kept as caveated appendix evidence.
- The next technical step is dev failure diagnosis of strict contradictions and
  uncertain rows without changing held-out validation policy.

## Dev Failure Diagnosis

Docker `relative_lateral_dev_failure_diagnosis` completed on 2026-06-06 KST.
It reads only `train_dev_policy_lock/rows.jsonl`, changes no policy, reads no
source predictions, and computes no source metrics.

Result:

- status: `relative_lateral_dev_failure_diagnosis_ready_no_policy_change_no_source_metrics`
- dev GT-positive rows: 378
- positive strict contradiction rows: 72 rows, but only 36 physical pairs
- positive uncertain rows: 140 rows, but only 70 physical pairs
- contradiction counterfactual mirrors: 72 rows / 36 physical pairs
- uncertain counterfactual mirrors: 140 rows / 70 physical pairs
- strict contradiction scan concentration: all 72 positive contradiction rows
  come from two dev scans
- strict contradiction same-label share: 0.5278
- uncertain same-label share: 0.4857

Interpretation:

- Strict contradictions are symmetric left/right pair-level sign conflicts, not
  random row noise.
- Contradictions are highly concentrated in two scans and often involve repeated
  same-label object pairs such as `pillow`-`pillow` or `box`-`box`.
- Most uncertain rows are caused by `conflicting_axis_dominates`, meaning the
  object pair is more separated along the orthogonal/front-back axis than along
  the lateral axis under the frozen scan frame.
- This supports treating `relative_lateral` as a coordinate/frame-orientation
  boundary case. It should not be promoted without a separate predeclared
  frame/annotation study or explicit caveated appendix framing.

## Stop Decision

Decision date: 2026-06-06 KST.

Final current-path decision:

- Stop `relative_lateral` as an AAAI main-claim expansion.
- Keep the artifacts as appendix/future-work boundary evidence.
- Do not run source metrics because the train/dev strict gate is caveated.
- Do not tune the validation policy to make dev pass.
- If this family is revisited later, start a separate predeclared
  frame/annotation study focused on repeated same-label objects and scan-frame
  versus viewpoint-frame semantics.

Why it did not work for the current main claim:

- The held-out coordinate audit had a promising lateral-only signal, but that
  split was derived after seeing the broader held-out `relative_horizontal`
  audit.
- The train side supports the frozen policy, but dev strict purity drops to
  0.6975.
- Dev strict contradictions are pair-symmetric, concentrated in two scans, and
  often involve same-label object pairs.
- Dev uncertain rows are mostly orthogonal-axis-dominance cases, so the issue is
  coordinate/frame semantics rather than a source-prediction metric problem.
