# Docs

`docs/` owns repository-wide workflow rules, dashboard state, and reproducibility guidance.

## Main Files

- `index.md`: current dashboard and file ownership pointers.
- `reproducibility.md`: H001 recovery, artifact bundle, dataset/checkpoint, Docker, and cleanup runbook.
- `paper.md`: novelty, claim boundary, and reviewer-defense rules.
- `experiments.md`: Docker experiment workflow and result-promotion rules.
- `literature.md`: literature workflow.
- `hypothesis.md`: hypothesis workflow.

Preserved hypothesis records now live under `archive/hypothesis_records/`.

## Rule

Do not use `docs/` as a dump for row-level runtime outputs or large artifacts. Link to the owning folder instead.
