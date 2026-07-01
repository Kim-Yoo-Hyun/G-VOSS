#!/usr/bin/env python3
"""Plan route-specific H002 target materialization after manifest audit."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan"
)
DEFAULT_MANIFEST_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit"
)

EXPECTED_AUDIT_STATUS = "h002_compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan_ready"
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit"
EXPECTED_MANIFEST_STATUS = "h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit_v1"
STATUS_READY = "h002_compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit_input_errors"
SELECTED_PATH = "freeze_materialization_waves_select_close_by_geometry_support_route_plan"
NEXT_TODO = "compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
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
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
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
                seen.add(key)
                fields.append(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    audit_summary: dict[str, Any],
    manifest_summary: dict[str, Any],
    target_manifest: list[dict[str, str]],
    field_manifest: list[dict[str, str]],
    hidden_manifest: list[dict[str, str]],
    control_manifest: list[dict[str, str]],
    audit_dir: Path,
    manifest_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit_summary.get("validation_errors")})
    if audit_summary.get("counts", {}).get("audit_fail_rows") != 0:
        errors.append({"error_type": "audit_fail_rows_present", "actual": audit_summary.get("counts", {}).get("audit_fail_rows")})
    if read_jsonl(audit_dir / "validation_errors.jsonl"):
        errors.append({"error_type": "audit_validation_error_rows_present"})

    if manifest_summary.get("status") != EXPECTED_MANIFEST_STATUS:
        errors.append({"error_type": "unexpected_manifest_status", "actual": manifest_summary.get("status")})
    if manifest_summary.get("validation_errors") != 0:
        errors.append({"error_type": "manifest_validation_errors_present", "actual": manifest_summary.get("validation_errors")})
    if read_jsonl(manifest_dir / "validation_errors.jsonl"):
        errors.append({"error_type": "manifest_validation_error_rows_present"})

    for name, table in [
        ("target_manifest", target_manifest),
        ("field_manifest", field_manifest),
        ("hidden_manifest", hidden_manifest),
        ("control_manifest", control_manifest),
    ]:
        if len(table) != 13:
            errors.append({"error_type": "unexpected_row_count", "table": name, "actual": len(table)})

    if audit_summary.get("audited_contracts", {}).get("close_by_route") != "geometry_support":
        errors.append({"error_type": "close_by_contract_not_preserved"})
    if audit_summary.get("audited_contracts", {}).get("supported_by_route") != "accept_relabel_abstain":
        errors.append({"error_type": "supported_by_contract_not_preserved"})
    if audit_summary.get("audited_contracts", {}).get("attachment_route") != "observability_then_reliability":
        errors.append({"error_type": "attachment_contract_not_preserved"})
    if audit_summary.get("audited_contracts", {}).get("Ce_excludes_Ze") is not True:
        errors.append({"error_type": "Ce_excludes_Ze_not_true"})
    return errors


def existing_source_artifacts() -> dict[str, list[str]]:
    return {
        "R1": [
            "compatibility_dataset_v3_proximity_close_by_target_plan",
            "compatibility_dataset_v3_proximity_close_by_candidate_materialization",
            "compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit",
            "compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit",
        ],
        "R2": [
            "compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview",
            "compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis",
        ],
        "R3": [
            "compatibility_dataset_v3_size_relative_candidate_materialization_after_plan",
            "compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization",
            "compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan",
            "compatibility_dataset_v3_size_relative_smoke_result_review_after_runner",
        ],
        "R4": [
            "compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan",
            "compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization",
            "compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan",
            "compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner",
        ],
        "R5": [
            "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization",
            "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit",
            "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner",
            "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position",
        ],
        "R6": [
            "compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization",
            "compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion",
            "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion",
        ],
        "R7": [
            "attachment_numeric_geometry_v1",
            "attachment_numeric_geometry_smoke_v1",
            "attachment_independent_positive_anchor_path_decision_after_audit_v1",
            "attachment_independent_positive_anchor_target_independence_audit_v1",
        ],
    }


def source_readiness(route_id: str) -> tuple[str, str]:
    artifacts = existing_source_artifacts().get(route_id, [])
    if not artifacts:
        return "no_existing_route_artifact", ""
    existing = [name for name in artifacts if (H2_ROOT / "artifacts" / name).exists()]
    missing = sorted(set(artifacts) - set(existing))
    status = "ready_from_existing_artifacts" if not missing else "partial_existing_artifacts"
    return status, "; ".join(existing) + (f" | missing: {'; '.join(missing)}" if missing else "")


def materialization_plan(
    target_manifest: list[dict[str, str]],
    field_manifest: list[dict[str, str]],
    hidden_manifest: list[dict[str, str]],
    control_manifest: list[dict[str, str]],
) -> list[dict[str, Any]]:
    field_by_route = {row["route_id"]: row for row in field_manifest}
    hidden_by_route = {row["route_id"]: row for row in hidden_manifest}
    control_by_route = {row["route_id"]: row for row in control_manifest}
    rows: list[dict[str, Any]] = []
    for row in target_manifest:
        route_id = row["route_id"]
        family = row["family"]
        readiness, sources = source_readiness(route_id)
        rows.append(
            {
                "route_id": route_id,
                "route_slug": row["route_slug"],
                "family": family,
                "relations": row["relations"],
                "target_axis": row["target_axis"],
                "label_space": row["label_space"],
                "materialization_wave": wave_for_route(route_id, family),
                "materialization_mode": mode_for_route(route_id, family),
                "planned_route_root": row["artifact_root"],
                "planned_model_safe_view": row["model_safe_view"],
                "planned_hidden_manifest": row["hidden_manifest"],
                "planned_audit_view": row["audit_view"],
                "source_readiness": readiness,
                "source_artifacts": sources,
                "required_model_safe_blocks": model_safe_blocks(field_by_route[route_id]),
                "required_hidden_blocks": hidden_by_route[route_id]["hidden_fields"],
                "required_controls": control_by_route[route_id]["required_controls"],
                "first_followup_allowed": first_followup_allowed(route_id, family),
                "actual_materialization_allowed_now": False,
                "reason_materialization_blocked_now": "this artifact is a plan only; route-specific follow-up must pass before writing rows",
            }
        )
    rows.sort(key=lambda item: wave_rank(item["materialization_wave"]))
    return rows


def wave_for_route(route_id: str, family: str) -> str:
    if route_id in {"R2", "R3", "R4", "R5"}:
        return "W0_normalize_existing_main_routes"
    if route_id == "R1":
        return "W1_close_by_geometry_only_route"
    if route_id == "R6":
        return "W2_supported_by_decomposition_route"
    if route_id == "R7":
        return "W3_attachment_observability_schema_audit"
    if route_id in {"R8", "R9", "R10"}:
        return "W4_feasibility_capacity_schema_audits"
    return "W5_boundary_future_manifests"


def wave_rank(wave: str) -> int:
    order = {
        "W0_normalize_existing_main_routes": 0,
        "W1_close_by_geometry_only_route": 1,
        "W2_supported_by_decomposition_route": 2,
        "W3_attachment_observability_schema_audit": 3,
        "W4_feasibility_capacity_schema_audits": 4,
        "W5_boundary_future_manifests": 5,
    }
    return order[wave]


def mode_for_route(route_id: str, family: str) -> str:
    if route_id in {"R2", "R3", "R4", "R5"}:
        return "normalize_existing_artifacts_into_route_root_plan"
    if route_id == "R1":
        return "new_route_root_plan_from_existing_close_by_artifacts"
    if route_id == "R6":
        return "new_decomposition_target_plan_before_rows"
    if route_id == "R7":
        return "schema_audit_before_observability_materialization"
    if route_id in {"R8", "R9", "R10"}:
        return "capacity_schema_audit_before_materialization"
    return "boundary_or_future_manifest_only"


def first_followup_allowed(route_id: str, family: str) -> str:
    if route_id == "R1":
        return "yes_next_todo_candidate"
    if route_id == "R6":
        return "yes_after_close_by_or_parallel_if_user_selects"
    if route_id == "R7":
        return "schema_audit_only"
    if route_id in {"R2", "R3", "R4", "R5"}:
        return "normalization_only"
    return "not_until_capacity_or_boundary_decision"


def model_safe_blocks(field_row: dict[str, str]) -> str:
    return (
        f"T_e=[{field_row['T_e_model_safe']}]; "
        f"Z_e=[{field_row['Z_e_model_safe']}]; "
        f"G_e=[{field_row['G_e_model_safe']}]; "
        f"Q_e=[{field_row['Q_e_model_safe']}]; "
        f"C_e=[{field_row['C_e_definition']}]"
    )


def wave_plan(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["materialization_wave"], []).append(row)
    wave_descriptions = {
        "W0_normalize_existing_main_routes": "normalize existing main-route artifacts into route-specific root plans; no new row mining",
        "W1_close_by_geometry_only_route": "first concrete route plan: geometry_support target for close by with distance/scale/coverage controls",
        "W2_supported_by_decomposition_route": "second concrete route plan: supported-by accept/relabel/reject/abstain decomposition",
        "W3_attachment_observability_schema_audit": "audit evidence availability for p_obs before attachment materialization",
        "W4_feasibility_capacity_schema_audits": "capacity/schema audits for leaning, cover, and containment",
        "W5_boundary_future_manifests": "boundary/future route manifests only",
    }
    wave_next = {
        "W0_normalize_existing_main_routes": "include in route materialization plan as normalization targets",
        "W1_close_by_geometry_only_route": NEXT_TODO,
        "W2_supported_by_decomposition_route": "supported_by_decomposition_route_materialization_plan",
        "W3_attachment_observability_schema_audit": "attachment_observability_route_schema_audit",
        "W4_feasibility_capacity_schema_audits": "feasibility_route_capacity_schema_audit_plan",
        "W5_boundary_future_manifests": "no immediate materialization",
    }
    waves: list[dict[str, Any]] = []
    for wave in sorted(grouped, key=wave_rank):
        routes = grouped[wave]
        waves.append(
            {
                "wave": wave,
                "route_ids": "; ".join(row["route_id"] for row in routes),
                "families": "; ".join(row["family"] for row in routes),
                "relations": "; ".join(row["relations"] for row in routes),
                "purpose": wave_descriptions[wave],
                "actual_materialization_allowed_now": False,
                "next_action": wave_next[wave],
            }
        )
    return waves


def route_output_contract(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for row in rows:
        contracts.append(
            {
                "route_id": row["route_id"],
                "family": row["family"],
                "planned_route_root": row["planned_route_root"],
                "required_files": (
                    "summary.json; schema.json; model_safe_rows.jsonl; hidden_manifest.jsonl; "
                    "audit_view.jsonl; control_manifest.json; split_or_group_manifest.json; report.md; validation_errors.jsonl"
                ),
                "must_report_counts": "rows; labels; abstain; groups; scans; class pairs; source artifacts; blocked field hits",
                "must_report_controls": row["required_controls"],
                "must_report_boundary": "train-only until explicitly promoted; no validation/test; no paper evidence from route root alone",
            }
        )
    return contracts


def blocker_matrix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for row in rows:
        blockers.append(
            {
                "route_id": row["route_id"],
                "family": row["family"],
                "blocking_condition": blocker_for_route(row["route_id"]),
                "unblock_requirement": unblock_for_route(row["route_id"]),
                "risk_if_ignored": risk_for_route(row["route_id"]),
            }
        )
    return blockers


def blocker_for_route(route_id: str) -> str:
    mapping = {
        "R1": "distance-only dominance could be misworded as predicate-geometry interaction",
        "R2": "existing vertical route must be normalized without changing target construction",
        "R3": "high AUROC with calibration caveat must not become calibrated reliability",
        "R4": "reference-frame caveat and in-front-of exclusion must remain explicit",
        "R5": "support/contact caveat and Q_e separation must remain explicit",
        "R6": "supported-by must not be used as clean negative for standing/lying",
        "R7": "observability and functional/physical connection ambiguity unresolved",
        "R8": "normal/pose evidence availability not yet audited",
        "R9": "view/occlusion evidence availability not yet audited",
        "R10": "containment count/class/occlusion risk not yet audited",
        "R11": "identity/symmetry may become separate task",
        "R12": "part/belonging may become ontology/class-pair task",
        "R13": "embedded structure needs mesh/cavity evidence",
    }
    return mapping[route_id]


def unblock_for_route(route_id: str) -> str:
    mapping = {
        "R1": "route-specific close-by materialization plan with geometry_support wording and controls",
        "R2": "normalization manifest from existing main-route artifacts",
        "R3": "normalization manifest with calibration caveat",
        "R4": "normalization manifest with wrong-frame/endpoint controls",
        "R5": "normalization manifest with support/contact caveat",
        "R6": "decomposition manifest with accept/relabel/reject/abstain labels",
        "R7": "observability schema audit before target rows",
        "R8": "capacity/schema audit for normals and pose",
        "R9": "capacity/schema audit for view and occlusion evidence",
        "R10": "capacity/schema audit for containment evidence and class controls",
        "R11": "boundary feasibility audit for identity/symmetry",
        "R12": "semantic/structural boundary manifest",
        "R13": "embedded-structure future feasibility manifest",
    }
    return mapping[route_id]


def risk_for_route(route_id: str) -> str:
    mapping = {
        "R1": "claim becomes a distance-threshold baseline instead of route evidence",
        "R2": "vertical route overstates generality",
        "R3": "mechanism result is overclaimed as probability calibration",
        "R4": "horizontal relation claim hides frame convention",
        "R5": "support/contact is overclaimed as solved",
        "R6": "superordinate label corrupts binary support target",
        "R7": "unobservable rows become false negatives",
        "R8": "leaning becomes generic contact classification",
        "R9": "cover becomes overlap-only or view-availability shortcut",
        "R10": "containment becomes class-pair shortcut",
        "R11": "identity task is mixed into physical relation reliability",
        "R12": "semantic ontology is mistaken for geometry compatibility",
        "R13": "build-in is mistaken for wall-near proximity",
    }
    return mapping[route_id]


def first_route_plan() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "R1",
            "family": "proximity",
            "next_todo": NEXT_TODO,
            "why_first": "it converts a previously diagnostic relation into a proper geometry-only learned/evaluated route",
            "must_preserve": "do not claim T_e x G_e interaction; report geometry_support with distance/scale/coverage controls",
        },
        {
            "rank": 2,
            "route_id": "R6",
            "family": "superordinate_support",
            "next_todo": "supported_by_decomposition_route_materialization_plan",
            "why_first": "it addresses the strongest revised-claim addition after close by",
            "must_preserve": "accept/relabel/reject/abstain; supported by is not a clean negative for standing/lying",
        },
        {
            "rank": 3,
            "route_id": "R7",
            "family": "attachment_observability",
            "next_todo": "attachment_observability_route_schema_audit",
            "why_first": "high-value but cannot be materialized before evidence availability audit",
            "must_preserve": "p_obs/Q_e before p_rel; unobservable rows should abstain",
        },
    ]


def write_report(
    path: Path,
    status: str,
    validation_errors: int,
    materialization_rows: list[dict[str, Any]],
    waves: list[dict[str, Any]],
    first_routes: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Route-Specific Target Materialization Plan After Manifest Audit",
        "",
        "## Status",
        "",
        "```text",
        f"status = {status}",
        f"selected_path = {SELECTED_PATH}",
        f"validation_errors = {validation_errors}",
        f"next_todo = {NEXT_TODO}",
        "```",
        "",
        "## Purpose",
        "",
        "This artifact plans route-specific target materialization. It does not materialize rows,",
        "does not run a model, and does not promote H002 to paper evidence.",
        "",
        "## Materialization Waves",
        "",
        "| Wave | Route IDs | Families | Purpose | Next Action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in waves:
        lines.append(
            f"| {row['wave']} | {row['route_ids']} | {row['families']} | {row['purpose']} | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Selected First Follow-Ups",
            "",
            "| Rank | Route | Family | Next TODO | Must Preserve |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for row in first_routes:
        lines.append(f"| {row['rank']} | {row['route_id']} | {row['family']} | {row['next_todo']} | {row['must_preserve']} |")
    lines.extend(
        [
            "",
            "## Route Plan Summary",
            "",
            "| Route | Relations | Mode | Source Readiness | Planned Root |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in materialization_rows:
        lines.append(
            f"| {row['route_id']} | {row['relations']} | {row['materialization_mode']} | {row['source_readiness']} | {row['planned_route_root']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Allowed now:",
            "",
            "- route-specific materialization planning",
            "- first concrete follow-up selection",
            "- source-artifact reuse planning",
            "",
            "Blocked now:",
            "",
            "- actual row materialization",
            "- learned smoke runner",
            "- Docker/paper promotion",
            "- calibrated `p_rel` / `p_obs` claim",
            "",
            "## Next",
            "",
            "```text",
            NEXT_TODO,
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    audit_dir = args.audit_dir.resolve()
    manifest_dir = args.manifest_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = read_json(audit_dir / "summary.json")
    manifest_summary = read_json(manifest_dir / "summary.json")
    target_manifest = read_csv(manifest_dir / "route_target_manifest.csv")
    field_manifest = read_csv(manifest_dir / "route_field_manifest.csv")
    hidden_manifest = read_csv(manifest_dir / "route_hidden_manifest.csv")
    control_manifest = read_csv(manifest_dir / "route_control_manifest.csv")

    errors = validate_inputs(
        audit_summary,
        manifest_summary,
        target_manifest,
        field_manifest,
        hidden_manifest,
        control_manifest,
        audit_dir,
        manifest_dir,
    )
    materialization_rows = materialization_plan(target_manifest, field_manifest, hidden_manifest, control_manifest)
    waves = wave_plan(materialization_rows)
    output_contract = route_output_contract(materialization_rows)
    blockers = blocker_matrix(materialization_rows)
    first_routes = first_route_plan()
    status = STATUS_ERRORS if errors else STATUS_READY

    output_paths = {
        "artifact_root": rel_path(output_dir),
        "route_materialization_plan": rel_path(output_dir / "route_materialization_plan.csv"),
        "materialization_wave_plan": rel_path(output_dir / "materialization_wave_plan.csv"),
        "route_output_contract": rel_path(output_dir / "route_output_contract.csv"),
        "materialization_blocker_matrix": rel_path(output_dir / "materialization_blocker_matrix.csv"),
        "first_route_followup_plan": rel_path(output_dir / "first_route_followup_plan.csv"),
        "report": rel_path(output_dir / "report.md"),
        "summary": rel_path(output_dir / "summary.json"),
        "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "input_errors_fix_before_materialization_plan",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "manifest_audit": rel_path(audit_dir),
            "target_manifest_plan": rel_path(manifest_dir),
        },
        "output_paths": output_paths,
        "counts": {
            "route_materialization_rows": len(materialization_rows),
            "wave_rows": len(waves),
            "route_output_contract_rows": len(output_contract),
            "blocker_rows": len(blockers),
            "first_route_rows": len(first_routes),
        },
        "selected_first_route": {
            "route_id": "R1",
            "family": "proximity",
            "relations": "close by",
            "target_axis": "geometry_support",
            "next_todo": NEXT_TODO,
        },
        "followup_priority": [
            "R1 close by geometry_support",
            "R6 supported by accept/relabel/reject/abstain",
            "R7 attachment observability schema audit",
        ],
        "boundary": {
            "materializes_rows": False,
            "runs_model": False,
            "paper_evidence_allowed_now": False,
            "h001_artifacts_modified": False,
            "validation_or_test_used": False,
        },
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
    }

    write_csv(output_dir / "route_materialization_plan.csv", materialization_rows)
    write_csv(output_dir / "materialization_wave_plan.csv", waves)
    write_csv(output_dir / "route_output_contract.csv", output_contract)
    write_csv(output_dir / "materialization_blocker_matrix.csv", blockers)
    write_csv(output_dir / "first_route_followup_plan.csv", first_routes)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", status, len(errors), materialization_rows, waves, first_routes)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
