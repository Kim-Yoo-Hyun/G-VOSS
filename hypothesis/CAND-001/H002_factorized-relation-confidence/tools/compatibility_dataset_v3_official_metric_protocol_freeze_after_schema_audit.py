#!/usr/bin/env python3
"""Freeze the H002 official validation metric protocol after schema audit."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCHEMA_STAGE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation"
)
DEFAULT_RUNTIME_AUDIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_schema_audit/latest"
DEFAULT_MATERIALIZATION_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_materialization/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit"

EXPECTED_PREV_STATUS = (
    "h002_compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation_ready_with_caveats"
)
EXPECTED_PREV_NEXT = "compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit"
EXPECTED_RUNTIME_STATUS = "h002_official_materialization_schema_audit_ready_with_shortcut_warnings"
EXPECTED_ROW_COUNT = 23062

SCHEMA_VERSION = "h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_v1"
STATUS_READY = "h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_input_errors"
SELECTED_PATH = "official_metric_protocol_frozen_select_official_metric_runner"
NEXT_TODO = "compatibility_dataset_v3_official_metric_runner_after_protocol_freeze"

FAMILY_ROLES = {
    "relative_horizontal": {
        "role": "primary_frame_aware_compatibility_route",
        "claim_status": "primary_if_family_metric_and_controls_pass",
        "metric_weighting_note": "large_family_report_per_family_and_macro_to_prevent_dominance",
    },
    "relative_vertical": {
        "role": "primary_signed_geometry_compatibility_route",
        "claim_status": "primary_if_family_metric_and_controls_pass",
        "metric_weighting_note": "small_balanced_family_report_per_family_and_macro",
    },
    "size_relative": {
        "role": "primary_size_compatibility_route",
        "claim_status": "primary_if_family_metric_and_controls_pass",
        "metric_weighting_note": "small_balanced_family_report_per_family_and_macro",
    },
    "support_contact": {
        "role": "challenging_support_contact_route",
        "claim_status": "diagnostic_challenging_not_solved",
        "metric_weighting_note": "report_but_do_not_claim_solved_due_to_predicate_class_pair_shortcut_caveat",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-stage-dir", type=Path, default=DEFAULT_SCHEMA_STAGE_DIR)
    parser.add_argument("--runtime-audit-dir", type=Path, default=DEFAULT_RUNTIME_AUDIT_DIR)
    parser.add_argument("--materialization-dir", type=Path, default=DEFAULT_MATERIALIZATION_DIR)
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def validate_inputs(
    *,
    schema_summary: dict[str, Any],
    runtime_manifest: dict[str, Any],
    row_manifest: dict[str, Any],
    runtime_audit_dir: Path,
    high_shortcuts: list[dict[str, str]],
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
    if runtime_manifest.get("next_todo") != EXPECTED_PREV_NEXT:
        errors.append({"error_type": "unexpected_runtime_audit_next_todo", "actual": runtime_manifest.get("next_todo")})
    if runtime_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_audit_validation_errors", "actual": runtime_manifest.get("validation_errors")})

    for filename in ["validation_errors.jsonl", "schema_violations.jsonl", "blocked_field_hits.jsonl"]:
        count = line_count(runtime_audit_dir / filename)
        if count != 0:
            errors.append({"error_type": "non_empty_runtime_audit_file", "file": filename, "rows": count})

    row_counts = row_manifest.get("row_counts", {})
    for key in ["candidate_rows", "model_safe_view", "hidden_manifest"]:
        if row_counts.get(key) != EXPECTED_ROW_COUNT:
            errors.append({"error_type": "unexpected_materialized_row_count", "key": key, "actual": row_counts.get(key)})

    blocking_shortcuts = [row for row in high_shortcuts if parse_bool(row.get("blocks_metric_freeze", ""))]
    if blocking_shortcuts:
        errors.append({"error_type": "shortcut_blocks_metric_freeze", "rows": blocking_shortcuts})

    blocking_controls = [row for row in control_rows if parse_bool(row.get("blocks_metric_freeze", ""))]
    if blocking_controls:
        errors.append({"error_type": "control_blocks_metric_freeze", "rows": blocking_controls})

    required_families = set(FAMILY_ROLES)
    observed_families = {row.get("family") for row in control_rows}
    missing = sorted(required_families - observed_families)
    if missing:
        errors.append({"error_type": "missing_control_readiness_family", "families": missing})

    return errors


def model_view_contract() -> list[dict[str, Any]]:
    return [
        {
            "view_id": "M0_constant",
            "role": "sanity_baseline",
            "allowed_blocks": [],
            "fit_policy": "majority_prior_fit_on_internal_train_only",
            "official_validation_use": "eval_only",
            "claim_use": "sanity_only",
        },
        {
            "view_id": "M1_T_semantic_only",
            "role": "semantic_content_baseline",
            "allowed_blocks": ["T_e"],
            "feature_policy": "predicate_label_route_family_subject_object_class_only",
            "fit_policy": "fit_on_internal_train_select_on_internal_dev_eval_on_official_validation",
            "official_validation_use": "eval_only",
            "claim_use": "baseline",
        },
        {
            "view_id": "M2_G_geometry_only",
            "role": "predicate_independent_geometry_baseline",
            "allowed_blocks": ["G_e"],
            "feature_policy": "numeric_geometry_vector_and_availability_mask_only",
            "fit_policy": "fit_on_internal_train_select_on_internal_dev_eval_on_official_validation",
            "official_validation_use": "eval_only",
            "claim_use": "baseline",
        },
        {
            "view_id": "M3_T_plus_G_concat",
            "role": "naive_fusion_baseline",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "plain_concatenation_without_explicit_TxG_interaction_terms",
            "fit_policy": "fit_on_internal_train_select_on_internal_dev_eval_on_official_validation",
            "official_validation_use": "eval_only",
            "claim_use": "baseline",
        },
        {
            "view_id": "M4_TxG_compatibility",
            "role": "primary_compatibility_model",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "predicate_or_route_conditioned_geometry_interaction_terms_allowed",
            "fit_policy": "fit_on_internal_train_select_on_internal_dev_eval_once_on_official_validation",
            "official_validation_use": "eval_only",
            "claim_use": "primary_C_e_evidence",
        },
        {
            "view_id": "C1_wrong_T_within_route",
            "role": "counterfactual_control",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "reuse_M4_with_wrong_predicate_or_wrong_T_e_within_route_when_possible",
            "fit_policy": "no_refit_control_on_official_validation_predictions",
            "official_validation_use": "eval_only",
            "claim_use": "control_must_degrade_or_invert",
        },
        {
            "view_id": "C2_wrong_T_across_route",
            "role": "counterfactual_control",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "reuse_M4_with_wrong_T_e_across_route_for_stress_test",
            "fit_policy": "no_refit_control_on_official_validation_predictions",
            "official_validation_use": "eval_only",
            "claim_use": "control_must_degrade",
        },
        {
            "view_id": "C3_shuffled_G_global",
            "role": "counterfactual_control",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "reuse_M4_with_G_e_shuffled_globally",
            "fit_policy": "no_refit_control_on_official_validation_predictions",
            "official_validation_use": "eval_only",
            "claim_use": "control_must_degrade_toward_chance",
        },
        {
            "view_id": "C4_shuffled_G_within_family",
            "role": "counterfactual_control",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "reuse_M4_with_G_e_shuffled_within_route_family",
            "fit_policy": "no_refit_control_on_official_validation_predictions",
            "official_validation_use": "eval_only",
            "claim_use": "control_must_degrade_toward_chance",
        },
        {
            "view_id": "C5_subject_object_swap",
            "role": "route_specific_control",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "swap_directed_pair_geometry_where_predicate_is_directional",
            "fit_policy": "no_refit_control_on_official_validation_predictions",
            "official_validation_use": "eval_only",
            "claim_use": "directionality_control",
        },
        {
            "view_id": "C6_sign_flip",
            "role": "route_specific_control",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "flip_signed_geometry_for_vertical_size_or_horizontal_routes_when_applicable",
            "fit_policy": "no_refit_control_on_official_validation_predictions",
            "official_validation_use": "eval_only",
            "claim_use": "signed_geometry_control",
        },
        {
            "view_id": "C7_horizontal_frame_swap",
            "role": "route_specific_control",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "frame_or_axis_swap_for_relative_horizontal_only",
            "fit_policy": "no_refit_control_on_official_validation_predictions",
            "official_validation_use": "eval_only",
            "claim_use": "relative_horizontal_frame_control",
        },
        {
            "view_id": "D1_Z_source_confidence_diagnostic",
            "role": "diagnostic_only_not_main_C_e",
            "allowed_blocks": ["Z_e"],
            "feature_policy": "source_score_rank_band_source_id_only",
            "fit_policy": "optional_diagnostic_only_after_primary_metric",
            "official_validation_use": "diagnostic_only",
            "claim_use": "source_shortcut_check_only",
        },
        {
            "view_id": "D2_Q_observability_diagnostic",
            "role": "diagnostic_only_not_main_C_e",
            "allowed_blocks": ["Q_e"],
            "feature_policy": "evidence_availability_and_observability_quality_only",
            "fit_policy": "optional_diagnostic_only_after_primary_metric",
            "official_validation_use": "diagnostic_only",
            "claim_use": "future_p_obs_check_only",
        },
    ]


def official_metric_contract() -> dict[str, Any]:
    return {
        "target": "C_e",
        "target_field": "target_y",
        "candidate_pool": "official_validation_materialized_candidates",
        "candidate_rows": EXPECTED_ROW_COUNT,
        "official_validation_policy": "eval_only_no_fit_no_threshold_selection",
        "official_test_policy": "not_used_until_single_frozen_final_protocol_exists",
        "fit_policy": [
            "fit trainable views on internal candidate-pool train split only",
            "select hyperparameters or thresholds on internal candidate-pool dev split only",
            "do not fit, select, tune, or repair after seeing official validation metrics",
            "official validation is evaluated once per frozen view/control",
        ],
        "primary_metric": "macro_family_AUROC",
        "secondary_metrics": [
            "weighted_family_AUROC",
            "overall_AUROC",
            "macro_family_AUPRC",
            "balanced_accuracy",
            "macro_F1",
            "Brier",
            "NLL_if_probabilistic",
        ],
        "required_breakdowns": [
            "per_family",
            "per_predicate",
            "macro_family",
            "weighted_family",
            "overall_secondary",
            "control_by_family",
            "support_contact_challenging_route_separate_row",
        ],
        "primary_comparison": "M4_TxG_compatibility_vs_M1_T_semantic_only_M2_G_geometry_only_M3_T_plus_G_concat",
        "primary_success_pattern": [
            "M4 improves macro_family_AUROC over M1, M2, and M3",
            "improvement is not driven only by relative_horizontal",
            "wrong_T and shuffled_G controls degrade relative to M4",
            "support_contact is reported as challenging and not used as solved-family evidence",
        ],
        "reporting_guardrails": [
            "do not promote aggregate-only results",
            "do not claim solved support/contact from this protocol",
            "do not include Z_e in main C_e",
            "do not include Q_e in main C_e",
            "do not use H001 p_geom_valid as the main G_e",
            "do not report paper result before leakage/control review",
        ],
    }


def family_metric_plan(label_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in label_rows:
        family = row.get("family")
        if family == "ALL":
            continue
        role = FAMILY_ROLES.get(family, {})
        rows.append(
            {
                "family": family,
                "rows": int(float(row.get("rows", 0))),
                "label_0": int(float(row.get("label_0", 0))),
                "label_1": int(float(row.get("label_1", 0))),
                "positive_rate": float(row.get("positive_rate", 0.0)),
                "majority_rate": float(row.get("majority_rate", 0.0)),
                "dataset_weight": float(row.get("dataset_weight", 0.0)),
                "role": role.get("role", "unknown"),
                "claim_status": role.get("claim_status", "unknown"),
                "metric_requirement": "per_family_AUROC_and_AUPRC_required",
                "aggregation_policy": role.get("metric_weighting_note", ""),
            }
        )
    return rows


def control_contract(control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in control_rows:
        ready = parse_bool(row.get("ready", ""))
        control = row.get("control", "")
        family = row.get("family", "")
        if control == "horizontal_frame_swap" and family != "relative_horizontal":
            requirement = "not_applicable"
        elif ready:
            requirement = "required_report"
        else:
            requirement = "must_explain_if_unavailable"
        rows.append(
            {
                "family": family,
                "control": control,
                "ready": ready,
                "requirement": requirement,
                "blocks_metric_freeze": parse_bool(row.get("blocks_metric_freeze", "")),
                "sampled_g_e_features": row.get("sampled_g_e_features", ""),
            }
        )
    return rows


def claim_boundary_contract(high_shortcuts: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "enabled": [
            "official_validation_C_e_mechanism_metric_after_runner_and_review",
            "family_wise_compatibility_comparison",
            "wrong_T_and_shuffled_G_control_analysis",
        ],
        "blocked_until_later_protocol": [
            "official_test_metric",
            "paper_level_result_promotion_without_metric_review",
            "calibrated_p_rel_claim",
            "p_obs_or_abstention_claim",
            "source_reranking_or_recall_tradeoff_claim",
            "all_relation_type_generalization_claim",
            "solved_support_contact_claim",
        ],
        "support_contact_caveat": high_shortcuts,
        "required_writing": [
            "`support_contact` is a challenging diagnostic route in this protocol",
            "primary table must show family-wise metrics before any aggregate",
            "macro-family result is primary; overall result is secondary",
            "`Z_e` source confidence is not part of main `C_e`",
        ],
    }


def next_runner_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "docker_service_to_add": "h002-official-metric-runner",
        "runtime_output_root": "experiments/H002_compatibility_routing/official_evaluation/latest/",
        "required_inputs": [
            "experiments/H002_compatibility_routing/official_materialization/latest/model_safe_view.jsonl",
            "experiments/H002_compatibility_routing/official_materialization/latest/hidden_manifest.jsonl",
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/model_view_contract.json",
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/official_metric_contract.json",
        ],
        "required_outputs": [
            "eval_manifest.json",
            "model_view_manifest.json",
            "family_metrics.csv",
            "predicate_metrics.csv",
            "aggregate_metrics.csv",
            "control_metrics.csv",
            "prediction_scores.jsonl",
            "leakage_audit.csv",
            "validation_errors.jsonl",
        ],
        "must_not_do": [
            "fit_or_tune_on_official_validation",
            "use_official_test",
            "include_hidden_fields_as_features",
            "include_Z_e_in_main_C_e",
            "include_Q_e_in_main_C_e",
        ],
    }


def report_text(
    *,
    status: str,
    validation_errors: list[dict[str, Any]],
    output_dir: Path,
    label_rows: list[dict[str, str]],
    high_shortcuts: list[dict[str, str]],
) -> str:
    lines = [
        "# H002 Official Metric Protocol Freeze After Schema Audit",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {rel_path(output_dir)}/",
        f"status = {status}",
        f"selected_path = {SELECTED_PATH if not validation_errors else 'blocked_fix_input_errors'}",
        f"validation_errors = {len(validation_errors)}",
        f"next_todo = {NEXT_TODO if not validation_errors else 'fix_official_metric_protocol_inputs'}",
        "```",
        "",
        "## Purpose",
        "",
        "Official validation metric을 실행하기 전에 metric, model view, control, aggregation,",
        "claim boundary를 고정했다. 이 단계는 protocol freeze이며 metric runner가 아니다.",
        "",
        "중요한 원칙은 official validation rows를 `eval-only`로 사용한다는 점이다.",
        "Trainable view의 fit, threshold, model selection은 internal train/dev에서 끝나야 하며,",
        "official validation metric을 본 뒤 protocol을 바꾸면 안 된다.",
        "",
        "## Metric Contract",
        "",
        "- target: `C_e`",
        "- primary metric: `macro_family_AUROC`",
        "- secondary: weighted-family AUROC, overall AUROC, AUPRC, balanced accuracy, macro-F1, Brier",
        "- main `C_e` input: `T_e`, `G_e` only",
        "- excluded from main `C_e`: `Z_e`, `Q_e`, H001 `p_geom_valid`, hidden construction fields",
        "- official test: not used",
        "- paper result: not promoted until metric review and claim-lock pass",
        "",
        "## Family Plan",
        "",
        "| Family | Rows | Label 0 | Label 1 | Role | Claim status |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in label_rows:
        if row.get("family") == "ALL":
            continue
        role = FAMILY_ROLES.get(row.get("family", ""), {})
        lines.append(
            f"| `{row.get('family')}` | {int(float(row.get('rows', 0)))} | "
            f"{int(float(row.get('label_0', 0)))} | {int(float(row.get('label_1', 0)))} | "
            f"{role.get('role', 'unknown')} | {role.get('claim_status', 'unknown')} |"
        )

    lines.extend(
        [
            "",
            "## Required Controls",
            "",
            "- wrong-`T` within route",
            "- wrong-`T` across route",
            "- shuffled-`G` global",
            "- shuffled-`G` within family",
            "- subject/object swap",
            "- signed-geometry flip where applicable",
            "- horizontal frame/axis swap for `relative_horizontal`",
            "",
            "## Caveat",
            "",
            f"- high shortcut warnings: `{len(high_shortcuts)}`",
            "- `support_contact` has a strong `predicate_x_class_pair` shortcut warning.",
            "- Therefore `support_contact` can be reported as a challenging route, but not as solved.",
            "",
            "## Boundary",
            "",
            "- No official metric was computed.",
            "- Official test was not used.",
            "- No paper-level result was promoted.",
            "- `p_rel` / `p_obs` remain disabled.",
            "",
            "## Next",
            "",
            "```text",
            NEXT_TODO,
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    schema_summary = read_json(args.schema_stage_dir / "summary.json")
    runtime_manifest = read_json(args.runtime_audit_dir / "audit_manifest.json")
    row_manifest = read_json(args.materialization_dir / "row_manifest.json")
    high_shortcuts = read_csv(args.runtime_audit_dir / "high_shortcut_warnings.csv")
    control_rows = read_csv(args.runtime_audit_dir / "control_readiness.csv")
    label_rows = read_csv(args.runtime_audit_dir / "label_balance.csv")

    validation_errors = validate_inputs(
        schema_summary=schema_summary,
        runtime_manifest=runtime_manifest,
        row_manifest=row_manifest,
        runtime_audit_dir=args.runtime_audit_dir,
        high_shortcuts=high_shortcuts,
        control_rows=control_rows,
    )

    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    selected_path = SELECTED_PATH if not validation_errors else "blocked_fix_input_errors"
    next_todo = NEXT_TODO if not validation_errors else "fix_official_metric_protocol_inputs"

    family_plan = family_metric_plan(label_rows)
    controls = control_contract(control_rows)
    models = model_view_contract()
    metric = official_metric_contract()
    boundary = claim_boundary_contract(high_shortcuts)
    runner_contract = next_runner_contract()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "input_artifacts": {
            "schema_stage_summary": rel_path(args.schema_stage_dir / "summary.json"),
            "runtime_audit_manifest": rel_path(args.runtime_audit_dir / "audit_manifest.json"),
            "materialization_manifest": rel_path(args.materialization_dir / "row_manifest.json"),
        },
        "output_artifacts": {
            "official_metric_contract": rel_path(args.output_dir / "official_metric_contract.json"),
            "model_view_contract": rel_path(args.output_dir / "model_view_contract.json"),
            "family_metric_plan": rel_path(args.output_dir / "family_metric_plan.csv"),
            "control_contract": rel_path(args.output_dir / "control_contract.csv"),
            "claim_boundary_contract": rel_path(args.output_dir / "claim_boundary_contract.json"),
            "next_runner_contract": rel_path(args.output_dir / "next_runner_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "boundary": {
            "official_validation_metric_produced": False,
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "main_C_e_allowed_blocks": ["T_e", "G_e"],
            "z_e_excluded_from_main_c_e": True,
            "q_e_excluded_from_main_c_e": True,
            "p_rel_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "support_contact_claim": "challenging_not_solved",
            "family_macro_metric_primary": True,
            "overall_metric_secondary": True,
        },
        "audit_caveats": {
            "high_shortcut_warnings": len(high_shortcuts),
            "support_contact_predicate_x_class_pair_shortcut": any(
                row.get("family") == "support_contact" and row.get("probe") == "predicate_x_class_pair"
                for row in high_shortcuts
            ),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "official_metric_contract.json", metric)
    write_json(args.output_dir / "model_view_contract.json", models)
    write_csv(args.output_dir / "family_metric_plan.csv", family_plan)
    write_csv(args.output_dir / "control_contract.csv", controls)
    write_json(args.output_dir / "claim_boundary_contract.json", boundary)
    write_json(args.output_dir / "next_runner_contract.json", runner_contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    (args.output_dir / "report.md").write_text(
        report_text(
            status=status,
            validation_errors=validation_errors,
            output_dir=args.output_dir,
            label_rows=label_rows,
            high_shortcuts=high_shortcuts,
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
