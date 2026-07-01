# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Path Decision

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_freeze_diagnostic
selected_path = freeze_support_contact_visual_mesh_class_pair_repair_as_diagnostic_select_scope_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze
```

## Decision

Support/contact visual/mesh class-pair repair artifact는 diagnostic-only로 freeze한다.

이유는 row count 문제가 아니라 target-identifiability 문제다. 현재 artifact는
`p_rel`/`C_e` binary row가 304개이고 positive/negative도 `198/106`으로 count
측면에서는 이전보다 좋아졌다. 하지만 `predicate + subject/object class-pair`만
봐도 binary target을 완전히 맞출 수 있다.

```text
p_rel/C_e binary rows = 304
p_rel/C_e binary counts = positive 198 / negative 106
relation multiclass = accept 198 / reject 106 / abstain 176
predicate_x_class_pair p_rel majority accuracy = 1.0000
hidden predicate_class_pair p_rel majority accuracy = 1.0000
subject_label p_rel majority accuracy = 0.7007
object_label p_rel majority accuracy = 0.6875
generic_endpoint_visible relation-multiclass majority accuracy = 0.6208
```

## Route Decision

Rejected routes:

- `run_learned_smoke_on_current_class_pair_repair_target`
  - Count는 충분하지만 `predicate_x_class_pair` shortcut이 target을 완전히 복원한다.
- `generic_endpoint_filtered_target`
  - Generic endpoint를 제거하면 multiclass abstain shortcut은 줄지만, binary
    `p_rel`/`C_e`에서 `predicate_x_class_pair` majority accuracy는 여전히 `1.0000`이다.
- `stricter_within_predicate_class_pair_visual_relabel`
  - 현재 artifact를 그대로 재라벨링하는 continuation으로는 부적절하다. 현재 visible-label
    policy 자체가 `predicate_x_class_pair` group을 pure하게 만들고 있으므로, 이 경로는 새
    independent visual/mesh audit protocol 또는 다른 source construction으로 다시 시작해야 한다.

Selected route:

- `freeze_support_contact_visual_mesh_class_pair_repair_as_diagnostic`
  - Class-pair repair가 binary row mass를 개선했다는 negative/diagnostic result는 보존한다.
  - 하지만 learned smoke, calibrated `p_rel`, calibrated `p_obs`, paper-level support/contact
    main claim으로는 승격하지 않는다.

## Interpretation

현재 결과는 H002 방향이 틀렸다는 의미가 아니라, Open3DSG train-side proxy construction으로
만든 support/contact visual/mesh target이 H002의 main reliability target으로는 독립성이
부족하다는 의미다.

따라서 H002의 현재 evidence boundary는 다음처럼 유지한다.

```text
relative_vertical = clean train-only C_e anchor
support/contact pose-conditioned target = scoped C_e mechanism evidence
support/contact visual/mesh class-pair repair = diagnostic negative result
calibrated p_rel / p_obs = still blocked
paper-level claim = not allowed
```

## Boundary

```text
split = train_only_path_decision
validation_usage = false
test_usage = false
h001_artifacts_modified = false
runs_learned_smoke = false
trains_new_model = false
fills_new_labels = false
materializes_rows = false
paper_evidence_allowed = false
```

## Artifacts

```text
summary.json
input_profile.json
key_shortcut_diagnostics.json
route_decision.csv
risk_register.csv
report.md
validation_errors.jsonl
```

## Next

```text
compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze
```

다음 단계에서는 H002 scope를 다시 정리해야 한다. 특히 support/contact visual/mesh repair를
main evidence에서 제외하고, 어떤 relation family와 target source를 다음 main path로 남길지
명시해야 한다.
