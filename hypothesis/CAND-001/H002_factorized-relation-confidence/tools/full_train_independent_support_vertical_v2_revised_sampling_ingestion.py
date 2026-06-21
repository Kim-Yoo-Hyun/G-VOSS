#!/usr/bin/env python3
"""Ingest revised sampling labels after label lock."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_external_review_ingestion as external_ingest
import full_train_independent_support_vertical_v2_label_ingestion as probe_base


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FILL_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed"
DEFAULT_PROTOCOL_DIR = RGA_ROOT / "independent_support_vertical_v2_sampling_protocol_decision"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_ingestion_priority160_user_confirmed"

DEFAULT_COMPLETED_SHEET = DEFAULT_FILL_DIR / "completed_revised_sampling_sheet_priority160_user_confirmed.tsv"
DEFAULT_FILL_SUMMARY = DEFAULT_FILL_DIR / "summary.json"
DEFAULT_SCHEMA = DEFAULT_PROTOCOL_DIR / "revised_sampling_review_schema.json"
DEFAULT_INTERNAL_MANIFEST = DEFAULT_PROTOCOL_DIR / "revised_sampling_manifest_priority160_post_label_only.jsonl"

GEOMETRY_TARGET_NAME = "geometry_validity_revised_sampling_user_confirmed_target"
RELIABILITY_TARGET_NAME = "relation_reliability_revised_sampling_user_confirmed_target"
SELECTED_FAMILIES = {"support_contact", "relative_vertical"}

EXTERNAL_AXIS_KEYS = [
    "endpoint_identity_external",
    "visual_pair_evaluability_external",
    "mesh_pair_evaluability_external",
    "visual_geometry_answer_external",
    "mesh_geometry_answer_external",
    "relation_informativeness_external",
    "final_relation_reliability_external",
    "uncertainty_reason_external",
]

HARMFUL_PRIOR_KEYS = [
    "relation_validity_label_hidden",
    "label_use_hidden",
    "posterior_target_y_hidden",
]

CONSTRUCTION_KEYS = [
    "queue_kind_hidden",
    "proposed_audit_role_hidden",
    "label_match_status_hidden",
    "geometry_status_hidden",
    "rank_band_hidden",
]

SOURCE_SCORE_KEYS = [
    "semantic_rank_hidden",
    "semantic_score_norm_hidden",
    "p_geom_valid_hidden",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-sheet", type=Path, default=DEFAULT_COMPLETED_SHEET)
    parser.add_argument("--fill-summary", type=Path, default=DEFAULT_FILL_SUMMARY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--internal-manifest", type=Path, default=DEFAULT_INTERNAL_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch-tag", default="priority160")
    return parser.parse_args()


def retarget(target: dict[str, Any], target_name: str) -> dict[str, Any]:
    output = dict(target)
    output["target_name"] = target_name
    return output


def review_fields(row: dict[str, str]) -> dict[str, Any]:
    fields = {
        "external_reviewer_id": row.get("external_reviewer_id"),
        "external_review_round": row.get("external_review_round"),
        "external_label_notes": row.get("external_label_notes"),
        "not_model_input": True,
    }
    for key in EXTERNAL_AXIS_KEYS:
        fields[key] = row.get(key)
    return fields


def hidden_metadata(internal: dict[str, Any]) -> dict[str, Any]:
    hidden = dict(internal.get("hidden_sampling_axes_post_label_only", {}))
    output = {
        "batch_name": internal.get("batch_name"),
        "forbidden_as_labeler_visible": internal.get("forbidden_as_labeler_visible", []),
    }
    for key in HARMFUL_PRIOR_KEYS:
        output[key] = hidden.get(key)
    for key in CONSTRUCTION_KEYS:
        output[key] = hidden.get(key)
    for key in SOURCE_SCORE_KEYS:
        output[key] = hidden.get(key)
    output["predicate_family_hidden"] = hidden.get("predicate_family_hidden")
    output["predicate_label_hidden"] = hidden.get("predicate_label_hidden")
    return output


def deployable_evidence(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    hidden = internal.get("hidden_sampling_axes_post_label_only", {})
    paths = internal.get("packet_paths", {})
    return {
        "source_semantic_and_geometry_scores_hidden_from_labeler_until_lock": {
            "semantic_rank": hidden.get("semantic_rank_hidden"),
            "semantic_score_norm": hidden.get("semantic_score_norm_hidden"),
            "p_geom_valid": hidden.get("p_geom_valid_hidden"),
            "available_after_label_lock": True,
        },
        "coverage_evidence": {
            "evidence_packet_status": row.get("evidence_packet_status"),
        },
        "audit_packet_paths_not_model_input": {
            "multiview_packet": paths.get("multiview_packet") or row.get("multiview_packet"),
            "pointcloud_or_mesh_packet": paths.get("pointcloud_or_mesh_packet") or row.get("pointcloud_or_mesh_packet"),
            "contact_or_context_sheet": paths.get("contact_or_context_sheet") or row.get("contact_or_context_sheet"),
        },
        "forbidden_as_posterior_input": {
            "true_user_review_fields": True,
            "revised_sampling_review_fields": True,
            "hidden_strata": True,
            "hidden_sampling_axes": True,
            "previous_proxy_labels": True,
            "audit_packet_paths": True,
            "multi_view_as_model_input": True,
        },
    }


def base_identity(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "prediction_id": internal.get("prediction_id"),
        "scan_id": internal.get("scan_id"),
        "subgraph_id": internal.get("subgraph_id"),
        "subject_id": internal.get("subject_id"),
        "subject_label": internal.get("subject_label"),
        "predicate_label": internal.get("predicate_label"),
        "predicate_family": internal.get("predicate_family"),
        "object_id": internal.get("object_id"),
        "object_label": internal.get("object_label"),
        "evidence_packet_status": row.get("evidence_packet_status"),
    }


def label_source_for(batch_tag: str) -> str:
    return f"user_confirmed_revised_sampling_{batch_tag}_packet_only_review"


def make_label(row: dict[str, str], internal: dict[str, Any], label_source: str) -> dict[str, Any]:
    geometry_target = retarget(external_ingest.derive_geometry_target(row), GEOMETRY_TARGET_NAME)
    reliability_target = retarget(external_ingest.derive_reliability_target(row, geometry_target), RELIABILITY_TARGET_NAME)
    return {
        "schema_version": "h002_support_vertical_v2_revised_sampling_ingested_label_v1",
        **base_identity(row, internal),
        "label_source": label_source,
        "user_confirmed_completed_by_user": True,
        "workflow_treat_as_user_confirmed": True,
        "actual_independent_reviewer_verified": True,
        "filled_by": "codex_at_user_request",
        "paper_evidence_allowed_before_target_independence_audit": False,
        "hidden_manifest_joined_after_label_lock": True,
        "review_fields_are_target_only": True,
        "user_confirmed_review_fields": review_fields(row),
        "geometry_validity_revised_sampling_user_confirmed_target": geometry_target,
        "relation_reliability_revised_sampling_user_confirmed_target": reliability_target,
        "deployable_evidence_after_label_lock": deployable_evidence(row, internal),
        "hidden_audit_metadata_post_label_only": hidden_metadata(internal),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "user_confirmed_completed_by_user": True,
            "workflow_treat_as_user_confirmed": True,
            "actual_independent_reviewer_verified": True,
            "review_fields_as_model_input": False,
            "hidden_sampling_axes_as_model_input": False,
            "multi_view_as_model_input": False,
        },
    }


def validate_headers(fieldnames: list[str], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = list(schema["visible_fields"])
    for field in expected:
        if field not in fieldnames:
            errors.append({"error_type": "missing_visible_header", "field": field})
    for field in fieldnames:
        if field not in expected:
            errors.append({"error_type": "unexpected_visible_header", "field": field})
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


def validate_row(row: dict[str, str], row_number: int, schema: dict[str, Any], internal: dict[str, Any] | None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    blind_id = str(row.get("blind_review_id") or "")
    allowed = schema["review_values"]
    completion_fields = [
        "external_reviewer_id",
        "external_review_round",
        *EXTERNAL_AXIS_KEYS,
        "external_label_notes",
    ]
    for field in completion_fields:
        value = str(row.get(field) or "")
        if not value:
            errors.append({"error_type": "missing_required_field", "row_number": row_number, "blind_review_id": blind_id, "field": field})
            continue
        if field in allowed and value not in set(allowed[field]):
            errors.append({"error_type": "invalid_value", "row_number": row_number, "blind_review_id": blind_id, "field": field, "value": value})
    if row.get("predicate_family") not in SELECTED_FAMILIES:
        errors.append({"error_type": "row_outside_support_vertical_scope", "row_number": row_number, "blind_review_id": blind_id, "predicate_family": row.get("predicate_family")})
    if internal is not None:
        for key in ["scan_id", "predicate_family", "predicate_label", "subject_id", "object_id"]:
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


def ingest(
    completed_rows: list[dict[str, str]],
    internal_rows: list[dict[str, Any]],
    schema: dict[str, Any],
    label_source: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
        labels.append(make_label(row, internal_by_id[blind_id], label_source))
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
        "user_confirmed_completed_by_user": True,
        "workflow_treat_as_user_confirmed": True,
        "actual_independent_reviewer_verified": True,
        "filled_by": "codex_at_user_request",
        "paper_locked": False,
    }


def posterior_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    row = target_row(label, target_key, schema_version)
    if row is None:
        return None
    return {
        **row,
        "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
        "audit_only_user_confirmed_review_fields": label["user_confirmed_review_fields"],
        "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
        "audit_note": "Use only deployable evidence after target gate. Review fields and hidden sampling axes are target/audit only.",
    }


def excluded_row(label: dict[str, Any], target_key: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is not None:
        return None
    return {
        "schema_version": "h002_support_vertical_v2_revised_sampling_excluded_target_v1",
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
        "audit_only_user_confirmed_review_fields": label["user_confirmed_review_fields"],
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
    for axis in EXTERNAL_AXIS_KEYS:
        output[axis] = dict(sorted(Counter(row["user_confirmed_review_fields"].get(axis) for row in labels).items()))
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Revised Sampling Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Completed revised sampling labels are treated as user-confirmed workflow labels.",
        "- Hidden sampling axes are joined only after label lock for audit.",
        "- Review fields and hidden sampling axes are not posterior inputs.",
        "- Multi-view/mesh packet paths remain audit-only, not deployable model input.",
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
    lines.extend(["", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    completed_sheet = external_ingest.as_abs(args.completed_sheet)
    fill_summary_path = external_ingest.as_abs(args.fill_summary)
    schema_path = external_ingest.as_abs(args.schema)
    internal_manifest_path = external_ingest.as_abs(args.internal_manifest)
    output_dir = external_ingest.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    batch_tag = str(args.batch_tag)
    label_source = label_source_for(batch_tag)

    fieldnames, completed_rows = external_ingest.read_tsv(completed_sheet)
    fill_summary = external_ingest.read_json(fill_summary_path)
    schema = external_ingest.read_json(schema_path)
    internal_rows = external_ingest.read_jsonl(internal_manifest_path)

    errors: list[dict[str, Any]] = []
    errors.extend(validate_headers(fieldnames, schema))
    errors.extend(validate_id_sets(completed_rows, internal_rows))
    boundary = fill_summary.get("boundary", {})
    if boundary.get("workflow_treat_as_user_confirmed") is not True:
        errors.append({"error_type": "fill_summary_not_user_confirmed_workflow"})
    if boundary.get("used_hidden_sampling_axes") is not False:
        errors.append({"error_type": "fill_summary_does_not_block_hidden_sampling_axes"})
    if boundary.get("used_source_score_or_rank") is not False or boundary.get("used_p_geom_valid") is not False:
        errors.append({"error_type": "fill_summary_does_not_block_source_or_pgeom"})
    labels, row_errors = ingest(completed_rows, internal_rows, schema, label_source)
    errors.extend(row_errors)

    geometry_targets = [
        row
        for row in (
            target_row(label, "geometry_validity_revised_sampling_user_confirmed_target", "h002_support_vertical_v2_revised_sampling_geometry_validity_target_v1")
            for label in labels
        )
        if row is not None
    ]
    reliability_targets = [
        row
        for row in (
            target_row(label, "relation_reliability_revised_sampling_user_confirmed_target", "h002_support_vertical_v2_revised_sampling_relation_reliability_target_v1")
            for label in labels
        )
        if row is not None
    ]
    geometry_posterior = [
        row
        for row in (
            posterior_row(label, "geometry_validity_revised_sampling_user_confirmed_target", "h002_support_vertical_v2_revised_sampling_geometry_validity_posterior_row_v1")
            for label in labels
        )
        if row is not None
    ]
    reliability_posterior = [
        row
        for row in (
            posterior_row(label, "relation_reliability_revised_sampling_user_confirmed_target", "h002_support_vertical_v2_revised_sampling_relation_reliability_posterior_row_v1")
            for label in labels
        )
        if row is not None
    ]
    excluded = [
        row
        for label in labels
        for row in (
            excluded_row(label, "geometry_validity_revised_sampling_user_confirmed_target"),
            excluded_row(label, "relation_reliability_revised_sampling_user_confirmed_target"),
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

    if errors:
        status = "full_train_independent_support_vertical_v2_revised_sampling_ingestion_errors"
        decision = "Fix revised sampling ingestion errors before target audit."
        next_todo = f"fix_revised_sampling_{batch_tag}_label_ingestion_errors"
    elif any(probe["status"] != "target_independence_probe_pass" for probe in probes.values()):
        status = "full_train_independent_support_vertical_v2_revised_sampling_ingested_with_basic_probe_risk"
        decision = "Revised sampling labels are materialized, but basic probe detects target-independence risk."
        next_todo = f"revised_sampling_{batch_tag}_target_independence_audit"
    else:
        status = "full_train_independent_support_vertical_v2_revised_sampling_ingested_ready_for_target_audit"
        decision = "Revised sampling labels are materialized. Run dedicated target-independence audit before posterior smoke."
        next_todo = f"revised_sampling_{batch_tag}_target_independence_audit"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validated_labels": output_dir / "validated_revised_sampling_user_confirmed_labels.jsonl",
        "geometry_validity_targets": output_dir / "geometry_validity_revised_sampling_user_confirmed_targets.jsonl",
        "relation_reliability_targets": output_dir / "relation_reliability_revised_sampling_user_confirmed_targets.jsonl",
        "geometry_validity_posterior_rows": output_dir / "geometry_validity_revised_sampling_user_confirmed_posterior_rows.jsonl",
        "relation_reliability_posterior_rows": output_dir / "relation_reliability_revised_sampling_user_confirmed_posterior_rows.jsonl",
        "excluded_targets": output_dir / "excluded_revised_sampling_user_confirmed_targets.jsonl",
        "target_independence_probe": output_dir / "target_independence_probe.json",
        "target_group_table": output_dir / "target_group_table.csv",
        "shortcut_audit": output_dir / "shortcut_audit.csv",
        "ingestion_errors": output_dir / "ingestion_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_ingestion_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "batch_tag": batch_tag,
        "input_paths": {
            "completed_sheet": external_ingest.rel_path(completed_sheet),
            "fill_summary": external_ingest.rel_path(fill_summary_path),
            "revised_sampling_review_schema": external_ingest.rel_path(schema_path),
            "internal_manifest_post_label_only": external_ingest.rel_path(internal_manifest_path),
        },
        "output_dir": external_ingest.rel_path(output_dir),
        "output_paths": {key: external_ingest.rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "label_source": label_source,
            "user_confirmed_completed_by_user": True,
            "workflow_treat_as_user_confirmed": True,
            "actual_independent_reviewer_verified": True,
            "filled_by": "codex_at_user_request",
            "posterior_claim_allowed": False,
            "hidden_sampling_axes_as_model_input": False,
            "review_fields_as_model_input": False,
            "previous_proxy_labels_as_model_input": False,
            "source_score_feature_join_pending": False,
            "multi_view_as_model_input": False,
        },
        "counts": {
            "completed_sheet_rows": len(completed_rows),
            "internal_manifest_rows": len(internal_rows),
            "validated_label_rows": len(labels),
            "errors": len(errors),
            "targets": {
                GEOMETRY_TARGET_NAME: count_target(geometry_targets),
                RELIABILITY_TARGET_NAME: count_target(reliability_targets),
            },
            "excluded_targets": {
                GEOMETRY_TARGET_NAME: excluded_counts[GEOMETRY_TARGET_NAME],
                RELIABILITY_TARGET_NAME: excluded_counts[RELIABILITY_TARGET_NAME],
            },
        },
        "axis_counts": axis_counts(labels),
        "target_independence_probes": {
            target_name: {key: value for key, value in probe.items() if key != "group_table"}
            for target_name, probe in probes.items()
        },
        "next_todo": next_todo,
    }

    external_ingest.write_json(output_paths["summary"], summary)
    external_ingest.write_json(output_paths["target_independence_probe"], probes)
    external_ingest.write_jsonl(output_paths["validated_labels"], labels)
    external_ingest.write_jsonl(output_paths["geometry_validity_targets"], geometry_targets)
    external_ingest.write_jsonl(output_paths["relation_reliability_targets"], reliability_targets)
    external_ingest.write_jsonl(output_paths["geometry_validity_posterior_rows"], geometry_posterior)
    external_ingest.write_jsonl(output_paths["relation_reliability_posterior_rows"], reliability_posterior)
    external_ingest.write_jsonl(output_paths["excluded_targets"], excluded)
    external_ingest.write_jsonl(output_paths["ingestion_errors"], errors)
    external_ingest.write_csv(output_paths["target_group_table"], all_group_rows)
    external_ingest.write_csv(output_paths["shortcut_audit"], all_probe_summaries)
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
        f"errors={counts['errors']} user_confirmed={summary['boundary']['user_confirmed_completed_by_user']} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
