# H002 Full-Train Independent Support/Vertical V2 Revised Sampling Target Independence Audit

## Purpose

`118_full_train_independent_support_vertical_v2_revised_sampling_ingestion.md`에서 만든
priority160 revised sampling targets에 대해 target-independence audit을 수행했다.

핵심 질문:

```text
Does revised sampling solve the previous H002 blocker enough to open a
controlled posterior smoke test?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- completed priority160 labels는 user-confirmed workflow labels로 취급한다.
- hidden sampling axes는 label lock 이후 audit과 controlled-slice construction에만 사용한다.
- review fields, hidden sampling axes, multi-view/mesh packet paths는 posterior input이 아니다.
- 이 단계는 target/evidence contract 검증이며 posterior performance evidence가 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit_blocked
relation_rows=122
relation_pos=20
relation_neg=102
errors=0
relation_strict=none
relation_construction=none
user_confirmed=True
validation_used=False test_used=False
next=revise_sampling_or_expand_revised_sampling_labels
```

## Per-Target Decision

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_revised_sampling_user_confirmed_target` | `blocked_no_controlled_slice` | 122 | 95 | 27 | `none` | `none` |
| `relation_reliability_revised_sampling_user_confirmed_target` | `blocked_no_controlled_slice` | 122 | 20 | 102 | `none` | `none` |

## Original Target Risks

| Target | Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | --- | ---: | ---: | ---: |
| `geometry_validity_revised_sampling_user_confirmed_target` | `harmful_prior_carryover` | none | 0.0000 | 0.0000 | 0.0000 |
| `geometry_validity_revised_sampling_user_confirmed_target` | `construction` | `proposed_audit_role_hidden` | 0.8033 | 0.2960 | 0.7143 |
| `geometry_validity_revised_sampling_user_confirmed_target` | `construction` | `label_match_status_hidden` | 0.7787 | 0.1575 | 0.3409 |
| `geometry_validity_revised_sampling_user_confirmed_target` | `visible_non_target` | `predicate_label` | 0.8770 | 0.4522 | 0.7308 |
| `geometry_validity_revised_sampling_user_confirmed_target` | `visible_non_target` | `predicate_family` | 0.8197 | 0.2517 | 0.4910 |
| `relation_reliability_revised_sampling_user_confirmed_target` | `harmful_prior_carryover` | none | 0.0000 | 0.0000 | 0.0000 |
| `relation_reliability_revised_sampling_user_confirmed_target` | `construction` | `proposed_audit_role_hidden` | 0.8607 | 0.3715 | 0.5714 |
| `relation_reliability_revised_sampling_user_confirmed_target` | `construction` | `rank_band_hidden` | 0.8361 | 0.2725 | 0.5000 |
| `relation_reliability_revised_sampling_user_confirmed_target` | `construction` | `queue_kind_hidden` | 0.8361 | 0.2243 | 0.3248 |
| `relation_reliability_revised_sampling_user_confirmed_target` | `expected_geometry_alignment` | `geometry_status_hidden` | 0.8361 | 0.2243 | 0.3248 |
| `relation_reliability_revised_sampling_user_confirmed_target` | `visible_non_target` | `predicate_label` | 0.8607 | 0.1460 | 0.6111 |

## Interpretation

- revised sampling은 previous proxy label carryover는 줄였다.
- 하지만 target-independence 문제를 해결하지 못했다.
- relation reliability target은 binary rows 기준 20 positive / 102 negative로, posterior smoke를 하기에 positive class가 너무 작다.
- strict slice와 construction-only slice가 모두 없다.
- 즉 지금 막힌 이유는 posterior 결합 방식이 아니라 target construction / sampling / label balance 문제다.
- 이 상태에서 posterior를 돌리면 factorized reliability가 아니라 predicate/role/rank/queue 구조를 맞추는 실험이 될 위험이 크다.

## Decision

현재 H002 posterior smoke는 계속 blocked다.

선택:

```text
revise_sampling_or_expand_revised_sampling_labels
```

Reason:

- ingestion과 target audit은 정상적으로 끝났다.
- validation/test는 사용하지 않았다.
- 그러나 relation target의 class balance와 controlled-slice 조건을 만족하지 못했다.
- 다음 단계는 posterior combiner 개선이 아니라, positive relation-reliability target을 더 확보하거나 sampling protocol을 다시 조정하는 것이다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/119_full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_target_independence_audit_priority160_user_confirmed/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_target_independence_audit_priority160_user_confirmed/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_target_independence_audit_priority160_user_confirmed/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_target_independence_audit_priority160_user_confirmed/validation_errors.jsonl
```

## Verification

Observed:

```text
relation_rows=122
relation_pos=20
relation_neg=102
validation_errors=0
slice_summaries.csv = 31 lines
group_summaries.csv = 331 lines
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
revise_sampling_or_expand_revised_sampling_labels
```

Goal:

- increase relation-reliability positive target coverage.
- reduce construction-axis correlation from `proposed_audit_role_hidden`, `rank_band_hidden`, and `queue_kind_hidden`.
- reduce visible predicate shortcut risk.
- keep posterior smoke blocked until a strict or defensible controlled slice exists.
