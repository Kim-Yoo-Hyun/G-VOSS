# Endpoint-Controlled Label Ingestion

Date: 2026-06-20 KST

## Purpose

`endpoint_controlled_label_ingestion`은 packet-ready 상태로 채운 62개
endpoint-controlled Codex-proxy label을 target artifact로 변환하는 단계다. 목표는
posterior를 바로 학습하는 것이 아니라, label lock 이후 hidden endpoint manifest를
join하고, geometry validity target과 relation reliability target의 class balance와
shortcut risk를 확인하는 것이다.

## Boundary

- Open3DSG train-only hypothesis-stage artifact다.
- Validation/test row는 사용하지 않았다.
- Posterior model은 학습하지 않았다.
- Label은 Codex-proxy review field이며 paper-level external human annotation이 아니다.
- Review field, hidden endpoint metadata, packet path, multi-view evidence는
  target/audit 전용이며 posterior input으로 쓰지 않는다.
- Hidden manifest는 label lock 이후에만 join했다.
- H001 산출물은 수정하지 않았다.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_label_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_label_ingestion.py
```

Observed output:

```text
status=h002_endpoint_controlled_label_ingested_positive_sparse labels=62 geom_binary=34 geom_pos=23 geom_neg=11 rel_binary=34 rel_pos=2 rel_neg=32 errors=0 validation_used=False test_used=False next=endpoint_controlled_target_independence_audit
```

## Inputs

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/completed_endpoint_controlled_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/endpoint_controlled_fill_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/endpoint_controlled_full_manifest_post_label_only.jsonl
```

## Target Counts

| Target | Binary Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_endpoint_controlled_target` | 34 | 23 | 11 | 0.6765 | 28 |
| `relation_reliability_endpoint_controlled_target` | 34 | 2 | 32 | 0.0588 | 28 |

By family:

| Target | Family | Positive | Negative |
| --- | --- | ---: | ---: |
| `geometry_validity_endpoint_controlled_target` | `support_contact` | 19 | 4 |
| `geometry_validity_endpoint_controlled_target` | `relative_vertical` | 4 | 7 |
| `relation_reliability_endpoint_controlled_target` | `support_contact` | 2 | 21 |
| `relation_reliability_endpoint_controlled_target` | `relative_vertical` | 0 | 11 |

## Probe Summary

The basic target-independence probe reports hidden-metadata correlation risk for
both target definitions.

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcut Risks |
| --- | --- | ---: | ---: |
| `geometry_validity_endpoint_controlled_target` | `target_independence_risk_hidden_metadata_correlated` | 5 | 1 |
| `relation_reliability_endpoint_controlled_target` | `target_independence_risk_hidden_metadata_correlated` | 8 | 3 |

The strongest immediate issue is not posterior combination. The reliability
target has only 2 positive rows out of 34 binary rows. A model trained here would
mostly learn a degenerate negative-majority target or endpoint construction
artifact rather than factorized relation reliability.

## Interpretation

This ingestion strengthens the H002 decomposition:

```text
geometry validity != relation reliability
```

In the same 34 binary rows, geometry validity is reasonably populated
(`23/11`), but relation reliability is extremely sparse (`2/32`). Therefore,
geometry-supported evidence alone is insufficient to treat an edge as reliable.
The target must also account for informativeness, ontology fit, annotation
support, and uncertainty.

However, this artifact does not validate the factorized posterior. It shows that
the endpoint-controlled fill is useful as failure diagnosis, but relation
reliability is not yet a posterior-ready target.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/validated_endpoint_controlled_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/geometry_validity_endpoint_controlled_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/relation_reliability_endpoint_controlled_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/geometry_validity_endpoint_controlled_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/relation_reliability_endpoint_controlled_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/excluded_endpoint_controlled_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/shortcut_audit.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/target_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/ingestion_errors.jsonl
```

## Decision

Status:

```text
h002_endpoint_controlled_label_ingested_positive_sparse
```

Decision:

```text
Endpoint-controlled labels are ingested, but relation reliability has too few positives for posterior smoke. Run target-independence audit as failure diagnosis, not method evidence.
```

## Next TODO

```text
endpoint_controlled_target_independence_audit
```
