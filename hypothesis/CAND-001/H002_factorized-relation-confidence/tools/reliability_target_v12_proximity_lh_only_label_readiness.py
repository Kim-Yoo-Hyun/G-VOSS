#!/usr/bin/env python3
"""Prepare H002 proximity LH-only label readiness artifacts."""

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

DEFAULT_PATH_DECISION_DIR = RGA_ROOT / "reliability_target_v10_proximity_lh_only_path_decision"
DEFAULT_PREVIEW_CANDIDATES = RGA_ROOT / "reliability_target_v10_proximity_relation_family_feasibility_scan/preview_candidates.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_label_readiness"

EXPECTED_PATH_STATUS = "h002_reliability_target_v10_proximity_lh_path_decision_select_lh_only_label_readiness"
EXPECTED_NEXT_TODO = "reliability_target_v12_proximity_lh_only_label_readiness"
NEXT_TODO = "reliability_target_v12_proximity_lh_only_label_fill"

SCHEMA_VERSION = "h002_reliability_target_v12_proximity_lh_only_label_readiness_v1"

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

REVIEW_FIELDS = [
    "relation_reliability_state_v12",
    "primary_reason_v12",
    "uncertainty_reason_v12",
    "review_notes_v12",
]

ALLOWED_REVIEW_VALUES = {
    "relation_reliability_state_v12": [
        "accept_reliable_close_by",
        "reject_unreliable_close_by",
        "abstain_uncertain",
    ],
    "primary_reason_v12": [
        "",
        "meaningful_spatial_relation",
        "dense_proximity_noise",
        "possible_missing_annotation",
        "alternative_relation_better",
        "endpoint_or_label_ambiguous",
        "trivial_or_redundant",
        "insufficient_evidence",
        "other",
    ],
    "uncertainty_reason_v12": [
        "",
        "insufficient_context",
        "endpoint_ambiguity",
        "close_by_definition_ambiguous",
        "dense_scene_ambiguity",
        "other",
    ],
}

FORBIDDEN_VISIBLE_TOKENS = [
    "bucket",
    "endpoint_cell",
    "exact_endpoint",
    "geometry_status",
    "hidden",
    "label_geometry",
    "label_match",
    "machine_hint",
    "p_geom",
    "rank_band",
    "scan_id",
    "semantic_rank",
    "semantic_score",
    "source_queue",
    "subject_object_label_pair",
]

REQUIRED_PREVIEW_FIELDS = [
    "blind_review_id",
    "prediction_id",
    "split",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_label",
    "source_queue_hidden",
    "label_match_status_hidden",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
    parser.add_argument("--preview-candidates", type=Path, default=DEFAULT_PREVIEW_CANDIDATES)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


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
    return str(value or "").strip()


def validate_path_decision(path_decision: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_decision.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_decision_status", "expected": EXPECTED_PATH_STATUS, "actual": path_decision.get("status")})
    if path_decision.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_path_decision_next_todo", "actual": path_decision.get("next_todo")})
    boundary = path_decision.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "label_fill_allowed",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "path_decision_boundary_violation", "key": key, "actual": boundary.get(key)})
    if boundary.get("label_readiness_allowed") is not True:
        errors.append({"error_type": "label_readiness_not_allowed", "actual": boundary.get("label_readiness_allowed")})
    return errors


def validate_preview_rows(rows: list[dict[str, Any]], expected_count: int | None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if expected_count is not None and len(rows) != expected_count:
        errors.append({"error_type": "unexpected_preview_row_count", "expected": expected_count, "actual": len(rows)})
    seen_ids: set[str] = set()
    seen_predictions: set[str] = set()
    for index, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_PREVIEW_FIELDS if field not in row]
        if missing:
            errors.append({"error_type": "missing_preview_fields", "row_index": index, "missing": missing, "blind_review_id": row.get("blind_review_id")})
            continue
        blind_id = str(row["blind_review_id"])
        prediction_id = str(row["prediction_id"])
        if blind_id in seen_ids:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id})
        if prediction_id in seen_predictions:
            errors.append({"error_type": "duplicate_prediction_id", "prediction_id": prediction_id})
        seen_ids.add(blind_id)
        seen_predictions.add(prediction_id)
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_preview_row", "blind_review_id": blind_id, "split": row.get("split")})
        if row.get("predicate_family") != "proximity" or row.get("predicate_label") != "close by":
            errors.append({"error_type": "unexpected_relation", "blind_review_id": blind_id, "predicate_family": row.get("predicate_family"), "predicate_label": row.get("predicate_label")})
        if row.get("source_queue_hidden") != "RGA-LH":
            errors.append({"error_type": "non_lh_preview_row", "blind_review_id": blind_id, "source_queue_hidden": row.get("source_queue_hidden")})
        if row.get("label_fill_allowed") is not False or row.get("posterior_input_allowed") is not False:
            errors.append({"error_type": "input_preview_boundary_violation", "blind_review_id": blind_id})
    return errors


def relation_text(row: dict[str, Any]) -> str:
    return f"{norm(row.get('subject_label'))} close by {norm(row.get('object_label'))}"


def visible_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "blind_review_id": norm(row.get("blind_review_id")),
        "review_card": f"review_cards/{norm(row.get('blind_review_id'))}.md",
        "candidate_relation": relation_text(row),
        "subject_label": norm(row.get("subject_label")),
        "predicate_label": "close by",
        "object_label": norm(row.get("object_label")),
        "review_question": "Is this close-by relation meaningful and reliable for the subject-object pair, rather than dense proximity noise, a trivial relation, or an annotation artifact?",
        "relation_reliability_state_v12": "",
        "primary_reason_v12": "",
        "uncertainty_reason_v12": "",
        "review_notes_v12": "",
    }


def hidden_manifest_row(row: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "blind_review_id": row.get("blind_review_id"),
        "prediction_id": row.get("prediction_id"),
        "split": row.get("split"),
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "review_card": rel_path(output_dir / "review_cards" / f"{row.get('blind_review_id')}.md"),
        "source_queue_hidden": row.get("source_queue_hidden"),
        "semantic_rank_hidden": row.get("semantic_rank_hidden"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm_hidden"),
        "p_geom_valid_hidden": row.get("p_geom_valid_hidden"),
        "geometry_status_hidden": row.get("geometry_status_hidden"),
        "label_match_status_hidden": row.get("label_match_status_hidden"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket_hidden"),
        "machine_hint_hidden": row.get("machine_hint_hidden"),
        "rank_band_hidden": row.get("rank_band_hidden"),
        "subject_object_label_pair_hidden": row.get("subject_object_label_pair_hidden"),
        "endpoint_cell_hidden": row.get("endpoint_cell_hidden"),
        "exact_endpoint_pair_key_hidden": row.get("exact_endpoint_pair_key_hidden"),
        "structural_pair_hidden": row.get("structural_pair_hidden"),
        "hard_room_surface_pair_hidden": row.get("hard_room_surface_pair_hidden"),
        "generic_endpoint_pair_hidden": row.get("generic_endpoint_pair_hidden"),
        "reviewer_visible": False,
        "model_input_allowed": False,
        "posterior_input_allowed": False,
    }


def write_review_card(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "# Close-by Relation Review",
            "",
            f"Blind review id: `{row['blind_review_id']}`",
            "",
            "## Candidate",
            "",
            f"`{row['candidate_relation']}`",
            "",
            "## Question",
            "",
            row["review_question"],
            "",
            "## Labels",
            "",
            "- `accept_reliable_close_by`",
            "- `reject_unreliable_close_by`",
            "- `abstain_uncertain`",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def visible_leakage_hits(sheet_rows: list[dict[str, str]], output_dir: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in VISIBLE_FIELDS:
        lower = field.lower()
        for token in FORBIDDEN_VISIBLE_TOKENS:
            if token in lower:
                hits.append({"surface": "visible_header", "field": field, "forbidden_token": token})
    fields_to_scan = ["review_card", "candidate_relation", "review_question"]
    for row_number, row in enumerate(sheet_rows, start=2):
        for field in fields_to_scan:
            lower = str(row.get(field, "")).lower()
            for token in FORBIDDEN_VISIBLE_TOKENS:
                if token in lower:
                    hits.append(
                        {
                            "surface": "visible_value",
                            "row_number": row_number,
                            "blind_review_id": row.get("blind_review_id"),
                            "field": field,
                            "forbidden_token": token,
                            "value_preview": str(row.get(field, ""))[:120],
                        }
                    )
                    break
    for card_path in sorted((output_dir / "review_cards").glob("*.md")):
        text = card_path.read_text(encoding="utf-8", errors="replace").lower()
        for token in FORBIDDEN_VISIBLE_TOKENS:
            if token in text:
                hits.append({"surface": "review_card_text", "path": rel_path(card_path), "forbidden_token": token})
                break
    return hits


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V12 Proximity LH-Only Label Readiness",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Result",
        "",
        "Prepared a reviewer-visible label sheet for the proximity LH-only branch.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"unique_blind_review_ids = {counts['unique_blind_review_ids']}",
        f"unique_scans_hidden = {counts['unique_scans_hidden']}",
        f"unique_label_pairs_hidden = {counts['unique_label_pairs_hidden']}",
        f"label_match_status_hidden = {counts['label_match_status_hidden']}",
        f"rank_band_hidden = {counts['rank_band_hidden']}",
        f"visible_leakage_hits = {summary['visible_leakage_hits']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Visible Columns",
        "",
        "```text",
        "\n".join(summary["visible_fields"]),
        "```",
        "",
        "## Hidden Audit Fields",
        "",
        "`machine_hint`, `label_match_status`, `rank_band`, `scan_id`, `semantic_rank`, `semantic_score`, `p_geom_valid`, and object-pair shortcut keys are kept only in `hidden_audit_manifest.jsonl`.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
        "Label fill is allowed next, but posterior smoke remains blocked until label ingestion and target-independence audit pass.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_decision_dir = as_abs(args.path_decision_dir)
    preview_path = as_abs(args.preview_candidates)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_decision = read_json(path_decision_dir / "summary.json")
    preview_rows = read_jsonl(preview_path)
    expected_count = path_decision.get("selected_plan", {}).get("candidate_pool_snapshot", {}).get("preview_rows")

    validation_errors = validate_path_decision(path_decision)
    validation_errors.extend(validate_preview_rows(preview_rows, expected_count))

    sheet_rows = [visible_row(row) for row in preview_rows]
    hidden_rows = [hidden_manifest_row(row, output_dir) for row in preview_rows]
    for sheet_row in sheet_rows:
        write_review_card(output_dir / sheet_row["review_card"], sheet_row)

    leakage_hits = visible_leakage_hits(sheet_rows, output_dir)
    for hit in leakage_hits:
        validation_errors.append({"error_type": "visible_leakage_hit", **hit})

    label_match = Counter(str(row.get("label_match_status_hidden")) for row in preview_rows)
    rank_band = Counter(str(row.get("rank_band_hidden")) for row in preview_rows)
    label_pair = Counter(str(row.get("subject_object_label_pair_hidden")) for row in preview_rows)
    scan_id = Counter(str(row.get("scan_id")) for row in preview_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "label_ready_sheet": output_dir / "label_ready_sheet.tsv",
        "hidden_audit_manifest": output_dir / "hidden_audit_manifest.jsonl",
        "allowed_review_values": output_dir / "allowed_review_values.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    status = (
        "h002_reliability_target_v12_proximity_lh_only_label_readiness_ready"
        if not validation_errors
        else "h002_reliability_target_v12_proximity_lh_only_label_readiness_blocked"
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "path_decision_summary": rel_path(path_decision_dir / "summary.json"),
            "preview_candidates": rel_path(preview_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "visible_fields": VISIBLE_FIELDS,
        "review_fields": REVIEW_FIELDS,
        "allowed_review_values": ALLOWED_REVIEW_VALUES,
        "counts": {
            "rows": len(preview_rows),
            "unique_blind_review_ids": len({row.get("blind_review_id") for row in preview_rows}),
            "unique_predictions": len({row.get("prediction_id") for row in preview_rows}),
            "unique_scans_hidden": len(scan_id),
            "unique_label_pairs_hidden": len(label_pair),
            "label_match_status_hidden": dict(label_match),
            "rank_band_hidden": dict(rank_band),
            "max_rows_per_scan_hidden": max(scan_id.values() or [0]),
            "max_rows_per_label_pair_hidden": max(label_pair.values() or [0]),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "label_readiness_allowed": True,
            "label_fill_allowed_next": True,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "visible_hidden_fields": False,
        },
        "visible_leakage_hits": len(leakage_hits),
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_tsv(output_paths["label_ready_sheet"], sheet_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["hidden_audit_manifest"], hidden_rows)
    write_json(output_paths["allowed_review_values"], ALLOWED_REVIEW_VALUES)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"visible_leakage_hits={summary['visible_leakage_hits']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"label_fill_allowed_next={summary['boundary']['label_fill_allowed_next']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
