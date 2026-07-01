# Compatibility Dataset V3 Official Metric Result Review After Runner

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner/
status = h002_compatibility_dataset_v3_official_metric_result_review_after_runner_ready_with_boundaries
selected_path = official_metric_review_ready_select_claim_boundary_lock
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
```

## Purpose

Official validation metric runner 결과를 paper-level experiment gate 관점에서 검토했다.
이 단계는 결과를 바로 paper table로 승격하는 단계가 아니라, paper-level experiment를
실행해도 되는 조건이 충족됐는지와 어떤 claim boundary가 필요한지를 판단하는 gate다.

## Gate Decision

| Gate | Status | Decision |
| --- | --- | --- |
| Docker reproducible runner | pass | runner execution is valid |
| Official validation policy | pass | validation was eval-only and official test was not used |
| Main feature boundary | pass | main `C_e` uses `T_e` and `G_e` only |
| Primary metric vs baselines | pass | `M4_TxG_compatibility` beats `M1`, `M2`, and `M3` |
| wrong-`T` / shuffled-`G` controls | pass | controls degrade strongly |
| relative-horizontal frame control | caveat | frame-control wording must be conservative |
| support-contact claim | caveat | diagnostic only, not solved |
| paper promotion | conditional pass | proceed to claim-boundary lock, not final paper promotion |

## Family Claim Boundary

| Family | Status | M4 AUROC | Boundary |
| --- | --- | ---: | --- |
| `relative_vertical` | paper candidate main evidence | 0.991321 | axis-order route supports predicate-geometry compatibility |
| `size_relative` | paper candidate main evidence | 0.999585 | size-comparison route supports predicate-geometry compatibility |
| `relative_horizontal` | candidate with caveat | 0.719568 | frame-aware route can be used with frame-control caveat |
| `support_contact` | diagnostic/challenging only | 0.631712 | use as failure taxonomy and evidence-gap analysis |

## Blocked Claims

- all-relation generalization
- solved support/contact
- strong relative-horizontal frame invariance
- calibrated `p_rel` / `p_obs` reliability
- source reranking / recall tradeoff
- official test result

## Decision

Official validation `C_e` mechanism experiment is valid enough to move to
claim-boundary lock. It is not yet a final paper table result because relation-family
scope, caveats, and paper wording still need to be locked.

## Next

```text
compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
```
