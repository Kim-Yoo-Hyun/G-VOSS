# Hypothesis

Last updated: 2026-04-30

## Hypothesis Statement

H001: For geometry-checkable 3DSSG relation families, adding explicit 3D geometry evidence and verification to candidate semantic relation edges will reduce geometry-inconsistent relation predictions while preserving useful predicate/triplet recall.

## Validation Phases

H001 should be evaluated in phases. The current one-scan path is a sanity check, not the final hypothesis test.

Phase A: Evidence export sanity check.

- Input: ground-truth 3DSSG relation tuples for one validated scan.
- Goal: confirm that each relation edge can be joined with object geometry and exported with explicit evidence.
- This phase does not test prediction recall or model performance.

Phase B: Ground-truth verifier sanity check.

- Input: ground-truth 3DSSG relation tuples plus `h001-rules-v0`.
- Goal: inspect whether rule outputs are plausible for geometry-checkable predicate families.
- This phase can report geometry availability, violation candidates, uncertain cases, and manual inspection results.
- This phase still does not establish that prediction reliability improves.

Phase C: Point-level support/contact smoke test.

- Input: support/contact edges plus `labels.instances.annotated.v2.ply` object points.
- Goal: check whether local support-surface evidence recovers OBB-only support/contact failures.
- This phase still does not establish prediction-level H001 performance.

Phase D: Prediction-level evaluation.

- Input: relation predictions from a closed-set or open-vocabulary baseline.
- Goal: measure violation rate, consistency-filtered recall, and predicate/triplet recall tradeoff before and after geometry verification.
- H001 is only directly tested as a prediction reliability claim in this phase.
- Protocol: `16_evaluation.md`.

## Independent Variable

Whether relation edges are evaluated with explicit geometry evidence.

Conditions:

- Semantic relation only.
- Semantic relation plus geometry evidence.
- Semantic relation plus geometry evidence and verification/recalibration.

## Dependent Variables

- Predicate R@K / mR@K.
- Triplet R@K / mR@K.
- Geometry consistency score.
- Violation rate.
- Consistency-filtered recall.
- Tail or zero-shot predicate performance if candidate predictions are available.

## Expected Effect

Inference:

- Support/contact and proximity predicates should show the clearest reduction in violation rate.
- Relative-position predicates may improve only if coordinate-frame definitions are handled explicitly.
- Some recall may drop after filtering invalid edges; this is acceptable if the violation reduction is large and the tradeoff is reported clearly.

## Falsification Condition

H001 is weakened or falsified if:

- geometry evidence does not reduce violation rate compared with semantic-only predictions;
- violation reduction only comes from removing most relation edges;
- consistency-filtered recall collapses below a useful threshold;
- relation labels are too noisy to define geometry validity;
- computed geometry evidence mostly duplicates trivial distance thresholds without meaningful relation reliability gains.

## Alternative Explanations

- Gains may come from dataset label bias rather than real geometry grounding.
- A verifier may simply favor head predicates such as `near` or `on`.
- Ground-truth object boxes may make the problem easier than predicted instances.
- Some semantic relations are valid despite weak geometry evidence because scans are partial or occluded.

## Success Criteria

Minimum success:

- Define a geometry-checkable predicate subset.
- Compute edge-level geometry evidence for each candidate relation.
- Complete Phase A and Phase B on at least one validated scan.
- Report geometry availability, violation candidates, uncertain cases, and manual inspection outcomes.

Minimum prediction-level H001 validation:

- Run the prediction-level phase on baseline predictions.
- Report violation rate and consistency-filtered recall.
- Show at least one predicate family where geometry verification improves prediction reliability without destroying useful recall.

Strong success:

- Improve violation rate across support/contact and proximity predicates.
- Preserve comparable predicate/triplet recall on the selected subset.
- Show that explicit evidence catches errors made by at least one closed-set or open-vocabulary baseline.

## User Judgment Needed

- Whether to prioritize closed-set 3DSSG comparability or open-vocabulary relation proposal first.
- Whether a recall/violation tradeoff is acceptable as a thesis contribution.
- Whether local functional relations should remain optional or be excluded entirely from H001.
