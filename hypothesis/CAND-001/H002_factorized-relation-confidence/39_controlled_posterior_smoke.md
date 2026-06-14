# H002 Controlled Posterior Smoke

Last updated: 2026-06-13

## Purpose

`38_controlled_codex_labels.md`에서 만든 Codex-filled controlled labels를
deployable feature rows에 join하고, current posterior 구성의 train-only plumbing을
확인한다.

검증 대상:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

여전히 `V_mv_e`는 model input으로 넣지 않는다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/controlled_posterior_smoke.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/controlled_posterior_smoke.py
```

Result:

```text
status=ready_plumbing_only_controlled_codex_labels targets=2 metrics=48 validation_used=False mined_controlled_codex_ver:d_auprc=0.0006:d_brier=-0.0012 combined_controlled_codex_ver:d_auprc=0.0337:d_brier=-0.0081
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/mined_controlled_codex_ver_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/combined_controlled_codex_ver_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/predictions_*.jsonl
```

## Target Counts

| Target | Rows | Positive | Negative | Family | Geometry status |
| --- | ---: | ---: | ---: | --- | --- |
| `mined_controlled_codex_ver` | 96 | 48 | 48 | `proximity` | `satisfied` |
| `combined_controlled_codex_ver` | 123 | 64 | 59 | `proximity` | `satisfied` |

## Main Baselines

Train-internal 5-fold, no validation/test rows.

| Target | Baseline | AUROC | AUPRC | Brier | ECE-5 | Acc@0.5 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | `semantic_only` | 0.9316 | 0.9484 | 0.1038 | 0.0749 | 0.8646 |
| `mined_controlled_codex_ver` | `geometry_only` | 0.5308 | 0.5416 | 0.2584 | 0.0296 | 0.4583 |
| `mined_controlled_codex_ver` | `semantic_plus_geometry` | 0.9484 | 0.9546 | 0.1024 | 0.0968 | 0.8438 |
| `mined_controlled_codex_ver` | `factorized_reliability_posterior` | 0.9531 | 0.9552 | 0.1011 | 0.0923 | 0.8333 |
| `combined_controlled_codex_ver` | `semantic_only` | 0.7897 | 0.7079 | 0.1914 | 0.2070 | 0.7480 |
| `combined_controlled_codex_ver` | `geometry_only` | 0.5421 | 0.5727 | 0.2564 | 0.0262 | 0.4959 |
| `combined_controlled_codex_ver` | `semantic_plus_geometry` | 0.7940 | 0.7321 | 0.1925 | 0.1417 | 0.7236 |
| `combined_controlled_codex_ver` | `factorized_reliability_posterior` | 0.8003 | 0.7658 | 0.1844 | 0.1266 | 0.7398 |

## Factorized Delta

Delta is `factorized_reliability_posterior - semantic_plus_geometry`.

| Target | Delta AUROC | Delta AUPRC | Delta Brier | Numeric rule met |
| --- | ---: | ---: | ---: | --- |
| `mined_controlled_codex_ver` | +0.0048 | +0.0006 | -0.0012 | `False` |
| `combined_controlled_codex_ver` | +0.0064 | +0.0337 | -0.0081 | `True` |

## Interpretation

This smoke confirms that the controlled target can be joined to deployable
features and consumed by all four baseline views.

Important reading:

- `geometry_only` is near random because the controlled target fixes
  `geometry_status=satisfied`; this is expected and useful.
- `semantic_only` is already strong, especially on the mined target. This means
  the Codex bootstrap target is still correlated with source/rank/selection
  structure.
- `factorized_reliability_posterior` only weakly improves over
  `semantic_plus_geometry` on the mined controlled target.
- The combined target numerically meets the AUPRC rule, but it includes
  `(codex_ver)` labels and existing strict seed rows. This is not evidence for
  a method claim.

## Decision

Established:

- controlled Codex labels can pass the readiness gate.
- deployable features can join to controlled binary targets.
- the four planned baselines run end-to-end.
- current posterior pipeline is executable under train-only constraints.

Not established:

- human/independent label quality.
- factorized posterior advantage.
- paper-level metric evidence.
- held-out generalization.

Therefore:

```text
H002 posterior implementation is ready for real labels, but the hypothesis is
not validated by codex_ver labels.
```

## Boundary

```text
split = train_only
validation usage = false
test usage = false
label source = codex_ver_sampling_prior_bootstrap
human confirmed = false
paper result = false
posterior claim allowed = false
V_mv_e model input allowed = false
```

## Next TODO

Next required gate:

```text
replace_codex_ver_with_human_or_independent_controlled_labels
```

The next scientific step is not more fitting. It is to replace Codex bootstrap
labels with human/independent labels, rerun readiness, and then rerun this same
posterior smoke.
