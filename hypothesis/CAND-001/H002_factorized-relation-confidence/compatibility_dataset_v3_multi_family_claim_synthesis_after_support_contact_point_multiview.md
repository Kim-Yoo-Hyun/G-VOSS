# H002 Multi-Family Claim Synthesis After Support/Contact Point/Multiview

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview/
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview_ready
selected_path = freeze_relation_aware_compatibility_routing_claim_select_ablation_table_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis
```

## Core Decision

H002의 현재 paper-framework skeleton은 다음 claim으로 고정한다.

```text
relation-aware predicate-geometry compatibility routing
```

의미는 다음과 같다.

- 모든 relation family에 같은 `semantic score + geometry score` 결합식을 강제하지 않는다.
- `T_e`, `Z_e`, `G_e`, `C_e`, `Q_e`를 분리하고, relation family와 evidence availability에 따라 필요한 evidence route를 다르게 둔다.
- `C_e = compatibility(T_e, G_e)`는 source confidence `Z_e`를 복사하지 않는 predicate-geometry compatibility signal이어야 한다.
- `Q_e`는 truth label이 아니라 `p_obs`/abstain을 위한 observability/evidence-quality axis다.

## Current Family Roles

| Family | Predicates | Current role | Decision |
| --- | --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | clean compatibility mechanism | main mechanism evidence |
| `support_contact` | `lying on`, `standing on` | challenging compatibility route | main route evidence with caveat |
| `support_contact_superordinate` | `supported by` | superordinate/ambiguous support relation | diagnostic only |
| `proximity` | `close by` | geometry-easy relation | diagnostic/generality control, not main compatibility proof |
| `attachment_like` | `attached to`, `hanging on`, `connected to` | observability-heavy route | future/diagnostic until visual/mesh evidence and independent target are ready |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | reference-frame dependent route | deferred |

## Evidence Interpretation

`relative_vertical`는 같은 geometry evidence라도 predicate semantic content에 따라
compatible/incompatible가 바뀐다는 clean `C_e` mechanism을 보여준다.

`support_contact`는 절대 성능으로 fully solved라고 말하면 안 된다. 하지만
semantic-only, geometry-only, plain concatenation이 약하고, predicate-geometry interaction만
강해지며, wrong-predicate와 shuffled-geometry controls가 무너지는 패턴은 H002의 핵심 주장에
직접 맞는다.

`close by`는 현재 target에서는 distance/rule geometry만으로 거의 풀리는 geometry-easy control이다.
따라서 main learned compatibility proof가 아니라, framework가 geometry-decidable family를 별도
route로 처리해야 한다는 generality/diagnostic evidence로 둔다.

## Blocked Claims

현재 artifact로는 다음 claim을 하면 안 된다.

- paper-level performance
- held-out/test relation reliability
- all relation-family generality
- support/contact fully solved
- `Q_e` as relation truth
- final calibrated `p_rel`/`p_obs` result

## Next

다음 작업은 더 많은 relation을 즉시 추가하는 것이 아니라, 현재 claim skeleton을 paper table과
ablation plan으로 바꾸는 것이다.

```text
compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis
```
