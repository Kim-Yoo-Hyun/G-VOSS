# Compatibility Dataset V3 Official Source Inventory After Protocol Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/
status = h002_compatibility_dataset_v3_official_source_inventory_after_protocol_plan_ready
selected_path = official_source_inventory_ready_select_candidate_materialization_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory
```

## Purpose

이 단계는 official validation/test protocol plan 이후, 실제로 official validation에서
H002 promoted route를 구성할 수 있는지 확인하는 inventory 단계다. 아직 candidate row
materialization, official metric, paper metric은 실행하지 않았다.

확인한 항목은 다음이다.

- `3DSSG_subset` official validation GT relation capacity.
- `3RScan` semseg/OBB 기반 object geometry join 가능성.
- H001 VL-SAT full validation source candidate availability.
- H001 Open3DSG recovery validation source candidate availability.
- H001 source artifacts read-only boundary.

## GT Geometry Inventory

Official validation의 promoted family GT relation과 object OBB join coverage는 다음과 같다.

| Family | Predicates | GT relations | Unique scans | OBB pair coverage | Status |
| --- | --- | ---: | ---: | ---: | --- |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | 5474 | 155 | 1.000000 | candidate_ready |
| `relative_vertical` | `higher than`, `lower than` | 390 | 63 | 1.000000 | candidate_ready |
| `size_relative` | `bigger than`, `smaller than` | 170 | 35 | 1.000000 | candidate_ready |
| `support_contact` | `standing on`, `lying on` | 1589 | 156 | 1.000000 | candidate_ready |

해석:

- validation GT 기준으로 네 promoted family 모두 object OBB join은 가능하다.
- count 기준으로 `relative_horizontal`과 `support_contact`는 충분하고,
  `relative_vertical`과 `size_relative`는 규모가 작지만 protocol design에는 사용할 수 있다.
- 이 수치는 GT inventory일 뿐이며 relation prediction 성능을 의미하지 않는다.

## Source Candidate Inventory

H001 source artifacts는 read-only inventory로만 사용했다.

| Source | Family | Prediction rows | Geometry checkable | `p_geom_valid` available | Checkable rate |
| --- | --- | ---: | ---: | ---: | ---: |
| `vlsat_full_validation` | `relative_horizontal` | 147232 | 0 | 0 | 0.000000 |
| `vlsat_full_validation` | `relative_vertical` | 73616 | 73616 | 73616 | 1.000000 |
| `vlsat_full_validation` | `size_relative` | 73616 | 0 | 0 | 0.000000 |
| `vlsat_full_validation` | `support_contact` | 73616 | 73616 | 73616 | 1.000000 |
| `open3dsg_recovery_relaxed_views_min2` | `relative_horizontal` | 107064 | 0 | 0 | 0.000000 |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 53532 | 53532 | 53532 | 1.000000 |
| `open3dsg_recovery_relaxed_views_min2` | `size_relative` | 53532 | 0 | 0 | 0.000000 |
| `open3dsg_recovery_relaxed_views_min2` | `support_contact` | 53532 | 53532 | 53532 | 1.000000 |

해석:

- VL-SAT와 Open3DSG recovery 모두 promoted predicates의 source candidate rows가 존재한다.
- H001 geometry verification은 `relative_vertical`과 `support_contact`에 대해서만
  `geometry_checkable = 1.0`이다.
- `relative_horizontal`과 `size_relative`은 H001 verification 기준으로 unsupported이며,
  H002에서는 official materialization 단계에서 새 `G_e` feature를 직접 구성해야 한다.
- 따라서 `p_geom_valid`는 H002 source bridge에서 그대로 main `G_e`로 쓰는 것이 아니라,
  provenance/caveat 또는 일부 family의 bridge feature로만 다뤄야 한다.

## Readiness

| Family | Readiness | Caveat |
| --- | --- | --- |
| `relative_horizontal` | ready_for_protocol_design | H001 source geometry checkable rate below 0.5; H002 frame-aware `G_e` required |
| `relative_vertical` | ready_for_protocol_design | none |
| `size_relative` | ready_for_protocol_design | H001 source geometry checkable rate below 0.5; H002 size `G_e` required |
| `support_contact` | diagnostic_challenging_route | partial internal claim; not solved support/contact |

## Boundary

- official validation metric 생성 없음.
- official test 사용 없음.
- paper-level result 생성 없음.
- calibrated `p_rel` / `p_obs` claim 생성 없음.
- H001 source artifacts 수정 없음.
- 다음 단계는 official candidate materialization protocol이며, 바로 metric runner로 가지 않는다.

## Outputs

```text
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/summary.json
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/next_contract.json
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/next_runner_contract.json
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/gt_geometry_inventory.csv
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/gt_predicate_inventory.csv
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/source_manifest_inventory.csv
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/source_family_inventory.csv
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/source_predicate_inventory.csv
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/source_readiness.csv
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/validation_errors.jsonl
artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/report.md
```

