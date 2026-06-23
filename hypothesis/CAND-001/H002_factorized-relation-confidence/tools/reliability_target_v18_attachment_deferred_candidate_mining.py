#!/usr/bin/env python3
"""Create the H002 v18 attachment-deferred hidden-field-safe candidate packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_DECISION_DIR = RGA_ROOT / "reliability_target_v17_attachment_deferred_witness_schema_path_decision_after_capacity_scan"
DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v17_attachment_deferred_witness_schema_capacity_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_candidate_mining"

EXPECTED_DECISION_STATUS = "h002_reliability_target_v17_attachment_deferred_witness_schema_path_decision_select_attachment_candidate_mining"
EXPECTED_DECISION_NEXT = "reliability_target_v18_attachment_deferred_candidate_mining"
EXPECTED_SELECTED_PATH = "select_v18_attachment_deferred_candidate_mining_attached_hanging_primary_connected_diagnostic"

STATUS_READY = "h002_reliability_target_v18_attachment_deferred_candidate_mining_ready_for_label_fill"
STATUS_ERRORS = "h002_reliability_target_v18_attachment_deferred_candidate_mining_errors"
NEXT_TODO = "reliability_target_v18_attachment_deferred_label_fill"

TARGET_ROWS = 240
PRIMARY_CELLS = {
    "A1_attached_near_anchor_supported_candidate": 40,
    "A2_attached_far_or_floor_confound_candidate": 40,
    "H1_hanging_anchor_supported_candidate": 40,
    "H2_hanging_no_anchor_or_floor_supported_candidate": 40,
}
DIAGNOSTIC_CELLS = {
    "C1_connected_near_or_overlap_diagnostic": 30,
    "C2_connected_far_or_functional_ambiguous_diagnostic": 30,
}
AUDIT_CELLS = {
    "U1_attachment_missing_or_uncertain_coverage_audit": 20,
}
REQUIRED_CELLS = {**PRIMARY_CELLS, **DIAGNOSTIC_CELLS, **AUDIT_CELLS}

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "scene_context_summary_v18",
    "geometry_witness_summary_v18",
    "attachment_witness_summary_v18",
    "coverage_summary_v18",
    "uncertainty_summary_v18",
    "review_question_v18",
    "relation_reliability_state_v18",
    "geometry_support_state_v18",
    "relation_usefulness_state_v18",
    "endpoint_identity_state_v18",
    "coverage_state_v18",
    "primary_reason_v18",
    "uncertainty_reason_v18",
    "review_notes_v18",
]

FORBIDDEN_VISIBLE_PATTERNS = [
    "cell_id",
    "cell id",
    "provisional",
    "anchor_bucket",
    "anchor bucket",
    "rank_band",
    "rank band",
    "machine_hint",
    "machine hint",
    "geometry_status",
    "geometry status",
    "reason_family",
    "reason family",
    "sampling_queue",
    "sampling queue",
    "bucket_top100",
    "semantic score",
    "semantic_score",
    "source score",
    "source_score",
    "label_match",
    "matched_predicate",
    "rga-",
    "rga_",
    "supported_candidate",
    "contradicted_candidate",
    "uncertain_candidate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-dir", type=Path, default=DEFAULT_DECISION_DIR)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


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


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
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


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_decision(decision: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if decision.get("status") != EXPECTED_DECISION_STATUS:
        errors.append({"error_type": "unexpected_decision_status", "expected": EXPECTED_DECISION_STATUS, "actual": decision.get("status")})
    if decision.get("next_todo") != EXPECTED_DECISION_NEXT:
        errors.append({"error_type": "unexpected_decision_next_todo", "expected": EXPECTED_DECISION_NEXT, "actual": decision.get("next_todo")})
    if decision.get("selected_path") != EXPECTED_SELECTED_PATH:
        errors.append({"error_type": "unexpected_selected_path", "expected": EXPECTED_SELECTED_PATH, "actual": decision.get("selected_path")})
    if decision.get("validation_errors") != 0:
        errors.append({"error_type": "decision_validation_errors_present", "actual": decision.get("validation_errors")})

    boundary = decision.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "label_sheet_created",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "decision_boundary_violation", "key": key, "actual": boundary.get(key)})

    plan = decision.get("selected_plan", {})
    if plan.get("candidate_mining_allowed") is not True:
        errors.append({"error_type": "candidate_mining_not_allowed_by_decision", "actual": plan.get("candidate_mining_allowed")})
    if plan.get("primary_relation_scope") != ["attached to", "hanging on"]:
        errors.append({"error_type": "unexpected_primary_relation_scope", "actual": plan.get("primary_relation_scope")})
    if plan.get("diagnostic_relation_scope") != ["connected to"]:
        errors.append({"error_type": "unexpected_diagnostic_relation_scope", "actual": plan.get("diagnostic_relation_scope")})
    return errors


def bin_range(value: float | None, cuts: tuple[float, float], labels: tuple[str, str, str], unknown: str) -> str:
    if value is None:
        return unknown
    if value <= cuts[0]:
        return labels[0]
    if value <= cuts[1]:
        return labels[1]
    return labels[2]


def distance_summary(row: dict[str, Any]) -> str:
    value = as_float(row.get("normalized_distance_3d"))
    if value is None:
        value = as_float(row.get("normalized_distance_xy"))
    return bin_range(
        value,
        (0.25, 0.75),
        ("very near 3D separation", "moderate 3D separation", "wide 3D separation"),
        "unknown 3D separation",
    )


def horizontal_summary(row: dict[str, Any]) -> str:
    value = as_float(row.get("normalized_distance_xy"))
    return bin_range(
        value,
        (0.25, 0.75),
        ("very near horizontal separation", "moderate horizontal separation", "wide horizontal separation"),
        "unknown horizontal separation",
    )


def overlap_summary(row: dict[str, Any]) -> str:
    values = [
        as_float(row.get("projected_iou_xy")),
        as_float(row.get("projected_subject_overlap_ratio")),
        as_float(row.get("projected_object_overlap_ratio")),
    ]
    values = [value for value in values if value is not None]
    if not values:
        return "unknown footprint overlap"
    value = max(values)
    if value >= 0.35:
        return "large footprint overlap"
    if value >= 0.10:
        return "partial footprint overlap"
    return "little footprint overlap"


def vertical_summary(row: dict[str, Any]) -> str:
    value = as_float(row.get("normalized_center_delta_z"))
    if value is None:
        value = as_float(row.get("center_delta_z"))
    if value is None:
        return "unknown vertical placement"
    if value > 0.25:
        return "subject center appears above object center"
    if value < -0.25:
        return "subject center appears below object center"
    return "subject and object appear in a similar height band"


def uncertainty_summary(flags: list[str]) -> str:
    if not flags:
        return "no extra ambiguity flag from the 3D pair summary"
    mapping = {
        "floor_support_confound": "ordinary support contact may explain the layout",
        "functional_connection_ambiguous_without_visual_or_mesh": "functional connection may need visual or mesh confirmation",
        "hard_surface_pair": "broad structural surfaces may make the directed relation ambiguous",
        "large_obb_overlap_confound": "large boxes can overstate footprint overlap",
        "thin_structure_or_boundary_missing": "thin contact regions may be missing from box-level geometry",
        "typed_witness_ambiguous": "3D cues are mixed or incomplete",
    }
    return "; ".join(mapping.get(flag, "unmapped ambiguity cue") for flag in flags)


def relation_family_visible(row: dict[str, Any]) -> str:
    predicate = str(row.get("predicate_label"))
    if predicate == "attached to":
        return "attachment-like relation"
    if predicate == "hanging on":
        return "hanging or mounted relation"
    if predicate == "connected to":
        return "connection-like relation"
    return "attachment-family relation"


def attachment_witness_summary(row: dict[str, Any]) -> str:
    predicate = str(row.get("predicate_label"))
    base = f"{distance_summary(row)}; {overlap_summary(row)}; {vertical_summary(row)}"
    if predicate == "attached to":
        return base + "; review whether the object labels and 3D layout support a physical attachment rather than ordinary proximity or support"
    if predicate == "hanging on":
        return base + "; review whether the layout suggests a hanging or mounted relation rather than floor support or loose proximity"
    if predicate == "connected to":
        return base + "; review whether the relation needs evidence beyond box-level geometry to establish a functional connection"
    return base


def visible_row(row: dict[str, Any], review_card: str) -> dict[str, str]:
    relation = f"{row.get('subject_label')} {row.get('predicate_label')} {row.get('object_label')}"
    geometry = f"{distance_summary(row)}; {horizontal_summary(row)}; {overlap_summary(row)}; {vertical_summary(row)}"
    return {
        "blind_review_id": "attv18_" + stable_hash(str(row.get("prediction_id")))[:12],
        "review_card": review_card,
        "candidate_relation": relation,
        "subject_label": str(row.get("subject_label")),
        "predicate_label": str(row.get("predicate_label")),
        "object_label": str(row.get("object_label")),
        "relation_family_visible": relation_family_visible(row),
        "scene_context_summary_v18": "review the directed relation using only object labels and the 3D layout summary shown here",
        "geometry_witness_summary_v18": geometry,
        "attachment_witness_summary_v18": attachment_witness_summary(row),
        "coverage_summary_v18": "3D pair geometry is available for this directed object pair; image or multi-view evidence is not used in this packet",
        "uncertainty_summary_v18": uncertainty_summary(list(row.get("uncertainty_flags") or [])),
        "review_question_v18": "Should this directed relation be treated as a reliable scene-graph edge under the visible 3D evidence?",
        "relation_reliability_state_v18": "",
        "geometry_support_state_v18": "",
        "relation_usefulness_state_v18": "",
        "endpoint_identity_state_v18": "",
        "coverage_state_v18": "",
        "primary_reason_v18": "",
        "uncertainty_reason_v18": "",
        "review_notes_v18": "",
    }


def raw_feature_subset(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "normalized_distance_3d",
        "normalized_distance_xy",
        "projected_iou_xy",
        "projected_subject_overlap_ratio",
        "projected_object_overlap_ratio",
        "center_delta_z",
        "normalized_center_delta_z",
        "vertical_gap_subject_on_object",
        "near_contact",
        "loose_near_contact",
        "projected_overlap_support",
        "far_separated",
    ]
    return {key: row.get(key) for key in keys if key in row}


def role_for_cell(cell_id: str) -> str:
    if cell_id in PRIMARY_CELLS:
        return "primary_binary_candidate"
    if cell_id in DIAGNOSTIC_CELLS:
        return "diagnostic_candidate"
    if cell_id in AUDIT_CELLS:
        return "uncertainty_coverage_audit"
    return "unknown"


def geometry_status_for_row(row: dict[str, Any]) -> str:
    status = str(row.get("provisional_status_hidden") or "")
    if status == "supported_candidate":
        return "typed_witness_supportive"
    if status == "contradicted_candidate":
        return "typed_witness_contradictory"
    if status == "uncertain_candidate":
        return "typed_witness_uncertain"
    return "typed_witness_unmapped"


def reason_family_for_cell(cell_id: str) -> str:
    return {
        "A1_attached_near_anchor_supported_candidate": "attached_near_object_or_surface",
        "A2_attached_far_or_floor_confound_candidate": "attached_far_or_support_confound",
        "H1_hanging_anchor_supported_candidate": "hanging_near_mounting_surface",
        "H2_hanging_no_anchor_or_floor_supported_candidate": "hanging_no_mounting_or_support_confound",
        "C1_connected_near_or_overlap_diagnostic": "connected_near_or_overlap_diagnostic",
        "C2_connected_far_or_functional_ambiguous_diagnostic": "connected_far_or_functional_ambiguous",
        "U1_attachment_missing_or_uncertain_coverage_audit": "missing_or_uncertain_coverage_audit",
    }.get(cell_id, "unknown")


def hidden_row(row: dict[str, Any], visible: dict[str, str]) -> dict[str, Any]:
    cell_id = str(row.get("cell_id_hidden"))
    return {
        "schema_version": "h002_reliability_target_v18_attachment_deferred_candidate_hidden_v1",
        "blind_review_id": visible["blind_review_id"],
        "prediction_id": row.get("prediction_id"),
        "split": "train",
        "source_id": "open3dsg_train_full",
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_family": "attachment_deferred",
        "predicate_label": row.get("predicate_label"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "candidate_role_hidden": role_for_cell(cell_id),
        "cell_id_hidden": cell_id,
        "provisional_status_hidden": row.get("provisional_status_hidden"),
        "anchor_bucket_hidden": row.get("anchor_bucket_hidden"),
        "rank_band_hidden": row.get("rank_band_hidden"),
        "semantic_rank_hidden": row.get("semantic_rank_hidden"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm_hidden"),
        "bucket_top100_hidden": row.get("bucket_top100_hidden"),
        "sampling_queue_hidden": cell_id,
        "geometry_status_hidden": geometry_status_for_row(row),
        "reason_family_hidden": reason_family_for_cell(cell_id),
        "machine_hint_hidden": reason_family_for_cell(cell_id),
        "label_match_status_hidden": row.get("label_match_status_hidden"),
        "matched_predicates_hidden": row.get("matched_predicates_hidden"),
        "directed_pair_id_hidden": row.get("directed_pair_id"),
        "source_geometry_family_hidden": row.get("source_geometry_family"),
        "source_geometry_predicate_hidden": row.get("source_geometry_predicate"),
        "raw_feature_join_state_hidden": row.get("raw_feature_join_state"),
        "attachment_witness_support_score_hidden": row.get("attachment_witness_support_score_hidden"),
        "attachment_witness_contradiction_score_hidden": row.get("attachment_witness_contradiction_score_hidden"),
        "uncertainty_flags_hidden": row.get("uncertainty_flags") or [],
        "raw_features_hidden": raw_feature_subset(row),
        "reviewer_visible": False,
        "posterior_input_allowed": False,
        "model_input_allowed": False,
    }


def write_review_card(path: Path, row: dict[str, str]) -> None:
    lines = [
        f"# {row['candidate_relation']}",
        "",
        "## Visible Evidence",
        "",
        f"- Relation family: {row['relation_family_visible']}",
        f"- Geometry: {row['geometry_witness_summary_v18']}",
        f"- Relation cue: {row['attachment_witness_summary_v18']}",
        f"- Coverage: {row['coverage_summary_v18']}",
        f"- Ambiguity: {row['uncertainty_summary_v18']}",
        "",
        "## Question",
        "",
        row["review_question_v18"],
        "",
        "## Fill Fields",
        "",
        "- relation_reliability_state_v18:",
        "- geometry_support_state_v18:",
        "- relation_usefulness_state_v18:",
        "- endpoint_identity_state_v18:",
        "- coverage_state_v18:",
        "- primary_reason_v18:",
        "- uncertainty_reason_v18:",
        "- review_notes_v18:",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def leakage_hits(visible_rows: list[dict[str, str]], review_card_dir: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in visible_rows:
        for field, value in row.items():
            lower = str(value).lower()
            for pattern in FORBIDDEN_VISIBLE_PATTERNS:
                if pattern in lower:
                    hits.append({"surface": "label_sheet", "blind_review_id": row["blind_review_id"], "field": field, "pattern": pattern})
        card_path = review_card_dir / f"{row['blind_review_id']}.md"
        text = card_path.read_text(encoding="utf-8").lower()
        for pattern in FORBIDDEN_VISIBLE_PATTERNS:
            if pattern in text:
                hits.append({"surface": "review_card", "blind_review_id": row["blind_review_id"], "field": str(card_path), "pattern": pattern})
    return hits


def cell_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_cell[str(row.get("cell_id_hidden"))].append(row)
    summary: list[dict[str, Any]] = []
    for cell_id, target in REQUIRED_CELLS.items():
        cell_rows = by_cell.get(cell_id, [])
        summary.append(
            {
                "cell_id": cell_id,
                "role": role_for_cell(cell_id),
                "target_rows": target,
                "selected_rows": len(cell_rows),
                "predicate_counts": json.dumps(dict(Counter(str(row.get("predicate_label")) for row in cell_rows)), sort_keys=True),
                "provisional_status_counts_hidden": json.dumps(dict(Counter(str(row.get("provisional_status_hidden")) for row in cell_rows)), sort_keys=True),
                "anchor_bucket_counts_hidden": json.dumps(dict(Counter(str(row.get("anchor_bucket_hidden")) for row in cell_rows).most_common(8)), sort_keys=True),
                "rank_band_counts_hidden": json.dumps(dict(Counter(str(row.get("rank_band_hidden")) for row in cell_rows).most_common(8)), sort_keys=True),
                "unique_scans": len({str(row.get("scan_id")) for row in cell_rows}),
                "unique_subgraphs": len({str(row.get("subgraph_id")) for row in cell_rows}),
                "unique_directed_pairs": len({str(row.get("directed_pair_id")) for row in cell_rows}),
            }
        )
    return summary


def validate_outputs(
    visible_rows: list[dict[str, str]],
    hidden_rows: list[dict[str, Any]],
    internal_rows: list[dict[str, Any]],
    leaks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(visible_rows) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_visible_row_count", "expected": TARGET_ROWS, "actual": len(visible_rows)})
    if len(hidden_rows) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_hidden_row_count", "expected": TARGET_ROWS, "actual": len(hidden_rows)})
    if len(internal_rows) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_internal_row_count", "expected": TARGET_ROWS, "actual": len(internal_rows)})
    if leaks:
        errors.append({"error_type": "visible_leakage_hits_present", "count": len(leaks)})

    blind_ids = [row["blind_review_id"] for row in visible_rows]
    if len(set(blind_ids)) != len(blind_ids):
        errors.append({"error_type": "duplicate_blind_review_id"})
    prediction_ids = [str(row["prediction_id"]) for row in hidden_rows]
    if len(set(prediction_ids)) != len(prediction_ids):
        errors.append({"error_type": "duplicate_prediction_id"})
    directed_pairs = [str(row["directed_pair_id_hidden"]) for row in hidden_rows]
    if len(set(directed_pairs)) != len(directed_pairs):
        errors.append({"error_type": "duplicate_directed_pair"})

    by_cell = Counter(str(row.get("cell_id_hidden")) for row in hidden_rows)
    for cell_id, target in REQUIRED_CELLS.items():
        actual = by_cell.get(cell_id, 0)
        if actual != target:
            errors.append({"error_type": "cell_count_mismatch", "cell_id": cell_id, "expected": target, "actual": actual})
    unexpected_cells = sorted(set(by_cell) - set(REQUIRED_CELLS))
    if unexpected_cells:
        errors.append({"error_type": "unexpected_cells", "cells": unexpected_cells})

    primary = sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "primary_binary_candidate")
    diagnostic = sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "diagnostic_candidate")
    audit = sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "uncertainty_coverage_audit")
    if primary != 160:
        errors.append({"error_type": "primary_candidate_count_mismatch", "expected": 160, "actual": primary})
    if diagnostic != 60:
        errors.append({"error_type": "diagnostic_candidate_count_mismatch", "expected": 60, "actual": diagnostic})
    if audit != 20:
        errors.append({"error_type": "audit_candidate_count_mismatch", "expected": 20, "actual": audit})

    for row in hidden_rows:
        if row.get("reviewer_visible") is not False:
            errors.append({"error_type": "hidden_row_marked_visible", "blind_review_id": row.get("blind_review_id")})
        if row.get("model_input_allowed") is not False:
            errors.append({"error_type": "hidden_row_model_input_allowed", "blind_review_id": row.get("blind_review_id")})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V18 Attachment Candidate Mining",
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
        "## Result",
        "",
        "```text",
        f"selected_rows = {counts['selected_rows']}",
        f"primary_binary_candidate_rows = {counts['primary_binary_candidate_rows']}",
        f"diagnostic_rows = {counts['diagnostic_rows']}",
        f"uncertainty_audit_rows = {counts['uncertainty_audit_rows']}",
        f"attached_to_rows = {counts['attached_to_rows']}",
        f"hanging_on_rows = {counts['hanging_on_rows']}",
        f"connected_to_rows = {counts['connected_to_rows']}",
        f"unique_scans = {counts['unique_scans']}",
        f"unique_subgraphs = {counts['unique_subgraphs']}",
        f"unique_directed_pairs = {counts['unique_directed_pairs']}",
        f"visible_leakage_hits = {counts['visible_leakage_hits']}",
        "```",
        "",
        "## Boundary",
        "",
        "This packet is train-only and label-ready, but not label-filled. It does not train or evaluate a posterior.",
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


def main() -> None:
    args = parse_args()
    decision_dir = as_abs(args.decision_dir)
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)
    review_card_dir = output_dir / "review_cards_v18"

    decision = read_json(decision_dir / "summary.json")
    validation_errors = validate_decision(decision)
    internal_rows = read_jsonl(capacity_dir / "selection_preview_internal.jsonl")

    visible_rows: list[dict[str, str]] = []
    hidden_rows: list[dict[str, Any]] = []
    selected_internal_rows: list[dict[str, Any]] = []
    for row in internal_rows:
        blind_id = "attv18_" + stable_hash(str(row.get("prediction_id")))[:12]
        review_card = f"review_cards_v18/{blind_id}.md"
        visible = visible_row(row, review_card)
        hidden = hidden_row(row, visible)
        visible_rows.append(visible)
        hidden_rows.append(hidden)
        selected_internal_rows.append(row)
        write_review_card(review_card_dir / f"{blind_id}.md", visible)

    leaks = leakage_hits(visible_rows, review_card_dir)
    validation_errors.extend(validate_outputs(visible_rows, hidden_rows, selected_internal_rows, leaks))
    status = STATUS_READY if not validation_errors else STATUS_ERRORS

    counts = {
        "selected_rows": len(visible_rows),
        "primary_binary_candidate_rows": sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "primary_binary_candidate"),
        "diagnostic_rows": sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "diagnostic_candidate"),
        "uncertainty_audit_rows": sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "uncertainty_coverage_audit"),
        "attached_to_rows": sum(1 for row in hidden_rows if row["predicate_label"] == "attached to"),
        "hanging_on_rows": sum(1 for row in hidden_rows if row["predicate_label"] == "hanging on"),
        "connected_to_rows": sum(1 for row in hidden_rows if row["predicate_label"] == "connected to"),
        "unique_scans": len({str(row["scan_id"]) for row in hidden_rows}),
        "unique_subgraphs": len({str(row["subgraph_id"]) for row in hidden_rows}),
        "unique_directed_pairs": len({str(row["directed_pair_id_hidden"]) for row in hidden_rows}),
        "unique_visible_label_pairs": len({f"{row['subject_label']}|{row['object_label']}" for row in hidden_rows}),
        "visible_leakage_hits": len(leaks),
    }

    cell_summary = cell_summary_rows(selected_internal_rows)
    boundary = {
        "split": "train_only",
        "validation_usage": False,
        "test_usage": False,
        "fills_new_labels": False,
        "ingests_existing_labels": False,
        "label_sheet_created": True,
        "trains_new_posterior": False,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "h001_artifacts_modified": False,
        "rga_redefined_as_lh_only": False,
        "multi_view_as_model_input": False,
        "hidden_fields_as_model_input": False,
    }
    summary = {
        "schema_version": "h002_reliability_target_v18_attachment_deferred_candidate_mining_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO,
        "validation_errors": len(validation_errors),
        "boundary": boundary,
        "counts": counts,
        "cell_summary": cell_summary,
        "input_paths": {
            "path_decision_summary": rel_path(decision_dir / "summary.json"),
            "capacity_preview": rel_path(capacity_dir / "selection_preview_internal.jsonl"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "label_ready_sheet": rel_path(output_dir / "label_ready_sheet_v18.tsv"),
            "hidden_audit_manifest": rel_path(output_dir / "hidden_audit_manifest_v18.jsonl"),
            "selected_candidates_internal": rel_path(output_dir / "selected_candidates_internal.jsonl"),
            "cell_summary": rel_path(output_dir / "cell_summary.csv"),
            "visible_leakage_hits": rel_path(output_dir / "visible_leakage_hits.jsonl"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
            "review_cards": rel_path(review_card_dir),
        },
        "label_surface_policy": {
            "visible_sheet_hides_construction_fields": True,
            "primary_relation_scope": ["attached to", "hanging on"],
            "diagnostic_relation_scope": ["connected to"],
            "multi_view_policy": "audit_or_confirmation_only",
            "posterior_smoke_allowed": False,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(output_dir / "label_ready_sheet_v18.tsv", visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_dir / "hidden_audit_manifest_v18.jsonl", hidden_rows)
    write_jsonl(output_dir / "selected_candidates_internal.jsonl", selected_internal_rows)
    write_jsonl(output_dir / "visible_leakage_hits.jsonl", leaks)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(output_dir / "cell_summary.csv", cell_summary)
    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)

    print(f"status={status}")
    print(f"next_todo={NEXT_TODO}")
    print(f"validation_errors={len(validation_errors)}")
    print(f"selected_rows={counts['selected_rows']}")
    print(f"primary_binary_candidate_rows={counts['primary_binary_candidate_rows']}")
    print(f"diagnostic_rows={counts['diagnostic_rows']}")
    print(f"uncertainty_audit_rows={counts['uncertainty_audit_rows']}")
    print(f"visible_leakage_hits={counts['visible_leakage_hits']}")
    print(f"output_dir={rel_path(output_dir)}")


if __name__ == "__main__":
    main()
