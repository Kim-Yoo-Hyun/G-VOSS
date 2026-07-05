# H002 Route-Specific Target Manifest Consistency Audit After Plan

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan/
status = h002_compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan_ready
selected_path = manifest_consistency_pass_select_route_target_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit
```

## Purpose

route-specific target manifest가 서로 모순되지 않는지 확인했다. 이 단계는 새 row를
materialize하지 않고, model을 학습하지 않는다.

검사 항목:

- 13개 route manifest 간 `route_id` set 일치
- route slug와 artifact root 유일성
- `close by = geometry_support` 보존
- `supported by = accept_relabel_abstain` 보존
- attachment route = `observability_then_reliability` 보존
- predicate-geometry route label space = `compatible / incompatible / abstain`
- `C_e`에서 `Z_e` 제외
- hidden construction fields의 model-safe / `C_e` input 금지
- materialization/model/paper-promotion boundary 보존

## Result

```text
audit_rows = 49
pass = 49
fail = 0
validation_errors = 0
```

Preserved contracts:

```text
close_by_route = geometry_support
supported_by_route = accept_relabel_abstain
attachment_route = observability_then_reliability
C_e_excludes_Z_e = true
hidden_fields_model_safe = false
```

## Claim Update

Allowed wording:

- `close by` evaluates a geometry-only route rather than predicate-geometry interaction.
- `supported by` is a superordinate decomposition route.
- attachment requires `p_obs` / `Q_e` before `p_rel`.
- H002 studies which route and target definition each relation family requires.

Blocked wording:

- `close by` proves `T_e x G_e` interaction.
- `supported by` is a clean negative for `standing on` / `lying on`.
- distance alone decides attachment reliability.
- all relation types use one binary target or one fixed fusion head.

## Next

다음 단계는 route-specific target materialization plan이다. audit는 통과했지만, 아직
row materialization 자체는 수행하지 않았다.

```text
compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit
```
