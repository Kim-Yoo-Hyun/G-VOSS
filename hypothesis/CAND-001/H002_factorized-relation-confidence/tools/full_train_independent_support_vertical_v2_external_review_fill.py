#!/usr/bin/env python3
"""Fill the external evidence review sheet as a user-requested Codex proxy."""

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

DEFAULT_PROTOCOL_DIR = RGA_ROOT / "independent_support_vertical_v2_external_review_protocol"
DEFAULT_INPUT_SHEET = DEFAULT_PROTOCOL_DIR / "external_evidence_review_sheet.tsv"
DEFAULT_SCHEMA = DEFAULT_PROTOCOL_DIR / "external_review_schema.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_external_review_fill_codex_proxy_user_requested"

REVIEWER_ID = "(codex_proxy_user_requested_as_user_review)"

ROOM_STRUCTURE = {
    "floor",
    "wall",
    "ceiling",
    "door",
    "doorframe",
    "window",
    "blinds",
    "curtain",
    "shower curtain",
}

SUPPORT_SURFACES = {
    "floor",
    "wall",
    "desk",
    "table",
    "bed",
    "chair",
    "armchair",
    "wardrobe",
    "shelf",
    "cabinet",
    "bath cabinet",
    "sink",
    "tv stand",
    "couch table",
    "commode",
    "counter",
}

WALL_ATTACHMENT_LIKE = {
    "mirror",
    "frame",
    "towel",
    "toilet paper",
    "shower curtain",
    "curtain",
    "blinds",
}

VERTICAL_RANK = {
    "floor": 0,
    "scale": 1,
    "trash can": 1,
    "garbage": 1,
    "toilet brush": 1,
    "shoe rack": 1,
    "chair": 2,
    "armchair": 2,
    "toilet": 2,
    "commode": 2,
    "bath cabinet": 2,
    "desk": 2,
    "table": 2,
    "bed": 2,
    "couch table": 2,
    "tv stand": 2,
    "counter": 2,
    "sink": 3,
    "kitchen cabinet": 3,
    "wardrobe": 3,
    "pillow": 3,
    "cushion": 3,
    "blanket": 3,
    "books": 3,
    "book": 3,
    "item": 3,
    "box": 3,
    "laundry basket": 3,
    "backpack": 3,
    "clothes": 3,
    "monitor": 3,
    "plant": 3,
    "shelf": 4,
    "mirror": 4,
    "window": 4,
    "door": 4,
    "doorframe": 4,
    "wall": 5,
    "ceiling": 6,
}


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


def packet_paths_exist(row: dict[str, str]) -> bool:
    for key in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
        value = row.get(key)
        if not value or not as_abs(Path(value)).exists():
            return False
    return True


def is_room_structure(label: str) -> bool:
    return label.strip().lower() in ROOM_STRUCTURE


def vertical_answer(predicate: str, subject: str, obj: str) -> tuple[str, str, str, str]:
    subject_l = subject.lower()
    object_l = obj.lower()
    pred_l = predicate.lower()
    subj_rank = VERTICAL_RANK.get(subject_l)
    obj_rank = VERTICAL_RANK.get(object_l)

    if subj_rank is None or obj_rank is None:
        return "uncertain", "uncertain", "uncertain", "ambiguous_relation"

    supports = (pred_l == "higher than" and subj_rank > obj_rank) or (pred_l == "lower than" and subj_rank < obj_rank)
    contradicts = (pred_l == "higher than" and subj_rank < obj_rank) or (pred_l == "lower than" and subj_rank > obj_rank)

    if supports and (is_room_structure(subject_l) or is_room_structure(object_l)):
        return "supports_predicate", "supports_predicate", "trivial_dense_or_room_structure", "trivial_dense_relation"
    if supports:
        return "supports_predicate", "supports_predicate", "informative", "none"
    if contradicts:
        return "contradicts_predicate", "contradicts_predicate", "ontology_mismatch", "ontology_mismatch"
    return "uncertain", "uncertain", "uncertain", "ambiguous_relation"


def support_answer(predicate: str, subject: str, obj: str) -> tuple[str, str, str, str]:
    subject_l = subject.lower()
    object_l = obj.lower()
    pred_l = predicate.lower()

    if subject_l == object_l:
        return "uncertain", "uncertain", "uncertain", "ambiguous_relation"

    if object_l == "wall" and subject_l in WALL_ATTACHMENT_LIKE and pred_l in {"supported by", "lying on"}:
        return "supports_predicate", "supports_predicate", "informative", "none"

    if object_l in SUPPORT_SURFACES:
        if is_room_structure(subject_l) or is_room_structure(object_l):
            return "supports_predicate", "supports_predicate", "trivial_dense_or_room_structure", "trivial_dense_relation"
        if pred_l in {"standing on", "lying on", "supported by"}:
            return "supports_predicate", "supports_predicate", "informative", "none"

    if subject_l in ROOM_STRUCTURE and object_l not in ROOM_STRUCTURE:
        return "contradicts_predicate", "contradicts_predicate", "ontology_mismatch", "ontology_mismatch"

    return "uncertain", "uncertain", "uncertain", "ambiguous_relation"


def fill_row(row: dict[str, str]) -> dict[str, Any]:
    filled = dict(row)
    family = row["predicate_family"]
    subject = row["subject_label"]
    obj = row["object_label"]
    predicate = row["predicate_label"]
    packet_ready = packet_paths_exist(row)
    packet_caveat = row.get("evidence_packet_status") != "ready"

    if family == "relative_vertical":
        visual_answer, mesh_answer, informativeness, uncertainty = vertical_answer(predicate, subject, obj)
    elif family == "support_contact":
        visual_answer, mesh_answer, informativeness, uncertainty = support_answer(predicate, subject, obj)
    else:
        visual_answer, mesh_answer, informativeness, uncertainty = "uncertain", "uncertain", "uncertain", "ambiguous_relation"

    if not packet_ready:
        visual_eval = "missing_views"
        mesh_eval = "missing_mesh"
        visual_answer = "not_applicable"
        mesh_answer = "not_applicable"
        informativeness = "uncertain"
        final = "uncertain"
        uncertainty = "insufficient_evidence"
    elif packet_caveat and visual_answer == "uncertain":
        visual_eval = "occluded_or_unclear"
        mesh_eval = "unclear"
        final = "uncertain"
        uncertainty = "insufficient_evidence"
    else:
        visual_eval = "evaluable" if not packet_caveat else "occluded_or_unclear"
        mesh_eval = "evaluable" if not packet_caveat else "unclear"
        if visual_answer == "supports_predicate" and mesh_answer == "supports_predicate" and informativeness == "informative":
            final = "reliable"
            uncertainty = "none"
        elif visual_answer == "uncertain" or mesh_answer == "uncertain":
            final = "uncertain"
            if uncertainty == "none":
                uncertainty = "ambiguous_relation"
        else:
            final = "unreliable"

    filled.update(
        {
            "external_reviewer_id": REVIEWER_ID,
            "external_review_round": "1",
            "endpoint_identity_external": "both_valid",
            "visual_pair_evaluability_external": visual_eval,
            "mesh_pair_evaluability_external": mesh_eval,
            "visual_geometry_answer_external": visual_answer,
            "mesh_geometry_answer_external": mesh_answer,
            "relation_informativeness_external": informativeness,
            "final_relation_reliability_external": final,
            "uncertainty_reason_external": uncertainty,
            "external_label_notes": (
                "codex proxy filled at user request; uses only labeler-visible identity fields "
                "and packet availability, with packet evidence reserved for user review"
            ),
        }
    )
    return filled


def validate_rows(rows: list[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = schema["allowed_review_values"]
    completion_fields = schema["completion_fields"]
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id")
        for field in completion_fields:
            value = row.get(field)
            if value is None or value == "":
                errors.append({"row_number": row_number, "blind_review_id": blind_id, "field": field, "error_type": "missing_completion_field"})
            elif field in allowed and value not in set(allowed[field]):
                errors.append({"row_number": row_number, "blind_review_id": blind_id, "field": field, "value": value, "error_type": "invalid_completion_value"})
    return errors


def label_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_support_vertical_v2_external_proxy_label_v1",
        "blind_review_id": row["blind_review_id"],
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
            "filled_by": "codex_proxy",
            "user_requested_treat_as_user_review": True,
            "actual_user_reviewer": False,
            "user_review_pending": True,
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
    lines = [
        "# H002 External Review Fill",
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
        "- Filled by Codex proxy at user request and treated as user review for workflow progression.",
        "- Not paper-level external human evidence before user confirmation.",
        "- Does not read hidden manifest, numeric witness values, previous proxy labels, source score/rank, or `p_geom_valid`.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {summary['counts']['rows']} |",
        f"| reliable | {summary['counts']['final_relation_reliability_external'].get('reliable', 0)} |",
        f"| unreliable | {summary['counts']['final_relation_reliability_external'].get('unreliable', 0)} |",
        f"| uncertain | {summary['counts']['final_relation_reliability_external'].get('uncertain', 0)} |",
        f"| validation errors | {summary['counts']['validation_errors']} |",
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
    errors = validate_rows(filled_rows, schema)
    label_rows = [label_record(row) for row in filled_rows]

    reliability_counts = Counter(row["final_relation_reliability_external"] for row in filled_rows)
    geometry_counts = Counter(row["visual_geometry_answer_external"] for row in filled_rows)
    family_counts = Counter(row["predicate_family"] for row in filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "completed_sheet": output_dir / "completed_external_evidence_review_sheet_codex_proxy_user_requested.tsv",
        "external_proxy_labels": output_dir / "external_proxy_labels.jsonl",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
    }

    status = "full_train_independent_support_vertical_v2_external_review_filled_codex_proxy_user_requested"
    if errors:
        status = "full_train_independent_support_vertical_v2_external_review_fill_errors"

    summary = {
        "schema_version": "h002_support_vertical_v2_external_review_fill_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": "Filled external evidence review fields as a user-requested Codex proxy; ingest and audit before any posterior smoke.",
        "input_paths": {
            "external_evidence_review_sheet": rel_path(input_sheet),
            "external_review_schema": rel_path(schema_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "filled_by": "codex_proxy",
            "user_requested_treat_as_user_review": True,
            "actual_user_reviewer": False,
            "user_review_pending": True,
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
            "visual_geometry_answer_external": dict(sorted(geometry_counts.items())),
            "final_relation_reliability_external": dict(sorted(reliability_counts.items())),
        },
        "next_todo": "external_evidence_review_label_ingestion",
    }

    write_tsv(output_paths["completed_sheet"], filled_rows, fieldnames)
    write_jsonl(output_paths["external_proxy_labels"], label_rows)
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
