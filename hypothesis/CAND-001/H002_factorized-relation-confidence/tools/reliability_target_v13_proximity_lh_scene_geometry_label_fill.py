#!/usr/bin/env python3
"""Fill H002 v13 proximity LH labels using reviewer-visible scene/geometry fields only."""

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

DEFAULT_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_candidate_mining"
DEFAULT_CANDIDATE_SUMMARY = DEFAULT_CANDIDATE_DIR / "summary.json"
DEFAULT_INPUT_SHEET = DEFAULT_CANDIDATE_DIR / "label_ready_sheet_v13.tsv"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_label_fill"

SCHEMA_VERSION = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_fill_v1"
EXPECTED_CANDIDATE_STATUS = "h002_reliability_target_v13_proximity_lh_scene_geometry_candidate_mining_ready_for_label_fill"
EXPECTED_NEXT_TODO = "reliability_target_v13_proximity_lh_scene_geometry_label_fill"
STATUS_READY = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_filled_codex_proxy_visible_only"
STATUS_ERROR = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_fill_errors"
NEXT_TODO = "reliability_target_v13_proximity_lh_scene_geometry_label_ingestion"

REVIEWER_ID = "codex_proxy_v13_scene_geometry_visible_only_user_requested"
REVIEW_ROUND = "1"
LABEL_POLICY = "v13_visible_scene_geometry_conservative"

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "scene_context_summary_v13",
    "geometry_witness_summary_v13",
    "nearest_neighbor_context_v13",
    "local_density_context_v13",
    "duplicate_or_many_alternatives_context_v13",
    "crop_or_layout_evidence_v13",
    "review_question_v13",
    "relation_reliability_state_v13",
    "scene_usefulness_state_v13",
    "primary_reason_v13",
    "uncertainty_reason_v13",
    "review_notes_v13",
]

FILLED_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "scene_context_summary_v13",
    "geometry_witness_summary_v13",
    "nearest_neighbor_context_v13",
    "local_density_context_v13",
    "duplicate_or_many_alternatives_context_v13",
    "crop_or_layout_evidence_v13",
    "review_question_v13",
    "reviewer_id_v13",
    "review_round_v13",
    "label_policy_v13",
    "relation_reliability_state_v13",
    "scene_usefulness_state_v13",
    "primary_reason_v13",
    "uncertainty_reason_v13",
    "review_notes_v13",
]

ALLOWED_VALUES = {
    "relation_reliability_state_v13": {
        "accept_reliable_close_by",
        "reject_dense_relation_noise",
        "reject_trivial_or_context_only",
        "abstain_uncertain",
    },
    "scene_usefulness_state_v13": {
        "useful_local_relation",
        "redundant_dense_neighborhood",
        "trivial_global_context",
        "not_evaluable",
    },
    "primary_reason_v13": {
        "mutual_nearest_or_functional_neighbor",
        "clear_local_adjacency",
        "many_equally_near_alternatives",
        "duplicate_object_ambiguity",
        "structural_or_room_context_only",
        "geometry_evidence_insufficient",
        "visual_or_layout_evidence_insufficient",
    },
    "uncertainty_reason_v13": {
        "none",
        "missing_layout_context",
        "occlusion_or_crop_gap",
        "ambiguous_dense_cluster",
        "object_identity_uncertain",
        "relation_definition_uncertain",
    },
}

FORBIDDEN_INPUT_FIELDS = {
    "machine_hint",
    "label_match_status",
    "rank_band",
    "scan_id",
    "subgraph_id",
    "prediction_id",
    "semantic_rank",
    "semantic_score",
    "p_geom",
    "source_queue",
    "target_construction",
    "hidden",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def extract_after(text: str, marker: str) -> str:
    text = norm(text)
    marker = norm(marker)
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split(";", 1)[0].strip()


def parse_visible_cues(row: dict[str, str]) -> dict[str, str]:
    return {
        "distance": extract_after(row.get("geometry_witness_summary_v13", ""), "distance="),
        "overlap": extract_after(row.get("geometry_witness_summary_v13", ""), "footprint_overlap="),
        "vertical": extract_after(row.get("geometry_witness_summary_v13", ""), "vertical_offset="),
        "neighbor_tier": extract_after(row.get("nearest_neighbor_context_v13", ""), "subject-side geometry-neighbor tier:"),
        "subgraph_density": extract_after(row.get("local_density_context_v13", ""), "subgraph proximity density="),
        "subject_density": extract_after(row.get("local_density_context_v13", ""), "subject candidate density="),
        "object_density": extract_after(row.get("local_density_context_v13", ""), "object candidate density="),
        "same_pair_density": extract_after(row.get("duplicate_or_many_alternatives_context_v13", ""), "same visible pair in local subgraph="),
        "same_object_alternatives": extract_after(row.get("duplicate_or_many_alternatives_context_v13", ""), "same object-label alternatives for subject="),
        "same_subject_alternatives": extract_after(row.get("duplicate_or_many_alternatives_context_v13", ""), "same subject-label alternatives for object="),
    }


def label_row(row: dict[str, str]) -> dict[str, str]:
    cues = parse_visible_cues(row)
    dense_context = cues["subgraph_density"] in {"dense", "very_dense"}
    many_same_pair = cues["same_pair_density"] in {"dense", "very_dense"}
    many_alternatives = cues["same_object_alternatives"] in {"moderate", "dense", "very_dense"} or cues["same_subject_alternatives"] in {"moderate", "dense", "very_dense"}
    front_or_single = cues["neighbor_tier"] in {"front_tier", "single_candidate"}
    middle_or_front = cues["neighbor_tier"] in {"front_tier", "middle_tier", "single_candidate"}
    close_geometry = cues["distance"] in {"tight_xy", "near_xy"}
    moderate_geometry = cues["distance"] == "moderate_xy"
    strong_overlap = cues["overlap"] in {"high_footprint_overlap", "medium_footprint_overlap"}
    weak_geometry = cues["distance"] == "broad_xy" and cues["overlap"] in {"little_or_no_footprint_overlap", "low_footprint_overlap"}
    large_vertical_broad = cues["distance"] == "broad_xy" and cues["vertical"] == "large_height_offset"

    if close_geometry and strong_overlap and front_or_single and not many_same_pair and not dense_context:
        return {
            "relation_reliability_state_v13": "accept_reliable_close_by",
            "scene_usefulness_state_v13": "useful_local_relation",
            "primary_reason_v13": "mutual_nearest_or_functional_neighbor",
            "uncertainty_reason_v13": "none",
            "review_notes_v13": "codex v13 visible-only: close/overlapping geometry with front-tier local-neighbor evidence and limited duplicate alternatives",
        }

    if (close_geometry or moderate_geometry) and strong_overlap and middle_or_front and not many_alternatives:
        return {
            "relation_reliability_state_v13": "accept_reliable_close_by",
            "scene_usefulness_state_v13": "useful_local_relation",
            "primary_reason_v13": "clear_local_adjacency",
            "uncertainty_reason_v13": "none",
            "review_notes_v13": "codex v13 visible-only: local geometry supports a useful close-by relation without strong duplicate-neighborhood evidence",
        }

    if dense_context and (many_same_pair or many_alternatives) and (cues["neighbor_tier"] == "tail_tier" or weak_geometry):
        return {
            "relation_reliability_state_v13": "reject_dense_relation_noise",
            "scene_usefulness_state_v13": "redundant_dense_neighborhood",
            "primary_reason_v13": "many_equally_near_alternatives",
            "uncertainty_reason_v13": "none",
            "review_notes_v13": "codex v13 visible-only: dense local neighborhood and duplicate/alternative evidence make this close-by edge redundant",
        }

    if many_same_pair and many_alternatives:
        return {
            "relation_reliability_state_v13": "reject_dense_relation_noise",
            "scene_usefulness_state_v13": "redundant_dense_neighborhood",
            "primary_reason_v13": "duplicate_object_ambiguity",
            "uncertainty_reason_v13": "none",
            "review_notes_v13": "codex v13 visible-only: same-pair or same-label alternatives dominate the local context",
        }

    if weak_geometry and large_vertical_broad:
        return {
            "relation_reliability_state_v13": "reject_trivial_or_context_only",
            "scene_usefulness_state_v13": "trivial_global_context",
            "primary_reason_v13": "geometry_evidence_insufficient",
            "uncertainty_reason_v13": "none",
            "review_notes_v13": "codex v13 visible-only: broad XY distance, weak overlap, and large height offset do not support a useful local close-by edge",
        }

    if weak_geometry and cues["neighbor_tier"] == "tail_tier":
        return {
            "relation_reliability_state_v13": "reject_dense_relation_noise",
            "scene_usefulness_state_v13": "redundant_dense_neighborhood",
            "primary_reason_v13": "many_equally_near_alternatives",
            "uncertainty_reason_v13": "none",
            "review_notes_v13": "codex v13 visible-only: tail-tier neighbor with broad/weak geometry is likely dense proximity noise",
        }

    return {
        "relation_reliability_state_v13": "abstain_uncertain",
        "scene_usefulness_state_v13": "not_evaluable",
        "primary_reason_v13": "visual_or_layout_evidence_insufficient",
        "uncertainty_reason_v13": "ambiguous_dense_cluster" if dense_context or many_alternatives else "relation_definition_uncertain",
        "review_notes_v13": "codex v13 visible-only: visible scene/geometry cues are mixed or insufficient for a reliable binary decision",
    }


def validate_inputs(candidate_summary: dict[str, Any], fieldnames: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if candidate_summary.get("status") != EXPECTED_CANDIDATE_STATUS:
        errors.append({"error_type": "unexpected_candidate_status", "expected": EXPECTED_CANDIDATE_STATUS, "actual": candidate_summary.get("status")})
    if candidate_summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_candidate_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": candidate_summary.get("next_todo")})
    if candidate_summary.get("validation_errors") != 0:
        errors.append({"error_type": "candidate_validation_errors_present", "actual": candidate_summary.get("validation_errors")})
    boundary = candidate_summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "paper_evidence_allowed", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "candidate_boundary_violation", "key": key, "actual": boundary.get(key)})
    expected_rows = candidate_summary.get("counts", {}).get("selected_rows")
    if expected_rows != len(rows):
        errors.append({"error_type": "row_count_mismatch", "expected": expected_rows, "actual": len(rows)})
    if fieldnames != VISIBLE_FIELDS:
        errors.append({"error_type": "visible_columns_mismatch", "expected": VISIBLE_FIELDS, "actual": fieldnames})
    for field in fieldnames:
        lower = field.lower()
        for token in FORBIDDEN_INPUT_FIELDS:
            if token in lower:
                errors.append({"error_type": "forbidden_visible_input_field", "field": field, "token": token})
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        if not blind_id:
            errors.append({"error_type": "missing_blind_review_id", "row_number": row_number})
        if blind_id in seen_ids:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id})
        seen_ids.add(blind_id)
        for field in ["relation_reliability_state_v13", "scene_usefulness_state_v13", "primary_reason_v13", "uncertainty_reason_v13", "review_notes_v13"]:
            if str(row.get(field, "")).strip():
                errors.append({"error_type": "review_field_already_filled", "row_number": row_number, "blind_review_id": blind_id, "field": field})
        if row.get("predicate_label") != "close by":
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "blind_review_id": blind_id, "predicate": row.get("predicate_label")})
    return errors


def fill_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    filled: list[dict[str, str]] = []
    decisions: list[dict[str, Any]] = []
    for row in rows:
        decision = label_row(row)
        filled_row = {key: row.get(key, "") for key in VISIBLE_FIELDS}
        filled_row.update(
            {
                "reviewer_id_v13": REVIEWER_ID,
                "review_round_v13": REVIEW_ROUND,
                "label_policy_v13": LABEL_POLICY,
                **decision,
            }
        )
        filled.append(filled_row)
        decisions.append(
            {
                "blind_review_id": row.get("blind_review_id"),
                "candidate_relation": row.get("candidate_relation"),
                "subject_label": row.get("subject_label"),
                "predicate_label": row.get("predicate_label"),
                "object_label": row.get("object_label"),
                **parse_visible_cues(row),
                **decision,
                "reviewer_id_v13": REVIEWER_ID,
                "label_policy_v13": LABEL_POLICY,
            }
        )
    return filled, decisions


def validate_outputs(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        for field, allowed in ALLOWED_VALUES.items():
            value = row.get(field, "")
            if value not in allowed:
                errors.append({"error_type": "invalid_review_value", "row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "value": value})
        if row.get("reviewer_id_v13") != REVIEWER_ID:
            errors.append({"error_type": "missing_reviewer_id", "row_number": row_number, "blind_review_id": row.get("blind_review_id")})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V13 Proximity Scene/Geometry Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Result",
        "",
        "Filled the v13 proximity scene/geometry label sheet with Codex proxy labels using only reviewer-visible fields.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"relation_reliability_state_v13 = {counts['relation_reliability_state_v13']}",
        f"scene_usefulness_state_v13 = {counts['scene_usefulness_state_v13']}",
        f"binary_usable_rows = {counts['binary_usable_rows']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Label Policy",
        "",
        "`accept` is used only when visible evidence shows close/overlapping geometry, front or middle local-neighbor tier, and limited duplicate alternatives. Dense neighborhoods, duplicate alternatives, broad/tail geometry, and weak overlap are rejected or abstained. Hidden audit metadata was not read or used during fill.",
        "",
        "## Boundary",
        "",
        "This is a hypothesis-stage proxy label fill. It is not paper evidence and not posterior evidence.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    candidate_summary_path = as_abs(args.candidate_summary)
    input_sheet = as_abs(args.input_sheet)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_summary = read_json(candidate_summary_path)
    fieldnames, input_rows = read_tsv(input_sheet)
    validation_errors = validate_inputs(candidate_summary, fieldnames, input_rows)
    filled_rows, decision_rows = fill_rows(input_rows)
    validation_errors.extend(validate_outputs(filled_rows))

    label_counts = Counter(row["relation_reliability_state_v13"] for row in filled_rows)
    usefulness_counts = Counter(row["scene_usefulness_state_v13"] for row in filled_rows)
    reason_counts = Counter(row["primary_reason_v13"] for row in filled_rows)
    uncertainty_counts = Counter(row["uncertainty_reason_v13"] for row in filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "filled_label_sheet": output_dir / "filled_label_sheet_v13.tsv",
        "label_decisions": output_dir / "label_decisions_v13.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    status = STATUS_READY if not validation_errors else STATUS_ERROR
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "candidate_summary": rel_path(candidate_summary_path),
            "input_sheet": rel_path(input_sheet),
            "hidden_manifest_read": False,
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "reviewer_id": REVIEWER_ID,
        "review_round": REVIEW_ROUND,
        "label_policy": LABEL_POLICY,
        "counts": {
            "rows": len(filled_rows),
            "relation_reliability_state_v13": dict(label_counts),
            "scene_usefulness_state_v13": dict(usefulness_counts),
            "primary_reason_v13": dict(reason_counts),
            "uncertainty_reason_v13": dict(uncertainty_counts),
            "binary_usable_rows": int(
                label_counts.get("accept_reliable_close_by", 0)
                + label_counts.get("reject_dense_relation_noise", 0)
                + label_counts.get("reject_trivial_or_context_only", 0)
            ),
            "positive_rows": int(label_counts.get("accept_reliable_close_by", 0)),
            "negative_rows": int(label_counts.get("reject_dense_relation_noise", 0) + label_counts.get("reject_trivial_or_context_only", 0)),
            "abstain_rows": int(label_counts.get("abstain_uncertain", 0)),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": True,
            "visible_only_label_fill": True,
            "hidden_audit_manifest_read": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_tsv(output_paths["filled_label_sheet"], filled_rows, FILLED_FIELDS)
    write_jsonl(output_paths["label_decisions"], decision_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"labels={summary['counts']['relation_reliability_state_v13']}")
    print(f"binary_usable_rows={summary['counts']['binary_usable_rows']}")
    print(f"hidden_manifest_read={summary['boundary']['hidden_audit_manifest_read']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
