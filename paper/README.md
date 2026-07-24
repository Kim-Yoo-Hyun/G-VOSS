# RelCompat3D Paper Workspace

Last updated: 2026-07-22 KST

This directory owns the active RelCompat3D manuscript, supplement, checklist,
figures, bibliography, and paper-facing planning documents. Experiment runtime
records belong under `experiments/`, compact evidence under `results/`, and
paper-writing rules under `docs/paper.md`.

## Current Identity

- Selected title: **RelCompat3D: Predicate–Geometry Compatibility for Re-ranking
  3D Scene Graph Relations**.
- Method: **RelCompat3D**, with Linear and MLP compatibility estimators.
- Venue source: `paper/aaai/`.
- Selected main artifact: `paper/aaai/main_teaser_aaai27.pdf`.
- Main task: predicate–geometry compatibility assessment and family-aware
  re-ranking of fixed 3D scene graph relation predictions.
- Main scope: re-rank proximity and vertical-order candidates while retaining
  support/contact candidates in source order.

The supplement source uses the selected title. Apply the same title to the
consolidated main and checklist during the pending layout pass so the stored
upload PDFs and all source entry points change together.

## Active Sources and Artifacts

| Role | Path |
| --- | --- |
| Selected manuscript source | `aaai/main_teaser.tex` |
| Alternate layout source | `aaai/main.tex` |
| Consolidated manuscript sections | `aaai/sec/0_abstract.tex` through `aaai/sec/6_conclusion.tex` |
| Supplement source | `aaai/supplement.tex` and `aaai/sec/supplement.tex` |
| Reproducibility checklist | `aaai/reproducibility_checklist_main.tex` |
| Bibliography | `references.bib` |
| Main figure assets | `aaai/AuthorKit27/Figures/` and `generated/figures/` |
| Supplement figures | `aaai/supplement_figures/` |
| User-assembled transcript | `user.tex` |
| Reviewer checklist | `user_feedback.md` |

The selected stored main PDF has nine total pages with technical content ending
on page 7. A fresh build from the consolidated source currently produces ten
pages and one 4.43-pt overfull table row. These layout issues must be resolved
before the final PDFs and anonymous release bundle are regenerated.

## Manuscript Structure

1. Abstract
2. Introduction
3. Related Work
4. Method
5. Experiments
6. Discussion and Limitations
7. Conclusion

`aaai/sec/old.tex` retains manuscript text that is not part of the active main
paper. The technical supplement is consolidated in
`aaai/sec/supplement.tex`.

## Figures and Tables

- Figure 1: Open3DSG vertical-order failure and demotion case.
- Figure 2: predicate/pair-measurement compatibility and family-aware
  re-ranking overview.
- Figure 3: Recall–Violation trajectories for Source, RelCompat3D-Linear, and
  RelCompat3D-MLP over all reported $K$ values.
- Table 1: shared-target main results.
- Table 2: Linear controls plus the MLP full-method operating point.
- Table 3: point- and mesh-based alternative geometric audit.

Detailed visual specifications belong in `figures.md`; method and evaluation
contracts belong in `method.md` and `experiment.md`.

## Planning File Roles

- `preview.md`: current handoff snapshot and selected artifact.
- `outline.md`: section logic, contributions, and figure/table placement.
- `method.md`: implementation-faithful method contract.
- `experiment.md`: datasets, comparison methods, metrics, and evidence scope.
- `figures.md`: figure intent, source values, coordinates, and caption rules.
- `progress.md`: completion state and remaining submission work.
- `risk.md`: active reviewer risks and claim boundaries.
- `review.md`: consolidated reviewer-style assessment.
- `appendix.md`: supplement content and provenance details.
- `user_feedback.md`: numbered revision TODO followed by detailed rationale.

## Build

Build with the pinned TeX image from the repository root:

```bash
docker build -f paper/aaai/Dockerfile.tex \
  -t relcompat3d-aaai27-tex:20260712 paper/aaai

docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main_teaser.tex
```

Do not regenerate the final upload bundle until the page-count, overfull-row,
and title synchronization tasks are complete.

## Archive Boundary

Superseded venue routes, non-submission analyses, historical experiments, and
inactive paper workspaces are preserved in the ignored local archive described
by `archive/README.md`. They are not part of the active anonymous submission
tree.
