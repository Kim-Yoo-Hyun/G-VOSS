# RelCompat3D Paper Progress

Last updated: 2026-07-28 KST

This file records submission status only. Experiment histories and artifact
inventories belong in the experiment README and reproducibility runbook.

## Current Phase

The scientific manuscript, technical supplement, reproducibility checklist,
figures, bibliography, code/data archive, and reviewer-defense experiments are
complete. The paper is in final source/PDF synchronization and upload
preparation.

## Completed Scientific Work

- source-score-excluded Linear and MLP compatibility estimators;
- linked positive--counterfactual training;
- transformation averaging;
- family-aware re-ranking;
- three-predictor shared-split evaluation;
- exact-match Recall and verifier-derived Violation;
- paired scan-level intervals;
- matched controls and fusion comparisons;
- point/mesh alternative audit;
- score-mapping and simple-baseline sensitivities;
- routing, component, feature, and seed diagnostics;
- candidate-pool oracle and row-level regeneration;
- transfer stress test and family slices.

## Completed Manuscript Work

- Abstract through Conclusion finalized.
- Figure 1--3 and Table 1--3 finalized and referenced.
- Supplement consolidated into `aaai/sec/supplement.tex`.
- Official reproducibility checklist completed.
- Citation keys and bibliography metadata audited.
- Manual-bold captions and 7-point table cells removed.
- First-page and Table 2 overfull warnings resolved.
- Outlined-v15 figures verified without font inclusion warnings.

## Final Terminology

- `validation split`: the official dataset partition;
- `validation scenes`: the evaluated reconstructed scenes;
- `shared`: all three predictors use the same split, contexts, relation scope,
  metrics, and cutoffs;
- `target`: retained only where the supplement describes the overall
  evaluation setting.

The latest source uses:

- Introduction: `on the shared 3DSSG validation scenes`;
- Discussion: `on the same 3DSSG validation split`;
- Conclusion: `on the shared 3DSSG validation scenes`.

## Final Canonical Build

| Artifact | Pages | SHA-256 |
| --- | ---: | --- |
| Main | 9 | `f0a3c6ab9810e58eb7e1cab6f61989eac6f4fcedca7b00ae68e2a6e001cc8cdf` |
| Supplement | 10 | `2785ba776d587fb9d38fba2cc652dfe6a99359470a2824c436229da5c687d760` |
| Checklist | 2 | `f712082e0709572f82be637bd962bf438580d3145ce60d7c7650bb38a5611939` |

These PDFs are synchronized with the latest source. The release is
`../release/relcompat3d_aaai27_openreview_20260728_214915/`.

## Locked Decisions

- Title remains **RelCompat3D: Re-Ranking 3D Scene Graph Relations with
  Geometric Evidence**.
- Main claim remains source-relative and point-estimate based.
- Product (all families) remains a scope comparison.
- Support/contact remains in source order.
- Point/mesh audit remains alternative evidence, not independent ground truth.
- M-1--M-3 remain in the main Results; detailed diagnostics remain in the
  supplement.
- Release remains conservative with respect to licensed data and source IDs.

## Required Before Upload

1. Add or otherwise resolve the AAAI-required documentation of generative-AI
   use.
2. Verify final author order, affiliations, profiles, conflicts, topics, title,
   abstract, and TL;DR in OpenReview.

## Optional, Not Submission-Blocking

- brace additional method acronyms in BibTeX title fields;
- obtain permission for redistribution of pseudonymized derived rows;
- add an independent human validity audit in future work;
- extend to additional datasets and relation families.
