# Compatibility Dataset V3 Docker Heldout Protocol Plan After Promotion Gap Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan/
status = h002_compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan_ready
selected_path = docker_heldout_protocol_ready_select_experiment_root_skeleton
validation_errors = 0
next_todo = compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan
```

## Purpose

This stage fixes the Docker and grouped-holdout protocol before any H002 paper-result experiment root is created.

It does not:

- create `experiments/H002_compatibility_routing/`,
- create `configs/h002/`,
- create `results/h002_compatibility_routing/`,
- run a model,
- run validation/test evaluation,
- produce a paper-level metric.

## Proposed Future Roots

| Path | Role | Create now |
| --- | --- | --- |
| `experiments/H002_compatibility_routing/` | future H002 Docker experiment workspace | false |
| `configs/h002/` | future H002 Dockerfile/compose root | false |
| `results/h002_compatibility_routing/` | future compact paper-facing summaries | false |

If these roots are created in a later step, update the local README files and repository indices before substantive work.

## Promoted Candidate Routes

| Family | Predicates | Included in grouped holdout metric |
| --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | true |
| `size_relative` | `bigger than`, `smaller than` | true |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | true |
| `support_contact` | `standing on`, `lying on` | true |

Diagnostic/deferred routes are not promoted in this path: `close by`, `supported by`,
`attached to` / `hanging on` / `connected to`, containment, `cover`, `leaning against`,
identity/symmetry, and semantic/structural relations.

## Source Pool Boundary

The grouped holdout is defined inside the H002 candidate source pool. It must not be called official
validation/test unless official dataset splits are explicitly adopted in a later protocol.

The split policy is:

- primary group: `scan_id`,
- secondary guard: endpoint pair when available,
- ratio: `train/dev/heldout = 70/15/15` by groups,
- tuning: train/dev only,
- final grouped holdout: read once for final route metrics.

## Docker Protocol Contract

Future services:

- `h002-protocol-check`
- `h002-materialize-routes`
- `h002-shortcut-audit`
- `h002-grouped-eval`
- `h002-calibration`, optional only if `p_rel` / `p_obs` claims remain active

Required mounts:

- repository root,
- `local_dataset/` read-only,
- H002 hypothesis artifacts,
- optional H001 reference artifacts read-only,
- `logs/`.

## Pass / Fail Gates

| Gate | Stage | Pass condition |
| --- | --- | --- |
| D0 | protocol | this artifact has validation errors 0 and no experiment root was created |
| D1 | Docker preflight | mounts resolve, prior artifacts match, H001 inputs are read-only |
| D2 | materialization | promoted route rows exist, labels are valid per split, validation errors 0 |
| D3 | grouped holdout | group leakage is 0, route metrics pass family-specific thresholds, controls collapse |
| D4 | calibration optional | calibration/selective-risk metrics support `p_rel` / `p_obs` |
| D5 | claim lock | paper wording matches passed gates and blocked claims remain explicit |

## Output Files

- `summary.json`
- `protocol_scope.csv`
- `proposed_root_plan.csv`
- `docker_mount_plan.csv`
- `compose_service_plan.csv`
- `heldout_split_policy.csv`
- `output_manifest_contract.csv`
- `route_metric_contract.csv`
- `control_matrix.csv`
- `leakage_audit_plan.csv`
- `pass_fail_gates.csv`
- `blocked_actions.csv`
- `command_contract.csv`
- `next_contract.json`
- `report.md`
- `validation_errors.jsonl`
