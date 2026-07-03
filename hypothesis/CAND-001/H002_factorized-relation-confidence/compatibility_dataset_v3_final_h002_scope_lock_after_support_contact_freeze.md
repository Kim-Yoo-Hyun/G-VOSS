# Final H002 Scope Lock After Support/Contact Freeze

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze/
status = h002_compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze_ready
selected_path = final_scope_locked_clean_Ce_routes_support_contact_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock
```

## 목적

`support_contact` hard route를 diagnostic/failure taxonomy로 freeze한 뒤, H002의 최종
paper-facing scope를 고정했다. 이 단계는 새 metric을 돌리는 것이 아니라, 현재까지의
official validation 결과와 path decision을 바탕으로 어떤 claim과 metric을 유지할지 lock하는
단계다.

## 최종 Scope

| Route family | Relation types | Final role | Paper position |
| --- | --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | primary clean `C_e` mechanism | main mechanism evidence |
| `size_relative` | `bigger than`, `smaller than` | primary clean `C_e` mechanism | main mechanism evidence |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | caveated frame-aware `C_e` mechanism | caveated mechanism evidence |
| `proximity` | `close by` | geometry-only route control | control / diagnostic |
| `support_contact` | `standing on`, `lying on`, `supported by` | diagnostic failure taxonomy | failure analysis / future redesign |
| `attachment_observability` | `attached to`, `hanging on`, `connected to` | future observability route | deferred |
| `containment_occlusion_identity_structural` | `inside`, `standing in`, `lying in`, `hanging in`, `cover`, `leaning against`, `same as`, `same symmetry as`, `part of`, `belonging to` | future route taxonomy | deferred |

## Metric Lock

현재 H002의 primary metric은 `C_e = compatibility(T_e, G_e)`가 의미 있는지를 보는
family-wise mechanism metric이다.

| Metric | Current role |
| --- | --- |
| family-wise AUROC / macro-family AUROC | primary current |
| wrong-`T`, shuffled-`G`, endpoint-swap, sign-flip controls | primary current |
| balanced accuracy / AUPRC | secondary current |
| `Recall@K` | downstream future |
| `Violation@K` | downstream future, not primary `C_e` metric |
| risk-coverage / abstain quality | future `p_obs` branch |

따라서 `Violation@K`는 폐기하지 않는다. 다만 현재 H002의 main mechanism 검증에서는 primary
metric이 아니며, source reranking protocol을 연 뒤 top-K graph selection의 downstream
geometry inconsistency를 평가할 때 다시 사용한다.

## Allowed Claims

- H002는 `T_e`, `Z_e`, `G_e`, `C_e`, `Q_e`를 분리하는 factorized evidence contract다.
- `relative_vertical`과 `size_relative`에서는 `C_e`가 semantic-only, geometry-only, simple concat보다 강한 clean mechanism evidence다.
- `relative_horizontal`은 frame-aware compatibility evidence로 보고하되 frame-invariant spatial reasoning으로 과장하지 않는다.
- relation family마다 필요한 evidence route가 다르다는 relation-aware routing claim은 허용한다.
- `Violation@K`는 source reranking 이후 downstream metric으로만 허용한다.

## Blocked Claims

- `support_contact` solved claim
- all-relation generalization
- source reranking result claim
- `Violation@K`를 현재 `C_e` mechanism의 primary metric으로 사용하는 claim
- calibrated `p_obs` / `p_rel` reliability claim
- official test result claim
- support/contact score post-hoc flip

## 다음 단계

다음 TODO는 source reranking protocol plan이다.

```text
compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock
```

이 다음 단계에서만 `Recall@K`와 `Violation@K`를 downstream metric으로 다시 열 수 있다.
