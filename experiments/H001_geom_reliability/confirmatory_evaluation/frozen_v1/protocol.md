# H001 Prospective Confirmatory Evaluation Protocol

Frozen at UTC: `2026-07-10T06:18:51.186058+00:00`  
Status: `human_confirmatory_open_source_metric_confirmatory_requires_target`

## Provenance verdict

The family calibrator itself predates the full-validation source metrics and was
fit only on `train_dev_calib` rows without semantic scores. However,
`family_conditional_risk` was interpreted as a method candidate on 2026-06-24
and promoted to the paper main score on 2026-06-25, after the 2026-06-23
VL-SAT/Open3DSG source results were available. Therefore the existing source
metric table is valid retrospective evidence but is not labeled confirmatory.
This distinction must remain explicit in the paper and supplement.

## Locked method and hypotheses

- Main score: `semantic_score * p_geom_valid_family`.
- Comparators: `semantic_only`, pooled calibration, geometry-only family score,
  fixed rank-average fusion, and fixed Reciprocal Rank Fusion (`c=60`).
- Families: `support_contact`, `proximity`, `relative_vertical`; no family may
  be removed after confirmatory results are observed.
- K grid: `{5,10,20,50,100}`; K=100 is primary, lower K values are secondary.
- Primary validity hypothesis: paired `Delta Human-V@100 = V_main - V_semantic < 0`.
- Recall guardrail for a new untouched source evaluation: lower 95% paired CI
  for `Delta R@100` must exceed `-0.01` absolute.
- Primary uncertainty unit: subgraph/scene cluster bootstrap, 1,000 fixed-seed
  resamples. Family-wise and low-K results are secondary and reported in full.

## Confirmatory tracks

### C1: independent human physical validity

This track is prospectively confirmatory for physical validity because the
490-item probability sample, blinding fields, estimands, and evaluation code
were frozen while both annotator sheets were empty. Two independent annotators
and blinded adjudication are required. This track does not retroactively make
the already-seen exact-label source metrics confirmatory.

### C2: untouched source metrics

This track remains blocked until one genuinely untouched evaluation target is
selected. Re-running or repartitioning the already inspected VL-SAT,
Open3DSG-recovery, or Qwen full-validation outputs is not a fresh confirmatory
test. The selected target must be recorded here before inference and before any
main-score/family/K changes.

## No-change rule

After this freeze, new fusion variants may be exploratory appendix analyses only.
They cannot replace the locked main score on the same confirmatory target. Any
protocol deviation, evidence replacement, label-policy change, or target reuse
must be logged and the affected result relabeled exploratory.
