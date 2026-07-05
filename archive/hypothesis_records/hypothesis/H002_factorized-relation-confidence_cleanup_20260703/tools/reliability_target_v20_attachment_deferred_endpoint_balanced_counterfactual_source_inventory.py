#!/usr/bin/env python3
"""Inventory visual/mesh evidence for the H002 v20 endpoint-balanced candidates."""

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

DEFAULT_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory"

EXPECTED_CANDIDATE_STATUS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_candidate_mining_ready_for_source_inventory"
)
EXPECTED_CANDIDATE_NEXT = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory"

STATUS_READY = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_source_inventory_ready_for_audit_packet_plan"
)
STATUS_BLOCKED = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_source_inventory_blocked"
)
STATUS_ERRORS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_source_inventory_validation_errors"
)
NEXT_TODO_READY = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan"
NEXT_TODO_BLOCKED = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_path_decision_after_source_inventory"


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
    candidate_sheet_rows: list[dict[str, str]],
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
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "candidate_boundary_violation", "key": key, "actual": boundary.get(key)})

    if len(manifest_rows) != 320:
        errors.append({"error_type": "manifest_row_count_mismatch", "expected": 320, "actual": len(manifest_rows)})
    if len(candidate_sheet_rows) != 320:
        errors.append({"error_type": "candidate_sheet_row_count_mismatch", "expected": 320, "actual": len(candidate_sheet_rows)})
    manifest_ids = [row.get("blind_review_id") for row in manifest_rows]
    sheet_ids = [row.get("blind_review_id") for row in candidate_sheet_rows]
    if len(set(manifest_ids)) != len(manifest_ids):
        errors.append({"error_type": "duplicate_manifest_blind_review_id"})
    if len(set(sheet_ids)) != len(sheet_ids):
        errors.append({"error_type": "duplicate_sheet_blind_review_id"})
    if set(manifest_ids) != set(sheet_ids):
        errors.append(
            {
                "error_type": "manifest_sheet_id_mismatch",
                "manifest_only": sorted(set(manifest_ids) - set(sheet_ids))[:10],
                "sheet_only": sorted(set(sheet_ids) - set(manifest_ids))[:10],
            }
        )
    for row in manifest_rows:
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_manifest_row", "blind_review_id": row.get("blind_review_id"), "split": row.get("split")})
        if row.get("model_input_allowed") is not False:
            errors.append({"error_type": "hidden_model_input_allowed", "blind_review_id": row.get("blind_review_id")})
    return errors


def build_inventory_rows(
    manifest_rows: list[dict[str, Any]],
    sheet_rows: list[dict[str, str]],
    three_rscan_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = as_abs(three_rscan_root)
    sheet_by_id = {row["blind_review_id"]: row for row in sheet_rows}
    scan_cache: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    for manifest in manifest_rows:
        blind_id = manifest["blind_review_id"]
        sheet = sheet_by_id.get(blind_id, {})
        scan_id = manifest["scan_id"]
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
                "schema_version": "h002_reliability_target_v20_attachment_source_inventory_v1",
                "blind_review_id": blind_id,
                "scan_id": scan_id,
                "subgraph_id": manifest.get("subgraph_id"),
                "source_id": manifest.get("source_id"),
                "split": manifest.get("split"),
                "predicate_label": manifest.get("predicate_label"),
                "predicate_family": manifest.get("predicate_family"),
                "candidate_role_hidden": manifest.get("candidate_role_hidden"),
                "proxy_role_hidden": manifest.get("proxy_role_hidden"),
                "capacity_evidence_tier_hidden": manifest.get("capacity_evidence_tier_hidden"),
                "selection_route_level_hidden": manifest.get("selection_route_level_hidden"),
                "cell_id_hidden": manifest.get("cell_id_hidden"),
                "subject_id": subject_id,
                "subject_label": manifest.get("subject_label"),
                "object_id": object_id,
                "object_label": manifest.get("object_label"),
                "candidate_relation": sheet.get("candidate_relation"),
                "relation_family_visible": sheet.get("relation_family_visible"),
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
    rows_by_role = Counter(row["candidate_role_hidden"] for row in rows)
    rows_by_proxy = Counter(f"{row['predicate_label']}|{row['proxy_role_hidden']}" for row in rows)
    rows_by_visual_context = Counter(row["visual_context_state"] for row in rows)
    rows_by_audit_ready = Counter(row["audit_ready_state"] for row in rows)
    primary = [row for row in rows if row["candidate_role_hidden"] == "primary_binary_candidate"]
    diagnostic = [row for row in rows if row["candidate_role_hidden"] == "connected_diagnostic_candidate"]
    by_predicate_primary: dict[str, dict[str, int]] = {}
    for predicate in ["attached to", "hanging on"]:
        subset = [row for row in primary if row["predicate_label"] == predicate]
        by_predicate_primary[predicate] = {
            "rows": len(subset),
            "both_have_crops": sum(1 for row in subset if row["both_have_crops"]),
            "audit_ready": sum(1 for row in subset if row["audit_ready_binary"]),
            "same_frame_strong": sum(1 for row in subset if row["strong_pair_visual_ready"]),
            "same_view_rank_weak": sum(1 for row in subset if row["visual_context_state"] == "same_view_rank_weak_proxy"),
        }
    by_proxy_role: dict[str, dict[str, int]] = {}
    for proxy_key in sorted(set(rows_by_proxy)):
        subset = [row for row in rows if f"{row['predicate_label']}|{row['proxy_role_hidden']}" == proxy_key]
        by_proxy_role[proxy_key] = {
            "rows": len(subset),
            "both_have_crops": sum(1 for row in subset if row["both_have_crops"]),
            "audit_ready": sum(1 for row in subset if row["audit_ready_binary"]),
            "same_frame_strong": sum(1 for row in subset if row["strong_pair_visual_ready"]),
            "same_view_rank_weak": sum(1 for row in subset if row["visual_context_state"] == "same_view_rank_weak_proxy"),
        }
    primary_possible_covisible_or_same_view = sum(
        1
        for row in primary
        if row["strong_pair_visual_ready"] or row["visual_context_state"] == "same_view_rank_weak_proxy"
    )
    diagnostic_audit_ready = sum(1 for row in diagnostic if row["audit_ready_binary"])
    gates = {
        "primary_rows_with_subject_and_object_crops_min_200": sum(1 for row in primary if row["both_have_crops"]) >= 200,
        "primary_rows_with_possible_covisible_or_same_view_context_min_120": primary_possible_covisible_or_same_view >= 120,
        "attached_and_hanging_each_audit_ready_min_50": all(
            by_predicate_primary.get(predicate, {}).get("audit_ready", 0) >= 50
            for predicate in ["attached to", "hanging on"]
        ),
        "connected_diagnostic_audit_ready_min_32": diagnostic_audit_ready >= 32,
    }
    return {
        "rows": len(rows),
        "rows_by_predicate": dict(rows_by_predicate),
        "rows_by_role": dict(rows_by_role),
        "rows_by_proxy": dict(rows_by_proxy),
        "rows_by_visual_context_state": dict(rows_by_visual_context),
        "rows_by_audit_ready_state": dict(rows_by_audit_ready),
        "audit_ready_rows": sum(1 for row in rows if row["audit_ready_binary"]),
        "strong_pair_visual_ready_rows": sum(1 for row in rows if row["strong_pair_visual_ready"]),
        "both_have_crop_rows": sum(1 for row in rows if row["both_have_crops"]),
        "primary_rows": len(primary),
        "primary_both_have_crop_rows": sum(1 for row in primary if row["both_have_crops"]),
        "primary_possible_covisible_or_same_view_rows": primary_possible_covisible_or_same_view,
        "primary_audit_ready_rows": sum(1 for row in primary if row["audit_ready_binary"]),
        "connected_diagnostic_rows": len(diagnostic),
        "connected_diagnostic_audit_ready_rows": diagnostic_audit_ready,
        "primary_by_predicate": by_predicate_primary,
        "by_proxy_role": by_proxy_role,
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
    return errors


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    lines = [
        "# H002 V20 Attachment Source Inventory",
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
        f"primary_rows = {counts['primary_rows']}",
        f"primary_both_have_crop_rows = {counts['primary_both_have_crop_rows']}",
        f"primary_possible_covisible_or_same_view_rows = {counts['primary_possible_covisible_or_same_view_rows']}",
        f"primary_audit_ready_rows = {counts['primary_audit_ready_rows']}",
        f"connected_diagnostic_rows = {counts['connected_diagnostic_rows']}",
        f"connected_diagnostic_audit_ready_rows = {counts['connected_diagnostic_audit_ready_rows']}",
        f"strong_pair_visual_ready_rows = {counts['strong_pair_visual_ready_rows']}",
        f"rows_by_visual_context_state = {counts['rows_by_visual_context_state']}",
        f"rows_by_audit_ready_state = {counts['rows_by_audit_ready_state']}",
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
            "This stage inventories source evidence only. It does not fill labels, train posterior, or promote multi-view/mesh as model input.",
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
    manifest_rows = read_jsonl(candidate_dir / "hidden_audit_manifest_v20.jsonl")
    sheet_rows = read_tsv(candidate_dir / "candidate_sheet_v20.tsv")
    validation_errors = validate_inputs(candidate_summary, manifest_rows, sheet_rows)
    inventory_rows, scan_summary = build_inventory_rows(manifest_rows, sheet_rows, args.three_rscan_root)
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
        "candidate_role_hidden",
        "proxy_role_hidden",
        "capacity_evidence_tier_hidden",
        "selection_route_level_hidden",
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
        "schema_version": "h002_reliability_target_v20_attachment_source_inventory_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "input_paths": {
            "candidate_summary": rel_path(candidate_dir / "summary.json"),
            "candidate_sheet": rel_path(candidate_dir / "candidate_sheet_v20.tsv"),
            "hidden_manifest": rel_path(candidate_dir / "hidden_audit_manifest_v20.jsonl"),
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
    print(f"primary_both_have_crop_rows={counts['primary_both_have_crop_rows']}")
    print(f"primary_possible_covisible_or_same_view_rows={counts['primary_possible_covisible_or_same_view_rows']}")
    print(f"primary_audit_ready_rows={counts['primary_audit_ready_rows']}")
    print(f"connected_diagnostic_audit_ready_rows={counts['connected_diagnostic_audit_ready_rows']}")
    print(f"validation_errors={summary['validation_errors']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
