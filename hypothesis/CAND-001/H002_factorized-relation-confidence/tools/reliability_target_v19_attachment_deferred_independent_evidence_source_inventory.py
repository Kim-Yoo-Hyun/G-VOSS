#!/usr/bin/env python3
"""Inventory independent visual/mesh evidence for H002 v19 attachment rows."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_repair_plan"
DEFAULT_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_candidate_mining"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_label_ingestion"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_source_inventory"

EXPECTED_PLAN_STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_repair_plan_ready_for_source_inventory"
EXPECTED_PLAN_NEXT = "reliability_target_v19_attachment_deferred_independent_evidence_source_inventory"
EXPECTED_CANDIDATE_STATUS = "h002_reliability_target_v18_attachment_deferred_candidate_mining_ready_for_label_fill"
EXPECTED_INGESTION_STATUS = "h002_reliability_target_v18_attachment_deferred_label_ingested_positive_sparse_with_probe_risk"

STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_source_inventory_ready"
NEXT_TODO = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan"

INSTANCE_RE = re.compile(r"^instance_(?P<instance_id>\d+)_class_(?P<label>.+?)_(?P<kind>croped_view|view)(?P<view_rank>\d+)(?:_score_(?P<score>[-+0-9.eE]+)_ratio_(?P<ratio>[-+0-9.eE]+))?(?:_(?P<frame_id>\d+))?_(?P<side>[AB])\.jpg$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def summarize_scores(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "max": None, "mean": None}
    return {"count": len(values), "max": max(values), "mean": sum(values) / len(values)}


def empty_instance_record() -> dict[str, Any]:
    return {
        "crop_count": 0,
        "origin_count": 0,
        "crop_view_ranks": set(),
        "origin_view_ranks": set(),
        "origin_frame_ids": set(),
        "crop_scores": [],
        "crop_ratios": [],
        "crop_files": [],
        "origin_files": [],
    }


def scan_inventory(scan_dir: Path) -> dict[str, Any]:
    inventory: dict[str, Any] = {
        "scan_exists": scan_dir.is_dir(),
        "multi_view_exists": False,
        "sequence_exists": False,
        "sequence_color_frames": 0,
        "sequence_depth_frames": 0,
        "sequence_pose_frames": 0,
        "mesh_obj_exists": False,
        "aligned_instance_ply_exists": False,
        "instance_ply_exists": False,
        "semseg_json_exists": False,
        "segment_json_exists": False,
        "instances": defaultdict(empty_instance_record),
    }
    if not scan_dir.is_dir():
        return inventory

    mv_dir = scan_dir / "multi_view"
    seq_dir = scan_dir / "sequence"
    inventory["multi_view_exists"] = mv_dir.is_dir()
    inventory["sequence_exists"] = seq_dir.is_dir()
    inventory["mesh_obj_exists"] = (scan_dir / "mesh.refined.v2.obj").is_file()
    inventory["aligned_instance_ply_exists"] = (scan_dir / "labels.instances.align.annotated.v2.ply").is_file()
    inventory["instance_ply_exists"] = (scan_dir / "labels.instances.annotated.v2.ply").is_file()
    inventory["semseg_json_exists"] = (scan_dir / "semseg.v2.json").is_file()
    inventory["segment_json_exists"] = (scan_dir / "mesh.refined.0.010000.segs.v2.json").is_file()

    if seq_dir.is_dir():
        inventory["sequence_color_frames"] = sum(1 for _ in seq_dir.glob("frame-*.color.jpg"))
        inventory["sequence_depth_frames"] = sum(1 for _ in seq_dir.glob("frame-*.depth.pgm"))
        inventory["sequence_pose_frames"] = sum(1 for _ in seq_dir.glob("frame-*.pose.txt"))

    if mv_dir.is_dir():
        for file_path in mv_dir.glob("instance_*_class_*"):
            if not file_path.is_file() or file_path.suffix.lower() != ".jpg":
                continue
            match = INSTANCE_RE.match(file_path.name)
            if not match:
                continue
            instance_id = int(match.group("instance_id"))
            record = inventory["instances"][instance_id]
            kind = match.group("kind")
            view_rank = int(match.group("view_rank"))
            if kind == "croped_view":
                record["crop_count"] += 1
                record["crop_view_ranks"].add(view_rank)
                score = parse_float(match.group("score"))
                ratio = parse_float(match.group("ratio"))
                if score is not None:
                    record["crop_scores"].append(score)
                if ratio is not None:
                    record["crop_ratios"].append(ratio)
                if len(record["crop_files"]) < 5:
                    record["crop_files"].append(rel_path(file_path))
            elif kind == "view":
                record["origin_count"] += 1
                record["origin_view_ranks"].add(view_rank)
                frame_id = match.group("frame_id")
                if frame_id is not None:
                    record["origin_frame_ids"].add(int(frame_id))
                if len(record["origin_files"]) < 5:
                    record["origin_files"].append(rel_path(file_path))
    return inventory


def instance_summary(scan_inv: dict[str, Any], instance_id: int) -> dict[str, Any]:
    record = scan_inv["instances"].get(instance_id, empty_instance_record())
    return {
        "crop_count": record["crop_count"],
        "origin_count": record["origin_count"],
        "crop_view_ranks": sorted(record["crop_view_ranks"]),
        "origin_view_ranks": sorted(record["origin_view_ranks"]),
        "origin_frame_ids": sorted(record["origin_frame_ids"]),
        "crop_score": summarize_scores(record["crop_scores"]),
        "crop_ratio": summarize_scores(record["crop_ratios"]),
        "crop_file_examples": record["crop_files"],
        "origin_file_examples": record["origin_files"],
    }


def classify_row(scan_inv: dict[str, Any], subj: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any]:
    subject_crop = subj["crop_count"]
    object_crop = obj["crop_count"]
    subject_origin = subj["origin_count"]
    object_origin = obj["origin_count"]
    shared_crop_view_ranks = sorted(set(subj["crop_view_ranks"]) & set(obj["crop_view_ranks"]))
    shared_origin_view_ranks = sorted(set(subj["origin_view_ranks"]) & set(obj["origin_view_ranks"]))
    shared_origin_frames = sorted(set(subj["origin_frame_ids"]) & set(obj["origin_frame_ids"]))

    both_have_crops = subject_crop > 0 and object_crop > 0
    both_have_origin = subject_origin > 0 and object_origin > 0
    sequence_ready = bool(scan_inv["sequence_exists"] and scan_inv["sequence_color_frames"] > 0 and scan_inv["sequence_pose_frames"] > 0)
    mesh_ready = bool(scan_inv["mesh_obj_exists"] and scan_inv["aligned_instance_ply_exists"] and scan_inv["semseg_json_exists"])

    if not scan_inv["scan_exists"]:
        visual_context_state = "scan_missing"
    elif not scan_inv["multi_view_exists"]:
        visual_context_state = "multi_view_missing"
    elif shared_origin_frames:
        visual_context_state = "same_frame_covisible_strong"
    elif shared_origin_view_ranks or shared_crop_view_ranks:
        visual_context_state = "same_view_rank_weak_proxy"
    elif both_have_crops or both_have_origin:
        visual_context_state = "both_instances_have_separate_views"
    elif subject_crop > 0 or object_crop > 0 or subject_origin > 0 or object_origin > 0:
        visual_context_state = "one_instance_view_only"
    else:
        visual_context_state = "no_instance_views"

    if not scan_inv["scan_exists"]:
        audit_ready_state = "not_ready_scan_missing"
        missing_reason = "scan_directory_missing"
    elif not scan_inv["multi_view_exists"] and not mesh_ready:
        audit_ready_state = "not_ready_no_visual_or_mesh"
        missing_reason = "multi_view_and_mesh_missing"
    elif shared_origin_frames:
        audit_ready_state = "strong_pair_visual_audit_ready"
        missing_reason = "none"
    elif both_have_crops and sequence_ready and mesh_ready:
        audit_ready_state = "individual_visual_plus_mesh_audit_ready"
        missing_reason = "no_exact_same_frame_overlap"
    elif both_have_crops and mesh_ready:
        audit_ready_state = "mesh_plus_individual_crop_limited_ready"
        missing_reason = "sequence_or_same_frame_context_missing"
    elif mesh_ready:
        audit_ready_state = "mesh_only_limited_ready"
        missing_reason = "subject_or_object_crop_missing"
    elif both_have_crops:
        audit_ready_state = "visual_only_limited_ready"
        missing_reason = "mesh_missing"
    else:
        audit_ready_state = "not_ready_insufficient_instance_views"
        missing_reason = "subject_or_object_visual_evidence_missing"

    return {
        "both_have_crops": both_have_crops,
        "both_have_origin_views": both_have_origin,
        "shared_crop_view_rank_count": len(shared_crop_view_ranks),
        "shared_origin_view_rank_count": len(shared_origin_view_ranks),
        "shared_origin_frame_count": len(shared_origin_frames),
        "shared_crop_view_ranks": shared_crop_view_ranks,
        "shared_origin_view_ranks": shared_origin_view_ranks,
        "shared_origin_frames": shared_origin_frames,
        "sequence_ready": sequence_ready,
        "mesh_ready": mesh_ready,
        "visual_context_state": visual_context_state,
        "audit_ready_state": audit_ready_state,
        "audit_ready_binary": audit_ready_state in {
            "strong_pair_visual_audit_ready",
            "individual_visual_plus_mesh_audit_ready",
            "mesh_plus_individual_crop_limited_ready",
            "mesh_only_limited_ready",
            "visual_only_limited_ready",
        },
        "strong_pair_visual_ready": audit_ready_state == "strong_pair_visual_audit_ready",
        "missing_reason": missing_reason,
    }


def validate_inputs(
    plan_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    ingestion_summary: dict[str, Any],
    manifest_rows: list[dict[str, Any]],
    ingested_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "expected": EXPECTED_PLAN_STATUS, "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "expected": EXPECTED_PLAN_NEXT, "actual": plan_summary.get("next_todo")})
    if candidate_summary.get("status") != EXPECTED_CANDIDATE_STATUS:
        errors.append({"error_type": "unexpected_candidate_status", "expected": EXPECTED_CANDIDATE_STATUS, "actual": candidate_summary.get("status")})
    if ingestion_summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "expected": EXPECTED_INGESTION_STATUS, "actual": ingestion_summary.get("status")})

    for source, payload in [("plan", plan_summary), ("candidate", candidate_summary), ("ingestion", ingestion_summary)]:
        boundary = payload.get("boundary", {})
        for key in ["validation_usage", "test_usage", "posterior_smoke_allowed", "trains_new_posterior", "paper_evidence_allowed", "h001_artifacts_modified", "multi_view_as_model_input"]:
            if boundary.get(key) is not False:
                errors.append({"error_type": "boundary_violation", "source": source, "key": key, "expected": False, "actual": boundary.get(key)})

    if len(manifest_rows) != 240:
        errors.append({"error_type": "unexpected_manifest_rows", "expected": 240, "actual": len(manifest_rows)})
    if len(ingested_rows) != 240:
        errors.append({"error_type": "unexpected_ingested_rows", "expected": 240, "actual": len(ingested_rows)})
    manifest_ids = [row.get("blind_review_id") for row in manifest_rows]
    ingested_ids = [row.get("blind_review_id") for row in ingested_rows]
    if len(set(manifest_ids)) != len(manifest_ids):
        errors.append({"error_type": "duplicate_manifest_blind_review_id"})
    if set(manifest_ids) != set(ingested_ids):
        errors.append({"error_type": "manifest_ingested_id_mismatch", "manifest_only": sorted(set(manifest_ids) - set(ingested_ids))[:10], "ingested_only": sorted(set(ingested_ids) - set(manifest_ids))[:10]})
    for row in manifest_rows:
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_manifest_row", "blind_review_id": row.get("blind_review_id"), "split": row.get("split")})
    return errors


def build_rows(
    manifest_rows: list[dict[str, Any]],
    ingested_rows: list[dict[str, Any]],
    three_rscan_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = as_abs(three_rscan_root)
    ingested_by_id = {row["blind_review_id"]: row for row in ingested_rows}
    scan_cache: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    for manifest in manifest_rows:
        blind_id = manifest["blind_review_id"]
        ingested = ingested_by_id.get(blind_id, {})
        scan_id = manifest["scan_id"]
        if scan_id not in scan_cache:
            scan_cache[scan_id] = scan_inventory(root / scan_id)
        inv = scan_cache[scan_id]
        subject_id = int(manifest["subject_id"])
        object_id = int(manifest["object_id"])
        subj = instance_summary(inv, subject_id)
        obj = instance_summary(inv, object_id)
        pair = classify_row(inv, subj, obj)

        rows.append(
            {
                "schema_version": "h002_reliability_target_v19_attachment_source_inventory_v1",
                "blind_review_id": blind_id,
                "scan_id": scan_id,
                "subgraph_id": manifest.get("subgraph_id"),
                "source_id": manifest.get("source_id"),
                "split": manifest.get("split"),
                "predicate_label": manifest.get("predicate_label"),
                "predicate_family": manifest.get("predicate_family"),
                "candidate_role_hidden": manifest.get("candidate_role_hidden"),
                "cell_id_hidden": manifest.get("cell_id_hidden"),
                "subject_id": subject_id,
                "subject_label": manifest.get("subject_label"),
                "object_id": object_id,
                "object_label": manifest.get("object_label"),
                "relation_family_visible": ingested.get("relation_family_visible"),
                "scan_exists": inv["scan_exists"],
                "multi_view_exists": inv["multi_view_exists"],
                "sequence_exists": inv["sequence_exists"],
                "sequence_color_frames": inv["sequence_color_frames"],
                "sequence_depth_frames": inv["sequence_depth_frames"],
                "sequence_pose_frames": inv["sequence_pose_frames"],
                "mesh_obj_exists": inv["mesh_obj_exists"],
                "aligned_instance_ply_exists": inv["aligned_instance_ply_exists"],
                "instance_ply_exists": inv["instance_ply_exists"],
                "semseg_json_exists": inv["semseg_json_exists"],
                "segment_json_exists": inv["segment_json_exists"],
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
    rows_by_visual_context = Counter(row["visual_context_state"] for row in rows)
    rows_by_audit_ready = Counter(row["audit_ready_state"] for row in rows)
    primary = [row for row in rows if row["candidate_role_hidden"] == "primary_binary_candidate"]
    by_predicate_primary: dict[str, dict[str, int]] = {}
    for predicate in sorted({row["predicate_label"] for row in primary}):
        subset = [row for row in primary if row["predicate_label"] == predicate]
        by_predicate_primary[predicate] = {
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
    gates = {
        "primary_rows_with_subject_and_object_crops_min_100": sum(1 for row in primary if row["both_have_crops"]) >= 100,
        "primary_rows_with_possible_covisible_or_same_view_context_min_60": primary_possible_covisible_or_same_view >= 60,
        "hanging_or_attached_each_audit_ready_min_30": all(
            by_predicate_primary.get(predicate, {}).get("audit_ready", 0) >= 30
            for predicate in ["attached to", "hanging on"]
        ),
    }
    return {
        "rows": len(rows),
        "rows_by_predicate": dict(rows_by_predicate),
        "rows_by_role": dict(rows_by_role),
        "rows_by_visual_context_state": dict(rows_by_visual_context),
        "rows_by_audit_ready_state": dict(rows_by_audit_ready),
        "audit_ready_rows": sum(1 for row in rows if row["audit_ready_binary"]),
        "strong_pair_visual_ready_rows": sum(1 for row in rows if row["strong_pair_visual_ready"]),
        "both_have_crop_rows": sum(1 for row in rows if row["both_have_crops"]),
        "primary_rows": len(primary),
        "primary_both_have_crop_rows": sum(1 for row in primary if row["both_have_crops"]),
        "primary_possible_covisible_or_same_view_rows": primary_possible_covisible_or_same_view,
        "primary_audit_ready_rows": sum(1 for row in primary if row["audit_ready_binary"]),
        "primary_by_predicate": by_predicate_primary,
        "source_inventory_gate_pass": all(gates.values()),
        "source_inventory_gates": gates,
    }


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    gates = counts["source_inventory_gates"]
    lines = [
        "# H002 V19 Attachment Source Inventory",
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
        f"strong_pair_visual_ready_rows = {counts['strong_pair_visual_ready_rows']}",
        f"rows_by_visual_context_state = {counts['rows_by_visual_context_state']}",
        f"rows_by_audit_ready_state = {counts['rows_by_audit_ready_state']}",
        "```",
        "",
        "## Gates",
        "",
        "```text",
    ]
    lines.extend([f"{key} = {value}" for key, value in gates.items()])
    lines.extend(
        [
            "```",
            "",
            "## Interpretation",
            "",
            "This stage inventories availability only. It does not fill labels, mine new candidates, train a posterior, or promote multi-view as a deployable input feature.",
            "",
            "If the gates pass, the next step is an audit-packet plan using visual/mesh evidence as independent label confirmation. If same-frame visual evidence is sparse, the audit packet should explicitly distinguish strong same-frame rows from individual-view-plus-mesh rows.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    candidate_summary = read_json(args.candidate_dir / "summary.json")
    ingestion_summary = read_json(args.ingestion_dir / "summary.json")
    manifest_rows = read_jsonl(args.candidate_dir / "hidden_audit_manifest_v18.jsonl")
    ingested_rows = read_jsonl(args.ingestion_dir / "ingested_rows.jsonl")

    validation_errors = validate_inputs(plan_summary, candidate_summary, ingestion_summary, manifest_rows, ingested_rows)
    inventory_rows, scan_summary = build_rows(manifest_rows, ingested_rows, args.three_rscan_root)
    counts = build_counts(inventory_rows)

    # Validate inventory output without converting it into labels.
    if len(inventory_rows) != len(manifest_rows):
        validation_errors.append({"error_type": "inventory_row_count_mismatch", "expected": len(manifest_rows), "actual": len(inventory_rows)})
    if any(row["split"] != "train" for row in inventory_rows):
        validation_errors.append({"error_type": "non_train_inventory_row"})

    fieldnames = [
        "blind_review_id",
        "scan_id",
        "subgraph_id",
        "predicate_label",
        "candidate_role_hidden",
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
        "schema_version": "h002_reliability_target_v19_attachment_source_inventory_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "next_todo": NEXT_TODO,
        "input_paths": {
            "plan_summary": rel_path(args.plan_dir / "summary.json"),
            "candidate_summary": rel_path(args.candidate_dir / "summary.json"),
            "hidden_manifest": rel_path(args.candidate_dir / "hidden_audit_manifest_v18.jsonl"),
            "ingestion_summary": rel_path(args.ingestion_dir / "summary.json"),
            "ingested_rows": rel_path(args.ingestion_dir / "ingested_rows.jsonl"),
            "three_rscan_root": rel_path(args.three_rscan_root),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
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

    print(f"status={STATUS}")
    print(f"next={NEXT_TODO}")
    print(f"rows={counts['rows']}")
    print(f"source_inventory_gate_pass={counts['source_inventory_gate_pass']}")
    print(f"primary_both_have_crop_rows={counts['primary_both_have_crop_rows']}")
    print(f"primary_possible_covisible_or_same_view_rows={counts['primary_possible_covisible_or_same_view_rows']}")
    print(f"primary_audit_ready_rows={counts['primary_audit_ready_rows']}")
    print(f"validation_errors={len(validation_errors)}")
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
