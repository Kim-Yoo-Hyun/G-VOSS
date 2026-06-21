# H002 Reliability Target V3 Label Ingestion

Date: 2026-06-20 KST

## Purpose

이 단계는 `139_reliability_target_v3_label_fill.md`에서 채운 160-row v3 Codex-proxy
sheet를 ingest하고, H002의 세 축을 분리한 target artifact로 만든다.

중요한 점은 posterior smoke를 재개하는 단계가 아니라는 것이다. Ingestion은 다음을 확인한다.

- v3 schema / allowed value / row identity가 맞는가.
- `relation reliability`, `geometry support`, `relation usefulness` target을 분리해서
  만들 수 있는가.
- binary target mass가 충분한가.
- hidden sampling metadata 또는 visible object-label shortcut이 target과 강하게 얽혀
  있는가.

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior training: not run.
- H001 artifacts: not modified.
- Labels are user-requested Codex proxy labels, not independent human annotation.
- V3 review fields are target/audit fields and must not be posterior input.
- Hidden manifest is joined only after label lock.
- Multi-view/mesh packet evidence remains audit evidence only, not model input.

## Command

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_label_ingestion.py
```

## Result

```text
status = h002_reliability_target_v3_label_ingested_with_probe_risk
rows = 160
ingestion_errors = 0
validation_used = False
test_used = False
next = reliability_target_v3_target_independence_audit
```

## Target Counts

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relation_reliability_v3_binary_target` | 110 | 32 | 78 | 0.2909 | 50 |
| `geometry_support_v3_binary_target` | 113 | 92 | 21 | 0.8142 | 47 |
| `relation_usefulness_v3_binary_target` | 113 | 34 | 79 | 0.3009 | 47 |

Multiclass reliability target:

| Class | Rows |
| --- | ---: |
| `reliable` | 32 |
| `unreliable_geometry` | 21 |
| `unreliable_trivial` | 57 |
| `unreliable_ontology` | 0 |
| `uncertain` | 50 |

## Probe Result

| Target | Probe Status | Hidden Risks | Visible Risks |
| --- | --- | ---: | ---: |
| `relation_reliability_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 2 |
| `geometry_support_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 4 |
| `relation_usefulness_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 2 |

Main reliability target risk:

- Hidden risks include `endpoint_flag_pattern_hidden`, `rank_band_hidden`,
  `sampling_category_hidden`, `expected_v3_role_hidden`, `queue_kind_hidden`,
  `geometry_status_hidden`, and `label_match_status_hidden`.
- Visible shortcut risks include `subject_label` and `object_label`.
- Therefore the target has usable positive mass, but is not yet posterior-ready.

## Interpretation

이번 ingestion은 이전 positive-sparse 문제를 완화했다. Relation reliability binary target은
`32/78`이므로 단순히 positive가 2개뿐이던 endpoint-controlled v2 상태보다 훨씬 낫다.

하지만 posterior를 바로 돌리면 안 된다. 현재 label은 visible heuristic proxy fill이므로
object identity와 hidden construction axes가 target과 강하게 얽혀 있다. 즉, posterior가
semantic/geometry factor를 학습하는 것이 아니라 `floor`, `wall`, endpoint pattern, sampling
bucket 같은 shortcut을 학습할 위험이 남아 있다.

따라서 다음 단계는 posterior smoke가 아니라 dedicated target-independence audit이다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/140_reliability_target_v3_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/validated_v3_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/geometry_support_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/relation_usefulness_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_multiclass_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/target_independence_probe_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/ingestion_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_target_independence_audit
```

이 audit에서는 hidden bucket / endpoint flag / object-label shortcut을 통제한 slice에서
relation reliability target이 여전히 usable한지 확인한다. 그 전까지 posterior smoke는
계속 block한다.
