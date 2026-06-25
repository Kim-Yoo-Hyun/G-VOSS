#!/usr/bin/env python3
"""Inventory visual/mesh evidence for H002 v22 hanging-on strict candidates."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v19_attachment_deferred_independent_evidence_source_inventory as v19inv


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory"

EXPECTED_CANDIDATE_STATUS = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining_ready_for_source_inventory"
EXPECTED_CANDIDATE_NEXT = "reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory"

STATUS_READY = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory_ready_for_audit_packet_plan"
STATUS_BLOCKED = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory_blocked"
STATUS_ERRORS = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory_validation_errors"
NEXT_TODO_READY = "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan"
NEXT_TODO_BLOCKED = "reliability_target_v22_hanging_on_strict_conditional_contrast_path_decision_after_source_inventory"

TARGET_ROWS = 240
ROLE_ACCEPT = "accept_proxy_supported_candidate"
ROLE_REJECT = "reject_proxy_contradicted_candidate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--three-rscan-root", type=Path, default=DEFAULT_3RSCAN_ROOT)
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


def read_tsv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", encoding="utf-8", newline="") as handle:
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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    candidate_summary: dict[str, Any],
    manifest_rows: list[dict[str, Any]],
    visible_sheet_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if candidate_summary.get("status") != EXPECTED_CANDIDATE_STATUS:
        errors.append(
            {
                "error_type": "unexpected_candidate_status",
                "expected": EXPECTED_CANDIDATE_STATUS,
                "actual": candidate_summary.get("status"),
            }
        )
    if candidate_summary.get("next_todo") != EXPECTED_CANDIDATE_NEXT:
        errors.append(
            {
                "error_type": "unexpected_candidate_next",
                "expected": EXPECTED_CANDIDATE_NEXT,
                "actual": candidate_summary.get("next_todo"),
            }
        )
    if candidate_summary.get("validation_errors") != 0:
        errors.append({"error_type": "candidate_validation_errors_present", "actual": candidate_summary.get("validation_errors")})

    boundary = candidate_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "materializes_packet_assets",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "candidate_boundary_violation", "key": key, "actual": boundary.get(key)})

    if len(manifest_rows) != TARGET_ROWS:
        errors.append({"error_type": "manifest_row_count_mismatch", "expected": TARGET_ROWS, "actual": len(manifest_rows)})
    if len(visible_sheet_rows) != TARGET_ROWS:
        errors.append({"error_type": "visible_sheet_row_count_mismatch", "expected": TARGET_ROWS, "actual": len(visible_sheet_rows)})

    manifest_ids = [row.get("blind_review_id") for row in manifest_rows]
    visible_ids = [row.get("blind_review_id") for row in visible_sheet_rows]
    if len(set(manifest_ids)) != len(manifest_ids):
        errors.append({"error_type": "duplicate_manifest_blind_review_id"})
    if len(set(visible_ids)) != len(visible_ids):
        errors.append({"error_type": "duplicate_visible_sheet_blind_review_id"})
    if set(manifest_ids) != set(visible_ids):
        errors.append(
            {
                "error_type": "manifest_visible_id_mismatch",
                "manifest_only": sorted(set(manifest_ids) - set(visible_ids))[:10],
                "visible_only": sorted(set(visible_ids) - set(manifest_ids))[:10],
            }
        )

    role_counts = Counter(row.get("planned_proxy_role") for row in manifest_rows)
    if role_counts != Counter({ROLE_ACCEPT: TARGET_ROWS // 2, ROLE_REJECT: TARGET_ROWS // 2}):
        errors.append({"error_type": "unexpected_proxy_role_balance", "actual": dict(role_counts)})
    predicate_counts = Counter(row.get("predicate_label") for row in manifest_rows)
    if predicate_counts != Counter({"hanging on": TARGET_ROWS}):
        errors.append({"error_type": "unexpected_predicate_counts", "actual": dict(predicate_counts)})
    return errors


def build_inventory_rows(
    manifest_rows: list[dict[str, Any]],
    visible_sheet_rows: list[dict[str, str]],
    three_rscan_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = as_abs(three_rscan_root)
    visible_by_id = {row["blind_review_id"]: row for row in visible_sheet_rows}
    scan_cache: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    for manifest in manifest_rows:
        blind_id = manifest["blind_review_id"]
        visible = visible_by_id.get(blind_id, {})
        scan_id = str(manifest["scan_id"])
        if scan_id not in scan_cache:
            scan_cache[scan_id] = v19inv.scan_inventory(root / scan_id)
        scan_inv = scan_cache[scan_id]
        subject_id = int(manifest["subject_id"])
        object_id = int(manifest["object_id"])
        subj = v19inv.instance_summary(scan_inv, subject_id)
        obj = v19inv.instance_summary(scan_inv, object_id)
        pair = v19inv.classify_row(scan_inv, subj, obj)
        rows.append(
            {
                "schema_version": "h002_reliability_target_v22_hanging_on_source_inventory_v1",
                "blind_review_id": blind_id,
                "scan_id": scan_id,
                "subgraph_id": manifest.get("subgraph_id"),
                "source_id": "open3dsg_train_full",
                "split": "train",
                "predicate_label": manifest.get("predicate_label"),
                "predicate_family": "attachment_deferred",
                "planned_proxy_role_hidden": manifest.get("planned_proxy_role"),
                "rank_band_hidden": manifest.get("rank_band"),
                "geometry_bucket_hidden": manifest.get("geometry_bucket"),
                "object_family_pair_hidden": manifest.get("object_family_pair"),
                "coverage_proxy_hidden": manifest.get("coverage_proxy"),
                "uncertainty_bucket_hidden": manifest.get("uncertainty_bucket"),
                "gt_label_match_status_hidden": manifest.get("gt_label_match_status"),
                "strict_group_value_hidden": manifest.get("strict_group_value"),
                "subject_id": subject_id,
                "subject_label": manifest.get("subject_label"),
                "object_id": object_id,
                "object_label": manifest.get("object_label"),
                "candidate_relation": visible.get("candidate_relation", manifest.get("candidate_relation")),
                "relation_family_visible": visible.get("relation_family_visible"),
                "scan_exists": scan_inv["scan_exists"],
                "multi_view_exists": scan_inv["multi_view_exists"],
                "sequence_exists": scan_inv["sequence_exists"],
                "sequence_color_frames": scan_inv["sequence_color_frames"],
                "sequence_depth_frames": scan_inv["sequence_depth_frames"],
                "sequence_pose_frames": scan_inv["sequence_pose_frames"],
                "mesh_obj_exists": scan_inv["mesh_obj_exists"],
                "aligned_instance_ply_exists": scan_inv["aligned_instance_ply_exists"],
                "instance_ply_exists": scan_inv["instance_ply_exists"],
                "semseg_json_exists": scan_inv["semseg_json_exists"],
                "segment_json_exists": scan_inv["segment_json_exists"],
                "subject_crop_count": subj["crop_count"],
                "subject_origin_count": subj["origin_count"],
                "subject_crop_score_max": subj["crop_score"]["max"],
                "subject_crop_score_mean": subj["crop_score"]["mean"],
                "subject_crop_ratio_max": subj["crop_ratio"]["max"],
                "subject_crop_ratio_mean": subj["crop_ratio"]["mean"],
                "object_crop_count": obj["crop_count"],
                "object_origin_count": obj["origin_count"],
                "object_crop_score_max": obj["crop_score"]["max"],
                "object_crop_score_mean": obj["crop_score"]["mean"],
                "object_crop_ratio_max": obj["crop_ratio"]["max"],
                "object_crop_ratio_mean": obj["crop_ratio"]["mean"],
                "both_have_crops": pair["both_have_crops"],
                "both_have_origin_views": pair["both_have_origin_views"],
                "shared_crop_view_rank_count": pair["shared_crop_view_rank_count"],
                "shared_origin_view_rank_count": pair["shared_origin_view_rank_count"],
                "shared_origin_frame_count": pair["shared_origin_frame_count"],
                "sequence_ready": pair["sequence_ready"],
                "mesh_ready": pair["mesh_ready"],
                "visual_context_state": pair["visual_context_state"],
                "audit_ready_state": pair["audit_ready_state"],
                "audit_ready_binary": pair["audit_ready_binary"],
                "strong_pair_visual_ready": pair["strong_pair_visual_ready"],
                "missing_reason": pair["missing_reason"],
                "subject_crop_file_examples": subj["crop_file_examples"],
                "object_crop_file_examples": obj["crop_file_examples"],
                "subject_origin_file_examples": subj["origin_file_examples"],
                "object_origin_file_examples": obj["origin_file_examples"],
                "shared_crop_view_ranks": pair["shared_crop_view_ranks"],
                "shared_origin_view_ranks": pair["shared_origin_view_ranks"],
                "shared_origin_frames": pair["shared_origin_frames"],
                "label_or_review_fields_used": False,
                "model_input_allowed_now": False,
                "visual_evidence_role_now": "audit_or_confirmation_only",
            }
        )

    scan_summary = {
        "unique_scans": len(scan_cache),
        "scan_exists": sum(1 for inv in scan_cache.values() if inv["scan_exists"]),
        "multi_view_exists": sum(1 for inv in scan_cache.values() if inv["multi_view_exists"]),
        "sequence_exists": sum(1 for inv in scan_cache.values() if inv["sequence_exists"]),
        "mesh_ready": sum(1 for inv in scan_cache.values() if inv["mesh_obj_exists"] and inv["aligned_instance_ply_exists"] and inv["semseg_json_exists"]),
    }
    return rows, scan_summary


def build_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_predicate = Counter(row["predicate_label"] for row in rows)
    rows_by_proxy = Counter(row["planned_proxy_role_hidden"] for row in rows)
    rows_by_visual_context = Counter(row["visual_context_state"] for row in rows)
    rows_by_audit_ready = Counter(row["audit_ready_state"] for row in rows)
    rows_by_rank_band = Counter(row["rank_band_hidden"] for row in rows)
    rows_by_geometry_bucket = Counter(row["geometry_bucket_hidden"] for row in rows)
    rows_by_coverage_proxy = Counter(row["coverage_proxy_hidden"] for row in rows)
    rows_by_uncertainty_bucket = Counter(row["uncertainty_bucket_hidden"] for row in rows)
    rows_by_gt_match = Counter(row["gt_label_match_status_hidden"] for row in rows)

    by_proxy_role: dict[str, dict[str, int]] = {}
    for proxy_role in sorted(rows_by_proxy):
        subset = [row for row in rows if row["planned_proxy_role_hidden"] == proxy_role]
        by_proxy_role[proxy_role] = {
            "rows": len(subset),
            "both_have_crops": sum(1 for row in subset if row["both_have_crops"]),
            "audit_ready": sum(1 for row in subset if row["audit_ready_binary"]),
            "same_frame_strong": sum(1 for row in subset if row["strong_pair_visual_ready"]),
            "same_view_rank_weak": sum(1 for row in subset if row["visual_context_state"] == "same_view_rank_weak_proxy"),
        }

    possible_covisible_or_same_view = sum(
        1
        for row in rows
        if row["strong_pair_visual_ready"] or row["visual_context_state"] == "same_view_rank_weak_proxy"
    )
    gates = {
        "rows_exactly_240": len(rows) == TARGET_ROWS,
        "hanging_on_rows_exactly_240": rows_by_predicate == Counter({"hanging on": TARGET_ROWS}),
        "subject_and_object_crops_min_200": sum(1 for row in rows if row["both_have_crops"]) >= 200,
        "possible_covisible_or_same_view_context_min_120": possible_covisible_or_same_view >= 120,
        "audit_ready_rows_min_200": sum(1 for row in rows if row["audit_ready_binary"]) >= 200,
        "accept_and_reject_each_audit_ready_min_100": all(
            by_proxy_role.get(role, {}).get("audit_ready", 0) >= 100
            for role in [ROLE_ACCEPT, ROLE_REJECT]
        ),
    }
    return {
        "rows": len(rows),
        "rows_by_predicate": dict(rows_by_predicate),
        "rows_by_proxy_role_hidden": dict(rows_by_proxy),
        "rows_by_rank_band_hidden": dict(rows_by_rank_band),
        "rows_by_geometry_bucket_hidden": dict(rows_by_geometry_bucket),
        "rows_by_coverage_proxy_hidden": dict(rows_by_coverage_proxy),
        "rows_by_uncertainty_bucket_hidden": dict(rows_by_uncertainty_bucket),
        "rows_by_gt_label_match_status_hidden": dict(rows_by_gt_match),
        "rows_by_visual_context_state": dict(rows_by_visual_context),
        "rows_by_audit_ready_state": dict(rows_by_audit_ready),
        "audit_ready_rows": sum(1 for row in rows if row["audit_ready_binary"]),
        "strong_pair_visual_ready_rows": sum(1 for row in rows if row["strong_pair_visual_ready"]),
        "both_have_crop_rows": sum(1 for row in rows if row["both_have_crops"]),
        "possible_covisible_or_same_view_rows": possible_covisible_or_same_view,
        "by_proxy_role": by_proxy_role,
        "strict_group_count_hidden": len(set(row["strict_group_value_hidden"] for row in rows)),
        "scan_count_hidden": len(set(row["scan_id"] for row in rows)),
        "visible_endpoint_pair_count_hidden": len(set(f"{row['subject_label']}|{row['object_label']}" for row in rows)),
        "source_inventory_gate_pass": all(gates.values()),
        "source_inventory_gates": gates,
    }


def validate_inventory(rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(rows) != len(manifest_rows):
        errors.append({"error_type": "inventory_row_count_mismatch", "expected": len(manifest_rows), "actual": len(rows)})
    if any(row["split"] != "train" for row in rows):
        errors.append({"error_type": "non_train_inventory_row"})
    if any(row["model_input_allowed_now"] is not False for row in rows):
        errors.append({"error_type": "inventory_row_model_input_allowed"})
    if any(row["label_or_review_fields_used"] is not False for row in rows):
        errors.append({"error_type": "inventory_row_used_label_or_review_fields"})
    return errors


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    lines = [
        "# H002 V22 Hanging-On Strict Source Inventory",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"source_inventory_gate_pass = {counts['source_inventory_gate_pass']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        f"multi_view_as_model_input = {summary['boundary']['multi_view_as_model_input']}",
        "```",
        "",
        "## Counts",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"both_have_crop_rows = {counts['both_have_crop_rows']}",
        f"possible_covisible_or_same_view_rows = {counts['possible_covisible_or_same_view_rows']}",
        f"audit_ready_rows = {counts['audit_ready_rows']}",
        f"strong_pair_visual_ready_rows = {counts['strong_pair_visual_ready_rows']}",
        f"rows_by_proxy_role_hidden = {counts['rows_by_proxy_role_hidden']}",
        f"rows_by_visual_context_state = {counts['rows_by_visual_context_state']}",
        f"rows_by_audit_ready_state = {counts['rows_by_audit_ready_state']}",
        f"scan_summary = {summary['scan_summary']}",
        "```",
        "",
        "## Gates",
        "",
        "```text",
    ]
    lines.extend(f"{key} = {value}" for key, value in counts["source_inventory_gates"].items())
    lines.extend(
        [
            "```",
            "",
            "## Boundary",
            "",
            "This stage inventories source availability only. Multi-view and mesh are audit/confirmation evidence, not deployable model input. It does not fill labels, train posterior, or modify H001 artifacts.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    candidate_dir = as_abs(args.candidate_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_summary = read_json(candidate_dir / "summary.json")
    manifest_rows = read_jsonl(candidate_dir / "hidden_candidate_manifest.jsonl")
    visible_sheet_rows = read_tsv(candidate_dir / "visible_candidate_sheet.tsv")
    validation_errors = validate_inputs(candidate_summary, manifest_rows, visible_sheet_rows)
    inventory_rows, scan_summary = build_inventory_rows(manifest_rows, visible_sheet_rows, args.three_rscan_root)
    validation_errors.extend(validate_inventory(inventory_rows, manifest_rows))
    counts = build_counts(inventory_rows)

    if validation_errors:
        status = STATUS_ERRORS
        next_todo = EXPECTED_CANDIDATE_NEXT
    elif counts["source_inventory_gate_pass"]:
        status = STATUS_READY
        next_todo = NEXT_TODO_READY
    else:
        status = STATUS_BLOCKED
        next_todo = NEXT_TODO_BLOCKED

    fieldnames = [
        "blind_review_id",
        "scan_id",
        "subgraph_id",
        "predicate_label",
        "planned_proxy_role_hidden",
        "rank_band_hidden",
        "geometry_bucket_hidden",
        "coverage_proxy_hidden",
        "uncertainty_bucket_hidden",
        "gt_label_match_status_hidden",
        "subject_id",
        "subject_label",
        "object_id",
        "object_label",
        "scan_exists",
        "multi_view_exists",
        "sequence_exists",
        "sequence_color_frames",
        "sequence_pose_frames",
        "mesh_ready",
        "subject_crop_count",
        "subject_origin_count",
        "subject_crop_score_max",
        "subject_crop_ratio_max",
        "object_crop_count",
        "object_origin_count",
        "object_crop_score_max",
        "object_crop_ratio_max",
        "both_have_crops",
        "shared_crop_view_rank_count",
        "shared_origin_view_rank_count",
        "shared_origin_frame_count",
        "visual_context_state",
        "audit_ready_state",
        "audit_ready_binary",
        "strong_pair_visual_ready",
        "missing_reason",
    ]

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "inventory_rows": output_dir / "inventory_rows.jsonl",
        "inventory_table": output_dir / "inventory_table.csv",
        "scan_summary": output_dir / "scan_summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": "h002_reliability_target_v22_hanging_on_source_inventory_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "input_paths": {
            "candidate_summary": rel_path(candidate_dir / "summary.json"),
            "visible_candidate_sheet": rel_path(candidate_dir / "visible_candidate_sheet.tsv"),
            "hidden_candidate_manifest": rel_path(candidate_dir / "hidden_candidate_manifest.jsonl"),
            "three_rscan_root": rel_path(args.three_rscan_root),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "candidate_mining_allowed": False,
            "audit_packet_plan_allowed_next": counts["source_inventory_gate_pass"] and not validation_errors,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_or_mesh_as_audit_or_confirmation_evidence_only": True,
            "label_or_review_fields_used": False,
        },
        "counts": counts,
        "scan_summary": scan_summary,
        "validation_errors": len(validation_errors),
    }
    write_json(output_paths["summary"], summary)
    write_json(output_paths["scan_summary"], scan_summary)
    write_jsonl(output_paths["inventory_rows"], inventory_rows)
    write_csv(output_paths["inventory_table"], inventory_rows, fieldnames)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(report_text(summary), encoding="utf-8")
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"rows={counts['rows']}")
    print(f"source_inventory_gate_pass={counts['source_inventory_gate_pass']}")
    print(f"both_have_crop_rows={counts['both_have_crop_rows']}")
    print(f"possible_covisible_or_same_view_rows={counts['possible_covisible_or_same_view_rows']}")
    print(f"audit_ready_rows={counts['audit_ready_rows']}")
    print(f"strong_pair_visual_ready_rows={counts['strong_pair_visual_ready_rows']}")
    print(f"validation_errors={summary['validation_errors']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
