# Compatibility Dataset V3 Support/Contact Individual Predicate Probe Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_probe_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_probe_plan_ready_for_source_inventory
selected_path = plan_individual_support_contact_source_inventory_standing_primary_lying_secondary_supported_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_source_inventory
```

## Decision

`support/contact`를 grouped target으로 다시 사용하지 않는다.

대신 predicate별로 분리해서 source inventory를 진행한다.

```text
primary = standing on
secondary = lying on
diagnostic = supported by
```

이 결정은 기존 결과와 충돌하지 않는다. 기존 grouped support/contact target은
predicate/class-pair/source shortcut 때문에 main learned target으로 부적합했다. 반면
`lying on` / `standing on` pose-conditioned same-geometry target은 `C_e` mechanism 자체가
가능하다는 scoped evidence를 줬다. 따라서 다음 단계는 grouped label을 재사용하는 것이 아니라,
개별 predicate별로 더 엄격한 source inventory를 만드는 것이다.

## Predicate Plan

| Priority | Predicate | Role | Queue Rows | Exact Matches | Mixed Class-Pair Groups | Boundary |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 1 | `standing on` | primary individual probe | 50245 | 5871 | 96 | source inventory가 통과하면 primary `C_e` / `p_rel` 후보 |
| 2 | `lying on` | secondary pose-conditioned probe | 60652 | 1440 | 75 | `standing on`과 paired pose-conditioned contrast 후보 |
| 3 | `supported by` | diagnostic superordinate probe | 50601 | 491 | 105 | clean binary negative가 아니라 taxonomy / `Q_e` diagnostic |

## Required Controls

다음 source inventory와 materialization 전에는 아래 gate가 필요하다.

| Gate | Applies To | Requirement |
| --- | --- | --- |
| predicate-specific balance | `standing on`, `lying on` | 각 predicate 안에서 accept/reject 또는 audit 가능한 candidate cell이 있어야 한다 |
| class-pair control | all | subject/object class pair만으로 target이 풀리면 안 된다 |
| rank/source control | all | source score/rank band가 target shortcut이 되면 안 된다 |
| hard-surface control | `standing on`, `supported by` | floor/table/wall-like endpoint strata를 cap/stratify해야 한다 |
| same-geometry anchor control | `lying on`, `standing on` | 가능한 경우 같은 `G_e`에서 `T_e`만 바뀌는 contrast를 확보한다 |
| supported-by boundary | `supported by` | `supported by`를 `standing on`의 negative로 쓰지 않는다 |
| no-GT policy | all | no-GT row는 audit 후보이지 자동 reject가 아니다 |

## Reuse Boundary

| Previous Artifact / Route | Decision | Reason |
| --- | --- | --- |
| grouped support/contact visual/mesh target | diagnostic only | predicate/class-pair/source shortcut risk가 높다 |
| pose-conditioned lying/standing same-G target | mechanism prior only | `C_e` control은 좋지만 constructed label이다 |
| `supported by` as `standing on` negative | reject | superordinate relation이라 동시에 참일 수 있다 |

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_source_inventory
```

다음 단계는 row를 만들거나 학습하는 단계가 아니라, full-train 후보에서 predicate별로
controlled source cell이 실제로 존재하는지 확인하는 source inventory다.
