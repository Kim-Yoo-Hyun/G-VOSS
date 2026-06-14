# Scripts

`scripts/` contains lightweight shell wrappers for reproducible long-running jobs.

## Current Contents

- Open3DSG payload/downstream loop wrappers.
- Qwen-VL full-source shard loop wrapper.

## Rule

Scripts should call Docker/compose entry points from `configs/` and write detailed runtime logs under ignored `logs/`. Do not place core metric, preprocessing, adapter, or model logic here; that belongs in `src/geocalib/`.
