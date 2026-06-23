# V34 Cross-Stratum Contrast Plan

Date: 2026-06-23 KST

## Purpose

v33 path decision에서 선택한 `controlled_cross_stratum_support_contact_contrast` route를
실제 target construction plan으로 고정했다. 이 단계는 candidate mining, label fill, posterior
smoke가 아니라 cross-stratum block construction, quota/cap policy, visible label surface,
post-label target-independence audit 조건을 정의하는 단계다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v16_cross_stratum_support_contact_contrast_plan/
    summary.json
    report.md
    contrast_schema.json
    sampling_policy.json
    quota_plan.csv
    label_surface_contract.json
    label_surface_contract.md
    target_independence_plan.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v16_cross_stratum_support_contact_contrast_plan_ready_for_capacity_scan
next_todo = reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan
quota_plan_total_rows = 240
posterior_smoke_allowed = false
validation_errors = 0
```

## Capacity Basis

```text
lying_on_eligible_hl = 896
lying_on_eligible_lh = 26882
standing_on_eligible_hl = 0
standing_on_eligible_lh = 23713
support_contact_rows_available = 51491
support_contact_rows_after_caps = 224
support_contact_mixed_witness_strata = 0
```

`lying on`만 primary balanced contrast로 사용한다. `standing on`은 hard filter 이후 eligible
HL이 없으므로 primary balanced target에 넣지 않고 diversity/diagnostic row로 둔다.

## Quota

```text
P1_lie_hl_primary_overconfidence = 100
P2_lie_lh_primary_underconfidence = 100
D1_stand_lh_diversity_diagnostic = 24
C1_vertical_lower_control = 16
```

Primary target rows:

```text
lying on HL = 100
lying on LH = 100
```

Diagnostic/control rows:

```text
standing on LH = 24
lower than LH = 16
```

## Core Rules

- HL/LH are not labels.
- HL rows must not be labeled reject by construction.
- LH rows must not be labeled accept by construction.
- `queue_kind`, `rank_band`, `geometry_status`, `p_geom_valid`, `machine_hint`, `label_match_status`, quota cell, `RGA-HL`, and `RGA-LH` are forbidden visible fields.
- Cross-stratum blocks match on predicate, endpoint generic state, coarse object category, and coverage state.
- Geometry status, `p_geom_bin`, reason signature, and witness bin are audit/control axes, not same-witness matching axes.
- Posterior smoke remains blocked until label fill, ingestion, and target-independence audit pass.

## Post-Label Gates

```text
minimum_binary_rows = 120
minimum_positive_rows = 50
minimum_negative_rows = 50
strict_slice_min_rows = 80
strict_slice_min_per_class = 35
diagnostic_slice_min_rows = 40
diagnostic_slice_min_per_class = 15
```

Shortcut probes must include queue-kind-only, geometry-status-only, p-geom-bin-only,
predicate/rank/source, scan/object/pair identity, reason-family-only, quota-cell-only, and block-id-only probes.

## Boundary

This is train-only hypothesis-stage planning.

It is not:

- a label-ready sheet
- posterior performance evidence
- validation/test evidence
- paper-level benchmark evidence
- a change to H001 or paper artifacts

## Next

```text
reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan
```
