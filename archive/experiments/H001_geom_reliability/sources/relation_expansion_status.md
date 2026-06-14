# Relation Expansion Status

Last updated: 2026-06-06 KST

This file summarizes relation-family expansion attempts beyond the current H001
main claim. It records why each family was tried, what evidence was produced,
why it was not promoted, and what the final paper-facing action is.

The current AAAI main claim remains scoped to:

- `support_contact`
- `proximity`
- `relative_vertical`

Those families have full-validation VL-SAT/Open3DSG source metrics, controls,
bootstrap CI, GT verifier checks, and failure-analysis artifacts. The families
below do not replace or expand that main claim.

## Summary Table

| Family / track | Labels | Why tried | Evidence produced | Why not main claim | Final action |
|---|---|---|---|---|---|
| `relative_horizontal` | `left`, `right`, `front`, `behind` | Largest excluded geometry-adjacent family; would expand GT denominator by 3,570 rows | Scope audit, coordinate audit, bucket inspection | Full-family macro strict purity is 0.7725; `front`/`behind` strict purity is 0.7445; `front`/`behind` ambiguity buckets remain large; frame semantics are not resolved | Stop as appendix/limitation evidence; do not run source metrics |
| `relative_depth_deferred` | `front`, `behind` | Split from `relative_horizontal` after left/right looked stronger | Inherited from relative-horizontal coordinate audit and bucket inspection | Depth/viewpoint semantics are unresolved; front/back labels are affected by frame/viewpoint ambiguity and orthogonal-axis dominance | Deferred; only revisit through a predeclared visual/frame-metadata study |
| `relative_lateral` | `left`, `right` | Narrower candidate after left/right strict purity reached 0.8005 in the held-out coordinate audit | Policy freeze, train/dev policy lock, train-only calibrator, dev failure diagnosis | Train side is strong, but dev strict purity is only 0.6975; contradictions are pair-symmetric, concentrated in two dev scans, and often same-label object pairs; uncertain rows are mostly orthogonal/front-back-axis dominance | Stop as appendix/future-work boundary; do not run paper-facing source metrics |
| `attachment_deferred` | `attached to`, `hanging on`, `connected to` | Best-aligned future physical-relation upgrade because attachment implies contact, surface, gravity, and adjacency constraints | G0-G5d completed: scope/schema, extractor contract, dry run, point/surface validation, verifier policy, train/dev route, GT smoke, strict calibration, source scoring/metrics/controls/bootstrap | Not failed, but not current main claim: Open3DSG covers only 768/967 exact-label GT rows; `attached to` is noisy; `connected to` has no dev strict rows; visual/failure audit is still needed before promotion | Keep as preferred future upgrade; requires explicit user confirmation before any main-claim update |
| Qwen-VL semantic source | H001 families only | Modern VLM third-source extension | Input/output contract, crops, model cache, runtime smoke, full-source runner plan, shards 0000-0013 complete | No full prediction JSONL, parser aggregation, geometry join, metrics, controls, bootstrap CI, or audit yet | Deferred until GPU runtime and full-source evaluation are completed |

## Why These Stops Help The Paper

The stops are not wasted work. They support a stricter top-tier claim boundary:

- H001 is not claiming that every spatial relation can be checked by the same
  simple rule.
- Expansion attempts are allowed only when the family passes the same standard
  as the current main families.
- Failed or caveated families reveal exactly where geometry-consistency
  evaluation needs more semantic/frame information.
- Reviewer-facing wording should use these tracks to show disciplined scope
  control, not to inflate coverage.

## Paper-Facing Decision

For the current AAAI path:

- Main results: keep full-validation `support_contact`, `proximity`, and
  `relative_vertical` across VL-SAT and Open3DSG.
- Appendix/limitations: mention `relative_horizontal` and `relative_lateral`
  as boundary diagnostics only.
- Future work: present `attachment_deferred`, especially `hanging on`, as the
  most plausible next physical-relation upgrade.
- Do not report `relative_lateral` source metrics as main evidence from the
  current strict policy because the train/dev gate is caveated.
