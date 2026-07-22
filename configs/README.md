# Docker Configuration

The public submission config tree contains only the focused H001 runtime:

- h001/Dockerfile: pinned lightweight Python image;
- h001/compose.structured.yaml: active RelCompat3D fitting, evaluation,
  ablation, audit, runtime, and transfer services;
- h001/README.md: command and service boundary.

Open3DSG source reproduction, Qwen-VL, FROSS/ReplicaSSG, SGFN full inference,
and the historical all-service compose registry are preserved only in the
ignored local archive. They are not required to inspect the compact submission
evidence.

Use Docker for paper-facing experiment execution. Raw datasets and row-level
inputs are mounted externally and are never copied into the image.
