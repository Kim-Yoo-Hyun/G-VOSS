# Open3DSG Training Repro Staged Root

Date: `2026-05-07`
Status: `training_repro_staged_root_ready_for_view_preprocess`
Staged root: `local_dataset/Open3DSG_staged/training_repro`

## Split

- Official train: 1178 scans, 3852 subgraphs, 81190 relations.
- Train-dev without H001 held-out: 30 scans, 160 subgraphs, 3749 relations.
- H001 held-out scan overlap in train: 0.
- H001 held-out scan overlap in train-dev: 0.

## Payload Readiness

- Train scan dirs ready: 1178 / 1178.
- Train-dev scan dirs ready: 30 / 30.
- Train views ready: 0 / 1178.
- Train preprocessed ready: 0 / 3852.

## Train Open3DSG Files

| File | Ready |
| --- | ---: |
| `mesh.refined.v2.obj` | 1178/1178 |
| `mesh.refined.mtl` | 1178/1178 |
| `mesh.refined_0.png` | 1178/1178 |

## Train Sequence Files

| File | Ready |
| --- | ---: |
| `sequence/_info.txt` | 1178/1178 |
| `sequence/frame-000000.color.jpg` | 1178/1178 |
| `sequence/frame-000000.depth.pgm` | 1178/1178 |
| `sequence/frame-000000.pose.txt` | 1178/1178 |

## Blockers

- none

## Next Gate

Open3DSG Docker env image build/import check

## Claim Limit

No Open3DSG checkpoint, raw dump, prediction JSONL, geometry join, or metric exists after training_repro staging.
