#!/usr/bin/env python3
"""Plan source-wide materialization for H002 source reranking."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INVENTORY_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan"
)
DEFAULT_OUTPUT_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory"
)
RUNTIME_OUTPUT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_materialization/latest"

EXPECTED_INVENTORY_STATUS = "h002_compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan_ready"
EXPECTED_INVENTORY_NEXT = "compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory_v1"
STATUS_READY = "h002_compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory_input_errors"
SELECTED_PATH = "source_reranking_materialization_protocol_ready_select_docker_implementation"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", type=Path, default=DEFAULT_INVENTORY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
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
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def validate_inputs(summary: dict[str, Any], inventory_dir: Path, family_rows: list[dict[str, str]], metric_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INVENTORY_STATUS:
        errors.append({"error_type": "unexpected_inventory_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INVENTORY_NEXT:
        errors.append({"error_type": "unexpected_inventory_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "inventory_validation_errors", "actual": summary.get("validation_errors")})
    if line_count(inventory_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "inventory_validation_error_file_not_empty"})

    decision = summary.get("decision", {})
    expected = {
        "S2_source_x_Ce_metric_ready_now": False,
        "recall_at_k_S0_source_score_computable": True,
        "source_prediction_join_keys_available": True,
        "source_score_and_rank_available": True,
        "official_test_usage": False,
        "metrics_run": False,
    }
    for key, value in expected.items():
        if decision.get(key) is not value:
            errors.append({"error_type": "unexpected_inventory_decision", "key": key, "actual": decision.get(key), "expected": value})

    if not family_rows:
        errors.append({"error_type": "missing_source_family_inventory"})
    if not metric_rows:
        errors.append({"error_type": "missing_metric_readiness"})

    source_ids = sorted({row.get("source_id") for row in family_rows if row.get("source_id")})
    if source_ids != ["open3dsg_recovery_relaxed_views_min2", "vlsat_full_validation"]:
        errors.append({"error_type": "unexpected_source_ids", "actual": source_ids})

    if not all(row.get("Recall@K_S2_source_x_Ce") == "blocked_needs_source_wide_Ce_materialization" for row in metric_rows):
        errors.append({"error_type": "expected_s2_source_x_ce_to_be_blocked_before_materialization"})
    return errors


def materialization_scope_rows(family_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in family_rows:
        family = row.get("route_family", "")
        if family == "support_contact":
            inclusion = "materialize_diagnostic_only_exclude_from_success"
            materialization_role = "diagnostic_failure_taxonomy"
        elif family == "relative_horizontal":
            inclusion = "materialize_caveated_separate_table"
            materialization_role = "caveated_frame_aware_bridge"
        elif family in {"relative_vertical", "size_relative"}:
            inclusion = "materialize_primary_bridge"
            materialization_role = "primary_bridge"
        elif family == "proximity":
            inclusion = "materialize_optional_geometry_control"
            materialization_role = "geometry_only_control"
        else:
            inclusion = "defer"
            materialization_role = "future"
        rows.append(
            {
                "source_id": row.get("source_id"),
                "route_family": family,
                "source_prediction_rows": row.get("source_prediction_rows"),
                "materialization_role": materialization_role,
                "inclusion_policy": inclusion,
                "current_h2_ce_direct_join_rate": row.get("h2_ce_direct_join_rate"),
                "needs_source_wide_Ce": row.get("source_wide_Ce_required"),
                "recall_at_k_s0_ready": row.get("recall_at_k_computable_now"),
                "h001_violation_ready": row.get("h001_violation_at_k_computable_now"),
            }
        )
    return rows


def output_manifest_rows() -> list[dict[str, Any]]:
    return [
        {
            "artifact": "source_candidates.jsonl",
            "runtime_path": rel_path(RUNTIME_OUTPUT_DIR / "source_candidates.jsonl"),
            "role": "full source prediction universe with row identity and non-feature metadata",
            "contains_model_features": "false",
            "contains_hidden_metric_labels": "false",
        },
        {
            "artifact": "model_safe_ce_view.jsonl",
            "runtime_path": rel_path(RUNTIME_OUTPUT_DIR / "model_safe_ce_view.jsonl"),
            "role": "T_e + G_e only view for C_e scoring",
            "contains_model_features": "true",
            "contains_hidden_metric_labels": "false",
        },
        {
            "artifact": "model_safe_geometry_only_view.jsonl",
            "runtime_path": rel_path(RUNTIME_OUTPUT_DIR / "model_safe_geometry_only_view.jsonl"),
            "role": "G_e only diagnostic/control view",
            "contains_model_features": "true",
            "contains_hidden_metric_labels": "false",
        },
        {
            "artifact": "source_rank_view.jsonl",
            "runtime_path": rel_path(RUNTIME_OUTPUT_DIR / "source_rank_view.jsonl"),
            "role": "Z_e source score/rank view for reranking stage only",
            "contains_model_features": "reranking_only",
            "contains_hidden_metric_labels": "false",
        },
        {
            "artifact": "hidden_metric_manifest.jsonl",
            "runtime_path": rel_path(RUNTIME_OUTPUT_DIR / "hidden_metric_manifest.jsonl"),
            "role": "GT match, violation labels, metric-only fields",
            "contains_model_features": "false",
            "contains_hidden_metric_labels": "true",
        },
        {
            "artifact": "row_manifest.json",
            "runtime_path": rel_path(RUNTIME_OUTPUT_DIR / "row_manifest.json"),
            "role": "row counts, family counts, input provenance, policy flags",
            "contains_model_features": "false",
            "contains_hidden_metric_labels": "false",
        },
        {
            "artifact": "validation_errors.jsonl",
            "runtime_path": rel_path(RUNTIME_OUTPUT_DIR / "validation_errors.jsonl"),
            "role": "runtime materialization validation errors",
            "contains_model_features": "false",
            "contains_hidden_metric_labels": "false",
        },
    ]


def model_safe_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "view": "model_safe_ce_view",
            "block": "row_identity_not_features",
            "fields": "candidate_id; source_id; prediction_id; scan_id; subject_id; object_id; predicate_label; route_family",
            "feature_use": "join_and_group_only",
            "allowed_for_Ce": "false",
        },
        {
            "view": "model_safe_ce_view",
            "block": "T_e",
            "fields": "predicate_text; predicate_label; route_family; subject_class_label; object_class_label; optional predicate family token",
            "feature_use": "semantic content",
            "allowed_for_Ce": "true",
        },
        {
            "view": "model_safe_ce_view",
            "block": "G_e",
            "fields": "family-specific predicate-independent geometry feature vector and mask",
            "feature_use": "geometry evidence",
            "allowed_for_Ce": "true",
        },
        {
            "view": "model_safe_ce_view",
            "block": "Q_e",
            "fields": "geometry availability and quality flags",
            "feature_use": "diagnostic only",
            "allowed_for_Ce": "false",
        },
        {
            "view": "source_rank_view",
            "block": "Z_e",
            "fields": "source ranking_score; predicate_score; predicate_rank_for_pair; semantic_rank_in_subgraph; source_id",
            "feature_use": "reranking stage only",
            "allowed_for_Ce": "false",
        },
        {
            "view": "hidden_metric_manifest",
            "block": "metric_only",
            "fields": "gt_match; gt_family_match; violation_status; p_geom_valid_if_available; selected_count/K labels",
            "feature_use": "metric computation only",
            "allowed_for_Ce": "false",
        },
    ]


def geometry_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "route_family": "relative_vertical",
            "source": "H002 OBB-derived G_e preferred; H001 p_geom_valid only metric/control hidden field",
            "required_Ge": "center_delta_z; normalized_center_delta_z; subject/object top/bottom; sign/order features",
            "violation_label_source": "H001 verification available for downstream Violation@K",
            "caveat": "do not use p_geom_valid inside C_e",
        },
        {
            "route_family": "size_relative",
            "source": "H002 OBB-derived G_e required",
            "required_Ge": "subject/object extents; volume/area ratios; signed size comparison features",
            "violation_label_source": "needs H002 materialized size-consistency labels; H001 verification absent",
            "caveat": "source-wide materialization required before S2 metric",
        },
        {
            "route_family": "relative_horizontal",
            "source": "H002 frame-aware OBB-derived G_e required",
            "required_Ge": "dx/dy; axis signs; frame token; horizontal separation; endpoint-swap controls",
            "violation_label_source": "needs H002 frame-aware labels/controls; H001 verification absent",
            "caveat": "report as caveated frame-aware route only",
        },
        {
            "route_family": "proximity",
            "source": "H002 or H001 geometry-only route control",
            "required_Ge": "3D/XY distance; normalized distance; object scale; optional p_geom_valid hidden control",
            "violation_label_source": "H001 geometry available",
            "caveat": "not T_e x G_e interaction evidence",
        },
        {
            "route_family": "support_contact",
            "source": "H001/H002 diagnostic only",
            "required_Ge": "contact/gap/overlap/pose features if materialized",
            "violation_label_source": "H001 geometry available but success aggregation blocked",
            "caveat": "diagnostic/failure taxonomy only",
        },
    ]


def score_materialization_rows() -> list[dict[str, Any]]:
    return [
        {
            "score_id": "S0_source_score",
            "materialization_source": "source_rank_view.Z_e",
            "requires_Ce": "false",
            "ready_after_materialization": "true",
            "notes": "baseline source ranking",
        },
        {
            "score_id": "S1_Ce_only",
            "materialization_source": "model_safe_ce_view through frozen C_e scorer",
            "requires_Ce": "true",
            "ready_after_materialization": "true_if_Ce_scorer_applied",
            "notes": "diagnostic compatibility ranking",
        },
        {
            "score_id": "S2_source_x_Ce",
            "materialization_source": "source_rank_view.Z_e combined with C_e score after scoring",
            "requires_Ce": "true",
            "ready_after_materialization": "true_if_score_normalization_frozen",
            "notes": "primary bridge candidate; Z_e not inside C_e",
        },
        {
            "score_id": "S3_source_plus_lambda_Ce",
            "materialization_source": "source_rank_view.Z_e combined with C_e score after scoring",
            "requires_Ce": "true",
            "ready_after_materialization": "ablation_only_if_lambda_pre_frozen",
            "notes": "do not tune lambda after validation metrics",
        },
        {
            "score_id": "C1_shuffled_Ce",
            "materialization_source": "control view generated after C_e scoring",
            "requires_Ce": "true",
            "ready_after_materialization": "control_required",
            "notes": "must underperform real C_e bridge",
        },
        {
            "score_id": "C2_wrong_predicate_Ce",
            "materialization_source": "wrong-T control view generated from model_safe_ce_view",
            "requires_Ce": "true",
            "ready_after_materialization": "control_required",
            "notes": "must underperform real predicate-geometry compatibility",
        },
    ]


def validation_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "source_model_safe_hidden_alignment",
            "required": "all source candidate ids appear exactly once in model_safe_ce_view, source_rank_view, and hidden_metric_manifest",
            "blocks_next": "true",
        },
        {
            "gate": "blocked_field_absence",
            "required": "no GT match, violation status, p_geom_valid, source score, source rank, or construction labels in model_safe_ce_view",
            "blocks_next": "true",
        },
        {
            "gate": "Ce_input_contract",
            "required": "C_e scorer consumes only T_e and G_e blocks",
            "blocks_next": "true",
        },
        {
            "gate": "source_rank_contract",
            "required": "Z_e fields exist only in source_rank_view and reranking-stage artifacts",
            "blocks_next": "true",
        },
        {
            "gate": "family_success_aggregation_contract",
            "required": "support_contact excluded from success aggregation; relative_horizontal separate/caveated",
            "blocks_next": "true",
        },
        {
            "gate": "metric_freeze_precondition",
            "required": "no Recall@K or Violation@K run before materialization schema audit and metric freeze",
            "blocks_next": "true",
        },
    ]


def docker_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "component": "script",
            "planned_path": "experiments/H002_compatibility_routing/scripts/materialize_source_reranking_candidates.py",
            "action": "create",
            "notes": "read H001 source predictions/geometry and write source-wide H002 materialization views",
        },
        {
            "component": "compose_service",
            "planned_path": "configs/h002/compose.yaml",
            "action": "add_service",
            "notes": "h002-source-rerank-materialize",
        },
        {
            "component": "runtime_output",
            "planned_path": rel_path(RUNTIME_OUTPUT_DIR),
            "action": "write_runtime_artifacts",
            "notes": "ignored experiment runtime output; no paper metric",
        },
        {
            "component": "next_validator",
            "planned_path": "hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol.py",
            "action": "create_next",
            "notes": "validate runtime materialization outputs after Docker run",
        },
    ]


def blocked_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_action": "run_source_reranking_metrics_now",
            "reason": "source-wide C_e materialization and schema audit are not complete",
        },
        {
            "blocked_action": "use_partial_GT_counterfactual_Ce_scores",
            "reason": "existing C_e scores cover only GT/counterfactual rows and would not score the source prediction universe",
        },
        {
            "blocked_action": "put_Ze_inside_Ce",
            "reason": "violates factor contract; source score belongs only to reranking stage",
        },
        {
            "blocked_action": "put_hidden_metric_labels_in_model_safe",
            "reason": "would leak Recall@K or Violation@K targets",
        },
        {
            "blocked_action": "promote_support_contact_success",
            "reason": "support_contact is frozen diagnostic/failure taxonomy",
        },
        {
            "blocked_action": "use_official_test",
            "reason": "official test remains unused and protocol-frozen validation is not complete",
        },
    ]


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    inventory_summary = read_json(args.inventory_dir / "summary.json")
    family_inventory = read_csv(args.inventory_dir / "source_family_inventory.csv")
    metric_readiness = read_csv(args.inventory_dir / "metric_readiness.csv")
    errors = validate_inputs(inventory_summary, args.inventory_dir, family_inventory, metric_readiness)

    materialization_scope = materialization_scope_rows(family_inventory)
    output_manifest = output_manifest_rows()
    model_safe_schema = model_safe_schema_rows()
    geometry_contract = geometry_contract_rows()
    score_contract = score_materialization_rows()
    validation_gates = validation_gate_rows()
    docker_plan = docker_plan_rows()
    blocked_actions = blocked_action_rows()

    total_source_rows = sum(int(row.get("source_prediction_rows") or 0) for row in family_inventory)
    success_rows = sum(
        int(row.get("source_prediction_rows") or 0)
        for row in family_inventory
        if row.get("route_family") in {"relative_vertical", "size_relative"}
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "validation_errors": len(errors),
        "selected_path": SELECTED_PATH if not errors else "blocked_fix_source_reranking_materialization_protocol_inputs",
        "next_todo": NEXT_TODO if not errors else "fix_source_reranking_materialization_protocol_inputs",
        "input_artifacts": {
            "inventory_summary": rel_path(args.inventory_dir / "summary.json"),
            "source_family_inventory": rel_path(args.inventory_dir / "source_family_inventory.csv"),
            "metric_readiness": rel_path(args.inventory_dir / "metric_readiness.csv"),
            "join_key_audit": rel_path(args.inventory_dir / "join_key_audit.csv"),
        },
        "decision": {
            "materialization_protocol_locked": not bool(errors),
            "metrics_run": False,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "source_wide_Ce_materialization_required": True,
            "C_e_input_blocks": ["T_e", "G_e"],
            "Z_e_allowed_stage": "reranking_only",
            "hidden_labels_allowed_stage": "metric_only",
            "support_contact_success_included": False,
        },
        "planned_runtime": {
            "output_dir": rel_path(RUNTIME_OUTPUT_DIR),
            "total_source_family_rows_to_materialize": total_source_rows,
            "primary_success_family_rows": success_rows,
            "expected_artifacts": [row["artifact"] for row in output_manifest],
        },
        "output_artifacts": {
            "summary": rel_path(out_dir / "summary.json"),
            "validation_errors": rel_path(out_dir / "validation_errors.jsonl"),
            "materialization_scope": rel_path(out_dir / "materialization_scope.csv"),
            "output_manifest": rel_path(out_dir / "output_manifest.csv"),
            "model_safe_schema": rel_path(out_dir / "model_safe_schema.csv"),
            "geometry_contract": rel_path(out_dir / "geometry_contract.csv"),
            "score_contract": rel_path(out_dir / "score_materialization_contract.csv"),
            "validation_gates": rel_path(out_dir / "validation_gates.csv"),
            "docker_plan": rel_path(out_dir / "docker_plan.csv"),
            "blocked_actions": rel_path(out_dir / "blocked_actions.csv"),
            "next_contract": rel_path(out_dir / "next_contract.json"),
            "report": rel_path(out_dir / "report.md"),
        },
    }

    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_source_reranking_docker_materialization" if not errors else "blocked",
        "next_todo": summary["next_todo"],
        "next_task": "implement and run Docker source-wide materialization",
        "runtime_output_dir": rel_path(RUNTIME_OUTPUT_DIR),
        "must_write": [row["artifact"] for row in output_manifest],
        "must_validate": [row["gate"] for row in validation_gates],
        "must_not_do": [row["blocked_action"] for row in blocked_actions],
    }

    report_lines = [
        "# Source Reranking Materialization Protocol After Source Inventory",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Result",
        "",
        "This stage freezes the source-wide materialization protocol. It does not run source reranking metrics.",
        "",
        "The next runtime materializer must create a source-wide C_e view over the full VL-SAT/Open3DSG prediction universe.",
        "`C_e` may consume only T_e and G_e; Z_e/source score is allowed only at the reranking stage.",
        "",
        f"- planned runtime output: `{rel_path(RUNTIME_OUTPUT_DIR)}`",
        f"- total source-family rows to materialize: `{total_source_rows}`",
        f"- primary success-family rows: `{success_rows}`",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
    ]

    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "next_contract.json", next_contract)
    write_jsonl(out_dir / "validation_errors.jsonl", errors)
    write_csv(out_dir / "materialization_scope.csv", materialization_scope)
    write_csv(out_dir / "output_manifest.csv", output_manifest)
    write_csv(out_dir / "model_safe_schema.csv", model_safe_schema)
    write_csv(out_dir / "geometry_contract.csv", geometry_contract)
    write_csv(out_dir / "score_materialization_contract.csv", score_contract)
    write_csv(out_dir / "validation_gates.csv", validation_gates)
    write_csv(out_dir / "docker_plan.csv", docker_plan)
    write_csv(out_dir / "blocked_actions.csv", blocked_actions)
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    summary = run(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
