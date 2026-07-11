# H002 Docker Configuration

Last updated: 2026-07-11 KST

This folder owns the reproducible runtime configuration for the scoped H002
compatibility-routing experiment.

## Files

- `Dockerfile`: Python 3.11 runtime for materialization, metrics, controls, and CI
- `Dockerfile.assets`: pinned Matplotlib runtime for paper figures
- `requirements.assets.txt`: paper-asset dependencies
- `compose.yaml`: current claim pipeline only

## Service Groups

| Group | Services |
| --- | --- |
| internal compatibility | preflight, materialize, schema audit, grouped split/eval |
| source reranking | materialize, schema audit, metric, bootstrap CI, sensitivity |
| lateral route | frame audit, route scorer, left/right vs front/behind split |
| paper assets | table refresh, qualitative package, figures/appendix |

The compose file intentionally excludes discarded learned-G_e, p_obs/p_rel,
support/contact repair-loop, test-resolution, and paper-transition services.

## Mount Contract

- repository: `/workspace`
- local data: `/data/local_dataset:ro`
- H001 compact results: read-only
- H001 experiment archive: read-only

H002 services must not write to any H001 path.

## Validate

```bash
docker compose -f configs/h002/compose.yaml config --services
```

Commands and execution order are documented in
`experiments/H002_compatibility_routing/commands.md`.
