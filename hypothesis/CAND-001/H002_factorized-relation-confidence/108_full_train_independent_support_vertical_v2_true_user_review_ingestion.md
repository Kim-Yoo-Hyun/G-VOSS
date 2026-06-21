# H002 Full-Train Independent Support/Vertical V2 True User Review Ingestion

## Purpose

`107_full_train_independent_support_vertical_v2_true_user_review_fill.md`에서 만든
70-row `rank_band70` Codex-proxy pending-confirmation review labels를 ingest했다.

이번 단계의 목표는 성능 검증이 아니라 다음을 확인하는 것이다.

- completed review sheet와 post-label-only manifest가 1:1로 맞는지 검증한다.
- review fields에서 `geometry_validity_true_user_review_target`과
  `relation_reliability_true_user_review_target`을 만든다.
- hidden metadata를 label lock 이후에만 join해서 target-independence probe를 실행한다.
- posterior smoke를 열어도 되는지 판단한다.

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- Codex-proxy pending-confirmation label이므로 실제 true user/external annotation이 아니다.
- paper evidence 또는 method-validation evidence로 쓰기 전에는 사용자 확인이 필요하다.
- review fields, hidden metadata, previous proxy labels, multi-view packet paths는 target/audit only이며 posterior input이 아니다.
- source score/rank와 `p_geom_valid`는 아직 join하지 않았다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_ingestion.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_true_user_review_ingested_with_basic_probe_risk
labels=70
geom_binary=70
geom_pos=69
geom_neg=1
rel_binary=70
rel_pos=35
rel_neg=35
errors=0
validation_used=False
test_used=False
next=true_user_review_rank_band70_target_independence_audit
```

## Target Counts

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_true_user_review_target` | 70 | 69 | 1 | 0.9857 | 0 |
| `relation_reliability_true_user_review_target` | 70 | 35 | 35 | 0.5000 | 0 |

`geometry_validity_true_user_review_target`은 거의 전부 positive라서 posterior method
검증 target으로는 약하다. 이 target은 현재 batch에서는 geometry evidence가 대체로
predicate를 지지한다는 sanity check에 가깝다.

`relation_reliability_true_user_review_target`은 35/35로 균형이 맞지만, 아래 probe에서
hidden prior carryover가 남아 있어 아직 posterior smoke를 열 수 없다.

## Basic Target-Independence Probe

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_true_user_review_target` | `target_independence_risk_hidden_metadata_correlated` | 8 | 3 |
| `relation_reliability_true_user_review_target` | `target_independence_risk_hidden_metadata_correlated` | 3 | 0 |

Key interpretation:

- relation reliability target은 visible non-target shortcut이 0이다.
- 그러나 hidden `relation_validity_label_hidden`, `label_use_hidden`,
  `posterior_target_y_hidden`과 여전히 강하게 연결된다.
- 따라서 이 ingestion은 label plumbing과 target materialization에는 성공했지만,
  posterior novelty 검증으로 바로 넘어가면 안 된다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/108_full_train_independent_support_vertical_v2_true_user_review_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/validated_true_user_review_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/geometry_validity_true_user_review_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/relation_reliability_true_user_review_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/geometry_validity_true_user_review_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/relation_reliability_true_user_review_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/target_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/shortcut_audit.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/ingestion_errors.jsonl
```

## Verification

Line counts:

```text
validated_true_user_review_labels.jsonl = 70
geometry_validity_true_user_review_targets.jsonl = 70
relation_reliability_true_user_review_targets.jsonl = 70
ingestion_errors.jsonl = 0
```

## Decision

```text
posterior_smoke_remains_blocked
```

Reason:

- relation reliability target 자체는 balanced 70 rows다.
- 하지만 target-independence probe에서 hidden prior risks가 남았다.
- dedicated target-independence audit으로 strict 또는 construction-only slice를 다시 확인해야 한다.

## Next TODO

Completed by:

```text
109_full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.md
```

Previous next action:

```text
true_user_review_rank_band70_target_independence_audit
```

Goal:

- run dedicated target-independence audit on the ingested true-user review targets.
- check whether a strict relation reliability slice exists.
- if only construction slice exists, keep it as plumbing/error-diagnostic evidence.
- keep posterior smoke blocked unless a strict or defensible controlled target exists.

New next action:

```text
revise_true_user_review_target_or_collect_real_user_labels
```
