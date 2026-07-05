#!/usr/bin/env python3
"""Validate and lock user-filled H002 v20 audit-packet labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

MATERIALIZATION_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization"
LEAKAGE_REVIEW_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review"
OUTPUT_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_fill"

VISIBLE_SHEET = MATERIALIZATION_DIR / "visible_review_sheet.tsv"
LEAKAGE_SUMMARY = LEAKAGE_REVIEW_DIR / "summary.json"

SCHEMA_VERSION = "h002_reliability_target_v20_attachment_endpoint_balanced_audit_packet_label_fill_v1"
STATUS_OK = "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_filled_user_visible_packet"
STATUS_ERROR = "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_fill_errors"
NEXT_TODO = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingestion"

EXPECTED_FIELDS = [
    "packet_id",
    "blind_review_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "packet_role",
    "evidence_tier",
    "evidence_tier_description",
    "visual_context_summary",
    "mesh_context_summary",
    "audit_question",
    "review_relation_reliability",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

ALLOWED = {
    "review_relation_reliability": {"accept_reliable", "reject_unreliable", "abstain_uncertain"},
    "review_geometry_support": {"supported", "unsupported", "uncertain"},
    "review_endpoint_identity": {"clear_endpoint_identity", "uncertain_endpoint_identity"},
    "review_coverage": {"sufficient", "limited"},
    "review_uncertainty": {
        "none",
        "visual_ambiguous",
        "functional_connection_ambiguous",
        "ontology_ambiguous",
        "mesh_needed",
    },
}

PRIMARY_PREDICATES = {"attached to", "hanging on"}
CONNECTED_PREDICATE = "connected to"
PRIMARY_ROLE = "primary_attachment_reliability_candidate"
CONNECTED_ROLE = "connected_diagnostic_only"
EVIDENCE_TIERS = {"T1_strong_pair_visual", "T2_individual_visual_plus_mesh"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visible-sheet", type=Path, default=VISIBLE_SHEET)
    parser.add_argument("--leakage-summary", type=Path, default=LEAKAGE_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_leakage_summary(path: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    summary = read_json(path)
    if summary.get("status") != "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review_passed_ready_for_label_fill":
        errors.append({"error_type": "unexpected_leakage_status", "actual": summary.get("status")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "leakage_validation_errors_present", "actual": summary.get("validation_errors")})
    counts = summary.get("counts", {})
    if counts.get("visible_leakage_hits") != 0:
        errors.append({"error_type": "visible_leakage_hits_present", "actual": counts.get("visible_leakage_hits")})
    if counts.get("visible_sheet_rows") != 320:
        errors.append({"error_type": "unexpected_leakage_visible_row_count", "actual": counts.get("visible_sheet_rows")})
    return errors


def validate_rows(fields: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if fields != EXPECTED_FIELDS:
        errors.append({"error_type": "visible_sheet_schema_mismatch", "expected": EXPECTED_FIELDS, "actual": fields})
    if len(rows) != 320:
        errors.append({"error_type": "unexpected_visible_row_count", "expected": 320, "actual": len(rows)})
    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        packet_id = row.get("packet_id", "")
        if not packet_id:
            errors.append({"error_type": "missing_packet_id", "row_number": row_number})
        elif packet_id in seen:
            errors.append({"error_type": "duplicate_packet_id", "row_number": row_number, "packet_id": packet_id})
        seen.add(packet_id)
        for field in EXPECTED_FIELDS:
            if field != "review_notes" and not str(row.get(field, "")).strip():
                errors.append({"error_type": "missing_required_field", "row_number": row_number, "packet_id": packet_id, "field": field})
        for field, allowed in ALLOWED.items():
            if row.get(field) not in allowed:
                errors.append({"error_type": f"invalid_{field}", "row_number": row_number, "packet_id": packet_id, "value": row.get(field)})
        if row.get("predicate_label") not in PRIMARY_PREDICATES | {CONNECTED_PREDICATE}:
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "packet_id": packet_id, "value": row.get("predicate_label")})
        if row.get("evidence_tier") not in EVIDENCE_TIERS:
            errors.append({"error_type": "unexpected_evidence_tier", "row_number": row_number, "packet_id": packet_id, "value": row.get("evidence_tier")})
        if row.get("predicate_label") == CONNECTED_PREDICATE and row.get("packet_role") != CONNECTED_ROLE:
            errors.append({"error_type": "connected_predicate_not_diagnostic_role", "row_number": row_number, "packet_id": packet_id})
        if row.get("predicate_label") in PRIMARY_PREDICATES and row.get("packet_role") != PRIMARY_ROLE:
            errors.append({"error_type": "primary_predicate_not_primary_role", "row_number": row_number, "packet_id": packet_id})
        if row.get("packet_role") == CONNECTED_ROLE and row.get("review_relation_reliability") != "abstain_uncertain":
            errors.append({"error_type": "connected_diagnostic_should_abstain", "row_number": row_number, "packet_id": packet_id, "value": row.get("review_relation_reliability")})
    return errors


def decision_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "schema_version": "h002_reliability_target_v20_attachment_label_decision_v1",
                "packet_id": row["packet_id"],
                "blind_review_id": row["blind_review_id"],
                "predicate_label": row["predicate_label"],
                "packet_role": row["packet_role"],
                "evidence_tier": row["evidence_tier"],
                "review_relation_reliability": row["review_relation_reliability"],
                "review_geometry_support": row["review_geometry_support"],
                "review_endpoint_identity": row["review_endpoint_identity"],
                "review_coverage": row["review_coverage"],
                "review_uncertainty": row["review_uncertainty"],
                "review_notes": row["review_notes"],
                "provenance": {
                    "label_source": "user_filled_visible_packet_v20",
                    "used_visible_review_sheet": True,
                    "used_packet_markdown_or_visible_assets": True,
                    "used_hidden_manifest": False,
                    "used_source_path": False,
                    "used_scan_id": False,
                    "used_existing_gt_match_axis": False,
                    "used_geometry_status_or_rank_hint": False,
                    "used_source_score_or_rank": False,
                    "used_p_geom_valid": False,
                    "used_validation_or_test": False,
                    "used_multi_view_as_model_input": False,
                    "used_mesh_as_model_input": False,
                    "paper_evidence_allowed": False,
                },
            }
        )
    return out


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V20 Attachment Audit Packet Label Fill",
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
        "## Counts",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"review_relation_reliability = {counts['review_relation_reliability']}",
        f"review_geometry_support = {counts['review_geometry_support']}",
        f"review_endpoint_identity = {counts['review_endpoint_identity']}",
        f"review_coverage = {counts['review_coverage']}",
        f"review_uncertainty = {counts['review_uncertainty']}",
        f"primary_binary_preview = {counts['primary_binary_preview']}",
        f"connected_diagnostic_rows = {counts['connected_diagnostic_rows']}",
        "```",
        "",
        "## Boundary",
        "",
        "The filled labels are user-filled visible-packet labels. Hidden manifest, scan/source ids, existing GT-match axis, geometry status, source score/rank, and `p_geom_valid` were not used in label-fill artifact construction.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fields, rows = read_tsv(args.visible_sheet)
    errors = validate_leakage_summary(args.leakage_summary)
    errors.extend(validate_rows(fields, rows))
    decisions = decision_rows(rows) if not errors else []

    rel_counts = Counter(row["review_relation_reliability"] for row in rows)
    geom_counts = Counter(row["review_geometry_support"] for row in rows)
    endpoint_counts = Counter(row["review_endpoint_identity"] for row in rows)
    coverage_counts = Counter(row["review_coverage"] for row in rows)
    uncertainty_counts = Counter(row["review_uncertainty"] for row in rows)
    predicate_counts = Counter(row["predicate_label"] for row in rows)
    role_counts = Counter(row["packet_role"] for row in rows)
    tier_counts = Counter(row["evidence_tier"] for row in rows)
    primary_binary = [
        row for row in rows
        if row["packet_role"] == PRIMARY_ROLE
        and row["predicate_label"] in PRIMARY_PREDICATES
        and row["review_relation_reliability"] in {"accept_reliable", "reject_unreliable"}
    ]
    primary_binary_counts = Counter(row["review_relation_reliability"] for row in primary_binary)
    connected_rows = [row for row in rows if row["packet_role"] == CONNECTED_ROLE]

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "filled_visible_review_sheet": output_dir / "filled_visible_review_sheet_v20.tsv",
        "label_decisions": output_dir / "label_decisions_v20.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_OK,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "visible_sheet": rel_path(args.visible_sheet),
            "leakage_summary": rel_path(args.leakage_summary),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "review_relation_reliability": dict(sorted(rel_counts.items())),
            "review_geometry_support": dict(sorted(geom_counts.items())),
            "review_endpoint_identity": dict(sorted(endpoint_counts.items())),
            "review_coverage": dict(sorted(coverage_counts.items())),
            "review_uncertainty": dict(sorted(uncertainty_counts.items())),
            "predicate_label": dict(sorted(predicate_counts.items())),
            "packet_role": dict(sorted(role_counts.items())),
            "evidence_tier": dict(sorted(tier_counts.items())),
            "primary_binary_preview": dict(sorted(primary_binary_counts.items())),
            "primary_binary_preview_rows": len(primary_binary),
            "connected_diagnostic_rows": len(connected_rows),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "locks_user_filled_labels": True,
            "hidden_manifest_read": False,
            "used_source_path": False,
            "used_scan_id": False,
            "used_existing_gt_match_axis": False,
            "used_geometry_status_or_rank_hint": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "connected_primary_binary_target": False,
        },
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO,
    }

    write_tsv(output_paths["filled_visible_review_sheet"], rows, EXPECTED_FIELDS)
    write_jsonl(output_paths["label_decisions"], decisions)
    write_jsonl(output_paths["validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"review_relation_reliability={summary['counts']['review_relation_reliability']}")
    print(f"primary_binary_preview={summary['counts']['primary_binary_preview']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
