# RelCompat3D Paper Workspace

Last updated: 2026-07-28 KST

This directory owns the active RelCompat3D manuscript, technical supplement,
reproducibility checklist, figures, bibliography, release-facing paper source,
and paper-planning documents.

## Current Identity

- Title: **RelCompat3D: Re-Ranking 3D Scene Graph Relations with Geometric
  Evidence**
- Venue: AAAI-27 Main Technical Track
- Main method: predicate--geometry compatibility for family-aware re-ranking
  of fixed 3D scene graph relation predictions
- Variants: RelCompat3D-Linear and RelCompat3D-MLP
- Main scope: re-rank proximity and vertical order while retaining
  support/contact in source order

## Active Sources

| Role | Path |
| --- | --- |
| Official main source | `aaai/main.tex` |
| Main sections | `aaai/sec/0_abstract.tex` through `aaai/sec/6_conclusion.tex` |
| Technical supplement wrapper | `aaai/supplement.tex` |
| Technical supplement content | `aaai/sec/supplement.tex` |
| Checklist wrapper | `aaai/reproducibility_checklist_main.tex` |
| Checklist content | `aaai/reproducibility_checklist.tex` |
| Bibliography | `references.bib` |
| Main figures | `reference_AAAI/figure/Figure{1,2,3}.pdf` |
| Supplement figure | `aaai/supplement_figures/qualitative_geometry_panels.png` |
| Integrated review | `user_feedback.md` |

`aaai/main_teaser.tex` is a compatibility wrapper and is not the official
submission entry point.

## Manuscript Structure

1. Abstract
2. Introduction
3. Related Work
4. Method
5. Experiments
6. Discussion and Limitations
7. Conclusion

The main paper is self-contained. Supplement-only material provides method
details, diagnostics, sensitivities, intervals, oracles, and reproducibility
support.

## Terminology

- Use **3DSSG validation split** for the dataset partition.
- Use **3DSSG validation scenes** for the evaluated reconstructed scenes.
- Use **shared** only to state that the predictors use the same split,
  contexts, relation scope, metrics, and \(K\) values.
- Use **verifier-derived Violation**, not physical-validity accuracy.

## Figures and Tables

- Figure 1: vertical-order failure and demotion.
- Figure 2: compatibility/re-ranking flow and proximity demotion.
- Figure 3: Recall--Violation trajectories.
- Table 1: main comparisons over all \(K\).
- Table 2: ablations and controls.
- Table 3: point/mesh consistency audit.

See `figures.md` for fixed visual values and `experiment.md` for metric and
comparison contracts.

## Planning Document Roles

| File | Owner role |
| --- | --- |
| `preview.md` | Current handoff snapshot |
| `outline.md` | Final story and section map |
| `method.md` | Implementation-faithful method contract |
| `experiment.md` | Evaluation contract and evidence map |
| `figures.md` | Figure intent, values, and caption contract |
| `appendix.md` | Technical supplement map and provenance boundary |
| `supplement.md` | Detailed supplement table/figure guide |
| `reproducibility.md` | Checklist answers and release boundary |
| `progress.md` | Submission completion state |
| `review.md` | Final reviewer-style assessment |
| `risk.md` | Residual scientific and submission risks |

## Build

From the repository root:

```bash
docker build -f paper/aaai/Dockerfile.tex \
  -t relcompat3d-aaai27-tex:20260712 paper/aaai

docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Build `supplement.tex` and `reproducibility_checklist_main.tex` in the same
image.

## Current Synchronization State

The final canonical set builds to 9/10/2 pages and passes warning, font,
manifest, anonymity, ZIP, and extracted-source checks. It is synchronized with
the latest main, supplement, and checklist sources. The current release is
`../release/relcompat3d_aaai27_openreview_20260728_214915/`.

## Archive Boundary

Historical venue routes, superseded drafts, inactive experiments, raw datasets,
source-derived rows, model caches, and checkpoints are not part of the active
anonymous submission tree.
