#!/usr/bin/env python3
"""Formal leakage review for H002 v19 materialized attachment audit packets."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_MATERIALIZATION_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review"

EXPECTED_MATERIALIZATION_STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization_ready_for_leakage_review"
EXPECTED_MATERIALIZATION_NEXT = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review"

STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review_passed_ready_for_label_fill"
NEXT_TODO = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_fill"

VISIBLE_FIELDS = [
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
    "review_uncertainty",
    "review_notes",
]
REVIEW_FIELDS = [
    "review_relation_reliability",
    "review_geometry_support",
    "review_uncertainty",
    "review_notes",
]
FORBIDDEN_COLUMNS = [
    "scan_id",
    "subgraph_id",
    "source_id",
    "subject_id",
    "object_id",
    "cell_id_hidden",
    "sampling_queue_hidden",
    "geometry_status_hidden",
    "rank_band_hidden",
    "semantic_rank_hidden",
    "semantic_score_norm_hidden",
    "machine_hint_hidden",
    "label_match_status_hidden",
    "matched_predicates_hidden",
    "raw_features_hidden",
    "relation_reliability_state_v18",
    "relation_reliability_binary_target",
    "geometry_support_state_v18",
    "geometry_support_binary_target",
    "relation_usefulness_state_v18",
    "relation_usefulness_binary_target",
    "primary_reason_v18",
    "review_notes_v18",
    "reviewer_id_v18",
    "label_source",
]
FORBIDDEN_TEXT_PATTERNS = [
    r"local_dataset",
    r"3RScan",
    r"scan_id",
    r"subgraph_id",
    r"subject_id",
    r"object_id",
    r"instance_\d+",
    r"_hidden",
    r"geometry_status",
    r"rank_band",
    r"semantic_rank",
    r"semantic_score",
    r"machine_hint",
    r"raw_features",
    r"label_source",
    r"cell_id",
    r"sampling_queue",
    r"p_geom_valid",
    r"RGA-HL",
    r"RGA-LH",
    r"accept_reliable_attachment",
    r"reject_unreliable_attachment",
    r"abstain_uncertain",
    r"diagnostic_connected_possible",
    r"diagnostic_connected_ambiguous",
    r"state_v18",
    r"reason_v18",
    r"review_notes_v18",
    r"reviewer_id_v18",
    r"binary_target",
]
UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)
IMAGE_NAME_RE = re.compile(r"^(subject|object)_(crop|view)_[0-9]{2}\.(jpg|jpeg|png)$", re.IGNORECASE)
PACKET_ID_RE = re.compile(r"^apv19_[0-9]{4}_attv18_[0-9a-f]{12}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization-dir", type=Path, default=DEFAULT_MATERIALIZATION_DIR)
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
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", encoding="utf-8", newline="") as handle:
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


def text_leakage_hits(text: str, source: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if UUID_RE.search(text):
        hits.append({"source": source, "hit_type": "uuid_like_scan_id", "pattern": "uuid"})
    for pattern in FORBIDDEN_TEXT_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append({"source": source, "hit_type": "forbidden_text_pattern", "pattern": pattern})
    return hits


def validate_materialization_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append(
            {
                "error_type": "unexpected_materialization_status",
                "expected": EXPECTED_MATERIALIZATION_STATUS,
                "actual": summary.get("status"),
            }
        )
    if summary.get("next_todo") != EXPECTED_MATERIALIZATION_NEXT:
        errors.append(
            {
                "error_type": "unexpected_materialization_next",
                "expected": EXPECTED_MATERIALIZATION_NEXT,
                "actual": summary.get("next_todo"),
            }
        )
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "materialization_validation_errors_present", "actual": summary.get("validation_errors")})
    counts = summary.get("counts", {})
    expected_counts = {
        "visible_review_rows": 240,
        "packet_dirs": 240,
        "materialized_hidden_manifest_rows": 240,
        "visible_leakage_hits": 0,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            errors.append({"error_type": "unexpected_materialization_count", "key": key, "expected": expected, "actual": counts.get(key)})
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})
    return errors


def validate_visible_sheet(header: list[str], rows: list[dict[str, str]], source: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    hits: list[dict[str, Any]] = []
    if header != VISIBLE_FIELDS:
        errors.append({"error_type": "visible_header_mismatch", "expected": VISIBLE_FIELDS, "actual": header})
    forbidden_columns = sorted(set(header) & set(FORBIDDEN_COLUMNS))
    if forbidden_columns:
        hits.append({"source": source, "hit_type": "forbidden_visible_columns", "columns": forbidden_columns})
    if len(rows) != 240:
        errors.append({"error_type": "unexpected_visible_sheet_rows", "expected": 240, "actual": len(rows)})
    packet_ids = []
    for row_idx, row in enumerate(rows):
        packet_id = row.get("packet_id", "")
        packet_ids.append(packet_id)
        if not PACKET_ID_RE.match(packet_id):
            errors.append({"error_type": "unexpected_packet_id_format", "row_idx": row_idx, "packet_id": packet_id})
        for field in REVIEW_FIELDS:
            if row.get(field, "") != "":
                errors.append({"error_type": "review_field_not_blank", "row_idx": row_idx, "packet_id": packet_id, "field": field})
        row_text = "\t".join(row.get(field, "") for field in header)
        hits.extend(text_leakage_hits(row_text, f"{source}:row:{row_idx}"))
    if len(set(packet_ids)) != len(packet_ids):
        errors.append({"error_type": "duplicate_visible_packet_id", "duplicates": [pid for pid, count in Counter(packet_ids).items() if count > 1][:20]})
    return errors, hits


def validate_packet_files(packet_index: list[dict[str, Any]], materialization_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    errors: list[dict[str, Any]] = []
    hits: list[dict[str, Any]] = []
    counts = Counter()
    if len(packet_index) != 240:
        errors.append({"error_type": "unexpected_packet_index_rows", "expected": 240, "actual": len(packet_index)})
    for row in packet_index:
        packet_id = row.get("packet_id", "")
        if not PACKET_ID_RE.match(packet_id):
            errors.append({"error_type": "unexpected_packet_id_format", "packet_id": packet_id})
        packet_dir = as_abs(Path(row.get("packet_dir", "")))
        packet_md = as_abs(Path(row.get("packet_markdown", "")))
        if not packet_dir.is_dir():
            errors.append({"error_type": "packet_dir_missing", "packet_id": packet_id, "packet_dir": rel_path(packet_dir)})
            continue
        if not packet_md.is_file():
            errors.append({"error_type": "packet_markdown_missing", "packet_id": packet_id, "packet_markdown": rel_path(packet_md)})
        else:
            text = packet_md.read_text(encoding="utf-8")
            hits.extend(text_leakage_hits(text, rel_path(packet_md)))
            counts["packet_markdown_files"] += 1
        image_dir = packet_dir / "images"
        if not image_dir.is_dir():
            errors.append({"error_type": "image_dir_missing", "packet_id": packet_id, "image_dir": rel_path(image_dir)})
            continue
        image_files = sorted(path for path in image_dir.iterdir() if path.is_file())
        if not image_files:
            errors.append({"error_type": "packet_has_no_images", "packet_id": packet_id})
        for image_path in image_files:
            counts["image_files"] += 1
            if not IMAGE_NAME_RE.match(image_path.name):
                hits.append(
                    {
                        "source": rel_path(image_path),
                        "hit_type": "non_neutral_image_filename",
                        "filename": image_path.name,
                    }
                )
            # Check only basename, not artifact path, because visible markdown sees only basename.
            hits.extend(text_leakage_hits(image_path.name, f"{packet_id}:image_name:{image_path.name}"))
        # packet dirs can contain only packet.md and images/.
        allowed = {"packet.md", "images"}
        unexpected = sorted(child.name for child in packet_dir.iterdir() if child.name not in allowed)
        if unexpected:
            errors.append({"error_type": "unexpected_packet_dir_entries", "packet_id": packet_id, "entries": unexpected})
    return errors, hits, dict(counts)


def validate_hidden_manifest(hidden_rows: list[dict[str, Any]], visible_packet_ids: set[str]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(hidden_rows) != 240:
        errors.append({"error_type": "unexpected_hidden_manifest_rows", "expected": 240, "actual": len(hidden_rows)})
    hidden_ids = {row.get("packet_id") for row in hidden_rows}
    if hidden_ids != visible_packet_ids:
        errors.append(
            {
                "error_type": "visible_hidden_packet_id_mismatch",
                "visible_only": sorted(visible_packet_ids - hidden_ids)[:20],
                "hidden_only": sorted(hidden_ids - visible_packet_ids)[:20],
            }
        )
    rows_with_source_paths = 0
    rows_with_scan_ids = 0
    for row in hidden_rows:
        if row.get("scan_id_hidden") and UUID_RE.match(str(row.get("scan_id_hidden"))):
            rows_with_scan_ids += 1
        copied_assets = row.get("copied_assets_hidden", [])
        if copied_assets and all(asset.get("source_path_hidden") for asset in copied_assets):
            rows_with_source_paths += 1
        if row.get("model_input_allowed_now") is not False:
            errors.append({"error_type": "hidden_model_input_allowed_unexpected", "packet_id": row.get("packet_id"), "actual": row.get("model_input_allowed_now")})
    if rows_with_source_paths != 240:
        errors.append({"error_type": "hidden_manifest_source_paths_incomplete", "expected": 240, "actual": rows_with_source_paths})
    if rows_with_scan_ids != 240:
        errors.append({"error_type": "hidden_manifest_scan_ids_incomplete", "expected": 240, "actual": rows_with_scan_ids})
    return errors


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    return f"""# H002 V19 Attachment Audit Packet Leakage Review

Created at: `{summary['created_at']}`

## Status

```text
status = {summary['status']}
next_todo = {summary['next_todo']}
validation_errors = {summary['validation_errors']}
visible_leakage_hits = {counts['visible_leakage_hits']}
formal_leakage_review_pass = {counts['formal_leakage_review_pass']}
posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}
multi_view_as_model_input = {summary['boundary']['multi_view_as_model_input']}
```

## Reviewed Surface

```text
visible_sheet_rows = {counts['visible_sheet_rows']}
packet_markdown_files = {counts['packet_markdown_files']}
packet_dirs = {counts['packet_dirs']}
neutral_image_files = {counts['neutral_image_files']}
hidden_manifest_rows = {counts['hidden_manifest_rows']}
hidden_rows_with_source_paths = {counts['hidden_rows_with_source_paths']}
hidden_rows_with_scan_ids = {counts['hidden_rows_with_scan_ids']}
```

## Decision

The formal leakage review passes. Visible sheet, packet markdown, and packet-local image
filenames do not expose source paths, scan/subgraph identifiers, instance ids, construction
metadata, old labels, or old review notes. The hidden manifest retains the original source paths
and scan/instance identifiers for provenance and materialization only.

This is still not a label-fill stage and not posterior evidence.
"""


def main() -> int:
    args = parse_args()
    materialization_dir = as_abs(args.materialization_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = read_json(materialization_dir / "summary.json")
    header, visible_rows = read_tsv(materialization_dir / "visible_review_sheet.tsv")
    packet_index = read_jsonl(materialization_dir / "packet_index.jsonl")
    hidden_rows = read_jsonl(materialization_dir / "materialized_hidden_manifest.jsonl")

    validation_errors = validate_materialization_summary(summary)
    visible_errors, visible_hits = validate_visible_sheet(header, visible_rows, rel_path(materialization_dir / "visible_review_sheet.tsv"))
    validation_errors.extend(visible_errors)
    packet_errors, packet_hits, packet_counts = validate_packet_files(packet_index, materialization_dir)
    validation_errors.extend(packet_errors)
    hidden_errors = validate_hidden_manifest(hidden_rows, {row.get("packet_id", "") for row in visible_rows})
    validation_errors.extend(hidden_errors)

    leakage_hits = visible_hits + packet_hits
    counts = {
        "visible_sheet_rows": len(visible_rows),
        "packet_dirs": len(packet_index),
        "packet_markdown_files": packet_counts.get("packet_markdown_files", 0),
        "neutral_image_files": packet_counts.get("image_files", 0),
        "hidden_manifest_rows": len(hidden_rows),
        "hidden_rows_with_source_paths": sum(1 for row in hidden_rows if row.get("copied_assets_hidden") and all(asset.get("source_path_hidden") for asset in row.get("copied_assets_hidden", []))),
        "hidden_rows_with_scan_ids": sum(1 for row in hidden_rows if row.get("scan_id_hidden") and UUID_RE.match(str(row.get("scan_id_hidden")))),
        "visible_leakage_hits": len(leakage_hits),
        "formal_leakage_review_pass": len(leakage_hits) == 0 and len(validation_errors) == 0,
    }
    if not counts["formal_leakage_review_pass"]:
        status = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review_blocked"
        next_todo = "repair_audit_packet_visible_leakage"
    else:
        status = STATUS
        next_todo = NEXT_TODO

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "reviewed_visible_fields": output_dir / "reviewed_visible_fields.json",
    }
    output_summary = {
        "schema_version": "h002_reliability_target_v19_attachment_audit_packet_leakage_review_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "input_paths": {
            "materialization_summary": rel_path(materialization_dir / "summary.json"),
            "visible_review_sheet": rel_path(materialization_dir / "visible_review_sheet.tsv"),
            "packet_index": rel_path(materialization_dir / "packet_index.jsonl"),
            "materialized_hidden_manifest": rel_path(materialization_dir / "materialized_hidden_manifest.jsonl"),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "candidate_mining_allowed": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_as_audit_or_confirmation_evidence_only": True,
            "mesh_as_audit_or_confirmation_evidence_only": True,
            "old_labels_visible": False,
            "construction_metadata_visible": False,
        },
        "counts": counts,
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], output_summary)
    write_json(output_paths["reviewed_visible_fields"], {"visible_fields": header, "forbidden_columns": FORBIDDEN_COLUMNS, "forbidden_text_patterns": FORBIDDEN_TEXT_PATTERNS})
    write_jsonl(output_paths["visible_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(report_text(output_summary), encoding="utf-8")

    print(f"status={status}")
    print(f"next={next_todo}")
    print(f"visible_sheet_rows={counts['visible_sheet_rows']}")
    print(f"packet_markdown_files={counts['packet_markdown_files']}")
    print(f"neutral_image_files={counts['neutral_image_files']}")
    print(f"hidden_manifest_rows={counts['hidden_manifest_rows']}")
    print(f"visible_leakage_hits={counts['visible_leakage_hits']}")
    print(f"validation_errors={len(validation_errors)}")
    return 0 if counts["formal_leakage_review_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
