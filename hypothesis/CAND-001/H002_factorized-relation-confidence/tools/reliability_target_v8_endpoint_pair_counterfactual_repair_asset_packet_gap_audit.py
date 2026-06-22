#!/usr/bin/env python3
"""Conservative gap audit for v8 repair asset packets.

This audit treats partial repair packets as diagnostic evidence only. The
primary posterior target must use complete packets or request replacements.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

PACKET_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_asset_packets_codex_proxy_user_requested"
DEFAULT_PACKET_SUMMARY = PACKET_DIR / "summary.json"
DEFAULT_FULL_LABEL_SHEET = PACKET_DIR / "repair_full_label_sheet.tsv"
DEFAULT_FULL_MANIFEST = PACKET_DIR / "repair_full_manifest_post_label_only.jsonl"
DEFAULT_NON_READY_PACKETS = PACKET_DIR / "generated_non_ready_packet_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_asset_packet_gap_audit_codex_proxy_user_requested"

SCHEMA_VERSION = "h002_reliability_target_v8_endpoint_pair_counterfactual_repair_asset_packet_gap_audit_v1"
EXPECTED_STATUS = "h002_reliability_target_v8_repair_asset_packets_partial_needs_gap_audit"
EXPECTED_NEXT = "reliability_target_v8_endpoint_pair_counterfactual_repair_asset_packet_gap_audit"
NEXT_TODO = "reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_mining"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-summary", type=Path, default=DEFAULT_PACKET_SUMMARY)
    parser.add_argument("--full-label-sheet", type=Path, default=DEFAULT_FULL_LABEL_SHEET)
    parser.add_argument("--full-manifest", type=Path, default=DEFAULT_FULL_MANIFEST)
    parser.add_argument("--non-ready-packets", type=Path, default=DEFAULT_NON_READY_PACKETS)
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


def read_tsv_with_header(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader), list(reader.fieldnames or [])


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        seen: set[str] = set()
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "ready"}


def intish(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def missing_sides(row: dict[str, Any]) -> list[str]:
    sides: list[str] = []
    if intish(row.get("subject_image_count")) <= 0:
        sides.append("subject")
    if intish(row.get("object_image_count")) <= 0:
        sides.append("object")
    return sides


def packet_diagnostic_status(packet_row: dict[str, Any]) -> tuple[str, str]:
    sides = missing_sides(packet_row)
    contact_ready = boolish(packet_row.get("contact_sheet_ready")) or bool(packet_row.get("contact_or_context_sheet"))
    mesh_ready = boolish(packet_row.get("mesh_packet_ready")) or bool(packet_row.get("pointcloud_or_mesh_packet"))
    if len(sides) == 1 and contact_ready and mesh_ready:
        return (
            "diagnostic_limited_view_only",
            "one endpoint crop is missing, but mesh and contact/context evidence exist; keep only for diagnostic review",
        )
    if len(sides) >= 2 and not contact_ready:
        return (
            "no_visual_or_contact_context",
            "both endpoint crops and contact/context evidence are insufficient; request replacement",
        )
    if len(sides) >= 2:
        return (
            "no_endpoint_visual_context",
            "both endpoint crops are missing; endpoint identity is too weak for the primary target",
        )
    return (
        "partial_evidence_not_primary",
        "packet is partial and therefore excluded from the primary target by conservative repair policy",
    )


def validate_inputs(summary: dict[str, Any], label_rows: list[dict[str, Any]], manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_STATUS:
        errors.append({"error": "unexpected_status", "expected": EXPECTED_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_NEXT:
        errors.append({"error": "unexpected_next_todo", "expected": EXPECTED_NEXT, "actual": summary.get("next_todo")})
    boundary = summary.get("boundary") or {}
    for key in [
        "validation_usage",
        "test_usage",
        "posterior_trained",
        "posterior_smoke_allowed",
        "multi_view_as_model_input",
        "h001_artifacts_modified",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error": f"boundary_{key}_not_false", "actual": boundary.get(key)})
    expected_rows = summary.get("counts", {}).get("full_label_sheet_rows")
    if len(label_rows) != expected_rows:
        errors.append({"error": "label_row_count_mismatch", "expected": expected_rows, "actual": len(label_rows)})
    if len(manifests) != len(label_rows):
        errors.append({"error": "manifest_label_row_count_mismatch", "manifests": len(manifests), "label_rows": len(label_rows)})
    return errors


def build_decisions(
    manifests: list[dict[str, Any]],
    non_ready_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for manifest in manifests:
        blind_id = str(manifest.get("blind_review_id"))
        status = str(manifest.get("packet_status_hidden") or "")
        packet = non_ready_by_id.get(blind_id, {})
        if status == "ready":
            diagnostic_status = "complete_packet"
            diagnostic_reason = "complete packet retained for primary label target"
            primary_decision = "primary_label_ready"
        else:
            diagnostic_status, diagnostic_reason = packet_diagnostic_status(packet)
            primary_decision = "replacement_needed"
        decisions.append(
            {
                "blind_review_id": blind_id,
                "scan_id": manifest.get("scan_id"),
                "scene_context_id": manifest.get("scene_context_id"),
                "subject_id": manifest.get("subject_id"),
                "subject_label": manifest.get("subject_label"),
                "predicate_label": manifest.get("predicate_label"),
                "predicate_family": manifest.get("predicate_family"),
                "object_id": manifest.get("object_id"),
                "object_label": manifest.get("object_label"),
                "packet_status_hidden": status,
                "primary_gap_decision": primary_decision,
                "diagnostic_status": diagnostic_status,
                "diagnostic_reason": diagnostic_reason,
                "subject_image_count": packet.get("subject_image_count"),
                "object_image_count": packet.get("object_image_count"),
                "contact_sheet_ready": packet.get("contact_sheet_ready"),
                "mesh_packet_ready": packet.get("mesh_packet_ready"),
                "missing_sides": missing_sides(packet) if packet else [],
                "counterfactual_pair_id_hidden": manifest.get("counterfactual_pair_id_hidden"),
                "counterfactual_pair_type_hidden": manifest.get("counterfactual_pair_type_hidden"),
                "semantic_geometry_bucket_hidden": manifest.get("label_geometry_bucket_hidden"),
                "geometry_status_hidden": manifest.get("geometry_status_hidden"),
                "source_queue_hidden": manifest.get("source_queue_hidden"),
                "rank_band_hidden": manifest.get("rank_band_hidden"),
                "exact_endpoint_pair_key_hidden": manifest.get("exact_endpoint_pair_key_hidden"),
                "subject_object_label_pair_hidden": manifest.get("subject_object_label_pair_hidden"),
                "additional_batch_role_hidden": manifest.get("additional_batch_role_hidden"),
            }
        )
    return decisions


def augment_label_rows(
    label_rows: list[dict[str, Any]],
    decisions_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ready: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    diagnostic: list[dict[str, Any]] = []
    for row in label_rows:
        decision = decisions_by_id[str(row.get("blind_review_id"))]
        updated = dict(row)
        updated["packet_gap_decision"] = decision["primary_gap_decision"]
        updated["packet_gap_reason"] = decision["diagnostic_reason"]
        updated["evidence_packet_status"] = row.get("evidence_packet_status") or decision["packet_status_hidden"]
        if decision["primary_gap_decision"] == "primary_label_ready":
            ready.append(updated)
        else:
            excluded.append(updated)
            if decision["diagnostic_status"] == "diagnostic_limited_view_only":
                diagnostic.append(updated)
    return ready, excluded, diagnostic


def augment_manifests(
    manifests: list[dict[str, Any]],
    decisions_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for row in manifests:
        decision = decisions_by_id[str(row.get("blind_review_id"))]
        updated = dict(row)
        updated["primary_gap_decision_hidden"] = decision["primary_gap_decision"]
        updated["diagnostic_status_hidden"] = decision["diagnostic_status"]
        updated["diagnostic_reason_hidden"] = decision["diagnostic_reason"]
        updated["label_fill_allowed"] = decision["primary_gap_decision"] == "primary_label_ready"
        updated["posterior_input_allowed"] = False
        forbidden = list(updated.get("forbidden_as_labeler_visible") or [])
        for field in [
            "primary_gap_decision_hidden",
            "diagnostic_status_hidden",
            "diagnostic_reason_hidden",
            "label_geometry_bucket_hidden",
            "geometry_status_hidden",
            "source_queue_hidden",
            "rank_band_hidden",
            "exact_endpoint_pair_key_hidden",
            "counterfactual_pair_id_hidden",
        ]:
            if field not in forbidden:
                forbidden.append(field)
        updated["forbidden_as_labeler_visible"] = forbidden
        if decision["primary_gap_decision"] == "primary_label_ready":
            ready.append(updated)
        else:
            excluded.append(updated)
    return ready, excluded


def counter_dict(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key)) for row in rows).items()))


def paired_counter(rows: list[dict[str, Any]], key_a: str, key_b: str) -> dict[str, int]:
    counts = Counter(f"{row.get(key_a)}::{row.get(key_b)}" for row in rows)
    return dict(sorted(counts.items()))


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V8 Repair Asset Packet Gap Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "```text",
        "split = train_only",
        "validation_usage = False",
        "test_usage = False",
        "labels_filled = False",
        "posterior_trained = False",
        "posterior_smoke_allowed = False",
        "multi_view_as_model_input = False",
        "h001_artifacts_modified = False",
        "```",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next = {summary['next_todo']}",
        "```",
        "",
        "## Conservative Decision",
        "",
        summary["decision"],
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| input rows | {summary['counts']['input_rows']} |",
        f"| primary label-ready rows | {summary['counts']['primary_label_ready_rows']} |",
        f"| primary replacement-needed rows | {summary['counts']['primary_replacement_needed_rows']} |",
        f"| diagnostic limited-view rows | {summary['counts']['diagnostic_limited_view_rows']} |",
        f"| hard replacement rows | {summary['counts']['hard_replacement_rows']} |",
        f"| input validation errors | {summary['validation']['input_validation_errors']} |",
        "",
        "## Decision Counts",
        "",
        "```text",
        f"primary_gap_decision_counts = {summary['primary_gap_decision_counts']}",
        f"diagnostic_status_counts = {summary['diagnostic_status_counts']}",
        f"replacement_family_counts = {summary['replacement_family_counts']}",
        f"ready_family_counts = {summary['ready_family_counts']}",
        "```",
        "",
        "## Interpretation",
        "",
        "The 24 partial rows are not treated as scientific negatives. They are coverage gaps. "
        "Keeping them in the primary label target would make endpoint identity and evidence coverage "
        "part of the target, so they are routed to replacement mining instead.",
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
    label_rows, label_fieldnames = read_tsv_with_header(args.full_label_sheet)
    manifests = read_jsonl(args.full_manifest)
    non_ready_packets = read_jsonl(args.non_ready_packets)
    input_errors = validate_inputs(packet_summary, label_rows, manifests)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    non_ready_by_id = {str(row["blind_review_id"]): row for row in non_ready_packets}
    decisions = build_decisions(manifests, non_ready_by_id)
    decisions_by_id = {str(row["blind_review_id"]): row for row in decisions}
    ready_labels, excluded_labels, diagnostic_labels = augment_label_rows(label_rows, decisions_by_id)
    ready_manifests, excluded_manifests = augment_manifests(manifests, decisions_by_id)

    decision_counts = counter_dict(decisions, "primary_gap_decision")
    diagnostic_counts = counter_dict(decisions, "diagnostic_status")
    replacement_decisions = [row for row in decisions if row["primary_gap_decision"] == "replacement_needed"]
    hard_replacement = [row for row in replacement_decisions if row["diagnostic_status"] != "diagnostic_limited_view_only"]

    label_ready_fieldnames = list(label_fieldnames)
    for field in ["packet_gap_decision", "packet_gap_reason"]:
        if field not in label_ready_fieldnames:
            label_ready_fieldnames.append(field)

    output_paths = {
        "primary_label_ready_sheet": output_dir / "primary_label_ready_sheet.tsv",
        "primary_label_ready_manifest_post_label_only": output_dir / "primary_label_ready_manifest_post_label_only.jsonl",
        "primary_excluded_rows": output_dir / "primary_excluded_rows.jsonl",
        "diagnostic_limited_view_rows": output_dir / "diagnostic_limited_view_rows.jsonl",
        "replacement_request_plan": output_dir / "replacement_request_plan.jsonl",
        "row_gap_decisions": output_dir / "row_gap_decisions.jsonl",
        "gap_summary_csv": output_dir / "gap_summary.csv",
        "input_validation_errors": output_dir / "input_validation_errors.jsonl",
        "report": output_dir / "report.md",
        "summary": output_dir / "summary.json",
    }

    write_tsv(output_paths["primary_label_ready_sheet"], ready_labels, label_ready_fieldnames)
    write_jsonl(output_paths["primary_label_ready_manifest_post_label_only"], ready_manifests)
    write_jsonl(output_paths["primary_excluded_rows"], excluded_manifests)
    write_jsonl(output_paths["diagnostic_limited_view_rows"], [row for row in decisions if row["diagnostic_status"] == "diagnostic_limited_view_only"])
    write_jsonl(output_paths["replacement_request_plan"], replacement_decisions)
    write_jsonl(output_paths["row_gap_decisions"], decisions)
    write_csv(
        output_paths["gap_summary_csv"],
        [
            {"group": "primary_gap_decision", "key": key, "rows": value}
            for key, value in decision_counts.items()
        ]
        + [
            {"group": "diagnostic_status", "key": key, "rows": value}
            for key, value in diagnostic_counts.items()
        ]
        + [
            {"group": "replacement_family", "key": key, "rows": value}
            for key, value in counter_dict(replacement_decisions, "predicate_family").items()
        ]
        + [
            {"group": "ready_family", "key": key, "rows": value}
            for key, value in counter_dict(ready_manifests, "predicate_family").items()
        ],
    )
    write_jsonl(output_paths["input_validation_errors"], input_errors)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "h002_reliability_target_v8_repair_asset_packet_gap_audit_needs_replacement",
        "decision": (
            "Use only the 176 complete packets as the primary label-ready set. "
            "Route all 24 partial rows to replacement mining. Sixteen partial rows are retained as "
            "diagnostic-limited-view evidence only; eight rows are hard replacement cases."
        ),
        "next_todo": NEXT_TODO,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "labels_filled": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "paper_metric_evidence": False,
            "h001_artifacts_modified": False,
        },
        "counts": {
            "input_rows": len(label_rows),
            "manifest_rows": len(manifests),
            "non_ready_packet_rows": len(non_ready_packets),
            "primary_label_ready_rows": len(ready_labels),
            "primary_replacement_needed_rows": len(replacement_decisions),
            "primary_excluded_rows": len(excluded_labels),
            "diagnostic_limited_view_rows": len(diagnostic_labels),
            "hard_replacement_rows": len(hard_replacement),
        },
        "primary_gap_decision_counts": decision_counts,
        "diagnostic_status_counts": diagnostic_counts,
        "replacement_family_counts": counter_dict(replacement_decisions, "predicate_family"),
        "ready_family_counts": counter_dict(ready_manifests, "predicate_family"),
        "replacement_predicate_counts": counter_dict(replacement_decisions, "predicate_label"),
        "ready_predicate_counts": counter_dict(ready_manifests, "predicate_label"),
        "replacement_family_role_counts": paired_counter(replacement_decisions, "predicate_family", "additional_batch_role_hidden"),
        "input_paths": {
            "packet_summary": rel_path(args.packet_summary),
            "full_label_sheet": rel_path(args.full_label_sheet),
            "full_manifest": rel_path(args.full_manifest),
            "non_ready_packets": rel_path(args.non_ready_packets),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "validation": {
            "input_validation_errors": len(input_errors),
        },
    }
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
