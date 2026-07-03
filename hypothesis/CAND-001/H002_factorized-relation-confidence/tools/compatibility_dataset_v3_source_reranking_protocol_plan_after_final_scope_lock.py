#!/usr/bin/env python3
"""Plan H002 source reranking after final scope lock."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCOPE_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze"
)
DEFAULT_SOURCE_INVENTORY_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan"
)
DEFAULT_OUTPUT_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock"
)

EXPECTED_SCOPE_STATUS = "h002_compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze_ready"
EXPECTED_SCOPE_NEXT = "compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock"
EXPECTED_SOURCE_INVENTORY_STATUS = "h002_compatibility_dataset_v3_official_source_inventory_after_protocol_plan_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock_v1"
STATUS_READY = "h002_compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock_input_errors"
SELECTED_PATH = "source_reranking_protocol_ready_select_source_inventory"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
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


def row_by_key(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def validate_inputs(
    scope_summary: dict[str, Any],
    source_summary: dict[str, Any],
    scope_dir: Path,
    source_inventory_dir: Path,
    route_rows: list[dict[str, str]],
    metric_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if scope_summary.get("status") != EXPECTED_SCOPE_STATUS:
        errors.append({"error_type": "unexpected_scope_status", "actual": scope_summary.get("status")})
    if scope_summary.get("next_todo") != EXPECTED_SCOPE_NEXT:
        errors.append({"error_type": "unexpected_scope_next_todo", "actual": scope_summary.get("next_todo")})
    if scope_summary.get("validation_errors") != 0:
        errors.append({"error_type": "scope_validation_errors", "actual": scope_summary.get("validation_errors")})
    if line_count(scope_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "scope_validation_error_file_not_empty"})

    decision = scope_summary.get("decision", {})
    required_decisions = {
        "official_test_usage": False,
        "paper_metric_promoted": False,
        "support_contact_frozen_diagnostic": True,
        "violation_at_k_primary_metric": False,
        "violation_at_k_downstream_metric": True,
    }
    for key, expected in required_decisions.items():
        if decision.get(key) is not expected:
            errors.append({"error_type": "unexpected_scope_decision", "key": key, "actual": decision.get(key), "expected": expected})

    required_roles = {
        "relative_vertical": "primary_clean_Ce_mechanism",
        "size_relative": "primary_clean_Ce_mechanism",
        "relative_horizontal": "caveated_frame_aware_Ce_mechanism",
        "proximity": "geometry_only_route_control",
        "support_contact": "diagnostic_failure_taxonomy",
    }
    for family, role in required_roles.items():
        row = row_by_key(route_rows, "route_family", family)
        if row.get("final_role") != role:
            errors.append({"error_type": "unexpected_route_role", "family": family, "actual": row.get("final_role"), "expected": role})

    violation_row = row_by_key(metric_rows, "metric", "Violation@K")
    if violation_row.get("role") != "downstream_future":
        errors.append({"error_type": "violation_at_k_not_downstream", "actual": violation_row})

    if source_summary.get("status") != EXPECTED_SOURCE_INVENTORY_STATUS:
        errors.append({"error_type": "unexpected_source_inventory_status", "actual": source_summary.get("status")})
    if source_summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_inventory_validation_errors", "actual": source_summary.get("validation_errors")})
    if line_count(source_inventory_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "source_inventory_validation_error_file_not_empty"})

    source_ids = sorted({row.get("source_id") for row in source_rows if row.get("source_id")})
    if source_ids != ["open3dsg_recovery_relaxed_views_min2", "vlsat_full_validation"]:
        errors.append({"error_type": "unexpected_source_ids", "actual": source_ids})
    if not all(row.get("readiness_status") in {"ready_for_protocol_design", "diagnostic_challenging_route"} for row in source_rows):
        errors.append({"error_type": "source_readiness_not_protocol_ready"})
    return errors


def protocol_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": "R0",
            "status": "completed_by_this_stage",
            "name": "final_scope_lock",
            "purpose": "Lock C_e route scope and move Recall@K/Violation@K to downstream metrics.",
            "output": "final scope lock artifact.",
        },
        {
            "step": "R1",
            "status": "next",
            "name": "source_reranking_source_inventory",
            "purpose": "Re-inventory VL-SAT/Open3DSG candidate rows under the final H002 route scope.",
            "output": "source candidate counts, join keys, feature availability, and per-family caveats.",
        },
        {
            "step": "R2",
            "status": "pending",
            "name": "source_reranking_materialization_protocol",
            "purpose": "Freeze source-candidate model-safe view and hidden manifest before any reranking metric.",
            "output": "candidate schema, blocked fields, K grid, and family inclusion contract.",
        },
        {
            "step": "R3",
            "status": "pending",
            "name": "source_reranking_metric_freeze",
            "purpose": "Freeze ranking scores, baselines, controls, aggregation, and wording.",
            "output": "metric-freeze artifact; no validation-driven score edits after this point.",
        },
        {
            "step": "R4",
            "status": "pending",
            "name": "source_reranking_docker_eval",
            "purpose": "Run Docker evaluation on official validation source candidates only.",
            "output": "Recall@K, Violation@K, family-wise tradeoff, and control tables.",
        },
        {
            "step": "R5",
            "status": "pending",
            "name": "source_reranking_result_review",
            "purpose": "Decide whether source reranking remains diagnostic or becomes paper-facing bridge evidence.",
            "output": "promotion decision and allowed/blocked wording.",
        },
    ]


def family_scope_rows(source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    source_lookup: dict[tuple[str, str], dict[str, str]] = {
        (row.get("route_family", ""), row.get("source_id", "")): row for row in source_rows
    }
    families = [
        {
            "route_family": "relative_vertical",
            "source_reranking_role": "primary_bridge_candidate",
            "inclusion": "include",
            "reason": "Primary clean C_e route and source geometry verification is available in H001 artifacts.",
        },
        {
            "route_family": "size_relative",
            "source_reranking_role": "primary_bridge_candidate_with_feature_caveat",
            "inclusion": "include_after_H002_Ge_materialization_check",
            "reason": "Primary clean C_e route, but H001 source geometry verification is not checkable; needs H002 G_e materialization.",
        },
        {
            "route_family": "relative_horizontal",
            "source_reranking_role": "caveated_frame_aware_bridge",
            "inclusion": "include_as_caveated_or_separate_table",
            "reason": "Frame-aware evidence only; source reranking must not imply frame-invariant spatial reasoning.",
        },
        {
            "route_family": "proximity",
            "source_reranking_role": "geometry_only_control",
            "inclusion": "optional_control_if_source_candidates_exist",
            "reason": "Geometry-only route control, not T_e x G_e interaction evidence.",
        },
        {
            "route_family": "support_contact",
            "source_reranking_role": "diagnostic_only",
            "inclusion": "exclude_from_success_metric",
            "reason": "Frozen diagnostic/failure taxonomy; no solved support/contact claim.",
        },
    ]
    rows: list[dict[str, Any]] = []
    for family in families:
        for source_id in ["vlsat_full_validation", "open3dsg_recovery_relaxed_views_min2"]:
            source_row = source_lookup.get((family["route_family"], source_id), {})
            rows.append(
                {
                    **family,
                    "source_id": source_id,
                    "source_prediction_rows": source_row.get("source_prediction_rows", ""),
                    "source_geometry_checkable_rate": source_row.get("source_geometry_checkable_rate", ""),
                    "source_readiness_status": source_row.get("readiness_status", "needs_source_inventory"),
                    "source_caveat": source_row.get("caveat", ""),
                }
            )
    return rows


def score_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "score_id": "S0_source_score",
            "role": "baseline",
            "formula": "source_score_or_ranking_score",
            "uses_Z_e": "yes",
            "uses_C_e": "no",
            "claim": "source confidence baseline only",
        },
        {
            "score_id": "S1_Ce_only",
            "role": "diagnostic",
            "formula": "C_e(T_e, G_e)",
            "uses_Z_e": "no",
            "uses_C_e": "yes",
            "claim": "compatibility ranking diagnostic, not source utility by itself",
        },
        {
            "score_id": "S2_source_x_Ce",
            "role": "primary_bridge_candidate",
            "formula": "normalized_source_score * normalized_C_e_score",
            "uses_Z_e": "yes_at_reranking_stage_only",
            "uses_C_e": "yes",
            "claim": "compatibility-aware source reranking bridge",
        },
        {
            "score_id": "S3_source_plus_lambda_Ce",
            "role": "ablation_or_future",
            "formula": "log(source_score) + lambda * normalized_C_e_score",
            "uses_Z_e": "yes_at_reranking_stage_only",
            "uses_C_e": "yes",
            "claim": "risk/utility-style soft reranking if lambda is frozen before metrics",
        },
        {
            "score_id": "C1_shuffled_Ce",
            "role": "control",
            "formula": "source_score combined with shuffled C_e or shuffled G_e",
            "uses_Z_e": "yes",
            "uses_C_e": "control_only",
            "claim": "must underperform real C_e bridge",
        },
        {
            "score_id": "C2_wrong_predicate_Ce",
            "role": "control",
            "formula": "source_score combined with wrong-T C_e",
            "uses_Z_e": "yes",
            "uses_C_e": "control_only",
            "claim": "must underperform real predicate-geometry compatibility",
        },
    ]


def metric_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric": "Recall@K",
            "role": "primary_downstream_candidate",
            "unit": "source x family x K",
            "k_grid": "5;10;20;50;100",
            "required_reporting": "family-wise before aggregate",
            "claim_boundary": "source reranking bridge only, not current C_e mechanism metric",
        },
        {
            "metric": "Violation@K",
            "role": "primary_downstream_candidate",
            "unit": "source x family x K",
            "k_grid": "5;10;20;50;100",
            "required_reporting": "family-wise before aggregate",
            "claim_boundary": "geometry inconsistency of top-K after reranking, not primary C_e metric",
        },
        {
            "metric": "selected_count@K",
            "role": "required_sanity",
            "unit": "source x family x K",
            "k_grid": "5;10;20;50;100",
            "required_reporting": "all tables",
            "claim_boundary": "prevents empty or coverage-shifted comparisons",
        },
        {
            "metric": "family_macro_delta",
            "role": "required_summary",
            "unit": "macro over included non-diagnostic families",
            "k_grid": "5;10;20;50;100",
            "required_reporting": "macro and per-family both",
            "claim_boundary": "aggregate-only reporting is blocked",
        },
        {
            "metric": "control_delta",
            "role": "required_control",
            "unit": "score condition x source x family",
            "k_grid": "5;10;20;50;100",
            "required_reporting": "real C_e vs shuffled/wrong C_e",
            "claim_boundary": "bridge invalid if controls do not collapse",
        },
    ]


def blocked_field_rows() -> list[dict[str, Any]]:
    return [
        {
            "field_or_action": "target label / GT match flag in model-safe features",
            "reason": "would leak Recall@K target into reranker",
        },
        {
            "field_or_action": "Violation@K status in model-safe features",
            "reason": "would leak geometry violation metric into the reranking score",
        },
        {
            "field_or_action": "support_contact success inclusion",
            "reason": "support_contact is frozen diagnostic and cannot carry a solved-family claim",
        },
        {
            "field_or_action": "Z_e inside C_e",
            "reason": "source confidence can be used only at reranking stage, not inside compatibility",
        },
        {
            "field_or_action": "official test",
            "reason": "test remains unused until validation protocol, code, metrics, and wording are frozen",
        },
        {
            "field_or_action": "post-hoc lambda tuning after validation metrics",
            "reason": "would make reranking objective validation-fitted rather than protocol-fixed",
        },
    ]


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    scope_summary = read_json(args.scope_dir / "summary.json")
    source_summary = read_json(args.source_inventory_dir / "summary.json")
    route_rows = read_csv(args.scope_dir / "route_scope_lock.csv")
    metric_rows = read_csv(args.scope_dir / "metric_role_lock.csv")
    source_rows = read_csv(args.source_inventory_dir / "source_readiness.csv")
    source_manifest_rows = read_csv(args.source_inventory_dir / "source_manifest_inventory.csv")

    errors = validate_inputs(
        scope_summary,
        source_summary,
        args.scope_dir,
        args.source_inventory_dir,
        route_rows,
        metric_rows,
        source_rows,
    )

    protocol = protocol_steps()
    family_scope = family_scope_rows(source_rows)
    score_contract = score_contract_rows()
    metric_contract = metric_contract_rows()
    blocked_fields = blocked_field_rows()

    source_ids = sorted({row.get("source_id") for row in source_manifest_rows if row.get("source_id")})
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "validation_errors": len(errors),
        "selected_path": SELECTED_PATH if not errors else "blocked_fix_source_reranking_protocol_inputs",
        "next_todo": NEXT_TODO if not errors else "fix_source_reranking_protocol_inputs",
        "input_artifacts": {
            "scope_summary": rel_path(args.scope_dir / "summary.json"),
            "route_scope_lock": rel_path(args.scope_dir / "route_scope_lock.csv"),
            "metric_role_lock": rel_path(args.scope_dir / "metric_role_lock.csv"),
            "source_inventory_summary": rel_path(args.source_inventory_dir / "summary.json"),
            "source_readiness": rel_path(args.source_inventory_dir / "source_readiness.csv"),
            "source_manifest_inventory": rel_path(args.source_inventory_dir / "source_manifest_inventory.csv"),
        },
        "decision": {
            "source_reranking_protocol_locked": not bool(errors),
            "metrics_run": False,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "recall_at_k_opened_as_downstream": True,
            "violation_at_k_opened_as_downstream": True,
            "violation_at_k_primary_Ce_metric": False,
            "support_contact_success_included": False,
            "source_score_allowed_only_at_reranking_stage": True,
            "C_e_must_exclude_Z_e": True,
        },
        "source_scope": {
            "source_ids": source_ids,
            "split": "official_validation_only",
            "primary_bridge_families": ["relative_vertical", "size_relative"],
            "caveated_bridge_families": ["relative_horizontal"],
            "control_families": ["proximity"],
            "diagnostic_only_families": ["support_contact"],
        },
        "metric_contract": {
            "k_grid": [5, 10, 20, 50, 100],
            "primary_downstream_metrics": ["Recall@K", "Violation@K"],
            "required_controls": ["shuffled_Ce_or_Ge", "wrong_predicate_Ce", "source_score_baseline"],
            "aggregation_policy": "family-wise first; macro before aggregate; support_contact diagnostic separately",
        },
        "output_artifacts": {
            "summary": rel_path(out_dir / "summary.json"),
            "validation_errors": rel_path(out_dir / "validation_errors.jsonl"),
            "protocol_steps": rel_path(out_dir / "protocol_steps.csv"),
            "family_source_scope": rel_path(out_dir / "family_source_scope.csv"),
            "score_contract": rel_path(out_dir / "score_contract.csv"),
            "metric_contract": rel_path(out_dir / "metric_contract.csv"),
            "blocked_fields": rel_path(out_dir / "blocked_fields.csv"),
            "next_contract": rel_path(out_dir / "next_contract.json"),
            "report": rel_path(out_dir / "report.md"),
        },
    }

    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_source_reranking_source_inventory" if not errors else "blocked",
        "next_todo": summary["next_todo"],
        "next_task": "inventory source candidates under the final reranking protocol",
        "must_check": [
            "source prediction join keys",
            "source score and rank availability",
            "H002 G_e materialization availability for each locked family",
            "C_e score availability or train/eval feature path",
            "support_contact excluded from success aggregation",
            "Recall@K and Violation@K computability by source/family/K",
        ],
        "must_not_do": [
            "run metrics before materialization and metric freeze",
            "use official test",
            "put Z_e inside C_e",
            "promote support_contact as solved",
            "tune lambda after viewing validation metrics",
        ],
    }

    report_lines = [
        "# Source Reranking Protocol Plan After Final Scope Lock",
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
        "This stage opens Recall@K and Violation@K only as downstream source-reranking metrics.",
        "No source-reranking metric was run, no official test was used, and no paper metric was promoted.",
        "",
        "The primary bridge score is planned as source confidence combined with C_e at the reranking stage.",
        "C_e itself must continue to exclude Z_e/source score.",
        "",
        "## Scope",
        "",
    ]
    for row in family_scope:
        if row["source_id"] == "vlsat_full_validation":
            report_lines.append(
                f"- {row['route_family']}: {row['source_reranking_role']} / {row['inclusion']}"
            )
    report_lines.extend(
        [
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
        ]
    )

    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "next_contract.json", next_contract)
    write_jsonl(out_dir / "validation_errors.jsonl", errors)
    write_csv(out_dir / "protocol_steps.csv", protocol)
    write_csv(out_dir / "family_source_scope.csv", family_scope)
    write_csv(out_dir / "score_contract.csv", score_contract)
    write_csv(out_dir / "metric_contract.csv", metric_contract)
    write_csv(out_dir / "blocked_fields.csv", blocked_fields)
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    summary = run(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
