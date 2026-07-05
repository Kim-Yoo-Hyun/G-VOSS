# H002 Size-Relative Source Inventory After Schema Probe Plan

Date: 2026-06-29 KST

## Purpose

`size_relative` family의 `bigger than` / `smaller than` relation이 H002의
predicate-geometry compatibility probe로 materialize 가능한지 확인했다. 이 단계는
source inventory이며, model row materialization이나 learned smoke는 수행하지 않았다.

## Artifact

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan/
status = h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_ready
selected_path = size_relative_inventory_ready_for_candidate_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory
```

Generated files:

- `source_inventory.csv`
- `predicate_anchor_inventory.csv`
- `semseg_join_inventory.csv`
- `size_margin_inventory.csv`
- `class_pair_inventory.csv`
- `anchor_preview.jsonl`
- `next_plan_contract.json`
- `summary.json`
- `report.md`
- `validation_errors.jsonl`

## Source

Train-side source:

```text
local_dataset/3DSSG_subset/relationships_train.json
```

Reference full source:

```text
local_dataset/3DSSG/relationships.json
```

Geometry source:

```text
local_dataset/3RScan/scans/*/semseg.v2.json
```

The train source contains `923` `bigger than` rows and `923` `smaller than` rows.
The previous coverage probe reported `911/911`; this source inventory records the
actual train-subset source count as `923/923` and keeps the plan count as provenance.

## Key Counts

| Predicate | Train rows | Unique pair-predicate | Both OBB rows | Join rate | Compatible | Ambiguous | Opposes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bigger than` | 923 | 923 | 923 | 1.000 | 880 | 25 | 18 |
| `smaller than` | 923 | 923 | 923 | 1.000 | 880 | 25 | 18 |

Overall:

```text
anchor_rows = 1846
unique_directed_pair_predicate = 1846
pair_obb_status = both_obb 1846
volume_compatibility = compatible 1760 / ambiguous 50 / opposes 36
volume_ratio_band = strong_ge_1.50 1680 / medium_1.25_1.50 78 / weak_1.15_1.25 38 / ambiguous_lt_1.15 50
structural_pair_rows = 0
```

## Same-G Predicate-Flip Capacity

Strict compatible groups are anchors where the GT predicate agrees with the OBB
volume direction and the size margin is at least `1.25x`.

```text
strict_compatible_unique_flip_groups = 1728
strict_compatible_same_g_predicate_flip_rows = 3456
strict_compatible_unique_by_predicate = bigger than 864 / smaller than 864
unique_join_rate = 1.0
strict_structural_fraction = 0.0
```

This is sufficient for the next materialization-plan step.

## Important Caveat

The top class-pair rows are mostly same-class pairs:

```text
box->box = 460
chair->chair = 402
pillow->pillow = 398
shelf->shelf = 204
```

This is not a blocker because `bigger than` and `smaller than` are both balanced
inside these class pairs. However, the materialization plan must keep class-pair,
GT/source labels, and construction metadata out of the model-safe view. The target
must use same-G predicate-flip rows so that `G_e_size` alone cannot solve the
compatibility label.

## Boundary

- Train-side source inventory only.
- No validation/test rows used.
- No model rows materialized.
- No learned smoke or training run.
- No H001 artifacts modified.
- Not paper-level evidence.

## Next

```text
compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory
```

The next step should freeze row quota, class-pair caps, same-G group schema,
blocked fields, `G_e_size` / `Q_e_size` model-safe feature list, and the required
geometry-only / wrong-T / shuffled-G controls before creating rows.
