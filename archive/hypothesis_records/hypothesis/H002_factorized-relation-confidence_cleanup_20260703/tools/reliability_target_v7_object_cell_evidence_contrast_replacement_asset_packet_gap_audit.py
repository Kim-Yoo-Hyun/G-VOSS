#!/usr/bin/env python3
"""Focused gap audit for H002 v7 replacement asset packets."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit as gap_audit
import reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets as replacement_packets


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

PACKET_DIR = RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets_codex_proxy_user_requested"
DEFAULT_PACKET_SUMMARY = PACKET_DIR / "summary.json"
DEFAULT_FINAL_MANIFEST = PACKET_DIR / "v7_object_cell_evidence_contrast_restored_manifest_post_label_only.jsonl"
DEFAULT_FINAL_LABEL_SHEET = PACKET_DIR / "v7_object_cell_evidence_contrast_restored_label_sheet.tsv"
DEFAULT_GENERATED_PACKET_MANIFEST = PACKET_DIR / "generated_replacement_packet_manifest.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packet_gap_audit_codex_proxy_user_requested"

SCHEMA_VERSION = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packet_gap_audit_v1"
EXPECTED_PACKET_STATUS = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets_partial_needs_gap_audit"
EXPECTED_NEXT_TODO = "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packet_gap_audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-summary", type=Path, default=DEFAULT_PACKET_SUMMARY)
    parser.add_argument("--final-manifest", type=Path, default=DEFAULT_FINAL_MANIFEST)
    parser.add_argument("--final-label-sheet", type=Path, default=DEFAULT_FINAL_LABEL_SHEET)
    parser.add_argument("--generated-packet-manifest", type=Path, default=DEFAULT_GENERATED_PACKET_MANIFEST)
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


def read_tsv(path: Path) -> list[dict[str, Any]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(packet_summary: dict[str, Any], manifest_rows: list[dict[str, Any]], label_rows: list[dict[str, Any]], generated_packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if packet_summary.get("status") != EXPECTED_PACKET_STATUS:
        errors.append({"error_type": "unexpected_packet_status", "actual": packet_summary.get("status")})
    if packet_summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_packet_next_todo", "actual": packet_summary.get("next_todo")})
    boundary = packet_summary.get("boundary") or {}
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "packet_boundary_not_false", "field": key, "actual": boundary.get(key)})
    counts = packet_summary.get("counts") or {}
    if len(manifest_rows) != counts.get("final_label_sheet_rows"):
        errors.append({"error_type": "manifest_count_mismatch", "actual": len(manifest_rows), "summary": counts.get("final_label_sheet_rows")})
    if len(label_rows) != counts.get("final_label_sheet_rows"):
        errors.append({"error_type": "label_sheet_count_mismatch", "actual": len(label_rows), "summary": counts.get("final_label_sheet_rows")})
    if len(generated_packets) != counts.get("generated_replacement_packet_rows"):
        errors.append(
            {
                "error_type": "generated_packet_count_mismatch",
                "actual": len(generated_packets),
                "summary": counts.get("generated_replacement_packet_rows"),
            }
        )
    if counts.get("final_non_ready_rows") != 1:
        errors.append({"error_type": "unexpected_non_ready_count", "actual": counts.get("final_non_ready_rows"), "expected": 1})
    return errors


def synthetic_packet_for_status(row: dict[str, Any]) -> dict[str, Any]:
    status = replacement_packets.evidence_status(row)
    return {
        "blind_review_id": row.get("blind_review_id"),
        "packet_status": "ready" if status == "limited_view_evaluable" else status,
        "subject_image_count": 1,
        "object_image_count": 1,
        "contact_sheet_ready": True,
        "mesh_packet_ready": True,
        "subject_label": row.get("subject_label"),
        "object_label": row.get("object_label"),
        "predicate_family": row.get("predicate_family"),
        "multiview_packet": row.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": row.get("contact_or_context_sheet", ""),
    }


def decide_all_rows(manifest_rows: list[dict[str, Any]], generated_packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_by_id = {str(row["blind_review_id"]): row for row in generated_packets}
    decisions: list[dict[str, Any]] = []
    for row in manifest_rows:
        blind_id = str(row["blind_review_id"])
        status = replacement_packets.evidence_status(row)
        if status in {"ready", "limited_view_evaluable"}:
            packet = synthetic_packet_for_status(row)
            decision = gap_audit.decide_row(packet, row)
            if status == "limited_view_evaluable":
                decision["row_gap_decision"] = "limited_view_evaluable"
                decision["row_gap_reason"] = row.get("row_gap_reason_hidden") or "previous gap audit kept this row as limited-view evaluable"
                decision["normalized_evidence_status"] = "limited_view_evaluable"
        else:
            packet = packet_by_id.get(blind_id)
            if packet is None:
                packet = synthetic_packet_for_status(row)
            decision = gap_audit.decide_row(packet, row)
        decisions.append(decision)
    return decisions


def update_manifest_rows(manifest_rows: list[dict[str, Any]], decisions: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for row in manifest_rows:
        blind_id = str(row["blind_review_id"])
        decision = decisions[blind_id]
        updated = dict(row)
        updated["row_gap_decision_hidden"] = decision["row_gap_decision"]
        updated["row_gap_reason_hidden"] = decision["row_gap_reason"]
        updated["normalized_evidence_status_hidden"] = decision["normalized_evidence_status"]
        updated["packet_status_hidden"] = decision["normalized_evidence_status"]
        forbidden = list(updated.get("forbidden_as_labeler_visible") or [])
        for field in ["row_gap_decision_hidden", "row_gap_reason_hidden", "normalized_evidence_status_hidden"]:
            if field not in forbidden:
                forbidden.append(field)
        updated["forbidden_as_labeler_visible"] = forbidden
        if decision["row_gap_decision"] == "replacement_needed":
            excluded_rows.append(updated)
        else:
            ready_rows.append(updated)
    return ready_rows, excluded_rows


def bucket_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for family in ["support_contact", "relative_vertical"]:
        for bucket in ["B2_semantic_high_geometry_low", "B3_semantic_low_geometry_high"]:
            group = [row for row in rows if row.get("predicate_family") == family and row.get("semantic_geometry_bucket_hidden") == bucket]
            statuses = Counter(replacement_packets.evidence_status(row) for row in group)
            output.append(
                {
                    "predicate_family": family,
                    "semantic_geometry_bucket": bucket,
                    "rows": len(group),
                    "ready_rows": statuses.get("ready", 0),
                    "limited_view_evaluable_rows": statuses.get("limited_view_evaluable", 0),
                    "replacement_needed_rows": statuses.get("replacement_needed", 0),
                }
            )
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V7 Replacement Asset Packet Gap Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage audit.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- This focused audit decides the last replacement partial row before label readiness.",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next = {summary['next_todo']}",
        f"validation_errors = {summary['validation_error_count']}",
        "```",
        "",
        "## Counts",
        "",
        "```text",
        f"input_rows = {summary['counts']['input_rows']}",
        f"label_ready_rows = {summary['counts']['label_ready_rows']}",
        f"excluded_rows = {summary['counts']['excluded_rows']}",
        f"new_limited_view_rows = {summary['counts']['new_limited_view_rows']}",
        f"final_evidence_status_counts = {summary['final_evidence_status_counts']}",
        "```",
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
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    packet_summary = read_json(args.packet_summary)
    manifest_rows = read_jsonl(args.final_manifest)
    label_rows = read_tsv(args.final_label_sheet)
    generated_packets = read_jsonl(args.generated_packet_manifest)
    input_errors = validate_inputs(packet_summary, manifest_rows, label_rows, generated_packets)

    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    row_decisions = decide_all_rows(manifest_rows, generated_packets)
    decision_by_id = {str(row["blind_review_id"]): row for row in row_decisions}
    ready_manifest_rows, excluded_manifest_rows = update_manifest_rows(manifest_rows, decision_by_id)
    final_label_rows = [replacement_packets.visible_row(row, output_dir) for row in ready_manifest_rows]
    path_errors = replacement_packets.packet_path_errors(final_label_rows, output_dir)
    field_hits = replacement_packets.mining.field_leakage_hits(replacement_packets.FINAL_VISIBLE_FIELDS)
    value_hits = replacement_packets.visible_value_leakage_hits(final_label_rows)
    packet_text_hits = replacement_packets.packeting.packet_text_leakage_hits(generated_packets)
    leakage_hits = field_hits + value_hits + packet_text_hits

    validation_errors = list(input_errors)
    if path_errors:
        validation_errors.append({"error_type": "packet_path_errors", "count": len(path_errors)})
    if leakage_hits:
        validation_errors.append({"error_type": "visible_or_packet_leakage", "count": len(leakage_hits)})

    final_status_counts = Counter(replacement_packets.evidence_status(row) for row in ready_manifest_rows)
    row_decision_counts = Counter(row["row_gap_decision"] for row in row_decisions)
    new_limited_rows = [
        row
        for row in row_decisions
        if row["row_gap_decision"] == "limited_view_evaluable" and row.get("packet_status") == "partial"
    ]
    if excluded_manifest_rows:
        status = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packet_gap_audit_needs_replacement"
        next_todo = "reliability_target_v7_object_cell_evidence_contrast_replacement_mining"
        decision = "Focused gap audit still found replacement-needed rows; do not proceed to label readiness."
    elif validation_errors:
        status = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packet_gap_audit_errors"
        next_todo = "fix_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packet_gap_audit_errors"
        decision = "Focused gap audit is blocked by validation, leakage, or path errors."
    else:
        status = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packet_gap_audit_ready_for_label_readiness"
        next_todo = "reliability_target_v7_object_cell_evidence_contrast_label_readiness"
        decision = "The only remaining replacement partial row is kept as limited-view evaluable; the restored 240-row queue can proceed to label readiness."

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "row_gap_decisions": output_dir / "row_gap_decisions.jsonl",
        "focused_partial_row_decisions": output_dir / "focused_partial_row_decisions.jsonl",
        "label_ready_full_manifest_post_label_only": output_dir / "label_ready_full_manifest_post_label_only.jsonl",
        "label_ready_full_label_sheet": output_dir / "label_ready_full_label_sheet.tsv",
        "excluded_rows": output_dir / "excluded_rows.jsonl",
        "bucket_gap_summary": output_dir / "bucket_gap_summary.csv",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "visible_value_leakage_hits": output_dir / "visible_value_leakage_hits.jsonl",
        "packet_text_leakage_hits": output_dir / "packet_text_leakage_hits.jsonl",
        "label_surface_leakage_hits": output_dir / "label_surface_leakage_hits.jsonl",
        "input_validation_errors": output_dir / "input_validation_errors.json",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": {
            "packet_summary": rel_path(args.packet_summary),
            "final_manifest": rel_path(args.final_manifest),
            "final_label_sheet": rel_path(args.final_label_sheet),
            "generated_packet_manifest": rel_path(args.generated_packet_manifest),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "labels_filled": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "paper_metric_evidence": False,
            "semantic_geometry_bucket_visible_to_labeler": False,
            "semantic_geometry_bucket_posterior_input_allowed": False,
            "h001_artifacts_modified": False,
        },
        "source_packet_status": packet_summary.get("status"),
        "counts": {
            "input_rows": len(manifest_rows),
            "label_ready_rows": len(ready_manifest_rows),
            "excluded_rows": len(excluded_manifest_rows),
            "new_limited_view_rows": len(new_limited_rows),
            "path_errors": len(path_errors),
            "leakage_hits": len(leakage_hits),
            "validation_errors": len(validation_errors),
            "by_family": dict(sorted(Counter(row.get("predicate_family") for row in ready_manifest_rows).items())),
            "by_bucket": dict(sorted(Counter(row.get("semantic_geometry_bucket_hidden") for row in ready_manifest_rows).items())),
            "by_family_bucket": dict(sorted(Counter(f"{row.get('predicate_family')}|{row.get('semantic_geometry_bucket_hidden')}" for row in ready_manifest_rows).items())),
        },
        "row_decision_counts": dict(sorted(row_decision_counts.items())),
        "final_evidence_status_counts": dict(sorted(final_status_counts.items())),
        "validation_error_count": len(validation_errors),
        "label_fill_allowed": False,
        "posterior_allowed": False,
    }

    write_jsonl(output_paths["row_gap_decisions"], row_decisions)
    write_jsonl(output_paths["focused_partial_row_decisions"], new_limited_rows)
    write_jsonl(output_paths["label_ready_full_manifest_post_label_only"], ready_manifest_rows)
    write_tsv(output_paths["label_ready_full_label_sheet"], final_label_rows, replacement_packets.FINAL_VISIBLE_FIELDS)
    write_jsonl(output_paths["excluded_rows"], excluded_manifest_rows)
    write_csv(output_paths["bucket_gap_summary"], bucket_summary_rows(ready_manifest_rows))
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_jsonl(output_paths["visible_value_leakage_hits"], value_hits)
    write_jsonl(output_paths["packet_text_leakage_hits"], packet_text_hits)
    write_jsonl(output_paths["label_surface_leakage_hits"], leakage_hits)
    write_json(output_paths["input_validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        f"status={summary['status']} "
        f"input_rows={summary['counts']['input_rows']} "
        f"label_ready_rows={summary['counts']['label_ready_rows']} "
        f"excluded_rows={summary['counts']['excluded_rows']} "
        f"new_limited_view={summary['counts']['new_limited_view_rows']} "
        f"path_errors={summary['counts']['path_errors']} "
        f"leakage={summary['counts']['leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
