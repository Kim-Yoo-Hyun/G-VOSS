# V31 Physical Relation-Family Repair Plan

Date: 2026-06-23 KST

## Purpose

v30 path decision 이후 v15 physical relation-family branch의 repair contract를 고정했다.
이 단계는 새로운 label fill이나 posterior smoke가 아니라, 다음 candidate mining 전에
만족해야 할 capacity, matching, label-surface 조건을 명시하는 단계다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v15_physical_relation_family_repair_plan/
    summary.json
    report.md
    requirements.json
    quota_plan.csv
    label_surface_contract.md
    capacity_scan_contract.json
    v14_failure_snapshot.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v15_physical_relation_family_repair_plan_ready_for_capacity_scan
selected_route = support_contact_witness_matched_repair_with_relative_vertical_control
quota_plan_total_rows = 240
support_contact_candidate_target_rows = 224
relative_vertical_control_rows = 16
minimum_binary_positive_after_label_fill = 60
minimum_binary_negative_after_label_fill = 60
minimum_mixed_witness_strata_before_label_fill = 8
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v15_physical_relation_family_capacity_scan
```

## Decision

v15는 `support_contact`를 primary target으로 유지하고, `relative_vertical`은 small control로
축소한다.

Selected route:

```text
support_contact_witness_matched_repair_with_relative_vertical_control
```

현재 primary predicates:

```text
lying on
standing on
```

현재 control predicate:

```text
lower than
```

`attached to`, `hanging on`, `connected to`는 여전히 유망하지만, 현재 H002 target에는 넣지
않는다. 이 계열은 witness schema와 multi-view audit protocol이 준비된 뒤 별도 probe로
넘기는 것이 맞다.

## Why This Repair

v14 failure는 단순히 reliable positive가 `48`개라서 `50`개 threshold보다 2개 부족한 문제가
아니다. Balanced `48/48` slice를 만들어도 다음 shortcut이 남는다.

- scan/object identity
- visible and hidden pair identity
- quota cell
- rank band
- machine hint
- direct witness-summary text

따라서 v15는 positive를 늘리는 동시에 같은 predicate/source queue/rank/geometry/witness
stratum 안에서 label이 갈릴 수 있는 후보를 찾아야 한다.

## Repair Requirements

- Positive/negative binary labels after fill must each reach at least `60`.
- Pre-label candidate groups must include at least `8` mixed witness strata.
- Candidate matching axes are `predicate_label`, source queue, `rank_band`, `geometry_status`, `p_geom_bin`, coarse witness bin, reason signature, endpoint generic state, and semantic score band.
- `relative_vertical` cannot be used to satisfy the primary support/contact positive-mass gate.
- Visible label sheet must not expose `geometry_status`, `p_geom_valid`, `machine_hint`, queue kind, quota cell, or direct witness-summary phrases.
- Hidden audit fields remain audit/control metadata only.
- Multi-view remains audit evidence only, not deployable posterior input.

## Boundary

This is train-only hypothesis-stage target repair.

It is not:

- paper-level benchmark evidence
- posterior performance evidence
- validation/test evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v15_physical_relation_family_capacity_scan
```

The next step should verify whether the train queue has enough witness-matched support/contact capacity
before producing a new label-ready sheet.
