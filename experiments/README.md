# Experiments

`experiments/` stores source-specific experiment records, ablations, analysis outputs, and row-level runtime result locations.

## Current Active Root

- `H001_geom_reliability/`: active GeoCalib experiment workspace.
- `H002_compatibility_routing/`: skeleton for future H002 Docker promotion. It currently has no paper-level metrics, no grouped-holdout run, and no official validation/test usage.

## Role Boundary

Keep compact paper-facing tables, reports, figure specs, and locked manifests in `results/`. Keep executable Python in `src/geocalib/`, shell wrappers in `scripts/`, and Docker/compose files in `configs/`. Old or optional expansion tracks that should not be part of the main release path are preserved under `archive/`.

## Reproduction

Before launching or cleaning any experiment, read `docs/reproducibility.md` and the local experiment README.

H002 must pass its local Docker preflight before materialization, grouped-holdout metrics, or calibration outputs are treated as paper-result candidates.
