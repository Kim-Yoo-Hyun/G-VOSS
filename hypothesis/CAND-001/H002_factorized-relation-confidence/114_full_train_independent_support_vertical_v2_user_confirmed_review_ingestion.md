# H002 Full-Train Independent Support/Vertical V2 User-Confirmed Review Ingestion

## Purpose

사용자가 70-row sheet를 직접 채운 것으로 취급하라고 명시했으므로, 기존
`user-submitted` provenance caveat를 user confirmation으로 해소하고 별도
`user-confirmed` target artifact를 생성했다.

핵심 질문:

```text
If the 70-row sheet is treated as user-completed, do the materialized targets
change enough to open target-independence audit and posterior smoke?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- 원본 sheet의 `external_reviewer_id=codex_packet_only_diagnostic`는 artifact provenance로
  그대로 기록한다.
- 사용자 확인에 따라 `actual_independent_reviewer_verified=True`로 별도 user-confirmed
  artifact를 생성한다.
- review fields는 target/audit only이며 posterior input이 아니다.
- hidden metadata는 label lock 이후 audit에만 사용한다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_user_confirmed_review_ingested_with_basic_probe_risk
labels=70
geom_binary=68 geom_pos=57 geom_neg=11
rel_binary=68 rel_pos=35 rel_neg=33
errors=0
user_confirmed=True
independent_verified=True
validation_used=False test_used=False
next=user_confirmed_rank_band70_target_independence_audit
```

## Target Counts

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_user_confirmed_review_target` | 68 | 57 | 11 | 0.8382 | 2 |
| `relation_reliability_user_confirmed_review_target` | 68 | 35 | 33 | 0.5147 | 2 |

## Interpretation

- 사용자 확인으로 provenance caveat는 user-confirmed artifact 안에서 해소했다.
- 하지만 label 값 자체는 동일하므로 target distribution도 동일하다.
- relation target은 35/33으로 균형이 좋지만 basic target-independence probe risk가 남았다.
- geometry target은 57/11로 negative count가 작다.
- 따라서 바로 posterior smoke로 가지 않고 dedicated target-independence audit을 다시 수행한다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/114_full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_ingestion_rank_band70/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_ingestion_rank_band70/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_ingestion_rank_band70/validated_user_confirmed_review_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_ingestion_rank_band70/geometry_validity_user_confirmed_review_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_ingestion_rank_band70/relation_reliability_user_confirmed_review_targets.jsonl
```

## Verification

Observed:

```text
validated_user_confirmed_review_labels.jsonl = 70
geometry_validity_user_confirmed_review_targets.jsonl = 68
relation_reliability_user_confirmed_review_targets.jsonl = 68
ingestion_errors.jsonl = 0
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
user_confirmed_rank_band70_target_independence_audit
```

Goal:

- rerun target-independence audit with provenance resolved as user-confirmed.
- check whether strict or construction-only controlled target slice exists.
- keep posterior smoke blocked until the audit clears.
