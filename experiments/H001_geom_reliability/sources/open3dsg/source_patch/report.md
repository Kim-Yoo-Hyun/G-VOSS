# Open3DSG Source Patch

Created at: `2026-05-31T22:19:16.491857+00:00`
Status: `ready`
Source root: `local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source`

## Purpose

Apply explicit `weights_only=False` to trusted local Open3DSG checkpoint/feature loads required by PyTorch 2.6+, install a NumPy pickle compatibility alias for staged preprocess artifacts, enable env-controlled lazy dataset loading to avoid full-train preload OOM, make train/validation/test feature dumping resumable before expensive forward passes, support H001 eval feature-dump sharding over remaining missing ids, skip eval-only relation mapper allocation during feature dumping, keep test-mode feature dumping from falling through into metric evaluation, chunk BLIP image embedding/projector forwards to reduce peak GPU memory, align avg-BLIP relationship image embedding dtype with the loaded BLIP model dtype, switch BLIP generation to `max_new_tokens` for current Transformers compatibility, and export H001 identity-preserving raw prediction JSONL during Open3DSG test.

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
- `open3dsg/data/open_dataset.py`: `already_patched`
- `open3dsg/scripts/trainer.py`: `already_patched`
- `open3dsg/scripts/trainer.py`: `already_patched`
- `open3dsg/models/sgpn.py`: `already_patched`
- `open3dsg/models/sgpn.py`: `already_patched`
- `open3dsg/models/sgpn.py`: `already_patched`
- `open3dsg/models/sgpn.py`: `already_patched`
- `open3dsg/data/open_dataset.py`: `already_patched`
