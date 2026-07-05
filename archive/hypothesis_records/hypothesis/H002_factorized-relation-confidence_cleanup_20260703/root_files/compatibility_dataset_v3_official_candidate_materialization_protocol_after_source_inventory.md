# Compatibility Dataset V3 Official Candidate Materialization Protocol After Source Inventory

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory/
status = h002_compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory_ready
selected_path = official_candidate_materialization_protocol_ready_select_docker_materializer
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol
```

## Purpose

이 단계는 official validation source inventory 이후, 실제 paper-level validation metric으로
가기 전에 candidate row materialization contract를 고정한 protocol 단계다. 아직 row를
materialize하지 않았고, metric도 실행하지 않았다.

Protocol의 핵심은 다음이다.

- official validation GT를 primary anchor로 사용한다.
- 같은 object pair에서 predicate counterfactual을 만든다.
- family-specific `G_e`를 H002에서 직접 구성한다.
- H001 VL-SAT/Open3DSG source artifacts는 read-only secondary bridge로만 사용한다.
- `source_score`, `rank`, H001 `p_geom_valid`, construction proxy는 main `C_e` model-safe
  features에서 금지한다.
- `p_rel` / `p_obs`는 아직 켜지 않는다.

## Family Route Contract

| Family | GT relations | Role | `G_e` policy | Boundary |
| --- | ---: | --- | --- | --- |
| `relative_horizontal` | 5474 | main frame-aware compatibility route | OBB centroid 기반 signed horizontal/depth deltas를 새로 구성 | no metric |
| `relative_vertical` | 390 | main signed-geometry compatibility route | OBB 기반 signed center/bottom/top vertical deltas 구성 | no metric |
| `size_relative` | 170 | main size compatibility route | OBB axes, volume, height, footprint 기반 size-ratio `G_e` 구성 | no metric |
| `support_contact` | 1589 | diagnostic/challenging support-contact route | contact gap, vertical order, footprint overlap, pose proxy 구성 | no solved claim |

## Source Bridge Contract

- `VL-SAT`와 `Open3DSG recovery` candidates는 official validation source bridge로 사용할 수 있다.
- 단, source score/rank는 `Z_e`이고 main `C_e` feature가 아니다.
- H001 `p_geom_valid`는 hidden/diagnostic bridge일 뿐, H002 official `G_e`의 main evidence가 아니다.
- `relative_horizontal`과 `size_relative`은 H001 geometry verification에서 unsupported이므로 반드시 H002-specific `G_e`를 구성해야 한다.

## Model-Safe Boundary

Main `C_e` model-safe view에는 다음만 들어간다.

- `T_e`: predicate text/label, route family, subject/object class.
- `G_e`: family-specific geometry evidence vector, mask, geometry reference policy.
- `C_e` target: compatibility label and label source.
- row identity는 grouping/trace metadata로만 사용하고 model feature로 쓰지 않는다.

다음은 hidden 또는 diagnostic-only다.

- source score/rank/source id,
- H001 `p_geom_valid`,
- H001 verification status,
- label/geometry/candidate/construction buckets,
- GT exact-match flag,
- counterfactual generation rule,
- old proxy label.

## Required Audit Before Metric

다음 audit이 통과되기 전에는 official validation metric을 실행하지 않는다.

- candidate row count check,
- model-safe / hidden disjointness check,
- blocked-field absence check,
- target balance by family and predicate,
- scan/pair leakage audit,
- predicate-only / class-pair-only / source-only / rank-only baselines,
- geometry-only, `T+G` concat, `T x G` compatibility baselines,
- wrong-`T` and shuffled-`G` controls,
- family-specific control report.

## Boundary

- official validation metric 생성 없음.
- official test 사용 없음.
- paper-level result 생성 없음.
- calibrated `p_rel` / `p_obs` claim 생성 없음.
- H001 artifacts 수정 없음.

다음 단계는 `/home/yoohyun/research/experiments/H002_compatibility_routing`에서
Docker service `h002-official-materialize-candidates`를 구현하는 것이다.

