#!/usr/bin/env python3
"""Freeze the official validation candidate materialization protocol for H002."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INVENTORY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory"

EXPECTED_INVENTORY_STATUS = "h002_compatibility_dataset_v3_official_source_inventory_after_protocol_plan_ready"
EXPECTED_INVENTORY_NEXT = "compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory_v1"
STATUS_READY = "h002_compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory_input_errors"
SELECTED_PATH = "official_candidate_materialization_protocol_ready_select_docker_materializer"
NEXT_TODO = "compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol"

FAMILY_PREDICATES = {
    "relative_horizontal": ["left", "right", "front", "behind"],
    "relative_vertical": ["higher than", "lower than"],
    "size_relative": ["bigger than", "smaller than"],
    "support_contact": ["standing on", "lying on"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", type=Path, default=DEFAULT_INVENTORY_DIR)
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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def validate_inventory(
    *,
    summary: dict[str, Any],
    errors: list[dict[str, Any]],
    gt_rows: list[dict[str, str]],
    readiness_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    validation_errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INVENTORY_STATUS:
        validation_errors.append({"error_type": "unexpected_inventory_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INVENTORY_NEXT:
        validation_errors.append({"error_type": "unexpected_inventory_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        validation_errors.append({"error_type": "inventory_summary_validation_errors", "actual": summary.get("validation_errors")})
    if errors:
        validation_errors.append({"error_type": "inventory_validation_error_rows_present", "rows": len(errors)})

    boundary = summary.get("boundary", {})
    expected_false = [
        "official_validation_metric_produced",
        "official_test_usage",
        "paper_metric_produced",
        "h001_artifacts_modified",
        "p_rel_claim_enabled",
        "p_obs_claim_enabled",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            validation_errors.append({"error_type": "unexpected_boundary_value", "key": key, "actual": boundary.get(key)})
    if boundary.get("h001_artifacts_read_only_inventory") is not True:
        validation_errors.append(
            {
                "error_type": "h001_read_only_inventory_not_recorded",
                "actual": boundary.get("h001_artifacts_read_only_inventory"),
            }
        )

    gt_by_family = {row.get("route_family"): row for row in gt_rows if row.get("level") == "family"}
    for family in FAMILY_PREDICATES:
        row = gt_by_family.get(family)
        if row is None:
            validation_errors.append({"error_type": "missing_gt_family_inventory", "family": family})
            continue
        if int(float(row.get("gt_relations", 0))) <= 0:
            validation_errors.append({"error_type": "empty_gt_family_inventory", "family": family})
        if float(row.get("obb_pair_coverage", 0.0)) < 0.99:
            validation_errors.append({"error_type": "low_obb_pair_coverage", "family": family, "actual": row.get("obb_pair_coverage")})

    sources = {row.get("source_id") for row in manifest_rows}
    for source_id in ["vlsat_full_validation", "open3dsg_recovery_relaxed_views_min2"]:
        if source_id not in sources:
            validation_errors.append({"error_type": "missing_source_manifest", "source_id": source_id})

    readiness_by_family_source = {(row.get("route_family"), row.get("source_id")): row for row in readiness_rows}
    for family in FAMILY_PREDICATES:
        for source_id in ["vlsat_full_validation", "open3dsg_recovery_relaxed_views_min2"]:
            row = readiness_by_family_source.get((family, source_id))
            if row is None:
                validation_errors.append({"error_type": "missing_source_readiness", "family": family, "source_id": source_id})
                continue
            if int(float(row.get("source_prediction_rows", 0))) <= 0:
                validation_errors.append({"error_type": "empty_source_candidate_rows", "family": family, "source_id": source_id})
    return validation_errors


def family_contract(gt_rows: list[dict[str, str]], readiness_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    gt_by_family = {row["route_family"]: row for row in gt_rows if row.get("level") == "family"}
    checkable_by_family = {}
    for row in readiness_rows:
        family = row.get("route_family")
        checkable_by_family.setdefault(family, []).append(float(row.get("source_geometry_checkable_rate", 0.0)))

    rows: list[dict[str, Any]] = []
    for family, predicates in FAMILY_PREDICATES.items():
        gt = gt_by_family[family]
        max_checkable = max(checkable_by_family.get(family, [0.0]))
        if family == "relative_horizontal":
            route_role = "main_frame_aware_compatibility_route"
            g_policy = "build H002 reference-frame-aware signed horizontal/depth deltas from OBB centroids; do not use H001 p_geom_valid"
            negative_policy = "predicate flip among left/right/front/behind on the same directed pair, with axis-consistency metadata hidden from model features"
            claim_status = "candidate_main_after_materialization_audit"
        elif family == "relative_vertical":
            route_role = "main_signed_geometry_compatibility_route"
            g_policy = "build signed vertical center/bottom/top deltas from OBB geometry; H001 p_geom_valid may be diagnostic bridge only"
            negative_policy = "higher/lower predicate flip on the same directed pair unless GT contains the flipped predicate"
            claim_status = "candidate_main_after_materialization_audit"
        elif family == "size_relative":
            route_role = "main_size_compatibility_route"
            g_policy = "build object-pair size ratio features from OBB axes, volume, height, and footprint; do not use H001 p_geom_valid"
            negative_policy = "bigger/smaller predicate flip on the same directed pair unless GT contains the flipped predicate"
            claim_status = "candidate_main_after_materialization_audit"
        else:
            route_role = "diagnostic_challenging_support_contact_route"
            g_policy = "build contact/support gap, vertical order, footprint overlap, and pose proxy features; H001 p_geom_valid may be diagnostic bridge only"
            negative_policy = "standing/lying predicate contrast plus geometry-violation counterfactuals; do not claim solved support/contact"
            claim_status = "diagnostic_or_partial_after_materialization_audit"
        rows.append(
            {
                "route_family": family,
                "predicates": "; ".join(predicates),
                "official_validation_gt_relations": int(float(gt.get("gt_relations", 0))),
                "unique_scans": int(float(gt.get("unique_scans", 0))),
                "obb_pair_coverage": float(gt.get("obb_pair_coverage", 0.0)),
                "route_role": route_role,
                "claim_status_before_metric": claim_status,
                "primary_materialization_route": "GT_counterfactual_mechanism",
                "g_e_policy": g_policy,
                "counterfactual_policy": negative_policy,
                "source_bridge_policy": "source candidates allowed for secondary bridge/provenance, not for target construction",
                "h001_geometry_checkable_max_rate": max_checkable,
                "paper_boundary": "protocol_only_no_metric",
            }
        )
    return rows


def source_bridge_contract(readiness_rows: list[dict[str, str]], manifest_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    manifest_by_source = {row["source_id"]: row for row in manifest_rows}
    rows: list[dict[str, Any]] = []
    for row in readiness_rows:
        source_id = row["source_id"]
        family = row["route_family"]
        geometry_rate = float(row.get("source_geometry_checkable_rate", 0.0))
        if geometry_rate >= 0.5:
            use_policy = "secondary_bridge_with_h001_geometry_diagnostic"
        else:
            use_policy = "secondary_bridge_predictions_only_h002_g_e_required"
        manifest = manifest_by_source.get(source_id, {})
        rows.append(
            {
                "source_id": source_id,
                "route_family": family,
                "source_prediction_rows": int(float(row.get("source_prediction_rows", 0))),
                "source_geometry_checkable_rate": geometry_rate,
                "bridge_use_policy": use_policy,
                "source_score_policy": "Z_e_hidden_for_main_C_e; allowed only in explicit source-baseline or p_rel protocol",
                "p_geom_valid_policy": "hidden_or_diagnostic; never the main G_e for official C_e materialization",
                "adapter_predictions": manifest.get("adapter_predictions", ""),
                "geometry_verification": manifest.get("geometry_verification", ""),
                "read_only_requirement": "must mount/read H001 artifacts read-only",
            }
        )
    return rows


def row_schema() -> dict[str, Any]:
    return {
        "row_files": {
            "candidate_rows": "experiments/H002_compatibility_routing/official_materialization/latest/candidate_rows.jsonl",
            "model_safe_view": "experiments/H002_compatibility_routing/official_materialization/latest/model_safe_view.jsonl",
            "hidden_manifest": "experiments/H002_compatibility_routing/official_materialization/latest/hidden_manifest.jsonl",
            "row_manifest": "experiments/H002_compatibility_routing/official_materialization/latest/row_manifest.json",
            "validation_errors": "experiments/H002_compatibility_routing/official_materialization/latest/validation_errors.jsonl",
        },
        "row_identity": [
            "candidate_id",
            "split",
            "scan_id",
            "subject_id",
            "object_id",
            "predicate_label",
            "route_family",
            "candidate_origin",
        ],
        "model_safe_feature_groups": {
            "T_e": [
                "predicate_label",
                "predicate_text",
                "route_family",
                "subject_class_label",
                "object_class_label",
                "predicate_family_embedding_key",
            ],
            "G_e": [
                "g_e_available",
                "g_e_feature_names",
                "g_e_feature_vector",
                "g_e_feature_mask",
                "geometry_reference_policy",
            ],
            "C_e_target": [
                "compatibility_label",
                "compatibility_label_source",
            ],
            "metadata_not_features": [
                "candidate_id",
                "scan_id",
                "subject_id",
                "object_id",
                "cv_or_group_key",
            ],
        },
        "diagnostic_only_groups": {
            "Q_e": [
                "geometry_observable",
                "geometry_quality_flag",
                "object_obb_available",
                "mesh_or_semseg_available",
            ],
            "Z_e": [
                "source_id",
                "source_score",
                "semantic_rank",
                "ranking_score",
            ],
        },
        "must_be_hidden_for_main_C_e": [
            "source_score",
            "ranking_score",
            "semantic_rank",
            "source_id",
            "h001_p_geom_valid",
            "h001_verification_status",
            "label_match_status",
            "geometry_status",
            "candidate_bucket",
            "construction_bucket",
            "distance_bucket",
            "rank_band",
            "gt_exact_match_flag",
            "counterfactual_type",
            "target_generation_rule",
            "old_proxy_label",
        ],
    }


def blocked_field_contract() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in row_schema()["must_be_hidden_for_main_C_e"]:
        rows.append(
            {
                "field": field,
                "blocked_from": "main_C_e_model_safe_view",
                "allowed_use": "hidden_manifest, audit, diagnostic baseline, or separate p_rel/p_obs protocol only",
                "reason": "prevents source/proxy/construction leakage into predicate-geometry compatibility",
            }
        )
    return rows


def audit_contract() -> dict[str, Any]:
    return {
        "required_before_metric": [
            "candidate_rows_count_check",
            "model_safe_hidden_disjointness_check",
            "blocked_field_absence_check",
            "target_balance_by_family_and_predicate",
            "scan_and_pair_leakage_audit",
            "predicate_only_baseline",
            "class_pair_only_baseline",
            "source_only_or_rank_only_baseline",
            "geometry_only_baseline",
            "T_plus_G_concat_baseline",
            "T_x_G_compatibility_model",
            "wrong_T_control",
            "shuffled_G_control",
            "family_specific_control_report",
        ],
        "pass_before_metric_gate": {
            "validation_errors": 0,
            "blocked_field_hits": 0,
            "hidden_manifest_required": True,
            "official_test_usage": False,
            "h001_artifacts_modified": False,
        },
        "claim_boundary": {
            "metric_stage": "not_yet_run",
            "official_validation_claim": "blocked_until_materialization_schema_audit_and_metric_protocol_pass",
            "paper_metric_claim": "blocked",
            "p_rel_p_obs_claim": "blocked",
            "support_contact_solved_claim": "blocked",
        },
    }


def materialization_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": "M0",
            "name": "read_official_validation_gt",
            "owner": "experiments/H002_compatibility_routing",
            "output": "raw official validation GT anchors with OBB join metadata",
            "metric": False,
        },
        {
            "step": "M1",
            "name": "construct_family_specific_G_e",
            "owner": "experiments/H002_compatibility_routing",
            "output": "predicate-independent geometry evidence vectors per route family",
            "metric": False,
        },
        {
            "step": "M2",
            "name": "generate_gt_counterfactuals",
            "owner": "experiments/H002_compatibility_routing",
            "output": "same-pair predicate counterfactuals and hidden generation manifest",
            "metric": False,
        },
        {
            "step": "M3",
            "name": "attach_read_only_source_bridge",
            "owner": "experiments/H002_compatibility_routing",
            "output": "optional VL-SAT/Open3DSG source provenance hidden from main C_e features",
            "metric": False,
        },
        {
            "step": "M4",
            "name": "write_model_safe_and_hidden_views",
            "owner": "experiments/H002_compatibility_routing",
            "output": "candidate_rows/model_safe_view/hidden_manifest/row_manifest",
            "metric": False,
        },
        {
            "step": "M5",
            "name": "run_materialization_validation",
            "owner": "experiments/H002_compatibility_routing",
            "output": "validation_errors.jsonl and count/provenance manifest",
            "metric": False,
        },
        {
            "step": "M6",
            "name": "schema_shortcut_audit_after_materialization",
            "owner": "experiments/H002_compatibility_routing",
            "output": "leakage/shortcut/control readiness report",
            "metric": False,
        },
    ]


def write_report(path: Path, summary: dict[str, Any], family_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# H002 Official Candidate Materialization Protocol",
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
        "## Decision",
        "",
        "Official validation candidate materialization protocol is frozen. This stage did not materialize rows and did not run metrics.",
        "",
        "## Family Protocol",
        "",
        "| Family | GT | Role | G_e policy | Boundary |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in family_rows:
        lines.append(
            f"| `{row['route_family']}` | {row['official_validation_gt_relations']} | "
            f"{row['route_role']} | {row['g_e_policy']} | {row['paper_boundary']} |"
        )
    lines.extend(
        [
            "",
            "## Source Bridge Protocol",
            "",
            "| Source | Family | Rows | Policy |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for row in source_rows:
        lines.append(
            f"| `{row['source_id']}` | `{row['route_family']}` | "
            f"{row['source_prediction_rows']} | {row['bridge_use_policy']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- official validation metric 생성 없음.",
            "- official test 사용 없음.",
            "- paper-level result 생성 없음.",
            "- `p_rel` / `p_obs` claim 생성 없음.",
            "- H001 source artifacts는 read-only bridge/provenance로만 사용.",
            "- 다음 단계는 Docker official candidate materializer 구현이다.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    inventory_summary = read_json(args.inventory_dir / "summary.json")
    inventory_errors = read_jsonl(args.inventory_dir / "validation_errors.jsonl")
    gt_rows = read_csv(args.inventory_dir / "gt_geometry_inventory.csv")
    readiness_rows = read_csv(args.inventory_dir / "source_readiness.csv")
    manifest_rows = read_csv(args.inventory_dir / "source_manifest_inventory.csv")

    validation_errors = validate_inventory(
        summary=inventory_summary,
        errors=inventory_errors,
        gt_rows=gt_rows,
        readiness_rows=readiness_rows,
        manifest_rows=manifest_rows,
    )
    family_rows = family_contract(gt_rows, readiness_rows)
    source_rows = source_bridge_contract(readiness_rows, manifest_rows)
    row_schema_payload = row_schema()
    blocked_rows = blocked_field_contract()
    audit_payload = audit_contract()
    steps = materialization_steps()

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked_fix_inventory_inputs",
        "next_todo": NEXT_TODO if not validation_errors else EXPECTED_INVENTORY_NEXT,
        "validation_errors": len(validation_errors),
        "input_artifacts": {
            "inventory_summary": rel_path(args.inventory_dir / "summary.json"),
            "gt_geometry_inventory": rel_path(args.inventory_dir / "gt_geometry_inventory.csv"),
            "source_readiness": rel_path(args.inventory_dir / "source_readiness.csv"),
            "source_manifest_inventory": rel_path(args.inventory_dir / "source_manifest_inventory.csv"),
        },
        "output_artifacts": {
            "materialization_contract": rel_path(args.output_dir / "materialization_contract.json"),
            "row_schema": rel_path(args.output_dir / "row_schema.json"),
            "family_route_contract": rel_path(args.output_dir / "family_route_contract.csv"),
            "source_bridge_contract": rel_path(args.output_dir / "source_bridge_contract.csv"),
            "blocked_field_contract": rel_path(args.output_dir / "blocked_field_contract.csv"),
            "audit_contract": rel_path(args.output_dir / "audit_contract.json"),
            "next_runner_contract": rel_path(args.output_dir / "next_runner_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "boundary": {
            "candidate_rows_materialized": False,
            "official_validation_metric_produced": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_rel_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "h001_artifacts_modified": False,
            "h001_artifacts_read_only_bridge_only": True,
        },
        "selected_policy": {
            "experiment_root": "experiments/H002_compatibility_routing",
            "next_docker_service_name": "h002-official-materialize-candidates",
            "materialization_output_root": "experiments/H002_compatibility_routing/official_materialization/latest",
            "primary_route": "GT_counterfactual_mechanism",
            "secondary_routes": ["VL-SAT_source_bridge", "Open3DSG_source_bridge"],
            "metric_after_this_stage": "blocked_until_materialization_and_schema_audit_pass",
        },
    }

    materialization_contract = {
        "schema_version": SCHEMA_VERSION,
        "status": "protocol_frozen_no_rows_materialized",
        "input_inventory": rel_path(args.inventory_dir),
        "steps": steps,
        "family_contract": family_rows,
        "source_bridge_contract": source_rows,
        "row_schema_path": rel_path(args.output_dir / "row_schema.json"),
        "audit_contract_path": rel_path(args.output_dir / "audit_contract.json"),
    }
    next_runner_contract = {
        "next_todo": NEXT_TODO,
        "runner_purpose": "Implement Docker official validation candidate materializer without metrics.",
        "docker_service": "h002-official-materialize-candidates",
        "output_root": "experiments/H002_compatibility_routing/official_materialization/latest",
        "required_outputs": row_schema_payload["row_files"],
        "must_not_do": [
            "compute official validation metrics",
            "touch official test",
            "modify H001 artifacts",
            "enable p_rel/p_obs",
            "use source score/rank/p_geom_valid in main C_e model-safe features",
        ],
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "materialization_contract.json", materialization_contract)
    write_json(args.output_dir / "row_schema.json", row_schema_payload)
    write_csv(args.output_dir / "family_route_contract.csv", family_rows)
    write_csv(args.output_dir / "source_bridge_contract.csv", source_rows)
    write_csv(args.output_dir / "blocked_field_contract.csv", blocked_rows)
    write_json(args.output_dir / "audit_contract.json", audit_payload)
    write_json(args.output_dir / "next_runner_contract.json", next_runner_contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_report(args.output_dir / "report.md", summary, family_rows, source_rows)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
