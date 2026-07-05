# Compatibility Dataset V3 Official Metric Claim Boundary Lock After Result Review

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review/
status = h002_compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review_locked
selected_path = official_claim_boundary_locked_select_paper_table_skeleton
validation_errors = 0
next_todo = compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock
```

## Purpose

Official validation metric result review 이후 paper-facing claim boundary를 고정했다.
이 단계는 새 metric을 계산하는 단계가 아니라, 이미 생성된 official validation `C_e`
mechanism result를 어떤 paper table row와 wording으로 사용할 수 있는지 잠그는 gate다.

## Locked Family Roles

| Family | Relation Types | Locked Role | Paper Use |
| --- | --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | main mechanism table primary row | primary evidence |
| `size_relative` | `bigger than`, `smaller than` | main mechanism table primary row | primary evidence |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | main mechanism table caveated row | frame-aware evidence only |
| `support_contact` | `standing on`, `lying on` | diagnostic failure-taxonomy row | challenging diagnostic only |

## Allowed Wording

- Official validation candidates에서 `C_e = compatibility(T_e, G_e)`는 route-specific
  predicate-geometry compatibility의 paper-candidate evidence로 사용할 수 있다.
- `relative_vertical`과 `size_relative`는 primary mechanism rows로 사용할 수 있다.
- `relative_horizontal`은 frame-aware compatibility evidence로 사용할 수 있지만,
  frame-invariant relation reasoning으로 주장하면 안 된다.
- `support_contact`는 current geometry evidence와 class-pair shortcut risk가 남는
  challenging diagnostic route로만 사용한다.
- 이번 official `C_e` metric은 `Z_e`, `Q_e`, H001 `p_geom_valid`를 main compatibility
  input에서 제외했다.

## Blocked Wording

- 모든 3DSSG relation type에 일반화된다고 쓰지 않는다.
- `support_contact`가 해결됐다고 쓰지 않는다.
- `relative_horizontal`을 frame-invariant로 해결했다고 쓰지 않는다.
- `p_rel`, `p_obs`, calibrated reliability, abstention 성능을 주장하지 않는다.
- VL-SAT/Open3DSG source reranking, Recall/Violation tradeoff 개선으로 쓰지 않는다.
- official test 결과로 쓰지 않는다.
- SOTA 또는 full 3DSSG improvement로 쓰지 않는다.

## Decision

Claim boundary는 locked 상태다. 따라서 다음 단계에서는 bounded paper-table draft를
만들 수 있다. 단, final paper result promotion은 아직 아니다. 다음 단계에서 table
skeleton을 만들고, primary/caveated/diagnostic row가 같은 표에서 어떻게 보이는지
검토해야 한다.

## Next

```text
compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock
```
