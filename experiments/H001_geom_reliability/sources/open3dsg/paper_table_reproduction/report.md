# Open3DSG CVPR 2024 Table-Reproduction Attempt

Created at: `2026-07-05T17:40:00+09:00`

## Target

Target paper table: CVPR 2024 Open3DSG Table 1, closed-vocabulary evaluation on
3DSSG.

Paper protocol from the paper text:

- dataset for quantitative evaluation: `3DSSG`
- object query set: 160 3DSSG object labels
- relationship label set: 27 3DSSG relationship labels
- metrics: top-k recall for objects, predicates, and subject-predicate-object
  relationship triplets
- compared paper row: `Open3DSG (Ours)`

Paper Table 1 values for `Open3DSG (Ours)`:

| metric | paper |
| --- | ---: |
| Object R@5 | 0.57 |
| Object R@10 | 0.68 |
| Predicate R@3 | 0.63 |
| Predicate R@5 | 0.70 |
| Relationship R@50 | 0.64 |
| Relationship R@100 | 0.66 |

## Local Checkpoint

Checkpoint:

`local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt`

Checkpoint provenance:

- trained locally through the Docker reproduction route because a trusted final
  official relation checkpoint was not available in the checked public release;
- selected by train-dev `val/loss=0.5724539160728455` at step 13103;
- checkpoint SHA256 recorded in `docs/reproducibility.md`.

Important split caveat:

- train preprocessing used 3744/3852 train subgraphs after filtering;
- validation preprocessing used 156/160 validation subgraphs after filtering;
- therefore this is not a strict full official 3DSSG/Open3DSG split
  reproduction.

## Official Eval Script Check

The public-source test path exposes an eval report template with:

- `Recall@1/5/10_object`
- `Recall@1/3/5_predicate`
- `Recall@1/50/100_relationship`
- object/predicate mRecall fields
- relationship mRecall fields present as placeholders set to `0`

The README test command is:

```bash
python open3dsg/script/run.py --test --dataset 3rscan --checkpoint [path to checkpoint] --n_beams 5 --weight_2d 0.5 --clip_model OpenSeg --node_model ViT-L/14@336px --blip
```

This route is the closest original-code output for Table 1-style metrics, but
the repository does not provide a one-command exact paper Table 1 reproduction
with a released final checkpoint.

## Runs

### Strict Public-Source Route

Status: `failed`

Exit file:

`logs/open3dsg_paper_table_repro_20260705_165539.exit`

Log:

`logs/open3dsg_paper_table_repro_20260705_165539.log`

Result:

- exit code: `1`
- failure point: first test batch in BLIP relationship generation
- error: `RuntimeError: mat1 and mat2 must have the same dtype, but got Float and BFloat16`

Conclusion: the strict public-source route did not produce a paper-table metric
report in the current Docker/runtime stack.

### Compatibility Route

Status: `completed`

This run used the H001 runtime Open3DSG source only for compatibility fixes
needed by the current environment. It did not enable GeoCalib reranking, H001
raw-dump export, H001 filtering at eval time, or H001 score patches.

Exit file:

`logs/open3dsg_paper_table_repro_compat_20260705_165823.exit`

Log:

`logs/open3dsg_paper_table_repro_compat_20260705_165823.log`

Metric file:

`local_dataset/Open3DSG_staged/training_repro/classwise_eval/open3dsg_paper_table_repro_compat_nonavg_20260705_165823_2026-07-05-08-32/eval_metrics.txt`

Run settings:

- dataset: `3rscan`
- checkpoint: local Docker-produced checkpoint above
- features: `clip_features_h001_official_blip_top5_scales3`
- `clip_model=OpenSeg`
- `node_model=ViT-L/14@336px`
- `blip=True`
- `avg_blip_emb=False`
- `weight_2d=0.5`
- `n_beams=5`
- `gt_objects=False`
- `workers=0`
- `use_rgb=False` in the test args, while the checkpoint params record
  `use_rgb=True`

## Compatibility-Run Result

| metric | paper Table 1 | local compatibility run | delta |
| --- | ---: | ---: | ---: |
| Object R@5 | 0.57 | 0.02120 | -0.54880 |
| Object R@10 | 0.68 | 0.04656 | -0.63344 |
| Predicate R@3 | 0.63 | 0.75523 | +0.12523 |
| Predicate R@5 | 0.70 | 0.76787 | +0.06787 |
| Relationship R@50 | 0.64 | 0.68041 | +0.04041 |
| Relationship R@100 | 0.66 | 0.68041 | +0.02041 |

Additional reported metrics:

| metric | local compatibility run |
| --- | ---: |
| Object R@1 | 0.00220 |
| Predicate R@1 | 0.68041 |
| Relationship R@1 | 0.68041 |
| Object mR@5 | 0.02372 |
| Object mR@10 | 0.03483 |
| Predicate mR@3 | 0.16873 |
| Predicate mR@5 | 0.24751 |

## Interpretation

This run is useful as an Open3DSG paper-style eval sanity check, but it is not a
strict reproduction of CVPR 2024 Open3DSG Table 1.

Reasons:

1. The strict public-source route fails in the current environment before
   producing metrics.
2. The completed route uses compatibility-patched runtime source.
3. The local checkpoint was trained on filtered train/dev preprocessing
   coverage, not the full official paper preprocessing route.
4. The test args record `use_rgb=False`, while the selected checkpoint was
   trained with `use_rgb=True`.
5. Object recall collapses relative to the paper row, while predicate and
   relationship recall are higher. This indicates a protocol/config mismatch
   rather than a faithful Table 1 reproduction.
6. In the eval implementation, `topk_relationship` uses `object_probs` for the
   triplet score but retrieves the GT subject/object category from
   `object_cat[edges]`; therefore relationship recall can be close to predicate
   recall even when object top-k recall is poor.

## Object-Metric Root Cause Review

The large object-metric deviation is not explained by a missing checkpoint or a
missing feature file. The strongest observed cause is an object-label namespace
mismatch in the local staged data/eval path.

Observed files:

- `3RScan/3DSSG_subset/classes.txt`: 160 3DSSG object labels used by
  `preprocess_3rscan.py` to create `objects_cat`.
- `3RScan/classes.txt`: 528 WordNet-style taxonomy rows used by
  `trainer.py` as `obj_class_dict` and by `eval.py` as `class_names`.

Code path:

- `preprocess_3rscan.py` reads `3DSSG_subset/classes.txt` and stores
  `objects_cat = word2idx[label]`.
- `trainer.py` reads `3RScan/classes.txt` as the object query list.
- `_predict_obj_from_clip()` ranks predictions over that query list.
- `eval.py` compares the predicted query-list indices directly against
  `objects_cat`.

This means the prediction index space and the GT index space are different.

Sanity check result:

- subset labels: 160
- full taxonomy rows: 528
- subset labels missing from the full taxonomy: 0
- subset labels at the same numeric index in the full taxonomy: 0/160

Examples:

| class | subset index | full-taxonomy index |
| --- | ---: | ---: |
| `armchair` | 0 | 3 |
| `chair` | 27 | 84 |
| `table` | 139 | 454 |
| `floor` | 57 | 187 |
| `wall` | 154 | 502 |

Therefore, if the model predicts the semantically correct full-taxonomy class
for `chair`, the eval still compares it against subset index 27, which points
to a different full-taxonomy label. This directly explains why Object R@5/R@10
can collapse to `0.02120/0.04656`.

The BLIP dtype failure is separate from this object-metric issue.

## Patched Public-Source Route

Status: `completed`

This run used the public Open3DSG source copy under the training-reproduction
workspace with minimal compatibility and label-namespace fixes:

- BLIP relationship image embeddings are cast to the BLIP parameter dtype before
  caption generation.
- BLIP generation uses `max_new_tokens=20` instead of the public-source
  `max_length/min_length` pair, which fails under the current Transformers
  runtime after the dtype issue is fixed.
- 3RScan object query/eval labels are aligned to
  `3DSSG_subset/classes.txt` so that predicted object indices are compared in
  the same 160-class namespace as `objects_cat`.

This run still does not enable GeoCalib reranking, H001 raw-dump export, or
H001 score patches.

Exit file:

`logs/open3dsg_table1_dtype_classfix_genfix_20260705_195158.exit`

Log:

`logs/open3dsg_table1_dtype_classfix_genfix_20260705_195158.log`

Metric file:

`local_dataset/Open3DSG_staged/training_repro/classwise_eval/open3dsg_table1_dtype_classfix_genfix_20260705_195158_2026-07-05-11-01/eval_metrics.txt`

Run settings:

- dataset: `3rscan`
- checkpoint: local Docker-produced checkpoint above
- features: `clip_features_h001_official_blip_top5_scales3`
- `clip_model=OpenSeg`
- `node_model=ViT-L/14@336px`
- `blip=True`
- `avg_blip_emb=False`
- `weight_2d=0.5`
- `n_beams=5`
- `gt_objects=False`
- `workers=0`
- `use_rgb=True`, matching the local checkpoint params

Patched public-source result:

| metric | paper Table 1 | patched public-source run | delta |
| --- | ---: | ---: | ---: |
| Object R@5 | 0.57 | 0.45856 | -0.11144 |
| Object R@10 | 0.68 | 0.56743 | -0.11257 |
| Predicate R@3 | 0.63 | 0.41744 | -0.21256 |
| Predicate R@5 | 0.70 | 0.44026 | -0.25974 |
| Relationship R@50 | 0.64 | 0.66823 | +0.02823 |
| Relationship R@100 | 0.66 | 0.72006 | +0.06006 |

Additional reported metrics:

| metric | patched public-source run |
| --- | ---: |
| Object R@1 | 0.25699 |
| Predicate R@1 | 0.38537 |
| Relationship R@1 | 0.00719 |
| Object mR@1 | 0.09734 |
| Object mR@5 | 0.24799 |
| Object mR@10 | 0.35794 |
| Predicate mR@1 | 0.10005 |
| Predicate mR@3 | 0.25304 |
| Predicate mR@5 | 0.36559 |

Object collapse check:

| metric | collapsed compatibility run | patched public-source run | change |
| --- | ---: | ---: | ---: |
| Object R@1 | 0.00220 | 0.25699 | +0.25479 |
| Object R@5 | 0.02120 | 0.45856 | +0.43736 |
| Object R@10 | 0.04656 | 0.56743 | +0.52087 |

Conclusion: the object metric collapse was caused primarily by the 528-class vs
160-class object-label namespace mismatch, not by missing data or a bad
checkpoint file. The patched route recovers object recall to a plausible range,
although it remains below the CVPR 2024 paper row because the local checkpoint,
preprocessing coverage, feature cache, and runtime are still not an exact
official reproduction.

## Strict-Route Dtype Failure Review

The strict public-source route failed because BLIP is loaded in `bfloat16`, while
the relationship image embeddings passed into BLIP caption generation are
`float32`.

Observed failing point:

- `sgpn.py::blip_predict_relationship()`
- `custom_instruct_blip.py::generate_caption()`
- Q-Former cross-attention linear layer
- error: `RuntimeError: mat1 and mat2 must have the same dtype, but got Float and BFloat16`

This is not a missing-file error. The model and checkpoint were found and the
test loop started. The crash happens during the first BLIP relationship
generation call.

The H001 runtime source avoids this by casting the relationship embeddings to
the BLIP parameter dtype before calling `generate_caption()`:

```python
if self.BLIP is not None:
    img_embeds = img_embeds.to(dtype=next(self.BLIP.parameters()).dtype)
```

A minimal strict-route compatibility fix would apply the same dtype cast to the
public-source `sgpn.py::blip_predict_relationship()`. This fixes the runtime
dtype mismatch, but in the current Transformers runtime a second BLIP generation
API fix is also required: replace the public-source `max_length/min_length`
caption-generation arguments with `max_new_tokens`. These BLIP fixes are
runtime compatibility fixes and are separate from the object-label namespace
fix above.

## Claim Boundary

Do not report this as reproduced Open3DSG Table 1 or as an Open3DSG leaderboard
comparison.

Allowed wording:

- "We attempted an Open3DSG CVPR 2024 Table 1-style evaluation using the
  Docker-trained local checkpoint."
- "The strict public-source route failed under the current runtime due to a
  BLIP dtype mismatch."
- "A compatibility-patched official-style eval completed, but the object metric
  deviation and split/config caveats prevent claiming strict paper
  reproduction."
- "After applying runtime BLIP compatibility fixes and aligning object labels to
  the 160-class 3DSSG subset, object recall no longer collapses, but the run is
  still not an exact Open3DSG Table 1 reproduction."

Not allowed:

- "Open3DSG Table 1 reproduced."
- "Our checkpoint matches/exceeds the CVPR 2024 Open3DSG paper."
- "Open3DSG official benchmark numbers are recovered."

## Next Action If Strict Reproduction Is Required

1. Restore an exact Open3DSG-compatible CUDA/PyTorch/Transformers stack matching
   the public repo expectation, or patch dtype handling while documenting that
   this is a runtime compatibility fix.
2. Recreate the unfiltered official preprocessing route, or record every
   missing/filtered subgraph as part of a non-strict reproduction.
3. Re-run eval with checkpoint-consistent settings, especially `use_rgb=True`
   if using the current local checkpoint.
4. For an exact Table 1 reproduction, recover the official checkpoint/runtime
   and verify whether the paper used the same BLIP generation settings, 3DSSG
   split coverage, and feature cache construction.

## Clean Baseline-Reproduction Route

Started at: `2026-07-05T21:38:04+09:00`

Purpose: reproduce the baseline paper as a baseline-reproduction task, separate
from the H001/GeoCalib claim and result route.

Prepared root:

`local_dataset/Open3DSG_staged/baseline_repro/`

Source:

- repo: `https://github.com/kochsebastian/Open3DSG.git`
- commit: `a568358d6bb718929aa9ff67b2dfdecc4a4c3261`
- local source: `local_dataset/Open3DSG_staged/baseline_repro/source/open3dsg_public`
- source modification so far: environment-driven `config.py` path patch only,
  needed to run the public source inside Docker without hard-coded local paths

Data staging:

| item | value |
| --- | ---: |
| train subgraphs | 3852 |
| train objects | 33153 |
| train relationships | 81190 |
| validation subgraphs | 160 |
| validation objects | 1395 |
| validation relationships | 3749 |

Label namespace:

- root `classes.txt` is aligned to `3DSSG_subset/classes.txt` for the
  paper-style 160-object query space;
- root `relationships.txt` is aligned to `3DSSG_subset/relationships.txt` for
  the paper-style 27-relation query space;
- this avoids the previously observed 528-class vs 160-class object-index
  mismatch while keeping the route separate from H001 runtime outputs.

Legacy Docker:

- added `configs/open3dsg/Dockerfile.legacy`
- target stack: CUDA 11.8, Python 3.9, PyTorch 2.0.1+cu118,
  Transformers 4.31.0, matching the public README more closely than the modern
  cu128 runtime
- build/env-check job launched in tmux:
  `open3dsg_legacy_build_20260705_213816`
- log: `logs/open3dsg_legacy_build_env_20260705_213816.log`
- exit file: `logs/open3dsg_legacy_build_env_20260705_213816.exit`

Expected risk:

- the local GPU is an RTX 5090. If PyTorch 2.0.1+cu118 cannot execute CUDA
  kernels on this GPU, the legacy route is a hardware/runtime blocker rather
  than an Open3DSG scientific failure.
- if legacy CUDA fails, the next defensible route is a two-track report:
  legacy stack build/config result plus a modern-CUDA execution route with
  explicitly documented runtime compatibility patches.
