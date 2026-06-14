# Source Code

`src/` contains the core executable GeoCalib code.

## Role

- `src/geocalib/`: Python entry points for dataset staging, geometry evidence extraction, prediction/geometry joins, metric evaluation, bootstrap confidence intervals, source adapters, Open3DSG/Qwen helpers, and paper table generation.
- `src/geocalib/paths.py`: shared repository path constants used by direct script entry points.

## Execution Rule

Paper-facing runs should be launched through Docker compose files in `configs/`, not by installing dependencies directly on the host. Most services mount the repository at `/workspace` and call scripts as `/workspace/src/geocalib/<script>.py`.

## Boundaries

Keep reusable execution logic here. Put shell orchestration in `scripts/`, Docker/runtime configuration in `configs/`, source-specific run outputs in `experiments/`, compact summaries in `results/`, and superseded or optional expansion material in `archive/`.

The paper-facing claim path is VL-SAT/Open3DSG over `support_contact`, `proximity`, and `relative_vertical`. Qwen-VL and relation-family expansion scripts may remain here when they are runnable Docker entry points, but their outputs stay extension/appendix or archived evidence unless explicitly promoted.
