# H002 Full-Train Independent Support/Vertical V2 User-Submitted Review Target Independence Audit

## Purpose

`111_full_train_independent_support_vertical_v2_user_submitted_review_ingestion.md`에서
ingest한 user-submitted 70-row target이 factorized posterior smoke의 target으로 쓸 수
있는지 dedicated audit으로 검증한다.

핵심 질문:

```text
Can the user-submitted relation-reliability target produce a strict or at least
defensible controlled slice that is not explained by hidden prior-label carryover?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- hidden metadata는 label lock 이후 audit과 controlled-slice construction에만 사용한다.
- sheet는 사용자 제출 completed sheet로 처리하지만, `external_reviewer_id`가
  `codex_packet_only_diagnostic`이므로 verified independent external annotation으로
  확정하지 않는다.
- 이 audit은 posterior 결합 방식 성능 평가가 아니라 target/evidence contract 검증이다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit_blocked
relation_rows=68
relation_pos=35
relation_neg=33
errors=0
relation_strict=none
relation_construction=none
reviewer_id_caveat=True
validation_used=False test_used=False
next=confirm_reviewer_independence_or_collect_external_labels
```

## Per-Target Decision

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_user_submitted_review_target` | `blocked_no_controlled_slice` | 68 | 57 | 11 | `none` | `none` |
| `relation_reliability_user_submitted_review_target` | `blocked_no_controlled_slice` | 68 | 35 | 33 | `none` | `none` |

## Original Target Risks

| Target | Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | --- | ---: | ---: | ---: |
| `geometry_validity_user_submitted_review_target` | `harmful_prior_carryover` | `relation_validity_label_hidden` | 0.8529 | 0.1454 | 1.0000 |
| `geometry_validity_user_submitted_review_target` | `construction` | `rank_band_hidden` | 0.8382 | 0.2403 | 0.3684 |
| `relation_reliability_user_submitted_review_target` | `harmful_prior_carryover` | `relation_validity_label_hidden` | 0.7794 | 0.2812 | 1.0000 |
| `relation_reliability_user_submitted_review_target` | `construction` | `proposed_audit_role_hidden` | 0.6765 | 0.2125 | 0.7500 |

## Interpretation

- user-submitted label은 기존 Codex-proxy true-user path보다 target balance가 좋아졌다.
- relation reliability target은 68 rows, 35/33으로 balanced에 가깝고 visible
  non-target shortcut은 0이다.
- 하지만 hidden prior carryover가 남아 strict slice가 없다.
- construction-only slice도 없다. 즉, 이번 sheet는 posterior method validation으로
  바로 쓰기 어렵다.
- geometry validity target은 57/11로 개선됐지만 min class 11이라 controlled slice
  기준에서 여전히 작다.
- reviewer id caveat가 남아 있으므로, 독립 reviewer provenance도 별도로 확인해야 한다.

## Decision

현재 H002 posterior smoke는 계속 blocked다.

선택:

```text
confirm_reviewer_independence_or_collect_external_labels
```

Reason:

- reviewer id caveat를 해소해야 label source 독립성을 주장할 수 있다.
- 그와 별개로 target-independence audit도 strict/construction slice를 만들지 못했다.
- 따라서 다음 단계는 같은 sheet provenance를 확인하거나, prior-label carryover가 덜한
  external label protocol로 추가 label을 확보하는 것이다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/112_full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_target_independence_audit_rank_band70/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_target_independence_audit_rank_band70/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_target_independence_audit_rank_band70/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_target_independence_audit_rank_band70/validation_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.py
```

Observed:

```text
relation_rows=68
relation_pos=35
relation_neg=33
validation_errors=0
strict_ready_targets=[]
construction_only_targets=[]
blocked_targets=[
  "geometry_validity_user_submitted_review_target",
  "relation_reliability_user_submitted_review_target"
]
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
confirm_reviewer_independence_or_collect_external_labels
```

Goal:

- confirm whether the completed sheet should be treated as actual user/human labels despite
  `codex_packet_only_diagnostic` reviewer id.
- if not confirmable, collect external labels with reviewer id/provenance fixed.
- if confirmable, still treat posterior smoke as blocked until a controlled target slice clears
  hidden prior carryover or a revised sampling protocol fixes the carryover.
- keep multi-view as audit evidence only and validation/test unavailable.
