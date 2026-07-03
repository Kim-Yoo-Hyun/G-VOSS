# Source Reranking Claim Boundary Lock

## 2026-07-02 Decision Update

목적:

Source-reranking metric result review 이후 paper-facing claim boundary를 고정했다.
이 단계는 새 metric을 계산하는 단계가 아니라, official validation source candidates에서
`S2_source_x_Ce` 결과를 어떤 범위의 논문 evidence로 사용할 수 있는지 잠그는 gate다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review/
status = h002_source_reranking_claim_boundary_lock_after_result_review_locked
selected_path = source_reranking_claim_boundary_locked_select_validation_table_skeleton
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock
```

Locked role:

- Source-reranking evidence는 validation-level deployability evidence로 고정한다.
- Paper table role은 `secondary_validation_table_candidate_or_appendix`다.
- Main text에 쓰려면 반드시 official validation-only, clean comparison families only라고 표시한다.
- Official test result, final paper result, SOTA/full 3DSSG improvement로 쓰지 않는다.
- Deployable score 후보는 `C_e` 단독이 아니라 `S2_source_x_Ce`다.

Allowed wording:

```text
On official validation source candidates, combining source confidence with
predicate-geometry compatibility improves the primary recall-violation tradeoff
over source-only ranking for clean comparison families.
```

Required caveats:

- official validation only; official test unused.
- `relative_vertical` and `size_relative` clean comparison families only.
- 20개 source-family-K cell 중 3개에서 Recall@K가 소폭 낮아졌다.
- 모든 reviewed cell에서 Violation@K는 개선됐다.
- `C_e` alone은 low-K source ranking용 deployable score가 아니다.
- `support_contact`, `p_obs`, `p_rel` claim은 이 결과로 검증되지 않았다.

Blocked wording:

- official test or final paper result.
- uniform improvement in every source/family/K cell.
- `C_e` alone is a deployable source-ranking score.
- `support_contact` is solved.
- `p_obs` / `p_rel` posterior is validated.
- SOTA or full 3DSSG improvement.
- post-hoc tuned reranking.

Next step:

`compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock`에서
위 boundary에 맞는 validation table skeleton을 작성한다.
