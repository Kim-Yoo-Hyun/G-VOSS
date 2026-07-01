# Docs

`docs/` owns repository-wide workflow rules, navigation, and reproducibility
runbooks. It is not the live research dashboard.

## Main Files

- `index.md`: documentation table of contents and file ownership pointers.
- `reproducibility.md`: H001 recovery, artifact bundle, dataset/checkpoint, Docker, and cleanup runbook.
- `paper.md`: novelty, claim boundary, and reviewer-defense rules.
- `experiments.md`: Docker experiment workflow and result-promotion rules.
- `literature.md`: literature workflow.
- `hypothesis.md`: hypothesis workflow.

Preserved hypothesis records now live under `archive/hypothesis_records/`.

## Rule

Use `docs/` the way documentation systems use a docs root: `index.md` and
`README.md` are entry points; other files are durable rulebooks or runbooks.
Current status, row counts, metric tables, long artifact inventories, and
completion logs belong in `TODO.md`, `summary.md`, folder `README.md` files, or
the closest experiment/report artifact. Link to those owners instead of copying
their content here.
