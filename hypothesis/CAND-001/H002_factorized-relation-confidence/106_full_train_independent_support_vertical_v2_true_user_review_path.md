# H002 Full-Train Independent Support/Vertical V2 True User Review Path

## Purpose

`105_full_train_independent_support_vertical_v2_external_review_target_independence_audit.md`에서
external proxy target도 strict method-validation target이 되지 못한다는 것을 확인했다.
이번 단계는 proxy label을 더 늘리는 대신 true user/external review path를 고정한다.

핵심 질문:

```text
Should H002 keep revising proxy labels, or stop proxy labels as method evidence
and collect true user/external labels on a controlled batch?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- 이번 단계는 label을 채우지 않는다.
- proxy labels는 method-validation evidence로 쓰지 않는다.
- multi-view/mesh/contact packet은 review evidence이며 model input이 아니다.
- source score/rank, `p_geom_valid`, deterministic geometry status, numeric witness,
  previous proxy labels, hidden prior labels은 labeler-visible field가 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_path.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_true_user_review_path_ready
rank_rows=70
full_rows=127
missing_rank_ids=0
rank_header_leaks=0
rank_packet_errors=0
validation_used=False
test_used=False
next=fill_true_user_review_sheet_rank_band70_or_user_confirmed_labels
```

## Decision

선택:

```text
collect_true_user_labels_on_rank_band70_first
```

판단:

- proxy label은 여기서 method-validation evidence로 중단한다.
- revised external review surface는 visible/construction shortcut을 줄였지만, proxy label
  자체는 harmful prior carryover를 제거하지 못했다.
- posterior smoke를 열기 전에 true user/external labels가 필요하다.
- 가장 효율적인 first pass는 `rank_band_balanced_external` 70 rows다.

## Why Proxy Stops Here

External review audit에서 relation reliability target은 다음 상태였다.

```text
relation_reliability_external_target
rows = 116
positive = 47
negative = 69
strict_slice = none
construction_diagnostic = rank_band_balanced_external
```

`rank_band_balanced_external` diagnostic:

```text
rows = 70
positive = 35
negative = 35
harmful_prior_risk_count = 3
construction_risk_count = 0
expected_geometry_alignment_risk_count = 0
visible_non_target_risk_count = 0
```

해석:

- labeler-visible surface와 construction shortcut은 상당히 통제됐다.
- 그럼에도 hidden prior carryover가 남는다.
- 이는 proxy rule이 candidate selection과 hidden prior structure를 재현할 가능성을 뜻한다.
- 따라서 더 강한 combiner나 더 많은 proxy label은 문제 원인을 해결하지 않는다.

## Review Batches

| Batch | Rows | Role | Proxy Planning Balance |
| --- | ---: | --- | --- |
| `rank_band70` | 70 | recommended first pass | 35 positive / 35 negative by proxy target; planning only |
| `full127` | 127 | optional expansion | 47 positive / 69 negative among 116 binary rows by proxy target; planning only |

`rank_band70` composition:

| Field | Counts |
| --- | --- |
| family | `relative_vertical`: 30, `support_contact`: 40 |
| predicate | `higher than`: 13, `lower than`: 17, `lying on`: 11, `standing on`: 14, `supported by`: 15 |
| packet status | `ready`: 67, `ready_with_packet_caveat`: 3 |

`full127` composition:

| Field | Counts |
| --- | --- |
| family | `relative_vertical`: 55, `support_contact`: 72 |
| predicate | `higher than`: 23, `lower than`: 32, `lying on`: 33, `standing on`: 19, `supported by`: 20 |
| packet status | `ready`: 124, `ready_with_packet_caveat`: 3 |

## Leakage Checks

| Check | Count |
| --- | ---: |
| rank-band header leakage | 0 |
| full header leakage | 0 |
| rank-band packet path errors | 0 |
| full packet path errors | 0 |
| missing rank-band ids | 0 |

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/106_full_train_independent_support_vertical_v2_true_user_review_path.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_path.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_review_sheet_rank_band70.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_review_sheet_full127.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_manifest_rank_band70_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_manifest_full127_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_review_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/reviewer_instructions.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/rank_band70_header_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/rank_band70_packet_path_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_path.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_path.py
```

Line counts:

```text
true_user_review_sheet_rank_band70.tsv = 70 rows + header
true_user_review_sheet_full127.tsv = 127 rows + header
true_user_manifest_rank_band70_post_label_only.jsonl = 70
true_user_manifest_full127_post_label_only.jsonl = 127
rank_band70_header_leakage_hits.jsonl = 0
rank_band70_packet_path_errors.jsonl = 0
```

## Next TODO

Completed by:

```text
107_full_train_independent_support_vertical_v2_true_user_review_fill.md
```

Previous next action:

```text
fill_true_user_review_sheet_rank_band70_or_user_confirmed_labels
```

Goal:

- fill `true_user_review_sheet_rank_band70.tsv` from packet evidence.
- do not use proxy labels, hidden metadata, numeric witness values, source score/rank, or `p_geom_valid`.
- ingest true-user labels after label lock.
- rerun target-independence audit.
- open posterior smoke only if a strict or defensible target exists.

New next action:

```text
true_user_review_rank_band70_label_ingestion
```
