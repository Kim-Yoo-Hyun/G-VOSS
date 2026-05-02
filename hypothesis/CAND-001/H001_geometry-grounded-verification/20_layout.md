# Layout

Last updated: 2026-05-03

## Role

This document records whether the local `3DSSG_subset` and 3RScan files are compatible with the expected `VL-SAT` baseline layout.

This is a compatibility check only. It does not run `VL-SAT`, does not create prediction artifacts, and does not modify `local_dataset/`.

## Source Check

Primary source:

- `VL-SAT` official repository: <https://github.com/wz7in/CVPR2023-VLSAT>
- local inspection checkout: `/tmp/CVPR2023-VLSAT`

Checked repository facts:

- `config/mmgnet.json` points `MODEL.obj_label_path` to `data/3DSSG_subset/classes.txt`.
- `config/mmgnet.json` points `MODEL.rel_label_path` to `data/3DSSG_subset/relations.txt`.
- `src/dataset/dataset_3dssg.py` reads `relationships.txt` inside the 3DSSG subset folder.
- `src/dataset/dataset_3dssg.py` reads `train_scans.txt` or `validation_scans.txt` for selected scans.
- `src/dataset/dataset_3dssg.py` uses `define.DATA_PATH` as the 3RScan root.
- The default config uses `label_file = labels.instances.align.annotated.v2.ply`.
- The dataset loader accepts `labels.instances.align.annotated.v2.ply` or `labels.instances.align.annotated.ply`.
- The default config has `MODEL.use_2d_feats = true`, which expects `multi_view` features.
- `data/pointcloud2image.py` reads `labels.instances.annotated.v2.ply` and writes per-scan `multi_view` features.

## Local Check

Local dataset root:

```text
/home/yoohyun/research/local_dataset
```

### Annotation Files

| Requirement | Local status | Note |
| --- | --- | --- |
| `local_dataset/3DSSG_subset/classes.txt` | pass | Object class names exist. |
| `local_dataset/3DSSG_subset/relationships.txt` | pass | Dataset loader relation names exist. |
| `local_dataset/3DSSG_subset/relations.txt` | missing | `VL-SAT` config expects this relation label path. |
| `local_dataset/3DSSG_subset/relationships.json` | pass | 1,335 entries, 1,335 unique scans. |
| `local_dataset/3DSSG_subset/relationships_train.json` | pass | 3,852 entries, 1,178 unique scans. |
| `local_dataset/3DSSG_subset/relationships_validation.json` | pass | 548 entries, 157 unique scans. |
| `local_dataset/3DSSG_subset/train_scans.txt` | missing | Required by `dataset_3dssg.py`. |
| `local_dataset/3DSSG_subset/validation_scans.txt` | missing | Required by `dataset_3dssg.py`. |

Inference:

- The annotation side is near-compatible.
- `relations.txt`, `train_scans.txt`, and `validation_scans.txt` can be generated from local official subset files, but the generation should be explicit and reproducible.
- `relations.txt` should initially mirror `relationships.txt` unless a later source check proves that `VL-SAT` expects a different relation-name ordering.

### 3RScan Files

Available local scan payload count:

```text
1 scan
```

Validated scan:

```text
f62fd5fd-9a3f-2f44-883a-1e5cf819608e
```

| Requirement | Local status | Note |
| --- | --- | --- |
| `local_dataset/3RScan/scans/<scan_id>/labels.instances.annotated.v2.ply` | pass | Present for the validated scan. |
| `local_dataset/3RScan/scans/<scan_id>/semseg.v2.json` | pass | Present for the validated scan. |
| `local_dataset/3RScan/scans/<scan_id>/mesh.refined.0.010000.segs.v2.json` | pass | Present for the validated scan. |
| `local_dataset/3RScan/scans/<scan_id>/labels.instances.align.annotated.v2.ply` | missing | Expected by the default `VL-SAT` config. |
| `local_dataset/3RScan/scans/<scan_id>/multi_view/` | missing | Required when `MODEL.use_2d_feats = true`. |
| `data/3RScan/<scan_id>/...` style root | missing | Local files are under `local_dataset/3RScan/scans/<scan_id>/`. |

Inference:

- The current one-scan H001 geometry verifier can use the local unaligned annotated PLY.
- A faithful `VL-SAT` eval path is not ready because aligned PLY files and `multi_view` features are missing.
- A small plumbing-only `VL-SAT` path may disable 2D features or patch the label file, but that must be reported as a deviation from the default baseline setup.

## Compatibility Verdict

The local dataset is not yet `VL-SAT`-ready.

Pass:

- official `3DSSG_subset` JSON annotations are present;
- object classes are present;
- relation names for the dataset loader are present;
- one sample 3RScan scan has the files needed for H001 geometry smoke tests.

Fail or pending:

- `relations.txt` is missing;
- `train_scans.txt` and `validation_scans.txt` are missing;
- `VL-SAT` root-path convention does not match the local `local_dataset/3RScan/scans/` convention;
- aligned PLY files are missing;
- `multi_view` features are missing;
- only one 3RScan scan payload is available, so multi-scan prediction-level evaluation is still blocked.

## Required Prep

Before full `VL-SAT` baseline reproduction:

1. Create a reproducible layout checker/prep script inside the H001 `tools/` folder.
2. Generate or stage `relations.txt` from `relationships.txt`.
3. Generate `train_scans.txt` and `validation_scans.txt` from the unique scan ids in `relationships_train.json` and `relationships_validation.json`.
4. Decide the 3RScan root-path strategy:
   - configure `define.DATA_PATH` to a staged local root; or
   - create an isolated symlink/copy layout outside `local_dataset` source files.
5. Decide the PLY route:
   - faithful route: generate aligned PLY files with the `VL-SAT` / 3DSSG preprocessing path; or
   - plumbing route: patch the config/loader to use `labels.instances.annotated.v2.ply` and mark it as non-faithful.
6. Decide the 2D feature route:
   - faithful route: generate `multi_view` features; or
   - 3D-only route: set `MODEL.use_2d_feats = false` only for plumbing/debugging and mark it as a baseline deviation.
7. Download the selected H001-Mini scan payloads before claiming multi-scan evidence.

## Decision

Do not start full baseline reproduction yet.

The H001-internal layout checker is implemented:

```text
tools/check_layout.py
tools/prep_layout.py
```

Latest output:

```text
artifacts/layout/vlsat/report.md
artifacts/layout/vlsat/summary.json
artifacts/layout/vlsat/prep_manifest.json
artifacts/layout/vlsat/generated_manifest.json
artifacts/layout/vlsat/generated/3DSSG_subset/
```

Latest checker result:

- status: `blocked`;
- default `VL-SAT` ready: `false`;
- H001 one-scan geometry-ready scan dirs: 1;
- generated annotation files staged: `relations.txt`, `train_scans.txt`, `validation_scans.txt`;
- remaining blockers: aligned PLY and `multi_view`;
- warnings: local 3RScan root convention mismatch, no downloaded validation split scan, and only one local scan payload.

`21_eval_path.md` decides the reportable path:

```text
faithful aligned PLY + faithful multi_view
```

Next implementation should write a layout prep policy that:

- does not silently mutate `local_dataset`;
- keeps any generated baseline-prep outputs separate from source dataset files.

## Next

1. Write the faithful layout prep staging policy.
2. Specify staged 3RScan root and config patch boundaries.
3. Keep calibration fitting blocked until prediction export and geometry join are validated.
