# Prep

Last updated: 2026-05-03

This document fixes the faithful `VL-SAT` layout prep policy for H001.

It does not run `VL-SAT`, does not create prediction artifacts, and does not start full baseline reproduction.

## Purpose

H001 needs prediction-level outputs from a learned 3DSSG baseline before rule/probabilistic geometry verification can be evaluated beyond one-scan smoke tests.

The first learned baseline is:

```text
VL-SAT / vlsat_closed_set
```

`20_layout.md` showed that local annotations are partially compatible with `VL-SAT`, but the default layout remains blocked by missing aligned PLY and `multi_view` features.

`21_eval_path.md` decided that reportable results must use:

```text
faithful aligned PLY + faithful multi_view
```

This document defines how to prepare those files without silently mutating source dataset files.

## Decision

Use a staged runtime root for baseline preparation.

Keep source data under:

```text
/home/yoohyun/research/local_dataset
```

Keep large generated/runtime files under:

```text
/home/yoohyun/research/local_dataset/VLSAT_staged
```

Keep small generated annotation files under tracked H001 artifacts:

```text
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/layout/vlsat/generated/3DSSG_subset
```

Rationale:

- `local_dataset/` is ignored by git and can hold large scan/runtime files.
- H001 artifacts can track small, reproducible annotation staging outputs.
- Source dataset files stay distinguishable from generated baseline-prep files.
- A faithful baseline route can be defended because the remaining changes are path/config staging, not semantic baseline changes.

## Staged Roots

Use these roots when implementing the prep script:

| Role | Path |
| --- | --- |
| source dataset root | `/home/yoohyun/research/local_dataset` |
| runtime staged root | `/home/yoohyun/research/local_dataset/VLSAT_staged` |
| staged VL-SAT root | `/home/yoohyun/research/local_dataset/VLSAT_staged/CVPR2023-VLSAT` |
| staged 3RScan root | `/home/yoohyun/research/local_dataset/VLSAT_staged/CVPR2023-VLSAT/data/3RScan` |
| staged 3DSSG subset root | `/home/yoohyun/research/local_dataset/VLSAT_staged/CVPR2023-VLSAT/data/3DSSG_subset` |
| staged file root | `/home/yoohyun/research/local_dataset/VLSAT_staged/CVPR2023-VLSAT/files` |
| tracked generated subset source | `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/layout/vlsat/generated/3DSSG_subset` |

Expected staged layout:

```text
local_dataset/VLSAT_staged/CVPR2023-VLSAT/
  data/3DSSG_subset/
    classes.txt
    relationships.txt
    relations.txt
    relationships_train.json
    relationships_validation.json
    train_scans.txt
    validation_scans.txt
  data/3RScan/<scan_id>/
    labels.instances.annotated.v2.ply
    labels.instances.align.annotated.v2.ply
    semseg.v2.json
    mesh.refined.0.010000.segs.v2.json
    sequence/
    multi_view/
  files/
    3RScan.json
    references.txt
    rescans.txt
```

## Annotation Policy

Use `tools/prep_layout.py` as the canonical generator for small `3DSSG_subset` annotation files:

```text
relations.txt
train_scans.txt
validation_scans.txt
```

These files are tracked under H001 artifacts.

The staged runtime root should copy or symlink from the tracked generated subset root into:

```text
local_dataset/VLSAT_staged/CVPR2023-VLSAT/data/3DSSG_subset/
```

The reportable route must preserve:

- official `relationships_train.json`;
- official `relationships_validation.json`;
- official `classes.txt`;
- official `relationships.txt`;
- generated `relations.txt` that mirrors the official relation-name order;
- generated scan lists derived from official subset JSON scan ids.

Do not reorder relation labels for convenience.

## Reference And Rescan Lists

`VL-SAT` / 3DSSG `transform_ply.py` expects:

```text
files/3RScan.json
files/references.txt
files/rescans.txt
```

Current local files include `3RScan.json`, but not `references.txt` or `rescans.txt`.

Generate the missing lists in the staged `files/` root from `3RScan.json`:

- `references.txt`: one scene-level `reference` scan id per scene;
- `rescans.txt`: scan ids listed under each scene's `scans` entries, excluding the scene reference when duplicated.

Record the generated list counts and source hash in a manifest.

For the current sample scan:

```text
f62fd5fd-9a3f-2f44-883a-1e5cf819608e
```

local `3RScan.json` identifies it as a reference scan. Therefore the official `transform_ply.py` reference branch should copy raw annotated PLY to aligned annotated PLY for this scan. This is acceptable because it is the official preprocessing behavior for reference scans, not an H001 shortcut.

## Aligned PLY Route

Use the official transform path.

Configure `VL-SAT` `utils/define.py` in the staged code copy or wrapper environment:

```text
ROOT_PATH = /home/yoohyun/research/local_dataset/VLSAT_staged/CVPR2023-VLSAT/
DATA_PATH = /home/yoohyun/research/local_dataset/VLSAT_staged/CVPR2023-VLSAT/data/3RScan/
FILE_PATH = /home/yoohyun/research/local_dataset/VLSAT_staged/CVPR2023-VLSAT/files/
LABEL_FILE_NAME_RAW = labels.instances.annotated.v2.ply
LABEL_FILE_NAME = labels.instances.align.annotated.v2.ply
```

Expected output per selected scan:

```text
data/3RScan/<scan_id>/labels.instances.align.annotated.v2.ply
```

Allowed:

- running official `data_processing/transform_ply.py`;
- using official reference-scan copy behavior;
- writing outputs only under the staged runtime root.

Not allowed for reportable results:

- renaming unaligned PLY as aligned PLY without the official transform path;
- changing loader expectations to consume unaligned PLY as the main result;
- mixing source scan folders and staged scan folders without a manifest.

## Multi-View Route

Keep `MODEL.use_2d_feats = true` for reportable `VL-SAT` results.

`VL-SAT` expects per-instance CLIP feature files:

```text
data/3RScan/<scan_id>/multi_view/instance_<instance_id>_class_<instance_name>_origin_view_mean.npy
```

Required source data per selected scan:

```text
sequence/_info.txt
sequence/frame-*.color.jpg
sequence/frame-*.pose.txt
labels.instances.annotated.v2.ply
```

The local 3RScan download script lists `sequence.zip` as a valid file type. For a selected scan, the expected download command is:

```text
python local_dataset/3RScan/download_3rscan.py -o local_dataset/3RScan/scans --id <scan_id> --type sequence.zip
```

Then unzip into the selected scan's `sequence/` directory before staging.

Implementation policy:

- use `pointcloud2image.py` or a minimal path-wrapper copy to generate `multi_view`;
- patch hard-coded paths only through a documented wrapper or staged copy;
- keep CLIP model choice as `ViT-B/32` unless environment constraints force a recorded non-semantic device patch;
- if CUDA is unavailable and CPU execution is required, record it as an environment patch, not a baseline semantics change.

Not allowed for reportable results:

- setting `MODEL.use_2d_feats = false`;
- fabricating zero `multi_view` features;
- using stale features from a different scan or instance id;
- changing object/relation vocabulary order to make feature loading easier.

## Config Boundary

Allowed path-only changes:

- `utils/define.py`: `ROOT_PATH`, `DATA_PATH`, `FILE_PATH`;
- `config/mmgnet.json`: `multi_view_root`;
- `config/mmgnet.json`: `MODEL.obj_label_path`;
- `config/mmgnet.json`: `MODEL.rel_label_path`;
- `config/mmgnet.json`: `dataset.root`;
- `config/mmgnet.json`: `dataset.label_file`, only to match the faithful aligned PLY filename;
- hard-coded paths in `pointcloud2image.py` through a wrapper or staged copy.

Not allowed for reportable results:

- disabling 2D features;
- changing predicate vocabulary;
- changing raw relation score semantics;
- changing edge sampling or predicate decoding to favor H001;
- evaluating on train scans as validation results.

## H001-Mini Requirement

The currently downloaded sample scan is useful for H001 one-scan geometry smoke tests, but it is not enough for prediction-level validation.

Next dataset target:

```text
H001-Mini validation payload set
```

Selection policy:

- choose scans from official `3DSSG_subset` validation split;
- prioritize support/contact coverage;
- include proximity and vertical relations when available;
- avoid selecting scans after inspecting model prediction failures;
- keep selected validation scans separate from calibration fitting data.

Needed payloads per selected scan:

```text
labels.instances.annotated.v2.ply
semseg.v2.json
mesh.refined.0.010000.segs.v2.json
sequence.zip
```

## Completion Criteria

The layout prep gate is passed when:

- staged `3DSSG_subset` files exist under the runtime root;
- staged `files/3RScan.json`, `references.txt`, and `rescans.txt` exist;
- selected H001-Mini validation scans have `labels.instances.align.annotated.v2.ply`;
- selected H001-Mini validation scans have `multi_view/*.npy` files;
- `tools/check_layout.py` reports no default-layout blockers for selected scans;
- a manifest records source paths, generated paths, and known path-only config patches.

This still does not prove H001. It only makes faithful `VL-SAT` prediction export possible.

## Next

1. Use `23_mini.md` as the selected H001-Mini validation scan set.
2. Implement a staged-root prep script for annotations, scan files, `references.txt`, and `rescans.txt`.
3. Download or stage required payloads for selected validation scans.
4. Generate aligned PLY for selected validation scans.
5. Generate `multi_view` features for selected validation scans.
6. Re-run `tools/check_layout.py` against the staged root.
7. Keep calibration blocked until faithful prediction export and geometry join pass.
