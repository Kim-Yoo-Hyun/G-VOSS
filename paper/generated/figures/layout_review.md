# Draft Figure Layout And Novelty Review

Last updated: 2026-05-22 KST

Status: `layout_review_passed_with_figure3_geometry_upgrade`

Review basis:

- Top-tier novelty claim standard: figures should support failure mechanism,
  cause, method necessity, and falsifiable evidence. They should not merely
  show a generic pipeline or broad motivation.
- Active paper claim: calibrated geometry-consistency evaluation and re-ranking
  improves relation reliability for measured geometry-checkable 3DSSG relation
  families under recall/violation tradeoffs.

## Decisions

| figure | decision | top-tier novelty judgment |
| --- | --- | --- |
| Figure 1 | keep revised draft | Pass. The revised version now shows failure mechanism -> cause -> design necessity before the framework pipeline, which better supports the novelty claim than a generic pipeline-only diagram. |
| Figure 2 | keep draft | Pass. The two-panel tradeoff is the strongest evidence figure because it directly ties method variants to recall and violation. Keep VL-SAT and Open3DSG separated to avoid overclaiming cross-source comparability. |
| Figure 3 | use geometry-backed draft | Pass for manuscript planning. The row-card panels were traceable, and the follow-up `figure3_geometry_panels.svg` now adds deterministic point-cloud geometry visualization for the same locked case IDs. Do not present either form as a representative human audit. |

## Required Caption Constraints

- Figure 1 caption must use "calibrated geometry-consistency evaluation and
  re-ranking framework"; never "verifier script."
- Figure 2 caption must mention recall and violation together and retain the
  Open3DSG averaged-BLIP / covered-scope caveat.
- Figure 3 caption must say the panels are qualitative reviewer-defense
  examples from Open3DSG deterministic inspection and preprocessed object
  geometry, not a representative visual audit or new metric.

## Next Step

- Proceed to reviewing `paper/draft.md` section structure now that Related Work citation keys have been inserted.
- Keep only an optional final-polish TODO: replace the geometry panels with
  rendered scene crops if a deterministic crop/render path is later added for
  the same locked case IDs.
