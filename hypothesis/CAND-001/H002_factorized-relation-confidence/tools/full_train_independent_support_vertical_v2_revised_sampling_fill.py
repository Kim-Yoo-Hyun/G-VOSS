#!/usr/bin/env python3
"""Fill the revised sampling priority160 sheet as user-confirmed workflow labels."""

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

DEFAULT_PROTOCOL_DIR = RGA_ROOT / "independent_support_vertical_v2_sampling_protocol_decision"
DEFAULT_INPUT_SHEET = DEFAULT_PROTOCOL_DIR / "revised_sampling_sheet_priority160.tsv"
DEFAULT_SCHEMA = DEFAULT_PROTOCOL_DIR / "revised_sampling_review_schema.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed"

REVIEWER_ID = "user_confirmed_revised_sampling_priority160"
REVIEW_ROUND = "r1_20260619_revised_sampling_priority160"

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
    "external_label_notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-tag", default="priority160")
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
    filled["external_review_round"] = REVIEW_ROUND
    filled["external_label_notes"] = (
        "user-confirmed workflow label filled by Codex at user request; "
        "uses only labeler-visible identity fields and packet availability; "
        "hidden sampling axes, source rank/score, p_geom_valid, and previous proxy labels were not used"
    )
    return filled


def validate_headers(fieldnames: list[str], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = list(schema["visible_fields"])
    missing = [field for field in expected if field not in fieldnames]
    extra = [field for field in fieldnames if field not in expected]
    for field in missing:
        errors.append({"error_type": "missing_visible_field", "field": field})
    for field in extra:
        errors.append({"error_type": "unexpected_visible_field", "field": field})
    return errors


def validate_rows(rows: list[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = schema["review_values"]
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id")
        for field in COMPLETION_FIELDS:
            value = row.get(field)
            if value is None or value == "":
                errors.append({"row_number": row_number, "blind_review_id": blind_id, "field": field, "error_type": "missing_completion_field"})
            elif field in allowed and value not in set(allowed[field]):
                errors.append({"row_number": row_number, "blind_review_id": blind_id, "field": field, "value": value, "error_type": "invalid_completion_value"})
        if row.get("predicate_family") not in {"support_contact", "relative_vertical"}:
            errors.append({"row_number": row_number, "blind_review_id": blind_id, "field": "predicate_family", "value": row.get("predicate_family"), "error_type": "outside_support_vertical_scope"})
        for path_field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = row.get(path_field)
            if not value or not as_abs(Path(str(value))).exists():
                errors.append({"row_number": row_number, "blind_review_id": blind_id, "field": path_field, "value": value, "error_type": "packet_path_missing"})
    return errors


def label_record(row: dict[str, Any], output_tag: str) -> dict[str, Any]:
    return {
        "schema_version": f"h002_support_vertical_v2_revised_sampling_{output_tag}_filled_label_v1",
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
        "external_review_fields": {
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
            "filled_by": "codex_at_user_request",
            "workflow_treat_as_user_confirmed": True,
            "paper_evidence_allowed_before_target_independence_audit": False,
            "used_hidden_sampling_axes": False,
            "used_hidden_manifest": False,
            "used_numeric_witness_values": False,
            "used_previous_proxy_labels": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "validation_usage": False,
            "test_usage": False,
            "posterior_trained": False,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    reliability = counts["final_relation_reliability_external"]
    geometry = counts["visual_geometry_answer_external"]
    lines = [
        "# H002 Revised Sampling Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage fill.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Filled by Codex at user request and treated as user-confirmed workflow labels.",
        "- Hidden sampling axes, source rank/score, `p_geom_valid`, previous proxy labels, and numeric witness values are not used.",
        "- This is not posterior evidence until ingestion and target-independence audit pass.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {counts['rows']} |",
        f"| reliable | {reliability.get('reliable', 0)} |",
        f"| unreliable | {reliability.get('unreliable', 0)} |",
        f"| uncertain | {reliability.get('uncertain', 0)} |",
        f"| supports predicate | {geometry.get('supports_predicate', 0)} |",
        f"| contradicts predicate | {geometry.get('contradicts_predicate', 0)} |",
        f"| uncertain geometry | {geometry.get('uncertain', 0)} |",
        f"| validation errors | {counts['validation_errors']} |",
        "",
        "## Next TODO",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_sheet = as_abs(args.input_sheet)
    schema_path = as_abs(args.schema)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    fieldnames, rows = read_tsv(input_sheet)
    schema = read_json(schema_path)
    output_tag = str(args.output_tag)
    filled_rows = [fill_row(row) for row in rows]
    for row in filled_rows:
        row["external_reviewer_id"] = f"user_confirmed_revised_sampling_{output_tag}"
        row["external_review_round"] = f"r1_20260619_revised_sampling_{output_tag}"
    errors = validate_headers(fieldnames, schema)
    errors.extend(validate_rows(filled_rows, schema))
    label_rows = [label_record(row, output_tag) for row in filled_rows]

    reliability_counts = Counter(row["final_relation_reliability_external"] for row in filled_rows)
    geometry_counts = Counter(row["visual_geometry_answer_external"] for row in filled_rows)
    family_counts = Counter(row["predicate_family"] for row in filled_rows)
    predicate_counts = Counter(row["predicate_label"] for row in filled_rows)
    packet_counts = Counter(row["evidence_packet_status"] for row in filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "completed_sheet": output_dir / f"completed_revised_sampling_sheet_{output_tag}_user_confirmed.tsv",
        "filled_labels": output_dir / f"revised_sampling_{output_tag}_user_confirmed_labels.jsonl",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
    }

    status = f"full_train_independent_support_vertical_v2_revised_sampling_{output_tag}_filled_user_confirmed"
    if errors:
        status = f"full_train_independent_support_vertical_v2_revised_sampling_{output_tag}_fill_errors"

    summary = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_fill_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": "Filled revised sampling review fields as user-confirmed workflow labels; ingest and audit before posterior smoke.",
        "input_paths": {
            "revised_sampling_sheet": rel_path(input_sheet),
            "revised_sampling_review_schema": rel_path(schema_path),
        },
        "output_tag": output_tag,
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "filled_by": "codex_at_user_request",
            "workflow_treat_as_user_confirmed": True,
            "paper_evidence_allowed_before_target_independence_audit": False,
            "used_hidden_sampling_axes": False,
            "used_hidden_manifest": False,
            "used_numeric_witness_values": False,
            "used_previous_proxy_labels": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "multi_view_as_model_input": False,
            "posterior_smoke_allowed": False,
        },
        "counts": {
            "rows": len(filled_rows),
            "validation_errors": len(errors),
            "by_family": dict(sorted(family_counts.items())),
            "by_predicate": dict(sorted(predicate_counts.items())),
            "by_packet_status": dict(sorted(packet_counts.items())),
            "visual_geometry_answer_external": dict(sorted(geometry_counts.items())),
            "final_relation_reliability_external": dict(sorted(reliability_counts.items())),
        },
        "next_todo": f"revised_sampling_{output_tag}_label_ingestion",
    }

    write_tsv(output_paths["completed_sheet"], filled_rows, fieldnames)
    write_jsonl(output_paths["filled_labels"], label_rows)
    write_jsonl(output_paths["fill_validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    reliability = counts["final_relation_reliability_external"]
    print(
        f"status={summary['status']} rows={counts['rows']} "
        f"reliable={reliability.get('reliable', 0)} unreliable={reliability.get('unreliable', 0)} "
        f"uncertain={reliability.get('uncertain', 0)} errors={counts['validation_errors']} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
