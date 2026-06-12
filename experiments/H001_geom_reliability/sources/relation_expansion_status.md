# Relation Expansion Status

Last updated: 2026-06-11 KST

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
| `attachment_deferred` | `attached to`, `hanging on`, `connected to` | Best-aligned future physical-relation upgrade because attachment implies contact, surface, gravity, and adjacency constraints | G0-G5d completed: scope/schema, extractor contract, dry run, point/surface validation, verifier policy, train/dev route, GT smoke, strict calibration, source scoring/metrics/controls/bootstrap | Not failed, but not current main claim: G5d is on the historical H001 388/377-context scope rather than the current full official validation route; Open3DSG covers only 768/967 exact-label GT rows; `attached to` is noisy; `connected to` has no dev strict rows; post-G5d visual/failure audit is still needed before promotion | Keep as appendix/preliminary extension evidence and preferred future upgrade; do not promote to the current AAAI main claim. Promotion requires full-validation rerun plus audit and explicit user confirmation |
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
- Appendix/future work: present `attachment_deferred`, especially `hanging on`,
  as the most plausible next physical-relation upgrade. It has G5d metric
  evidence, so it is stronger than a pure idea, but it remains preliminary
  extension evidence because it was not rerun on the current full official
  validation route and still has Open3DSG denominator and audit caveats.
- Do not report `relative_lateral` source metrics as main evidence from the
  current strict policy because the train/dev gate is caveated.

## Attachment Deferred Promotion Gate

Decision on 2026-06-11 KST: do not promote `attachment_deferred` into the
current AAAI main claim.

Reasoning:

- G5d is promising but belongs to the older H001 388/377-context scope:
  VL-SAT has 388 subgraphs and Open3DSG has 377 subgraphs. The current paper
  main route is full official validation, with VL-SAT full-validation and the
  Open3DSG 548/548 recovery branch.
- Open3DSG attachment coverage is 768/967 exact-label GT rows, leaving 199
  missing exact-label rows. This caveat is too large for a clean main-claim
  expansion.
- `connected to` has no dev strict rows, so any label-specific calibration
  claim is blocked. Pooled calibration is usable only with an explicit caveat.
- G5d has failure rows and bootstrap, but it does not yet have a post-G5d
  qualitative/visual audit at the same standard as the selected main H001
  families.
- The rule-verified attachment policy has a strong violation reduction
  signal, but high uncertain rates mean the appendix wording must treat it as a
  conservative extension, not broad solved functional reasoning.

Minimum requirements before any future promotion:

- Rebuild the attachment denominator and source rows on the current
  full-validation route.
- Rerun VL-SAT full-validation and Open3DSG full-validation recovery
  attachment scoring/metrics/controls/bootstrap.
- Report global and source-covered denominators separately.
- Add post-G5d failure taxonomy and qualitative/visual audit.
- Include pairwise bootstrap deltas for semantic-only versus rule-verified and
  calibrated variants.
- Keep `connected to` pooled-calibration caveat, or collect a defensible
  train/dev split with dev strict rows before making label-specific claims.
- Ask the user again before changing the main AAAI claim.
