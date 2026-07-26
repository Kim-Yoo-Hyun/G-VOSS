# RelCompat3D Paper Workspace

Last updated: 2026-07-26 KST

This directory owns the active RelCompat3D manuscript, supplement, checklist,
figures, bibliography, and paper-facing planning documents. Experiment runtime
records belong under `experiments/`, compact evidence under `results/`, and
paper-writing rules under `docs/paper.md`.

## Current Identity

- Selected title: **RelCompat3D: Predicate–Geometry Compatibility for Re-Ranking
  3D Scene Graph Relations**.
- Method: **RelCompat3D**, with Linear and MLP compatibility estimators.
- Venue source: `paper/aaai/`.
- Selected main artifact: `paper/aaai/main_teaser_aaai27.pdf`.
- Main task: predicate–geometry compatibility assessment and family-aware
  re-ranking of fixed 3D scene graph relation predictions.
- Main scope: re-rank proximity and vertical-order candidates while retaining
  support/contact candidates in source order.

The selected title is synchronized across the consolidated main source,
supplement source, and paper-facing planning documents. The stored PDFs will be
regenerated during the final release pass.

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

The current main source has nine total pages with technical content ending on
page 7. The prior Table 2 horizontal overflow is resolved. The build retains
one 36.78-pt first-page vertical overfull for the final layout pass.

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
- `supplement.md`: active supplement의 section, table, figure 역할과
  reviewer-facing 유지 우선순위.
- `reproducibility.md`: checklist 응답 근거와 제출 artifact의 공개 범위.
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

The synchronized candidate release can be regenerated for verification. Do not
treat it as upload-ready until the first-page overfull and final
submission-system disclosure checks are resolved.

## Archive Boundary

Superseded venue routes, non-submission analyses, historical experiments, and
inactive paper workspaces are preserved in the ignored local archive described
by `archive/README.md`. They are not part of the active anonymous submission
tree.
