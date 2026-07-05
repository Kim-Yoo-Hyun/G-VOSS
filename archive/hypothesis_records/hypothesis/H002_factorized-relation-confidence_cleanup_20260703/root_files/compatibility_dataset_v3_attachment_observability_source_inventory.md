# Compatibility Dataset V3 Attachment Observability Source Inventory

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_source_inventory/
status = h002_compatibility_dataset_v3_attachment_observability_source_inventory_ready_for_materialization_plan
selected_path = r7_source_inventory_supports_attached_hanging_materialization_connected_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_materialization_plan
```

This step inventories source availability only. It does not materialize rows, run
a learned model, use validation/test data, or promote paper evidence.

## Full Train Inventory

The full train-side Open3DSG relation rows contain broad R7 candidate capacity:

| Predicate | Full-Train Rows | Exact GT Match | Family Match | No GT Pair | Unsupported Geometry |
| --- | ---: | ---: | ---: | ---: | ---: |
| `attached to` | 185,346 | 6,190 | 1,113 | 142,571 | 185,346 |
| `hanging on` | 185,346 | 939 | 6,364 | 142,571 | 185,346 |
| `connected to` | 185,346 | 174 | 7,129 | 142,571 | 185,346 |

All R7 predicates are `unsupported` under the existing geometry verifier. This is
not treated as a failure. It means the attachment route cannot reuse the old
numeric geometry-only verifier as the main evidence source; it needs explicit
point/mesh/multiview observability evidence before materialization.

The full-train R7 rows cover `1,157` unique scans and `185,346` unique directed
pairs. All `1,157` scans have scan directories, multiview data, sequence data,
mesh-ready files, and point/mesh-ready files in the local source inventory.

## Packet Reuse Inventory

The previous attachment positive-anchor packet artifact remains useful as
source evidence, not as a direct training target.

| Predicate | Packet Rows | Packet Ready | Audit Ready | Strong Pair Visual | Explicit Topology |
| --- | ---: | ---: | ---: | ---: | ---: |
| `attached to` | 238 | 238 | 238 | 46 | 0 |
| `hanging on` | 242 | 242 | 242 | 58 | 0 |
| `connected to` | 80 | 80 | 80 | 12 | 0 |

Aggregate packet source availability:

- rows: `560`
- ready packets: `560`
- both subject/object packet images: `560`
- mesh packet ready: `560`
- multiview packet ready: `560`
- audit-ready rows: `560`
- strong same-frame pair visual rows: `116`
- individual visual plus mesh rows: `444`

## Route Decision

`attached to` and `hanging on` are ready for an observability materialization plan.
The next step should define model-safe `G_e` and `Q_e` fields, then materialize a
row set only after the schema blocks review labels, source rank/score, packet id,
and construction fields.

`connected to` remains diagnostic. The inventory has `80` ready packet rows, but
`0` rows with explicit topology or functional-connection source evidence. It can
support observability/failure taxonomy, but not a primary `p_rel` target yet.

## Boundary

- Multi-view and mesh are source-inventory/audit evidence only at this stage.
- `review_*` labels are not used for inventory construction.
- No row materialization or learned smoke is allowed from this step alone.
- The next plan must keep `p_obs` before `p_rel`.
