# H002 Reliability Target V4 Matched Contrast Label Ingestion

Date: 2026-06-21 KST

## Purpose

이 단계는 v4 matched-contrast proxy labels를 ingest해서 relation reliability, geometry
support, relation usefulness target artifacts로 분리하는 단계다. Posterior candidate file은
생성하지만 posterior smoke는 실행하지 않는다.

## Boundary

```text
split = train_only
validation_used = False
test_used = False
posterior_trained = False
posterior_smoke_allowed = False
paper_evidence_allowed = False
filled_by = codex_proxy
actual_user_reviewer = False
hidden_manifest_joined_after_label_lock = True
review_fields_as_model_input = False
hidden_sampling_axes_as_model_input = False
multi_view_as_model_input = False
```

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_ingestion.py
```

## Result

```text
status = h002_reliability_target_v4_matched_contrast_label_ingested_with_probe_risk
rows = 158
relation reliability binary = 47 rows, 23 positive, 24 negative
geometry support binary = 47 rows, 30 positive, 17 negative
relation usefulness binary = 50 rows, 25 positive, 25 negative
ingestion errors = 0
relation reliability probe = target_independence_risk_hidden_metadata_correlated
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_target_independence_audit
```

## Binary Target Counts

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relation_reliability_v4_binary_target` | 47 | 23 | 24 | 0.4894 | 111 |
| `geometry_support_v4_binary_target` | 47 | 30 | 17 | 0.6383 | 111 |
| `relation_usefulness_v4_binary_target` | 50 | 25 | 25 | 0.5000 | 108 |

Multiclass target:

| Class | Rows |
| --- | ---: |
| `reliable` | 23 |
| `unreliable` | 24 |
| `uncertain` | 111 |

## Probe Summary

| Target | Probe Status | Hidden Risks | Visible Risks |
| --- | --- | ---: | ---: |
| `relation_reliability_v4_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 3 | 2 |
| `geometry_support_v4_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 3 | 4 |
| `relation_usefulness_v4_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 3 | 2 |

Top relation reliability risks:

| Source | Group Key | NMI | Majority Accuracy | Positive Rate Range |
| --- | --- | ---: | ---: | ---: |
| hidden | `subject_object_family_cell_hidden` | 1.0000 | 1.0000 | 1.0000 |
| hidden | `endpoint_flag_pattern_hidden` | 0.5774 | 0.8085 | 1.0000 |
| hidden | `object_family_cell_hidden` | 0.3937 | 0.7447 | 1.0000 |
| visible | `subject_label` | 0.7764 | 0.9149 | 1.0000 |
| visible | `object_label` | 0.3914 | 0.7447 | 1.0000 |

## Interpretation

- Relation reliability target mass is balanced: `23` positive / `24` negative.
- This is better than positive-sparse earlier targets, so ingestion itself succeeds.
- However, target independence is not established. The target is highly correlated with
  object/family cells and visible object labels.
- The result is therefore not posterior evidence.
- The correct next step is a dedicated target-independence audit, not changing the combiner or
  running posterior smoke.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/162_reliability_target_v4_matched_contrast_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/validated_v4_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_reliability_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/geometry_support_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_usefulness_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_reliability_v4_multiclass_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_reliability_v4_posterior_candidates.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/target_independence_probe_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/target_independence_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/ingestion_errors.jsonl
```

## Next TODO

```text
reliability_target_v4_matched_contrast_target_independence_audit
```

Goal:

- test whether a controlled slice remains after object/family/rank/packet-source risks are removed.
- decide whether posterior smoke is allowed, blocked, or needs another target construction revision.
