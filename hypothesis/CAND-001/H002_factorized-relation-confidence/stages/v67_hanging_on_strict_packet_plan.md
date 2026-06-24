# V67 Hanging-On Strict Packet Plan

## 목적

v66 path decision에서 선택한 `hanging on` strict primary route에 대해, 실제 label sheet를
만들기 전에 240-row packet plan이 가능한지 확인했다.

이 단계는 candidate materialization, visible packet 생성, label fill, ingestion, posterior smoke가
아니다. Full-train에서 hidden-only dry-run preview를 만들고, 다음 candidate mining의 quota와
visible/hidden field policy를 고정하는 단계다.

## 입력

- Input rows: `artifacts/train_rga_full/open3dsg_train_full/rga/match_rows.jsonl`
- Previous gate: `reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan`
- Primary predicate: `hanging on`
- Diagnostic predicates: `attached to`, `connected to`

## Strict Control

```text
strict_spec = predicate_label + rank_band + geometry_bucket + object_family_pair
predicate_label = hanging on
```

이 strict control은 모든 relation에 동일한 field 조합을 강제하는 rule이 아니다.
relation-family별 mismatch 구조가 다르므로, 공통 원칙은 shortcut control이고 구체 witness/control
field는 relation-specific이어야 한다.

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan_ready_for_candidate_mining
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining
validation_errors = 0
posterior_smoke_allowed = false
```

Full-train capacity:

```text
full_train_hanging_on_rows = 185346
strict_groups = 2222
strict_mixed_groups = 258
strict_balanced_capacity = 4507
```

Hidden-only dry-run selection:

```text
selected_rows = 240
selected_role_counts = 120 accept_proxy_supported_candidate / 120 reject_proxy_contradicted_candidate
selected_strict_groups = 95
scan_count = 192
visible_endpoint_pair_count = 193
max_rows_per_scan = 4
max_rows_per_visible_endpoint_pair = 5
max_rows_per_strict_group = 4
```

모든 pre-label gate가 통과했다.

## 해석

`hanging on` strict route는 packet planning 관점에서 충분히 넓고 균형 잡힌 후보 공간을 가진다.
특히 240-row preview가 95개 strict group과 192개 scan에 분산되므로, 이전 단계에서 반복적으로
문제가 됐던 scan/object/endpoint concentration risk가 상대적으로 낮다.

단, 이것은 아직 reliability label이나 posterior evidence가 아니다. 다음 candidate mining에서는
reviewer-visible sheet에서 다음 field를 숨겨야 한다.

- `scan_id`, `subgraph_id`, instance id
- `rank_band`, semantic rank/score
- `geometry_bucket`, geometry status, `p_geom_valid`
- `object_family_pair`
- `coverage_proxy`, `uncertainty_bucket`
- `gt_label_match_status`
- `planned_proxy_role`
- `strict_group_value`

## 다음 단계

```text
reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining
```

다음 단계에서는 이 plan을 사용해 hidden-field-safe candidate sheet를 만들어야 한다.
아직 label fill이나 posterior smoke로 넘어가지 않는다.

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan/`
- Summary: `summary.json`
- Packet plan: `packet_plan.json`
- Strict quota table: `strict_group_quota.csv`
- Hidden dry-run preview: `hidden_selection_preview.jsonl`
- Report: `report.md`
