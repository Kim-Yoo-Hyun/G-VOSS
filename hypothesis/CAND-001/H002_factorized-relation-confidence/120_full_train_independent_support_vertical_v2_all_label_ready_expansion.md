# H002 Full-Train Independent Support/Vertical V2 All-Label-Ready Expansion

## Purpose

`119_full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.md`의
next TODO인 `revise_sampling_or_expand_revised_sampling_labels`를 진행했다. priority160만으로는
relation reliability target이 20/102로 불균형했고 strict slice가 없었기 때문에, 기존
sampling protocol이 이미 materialize한 all-label-ready 302개 후보를 모두 user-confirmed
workflow label로 확장했다.

핵심 질문:

```text
Is the current blocker solved by expanding revised-sampling labels, or does H002
need another sampling redesign before posterior smoke?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- all-label-ready labels는 user-confirmed workflow labels로 취급한다.
- hidden sampling axes는 label lock 이후 audit과 controlled-slice construction에만 사용한다.
- review fields, hidden sampling axes, multi-view/mesh packet paths는 posterior input이 아니다.
- 이 단계는 target/evidence contract 검증이며 posterior performance evidence가 아니다.

## Execution

```bash
python3 -m py_compile \
  hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py \
  hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_ingestion.py \
  hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.py

python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py \
  --input-sheet hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_sheet_all_label_ready.tsv \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_all_label_ready_user_confirmed \
  --output-tag all_label_ready

python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_ingestion.py \
  --batch-tag all_label_ready \
  --completed-sheet hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_all_label_ready_user_confirmed/completed_revised_sampling_sheet_all_label_ready_user_confirmed.tsv \
  --fill-summary hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_all_label_ready_user_confirmed/summary.json \
  --internal-manifest hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_manifest_all_label_ready_post_label_only.jsonl \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_all_label_ready_user_confirmed

python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.py \
  --batch-tag all_label_ready \
  --ingestion-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_all_label_ready_user_confirmed \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_target_independence_audit_all_label_ready_user_confirmed
```

Observed:

```text
fill:
status=full_train_independent_support_vertical_v2_revised_sampling_all_label_ready_filled_user_confirmed
rows=302 reliable=70 unreliable=161 uncertain=71 errors=0
validation_used=False test_used=False
next=revised_sampling_all_label_ready_label_ingestion

ingestion:
status=full_train_independent_support_vertical_v2_revised_sampling_ingested_with_basic_probe_risk
labels=302
geom_binary=231 geom_pos=198 geom_neg=33
rel_binary=231 rel_pos=70 rel_neg=161
errors=0
validation_used=False test_used=False
next=revised_sampling_all_label_ready_target_independence_audit

audit:
status=full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit_relation_strict_slice_ready
relation_rows=231
relation_pos=70
relation_neg=161
errors=0
relation_strict=rank_band_balanced_revised_sampling
relation_construction=none
validation_used=False test_used=False
next=revised_sampling_all_label_ready_source_feature_join
```

## Target Counts

| Target | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| `geometry_validity_revised_sampling_user_confirmed_target` | 231 | 198 | 33 |
| `relation_reliability_revised_sampling_user_confirmed_target` | 231 | 70 | 161 |

## Strict Slice

| Target | Strict Slice | Rows | Positive | Negative | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| `geometry_validity_revised_sampling_user_confirmed_target` | `role_balanced_revised_sampling` | 66 | 33 | 33 | strict controlled slice ready |
| `relation_reliability_revised_sampling_user_confirmed_target` | `rank_band_balanced_revised_sampling` | 134 | 67 | 67 | strict controlled slice ready |

Relation strict slice details:

```text
slice = rank_band_balanced_revised_sampling
balanced_keys = [rank_band_hidden]
rows = 134
positive = 67
negative = 67
harmful_prior_risk_count = 0
construction_risk_count = 0
expected_geometry_alignment_risk_count = 0
visible_non_target_risk_count = 0
```

## Interpretation

- priority160에서 막힌 원인은 posterior combiner가 아니라 relation-positive coverage 부족이었다.
- all-label-ready 302개로 확장하면 relation target이 70 positive / 161 negative까지 늘어난다.
- 원본 231 binary rows에는 여전히 class imbalance가 있지만, `rank_band_hidden`을 balance한
  134-row strict relation slice가 생겼다.
- 이 strict slice는 harmful prior, construction, expected geometry alignment, visible
  non-target risk count가 모두 0으로 보고되었다.
- 따라서 지금은 추가 sampling redesign보다 source feature join으로 넘어가는 것이 맞다.
- 단, 이 결과는 hypothesis-stage train-only user-confirmed workflow artifact이며, 아직
  posterior 성능 claim은 아니다.

## Decision

선택:

```text
expand_revised_sampling_to_all_label_ready
```

Reason:

- all-label-ready expansion이 strict relation-reliability controlled slice를 열었다.
- 현재 H002는 posterior smoke를 위한 target/evidence contract 최소 조건을 처음으로 만족했다.
- 다음 단계는 strict slice에 source semantic / geometry / coverage evidence를 join하되,
  review fields와 hidden audit metadata를 posterior input으로 넣지 않는 것이다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/120_full_train_independent_support_vertical_v2_all_label_ready_expansion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_all_label_ready_user_confirmed/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_all_label_ready_user_confirmed/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_target_independence_audit_all_label_ready_user_confirmed/summary.json
```

## Verification

Observed line counts:

```text
completed_revised_sampling_sheet_all_label_ready_user_confirmed.tsv = 303 lines
revised_sampling_all_label_ready_user_confirmed_labels.jsonl = 302
validated_revised_sampling_user_confirmed_labels.jsonl = 302
relation_reliability_revised_sampling_user_confirmed_targets.jsonl = 231
slice_summaries.csv = 31 lines
validation_errors.jsonl = 0
```

## Next TODO

Current next action:

```text
revised_sampling_all_label_ready_source_feature_join
```

Goal:

- join source semantic score/rank, geometry evidence, and coverage fields for the strict relation slice.
- exclude review fields, target labels, hidden audit metadata, and packet paths from posterior input.
- prepare controlled posterior smoke only on the strict relation slice.
