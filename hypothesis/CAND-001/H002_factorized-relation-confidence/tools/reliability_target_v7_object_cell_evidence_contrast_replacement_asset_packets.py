#!/usr/bin/env python3
"""Generate asset packets for H002 v7 replacement rows."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_asset_packets as base_packets
import reliability_target_v7_object_cell_evidence_contrast_asset_packets as packeting
import reliability_target_v7_object_cell_evidence_contrast_candidate_mining as mining


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

REPLACEMENT_DIR = RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_replacement_mining_codex_proxy_user_requested"
DEFAULT_REPLACEMENT_SUMMARY = REPLACEMENT_DIR / "summary.json"
DEFAULT_COMBINED_MANIFEST = REPLACEMENT_DIR / "combined_manifest_pre_asset_packet.jsonl"
DEFAULT_REPLACEMENT_ASSET_NEEDED = REPLACEMENT_DIR / "replacement_asset_needed_candidates.jsonl"
DEFAULT_REPLACEMENT_ASSET_REQUESTS = REPLACEMENT_DIR / "replacement_asset_request_manifest.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets_codex_proxy_user_requested"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"

SCHEMA_VERSION = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets_v1"
EXPECTED_REPLACEMENT_STATUS = (
    "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_mining_ready_needs_replacement_asset_packets"
)
EXPECTED_NEXT_TODO = "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets"
GENERATED_REPLACEMENT_PACKET_SOURCE = "generated_v7_object_cell_evidence_contrast_replacement_asset_packet"
REVIEW_SCOPE = "h002_reliability_v7_object_cell_evidence_contrast_restored_packeted_review"
FINAL_VISIBLE_FIELDS = mining.VISIBLE_FIELDS + ["packet_gap_decision", "packet_gap_reason"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replacement-summary", type=Path, default=DEFAULT_REPLACEMENT_SUMMARY)
    parser.add_argument("--combined-manifest", type=Path, default=DEFAULT_COMBINED_MANIFEST)
    parser.add_argument("--replacement-asset-needed", type=Path, default=DEFAULT_REPLACEMENT_ASSET_NEEDED)
    parser.add_argument("--replacement-asset-requests", type=Path, default=DEFAULT_REPLACEMENT_ASSET_REQUESTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--images-per-object", type=int, default=4)
    parser.add_argument("--thumb-size", type=int, default=320)
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


def validate_inputs(
    replacement_summary: dict[str, Any],
    combined_rows: list[dict[str, Any]],
    asset_needed_rows: list[dict[str, Any]],
    asset_requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if replacement_summary.get("status") != EXPECTED_REPLACEMENT_STATUS:
        errors.append({"error_type": "unexpected_replacement_status", "actual": replacement_summary.get("status")})
    if replacement_summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_replacement_next_todo", "actual": replacement_summary.get("next_todo")})
    boundary = replacement_summary.get("boundary") or {}
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "replacement_boundary_not_false", "field": key, "actual": boundary.get(key)})
    counts = replacement_summary.get("counts") or {}
    if len(combined_rows) != counts.get("combined_rows"):
        errors.append({"error_type": "combined_manifest_count_mismatch", "actual": len(combined_rows), "summary": counts.get("combined_rows")})
    if len(asset_needed_rows) != counts.get("replacement_asset_needed_rows"):
        errors.append(
            {
                "error_type": "asset_needed_count_mismatch",
                "actual": len(asset_needed_rows),
                "summary": counts.get("replacement_asset_needed_rows"),
            }
        )
    request_ids = {str(row.get("blind_review_id")) for row in asset_requests}
    needed_ids = {str(row.get("blind_review_id")) for row in asset_needed_rows}
    if request_ids != needed_ids:
        errors.append(
            {
                "error_type": "asset_request_id_set_mismatch",
                "needed_only": sorted(needed_ids - request_ids),
                "request_only": sorted(request_ids - needed_ids),
            }
        )
    combined_asset_needed = {str(row.get("blind_review_id")) for row in combined_rows if row.get("packet_status_hidden") == "asset_needed"}
    if combined_asset_needed != needed_ids:
        errors.append(
            {
                "error_type": "combined_asset_needed_id_set_mismatch",
                "combined_only": sorted(combined_asset_needed - needed_ids),
                "needed_only": sorted(needed_ids - combined_asset_needed),
            }
        )
    family_bucket_counts = Counter(f"{row.get('predicate_family')}|{row.get('semantic_geometry_bucket_hidden')}" for row in combined_rows)
    expected = {
        "relative_vertical|B2_semantic_high_geometry_low": 60,
        "relative_vertical|B3_semantic_low_geometry_high": 60,
        "support_contact|B2_semantic_high_geometry_low": 60,
        "support_contact|B3_semantic_low_geometry_high": 60,
    }
    if dict(sorted(family_bucket_counts.items())) != expected:
        errors.append({"error_type": "combined_family_bucket_count_mismatch", "actual": dict(sorted(family_bucket_counts.items())), "expected": expected})
    return errors


def update_replacement_seed(seed: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    updated = packeting.update_seed_with_packet(seed, packet)
    updated["batch_name"] = "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets"
    updated["asset_packet_source_hidden"] = GENERATED_REPLACEMENT_PACKET_SOURCE
    updated["normalized_evidence_status_hidden"] = packet.get("packet_status", "")
    if packet.get("packet_status") == "ready":
        updated["row_gap_decision_hidden"] = "replacement_packet_ready"
        updated["row_gap_reason_hidden"] = "replacement asset packet generated with complete endpoint, contact, and mesh evidence"
    else:
        updated["row_gap_decision_hidden"] = "replacement_packet_non_ready"
        updated["row_gap_reason_hidden"] = "replacement asset packet generated but still has incomplete endpoint/contact evidence"
    forbidden = list(updated.get("forbidden_as_labeler_visible") or [])
    for field in ["asset_packet_source_hidden", "normalized_evidence_status_hidden", "row_gap_decision_hidden", "row_gap_reason_hidden"]:
        if field not in forbidden:
            forbidden.append(field)
    updated["forbidden_as_labeler_visible"] = forbidden
    return updated


def evidence_status(row: dict[str, Any]) -> str:
    return str(row.get("normalized_evidence_status_hidden") or row.get("packet_status_hidden") or "")


def visible_row(row: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    prompt = mining.family_prompt(row)
    status = evidence_status(row)
    output = {
        "blind_review_id": row["blind_review_id"],
        "review_scope": REVIEW_SCOPE,
        "scan_id": row.get("scan_id", ""),
        "scene_context_id": row.get("scene_context_id", ""),
        "subject_id": row.get("subject_id", ""),
        "subject_label": row.get("subject_label", ""),
        "predicate_label": row.get("predicate_label", ""),
        "predicate_family": row.get("predicate_family", ""),
        "object_id": row.get("object_id", ""),
        "object_label": row.get("object_label", ""),
        "family_question": prompt["question"],
        "supporting_cues": prompt["supporting_cues"],
        "contradicting_cues": prompt["contradicting_cues"],
        "evidence_packet_status": status,
        "multiview_packet": packeting.label_facing_packet_path(row, "multiview_packet", output_dir),
        "pointcloud_or_mesh_packet": packeting.label_facing_packet_path(row, "pointcloud_or_mesh_packet", output_dir),
        "contact_or_context_sheet": packeting.label_facing_packet_path(row, "contact_or_context_sheet", output_dir),
    }
    for field in mining.COMPLETION_FIELDS:
        output[field] = ""
    output["packet_gap_decision"] = row.get("row_gap_decision_hidden", "")
    output["packet_gap_reason"] = row.get("row_gap_reason_hidden", "")
    return output


def packet_path_errors(label_rows: list[dict[str, Any]], output_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(label_rows, start=2):
        status = str(row.get("evidence_packet_status") or "")
        if status not in {"ready", "limited_view_evaluable"}:
            continue
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(field) or "")
            if not value:
                errors.append({"row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "error": "empty_packet_path"})
                continue
            resolved = packeting.resolve_label_packet_path(value, output_dir)
            if not resolved.exists():
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": row.get("blind_review_id"),
                        "field": field,
                        "path": value,
                        "error": "packet_path_missing_on_disk",
                    }
                )
    return errors


def visible_value_leakage_hits(label_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row_number, row in enumerate(label_rows, start=2):
        for field, value in row.items():
            if field in {"multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet", "packet_gap_decision", "packet_gap_reason"}:
                continue
            lower = str(value).lower()
            for token in mining.FORBIDDEN_VISIBLE_VALUE_TOKENS:
                if token in lower:
                    hits.append({"row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "forbidden_token": token})
                    break
    return hits


def bucket_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for family in mining.PRIMARY_FAMILIES:
        for bucket in mining.BUCKETS:
            group = [row for row in rows if row.get("predicate_family") == family and row.get("semantic_geometry_bucket_hidden") == bucket]
            statuses = Counter(evidence_status(row) for row in group)
            output.append(
                {
                    "predicate_family": family,
                    "semantic_geometry_bucket": bucket,
                    "rows": len(group),
                    "ready_rows": statuses.get("ready", 0),
                    "limited_view_evaluable_rows": statuses.get("limited_view_evaluable", 0),
                    "partial_rows": statuses.get("partial", 0),
                    "asset_needed_rows": statuses.get("asset_needed", 0),
                    "missing_rows": statuses.get("missing", 0),
                }
            )
    return output


def non_ready_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        status = evidence_status(row)
        if status in {"ready", "limited_view_evaluable"}:
            continue
        output.append(
            {
                "blind_review_id": row.get("blind_review_id"),
                "predicate_family": row.get("predicate_family"),
                "predicate_label": row.get("predicate_label"),
                "semantic_geometry_bucket_hidden": row.get("semantic_geometry_bucket_hidden"),
                "scan_id": row.get("scan_id"),
                "subject_id": row.get("subject_id"),
                "subject_label": row.get("subject_label"),
                "object_id": row.get("object_id"),
                "object_label": row.get("object_label"),
                "evidence_status": status,
                "packet_status_hidden": row.get("packet_status_hidden"),
                "multiview_packet_present": bool(row.get("multiview_packet")),
                "pointcloud_or_mesh_packet_present": bool(row.get("pointcloud_or_mesh_packet")),
                "contact_or_context_sheet_present": bool(row.get("contact_or_context_sheet")),
            }
        )
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V7 Object-Cell Evidence Contrast Replacement Asset Packets",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage artifact.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- Replacement multi-view and mesh packets are audit/label evidence only, not posterior input.",
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
        "| Item | Count |",
        "| --- | ---: |",
        f"| input combined rows | {counts['input_combined_rows']} |",
        f"| replacement asset-needed input rows | {counts['replacement_asset_needed_input_rows']} |",
        f"| generated replacement packet rows | {counts['generated_replacement_packet_rows']} |",
        f"| generated non-ready rows | {counts['generated_non_ready_rows']} |",
        f"| final label sheet rows | {counts['final_label_sheet_rows']} |",
        f"| final label-ready candidate rows | {counts['final_label_ready_candidate_rows']} |",
        f"| path errors | {counts['packet_path_errors']} |",
        f"| leakage hits | {counts['leakage_hits']} |",
        "",
        "## Evidence Status",
        "",
        "```text",
        f"final_evidence_status_counts = {summary['final_evidence_status_counts']}",
        f"generated_packet_status_counts = {summary['generated_packet_status_counts']}",
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
    replacement_summary = read_json(args.replacement_summary)
    combined_rows = read_jsonl(args.combined_manifest)
    asset_needed_rows = read_jsonl(args.replacement_asset_needed)
    asset_requests = read_jsonl(args.replacement_asset_requests)
    validation_errors = validate_inputs(replacement_summary, combined_rows, asset_needed_rows, asset_requests)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    packet_args = argparse.Namespace(scan_root=as_abs(args.scan_root), images_per_object=args.images_per_object, thumb_size=args.thumb_size)
    generation_rows = [packeting.asset_generation_row(row) for row in asset_needed_rows]
    generated_packets = [base_packets.generate_packet(row, packet_args, output_dir) for row in generation_rows]
    generated_by_id = {str(row["blind_review_id"]): row for row in generated_packets}
    updated_by_id = {
        str(row["blind_review_id"]): update_replacement_seed(row, generated_by_id[str(row["blind_review_id"])])
        for row in asset_needed_rows
    }
    final_rows: list[dict[str, Any]] = []
    for row in combined_rows:
        blind_id = str(row.get("blind_review_id"))
        final_rows.append(updated_by_id.get(blind_id, row))
    final_rows = sorted(
        final_rows,
        key=lambda row: (
            str(row.get("predicate_family")),
            str(row.get("semantic_geometry_bucket_hidden")),
            str(row.get("blind_review_id")),
        ),
    )

    final_label_rows = [visible_row(row, output_dir) for row in final_rows]
    final_ready_candidate_rows = [row for row in final_label_rows if row.get("evidence_packet_status") in {"ready", "limited_view_evaluable"}]
    generated_non_ready = [row for row in generated_packets if row.get("packet_status") != "ready"]
    final_non_ready = non_ready_rows(final_rows)
    path_errors = packet_path_errors(final_label_rows, output_dir)
    field_hits = mining.field_leakage_hits(FINAL_VISIBLE_FIELDS)
    value_hits = visible_value_leakage_hits(final_label_rows)
    packet_text_hits = packeting.packet_text_leakage_hits(generated_packets)
    leakage_hits = field_hits + value_hits + packet_text_hits
    if path_errors:
        validation_errors.append({"error_type": "packet_path_errors", "count": len(path_errors)})
    if leakage_hits:
        validation_errors.append({"error_type": "visible_or_packet_leakage", "count": len(leakage_hits)})

    final_status_counts = Counter(row.get("evidence_packet_status") for row in final_label_rows)
    generated_status_counts = Counter(row.get("packet_status") for row in generated_packets)
    all_ready_or_limited = len(final_ready_candidate_rows) == len(final_label_rows)
    if all_ready_or_limited and not generated_non_ready and not validation_errors:
        status = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets_ready_for_label_readiness"
        next_todo = "reliability_target_v7_object_cell_evidence_contrast_label_readiness"
        decision = "Replacement asset packets completed the restored 240-row v7 queue; proceed to label readiness."
    elif final_ready_candidate_rows and not validation_errors:
        status = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets_partial_needs_gap_audit"
        next_todo = "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packet_gap_audit"
        decision = "Replacement asset packet generation produced non-ready rows; run a focused gap audit before label readiness."
    else:
        status = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets_blocked"
        next_todo = "fix_reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets"
        decision = "Replacement asset packet generation is blocked by validation, path, or leakage errors."

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "final_label_sheet": output_dir / "v7_object_cell_evidence_contrast_restored_label_sheet.tsv",
        "final_label_ready_candidate_sheet": output_dir / "v7_object_cell_evidence_contrast_restored_label_ready_candidate_sheet.tsv",
        "final_manifest_post_label_only": output_dir / "v7_object_cell_evidence_contrast_restored_manifest_post_label_only.jsonl",
        "final_label_ready_candidate_manifest": output_dir / "v7_object_cell_evidence_contrast_restored_label_ready_candidate_manifest.jsonl",
        "generated_replacement_packet_manifest": output_dir / "generated_replacement_packet_manifest.jsonl",
        "generated_non_ready_packet_rows": output_dir / "generated_non_ready_packet_rows.jsonl",
        "final_non_ready_rows": output_dir / "final_non_ready_rows.jsonl",
        "bucket_packet_summary": output_dir / "bucket_packet_summary.csv",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "visible_value_leakage_hits": output_dir / "visible_value_leakage_hits.jsonl",
        "packet_text_leakage_hits": output_dir / "packet_text_leakage_hits.jsonl",
        "label_surface_leakage_hits": output_dir / "label_surface_leakage_hits.jsonl",
        "input_validation_errors": output_dir / "input_validation_errors.json",
        "asset_request_snapshot": output_dir / "asset_request_snapshot.jsonl",
        "packets_dir": output_dir / "packets",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": {
            "replacement_summary": rel_path(args.replacement_summary),
            "combined_manifest": rel_path(args.combined_manifest),
            "replacement_asset_needed": rel_path(args.replacement_asset_needed),
            "replacement_asset_requests": rel_path(args.replacement_asset_requests),
            "scan_root": rel_path(args.scan_root),
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
        "source_replacement_status": replacement_summary.get("status"),
        "counts": {
            "input_combined_rows": len(combined_rows),
            "replacement_asset_needed_input_rows": len(asset_needed_rows),
            "generated_replacement_packet_rows": len(generated_packets),
            "generated_non_ready_rows": len(generated_non_ready),
            "final_label_sheet_rows": len(final_label_rows),
            "final_label_ready_candidate_rows": len(final_ready_candidate_rows),
            "final_non_ready_rows": len(final_non_ready),
            "packet_path_errors": len(path_errors),
            "field_leakage_hits": len(field_hits),
            "visible_value_leakage_hits": len(value_hits),
            "packet_text_leakage_hits": len(packet_text_hits),
            "leakage_hits": len(leakage_hits),
            "validation_errors": len(validation_errors),
            "by_family": dict(sorted(Counter(row.get("predicate_family") for row in final_rows).items())),
            "by_bucket": dict(sorted(Counter(row.get("semantic_geometry_bucket_hidden") for row in final_rows).items())),
            "by_family_bucket": dict(sorted(Counter(f"{row.get('predicate_family')}|{row.get('semantic_geometry_bucket_hidden')}" for row in final_rows).items())),
        },
        "final_evidence_status_counts": dict(sorted(final_status_counts.items())),
        "generated_packet_status_counts": dict(sorted(generated_status_counts.items())),
        "generated_packet_coverage": {
            "subject_image_rows": sum(1 for row in generated_packets if int(row.get("subject_image_count") or 0) > 0),
            "object_image_rows": sum(1 for row in generated_packets if int(row.get("object_image_count") or 0) > 0),
            "contact_sheet_rows": sum(1 for row in generated_packets if row.get("contact_sheet_ready")),
            "mesh_packet_rows": sum(1 for row in generated_packets if row.get("mesh_packet_ready")),
        },
        "validation_error_count": len(validation_errors),
        "label_fill_allowed": False,
        "posterior_allowed": False,
    }

    write_tsv(output_paths["final_label_sheet"], final_label_rows, FINAL_VISIBLE_FIELDS)
    write_tsv(output_paths["final_label_ready_candidate_sheet"], final_ready_candidate_rows, FINAL_VISIBLE_FIELDS)
    write_jsonl(output_paths["final_manifest_post_label_only"], final_rows)
    write_jsonl(
        output_paths["final_label_ready_candidate_manifest"],
        [row for row in final_rows if evidence_status(row) in {"ready", "limited_view_evaluable"}],
    )
    write_jsonl(output_paths["generated_replacement_packet_manifest"], generated_packets)
    write_jsonl(output_paths["generated_non_ready_packet_rows"], generated_non_ready)
    write_jsonl(output_paths["final_non_ready_rows"], final_non_ready)
    write_csv(output_paths["bucket_packet_summary"], bucket_summary_rows(final_rows))
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_jsonl(output_paths["visible_value_leakage_hits"], value_hits)
    write_jsonl(output_paths["packet_text_leakage_hits"], packet_text_hits)
    write_jsonl(output_paths["label_surface_leakage_hits"], leakage_hits)
    write_json(output_paths["input_validation_errors"], validation_errors)
    write_jsonl(output_paths["asset_request_snapshot"], asset_requests)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        f"status={summary['status']} "
        f"combined={summary['counts']['input_combined_rows']} "
        f"generated={summary['counts']['generated_replacement_packet_rows']} "
        f"generated_non_ready={summary['counts']['generated_non_ready_rows']} "
        f"final_ready_candidates={summary['counts']['final_label_ready_candidate_rows']} "
        f"path_errors={summary['counts']['packet_path_errors']} "
        f"leakage={summary['counts']['leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
