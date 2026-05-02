# Feasibility

Last updated: 2026-05-03

## Status

H001 is feasible as a one-scan hypothesis smoke test.

The current gate is no longer dataset access, baseline selection, prediction schema definition, layout compatibility, or layout checker implementation. The current gate is selecting a minimal `VL-SAT` eval path.

Current gate:

```text
one-scan verifier smoke test: passed
subtype-aware verifier contract: written
official subset strategy: written
prediction-level baseline: VL-SAT selected
prediction schema: written
layout compatibility: checked
layout checker: implemented and run
multi-scan evaluation: pending
prediction-level evaluation: pending
baseline reproduction: deferred
```

## Dataset

Validated local data:

```text
local_dataset/3DSSG/objects.json
local_dataset/3DSSG/relationships.json
local_dataset/3DSSG/classes.txt
local_dataset/3DSSG/relationships.txt
local_dataset/3DSSG_subset/relationships.json
local_dataset/3DSSG_subset/relationships_train.json
local_dataset/3DSSG_subset/relationships_validation.json
local_dataset/3DSSG_subset/classes.txt
local_dataset/3DSSG_subset/relationships.txt
local_dataset/3RScan/files/3RScan.json
local_dataset/3RScan/files/train_scans.full.txt
local_dataset/3RScan/files/val_scans.full.txt
local_dataset/3RScan/download_3rscan.py
```

Validated sample scan:

```text
f62fd5fd-9a3f-2f44-883a-1e5cf819608e
```

Required sample payload exists:

```text
labels.instances.annotated.v2.ply
semseg.v2.json
mesh.refined.0.010000.segs.v2.json
```

Dataset facts:

- 60 3DSSG objects join to 60 `semseg.v2.json` objects.
- 772 relation tuples are available.
- PLY vertex count matches `segIndices`: 72,017.

## Implementation

Completed smoke-test scripts:

```text
tools/export_evidence.py
tools/apply_rules_v0.py
tools/export_point_support.py
tools/apply_rules_v1.py
tools/export_visual_inspection_points.py
tools/check_layout.py
```

All scripts are kept inside the H001 folder.

## Results So Far

Phase A evidence export:

- 772 edges exported;
- validation passed;
- missing object/semseg joins: 0.

Phase B rule verifier:

- 772 decisions;
- primary metric denominator: 129;
- `proximity`: 68 satisfied;
- `relative_vertical`: 40 satisfied, 2 violated, 6 uncertain;
- `support_contact`: weak under OBB-only evidence.

Phase C point support evidence:

- 32 support/contact records;
- 19 `point_satisfied`;
- 1 `point_uncertain`;
- 12 `point_violated`;
- floor-support recovery: 13/16.

Phase D v1 verifier:

- all 772 edges preserved;
- 32 support/contact edges checked;
- 19 `satisfied`;
- 1 `uncertain`;
- 12 `violated`;
- v1 review queue: 13.

Visual inspection:

- 7 representative support/contact cases inspected with colored point subsets;
- 6 visually plausible or likely plausible;
- 3 `rule_too_strict`;
- 3 `local_surface_estimator_issue`;
- 1 `segmentation_or_instance_issue`.

## Remaining Gaps

Still pending:

- minimal `VL-SAT` eval path decision;
- layout prep staging policy;
- calibration table schema and counterfactual negative generation;
- prediction-level validation with model outputs;
- horizontal coordinate-frame validation.

## Decision

Proceed inside the hypothesis folder.

Do not start full baseline reproduction or broader experiment infrastructure until local `VL-SAT` layout prep and a minimal eval path are selected.

## Layout Checker Result

Latest output:

```text
artifacts/layout/vlsat/report.md
artifacts/layout/vlsat/summary.json
artifacts/layout/vlsat/prep_manifest.json
```

Result:

- default `VL-SAT` layout status: blocked;
- H001 one-scan geometry-ready scan dirs: 1;
- blockers: missing `relations.txt`, `train_scans.txt`, `validation_scans.txt`, aligned PLY, and `multi_view`;
- warnings: local 3RScan path convention mismatch, no downloaded validation split scan, and only one local scan payload.
