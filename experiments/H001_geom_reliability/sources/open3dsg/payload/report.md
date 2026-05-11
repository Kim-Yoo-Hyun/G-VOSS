# 3RScan Payload Batch

Date: `2026-05-07T14:35:50+00:00`
Status: `payload_download_batch_complete`
Download missing: `True`
Extract sequence: `True`
File set: `all`
Processed scans: `82`

## Processed Readiness

- scan dirs: `82/82`
- sequence zip: `82/82`
- sequence extracted: `82/82`

## Raw Files

| File | Ready |
| --- | ---: |
| `labels.instances.annotated.v2.ply` | 82/82 |
| `mesh.refined.0.010000.segs.v2.json` | 82/82 |
| `semseg.v2.json` | 82/82 |

## Mesh/Texture Files

| File | Ready |
| --- | ---: |
| `mesh.refined.v2.obj` | 82/82 |
| `mesh.refined.mtl` | 82/82 |
| `mesh.refined_0.png` | 82/82 |

## Actions

- `already_ready`: `23`
- `downloaded`: `552`
- `extracted`: `81`

## Failures

- none

## Next Action

Re-run open3dsg_train_root, then continue payload batches until train scan dirs, mesh/texture, and sequence readiness reach 1178/1178.
