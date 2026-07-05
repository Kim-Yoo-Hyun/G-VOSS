#!/usr/bin/env python3
"""Fill human-field sheets with a Codex proxy pending user review."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_independent_label_fill as fill_base


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_COLLECTION_DIR = RGA_ROOT / "independent_support_vertical_v2_human_label_path_decision_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending"

REVIEWER_ID = "(codex_proxy_user_review_pending)"
REVIEW_ROUND = "1"
LABEL_SOURCE = "codex_proxy_human_fields_user_review_pending"

HUMAN_FIELDS = [
    "human_reviewer_id",
    "human_review_round",
    "endpoint_identity_human",
    "pair_evaluability_human",
    "geometry_validity_human",
    "relation_reliability_human",
    "primary_reason_human",
    "uncertainty_reason_human",
    "label_notes_human",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-dir", type=Path, default=DEFAULT_COLLECTION_DIR)
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


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fill_human_row(row: dict[str, str]) -> dict[str, str]:
    endpoint = fill_base.endpoint_identity(row)
    geometry, primary_reason, reason_note = fill_base.geometry_decision(row)
    reliability, uncertainty = fill_base.reliability_decision(endpoint, geometry, primary_reason)
    evaluability = fill_base.pair_evaluability(row, endpoint, geometry)
    output = dict(row)
    output.update(
        {
            "human_reviewer_id": REVIEWER_ID,
            "human_review_round": REVIEW_ROUND,
            "endpoint_identity_human": endpoint,
            "pair_evaluability_human": evaluability,
            "geometry_validity_human": geometry,
            "relation_reliability_human": reliability,
            "primary_reason_human": primary_reason,
            "uncertainty_reason_human": uncertainty,
            "label_notes_human": f"codex proxy pending user review; {reason_note}",
        }
    )
    return output


def validate_rows(rows: list[dict[str, str]], schema: dict[str, Any], batch_name: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = schema["allowed_review_values"]
    required = schema["required_completion_fields"]
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id")
        for field in required:
            value = str(row.get(field) or "")
            if not value:
                errors.append({"batch": batch_name, "row_number": row_number, "blind_review_id": blind_id, "error_type": "missing_required_field", "field": field})
                continue
            if field in allowed and value not in set(allowed[field]):
                errors.append(
                    {
                        "batch": batch_name,
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "error_type": "invalid_value",
                        "field": field,
                        "value": value,
                    }
                )
    return errors


def labels_jsonl_rows(rows: list[dict[str, str]], batch_name: str) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    for row in rows:
        labels.append(
            {
                "schema_version": "h002_support_vertical_human_field_proxy_label_v1",
                "batch_name": batch_name,
                "blind_review_id": row["blind_review_id"],
                "scan_id": row.get("scan_id"),
                "scene_context_id": row.get("scene_context_id"),
                "subject_id": row.get("subject_id"),
                "subject_label": row.get("subject_label"),
                "predicate_label": row.get("predicate_label"),
                "predicate_family": row.get("predicate_family"),
                "object_id": row.get("object_id"),
                "object_label": row.get("object_label"),
                "label_source": LABEL_SOURCE,
                "actual_human_reviewer": False,
                "user_review_pending": True,
                "treat_as_human_confirmed_by_user_request": True,
                "paper_evidence_allowed_before_user_confirmation": False,
                "human_fields": {field: row.get(field) for field in HUMAN_FIELDS},
                "boundary": {
                    "split": "train_only",
                    "validation_usage": False,
                    "test_usage": False,
                    "trains_new_posterior": False,
                    "multi_view_as_model_input": False,
                    "filled_by_codex_proxy": True,
                    "requires_user_confirmation": True,
                },
            }
        )
    return labels


def batch_counts(rows: list[dict[str, str]]) -> dict[str, Any]:
    relation = Counter(row["relation_reliability_human"] for row in rows)
    geometry = Counter(row["geometry_validity_human"] for row in rows)
    return {
        "rows": len(rows),
        "by_family": dict(sorted(Counter(row["predicate_family"] for row in rows).items())),
        "by_predicate": dict(sorted(Counter(row["predicate_label"] for row in rows).items())),
        "relation_reliability_human": dict(sorted(relation.items())),
        "geometry_validity_human": dict(sorted(geometry.items())),
        "relation_binary": relation["reliable"] + relation["unreliable"],
        "relation_positive": relation["reliable"],
        "relation_negative": relation["unreliable"],
        "relation_uncertain": relation["uncertain"],
        "geometry_binary": geometry["supports_predicate"] + geometry["contradicts_predicate"],
        "geometry_positive": geometry["supports_predicate"],
        "geometry_negative": geometry["contradicts_predicate"],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Human Field Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage fill.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Fields are filled by Codex proxy at user request and remain user-review-pending.",
        "- They may be treated as human-confirmed only after user review/acceptance.",
        "- Paper evidence is not allowed before user confirmation.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Batch | Rows | Binary | Pos | Neg | Uncertain | Errors |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in ["minimum", "full"]:
        counts = summary["counts"][name]
        lines.append(
            f"| `{name}` | {counts['rows']} | {counts['relation_binary']} | "
            f"{counts['relation_positive']} | {counts['relation_negative']} | "
            f"{counts['relation_uncertain']} | {summary['validation_errors_by_batch'][name]} |"
        )
    lines.extend(
        [
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    collection_dir = as_abs(args.collection_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    schema = read_json(collection_dir / "human_collection_schema.json")
    minimum_fieldnames, minimum_source_rows = read_tsv(collection_dir / "minimum_human_collection_sheet.tsv")
    full_fieldnames, full_source_rows = read_tsv(collection_dir / "full_human_collection_sheet.tsv")

    minimum_rows = [fill_human_row(row) for row in minimum_source_rows]
    full_rows = [fill_human_row(row) for row in full_source_rows]
    minimum_errors = validate_rows(minimum_rows, schema, "minimum")
    full_errors = validate_rows(full_rows, schema, "full")
    errors = minimum_errors + full_errors

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "completed_minimum_sheet": output_dir / "completed_minimum_human_collection_sheet_codex_proxy_user_review_pending.tsv",
        "completed_full_sheet": output_dir / "completed_full_human_collection_sheet_codex_proxy_user_review_pending.tsv",
        "minimum_labels": output_dir / "minimum_human_proxy_labels.jsonl",
        "full_labels": output_dir / "full_human_proxy_labels.jsonl",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
    }

    if errors:
        status = "full_train_independent_support_vertical_v2_human_fields_fill_errors"
        decision = "Fix proxy-filled human field validation errors before ingestion."
        next_todo = "fix_full_train_independent_support_vertical_v2_human_field_fill_errors"
    else:
        status = "full_train_independent_support_vertical_v2_human_fields_filled_codex_proxy_user_review_pending"
        decision = (
            "Human fields are filled by Codex proxy at user request. Proceed only as a user-review-pending "
            "hypothesis artifact; paper-facing human-confirmed status requires user acceptance."
        )
        next_todo = "full_train_independent_support_vertical_v2_human_label_ingestion"

    summary = {
        "schema_version": "h002_support_vertical_v2_human_label_fill_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "input_paths": {
            "human_collection_schema": rel_path(collection_dir / "human_collection_schema.json"),
            "minimum_blank_sheet": rel_path(collection_dir / "minimum_human_collection_sheet.tsv"),
            "full_blank_sheet": rel_path(collection_dir / "full_human_collection_sheet.tsv"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "label_source": LABEL_SOURCE,
            "filled_by_codex_proxy": True,
            "actual_human_reviewer": False,
            "user_review_pending": True,
            "treat_as_human_confirmed_by_user_request": True,
            "paper_evidence_allowed_before_user_confirmation": False,
            "multi_view_as_model_input": False,
        },
        "counts": {
            "minimum": batch_counts(minimum_rows),
            "full": batch_counts(full_rows),
        },
        "validation_errors": len(errors),
        "validation_errors_by_batch": {
            "minimum": len(minimum_errors),
            "full": len(full_errors),
        },
        "next_todo": next_todo,
    }

    write_tsv(output_paths["completed_minimum_sheet"], minimum_fieldnames, minimum_rows)
    write_tsv(output_paths["completed_full_sheet"], full_fieldnames, full_rows)
    write_jsonl(output_paths["minimum_labels"], labels_jsonl_rows(minimum_rows, "minimum"))
    write_jsonl(output_paths["full_labels"], labels_jsonl_rows(full_rows, "full"))
    write_jsonl(output_paths["fill_validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    minimum = summary["counts"]["minimum"]
    full = summary["counts"]["full"]
    print(
        f"status={summary['status']} min_rows={minimum['rows']} "
        f"min_binary={minimum['relation_binary']} min_pos={minimum['relation_positive']} "
        f"min_neg={minimum['relation_negative']} full_rows={full['rows']} "
        f"full_binary={full['relation_binary']} full_pos={full['relation_positive']} "
        f"full_neg={full['relation_negative']} errors={summary['validation_errors']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
