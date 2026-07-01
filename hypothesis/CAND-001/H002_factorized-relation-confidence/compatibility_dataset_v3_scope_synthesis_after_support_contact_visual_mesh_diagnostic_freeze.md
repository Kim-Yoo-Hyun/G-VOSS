# H002 Scope Synthesis After Support/Contact Visual-Mesh Diagnostic Freeze

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze/
status = h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_ready
selected_path = all_relation_family_generalization_scan_with_proximity_first
validation_errors = 0
next_todo = compatibility_dataset_v3_relation_family_generalization_capacity_scan
selected_first_active_family = proximity
selected_first_active_predicates = close by
```

## Decision

H002는 `close by` / proximity로 진행하되, paper framing은 단순히 “잘 되는 relation만
고른다”가 아니라 **all-relation-family eligibility scan**으로 고정한다.

즉, 모든 relation type을 같은 기준으로 먼저 평가한다.

```text
1. target row mass가 충분한가?
2. same predicate / same class-pair / similar rank 안에서 accept/reject contrast가 있는가?
3. semantic-only, class-pair-only, source-only shortcut으로 풀리지 않는가?
4. G_e가 정의 가능한가?
5. C_e = compatibility(T_e, G_e)가 geometry-only/source-only보다 추가 정보를 주는가?
6. Q_e / p_obs를 만들 수 있을 만큼 observability variation이 있는가?
```

그 다음:

```text
pass family = main evidence candidate
fail family = failure taxonomy / claim boundary evidence
```

이렇게 해야 잘 되는 family만 숨겨서 고른다는 cherry-picking 공격을 피할 수 있다.

## Route Decision

Selected:

- `all_relation_family_capacity_scan`
- `proximity_close_by_first`

Rejected:

- `run_all_relation_type_model_now`
  - target eligibility 없이 바로 모델을 돌리면 support/contact에서 본 shortcut 문제가 반복된다.
- `main_claim_only_on_successful_families`
  - 성공 family를 main result로 쓸 수는 있지만, 시도한 family와 실패 원인을 함께 공개해야 한다.

Deferred:

- `support_contact_individual_predicate_scan`
  - `standing on`, `lying on`, `supported by`는 개별적으로 다르게 동작할 수 있다.
  - grouped support/contact failure가 각 predicate failure를 의미하지는 않는다.
  - 다만 현재 visual/mesh proxy target은 `predicate + class-pair` shortcut이 남아 있어 immediate main route는 아니다.

## Family Priority

| Family | Predicates | Train GT | H002 Queue | Verdict |
| --- | --- | ---: | ---: | --- |
| `proximity` | `close by` | 12300 | 171324 | selected first active probe |
| `support_contact` | `standing on`, `lying on`, `supported by` | 12600 | 161498 | individual predicate probe possible |
| `relative_vertical` | `higher than`, `lower than` | 3552 | 124604 | already clean anchor |
| `size_relative` | `bigger than`, `smaller than` | 1822 | 0 | optional quick probe |
| `containment_in` | `inside`, `standing in`, `lying in`, `hanging in` | 330 | 0 | optional schema probe |
| `attachment_deferred` | `attached to`, `hanging on`, `mounted on`, `connected to` | 8767 | 0 | defer visual/mesh-heavy |
| `relative_horizontal` | `left`, `right`, `front`, `behind`, `in front of` | 36944 | 0 | defer reference-frame ambiguity |
| `identity_symmetry` | `same as`, `same symmetry as` | 2688 | 0 | defer/diagnostic |
| `part_structural` | `part of`, `belonging to`, `build in`, `cover`, `leaning against` | 701 | 0 | defer/diagnostic |

## All Relation Types

Open3DSG train-full GT에서 관측된 relation type은 25개다.

```text
close by        12300
left            11833
right           11833
standing on      9790
attached to      7384
behind           6639
front            6639
same as          2464
lying on         2003
higher than      1776
lower than       1776
hanging on       1193
bigger than       911
smaller than      911
supported by      807
build in          238
standing in       227
same symmetry as  224
connected to      190
leaning against   184
belonging to      169
lying in           94
part of            66
cover              44
hanging in          9
```

Official/mapped inventory에는 현재 train-full GT count가 0인 다음 label도 유지한다.

```text
inside
in front of
mounted on
none
```

## Interpretation

`support/contact`의 grouped target이 막혔다고 해서 `standing on`, `lying on`,
`supported by` 각각이 모두 불가능하다는 의미는 아니다. 특히 `lying on`과
`standing on`은 pose-conditioned `C_e` mechanism evidence가 이미 있다.

다만 main claim으로 승격하려면 개별 predicate도 다음 조건을 통과해야 한다.

```text
same predicate + similar class-pair 안에서 accept/reject가 같이 존재해야 함
predicate/class-pair shortcut으로 target이 복원되지 않아야 함
geometry/compatibility가 source-only 또는 semantic-only보다 추가 정보를 줘야 함
```

따라서 다음은 `close by`를 첫 family로 두되, 전체 relation-family capacity scan을 수행한다.

## Boundary

```text
split = train_only_scope_synthesis
validation_usage = false
test_usage = false
h001_artifacts_modified = false
runs_learned_smoke = false
trains_new_model = false
paper_evidence_allowed = false
```

## Artifacts

```text
summary.json
all_relation_types.csv
family_priority_table.csv
route_decision.csv
report.md
validation_errors.jsonl
```

## Next

```text
compatibility_dataset_v3_relation_family_generalization_capacity_scan
```
