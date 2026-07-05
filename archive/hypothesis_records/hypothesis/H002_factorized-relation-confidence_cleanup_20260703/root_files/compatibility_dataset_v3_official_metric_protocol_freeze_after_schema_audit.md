# Compatibility Dataset V3 Official Metric Protocol Freeze After Schema Audit

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/
status = h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_ready
selected_path = official_metric_protocol_frozen_select_official_metric_runner
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_runner_after_protocol_freeze
```

## Purpose

이 단계는 official validation metric을 실행하기 전에 metric, model view,
control, aggregation, claim boundary를 고정한다. 아직 metric runner가 아니며,
paper-level result도 아니다.

핵심 원칙은 official validation rows를 `eval-only`로 사용한다는 점이다.
Trainable view의 fit, threshold, model selection은 internal train/dev에서 끝나야 하며,
official validation metric을 본 뒤 protocol을 바꾸면 안 된다.

## Inputs

```text
artifacts/compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation/summary.json
experiments/H002_compatibility_routing/official_schema_audit/latest/audit_manifest.json
experiments/H002_compatibility_routing/official_materialization/latest/row_manifest.json
```

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit.py
```

## Artifact Outputs

```text
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/summary.json
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/official_metric_contract.json
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/model_view_contract.json
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/family_metric_plan.csv
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/control_contract.csv
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/claim_boundary_contract.json
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/next_runner_contract.json
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/report.md
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/validation_errors.jsonl
```

## Metric Contract

- target: `C_e`
- primary metric: `macro_family_AUROC`
- secondary metrics: weighted-family AUROC, overall AUROC, AUPRC, balanced accuracy, macro-F1, Brier
- main `C_e` input: `T_e`, `G_e` only
- excluded from main `C_e`: `Z_e`, `Q_e`, H001 `p_geom_valid`, hidden construction fields
- official validation: eval-only
- official test: not used
- paper result: not promoted until metric review and claim-lock pass

## Family Plan

| Family | Rows | Label 0 | Label 1 | Role | Claim status |
| --- | ---: | ---: | ---: | --- | --- |
| `relative_horizontal` | 18764 | 13290 | 5474 | primary frame-aware compatibility route | primary if family metric and controls pass |
| `relative_vertical` | 780 | 390 | 390 | primary signed-geometry compatibility route | primary if family metric and controls pass |
| `size_relative` | 340 | 170 | 170 | primary size compatibility route | primary if family metric and controls pass |
| `support_contact` | 3178 | 1589 | 1589 | challenging support/contact route | diagnostic/challenging, not solved |

## Required Controls

- wrong-`T` within route
- wrong-`T` across route
- shuffled-`G` global
- shuffled-`G` within family
- subject/object swap
- signed-geometry flip where applicable
- horizontal frame/axis swap for `relative_horizontal`

## Boundary

- No official metric was computed.
- Official test was not used.
- No paper-level result was promoted.
- `p_rel` / `p_obs` remain disabled.
- `support_contact` remains challenging because schema audit found a strong
  `predicate_x_class_pair` shortcut warning.

## Next

```text
compatibility_dataset_v3_official_metric_runner_after_protocol_freeze
```

The next stage should add a Docker metric runner that follows this frozen
protocol and writes runtime outputs under:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
```
