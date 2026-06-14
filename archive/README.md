# Archive

`archive/` preserves material that should not sit on the main execution path but is not safe to delete.

## Contents

- `experiments/`: optional/future-work relation expansion outputs and superseded experiment material.
- `hypothesis_records/`: preserved H001/H002 pre-paper hypothesis records moved out of active `docs/`.
- `code/`: old feasibility or non-active code kept for reference.
- `paper/`: superseded venue files and LaTeX build byproducts.
- `notes/`: old notes not part of the current paper-facing route.
- `cache/`: moved runtime caches such as `__pycache__`.

## Rule

Archive contents are not the primary reproduction path. If archived material is promoted again, move only the necessary files back into the owning active folder and update README, configs, and reproducibility docs in the same change.
