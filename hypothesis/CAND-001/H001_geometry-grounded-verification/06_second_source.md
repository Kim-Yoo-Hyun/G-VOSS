# Second Source

Last updated: 2026-05-07

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
VL-SAT-centered only
```

Selected top-tier expansion:

```text
Open3DSG second-source adapter result from a Docker-reproduced checkpoint
```

Blocked claims:

- baseline-agnostic 3DSSG reliability-layer claim;
- broad open-vocabulary 3DSSG improvement claim.

Remaining blockers:

- `second_source_metric_missing_for_baseline_agnostic_claim`
- `open_vocab_adapter_metric_missing_for_broad_open_vocabulary_claim`

## Baseline Matrix Decision

Fact:

- No clean immediate second closed-set baseline is locally ready.
- `SGGpoint`, `SMKA`, and `CCL-3DSGG` are not currently suitable as fast
  executable second baselines for this H001 stage.
- `FROSS` and `Open3DSG` remain conditional proposal-source tracks.

Inference:

- A second source is not required before entering the first scoped
  `VL-SAT`-centered experiment phase.
- A second source is required before claiming baseline-agnostic transfer.
- For a top-tier main paper target, second-source adapter evidence is preferred
  over relying only on a single-baseline reliability-layer justification.

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

Source-contract status:

```text
source_contract_ready_runtime_blocked
```

Coverage:

| Family | Source-level coverage |
| --- | --- |
| `support_contact` | ready |
| `proximity` | ready |
| `relative_vertical` | ready |

Adapter status:

```text
adapter_feasibility_ready_runtime_blocked
```

Adapter facts:

- generated `dump_patch.diff` applies cleanly to `/tmp/open3dsg_source`;
- raw schema and H001 adapter mapping are fixed;
- no Open3DSG metric claim exists yet.

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
| trained Open3DSG checkpoint | missing |

Training route preflight:

```text
training_route_not_immediate
```

Reason:

- staged train subgraphs are not ready;
- full-train views/preprocessed pickles/scan dirs are incomplete;
- local environment lacks required dependencies;
- local compute is below the official README example.

Superseded decision:

```text
The earlier checkpoint-waiting branch is superseded because the top-tier target
now justifies a Dockerized Open3DSG reproduction budget.
```

Updated direction:

```text
Generate the Open3DSG checkpoint ourselves through a Dockerized reproduction
track, then use the trained checkpoint for identity-preserving raw dump,
prediction JSONL export, geometry join, and second-source metric evaluation.
```

Rationale:

- second-source evidence is the stronger path for a top-tier target than
  defending H001 as a single-baseline reliability layer;
- Open3DSG covers all H001 target families at source-contract level;
- generating the checkpoint ourselves avoids relying on an unavailable official
  trained checkpoint;
- the checkpoint reproduction must be treated as paper experiment work and
  therefore must be Docker-based, with mounted dataset/cache roots and recorded
  commands.

Single-baseline fallback:

```text
Keep the VL-SAT-only reliability-layer claim as fallback if Dockerized
Open3DSG checkpoint reproduction is infeasible within the research budget.
```

## Next Source Conditions

Start second-source metric work only if one of these becomes true:

- user chooses baseline-agnostic or stronger top-tier claim before final paper
  framing;
- Dockerized Open3DSG checkpoint reproduction is started;
- a trusted external Open3DSG checkpoint is supplied;
- FROSS-compatible prediction pickle or staged root is supplied;
- a new identity-preserving proposal source becomes locally executable.

Acceptance for second-source evidence:

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
Upgrade the claim from VL-SAT-centered to cross-predictor reliability-layer
only if the Open3DSG metric result is valid.
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
