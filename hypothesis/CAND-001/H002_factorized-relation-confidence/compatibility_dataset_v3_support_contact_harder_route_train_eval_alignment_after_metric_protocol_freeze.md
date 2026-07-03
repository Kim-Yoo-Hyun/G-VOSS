# Support/Contact Harder Route Train/Eval Alignment After Metric Protocol Freeze

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze/
status = h002_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze_ready
selected_path = support_contact_train_eval_aligned_select_metric_runner_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment
```

이 단계는 support/contact hard-route metric runner 전에 train-side point/OBB/contact
features를 official validation의 43-feature canonical `G_e` schema에 맞추는 단계다.
Metric은 실행하지 않았고 official test도 사용하지 않았다.

## Inputs

| Input | 역할 |
| --- | --- |
| `metric_protocol_freeze_after_schema_shortcut_audit/` | frozen metric/model/control/claim contract |
| `support_contact_individual_predicate_point_multiview_materialization/` | train-side point/OBB/contact feature source |
| `support_contact_individual_predicate_point_multiview_schema_shortcut_audit/` | train-side schema/shortcut gate |
| `support_contact_harder_materialization/latest/` | official validation 43-feature schema reference |

## Alignment Result

| 항목 | 값 |
| --- | ---: |
| official canonical features | 43 |
| mapped train features | 43 |
| direct/direct-transform features | 31 |
| derived/proxy features | 12 |
| feature mapping errors | 0 |
| aligned rows | 640 |
| internal train rows | 531 |
| internal dev rows | 109 |
| validation errors | 0 |

Split balance:

| Split | Rows | Label 0 | Label 1 | `standing on` | `lying on` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `internal_train` | 531 | 270 | 261 | 263 | 268 |
| `internal_dev` | 109 | 50 | 59 | 57 | 52 |

## Leakage Audit

| Check | Count | Pass |
| --- | ---: | --- |
| scan overlap with official validation | 0 | true |
| endpoint overlap with official validation | 0 | true |
| official test usage | 0 | true |

## Output Views

| Output | 역할 |
| --- | --- |
| `model_safe_no_class_train_dev.jsonl` | primary M1-M4 train/dev input, no class labels, no `Q_e`, no `Z_e` |
| `class_ablation_train_dev.jsonl` | class-label diagnostic only |
| `hidden_train_dev_manifest.jsonl` | scan/object/class/source provenance, hidden from primary model |
| `feature_map.csv` | official 43-feature to train feature/formula mapping |
| `feature_alignment_audit.csv` | per-feature completeness/nonfinite audit |
| `runner_input_contract.json` | next runner input/fit policy |

## Important Caveat

Feature parity is schema-ready, not evidence-identical. `31/43` features are direct or direct-transform
mappings, while `12/43` are derived/proxy mappings such as contact-band count/density,
intersection volume, vertical overlap ratio, and symmetric contact-band ratio. The next runner must
report this provenance and avoid claiming that train/eval evidence is physically identical at the raw
extractor level.

## Boundary

- no metric run
- no official test
- no paper result promotion
- class labels remain ablation-only
- `Q_e` remains diagnostic-only
- no `p_obs` / `p_rel` claim
- no `support_contact solved` claim

## Next

```text
compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment
```

다음 단계는 Docker metric runner를 추가/실행하는 단계다. Fit은 `internal_train`,
hyperparameter/threshold selection은 `internal_dev`에서만 가능하며, official validation은
eval-only로 한 번만 사용해야 한다.
