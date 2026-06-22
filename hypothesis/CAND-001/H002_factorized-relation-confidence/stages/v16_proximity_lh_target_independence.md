# V16 Proximity LH Target Independence

Date: 2026-06-22 KST

## Purpose

v15에서 ingested 된 `proximity / close by` LH-only proxy target이 posterior smoke에 쓸 수
있을 만큼 독립적인지 확인했다.

이 단계의 핵심 질문:

```text
Can the target be predicted by shortcut variables such as object pair or scan id?
Does any controlled slice remain after balancing rank, label-match, machine-hint, scan, and object-pair axes?
```

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v12_proximity_lh_only_target_independence_audit/
    summary.json
    report.md
    full_risk_audit.json
    slice_audit.json
    object_pair_mixed_stats.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Result

```text
status = h002_reliability_target_v12_proximity_lh_only_independence_blocked_object_pair_shortcut
binary_rows = 107
binary_target = 1:36, 0:71
strict_slices = 0
diagnostic_slices = 0
object_pair_mixed_binary_groups = 0
quick_risk_flags = 10
next_todo = reliability_target_v12_proximity_lh_only_path_decision_after_audit
```

## Main Blocker

The proxy target is explained by object-pair identity.

```text
subject_object_label_pair_hidden -> binary accuracy = 1.0000
subject_object_visible_pair -> binary accuracy = 1.0000
scan_id -> binary accuracy = 0.9720
```

Exact object-pair mixed contrast:

```text
subject_object_visible_pair_binary mixed_groups = 0
subject_object_label_pair_hidden_binary mixed_groups = 0
```

This means that within the same visible subject-object pair, the proxy labels do not contain both
positive and negative examples. Therefore a posterior model could solve the target through object
identity rather than relation reliability.

## Slice Audit

No slice passed:

```text
full_binary: count gate passes, object-pair and scan risks remain
label_match_balanced: count gate passes, object-pair and scan risks remain
machine_hint_balanced: count gate passes, object-pair and scan risks remain
rank_band_balanced: count gate passes, object-pair and scan risks remain
scan_balanced: too few rows
subject_label_balanced: diagnostic count gate passes, object-pair risk remains
object_label_balanced: diagnostic count gate passes, object-pair risk remains
subject_object_pair_balanced: 0 rows
```

## Interpretation

This is a target construction failure, not evidence against the H002 framework.

The path that failed is specifically:

```text
visible object-pair text -> proxy label -> posterior target
```

The failure says that text-only proxy labels are not independent enough for H002 posterior validation.
It does not falsify the claim:

```text
semantic score != geometry validity != relation reliability
```

## Next

```text
reliability_target_v12_proximity_lh_only_path_decision_after_audit
```

The next decision should choose whether to:

1. freeze this proximity branch as diagnostic-only negative evidence;
2. repair the target with scene/geometry-aware label evidence;
3. mine same object-pair mixed contrasts from additional rows;
4. route back to another relation family.
