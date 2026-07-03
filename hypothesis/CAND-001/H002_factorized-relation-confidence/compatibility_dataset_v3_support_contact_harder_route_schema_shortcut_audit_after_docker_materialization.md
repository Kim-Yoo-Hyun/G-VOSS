# Support/Contact Harder Route Schema Shortcut Audit After Docker Materialization

## Status

```text
runtime_audit_root = experiments/H002_compatibility_routing/support_contact_harder_schema_audit/latest/
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization/
status = h002_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization_ready_with_warnings
selected_path = support_contact_harder_route_schema_ready_select_metric_protocol_freeze
validation_errors = 0
shortcut_warnings = 3
high_shortcut_warnings = 2
next_todo = compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit
```

이 단계는 richer support/contact hard-route materialization이 metric runner로 넘어가기
전에 schema leakage, shortcut risk, view alignment, feature availability, control
readiness를 audit한 단계다. Metric은 실행하지 않았고 official test도 사용하지 않았다.

## Docker Audit

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-schema-audit
```

Docker audit 결과:

| 항목 | 값 |
| --- | ---: |
| rows | 3178 |
| groups | 1589 |
| richer `G_e` features | 43 |
| labels | 1589 / 1589 |
| `standing on` / `lying on` | 1589 / 1589 |
| validation errors | 0 |
| blocked field hits | 0 |
| bad groups | 0 |

Primary model-safe view는 `model_safe_main_no_class`이고, main `C_e` input은
`T_e + G_e`만 허용된다. `Z_e`, `Q_e`, class labels, source score/rank, H001
`p_geom_valid`, hidden construction/provenance fields는 primary view에서 제외됐다.

## Shortcut Audit

| Probe | Scope | Majority Acc. | Risk | 해석 |
| --- | --- | ---: | --- | --- |
| `primary_predicate_only` | primary main input | 0.853996 | medium | predicate prior가 존재하므로 metric protocol에서 baseline으로 보고해야 함 |
| `hidden_class_pair` | hidden audit only | 0.500000 | low | class pair 단독은 balanced |
| `hidden_predicate_x_class_pair` | hidden audit only | 0.993707 | high | solved claim 금지, class-controlled control 필수 |
| `class_ablation_class_pair` | ablation only | 0.500000 | low | ablation view의 class pair 단독은 balanced |
| `class_ablation_predicate_x_class_pair` | ablation only | 0.993707 | high | class ablation은 paper claim이 아니라 shortcut diagnostic |

결론은 통과와 경고가 함께 있는 상태다. Schema는 metric freeze로 넘어갈 수 있지만,
`predicate x class-pair` shortcut이 너무 강하기 때문에 support/contact를 solved relation
family로 주장할 수는 없다. 다음 metric protocol에서는 class-controlled split/control,
shortcut baseline, wrong-`T`, shuffled-`G`를 필수로 고정해야 한다.

## Control Readiness

다음 control은 모두 생성 가능하다.

- wrong-`T` same-route
- shuffled-`G` global
- shuffled-`G` within class-pair
- class ablation view
- `Q_e` diagnostic view
- richer `G_e` feature availability
- predicate x class-pair shortcut probe

## Boundary

- 이 단계는 paper metric이 아니다.
- official validation은 eval-only source로만 사용했다.
- official test는 사용하지 않았다.
- `Q_e`는 diagnostic-only다.
- class labels는 ablation-only다.
- source reranking, `p_obs`, `p_rel` claim은 아직 defer한다.
- `support_contact solved` claim은 금지다.

## Next

```text
compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit
```

다음 단계는 metric을 바로 실행하는 것이 아니라, support/contact hard route metric protocol을
먼저 freeze하는 것이다. 특히 `T_e x G_e` interaction이 semantic-only, geometry-only,
plain concat, predicate-only, `predicate x class-pair`, wrong-`T`, shuffled-`G`보다
의미 있게 나은지 판단할 protocol을 결과 확인 전에 고정해야 한다.
