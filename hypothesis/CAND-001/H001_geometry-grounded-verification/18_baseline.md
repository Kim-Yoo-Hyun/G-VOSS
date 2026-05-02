# Baseline

Last updated: 2026-05-03

## Role

This document records the first prediction-level baseline choice for H001.

The decision fixes the baseline source before implementing:

```text
prediction JSONL schema
baseline output adapter
semantic_only vs rule_verified evaluation
calibration table export
```

## Decision

Use `VL-SAT` as the first prediction-level learned baseline.

Baseline id:

```text
vlsat_closed_set
```

Role:

```text
closed-set semantic-assisted 3DSSG relation prediction baseline
```

Use `SGGpoint` as an edge-reasoning paper/reference baseline, not as the first reproduction target.

Use `Open3DSG` as the later open-vocabulary proposal baseline after the H001 prediction artifact contract is stable.

Keep `CCL-3DSGG` as paper-level open-vocabulary/zero-shot evidence unless official code or prediction outputs become available.

## Source Check

Checked on 2026-05-01.

Primary sources:

- `VL-SAT` official repository: <https://github.com/wz7in/CVPR2023-VLSAT>
- `SGGpoint` official repository: <https://github.com/chaoyivision/SGGpoint>
- `Open3DSG` official repository: <https://github.com/boschresearch/Open3DSG>
- `CCL-3DSGG` CVF paper page: <https://openaccess.thecvf.com/content/CVPR2024/html/Chen_CLIP-Driven_Open-Vocabulary_3D_Scene_Graph_Generation_via_Cross-Modality_Contrastive_Learning_CVPR_2024_paper.html>

Local evidence:

- `literature/CAND-001.md`
- `literature/2023_cvpr_vl-sat/`
- `literature/2021_cvpr_sggpoint/`
- `literature/2024_cvpr_open3dsg/`
- `literature/2024_cvpr_ccl-3dsgg/`
- `16_evaluation.md`
- `17_subset.md`

## Selection Criteria

The first baseline should maximize prediction-level H001 signal while minimizing reproduction risk.

Criteria:

1. can run on or adapt to 3DSSG / 3RScan;
2. can produce relation predicate scores and ranks;
3. uses or can be aligned to official `3DSSG_subset`;
4. does not require open-vocabulary system engineering before the verifier is evaluated;
5. supports standard recall-style metrics so H001 can report recall retention, not only violation reduction.

## Candidate Comparison

| Candidate | Fit | Burden | Decision |
| --- | --- | --- | --- |
| `VL-SAT` | Direct 3DSSG relation prediction; semantic-assisted closed-set baseline; official repo includes train/eval path and 3DSSG-sub layout guidance. | Medium: old Python/PyTorch/PyG/CUDA stack, multi-view generation, CLIP adapter/checkpoint handling. | First prediction baseline. |
| `SGGpoint` | Strong edge-reasoning precedent; useful for latent edge feature vs explicit edge evidence argument. | Medium-high for first run: official repo centers on cleaned `3DSSG-O27R16` and FullScenes preprocessing, less direct for official subset subgraph evaluation. | Paper/reference baseline first. |
| `Open3DSG` | Best later open-vocabulary relation proposal baseline. | High: broader ScanNet/3RScan/3DSSG setup, OpenSeg/BLIP/PointNet dependencies, large 2D feature burden. | Later Stage S3 candidate. |
| `CCL-3DSGG` | Strong open-vocabulary/zero-shot paper baseline. | Low practical reproducibility now: no official code path confirmed in this pass. | Paper-level evidence only. |
| `SMKA` | Strong spatial-knowledge closed-set warning baseline. | Code path not fixed in current H001 workflow. | Positioning/reference baseline. |

## Why VL-SAT First

Facts:

- `VL-SAT` directly targets 3DSSG relation prediction from point clouds.
- Its public repository exposes dependencies, data preparation notes, default config, checkpoint link, and train/eval commands.
- It expects `3DSSG_subset`-style resources and 3RScan payloads, which now match the local dataset direction.

Inference:

- `VL-SAT` is the smallest credible step from H001 one-scan verifier artifacts to prediction-level model outputs.
- It is semantically stronger than a pure geometry/edge baseline, so geometry verification has a meaningful target: semantic relation predictions that may still violate 3D evidence.
- It keeps the first run closed-set, which avoids conflating H001's verifier contribution with open-vocabulary parsing and mapping failures.

## Expected Prediction Adapter

The next H001 implementation document should define a baseline-neutral JSONL schema, but the first adapter should target `VL-SAT`.

Required output fields:

```text
scan_id
split_id
subject_id
object_id
subject_label
object_label
predicate_label
predicate_score
rank
baseline_name
subset_source
object_source
predicate_vocab
```

Adapter policy:

- preserve raw `VL-SAT` predicate scores where available;
- emit predictions per official `3DSSG_subset` subgraph entry;
- if the baseline outputs scan-level object-pair predictions, filter or group them by `(scan_id, split_id)` using the subgraph object ids;
- preserve the original rank before applying H001 geometry verification;
- do not overwrite semantic scores with geometry scores.

Naming note:

- Local file: `local_dataset/3DSSG_subset/relationships.txt`
- `VL-SAT` README examples may refer to `relations.txt`
- The adapter/setup checklist should verify whether a copy or symlink is needed before running baseline code.

## First Evaluation Scope

Initial prediction-level comparison:

```text
semantic_only vs rule_verified
```

Default geometry policy:

```text
filter_safe
```

Predicate scope:

```text
support_contact
proximity
relative_vertical
```

Deferred:

```text
probabilistic_recalibrated
relative_horizontal
open-vocabulary relation proposal evaluation
```

## Risks

- The `VL-SAT` environment may require older CUDA/PyTorch/PyG versions.
- Multi-view image generation can become a preprocessing time sink.
- Existing local payloads include only one 3RScan scan, so multi-scan prediction evaluation still requires additional scan payloads.
- If `VL-SAT` output does not expose usable per-edge predicate scores, the adapter may need to hook into eval-time logits rather than final printed metrics.

## Fallbacks

If `VL-SAT` cannot produce prediction JSONL within reasonable setup effort:

1. use the `VL-SAT` repository's SGGpoint/SGFN-style closed-set components if they expose easier prediction dumps;
2. run a small controlled prediction surrogate only for schema/verifier plumbing, but do not report it as a baseline result;
3. move `Open3DSG` to the next feasibility target only after the prediction schema is stable.

## Next

1. Use `19_schema.md` as the prediction JSONL schema and adapter contract for `vlsat_closed_set`.
2. Use `20_layout.md` as the local `3DSSG_subset` / 3RScan layout compatibility result.
3. Use `artifacts/layout/vlsat/report.md` as the latest checker output.
4. Use `21_eval_path.md` as the faithful eval path decision.
5. Write the faithful layout prep staging policy.
6. Do not start full training or broad experiment infrastructure until the local layout prep and minimal eval path are fixed.
