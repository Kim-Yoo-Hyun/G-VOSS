# H002 Grouped Control Smoke

Last updated: 2026-06-13

## Purpose

`40_real_label_claim_audit.md`의 다음 gate를 실행한다. 사용자 지시에 따라
`(codex_ver)` labels를 hypothesis-stage real label로 취급하고, current controlled
posterior 결과가 scan-level grouped split에서도 유지되는지 확인한다.

검증 대상:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

Still excluded:

```text
V_mv_e
validation rows
test rows
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/grouped_control_smoke.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/grouped_control_smoke.py
```

Result:

```text
status=ready_grouped_control_smoke_codex_real_assumption metrics=32 validation_used=False mined_d_auprc=0.0341 mined_d_brier=-0.0234 combined_d_auprc=0.0268 combined_d_brier=-0.0082
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/predictions_*.jsonl
```

## Method

The split is grouped by:

```text
scan_id
```

This is stricter than the previous row-stratified train-internal split because
rows from the same scan cannot appear in both train and held-out fold.

Method references:

- `GroupKFold` style evaluation keeps the same group out of both train and test
  folds. Source checked: scikit-learn GroupKFold documentation.
- Calibration is still evaluated with Brier/ECE because H002 is a reliability
  posterior, not only a ranking model. Source checked: Guo et al., `On
  Calibration of Modern Neural Networks`, ICML 2017.

## Main Results

Scan-grouped train-internal evaluation:

| Target | View | AUROC | AUPRC | Brier | ECE-5 |
| --- | --- | ---: | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | `semantic_plus_geometry` | 0.8989 | 0.9069 | 0.1333 | 0.0894 |
| `mined_controlled_codex_ver` | `factorized_reliability_posterior` | 0.9427 | 0.9409 | 0.1098 | 0.0980 |
| `combined_controlled_codex_ver` | `semantic_plus_geometry` | 0.7336 | 0.6533 | 0.2168 | 0.1388 |
| `combined_controlled_codex_ver` | `factorized_reliability_posterior` | 0.7397 | 0.6801 | 0.2086 | 0.0878 |

Delta is `factorized_reliability_posterior - semantic_plus_geometry`.

| Target | Delta AUROC | Delta AUPRC | Delta Brier | Initial verdict |
| --- | ---: | ---: | ---: | --- |
| `mined_controlled_codex_ver` | +0.0438 | +0.0341 | -0.0234 | passes numeric threshold |
| `combined_controlled_codex_ver` | +0.0061 | +0.0268 | -0.0082 | weak / below AUPRC threshold |

Under the user-directed real-label assumption, this is more positive than the
row-level result for the mined target.

## Factor Ablation

| Target | View | Delta AUPRC vs `S+G` | Delta Brier vs `S+G` |
| --- | --- | ---: | ---: |
| `mined_controlled_codex_ver` | `S+G+C` | +0.0000 | +0.0000 |
| `mined_controlled_codex_ver` | `S+G+U` | +0.0338 | -0.0233 |
| `mined_controlled_codex_ver` | `S+G+C+U` | +0.0338 | -0.0233 |
| `combined_controlled_codex_ver` | `S+G+C` | +0.0000 | +0.0000 |
| `combined_controlled_codex_ver` | `S+G+U` | +0.0293 | -0.0085 |
| `combined_controlled_codex_ver` | `S+G+C+U` | +0.0293 | -0.0085 |

Interpretation:

- `C_e` alone adds no signal in the current controlled target.
- The improvement comes from uncertainty/disagreement-like features.
- Because all rows are `geometry_status=satisfied`, coverage features are mostly
  constant; this is expected.

## Proxy Baseline Audit

The strongest warning is the rank proxy.

| Target | View | AUROC | AUPRC | Brier |
| --- | --- | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | `factorized_reliability_posterior` | 0.9427 | 0.9409 | 0.1098 |
| `mined_controlled_codex_ver` | `negative_rank_only` | 0.9505 | 0.9589 | 0.1057 |
| `combined_controlled_codex_ver` | `factorized_reliability_posterior` | 0.7397 | 0.6801 | 0.2086 |
| `combined_controlled_codex_ver` | `negative_rank_only` | 0.7884 | 0.7094 | 0.1899 |

This means:

```text
factorized posterior does not yet beat a simple rank-derived proxy.
```

Therefore the current signal may be explained by semantic rank / underconfidence
structure rather than a general factorized reliability posterior.

## Decision

Under the user-directed real-label assumption:

Established:

- scan-grouped evaluation runs without validation/test rows.
- `geometry_only` remains weak, supporting `geometry validity != reliability`.
- `factorized` beats `semantic_plus_geometry` on mined grouped CV.
- uncertainty/disagreement features carry useful signal in this controlled target.

Not established:

- factorized posterior beats strong rank-only proxies.
- `C_e` contributes signal in the current target.
- improvement is independent of semantic-rank construction.
- calibration advantage is strong enough across target variants.

Current verdict:

```text
H002 has conditional support for the reliability framing,
but not yet strong support for the factorized posterior as a method contribution.
```

## Remaining Hypothesis Checks

Highest priority:

1. `rank_proxy_debias`
   - Remove or residualize rank-derived features.
   - Require factorized evidence to beat `negative_rank_only`.

2. `within-rank-band evaluation`
   - Report metrics separately for `rank_201_500`, `rank_501_1000`, `rank_gt1000`.
   - Verify the gain is not from one rank band.

3. `bootstrap_ci`
   - Paired bootstrap CI for AUPRC, Brier, AUROC deltas.
   - Required because N is still 96/123.

4. `calibration_report`
   - Reliability bins, Brier, ECE.
   - H002 is a reliability posterior, so calibration must be explicit.

5. `failure_delta_audit`
   - Inspect rows where factorized beats `S+G` and vice versa.
   - Verify wins correspond to uncertainty/evidence reasoning, not rank artifact.

## Next TODO

Next document:

```text
42_rank_proxy_debias.md
```

Recommended next implementation:

- create rank-debiased feature views.
- compare against `negative_rank_only`.
- run scan-grouped CV again.
- report mined and combined targets separately.
