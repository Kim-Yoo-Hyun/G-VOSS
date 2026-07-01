# H002 Ablation And Table Plan After Multi-Family Synthesis

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis/
status = h002_compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis_ready
selected_path = freeze_candidate_ablation_contract_select_relation_family_coverage_gap_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan
```

## Decision

이 단계의 결론은 최종 main table을 만드는 것이 아니다. 현재 H002 claim이 paper table로
승격되려면 어떤 ablation/control이 필요한지 후보 contract를 고정한 것이다. 새 learned smoke나
posterior run은 수행하지 않았다.

현재 short claim:

```text
relation-aware predicate-geometry compatibility routing
```

## Candidate Tables

| Table | Role | Rows | Message |
| --- | --- | --- | --- |
| `T1` | candidate mechanism table | `relative_vertical`, `support_contact` | fixed concat이 아니라 `C_e = interaction(T_e, G_e)`가 핵심이다 |
| `T2` | route taxonomy | main/diagnostic/future/deferred relation families | relation마다 필요한 evidence route가 다르다 |
| `T3` | diagnostic table | `close by`, `attached to`, `hanging on`, `connected to`, `supported by` | geometry-easy와 observability-heavy relation은 main claim과 분리한다 |
| `T4` | reviewer-risk / claim boundary | blocked claims, caveats, promotion gates | 현재는 train-only mechanism hypothesis다 |

## Relation Coverage Gap

현재 H002 queue에서 직접 다룬 relation은 전체가 아니다. 기존 inventory 기준으로 남은 큰 gap은 다음이다.

- `relative_horizontal`: `left`, `right`, `front`, `behind`, `in front of`
- `attachment_deferred`: `attached to`, `hanging on`, `mounted on`, `connected to`
- `containment_in`: `inside`, `standing in`, `lying in`, `hanging in`
- `size_relative`: `bigger than`, `smaller than`
- `part_structural`: `part of`, `belonging to`, `build in`, `cover`, `leaning against`
- `identity_symmetry`: `same as`, `same symmetry as`

따라서 final main table 또는 Docker promotion 전에 relation-family coverage/gap audit이 먼저 필요하다.

## Required Ablations

핵심 비교군은 다음으로 고정한다.

```text
A0 constant_or_label_prior
A1 T_e semantic content only
A2 Z_e source confidence only
A3 G_e geometry-only
A4 T_e + G_e plain concat
A5 C_e predicate-geometry interaction
A6 C_e + Q_e selective decision
A7 C_e + Q_e + Z_e final p_rel
A8 fixed fusion without route
```

`C_e`에는 `Z_e`를 넣지 않는다. Source score/rank는 final `p_rel` ablation에는 들어갈 수 있지만,
predicate-geometry compatibility를 검증하는 head에서는 shortcut이 될 수 있다.

## Required Controls

필수 control은 다음으로 고정한다.

- wrong predicate same geometry
- shuffled geometry global
- shuffled geometry within predicate/family
- class-pair only
- source/rank only
- distance or `p_geom_valid` only
- `Q_e` shuffled or `Q_e` only
- scan and endpoint leakage

## Promotion Boundary

현재 결과는 paper-level evidence가 아니다. 논문 본문 claim으로 승격하려면 relation-family
coverage/gap audit, Docker reproduction, frozen schema, grouped held-out evaluation, control
matrix, bootstrap/CI, 그리고 wording lock이 필요하다.

## Next

```text
compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan
```
