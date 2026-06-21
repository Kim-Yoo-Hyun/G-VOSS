# H002 Full-Train Independent Support/Vertical V2 Human Label Ingestion

## Purpose

`99_full_train_independent_support_vertical_v2_human_label_fill.md`에서 채운 full 127-row
sheet를 ingest하여 H002의 scoped human-target artifacts를 만들었다.

이번 단계의 역할은 다음과 같다.

- filled sheet를 schema에 맞게 검증한다.
- `geometry_validity_human_target`을 만든다.
- `relation_reliability_human_target`을 만든다.
- posterior row artifact를 만든다.
- dedicated target-independence audit 전에 basic probe risk를 확인한다.

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- labels are Codex proxy human fields pending user review.
- workflow에서는 사용자 요청에 따라 human-confirmed로 취급하고 다음 hypothesis step을
  진행한다.
- paper evidence로 쓰기 전에는 사용자 확인이 필요하다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_ingestion.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_human_label_ingested_with_basic_probe_risk
labels=127
geom_binary=102 geom_pos=81 geom_neg=21
rel_binary=102 rel_pos=32 rel_neg=70
errors=0 validation_used=False test_used=False
next=full_train_independent_support_vertical_v2_human_target_independence_audit
```

## Target Counts

| Target | Binary Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_human_target` | 102 | 81 | 21 | 0.7941 | 25 |
| `relation_reliability_human_target` | 102 | 32 | 70 | 0.3137 | 25 |

Interpretation:

- Geometry validity target은 geometry evidence가 성립하는지에 가까운 target이다.
- Relation reliability target은 semantic/label plausibility와 geometry agreement를
  함께 반영한 stricter target이다.
- H002의 main target은 `relation_reliability_human_target`이다.
- `geometry_validity_human_target`은 geometry-only baseline 및 failure diagnosis에 쓴다.

## Basic Probe Result

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_human_target` | `target_independence_risk_hidden_metadata_correlated` | 6 | 1 |
| `relation_reliability_human_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 1 |

Interpretation:

- Ingestion 자체는 성공했지만, basic probe는 hidden metadata correlation risk를 계속
  표시한다.
- 이 probe는 strict pass/fail gate가 아니라 다음 audit에서 확인할 위험 신호다.
- posterior smoke는 아직 열지 않는다.
- 다음 단계는 target-independence audit에서 relation-reliability target이 score/rank,
  `p_geom_valid`, geometry status, construction slice shortcut 없이 유지되는지 확인하는
  것이다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/validated_human_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/geometry_validity_human_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/relation_reliability_human_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/geometry_validity_human_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/relation_reliability_human_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/excluded_human_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/target_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/shortcut_audit.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/ingestion_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_ingestion.py
```

Observed line counts:

```text
validated_human_labels.jsonl = 127
geometry_validity_human_targets.jsonl = 102
relation_reliability_human_targets.jsonl = 102
geometry_validity_human_posterior_rows.jsonl = 102
relation_reliability_human_posterior_rows.jsonl = 102
excluded_human_targets.jsonl = 25
ingestion_errors.jsonl = 0
```

## Next TODO

Next action:

```text
completed_by_101_full_train_independent_support_vertical_v2_human_target_independence_audit
```

Goal:

- The requested audit was completed in
  `101_full_train_independent_support_vertical_v2_human_target_independence_audit.md`.
- Current active next action is
  `revise_human_label_protocol_or_add_external_review_evidence`.
