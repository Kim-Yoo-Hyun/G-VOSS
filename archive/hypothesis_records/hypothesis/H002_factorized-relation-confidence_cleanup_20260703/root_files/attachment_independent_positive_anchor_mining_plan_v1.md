# H002 Attachment Independent Positive Anchor Mining Plan V1

Created: 2026-06-25 KST

## Purpose

`attachment_independent_target_repair_plan_v1` 이후의 다음 mining 경로를 고정한다.

현재 H002의 새 방향은 `T_e`, `Z_e`, `G_e`, `C_e`, `Q_e`를 분리해 relation reliability를
학습하는 것이다. 하지만 attachment 계열에서는 독립 audit label이 positive-sparse하게
형성되어, 지금 상태로 posterior smoke를 돌리면 factorized method를 검증하는 것이 아니라
target 부족과 shortcut을 학습할 위험이 크다.

따라서 이 단계의 목적은 모델 학습이 아니라, 다음 후보 mining이 지켜야 할 quota, control,
visible/hidden field boundary, fallback rule을 명시하는 것이다.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_positive_anchor_mining_plan_v1.py
```

Default output:

```text
artifacts/attachment_independent_positive_anchor_mining_plan_v1/
```

## Result

```text
status = h002_attachment_independent_positive_anchor_mining_plan_v1_ready
selected_route = train_only_positive_anchor_candidate_mining_then_packet_materialization
next_todo = attachment_independent_positive_anchor_candidate_mining_v1
validation_errors = 0
```

Prior capacity:

```text
current_200 = 17 positive / 91 negative
all_v20_matched_298 = 24 positive / 116 negative
full_candidate_400_visible_rule = 45 positive / 174 negative
full_candidate_400 mixed_predicate_visible_pair_groups = 0
```

## Mining Contract

```text
target_rows_before_audit = 560
primary_requested_rows_before_audit = 480
diagnostic_requested_rows_before_audit = 80
post_audit_min_primary_binary_rows = 160
post_audit_min_accept_positive = 60
post_audit_min_reject_negative = 60
post_audit_min_hanging_on_accept = 40
post_audit_min_attached_to_accept_for_primary = 30
post_audit_min_mixed_endpoint_family_groups = 10
post_audit_min_mixed_visible_pair_groups = 3
```

## Query Plan

| Query | Predicate | Role | Requested | Gate |
| --- | --- | --- | ---: | --- |
| `Q1_hanging_on_positive_anchor` | `hanging on` | primary positive anchor | 120 | audit accept >= 40 |
| `Q2_hanging_on_hard_negative` | `hanging on` | matched hard negative | 120 | audit reject >= 60 |
| `Q3_attached_to_structural_positive_anchor` | `attached to` | primary if capacity passes | 120 | audit accept >= 30 |
| `Q4_attached_to_hard_negative` | `attached to` | matched hard negative | 120 | audit reject >= 60 |
| `Q5_connected_to_diagnostic_optional` | `connected to` | diagnostic only | 80 | no primary gate |

## Field Boundary

Visible to label fill:

- subject/object/predicate labels;
- subject/object/pair visual crops;
- mesh/contact/context packet;
- packet completeness or coverage note.

Hidden from label fill:

- source score and rank;
- source id;
- proxy role;
- cell id;
- machine hint;
- geometry-status bucket;
- prior v20 labels;
- current visible-rule labels;
- existing GT match status.

## Interpretation

현재 병목은 posterior 결합 방식이 아니라 independent accept-positive evidence 부족이다.

Full train proxy capacity 자체는 크지만, 이전 v23 blocker가 보인 것처럼 affordance, rank,
coverage를 함께 통제하면 mixed cell diversity가 급격히 줄어든다. 따라서 다음 mining은 단순히
positive row를 많이 모으는 것이 아니라, positive anchor와 hard negative가 같은 endpoint
family, rank band, coverage tier 안에서 같이 존재하도록 설계해야 한다.

`hanging on`은 primary anchor 후보로 유지한다. `attached to`는 audit 이후 accept-positive가
30개 이상 확보될 때만 primary로 올리고, 그렇지 않으면 diagnostic으로 둔다. `connected to`는
기능적 연결을 확인할 수 있는 visual/mesh evidence가 생기기 전까지 diagnostic-only다.

## Next

```text
attachment_independent_positive_anchor_candidate_mining_v1
```
