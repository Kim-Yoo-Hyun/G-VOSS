# H002 Docker Config

This folder will own Docker configuration for H002 compatibility-routing promotion.

## Current Status

```text
status = official_metric_result_review_ready_with_boundaries_no_paper_result
paper_metric_ready = false
next_todo = compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
```

## Planned Services

| Service | Role |
| --- | --- |
| `h002-protocol-check` | verify mounts, artifact statuses, and output roots |
| `h002-materialize-routes` | regenerate promoted route rows and model-safe/hidden manifests |
| `h002-materialization-schema-audit` | audit materialized rows for schema leakage, shortcut risk, and split-readiness |
| `h002-grouped-split` | create internal train/dev/heldout split by `cv_group_id` without running metrics |
| `h002-shortcut-audit` | run leakage, shortcut, wrong-T, and shuffled-G audits |
| `h002-grouped-eval` | run grouped-holdout route metrics and controls |
| `h002-official-materialize-candidates` | materialize official validation candidates without metrics |
| `h002-official-materialization-schema-audit` | audit official candidate materialization for leakage, shortcut risk, label balance, and control readiness |
| `h002-official-metric-runner` | run official validation metrics after protocol freeze |
| `h002-calibration` | optional calibration/selective-risk evaluation for `p_rel` / `p_obs` |

## Boundary

`Dockerfile` and `compose.yaml` currently implement `h002-protocol-check`,
`h002-materialize-routes`, `h002-materialization-schema-audit`,
`h002-grouped-split`, `h002-grouped-eval`,
`h002-official-materialize-candidates`, and
`h002-official-materialization-schema-audit`.

Docker preflight passed with exit 0. Route materialization also passed with exit
0 and wrote row-level runtime outputs under:

```text
experiments/H002_compatibility_routing/materialization/latest/
```

Materialization schema audit also passed with exit 0 and wrote audit outputs under:

```text
experiments/H002_compatibility_routing/schema_audit/latest/
```

Grouped split protocol also passed with exit 0 and wrote split outputs under:

```text
experiments/H002_compatibility_routing/splits/latest/
```

Do not add grouped evaluation or calibration services to paper-result use until their review and claim-lock artifacts exist.

Grouped evaluation protocol now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/
```

Grouped evaluation runner has passed and wrote runtime metrics under:

```text
experiments/H002_compatibility_routing/evaluation/latest/
```

Relative-vertical failure analysis has passed, and `h002-grouped-eval` feature
extraction has been repaired so compatibility features read explicit raw
geometry paths rather than suffix-matching availability-mask fields. Repaired
grouped-eval claim-boundary review and official validation/source-inventory
planning have also passed.
`Z_e` and `Q_e` remain outside the main `C_e` model unless a separate `p_rel` /
`p_obs` protocol is created.

Official source inventory now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/
```

The previous config-level blocker was defining the official candidate
materialization protocol before adding new Docker commands.

Official candidate materialization protocol now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory/
```

`h002-official-materialize-candidates` has been added to `configs/h002/compose.yaml`
and has completed once with exit 0. `h002-official-materialization-schema-audit`
has also completed once with exit 0 and wrote:

```text
experiments/H002_compatibility_routing/official_schema_audit/latest/
```

The audit found `0` schema violations, `0` blocked field hits, `0` runtime
validation errors, and `0` control-readiness blockers. It also found one
claim-boundary caveat: `support_contact` `predicate_x_class_pair` majority
accuracy `0.993707`. Official validation metrics remain blocked until the
official metric runner is implemented, executed, and reviewed under the frozen
protocol.

Official metric protocol freeze now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/
```

`h002-official-metric-runner` has now completed once with exit 0 and wrote under:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
```

It treats official validation rows as eval-only and does not use official test.
The next work is not config implementation; it is result review and claim
boundary lock.

Official metric result review has completed. The next work remains outside
config implementation: claim-boundary lock and paper-facing wording/table-role
decision.

H001 artifacts must be mounted read-only if referenced.
