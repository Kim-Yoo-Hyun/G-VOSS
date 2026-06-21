#!/usr/bin/env python3
"""Ingest endpoint-controlled labels after label lock."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_label_ingestion as probe_base


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
FILL_DIR = RGA_ROOT / "endpoint_controlled_label_fill_codex_proxy_user_requested"
ASSET_DIR = RGA_ROOT / "endpoint_controlled_asset_packets"
DEFAULT_COMPLETED_SHEET = FILL_DIR / "completed_endpoint_controlled_label_sheet_codex_proxy_user_requested.tsv"
DEFAULT_FILL_SUMMARY = FILL_DIR / "summary.json"
DEFAULT_SCHEMA = FILL_DIR / "endpoint_controlled_fill_schema.json"
DEFAULT_INTERNAL_MANIFEST = ASSET_DIR / "endpoint_controlled_full_manifest_post_label_only.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "endpoint_controlled_label_ingestion_codex_proxy_user_requested"

LABEL_SOURCE = "codex_proxy_endpoint_controlled_user_requested"
GEOMETRY_TARGET_NAME = "geometry_validity_endpoint_controlled_target"
RELIABILITY_TARGET_NAME = "relation_reliability_endpoint_controlled_target"
SELECTED_FAMILIES = {"support_contact", "relative_vertical"}
MIN_POSITIVES_FOR_POSTERIOR_SMOKE = 10

REVIEW_AXIS_KEYS = [
    "endpoint_identity_external",
    "visual_pair_evaluability_external",
    "mesh_pair_evaluability_external",
    "visual_geometry_answer_external",
    "mesh_geometry_answer_external",
    "relation_informativeness_external",
    "final_relation_reliability_external",
    "uncertainty_reason_external",
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
    "endpoint_flag_pattern_hidden",
    "expected_label_proxy_hidden",
    "needed_label_proxy_hidden",
    "selected_source_hidden",
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
    probe_base.write_csv(path, rows)


def validate_headers(fieldnames: list[str], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for field in ["blind_review_id", *schema["completion_fields"]]:
        if field not in fieldnames:
            errors.append({"error_type": "missing_required_header", "field": field})
    return errors


def validate_id_sets(completed_rows: list[dict[str, str]], internal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    completed_ids = [str(row.get("blind_review_id") or "") for row in completed_rows]
    internal_ids = [str(row.get("blind_review_id") or "") for row in internal_rows]
    for blind_id, count in Counter(completed_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_completed_blind_review_id", "blind_review_id": blind_id, "count": count})
    completed_set = {blind_id for blind_id in completed_ids if blind_id}
    internal_set = {blind_id for blind_id in internal_ids if blind_id}
    for blind_id in sorted(completed_set - internal_set):
        errors.append({"error_type": "completed_id_missing_from_internal_manifest", "blind_review_id": blind_id})
    for blind_id in sorted(internal_set - completed_set):
        errors.append({"error_type": "internal_manifest_id_missing_from_completed_sheet", "blind_review_id": blind_id})
    return errors


def validate_fill_summary(fill_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    boundary = fill_summary.get("boundary", {})
    expected_false = [
        "actual_user_reviewer",
        "paper_evidence_allowed_before_user_confirmation",
        "used_hidden_manifest",
        "used_endpoint_flag_pattern",
        "used_needed_label_proxy",
        "used_numeric_witness_values",
        "used_previous_proxy_labels",
        "used_source_score_or_rank",
        "used_p_geom_valid",
        "used_geometry_status",
        "validation_usage",
        "test_usage",
        "multi_view_as_model_input",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_summary_boundary_mismatch", "field": key, "expected": False, "value": boundary.get(key)})
    if boundary.get("filled_by") != "codex_proxy":
        errors.append({"error_type": "fill_summary_boundary_mismatch", "field": "filled_by", "expected": "codex_proxy", "value": boundary.get("filled_by")})
    if boundary.get("split_policy") != "train_only":
        errors.append({"error_type": "fill_summary_boundary_mismatch", "field": "split_policy", "expected": "train_only", "value": boundary.get("split_policy")})
    return errors


def validate_row(row: dict[str, str], row_number: int, schema: dict[str, Any], internal: dict[str, Any] | None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = schema["allowed_review_values"]
    blind_id = str(row.get("blind_review_id") or "")
    for field in schema["completion_fields"]:
        value = str(row.get(field) or "")
        if not value:
            errors.append({"error_type": "missing_required_field", "row_number": row_number, "blind_review_id": blind_id, "field": field})
            continue
        if field in allowed and value not in set(allowed[field]):
            errors.append({"error_type": "invalid_value", "row_number": row_number, "blind_review_id": blind_id, "field": field, "value": value})
    if row.get("predicate_family") not in SELECTED_FAMILIES:
        errors.append({"error_type": "row_outside_selected_scope", "row_number": row_number, "blind_review_id": blind_id, "predicate_family": row.get("predicate_family")})
    if internal is not None:
        identity_pairs = {
            "scan_id": "scan_id",
            "scene_context_id": "subgraph_id",
            "predicate_family": "predicate_family",
            "predicate_label": "predicate_label",
            "subject_id": "subject_id",
            "object_id": "object_id",
        }
        for completed_key, internal_key in identity_pairs.items():
            if str(row.get(completed_key) or "") != str(internal.get(internal_key) or ""):
                errors.append(
                    {
                        "error_type": "completed_internal_identity_mismatch",
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": completed_key,
                        "completed_value": row.get(completed_key),
                        "internal_value": internal.get(internal_key),
                    }
                )
    return errors


def base_identity(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "prediction_id": internal.get("prediction_id") or row["blind_review_id"],
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("scene_context_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "evidence_packet_status": row.get("evidence_packet_status"),
    }


def review_fields(row: dict[str, str]) -> dict[str, Any]:
    fields = {
        "external_reviewer_id": row.get("external_reviewer_id"),
        "external_review_round": row.get("external_review_round"),
        "external_label_notes": row.get("external_label_notes"),
        "not_model_input": True,
    }
    for key in REVIEW_AXIS_KEYS:
        fields[key] = row.get(key)
    return fields


def hidden_metadata(internal: dict[str, Any]) -> dict[str, Any]:
    hidden = internal.get("hidden_sampling_axes_post_label_only", {})
    output = {key: hidden.get(key) for key in HIDDEN_GROUP_KEYS}
    output["forbidden_as_labeler_visible"] = internal.get("forbidden_as_labeler_visible", [])
    output["asset_packet_source"] = internal.get("asset_packet_source")
    output["batch_name"] = internal.get("batch_name")
    return output


def deployable_evidence(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    paths = internal.get("packet_paths", {})
    return {
        "source_semantic_and_geometry_scores_hidden_from_labeler_until_lock": {
            "available_in_this_ingestion": False,
            "reason": "Source semantic score/rank, p_geom_valid, endpoint flags, and geometry status are intentionally not joined before target-independence audit.",
        },
        "coverage_evidence": {"evidence_packet_status": row.get("evidence_packet_status")},
        "audit_packet_paths_not_model_input": {
            "multiview_packet": paths.get("multiview_packet") or row.get("multiview_packet"),
            "pointcloud_or_mesh_packet": paths.get("pointcloud_or_mesh_packet") or row.get("pointcloud_or_mesh_packet"),
            "contact_or_context_sheet": paths.get("contact_or_context_sheet") or row.get("contact_or_context_sheet"),
        },
        "forbidden_as_posterior_input": {
            "endpoint_controlled_review_fields": True,
            "hidden_strata": True,
            "audit_packet_paths": True,
            "multi_view_as_model_input": True,
        },
    }


def derive_geometry_target(row: dict[str, str]) -> dict[str, Any]:
    endpoint = row["endpoint_identity_external"]
    visual = row["visual_geometry_answer_external"]
    mesh = row["mesh_geometry_answer_external"]
    uncertainty = row["uncertainty_reason_external"]
    answers = {visual, mesh}
    if endpoint != "both_valid":
        return {"target_name": GEOMETRY_TARGET_NAME, "target_use": "exclude", "target_y": None, "reason": f"exclude_endpoint={endpoint}"}
    if "contradicts_predicate" in answers and "supports_predicate" not in answers:
        return {"target_name": GEOMETRY_TARGET_NAME, "target_use": "negative", "target_y": 0, "reason": "endpoint_controlled_geometry_contradicts_predicate"}
    if "supports_predicate" in answers and "contradicts_predicate" not in answers:
        return {"target_name": GEOMETRY_TARGET_NAME, "target_use": "positive", "target_y": 1, "reason": "endpoint_controlled_geometry_supports_predicate"}
    if "supports_predicate" in answers and "contradicts_predicate" in answers:
        return {"target_name": GEOMETRY_TARGET_NAME, "target_use": "exclude", "target_y": None, "reason": "exclude_visual_mesh_disagree"}
    return {"target_name": GEOMETRY_TARGET_NAME, "target_use": "exclude", "target_y": None, "reason": f"exclude_endpoint_controlled_geometry_uncertain={uncertainty}"}


def derive_reliability_target(row: dict[str, str], geometry_target: dict[str, Any]) -> dict[str, Any]:
    endpoint = row["endpoint_identity_external"]
    informativeness = row["relation_informativeness_external"]
    final = row["final_relation_reliability_external"]
    uncertainty = row["uncertainty_reason_external"]
    if final == "uncertain":
        return {"target_name": RELIABILITY_TARGET_NAME, "target_use": "exclude", "target_y": None, "reason": f"exclude_endpoint_controlled_reliability_uncertain={uncertainty}"}
    if endpoint != "both_valid":
        return {"target_name": RELIABILITY_TARGET_NAME, "target_use": "negative", "target_y": 0, "reason": f"endpoint_controlled_endpoint_invalid={endpoint}"}
    if final == "reliable" and geometry_target["target_y"] == 1 and informativeness == "informative":
        return {"target_name": RELIABILITY_TARGET_NAME, "target_use": "positive", "target_y": 1, "reason": "endpoint_controlled_relation_reliable"}
    if final == "unreliable":
        return {"target_name": RELIABILITY_TARGET_NAME, "target_use": "negative", "target_y": 0, "reason": "endpoint_controlled_relation_unreliable"}
    if geometry_target["target_y"] == 0:
        return {"target_name": RELIABILITY_TARGET_NAME, "target_use": "negative", "target_y": 0, "reason": "endpoint_controlled_geometry_contradicts_predicate"}
    if informativeness in {"trivial_dense_or_room_structure", "ontology_mismatch"}:
        return {"target_name": RELIABILITY_TARGET_NAME, "target_use": "negative", "target_y": 0, "reason": f"endpoint_controlled_informativeness={informativeness}"}
    return {"target_name": RELIABILITY_TARGET_NAME, "target_use": "exclude", "target_y": None, "reason": "exclude_endpoint_controlled_reliability_ambiguous_contract"}


def make_label(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    geometry_target = derive_geometry_target(row)
    reliability_target = derive_reliability_target(row, geometry_target)
    return {
        "schema_version": "h002_endpoint_controlled_ingested_label_v1",
        **base_identity(row, internal),
        "label_source": LABEL_SOURCE,
        "filled_by": "codex_proxy",
        "actual_user_reviewer": False,
        "user_requested_proxy_review": True,
        "paper_evidence_allowed_before_user_confirmation": False,
        "hidden_manifest_joined_after_label_lock": True,
        "endpoint_controlled_review_fields_are_target_only": True,
        "endpoint_controlled_review_fields": review_fields(row),
        "geometry_validity_endpoint_controlled_target": geometry_target,
        "relation_reliability_endpoint_controlled_target": reliability_target,
        "deployable_evidence_after_label_lock": deployable_evidence(row, internal),
        "hidden_audit_metadata_post_label_only": hidden_metadata(internal),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "actual_user_reviewer": False,
            "multi_view_as_model_input": False,
        },
    }


def ingest(completed_rows: list[dict[str, str]], internal_rows: list[dict[str, Any]], schema: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    internal_by_id = {str(row["blind_review_id"]): row for row in internal_rows}
    labels: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(completed_rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        internal = internal_by_id.get(blind_id)
        row_errors = validate_row(row, row_number, schema, internal)
        if internal is None:
            row_errors.append({"error_type": "missing_internal_manifest_for_completed_row", "row_number": row_number, "blind_review_id": blind_id})
        if row_errors:
            errors.extend(row_errors)
            continue
        labels.append(make_label(row, internal_by_id[blind_id]))
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
        "actual_user_reviewer": False,
        "user_requested_proxy_review": True,
        "paper_locked": False,
        "queue_kind_hidden": hidden.get("queue_kind_hidden"),
        "proposed_audit_role_hidden": hidden.get("proposed_audit_role_hidden"),
        "label_match_status_hidden": hidden.get("label_match_status_hidden"),
        "geometry_status_hidden": hidden.get("geometry_status_hidden"),
        "rank_band_hidden": hidden.get("rank_band_hidden"),
        "relation_validity_label_hidden": hidden.get("relation_validity_label_hidden"),
        "label_use_hidden": hidden.get("label_use_hidden"),
        "posterior_target_y_hidden": hidden.get("posterior_target_y_hidden"),
        "endpoint_flag_pattern_hidden": hidden.get("endpoint_flag_pattern_hidden"),
        "expected_label_proxy_hidden": hidden.get("expected_label_proxy_hidden"),
        "needed_label_proxy_hidden": hidden.get("needed_label_proxy_hidden"),
        "selected_source_hidden": hidden.get("selected_source_hidden"),
    }


def posterior_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    row = target_row(label, target_key, schema_version)
    if row is None:
        return None
    return {
        **row,
        "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
        "audit_only_endpoint_controlled_review_fields": label["endpoint_controlled_review_fields"],
        "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
        "audit_note": "Use only deployable evidence after target gate. Endpoint-controlled review fields are target/audit only.",
    }


def excluded_row(label: dict[str, Any], target_key: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is not None:
        return None
    return {
        "schema_version": "h002_endpoint_controlled_excluded_target_v1",
        "target_name": target["target_name"],
        "target_use": target["target_use"],
        "target_y": None,
        "target_reason": target["reason"],
        "blind_review_id": label["blind_review_id"],
        "scan_id": label["scan_id"],
        "predicate_label": label["predicate_label"],
        "predicate_family": label["predicate_family"],
        "subject_label": label["subject_label"],
        "object_label": label["object_label"],
        "audit_only_endpoint_controlled_review_fields": label["endpoint_controlled_review_fields"],
    }


def count_target(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["target_y"] for row in rows)
    total = len(rows)
    return {
        "rows": total,
        "positive": counts[1],
        "negative": counts[0],
        "positive_rate": (counts[1] / total) if total else 0.0,
        "by_family": probe_base.nested_target_counts(rows, "predicate_family"),
        "by_predicate": probe_base.nested_target_counts(rows, "predicate_label"),
    }


def axis_counts(labels: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for axis in REVIEW_AXIS_KEYS:
        output[axis] = dict(sorted(Counter(row["endpoint_controlled_review_fields"].get(axis) for row in labels).items()))
    return output


def positive_sparse(target_counts: dict[str, Any]) -> bool:
    return target_counts["positive"] < MIN_POSITIVES_FOR_POSTERIOR_SMOKE


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Endpoint-Controlled Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Labels are Codex-proxy review fields, not paper-level external human annotations.",
        "- Review fields and hidden endpoint metadata are target/audit only, not posterior inputs.",
        "- Hidden manifest is joined only after label lock.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
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
    lines.extend(
        [
            "",
            "## Probe",
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


def run(args: argparse.Namespace) -> dict[str, Any]:
    completed_sheet = as_abs(args.completed_sheet)
    fill_summary_path = as_abs(args.fill_summary)
    schema_path = as_abs(args.schema)
    internal_manifest_path = as_abs(args.internal_manifest)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fieldnames, completed_rows = read_tsv(completed_sheet)
    fill_summary = read_json(fill_summary_path)
    schema = read_json(schema_path)
    internal_rows = read_jsonl(internal_manifest_path)

    errors: list[dict[str, Any]] = []
    errors.extend(validate_headers(fieldnames, schema))
    errors.extend(validate_id_sets(completed_rows, internal_rows))
    errors.extend(validate_fill_summary(fill_summary))
    labels, row_errors = ingest(completed_rows, internal_rows, schema)
    errors.extend(row_errors)

    geometry_targets = [
        row
        for row in (
            target_row(label, "geometry_validity_endpoint_controlled_target", "h002_endpoint_controlled_geometry_validity_target_v1")
            for label in labels
        )
        if row is not None
    ]
    reliability_targets = [
        row
        for row in (
            target_row(label, "relation_reliability_endpoint_controlled_target", "h002_endpoint_controlled_relation_reliability_target_v1")
            for label in labels
        )
        if row is not None
    ]
    geometry_posterior = [
        row
        for row in (
            posterior_row(label, "geometry_validity_endpoint_controlled_target", "h002_endpoint_controlled_geometry_validity_posterior_row_v1")
            for label in labels
        )
        if row is not None
    ]
    reliability_posterior = [
        row
        for row in (
            posterior_row(label, "relation_reliability_endpoint_controlled_target", "h002_endpoint_controlled_relation_reliability_posterior_row_v1")
            for label in labels
        )
        if row is not None
    ]
    excluded = [
        row
        for label in labels
        for row in (
            excluded_row(label, "geometry_validity_endpoint_controlled_target"),
            excluded_row(label, "relation_reliability_endpoint_controlled_target"),
        )
        if row is not None
    ]

    probes = {
        GEOMETRY_TARGET_NAME: probe_base.target_independence_probe(geometry_posterior, GEOMETRY_TARGET_NAME),
        RELIABILITY_TARGET_NAME: probe_base.target_independence_probe(reliability_posterior, RELIABILITY_TARGET_NAME),
    }
    all_group_rows = [row for probe in probes.values() for row in probe["group_table"]]
    all_probe_summaries = [row for probe in probes.values() for row in probe["summaries"]]
    excluded_counts = Counter(row["target_name"] for row in excluded)
    geometry_count = count_target(geometry_targets)
    reliability_count = count_target(reliability_targets)
    sparse_flags = {
        GEOMETRY_TARGET_NAME: positive_sparse(geometry_count),
        RELIABILITY_TARGET_NAME: positive_sparse(reliability_count),
    }

    if errors:
        status = "h002_endpoint_controlled_label_ingestion_errors"
        decision = "Fix endpoint-controlled label ingestion errors before target audit."
        next_todo = "fix_endpoint_controlled_label_ingestion_errors"
    elif sparse_flags[RELIABILITY_TARGET_NAME]:
        status = "h002_endpoint_controlled_label_ingested_positive_sparse"
        decision = (
            "Endpoint-controlled labels are ingested, but relation reliability has too few positives "
            "for posterior smoke. Run target-independence audit as failure diagnosis, not method evidence."
        )
        next_todo = "endpoint_controlled_target_independence_audit"
    elif any(probe["status"] != "target_independence_probe_pass" for probe in probes.values()):
        status = "h002_endpoint_controlled_label_ingested_with_basic_probe_risk"
        decision = "Endpoint-controlled labels are materialized, but basic probe detects shortcut risk."
        next_todo = "endpoint_controlled_target_independence_audit"
    else:
        status = "h002_endpoint_controlled_label_ingested_ready_for_target_audit"
        decision = "Endpoint-controlled labels are materialized. Run dedicated target-independence audit before posterior smoke."
        next_todo = "endpoint_controlled_target_independence_audit"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validated_labels": output_dir / "validated_endpoint_controlled_labels.jsonl",
        "geometry_validity_targets": output_dir / "geometry_validity_endpoint_controlled_targets.jsonl",
        "relation_reliability_targets": output_dir / "relation_reliability_endpoint_controlled_targets.jsonl",
        "geometry_validity_posterior_rows": output_dir / "geometry_validity_endpoint_controlled_posterior_rows.jsonl",
        "relation_reliability_posterior_rows": output_dir / "relation_reliability_endpoint_controlled_posterior_rows.jsonl",
        "excluded_targets": output_dir / "excluded_endpoint_controlled_targets.jsonl",
        "target_independence_probe": output_dir / "target_independence_probe.json",
        "target_group_table": output_dir / "target_group_table.csv",
        "shortcut_audit": output_dir / "shortcut_audit.csv",
        "ingestion_errors": output_dir / "ingestion_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_endpoint_controlled_label_ingestion_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "input_paths": {
            "completed_sheet": rel_path(completed_sheet),
            "fill_summary": rel_path(fill_summary_path),
            "endpoint_controlled_fill_schema": rel_path(schema_path),
            "internal_manifest_post_label_only": rel_path(internal_manifest_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split_policy": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "posterior_trained": False,
            "label_source": LABEL_SOURCE,
            "filled_by": "codex_proxy",
            "actual_user_reviewer": False,
            "paper_evidence_allowed_before_user_confirmation": False,
            "hidden_metadata_as_model_input": False,
            "endpoint_controlled_review_fields_as_model_input": False,
            "source_score_feature_join_pending": True,
            "multi_view_as_model_input": False,
            "posterior_smoke_allowed": False,
        },
        "counts": {
            "completed_sheet_rows": len(completed_rows),
            "internal_manifest_rows": len(internal_rows),
            "validated_label_rows": len(labels),
            "errors": len(errors),
            "targets": {
                GEOMETRY_TARGET_NAME: geometry_count,
                RELIABILITY_TARGET_NAME: reliability_count,
            },
            "excluded_targets": {
                GEOMETRY_TARGET_NAME: excluded_counts[GEOMETRY_TARGET_NAME],
                RELIABILITY_TARGET_NAME: excluded_counts[RELIABILITY_TARGET_NAME],
            },
            "positive_sparse_flags": sparse_flags,
            "min_positives_for_posterior_smoke": MIN_POSITIVES_FOR_POSTERIOR_SMOKE,
        },
        "axis_counts": axis_counts(labels),
        "target_independence_probes": {
            target_name: {key: value for key, value in probe.items() if key != "group_table"}
            for target_name, probe in probes.items()
        },
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["target_independence_probe"], probes)
    write_jsonl(output_paths["validated_labels"], labels)
    write_jsonl(output_paths["geometry_validity_targets"], geometry_targets)
    write_jsonl(output_paths["relation_reliability_targets"], reliability_targets)
    write_jsonl(output_paths["geometry_validity_posterior_rows"], geometry_posterior)
    write_jsonl(output_paths["relation_reliability_posterior_rows"], reliability_posterior)
    write_jsonl(output_paths["excluded_targets"], excluded)
    write_jsonl(output_paths["ingestion_errors"], errors)
    write_csv(output_paths["target_group_table"], all_group_rows)
    write_csv(output_paths["shortcut_audit"], all_probe_summaries)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    rel = counts["targets"][RELIABILITY_TARGET_NAME]
    geom = counts["targets"][GEOMETRY_TARGET_NAME]
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
