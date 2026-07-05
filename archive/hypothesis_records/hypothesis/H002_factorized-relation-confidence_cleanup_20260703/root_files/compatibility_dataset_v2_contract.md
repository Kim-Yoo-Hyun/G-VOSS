# Compatibility Dataset V2 Contract

Date: 2026-06-26 KST

## Purpose

This contract fixes the concrete v2 dataset requirements for H002 after the method-level scope was
selected. It turns the selected scope into a materialization contract: what rows are allowed, which
families are primary, which labels are valid, which fields are blocked, and which controls must be
present before any smoke test.

The v2 dataset is still a train-only hypothesis artifact. It is not paper evidence until promoted
through a Docker experiment workflow.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v2_contract.py
```

Output root:

```text
artifacts/compatibility_dataset_v2_contract/
```

Main outputs:

- `summary.json`
- `dataset_contract.json`
- `row_schema.json`
- `family_contract.csv`
- `control_contract.json`
- `report.md`
- `validation_errors.jsonl`

## Result

```text
status = h002_compatibility_dataset_v2_contract_ready
dataset_name = h002_compatibility_dataset_v2
selected_scope = primary_support_contact_relative_vertical_attachment_diagnostic
posterior_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_dataset_v2_materialization_plan
```

## Dataset Scope

```text
primary = support_contact, relative_vertical
diagnostic = attachment_like
future = proximity
deferred = relative_horizontal, containment
```

## Family Contract

| Family | Scope | Requested Min | Minimum Reportable | Required Counterfactuals |
| --- | --- | ---: | ---: | --- |
| `support_contact` | primary | `120/120` | `60/60` | wrong-pair, shuffled geometry, contact/support perturbation |
| `relative_vertical` | primary needs expansion | `80/80` | `60/60` | higher/lower flip, subject/object swap, wrong-pair, shuffled geometry |
| `attachment_like` | diagnostic only | `0/0` | `0/0` | not a current primary `C_e` target |
| `proximity` | future generality | `0/0` | `0/0` | not in v2 primary |

## Required Files For V2 Materialization

The future materialized dataset root should be:

```text
artifacts/compatibility_dataset_v2/
```

Required files:

- `source_candidates.jsonl`
- `compatibility_rows.jsonl`
- `diagnostic_rows.jsonl`
- `counterfactual_groups.jsonl`
- `baseline_view.jsonl`
- `audit_view.jsonl`
- `schema.json`
- `split_manifest.json`
- `summary.json`
- `validation_errors.jsonl`
- `report.md`

## Row Schema

Every v2 row must contain:

- stable identity fields: `row_id`, `group_id`, `split`, `scan_id`, `subject_instance_id`,
  `object_instance_id`, `directed_pair_id`;
- `T_e`: predicate, relation family, subject/object labels, text fields;
- `Z_e`: source id, source score, source rank, rank band;
- `G_e`: predicate-independent geometry features and masks;
- `Q_e`: evidence quality / observability fields;
- label axes: compatibility, observability, reliability, official GT, audit;
- hidden controls: scan/instance/provenance/construction fields for audit only.

`C_e` input is exactly:

```text
T_e + G_e
```

`Z_e` must not enter `C_e`.

## Blocking Conditions

Materialization or smoke must stop if any of the following occurs:

- validation errors are nonzero;
- validation/test data are used;
- `G_e` contains predicate, relation family, source score/rank, GT/audit label, or construction key;
- `C_e` uses `Z_e`;
- hidden construction fields appear in model input;
- `no_gt_for_pair` is treated as negative;
- `attachment_like` is used as a primary `p_rel/C_e` target;
- `relative_vertical` lacks directional flip or subject/object swap controls.

## H001 `p_geom_valid` Boundary

H001 `p_geom_valid` is allowed only as:

- geometry-only baseline;
- teacher or auxiliary supervision;
- named ablation input.

It is not the final H002 reliability score and should not be silently folded into the main `G_e`
condition.

## Next

The next step should inspect source capacity and decide how to materialize v2 rows under this
contract.

```text
compatibility_dataset_v2_materialization_plan
```

## Boundary

- Train-only H002 contract.
- No validation/test usage.
- No new posterior trained.
- No paper-level evidence promotion.
- H001 artifacts are not modified.
