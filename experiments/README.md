# Experiments

`experiments/` stores source-specific experiment records, ablations, analysis outputs, and row-level runtime result locations for H001/GeoCalib.

## Current Active Root

- `H001_geom_reliability/`: active GeoCalib experiment workspace.

## Role Boundary

Keep compact paper-facing tables, reports, figure specs, and locked manifests in `results/`. Keep executable Python in `src/geocalib/`, shell wrappers in `scripts/`, and Docker/compose files in `configs/`. Old or optional expansion tracks that should not be part of the main release path are preserved under `archive/`.

## Reproduction

Before launching or cleaning any experiment, read `docs/reproducibility.md` and the local experiment README.
