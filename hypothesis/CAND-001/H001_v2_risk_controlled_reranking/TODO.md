# H001_v2 TODO

Last updated: 2026-06-24 KST

## Now

- No active H001_v2 source-metric rerun task. The paper-facing naming pass is
  complete; legacy metric JSON keys are preserved.

## Next

- [ ] Optional coverage-aware extension: keep missing/unsupported/uncertain
      geometry as explicit states rather than hiding them inside a single risk
      score.

## Guardrails

- [ ] Do not overwrite H001_v1 metrics, tables, reports, paper source, or
      release bundles.
- [ ] Do not select `alpha`, `delta`, `tau_grid`, or `tau*` from
      full-validation source metrics.
- [ ] Do not promote H001_v2 to the current H001/GeoCalib paper main claim
      without explicit user confirmation.
- [ ] Do not hide coverage loss or selected-count reduction.

## Completed

- [x] Created H001_v2 branch under
      `hypothesis/CAND-001/H001_v2_risk_controlled_reranking/`.
- [x] Fixed the H001_v2 direction as risk-controlled semantic reranking, not
      learned fusion or H003-style representation learning.
- [x] Froze initial primary risk budget `alpha=0.05`, `delta=0.05`, K grid
      `{5,10,20,50,100}`, and `tau_grid={0.00,...,1.00}`.
- [x] Defined the deterministic primary threshold-selection rule:
      choose the largest `tau` whose calibration upper bound satisfies the
      violation budget across all K.
- [x] Defined branch boundary, read-only H001 artifact contract, output root,
      evaluation metrics, controls, and pass/falsification criteria.
- [x] Wrote `05_source_inventory.md`: read-only calibration/source paths, row
      counts, observed schema fields, allowed use, derived output root, and
      no-overwrite guard roots.
- [x] Completed `06_schema_probe.md`: confirmed calibration table lacks
      deployable `p_geom_valid` and semantic ranks, confirmed
      `p_geom_valid_smoke/scores.jsonl` has held-out `role == "dev"` rows for
      threshold selection, and confirmed source geometry JSONL has all fields
      needed for fixed-threshold top-K evaluation.
- [x] Selected first implementation route: calibration-threshold dry run only;
      full source evaluation remains blocked until `tau*` selection succeeds.
- [x] Added `src/geocalib/select_h001_v2_threshold.py` as the calibration-only
      dry-run runner with read-only-root no-overwrite guard.
- [x] Ran threshold dry run under
      `artifacts/calibration_threshold_selection/`: selected `tau*=0.20`
      (`p_geom_valid >= 0.80`) from 1,193 held-out dev rows, with 423 selected
      rows, 13 violations, empirical violation 0.0307, and CP upper 0.0484
      under `alpha=0.05`, `delta=0.05`.
- [x] Verified the guard rejects output under the VL-SAT H001 source root and
      creates no guard-test directory.
- [x] Wrote `07_source_eval_contract.md`: fixed source inputs, output root,
      K grid, H001_v2 selection semantics, required metrics/deltas,
      selected-count reporting, no-overwrite guard roots, proposed commands,
      and promotion gate.
- [x] Decided source-evaluation implementation route: first as a hypothesis
      runner under `src/geocalib/`; Docker service is deferred until H001_v2
      point metrics are promising enough for paper-facing promotion.
- [x] Implemented `src/geocalib/evaluate_h001_v2_source.py` as a
      hypothesis-stage fixed-threshold source-eval runner following
      `07_source_eval_contract.md`. The runner writes only under the H001_v2
      artifact root, reports selected counts and coverage, and refuses
      non-empty output directories unless `--overwrite` is passed.
- [x] Ran fixed `tau*=0.20` / `p_geom_valid >= 0.80` source point metrics for
      VL-SAT and Open3DSG recovery under `artifacts/source_eval/`.
      VL-SAT H001_v2 R@5/10/20/50/100 is
      `0.3797/0.5541/0.6772/0.7485/0.7666` with V
      `0.0018/0.0077/0.0125/0.0249/0.0482`; Open3DSG H001_v2 R is
      `0.0740/0.1740/0.3147/0.4436/0.5587` with V
      `0.1307/0.0993/0.0806/0.0634/0.0667`.
- [x] Wrote `08_source_eval_result.md`: source point metrics are mixed and not
      promotable yet. Open3DSG improves strongly over `semantic_only`, but
      VL-SAT shows recall collapse and H001_v2 does not dominate
      `probabilistic_recalibrated`.
- [x] Completed H001_v2 `tau_corruption_controls`: extended
      `src/geocalib/evaluate_h001_v2_source.py` with
      `control_shuffled_geometry_tau` and `control_wrong_pair_geometry_tau`,
      regenerated VL-SAT and Open3DSG source-eval artifacts under
      `artifacts/source_eval/`, and updated `08_source_eval_result.md`.
      Controls are consistently worse than H001_v2 on both sources, supporting
      geometry-specific signal, but the method remains mixed/not promotable
      because VL-SAT recall collapses and H001_v2 does not dominate
      `probabilistic_recalibrated`.
- [x] Completed H001_v2 `source_result_path_decision`: fixed-`tau*` H001_v2 is
      locked as diagnostic evidence only. Do not add it to the current
      H001/GeoCalib main paper table, and do not run fixed-`tau*` bootstrap
      unless appendix/supplement diagnostic uncertainty is explicitly needed.
- [x] Completed H001_v2 `risk_aware_soft_reranking_reframing`: added
      `09_risk_aware_soft_reranking.md` and updated the branch overview so the
      current GeoCalib `semantic_score * p_geom_valid` score is framed as the
      `lambda=1` log-linear utility-risk objective rather than an ad hoc
      multiplication heuristic. Locked metrics remain unchanged.
- [x] Completed H001_v2 `paper_prose_pass`: updated the active AAAI method
      source and synchronized draft prose so `semantic_score * p_geom_valid` is
      described as the `lambda=1` risk-aware soft re-ranking objective. No
      result table, locked metric, or artifact path was changed.
- [x] Completed H001_v2 `lambda_soft_protocol_and_source_eval`: added
      `src/geocalib/select_h001_v2_lambda.py` and
      `src/geocalib/evaluate_h001_v2_lambda_source.py`; selected `lambda*=1.25`
      from calibration dev rows only; generated VL-SAT/Open3DSG K={5,10,20,50,100}
      metrics under `artifacts/source_eval_lambda/`; wrote
      `10_lambda_soft_reranking_result.md`. Result is mixed against current
      `lambda=1` GeoCalib and remains diagnostic-only.
- [x] Completed H001_v2 `family_conditional_risk_formalization`: promoted the
      existing frozen `family_specific_p_geom_valid` artifact from a
      control-like interpretation to a family-conditional calibrated
      geometry-risk operating point in H001_v2. Wrote
      `11_family_conditional_risk_result.md`. This direction dominates pooled
      risk on Open3DSG across K for both recall and violation, and lowers
      VL-SAT violation with near-flat recall.
- [x] Completed H001_v2 `paper_facing_family_conditional_naming_pass`: updated
      paper-facing summaries, tables, figure inputs, and AAAI prose to report
      the frozen family-calibrator artifact as `family_conditional_risk` while
      preserving legacy metric JSON keys such as
      `control_family_specific_p_geom_valid`.
- [x] Verification: `python -m py_compile` passed for
      `evaluate_h001_v2_source.py`, `select_h001_v2_lambda.py`, and
      `evaluate_h001_v2_lambda_source.py`; source-eval lambda outputs report no
      warnings.
