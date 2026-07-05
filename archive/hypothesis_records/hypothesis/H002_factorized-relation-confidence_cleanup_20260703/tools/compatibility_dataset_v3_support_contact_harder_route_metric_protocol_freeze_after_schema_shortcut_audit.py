#!/usr/bin/env python3
"""Freeze support/contact hard-route metric protocol after schema audit."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCHEMA_STAGE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization"
)
DEFAULT_RUNTIME_AUDIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/support_contact_harder_schema_audit/latest"
DEFAULT_MATERIALIZATION_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/support_contact_harder_materialization/latest"
DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit"
)

EXPECTED_PREV_STATUS = (
    "h002_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization_ready_with_warnings"
)
EXPECTED_PREV_NEXT = "compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit"
EXPECTED_RUNTIME_STATUS = "h002_support_contact_harder_schema_shortcut_audit_ready_with_warnings"
EXPECTED_MATERIALIZATION_STATUS = "h002_support_contact_harder_route_materialization_ready"
EXPECTED_SOURCE_INVENTORY_STATUS = "h002_compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol_ready"

EXPECTED_ROWS = 3178
EXPECTED_GROUPS = 1589
EXPECTED_FEATURES = 43
EXPECTED_TRAIN_MAIN_ROWS = 640

SCHEMA_VERSION = "h002_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit_v1"
STATUS_READY = "h002_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit_ready"
STATUS_ERRORS = "h002_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit_input_errors"
SELECTED_PATH = "support_contact_hard_metric_protocol_frozen_select_train_eval_alignment"
NEXT_TODO = "compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-stage-dir", type=Path, default=DEFAULT_SCHEMA_STAGE_DIR)
    parser.add_argument("--runtime-audit-dir", type=Path, default=DEFAULT_RUNTIME_AUDIT_DIR)
    parser.add_argument("--materialization-dir", type=Path, default=DEFAULT_MATERIALIZATION_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def validate_inputs(
    *,
    schema_summary: dict[str, Any],
    runtime_manifest: dict[str, Any],
    materialization_manifest: dict[str, Any],
    source_inventory: dict[str, Any],
    runtime_audit_dir: Path,
    schema_stage_dir: Path,
    control_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    if schema_summary.get("status") != EXPECTED_PREV_STATUS:
        errors.append({"error_type": "unexpected_schema_stage_status", "actual": schema_summary.get("status")})
    if schema_summary.get("next_todo") != EXPECTED_PREV_NEXT:
        errors.append({"error_type": "unexpected_schema_stage_next_todo", "actual": schema_summary.get("next_todo")})
    if schema_summary.get("validation_errors") != 0:
        errors.append({"error_type": "schema_stage_validation_errors", "actual": schema_summary.get("validation_errors")})

    if runtime_manifest.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_audit_status", "actual": runtime_manifest.get("status")})
    if runtime_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_audit_validation_errors", "actual": runtime_manifest.get("validation_errors")})
    if runtime_manifest.get("next_todo") != EXPECTED_PREV_NEXT:
        errors.append({"error_type": "unexpected_runtime_next_todo", "actual": runtime_manifest.get("next_todo")})

    if materialization_manifest.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append({"error_type": "unexpected_materialization_status", "actual": materialization_manifest.get("status")})
    if materialization_manifest.get("validation_errors") != 0:
        errors.append(
            {"error_type": "materialization_validation_errors", "actual": materialization_manifest.get("validation_errors")}
        )

    row_counts = materialization_manifest.get("row_counts", {})
    expected_counts = {
        "candidate_rows": EXPECTED_ROWS,
        "model_safe_main_no_class": EXPECTED_ROWS,
        "model_safe_main_with_class_ablation": EXPECTED_ROWS,
        "model_safe_geometry_only": EXPECTED_ROWS,
        "model_safe_qe_diagnostic": EXPECTED_ROWS,
        "hidden_manifest": EXPECTED_ROWS,
        "group_manifest": EXPECTED_GROUPS,
        "feature_count": EXPECTED_FEATURES,
    }
    for key, expected in expected_counts.items():
        if row_counts.get(key) != expected:
            errors.append({"error_type": "unexpected_materialization_count", "key": key, "actual": row_counts.get(key), "expected": expected})

    main_view = runtime_manifest.get("main_view", {})
    if main_view.get("blocked_field_hits") != 0:
        errors.append({"error_type": "blocked_field_hits_present", "actual": main_view.get("blocked_field_hits")})
    if main_view.get("policy_violations") != 0:
        errors.append({"error_type": "policy_violations_present", "actual": main_view.get("policy_violations")})
    if runtime_manifest.get("group_summary", {}).get("bad_group_count") != 0:
        errors.append({"error_type": "bad_groups_present", "actual": runtime_manifest.get("group_summary", {})})

    for filename in ["validation_errors.jsonl", "blocked_field_hits.jsonl"]:
        count = line_count(runtime_audit_dir / filename)
        if count != 0:
            errors.append({"error_type": "non_empty_runtime_audit_file", "file": filename, "rows": count})
    if line_count(schema_stage_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "non_empty_schema_stage_validation_errors"})

    blocking_controls = [row for row in control_rows if parse_bool(row.get("blocks_metric_freeze", ""))]
    if blocking_controls:
        errors.append({"error_type": "control_blocks_metric_freeze", "rows": blocking_controls})
    required_controls = {
        "wrong_T_same_route",
        "shuffled_G_global",
        "shuffled_G_within_class_pair",
        "class_ablation_view",
        "q_e_diagnostic_view",
        "richer_G_e_feature_availability",
        "predicate_x_class_pair_shortcut_probe",
    }
    observed_controls = {row.get("control") for row in control_rows if parse_bool(row.get("ready", ""))}
    missing_controls = sorted(required_controls - observed_controls)
    if missing_controls:
        errors.append({"error_type": "missing_required_ready_controls", "controls": missing_controls})

    if source_inventory.get("status") != EXPECTED_SOURCE_INVENTORY_STATUS:
        errors.append({"error_type": "unexpected_source_inventory_status", "actual": source_inventory.get("status")})
    train_rows = source_inventory.get("decision", {}).get("train_point_multiview_main_rows")
    if train_rows != EXPECTED_TRAIN_MAIN_ROWS:
        errors.append({"error_type": "unexpected_train_main_rows", "actual": train_rows, "expected": EXPECTED_TRAIN_MAIN_ROWS})

    for key in ["metrics_run", "official_test_usage", "paper_metric_produced"]:
        if runtime_manifest.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "unexpected_runtime_boundary_true", "key": key})
    return errors


def model_view_contract() -> list[dict[str, Any]]:
    return [
        {
            "view_id": "M0_constant",
            "role": "sanity_baseline",
            "primary_input": "none",
            "allowed_blocks": "",
            "uses_class_labels": False,
            "uses_Q_e": False,
            "fit_policy": "train_prior_on_internal_train_only",
            "claim_use": "sanity_only",
        },
        {
            "view_id": "M1_predicate_only",
            "role": "semantic_baseline_no_class",
            "primary_input": "T_e.predicate_text + route_family",
            "allowed_blocks": "T_e",
            "uses_class_labels": False,
            "uses_Q_e": False,
            "fit_policy": "fit_internal_train_select_internal_dev_eval_official_validation_once",
            "claim_use": "shortcut_baseline_required",
        },
        {
            "view_id": "M2_geometry_only",
            "role": "predicate_independent_geometry_baseline",
            "primary_input": "G_e numeric hard-route features",
            "allowed_blocks": "G_e",
            "uses_class_labels": False,
            "uses_Q_e": False,
            "fit_policy": "fit_internal_train_select_internal_dev_eval_official_validation_once",
            "claim_use": "baseline",
        },
        {
            "view_id": "M3_T_plus_G_concat",
            "role": "plain_fusion_baseline",
            "primary_input": "T_e + G_e without explicit interaction terms",
            "allowed_blocks": "T_e,G_e",
            "uses_class_labels": False,
            "uses_Q_e": False,
            "fit_policy": "fit_internal_train_select_internal_dev_eval_official_validation_once",
            "claim_use": "baseline",
        },
        {
            "view_id": "M4_TxG_compatibility",
            "role": "primary_compatibility_model",
            "primary_input": "predicate-conditioned geometry interaction from T_e and G_e",
            "allowed_blocks": "T_e,G_e",
            "uses_class_labels": False,
            "uses_Q_e": False,
            "fit_policy": "fit_internal_train_select_internal_dev_eval_official_validation_once",
            "claim_use": "primary_hard_route_C_e",
        },
        {
            "view_id": "A1_class_ablation",
            "role": "diagnostic_ablation_only",
            "primary_input": "T_e class labels + predicate + G_e",
            "allowed_blocks": "T_e,G_e",
            "uses_class_labels": True,
            "uses_Q_e": False,
            "fit_policy": "diagnostic_only_report_after_primary",
            "claim_use": "shortcut_diagnostic_not_primary",
        },
        {
            "view_id": "D1_Q_e_diagnostic",
            "role": "observability_diagnostic_only",
            "primary_input": "Q_e evidence availability only",
            "allowed_blocks": "Q_e",
            "uses_class_labels": False,
            "uses_Q_e": True,
            "fit_policy": "diagnostic_only_no_p_obs_claim",
            "claim_use": "future_p_obs_boundary_check",
        },
    ]


def control_contract(shortcut_warnings: list[dict[str, str]], control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in control_rows:
        rows.append(
            {
                "control": row.get("control"),
                "ready": parse_bool(row.get("ready", "")),
                "requirement": "required_for_metric_review",
                "reason": row.get("reason", ""),
                "blocks_metric_freeze": parse_bool(row.get("blocks_metric_freeze", "")),
            }
        )
    for row in shortcut_warnings:
        rows.append(
            {
                "control": row.get("probe"),
                "ready": True,
                "requirement": "required_shortcut_baseline_or_claim_caveat",
                "reason": f"majority_accuracy={row.get('majority_accuracy')} risk={row.get('risk')}",
                "blocks_metric_freeze": False,
            }
        )
    return rows


def shortcut_baseline_contract(shortcut_table: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in shortcut_table:
        probe = row.get("probe")
        rows.append(
            {
                "probe": probe,
                "scope": row.get("scope"),
                "majority_accuracy_at_protocol_freeze": row.get("majority_accuracy"),
                "risk": row.get("risk"),
                "metric_protocol_role": (
                    "primary_required_baseline"
                    if probe == "primary_predicate_only"
                    else "hidden_or_ablation_shortcut_diagnostic"
                ),
                "claim_effect": (
                    "blocks_solved_support_contact_claim"
                    if row.get("blocks_solved_claim") == "True"
                    else "report_for_context"
                ),
            }
        )
    return rows


def metric_contract() -> dict[str, Any]:
    return {
        "target": "C_e",
        "route_family": "support_contact",
        "predicates": ["standing on", "lying on"],
        "candidate_rows": EXPECTED_ROWS,
        "paired_groups": EXPECTED_GROUPS,
        "official_validation_policy": "eval_only_no_fit_no_threshold_selection",
        "official_test_policy": "not_used",
        "primary_metric": "support_contact_AUROC",
        "secondary_metrics": [
            "support_contact_AUPRC",
            "balanced_accuracy",
            "macro_F1",
            "Brier_if_probabilistic",
            "paired_group_accuracy",
            "per_predicate_AUROC",
            "per_class_pair_diagnostic_when_cell_size_sufficient",
        ],
        "primary_comparison": "M4_TxG_compatibility_vs_M1_predicate_only_M2_geometry_only_M3_concat",
        "required_success_pattern": [
            "M4_TxG_compatibility improves over M1, M2, and M3",
            "wrong_T_same_route degrades relative to M4",
            "shuffled_G_global degrades relative to M4",
            "shuffled_G_within_class_pair degrades relative to M4",
            "class_ablation and predicate_x_class_pair results are reported as shortcut diagnostics, not primary evidence",
            "failure cases are interpreted as contact/pose/evidence limitations rather than solved-family success",
        ],
        "reporting_order": [
            "schema_and_shortcut_status",
            "primary_no_class_view_results",
            "control_collapse_results",
            "shortcut_diagnostic_results",
            "failure_analysis",
            "claim_boundary",
        ],
    }


def train_eval_policy(source_inventory: dict[str, Any]) -> dict[str, Any]:
    train_summary = source_inventory.get("inventory_summary", {}).get("train_point_multiview", {})
    return {
        "official_validation_eval_only": True,
        "official_validation_rows": EXPECTED_ROWS,
        "official_validation_feature_count": EXPECTED_FEATURES,
        "available_train_reference": {
            "rows": train_summary.get("rows"),
            "main_rows": train_summary.get("main_rows"),
            "diagnostic_rows": train_summary.get("diagnostic_rows"),
            "feature_count": train_summary.get("feature_count"),
            "predicate_counts": train_summary.get("predicate_counts", {}),
            "label_counts": train_summary.get("label_counts", {}),
        },
        "feature_parity_status": "needs_train_eval_alignment_audit",
        "reason": (
            "official validation hard-route view has 43 canonical G_e features, while the existing "
            "train point/multiview reference has a different 63-feature prefixed schema; training "
            "or hyperparameter selection must not happen on official validation."
        ),
        "allowed_next_actions": [
            "map train-side point/OBB/contact features to the official 43-feature canonical schema",
            "verify no official validation rows leak into train/dev",
            "freeze internal train/dev split before metric runner",
            "run metric only after train/eval feature parity validation passes",
        ],
        "blocked_actions": [
            "fit model on official validation rows",
            "select thresholds on official validation rows",
            "use class labels in primary no-class metric",
            "use Q_e in primary C_e metric",
            "claim p_obs or p_rel",
        ],
    }


def claim_boundary_contract(shortcut_warnings: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "enabled_after_runner_and_review": [
            "support_contact_hard_route_C_e_metric",
            "predicate_geometry_interaction_vs_baseline_comparison",
            "wrong_T_and_shuffled_G_control_analysis",
            "challenging_route_failure_analysis",
        ],
        "blocked": [
            "support_contact_solved_claim",
            "official_test_claim",
            "source_reranking_claim",
            "p_obs_claim",
            "p_rel_calibration_claim",
            "all_relation_type_generalization_claim",
            "paper_result_promotion_without_metric_review",
        ],
        "required_wording": [
            "`support_contact` is a hard compatibility route, not a solved family.",
            "Report `predicate x class-pair` shortcut risk next to any support/contact metric.",
            "If M4 improves but shortcut controls remain strong, claim interaction necessity rather than relation-family success.",
            "If M4 does not improve, interpret the result as evidence-quality or target-construction limitation.",
        ],
        "shortcut_warnings": shortcut_warnings,
    }


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "selected_path": SELECTED_PATH,
        "purpose": "Audit and materialize train/dev support-contact features aligned to the official 43-feature hard-route schema before metric execution.",
        "must_do": [
            "create a canonical train/eval G_e feature map",
            "verify internal train/dev rows have no official validation leakage",
            "verify all M1-M4 views can be built without class labels or Q_e",
            "verify class-ablation and Q_e views remain diagnostic-only",
            "write runner-ready input contract if alignment passes",
        ],
        "must_not_do": [
            "do not train on official validation",
            "do not run official test",
            "do not run metric before feature alignment passes",
            "do not promote support_contact as solved",
        ],
    }


def build_report(summary: dict[str, Any]) -> str:
    return f"""# Support/Contact Hard Route Metric Protocol Freeze

## Status

```text
artifact_root = {summary['output_artifacts']['artifact_root']}/
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Purpose

이 단계는 richer support/contact hard route metric을 실행하기 전에 metric, model view,
control, shortcut baseline, train/eval policy, claim boundary를 고정한 단계다.
Metric은 실행하지 않았고 official test도 사용하지 않았다.

## Frozen Metric

- target: `C_e`
- route family: `support_contact`
- predicates: `standing on`, `lying on`
- official validation rows: `{summary['row_counts']['official_validation_rows']}`
- paired groups: `{summary['row_counts']['paired_groups']}`
- primary metric: `support_contact_AUROC`
- primary comparison: `M4_TxG_compatibility` vs `M1_predicate_only`, `M2_geometry_only`, `M3_concat`

## Required Controls

- wrong-`T` same-route
- shuffled-`G` global
- shuffled-`G` within class-pair
- predicate-only shortcut baseline
- `predicate x class-pair` shortcut diagnostic
- class-ablation diagnostic
- `Q_e` diagnostic, not primary

## Key Decision

Official validation은 eval-only다. 현재 official hard-route view는 `43`개 canonical `G_e`
features를 갖고, 기존 train point/multiview reference는 다른 prefixed `63` feature schema를
갖는다. 따라서 metric runner 전에 train/eval feature alignment audit가 필요하다.

## Boundary

- no metric
- no official test
- no paper result promotion
- no source reranking
- no `p_obs` / `p_rel` claim
- no solved `support_contact` claim

## Next

```text
{summary['next_todo']}
```
"""


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    schema_summary = read_json(args.schema_stage_dir / "summary.json")
    runtime_manifest = read_json(args.runtime_audit_dir / "audit_manifest.json")
    materialization_manifest = read_json(args.materialization_dir / "row_manifest.json")
    source_inventory = read_json(args.source_inventory_dir / "summary.json")
    shortcut_warnings = read_csv(args.schema_stage_dir / "shortcut_warnings.csv")
    shortcut_table = read_csv(args.schema_stage_dir / "shortcut_risk_table.csv")
    control_rows = read_csv(args.schema_stage_dir / "control_readiness.csv")

    validation_errors = validate_inputs(
        schema_summary=schema_summary,
        runtime_manifest=runtime_manifest,
        materialization_manifest=materialization_manifest,
        source_inventory=source_inventory,
        runtime_audit_dir=args.runtime_audit_dir,
        schema_stage_dir=args.schema_stage_dir,
        control_rows=control_rows,
    )

    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    selected_path = SELECTED_PATH if not validation_errors else "blocked_fix_protocol_inputs"
    next_todo = NEXT_TODO if not validation_errors else "fix_support_contact_metric_protocol_inputs"

    row_counts = {
        "official_validation_rows": EXPECTED_ROWS,
        "paired_groups": EXPECTED_GROUPS,
        "feature_count": EXPECTED_FEATURES,
        "label_0": runtime_manifest.get("main_view", {}).get("label_0"),
        "label_1": runtime_manifest.get("main_view", {}).get("label_1"),
        "standing_on": runtime_manifest.get("main_view", {}).get("standing_on"),
        "lying_on": runtime_manifest.get("main_view", {}).get("lying_on"),
    }
    train_policy = train_eval_policy(source_inventory)

    output_artifacts = {
        "artifact_root": rel_path(args.output_dir),
        "summary": rel_path(args.output_dir / "summary.json"),
        "metric_contract": rel_path(args.output_dir / "support_contact_metric_contract.json"),
        "model_view_contract": rel_path(args.output_dir / "model_view_contract.csv"),
        "control_contract": rel_path(args.output_dir / "control_contract.csv"),
        "shortcut_baseline_contract": rel_path(args.output_dir / "shortcut_baseline_contract.csv"),
        "train_eval_policy": rel_path(args.output_dir / "train_eval_policy.json"),
        "claim_boundary_contract": rel_path(args.output_dir / "claim_boundary_contract.json"),
        "next_contract": rel_path(args.output_dir / "next_contract.json"),
        "report": rel_path(args.output_dir / "report.md"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "row_counts": row_counts,
        "shortcut_warnings": len(shortcut_warnings),
        "high_shortcut_warnings": sum(1 for row in shortcut_warnings if row.get("risk") == "high"),
        "controls_ready": sum(1 for row in control_rows if parse_bool(row.get("ready", ""))),
        "controls_total": len(control_rows),
        "train_eval_feature_parity": train_policy["feature_parity_status"],
        "decision": {
            "metric_protocol_frozen": not bool(validation_errors),
            "metric_runner_next": False,
            "train_eval_alignment_next": not bool(validation_errors),
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "support_contact_solved_claim_allowed": False,
            "source_reranking_enabled": False,
            "p_obs_p_rel_enabled": False,
        },
        "input_artifacts": {
            "schema_stage_summary": rel_path(args.schema_stage_dir / "summary.json"),
            "runtime_audit_manifest": rel_path(args.runtime_audit_dir / "audit_manifest.json"),
            "materialization_manifest": rel_path(args.materialization_dir / "row_manifest.json"),
            "source_inventory_summary": rel_path(args.source_inventory_dir / "summary.json"),
        },
        "output_artifacts": output_artifacts,
    }

    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "support_contact_metric_contract.json", metric_contract())
    write_csv(args.output_dir / "model_view_contract.csv", model_view_contract())
    write_csv(args.output_dir / "control_contract.csv", control_contract(shortcut_warnings, control_rows))
    write_csv(args.output_dir / "shortcut_baseline_contract.csv", shortcut_baseline_contract(shortcut_table))
    write_json(args.output_dir / "train_eval_policy.json", train_policy)
    write_json(args.output_dir / "claim_boundary_contract.json", claim_boundary_contract(shortcut_warnings))
    write_json(args.output_dir / "next_contract.json", next_contract())
    (args.output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
