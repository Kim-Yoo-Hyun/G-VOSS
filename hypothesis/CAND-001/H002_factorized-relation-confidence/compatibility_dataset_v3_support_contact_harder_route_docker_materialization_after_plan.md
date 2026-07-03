# Support/Contact Harder Route Docker Materialization After Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan/
status = h002_support_contact_harder_route_docker_materialization_after_plan_ready
selected_path = support_contact_harder_route_materialized_select_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization
```

이 단계는 Docker 기반 richer support/contact `G_e` materializer를 실제 실행하고, runtime
output이 다음 schema/shortcut audit로 넘어갈 수 있는지 검증한 단계다. Metric은 실행하지
않았다.

## Runtime Output

```text
output_root = experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
candidate_rows = 3178
model_safe_main_no_class = 3178
model_safe_main_with_class_ablation = 3178
model_safe_geometry_only = 3178
model_safe_qe_diagnostic = 3178
hidden_manifest = 3178
group_manifest = 1589
validation_errors = 0
feature_count = 43
official_test_usage = false
metrics_run = false
```

## Generated Views

| View | 역할 |
| --- | --- |
| `candidate_rows.jsonl` | full row-level candidate/provenance output |
| `model_safe_main_no_class.jsonl` | primary `T_e + G_e` view, class labels 제외 |
| `model_safe_main_with_class_ablation.jsonl` | class semantic ablation-only view |
| `model_safe_geometry_only.jsonl` | geometry-only baseline/audit view |
| `model_safe_qe_diagnostic.jsonl` | `Q_e`/missingness/observability diagnostic view |
| `hidden_manifest.jsonl` | GT/source/class-pair/provenance audit only |
| `group_manifest.jsonl` | same-pair predicate-flip integrity |
| `feature_availability.csv` | 43 richer `G_e` feature availability summary |

## Richer `G_e`

생성된 `G_e`는 기존 OBB proxy보다 넓다.

- gap/overlap: vertical gap, XY overlap, bottom proximity
- pose/shape: subject/object flatness, extent ratio, principal/minor axis upness
- surface: dominant-normal upness, normal alignment, support surface normal upness
- point/contact: point counts, near-contact point ratios, local contact density, contact patch proxy
- optional mesh boundary: mesh gap/intersection은 아직 main extractor가 아니라 `Q_e` missing mask로 둠

## Boundary

- official validation은 eval-only source로만 사용했다.
- official test는 사용하지 않았다.
- `Z_e`, `Q_e`, class labels, source score/rank, H001 `p_geom_valid`는 primary `C_e` input에서 제외했다.
- 이 단계는 metric이 아니며 paper result가 아니다.
- `support_contact solved` claim은 아직 금지다.

## Next

```text
compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization
```

다음 단계는 schema leakage, shortcut risk, within-class-pair shuffled-`G`, wrong-`T`, control readiness를 audit하는 단계다.
