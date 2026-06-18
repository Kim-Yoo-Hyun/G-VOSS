# H002 Full Train Independent Label Ingestion

Last updated: 2026-06-17

## Purpose

`69_full_train_independent_label_fill.md`에서 355개
`(codex_ver_full_train_independent)` label을 채웠다. 이번 단계는 label lock 이후
처음으로 `internal_key.jsonl`을 join해 binary/multiclass target과 posterior
diagnostic row를 materialize한다.

핵심 질문:

```text
After label lock, can the independent labels be ingested cleanly, and do they
still show target-construction shortcut risk?
```

## Decision

Current status:

```text
full_train_independent_label_ingested_with_target_policy_risk
```

Meaning:

```text
Ingestion succeeds with 0 schema errors and 283 binary targets, but the basic
target probe detects hidden metadata correlation through proposed_audit_role.
```

Therefore, the next step is not posterior smoke. The next step is a dedicated
target-independence audit.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_ingestion.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_ingestion.py
```

Observed:

```text
status=full_train_independent_label_ingested_with_target_policy_risk labels=355 binary=283 positive=155 negative=128 errors=0 probe=target_independence_risk_hidden_metadata_correlated validation_used=False
```

## Input

Completed sheet:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/completed_all_sheet_codex_ver.tsv
```

Hidden key joined after label lock:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/internal_key.jsonl
```

Locked schema:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/label_ingestion_schema.json
```

## Boundary

Established:

- train-only.
- no validation/test rows.
- no posterior is trained.
- completed labels are joined to hidden provenance only after label lock.
- hidden target-construction metadata is audit-only.
- deployable posterior evidence and audit-only metadata are separated.
- labels remain Codex bootstrap labels, not human-confirmed labels.
- paper evidence and posterior novelty claims remain blocked.

## Materialized Targets

Counts:

| Item | Rows |
| --- | ---: |
| completed sheet rows | 355 |
| validated label rows | 355 |
| multiclass target rows | 355 |
| binary target rows | 283 |
| positive rows | 155 |
| negative rows | 128 |
| ingestion errors | 0 |

Label counts:

| Label | Rows |
| --- | ---: |
| `reliable_informative` | 128 |
| `annotation_sparsity_candidate` | 27 |
| `valid_but_trivial_dense` | 92 |
| `invalid_relation` | 24 |
| `invalid_pair` | 12 |
| `ontology_mismatch` | 8 |
| `abstain_uncertain` | 64 |

Generated target files:

```text
validated_labels.jsonl
multiclass_targets.jsonl
binary_targets.jsonl
posterior_rows.jsonl
```

`posterior_rows.jsonl` separates:

```text
deployable_evidence_after_label_lock
hidden_audit_metadata_post_label_only
```

The former can be used for train-only posterior diagnostics. The latter is only
for target-independence probes.

## Target Probe

Basic group-level target probe result:

```text
target_independence_risk_hidden_metadata_correlated
```

The triggered hidden risk:

| Source | Group Key | Majority Acc | NMI |
| --- | --- | ---: | ---: |
| `hidden_post_label_audit` | `proposed_audit_role_hidden` | 0.7208 | 0.2897 |

Other notable groups:

| Source | Group Key | Majority Acc | NMI |
| --- | --- | ---: | ---: |
| `hidden_post_label_audit` | `label_match_status_hidden` | 0.6678 | 0.1584 |
| `visible_label_surface` | `predicate_label` | 0.6961 | 0.1318 |
| `visible_label_surface` | `predicate_family` | 0.6961 | 0.1222 |

Interpretation:

```text
The target is cleaner than the earlier controlled target because the fill did
not read hidden role/status/rank metadata. However, candidate sampling and
visible category policy still correlate with proposed_audit_role. This target
cannot yet support posterior novelty claims.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/validated_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/multiclass_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/ingestion_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/target_group_table.csv
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `validated_labels.jsonl` | 355 |
| `multiclass_targets.jsonl` | 355 |
| `binary_targets.jsonl` | 283 |
| `posterior_rows.jsonl` | 283 |
| `ingestion_errors.jsonl` | 0 |
| `target_group_table.csv` | 52 + header |

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_ingestion.py
```

Observed:

```text
validation_used=False
errors=0
trains_new_posterior=False
```

## Next TODO

Completed next action:

```text
full_train_independent_target_independence_audit
```

Result:

```text
full_train_independent_target_independence_audit_controlled_slice_ready
```

The original 283-row target has hidden metadata risk, but
`proposed_role_balanced_codex_ver` is available as a 158-row controlled slice
with 79 positive and 79 negative rows.

Next action:

```text
full_train_independent_controlled_posterior_smoke
```

Goal:

- run posterior smoke only on the controlled slice.
- keep original target as diagnostic reference.
- do not use validation/test or paper-level claims.
