# H002 Codex Label Smoke

Last updated: 2026-06-13

## Purpose

`32_human_label_readiness.md`에서 만든 `(codex_ver)` strict binary target이 H002
factorized reliability posterior pipeline에 실제로 들어갈 수 있는지 확인했다.

이 단계는 posterior 성능 주장 단계가 아니다.

Core question:

```text
Can the H002 posterior pipeline consume codex_ver strict labels under a
train-only contract?
```

## Boundary

```text
split = train_only
validation usage = false
paper result = false
human confirmed labels = false
posterior claim allowed = false
```

Important:

```text
(codex_ver) labels are not human-confirmed labels.
```

따라서 이 결과는 plumbing viability와 leakage-boundary 점검으로만 해석한다.

## Input Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/strict_proximity_informativeness.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_codex_ver_binary_targets.jsonl
```

Input counts:

| Target | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| `strict_codex_ver` | 27 | 16 | 11 |

Codex target mapping:

| Codex final label | Target |
| --- | ---: |
| `reliable_promote` | 1 |
| `unreliable_dense_noise` | 0 |

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/codex_label_smoke.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/codex_label_smoke.py
```

Status:

```text
ready_plumbing_only_codex_labels
```

Implementation note:

- Uses the existing pure-Python logistic regression from `factor_smoke.py`.
- Uses train-internal 5-fold crossfit only.
- Hyperparameters are inherited from previous smoke:
  - folds: `5`
  - epochs: `1500`
  - learning rate: `0.08`
  - L2: `0.03`
- No validation/test rows were used.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/predictions_*.jsonl
```

## Train-Internal 5-Fold Metrics

These are train-only diagnostics, not held-out results.

| Baseline | Inputs | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | `S_e` | 0.6080 | 0.7431 | 0.2381 | 0.2620 | 0.6296 |
| `geometry_only` | `G_e` | 0.8523 | 0.8986 | 0.1828 | 0.0300 | 0.7778 |
| `semantic_plus_geometry` | `S_e + G_e` | 0.8864 | 0.9217 | 0.1420 | 0.0960 | 0.8519 |
| `factorized_reliability_posterior` | `S_e + G_e + C_e + U_e` | 0.8864 | 0.9339 | 0.1434 | 0.1376 | 0.8519 |

Reading:

- `semantic_only` is weak.
- `geometry_only` is stronger, but not sufficient for full reliability.
- `semantic_plus_geometry` and `factorized_reliability_posterior` are close.
- `factorized` improves AUPRC over `semantic_plus_geometry`, but AUROC and
  accuracy are identical.
- Because `N=27`, this is not evidence of posterior superiority.

## Controlled Views

| View | AUROC | AUPRC | Brier | Accuracy@0.5 |
| --- | ---: | ---: | ---: | ---: |
| `drop_direct_identity` | 0.8864 | 0.9217 | 0.1420 | 0.8519 |
| `drop_direct_identity_rank` | 0.8409 | 0.8975 | 0.1725 | 0.7407 |
| `safe_continuous` | 0.8409 | 0.8975 | 0.1725 | 0.7407 |
| `geometry_continuous_only` | 0.8523 | 0.8986 | 0.1828 | 0.7778 |
| `semantic_raw_only` | 0.5483 | 0.7204 | 0.2364 | 0.5926 |

Reading:

- Direct target identity removal does not collapse performance.
- Removing rank/status identity reduces performance but keeps nontrivial signal.
- The remaining signal is mostly continuous geometry evidence plus raw semantic
  confidence.
- Since the target labels are still `(codex_ver)`, this only shows pipeline
  viability.

## Probe Metrics

| Probe | AUROC | AUPRC | Interpretation |
| --- | ---: | ---: | --- |
| `semantic_score_raw` | 0.6108 | 0.8444 | weak-to-moderate source signal |
| `semantic_score_norm` | 0.6051 | 0.7808 | rank no longer solves target |
| `negative_semantic_score_norm` | 0.3949 | 0.6368 | inverted rank no longer solves target |
| `p_geom_valid` | 0.0966 | 0.4202 | raw `p_geom_valid` is anti-aligned for this target |
| `consistency_score` | 0.5000 | 0.7691 | no AUROC ranking signal |
| `negative_geometry_residual` | 0.5000 | 0.7691 | no AUROC ranking signal |

The anti-aligned `p_geom_valid` result is important: the current strict
Codex target is not "geometry validity" itself. It is relation reliability under
geometry-satisfied proximity rows, where the positive/negative distinction is
informativeness:

```text
true_underconfidence / reliable_promote
vs
dense_relation_noise / unreliable_dense_noise
```

This supports the H002 separation:

```text
geometry validity != relation reliability
```

## Interpretation

Established:

- `(codex_ver)` strict labels can be joined to target-v2 feature rows.
- H002 can run the planned baseline set on these labels.
- The current target is no longer solved by semantic rank alone.
- `p_geom_valid` alone is not the reliability target.
- No validation/test rows were used.

Not established:

- human-confirmed reliability labels.
- posterior advantage over `semantic_plus_geometry`.
- generalization across scans, sources, or relation families.
- paper-level metric evidence.

The main result of this step is:

```text
H002 posterior plumbing is ready, but method evidence is still blocked by label
quality and target independence.
```

## Relation To Multi-View Feasibility

`feasibility_check.md` argues that point cloud + multi-view is reasonable if it is
framed as an RGA evidence-axis extension:

```text
P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)
```

However, this smoke deliberately does not include `V_mv_e`. The reason is that
current labels are `(codex_ver)` bootstrap labels. Adding visual features before
independent audit would make it hard to separate:

```text
target construction shortcut
vs
true visual-geometric reliability evidence
```

## Next TODO

Next document:

```text
34_multiview_audit_protocol.md
```

Required next work:

- define how multi-view evidence is used first as audit/confirmation evidence.
- define a clean `V_mv_e` feature contract separate from label evidence.
- specify wrong-pair, shuffled-view, shuffled-geometry, no-view/low-visibility
  controls.
- decide whether the next target should remain proximity-only or shift toward
  `support_contact` / `attachment_deferred` style relation families.
