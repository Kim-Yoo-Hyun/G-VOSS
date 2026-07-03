# Support/Contact Harder Route Path Decision After Result Review

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_path_decision_after_result_review/
status = h002_support_contact_harder_route_path_decision_after_result_review_freeze_diagnostic
selected_path = freeze_support_contact_harder_route_as_diagnostic_scope_h002_to_clean_routes
validation_errors = 0
next_todo = compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze
```

## 목적

`support_contact` hard route result review 이후, 이 route를 계속 수리할지 아니면
diagnostic/failure taxonomy로 고정하고 H002 paper scope를 clean `C_e` route 중심으로
제한할지 결정했다.

## 결과

선택한 경로는 `support_contact` hard route freeze다.

| Option | Decision | 이유 |
| --- | --- | --- |
| freeze support/contact as diagnostic | selected | official validation에서 correct `T_e`보다 wrong-`T`가 강함 |
| redesign support/contact target/feature contract now | defer | minor repair가 아니라 새 target/feature contract가 필요함 |
| post-hoc score flip | reject | validation failure를 본 뒤 method direction을 바꾸는 것이므로 invalid |
| promote support/contact as success | reject | 모든 success gate가 실패함 |
| run source reranking or official test | reject for now | final scope lock 전에 실패 route를 전파하면 안 됨 |

핵심 evidence는 다음과 같다.

| Metric | Value |
| --- | ---: |
| official validation `M4_TxG_compatibility` AUROC | 0.077539 |
| official validation wrong-`T` AUROC | 0.922461 |
| paired `M4` accuracy | 0.182505 |
| paired wrong-`T` accuracy | 0.817495 |

따라서 현재 support/contact hard route는 성공 결과가 아니라 inversion failure다. 이 결과는
H002 전체 방향을 반박하기보다, support/contact가 현재 clean comparison route와 다른
target/feature contract를 요구한다는 근거로 처리한다.

## Locked Scope

| Route family | Paper role | Status | Claim boundary |
| --- | --- | --- | --- |
| `relative_vertical` | main clean `C_e` evidence | keep | predicate-conditioned signed vertical-order compatibility |
| `size_relative` | main clean `C_e` evidence | keep | predicate-conditioned signed size-comparison compatibility |
| `relative_horizontal` | caveated frame-aware evidence | keep with caveat | frame-aware horizontal compatibility, not frame-invariant spatial reference |
| `support_contact` | diagnostic failure taxonomy | freeze | hard contact/pose route exposes target/feature transfer failure |

## Blocked Claims

- `support_contact` solved claim
- post-hoc score flip
- all-relation generalization
- source reranking with the failed support/contact route
- official test evaluation before final scope/method freeze
- calibrated `p_obs` / `p_rel` reliability claim from the current `C_e` result

## 다음 단계

다음 TODO는 final H002 scope lock이다.

```text
compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze
```

이 단계에서는 clean route와 diagnostic route를 명확히 분리하고, paper-facing claim과
blocked claim을 최종적으로 정리해야 한다.
