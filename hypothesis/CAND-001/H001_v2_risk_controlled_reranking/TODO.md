# H001_v2 TODO

Last updated: 2026-06-22 KST

## Now

- [ ] Add H001_v2 metrics condition only in separate H001_v2 artifact root.
- [ ] Implement `src/geocalib/evaluate_h001_v2_source.py` as a hypothesis
      runner that follows `07_source_eval_contract.md`.

## Next

- [ ] Implement fixed-threshold source evaluation if approved:
      select edges with `calibration.p_geom_valid >= 0.80`, rank eligible rows
      by semantic score, and compute K={5,10,20,50,100}.
- [ ] Add fixed-`tau*` bootstrap behavior only after source point metrics are
      generated.

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
