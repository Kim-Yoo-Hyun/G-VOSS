# Reliability Target V3 Informative Anchor Label Ingestion

Date: 2026-06-20 KST

## Purpose

`152_reliability_target_v3_informative_anchor_label_fill.md`에서 채운 full `160`개
informative-anchor v3 label을 ingest하고, 세 가지 target을 분리해 만든다.

핵심 질문:

```text
After informative-anchor label fill, do we finally have a usable relation
reliability target, and is it safe enough to open posterior smoke?
```

## Boundary

- Split: Open3DSG train only.
- Validation/test row는 사용하지 않았다.
- Posterior training/smoke는 수행하지 않았다.
- Labels are user-requested Codex proxy labels, not independent human annotation.
- V3 review fields are target/audit fields only, not model input.
- Hidden manifest는 label lock 이후에만 조인했다.
- Multi-view/mesh packet evidence는 audit evidence일 뿐, posterior input이 아니다.
- H001 artifact는 수정하지 않았다.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_ingestion.py
```

Observed:

```text
status=h002_reliability_target_v3_informative_anchor_label_ingested_with_probe_risk
rows=160
rel_binary=82
rel_pos=35
rel_neg=47
geom_binary=85
geom_pos=72
geom_neg=13
use_binary=85
use_pos=37
use_neg=48
errors=0
probe=target_independence_risk_hidden_metadata_correlated
validation_used=False
test_used=False
posterior_allowed=False
next=reliability_target_v3_informative_anchor_target_independence_audit
```

## Result

Status:

```text
h002_reliability_target_v3_informative_anchor_label_ingested_with_probe_risk
```

Decision:

```text
Informative-anchor v3 labels are ingested and binary target mass is usable, but
hidden/visible shortcut probes still flag target-construction risk. Run
target-independence audit before posterior smoke.
```

## Binary Targets

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relation_reliability_v3_binary_target` | 82 | 35 | 47 | 0.4268 | 78 |
| `geometry_support_v3_binary_target` | 85 | 72 | 13 | 0.8471 | 75 |
| `relation_usefulness_v3_binary_target` | 85 | 37 | 48 | 0.4353 | 75 |

Multiclass reliability:

| Class | Count |
| --- | ---: |
| `reliable` | 35 |
| `unreliable_geometry` | 13 |
| `unreliable_trivial` | 34 |
| `uncertain` | 78 |

## Probe Summary

| Target | Probe Status | Hidden Risks | Visible Risks |
| --- | --- | ---: | ---: |
| `relation_reliability_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 11 | 2 |
| `geometry_support_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 13 | 4 |
| `relation_usefulness_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 11 | 2 |

Important probe risks:

- `anchor_category_hidden` strongly predicts relation reliability.
- `endpoint_flag_pattern_hidden`, `subject_object_family_cell_hidden`, and `rank_band_hidden` also show high shortcut risk.
- `asset_packet_source_hidden` is not a binary-target risk here because generated packet rows were excluded as uncertain from binary targets.
- Visible `subject_label` and `object_label` also flag shortcut risk, so the next audit must distinguish real object-relation semantics from construction leakage.

## Interpretation

This is the first informative-anchor v3 stage where the relation reliability binary target has usable mass:

```text
relation reliability = 35 positive / 47 negative
```

This improves the previous object/endpoint attempt:

```text
object/endpoint relation reliability = 8 positive / 99 negative
```

However, it does not yet validate the posterior hypothesis. The positive mass was created by informative-anchor sampling, so a reviewer would ask whether the target is simply recovering the sampling category. The quick probe says this risk is real.

Therefore the next step is not posterior smoke. The next step is a target-independence audit that checks whether there exists a controlled slice where:

- relation reliability has enough positive and negative rows,
- anchor category does not trivially determine the target,
- subject/object label shortcuts are controlled,
- endpoint and rank-band shortcuts are controlled,
- geometry-support and usefulness targets are audited separately,
- posterior input fields remain deployable evidence only.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/153_reliability_target_v3_informative_anchor_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/validated_informative_anchor_v3_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/geometry_support_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/relation_usefulness_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_posterior_candidates.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/target_independence_probe_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/target_independence_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/ingestion_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_informative_anchor_target_independence_audit
```

Goal:

- Determine whether the probe risk is fatal construction leakage or an auditable sampling artifact.
- Audit reliability, geometry-support, and usefulness targets separately.
- Search for strict/diagnostic controlled slices with enough positive and negative rows.
- Keep posterior smoke blocked unless a target-independent controlled slice exists.
