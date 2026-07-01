# Configs

`configs/` owns Docker and runtime configuration entry points.

## Layout

- `h001/`: GeoCalib core Dockerfile and compose services for table generation, metrics, bootstrap CI, and analysis.
- `h002/`: skeleton Docker configuration root for future H002 compatibility-routing promotion. No active compose service exists yet.
- `open3dsg/`: Open3DSG reproduction/runtime Dockerfile and compose services.
- `qwen_vl/`: Qwen-VL extension runtime Dockerfile and compose services.

## Rule

Use these configs for paper-facing reproduction. If a path changes in `src/`, `experiments/`, or `results/`, update the corresponding compose service and `docs/reproducibility.md` together.
