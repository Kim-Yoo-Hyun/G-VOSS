# Eval Path

Last updated: 2026-05-03

## Role

This document decides the minimal `VL-SAT` evaluation path for H001 prediction-level validation.

The decision is made from a paper defensibility perspective: the baseline should stay as close as possible to the official `VL-SAT` assumptions so that any observed gain or loss can be attributed to H001 geometry verification/recalibration, not to a weakened baseline reproduction.

## Decision

Use the faithful route for both remaining blockers:

```text
aligned PLY: faithful route
multi_view: faithful route
```

Do not use the 3D-only plumbing route for reported baseline numbers.

The plumbing route remains allowed only as a temporary adapter smoke test if the faithful route is blocked by environment setup. Any plumbing result must be labeled non-reportable and excluded from main tables.

## Rationale

Top-tier reviewer risk:

- If `MODEL.use_2d_feats` is disabled, the `VL-SAT` baseline no longer follows its default visual-language setting.
- If unaligned PLY is used as a substitute for aligned PLY, geometry, object coordinates, and feature extraction may differ from the intended pipeline.
- If H001 is evaluated on a weakened or materially modified baseline, a reviewer can argue that improvements come from baseline degradation or setup mismatch, not from geometry-grounded verification.

Therefore the main H001 prediction-level path should preserve:

- official `3DSSG_subset` train/validation split;
- `VL-SAT` closed-set predicate vocabulary and relation score semantics;
- aligned PLY input expected by the dataset loader;
- `multi_view` 2D CLIP feature inputs expected when `MODEL.use_2d_feats = true`;
- scan-level validation without train/validation leakage.

## Current State

Already staged:

```text
artifacts/layout/vlsat/generated/3DSSG_subset/relations.txt
artifacts/layout/vlsat/generated/3DSSG_subset/train_scans.txt
artifacts/layout/vlsat/generated/3DSSG_subset/validation_scans.txt
```

Latest checker result:

```text
status: blocked
remaining blockers: aligned PLY, multi_view
warnings: path convention mismatch, no downloaded validation payload, one local scan payload only
```

## Faithful Aligned PLY Route

Goal:

```text
Provide scan-level aligned instance PLY files compatible with VL-SAT dataset loading.
```

Target files:

```text
labels.instances.align.annotated.v2.ply
labels.instances.align.annotated.ply
```

Policy:

- prefer the exact file name used by `config/mmgnet.json`: `labels.instances.align.annotated.v2.ply`;
- if the official preprocessing script produces `labels.instances.align.annotated.ply`, use that only through an explicit config value accepted by `dataset_3dssg.py`;
- record the script, source files, output file name, and any config difference;
- do not silently rename or copy files without documenting whether the contents are identical.

Required source files per scan:

```text
labels.instances.annotated.v2.ply
semseg.v2.json
mesh.refined.0.010000.segs.v2.json
```

Expected implementation path:

1. Inspect `VL-SAT` / 3DSSG `data_processing/transform_ply.py`.
2. Patch only paths or wrappers, not geometry semantics.
3. Run on a small H001-Mini validation scan set.
4. Re-run `tools/check_layout.py`.
5. Treat aligned PLY as pass only when checker confirms the target file exists for every selected scan.

## Faithful Multi-View Route

Goal:

```text
Provide per-instance multi_view CLIP features expected by VL-SAT with use_2d_feats=true.
```

Target directory:

```text
<staged_3RScan_root>/<scan_id>/multi_view/
```

Expected feature files:

```text
instance_<instance_id>_class_<instance_name>_origin_view_mean.npy
```

Required source data per scan:

```text
sequence/_info.txt
sequence/frame-*.color.jpg
sequence/frame-*.pose.txt
labels.instances.annotated.v2.ply
```

`VL-SAT` source facts:

- `config/mmgnet.json` has `MODEL.use_2d_feats = true`;
- `data/pointcloud2image.py` uses CLIP `ViT-B/32`;
- `data/pointcloud2image.py` reads per-scan `sequence/` frames and poses;
- `dataset_3dssg.py` loads `multi_view/instance_*_origin_view_mean.npy`.

Expected implementation path:

1. Confirm which 3RScan download/preprocessing route provides `sequence/` frames and poses.
2. Patch `pointcloud2image.py` path handling through a wrapper or minimal local copy.
3. Generate `multi_view` for H001-Mini validation scans.
4. Keep `MODEL.use_2d_feats = true` for reportable baseline runs.
5. Re-run `tools/check_layout.py`.

## Validation Scan Requirement

The current local scan payload belongs to the official train split.

For reportable prediction-level validation, H001 needs downloaded scan payloads from the official `3DSSG_subset` validation split.

Minimum next dataset target:

```text
H001-Mini validation payload set
```

Selection policy:

- choose validation scans with support/contact, proximity, and vertical relation coverage;
- include enough support/contact edges to stress the H001 verifier;
- keep scan-level separation from calibration fitting data.

## Plumbing Route Boundary

The 3D-only plumbing route may be used only to test:

- prediction JSONL adapter fields;
- scan/object/relation identity preservation;
- geometry join code;
- evaluator input validation.

It must not be used for:

- main baseline comparison;
- recall retention claims;
- violation reduction claims;
- calibration claims;
- top-tier paper tables.

## Next

1. Use `22_prep.md` as the faithful layout prep staging policy.
2. Use `23_mini.md` as the selected H001-Mini validation scan set.
3. Implement staged-root prep for selected scans.
4. Generate aligned PLY and `multi_view`.
5. Keep calibration blocked until faithful prediction export and geometry join pass.
