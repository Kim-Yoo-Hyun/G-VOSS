# H002 Full-Train Independent Support/Vertical V2 User-Confirmed Review Target Independence Audit

## Purpose

`114_full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.md`에서
생성한 user-confirmed target에 대해 dedicated target-independence audit을 다시 수행했다.

핵심 질문:

```text
Does user confirmation alone produce a strict or defensible controlled
relation-reliability target slice?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- 사용자 확인에 따라 provenance는 `actual_independent_reviewer_verified=True`로 처리한다.
- hidden metadata는 label lock 이후 audit과 controlled-slice construction에만 사용한다.
- 이 단계는 target/evidence contract 검증이며 posterior performance 실험이 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit_blocked
relation_rows=68
relation_pos=35
relation_neg=33
errors=0
relation_strict=none
relation_construction=none
user_confirmed=True
validation_used=False test_used=False
next=expand_user_confirmed_labels_or_revise_sampling_protocol
```

## Per-Target Decision

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_user_confirmed_review_target` | `blocked_no_controlled_slice` | 68 | 57 | 11 | `none` | `none` |
| `relation_reliability_user_confirmed_review_target` | `blocked_no_controlled_slice` | 68 | 35 | 33 | `none` | `none` |

## Original Target Risks

| Target | Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | --- | ---: | ---: | ---: |
| `geometry_validity_user_confirmed_review_target` | `harmful_prior_carryover` | `relation_validity_label_hidden` | 0.8529 | 0.1454 | 1.0000 |
| `geometry_validity_user_confirmed_review_target` | `construction` | `rank_band_hidden` | 0.8382 | 0.2403 | 0.3684 |
| `relation_reliability_user_confirmed_review_target` | `harmful_prior_carryover` | `relation_validity_label_hidden` | 0.7794 | 0.2812 | 1.0000 |
| `relation_reliability_user_confirmed_review_target` | `construction` | `proposed_audit_role_hidden` | 0.6765 | 0.2125 | 0.7500 |

## Interpretation

- 사용자 확인은 provenance 문제를 해결한다.
- 그러나 posterior smoke를 막던 더 큰 문제는 target-independence다.
- relation target은 35/33으로 균형이 좋지만 hidden prior carryover를 제거한 strict slice가 없다.
- construction-only slice도 없다.
- 따라서 현재 70-row user-confirmed target은 posterior method-validation target으로 쓰기 어렵다.
- 다음 단계는 label을 더 많이 모으는 것만이 아니라, hidden prior carryover를 줄이는 sampling
  protocol을 재설계해야 한다.

## Decision

현재 H002 posterior smoke는 계속 blocked다.

선택:

```text
expand_user_confirmed_labels_or_revise_sampling_protocol
```

Reason:

- 70-row label의 provenance는 사용자가 확인했다.
- 하지만 target audit 결과는 `blocked_no_controlled_slice`다.
- 이 상태에서 posterior를 돌리면 factorized reliability가 아니라 hidden prior structure를
  다시 맞추는 실험이 될 위험이 있다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/115_full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_target_independence_audit_rank_band70/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_target_independence_audit_rank_band70/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_target_independence_audit_rank_band70/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_target_independence_audit_rank_band70/validation_errors.jsonl
```

## Verification

Observed:

```text
relation_rows=68
relation_pos=35
relation_neg=33
validation_errors=0
slice_summaries.csv = 31 lines
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
expand_user_confirmed_labels_or_revise_sampling_protocol
```

Goal:

- decide whether to expand to full-127 user-confirmed labels or redesign sampling first.
- prioritize reducing hidden `relation_validity_label_hidden` and `proposed_audit_role_hidden`
  carryover.
- keep posterior smoke blocked until a strict or defensible controlled slice exists.
