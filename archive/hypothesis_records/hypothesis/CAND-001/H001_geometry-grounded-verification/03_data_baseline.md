# Data And Baseline

Last updated: 2026-05-19

## Role

This document merges the `VL-SAT` layout, faithful staging, hardened validation
scope, and payload-readiness records.

Merged former files:

- `05_vlsat_prep.md`
- `09_scope.md`
- `10_payload.md`

## Dataset And Split

Primary benchmark path:

```text
3DSSG_subset / 3RScan
```

Local dataset facts:

- `local_dataset/3DSSG` contains full annotation files.
- `local_dataset/3DSSG_subset` contains official train/validation files.
- `local_dataset/3RScan/files` contains metadata and split files.
- 3RScan scan payloads are staged under `local_dataset/3RScan/scans/`.

Split policy:

- use official `3DSSG_subset` as the primary split and relation-subgraph source;
- exclude H001-Mini reference/rescan groups from hardened validation;
- keep calibration train/dev separate from held-out validation;
- do not retune scan selection after prediction failures.

## Baseline

First learned prediction source:

```text
VL-SAT / vlsat_closed_set
```

Reason:

- public checkpoint and local reproduction path were available;
- object-pair identity could be preserved through a raw score dump;
- output could be adapted to H001 prediction JSONL;
- it supports the first scoped reliability-layer claim.

Claim boundary:

```text
VL-SAT is the primary locked source. Open3DSG now provides measured second-source
evidence for H001 families, but broad open-vocabulary 3DSSG generation claims
remain out of scope.
```

## Staged Runtime Roots

H001-Mini staged root:

```text
local_dataset/VLSAT_staged/CVPR2023-VLSAT/
```

Hardened staged root:

```text
local_dataset/VLSAT_staged/h001_validation_hardened/CVPR2023-VLSAT/
```

Policy:

- do not mutate source dataset files;
- generate baseline-compatible files under staged roots;
- keep large runtime files in ignored local dataset roots;
- keep compact manifests/reports under hypothesis artifacts.

## H001-Mini Setup

H001-Mini role:

```text
smoke/pilot only, not final evidence
```

Facts:

| Item | Count / Status |
| --- | ---: |
| selected validation scans | 8 |
| subgraphs | 56 |
| selected scan payloads | 8 / 8 |
| `sequence.zip` integrity | 8 / 8 |
| aligned PLY | 8 / 8 |
| `multi_view` generation | 8 / 8 |
| staged checker | `ready` |

## Hardened Validation Scope

Fixed scope:

| Item | Count |
| --- | ---: |
| selected scans | 127 |
| subgraphs | 388 |
| relations | 7,505 |
| scan symlinks | 127 |

Selection:

```text
official validation minus H001-Mini reference/rescan groups
```

Scope artifact:

```text
artifacts/subset/h001_validation_hardened/
```

## Hardened Payload Readiness

Hardened payload facts:

| Item | Count / Status |
| --- | ---: |
| source payload scans | 127 / 127 |
| `sequence.zip` | 127 / 127 |
| `sequence.zip` integrity | 127 / 127 |
| sequence extraction/staging | 127 / 127 |
| aligned PLY | 127 / 127 |
| `multi_view` generation | 127 / 127 |
| generated instances | 3,089 |
| generated `.npy` files | 6,178 |
| staged checker | `ready` |
| blockers/warnings | 0 |

Hardened layout artifacts:

```text
artifacts/layout/vlsat/hardened/
```

## Fixed Inputs For Experiment Spec

The scoped experiment spec uses:

| Item | Count |
| --- | ---: |
| held-out scans | 127 |
| subgraphs | 388 |
| prediction rows | 673,816 |
| ground-truth rows | 7,505 |
| in-scope prediction rows | 155,496 |
| in-scope GT denominator | 2,545 |

These counts are acceptance checks for experiment entry.
