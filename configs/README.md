# Configs

`configs/` owns Docker and runtime configuration entry points.

## Layout

- `h001/`: GeoCalib core Dockerfile and compose services for table generation, metrics, bootstrap CI, and analysis.
- `open3dsg/`: Open3DSG reproduction/runtime Dockerfile and compose services.
- `qwen_vl/`: Qwen-VL extension runtime Dockerfile and compose services.

## Rule

Use these configs for paper-facing reproduction. If a path changes in `src/`, `experiments/`, or `results/`, update the corresponding compose service and `docs/reproducibility.md` together.
