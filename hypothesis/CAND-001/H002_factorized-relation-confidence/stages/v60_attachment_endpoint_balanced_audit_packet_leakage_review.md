# V60 Attachment Endpoint-Balanced Audit Packet Leakage Review

## Purpose

v59에서 materialize한 320-row v20 audit packet의 reviewer-visible surface가
hidden construction metadata를 누출하지 않는지 formal review를 수행한다.

이 단계는 leakage review만 수행한다. Label fill, ingestion, posterior smoke는 수행하지
않는다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization/
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review/
```

Script:

```text
tools/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review.py
```

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review_passed_ready_for_label_fill
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_fill
validation_errors = 0
visible_leakage_hits = 0
formal_leakage_review_pass = true
posterior_smoke_allowed = false
multi_view_as_model_input = false
```

## Reviewed Surface

```text
visible_sheet_rows = 320
packet_markdown_files = 320
packet_dirs = 320
neutral_image_files = 5836
hidden_manifest_rows = 320
hidden_rows_with_source_paths = 320
hidden_rows_with_scan_ids = 320
hidden_rows_with_gt_match_axis = 320
```

## GT Auxiliary Axis

Existing GT relation match is preserved only in the hidden materialized manifest.
It is not exposed to the reviewer-visible sheet, packet markdown, or packet-local
image filenames.

```text
gt_label_match_status:
  exact_match = 1
  family_match = 5
  pair_has_other_predicate = 81
  no_gt_for_pair = 233
```

## Leakage Checks

Reviewer-visible surface was checked for:

- source paths
- scan/subgraph identifiers
- subject/object instance ids
- prediction ids
- construction metadata
- geometry status
- rank/score fields
- `p_geom_valid`
- raw feature fields
- existing GT-match fields
- RGA bucket labels
- non-neutral image filenames
- UUID-like scan ids

All checks passed with zero visible leakage hits.

## Interpretation

The v20 audit packets are clean enough to begin label fill. This does not mean
relation reliability labels are valid or target-independent. It only means the
visible audit surface does not expose hidden construction, geometry, semantic
rank/score, or GT-match metadata.

The next label fill must use only the leakage-reviewed visible sheet, packet
markdown, and packet-local neutral assets. Hidden manifest and GT-match axis are
allowed only after labels are locked, during label ingestion and mismatch
analysis.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows used.
- No labels filled.
- No posterior trained or evaluated.
- Multi-view/mesh remains audit/confirmation evidence only.
- Existing GT relation match remains an auxiliary analysis axis, not the primary target.
- Human-audited reliability label remains the primary future target.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_fill
```
