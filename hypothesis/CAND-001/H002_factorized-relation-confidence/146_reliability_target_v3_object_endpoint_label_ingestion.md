# H002 Reliability Target V3 Object/Endpoint Label Ingestion

Date: 2026-06-20 KST

## Purpose

`145_reliability_target_v3_object_endpoint_label_fill.md`에서 채운 train-only `130`개
object/endpoint-controlled v3 label을 ingest하고, 세 가지 target을 분리해 만든다.

핵심 질문:

```text
After label fill, what binary targets are actually available for reliability,
geometry support, and relation usefulness, and are they safe enough to open
posterior smoke?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior training/smoke: not run.
- Labels are user-requested Codex proxy labels, not independent human annotation.
- V3 review fields are target/audit fields only, not model input.
- Hidden manifest is joined only after label lock.
- Multi-view/mesh packet evidence remains audit evidence only, not posterior input.
- H001 artifacts: not modified.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_label_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_label_ingestion.py
```

Observed:

```text
status=h002_reliability_target_v3_object_endpoint_label_ingested_positive_sparse_with_probe_risk
rows=130
rel_binary=107
rel_pos=8
rel_neg=99
geom_binary=111
geom_pos=85
geom_neg=26
use_binary=111
use_pos=10
use_neg=101
errors=0
probe=target_independence_risk_hidden_metadata_correlated
validation_used=False
test_used=False
posterior_allowed=False
next=reliability_target_v3_object_endpoint_target_independence_audit
```

## Result

Status:

```text
h002_reliability_target_v3_object_endpoint_label_ingested_positive_sparse_with_probe_risk
```

Decision:

```text
Object/endpoint v3 labels are ingested, but the main relation reliability target
is positive-sparse and shortcut probes still flag construction risk. Run
target-independence audit before any posterior smoke.
```

## Binary Targets

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relation_reliability_v3_binary_target` | 107 | 8 | 99 | 0.0748 | 23 |
| `geometry_support_v3_binary_target` | 111 | 85 | 26 | 0.7658 | 19 |
| `relation_usefulness_v3_binary_target` | 111 | 10 | 101 | 0.0901 | 19 |

Multiclass reliability:

| Class | Count |
| --- | ---: |
| `reliable` | 8 |
| `unreliable_geometry` | 26 |
| `unreliable_trivial` | 73 |
| `uncertain` | 23 |

## Probe Summary

| Target | Probe Status | Hidden Risks | Visible Risks |
| --- | --- | ---: | ---: |
| `relation_reliability_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 10 | 5 |
| `geometry_support_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 6 | 4 |
| `relation_usefulness_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 10 | 5 |

Important caveat:

```text
The quick probe is imbalance-sensitive.
```

For `relation_reliability_v3_binary_target`, positive rate is only `8/107`.
Therefore majority-rule accuracy is high even for many grouping keys. The next
target-independence audit must separate:

- genuine shortcut correlation,
- positive-sparse majority baseline artifact,
- object/endpoint cell design failure,
- and relation-reliability definition failure.

## Interpretation

This ingestion confirms the strongest current H002 issue:

```text
geometry_support has mass, relation_reliability does not.
```

`geometry_support_v3_binary_target` has `85/26` positive/negative rows, but
`relation_reliability_v3_binary_target` has only `8/99`. This means the label
schema successfully separates geometric satisfiability from reliability, but the
current object/endpoint-controlled sample still does not provide a posterior-ready
main reliability target.

Therefore the next step is not a combiner upgrade. The immediate scientific
question is whether the failure comes from:

- too many trivial room/surface relations in the mined cells,
- a too strict reliability definition,
- insufficient positive informative pairs,
- or remaining endpoint/object shortcut construction.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/146_reliability_target_v3_object_endpoint_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/validated_object_endpoint_v3_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/geometry_support_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/relation_usefulness_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/target_independence_probe_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/target_independence_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/ingestion_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_object_endpoint_target_independence_audit
```

Goal:

- Determine whether the failure is true shortcut risk or positive-sparse artifact.
- Audit reliability, geometry-support, and usefulness targets separately.
- Check strict/diagnostic controlled slices.
- Keep posterior smoke blocked unless a target-independent controlled slice exists.
