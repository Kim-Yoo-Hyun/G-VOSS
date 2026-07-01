# R7 Attachment Observability Class-Pair Repair Mining Plan

Date: 2026-06-30

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan_ready
selected_path = plan_exact_predicate_class_pair_capacity_scan_before_packet_mining
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan
```

## Decision

Do not start candidate mining or packet materialization yet.

The next step must first scan full-train R7 candidates for exact
`predicate_label + subject_label + object_label` cells that contain both likely
positive and likely negative rows. This is necessary because the current 560-row
artifact has zero exact predicate/class-pair mixed capacity.

## Input Evidence

- Current R7 path decision selected one repair attempt before diagnostic freeze.
- Source inventory has `185,346` full-train rows for each of:
  - `attached to`
  - `hanging on`
  - `connected to`
- Prior attachment capacity scans show broad capacity exists:
  - V20 exact endpoint-pair mixed groups: `4,616`
  - V20 exact endpoint-pair balanced pair capacity: `26,054`
  - V21 same predicate/rank/family mixed groups: `591`
  - V21 same predicate/rank/family balanced capacity: `53,539`
  - V21 strict rank/geometry/family balanced capacity: `4,507`

These are not yet sufficient for R7 repair, because the missing control is exact
subject/object class pair under the same predicate.

## Quota Plan

| Quota | Predicate | Role | Requested Packet Rows If Capacity Passes | Post-label Accept Min | Post-label Reject Min |
| --- | --- | --- | ---: | ---: | ---: |
| `R7A_attached_exact_class_pair_repair` | `attached to` | primary repair | 240 | 50 | 100 |
| `R7H_hanging_exact_class_pair_repair` | `hanging on` | primary repair | 240 | 50 | 100 |
| `R7C_connected_diagnostic` | `connected to` | diagnostic only | 0 | 0 | 0 |

## Capacity Gates

The next capacity scan must pass:

- at least `400` balanced primary rows
- at least `100` positive rows
- at least `20` exact predicate/class-pair mixed strata

If exact class-pair capacity fails, coarse object-family balancing can be
reported only as a weaker fallback. It must not be treated as equivalent to
exact class-pair control.

## Field Boundary

Hidden selection-only fields:

- proxy role
- geometry bucket
- coverage proxy
- rank band
- source score / source rank
- GT match status
- packet id / packet path
- review label

Allowed model-safe fields after future label ingestion:

- `T_e` predicate/object semantic content
- `G_e_attachment` derived geometry evidence
- `Q_e_observability` derived evidence availability

## Route Decisions

| Route | Decision | Reason |
| --- | --- | --- |
| exact predicate/class-pair capacity scan | selected next | avoids repeating the class-pair shortcut failure |
| candidate mining now | reject | capacity under exact class-pair control is unknown |
| family-pair fallback | fallback only | may still leak exact class labels |
| freeze R7 diagnostic now | fallback not selected | one targeted repair scan is still justified |
| `connected to` primary | defer | explicit topology/functional evidence is missing |

## Boundary

- Train-only planning artifact.
- No labels were filled.
- No rows were materialized.
- No packet materialization was started.
- No learned smoke was run.
- No validation/test split was used.
- H001 artifacts were not modified.
