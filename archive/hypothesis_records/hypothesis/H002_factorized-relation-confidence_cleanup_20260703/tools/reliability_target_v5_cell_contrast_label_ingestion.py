#!/usr/bin/env python3
"""Ingest v5 cell-contrast labels after proxy fill."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

FILL_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_fill_codex_proxy_user_requested"
READINESS_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_readiness"

DEFAULT_COMPLETED_SHEET = FILL_DIR / "completed_v5_cell_contrast_label_sheet_codex_proxy_user_requested.tsv"
DEFAULT_FILL_SUMMARY = FILL_DIR / "summary.json"
DEFAULT_SCHEMA = READINESS_DIR / "label_schema.json"
DEFAULT_MANIFEST = READINESS_DIR / "ready_manifest_post_label_only.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_ingestion_codex_proxy_user_requested"

LABEL_SOURCE = "codex_proxy_reliability_target_v5_cell_contrast_user_requested"
RELIABILITY_TARGET = "relation_reliability_v5_binary_target"
GEOMETRY_TARGET = "geometry_support_v5_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v5_binary_target"
RELIABILITY_MULTICLASS = "relation_reliability_v5_multiclass_target"

COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_v5",
    "pair_evaluability_v5",
    "geometry_support_v5",
    "relation_usefulness_v5",
    "relation_reliability_v5",
    "primary_reason_v5",
    "uncertainty_reason_v5",
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
    "cell_contrast_role_hidden",
    "contrast_role_hidden",
    "cell_contrast_pair_id_hidden",
    "cell_contrast_level_hidden",
    "cell_contrast_key_hidden",
    "object_family_cell_hidden",
    "endpoint_family_cell_hidden",
    "endpoint_flag_pattern_hidden",
    "subject_object_family_cell_hidden",
    "source_queue_hidden",
    "queue_kind_hidden",
    "geometry_status_hidden",
    "h001_verification_status_hidden",
    "label_match_status_hidden",
    "label_match_family_hidden",
    "label_geometry_bucket_hidden",
    "rank_band_hidden",
    "machine_hint_hidden",
    "asset_packet_source_hidden",
    "row_gap_decision_hidden",
    "pair_gap_decision_hidden",
]

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "normalized_mutual_information": 0.20,
    "positive_rate_range": 0.70,
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
    expected_status = "h002_reliability_target_v5_cell_contrast_label_filled_codex_proxy_user_requested"
    if fill_summary.get("status") != expected_status:
        errors.append({"error_type": "fill_summary_status_unexpected", "expected": expected_status, "value": fill_summary.get("status")})
    expected_next = "reliability_target_v5_cell_contrast_label_ingestion"
    if fill_summary.get("next_todo") != expected_next:
        errors.append({"error_type": "fill_summary_next_todo_unexpected", "expected": expected_next, "value": fill_summary.get("next_todo")})

    boundary = fill_summary.get("boundary", {})
    expected_false = [
        "actual_user_reviewer",
        "paper_evidence_allowed",
        "used_hidden_manifest_for_label_decision",
        "used_cell_contrast_role_for_label_decision",
        "used_pair_id_for_label_decision",
        "used_source_score_or_rank",
        "used_p_geom_valid",
        "used_geometry_status",
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
        if not value and field != "uncertainty_reason_v5":
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
    completed_packet_status = str(row.get("evidence_packet_status") or "")
    manifest_packet_status = str(manifest.get("evidence_packet_status") or "")
    packet_status_alias_ok = completed_packet_status == "limited_view_evaluable" and manifest_packet_status == "partial"
    if completed_packet_status != manifest_packet_status and not packet_status_alias_ok:
        errors.append(
            {
                "error_type": "completed_manifest_packet_status_mismatch",
                "row_number": row_number,
                "blind_review_id": blind_id,
                "field": "evidence_packet_status",
                "completed_value": completed_packet_status,
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
        "cell_contrast_key_hidden",
        "cell_contrast_level_hidden",
        "cell_contrast_pair_id_hidden",
        "cell_contrast_role_hidden",
        "contrast_role_hidden",
        "endpoint_family_cell_hidden",
        "endpoint_flag_pattern_hidden",
        "generated_blind_review_id_hidden",
        "geometry_status_hidden",
        "h001_verification_status_hidden",
        "informative_score_hidden",
        "label_geometry_bucket_hidden",
        "label_match_family_hidden",
        "label_match_status_hidden",
        "machine_hint_hidden",
        "matched_predicates_hidden",
        "object_family_cell_hidden",
        "object_label_norm_hidden",
        "original_packet_id_hidden",
        "p_geom_valid_hidden",
        "packet_status_hidden",
        "pair_gap_decision_hidden",
        "pair_gap_reason_hidden",
        "predicate_label",
        "prediction_id_hidden",
        "queue_kind_hidden",
        "rank_band_hidden",
        "reason_codes_hidden",
        "room_surface_score_hidden",
        "row_gap_decision_hidden",
        "row_gap_reason_hidden",
        "semantic_rank_hidden",
        "semantic_score_norm_hidden",
        "semantic_score_raw_hidden",
        "source_id_hidden",
        "source_queue_hidden",
        "subject_label_norm_hidden",
        "subject_object_family_cell_hidden",
    ]
    output = {key: manifest.get(key) for key in keys}
    output["forbidden_as_labeler_visible"] = manifest.get("forbidden_as_labeler_visible", [])
    output["packet_paths"] = manifest.get("packet_paths", {})
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
            "packet_paths": manifest.get("packet_paths", {}),
            "multi_view_as_model_input": False,
            "used_for_label_audit_only": True,
        },
        "forbidden_as_posterior_input": {
            "v5_review_fields": True,
            "cell_contrast_role_hidden": True,
            "cell_contrast_pair_id_hidden": True,
            "cell_contrast_key_hidden": True,
            "source_queue_hidden": True,
            "geometry_status_hidden": True,
            "label_match_status_hidden": True,
            "rank_band_hidden": True,
            "endpoint_flag_pattern_hidden": True,
            "asset_packet_source_hidden": True,
            "audit_packet_paths": True,
            "multi_view_content": True,
        },
    }


def review_fields(row: dict[str, str]) -> dict[str, Any]:
    return {
        "reviewer_id": row.get("reviewer_id"),
        "review_round": row.get("review_round"),
        "endpoint_identity_v5": row.get("endpoint_identity_v5"),
        "pair_evaluability_v5": row.get("pair_evaluability_v5"),
        "geometry_support_v5": row.get("geometry_support_v5"),
        "relation_usefulness_v5": row.get("relation_usefulness_v5"),
        "relation_reliability_v5": row.get("relation_reliability_v5"),
        "primary_reason_v5": row.get("primary_reason_v5"),
        "uncertainty_reason_v5": row.get("uncertainty_reason_v5"),
        "label_notes_v5": row.get("label_notes_v5"),
        "not_model_input": True,
    }


def base_identity(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "prediction_id": manifest.get("prediction_id_hidden"),
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


def derive_reliability_binary(row: dict[str, str]) -> dict[str, Any]:
    value = row["relation_reliability_v5"]
    if value == "reliable":
        return {"target_name": RELIABILITY_TARGET, "target_y": 1, "target_use": "positive", "reason": "v5_relation_reliability_reliable"}
    if value == "unreliable":
        return {"target_name": RELIABILITY_TARGET, "target_y": 0, "target_use": "negative", "reason": "v5_relation_reliability_unreliable"}
    return {"target_name": RELIABILITY_TARGET, "target_y": None, "target_use": "exclude", "reason": f"exclude_relation_reliability={value}"}


def derive_geometry_binary(row: dict[str, str]) -> dict[str, Any]:
    value = row["geometry_support_v5"]
    if value == "supports":
        return {"target_name": GEOMETRY_TARGET, "target_y": 1, "target_use": "positive", "reason": "v5_geometry_supports"}
    if value == "contradicts":
        return {"target_name": GEOMETRY_TARGET, "target_y": 0, "target_use": "negative", "reason": "v5_geometry_contradicts"}
    return {"target_name": GEOMETRY_TARGET, "target_y": None, "target_use": "exclude", "reason": f"exclude_geometry_support={value}"}


def derive_usefulness_binary(row: dict[str, str]) -> dict[str, Any]:
    value = row["relation_usefulness_v5"]
    if value == "useful_nontrivial":
        return {"target_name": USEFULNESS_TARGET, "target_y": 1, "target_use": "positive", "reason": "v5_relation_usefulness_useful_nontrivial"}
    if value in {"trivial_or_redundant", "not_a_relation"}:
        return {"target_name": USEFULNESS_TARGET, "target_y": 0, "target_use": "negative", "reason": f"v5_relation_usefulness={value}"}
    return {"target_name": USEFULNESS_TARGET, "target_y": None, "target_use": "exclude", "reason": f"exclude_relation_usefulness={value}"}


def relation_multiclass(row: dict[str, str]) -> dict[str, Any]:
    return {
        "target_name": RELIABILITY_MULTICLASS,
        "target_y": row["relation_reliability_v5"],
        "target_use": "multiclass",
        "reason": f"v5_relation_reliability={row['relation_reliability_v5']}",
    }


def make_label(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v5_cell_contrast_ingested_label_v1",
        **base_identity(row, manifest),
        "label_source": LABEL_SOURCE,
        "filled_by": "codex_proxy",
        "actual_user_reviewer": False,
        "user_requested_proxy_fill": True,
        "paper_evidence_allowed": False,
        "posterior_claim_allowed": False,
        "hidden_manifest_joined_after_label_lock": True,
        "review_fields_are_target_only": True,
        "v5_review_fields": review_fields(row),
        "relation_reliability_v5_binary_target": derive_reliability_binary(row),
        "geometry_support_v5_binary_target": derive_geometry_binary(row),
        "relation_usefulness_v5_binary_target": derive_usefulness_binary(row),
        "relation_reliability_v5_multiclass_target": relation_multiclass(row),
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
    return {
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
        "cell_contrast_role_hidden": hidden.get("cell_contrast_role_hidden"),
        "contrast_role_hidden": hidden.get("contrast_role_hidden"),
        "cell_contrast_pair_id_hidden": hidden.get("cell_contrast_pair_id_hidden"),
        "cell_contrast_level_hidden": hidden.get("cell_contrast_level_hidden"),
        "cell_contrast_key_hidden": hidden.get("cell_contrast_key_hidden"),
        "object_family_cell_hidden": hidden.get("object_family_cell_hidden"),
        "endpoint_family_cell_hidden": hidden.get("endpoint_family_cell_hidden"),
        "endpoint_flag_pattern_hidden": hidden.get("endpoint_flag_pattern_hidden"),
        "subject_object_family_cell_hidden": hidden.get("subject_object_family_cell_hidden"),
        "source_queue_hidden": hidden.get("source_queue_hidden"),
        "queue_kind_hidden": hidden.get("queue_kind_hidden"),
        "geometry_status_hidden": hidden.get("geometry_status_hidden"),
        "h001_verification_status_hidden": hidden.get("h001_verification_status_hidden"),
        "label_match_status_hidden": hidden.get("label_match_status_hidden"),
        "label_match_family_hidden": hidden.get("label_match_family_hidden"),
        "label_geometry_bucket_hidden": hidden.get("label_geometry_bucket_hidden"),
        "rank_band_hidden": hidden.get("rank_band_hidden"),
        "machine_hint_hidden": hidden.get("machine_hint_hidden"),
        "asset_packet_source_hidden": hidden.get("asset_packet_source_hidden"),
        "row_gap_decision_hidden": hidden.get("row_gap_decision_hidden"),
        "pair_gap_decision_hidden": hidden.get("pair_gap_decision_hidden"),
    }


def multiclass_target_row(label: dict[str, Any]) -> dict[str, Any]:
    row = target_row(label, "relation_reliability_v5_multiclass_target", "h002_reliability_target_v5_cell_contrast_multiclass_row_v1")
    assert row is not None
    return row


def posterior_candidate_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    row = target_row(label, target_key, schema_version)
    if row is None:
        return None
    return {
        **row,
        "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
        "audit_only_v5_review_fields": label["v5_review_fields"],
        "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
        "audit_note": (
            "Posterior smoke remains blocked until target-independence audit. "
            "Do not use v5 review fields, cell contrast role, pair id, cell key, source queue, "
            "geometry_status, label_match_status, rank band, endpoint flags, packet source, "
            "audit packet paths, or multi-view content as model input."
        ),
    }


def excluded_target_row(label: dict[str, Any], target_key: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is not None:
        return None
    return {
        "schema_version": "h002_reliability_target_v5_cell_contrast_excluded_target_v1",
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
        "v5_review_fields": label["v5_review_fields"],
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


def group_probe(rows: list[dict[str, Any]], key: str, source: str, target_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[group_value(row, key)].append(row)

    overall_counts = Counter(int(row["target_y"]) for row in rows)
    overall_entropy = entropy_from_counts(overall_counts)
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    positive_rates: list[float] = []
    large_group_high_purity = False
    table: list[dict[str, Any]] = []
    for value, group_rows in sorted(groups.items()):
        counts = Counter(int(row["target_y"]) for row in group_rows)
        pos = counts[1]
        neg = counts[0]
        total = pos + neg
        majority = max(pos, neg)
        purity = majority / total if total else 0.0
        pos_rate = pos / total if total else 0.0
        group_entropy = entropy_from_counts(counts)
        weighted_conditional_entropy += (total / len(rows) * group_entropy) if rows else 0.0
        majority_correct += majority
        positive_rates.append(pos_rate)
        if total >= RISK_THRESHOLDS["large_group_rows"] and purity >= RISK_THRESHOLDS["large_group_purity"]:
            large_group_high_purity = True
        table.append(
            {
                "target_name": target_name,
                "source": source,
                "group_key": key,
                "group_value": value,
                "rows": total,
                "positive": pos,
                "negative": neg,
                "positive_rate": pos_rate,
                "majority_label": 1 if pos >= neg else 0,
                "majority_accuracy": purity,
                "entropy_bits": group_entropy,
            }
        )
    mutual_info = max(0.0, overall_entropy - weighted_conditional_entropy)
    nmi = mutual_info / overall_entropy if overall_entropy > 0 else 0.0
    pos_rate_range = (max(positive_rates) - min(positive_rates)) if positive_rates else 0.0
    majority_rule_accuracy = majority_correct / len(rows) if rows else 0.0
    risk_flag = (
        majority_rule_accuracy >= RISK_THRESHOLDS["majority_rule_accuracy"]
        or nmi >= RISK_THRESHOLDS["normalized_mutual_information"]
        or pos_rate_range >= RISK_THRESHOLDS["positive_rate_range"]
        or large_group_high_purity
    )
    summary = {
        "target_name": target_name,
        "source": source,
        "group_key": key,
        "groups": len(groups),
        "rows": len(rows),
        "overall_positive": overall_counts[1],
        "overall_negative": overall_counts[0],
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_info,
        "normalized_mutual_information": nmi,
        "majority_rule_accuracy": majority_rule_accuracy,
        "positive_rate_range": pos_rate_range,
        "large_group_high_purity": large_group_high_purity,
        "risk_flag": risk_flag,
    }
    return table, summary


def target_independence_probe(target_rows: list[dict[str, Any]], target_name: str) -> dict[str, Any]:
    group_table: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    if not target_rows:
        return {
            "schema_version": "h002_reliability_target_v5_cell_contrast_independence_probe_v1",
            "target_name": target_name,
            "status": "target_independence_probe_no_binary_rows",
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
        "schema_version": "h002_reliability_target_v5_cell_contrast_independence_probe_v1",
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
        grouped[str(row.get(key))][str(row.get("target_y"))] += 1
    return {group: dict(sorted(counter.items())) for group, counter in sorted(grouped.items())}


def count_binary_target(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["target_y"] for row in rows)
    total = len(rows)
    return {
        "rows": total,
        "positive": counts[1],
        "negative": counts[0],
        "positive_rate": counts[1] / total if total else 0.0,
        "by_family": nested_counts(rows, "predicate_family"),
        "by_predicate": nested_counts(rows, "predicate_label"),
        "by_cell_role": nested_counts(rows, "cell_contrast_role_hidden"),
        "by_source_queue": nested_counts(rows, "source_queue_hidden"),
        "by_geometry_status": nested_counts(rows, "geometry_status_hidden"),
        "by_label_geometry_bucket": nested_counts(rows, "label_geometry_bucket_hidden"),
        "by_packet_source": nested_counts(rows, "asset_packet_source_hidden"),
        "by_rank_band": nested_counts(rows, "rank_band_hidden"),
    }


def count_multiclass(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["target_y"] for row in rows)
    return {"rows": len(rows), "classes": dict(sorted(counts.items()))}


def axis_counts(labels: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for axis in [
        "endpoint_identity_v5",
        "pair_evaluability_v5",
        "geometry_support_v5",
        "relation_usefulness_v5",
        "relation_reliability_v5",
        "primary_reason_v5",
        "uncertainty_reason_v5",
    ]:
        output[axis] = dict(sorted(Counter(label["v5_review_fields"].get(axis) for label in labels).items()))
    return output


def pair_diagnostics(labels: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        pair_id = str(label["hidden_audit_metadata_post_label_only"].get("cell_contrast_pair_id_hidden"))
        grouped[pair_id].append(label)

    pair_rows: list[dict[str, Any]] = []
    for pair_id, rows in sorted(grouped.items()):
        reliability = Counter(row["v5_review_fields"]["relation_reliability_v5"] for row in rows)
        roles = Counter(str(row["hidden_audit_metadata_post_label_only"].get("cell_contrast_role_hidden")) for row in rows)
        pattern = "/".join(sorted(reliability.elements()))
        pair_rows.append(
            {
                "cell_contrast_pair_id_hidden": pair_id,
                "rows": len(rows),
                "positive_proxy_rows": roles["positive_proxy"],
                "negative_proxy_rows": roles["negative_proxy"],
                "reliable": reliability["reliable"],
                "unreliable": reliability["unreliable"],
                "uncertain": reliability["uncertain"],
                "pair_label_pattern": pattern,
                "direct_reliable_unreliable_contrast": reliability["reliable"] > 0 and reliability["unreliable"] > 0,
            }
        )
    pattern_counts = Counter(row["pair_label_pattern"] for row in pair_rows)
    return {
        "pair_count": len(pair_rows),
        "direct_reliable_unreliable_contrast_pairs": sum(1 for row in pair_rows if row["direct_reliable_unreliable_contrast"]),
        "pair_label_pattern_counts": dict(sorted(pattern_counts.items())),
        "rows": pair_rows,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    targets = summary["counts"]["binary_targets"]
    probes = summary["target_independence_probes"]
    pair_summary = summary["pair_diagnostics"]
    lines = [
        "# H002 Reliability Target V5 Cell Contrast Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Labels are user-requested Codex proxy labels, not independent human annotation.",
        "- V5 review fields are target/audit fields and must not be posterior input.",
        "- Hidden manifest is joined only after label lock.",
        "- Multi-view/mesh packet evidence remains audit evidence only, not model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Binary Target Counts",
        "",
        "| Target | Rows | Positive | Negative | Positive Rate | Excluded |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for target_name in [RELIABILITY_TARGET, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        item = targets[target_name]
        excluded = summary["counts"]["excluded_targets"][target_name]
        lines.append(
            f"| `{target_name}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['positive_rate']:.4f} | {excluded} |"
        )
    lines.extend(
        [
            "",
            "## Pair Contrast",
            "",
            f"- Pairs: `{pair_summary['pair_count']}`",
            f"- Direct reliable/unreliable contrast pairs: `{pair_summary['direct_reliable_unreliable_contrast_pairs']}`",
            f"- Pair patterns: `{pair_summary['pair_label_pattern_counts']}`",
            "",
            "## Probe",
            "",
            "| Target | Probe Status | Hidden Risks | Visible Risks |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for target_name in [RELIABILITY_TARGET, GEOMETRY_TARGET, USEFULNESS_TARGET]:
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


def build_summary_status(
    errors: list[dict[str, Any]],
    probes: dict[str, dict[str, Any]],
    reliability_count: dict[str, Any],
    pair_summary: dict[str, Any],
) -> tuple[str, str, str]:
    any_probe_risk = any(probe["status"] != "target_independence_probe_pass" for probe in probes.values())
    enough_reliability_mass = reliability_count["positive"] >= 20 and reliability_count["negative"] >= 20
    has_direct_pair_contrast = pair_summary["direct_reliable_unreliable_contrast_pairs"] > 0
    if errors:
        return (
            "h002_reliability_target_v5_cell_contrast_label_ingestion_errors",
            "Fix v5 cell-contrast label ingestion errors before target audit.",
            "fix_reliability_target_v5_cell_contrast_label_ingestion_errors",
        )
    if not enough_reliability_mass and not has_direct_pair_contrast and any_probe_risk:
        return (
            "h002_reliability_target_v5_cell_contrast_label_ingested_sparse_no_direct_pair_contrast_with_probe_risk",
            (
                "V5 labels are ingested, but relation reliability has only 31 binary rows "
                "and no direct reliable/unreliable pair contrast. Shortcut probes also flag "
                "target-construction risk. Run target-independence audit before any posterior smoke."
            ),
            "reliability_target_v5_cell_contrast_target_independence_audit",
        )
    if not enough_reliability_mass:
        return (
            "h002_reliability_target_v5_cell_contrast_label_ingested_sparse",
            "V5 labels are ingested, but relation reliability target mass is sparse.",
            "reliability_target_v5_cell_contrast_target_independence_audit",
        )
    if not has_direct_pair_contrast:
        return (
            "h002_reliability_target_v5_cell_contrast_label_ingested_no_direct_pair_contrast",
            "V5 labels are ingested, but direct reliable/unreliable pair contrast is absent.",
            "reliability_target_v5_cell_contrast_target_independence_audit",
        )
    if any_probe_risk:
        return (
            "h002_reliability_target_v5_cell_contrast_label_ingested_with_probe_risk",
            "V5 labels are ingested, but hidden/visible shortcut probes still flag target-construction risk.",
            "reliability_target_v5_cell_contrast_target_independence_audit",
        )
    return (
        "h002_reliability_target_v5_cell_contrast_label_ingested_ready_for_target_independence_audit",
        "V5 labels are ingested. Run dedicated target-independence audit before posterior smoke.",
        "reliability_target_v5_cell_contrast_target_independence_audit",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    completed_sheet = as_abs(args.completed_sheet)
    fill_summary_path = as_abs(args.fill_summary)
    schema_path = as_abs(args.schema)
    manifest_path = as_abs(args.manifest)
    output_dir = as_abs(args.output_dir)
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

    reliability_targets = [
        row
        for row in (
            target_row(label, "relation_reliability_v5_binary_target", "h002_reliability_target_v5_cell_contrast_binary_row_v1")
            for label in labels
        )
        if row is not None
    ]
    geometry_targets = [
        row
        for row in (
            target_row(label, "geometry_support_v5_binary_target", "h002_geometry_support_v5_cell_contrast_binary_row_v1")
            for label in labels
        )
        if row is not None
    ]
    usefulness_targets = [
        row
        for row in (
            target_row(label, "relation_usefulness_v5_binary_target", "h002_relation_usefulness_v5_cell_contrast_binary_row_v1")
            for label in labels
        )
        if row is not None
    ]
    multiclass_targets = [multiclass_target_row(label) for label in labels]

    reliability_posterior = [
        row
        for row in (
            posterior_candidate_row(label, "relation_reliability_v5_binary_target", "h002_reliability_target_v5_cell_contrast_posterior_candidate_row_v1")
            for label in labels
        )
        if row is not None
    ]
    geometry_posterior = [
        row
        for row in (
            posterior_candidate_row(label, "geometry_support_v5_binary_target", "h002_geometry_support_v5_cell_contrast_posterior_candidate_row_v1")
            for label in labels
        )
        if row is not None
    ]
    usefulness_posterior = [
        row
        for row in (
            posterior_candidate_row(label, "relation_usefulness_v5_binary_target", "h002_relation_usefulness_v5_cell_contrast_posterior_candidate_row_v1")
            for label in labels
        )
        if row is not None
    ]

    excluded_targets = [
        row
        for label in labels
        for row in (
            excluded_target_row(label, "relation_reliability_v5_binary_target"),
            excluded_target_row(label, "geometry_support_v5_binary_target"),
            excluded_target_row(label, "relation_usefulness_v5_binary_target"),
        )
        if row is not None
    ]
    excluded_counts = Counter(row["target_name"] for row in excluded_targets)
    probes = {
        RELIABILITY_TARGET: target_independence_probe(reliability_posterior, RELIABILITY_TARGET),
        GEOMETRY_TARGET: target_independence_probe(geometry_posterior, GEOMETRY_TARGET),
        USEFULNESS_TARGET: target_independence_probe(usefulness_posterior, USEFULNESS_TARGET),
    }
    probe_summaries = [row for probe in probes.values() for row in probe["summaries"]]
    probe_group_rows = [row for probe in probes.values() for row in probe["group_table"]]

    reliability_count = count_binary_target(reliability_targets)
    pair_summary = pair_diagnostics(labels)
    status, decision, next_todo = build_summary_status(errors, probes, reliability_count, pair_summary)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validated_v5_labels": output_dir / "validated_v5_labels.jsonl",
        "relation_reliability_binary_targets": output_dir / "relation_reliability_v5_binary_targets.jsonl",
        "geometry_support_binary_targets": output_dir / "geometry_support_v5_binary_targets.jsonl",
        "relation_usefulness_binary_targets": output_dir / "relation_usefulness_v5_binary_targets.jsonl",
        "relation_reliability_multiclass_targets": output_dir / "relation_reliability_v5_multiclass_targets.jsonl",
        "relation_reliability_posterior_candidates": output_dir / "relation_reliability_v5_posterior_candidates.jsonl",
        "geometry_support_posterior_candidates": output_dir / "geometry_support_v5_posterior_candidates.jsonl",
        "relation_usefulness_posterior_candidates": output_dir / "relation_usefulness_v5_posterior_candidates.jsonl",
        "excluded_targets": output_dir / "excluded_v5_targets.jsonl",
        "target_independence_probe": output_dir / "target_independence_probe.json",
        "target_independence_probe_summaries": output_dir / "target_independence_probe_summaries.csv",
        "target_independence_group_table": output_dir / "target_independence_group_table.csv",
        "pair_diagnostics": output_dir / "pair_diagnostics.csv",
        "ingestion_errors": output_dir / "ingestion_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_reliability_target_v5_cell_contrast_label_ingestion_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "input_paths": {
            "completed_sheet": rel_path(completed_sheet),
            "fill_summary": rel_path(fill_summary_path),
            "v5_label_schema": rel_path(schema_path),
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
            "binary_targets": {
                RELIABILITY_TARGET: reliability_count,
                GEOMETRY_TARGET: count_binary_target(geometry_targets),
                USEFULNESS_TARGET: count_binary_target(usefulness_targets),
            },
            "multiclass_targets": {
                RELIABILITY_MULTICLASS: count_multiclass(multiclass_targets),
            },
            "excluded_targets": {
                RELIABILITY_TARGET: excluded_counts[RELIABILITY_TARGET],
                GEOMETRY_TARGET: excluded_counts[GEOMETRY_TARGET],
                USEFULNESS_TARGET: excluded_counts[USEFULNESS_TARGET],
            },
        },
        "pair_diagnostics": {
            "pair_count": pair_summary["pair_count"],
            "direct_reliable_unreliable_contrast_pairs": pair_summary["direct_reliable_unreliable_contrast_pairs"],
            "pair_label_pattern_counts": pair_summary["pair_label_pattern_counts"],
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

    write_jsonl(output_paths["validated_v5_labels"], labels)
    write_jsonl(output_paths["relation_reliability_binary_targets"], reliability_targets)
    write_jsonl(output_paths["geometry_support_binary_targets"], geometry_targets)
    write_jsonl(output_paths["relation_usefulness_binary_targets"], usefulness_targets)
    write_jsonl(output_paths["relation_reliability_multiclass_targets"], multiclass_targets)
    write_jsonl(output_paths["relation_reliability_posterior_candidates"], reliability_posterior)
    write_jsonl(output_paths["geometry_support_posterior_candidates"], geometry_posterior)
    write_jsonl(output_paths["relation_usefulness_posterior_candidates"], usefulness_posterior)
    write_jsonl(output_paths["excluded_targets"], excluded_targets)
    write_jsonl(output_paths["ingestion_errors"], errors)
    write_json(
        output_paths["target_independence_probe"],
        {
            "schema_version": "h002_reliability_target_v5_cell_contrast_target_independence_probe_bundle_v1",
            "probes": probes,
        },
    )
    write_csv(output_paths["target_independence_probe_summaries"], probe_summaries)
    write_csv(output_paths["target_independence_group_table"], probe_group_rows)
    write_csv(output_paths["pair_diagnostics"], pair_summary["rows"])
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    targets = summary["counts"]["binary_targets"]
    reliability = targets[RELIABILITY_TARGET]
    geometry = targets[GEOMETRY_TARGET]
    usefulness = targets[USEFULNESS_TARGET]
    print(
        "status={status} rows={rows} rel_binary={rel_rows} rel_pos={rel_pos} rel_neg={rel_neg} "
        "geom_binary={geom_rows} geom_pos={geom_pos} geom_neg={geom_neg} "
        "use_binary={use_rows} use_pos={use_pos} use_neg={use_neg} errors={errors} "
        "direct_pair_contrast={direct_pair_contrast} probe={probe} "
        "validation_used={validation_used} test_used={test_used} posterior_allowed={posterior_allowed} "
        "next={next_todo}".format(
            status=summary["status"],
            rows=summary["counts"]["rows"],
            rel_rows=reliability["rows"],
            rel_pos=reliability["positive"],
            rel_neg=reliability["negative"],
            geom_rows=geometry["rows"],
            geom_pos=geometry["positive"],
            geom_neg=geometry["negative"],
            use_rows=usefulness["rows"],
            use_pos=usefulness["positive"],
            use_neg=usefulness["negative"],
            errors=summary["counts"]["ingestion_errors"],
            direct_pair_contrast=summary["pair_diagnostics"]["direct_reliable_unreliable_contrast_pairs"],
            probe=summary["target_independence_probes"][RELIABILITY_TARGET]["status"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
