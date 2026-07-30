# Row-Level Paper Reproduction

This folder owns the frozen P1 row-level reproduction protocol. The gated
export reads the canonical candidate rows and model locks, removes original
identifiers and raw geometry, and writes a deterministic pseudonymized bundle.
A separate command consumes only that bundle and the compact canonical
references to regenerate:

- main-paper Table 1
- main-paper Table 2
- main-paper Table 3
- Figure 3 data and a verification rendering
- a cell-by-cell numerical tolerance report

The large derived bundle is written under `artifacts/` and is intentionally
ignored by Git until the authors confirm whether derived annotation rows may be
redistributed under the 3RScan/3DSSG terms. The compact protocol, manifest,
tables, figure data, and validation report are submission-repository
artifacts.

`schema.json` publishes the row contract without publishing row contents.
`expected_bundle.json` records the expected file counts, sizes, and hashes so a
locally exported bundle can be checked before paper regeneration.

## Commands

Build the pseudonymized bundle from gated inputs:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_export_rows
```

Regenerate all paper artifacts from the bundle:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_reproduce_rows
```

The public rerun writes to `regenerated/`. The tracked `evaluation/` directory
contains the frozen canonical outputs used for the cell-by-cell comparison and
is not overwritten.

## User action

Before putting `artifacts/derived_rows/` in a public code/data ZIP, confirm
derived-row redistribution with the dataset owner or the governing terms. If
permission is not explicit, distribute the export/reproduction commands and
manifest but require authorized users to build the bundle locally.
