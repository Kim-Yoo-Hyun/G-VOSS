# V23 Proximity Scene/Geometry Path Decision

Date: 2026-06-23 KST

## Purpose

v22 target-independence audit 이후 `close by` / proximity branch를 계속 primary posterior
route로 밀지, diagnostic evidence로 고정할지, 또는 다른 relation-family target route로 이동할지
결정했다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v13_proximity_lh_scene_geometry_path_decision_after_audit/
    summary.json
    report.md
    option_matrix.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_path_decision_select_physical_relation_feasibility
selected_path = freeze_v13_proximity_diagnostic_select_v14_physical_relation_family_feasibility
next_todo = reliability_target_v14_physical_relation_family_feasibility_scan
```

## Decision

v13 proximity branch는 primary posterior target으로 쓰지 않는다. 대신 다음 역할로 고정한다.

```text
diagnostic_only_generality_and_limitation_evidence
```

이 branch가 보여준 것은 다음이다.

- `close by`는 train-only LH row count가 충분하다.
- scene/geometry-aware label surface는 v12 visible-only label보다 same-pair mixed contrast를
  개선했다.
- 하지만 dense proximity는 reliable positive가 sparse하고, geometry/scene text shortcut과
  강하게 얽힌다.
- current RGA queue에서는 proximity가 LH-only라 bidirectional RGA claim을 단독으로 담당할 수
  없다.

## Rejected Options

| Option | Verdict | Reason |
| --- | --- | --- |
| run posterior smoke now | reject | primary reliability target이 positive-sparse이고 strict/diagnostic clear slice가 0개 |
| use geometry-support as primary target | reject | class mass는 있지만 auxiliary evidence-axis target이고 strict independent slice가 0개 |
| mine more `close by` positives immediately | reject for primary path | geometry-witness text shortcut을 강화할 가능성이 큼 |
| return to exact support/vertical pair route | reject as repeat | v8/v9에서 exact-pair support/vertical route는 rank/predicate entanglement로 이미 막힘 |
| add multi-view as model input now | reject for now | clean S/G/C/U target 전에 deployable visual axis를 넣으면 target repair와 model expansion이 섞임 |

## Selected Next Route

```text
reliability_target_v14_physical_relation_family_feasibility_scan
```

목표는 dense proximity noise나 exact-pair predicate/rank shortcut에 덜 지배되는 primary H002
target route를 찾는 것이다.

Candidate families:

- `support_contact`: `standing on`, `lying on`
  - first feasibility anchor.
  - contact/support witness가 구체적이지만 old exact-pair construction은 반복하지 않는다.
- `attachment_deferred`: `attached to`, `hanging on`, `connected to`
  - novelty-oriented feasibility candidate.
  - dense proximity보다는 relation reliability를 설명할 여지가 크지만 witness schema가 필요하다.
- `relative_vertical`: `higher than`, `lower than`
  - control family only.
  - geometry-easy relation이라 primary novelty target보다는 control 역할이 적합하다.

## Claim Boundary

이 결정은 H002 가설 포기가 아니다. 실패한 것은 current proximity target construction이다.

```text
semantic score != geometry validity != relation reliability
```

이 핵심 claim은 유지한다. 다만 primary posterior target은 v13 proximity가 아니라 physical
relation-family feasibility route에서 다시 찾아야 한다.

## Next

```text
reliability_target_v14_physical_relation_family_feasibility_scan
```

다음 단계는 train-only에서 family/predicate별 row mass, label 가능성, same-family/witness
controlled slice 가능성, continuous geometry evidence와 frozen geometry-status shortcut 분리
가능성을 먼저 확인한다.
