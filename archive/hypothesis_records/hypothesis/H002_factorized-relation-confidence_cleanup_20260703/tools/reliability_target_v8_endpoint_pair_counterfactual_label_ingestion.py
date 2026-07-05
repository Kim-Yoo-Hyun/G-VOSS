#!/usr/bin/env python3
"""Ingest v8 endpoint-pair counterfactual labels after proxy fill."""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

FILL_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_label_fill_codex_proxy_user_requested"
READINESS_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_label_readiness_codex_proxy_user_requested"

DEFAULT_COMPLETED_SHEET = FILL_DIR / "completed_v8_endpoint_pair_counterfactual_label_sheet_codex_proxy_user_requested.tsv"
DEFAULT_FILL_SUMMARY = FILL_DIR / "summary.json"
DEFAULT_SCHEMA = READINESS_DIR / "label_schema.json"
DEFAULT_MANIFEST = READINESS_DIR / "ready_manifest_post_label_only.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_label_ingestion_codex_proxy_user_requested"

LABEL_SOURCE = "codex_proxy_reliability_target_v8_endpoint_pair_counterfactual_user_requested"
RELIABILITY_MULTICLASS = "relation_reliability_state_v6_multiclass_target"
RELIABILITY_BINARY = "relation_reliability_v6_binary_target"
GEOMETRY_TARGET = "geometry_support_v6_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v6_binary_target"

COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_v6",
    "pair_evaluability_v6",
    "geometry_support_v6",
    "relation_usefulness_v6",
    "relation_reliability_state_v6",
    "primary_reason_v6",
    "uncertainty_reason_v6",
]

VISIBLE_GROUP_KEYS = [
    "predicate_family",
    "predicate_label",
    "subject_label",
    "object_label",
    "evidence_packet_status",
    "packet_gap_decision",
]

HIDDEN_GROUP_KEYS = [
    "semantic_geometry_bucket_hidden",
    "rank_band_hidden",
    "source_queue_hidden",
    "geometry_status_hidden",
    "h001_verification_status_hidden",
    "label_match_status_hidden",
    "label_geometry_bucket_hidden",
    "machine_hint_hidden",
    "object_family_cell_hidden",
    "subject_object_family_cell_hidden",
    "subject_object_label_pair_hidden",
    "endpoint_pattern_hidden",
    "exact_endpoint_pair_key_hidden",
    "undirected_endpoint_pair_key_hidden",
    "scene_label_pair_key_hidden",
    "v8_group_level_hidden",
    "v8_group_key_hidden",
    "v8_group_row_count_hidden",
    "v8_group_predicate_count_hidden",
    "v8_group_has_queue_mix_hidden",
    "v8_group_has_family_mix_hidden",
    "v8_group_has_vertical_contradiction_hidden",
    "v8_group_has_support_alternative_hidden",
    "v8_group_geometry_range_hidden",
    "v8_group_rank_range_hidden",
    "structural_pair_hidden",
    "hard_room_surface_pair_hidden",
    "asset_packet_source_hidden",
    "packet_source_hidden",
    "replacement_source_hidden",
    "replacement_for_family_bucket_hidden",
    "row_gap_decision_hidden",
    "normalized_evidence_status_hidden",
    "packet_status_hidden",
]

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "normalized_mutual_information": 0.20,
    "class_rate_range": 0.70,
    "large_group_rows": 20,
    "large_group_purity": 0.90,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-sheet", type=Path, default=DEFAULT_COMPLETED_SHEET)
    parser.add_argument("--fill-summary", type=Path, default=DEFAULT_FILL_SUMMARY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_headers(fieldnames: list[str], schema: dict[str, Any]) -> list[dict[str, Any]]:
    required = [
        "blind_review_id",
        "scan_id",
        "scene_context_id",
        "subject_id",
        "subject_label",
        "predicate_label",
        "predicate_family",
        "object_id",
        "object_label",
        *schema.get("review_fields", []),
    ]
    return [{"error_type": "missing_required_header", "field": field} for field in required if field not in fieldnames]


def validate_id_sets(completed_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    completed_ids = [str(row.get("blind_review_id") or "") for row in completed_rows]
    manifest_ids = [str(row.get("blind_review_id") or "") for row in manifest_rows]
    for blind_id, count in Counter(completed_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_completed_blind_review_id", "blind_review_id": blind_id, "count": count})
    for blind_id, count in Counter(manifest_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_manifest_blind_review_id", "blind_review_id": blind_id, "count": count})
    completed_set = {blind_id for blind_id in completed_ids if blind_id}
    manifest_set = {blind_id for blind_id in manifest_ids if blind_id}
    for blind_id in sorted(completed_set - manifest_set):
        errors.append({"error_type": "completed_id_missing_from_manifest", "blind_review_id": blind_id})
    for blind_id in sorted(manifest_set - completed_set):
        errors.append({"error_type": "manifest_id_missing_from_completed_sheet", "blind_review_id": blind_id})
    return errors


def validate_fill_summary(fill_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v8_endpoint_pair_counterfactual_label_filled_codex_proxy_user_requested"
    if fill_summary.get("status") != expected_status:
        errors.append({"error_type": "fill_summary_status_unexpected", "expected": expected_status, "value": fill_summary.get("status")})
    expected_next = "reliability_target_v8_endpoint_pair_counterfactual_label_ingestion"
    if fill_summary.get("next_todo") != expected_next:
        errors.append({"error_type": "fill_summary_next_todo_unexpected", "expected": expected_next, "value": fill_summary.get("next_todo")})

    boundary = fill_summary.get("boundary", {})
    expected_false = [
        "actual_user_reviewer",
        "paper_evidence_allowed",
        "paper_metric_evidence",
        "h001_artifacts_modified",
        "used_hidden_manifest_for_label_decision",
        "used_candidate_bucket_for_label_decision",
        "used_semantic_geometry_bucket_for_label_decision",
        "used_object_cell_metadata_for_label_decision",
        "used_endpoint_pair_metadata_for_label_decision",
        "used_v8_group_metadata_for_label_decision",
        "used_source_score_or_rank",
        "used_p_geom_valid",
        "used_geometry_status",
        "used_source_queue",
        "used_label_match_status",
        "used_target_construction_metadata",
        "validation_usage",
        "test_usage",
        "multi_view_as_model_input",
        "posterior_smoke_allowed",
        "trains_new_posterior",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_summary_boundary_mismatch", "field": key, "expected": False, "value": boundary.get(key)})
    if boundary.get("filled_by") != "codex_proxy":
        errors.append({"error_type": "fill_summary_boundary_mismatch", "field": "filled_by", "expected": "codex_proxy", "value": boundary.get("filled_by")})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "fill_summary_boundary_mismatch", "field": "split", "expected": "train_only", "value": boundary.get("split")})
    if boundary.get("user_requested_proxy_fill") is not True:
        errors.append({"error_type": "fill_summary_boundary_mismatch", "field": "user_requested_proxy_fill", "expected": True, "value": boundary.get("user_requested_proxy_fill")})
    return errors


def validate_row(row: dict[str, str], row_number: int, schema: dict[str, Any], manifest: dict[str, Any] | None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = {key: set(values) for key, values in schema.get("allowed_review_values", {}).items()}
    blind_id = str(row.get("blind_review_id") or "")
    for field in COMPLETION_FIELDS:
        value = str(row.get(field) or "")
        if not value and field != "uncertainty_reason_v6":
            errors.append({"error_type": "missing_completion_field", "row_number": row_number, "blind_review_id": blind_id, "field": field})
        elif field in allowed and value not in allowed[field]:
            errors.append({"error_type": "invalid_completion_value", "row_number": row_number, "blind_review_id": blind_id, "field": field, "value": value})
    if manifest is None:
        return errors
    identity_pairs = {
        "scan_id": "scan_id",
        "scene_context_id": "scene_context_id",
        "predicate_family": "predicate_family",
        "predicate_label": "predicate_label",
        "subject_id": "subject_id",
        "subject_label": "subject_label",
        "object_id": "object_id",
        "object_label": "object_label",
    }
    for completed_key, manifest_key in identity_pairs.items():
        if str(row.get(completed_key) or "") != str(manifest.get(manifest_key) or ""):
            errors.append(
                {
                    "error_type": "completed_manifest_identity_mismatch",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "field": completed_key,
                    "completed_value": row.get(completed_key),
                    "manifest_value": manifest.get(manifest_key),
                }
            )
    manifest_packet_status = str(
        manifest.get("normalized_evidence_status_hidden")
        or manifest.get("evidence_packet_status")
        or ""
    )
    if str(row.get("evidence_packet_status") or "") != manifest_packet_status:
        errors.append(
            {
                "error_type": "completed_manifest_packet_status_mismatch",
                "row_number": row_number,
                "blind_review_id": blind_id,
                "completed_value": row.get("evidence_packet_status"),
                "manifest_value": manifest_packet_status,
            }
        )
    if str(row.get("packet_gap_decision") or "") != str(manifest.get("row_gap_decision_hidden") or ""):
        errors.append(
            {
                "error_type": "completed_manifest_packet_gap_mismatch",
                "row_number": row_number,
                "blind_review_id": blind_id,
                "completed_value": row.get("packet_gap_decision"),
                "manifest_value": manifest.get("row_gap_decision_hidden"),
            }
        )
    return errors


def hidden_metadata(manifest: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "asset_packet_source_hidden",
        "generated_blind_review_id_hidden",
        "geometry_status_hidden",
        "h001_verification_status_hidden",
        "hard_room_surface_pair_hidden",
        "label_geometry_bucket_hidden",
        "label_match_status_hidden",
        "machine_hint_hidden",
        "matched_predicates_hidden",
        "normalized_evidence_status_hidden",
        "object_family_cell_hidden",
        "p_geom_valid_hidden",
        "packet_source_hidden",
        "packet_status_hidden",
        "rank_band_hidden",
        "replacement_for_family_bucket_hidden",
        "replacement_source_hidden",
        "row_gap_decision_hidden",
        "row_gap_reason_hidden",
        "exact_endpoint_pair_key_hidden",
        "undirected_endpoint_pair_key_hidden",
        "scene_label_pair_key_hidden",
        "semantic_geometry_bucket_hidden",
        "semantic_rank_hidden",
        "semantic_score_norm_hidden",
        "semantic_score_raw_hidden",
        "source_queue_hidden",
        "structural_pair_hidden",
        "subject_object_family_cell_hidden",
        "subject_object_label_pair_hidden",
        "endpoint_pattern_hidden",
        "v8_group_level_hidden",
        "v8_group_key_hidden",
        "v8_group_row_count_hidden",
        "v8_group_predicate_count_hidden",
        "v8_group_has_queue_mix_hidden",
        "v8_group_has_family_mix_hidden",
        "v8_group_has_vertical_contradiction_hidden",
        "v8_group_has_support_alternative_hidden",
        "v8_group_geometry_range_hidden",
        "v8_group_rank_range_hidden",
    ]
    output = {key: manifest.get(key) for key in keys}
    output["prediction_id"] = manifest.get("prediction_id")
    output["forbidden_as_labeler_visible"] = manifest.get("forbidden_as_labeler_visible", [])
    output["packet_paths"] = {
        "multiview_packet": manifest.get("multiview_packet"),
        "pointcloud_or_mesh_packet": manifest.get("pointcloud_or_mesh_packet"),
        "contact_or_context_sheet": manifest.get("contact_or_context_sheet"),
    }
    return output


def deployable_evidence_after_label_lock(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "semantic_evidence": {
            "semantic_rank": manifest.get("semantic_rank_hidden"),
            "semantic_score_raw": manifest.get("semantic_score_raw_hidden"),
            "semantic_score_norm": manifest.get("semantic_score_norm_hidden"),
            "available_after_label_lock": True,
        },
        "geometry_scalar_evidence": {
            "p_geom_valid": manifest.get("p_geom_valid_hidden"),
            "role": "geometry_only_baseline_scalar",
            "available_after_label_lock": True,
        },
        "coverage_evidence": {
            "evidence_packet_status": row.get("evidence_packet_status"),
            "packet_gap_decision": row.get("packet_gap_decision"),
            "packet_gap_reason": row.get("packet_gap_reason"),
        },
        "audit_packet_evidence": {
            "packet_paths": {
                "multiview_packet": manifest.get("multiview_packet"),
                "pointcloud_or_mesh_packet": manifest.get("pointcloud_or_mesh_packet"),
                "contact_or_context_sheet": manifest.get("contact_or_context_sheet"),
            },
            "multi_view_as_model_input": False,
            "used_for_label_audit_only": True,
        },
        "forbidden_as_posterior_input": {
            "v6_review_fields": True,
            "semantic_geometry_bucket_hidden": True,
            "source_queue_hidden": True,
            "geometry_status_hidden": True,
            "label_match_status_hidden": True,
            "rank_band_hidden": True,
            "object_family_cell_hidden": True,
            "subject_object_family_cell_hidden": True,
            "endpoint_pattern_hidden": True,
            "exact_endpoint_pair_key_hidden": True,
            "v8_group_key_hidden": True,
            "asset_packet_source_hidden": True,
            "audit_packet_paths": True,
            "multi_view_content": True,
        },
    }


def review_fields(row: dict[str, str]) -> dict[str, Any]:
    return {
        "reviewer_id": row.get("reviewer_id"),
        "review_round": row.get("review_round"),
        "endpoint_identity_v6": row.get("endpoint_identity_v6"),
        "pair_evaluability_v6": row.get("pair_evaluability_v6"),
        "geometry_support_v6": row.get("geometry_support_v6"),
        "relation_usefulness_v6": row.get("relation_usefulness_v6"),
        "relation_reliability_state_v6": row.get("relation_reliability_state_v6"),
        "primary_reason_v6": row.get("primary_reason_v6"),
        "uncertainty_reason_v6": row.get("uncertainty_reason_v6"),
        "label_notes_v6": row.get("label_notes_v6"),
        "not_model_input": True,
    }


def base_identity(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "prediction_id": manifest.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("scene_context_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "evidence_packet_status": row.get("evidence_packet_status"),
        "packet_gap_decision": row.get("packet_gap_decision"),
    }


def relation_multiclass(row: dict[str, str]) -> dict[str, Any]:
    label = row["relation_reliability_state_v6"]
    label_to_id = {"accept_reliable": 1, "reject_unreliable": 0, "abstain_uncertain": 2}
    return {
        "target_name": RELIABILITY_MULTICLASS,
        "target_y": label,
        "target_class_id": label_to_id[label],
        "target_use": "multiclass",
        "reason": f"v6_relation_reliability_state={label}",
    }


def derive_reliability_binary(row: dict[str, str]) -> dict[str, Any]:
    value = row["relation_reliability_state_v6"]
    if value == "accept_reliable":
        return {"target_name": RELIABILITY_BINARY, "target_y": 1, "target_use": "positive", "reason": "v6_relation_reliability_accept_reliable"}
    if value == "reject_unreliable":
        return {"target_name": RELIABILITY_BINARY, "target_y": 0, "target_use": "negative", "reason": "v6_relation_reliability_reject_unreliable"}
    return {"target_name": RELIABILITY_BINARY, "target_y": None, "target_use": "exclude", "reason": f"exclude_relation_reliability_state={value}"}


def derive_geometry_binary(row: dict[str, str]) -> dict[str, Any]:
    value = row["geometry_support_v6"]
    if value == "supports":
        return {"target_name": GEOMETRY_TARGET, "target_y": 1, "target_use": "positive", "reason": "v6_geometry_supports"}
    if value == "contradicts":
        return {"target_name": GEOMETRY_TARGET, "target_y": 0, "target_use": "negative", "reason": "v6_geometry_contradicts"}
    return {"target_name": GEOMETRY_TARGET, "target_y": None, "target_use": "exclude", "reason": f"exclude_geometry_support={value}"}


def derive_usefulness_binary(row: dict[str, str]) -> dict[str, Any]:
    value = row["relation_usefulness_v6"]
    if value == "useful_nontrivial":
        return {"target_name": USEFULNESS_TARGET, "target_y": 1, "target_use": "positive", "reason": "v6_relation_usefulness_useful_nontrivial"}
    if value in {"trivial_or_redundant", "not_a_relation"}:
        return {"target_name": USEFULNESS_TARGET, "target_y": 0, "target_use": "negative", "reason": f"v6_relation_usefulness={value}"}
    return {"target_name": USEFULNESS_TARGET, "target_y": None, "target_use": "exclude", "reason": f"exclude_relation_usefulness={value}"}


def make_label(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_ingested_label_v1",
        **base_identity(row, manifest),
        "label_source": LABEL_SOURCE,
        "filled_by": "codex_proxy",
        "actual_user_reviewer": False,
        "user_requested_proxy_fill": True,
        "paper_evidence_allowed": False,
        "posterior_claim_allowed": False,
        "hidden_manifest_joined_after_label_lock": True,
        "review_fields_are_target_only": True,
        "v6_review_fields": review_fields(row),
        "relation_reliability_state_v6_multiclass_target": relation_multiclass(row),
        "relation_reliability_v6_binary_target": derive_reliability_binary(row),
        "geometry_support_v6_binary_target": derive_geometry_binary(row),
        "relation_usefulness_v6_binary_target": derive_usefulness_binary(row),
        "deployable_evidence_after_label_lock": deployable_evidence_after_label_lock(row, manifest),
        "hidden_audit_metadata_post_label_only": hidden_metadata(manifest),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "actual_user_reviewer": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "review_fields_as_model_input": False,
            "hidden_sampling_axes_as_model_input": False,
            "multi_view_as_model_input": False,
        },
    }


def ingest(
    completed_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, Any]],
    schema: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_by_id = {str(row["blind_review_id"]): row for row in manifest_rows}
    labels: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(completed_rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        manifest = manifest_by_id.get(blind_id)
        row_errors = validate_row(row, row_number, schema, manifest)
        if manifest is None:
            row_errors.append({"error_type": "missing_manifest_for_completed_row", "row_number": row_number, "blind_review_id": blind_id})
        if row_errors:
            errors.extend(row_errors)
            continue
        labels.append(make_label(row, manifest))
    return labels, errors


def target_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is None:
        return None
    hidden = label["hidden_audit_metadata_post_label_only"]
    row = {
        "schema_version": schema_version,
        "target_name": target["target_name"],
        "target_y": target["target_y"],
        "target_use": target["target_use"],
        "target_reason": target["reason"],
        "blind_review_id": label["blind_review_id"],
        "prediction_id": label["prediction_id"],
        "scan_id": label["scan_id"],
        "subgraph_id": label["subgraph_id"],
        "subject_id": label["subject_id"],
        "subject_label": label["subject_label"],
        "predicate_label": label["predicate_label"],
        "predicate_family": label["predicate_family"],
        "object_id": label["object_id"],
        "object_label": label["object_label"],
        "evidence_packet_status": label["evidence_packet_status"],
        "packet_gap_decision": label["packet_gap_decision"],
        "filled_by": "codex_proxy",
        "actual_user_reviewer": False,
        "paper_locked": False,
    }
    if "target_class_id" in target:
        row["target_class_id"] = target["target_class_id"]
    for key in HIDDEN_GROUP_KEYS:
        row[key] = hidden.get(key)
    return row


def posterior_candidate_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    row = target_row(label, target_key, schema_version)
    if row is None:
        return None
    return {
        **row,
        "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
        "audit_only_v6_review_fields": label["v6_review_fields"],
        "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
        "audit_note": (
            "Posterior smoke remains blocked until target-independence audit. "
            "Do not use v6 review fields, semantic-geometry bucket, source queue, geometry_status, "
            "label_match_status, object-cell metadata, endpoint-pair/v8 group metadata, rank band, endpoint pattern, packet source, "
            "audit packet paths, or multi-view content as model input."
        ),
    }


def excluded_target_row(label: dict[str, Any], target_key: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is not None:
        return None
    return {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_excluded_target_v1",
        "target_name": target["target_name"],
        "target_y": None,
        "target_use": target["target_use"],
        "target_reason": target["reason"],
        "blind_review_id": label["blind_review_id"],
        "scan_id": label["scan_id"],
        "predicate_label": label["predicate_label"],
        "predicate_family": label["predicate_family"],
        "subject_label": label["subject_label"],
        "object_label": label["object_label"],
        "v6_review_fields": label["v6_review_fields"],
    }


def entropy_from_counts(counts: Counter[Any]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    value = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        p = count / total
        value -= p * math.log2(p)
    return value


def group_value(row: dict[str, Any], key: str) -> str:
    if key in row:
        return str(row.get(key))
    hidden = row.get("hidden_audit_metadata_post_label_only", {})
    if key in hidden:
        return str(hidden.get(key))
    return "missing"


def target_label(row: dict[str, Any]) -> str:
    return str(row.get("target_y"))


def group_probe(rows: list[dict[str, Any]], key: str, source: str, target_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[group_value(row, key)].append(row)

    overall_counts = Counter(target_label(row) for row in rows)
    overall_entropy = entropy_from_counts(overall_counts)
    classes = sorted(overall_counts)
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    class_rates: dict[str, list[float]] = {label: [] for label in classes}
    large_group_high_purity = False
    table: list[dict[str, Any]] = []
    for value, group_rows in sorted(groups.items()):
        counts = Counter(target_label(row) for row in group_rows)
        total = len(group_rows)
        majority_label, majority = max(counts.items(), key=lambda item: (item[1], str(item[0])))
        purity = majority / total if total else 0.0
        group_entropy = entropy_from_counts(counts)
        weighted_conditional_entropy += (total / len(rows) * group_entropy) if rows else 0.0
        majority_correct += majority
        if total >= RISK_THRESHOLDS["large_group_rows"] and purity >= RISK_THRESHOLDS["large_group_purity"]:
            large_group_high_purity = True
        class_counts_json = json.dumps(dict(sorted(counts.items())), sort_keys=True)
        for label in classes:
            class_rates[label].append(counts[label] / total if total else 0.0)
        table.append(
            {
                "target_name": target_name,
                "source": source,
                "group_key": key,
                "group_value": value,
                "rows": total,
                "class_counts": class_counts_json,
                "majority_label": majority_label,
                "majority_accuracy": purity,
                "entropy_bits": group_entropy,
            }
        )
    mutual_info = max(0.0, overall_entropy - weighted_conditional_entropy)
    nmi = mutual_info / overall_entropy if overall_entropy > 0 else 0.0
    class_rate_ranges = {
        label: (max(values) - min(values)) if values else 0.0 for label, values in class_rates.items()
    }
    max_class_rate_range = max(class_rate_ranges.values()) if class_rate_ranges else 0.0
    majority_rule_accuracy = majority_correct / len(rows) if rows else 0.0
    risk_flag = (
        majority_rule_accuracy >= RISK_THRESHOLDS["majority_rule_accuracy"]
        or nmi >= RISK_THRESHOLDS["normalized_mutual_information"]
        or max_class_rate_range >= RISK_THRESHOLDS["class_rate_range"]
        or large_group_high_purity
    )
    summary = {
        "target_name": target_name,
        "source": source,
        "group_key": key,
        "groups": len(groups),
        "rows": len(rows),
        "overall_class_counts": dict(sorted(overall_counts.items())),
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_info,
        "normalized_mutual_information": nmi,
        "majority_rule_accuracy": majority_rule_accuracy,
        "class_rate_ranges": class_rate_ranges,
        "max_class_rate_range": max_class_rate_range,
        "large_group_high_purity": large_group_high_purity,
        "risk_flag": risk_flag,
    }
    return table, summary


def target_independence_probe(target_rows: list[dict[str, Any]], target_name: str) -> dict[str, Any]:
    group_table: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    if not target_rows:
        return {
            "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_independence_probe_v1",
            "target_name": target_name,
            "status": "target_independence_probe_no_rows",
            "summaries": [],
            "group_table": [],
            "hidden_risks": [],
            "visible_non_target_shortcuts": [],
        }
    for key in VISIBLE_GROUP_KEYS:
        table, summary = group_probe(target_rows, key, "visible_non_target_surface", target_name)
        group_table.extend(table)
        summaries.append(summary)
    for key in HIDDEN_GROUP_KEYS:
        table, summary = group_probe(target_rows, key, "hidden_post_label_audit", target_name)
        group_table.extend(table)
        summaries.append(summary)

    hidden_risks = [item for item in summaries if item["source"] == "hidden_post_label_audit" and item["risk_flag"]]
    visible_risks = [item for item in summaries if item["source"] == "visible_non_target_surface" and item["risk_flag"]]
    if hidden_risks:
        status = "target_independence_risk_hidden_metadata_correlated"
    elif visible_risks:
        status = "target_independence_risk_visible_non_target_shortcut"
    else:
        status = "target_independence_probe_pass"
    return {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_independence_probe_v1",
        "target_name": target_name,
        "status": status,
        "risk_thresholds": RISK_THRESHOLDS,
        "summaries": summaries,
        "group_table": group_table,
        "hidden_risks": sorted(hidden_risks, key=lambda row: (-row["normalized_mutual_information"], -row["majority_rule_accuracy"])),
        "visible_non_target_shortcuts": sorted(visible_risks, key=lambda row: (-row["normalized_mutual_information"], -row["majority_rule_accuracy"])),
    }


def nested_counts(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[str(row.get(key))][target_label(row)] += 1
    return {group: dict(sorted(counter.items())) for group, counter in sorted(grouped.items())}


def count_target(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(target_label(row) for row in rows)
    total = len(rows)
    output: dict[str, Any] = {
        "rows": total,
        "classes": dict(sorted(counts.items())),
        "by_family": nested_counts(rows, "predicate_family"),
        "by_predicate": nested_counts(rows, "predicate_label"),
        "by_semantic_geometry_bucket": nested_counts(rows, "semantic_geometry_bucket_hidden"),
        "by_source_queue": nested_counts(rows, "source_queue_hidden"),
        "by_geometry_status": nested_counts(rows, "geometry_status_hidden"),
        "by_packet_gap_decision": nested_counts(rows, "packet_gap_decision"),
        "by_rank_band": nested_counts(rows, "rank_band_hidden"),
        "by_object_family_cell": nested_counts(rows, "object_family_cell_hidden"),
        "by_endpoint_pattern": nested_counts(rows, "endpoint_pattern_hidden"),
    }
    if set(counts) <= {"0", "1"}:
        output.update(
            {
                "positive": counts["1"],
                "negative": counts["0"],
                "positive_rate": counts["1"] / total if total else 0.0,
            }
        )
    return output


def axis_counts(labels: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for axis in [
        "endpoint_identity_v6",
        "pair_evaluability_v6",
        "geometry_support_v6",
        "relation_usefulness_v6",
        "relation_reliability_state_v6",
        "primary_reason_v6",
        "uncertainty_reason_v6",
    ]:
        output[axis] = dict(sorted(Counter(label["v6_review_fields"].get(axis) for label in labels).items()))
    return output


def build_summary_status(
    errors: list[dict[str, Any]],
    probes: dict[str, dict[str, Any]],
    reliability_binary_count: dict[str, Any],
    multiclass_count: dict[str, Any],
) -> tuple[str, str, str]:
    any_probe_risk = any(probe["status"] != "target_independence_probe_pass" for probe in probes.values())
    enough_binary_mass = reliability_binary_count.get("positive", 0) >= 20 and reliability_binary_count.get("negative", 0) >= 20
    enough_multiclass_mass = all(multiclass_count.get("classes", {}).get(label, 0) >= 20 for label in ["accept_reliable", "reject_unreliable", "abstain_uncertain"])
    if errors:
        return (
            "h002_reliability_target_v8_endpoint_pair_counterfactual_label_ingestion_errors",
            "Fix v8 endpoint-pair counterfactual label ingestion errors before target audit.",
            "fix_reliability_target_v8_endpoint_pair_counterfactual_label_ingestion_errors",
        )
    if not enough_multiclass_mass:
        return (
            "h002_reliability_target_v8_endpoint_pair_counterfactual_label_ingested_multiclass_sparse",
            "V8 labels are ingested, but at least one multiclass reliability state is sparse.",
            "reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit",
        )
    if not enough_binary_mass:
        return (
            "h002_reliability_target_v8_endpoint_pair_counterfactual_label_ingested_binary_sparse",
            "V8 labels are ingested, but binary reliable/unreliable diagnostic mass is sparse.",
            "reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit",
        )
    if any_probe_risk:
        return (
            "h002_reliability_target_v8_endpoint_pair_counterfactual_label_ingested_with_probe_risk",
            "V8 labels are ingested, but hidden/visible shortcut probes flag target-construction risk. Run target-independence audit before any posterior smoke.",
            "reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit",
        )
    return (
        "h002_reliability_target_v8_endpoint_pair_counterfactual_label_ingested_ready_for_target_independence_audit",
        "V8 labels are ingested. Run dedicated target-independence audit before posterior smoke.",
        "reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    completed_sheet = as_abs(args.completed_sheet)
    fill_summary_path = as_abs(args.fill_summary)
    schema_path = as_abs(args.schema)
    manifest_path = as_abs(args.manifest)
    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    fieldnames, completed_rows = read_tsv(completed_sheet)
    fill_summary = read_json(fill_summary_path)
    schema = read_json(schema_path)
    manifest_rows = read_jsonl(manifest_path)

    errors: list[dict[str, Any]] = []
    errors.extend(validate_headers(fieldnames, schema))
    errors.extend(validate_id_sets(completed_rows, manifest_rows))
    errors.extend(validate_fill_summary(fill_summary))
    labels, label_errors = ingest(completed_rows, manifest_rows, schema)
    errors.extend(label_errors)

    multiclass_targets = [
        target_row(label, "relation_reliability_state_v6_multiclass_target", "h002_reliability_target_v8_endpoint_pair_counterfactual_multiclass_row_v1")
        for label in labels
    ]
    reliability_targets = [
        row
        for row in (
            target_row(label, "relation_reliability_v6_binary_target", "h002_reliability_target_v8_endpoint_pair_counterfactual_binary_row_v1")
            for label in labels
        )
        if row is not None
    ]
    geometry_targets = [
        row
        for row in (
            target_row(label, "geometry_support_v6_binary_target", "h002_geometry_support_v6_endpoint_pair_counterfactual_binary_row_v1")
            for label in labels
        )
        if row is not None
    ]
    usefulness_targets = [
        row
        for row in (
            target_row(label, "relation_usefulness_v6_binary_target", "h002_relation_usefulness_v6_endpoint_pair_counterfactual_binary_row_v1")
            for label in labels
        )
        if row is not None
    ]

    multiclass_posterior = [
        row
        for row in (
            posterior_candidate_row(label, "relation_reliability_state_v6_multiclass_target", "h002_reliability_target_v8_endpoint_pair_counterfactual_multiclass_posterior_candidate_row_v1")
            for label in labels
        )
        if row is not None
    ]
    reliability_posterior = [
        row
        for row in (
            posterior_candidate_row(label, "relation_reliability_v6_binary_target", "h002_reliability_target_v8_endpoint_pair_counterfactual_binary_posterior_candidate_row_v1")
            for label in labels
        )
        if row is not None
    ]
    geometry_posterior = [
        row
        for row in (
            posterior_candidate_row(label, "geometry_support_v6_binary_target", "h002_geometry_support_v6_endpoint_pair_counterfactual_posterior_candidate_row_v1")
            for label in labels
        )
        if row is not None
    ]
    usefulness_posterior = [
        row
        for row in (
            posterior_candidate_row(label, "relation_usefulness_v6_binary_target", "h002_relation_usefulness_v6_endpoint_pair_counterfactual_posterior_candidate_row_v1")
            for label in labels
        )
        if row is not None
    ]

    excluded_targets = [
        row
        for label in labels
        for row in (
            excluded_target_row(label, "relation_reliability_v6_binary_target"),
            excluded_target_row(label, "geometry_support_v6_binary_target"),
            excluded_target_row(label, "relation_usefulness_v6_binary_target"),
        )
        if row is not None
    ]
    excluded_counts = Counter(row["target_name"] for row in excluded_targets)
    probes = {
        RELIABILITY_MULTICLASS: target_independence_probe(multiclass_posterior, RELIABILITY_MULTICLASS),
        RELIABILITY_BINARY: target_independence_probe(reliability_posterior, RELIABILITY_BINARY),
        GEOMETRY_TARGET: target_independence_probe(geometry_posterior, GEOMETRY_TARGET),
        USEFULNESS_TARGET: target_independence_probe(usefulness_posterior, USEFULNESS_TARGET),
    }
    probe_summaries = [row for probe in probes.values() for row in probe["summaries"]]
    probe_group_rows = [row for probe in probes.values() for row in probe["group_table"]]

    reliability_binary_count = count_target(reliability_targets)
    multiclass_count = count_target(multiclass_targets)
    status, decision, next_todo = build_summary_status(errors, probes, reliability_binary_count, multiclass_count)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validated_v8_labels": output_dir / "validated_v8_labels.jsonl",
        "relation_reliability_multiclass_targets": output_dir / "relation_reliability_v6_multiclass_targets.jsonl",
        "relation_reliability_binary_targets": output_dir / "relation_reliability_v6_binary_targets.jsonl",
        "geometry_support_binary_targets": output_dir / "geometry_support_v6_binary_targets.jsonl",
        "relation_usefulness_binary_targets": output_dir / "relation_usefulness_v6_binary_targets.jsonl",
        "relation_reliability_multiclass_posterior_candidates": output_dir / "relation_reliability_v6_multiclass_posterior_candidates.jsonl",
        "relation_reliability_binary_posterior_candidates": output_dir / "relation_reliability_v6_binary_posterior_candidates.jsonl",
        "geometry_support_posterior_candidates": output_dir / "geometry_support_v6_posterior_candidates.jsonl",
        "relation_usefulness_posterior_candidates": output_dir / "relation_usefulness_v6_posterior_candidates.jsonl",
        "excluded_targets": output_dir / "excluded_v8_targets.jsonl",
        "target_independence_probe": output_dir / "target_independence_probe.json",
        "target_independence_probe_summaries": output_dir / "target_independence_probe_summaries.csv",
        "target_independence_group_table": output_dir / "target_independence_group_table.csv",
        "ingestion_errors": output_dir / "ingestion_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_label_ingestion_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "input_paths": {
            "completed_sheet": rel_path(completed_sheet),
            "fill_summary": rel_path(fill_summary_path),
            "v8_label_schema": rel_path(schema_path),
            "post_label_manifest": rel_path(manifest_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "filled_by": "codex_proxy",
            "actual_user_reviewer": False,
            "user_requested_proxy_fill": True,
            "paper_evidence_allowed": False,
            "paper_metric_evidence": False,
            "h001_artifacts_modified": False,
            "hidden_manifest_joined_after_label_lock": True,
            "review_fields_as_model_input": False,
            "hidden_sampling_axes_as_model_input": False,
            "multi_view_as_model_input": False,
            "posterior_smoke_allowed": False,
        },
        "counts": {
            "rows": len(labels),
            "ingestion_errors": len(errors),
            "axis_counts": axis_counts(labels),
            "targets": {
                RELIABILITY_MULTICLASS: multiclass_count,
                RELIABILITY_BINARY: reliability_binary_count,
                GEOMETRY_TARGET: count_target(geometry_targets),
                USEFULNESS_TARGET: count_target(usefulness_targets),
            },
            "excluded_targets": {
                RELIABILITY_BINARY: excluded_counts[RELIABILITY_BINARY],
                GEOMETRY_TARGET: excluded_counts[GEOMETRY_TARGET],
                USEFULNESS_TARGET: excluded_counts[USEFULNESS_TARGET],
            },
        },
        "target_independence_probes": {
            key: {
                "status": value["status"],
                "hidden_risks": value["hidden_risks"],
                "visible_non_target_shortcuts": value["visible_non_target_shortcuts"],
            }
            for key, value in probes.items()
        },
        "next_todo": next_todo,
    }

    write_jsonl(output_paths["validated_v8_labels"], labels)
    write_jsonl(output_paths["relation_reliability_multiclass_targets"], multiclass_targets)
    write_jsonl(output_paths["relation_reliability_binary_targets"], reliability_targets)
    write_jsonl(output_paths["geometry_support_binary_targets"], geometry_targets)
    write_jsonl(output_paths["relation_usefulness_binary_targets"], usefulness_targets)
    write_jsonl(output_paths["relation_reliability_multiclass_posterior_candidates"], multiclass_posterior)
    write_jsonl(output_paths["relation_reliability_binary_posterior_candidates"], reliability_posterior)
    write_jsonl(output_paths["geometry_support_posterior_candidates"], geometry_posterior)
    write_jsonl(output_paths["relation_usefulness_posterior_candidates"], usefulness_posterior)
    write_jsonl(output_paths["excluded_targets"], excluded_targets)
    write_jsonl(output_paths["ingestion_errors"], errors)
    write_json(
        output_paths["target_independence_probe"],
        {
            "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_target_independence_probe_bundle_v1",
            "probes": probes,
        },
    )
    write_csv(output_paths["target_independence_probe_summaries"], probe_summaries)
    write_csv(output_paths["target_independence_group_table"], probe_group_rows)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    targets = summary["counts"]["targets"]
    probes = summary["target_independence_probes"]
    multiclass = targets[RELIABILITY_MULTICLASS]
    binary = targets[RELIABILITY_BINARY]
    geometry = targets[GEOMETRY_TARGET]
    usefulness = targets[USEFULNESS_TARGET]
    lines = [
        "# H002 Reliability Target V8 Endpoint-Pair Counterfactual Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Labels are user-requested Codex proxy labels, not independent human annotation.",
        "- V6 review fields are target/audit fields and must not be posterior input.",
        "- Hidden manifest is joined only after label lock.",
        "- Multi-view/mesh packet evidence remains audit evidence only, not model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Target Counts",
        "",
        "| Target | Rows | Classes / Pos-Neg | Excluded |",
        "| --- | ---: | --- | ---: |",
        f"| `{RELIABILITY_MULTICLASS}` | {multiclass['rows']} | `{multiclass['classes']}` | 0 |",
        f"| `{RELIABILITY_BINARY}` | {binary['rows']} | `pos={binary.get('positive', 0)}, neg={binary.get('negative', 0)}` | {summary['counts']['excluded_targets'][RELIABILITY_BINARY]} |",
        f"| `{GEOMETRY_TARGET}` | {geometry['rows']} | `pos={geometry.get('positive', 0)}, neg={geometry.get('negative', 0)}` | {summary['counts']['excluded_targets'][GEOMETRY_TARGET]} |",
        f"| `{USEFULNESS_TARGET}` | {usefulness['rows']} | `pos={usefulness.get('positive', 0)}, neg={usefulness.get('negative', 0)}` | {summary['counts']['excluded_targets'][USEFULNESS_TARGET]} |",
        "",
        "## Probe",
        "",
        "| Target | Probe Status | Hidden Risks | Visible Risks |",
        "| --- | --- | ---: | ---: |",
    ]
    for target_name in [RELIABILITY_MULTICLASS, RELIABILITY_BINARY, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        probe = probes[target_name]
        lines.append(f"| `{target_name}` | `{probe['status']}` | {len(probe['hidden_risks'])} | {len(probe['visible_non_target_shortcuts'])} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    summary = run(parse_args())
    targets = summary["counts"]["targets"]
    multiclass = targets[RELIABILITY_MULTICLASS]
    reliability = targets[RELIABILITY_BINARY]
    geometry = targets[GEOMETRY_TARGET]
    usefulness = targets[USEFULNESS_TARGET]
    print(
        "status={status} rows={rows} multiclass={multiclass} rel_binary={rel_rows} rel_pos={rel_pos} "
        "rel_neg={rel_neg} geom_binary={geom_rows} geom_pos={geom_pos} geom_neg={geom_neg} "
        "use_binary={use_rows} use_pos={use_pos} use_neg={use_neg} errors={errors} "
        "probe={probe} validation_used={validation_used} test_used={test_used} "
        "posterior_allowed={posterior_allowed} next={next_todo}".format(
            status=summary["status"],
            rows=summary["counts"]["rows"],
            multiclass=multiclass["classes"],
            rel_rows=reliability["rows"],
            rel_pos=reliability.get("positive", 0),
            rel_neg=reliability.get("negative", 0),
            geom_rows=geometry["rows"],
            geom_pos=geometry.get("positive", 0),
            geom_neg=geometry.get("negative", 0),
            use_rows=usefulness["rows"],
            use_pos=usefulness.get("positive", 0),
            use_neg=usefulness.get("negative", 0),
            errors=summary["counts"]["ingestion_errors"],
            probe=summary["target_independence_probes"][RELIABILITY_MULTICLASS]["status"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
