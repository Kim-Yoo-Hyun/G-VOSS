# H002 Full-Train Independent Support/Vertical V2 True User Review Target Independence Audit

## Purpose

`108_full_train_independent_support_vertical_v2_true_user_review_ingestion.md`에서 만든
70-row true-user-review targets에 대해 dedicated target-independence audit을 실행했다.

핵심 질문:

```text
Can the Codex-proxy pending-confirmation true-user-review target support
posterior smoke, or is it still dominated by hidden prior carryover?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- label은 Codex-proxy pending-confirmation 상태이며 실제 true user/external annotation이 아니다.
- hidden metadata는 label lock 이후 audit과 controlled-slice construction에만 사용한다.
- true-user review fields, hidden strata, previous proxy labels, audit packet paths는 posterior input이 아니다.
- source score/rank와 `p_geom_valid` feature join은 아직 하지 않는다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_true_user_review_target_independence_audit_strict_blocked_construction_slice_available
relation_rows=70
relation_pos=35
relation_neg=35
errors=0
relation_strict=none
relation_construction=rank_band_balanced_true_user_review
validation_used=False
test_used=False
next=revise_true_user_review_target_or_collect_real_user_labels
```

## Per-Target Decisions

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_true_user_review_target` | `blocked_no_controlled_slice` | 70 | 69 | 1 | `none` | `none` |
| `relation_reliability_true_user_review_target` | `strict_blocked_construction_slice_available` | 70 | 35 | 35 | `none` | `rank_band_balanced_true_user_review` |

## Key Risks

`geometry_validity_true_user_review_target`:

- 69/1로 거의 single-class다.
- posterior target으로 부적절하고, 현재 batch에서는 geometry sanity check에 가깝다.
- strict 또는 construction-only controlled slice가 없다.

`relation_reliability_true_user_review_target`:

- 35/35로 균형은 맞다.
- visible non-target risk는 없다.
- 하지만 hidden harmful prior carryover가 그대로 남는다.

Original relation target harmful risks:

| Hidden Key | Majority Acc | NMI | Pos Rate Range |
| --- | ---: | ---: | ---: |
| `relation_validity_label_hidden` | 0.8571 | 0.5096 | 0.8333 |
| `label_use_hidden` | 0.8571 | 0.4572 | 0.7537 |
| `posterior_target_y_hidden` | 0.8571 | 0.4572 | 0.7537 |

Construction-only slice:

| Slice | Rows | Pos | Neg | Harmful Risks | Construction Risks | Strict |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `rank_band_balanced_true_user_review` | 70 | 35 | 35 | 3 | 0 | `False` |

Prior-label-balanced slices:

| Slice | Rows | Pos | Neg | Main Issue |
| --- | ---: | ---: | ---: | --- |
| `prior_relation_validity_balanced_true_user_review` | 20 | 10 | 10 | too small, construction/visible risks remain |
| `prior_label_use_balanced_true_user_review` | 20 | 10 | 10 | too small, residual risk remains |
| `prior_target_y_balanced_true_user_review` | 20 | 10 | 10 | too small, residual risk remains |

## Interpretation

이번 audit은 H002의 현재 blocker를 더 분명하게 만든다.

좋은 점:

- relation reliability target은 visible family/predicate shortcut으로 쉽게 풀리는 target은 아니다.
- rank/queue/geometry-status construction axis는 이미 잘 균형화되어 있다.
- 즉, 단순한 construction artifact 문제는 상당히 줄었다.

문제:

- Codex-proxy pending-confirmation target은 hidden prior label structure를 여전히 강하게 반영한다.
- 이 상태에서 posterior smoke를 실행하면 factorized reliability posterior를 검증하는 것이 아니라
  `relation_validity_label_hidden`, `label_use_hidden`, `posterior_target_y_hidden`을 재현하는
  실험이 될 수 있다.
- 따라서 posterior smoke는 계속 blocked다.

## Decision

```text
posterior_smoke_remains_blocked
```

Reason:

- strict relation reliability slice가 없다.
- construction-only slice는 `rank_band_balanced_true_user_review`로 존재하지만 method-validation evidence가 아니다.
- Codex-proxy label로는 target independence 문제를 충분히 해결하지 못했다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/109_full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/target_slices/relation_reliability_true_user_review_target/rank_band_balanced_true_user_review.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/validation_errors.jsonl
```

## Verification

Line counts:

```text
slice_summaries.csv = 30 rows + header
group_summaries.csv = 330 rows + header
group_table.csv = 774 rows + header
validation_errors.jsonl = 0
```

## Next TODO

Completed by:

```text
110_full_train_independent_support_vertical_v2_true_user_review_target_path_decision.md
```

Previous next action:

```text
revise_true_user_review_target_or_collect_real_user_labels
```

Goal:

- stop treating Codex-proxy true-user labels as method-validation evidence.
- decide whether to revise target construction or collect genuinely independent user/external labels.
- if revising target, remove dependence on hidden prior relation-validity structure rather than adding a stronger posterior combiner.
- keep posterior smoke blocked until a strict or defensible controlled target exists.

New next action:

```text
collect_real_user_labels_on_rank_band70_sheet
```
