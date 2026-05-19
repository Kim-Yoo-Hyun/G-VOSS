# Second Source

Last updated: 2026-05-19

## Role

This document merges second-baseline feasibility and proposal-source expansion
decisions.

Merged former files:

- `14_baseline.md`
- `16_fross.md`
- `17_fross_runtime.md`
- `18_open3dsg.md`
- `19_open3dsg_adapter.md`
- `20_open3dsg_runtime.md`

## Claim Boundary

Current executable evidence:

```text
VL-SAT and Docker-reproduced Open3DSG within measured H001 families
```

Selected top-tier expansion:

```text
Open3DSG second-source adapter result from a Docker-reproduced checkpoint
```

Blocked claims:

- arbitrary-baseline 3DSSG reliability-layer claim beyond measured `VL-SAT` and Open3DSG sources;
- broad open-vocabulary 3DSSG improvement claim.

Remaining blockers:

- `open_vocab_adapter_metric_missing_for_broad_open_vocabulary_claim`

## Baseline Matrix Decision

Fact:

- No clean immediate second closed-set baseline is locally ready.
- `SGGpoint`, `SMKA`, and `CCL-3DSGG` are not currently suitable as fast
  executable second baselines for this H001 stage.
- `FROSS` and `Open3DSG` remain conditional proposal-source tracks.

Inference:

- A second source is now available for measured H001-family reliability claims.
- The remaining question is not whether Open3DSG evidence exists, but how
  tightly to word the claim around denominator, averaged-BLIP, covered-scope,
  and `validation_missing_preprocessed:11` caveats.
- Open3DSG satisfies the second-source requirement for a measured cross-source
  H001-family claim, but not for arbitrary-baseline transfer.
- For a top-tier main paper target, keep using second-source evidence instead
  of reverting to single-baseline-only justification.

## FROSS Track

Source status:

| Item | Value |
| --- | --- |
| inspected revision | `645153bf2b4b54ffd3d214ee4b8fdd2539b1bf55` |
| source contract | ready |
| object matching route | GT-object overlap matching |
| supported H001 scope | support/contact-only transfer smoke |

Runtime status:

```text
blocked_runtime_artifact
```

Missing local runtime artifacts:

- FROSS prediction pickle;
- FROSS staged root;
- rendered depth;
- `2DSG20`;
- mapping files.

Family coverage limitation:

```text
FROSS does not cover H001 proximity / relative_vertical families by default.
```

Use:

- possible future support/contact second-source smoke;
- not full-family evidence;
- not broad open-vocabulary evidence.

## Open3DSG Track

Current status:

```text
second_source_metrics_ready_with_provenance_caveats
```

Coverage:

| Family | Source-level coverage |
| --- | --- |
| `support_contact` | ready |
| `proximity` | ready |
| `relative_vertical` | ready |

Adapter / metric status:

```text
adapter_geometry_metrics_failure_rows_ready
```

Adapter facts:

- selected checkpoint: `epoch=13-step=13104.ckpt`, chosen by train-dev
  `val/loss` before H001 held-out inspection;
- raw dump: `raw_dump/raw.jsonl`, 19,162 rows, identity-audited;
- adapter export: 496,600 prediction rows, with 62 raw rows filtered outside
  fixed H001 object context;
- geometry join: 496,600/496,600 rows preserved, 114,600 geometry-checkable
  rows scored;
- metric eval: ready, Table 6 ready;
- real failure rows: 57,736 rows, 0 validation errors, 6,162 visual-audit queue
  rows, 36 qualitative case candidates, deterministic qualitative inspection
  with residual calibration-risk cases, and frozen paper caveat wording.

Runtime readiness:

| Artifact | Status |
| --- | --- |
| H001 validation/test staged metadata/root | ready |
| selected scan symlinks | 127 / 127 |
| mesh/texture | 127 / 127 |
| view pickles | 127 / 127 |
| source-visible preprocessed pickles | 377 / 388 |
| unique ready scans for preprocess | 126 / 127 |
| BLIP2 positional embedding | ready |
| OpenSeg SavedModel | ready |
| PointNet weights | ready |
| PointNet2 weights | ready |
| official BLIP TopK5/scales3 feature dump | 3900 / 3900 complete |
| H001 held-out eval feature cache | 377 / 377 covered loadable ids |
| trained Open3DSG checkpoint | ready, averaged-BLIP variant |

Current limitations:

```text
filtered_train_split; averaged_blip_variant; covered_loadable_scope; validation_missing_preprocessed_11
```

Frozen caveat wording:

```text
open3dsg_paper_caveats_ready
```

Superseded decision:

```text
The earlier checkpoint-waiting branch is superseded because the top-tier target
justified a Dockerized Open3DSG reproduction budget. That reproduction has now
produced the avg-BLIP checkpoint and H001 metrics.
```

Current direction:

```text
Use the Docker-reproduced Open3DSG outputs as measured H001-family second-source
evidence. Clean v14 streaming raw-dump provenance, qualitative case inspection,
and frozen paper caveat wording are available; earlier exit-137 attempts remain
historical run records.
```

Rationale:

- second-source evidence is stronger than defending H001 as a single-baseline
  reliability layer;
- Open3DSG covers all H001 target families at source-contract level;
- generating the checkpoint ourselves avoids relying on an unavailable official
  trained checkpoint;
- all paper-facing experiment work remains Docker-based, with mounted
  dataset/cache roots and recorded commands.

Single-baseline fallback:

```text
Keep the VL-SAT-only reliability-layer claim as fallback if Dockerized
Open3DSG checkpoint reproduction is infeasible within the research budget.
```

## Next Source Conditions

Open3DSG second-source metric work has completed for measured H001 families.
Start additional source work only if one of these becomes true:

- the paper claim expands beyond measured `VL-SAT` + Open3DSG H001-family
  reliability;
- Qwen-VL is promoted from optional runtime smoke to a metric-bearing modern
  semantic-source extension;
- FROSS-compatible prediction pickle or staged root is supplied;
- a new identity-preserving proposal source becomes locally executable.

Acceptance for any additional second-source evidence:

- object-pair identity preserved;
- prediction JSONL export exists;
- geometry join succeeds;
- at least one metric run exists;
- family coverage is explicitly stated;
- no broad claim is made beyond measured families/source.

## Selected Expansion Sequence

E1:

```text
Dockerize and reproduce the locked VL-SAT table/report path.
```

E2:

```text
Create a Dockerized Open3DSG checkpoint reproduction plan with fixed train/test
splits, staged data roots, dependency pins, cache mounts, and failure budget.
```

E3:

```text
Train or reproduce the Open3DSG checkpoint without touching held-out H001
validation metrics.
```

E4:

```text
Run Open3DSG identity-preserving raw dump, H001 prediction JSONL export,
geometry join, and the same H001 metric suite.
```

E5:

```text
Use the completed Open3DSG metric result to support a measured cross-source
reliability-layer claim, but do not broaden it to arbitrary baselines or broad
open-vocabulary 3DSSG generation.
```

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| FROSS runtime check | `artifacts/evaluation/fross_scannet20/runtime/manifest.json` |
| Open3DSG source contract | `artifacts/evaluation/open3dsg_ov/source_contract/manifest.json` |
| Open3DSG adapter prep | `artifacts/evaluation/open3dsg_ov/adapter/manifest.json` |
| Open3DSG runtime plan | `artifacts/evaluation/open3dsg_ov/runtime_plan/manifest.json` |
| Open3DSG staged root | `artifacts/evaluation/open3dsg_ov/staged_root/manifest.json` |
| Open3DSG mesh/texture | `artifacts/evaluation/open3dsg_ov/mesh_texture/manifest.json` |
| Open3DSG views | `artifacts/evaluation/open3dsg_ov/views/manifest.json` |
| Open3DSG preprocess | `artifacts/evaluation/open3dsg_ov/preprocess/manifest.json` |
| Open3DSG model audit | `artifacts/evaluation/open3dsg_ov/model_artifacts/manifest.json` |
| Open3DSG training preflight | `artifacts/evaluation/open3dsg_ov/training_route/manifest.json` |
