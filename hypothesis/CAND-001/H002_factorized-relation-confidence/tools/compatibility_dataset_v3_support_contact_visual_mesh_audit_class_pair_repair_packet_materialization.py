#!/usr/bin/env python3
"""Materialize packets for class-pair controlled support/contact repair candidates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization as base


H2_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SOURCE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion"
)
DEFAULT_SCAN_ROOT = base.REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization"
)

EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_class_pair_repair_ready_for_packet_materialization"
)
EXPECTED_SOURCE_NEXT = (
    "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization_ready_for_label_fill"
)
STATUS_PARTIAL = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization_partial_needs_gap_audit"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization_errors"
)
SELECTED_PATH_READY = "class_pair_repair_packet_assets_materialized_visible_sheet_ready_for_label_fill"
SELECTED_PATH_PARTIAL = "class_pair_repair_packet_assets_materialized_partial_gap_audit_required"
NEXT_READY = "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill"
NEXT_PARTIAL = "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_gap_audit"

TARGET_ROWS = 480


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def validate_inputs(
    summary: dict[str, Any],
    visible_rows: list[dict[str, str]],
    hidden_rows: list[dict[str, Any]],
    packet_sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append(
            {
                "error_type": "unexpected_source_status",
                "actual": summary.get("status"),
                "expected": EXPECTED_SOURCE_STATUS,
            }
        )
    if summary.get("next_todo") != EXPECTED_SOURCE_NEXT:
        errors.append(
            {
                "error_type": "unexpected_source_next_todo",
                "actual": summary.get("next_todo"),
                "expected": EXPECTED_SOURCE_NEXT,
            }
        )
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_validation_errors_present", "actual": summary.get("validation_errors")})
    if len(visible_rows) != TARGET_ROWS:
        errors.append({"error_type": "visible_row_count_mismatch", "actual": len(visible_rows), "expected": TARGET_ROWS})
    if len(hidden_rows) != TARGET_ROWS:
        errors.append({"error_type": "hidden_row_count_mismatch", "actual": len(hidden_rows), "expected": TARGET_ROWS})
    if len(packet_sources) != TARGET_ROWS:
        errors.append({"error_type": "packet_source_count_mismatch", "actual": len(packet_sources), "expected": TARGET_ROWS})
    visible_ids = {row["review_id"] for row in visible_rows}
    hidden_ids = {row["review_id"] for row in hidden_rows}
    packet_ids = {row["review_id"] for row in packet_sources}
    if visible_ids != hidden_ids or visible_ids != packet_ids:
        errors.append({"error_type": "review_id_set_mismatch"})
    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "source_boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("repair_proxy_is_sampling_only") is not True:
        errors.append(
            {
                "error_type": "repair_proxy_boundary_not_true",
                "actual": boundary.get("repair_proxy_is_sampling_only"),
            }
        )
    if boundary.get("final_target_requires_visible_packet_label_fill") is not True:
        errors.append(
            {
                "error_type": "label_fill_boundary_not_true",
                "actual": boundary.get("final_target_requires_visible_packet_label_fill"),
            }
        )
    return errors


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Packet Materialization",
            "",
            "## Result",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Packet Counts",
            "",
            "```json",
            json.dumps(summary["counts"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Repair Candidate Boundary",
            "",
            "The packets come from the class-pair controlled repair candidate set. `repair_proxy_kind` remains hidden and sampling-only. This step does not fill labels, train a model, run learned smoke, use validation/test rows, or modify H001 artifacts.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    source_summary = base.read_json(args.source_dir / "summary.json")
    visible_input = base.read_csv(args.source_dir / "label_sheet_template.csv")
    hidden_input = base.read_jsonl(args.source_dir / "hidden_manifest.jsonl")
    packet_sources = base.read_jsonl(args.source_dir / "packet_source_manifest.jsonl")
    validation_errors = validate_inputs(source_summary, visible_input, hidden_input, packet_sources)

    hidden_by_id = {row["review_id"]: row for row in hidden_input}
    source_by_id = {row["review_id"]: row for row in packet_sources}

    visible_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    for visible_template in visible_input:
        review_id = visible_template["review_id"]
        packet_dir = output_dir / "packets" / review_id
        visible, hidden = base.materialize_packet(
            visible_template,
            hidden_by_id[review_id],
            source_by_id[review_id],
            packet_dir,
            args.scan_root,
        )
        visible_rows.append(visible)
        hidden_rows.append(hidden)

    visible_leakage_hits = base.leakage_scan_visible_rows(visible_rows)
    for packet_md in output_dir.glob("packets/*/packet.md"):
        visible_leakage_hits.extend(base.leakage_scan_text(packet_md))

    status_counts = Counter(row["packet_status_hidden"] for row in hidden_rows)
    predicate_status_counts = Counter(f"{row['predicate_label']}|{row['packet_status_hidden']}" for row in hidden_rows)
    proxy_status_counts = Counter(f"{row['repair_proxy_kind']}|{row['packet_status_hidden']}" for row in hidden_rows)
    non_ready = [row for row in hidden_rows if row["packet_status_hidden"] != "ready"]
    label_ready = [row for row in hidden_rows if row["packet_status_hidden"] == "ready"]

    if visible_leakage_hits:
        validation_errors.append({"error_type": "visible_leakage_hits_present", "count": len(visible_leakage_hits)})
    if len(visible_rows) != TARGET_ROWS:
        validation_errors.append({"error_type": "materialized_visible_count_mismatch", "actual": len(visible_rows)})
    if len(hidden_rows) != TARGET_ROWS:
        validation_errors.append({"error_type": "materialized_hidden_count_mismatch", "actual": len(hidden_rows)})

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "class_pair_repair_packet_materialization_errors"
        next_todo = "repair_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization"
    elif non_ready:
        status = STATUS_PARTIAL
        selected_path = SELECTED_PATH_PARTIAL
        next_todo = NEXT_PARTIAL
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH_READY
        next_todo = NEXT_READY

    output_paths = {
        "label_ready_manifest": output_dir / "label_ready_manifest.jsonl",
        "materialized_hidden_manifest": output_dir / "materialized_hidden_manifest.jsonl",
        "non_ready_packet_rows": output_dir / "non_ready_packet_rows.jsonl",
        "packet_manifest": output_dir / "packet_manifest.jsonl",
        "report": output_dir / "report.md",
        "summary": output_dir / "summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "visible_review_sheet_with_packets": output_dir / "visible_review_sheet_with_packets.csv",
    }

    counts = {
        "packet_rows": len(hidden_rows),
        "packet_status_counts": dict(status_counts),
        "predicate_status_counts": dict(sorted(predicate_status_counts.items())),
        "proxy_status_counts": dict(sorted(proxy_status_counts.items())),
        "label_ready_rows": len(label_ready),
        "non_ready_rows": len(non_ready),
        "subject_image_rows": sum(1 for row in hidden_rows if row["subject_image_count_hidden"] > 0),
        "object_image_rows": sum(1 for row in hidden_rows if row["object_image_count_hidden"] > 0),
        "pair_crop_rows": sum(1 for row in hidden_rows if row["pair_crop_ready_hidden"]),
        "mesh_render_rows": sum(1 for row in hidden_rows if row["mesh_render_ready_hidden"]),
        "multiview_sheet_rows": sum(1 for row in hidden_rows if row["multiview_sheet_ready_hidden"]),
        "total_subject_images": sum(row["subject_image_count_hidden"] for row in hidden_rows),
        "total_object_images": sum(row["object_image_count_hidden"] for row in hidden_rows),
        "visible_leakage_hits": len(visible_leakage_hits),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "source_path_decision_status": source_summary.get("status"),
        "source_selected_candidate_summary": source_summary.get("selected_candidate_summary"),
        "counts": counts,
        "boundary": {
            "split": "train full only",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_packet_assets": True,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "repair_proxy_is_sampling_only": True,
            "final_target_requires_visible_packet_label_fill": True,
            "multi_view_or_mesh_as_audit_evidence": True,
            "multi_view_or_mesh_as_model_input": False,
        },
        "output_paths": {key: base.rel_path(path) for key, path in output_paths.items()},
    }

    base.write_csv(output_paths["visible_review_sheet_with_packets"], visible_rows, base.VISIBLE_FIELDS)
    base.write_jsonl(output_paths["packet_manifest"], visible_rows)
    base.write_jsonl(output_paths["materialized_hidden_manifest"], hidden_rows)
    base.write_jsonl(output_paths["label_ready_manifest"], label_ready)
    base.write_jsonl(output_paths["non_ready_packet_rows"], non_ready)
    base.write_jsonl(output_paths["visible_leakage_hits"], visible_leakage_hits)
    base.write_jsonl(output_paths["validation_errors"], validation_errors)
    base.write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status != STATUS_ERROR else 1


if __name__ == "__main__":
    raise SystemExit(main())
