#!/usr/bin/env python3
"""Fill the v4 matched-contrast reliability label sheet as a Codex proxy."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_external_review_fill as visible_fill


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

READINESS_DIR = RGA_ROOT / "reliability_target_v4_matched_contrast_label_readiness"
GAP_DIR = RGA_ROOT / "reliability_target_v4_matched_contrast_asset_packet_gap_audit"
DEFAULT_READINESS_SUMMARY = READINESS_DIR / "summary.json"
DEFAULT_INPUT_SHEET = READINESS_DIR / "ready_label_sheet.tsv"
DEFAULT_SCHEMA = READINESS_DIR / "label_schema.json"
DEFAULT_MANIFEST = READINESS_DIR / "ready_manifest_post_label_only.jsonl"
DEFAULT_LABEL_PATH_BASE = GAP_DIR
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested"

SCHEMA_VERSION = "h002_reliability_target_v4_matched_contrast_label_fill_summary_v1"
STATUS_READY = "h002_reliability_target_v4_matched_contrast_label_filled_codex_proxy_user_requested"
STATUS_ERROR = "h002_reliability_target_v4_matched_contrast_label_fill_errors"
REVIEWER_ID = "(codex_proxy_v4_user_requested_visible_only)"
REVIEW_ROUND = "1"

REVIEW_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_v4",
    "pair_evaluability_v4",
    "geometry_support_v4",
    "relation_usefulness_v4",
    "relation_reliability_v4",
    "primary_reason_v4",
    "uncertainty_reason_v4",
]

GENERIC_LABELS = {
    "item",
    "object",
    "objects",
    "furniture",
    "thing",
    "stuff",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-summary", type=Path, default=DEFAULT_READINESS_SUMMARY)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--label-path-base", type=Path, default=DEFAULT_LABEL_PATH_BASE)
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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
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


def resolve_label_path(value: str, base_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    repo_candidate = as_abs(path)
    if repo_candidate.exists():
        return repo_candidate
    return as_abs(base_dir) / path


def manifest_packet_paths_exist(manifest: dict[str, Any]) -> bool:
    packet_paths = manifest.get("packet_paths", {})
    for key in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
        value = packet_paths.get(key)
        if not value or not as_abs(Path(value)).exists():
            return False
    return True


def visible_packet_paths_exist(row: dict[str, str], label_path_base: Path) -> bool:
    for key in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
        value = row.get(key, "")
        if not value or not resolve_label_path(value, label_path_base).exists():
            return False
    return True


def validate_inputs(
    readiness_summary: dict[str, Any],
    fieldnames: list[str],
    rows: list[dict[str, str]],
    manifest_rows: list[dict[str, Any]],
    schema: dict[str, Any],
    label_path_base: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if readiness_summary.get("next_todo") != "reliability_target_v4_matched_contrast_label_fill":
        errors.append({"error_type": "unexpected_readiness_next_todo", "value": readiness_summary.get("next_todo")})
    if readiness_summary.get("status") != "h002_reliability_target_v4_matched_contrast_label_readiness_ready_for_label_fill":
        errors.append({"error_type": "unexpected_readiness_status", "value": readiness_summary.get("status")})

    boundary = readiness_summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": f"readiness_boundary_{key}_not_false", "value": boundary.get(key)})

    expected_rows = readiness_summary.get("counts", {}).get("label_ready_rows")
    if expected_rows != len(rows):
        errors.append({"error_type": "row_count_mismatch", "expected": expected_rows, "actual": len(rows)})
    if len(manifest_rows) != len(rows):
        errors.append({"error_type": "manifest_row_count_mismatch", "manifest": len(manifest_rows), "visible": len(rows)})

    expected_visible = schema.get("visible_fields", [])
    if expected_visible and fieldnames != expected_visible:
        errors.append({"error_type": "visible_columns_mismatch", "expected": expected_visible, "actual": fieldnames})

    visible_ids = [str(row.get("blind_review_id") or "") for row in rows]
    manifest_ids = [str(row.get("blind_review_id") or "") for row in manifest_rows]
    for blind_id, count in Counter(visible_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_visible_blind_review_id", "blind_review_id": blind_id, "count": count})
    for blind_id, count in Counter(manifest_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_manifest_blind_review_id", "blind_review_id": blind_id, "count": count})

    visible_set = {blind_id for blind_id in visible_ids if blind_id}
    manifest_set = {blind_id for blind_id in manifest_ids if blind_id}
    for blind_id in sorted(visible_set - manifest_set):
        errors.append({"error_type": "visible_id_missing_from_manifest", "blind_review_id": blind_id})
    for blind_id in sorted(manifest_set - visible_set):
        errors.append({"error_type": "manifest_id_missing_from_visible_sheet", "blind_review_id": blind_id})

    for row_number, row in enumerate(rows, start=2):
        for field in REVIEW_FIELDS + ["label_notes_v4"]:
            if str(row.get(field, "")).strip():
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": row.get("blind_review_id"),
                        "field": field,
                        "error_type": "review_field_already_filled",
                    }
                )
        if not visible_packet_paths_exist(row, label_path_base):
            errors.append(
                {
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id"),
                    "error_type": "visible_packet_path_missing",
                }
            )

    for manifest in manifest_rows:
        if not manifest_packet_paths_exist(manifest):
            errors.append(
                {
                    "blind_review_id": manifest.get("blind_review_id"),
                    "error_type": "manifest_packet_path_missing",
                }
            )
    return errors


def endpoint_identity(row: dict[str, str]) -> str:
    labels = {row.get("subject_label", "").strip().lower(), row.get("object_label", "").strip().lower()}
    if labels & GENERIC_LABELS:
        return "uncertain"
    if not row.get("subject_id") or not row.get("object_id"):
        return "endpoint_identity_issue"
    return "same_endpoints"


def visible_geometry_and_usefulness(row: dict[str, str]) -> tuple[str, str, str, str]:
    family = row.get("predicate_family", "")
    predicate = row.get("predicate_label", "")
    subject = row.get("subject_label", "")
    obj = row.get("object_label", "")
    if family == "relative_vertical":
        geometry, _mesh_geometry, usefulness, uncertainty = visible_fill.vertical_answer(predicate, subject, obj)
    elif family == "support_contact":
        geometry, _mesh_geometry, usefulness, uncertainty = visible_fill.support_answer(predicate, subject, obj)
    else:
        geometry, usefulness, uncertainty = "uncertain", "uncertain", "ambiguous_relation"

    geometry_v4 = {
        "supports_predicate": "supports",
        "contradicts_predicate": "contradicts",
        "uncertain": "ambiguous",
    }.get(geometry, "ambiguous")
    usefulness_v4 = {
        "informative": "useful_nontrivial",
        "trivial_dense_or_room_structure": "trivial_or_redundant",
        "ontology_mismatch": "not_a_relation",
        "uncertain": "uncertain",
    }.get(usefulness, "uncertain")
    return geometry_v4, usefulness_v4, usefulness, uncertainty


def uncertainty_reason_for(row: dict[str, str], uncertainty_hint: str) -> str:
    if row.get("evidence_packet_status") == "limited_view_evaluable":
        return "occlusion_or_view_limit"
    family = row.get("predicate_family")
    if uncertainty_hint == "ambiguous_relation":
        return "predicate_definition_ambiguous"
    if family == "support_contact":
        return "ambiguous_contact"
    if family == "relative_vertical":
        return "ambiguous_vertical_order"
    return "other"


def label_axes(row: dict[str, str]) -> dict[str, str]:
    endpoint = endpoint_identity(row)
    geometry, usefulness, raw_usefulness, uncertainty_hint = visible_geometry_and_usefulness(row)
    packet_status = row.get("evidence_packet_status", "")

    if endpoint == "endpoint_identity_issue":
        return {
            "endpoint_identity_v4": endpoint,
            "pair_evaluability_v4": "not_evaluable",
            "geometry_support_v4": "not_evaluable",
            "relation_usefulness_v4": "uncertain",
            "relation_reliability_v4": "uncertain",
            "primary_reason_v4": "endpoint_identity_issue",
            "uncertainty_reason_v4": "object_segmentation_issue",
        }

    if endpoint == "uncertain":
        return {
            "endpoint_identity_v4": endpoint,
            "pair_evaluability_v4": "needs_more_evidence",
            "geometry_support_v4": "ambiguous",
            "relation_usefulness_v4": "uncertain",
            "relation_reliability_v4": "uncertain",
            "primary_reason_v4": "endpoint_identity_issue",
            "uncertainty_reason_v4": "object_segmentation_issue",
        }

    if packet_status == "limited_view_evaluable":
        return {
            "endpoint_identity_v4": endpoint,
            "pair_evaluability_v4": "needs_more_evidence",
            "geometry_support_v4": "ambiguous",
            "relation_usefulness_v4": usefulness if usefulness != "not_a_relation" else "uncertain",
            "relation_reliability_v4": "uncertain",
            "primary_reason_v4": "insufficient_evidence",
            "uncertainty_reason_v4": "occlusion_or_view_limit",
        }

    if geometry == "contradicts":
        return {
            "endpoint_identity_v4": endpoint,
            "pair_evaluability_v4": "evaluable",
            "geometry_support_v4": geometry,
            "relation_usefulness_v4": usefulness,
            "relation_reliability_v4": "unreliable",
            "primary_reason_v4": "geometric_contradiction",
            "uncertainty_reason_v4": "",
        }

    if usefulness == "trivial_or_redundant":
        return {
            "endpoint_identity_v4": endpoint,
            "pair_evaluability_v4": "evaluable",
            "geometry_support_v4": geometry,
            "relation_usefulness_v4": usefulness,
            "relation_reliability_v4": "unreliable",
            "primary_reason_v4": "trivial_room_surface_or_structure",
            "uncertainty_reason_v4": "",
        }

    if usefulness == "not_a_relation":
        return {
            "endpoint_identity_v4": endpoint,
            "pair_evaluability_v4": "evaluable",
            "geometry_support_v4": geometry,
            "relation_usefulness_v4": usefulness,
            "relation_reliability_v4": "unreliable",
            "primary_reason_v4": "semantic_ontology_mismatch",
            "uncertainty_reason_v4": "",
        }

    if geometry == "supports" and usefulness == "useful_nontrivial":
        return {
            "endpoint_identity_v4": endpoint,
            "pair_evaluability_v4": "evaluable",
            "geometry_support_v4": geometry,
            "relation_usefulness_v4": usefulness,
            "relation_reliability_v4": "reliable",
            "primary_reason_v4": "geometric_support",
            "uncertainty_reason_v4": "",
        }

    if geometry == "ambiguous" and raw_usefulness == "ontology_mismatch":
        return {
            "endpoint_identity_v4": endpoint,
            "pair_evaluability_v4": "evaluable",
            "geometry_support_v4": "ambiguous",
            "relation_usefulness_v4": "not_a_relation",
            "relation_reliability_v4": "unreliable",
            "primary_reason_v4": "semantic_ontology_mismatch",
            "uncertainty_reason_v4": "",
        }

    return {
        "endpoint_identity_v4": endpoint,
        "pair_evaluability_v4": "evaluable",
        "geometry_support_v4": "ambiguous",
        "relation_usefulness_v4": "uncertain",
        "relation_reliability_v4": "uncertain",
        "primary_reason_v4": "insufficient_evidence",
        "uncertainty_reason_v4": uncertainty_reason_for(row, uncertainty_hint),
    }


def fill_row(row: dict[str, str]) -> dict[str, Any]:
    filled: dict[str, Any] = dict(row)
    filled.update(label_axes(row))
    filled["reviewer_id"] = REVIEWER_ID
    filled["review_round"] = REVIEW_ROUND
    filled["label_notes_v4"] = (
        "codex proxy v4 visible-only fill; used visible subject/object/predicate labels, "
        "predicate family question, cue text, and packet status; did not use hidden contrast "
        "role, semantic rank/score, p_geom_valid, geometry status, label-match status, or "
        "target-construction metadata before label lock"
    )
    return filled


def validate_filled_rows(rows: list[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = {key: set(values) for key, values in schema.get("allowed_review_values", {}).items()}
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id")
        for field in REVIEW_FIELDS:
            value = row.get(field)
            if value is None or (value == "" and field != "uncertainty_reason_v4"):
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "error_type": "missing_review_field",
                    }
                )
            elif field in allowed and value not in allowed[field]:
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "value": value,
                        "error_type": "invalid_review_value",
                    }
                )
        if not str(row.get("label_notes_v4", "")).strip():
            errors.append(
                {
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "field": "label_notes_v4",
                    "error_type": "missing_label_notes",
                }
            )
    return errors


def label_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v4_matched_contrast_proxy_label_v1",
        "blind_review_id": row["blind_review_id"],
        "review_scope": row["review_scope"],
        "scan_id": row["scan_id"],
        "scene_context_id": row["scene_context_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "evidence_packet_status": row["evidence_packet_status"],
        "packet_gap_decision": row.get("packet_gap_decision", ""),
        "v4_review_fields": {
            "reviewer_id": row["reviewer_id"],
            "review_round": row["review_round"],
            "endpoint_identity_v4": row["endpoint_identity_v4"],
            "pair_evaluability_v4": row["pair_evaluability_v4"],
            "geometry_support_v4": row["geometry_support_v4"],
            "relation_usefulness_v4": row["relation_usefulness_v4"],
            "relation_reliability_v4": row["relation_reliability_v4"],
            "primary_reason_v4": row["primary_reason_v4"],
            "uncertainty_reason_v4": row["uncertainty_reason_v4"],
            "label_notes_v4": row["label_notes_v4"],
        },
        "provenance": {
            "batch_name": "reliability_target_v4_matched_contrast_label_fill",
            "filled_by": "codex_proxy",
            "user_requested_proxy_fill": True,
            "actual_user_reviewer": False,
            "paper_evidence_allowed": False,
            "used_hidden_manifest_for_label_decision": False,
            "used_contrast_role_for_label_decision": False,
            "used_pair_id_for_label_decision": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "used_geometry_status": False,
            "used_label_match_status": False,
            "used_target_construction_metadata": False,
            "post_label_hidden_manifest_diagnostic_join": True,
            "validation_usage": False,
            "test_usage": False,
            "multi_view_as_model_input": False,
        },
    }


def diagnostic_group_value(manifest: dict[str, Any], group_key: str) -> str:
    value = manifest.get(group_key)
    if isinstance(value, list):
        return "|".join(str(item) for item in value) if value else "[]"
    if value is None or value == "":
        return "missing"
    return str(value)


def grouped_diagnostics(
    filled_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    group_key: str,
) -> list[dict[str, Any]]:
    manifest_by_id = {str(row["blind_review_id"]): row for row in manifest_rows}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in filled_rows:
        manifest = manifest_by_id.get(str(row["blind_review_id"]), {})
        grouped[diagnostic_group_value(manifest, group_key)].append(row)

    diagnostics: list[dict[str, Any]] = []
    for value, rows in sorted(grouped.items()):
        reliability = Counter(row["relation_reliability_v4"] for row in rows)
        geometry = Counter(row["geometry_support_v4"] for row in rows)
        usefulness = Counter(row["relation_usefulness_v4"] for row in rows)
        primary = Counter(row["primary_reason_v4"] for row in rows)
        diagnostics.append(
            {
                "group_key_post_label_only": group_key,
                "group_value": value,
                "rows": len(rows),
                "reliable": reliability.get("reliable", 0),
                "unreliable": reliability.get("unreliable", 0),
                "uncertain": reliability.get("uncertain", 0),
                "geometry_counts": json.dumps(dict(sorted(geometry.items())), sort_keys=True),
                "usefulness_counts": json.dumps(dict(sorted(usefulness.items())), sort_keys=True),
                "primary_reason_counts": json.dumps(dict(sorted(primary.items())), sort_keys=True),
            }
        )
    return diagnostics


def post_label_diagnostics(
    filled_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for group_key in [
        "matched_contrast_pair_id_hidden",
        "matched_contrast_role_hidden",
        "contrast_role_hidden",
        "matched_contrast_level_hidden",
        "object_family_cell_hidden",
        "endpoint_flag_pattern_hidden",
        "subject_object_family_cell_hidden",
        "label_match_status_hidden",
        "label_match_family_hidden",
        "label_geometry_bucket_hidden",
        "source_queue_hidden",
        "rank_band_hidden",
        "geometry_status_hidden",
        "asset_packet_source_hidden",
        "row_gap_decision_hidden",
        "pair_gap_decision_hidden",
    ]:
        diagnostics.extend(grouped_diagnostics(filled_rows, manifest_rows, group_key))
    return diagnostics


def pair_diagnostics(filled_rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest_by_id = {str(row["blind_review_id"]): row for row in manifest_rows}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in filled_rows:
        manifest = manifest_by_id.get(str(row["blind_review_id"]), {})
        pair_id = str(manifest.get("matched_contrast_pair_id_hidden", "missing"))
        grouped[pair_id].append(row)

    diagnostics: list[dict[str, Any]] = []
    for pair_id, rows in sorted(grouped.items()):
        reliability = Counter(row["relation_reliability_v4"] for row in rows)
        roles = Counter()
        for row in rows:
            manifest = manifest_by_id.get(str(row["blind_review_id"]), {})
            roles[str(manifest.get("matched_contrast_role_hidden", "missing"))] += 1
        diagnostics.append(
            {
                "matched_contrast_pair_id_hidden": pair_id,
                "rows": len(rows),
                "positive_proxy_rows": roles.get("positive_proxy", 0),
                "negative_proxy_rows": roles.get("negative_proxy", 0),
                "reliable": reliability.get("reliable", 0),
                "unreliable": reliability.get("unreliable", 0),
                "uncertain": reliability.get("uncertain", 0),
                "pair_label_pattern": "/".join(sorted(row["relation_reliability_v4"] for row in rows)),
            }
        )
    return diagnostics


def binary_target_rows(filled_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for row in filled_rows:
        label = row["relation_reliability_v4"]
        if label == "uncertain":
            continue
        targets.append(
            {
                "schema_version": "h002_reliability_target_v4_matched_contrast_binary_target_v1",
                "blind_review_id": row["blind_review_id"],
                "scan_id": row["scan_id"],
                "scene_context_id": row["scene_context_id"],
                "subject_id": row["subject_id"],
                "object_id": row["object_id"],
                "predicate_label": row["predicate_label"],
                "predicate_family": row["predicate_family"],
                "relation_reliability_v4": label,
                "relation_reliability_v4_binary": 1 if label == "reliable" else 0,
                "target_source": "codex_proxy_user_requested_visible_only_v4_label_fill",
                "split": "train_only",
                "paper_evidence_allowed": False,
            }
        )
    return targets


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    reliability = counts["relation_reliability_v4"]
    geometry = counts["geometry_support_v4"]
    usefulness = counts["relation_usefulness_v4"]
    lines = [
        "# H002 Reliability Target V4 Matched Contrast Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage label fill.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Filled by Codex proxy at user request; this is not independent human annotation.",
        "- Label decisions use only labeler-visible identity, predicate/family question, cue text, and packet status.",
        "- Hidden contrast role, pair id, semantic score/rank, `p_geom_valid`, geometry status, label-match status, and target-construction metadata are not used before label lock.",
        "- Hidden manifest is joined only after label fill for diagnostics.",
        "- Multi-view remains audit/label evidence only and is not posterior input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {counts['rows']} |",
        f"| reliable | {reliability.get('reliable', 0)} |",
        f"| unreliable | {reliability.get('unreliable', 0)} |",
        f"| uncertain | {reliability.get('uncertain', 0)} |",
        f"| binary usable rows | {counts['binary_target_rows']} |",
        f"| binary positive rows | {counts['binary_positive_rows']} |",
        f"| binary negative rows | {counts['binary_negative_rows']} |",
        f"| input validation errors | {counts['input_validation_errors']} |",
        f"| fill validation errors | {counts['fill_validation_errors']} |",
        "",
        "## Geometry Support",
        "",
        "| Geometry support | Count |",
        "| --- | ---: |",
    ]
    for key, value in geometry.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Relation Usefulness", "", "| Usefulness | Count |", "| --- | ---: |"])
    for key, value in usefulness.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Interpretation",
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


def run(args: argparse.Namespace) -> dict[str, Any]:
    readiness_summary_path = as_abs(args.readiness_summary)
    input_sheet = as_abs(args.input_sheet)
    schema_path = as_abs(args.schema)
    manifest_path = as_abs(args.manifest)
    label_path_base = as_abs(args.label_path_base)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    fieldnames, visible_rows = read_tsv(input_sheet)
    schema = read_json(schema_path)
    manifest_rows = read_jsonl(manifest_path)
    readiness_summary = read_json(readiness_summary_path)

    input_errors = validate_inputs(
        readiness_summary=readiness_summary,
        fieldnames=fieldnames,
        rows=visible_rows,
        manifest_rows=manifest_rows,
        schema=schema,
        label_path_base=label_path_base,
    )
    filled_rows = [fill_row(row) for row in visible_rows]
    fill_errors = validate_filled_rows(filled_rows, schema)
    label_rows = [label_record(row) for row in filled_rows]
    targets = binary_target_rows(filled_rows)
    diagnostics = post_label_diagnostics(filled_rows, manifest_rows)
    pairs = pair_diagnostics(filled_rows, manifest_rows)

    reliability_counts = Counter(row["relation_reliability_v4"] for row in filled_rows)
    geometry_counts = Counter(row["geometry_support_v4"] for row in filled_rows)
    usefulness_counts = Counter(row["relation_usefulness_v4"] for row in filled_rows)
    family_counts = Counter(row["predicate_family"] for row in filled_rows)
    endpoint_counts = Counter(row["endpoint_identity_v4"] for row in filled_rows)
    evaluability_counts = Counter(row["pair_evaluability_v4"] for row in filled_rows)
    primary_counts = Counter(row["primary_reason_v4"] for row in filled_rows)
    uncertainty_counts = Counter(row["uncertainty_reason_v4"] for row in filled_rows)
    packet_status_counts = Counter(row["evidence_packet_status"] for row in filled_rows)
    target_counts = Counter(row["relation_reliability_v4_binary"] for row in targets)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "completed_sheet": output_dir / "completed_v4_matched_contrast_label_sheet_codex_proxy_user_requested.tsv",
        "v4_proxy_labels": output_dir / "v4_proxy_labels.jsonl",
        "relation_reliability_v4_binary_targets": output_dir / "relation_reliability_v4_binary_targets.jsonl",
        "post_label_diagnostics": output_dir / "post_label_diagnostics.csv",
        "post_label_diagnostics_json": output_dir / "post_label_diagnostics.json",
        "pair_post_label_diagnostics": output_dir / "pair_post_label_diagnostics.csv",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
        "input_validation_errors": output_dir / "input_validation_errors.jsonl",
    }

    errors = input_errors + fill_errors
    status = STATUS_ERROR if errors else STATUS_READY
    next_todo = (
        "fix_reliability_target_v4_matched_contrast_label_fill"
        if errors
        else "reliability_target_v4_matched_contrast_label_ingestion"
    )
    decision = (
        "Input or fill validation errors block ingestion."
        if errors
        else (
            "Filled the 158-row / 79-pair v4 matched-contrast sheet as a user-requested "
            "Codex proxy. This creates hypothesis-stage labels and binary target rows for "
            "ingestion and target-independence audit, but it is not paper metric evidence "
            "and does not unlock posterior smoke by itself."
        )
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "input_paths": {
            "readiness_summary": rel_path(readiness_summary_path),
            "ready_label_sheet": rel_path(input_sheet),
            "label_schema": rel_path(schema_path),
            "ready_manifest_post_label_only": rel_path(manifest_path),
            "label_path_base": rel_path(label_path_base),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "filled_by": "codex_proxy",
            "user_requested_proxy_fill": True,
            "actual_user_reviewer": False,
            "paper_evidence_allowed": False,
            "used_hidden_manifest_for_label_decision": False,
            "used_contrast_role_for_label_decision": False,
            "used_pair_id_for_label_decision": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "used_geometry_status": False,
            "used_label_match_status": False,
            "used_target_construction_metadata": False,
            "post_label_hidden_manifest_diagnostic_join": True,
            "multi_view_as_model_input": False,
        },
        "counts": {
            "rows": len(filled_rows),
            "input_validation_errors": len(input_errors),
            "fill_validation_errors": len(fill_errors),
            "by_family": dict(sorted(family_counts.items())),
            "packet_status": dict(sorted(packet_status_counts.items())),
            "endpoint_identity_v4": dict(sorted(endpoint_counts.items())),
            "pair_evaluability_v4": dict(sorted(evaluability_counts.items())),
            "geometry_support_v4": dict(sorted(geometry_counts.items())),
            "relation_usefulness_v4": dict(sorted(usefulness_counts.items())),
            "relation_reliability_v4": dict(sorted(reliability_counts.items())),
            "primary_reason_v4": dict(sorted(primary_counts.items())),
            "uncertainty_reason_v4": dict(sorted(uncertainty_counts.items())),
            "binary_target_rows": len(targets),
            "binary_positive_rows": target_counts.get(1, 0),
            "binary_negative_rows": target_counts.get(0, 0),
            "pair_count": len(pairs),
        },
        "post_label_diagnostics": diagnostics,
        "pair_post_label_diagnostics": pairs,
        "next_todo": next_todo,
    }

    write_tsv(output_paths["completed_sheet"], filled_rows, fieldnames)
    write_jsonl(output_paths["v4_proxy_labels"], label_rows)
    write_jsonl(output_paths["relation_reliability_v4_binary_targets"], targets)
    write_csv(output_paths["post_label_diagnostics"], diagnostics)
    write_json(output_paths["post_label_diagnostics_json"], {"diagnostics": diagnostics})
    write_csv(output_paths["pair_post_label_diagnostics"], pairs)
    write_jsonl(output_paths["fill_validation_errors"], fill_errors)
    write_jsonl(output_paths["input_validation_errors"], input_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    reliability = counts["relation_reliability_v4"]
    print(
        "status={status} rows={rows} reliable={reliable} unreliable={unreliable} "
        "uncertain={uncertain} binary_rows={binary_rows} binary_pos={binary_pos} "
        "binary_neg={binary_neg} input_errors={input_errors} fill_errors={fill_errors} "
        "validation_used={validation_used} test_used={test_used} posterior_allowed={posterior_allowed} "
        "next={next_todo}".format(
            status=summary["status"],
            rows=counts["rows"],
            reliable=reliability.get("reliable", 0),
            unreliable=reliability.get("unreliable", 0),
            uncertain=reliability.get("uncertain", 0),
            binary_rows=counts["binary_target_rows"],
            binary_pos=counts["binary_positive_rows"],
            binary_neg=counts["binary_negative_rows"],
            input_errors=counts["input_validation_errors"],
            fill_errors=counts["fill_validation_errors"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
