# H002 R6 Supported-By Decomposition Target Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_target_plan/
status = h002_compatibility_dataset_v3_supported_by_decomposition_target_plan_ready
selected_path = plan_supported_by_superordinate_accept_relabel_reject_abstain_route
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan
```

## Decision

`supported by`는 clean binary compatibility target으로 두지 않는다.

이 relation은 `standing on` / `lying on`과 동시에 참일 수 있는 broad superordinate
support label이다. 따라서 R6는 `accept_broad_support`, `relabel_to_subtype`,
`reject_no_support`, `abstain`으로 분해하는 route-specific target으로 설계한다.

## Label Space

| Label | Decision Head | Meaning |
| --- | --- | --- |
| `accept_broad_support` | `p_obs=1,p_rel=accept` | broad support relation 자체로 신뢰 가능 |
| `relabel_to_subtype` | `p_obs=1,p_rel=accept_with_relabel` | support는 맞지만 `standing on`/`lying on`이 더 정확함 |
| `reject_no_support` | `p_obs=1,p_rel=reject` | geometry/visual evidence상 support가 없음 |
| `abstain` | `p_obs=0,p_rel=undefined` | generic endpoint, missing evidence, ontology overlap, subtype ambiguity |

## Source Snapshot

```text
existing supported-by diagnostic rows = 160
supported by::clear_accept = 40
supported by::hard_reject_no_support = 40
supported by::overlap_or_abstain = 80
visual-label supported-by counts = accept 82 / reject 11 / abstain 37
class-pair repair supported-by counts = accept 99 / reject 15 / abstain 46
```

## Main Risks

- `supported_by_is_superordinate`: binary target으로 만들면 standing/lying support와 충돌한다.
- `reject_sparse_under_proxy_labels`: 기존 proxy label에서 reject가 너무 적다.
- `class_pair_shortcut`: 이전 repair에서도 predicate/class-pair가 label을 거의 복원했다.
- `abstain_shortcut`: generic endpoint가 abstain label을 지배할 수 있다.
- `q_e_degenerate`: 이전 support/contact audit은 모든 row가 observable/sufficient였다.

## Materialization Requirements

다음 materialization plan은 최소한 다음 조건을 고정해야 한다.

- four-way target: `accept_broad_support`, `relabel_to_subtype`, `reject_no_support`, `abstain`
- 각 label 최소 60 rows, 목표 80 rows
- same supported-by class-pair 안에 mixed route labels 확보
- generic endpoint만으로 abstain이 결정되지 않도록 non-generic low-observability rows 포함
- no-GT를 자동 reject로 쓰지 않음
- source score/rank, queue kind, GT match, old geometry status, `p_geom_valid`, construction bucket은 hidden audit only

## Boundary

- Train-only planning only.
- No row materialization.
- No learned smoke/model training.
- No validation/test usage.
- H001 artifacts were not modified.
- No paper-level evidence is claimed.

## Next

```text
compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan
```
