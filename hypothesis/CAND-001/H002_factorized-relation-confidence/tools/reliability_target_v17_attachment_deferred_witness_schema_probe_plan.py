#!/usr/bin/env python3
"""Plan the H002 v17 attachment-deferred witness schema probe."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_DECISION_DIR = RGA_ROOT / "reliability_target_v16_cross_stratum_support_contact_contrast_path_decision_after_capacity_scan"
DEFAULT_FEASIBILITY_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_feasibility_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v17_attachment_deferred_witness_schema_probe_plan"

EXPECTED_DECISION_STATUS = "h002_reliability_target_v16_cross_stratum_path_decision_select_attachment_deferred_witness_schema_probe"
EXPECTED_DECISION_NEXT = "reliability_target_v17_attachment_deferred_witness_schema_probe_plan"
EXPECTED_SELECTED_PATH = "freeze_v16_diagnostic_select_v17_attachment_deferred_witness_schema_probe"
EXPECTED_FEASIBILITY_STATUS = "h002_reliability_target_v14_physical_relation_family_feasibility_scan_ready_support_primary_attachment_schema_deferred"

STATUS = "h002_reliability_target_v17_attachment_deferred_witness_schema_probe_plan_ready_for_capacity_scan"
NEXT_TODO = "reliability_target_v17_attachment_deferred_witness_schema_capacity_scan"

PREDICATES = ["attached to", "hanging on", "connected to"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-dir", type=Path, default=DEFAULT_DECISION_DIR)
    parser.add_argument("--feasibility-dir", type=Path, default=DEFAULT_FEASIBILITY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(decision: dict[str, Any], feasibility: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if decision.get("status") != EXPECTED_DECISION_STATUS:
        errors.append({"error_type": "unexpected_decision_status", "expected": EXPECTED_DECISION_STATUS, "actual": decision.get("status")})
    if decision.get("next_todo") != EXPECTED_DECISION_NEXT:
        errors.append({"error_type": "unexpected_decision_next_todo", "expected": EXPECTED_DECISION_NEXT, "actual": decision.get("next_todo")})
    if decision.get("selected_path") != EXPECTED_SELECTED_PATH:
        errors.append({"error_type": "unexpected_selected_path", "expected": EXPECTED_SELECTED_PATH, "actual": decision.get("selected_path")})
    if decision.get("validation_errors") != 0:
        errors.append({"error_type": "decision_validation_errors_present", "actual": decision.get("validation_errors")})
    if feasibility.get("status") != EXPECTED_FEASIBILITY_STATUS:
        errors.append({"error_type": "unexpected_feasibility_status", "expected": EXPECTED_FEASIBILITY_STATUS, "actual": feasibility.get("status")})
    if feasibility.get("validation_errors") != 0:
        errors.append({"error_type": "feasibility_validation_errors_present", "actual": feasibility.get("validation_errors")})

    for source, payload in [("decision", decision), ("feasibility", feasibility)]:
        boundary = payload.get("boundary", {})
        for key in [
            "validation_usage",
            "test_usage",
            "trains_new_posterior",
            "posterior_smoke_allowed",
            "paper_evidence_allowed",
            "h001_artifacts_modified",
            "rga_redefined_as_lh_only",
            "multi_view_as_model_input",
            "hidden_fields_as_model_input",
        ]:
            if boundary.get(key) is not False:
                errors.append({"error_type": "boundary_violation", "source": source, "key": key, "actual": boundary.get(key)})

    family_rows = {row["family"]: row for row in feasibility.get("family_inventory", [])}
    attachment = family_rows.get("attachment_deferred")
    if attachment is None:
        errors.append({"error_type": "attachment_family_missing_from_v14_feasibility"})
    else:
        if int(attachment.get("rows", 0)) <= 0:
            errors.append({"error_type": "attachment_rows_missing", "actual": attachment.get("rows")})
        if int(attachment.get("checkable_rows", -1)) != 0:
            errors.append({"error_type": "attachment_expected_uncheckable_before_schema", "actual": attachment.get("checkable_rows")})
        if float(attachment.get("unsupported_share", 0.0)) != 1.0:
            errors.append({"error_type": "attachment_expected_fully_unsupported_before_schema", "actual": attachment.get("unsupported_share")})

    route_rows = {row["family"]: row for row in feasibility.get("route_matrix", [])}
    route = route_rows.get("attachment_deferred")
    if route and route.get("verdict") != "defer_until_geometry_witness_schema_exists":
        errors.append({"error_type": "unexpected_attachment_route_verdict", "actual": route.get("verdict")})
    return errors


def build_witness_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_attachment_deferred_witness_schema_v1",
        "relation_family": "attachment_deferred",
        "predicate_scope": PREDICATES,
        "purpose": "Turn attachment-like open/closed predicates from unsupported RGA rows into geometry-checkable evidence candidates before label mining.",
        "not_a_label_policy": {
            "geometry_status_is_not_relation_reliability": True,
            "witness_score_is_not_posterior": True,
            "queue_kind_is_not_label": True,
            "label_fill_required_after_capacity": True,
            "target_independence_audit_required_before_posterior": True,
        },
        "available_geometry_source": {
            "primary": "match_rows directed-pair geometry reused from checkable pair-level support_contact or relative_vertical rows",
            "rationale": "Attachment rows are unsupported only because the predicate family has no policy; the directed object pair still has OBB/pair geometry in the same train RGA artifact.",
            "allowed_features": [
                "distance_3d",
                "distance_xy",
                "normalized_distance_3d",
                "normalized_distance_xy",
                "projected_iou_xy",
                "projected_subject_overlap_ratio",
                "projected_object_overlap_ratio",
                "center_delta_z",
                "normalized_center_delta_z",
                "subject_bottom_z",
                "subject_top_z",
                "object_bottom_z",
                "object_top_z",
                "vertical_gap_subject_on_object",
            ],
            "not_available_in_current_schema": [
                "surface normals",
                "explicit contact patch area",
                "mesh-level attachment boundary",
                "true physical connector state",
            ],
        },
        "predicate_templates": {
            "attached to": {
                "template_type": "near_contact_anchor_attachment",
                "positive_witnesses": [
                    "subject and object are near in 3D or projected overlap is nontrivial",
                    "object is a plausible anchor surface or anchor object",
                    "floor-support confound is low or explicitly marked as support/contact confound",
                    "coverage is sufficient for both endpoints",
                ],
                "negative_witnesses": [
                    "large normalized 3D/XY distance with low overlap",
                    "object is floor-only support rather than attachment anchor",
                    "endpoint is hard room-surface to hard room-surface with no object-level attachment meaning",
                ],
                "uncertainty_sources": [
                    "large OBBs create false overlap",
                    "thin structures are missing in point/OBB representation",
                    "visual attachment boundary is occluded or unavailable",
                ],
            },
            "hanging on": {
                "template_type": "vertical_anchor_hanging_plausibility",
                "positive_witnesses": [
                    "near contact or overlap with wall/ceiling/rod/rack/shelf/door-like anchor",
                    "subject pose is vertically plausible relative to anchor",
                    "floor support is weak or absent",
                    "coverage is sufficient around the likely attachment region",
                ],
                "negative_witnesses": [
                    "far from plausible anchor",
                    "subject appears floor-supported with no anchor proximity",
                    "anchor category is implausible for hanging",
                ],
                "uncertainty_sources": [
                    "small hooks/cables/handles absent from point geometry",
                    "wall-mounted objects can be under-segmented",
                    "multi-view evidence may be needed to confirm hanging boundary",
                ],
            },
            "connected to": {
                "template_type": "weak_functional_connection_proxy",
                "positive_witnesses": [
                    "near contact or overlap between endpoints",
                    "endpoint labels suggest connector/pipe/cable/device/furniture linkage",
                    "coverage supports both endpoints",
                ],
                "negative_witnesses": [
                    "large separation with no overlap",
                    "pure room-surface or floor-support relation with no connection semantics",
                ],
                "uncertainty_sources": [
                    "functional connection is not always visible in OBB geometry",
                    "visual connector evidence may be necessary",
                    "treat as diagnostic until visual/mesh audit confirms usefulness",
                ],
            },
        },
        "continuous_evidence_factors": [
            {
                "factor": "near_contact_distance",
                "source_features": ["normalized_distance_3d", "normalized_distance_xy", "distance_3d", "distance_xy"],
                "direction": "lower_is_more_supportive",
            },
            {
                "factor": "projected_overlap",
                "source_features": ["projected_iou_xy", "projected_subject_overlap_ratio", "projected_object_overlap_ratio"],
                "direction": "higher_is_more_supportive_but_large_obb_overlap_can_be_uncertain",
            },
            {
                "factor": "relative_vertical_anchor",
                "source_features": ["center_delta_z", "normalized_center_delta_z", "subject_bottom_z", "subject_top_z", "object_bottom_z", "object_top_z"],
                "direction": "predicate_specific",
            },
            {
                "factor": "floor_support_confound",
                "source_features": ["vertical_gap_subject_on_object", "object_label", "subject_label"],
                "direction": "higher_confound_reduces_attachment_reliability",
            },
            {
                "factor": "anchor_affordance_bucket",
                "source_features": ["subject_label", "object_label"],
                "direction": "label_based_schema_probe_only_control_or_audit_axis",
            },
            {
                "factor": "coverage",
                "source_features": ["raw_feature_join_state", "endpoint_geometry_available", "optional_view_coverage_audit"],
                "direction": "separates missing evidence from negative evidence",
            },
            {
                "factor": "uncertainty",
                "source_features": ["thin_structure_flag", "large_obb_flag", "occlusion_or_view_gap_flag", "functional_connection_ambiguity"],
                "direction": "abstain_or_defer_if_high",
            },
        ],
        "provisional_statuses_for_capacity_scan": [
            "supported_candidate",
            "contradicted_candidate",
            "uncertain_candidate",
            "missing_geometry",
            "unsupported_template",
        ],
    }


def build_predicate_templates_rows(schema: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for predicate, template in schema["predicate_templates"].items():
        rows.append(
            {
                "predicate_label": predicate,
                "template_type": template["template_type"],
                "positive_witnesses": "; ".join(template["positive_witnesses"]),
                "negative_witnesses": "; ".join(template["negative_witnesses"]),
                "uncertainty_sources": "; ".join(template["uncertainty_sources"]),
                "primary_capacity_role": "candidate" if predicate in {"attached to", "hanging on"} else "diagnostic_until_visual_or_mesh_audit",
            }
        )
    return rows


def build_capacity_scan_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_attachment_deferred_capacity_scan_contract_v1",
        "next_todo": NEXT_TODO,
        "input_paths": {
            "match_rows": rel_path(RGA_ROOT / "match_rows.jsonl"),
            "v14_feasibility_summary": rel_path(DEFAULT_FEASIBILITY_DIR / "summary.json"),
            "v16_path_decision_summary": rel_path(DEFAULT_DECISION_DIR / "summary.json"),
        },
        "split": "train_only",
        "scan_scope": {
            "family": "attachment_deferred",
            "predicates": PREDICATES,
            "expected_match_rows_per_predicate_from_v14": 185346,
            "expected_total_match_rows_from_v14": 556038,
            "current_hl_lh_queue_rows_expected": 0,
        },
        "raw_feature_join_policy": {
            "join_key": "identity.directed_pair_id",
            "primary_join_source": "support_contact rows with geometry.raw_features",
            "fallback_join_source": "relative_vertical rows with geometry.raw_features",
            "reason": "Attachment rows currently carry no raw_features because their predicate family is unsupported, but the same directed pair has OBB pair features in other checkable families.",
            "minimum_join_coverage": 0.95,
        },
        "hard_filters": [
            "missing_directed_pair_id",
            "missing_subject_or_object_label",
            "self_loop_or_identical_node_if_present",
            "no_pair_raw_features_after_join",
        ],
        "do_not_filter_but_mark_uncertain": [
            "floor_anchor_for_attachment",
            "hard_room_surface_to_hard_room_surface_pair",
            "large_obb_overlap_confound",
            "thin_structure_or_connector_likely_missing",
            "connected_to_functional_connection_without_visual_confirmation",
        ],
        "probe_cells": [
            {
                "cell_id": "A1_attached_near_anchor_supported_candidate",
                "predicate_label": "attached to",
                "provisional_status": "supported_candidate",
                "target_preview_rows": 40,
                "minimum_capacity_rows": 80,
            },
            {
                "cell_id": "A2_attached_far_or_floor_confound_candidate",
                "predicate_label": "attached to",
                "provisional_status": "contradicted_or_uncertain_candidate",
                "target_preview_rows": 40,
                "minimum_capacity_rows": 80,
            },
            {
                "cell_id": "H1_hanging_anchor_supported_candidate",
                "predicate_label": "hanging on",
                "provisional_status": "supported_candidate",
                "target_preview_rows": 40,
                "minimum_capacity_rows": 80,
            },
            {
                "cell_id": "H2_hanging_no_anchor_or_floor_supported_candidate",
                "predicate_label": "hanging on",
                "provisional_status": "contradicted_or_uncertain_candidate",
                "target_preview_rows": 40,
                "minimum_capacity_rows": 80,
            },
            {
                "cell_id": "C1_connected_near_or_overlap_diagnostic",
                "predicate_label": "connected to",
                "provisional_status": "supported_or_uncertain_candidate",
                "target_preview_rows": 30,
                "minimum_capacity_rows": 60,
            },
            {
                "cell_id": "C2_connected_far_or_functional_ambiguous_diagnostic",
                "predicate_label": "connected to",
                "provisional_status": "contradicted_or_uncertain_candidate",
                "target_preview_rows": 30,
                "minimum_capacity_rows": 60,
            },
            {
                "cell_id": "U1_attachment_missing_or_uncertain_coverage_audit",
                "predicate_label": "*",
                "provisional_status": "missing_or_uncertain_coverage",
                "target_preview_rows": 20,
                "minimum_capacity_rows": 20,
            },
        ],
        "preview_total_rows": 240,
        "caps_for_capacity_preview": {
            "max_rows_per_scan": 4,
            "max_rows_per_subgraph": 2,
            "max_rows_per_directed_pair": 1,
            "max_rows_per_visible_pair": 3,
            "max_single_predicate_share": 0.40,
            "max_single_anchor_bucket_share": 0.45,
            "max_single_rank_band_share": 0.45,
        },
        "pass_criteria": {
            "validation_errors": 0,
            "raw_feature_join_coverage_min": 0.95,
            "attached_to_supported_and_counter_capacity_min": 80,
            "hanging_on_supported_and_counter_capacity_min": 80,
            "connected_to_diagnostic_capacity_min": 60,
            "preview_rows_after_caps_min": 160,
            "forbidden_visible_field_hits": 0,
        },
        "if_capacity_passes": "produce attachment witness capacity report and decide whether candidate mining is allowed",
        "if_capacity_fails": "freeze attachment as schema limitation evidence and consider multi-view audit packet design before label mining",
    }


def build_label_surface_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_attachment_deferred_label_surface_contract_v1",
        "label_sheet_now": False,
        "visible_fields_allowed_later": [
            "blind_review_id",
            "candidate_relation",
            "subject_label",
            "predicate_label",
            "object_label",
            "relation_family_visible",
            "non_template_geometry_factor_summary",
            "coverage_note",
            "anchor_plausibility_note",
            "uncertainty_note",
            "review_question",
            "relation_reliability_state",
            "geometry_support_state",
            "relation_usefulness_state",
            "primary_reason",
            "uncertainty_reason",
            "review_notes",
        ],
        "visible_fields_forbidden_later": [
            "queue_kind",
            "rank_band",
            "semantic_geometry_bucket",
            "geometry_status",
            "p_geom_valid",
            "attachment_witness_score",
            "provisional_status",
            "machine_hint",
            "label_match_status",
            "quota_cell_id",
            "direct_accept_reject_hint",
            "HL",
            "LH",
            "RGA-HL",
            "RGA-LH",
        ],
        "multi_view_policy": {
            "current_stage": "audit_or_confirmation_only",
            "not_deployable_input": True,
            "allowed_audit_use": [
                "confirm contact boundary visibility",
                "flag occlusion or thin-structure missingness",
                "distinguish hanging/attached plausibility from mere proximity",
            ],
        },
    }


def write_schema_markdown(path: Path, schema: dict[str, Any], contract: dict[str, Any], label_surface: dict[str, Any]) -> None:
    lines = [
        "# Attachment Witness Schema Probe Plan",
        "",
        "## Purpose",
        "",
        "`attached to`, `hanging on`, `connected to`를 현재 RGA의 `unsupported_family` 상태에서",
        "geometry-checkable evidence family로 올릴 수 있는지 검증하기 위한 schema plan이다.",
        "이 문서는 label sheet가 아니며 posterior evidence도 아니다.",
        "",
        "## Predicate Scope",
        "",
        "```text",
        "\n".join(schema["predicate_scope"]),
        "```",
        "",
        "## Evidence Factors",
        "",
    ]
    for factor in schema["continuous_evidence_factors"]:
        lines.extend(
            [
                f"### {factor['factor']}",
                "",
                f"- source: `{', '.join(factor['source_features'])}`",
                f"- direction: `{factor['direction']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Capacity Scan Contract",
            "",
            "```text",
            f"next_todo = {contract['next_todo']}",
            f"expected_total_match_rows_from_v14 = {contract['scan_scope']['expected_total_match_rows_from_v14']}",
            f"minimum_join_coverage = {contract['raw_feature_join_policy']['minimum_join_coverage']}",
            f"preview_total_rows = {contract['preview_total_rows']}",
            "```",
            "",
            "## Label Surface Boundary",
            "",
            "Forbidden later visible fields include:",
            "",
            "```text",
            "\n".join(label_surface["visible_fields_forbidden_later"]),
            "```",
            "",
            "Multi-view remains audit/confirmation evidence only at this stage.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    snap = summary["attachment_feasibility_snapshot"]
    lines = [
        "# H002 V17 Attachment-Deferred Witness Schema Probe Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Snapshot",
        "",
        "```text",
        f"attachment_rows = {snap['rows']}",
        f"checkable_rows_before_schema = {snap['checkable_rows']}",
        f"unsupported_share_before_schema = {snap['unsupported_share']}",
        f"predicates = {snap['top_predicates']}",
        "```",
        "",
        "## Decision",
        "",
        "The next step is a train-only capacity scan that joins attachment rows to pair-level raw geometry and computes typed attachment witnesses. No label sheet or posterior smoke is allowed yet.",
        "",
        "## Boundary",
        "",
        "This is not a posterior method result, not a benchmark result, and not a change to H001 or paper artifacts.",
        "",
        "## Next",
        "",
        "```text",
        summary["next_todo"],
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    decision_dir = as_abs(args.decision_dir)
    feasibility_dir = as_abs(args.feasibility_dir)
    output_dir = as_abs(args.output_dir)
    decision = read_json(decision_dir / "summary.json")
    feasibility = read_json(feasibility_dir / "summary.json")
    errors = validate_inputs(decision, feasibility)

    family_rows = {row["family"]: row for row in feasibility.get("family_inventory", [])}
    attachment = family_rows.get("attachment_deferred", {})
    witness_schema = build_witness_schema()
    predicate_rows = build_predicate_templates_rows(witness_schema)
    capacity_contract = build_capacity_scan_contract()
    label_surface_contract = build_label_surface_contract()

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "witness_schema.json", witness_schema)
    write_csv(output_dir / "predicate_templates.csv", predicate_rows)
    write_json(output_dir / "capacity_scan_contract.json", capacity_contract)
    write_json(output_dir / "label_surface_contract.json", label_surface_contract)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_schema_markdown(output_dir / "witness_schema.md", witness_schema, capacity_contract, label_surface_contract)

    status = STATUS if not errors else "h002_reliability_target_v17_attachment_deferred_witness_schema_probe_plan_validation_errors"
    next_todo = NEXT_TODO if not errors else EXPECTED_DECISION_NEXT
    summary = {
        "schema_version": "h002_reliability_target_v17_attachment_deferred_witness_schema_probe_plan_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "hidden_fields_as_model_input": False,
        },
        "input_paths": {
            "v16_path_decision_summary": rel_path(decision_dir / "summary.json"),
            "v14_feasibility_summary": rel_path(feasibility_dir / "summary.json"),
            "match_rows": rel_path(RGA_ROOT / "match_rows.jsonl"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "witness_schema": rel_path(output_dir / "witness_schema.json"),
            "witness_schema_md": rel_path(output_dir / "witness_schema.md"),
            "predicate_templates": rel_path(output_dir / "predicate_templates.csv"),
            "capacity_scan_contract": rel_path(output_dir / "capacity_scan_contract.json"),
            "label_surface_contract": rel_path(output_dir / "label_surface_contract.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "attachment_feasibility_snapshot": {
            "rows": attachment.get("rows"),
            "unique_scans": attachment.get("unique_scans"),
            "unique_subgraphs": attachment.get("unique_subgraphs"),
            "unique_directed_pairs": attachment.get("unique_directed_pairs"),
            "checkable_rows": attachment.get("checkable_rows"),
            "raw_feature_rows": attachment.get("raw_feature_rows"),
            "unsupported_rows": attachment.get("unsupported_rows"),
            "unsupported_share": attachment.get("unsupported_share"),
            "top_predicates": attachment.get("top_predicates"),
            "bucket_top100_counts": attachment.get("bucket_top100_counts"),
            "rank_band_counts": attachment.get("rank_band_counts"),
            "label_match_status_counts": attachment.get("label_match_status_counts"),
        },
        "selected_plan": {
            "route": "attachment_deferred_witness_schema_probe",
            "predicate_scope": PREDICATES,
            "capacity_scan_next": NEXT_TODO,
            "label_sheet_now": "blocked",
            "posterior_smoke_now": "blocked",
            "multi_view_policy": "audit_or_confirmation_only",
            "core_design": [
                "reuse pair-level raw geometry by directed_pair_id",
                "compile each attachment predicate into typed geometry/coverage/uncertainty witnesses",
                "treat connected-to as diagnostic unless capacity/audit shows OBB evidence is meaningful",
                "separate missing/unsupported evidence from negative geometry",
            ],
        },
        "capacity_scan_contract_summary": {
            "expected_total_match_rows_from_v14": capacity_contract["scan_scope"]["expected_total_match_rows_from_v14"],
            "minimum_raw_feature_join_coverage": capacity_contract["raw_feature_join_policy"]["minimum_join_coverage"],
            "preview_total_rows": capacity_contract["preview_total_rows"],
            "pass_criteria": capacity_contract["pass_criteria"],
        },
    }
    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"next_todo={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"attachment_rows={summary['attachment_feasibility_snapshot']['rows']}")
    print(f"checkable_rows_before_schema={summary['attachment_feasibility_snapshot']['checkable_rows']}")
    print(f"output_dir={summary['output_dir']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
