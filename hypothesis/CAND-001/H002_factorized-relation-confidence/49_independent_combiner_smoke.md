# H002 Independent Combiner Smoke

Last updated: 2026-06-14

## Purpose

`48_blind_label_fill.md`에서 만든 `75`개 binary-usable rank-hidden bootstrap
target을 deployable feature rows에 join하고, H002의 factorized reliability 방향이
`semantic + geometry` baseline보다 실제로 더 설명력이 있는지 train-only smoke로
확인한다.

이번 단계의 핵심 질문:

```text
Does factorized / residual / gated evidence explain independent relation
reliability beyond semantic+geometry and rank/family proxies?
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_combiner_smoke.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_combiner_smoke.py
```

Result:

```text
status=independent_combiner_no_strong_signal rows=75 binary_pos=46 binary_neg=29 metrics=66 validation_used=False grouped_factorized_d_auprc=-0.0013 grouped_residual_d_auprc=-0.1010 grouped_gated_d_auprc=-0.0969 grouped_factorized_vs_rank_d_auprc=0.1412
```

## Boundary

- Train-only hypothesis-stage smoke.
- No validation/test rows are used.
- Labels are `(codex_ver_blind)` bootstrap labels from sanitized blind sheets.
- `V_mv_e` is not used as model input.
- Label/audit evidence is not used as deployable input.
- This is not a paper-level metric.
- Posterior method claim remains blocked unless controls become favorable.

## Input Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/deployable_features_all.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/binary_targets.jsonl
```

Target counts:

| Item | Count |
| --- | ---: |
| binary rows | 75 |
| positive | 46 |
| negative | 29 |

Family counts:

| Family | Positive | Negative | Rows |
| --- | ---: | ---: | ---: |
| `proximity` | 15 | 12 | 27 |
| `relative_vertical` | 8 | 15 | 23 |
| `support_contact` | 23 | 2 | 25 |

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/family_slices.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/pairwise.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/matched_pairs.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/independent_codex_ver_blind_rows.jsonl
```

## Views

Main views:

| View | Meaning |
| --- | --- |
| `semantic_only` | source semantic score/rank/predicate view |
| `geometry_only` | geometry evidence only |
| `semantic_plus_geometry` | direct semantic + geometry baseline |
| `factorized_reliability_posterior` | existing full factorized feature block |
| `residual_reliability_model` | semantic prior plus geometry/coverage/uncertainty residual |
| `gated_evidence_model` | semantic prior plus coverage/uncertainty-gated geometry evidence |

Controls:

```text
rank_only
negative_rank_only
rank_band_only
family_only
predicate_only
p_geom_valid_only
drop_direct_identity
drop_direct_identity_rank
safe_continuous
geometry_continuous_only
semantic_raw_only
```

## Main Result

Grouped by `scan_id`:

| View | AUROC | AUPRC | Brier | ECE-5 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.7774 | 0.8682 | 0.1822 | 0.0523 |
| `geometry_only` | 0.4265 | 0.6216 | 0.2473 | 0.1351 |
| `semantic_plus_geometry` | 0.7736 | 0.8539 | 0.1870 | 0.0332 |
| `factorized_reliability_posterior` | 0.7714 | 0.8526 | 0.1886 | 0.0389 |
| `residual_reliability_model` | 0.7249 | 0.7528 | 0.2054 | 0.0625 |
| `gated_evidence_model` | 0.7234 | 0.7569 | 0.2057 | 0.0620 |

Key deltas under grouped folds:

| Comparison | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | ---: | ---: | ---: |
| `factorized - semantic_plus_geometry` | -0.0022 | -0.0013 | +0.0016 |
| `residual - semantic_plus_geometry` | -0.0487 | -0.1010 | +0.0184 |
| `gated - semantic_plus_geometry` | -0.0502 | -0.0969 | +0.0186 |
| `factorized - negative_rank_only` | +0.1657 | +0.1412 | -0.0289 |

Interpretation:

```text
Factorized is better than a simple negative-rank proxy, but it does not beat the
semantic_plus_geometry baseline. Residual/gated variants are worse in this
bootstrap target.
```

## Proxy Risk

The strongest warning is not rank-only anymore. It is family/predicate policy.

Grouped controls:

| Proxy | AUROC | AUPRC | Brier |
| --- | ---: | ---: | ---: |
| `family_only` | 0.7324 | 0.8330 | 0.1974 |
| `predicate_only` | 0.7571 | 0.8650 | 0.1899 |
| `negative_rank_only` | 0.6057 | 0.7114 | 0.2175 |
| `p_geom_valid_only` | 0.4970 | 0.6522 | 0.2427 |

This means:

```text
The current codex_ver_blind label policy is strongly entangled with predicate
family and predicate semantics.
```

This is expected because the bootstrap labels were assigned from visible
metadata and family rules. It makes the target useful for plumbing, but not yet
strong evidence for a factorized posterior method.

## Family Slice Observation

Train-internal 5-fold family slices show heterogeneous behavior.

`proximity`:

| View | AUPRC |
| --- | ---: |
| `semantic_plus_geometry` | 0.6876 |
| `factorized_reliability_posterior` | 0.6876 |
| `residual_reliability_model` | 0.7115 |
| `gated_evidence_model` | 0.7449 |

`relative_vertical`:

| View | AUPRC |
| --- | ---: |
| `semantic_plus_geometry` | 0.6483 |
| `factorized_reliability_posterior` | 0.6483 |
| `residual_reliability_model` | 0.4454 |
| `gated_evidence_model` | 0.4454 |

`support_contact`:

| View | AUPRC |
| --- | ---: |
| `semantic_plus_geometry` | 0.9622 |
| `factorized_reliability_posterior` | 0.9593 |
| `residual_reliability_model` | 0.9032 |
| `gated_evidence_model` | 0.8750 |

Interpretation:

- `proximity` is the only slice where gated/residual variants look useful.
- `relative_vertical` and `support_contact` do not support the new combiner.
- `support_contact` is highly imbalanced (`23` positive / `2` negative), so its
  AUPRC is not enough evidence.

## Pairwise Diagnostic

Rank-matched pairwise rows:

```text
pairs = 22
```

Selected pairwise accuracy:

| View | Pairwise Accuracy |
| --- | ---: |
| `semantic_plus_geometry` | 0.8182 |
| `factorized_reliability_posterior` | 0.7727 |
| `residual_reliability_model` | 0.8182 |
| `gated_evidence_model` | 0.8182 |
| `negative_rank_only` | 0.5909 |
| `p_geom_valid_only` | 0.5000 |

This suggests:

```text
Pairwise evidence is not hostile to residual/gated views, but it does not beat
semantic_plus_geometry either.
```

## Decision

Current status:

```text
independent_combiner_no_strong_signal
```

Meaning:

```text
The independent bootstrap target is executable, but it does not currently
support a factorized posterior method claim. The main issue is now label policy
and family/predicate entanglement, not data plumbing.
```

Allowed:

- continue H002 as RGA benchmark/failure-analysis.
- use this result as evidence that current posterior method is not yet justified.
- investigate family-specific target policy, especially `proximity`.

Blocked:

- factorized posterior advantage claim.
- residual/gated combiner claim.
- paper-level result claim.
- claim that multi-view should now be promoted to model input.

## Next TODO

Next document:

```text
50_label_policy_audit.md
```

Goal:

- audit whether `(codex_ver_blind)` labels are mostly recoverable from
  predicate/family rules.
- create a target variant that controls family/predicate policy more tightly.
- decide whether H002 should keep posterior as method candidate or retreat to
  RGA benchmark/failure taxonomy.
- continue using only train-pilot rows.
