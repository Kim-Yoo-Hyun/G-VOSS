# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Label Fill

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill_completed
selected_path = codex_visible_packet_proxy_labels_filled_user_requested
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion
```

## Purpose

This step fills the 480 label-ready support/contact packet rows with Codex proxy labels, as requested
by the user.

It uses reviewer-visible packet fields and packet asset paths only. It does not use hidden manifest
fields, source score/rank, old `geometry_status`, old `p_geom_valid`, label-match status, prediction
ids, subject ids, object ids, validation/test rows, or H001 artifacts.

Important provenance:

```text
label_provenance = codex_visible_packet_proxy_labeler_user_requested
independent_human_audit = false
```

Therefore this is a user-requested proxy label fill, not an independent blind human audit.

## Label Counts

Overall:

```text
rows = 480
accept = 208
reject = 161
abstain = 111
observability sufficient = 480
```

By predicate:

```text
lying on: accept 53 / reject 87 / abstain 54
standing on: accept 73 / reject 63 / abstain 20
supported by: accept 82 / reject 11 / abstain 37
```

Geometry support:

```text
supports = 208
contradicts = 161
ambiguous = 111
```

Uncertainty reason:

```text
other = 265
ambiguous_pose = 120
ontology_overlap = 95
```

## Label Policy

The fill uses conservative visible-category rules:

- `lying on` accepts soft/resting subjects on plausible support surfaces.
- `standing on` accepts upright/movable objects on plausible support surfaces.
- `supported by` is broad and accepts many support-surface cases, but same-label, generic, and
  structural ambiguities are abstained or rejected.

Counter-relation handling:

- rejected `lying on` rows may point to `standing on` or `supported by`.
- rejected `standing on` rows may point to `lying on` or `supported by`.
- `supported by` is not treated as a clean negative for `standing on`; it remains broad.

## Outputs

- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/summary.json`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/filled_visible_review_sheet.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/label_decisions.jsonl`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/label_counts.csv`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/report.md`
- `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/validation_errors.jsonl`

## Verification

```text
python -m py_compile tools/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill.py
filled rows = 480
label decisions = 480
validation_errors.jsonl rows = 0
```

## Next

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion
```

The next step should join the filled visible sheet with the hidden manifest after label lock and
derive `C_e`, `Q_e`, `p_obs`, and `p_rel` targets. Shortcut and target-independence audits must run
before any learned smoke.
