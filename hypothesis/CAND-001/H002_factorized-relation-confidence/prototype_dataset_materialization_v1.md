# H002 Prototype Dataset Materialization V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `prototype_dataset_contract_v1.md`를 실제 artifact로 만드는 materialization step을
정의한다. 목표는 `smoke_baseline_plan_v1.md`가 요구하는 입력 파일을 train-only로 만들고,
기존 H002 artifact를 새 `T_e`, `Z_e`, `G_e`, `Q_e` contract에 맞춰 변환하는 것이다.

## Runner

Materialization runner:

```text
tools/prototype_dataset_materialization_v1.py
```

Default command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/prototype_dataset_materialization_v1.py
```

Default output root:

```text
artifacts/prototype_dataset_v1/
```

## Inputs

The runner reads three train-only sources.

| Source | Role |
| --- | --- |
| `independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/posterior_ready_rows.jsonl` | numeric `G_e` source for `support_contact` and `relative_vertical` compatibility smoke |
| `reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingestion/ingested_rows.jsonl` | attachment reliability/observability audit rows |
| `reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion/ingested_rows.jsonl` | hanging-on reliability/observability audit rows |

The runner does not modify any source artifact.

## Output Files

The runner writes:

| File | Role |
| --- | --- |
| `source_candidates.jsonl` | normalized source candidate inventory |
| `prototype_rows.jsonl` | canonical `T_e`, `Z_e`, `G_e`, `Q_e` rows |
| `counterfactual_groups.jsonl` | anchor/counterfactual grouping for compatibility smoke |
| `baseline_view.jsonl` | flattened baseline fields |
| `audit_view.jsonl` | label/control/audit fields, not model input |
| `split_manifest.json` | train-only split and source provenance |
| `schema.json` | model-view schema and blocked-input declaration |
| `summary.json` | counts, status, and boundary |
| `validation_errors.jsonl` | materialization validation errors |
| `report.md` | human-readable materialization summary |

## Mapping Policy

### Support / Vertical Rows

Support/vertical rows are the first compatibility-smoke-ready subset because they contain numeric
raw geometry features.

Mapping:

```text
T_e <- predicate label, relation family, subject/object label
Z_e <- source semantic score/rank from semantic_only view
G_e <- cleaned raw_witness_only_v2 numeric geometry fields
Q_e <- coverage and raw-witness availability fields
compatibility_label <- target y
reliability_label <- target y
```

Important filtering:

- `support_contact_gate`, `relative_vertical_gate`, `expected_z_sign`, predicate/family/rank/source
  proxy fields are not copied into `G_e`;
- `p_geom_valid` is preserved only as `p_geom_valid_baseline`;
- target labels and hidden metadata are not model inputs.

### Attachment / Hanging Audit Rows

Attachment rows are included as reliability/observability diagnostic rows, not as the main numeric
compatibility subset.

Reason:

```text
v20/v22 rows have visual/mesh audit evidence, but current materialization does not yet expose
numeric attachment G_e such as contact surface, hanging anchor point, or mesh boundary evidence.
```

Mapping:

```text
T_e <- predicate label, relation family, subject/object label
Z_e <- available source/rank fields when present
G_e <- empty numeric geometry block with geometry_source = audit_packet_no_numeric_g
Q_e <- evidence tier, same-frame/multi-view/mesh availability, coverage review
reliability_label <- audit accept/reject/abstain
observability_label <- coverage/uncertainty review
compatibility_label <- unknown unless numeric G_e later becomes available
```

This prevents attachment audit labels from becoming fake compatibility labels.

## Validation Rules

Materialization fails if:

- any row is not train split;
- `compatibility_main` contains `Z_e`;
- `G_e.geometry_features` contains predicate/family/source/rank/label/hidden/status/bucket/target
  fragments;
- a no-GT row is treated as a counterfactual negative without a negative tier;
- counterfactual group ids are duplicated or refer to missing rows.

## Current Result

The default runner has been executed once.

Result artifact:

```text
artifacts/prototype_dataset_v1/summary.json
```

Current counts:

```text
prototype_rows = 694
counterfactual_groups = 67
compatibility positive / negative / unknown = 67 / 67 / 560
reliability accept / reject / abstain = 101 / 442 / 151
observability observable / limited = 280 / 414
validation_errors = 0
```

The intended interpretation is:

- `support_contact` and `relative_vertical` are the first compatibility-smoke-ready families;
- `attachment_deferred` is present for reliability/observability diagnostics;
- attachment compatibility remains blocked until numeric attachment `G_e` is materialized.

## Boundary

This step:

- uses train-only data;
- does not train a model;
- does not use validation/test data;
- does not promote any result to paper evidence;
- does not modify H001 artifacts;
- does not modify source H002 v20/v22/support artifacts.

## Next TODO

```text
smoke_baseline_runner_v1 = completed
learned_smoke_runner_v1 = completed
attachment_numeric_geometry_materialization_v1 = completed
next = attachment_numeric_geometry_smoke_v1
```

The first deterministic and learned smoke runners have completed. Attachment numeric `G_e` is now
materialized separately under `artifacts/attachment_numeric_geometry_v1/`; the next step should
run an attachment-specific smoke over that artifact.
