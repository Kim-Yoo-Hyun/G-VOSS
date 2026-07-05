#!/usr/bin/env python3
"""Fill H002 proximity LH-only labels using reviewer-visible fields only."""

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

DEFAULT_READINESS_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_label_readiness"
DEFAULT_READINESS_SUMMARY = DEFAULT_READINESS_DIR / "summary.json"
DEFAULT_INPUT_SHEET = DEFAULT_READINESS_DIR / "label_ready_sheet.tsv"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_label_fill"

SCHEMA_VERSION = "h002_reliability_target_v12_proximity_lh_only_label_fill_v1"
EXPECTED_READINESS_STATUS = "h002_reliability_target_v12_proximity_lh_only_label_readiness_ready"
EXPECTED_NEXT_TODO = "reliability_target_v12_proximity_lh_only_label_fill"
STATUS_READY = "h002_reliability_target_v12_proximity_lh_only_label_filled_codex_proxy_visible_only"
STATUS_ERROR = "h002_reliability_target_v12_proximity_lh_only_label_fill_errors"
NEXT_TODO = "reliability_target_v12_proximity_lh_only_label_ingestion"

REVIEWER_ID = "codex_proxy_v12_visible_only_user_requested"
REVIEW_ROUND = "1"
LABEL_POLICY = "v12_visible_pair_semantics_conservative"

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "review_question",
    "relation_reliability_state_v12",
    "primary_reason_v12",
    "uncertainty_reason_v12",
    "review_notes_v12",
]
FILLED_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "review_question",
    "reviewer_id_v12",
    "review_round_v12",
    "label_policy_v12",
    "relation_reliability_state_v12",
    "primary_reason_v12",
    "uncertainty_reason_v12",
    "review_notes_v12",
]

ALLOWED_REVIEW_VALUES = {
    "relation_reliability_state_v12": {
        "accept_reliable_close_by",
        "reject_unreliable_close_by",
        "abstain_uncertain",
    },
    "primary_reason_v12": {
        "meaningful_spatial_relation",
        "dense_proximity_noise",
        "possible_missing_annotation",
        "alternative_relation_better",
        "endpoint_or_label_ambiguous",
        "trivial_or_redundant",
        "insufficient_evidence",
        "other",
    },
    "uncertainty_reason_v12": {
        "",
        "insufficient_context",
        "endpoint_ambiguity",
        "close_by_definition_ambiguous",
        "dense_scene_ambiguity",
        "other",
    },
}

FORBIDDEN_INPUT_FIELDS = {
    "machine_hint",
    "label_match_status",
    "rank_band",
    "scan_id",
    "semantic_rank",
    "semantic_score",
    "p_geom",
    "source_queue",
    "subject_object_label_pair",
    "endpoint_cell",
    "exact_endpoint",
    "hidden",
}

GENERIC_LABELS = {"item", "items", "object", "objects", "thing", "things", "stuff", "unknown"}
SEATING = {"chair", "armchair", "bench", "stool", "sofa", "couch", "ottoman"}
TABLES = {"table", "desk", "dining table", "coffee table", "couch table", "side table", "nightstand"}
PLANTS = {"plant", "plants"}
BATHROOM = {"toilet", "sink", "bathtub", "shower", "towel"}
LIGHTING = {"lamp", "floor lamp", "table lamp"}
BED_AREA = {"bed", "nightstand", "side table"}
STORAGE = {"shelf", "cabinet", "kitchen cabinet", "wardrobe", "rack", "commode", "tv stand", "organizer"}
SMALL_PORTABLE = {"box", "clothes", "towel", "pillow", "book", "books", "blanket", "bag", "basket"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-summary", type=Path, default=DEFAULT_READINESS_SUMMARY)
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


def validate_inputs(readiness: dict[str, Any], fieldnames: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if readiness.get("status") != EXPECTED_READINESS_STATUS:
        errors.append({"error_type": "unexpected_readiness_status", "expected": EXPECTED_READINESS_STATUS, "actual": readiness.get("status")})
    if readiness.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_readiness_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": readiness.get("next_todo")})
    boundary = readiness.get("boundary", {})
    if boundary.get("label_fill_allowed_next") is not True:
        errors.append({"error_type": "readiness_does_not_allow_label_fill", "actual": boundary.get("label_fill_allowed_next")})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "paper_evidence_allowed", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "readiness_boundary_violation", "key": key, "actual": boundary.get(key)})

    expected_rows = readiness.get("counts", {}).get("rows")
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
        for field in ["relation_reliability_state_v12", "primary_reason_v12", "uncertainty_reason_v12", "review_notes_v12"]:
            if str(row.get(field, "")).strip():
                errors.append({"error_type": "review_field_already_filled", "row_number": row_number, "blind_review_id": blind_id, "field": field})
        if row.get("predicate_label") != "close by":
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "blind_review_id": blind_id, "predicate": row.get("predicate_label")})
    return errors


def unordered_pair(a: str, b: str) -> frozenset[str]:
    return frozenset((a, b))


def is_seating_table_pair(a: str, b: str) -> bool:
    return (a in SEATING and b in TABLES) or (b in SEATING and a in TABLES)


def is_decor_pair(a: str, b: str) -> bool:
    furniture = SEATING | TABLES | {"cabinet", "shelf", "desk"}
    return (a in PLANTS and b in furniture) or (b in PLANTS and a in furniture)


def is_bathroom_pair(a: str, b: str) -> bool:
    pair = unordered_pair(a, b)
    return pair in {
        unordered_pair("toilet", "sink"),
        unordered_pair("bathtub", "towel"),
        unordered_pair("sink", "towel"),
        unordered_pair("shower", "towel"),
    }


def is_bed_area_pair(a: str, b: str) -> bool:
    pair = unordered_pair(a, b)
    return pair in {
        unordered_pair("bed", "nightstand"),
        unordered_pair("bed", "side table"),
        unordered_pair("bed", "lamp"),
    }


def is_lighting_pair(a: str, b: str) -> bool:
    furniture = SEATING | TABLES | {"bed"}
    return (a in LIGHTING and b in furniture) or (b in LIGHTING and a in furniture)


def is_alternative_relation_pair(a: str, b: str) -> bool:
    return (a in STORAGE and b in SMALL_PORTABLE) or (b in STORAGE and a in SMALL_PORTABLE)


def label_row(row: dict[str, str]) -> dict[str, str]:
    subject = norm(row.get("subject_label"))
    obj = norm(row.get("object_label"))

    if not subject or not obj or subject in GENERIC_LABELS or obj in GENERIC_LABELS:
        return {
            "relation_reliability_state_v12": "abstain_uncertain",
            "primary_reason_v12": "endpoint_or_label_ambiguous",
            "uncertainty_reason_v12": "endpoint_ambiguity",
            "review_notes_v12": "visible-only proxy: endpoint label is missing, generic, or ambiguous",
        }

    if subject == obj:
        return {
            "relation_reliability_state_v12": "reject_unreliable_close_by",
            "primary_reason_v12": "dense_proximity_noise",
            "uncertainty_reason_v12": "",
            "review_notes_v12": "visible-only proxy: same-label object pair is likely dense proximity rather than an informative relation",
        }

    if is_alternative_relation_pair(subject, obj):
        return {
            "relation_reliability_state_v12": "reject_unreliable_close_by",
            "primary_reason_v12": "alternative_relation_better",
            "uncertainty_reason_v12": "",
            "review_notes_v12": "visible-only proxy: object-storage pair likely needs containment/support rather than close-by",
        }

    if is_seating_table_pair(subject, obj) or is_decor_pair(subject, obj) or is_bathroom_pair(subject, obj) or is_bed_area_pair(subject, obj) or is_lighting_pair(subject, obj):
        return {
            "relation_reliability_state_v12": "accept_reliable_close_by",
            "primary_reason_v12": "meaningful_spatial_relation",
            "uncertainty_reason_v12": "",
            "review_notes_v12": "visible-only proxy: object types form a plausible nontrivial close-by relation",
        }

    return {
        "relation_reliability_state_v12": "abstain_uncertain",
        "primary_reason_v12": "insufficient_evidence",
        "uncertainty_reason_v12": "insufficient_context",
        "review_notes_v12": "visible-only proxy: text labels alone are insufficient to decide close-by reliability",
    }


def fill_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    filled: list[dict[str, str]] = []
    decisions: list[dict[str, Any]] = []
    for row in rows:
        decision = label_row(row)
        filled_row = {key: row.get(key, "") for key in VISIBLE_FIELDS}
        filled_row.update(
            {
                "reviewer_id_v12": REVIEWER_ID,
                "review_round_v12": REVIEW_ROUND,
                "label_policy_v12": LABEL_POLICY,
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
                **decision,
                "reviewer_id_v12": REVIEWER_ID,
                "label_policy_v12": LABEL_POLICY,
            }
        )
    return filled, decisions


def validate_outputs(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        for field, allowed in ALLOWED_REVIEW_VALUES.items():
            value = row.get(field, "")
            if value not in allowed:
                errors.append({"error_type": "invalid_review_value", "row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "value": value})
        if row.get("reviewer_id_v12") != REVIEWER_ID:
            errors.append({"error_type": "missing_reviewer_id", "row_number": row_number, "blind_review_id": row.get("blind_review_id")})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V12 Proximity LH-Only Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Result",
        "",
        "Filled the proximity LH-only visible sheet with Codex proxy labels using only reviewer-visible fields.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"relation_reliability_state_v12 = {counts['relation_reliability_state_v12']}",
        f"primary_reason_v12 = {counts['primary_reason_v12']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Label Policy",
        "",
        "`accept` is used only for visible object pairs that form a plausible nontrivial close-by relation. Same-label pairs are rejected as dense proximity noise. Storage/object pairs are rejected when a containment/support relation is likely more appropriate. Remaining rows abstain because text-only evidence is insufficient.",
        "",
        "Hidden audit metadata was not read or used during fill.",
        "",
        "## Boundary",
        "",
        "This is a hypothesis-stage proxy label fill, not paper evidence and not posterior evidence.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    readiness_path = as_abs(args.readiness_summary)
    input_sheet = as_abs(args.input_sheet)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    readiness = read_json(readiness_path)
    fieldnames, input_rows = read_tsv(input_sheet)
    validation_errors = validate_inputs(readiness, fieldnames, input_rows)
    filled_rows, decision_rows = fill_rows(input_rows)
    validation_errors.extend(validate_outputs(filled_rows))

    label_counts = Counter(row["relation_reliability_state_v12"] for row in filled_rows)
    reason_counts = Counter(row["primary_reason_v12"] for row in filled_rows)
    uncertainty_counts = Counter(row["uncertainty_reason_v12"] for row in filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "filled_label_sheet": output_dir / "filled_label_sheet.tsv",
        "label_decisions": output_dir / "label_decisions.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    status = STATUS_READY if not validation_errors else STATUS_ERROR
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "readiness_summary": rel_path(readiness_path),
            "input_sheet": rel_path(input_sheet),
            "hidden_manifest_read": False,
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "reviewer_id": REVIEWER_ID,
        "label_policy": LABEL_POLICY,
        "counts": {
            "rows": len(filled_rows),
            "relation_reliability_state_v12": dict(label_counts),
            "primary_reason_v12": dict(reason_counts),
            "uncertainty_reason_v12": dict(uncertainty_counts),
            "binary_usable_rows": int(label_counts.get("accept_reliable_close_by", 0) + label_counts.get("reject_unreliable_close_by", 0)),
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
    print(f"labels={summary['counts']['relation_reliability_state_v12']}")
    print(f"binary_usable_rows={summary['counts']['binary_usable_rows']}")
    print(f"hidden_manifest_read={summary['boundary']['hidden_audit_manifest_read']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
