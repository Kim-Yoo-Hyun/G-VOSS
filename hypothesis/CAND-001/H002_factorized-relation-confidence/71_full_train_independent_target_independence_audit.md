# H002 Full Train Independent Target Independence Audit

Last updated: 2026-06-17

## Purpose

`70_full_train_independent_label_ingestion.md`에서 ingestion은 성공했지만,
`proposed_audit_role_hidden`이 binary target과 상관되어 있었다. 이번 단계는
original target의 shortcut risk를 정량화하고, posterior smoke를 재개할 수 있는
controlled target slice가 남는지 확인한다.

핵심 질문:

```text
Can we construct a sufficiently large train-only target slice where the binary
target is not explained by hidden role/status/rank metadata?
```

## Decision

Current status:

```text
full_train_independent_target_independence_audit_controlled_slice_ready
```

Meaning:

```text
The original ingested target has hidden metadata shortcut risk, but a
proposed-role-balanced controlled slice remains large enough for train-only
posterior smoke: 158 rows, 79 positive, 79 negative.
```

The next step may resume posterior smoke only on the controlled slice. This is
still not paper-level method evidence because the labels are Codex bootstrap
labels, not human-confirmed labels.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_target_independence_audit.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_target_independence_audit_controlled_slice_ready recommended=proposed_role_balanced_codex_ver rows=158 positive=79 negative=79 validation_used=False
```

## Input

Posterior diagnostic rows from ingestion:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/posterior_rows.jsonl
```

Rows:

```text
283 binary targets
155 positive
128 negative
```

## Boundary

Established:

- train-only.
- no validation/test rows.
- no posterior is trained in this step.
- hidden metadata is used only after label lock for audit and controlled-slice
  construction.
- target-construction metadata is not deployable input.
- multi-view remains audit evidence only, not model input.
- labels are not human-confirmed.
- paper evidence and posterior novelty claims remain blocked.

## Original Target Risk

Original target:

```text
original_independent_codex_ver
```

Rows:

```text
283
```

Original hidden risk:

| Hidden Key | Majority Acc | NMI |
| --- | ---: | ---: |
| `proposed_audit_role_hidden` | 0.7208 | 0.2897 |

Risk thresholds:

| Metric | Threshold |
| --- | ---: |
| majority rule accuracy | 0.85 |
| normalized mutual information | 0.25 |

Interpretation:

```text
The original binary target cannot be used for posterior novelty claims because
it still carries target-construction correlation through proposed_audit_role.
```

## Controlled Slice Results

Candidate criteria:

```text
rows >= 120
min(positive, negative) >= 50
hidden risk count == 0
```

Slice summary:

| Target Slice | Rows | Pos | Neg | Hidden Risks | Candidate |
| --- | ---: | ---: | ---: | ---: | --- |
| `proposed_role_balanced_codex_ver` | 158 | 79 | 79 | 0 | yes |
| `queue_family_balanced_codex_ver` | 162 | 81 | 81 | 0 | yes |
| `label_status_balanced_codex_ver` | 188 | 94 | 94 | 0 | yes |
| `label_status_family_balanced_codex_ver` | 134 | 67 | 67 | 0 | yes |
| `rank_band_balanced_codex_ver` | 218 | 109 | 109 | 0 | yes |
| `rank_family_balanced_codex_ver` | 152 | 76 | 76 | 0 | yes |
| `family_balanced_codex_ver` | 172 | 86 | 86 | 0 | yes |
| `predicate_balanced_codex_ver` | 172 | 86 | 86 | 0 | yes |
| `role_family_balanced_codex_ver` | 114 | 57 | 57 | 0 | no, below row threshold |
| `role_predicate_balanced_codex_ver` | 94 | 47 | 47 | 0 | no, below row/class threshold |
| `queue_balanced_codex_ver` | 218 | 109 | 109 | 1 | no, hidden risk remains |
| `geometry_status_balanced_codex_ver` | 218 | 109 | 109 | 1 | no, hidden risk remains |
| `original_independent_codex_ver` | 283 | 155 | 128 | 1 | no, hidden risk remains |

Recommended primary slice:

```text
proposed_role_balanced_codex_ver
```

Reason:

```text
It directly controls the triggered hidden risk key, proposed_audit_role_hidden,
while preserving 158 rows with balanced positive/negative labels.
```

Slice coverage:

| Family | Rows |
| --- | ---: |
| `support_contact` | 72 |
| `relative_vertical` | 55 |
| `proximity` | 31 |

| Predicate | Rows |
| --- | ---: |
| `lying on` | 33 |
| `close by` | 31 |
| `lower than` | 32 |
| `higher than` | 23 |
| `supported by` | 20 |
| `standing on` | 19 |

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/target_slices/
```

Primary controlled slice:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/target_slices/proposed_role_balanced_codex_ver.jsonl
```

## Interpretation

This audit changes the immediate path:

```text
Do not use the original 283-row target for posterior smoke.
Use the proposed-role-balanced 158-row slice for the next train-only controlled
posterior smoke.
```

This is a hypothesis-stage diagnostic. A positive posterior result on this
slice would suggest the factorized formulation is worth further work, but it
would still not be final paper evidence without human-confirmed or externally
audited labels.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_target_independence_audit.py
```

Observed:

```text
validation_used=False
trains_new_posterior=False
```

## Next TODO

Completed next action:

```text
full_train_independent_controlled_posterior_smoke
```

Result:

```text
full_train_independent_controlled_posterior_no_strong_signal
```

On the 158-row controlled slice, factorized reliability is better than
geometry-only but worse than `semantic_plus_geometry` under scan-grouped
train-only folds.

Next action:

```text
full_train_independent_controlled_error_analysis
```

Goal:

- inspect where factorized posterior loses to semantic+geometry.
- decide whether factor construction or target construction needs revision.
