#!/usr/bin/env python3
"""Ingest the user-submitted rank-band review sheet after label lock."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_label_ingestion as probe_base
import full_train_independent_support_vertical_v2_true_user_review_ingestion as true_ingest


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_REVIEW_DIR = RGA_ROOT / "independent_support_vertical_v2_true_user_review_path"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70"

DEFAULT_COMPLETED_SHEET = DEFAULT_REVIEW_DIR / "true_user_review_sheet_rank_band70.tsv"
DEFAULT_SCHEMA = DEFAULT_REVIEW_DIR / "true_user_review_schema.json"
DEFAULT_INTERNAL_MANIFEST = DEFAULT_REVIEW_DIR / "true_user_manifest_rank_band70_post_label_only.jsonl"

LABEL_SOURCE = "user_submitted_rank_band70_packet_only_review"
GEOMETRY_TARGET_NAME = "geometry_validity_user_submitted_review_target"
RELIABILITY_TARGET_NAME = "relation_reliability_user_submitted_review_target"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-sheet", type=Path, default=DEFAULT_COMPLETED_SHEET)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--internal-manifest", type=Path, default=DEFAULT_INTERNAL_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def retarget(target: dict[str, Any], target_name: str) -> dict[str, Any]:
    output = dict(target)
    output["target_name"] = target_name
    return output


def reviewer_metadata(rows: list[dict[str, str]]) -> dict[str, Any]:
    reviewer_ids = Counter((row.get("external_reviewer_id") or "").strip() for row in rows)
    review_rounds = Counter((row.get("external_review_round") or "").strip() for row in rows)
    lower_ids = [key.lower() for key in reviewer_ids]
    return {
        "reviewer_ids": dict(sorted(reviewer_ids.items())),
        "review_rounds": dict(sorted(review_rounds.items())),
        "reviewer_id_indicates_codex_diagnostic": any("codex" in key for key in lower_ids),
        "reviewer_id_indicates_packet_only": any("packet_only" in key for key in lower_ids),
    }


def make_label(row: dict[str, str], internal: dict[str, Any], reviewer_meta: dict[str, Any]) -> dict[str, Any]:
    geometry_target = retarget(true_ingest.derive_geometry_target(row), GEOMETRY_TARGET_NAME)
    reliability_target = retarget(true_ingest.derive_reliability_target(row, geometry_target), RELIABILITY_TARGET_NAME)
    return {
        "schema_version": "h002_support_vertical_v2_user_submitted_review_ingested_label_v1",
        **true_ingest.base_identity(row),
        "label_source": LABEL_SOURCE,
        "user_reported_completed_by_user": True,
        "user_submitted_completed_sheet": True,
        "reviewer_id_indicates_codex_diagnostic": reviewer_meta["reviewer_id_indicates_codex_diagnostic"],
        "actual_independent_reviewer_verified": False,
        "paper_evidence_allowed_before_independence_confirmation": False,
        "hidden_manifest_joined_after_label_lock": True,
        "review_fields_are_target_only": True,
        "user_submitted_review_fields": true_ingest.true_user_review_fields(row),
        "geometry_validity_user_submitted_review_target": geometry_target,
        "relation_reliability_user_submitted_review_target": reliability_target,
        "deployable_evidence_after_label_lock": true_ingest.deployable_evidence(row, internal),
        "hidden_audit_metadata_post_label_only": true_ingest.hidden_metadata(internal),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "user_reported_completed_by_user": True,
            "actual_independent_reviewer_verified": False,
            "reviewer_id_indicates_codex_diagnostic": reviewer_meta["reviewer_id_indicates_codex_diagnostic"],
            "multi_view_as_model_input": False,
        },
    }


def ingest(
    completed_rows: list[dict[str, str]],
    internal_rows: list[dict[str, Any]],
    schema: dict[str, Any],
    reviewer_meta: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    internal_by_id = {str(row["blind_review_id"]): row for row in internal_rows}
    labels: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(completed_rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        internal = internal_by_id.get(blind_id)
        row_errors = true_ingest.validate_row(row, row_number, schema, internal)
        if internal is None:
            row_errors.append({"error_type": "missing_internal_manifest_for_completed_row", "row_number": row_number, "blind_review_id": blind_id})
        if row_errors:
            errors.extend(row_errors)
            continue
        labels.append(make_label(row, internal_by_id[blind_id], reviewer_meta))
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
        "user_reported_completed_by_user": True,
        "user_submitted_completed_sheet": True,
        "reviewer_id_indicates_codex_diagnostic": label["reviewer_id_indicates_codex_diagnostic"],
        "actual_independent_reviewer_verified": False,
        "paper_locked": False,
    }


def posterior_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    row = target_row(label, target_key, schema_version)
    if row is None:
        return None
    return {
        **row,
        "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
        "audit_only_user_submitted_review_fields": label["user_submitted_review_fields"],
        "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
        "audit_note": "Use only deployable evidence after target gate. User-submitted review fields are target/audit only.",
    }


def excluded_row(label: dict[str, Any], target_key: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is not None:
        return None
    return {
        "schema_version": "h002_support_vertical_v2_user_submitted_review_excluded_target_v1",
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
        "audit_only_user_submitted_review_fields": label["user_submitted_review_fields"],
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
    for axis in true_ingest.TRUE_USER_AXIS_KEYS:
        output[axis] = dict(sorted(Counter(row["user_submitted_review_fields"].get(axis) for row in labels).items()))
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 User-Submitted Review Ingestion",
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
        "- Sheet was submitted as completed by the user.",
        "- Reviewer id indicates `codex_packet_only_diagnostic`, so this is not over-claimed as verified independent external annotation.",
        "- Review fields are target/audit only and are not posterior inputs.",
        "- Hidden manifest is joined only after label lock for audit.",
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
    completed_sheet = true_ingest.as_abs(args.completed_sheet)
    schema_path = true_ingest.as_abs(args.schema)
    internal_manifest_path = true_ingest.as_abs(args.internal_manifest)
    output_dir = true_ingest.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    fieldnames, completed_rows = true_ingest.read_tsv(completed_sheet)
    schema = true_ingest.read_json(schema_path)
    internal_rows = true_ingest.read_jsonl(internal_manifest_path)
    reviewer_meta = reviewer_metadata(completed_rows)

    errors: list[dict[str, Any]] = []
    errors.extend(true_ingest.validate_headers(fieldnames, schema))
    errors.extend(true_ingest.validate_id_sets(completed_rows, internal_rows))
    labels, row_errors = ingest(completed_rows, internal_rows, schema, reviewer_meta)
    errors.extend(row_errors)

    geometry_targets = [
        row
        for row in (
            target_row(label, "geometry_validity_user_submitted_review_target", "h002_support_vertical_v2_user_submitted_review_geometry_validity_target_v1")
            for label in labels
        )
        if row is not None
    ]
    reliability_targets = [
        row
        for row in (
            target_row(label, "relation_reliability_user_submitted_review_target", "h002_support_vertical_v2_user_submitted_review_relation_reliability_target_v1")
            for label in labels
        )
        if row is not None
    ]
    geometry_posterior = [
        row
        for row in (
            posterior_row(label, "geometry_validity_user_submitted_review_target", "h002_support_vertical_v2_user_submitted_review_geometry_validity_posterior_row_v1")
            for label in labels
        )
        if row is not None
    ]
    reliability_posterior = [
        row
        for row in (
            posterior_row(label, "relation_reliability_user_submitted_review_target", "h002_support_vertical_v2_user_submitted_review_relation_reliability_posterior_row_v1")
            for label in labels
        )
        if row is not None
    ]
    excluded = [
        row
        for label in labels
        for row in (
            excluded_row(label, "geometry_validity_user_submitted_review_target"),
            excluded_row(label, "relation_reliability_user_submitted_review_target"),
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
        status = "full_train_independent_support_vertical_v2_user_submitted_review_ingestion_errors"
        decision = "Fix user-submitted review ingestion errors before target audit."
        next_todo = "fix_user_submitted_rank_band70_review_ingestion_errors"
    elif any(probe["status"] != "target_independence_probe_pass" for probe in probes.values()):
        status = "full_train_independent_support_vertical_v2_user_submitted_review_ingested_with_basic_probe_risk"
        decision = "User-submitted labels are materialized, but basic probe detects target-independence risk."
        next_todo = "user_submitted_rank_band70_target_independence_audit"
    else:
        status = "full_train_independent_support_vertical_v2_user_submitted_review_ingested_ready_for_target_audit"
        decision = "User-submitted labels are materialized. Run dedicated target-independence audit before posterior smoke."
        next_todo = "user_submitted_rank_band70_target_independence_audit"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validated_labels": output_dir / "validated_user_submitted_review_labels.jsonl",
        "geometry_validity_targets": output_dir / "geometry_validity_user_submitted_review_targets.jsonl",
        "relation_reliability_targets": output_dir / "relation_reliability_user_submitted_review_targets.jsonl",
        "geometry_validity_posterior_rows": output_dir / "geometry_validity_user_submitted_review_posterior_rows.jsonl",
        "relation_reliability_posterior_rows": output_dir / "relation_reliability_user_submitted_review_posterior_rows.jsonl",
        "excluded_targets": output_dir / "excluded_user_submitted_review_targets.jsonl",
        "target_independence_probe": output_dir / "target_independence_probe.json",
        "target_group_table": output_dir / "target_group_table.csv",
        "shortcut_audit": output_dir / "shortcut_audit.csv",
        "ingestion_errors": output_dir / "ingestion_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_support_vertical_v2_user_submitted_review_ingestion_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "input_paths": {
            "completed_sheet": true_ingest.rel_path(completed_sheet),
            "true_user_review_schema": true_ingest.rel_path(schema_path),
            "internal_manifest_post_label_only": true_ingest.rel_path(internal_manifest_path),
        },
        "output_dir": true_ingest.rel_path(output_dir),
        "output_paths": {key: true_ingest.rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "label_source": LABEL_SOURCE,
            "user_reported_completed_by_user": True,
            "user_submitted_completed_sheet": True,
            "reviewer_id_indicates_codex_diagnostic": reviewer_meta["reviewer_id_indicates_codex_diagnostic"],
            "actual_independent_reviewer_verified": False,
            "paper_evidence_allowed_before_independence_confirmation": False,
            "hidden_metadata_as_model_input": False,
            "review_fields_as_model_input": False,
            "previous_proxy_labels_as_model_input": False,
            "source_score_feature_join_pending": True,
            "multi_view_as_model_input": False,
        },
        "reviewer_metadata": reviewer_meta,
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

    true_ingest.write_json(output_paths["summary"], summary)
    true_ingest.write_json(output_paths["target_independence_probe"], probes)
    true_ingest.write_jsonl(output_paths["validated_labels"], labels)
    true_ingest.write_jsonl(output_paths["geometry_validity_targets"], geometry_targets)
    true_ingest.write_jsonl(output_paths["relation_reliability_targets"], reliability_targets)
    true_ingest.write_jsonl(output_paths["geometry_validity_posterior_rows"], geometry_posterior)
    true_ingest.write_jsonl(output_paths["relation_reliability_posterior_rows"], reliability_posterior)
    true_ingest.write_jsonl(output_paths["excluded_targets"], excluded)
    true_ingest.write_jsonl(output_paths["ingestion_errors"], errors)
    true_ingest.write_csv(output_paths["target_group_table"], all_group_rows)
    true_ingest.write_csv(output_paths["shortcut_audit"], all_probe_summaries)
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
        f"errors={counts['errors']} reviewer_id_caveat={summary['boundary']['reviewer_id_indicates_codex_diagnostic']} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
