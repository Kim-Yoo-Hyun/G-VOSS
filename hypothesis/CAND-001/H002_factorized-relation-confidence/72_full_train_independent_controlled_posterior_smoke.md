# H002 Full Train Independent Controlled Posterior Smoke

Last updated: 2026-06-17

## Purpose

`71_full_train_independent_target_independence_audit.md`에서 original 283-row
target은 shortcut-risky하지만, `proposed_role_balanced_codex_ver` controlled
slice가 남는 것을 확인했다. 이번 단계는 이 slice에서만 train-only posterior
smoke를 실행해 H002의 factorized reliability posterior가 단순 비교군보다
나은지 확인한다.

핵심 질문:

```text
On the role-balanced controlled slice, does factorized reliability outperform
semantic-only, geometry-only, and semantic+geometry baselines?
```

## Decision

Current status:

```text
full_train_independent_controlled_posterior_no_strong_signal
```

Meaning:

```text
The controlled slice is executable, but factorized reliability does not improve
over semantic+geometry under scan-grouped train-only folds.
```

This blocks any posterior novelty claim. The next step is controlled error and
feature analysis, not expansion or paper-level result framing.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_posterior_smoke.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_posterior_smoke.py
```

Observed:

```text
status=full_train_independent_controlled_posterior_no_strong_signal rows=158 pos=79 neg=79 metrics=36 validation_used=False d_auprc_factorized_vs_sg=-0.0047 d_auprc_factorized_vs_semantic=-0.0039 d_auprc_factorized_vs_geometry=0.1155
```

## Input

Active target slice:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/target_slices/proposed_role_balanced_codex_ver.jsonl
```

Reference target, not used for claim:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/target_slices/original_independent_codex_ver.jsonl
```

## Boundary

Established:

- train-only.
- no validation/test rows.
- active target is `proposed_role_balanced_codex_ver`.
- original 283-row target is diagnostic reference only.
- hidden audit metadata is not used as model input.
- multi-view evidence is not used as model input.
- labels are Codex bootstrap labels, not human-confirmed labels.
- paper evidence and posterior novelty claims remain blocked.

## Target Summary

| Item | Rows |
| --- | ---: |
| total | 158 |
| positive | 79 |
| negative | 79 |

Family coverage:

| Family | Rows |
| --- | ---: |
| `support_contact` | 72 |
| `relative_vertical` | 55 |
| `proximity` | 31 |

Predicate coverage:

| Predicate | Rows |
| --- | ---: |
| `lying on` | 33 |
| `lower than` | 32 |
| `close by` | 31 |
| `higher than` | 23 |
| `supported by` | 20 |
| `standing on` | 19 |

## Main Result

Scan-grouped train-only folds:

| View | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.6623 | 0.6291 | 0.2360 | 0.0671 | 0.6076 |
| `geometry_only` | 0.4575 | 0.5098 | 0.2559 | 0.0230 | 0.4810 |
| `semantic_plus_geometry` | 0.6640 | 0.6300 | 0.2341 | 0.0418 | 0.6392 |
| `factorized_reliability_posterior` | 0.6531 | 0.6253 | 0.2363 | 0.0758 | 0.5823 |

Key deltas:

| Left | Right | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | --- | ---: | ---: | ---: |
| `factorized_reliability_posterior` | `semantic_plus_geometry` | -0.0109 | -0.0047 | +0.0021 |
| `factorized_reliability_posterior` | `semantic_only` | -0.0092 | -0.0039 | +0.0002 |
| `factorized_reliability_posterior` | `geometry_only` | +0.1956 | +0.1155 | -0.0196 |
| `semantic_plus_geometry` | `geometry_only` | +0.2065 | +0.1202 | -0.0218 |

Interpretation:

```text
Semantic evidence dominates this controlled bootstrap target. Geometry-only is
weak. Adding geometry to semantic gives a small benefit, but the current
factorized feature construction does not outperform semantic+geometry.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/family_slices.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/pairwise.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/matched_pairs.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/controlled_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/predictions.jsonl
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `controlled_posterior_rows.jsonl` | 158 |
| `predictions.jsonl` | 1,422 |
| `metrics.csv` | 36 + header |
| `comparisons.csv` | 12 + header |
| `matched_pairs.jsonl` | 79 |

## Interpretation

This is a useful negative result. It says the current factorized combination is
not yet the right posterior form for H002, at least under the current
Codex-bootstrap controlled target.

Likely next checks:

- feature construction may be too redundant with `semantic_plus_geometry`.
- `semantic_only` still carries strong ranking/selection signal.
- geometry evidence may be too weak or too noisy after role balancing.
- factorized interactions may need calibrated family-specific residuals rather
  than generic disagreement terms.
- target remains bootstrap-label dependent, so human/audited labels are still
  needed before paper claims.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_posterior_smoke.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_posterior_smoke.py
```

Observed:

```text
validation_used=False
hidden_metadata_as_model_input=False
```

## Next TODO

Completed next action:

```text
full_train_independent_controlled_error_analysis
```

Result:

```text
full_train_independent_controlled_error_analysis_ready_for_combiner_design
```

The error analysis shows that current factorized posterior creates more
threshold mistakes than it fixes relative to `semantic_plus_geometry`
(`factorized_wrong_sg_correct=10`, `factorized_correct_sg_wrong=1`).
The next action is:

```text
full_train_independent_combiner_upgrade_design
```
