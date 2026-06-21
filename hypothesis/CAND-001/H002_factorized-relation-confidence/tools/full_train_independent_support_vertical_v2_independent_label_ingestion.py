#!/usr/bin/env python3
"""Ingest independent support/vertical labels after label lock."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_label_ingestion as base


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FILL_DIR = RGA_ROOT / "independent_support_vertical_v2_independent_label_fill_codex_independent_ver"
DEFAULT_DECISION_DIR = RGA_ROOT / "independent_support_vertical_v2_target_path_decision_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver"

DEFAULT_COMPLETED_SHEET = DEFAULT_FILL_DIR / "completed_independent_collection_sheet_codex_independent_ver.tsv"
DEFAULT_FILL_SUMMARY = DEFAULT_FILL_DIR / "summary.json"
DEFAULT_SCHEMA = DEFAULT_DECISION_DIR / "independent_collection_schema.json"
DEFAULT_INTERNAL_MANIFEST = DEFAULT_DECISION_DIR / "internal_manifest_post_label_only.jsonl"

LABEL_SOURCE = "codex_independent_support_vertical_visible_only_bootstrap"
SELECTED_FAMILIES = {"support_contact", "relative_vertical"}

GEOMETRY_TARGET_NAME = "geometry_validity_independent_target"
RELIABILITY_TARGET_NAME = "relation_reliability_independent_target"

INDEPENDENT_AXIS_KEYS = [
    "endpoint_identity_independent",
    "pair_evaluability_independent",
    "geometry_validity_independent",
    "relation_reliability_independent",
    "primary_reason_independent",
    "uncertainty_reason_independent",
]

HIDDEN_GROUP_KEYS = [
    "queue_kind_hidden",
    "proposed_audit_role_hidden",
    "label_match_status_hidden",
    "geometry_status_hidden",
    "rank_band_hidden",
    "relation_validity_label_hidden",
    "label_use_hidden",
    "posterior_target_y_hidden",
]

FORBIDDEN_COMPLETED_HEADER_FRAGMENTS = [
    "semantic_score",
    "semantic_rank",
    "source_score",
    "source_rank",
    "confidence",
    "p_geom",
    "geometry_status",
    "label_match",
    "proposed_audit_role",
    "queue_kind",
    "rank_band",
    "posterior_target",
    "target_y",
    "label_use",
    "relation_validity_label",
    "hidden",
    "hidden_strata",
    "v2_",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-sheet", type=Path, default=DEFAULT_COMPLETED_SHEET)
    parser.add_argument("--fill-summary", type=Path, default=DEFAULT_FILL_SUMMARY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--internal-manifest", type=Path, default=DEFAULT_INTERNAL_MANIFEST)
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
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
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def hidden_value(internal: dict[str, Any], key: str) -> Any:
    if key in internal:
        return internal.get(key)
    hidden = internal.get("hidden_strata") or {}
    return hidden.get(key)


def validate_completed_headers(fieldnames: list[str], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = ["blind_review_id", *schema["required_completion_fields"]]
    for field in required:
        if field not in fieldnames:
            errors.append({"error_type": "missing_required_header", "field": field})
    for field in fieldnames:
        lower = field.lower()
        matches = [token for token in FORBIDDEN_COMPLETED_HEADER_FRAGMENTS if token in lower]
        if matches:
            errors.append({"error_type": "forbidden_completed_header", "field": field, "matches": matches})
    return errors


def validate_completed_row(
    row: dict[str, str],
    row_number: int,
    schema: dict[str, Any],
    internal: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = schema["allowed_review_values"]
    blind_id = str(row.get("blind_review_id") or "")
    for field in schema["required_completion_fields"]:
        value = str(row.get(field, "")).strip()
        if not value:
            errors.append(
                {
                    "error_type": "missing_required_completion_field",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "field": field,
                }
            )
            continue
        if field in allowed and value not in set(allowed[field]):
            errors.append(
                {
                    "error_type": "invalid_review_value",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "field": field,
                    "value": value,
                    "allowed": allowed[field],
                }
            )
    if row.get("predicate_family") not in SELECTED_FAMILIES:
        errors.append(
            {
                "error_type": "completed_row_family_outside_selected_scope",
                "row_number": row_number,
                "blind_review_id": blind_id,
                "predicate_family": row.get("predicate_family"),
            }
        )
    if internal is not None:
        for key in ("scan_id", "predicate_label", "predicate_family"):
            if str(row.get(key) or "") != str(internal.get(key) or ""):
                errors.append(
                    {
                        "error_type": "completed_internal_identity_mismatch",
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": key,
                        "completed_value": row.get(key),
                        "internal_value": internal.get(key),
                    }
                )
    return errors


def validate_id_sets(completed_rows: list[dict[str, str]], internal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    completed_ids = [str(row.get("blind_review_id") or "") for row in completed_rows]
    internal_ids = [str(row.get("blind_review_id") or "") for row in internal_rows]
    for blind_id, count in Counter(completed_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_completed_blind_review_id", "blind_review_id": blind_id, "count": count})
    for blind_id, count in Counter(internal_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_internal_blind_review_id", "blind_review_id": blind_id, "count": count})
    completed_set = {blind_id for blind_id in completed_ids if blind_id}
    internal_set = {blind_id for blind_id in internal_ids if blind_id}
    for blind_id in sorted(completed_set - internal_set):
        errors.append({"error_type": "completed_id_missing_from_internal_manifest", "blind_review_id": blind_id})
    for blind_id in sorted(internal_set - completed_set):
        errors.append({"error_type": "internal_manifest_id_missing_from_completed_sheet", "blind_review_id": blind_id})
    return errors


def validate_internal_rows(internal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for idx, row in enumerate(internal_rows, start=1):
        blind_id = row.get("blind_review_id")
        if row.get("post_label_join_only") is not True:
            errors.append({"error_type": "internal_manifest_not_post_label_only", "row_number": idx, "blind_review_id": blind_id})
        if row.get("labeler_visible") is not False:
            errors.append({"error_type": "internal_manifest_marked_labeler_visible", "row_number": idx, "blind_review_id": blind_id})
        if row.get("predicate_family") not in SELECTED_FAMILIES:
            errors.append(
                {
                    "error_type": "internal_manifest_family_outside_selected_scope",
                    "row_number": idx,
                    "blind_review_id": blind_id,
                    "predicate_family": row.get("predicate_family"),
                }
            )
        hidden = row.get("hidden_strata")
        if not isinstance(hidden, dict):
            errors.append({"error_type": "internal_manifest_missing_hidden_strata", "row_number": idx, "blind_review_id": blind_id})
            continue
        for key in HIDDEN_GROUP_KEYS:
            if key not in hidden:
                errors.append({"error_type": "internal_manifest_missing_hidden_key", "row_number": idx, "blind_review_id": blind_id, "field": key})
        v2_reference = row.get("v2_audit_axes_post_label_reference")
        if not isinstance(v2_reference, dict):
            errors.append({"error_type": "internal_manifest_missing_v2_reference", "row_number": idx, "blind_review_id": blind_id})
    return errors


def validate_fill_boundary(fill_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    boundary = fill_summary.get("boundary", {})
    expected_false = [
        "hidden_manifest_read",
        "v2_codex_axes_read",
        "prior_label_or_label_use_read",
        "semantic_score_or_rank_used",
        "p_geom_valid_used",
        "geometry_status_used",
        "multi_view_as_model_input",
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "human_confirmed",
        "paper_evidence_allowed",
        "posterior_claim_allowed",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_summary_boundary_not_false", "field": key, "value": boundary.get(key)})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "fill_summary_boundary_not_train_only", "value": boundary.get("split")})
    return errors


def derive_geometry_validity(row: dict[str, str]) -> dict[str, Any]:
    value = row["geometry_validity_independent"]
    if value == "supports_predicate":
        return {
            "target_name": GEOMETRY_TARGET_NAME,
            "target_use": "positive",
            "target_y": 1,
            "reason": "independent_geometry_supports_predicate",
        }
    if value == "contradicts_predicate":
        return {
            "target_name": GEOMETRY_TARGET_NAME,
            "target_use": "negative",
            "target_y": 0,
            "reason": "independent_geometry_contradicts_predicate",
        }
    return {
        "target_name": GEOMETRY_TARGET_NAME,
        "target_use": "exclude",
        "target_y": None,
        "reason": f"exclude_independent_geometry={value}",
    }


def derive_relation_reliability(row: dict[str, str]) -> dict[str, Any]:
    value = row["relation_reliability_independent"]
    if value == "reliable":
        return {
            "target_name": RELIABILITY_TARGET_NAME,
            "target_use": "positive",
            "target_y": 1,
            "reason": "independent_relation_reliable",
        }
    if value == "unreliable":
        return {
            "target_name": RELIABILITY_TARGET_NAME,
            "target_use": "negative",
            "target_y": 0,
            "reason": "independent_relation_unreliable",
        }
    return {
        "target_name": RELIABILITY_TARGET_NAME,
        "target_use": "exclude",
        "target_y": None,
        "reason": f"exclude_independent_reliability={value}",
    }


def independent_label_fields(row: dict[str, str]) -> dict[str, Any]:
    output = {
        "reviewer_id": row.get("reviewer_id"),
        "review_round": row.get("review_round"),
        "label_notes_independent": row.get("label_notes_independent"),
        "not_model_input": True,
    }
    for key in INDEPENDENT_AXIS_KEYS:
        output[key] = row.get(key)
    return output


def deployable_evidence(row: dict[str, str]) -> dict[str, Any]:
    visible_witness = {key: base.safe_float(row.get(key)) for key in base.VISIBLE_WITNESS_KEYS if key in row}
    return {
        "source_semantic_and_geometry_scores_hidden_from_labeler_until_lock": {
            "available_in_this_ingestion": False,
            "reason": (
                "The independent target-path manifest intentionally excludes semantic score, "
                "semantic rank, and p_geom_valid. Join source-score features only after this "
                "label-locked artifact if posterior smoke is later allowed."
            ),
        },
        "raw_visible_witness_values": visible_witness,
        "coverage_evidence": {
            "evidence_packet_status": row.get("evidence_packet_status"),
        },
        "audit_packet_paths_not_model_input": {
            "multiview_packet": row.get("multiview_packet"),
            "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet"),
            "contact_or_context_sheet": row.get("contact_or_context_sheet"),
        },
        "forbidden_as_posterior_input": {
            "independent_label_fields": True,
            "hidden_strata": True,
            "v2_audit_axes_post_label_reference": True,
            "geometry_status_hidden": True,
            "label_match_status_hidden": True,
            "proposed_audit_role_hidden": True,
            "queue_kind_hidden": True,
            "relation_validity_label_hidden": True,
            "posterior_target_y_hidden": True,
            "audit_packet_paths": True,
            "multi_view_as_model_input": True,
        },
    }


def hidden_audit_metadata(internal: dict[str, Any]) -> dict[str, Any]:
    metadata = {key: hidden_value(internal, key) for key in HIDDEN_GROUP_KEYS}
    metadata["in_relation_reliability_rank_band_construction_slice"] = internal.get(
        "in_relation_reliability_rank_band_construction_slice"
    )
    metadata["v2_audit_axes_post_label_reference"] = internal.get("v2_audit_axes_post_label_reference", {})
    return metadata


def base_identity(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "prediction_id": row.get("blind_review_id"),
        "scan_id": row.get("scan_id") or internal.get("scan_id"),
        "subgraph_id": row.get("scene_context_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label") or internal.get("predicate_label"),
        "predicate_family": row.get("predicate_family") or internal.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "evidence_packet_status": row.get("evidence_packet_status"),
    }


def make_validated_label(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    geometry_target = derive_geometry_validity(row)
    reliability_target = derive_relation_reliability(row)
    return {
        "schema_version": "h002_support_vertical_v2_independent_ingested_label_v1",
        **base_identity(row, internal),
        "label_source": LABEL_SOURCE,
        "not_human_confirmed": True,
        "paper_evidence_allowed": False,
        "posterior_claim_allowed": False,
        "hidden_manifest_joined_after_label_lock": True,
        "independent_label_fields_are_target_only": True,
        "direct_relation_reliability_label_present": True,
        "independent_label_fields": independent_label_fields(row),
        "geometry_validity_independent_target": geometry_target,
        "relation_reliability_independent_target": reliability_target,
        "deployable_evidence_after_label_lock": deployable_evidence(row),
        "hidden_audit_metadata_post_label_only": hidden_audit_metadata(internal),
        "boundary": {
            "split": "train_only",
            "label_source": LABEL_SOURCE,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_target_metadata_as_model_input": False,
            "independent_label_fields_as_model_input": False,
            "v2_audit_axes_as_model_input": False,
            "multi_view_as_model_input": False,
            "source_score_feature_join_pending": True,
        },
    }


def ingest(
    completed_rows: list[dict[str, str]],
    internal_rows: list[dict[str, Any]],
    schema: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    internal_by_id = {str(row["blind_review_id"]): row for row in internal_rows}
    labels: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(completed_rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        row_errors: list[dict[str, Any]] = []
        if not blind_id:
            row_errors.append({"error_type": "missing_blind_review_id", "row_number": row_number})
        internal = internal_by_id.get(blind_id)
        if internal is None:
            row_errors.append({"error_type": "missing_internal_manifest_for_completed_row", "row_number": row_number, "blind_review_id": blind_id})
        row_errors.extend(validate_completed_row(row, row_number, schema, internal))
        if row_errors:
            errors.extend(row_errors)
            continue
        labels.append(make_validated_label(row, internal_by_id[blind_id]))
    return labels, errors


def target_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is None:
        return None
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
        "human_confirmed": False,
        "paper_locked": False,
    }


def posterior_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    row = target_row(label, target_key, schema_version)
    if row is None:
        return None
    return {
        **row,
        "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
        "audit_only_independent_label_fields": label["independent_label_fields"],
        "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
        "audit_note": (
            "This is a label-locked train-only posterior-row shell. Use only deployable evidence "
            "after an explicit source-score feature join. Do not use independent labels, hidden "
            "strata, or v2 audit axes as model input."
        ),
    }


def excluded_target_row(label: dict[str, Any], target_key: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is not None:
        return None
    return {
        "schema_version": "h002_support_vertical_v2_independent_excluded_target_v1",
        "target_name": target["target_name"],
        "target_use": target["target_use"],
        "target_y": None,
        "target_reason": target["reason"],
        "blind_review_id": label["blind_review_id"],
        "prediction_id": label["prediction_id"],
        "scan_id": label["scan_id"],
        "predicate_label": label["predicate_label"],
        "predicate_family": label["predicate_family"],
        "subject_label": label["subject_label"],
        "object_label": label["object_label"],
        "audit_only_independent_label_fields": label["independent_label_fields"],
    }


def count_target(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_counts = Counter(row["target_y"] for row in rows)
    total = len(rows)
    return {
        "rows": total,
        "positive": target_counts[1],
        "negative": target_counts[0],
        "positive_rate": (target_counts[1] / total) if total else 0.0,
        "by_family": base.nested_target_counts(rows, "predicate_family"),
        "by_predicate": base.nested_target_counts(rows, "predicate_label"),
    }


def axis_counts(labels: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for axis in INDEPENDENT_AXIS_KEYS:
        output[axis] = dict(sorted(Counter(row["independent_label_fields"].get(axis) for row in labels).items()))
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Full-Train Independent Support/Vertical V2 Independent Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained in this step.",
        "- Independent labels are joined to hidden strata only after label lock.",
        "- Independent label fields, hidden strata, and v2 reference axes are audit-only.",
        "- Multi-view/mesh packet paths remain audit evidence only, not model input.",
        "- Source score/rank and `p_geom_valid` feature join is pending by design.",
        "- Labels are Codex independent visible-only bootstrap labels, not human-confirmed paper evidence.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| completed sheet rows | {counts['completed_sheet_rows']} |",
        f"| internal manifest rows | {counts['internal_manifest_rows']} |",
        f"| validated independent labels | {counts['validated_label_rows']} |",
        f"| ingestion errors | {counts['errors']} |",
        "",
        "## Target Counts",
        "",
        "| Target | Rows | Positive | Negative | Positive Rate | Excluded |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for target_name in [GEOMETRY_TARGET_NAME, RELIABILITY_TARGET_NAME]:
        item = counts["targets"][target_name]
        lines.append(
            f"| `{target_name}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['positive_rate']:.4f} | {counts['excluded_targets'][target_name]} |"
        )
    lines.extend(["", "## Axis Counts", ""])
    for axis, values in summary["axis_counts"].items():
        joined = ", ".join(f"`{key}:{value}`" for key, value in values.items())
        lines.append(f"- `{axis}`: {joined}")
    lines.extend(
        [
            "",
            "## Target Independence Probe",
            "",
            "| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for target_name, probe in summary["target_independence_probes"].items():
        lines.append(
            f"| `{target_name}` | `{probe['status']}` | {len(probe['hidden_risks'])} | "
            f"{len(probe['visible_non_target_shortcuts'])} |"
        )
    lines.extend(
        [
            "",
            "## Top Hidden Risks",
            "",
            "| Target | Hidden Key | Majority Acc | NMI | Pos Rate Range |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for target_name, probe in summary["target_independence_probes"].items():
        for item in probe["hidden_risks"][:6]:
            lines.append(
                f"| `{target_name}` | `{item['group_key']}` | {item['majority_rule_accuracy']:.4f} | "
                f"{item['normalized_mutual_information']:.4f} | {item['positive_rate_range']:.4f} |"
            )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    completed_sheet = as_abs(args.completed_sheet)
    fill_summary_path = as_abs(args.fill_summary)
    schema_path = as_abs(args.schema)
    internal_manifest_path = as_abs(args.internal_manifest)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    fieldnames, completed_rows = read_tsv(completed_sheet)
    fill_summary = read_json(fill_summary_path)
    schema = read_json(schema_path)
    internal_rows = read_jsonl(internal_manifest_path)

    errors: list[dict[str, Any]] = []
    errors.extend(validate_completed_headers(fieldnames, schema))
    errors.extend(validate_id_sets(completed_rows, internal_rows))
    errors.extend(validate_internal_rows(internal_rows))
    errors.extend(validate_fill_boundary(fill_summary))

    validated_labels, row_errors = ingest(completed_rows, internal_rows, schema)
    errors.extend(row_errors)

    geometry_targets = [
        row
        for row in (
            target_row(label, "geometry_validity_independent_target", "h002_support_vertical_v2_independent_geometry_validity_target_v1")
            for label in validated_labels
        )
        if row is not None
    ]
    reliability_targets = [
        row
        for row in (
            target_row(label, "relation_reliability_independent_target", "h002_support_vertical_v2_independent_relation_reliability_target_v1")
            for label in validated_labels
        )
        if row is not None
    ]
    geometry_posterior_rows = [
        row
        for row in (
            posterior_row(
                label,
                "geometry_validity_independent_target",
                "h002_support_vertical_v2_independent_geometry_validity_posterior_row_v1",
            )
            for label in validated_labels
        )
        if row is not None
    ]
    reliability_posterior_rows = [
        row
        for row in (
            posterior_row(
                label,
                "relation_reliability_independent_target",
                "h002_support_vertical_v2_independent_relation_reliability_posterior_row_v1",
            )
            for label in validated_labels
        )
        if row is not None
    ]
    excluded_targets = [
        row
        for label in validated_labels
        for row in (
            excluded_target_row(label, "geometry_validity_independent_target"),
            excluded_target_row(label, "relation_reliability_independent_target"),
        )
        if row is not None
    ]

    probes = {
        GEOMETRY_TARGET_NAME: base.target_independence_probe(geometry_posterior_rows, GEOMETRY_TARGET_NAME),
        RELIABILITY_TARGET_NAME: base.target_independence_probe(reliability_posterior_rows, RELIABILITY_TARGET_NAME),
    }
    all_group_rows = [row for probe in probes.values() for row in probe["group_table"]]
    all_probe_summaries = [row for probe in probes.values() for row in probe["summaries"]]

    target_counts = {
        GEOMETRY_TARGET_NAME: count_target(geometry_targets),
        RELIABILITY_TARGET_NAME: count_target(reliability_targets),
    }
    excluded_counts = Counter(row["target_name"] for row in excluded_targets)

    if errors:
        status = "full_train_independent_support_vertical_v2_independent_label_ingestion_errors"
        decision = "Fix independent support/vertical ingestion errors before target audit or posterior smoke."
        next_todo = "fix_full_train_independent_support_vertical_v2_independent_label_ingestion_errors"
    elif any(probe["status"] != "target_independence_probe_pass" for probe in probes.values()):
        status = "full_train_independent_support_vertical_v2_independent_label_ingested_with_basic_probe_risk"
        decision = (
            "Independent labels are materialized, but the basic post-label group probe still "
            "detects target-construction or visible-surface correlation risk. Run the dedicated "
            "independent target-independence audit before any posterior smoke."
        )
        next_todo = "full_train_independent_support_vertical_v2_independent_target_independence_audit"
    else:
        status = "full_train_independent_support_vertical_v2_independent_label_ingested_ready_for_target_audit"
        decision = (
            "Independent labels are materialized and the basic group probe did not flag shortcut "
            "risk. Still run the dedicated independent target-independence audit before posterior smoke."
        )
        next_todo = "full_train_independent_support_vertical_v2_independent_target_independence_audit"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validated_labels": output_dir / "validated_independent_labels.jsonl",
        "geometry_validity_targets": output_dir / "geometry_validity_independent_targets.jsonl",
        "relation_reliability_targets": output_dir / "relation_reliability_independent_targets.jsonl",
        "geometry_validity_posterior_rows": output_dir / "geometry_validity_independent_posterior_rows.jsonl",
        "relation_reliability_posterior_rows": output_dir / "relation_reliability_independent_posterior_rows.jsonl",
        "excluded_targets": output_dir / "excluded_independent_targets.jsonl",
        "target_independence_probe": output_dir / "target_independence_probe.json",
        "target_group_table": output_dir / "target_group_table.csv",
        "shortcut_audit": output_dir / "shortcut_audit.csv",
        "ingestion_errors": output_dir / "ingestion_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_support_vertical_v2_independent_label_ingestion_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "completed_sheet": rel_path(completed_sheet),
            "fill_summary": rel_path(fill_summary_path),
            "independent_collection_schema": rel_path(schema_path),
            "internal_manifest_post_label_only": rel_path(internal_manifest_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "selected_scope": sorted(SELECTED_FAMILIES),
            "label_source": LABEL_SOURCE,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_manifest_joined_after_label_lock": True,
            "hidden_target_metadata_as_model_input": False,
            "independent_label_fields_as_model_input": False,
            "v2_audit_axes_as_model_input": False,
            "source_score_feature_join_pending": True,
            "multi_view_as_model_input": False,
            "geometry_validity_and_relation_reliability_separated": True,
        },
        "counts": {
            "completed_sheet_rows": len(completed_rows),
            "internal_manifest_rows": len(internal_rows),
            "validated_label_rows": len(validated_labels),
            "errors": len(errors),
            "targets": target_counts,
            "excluded_targets": {
                GEOMETRY_TARGET_NAME: excluded_counts[GEOMETRY_TARGET_NAME],
                RELIABILITY_TARGET_NAME: excluded_counts[RELIABILITY_TARGET_NAME],
            },
        },
        "axis_counts": axis_counts(validated_labels),
        "target_independence_probes": {
            target_name: {key: value for key, value in probe.items() if key != "group_table"}
            for target_name, probe in probes.items()
        },
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["target_independence_probe"], probes)
    write_jsonl(output_paths["validated_labels"], validated_labels)
    write_jsonl(output_paths["geometry_validity_targets"], geometry_targets)
    write_jsonl(output_paths["relation_reliability_targets"], reliability_targets)
    write_jsonl(output_paths["geometry_validity_posterior_rows"], geometry_posterior_rows)
    write_jsonl(output_paths["relation_reliability_posterior_rows"], reliability_posterior_rows)
    write_jsonl(output_paths["excluded_targets"], excluded_targets)
    write_jsonl(output_paths["ingestion_errors"], errors)
    write_csv(output_paths["target_group_table"], all_group_rows)
    write_csv(output_paths["shortcut_audit"], all_probe_summaries)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    geom = counts["targets"][GEOMETRY_TARGET_NAME]
    rel = counts["targets"][RELIABILITY_TARGET_NAME]
    print(
        f"status={summary['status']} labels={counts['validated_label_rows']} "
        f"geom_binary={geom['rows']} geom_pos={geom['positive']} geom_neg={geom['negative']} "
        f"rel_binary={rel['rows']} rel_pos={rel['positive']} rel_neg={rel['negative']} "
        f"errors={counts['errors']} validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
