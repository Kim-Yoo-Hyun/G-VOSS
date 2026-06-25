# Full Official Validation Transition

Date: `2026-06-03 KST`

Status: `full_validation_primary_route_selected_metric_and_failure_analysis_ready`

Scope contract artifact:

```text
results/h001_geom_reliability/full_validation_transition/scope_contract/
```

Created by Docker service:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm full_validation_scope_contract'
```

## Decision

The paper-facing primary evaluation route has moved from the completed
pilot-excluded H001 hardened scope to the full official `3DSSG_subset`
validation split after the Docker rerun completed.

This does not invalidate existing results. The 127-scan tables remain
historical/sensitivity evidence. The current paper-facing route is
VL-SAT full-validation as the controlled anchor and Open3DSG
`recovery_relaxed_views_min2/` as the primary open-vocabulary source.

## Method Provenance Rule

Paper wording should state that the final method design, predicate-family map,
hard-rule policies, counterfactual construction, and `p_geom_valid` calibrators
are fixed from train/train-dev artifacts before validation source-result
reporting.

H001-Mini remains hypothesis/feasibility evidence. It is not a paper metric
split and should not be described as the source of final threshold fitting or
calibrator fitting.

## Scope Comparison

| Scope | Scans | Contexts | GT-positive directed pairs | GT rows | H001-family GT rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| completed H001 hardened | 127 | 388 | 5,263 | 7,505 | 2,545 |
| full official validation | 157 | 548 | 7,720 | 11,254 | 3,972 |

The full official validation contract also records `36,808` candidate directed
pairs and `957,008` expected VL-SAT prediction rows under the current
all-non-`none` predicate export policy.

Full official validation H001-family counts:

| Family | Count |
| --- | ---: |
| `support_contact` | 1,816 |
| `proximity` | 1,766 |
| `relative_vertical` | 390 |
| total | 3,972 |

Other full-validation family counts:

| Family | Count |
| --- | ---: |
| `relative_horizontal` | 5,474 |
| `attachment_deferred` | 1,205 |
| `unsupported_first_pass` | 603 |

## Preflight Snapshot

Lightweight local preflight on 2026-06-03 KST:

| Item | Status |
| --- | --- |
| raw 3RScan payload | 157/157 validation scans ready |
| VL-SAT raw geometry payload | 157/157 validation scans ready |
| VL-SAT full-validation staged root | 157/157 faithful staged scans ready |
| VL-SAT full-validation raw preflight | ready_to_run, 0 errors, 1 expected import-shim warning |
| Open3DSG mesh/texture payload | 157/157 validation scans ready |
| Open3DSG sequence payload | 157/157 validation scans ready |
| VL-SAT hardened staged root | 127/157 scan dirs present |
| VL-SAT mini staged root | 8/157 scan dirs present |
| Open3DSG H001 runtime views | 127/157 validation scans ready |
| Open3DSG H001 runtime preprocess | 377/548 validation contexts ready |
| Open3DSG training-repro views | 30/157 validation scans ready |
| Open3DSG training-repro preprocess | 155/548 validation contexts ready |

Interpretation:

- Full official validation is feasible in principle because raw 3RScan payload
  exists for all validation scans.
- It is not a denominator edit. VL-SAT staging/export and Open3DSG
  preprocessing/features/raw dump must be regenerated under separate
  full-validation output paths.
- Open3DSG full-validation coverage caveats must be recomputed from the new
  raw dump identity audit and adapter export.
- The scope contract is not metric evidence. It only freezes the denominator,
  provenance wording, output paths, promotion gates, and command templates.
- VL-SAT staging/runtime preflight is also not metric evidence. It only proves
  the full-validation raw dump can be launched through a Docker-compatible
  command with fixed inputs and checkpoint provenance.

## Required Rerun Gates

VL-SAT full-validation gates:

1. Stage official validation scans and annotations under a separate
   full-validation runtime root. Done: `sources/vlsat/full_validation/stage/`
   is ready with 157/157 faithful scans.
2. Freeze Docker runtime record and raw-dump preflight. Done:
   `sources/vlsat/full_validation/runtime_record/` and
   `sources/vlsat/full_validation/raw_preflight/` are ready.
3. Launch raw predictions dump as a timestamped tmux/background job when GPU
   contention with Open3DSG R1 training is acceptable. Done.
4. Export identity-preserving prediction JSONL and full-validation
   ground-truth JSONL. Done.
5. Run geometry join and `p_geom_valid` scoring with frozen train-dev
   calibrators. Done.
6. Run metrics, controls, GT verifier check, bootstrap CI, tables, and report.
   Done.
7. Generate full-validation failure-analysis rows and deterministic qualitative
   inspection queue. Done: 59,841 rows and 36 selected cases.

Open3DSG full-validation gates:

1. Decide checkpoint route after the running non-averaged BLIP retry finishes.
   Done: selected official non-avg checkpoint.
2. Generate full-validation views/preprocess/features under separate paths.
   Done: original 533/548 branch and recovery 548/548 branch exist.
3. Run raw dump identity audit for 157 scans / 548 contexts. Done for the
   recovery branch.
4. Export adapter prediction JSONL, geometry join, metrics, bootstrap CI,
   failure rows, qualitative queue, and caveat wording. Done for the recovery
   branch: 695,916 predictions, 695,916 geometry rows, 82,155 failure rows, and
   36 selected qualitative cases.
5. Update paper tables only after all source-specific caveats are known. Done:
   AAAI tables/prose use the selected full-validation route.

## Completed Source Outcomes

| Source | Role | Output root | Metric status | Failure-analysis status |
| --- | --- | --- | --- | --- |
| VL-SAT full-validation | controlled anchor | `sources/vlsat/full_validation/` | `ready` | 59,841 rows, 36 qualitative cases |
| Open3DSG recovery full-validation | primary open-vocabulary source | `sources/open3dsg/full_validation/recovery_relaxed_views_min2/` | `ready` | 82,155 rows, 36 qualitative cases |
| Open3DSG 533/548 branch | sensitivity / unmodified-source route | `sources/open3dsg/full_validation/` | `ready` | 81,448 rows |

The recovery branch is selected because it handles all 548 official validation
contexts. It must still be reported as a recovery-policy variant because it
uses `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` and relaxed two-scan view regeneration.

## Paper Claim Boundary

Allowed after full rerun:

```text
Across reproduced VL-SAT and Open3DSG prediction sources on the full official
3DSSG_subset validation split, calibrated geometry-consistency re-ranking
improves relation reliability for geometry-checkable families while preserving
explicit recall tradeoffs.
```

Superseded pre-rerun warning:

```text
127-scan results alone prove the full official validation claim.
```

This statement is no longer used as a blocker because the full-validation
VL-SAT and Open3DSG recovery artifacts are complete. The 127-scan branch remains
historical/sensitivity evidence only.

Blocked regardless:

```text
The method broadly improves open-vocabulary 3D scene graph generation.
```
