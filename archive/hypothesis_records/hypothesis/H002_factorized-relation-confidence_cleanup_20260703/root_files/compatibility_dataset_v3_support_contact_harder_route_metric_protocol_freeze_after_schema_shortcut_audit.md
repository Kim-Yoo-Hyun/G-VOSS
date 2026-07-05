# Support/Contact Harder Route Metric Protocol Freeze After Schema Shortcut Audit

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit/
status = h002_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit_ready
selected_path = support_contact_hard_metric_protocol_frozen_select_train_eval_alignment
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze
```

이 단계는 richer support/contact hard route metric을 실행하기 전에 metric, model view,
control, shortcut baseline, train/eval policy, claim boundary를 고정한 단계다. Metric은
실행하지 않았고 official test도 사용하지 않았다.

## Frozen Metric Contract

| 항목 | 값 |
| --- | --- |
| target | `C_e` |
| route family | `support_contact` |
| predicates | `standing on`, `lying on` |
| official validation rows | `3178` |
| paired groups | `1589` |
| richer `G_e` features | `43` |
| primary metric | `support_contact_AUROC` |
| primary comparison | `M4_TxG_compatibility` vs `M1_predicate_only`, `M2_geometry_only`, `M3_concat` |

Secondary metrics:

- `support_contact_AUPRC`
- balanced accuracy
- macro-F1
- Brier if probabilistic
- paired-group accuracy
- per-predicate AUROC
- per-class-pair diagnostic when cell size is sufficient

## Model Views

| View | 역할 | Main claim 사용 |
| --- | --- | --- |
| `M0_constant` | sanity baseline | no |
| `M1_predicate_only` | no-class predicate shortcut baseline | required baseline |
| `M2_geometry_only` | predicate-independent geometry baseline | baseline |
| `M3_T_plus_G_concat` | plain fusion baseline | baseline |
| `M4_TxG_compatibility` | primary compatibility model | primary hard-route `C_e` |
| `A1_class_ablation` | class-label diagnostic ablation | diagnostic only |
| `D1_Q_e_diagnostic` | observability diagnostic | diagnostic only, no `p_obs` claim |

Primary `C_e`는 `T_e + G_e`만 사용한다. Class labels, `Q_e`, `Z_e`, source score/rank,
H001 `p_geom_valid`, hidden construction fields는 primary metric input에서 제외한다.

## Required Controls

- wrong-`T` same-route
- shuffled-`G` global
- shuffled-`G` within class-pair
- predicate-only shortcut baseline
- `predicate x class-pair` shortcut diagnostic
- class-ablation diagnostic
- `Q_e` diagnostic

`predicate x class-pair` majority accuracy는 `0.993707`로 높다. 따라서 이 protocol은
support/contact를 solved family로 주장하지 않는다. Metric이 좋아지더라도 주장은
“support/contact에서 predicate-geometry interaction이 필요한지”로 제한한다.

## Train/Eval Policy

Official validation은 eval-only다. 이 row에서 모델을 학습하거나 threshold를 고르면 안 된다.

현재 available train reference:

| 항목 | 값 |
| --- | ---: |
| train point/multiview rows | 800 |
| train main rows | 640 |
| train diagnostic rows | 160 |
| train feature count | 63 |
| official validation feature count | 43 |

문제는 train reference가 prefixed 63-feature schema이고, official validation hard-route view가
canonical 43-feature schema라는 점이다. 따라서 metric runner 전에 train/eval feature
alignment audit가 필요하다.

## Claim Boundary

Enabled after runner and review:

- support/contact hard-route `C_e` metric
- predicate-geometry interaction vs baselines
- wrong-`T` and shuffled-`G` control analysis
- challenging-route failure analysis

Blocked:

- solved `support_contact` claim
- official test claim
- source reranking claim
- `p_obs` claim
- calibrated `p_rel` claim
- all-relation generalization claim
- paper result promotion without metric review

## Next

```text
compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze
```

다음 단계는 metric runner가 아니다. 먼저 train-side point/OBB/contact features를 official
43-feature canonical schema에 맞출 수 있는지 확인하고, internal train/dev split이 official
validation과 누수 없이 분리되는지 audit해야 한다.
