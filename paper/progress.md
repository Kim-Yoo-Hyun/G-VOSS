# RelCompat3D Paper Progress

Last updated: 2026-07-27 KST

이 문서는 paper-facing completion state, selected submission artifact, and
remaining work만 기록한다. Experiment chronology와 runtime artifact는
`experiments/`, 복구 명령은 `docs/reproducibility.md`, reviewer 판단과 위험은
`paper/review.md`와 `paper/risk.md`가 소유한다.

## Current Phase

Status: `source_and_release_synchronized`

`paper/aaai/main_teaser_aaai27.pdf`를 main submission layout으로 선택했다.
Scientific claim, main comparisons, controls, audit, supplement,
reproducibility checklist, canonical PDFs, and the anonymous release bundle are
synchronized. The remaining work is the deferred first-page layout warning and
submission-system metadata rather than new experiments.

The selected title is **RelCompat3D: Predicate–Geometry Compatibility for
Re-Ranking 3D Scene Graph Relations**. The consolidated main and selected
stored PDF use this title. Supplement/checklist capitalization synchronization
remains part of the final release pass.

## Completed Scientific Components

| component | status | paper role |
| --- | --- | --- |
| fixed-candidate geometric-compatibility task | complete | Introduction / Method |
| ordered-pair and exact relation identity contract | complete | Method / Metrics |
| source-score-excluded compatibility estimation | complete | Method |
| Linear and shared compact MLP estimators | complete | Method / Table 1 |
| linked positive--counterfactual training | complete | Method / supplement |
| proximity and vertical transformation averaging | complete | Method / proof |
| family-aware re-ranking | complete | Method / main comparisons |
| strict train/development/evaluation split | complete | Experimental Setup |
| VL-SAT/Open3DSG/SGFN shared-target evaluation | complete | Table 1 / Figure 3 |
| RankAvg, RRF, Product (all families) | complete | Table 1 |
| matched wrong-predicate/pair/shuffle/swap controls | complete | Table 2 / supplement |
| distance-only and compatibility-only controls | complete | Table 2 / supplement |
| scan-level paired intervals | complete | Results / supplement |
| feature-removal and counterfactual sensitivity | complete | supplement |
| matched component diagnostics | complete | supplement |
| five-seed fitting robustness | complete | supplement |
| point- and mesh-based consistency audit | complete | Table 3 / supplement |
| uncertainty and family decomposition | complete | supplement |
| bounded re-ranking runtime and parameter count | complete | supplement |
| external ReplicaSSG/FROSS stress test | complete | supplement limitation evidence |

Relative-size and support/contact extensions remain completed research artifacts
but are not active main-paper evidence.

## Completed Manuscript Components

- Abstract and six-section AAAI manuscript structure.
- Main source consolidated into seven numbered files:
  `0_abstract`, `1_introduction`, `2_related_work`, `3_method`,
  `4_experiments`, `5_discussion_limitations`, and `6_conclusion`.
- Active supplement consolidated into `paper/aaai/sec/supplement.tex`.
- Inactive relative-size manuscript text retained in `paper/aaai/sec/old.tex`.
- Reviewer feedback converted from `paper/user_feedback.tex` to
  `paper/user_feedback.md`.
- Active Python modules use the `src/relcompat3d/` namespace and concise
  role-based filenames; Docker, manifests, and documentation use the same
  paths.
- Generated figure directory reduced to current Figure 1--3 assets and their
  locked data/manifests; the active supplemental qualitative image moved to
  `paper/aaai/supplement_figures/`.
- Figure 1 demotion case, Figure 2 method overview, and Figure 3 all-K
  Recall--Violation trajectories finalized for the selected teaser.
- Table 1 all-K comparison, Table 2 K=50 matched controls, and Table 3 K=50
  alternative audit finalized.
- Discussion consolidates construct, shared-target, and support/contact limits.
- Anonymous supplement and standalone reproducibility checklist are available.

## Selected Canonical Build

| artifact | status | pages | SHA-256 |
| --- | --- | ---: | --- |
| `paper/aaai/main_teaser_aaai27.pdf` | **selected main** | 9 | `ddaa71272112dfd231745bf8125b9daf22c7a4c65e245583e4f0630b53919d70` |
| `paper/aaai/main_aaai27.pdf` | retained comparison | 9 | `e6b56666e2e76cad11bcde2c725704283e70fa625fc1560fc9ad4bc9149944b6` |
| `paper/aaai/supplement_aaai27.pdf` | active supplement | 10 | `8c718bb50eea9d8665f0e198661e1fc41213e4323ee3205b7272c9524bf2b5a5` |
| `paper/aaai/reproducibility_checklist_aaai27.pdf` | active checklist | 2 | `d929e8b5dc38e32bc1e92c498ae7d41a7699d37f4aaf80027152117e8f6bb270` |

The selected canonical main now builds from the consolidated
`user_v6`-aligned source as nine pages with seven technical pages. It retains a
36.78-pt first-page vertical overfull. The prior 4.43-pt horizontal overfull is
resolved. The user has explicitly deferred the remaining warning.

The latest synchronized bundle is
`release/relcompat3d_aaai27_openreview_20260728_022521/`. It chooses the teaser
layout and was regenerated from the consolidated source. Its PDFs, ZIP, and
manifests pass independent verification. The remaining layout issue is the
first-page vertical overfull.

## Decisions Locked

- `main_teaser_aaai27.pdf` is the main submission layout; the default PDF is no
  longer an upload candidate.
- Main claim is shared-target, cross-predictor relation reliability.
- All $K\in\{5,10,20,50,100\}$ remain visible.
- K=50 is an intermediate reported setting, not a selected endpoint.
- RelCompat3D-Linear and RelCompat3D-MLP are equal proposed estimators within
  one framework; neither is universally superior.
- Proximity and vertical-order candidates are re-ranked.
- Support/contact candidates retain source order.
- Product (all families) is a scope comparison, not the primary method.
- Violation is verifier-derived; the point/mesh audit is an alternative
  construct check rather than independent ground truth.
- Dataset-level generalization and support/contact improvement remain outside
  the claim.

## Deferred or Non-Main Tracks

| track | status | reason outside main claim |
| --- | --- | --- |
| relative size | artifact only | fixed geometric rule is equally strong; stored in `old.tex` |
| support/contact learned re-ranking | deferred | insufficient local contact/pose evidence and no family-wide transform |
| attachment subtype | development only | multi-source gate not met |
| relative horizontal | blocked | reference-frame semantics unresolved |
| Qwen-VL | extension only | outside the frozen three-predictor contract |
| ReplicaSSG/FROSS | supplement stress test | target-dependent transfer and candidate-coverage limits |
| independent human reference | optional | would strengthen construct validity but is not required for the scoped claim |

## Remaining Work

### Required before submission

1. Resolve the first-page vertical overfull without changing margins, type
   size, or using negative spacing.
2. Complete OpenReview author metadata, conflicts, reciprocal-reviewer
   declaration, topics, title, abstract, and TL;DR fields.
3. Complete the generative-AI role disclosure in the required venue location.
4. Confirm the derived-row redistribution boundary and public license.
5. Decide the post-acceptance artifact URL.

### Optional scientific strengthening

- independent reference labels or human alignment;
- additional dataset evaluation with adequate exact-label candidate coverage;
- richer contact and pose measurements for support/contact.

Optional work must not broaden the current claim unless its protocol and
evidence are frozen first.
