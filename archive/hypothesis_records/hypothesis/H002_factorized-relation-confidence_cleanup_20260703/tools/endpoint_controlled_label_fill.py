#!/usr/bin/env python3
"""Fill the endpoint-controlled review sheet as a Codex proxy."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_external_review_fill as visible_fill


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
ASSET_ROOT = RGA_ROOT / "endpoint_controlled_asset_packets"
DEFAULT_INPUT_SHEET = ASSET_ROOT / "endpoint_controlled_full_label_sheet.tsv"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "endpoint_controlled_label_fill_codex_proxy_user_requested"

REVIEWER_ID = "(codex_proxy_endpoint_controlled_user_requested)"

COMPLETION_FIELDS = [
    "external_reviewer_id",
    "external_review_round",
    "endpoint_identity_external",
    "visual_pair_evaluability_external",
    "mesh_pair_evaluability_external",
    "visual_geometry_answer_external",
    "mesh_geometry_answer_external",
    "relation_informativeness_external",
    "final_relation_reliability_external",
    "uncertainty_reason_external",
]

ALLOWED_VALUES = {
    "endpoint_identity_external": {"both_valid", "subject_invalid", "object_invalid", "both_invalid", "uncertain"},
    "visual_pair_evaluability_external": {"evaluable", "occluded_or_unclear", "missing_views", "not_applicable"},
    "mesh_pair_evaluability_external": {"evaluable", "unclear", "missing_mesh", "not_applicable"},
    "visual_geometry_answer_external": {"supports_predicate", "contradicts_predicate", "uncertain", "not_applicable"},
    "mesh_geometry_answer_external": {"supports_predicate", "contradicts_predicate", "uncertain", "not_applicable"},
    "relation_informativeness_external": {"informative", "trivial_dense_or_room_structure", "ontology_mismatch", "uncertain"},
    "final_relation_reliability_external": {"reliable", "unreliable", "uncertain"},
    "uncertainty_reason_external": {
        "none",
        "insufficient_evidence",
        "ambiguous_relation",
        "ontology_mismatch",
        "trivial_dense_relation",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fill_row(row: dict[str, str]) -> dict[str, Any]:
    filled = visible_fill.fill_row(row)
    filled["external_reviewer_id"] = REVIEWER_ID
    filled["external_label_notes"] = (
        "codex proxy filled for endpoint-controlled workflow; used only labeler-visible "
        "identity fields and packet availability; hidden endpoint/sampling metadata was not read"
    )
    return filled


def validate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id")
        for field in COMPLETION_FIELDS:
            value = row.get(field)
            if value is None or value == "":
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "error_type": "missing_completion_field",
                    }
                )
            elif field in ALLOWED_VALUES and value not in ALLOWED_VALUES[field]:
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "value": value,
                        "error_type": "invalid_completion_value",
                    }
                )
        for packet_field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = row.get(packet_field, "")
            if not value or not as_abs(Path(value)).exists():
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": packet_field,
                        "value": value,
                        "error_type": "packet_path_missing",
                    }
                )
    return errors


def label_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_endpoint_controlled_proxy_label_v1",
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
        "endpoint_controlled_review_fields": {
            "external_reviewer_id": row["external_reviewer_id"],
            "external_review_round": row["external_review_round"],
            "endpoint_identity_external": row["endpoint_identity_external"],
            "visual_pair_evaluability_external": row["visual_pair_evaluability_external"],
            "mesh_pair_evaluability_external": row["mesh_pair_evaluability_external"],
            "visual_geometry_answer_external": row["visual_geometry_answer_external"],
            "mesh_geometry_answer_external": row["mesh_geometry_answer_external"],
            "relation_informativeness_external": row["relation_informativeness_external"],
            "final_relation_reliability_external": row["final_relation_reliability_external"],
            "uncertainty_reason_external": row["uncertainty_reason_external"],
            "external_label_notes": row["external_label_notes"],
        },
        "provenance": {
            "filled_by": "codex_proxy",
            "user_requested_treat_as_user_review": True,
            "actual_user_reviewer": False,
            "paper_evidence_allowed_before_user_confirmation": False,
            "used_hidden_manifest": False,
            "used_endpoint_flag_pattern": False,
            "used_needed_label_proxy": False,
            "used_numeric_witness_values": False,
            "used_previous_proxy_labels": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "used_geometry_status": False,
            "validation_usage": False,
            "test_usage": False,
            "multi_view_as_model_input": False,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    reliability = counts["final_relation_reliability_external"]
    geometry = counts["visual_geometry_answer_external"]
    lines = [
        "# H002 Endpoint-Controlled Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage fill.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Filled by Codex proxy at user request for workflow progression.",
        "- This is not paper-level external human annotation before user confirmation.",
        "- Hidden endpoint/sampling manifest, score/rank, `p_geom_valid`, geometry status, and numeric witness values are not read.",
        "- Multi-view/mesh packet paths are label evidence only, not model input.",
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
        f"| validation errors | {counts['validation_errors']} |",
        "",
        "## Geometry Answers",
        "",
        "| Visual geometry answer | Count |",
        "| --- | ---: |",
    ]
    for key, value in geometry.items():
        lines.append(f"| `{key}` | {value} |")
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
    input_sheet = as_abs(args.input_sheet)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fieldnames, rows = read_tsv(input_sheet)
    filled_rows = [fill_row(row) for row in rows]
    errors = validate_rows(filled_rows)
    label_rows = [label_record(row) for row in filled_rows]

    reliability_counts = Counter(row["final_relation_reliability_external"] for row in filled_rows)
    geometry_counts = Counter(row["visual_geometry_answer_external"] for row in filled_rows)
    mesh_geometry_counts = Counter(row["mesh_geometry_answer_external"] for row in filled_rows)
    family_counts = Counter(row["predicate_family"] for row in filled_rows)
    packet_counts = Counter(row["evidence_packet_status"] for row in filled_rows)
    informativeness_counts = Counter(row["relation_informativeness_external"] for row in filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "completed_sheet": output_dir / "completed_endpoint_controlled_label_sheet_codex_proxy_user_requested.tsv",
        "endpoint_controlled_proxy_labels": output_dir / "endpoint_controlled_proxy_labels.jsonl",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
        "schema": output_dir / "endpoint_controlled_fill_schema.json",
    }

    status = "h002_endpoint_controlled_label_fill_ready_for_ingestion"
    if errors:
        status = "h002_endpoint_controlled_label_fill_errors"
    next_todo = (
        "endpoint_controlled_label_ingestion"
        if not errors
        else "fix_endpoint_controlled_label_fill"
    )
    decision = (
        "Endpoint-controlled label fill is complete. Ingest the 62 labels and run target-independence audit before posterior smoke."
        if not errors
        else "Endpoint-controlled label fill has validation errors. Fix the sheet before ingestion."
    )
    summary = {
        "schema_version": "h002_endpoint_controlled_label_fill_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "input_paths": {
            "endpoint_controlled_full_label_sheet": rel_path(input_sheet),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split_policy": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "posterior_trained": False,
            "filled_by": "codex_proxy",
            "user_requested_treat_as_user_review": True,
            "actual_user_reviewer": False,
            "paper_evidence_allowed_before_user_confirmation": False,
            "used_hidden_manifest": False,
            "used_endpoint_flag_pattern": False,
            "used_needed_label_proxy": False,
            "used_numeric_witness_values": False,
            "used_previous_proxy_labels": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "used_geometry_status": False,
            "multi_view_as_model_input": False,
            "posterior_smoke_allowed": False,
        },
        "counts": {
            "rows": len(filled_rows),
            "validation_errors": len(errors),
            "by_family": dict(sorted(family_counts.items())),
            "by_packet_status": dict(sorted(packet_counts.items())),
            "visual_geometry_answer_external": dict(sorted(geometry_counts.items())),
            "mesh_geometry_answer_external": dict(sorted(mesh_geometry_counts.items())),
            "relation_informativeness_external": dict(sorted(informativeness_counts.items())),
            "final_relation_reliability_external": dict(sorted(reliability_counts.items())),
        },
        "next_todo": next_todo,
    }
    schema = {
        "schema_version": "h002_endpoint_controlled_fill_schema_v1",
        "completion_fields": COMPLETION_FIELDS,
        "allowed_review_values": {key: sorted(value) for key, value in ALLOWED_VALUES.items()},
        "boundary": summary["boundary"],
    }

    write_tsv(output_paths["completed_sheet"], filled_rows, fieldnames)
    write_jsonl(output_paths["endpoint_controlled_proxy_labels"], label_rows)
    write_jsonl(output_paths["fill_validation_errors"], errors)
    write_json(output_paths["schema"], schema)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    reliability = counts["final_relation_reliability_external"]
    print(
        f"status={summary['status']} rows={counts['rows']} "
        f"reliable={reliability.get('reliable', 0)} "
        f"unreliable={reliability.get('unreliable', 0)} "
        f"uncertain={reliability.get('uncertain', 0)} "
        f"errors={counts['validation_errors']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
