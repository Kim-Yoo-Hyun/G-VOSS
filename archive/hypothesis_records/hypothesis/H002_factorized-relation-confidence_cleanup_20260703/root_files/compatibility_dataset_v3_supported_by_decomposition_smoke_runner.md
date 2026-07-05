# R6 Supported-By Decomposition Smoke Runner

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_runner/
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_runner_q_observability_diagnostic
validation_errors = 0
learned_smoke_executed = true
epochs = 5
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_result_review
```

This is a train-only hypothesis smoke. It does not use validation/test rows and does not promote a paper-level claim.

## Input

- rows: `320`
- decomposition labels: `accept_broad_support 80`, `relabel_to_subtype 80`, `reject_no_support 80`, `abstain 80`
- `p_obs`: observable `240`, abstain `80`
- observable `p_rel` binary: accept-or-relabel `160`, reject `80`
- observable `p_rel` 3-way: `80/80/80`
- grouped CV groups: `257`

Allowed model features:

- `T_e`
- `G_e_mesh_pose_contact`
- `Q_e`

Hidden source/rank/GT/old-geometry/construction fields are audit probes only.

## Result Snapshot

```text
T1 p_obs M6_TGQ AUROC = 0.978802
T1 p_obs Q-only AUROC = 1.000000

T2 observable p_rel M6_TGQ AUROC = 0.831328
T2 observable p_rel GQ AUROC = 0.905703
T2 observable p_rel Q-only AUROC = 0.880547
T2 observable p_rel geometry-only AUROC = 0.875781
T2 observable p_rel best single G_e AUROC = 0.888984
T2 observable p_rel class-pair/T-only AUROC = 0.251719

T2 shuffled-G AUROC = 0.540703 / 0.459063
T2 shuffled-Q AUROC = 0.767266
T3 observable p_rel 3-way M6 macro OVR AUROC = 0.773047
T3 observable p_rel 3-way M6 macro F1 = 0.540704
```

Hidden probes:

```text
source/rank p_rel AUROC = 0.690078
construction p_rel AUROC = 1.000000
```

## Gate Result

- data integrity: pass
- `p_obs` signal: pass
- `p_rel` signal: pass
- `p_rel` gain over best component: fail
- `Q_e` boundary on observable `p_rel`: fail
- shortcut/single-factor boundary: pass
- shuffled-`G_e` degradation: pass
- shuffled-`Q_e` boundary: pass

## Interpretation

R6 `supported by` is not a clean factorized-route success.

The positive result is that observable `p_rel` is not explained by semantic/class shortcuts, and shuffled geometry degrades strongly. This means geometry evidence is involved.

The blocker is that `Q_e` and `G_e + Q_e` outperform the full `T_e + G_e + Q_e` route on observable `p_rel`. Therefore the target currently behaves more like a support-decomposition / observability-quality diagnostic than an independent relation reliability target.

Paper-facing boundary:

- usable as superordinate support decomposition diagnostic;
- usable as evidence that broad `supported by` should not be treated like clean `standing on` / `lying on`;
- not usable as a main calibrated `p_rel` or factorized-reliability success.

## Next

Run `compatibility_dataset_v3_supported_by_decomposition_smoke_result_review` to decide whether:

- R6 remains diagnostic/future-route evidence;
- R6 target definition should be revised;
- the route map should keep `supported by` separate from support/contact predicate-level compatibility.
