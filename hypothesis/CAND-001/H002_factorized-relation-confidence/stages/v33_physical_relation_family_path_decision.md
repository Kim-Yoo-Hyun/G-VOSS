# V33 Physical Relation-Family Path Decision

Date: 2026-06-23 KST

## Purpose

v32 capacity scan 이후 v15 same-witness HL/LH matching 조건을 유지할지, 완화할지,
cross-stratum contrast로 재정의할지 결정했다. 이 단계는 label sheet 생성이나 posterior
smoke가 아니라 target construction route를 다시 고정하는 path decision이다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v15_physical_relation_family_path_decision_after_capacity_scan/
    summary.json
    report.md
    option_matrix.jsonl
    selected_plan.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v15_physical_relation_family_path_decision_select_cross_stratum_support_contact_contrast
selected_path = reject_same_witness_select_v16_cross_stratum_support_contact_contrast
support_contact_rows_available = 51491
support_contact_rows_after_caps = 224
support_contact_mixed_witness_strata = 0
selected_by_queue = LH:240
selected_by_geometry_status = satisfied:240
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v16_cross_stratum_support_contact_contrast_plan
```

## Decision

Selected next route:

```text
controlled_cross_stratum_support_contact_contrast
```

Same-witness HL/LH matching은 reject했다. H002가 검증하려는 핵심은 서로 다른
semantic-geometry disagreement state의 reliability다. 따라서 `HL`과 `LH`가 같은 geometry
witness bucket 안에 들어와야 한다는 요구는 H002 문제 정의와 맞지 않는다.

## Rejected Options

- `run_posterior_smoke_now`: label target이 아직 없으므로 reject.
- `mine_v15_preview_as_label_sheet`: preview가 전부 `LH/satisfied`라 shortcut target이 될 위험이 커서 reject.
- `add_more_support_contact_rows`: row count는 이미 충분하므로 reject.
- `relax_same_witness_matching_only`: 대체 independence control이 없어 reject.
- `freeze_support_contact_and_switch_to_attachment_now`: attachment는 유망하지만 support/contact 자체가 막힌 것은 아니므로 defer.

## V16 Requirements

v16은 `support_contact`를 유지하되, matching 단위를 same witness stratum이 아니라
cross-stratum pair/block으로 바꾼다.

Required controls:

- predicate label
- source queue kind
- semantic rank band
- scan/subgraph distribution
- subject/object label distribution
- endpoint generic state
- coverage state
- reason family
- `p_geom_bin`
- `geometry_status`

Boundary:

- `queue_kind`, `rank_band`, `geometry_status`, `p_geom_valid`, `machine_hint`, `label_match_status`, quota cell은 visible label surface에 노출하지 않는다.
- `standing on`은 eligible HL row가 없으므로 primary balanced target이 아니라 diversity/control로만 사용한다.
- `attachment_deferred`는 backup schema probe로 유지한다.
- posterior smoke는 label fill, ingestion, target-independence audit이 끝나기 전까지 계속 금지한다.

## Next

```text
reliability_target_v16_cross_stratum_support_contact_contrast_plan
```
