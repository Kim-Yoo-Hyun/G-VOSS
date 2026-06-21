#!/usr/bin/env python3
"""Fill the rank-band true-user review sheet as a Codex proxy pending confirmation."""

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

DEFAULT_REVIEW_DIR = RGA_ROOT / "independent_support_vertical_v2_true_user_review_path"
DEFAULT_INPUT_SHEET = DEFAULT_REVIEW_DIR / "true_user_review_sheet_rank_band70.tsv"
DEFAULT_SCHEMA = DEFAULT_REVIEW_DIR / "true_user_review_schema.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_true_user_review_fill_rank_band70_codex_proxy_pending_confirmation"

REVIEWER_ID = "(codex_proxy_true_user_review_pending_confirmation)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
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
        "codex proxy filled for true-user rank-band workflow; pending real user confirmation; "
        "used only labeler-visible identity fields and packet availability"
    )
    return filled


def label_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_support_vertical_v2_true_user_rank_band70_proxy_label_v1",
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
        "true_user_review_fields": {
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
            "actual_true_user_reviewer": False,
            "workflow_treat_as_user_review_for_next_hypothesis_steps": True,
            "user_confirmation_pending": True,
            "paper_evidence_allowed_before_user_confirmation": False,
            "used_hidden_manifest": False,
            "used_numeric_witness_values": False,
            "used_previous_proxy_labels": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "validation_usage": False,
            "test_usage": False,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    reliability = counts["final_relation_reliability_external"]
    lines = [
        "# H002 True User Review Fill",
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
        "- Filled by Codex proxy for workflow progression, pending real user confirmation.",
        "- Not true user/external annotation and not paper evidence before user confirmation.",
        "- Does not read hidden manifest, numeric witness values, previous proxy labels, source score/rank, or `p_geom_valid`.",
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
    filled_rows = [fill_row(row) for row in rows]
    errors = visible_fill.validate_rows(filled_rows, schema)
    label_rows = [label_record(row) for row in filled_rows]

    reliability_counts = Counter(row["final_relation_reliability_external"] for row in filled_rows)
    geometry_counts = Counter(row["visual_geometry_answer_external"] for row in filled_rows)
    family_counts = Counter(row["predicate_family"] for row in filled_rows)
    packet_counts = Counter(row["evidence_packet_status"] for row in filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "completed_sheet": output_dir / "completed_true_user_review_sheet_rank_band70_codex_proxy_pending_confirmation.tsv",
        "true_user_proxy_labels": output_dir / "true_user_proxy_labels_rank_band70.jsonl",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
    }

    status = "full_train_independent_support_vertical_v2_true_user_review_rank_band70_filled_codex_proxy_pending_confirmation"
    if errors:
        status = "full_train_independent_support_vertical_v2_true_user_review_rank_band70_fill_errors"

    summary = {
        "schema_version": "h002_support_vertical_v2_true_user_review_fill_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": "Rank-band true-user sheet filled by Codex proxy for workflow progression; requires real user confirmation before method evidence.",
        "input_paths": {
            "true_user_review_sheet_rank_band70": rel_path(input_sheet),
            "true_user_review_schema": rel_path(schema_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "filled_by": "codex_proxy",
            "actual_true_user_reviewer": False,
            "workflow_treat_as_user_review_for_next_hypothesis_steps": True,
            "user_confirmation_pending": True,
            "paper_evidence_allowed_before_user_confirmation": False,
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
            "by_packet_status": dict(sorted(packet_counts.items())),
            "visual_geometry_answer_external": dict(sorted(geometry_counts.items())),
            "final_relation_reliability_external": dict(sorted(reliability_counts.items())),
        },
        "next_todo": "true_user_review_rank_band70_label_ingestion",
    }

    write_tsv(output_paths["completed_sheet"], filled_rows, fieldnames)
    write_jsonl(output_paths["true_user_proxy_labels"], label_rows)
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
        f"reliable={reliability.get('reliable', 0)} "
        f"unreliable={reliability.get('unreliable', 0)} "
        f"uncertain={reliability.get('uncertain', 0)} "
        f"errors={counts['validation_errors']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
