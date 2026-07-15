# H001 Paper Reviewer-Risk Register

Last updated: 2026-07-15 KST

Scope: current scientific and submission risks for `paper/aaai/`. Historical
mitigation logs belong in experiment reports and archived snapshots.

## Current Verdict

RelCompat3D is defensible as a scoped empirical/method paper about geometric
compatibility assessment for fixed 3D relation predictions. Its acceptance case is the combination of
a concrete failure mechanism, source-score exclusion, identity-preserving
geometry joins, linked counterfactuals, exact algebraic controls, applicability
routing, and joint Recall--Violation evaluation. It is not accept-safe because
construct validity and the absence of an unbiased, full-coverage external-
dataset confirmation remain substantive limitations.

## Risk 1: Compatibility and Violation Share Geometry Primitives

The learned target and verifier use some of the same engineered geometric
measurements. Wrong-predicate, wrong-pair, shuffled-geometry, and transformation
controls rule out simple score copying, but they do not provide an independent
physical-validity construct.

Current defense:

- call `C_e` a constructed-target compatibility score, not a physical-validity
  probability;
- call V verifier-derived everywhere;
- report uncertainty and family decomposition;
- retain the reviewer-verified Codex study outside the submission.

An additional strict train-only diagnostic removes either the exact normalized
scalar consumed by the verifier, every directly related distance/vertical
measurement, or all but alternative evidence. Exact-scalar removal preserves
nearly the full result, excluding literal scalar reuse as the sole mechanism.
The broader holdouts retain a clear Open3DSG effect but attenuate K=50
violation gains on VL-SAT and SGFN. This is useful construct-overlap
sensitivity, not an independent validity reference.

Reviewers A/B/C confirmed all 488 completed Codex labels with zero revisions at
`2026-07-14T22:49:11+09:00`. This validates transcription and review coverage,
not independent first-pass human validity. The scientific risk is reduced only
by a separate two-annotator plus blinded-adjudicator Human V@K study.

## Risk 2: One Shared Dataset Target

VL-SAT, Open3DSG, and SGFN are different predictors but all operate on the same
3DSSG/3RScan target. A zero-target-fitting application of the unchanged model
to ReplicaSSG/FROSS adds external diagnostic evidence. The routed product has
paired joint gains at K=10 and K=50, but becomes nearly inert at K=100 under
heavy source-score quantization. A family-slot-preserving rank diagnostic
separately identifies scale sensitivity and cross-family displacement, but is
not promoted as the paper's ranking rule. These results do not establish
cross-dataset generalization.

Residual blockers are material: the Replica target had been inspected in prior
development, only 76/172 exact GT relations have candidate support,
support/contact is unmapped, 19.20% of model feature cells exceed three training
standard deviations, and only 11 scene bootstrap units are available.

Current defense: state the shared main target once in Setup and once in
Limitations; report the Replica stress test in the supplement across every K,
including the K=100 saturation and candidate ceiling; and never use established
dataset-generalization or arbitrary-source wording.

## Risk 3: Support/Contact Applicability

The unrestricted product regresses on support/contact because the current
geometry representation lacks a valid blanket endpoint transformation and
does not fully observe contact/pose evidence.

The primary family-slot route resolves the operational aggregate failure by
preserving support/contact source selections and global family composition
exactly while reranking only proximity/vertical slots. It does not solve or
improve support/contact compatibility.

Blocked wording: family-uniform improvement, support/contact solved, or a
universal relation router. Required wording: applicability-scoped routing with
support/contact pass-through.

## Risk 4: Nonlinear Rescorer and Novelty Ceiling

A frozen train-only, source-score-excluded nonlinear model was trained with the
same constructed supervision and evaluated under the same family-slot route.
It does not jointly dominate the product. At Open3DSG K=100, it changes Recall
by `+.0297` and Violation by `+.0047` relative to the routed product; on VL-SAT
and SGFN, neither rule is uniformly superior across budgets.

A separate SGFN-specific exact-label nonlinear rescorer uses stronger,
source-specific supervision and is stronger on SGFN. Therefore the paper must
not claim best rescorer or formula superiority. The defensible novelty is the
factor-isolated compatibility and evaluation contract plus transfer behavior,
not the multiplication operator.

## Risk 5: Open3DSG Coverage Route

The public preprocessing pipeline yields predictions for 533 of the 548
official contexts because 15 contexts fail its object-to-image visibility
gate. The main result uses the label-independent 548-context universe and gives
those 15 contexts no predictions. This is the conservative official-target
evaluation.

Sensitivity at K=100:

| Route | Contexts | Source R/V | Routed R/V |
| --- | ---: | ---: | ---: |
| public eligible | 533 | .5206/.1242 | .5799/.0324 |
| public/full target | 548 | .5111/.1242 | .5692/.0324 |
| recovered/full target | 548 | .5161/.1242 | .5743/.0332 |

Current defense: use public/full target in the main paper; report the eligible
and recovery variants only as sensitivity. Do not describe the recovered route
as the unmodified public pipeline.

## Additional Bounded Risks

- The measured family scope is narrow. Relative size is a supplement-only
  extension and not core learned-method evidence.
- Hard filtering obtains V=0 by construction and can select fewer than K; keep
  it diagnostic.
- Budget behavior is source dependent. Report all five K values, use K=50
  descriptively as a mid-curve reference rather than a separately registered
  endpoint, and distinguish pointwise preservation from strict
  Recall improvement when an interval contains zero.
- Open3DSG uses a selected public checkpoint/preprocessing route. Keep the
  necessary setup provenance in the supplement without narrating internal
  research chronology in the main text.
- Author profiles, reciprocal reviewer eligibility, conflicts, public license,
  and artifact URL remain user-controlled submission tasks.

## Claim Contract

Allowed:

> A single source-score-excluded compatibility model, combined with an
> applicability-aware family-slot route, reduces verifier-derived Violation
> across three predictors at K=50 while
> preserving or improving Recall; the full K=5--100 curve is reported.

Not allowed:

- best or universally optimal rescorer;
- independent human physical-validity validation;
- cross-dataset or all-relation generalization;
- support/contact improvement;
- Open3DSG SOTA or complete generator reproduction.

## Submission Gate

The scientific package is ready when the canonical PDFs and anonymous source
bundle reproduce the routed tables and figures. Remaining portal work is the
author list/profiles, topics, reciprocal reviewer, conflicts, license, and
artifact URL. An independent-human alignment study is optional strengthening,
not a prerequisite for the current scoped submission claim.
