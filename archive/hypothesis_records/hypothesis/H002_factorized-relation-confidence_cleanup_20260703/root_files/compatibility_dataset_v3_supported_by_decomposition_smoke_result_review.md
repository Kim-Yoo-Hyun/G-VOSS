# R6 Supported-By Decomposition Smoke Result Review

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_result_review/
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_result_review_ready_for_route_update
selected_path = freeze_supported_by_as_superordinate_decomposition_diagnostic_keep_out_of_main_factorized_success
validation_errors = 0
next_todo = compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review
```

This review consumes the train-only R6 smoke runner result and freezes the claim boundary. It does not use validation/test rows and does not promote a paper-level result.

## Decision

`supported by` is frozen as a superordinate support decomposition diagnostic.

It should not be treated as a main factorized-route success because observable `p_rel` is better explained by `G_e + Q_e` and Q-only routes than by the full `T_e + G_e + Q_e` route.

## Key Evidence

```text
p_obs M6_TGQ AUROC = 0.978802
p_obs Q-only AUROC = 1.000000
observable p_rel M6_TGQ AUROC = 0.831328
observable p_rel G_e+Q_e AUROC = 0.905703
observable p_rel Q-only AUROC = 0.880547
observable p_rel best single G_e AUROC = 0.888984
shuffled-G AUROC = 0.540703 / 0.459063
hidden construction p_rel AUROC = 1.000000
```

## Route Position

- R6 `supported by`: diagnostic broad-label decomposition route.
- R3 `standing on` / `lying on`: remains separate support/contact predicate-geometry compatibility route.
- R7 `attached to` / `hanging on` / `connected to`: remains queued as observability-first route after route map update.

## Claim Boundary

Allowed:

- broad `supported by` labels need accept/relabel/reject/abstain decomposition;
- `Q_e` is useful for p_obs and for exposing observability-dominated labels;
- `supported by` should be separated from cleaner predicate-level support/contact relations.

Blocked:

- R6 proves factorized reliability success;
- `T_e + G_e + Q_e` improves observable p_rel over component routes;
- `Q_e` directly represents relation truth;
- this train-only smoke is paper-level evidence.

## Next

Run `compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review` to merge the R6 boundary into the H002 route map before any attachment/observability expansion or promotion planning.
