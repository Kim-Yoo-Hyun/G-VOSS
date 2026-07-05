# H002 Official Validation/Test Protocol Plan

## Status

```text
status = h002_compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review_ready
selected_path = official_protocol_ready_select_source_inventory
validation_errors = 0
next_todo = compatibility_dataset_v3_official_source_inventory_after_protocol_plan
```

## Purpose

Repaired grouped-eval claim boundary 이후, H002를 official validation/test로 옮기기
위한 protocol을 정의했다. 이 단계는 official metric 실행이 아니라 protocol planning과
split inventory다.

핵심 원칙은 다음이다.

- official validation을 먼저 inventory / metric-freeze 대상으로 사용한다.
- test는 local label file 또는 evaluation server가 확인되고, protocol이 완전히 freeze된
  뒤에만 single final evaluation으로 사용한다.
- 현재 internal candidate-pool grouped metric은 paper metric이 아니다.
- `p_rel` / `p_obs`는 아직 비활성화 상태이며, 현재 protocol은 `C_e` mechanism 검증을
  먼저 다룬다.

## Outputs

```text
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/summary.json
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/official_split_inventory.csv
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/official_protocol_steps.csv
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/source_candidate_contract.csv
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/family_eval_scope.csv
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/metric_contract.csv
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/baseline_control_contract.csv
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/promotion_gates.csv
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/next_runner_contract.json
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/report.md
artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/validation_errors.jsonl
```

## Local Official Split Inventory

`local_dataset/3DSSG_subset` 기준으로 확인한 split inventory다. 이는 metric이 아니라
capacity 확인이다.

| Split | Scans | Relations | Status |
| --- | ---: | ---: | --- |
| `train` | 3852 | 81190 | reference only |
| `validation` | 548 | 11254 | primary official inventory / future metric split |
| `test` | 0 | 0 | local `relationships_test.json` not found |

Promoted family의 validation relation capacity:

| Family | Validation count | Predicate counts |
| --- | ---: | --- |
| `relative_horizontal` | 5474 | `left=1713`, `right=1713`, `front=1024`, `behind=1024` |
| `relative_vertical` | 390 | `higher than=195`, `lower than=195` |
| `size_relative` | 170 | `bigger than=85`, `smaller than=85` |
| `support_contact` | 1589 | `standing on=1357`, `lying on=232` |

## Protocol Steps

| Step | Status | Name | Purpose |
| --- | --- | --- | --- |
| `O1` | completed | claim boundary lock | internal metric을 paper metric으로 잘못 승격하지 않도록 claim boundary 고정 |
| `O2` | next | official source inventory | validation GT, object geometry, VL-SAT/Open3DSG source candidate availability 확인 |
| `O3` | pending | official candidate materialization protocol | GT/counterfactual/source candidate construction freeze |
| `O4` | pending | official metric freeze | metric, baseline, control, family scope, table wording freeze |
| `O5` | pending | official validation eval | Docker official validation evaluation 실행 |
| `O6` | conditional | official test eval | accessible test target이 있을 때만 single frozen final evaluation |
| `O7` | pending | paper promotion review | H002를 paper main/appendix/hypothesis evidence 중 어디에 둘지 결정 |

## Source Candidate Routes

| Source route | Priority | Role |
| --- | --- | --- |
| `GT_counterfactual_mechanism` | primary | official validation에서 `C_e` compatibility mechanism 검증 |
| `VL-SAT_source_candidates` | secondary bridge | source prediction 후보 위에서 reliability/reranking bridge 검증 |
| `Open3DSG_source_candidates` | secondary bridge | open-vocabulary source 후보 위에서 bridge 검증 |
| `official_test` | deferred | protocol freeze 이후 접근 가능할 때만 final check |

## Metric Contract

Primary `C_e` mechanism metric:

- AUROC
- AUPRC
- balanced accuracy
- macro-F1
- family-level and predicate-level reporting

Required baselines:

- `M1_T_semantic_only`
- `M2_G_geometry_only`
- `M3_T_plus_G_concat`
- `M4_TxG_compatibility`

Required controls:

- wrong-`T_e`
- shuffled-`G_e`
- split leakage audit
- blocked-field audit

Optional source bridge metric:

- Recall@K 또는 relation retrieval metric
- invalid / violation rate
- compatibility-risk tradeoff
- source score baseline, geometry-only baseline, shuffled/wrong-pair controls

## Family Scope For Official Validation

| Family | Current internal status | Official validation role |
| --- | --- | --- |
| `relative_horizontal` | claim-supporting | primary `C_e` mechanism |
| `relative_vertical` | claim-supporting | primary `C_e` mechanism |
| `size_relative` | claim-supporting | primary `C_e` mechanism |
| `support_contact` | partial | challenging diagnostic / failure taxonomy |

`support_contact`는 validation에 충분한 row 수가 있지만, 현재 내부 결과가 partial이므로
main solved-family table에 바로 올리지 않는다. 대신 error taxonomy와 evidence gap 분석을
동반해야 한다.

## Promotion Gates

다음 조건이 충족되기 전까지 paper-level H002 result로 승격하지 않는다.

- official validation source inventory 통과.
- candidate construction protocol freeze.
- schema leakage zero.
- wrong-`T_e`와 shuffled-`G_e` controls 보고.
- family-level and predicate-level reporting.
- aggregate-only claim 금지.
- test는 protocol freeze 전 사용 금지.

## Boundary

- official validation metric 생성 없음. 이번 단계는 split inventory만 수행했다.
- official test 사용 없음.
- paper-level result 생성 없음.
- `C_e` official protocol만 planning했다.
- `p_rel` / `p_obs`는 optional future protocol이다.
- H001 artifact 수정 없음.

## Next

```text
compatibility_dataset_v3_official_source_inventory_after_protocol_plan
```

다음 단계에서는 official validation의 GT relation, object geometry join, VL-SAT source
candidate, Open3DSG source candidate가 실제로 어느 정도 사용 가능한지 inventory를
작성해야 한다.
