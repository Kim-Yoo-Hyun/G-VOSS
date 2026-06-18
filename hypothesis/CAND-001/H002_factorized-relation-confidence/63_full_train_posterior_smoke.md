# H002 Full Train Posterior Smoke

Last updated: 2026-06-16

## Purpose

`62_full_train_label_fill.md`에서 만든 full-train `(codex_ver_full_train)` binary
target으로 train-only posterior smoke를 실행한다.

핵심 질문:

```text
Does factorized reliability evidence explain the bootstrap relation target
beyond semantic+geometry and proxy shortcuts?
```

## Decision

Current status:

```text
full_train_posterior_proxy_blocked
```

Meaning:

```text
The full-train bootstrap target is executable, but proxy controls explain the
target better than the factorized posterior. This is target-policy evidence,
not posterior method evidence.
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_posterior_smoke.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_posterior_smoke.py
```

Result:

```text
status=full_train_posterior_proxy_blocked rows=173 pos=74 neg=99 metrics=62 validation_used=False grouped_factorized_d_auprc=0.0117 grouped_factorized_vs_queue_d_auprc=0.0470
```

## Input

Target:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness_codex_ver/binary_targets.jsonl
```

Rows:

| Item | Count |
| --- | ---: |
| binary rows | 173 |
| positive | 74 |
| negative | 99 |

Target distribution:

| Field | Distribution |
| --- | --- |
| queue | `HL=83`, `LH=90` |
| family | `support_contact=93`, `relative_vertical=50`, `proximity=30` |
| final label | `reliable_promote=74`, `unreliable_dense_noise=99` |
| taxonomy | `true_underconfidence=74`, `semantic_overconfidence_invalid=83`, `dense_relation_noise=16` |

## Method

The smoke uses compact target-row fields only. It does not reread the 17G
`match_rows.jsonl`.

Main views:

| View | Input |
| --- | --- |
| `semantic_only` | semantic score/rank features |
| `geometry_only` | continuous `p_geom_valid` features |
| `semantic_plus_geometry` | semantic + continuous geometry |
| `factorized_reliability_posterior` | semantic + geometry + disagreement/residual features |

Proxy controls:

```text
negative_rank_only
rank_band_only
queue_only
candidate_axis_only
family_only
predicate_only
label_status_only
geometry_status_only
proposed_role_only
p_geom_valid_only
```

Grouped evaluation:

```text
train_internal_grouped_by_scan, 3 folds
```

Reason for 3 folds:

```text
The target has only 173 binary rows and scan groups are uneven. A 5-fold grouped
split produced very small folds, so this full-train smoke uses scan-grouped
3-fold CV for the main diagnostic.
```

Final grouped fold distribution:

| Fold | Groups | Rows | Positive | Negative |
| --- | ---: | ---: | ---: | ---: |
| 0 | 12 | 58 | 25 | 33 |
| 1 | 25 | 58 | 25 | 33 |
| 2 | 45 | 57 | 24 | 33 |

## Main Result

Grouped by scan:

| View | AUROC | AUPRC | Brier | ECE-5 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9070 | 0.7598 | 0.1221 | 0.1704 |
| `geometry_only` | 0.6084 | 0.4824 | 0.2275 | 0.0345 |
| `semantic_plus_geometry` | 0.9044 | 0.7547 | 0.1188 | 0.1643 |
| `factorized_reliability_posterior` | 0.9085 | 0.7665 | 0.1170 | 0.1414 |

Delta:

| Comparison | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | ---: | ---: | ---: |
| `factorized - semantic_plus_geometry` | +0.0041 | +0.0117 | -0.0019 |
| `residual - semantic_plus_geometry` | +0.0051 | +0.0103 | -0.0021 |
| `factorized - negative_rank_only` | +0.0121 | +0.0182 | -0.0241 |

Interpretation:

```text
The factorized view is executable and slightly better than semantic+geometry,
but the margin is below the H002 revival threshold.
```

The predeclared method-revival threshold was:

```text
AUPRC >= +0.03 or Brier <= -0.02 over semantic_plus_geometry,
with AUROC drop <= 0.02.
```

This smoke does not meet that threshold.

## Proxy Controls

Grouped proxy results:

| Proxy | AUROC | AUPRC | Brier |
| --- | ---: | ---: | ---: |
| `negative_rank_only` | 0.8965 | 0.7482 | 0.1411 |
| `queue_only` | 0.8793 | 0.7195 | 0.0881 |
| `predicate_only` | 0.7652 | 0.7572 | 0.1968 |
| `label_status_only` | 0.9916 | 0.9473 | 0.0087 |
| `proposed_role_only` | 1.0000 | 1.0000 | 0.0035 |
| `geometry_status_only` | 0.8793 | 0.7195 | 0.0881 |

Critical blockers:

| Comparison | Delta AUPRC | Delta Brier |
| --- | ---: | ---: |
| `factorized - proposed_role_only` | -0.2335 | +0.1135 |
| `factorized - label_status_only` | -0.1808 | +0.1083 |

Interpretation:

```text
The current codex_ver_full_train target is recoverable from proposed audit role
and label status. Therefore it cannot validate the factorized posterior method.
```

## Pairwise Check

Rank-matched pairwise rows:

```text
pairs = 74
```

Selected pairwise accuracy:

| View | Accuracy |
| --- | ---: |
| `semantic_plus_geometry` | 0.8919 |
| `factorized_reliability_posterior` | 0.8919 |
| `negative_rank_only` | 0.9189 |
| `queue_only` | 0.8851 |
| `label_status_only` | 0.9932 |
| `proposed_role_only` | 1.0000 |

Interpretation:

```text
Pairwise matching also does not show factorized advantage over the strong
semantic+geometry baseline.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_posterior_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_posterior_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_posterior_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_posterior_smoke_codex_ver/family_slices.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_posterior_smoke_codex_ver/pairwise.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_posterior_smoke_codex_ver/full_train_controlled_codex_ver_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_posterior_smoke_codex_ver/matched_pairs.jsonl
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `metrics.csv` | 62 + header |
| `family_slices.csv` | 78 + header |
| `pairwise.csv` | 26 + header |
| `full_train_controlled_codex_ver_rows.jsonl` | 173 |
| `matched_pairs.jsonl` | 74 |

## Boundary

Established:

- full-train posterior smoke is executable.
- factorized view can consume semantic, geometry, and disagreement features.
- validation/test rows are unused.
- `V_mv_e` is not model input.

Not established:

- factorized posterior method advantage.
- shortcut-free target independence.
- human-confirmed label evidence.
- paper-level performance.

Blocked:

```text
factorized_reliability_posterior as a method contribution
```

Still supported:

```text
H002 as RGA benchmark / failure taxonomy / controlled audit framework
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_posterior_smoke.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_posterior_smoke.py
```

Observed:

```text
status=full_train_posterior_proxy_blocked
validation_used=False
```

## Next TODO

Completed next action:

```text
full_train_label_policy_audit
```

Result:

```text
full_train_label_policy_entangled
```

The audit confirmed that the current bootstrap target is recoverable from
`proposed_audit_role` and `label_match_status`, so the next step is not another
posterior fitting run.

Next action:

```text
full_train_independent_label_protocol
```
