# Draft Figure Layout And Novelty Review

Last updated: 2026-05-22 KST

Status: `layout_review_passed_with_figure3_upgrade_recommended`

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
| Figure 3 | keep as draft placeholder; upgrade recommended | Partial pass. The row-card panels are traceable and useful for manuscript drafting, but top-tier final presentation would be stronger with rendered/crop or geometry visualization for the same locked case IDs. Do not present the row-card form as a representative human audit. |

## Required Caption Constraints

- Figure 1 caption must use "calibrated geometry-consistency evaluation and
  re-ranking framework"; never "verifier script."
- Figure 2 caption must mention recall and violation together and retain the
  Open3DSG averaged-BLIP / covered-scope caveat.
- Figure 3 caption must say the panels are qualitative reviewer-defense
  examples from Open3DSG deterministic inspection, not a representative visual
  audit or new metric.

## Next Step

- Proceed to replacing Related Work citation placeholders in `paper/draft.md`.
- Keep a later optional figure-improvement TODO: upgrade Figure 3 from row-card
  panels to rendered/crop evidence if a deterministic rendering path is added.
