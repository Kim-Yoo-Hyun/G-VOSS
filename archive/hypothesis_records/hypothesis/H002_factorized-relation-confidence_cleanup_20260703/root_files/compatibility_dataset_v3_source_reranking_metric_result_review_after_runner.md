# Source Reranking Metric Result Review

## 2026-07-02 Decision Update

목적:

Source-reranking metric runner 결과를 paper-facing claim으로 올릴 수 있는지 심사했다.
단순히 `S2_source_x_Ce`가 좋아 보이는지 보는 것이 아니라, frozen protocol 기준으로
`S2` vs `S0`, shuffled-`C_e`, wrong-`T`, source/family/K별 비대칭, and claim boundary를
분리해서 검토했다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_metric_result_review_after_runner/
status = h002_source_reranking_metric_result_review_after_runner_ready
selected_path = source_reranking_validation_evidence_ready_select_claim_boundary_lock
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review
```

Review decision:

- Source-reranking validation evidence는 positive다.
- `S2_source_x_Ce`는 primary weighted 기준으로 모든 K에서 `S0_source_score` 대비
  Recall@K를 유지/개선하고 Violation@K를 낮췄다.
- shuffled-`C_e`와 wrong-`T` controls는 `S2`보다 낮은 Recall@K를 보였다.
- wrong-`T` control은 Violation@K가 크게 높아, predicate-geometry compatibility가 실제
  ranking에 영향을 준다는 evidence가 있다.
- 그러나 final paper promotion은 아직 아니다. 다음 단계에서 claim boundary를 잠가야 한다.

Important caveats:

- 20개 source-family-K cell 중 3개에서 Recall@K가 소폭 낮아졌다.
- Violation@K는 review한 모든 source-family-K cell에서 개선됐다.
- `C_e` alone인 `S1_Ce_only`는 low-K recall이 낮으므로 deployable score로 주장하면 안 된다.
- `support_contact`는 success aggregation에서 제외된 diagnostic/failure-taxonomy route다.
- Official test는 사용하지 않았다.

Allowed wording candidate:

```text
On official validation source candidates, combining source confidence with
predicate-geometry compatibility improves the primary recall-violation tradeoff
over source-only ranking for the clean comparison families.
```

Blocked wording:

- 모든 source/family/K cell에서 uniformly improves.
- `C_e` alone is sufficient for deployable source ranking.
- official test result.
- final paper result promotion.
- `support_contact` solved.
- `p_obs` / `p_rel` posterior validated.

Next step:

`compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review`에서
위 allowed/blocked wording을 고정하고, source-reranking result를 paper table 후보로 둘지
appendix/validation evidence로 둘지 결정한다.
