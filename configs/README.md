# Docker Configuration

The public submission config tree contains only the focused RelCompat3D runtime:

- relcompat3d/Dockerfile: pinned lightweight Python image;
- relcompat3d/compose.structured.yaml: active RelCompat3D fitting, evaluation,
  ablation, audit, runtime, and transfer services;
- relcompat3d/README.md: command and service boundary.

Open3DSG source reproduction, Qwen-VL, FROSS/ReplicaSSG, SGFN full inference,
and the historical all-service compose registry are preserved only in the
ignored local archive. They are not required to inspect the compact submission
evidence.

Use Docker for paper-facing experiment execution. Raw datasets and row-level
inputs are mounted externally and are never copied into the image.
