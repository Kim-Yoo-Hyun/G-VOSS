# Open3DSG Source Patch

Created at: `2026-05-08T02:45:42.572644+00:00`
Status: `ready`
Source root: `local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source`

## Purpose

Apply explicit `weights_only=False` to trusted local Open3DSG checkpoint/feature loads required by PyTorch 2.6+, enable env-controlled lazy dataset loading to avoid full-train preload OOM, and make feature dumping resumable before expensive forward passes.

## Records

- `open3dsg/models/sgpn.py`: `already_patched`
- `open3dsg/models/sgpn.py`: `already_patched`
- `open3dsg/models/sgpn.py`: `already_patched`
- `open3dsg/models/sgpn.py`: `already_patched`
- `open3dsg/models/sgpn.py`: `already_patched`
- `open3dsg/scripts/run.py`: `already_patched`
- `open3dsg/data/open_dataset.py`: `already_patched`
- `open3dsg/data/open_dataset.py`: `already_patched`
- `open3dsg/data/open_dataset.py`: `already_patched`
- `open3dsg/scripts/trainer.py`: `already_patched`
- `open3dsg/scripts/trainer.py`: `already_patched`
- `open3dsg/scripts/trainer.py`: `already_patched`
- `open3dsg/scripts/trainer.py`: `already_patched`
- `open3dsg/data/open_dataset.py`: `already_patched`
