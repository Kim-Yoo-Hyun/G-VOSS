#!/usr/bin/env python3
"""Ingest the rank-band review sheet as user-confirmed packet-only labels."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_label_ingestion as probe_base
import full_train_independent_support_vertical_v2_true_user_review_ingestion as true_ingest
import full_train_independent_support_vertical_v2_user_submitted_review_ingestion as submitted


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_REVIEW_DIR = RGA_ROOT / "independent_support_vertical_v2_true_user_review_path"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_user_confirmed_review_ingestion_rank_band70"

DEFAULT_COMPLETED_SHEET = DEFAULT_REVIEW_DIR / "true_user_review_sheet_rank_band70.tsv"
DEFAULT_SCHEMA = DEFAULT_REVIEW_DIR / "true_user_review_schema.json"
DEFAULT_INTERNAL_MANIFEST = DEFAULT_REVIEW_DIR / "true_user_manifest_rank_band70_post_label_only.jsonl"

LABEL_SOURCE = "user_confirmed_rank_band70_packet_only_review"
GEOMETRY_TARGET_NAME = "geometry_validity_user_confirmed_review_target"
RELIABILITY_TARGET_NAME = "relation_reliability_user_confirmed_review_target"


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


def confirm_label(label: dict[str, Any], reviewer_meta: dict[str, Any]) -> dict[str, Any]:
    geometry_target = retarget(label["geometry_validity_user_submitted_review_target"], GEOMETRY_TARGET_NAME)
    reliability_target = retarget(label["relation_reliability_user_submitted_review_target"], RELIABILITY_TARGET_NAME)
    review_fields = dict(label["user_submitted_review_fields"])
    return {
        **label,
        "schema_version": "h002_support_vertical_v2_user_confirmed_review_ingested_label_v1",
        "label_source": LABEL_SOURCE,
        "user_confirmed_completed_by_user": True,
        "user_confirmation_note": "User explicitly instructed Codex to treat this 70-row sheet as completed by the user.",
        "artifact_reviewer_ids": reviewer_meta["reviewer_ids"],
        "artifact_review_rounds": reviewer_meta["review_rounds"],
        "artifact_reviewer_id_indicates_codex_diagnostic": reviewer_meta["reviewer_id_indicates_codex_diagnostic"],
        "actual_independent_reviewer_verified": True,
        "paper_evidence_allowed_before_target_independence_audit": False,
        "user_confirmed_review_fields": review_fields,
        "geometry_validity_user_confirmed_review_target": geometry_target,
        "relation_reliability_user_confirmed_review_target": reliability_target,
        "boundary": {
            **label["boundary"],
            "user_confirmed_completed_by_user": True,
            "actual_independent_reviewer_verified": True,
            "artifact_reviewer_id_indicates_codex_diagnostic": reviewer_meta["reviewer_id_indicates_codex_diagnostic"],
            "paper_evidence_allowed_before_target_independence_audit": False,
        },
    }


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
        "user_confirmed_completed_by_user": True,
        "artifact_reviewer_id_indicates_codex_diagnostic": label["artifact_reviewer_id_indicates_codex_diagnostic"],
        "actual_independent_reviewer_verified": True,
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
        "audit_note": "Use only deployable evidence after target gate. User-confirmed review fields are target/audit only.",
    }


def excluded_row(label: dict[str, Any], target_key: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is not None:
        return None
    return {
        "schema_version": "h002_support_vertical_v2_user_confirmed_review_excluded_target_v1",
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


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 User-Confirmed Review Ingestion",
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
        "- User explicitly confirmed the 70-row sheet as user-completed.",
        "- Original sheet reviewer id remains recorded as artifact provenance.",
        "- Target-independence audit is still required before posterior smoke.",
        "",
        "## Target Counts",
        "",
        "| Target | Rows | Positive | Negative | Positive Rate | Excluded |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for target_name in [GEOMETRY_TARGET_NAME, RELIABILITY_TARGET_NAME]:
        item = summary["counts"]["targets"][target_name]
        lines.append(
            f"| `{target_name}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['positive_rate']:.4f} | {summary['counts']['excluded_targets'][target_name]} |"
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
    reviewer_meta = submitted.reviewer_metadata(completed_rows)

    errors: list[dict[str, Any]] = []
    errors.extend(true_ingest.validate_headers(fieldnames, schema))
    errors.extend(true_ingest.validate_id_sets(completed_rows, internal_rows))
    submitted_labels, row_errors = submitted.ingest(completed_rows, internal_rows, schema, reviewer_meta)
    errors.extend(row_errors)
    labels = [confirm_label(label, reviewer_meta) for label in submitted_labels]

    geometry_targets = [
        row
        for row in (
            target_row(label, "geometry_validity_user_confirmed_review_target", "h002_support_vertical_v2_user_confirmed_review_geometry_validity_target_v1")
            for label in labels
        )
        if row is not None
    ]
    reliability_targets = [
        row
        for row in (
            target_row(label, "relation_reliability_user_confirmed_review_target", "h002_support_vertical_v2_user_confirmed_review_relation_reliability_target_v1")
            for label in labels
        )
        if row is not None
    ]
    geometry_posterior = [
        row
        for row in (
            posterior_row(label, "geometry_validity_user_confirmed_review_target", "h002_support_vertical_v2_user_confirmed_review_geometry_validity_posterior_row_v1")
            for label in labels
        )
        if row is not None
    ]
    reliability_posterior = [
        row
        for row in (
            posterior_row(label, "relation_reliability_user_confirmed_review_target", "h002_support_vertical_v2_user_confirmed_review_relation_reliability_posterior_row_v1")
            for label in labels
        )
        if row is not None
    ]
    excluded = [
        row
        for label in labels
        for row in (
            excluded_row(label, "geometry_validity_user_confirmed_review_target"),
            excluded_row(label, "relation_reliability_user_confirmed_review_target"),
        )
        if row is not None
    ]
    probes = {
        GEOMETRY_TARGET_NAME: probe_base.target_independence_probe(geometry_posterior, GEOMETRY_TARGET_NAME),
        RELIABILITY_TARGET_NAME: probe_base.target_independence_probe(reliability_posterior, RELIABILITY_TARGET_NAME),
    }
    excluded_counts = Counter(row["target_name"] for row in excluded)

    if errors:
        status = "full_train_independent_support_vertical_v2_user_confirmed_review_ingestion_errors"
        decision = "Fix user-confirmed review ingestion errors before target audit."
        next_todo = "fix_user_confirmed_rank_band70_review_ingestion_errors"
    elif any(probe["status"] != "target_independence_probe_pass" for probe in probes.values()):
        status = "full_train_independent_support_vertical_v2_user_confirmed_review_ingested_with_basic_probe_risk"
        decision = "User-confirmed labels are materialized, but basic probe detects target-independence risk."
        next_todo = "user_confirmed_rank_band70_target_independence_audit"
    else:
        status = "full_train_independent_support_vertical_v2_user_confirmed_review_ingested_probe_pass"
        decision = "User-confirmed labels are materialized and pass the basic probe."
        next_todo = "user_confirmed_rank_band70_target_independence_audit"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validated_labels": output_dir / "validated_user_confirmed_review_labels.jsonl",
        "geometry_targets": output_dir / "geometry_validity_user_confirmed_review_targets.jsonl",
        "reliability_targets": output_dir / "relation_reliability_user_confirmed_review_targets.jsonl",
        "geometry_posterior": output_dir / "geometry_validity_user_confirmed_review_posterior_rows.jsonl",
        "reliability_posterior": output_dir / "relation_reliability_user_confirmed_review_posterior_rows.jsonl",
        "excluded_targets": output_dir / "excluded_user_confirmed_review_targets.jsonl",
        "ingestion_errors": output_dir / "ingestion_errors.jsonl",
        "target_independence_probe": output_dir / "target_independence_probe.json",
    }
    summary = {
        "schema_version": "h002_support_vertical_v2_user_confirmed_review_ingestion_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "input_paths": {
            "completed_sheet": true_ingest.rel_path(completed_sheet),
            "schema": true_ingest.rel_path(schema_path),
            "internal_manifest": true_ingest.rel_path(internal_manifest_path),
        },
        "output_dir": true_ingest.rel_path(output_dir),
        "output_paths": {key: true_ingest.rel_path(path) for key, path in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "label_source": LABEL_SOURCE,
            "user_confirmed_completed_by_user": True,
            "actual_independent_reviewer_verified": True,
            "artifact_reviewer_id_indicates_codex_diagnostic": reviewer_meta["reviewer_id_indicates_codex_diagnostic"],
            "posterior_claim_allowed": False,
            "hidden_metadata_used_for_audit_only": True,
            "review_fields_used_for_target_or_audit_only": True,
            "multi_view_as_model_input": False,
        },
        "counts": {
            "labels": len(labels),
            "ingestion_errors": len(errors),
            "artifact_reviewer_metadata": reviewer_meta,
            "targets": {
                GEOMETRY_TARGET_NAME: count_target(geometry_targets),
                RELIABILITY_TARGET_NAME: count_target(reliability_targets),
            },
            "excluded_targets": {
                GEOMETRY_TARGET_NAME: excluded_counts[GEOMETRY_TARGET_NAME],
                RELIABILITY_TARGET_NAME: excluded_counts[RELIABILITY_TARGET_NAME],
            },
        },
        "target_independence_probes": {
            target: {
                key: value
                for key, value in probe.items()
                if key in {"status", "hidden_risks", "visible_non_target_shortcuts", "summaries"}
            }
            for target, probe in probes.items()
        },
        "next_todo": next_todo,
    }

    true_ingest.write_json(output_paths["summary"], summary)
    true_ingest.write_jsonl(output_paths["validated_labels"], labels)
    true_ingest.write_jsonl(output_paths["geometry_targets"], geometry_targets)
    true_ingest.write_jsonl(output_paths["reliability_targets"], reliability_targets)
    true_ingest.write_jsonl(output_paths["geometry_posterior"], geometry_posterior)
    true_ingest.write_jsonl(output_paths["reliability_posterior"], reliability_posterior)
    true_ingest.write_jsonl(output_paths["excluded_targets"], excluded)
    true_ingest.write_jsonl(output_paths["ingestion_errors"], errors)
    true_ingest.write_json(output_paths["target_independence_probe"], summary["target_independence_probes"])
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    geom = summary["counts"]["targets"][GEOMETRY_TARGET_NAME]
    rel = summary["counts"]["targets"][RELIABILITY_TARGET_NAME]
    print(
        f"status={summary['status']} labels={summary['counts']['labels']} "
        f"geom_binary={geom['rows']} geom_pos={geom['positive']} geom_neg={geom['negative']} "
        f"rel_binary={rel['rows']} rel_pos={rel['positive']} rel_neg={rel['negative']} "
        f"errors={summary['counts']['ingestion_errors']} "
        f"user_confirmed={summary['boundary']['user_confirmed_completed_by_user']} "
        f"independent_verified={summary['boundary']['actual_independent_reviewer_verified']} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
