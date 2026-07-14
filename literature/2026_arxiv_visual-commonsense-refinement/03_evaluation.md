# Evaluation

## Dataset / Benchmark

The manuscript evaluates image scene graph generation on PSG, VG150, and
IndoorVG with Motifs, Transformer, and REACT++ source architectures.

## Splits

Constraints are mined from training annotations. A verifier tests candidate
rules against predictions on a data subset before deployment. Exact
split-isolation details should be rechecked if used as a reproduced baseline.

## Metrics

The paper reports standard scene-graph metrics including F1@K and zero-shot
Recall, plus Constraint Violation Rate: the share of selected triplets that
violate at least one mined constraint.

## Baselines

The key comparison is each neural SGG architecture before and after the same
declarative refinement framework.

## Main Results

Paper claim: consistent F1@K improvement and lower constraint violation across
the three benchmarks and architectures. This H001 intake records the claim and
method overlap; it does not reuse the paper's numbers as H001 evidence.

## Reproducibility Notes

- arXiv v1 checked on 2026-07-13.
- No code link was identified during the targeted skim.
- The rule confidence threshold and candidate-rule verifier are material
  implementation details.

## Evaluation Weaknesses

- Constraint Violation Rate is defined by the same mined constraint system
  used for refinement, so independent construct validity is limited.
- The setting is 2D SGG; it does not test reconstructed 3D point evidence,
  source-score exclusion, or 3D uncertainty/observability.
