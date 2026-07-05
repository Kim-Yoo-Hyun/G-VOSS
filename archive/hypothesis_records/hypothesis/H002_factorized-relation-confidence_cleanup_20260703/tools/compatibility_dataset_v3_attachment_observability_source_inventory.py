#!/usr/bin/env python3
"""Inventory R7 attachment-observability sources before materialization."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_TARGET_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_target_plan"
DEFAULT_TRAIN_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_PACKET_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_packet_materialization_v1"
DEFAULT_CANDIDATE_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_candidate_mining_v1"
DEFAULT_INGESTION_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_label_ingestion_v1"
DEFAULT_AUDIT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_target_independence_audit_v1"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_source_inventory"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_attachment_observability_target_plan_ready_for_source_inventory"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_attachment_observability_source_inventory"
EXPECTED_PACKET_STATUS = "h002_attachment_independent_positive_anchor_packet_materialization_v1_ready_for_label_fill"
EXPECTED_CANDIDATE_STATUS = "h002_attachment_independent_positive_anchor_candidate_mining_v1_ready_mixed_strata"
EXPECTED_INGESTION_STATUS = "h002_attachment_independent_positive_anchor_label_ingested_class_mass_pass_with_shortcut_risk"
EXPECTED_AUDIT_STATUS = "h002_attachment_independent_positive_anchor_target_independence_audit_blocked_shortcut_risk"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_attachment_observability_source_inventory_v1"
STATUS_READY = "h002_compatibility_dataset_v3_attachment_observability_source_inventory_ready_for_materialization_plan"
STATUS_LIMITED = "h002_compatibility_dataset_v3_attachment_observability_source_inventory_limited_connected_topology_diagnostic"
STATUS_ERROR = "h002_compatibility_dataset_v3_attachment_observability_source_inventory_input_errors"
SELECTED_PATH = "r7_source_inventory_supports_attached_hanging_materialization_connected_diagnostic"
NEXT_TODO = "compatibility_dataset_v3_attachment_observability_materialization_plan"
NEXT_TODO_ERROR = "fix_attachment_observability_source_inventory_inputs"

TARGET_PREDICATES = ("attached to", "hanging on", "connected to")
PRIMARY_PREDICATES = ("attached to", "hanging on")
DIAGNOSTIC_PREDICATES = ("connected to",)

INSTANCE_RE = re.compile(
    r"^instance_(?P<instance_id>\d+)_class_(?P<label>.+?)_"
    r"(?P<kind>croped_view|view)(?P<view_rank>\d+)"
    r"(?:_score_(?P<score>[-+0-9.eE]+)_ratio_(?P<ratio>[-+0-9.eE]+))?"
    r"(?:_(?P<frame_id>\d+))?_(?P<side>[AB])\.jpg$"
)

ATTACHMENT_ANCHOR_KEYWORDS = {
    "wall",
    "ceiling",
    "door",
    "window",
    "shelf",
    "cabinet",
    "rack",
    "frame",
    "board",
    "rail",
    "curtain",
    "blinds",
}
HANGING_ANCHOR_KEYWORDS = {
    "wall",
    "ceiling",
    "rail",
    "rack",
    "curtain",
    "blinds",
    "rod",
    "hook",
    "shelf",
}
CONNECTOR_KEYWORDS = {
    "cable",
    "cord",
    "wire",
    "pipe",
    "hose",
    "plug",
    "socket",
    "outlet",
    "switch",
    "lamp",
    "light",
    "radiator",
    "heater",
    "sink",
    "faucet",
    "shower",
    "toilet",
    "tv",
    "television",
    "monitor",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-plan-dir", type=Path, default=DEFAULT_TARGET_PLAN_DIR)
    parser.add_argument("--train-rga-dir", type=Path, default=DEFAULT_TRAIN_RGA_DIR)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def flatten(counter: Counter[Any], limit: int = 12) -> str:
    return "; ".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def numeric(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def contains_any(label: str | None, keywords: set[str]) -> bool:
    text = (label or "").lower()
    return any(keyword in text for keyword in keywords)


def validate_inputs(
    plan_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    ingestion_summary: dict[str, Any],
    audit_summary: dict[str, Any],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    for key in ["materializes_rows", "runs_model", "validation_usage", "test_usage", "h001_artifacts_modified"]:
        if plan_summary.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": plan_summary.get("boundary", {}).get(key)})

    if packet_summary.get("status") != EXPECTED_PACKET_STATUS:
        errors.append({"error_type": "unexpected_packet_status", "actual": packet_summary.get("status")})
    if candidate_summary.get("status") != EXPECTED_CANDIDATE_STATUS:
        errors.append({"error_type": "unexpected_candidate_status", "actual": candidate_summary.get("status")})
    if ingestion_summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "actual": ingestion_summary.get("status")})
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})

    boundary_sources = {
        "packet": packet_summary,
        "candidate": candidate_summary,
        "ingestion": ingestion_summary,
    }
    for source, payload in boundary_sources.items():
        boundary = payload.get("boundary", {})
        for key in ["validation_usage", "test_usage", "posterior_smoke_allowed", "paper_evidence_allowed", "h001_artifacts_modified"]:
            if boundary.get(key) is not False:
                errors.append({"error_type": "boundary_not_false", "source": source, "key": key, "actual": boundary.get(key)})
        for key in ["multi_view_as_model_input", "mesh_as_model_input"]:
            if boundary.get(key) is not False:
                errors.append({"error_type": "model_input_boundary_not_false", "source": source, "key": key, "actual": boundary.get(key)})

    required_paths = [
        args.train_rga_dir / "match_rows.jsonl",
        args.packet_dir / "label_ready_manifest.jsonl",
        args.packet_dir / "packet_manifest.jsonl",
        args.candidate_dir / "candidate_rows_internal.jsonl",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append({"error_type": "missing_required_input", "path": rel_path(path)})
    if not args.scan_root.exists():
        errors.append({"error_type": "missing_scan_root", "path": rel_path(args.scan_root)})
    return errors


def empty_instance_record() -> dict[str, Any]:
    return {
        "crop_count": 0,
        "origin_count": 0,
        "crop_view_ranks": set(),
        "origin_view_ranks": set(),
        "origin_frame_ids": set(),
        "crop_scores": [],
        "crop_ratios": [],
    }


def scan_inventory(scan_dir: Path, parse_instances: bool = False) -> dict[str, Any]:
    inventory: dict[str, Any] = {
        "scan_exists": scan_dir.is_dir(),
        "multi_view_exists": False,
        "sequence_dir_exists": False,
        "sequence_zip_exists": False,
        "sequence_color_frames": 0,
        "sequence_depth_frames": 0,
        "sequence_pose_frames": 0,
        "mesh_obj_exists": False,
        "aligned_instance_ply_exists": False,
        "instance_ply_exists": False,
        "semseg_json_exists": False,
        "segment_json_exists": False,
        "mesh_ready": False,
        "point_mesh_ready": False,
        "instances": defaultdict(empty_instance_record),
    }
    if not scan_dir.is_dir():
        return inventory

    mv_dir = scan_dir / "multi_view"
    seq_dir = scan_dir / "sequence"
    inventory["multi_view_exists"] = mv_dir.is_dir()
    inventory["sequence_dir_exists"] = seq_dir.is_dir()
    inventory["sequence_zip_exists"] = (scan_dir / "sequence.zip").is_file()
    inventory["mesh_obj_exists"] = (scan_dir / "mesh.refined.v2.obj").is_file()
    inventory["aligned_instance_ply_exists"] = (scan_dir / "labels.instances.align.annotated.v2.ply").is_file()
    inventory["instance_ply_exists"] = (scan_dir / "labels.instances.annotated.v2.ply").is_file()
    inventory["semseg_json_exists"] = (scan_dir / "semseg.v2.json").is_file()
    inventory["segment_json_exists"] = (scan_dir / "mesh.refined.0.010000.segs.v2.json").is_file()
    inventory["mesh_ready"] = bool(
        inventory["mesh_obj_exists"] and inventory["aligned_instance_ply_exists"] and inventory["semseg_json_exists"]
    )
    inventory["point_mesh_ready"] = bool(inventory["aligned_instance_ply_exists"] and inventory["semseg_json_exists"])

    if seq_dir.is_dir():
        inventory["sequence_color_frames"] = sum(1 for _ in seq_dir.glob("frame-*.color.jpg"))
        inventory["sequence_depth_frames"] = sum(1 for _ in seq_dir.glob("frame-*.depth.pgm"))
        inventory["sequence_pose_frames"] = sum(1 for _ in seq_dir.glob("frame-*.pose.txt"))

    if parse_instances and mv_dir.is_dir():
        for file_path in mv_dir.glob("instance_*_class_*"):
            if not file_path.is_file() or file_path.suffix.lower() != ".jpg":
                continue
            match = INSTANCE_RE.match(file_path.name)
            if not match:
                continue
            instance_id = int(match.group("instance_id"))
            record = inventory["instances"][instance_id]
            view_rank = int(match.group("view_rank"))
            if match.group("kind") == "croped_view":
                record["crop_count"] += 1
                record["crop_view_ranks"].add(view_rank)
                score = numeric(match.group("score"))
                ratio = numeric(match.group("ratio"))
                if score is not None:
                    record["crop_scores"].append(score)
                if ratio is not None:
                    record["crop_ratios"].append(ratio)
            else:
                record["origin_count"] += 1
                record["origin_view_ranks"].add(view_rank)
                frame_id = match.group("frame_id")
                if frame_id is not None:
                    record["origin_frame_ids"].add(int(frame_id))
    return inventory


def instance_summary(scan_inv: dict[str, Any], instance_id: int) -> dict[str, Any]:
    record = scan_inv["instances"].get(instance_id, empty_instance_record())
    return {
        "crop_count": record["crop_count"],
        "origin_count": record["origin_count"],
        "crop_view_ranks": sorted(record["crop_view_ranks"]),
        "origin_view_ranks": sorted(record["origin_view_ranks"]),
        "origin_frame_ids": sorted(record["origin_frame_ids"]),
        "crop_score_max": max(record["crop_scores"]) if record["crop_scores"] else None,
        "crop_ratio_max": max(record["crop_ratios"]) if record["crop_ratios"] else None,
    }


def classify_pair_visibility(scan_inv: dict[str, Any], subj: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any]:
    shared_crop = sorted(set(subj["crop_view_ranks"]) & set(obj["crop_view_ranks"]))
    shared_origin = sorted(set(subj["origin_view_ranks"]) & set(obj["origin_view_ranks"]))
    shared_frames = sorted(set(subj["origin_frame_ids"]) & set(obj["origin_frame_ids"]))
    both_have_crops = subj["crop_count"] > 0 and obj["crop_count"] > 0
    both_have_origin = subj["origin_count"] > 0 and obj["origin_count"] > 0
    sequence_ready = bool(scan_inv["sequence_dir_exists"] and scan_inv["sequence_color_frames"] > 0 and scan_inv["sequence_pose_frames"] > 0)
    if not scan_inv["scan_exists"]:
        state = "scan_missing"
    elif not scan_inv["multi_view_exists"]:
        state = "multi_view_missing"
    elif shared_frames:
        state = "same_frame_covisible_strong"
    elif shared_origin or shared_crop:
        state = "same_view_rank_weak_proxy"
    elif both_have_crops or both_have_origin:
        state = "both_instances_have_separate_views"
    elif subj["crop_count"] or obj["crop_count"] or subj["origin_count"] or obj["origin_count"]:
        state = "one_instance_view_only"
    else:
        state = "no_instance_views"
    if shared_frames:
        audit_state = "strong_pair_visual_audit_ready"
    elif both_have_crops and sequence_ready and scan_inv["mesh_ready"]:
        audit_state = "individual_visual_plus_mesh_audit_ready"
    elif both_have_crops and scan_inv["mesh_ready"]:
        audit_state = "mesh_plus_individual_crop_limited_ready"
    elif scan_inv["mesh_ready"]:
        audit_state = "mesh_only_limited_ready"
    elif both_have_crops:
        audit_state = "visual_only_limited_ready"
    else:
        audit_state = "not_ready_insufficient_instance_views"
    return {
        "visual_context_state": state,
        "audit_ready_state": audit_state,
        "audit_ready_binary": audit_state
        in {
            "strong_pair_visual_audit_ready",
            "individual_visual_plus_mesh_audit_ready",
            "mesh_plus_individual_crop_limited_ready",
            "mesh_only_limited_ready",
            "visual_only_limited_ready",
        },
        "both_have_crops": both_have_crops,
        "both_have_origin_views": both_have_origin,
        "shared_crop_view_rank_count": len(shared_crop),
        "shared_origin_view_rank_count": len(shared_origin),
        "shared_origin_frame_count": len(shared_frames),
        "strong_pair_visual_ready": bool(shared_frames),
    }


def extract_match_row_fields(row: dict[str, Any]) -> dict[str, Any]:
    edge = row.get("edge", {})
    ident = row.get("identity", {})
    label = row.get("label", {})
    geometry = row.get("geometry", {})
    rga = row.get("rga", {})
    semantic = row.get("semantic", {})
    predicate = row.get("predicate", {})
    subject_label = edge.get("subject_label")
    object_label = edge.get("object_label")
    pred = predicate.get("predicate_label")
    return {
        "predicate_label": pred,
        "scan_id": ident.get("scan_id"),
        "directed_pair_id": ident.get("directed_pair_id"),
        "subject_id": ident.get("subject_id"),
        "object_id": ident.get("object_id"),
        "subject_label": subject_label,
        "object_label": object_label,
        "class_pair": f"{subject_label}|{object_label}",
        "label_match_status": label.get("label_match_status"),
        "matched_predicates": label.get("matched_predicates") or [],
        "geometry_status": geometry.get("geometry_status"),
        "coverage_state": rga.get("coverage_state"),
        "rank_band": rga.get("rank_band"),
        "semantic_score_norm": semantic.get("semantic_score_norm"),
        "top50_semantic": bool(semantic.get("top50_semantic")),
        "top100_semantic": bool(semantic.get("top100_semantic")),
        "source_geometry_checkable": bool(geometry.get("geometry_checkable")),
        "source_geometry_available": bool(geometry.get("geometry_available")),
        "attachment_anchor_hint": contains_any(subject_label, ATTACHMENT_ANCHOR_KEYWORDS)
        or contains_any(object_label, ATTACHMENT_ANCHOR_KEYWORDS),
        "hanging_anchor_hint": contains_any(subject_label, HANGING_ANCHOR_KEYWORDS)
        or contains_any(object_label, HANGING_ANCHOR_KEYWORDS),
        "connector_semantic_hint": contains_any(subject_label, CONNECTOR_KEYWORDS)
        or contains_any(object_label, CONNECTOR_KEYWORDS),
    }


def build_full_train_inventory(match_rows_path: Path, scan_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    counts = Counter()
    label_status = Counter()
    geometry_status = Counter()
    coverage_state = Counter()
    rank_band = Counter()
    top_class_pairs = Counter()
    semantic_available = Counter()
    top50 = Counter()
    top100 = Counter()
    source_geometry_available = Counter()
    source_geometry_checkable = Counter()
    anchor_hints = Counter()
    scan_ids: set[str] = set()
    directed_pairs: set[str] = set()

    with match_rows_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            fields = extract_match_row_fields(row)
            pred = fields["predicate_label"]
            if pred not in TARGET_PREDICATES:
                continue
            counts[pred] += 1
            if fields["scan_id"]:
                scan_ids.add(fields["scan_id"])
            if fields["directed_pair_id"]:
                directed_pairs.add(fields["directed_pair_id"])
            label_status[f"{pred}|{fields['label_match_status']}"] += 1
            geometry_status[f"{pred}|{fields['geometry_status']}"] += 1
            coverage_state[f"{pred}|{fields['coverage_state']}"] += 1
            rank_band[f"{pred}|{fields['rank_band']}"] += 1
            top_class_pairs[f"{pred}|{fields['class_pair']}"] += 1
            semantic_available[pred] += int(fields["semantic_score_norm"] is not None)
            top50[pred] += int(fields["top50_semantic"])
            top100[pred] += int(fields["top100_semantic"])
            source_geometry_available[pred] += int(fields["source_geometry_available"])
            source_geometry_checkable[pred] += int(fields["source_geometry_checkable"])
            if fields["attachment_anchor_hint"]:
                anchor_hints[f"{pred}|attachment_anchor_hint"] += 1
            if fields["hanging_anchor_hint"]:
                anchor_hints[f"{pred}|hanging_anchor_hint"] += 1
            if fields["connector_semantic_hint"]:
                anchor_hints[f"{pred}|connector_semantic_hint"] += 1

    scan_assets: dict[str, dict[str, Any]] = {}
    for scan_id in sorted(scan_ids):
        scan_assets[scan_id] = scan_inventory(scan_root / scan_id, parse_instances=False)
    scan_summary = {
        "unique_scans": len(scan_ids),
        "scan_dir_exists": sum(1 for item in scan_assets.values() if item["scan_exists"]),
        "multi_view_exists": sum(1 for item in scan_assets.values() if item["multi_view_exists"]),
        "sequence_dir_exists": sum(1 for item in scan_assets.values() if item["sequence_dir_exists"]),
        "sequence_zip_exists": sum(1 for item in scan_assets.values() if item["sequence_zip_exists"]),
        "mesh_ready": sum(1 for item in scan_assets.values() if item["mesh_ready"]),
        "point_mesh_ready": sum(1 for item in scan_assets.values() if item["point_mesh_ready"]),
    }

    predicate_rows: list[dict[str, Any]] = []
    for pred in TARGET_PREDICATES:
        rows = counts[pred]
        predicate_rows.append(
            {
                "predicate_label": pred,
                "rows": rows,
                "unique_directed_pairs_shared_route": len(directed_pairs),
                "semantic_score_available_rows": semantic_available[pred],
                "semantic_score_available_rate": semantic_available[pred] / rows if rows else 0.0,
                "top50_rows": top50[pred],
                "top100_rows": top100[pred],
                "source_geometry_available_rows": source_geometry_available[pred],
                "source_geometry_checkable_rows": source_geometry_checkable[pred],
                "exact_match_rows": label_status[f"{pred}|exact_match"],
                "family_match_rows": label_status[f"{pred}|family_match"],
                "pair_has_other_predicate_rows": label_status[f"{pred}|pair_has_other_predicate"],
                "no_gt_for_pair_rows": label_status[f"{pred}|no_gt_for_pair"],
                "unsupported_geometry_rows": geometry_status[f"{pred}|unsupported"],
                "unsupported_geometry_rate": geometry_status[f"{pred}|unsupported"] / rows if rows else 0.0,
                "attachment_anchor_hint_rows": anchor_hints[f"{pred}|attachment_anchor_hint"],
                "hanging_anchor_hint_rows": anchor_hints[f"{pred}|hanging_anchor_hint"],
                "connector_semantic_hint_rows": anchor_hints[f"{pred}|connector_semantic_hint"],
                "rank_band_top": flatten(Counter({key.split("|", 1)[1]: val for key, val in rank_band.items() if key.startswith(pred + "|")})),
                "label_status_top": flatten(Counter({key.split("|", 1)[1]: val for key, val in label_status.items() if key.startswith(pred + "|")})),
            }
        )

    class_pair_rows = [
        {
            "predicate_label": key.split("|", 1)[0],
            "class_pair": key.split("|", 1)[1],
            "rows": value,
        }
        for key, value in top_class_pairs.most_common(80)
    ]
    full_summary = {
        "rows_total": sum(counts.values()),
        "rows_by_predicate": dict(counts),
        "unique_scans": len(scan_ids),
        "unique_directed_pairs": len(directed_pairs),
        "scan_asset_summary": scan_summary,
        "geometry_status_top": dict(geometry_status.most_common()),
        "coverage_state_top": dict(coverage_state.most_common()),
        "rank_band_top": dict(rank_band.most_common()),
        "label_status_top": dict(label_status.most_common()),
        "top_class_pairs": dict(top_class_pairs.most_common(20)),
    }
    return full_summary, predicate_rows, class_pair_rows, scan_summary


def build_packet_inventory(packet_dir: Path, candidate_dir: Path, scan_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    label_ready_rows = read_jsonl(packet_dir / "label_ready_manifest.jsonl")
    packet_rows = read_jsonl(packet_dir / "packet_manifest.jsonl")
    candidate_rows = read_jsonl(candidate_dir / "candidate_rows_internal.jsonl")
    packet_by_id = {row.get("candidate_id"): row for row in packet_rows}
    candidate_by_id = {row.get("candidate_id"): row for row in candidate_rows}
    scan_cache: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    counts = Counter()

    for row in label_ready_rows:
        candidate_id = row.get("candidate_id")
        packet = packet_by_id.get(candidate_id, {})
        candidate = candidate_by_id.get(candidate_id, {})
        pred = packet.get("predicate_label") or candidate.get("predicate_label")
        scan_id = row.get("scan_id")
        if scan_id not in scan_cache:
            scan_cache[scan_id] = scan_inventory(scan_root / scan_id, parse_instances=True)
        scan_inv = scan_cache[scan_id]
        subject_id = int(row.get("subject_id"))
        object_id = int(row.get("object_id"))
        subj = instance_summary(scan_inv, subject_id)
        obj = instance_summary(scan_inv, object_id)
        pair = classify_pair_visibility(scan_inv, subj, obj)
        is_primary = pred in PRIMARY_PREDICATES
        is_connected = pred in DIAGNOSTIC_PREDICATES
        query_id = candidate.get("query_id") or row.get("query_id")
        out = {
            "candidate_id": candidate_id,
            "predicate_label": pred,
            "route_role": "primary_observability_then_reliability" if is_primary else "diagnostic_observability_then_topology",
            "query_id_hidden": query_id,
            "scan_id": scan_id,
            "subject_label": packet.get("subject_label") or candidate.get("subject_label"),
            "object_label": packet.get("object_label") or candidate.get("object_label"),
            "packet_status": packet.get("packet_status") or row.get("packet_status_hidden"),
            "contact_sheet_ready": bool(row.get("contact_sheet_ready_hidden")),
            "mesh_packet_ready": bool(row.get("mesh_packet_ready_hidden")),
            "multiview_packet_ready": bool(row.get("multiview_packet_hidden")),
            "subject_image_count": row.get("subject_image_count_hidden"),
            "object_image_count": row.get("object_image_count_hidden"),
            "subject_scan_crop_count": subj["crop_count"],
            "object_scan_crop_count": obj["crop_count"],
            "subject_scan_origin_count": subj["origin_count"],
            "object_scan_origin_count": obj["origin_count"],
            "scan_mesh_ready": scan_inv["mesh_ready"],
            "scan_point_mesh_ready": scan_inv["point_mesh_ready"],
            "scan_multi_view_exists": scan_inv["multi_view_exists"],
            "scan_sequence_dir_exists": scan_inv["sequence_dir_exists"],
            "both_have_packet_images": (row.get("subject_image_count_hidden") or 0) > 0 and (row.get("object_image_count_hidden") or 0) > 0,
            "both_have_scan_crops": pair["both_have_crops"],
            "shared_origin_frame_count": pair["shared_origin_frame_count"],
            "shared_view_rank_count": max(pair["shared_crop_view_rank_count"], pair["shared_origin_view_rank_count"]),
            "visual_context_state": pair["visual_context_state"],
            "audit_ready_state": pair["audit_ready_state"],
            "audit_ready_binary": pair["audit_ready_binary"],
            "strong_pair_visual_ready": pair["strong_pair_visual_ready"],
            "explicit_topology_source_available": False,
            "connector_semantic_hint": contains_any(packet.get("subject_label") or candidate.get("subject_label"), CONNECTOR_KEYWORDS)
            or contains_any(packet.get("object_label") or candidate.get("object_label"), CONNECTOR_KEYWORDS),
            "label_or_review_fields_used": False,
            "model_input_allowed_now": False,
        }
        rows.append(out)
        counts["rows"] += 1
        counts[f"predicate:{pred}"] += 1
        counts[f"route_role:{out['route_role']}"] += 1
        counts[f"query:{query_id}"] += 1
        counts[f"visual_context:{out['visual_context_state']}"] += 1
        counts[f"audit_ready:{out['audit_ready_state']}"] += 1
        counts["packet_ready"] += int(out["packet_status"] == "ready")
        counts["contact_sheet_ready"] += int(out["contact_sheet_ready"])
        counts["mesh_packet_ready"] += int(out["mesh_packet_ready"])
        counts["multiview_packet_ready"] += int(out["multiview_packet_ready"])
        counts["both_have_packet_images"] += int(out["both_have_packet_images"])
        counts["audit_ready_binary"] += int(out["audit_ready_binary"])
        counts["strong_pair_visual_ready"] += int(out["strong_pair_visual_ready"])
        counts["connected_rows_without_explicit_topology"] += int(is_connected and not out["explicit_topology_source_available"])

    predicate_rows: list[dict[str, Any]] = []
    for pred in TARGET_PREDICATES:
        subset = [row for row in rows if row["predicate_label"] == pred]
        predicate_rows.append(
            {
                "predicate_label": pred,
                "packet_rows": len(subset),
                "packet_ready_rows": sum(1 for row in subset if row["packet_status"] == "ready"),
                "both_have_packet_images": sum(1 for row in subset if row["both_have_packet_images"]),
                "mesh_packet_ready_rows": sum(1 for row in subset if row["mesh_packet_ready"]),
                "multiview_packet_ready_rows": sum(1 for row in subset if row["multiview_packet_ready"]),
                "scan_mesh_ready_rows": sum(1 for row in subset if row["scan_mesh_ready"]),
                "audit_ready_rows": sum(1 for row in subset if row["audit_ready_binary"]),
                "strong_pair_visual_ready_rows": sum(1 for row in subset if row["strong_pair_visual_ready"]),
                "explicit_topology_source_rows": sum(1 for row in subset if row["explicit_topology_source_available"]),
                "connector_semantic_hint_rows": sum(1 for row in subset if row["connector_semantic_hint"]),
                "visual_context_top": flatten(Counter(row["visual_context_state"] for row in subset)),
                "audit_ready_top": flatten(Counter(row["audit_ready_state"] for row in subset)),
            }
        )

    summary = {
        "rows": len(rows),
        "unique_scans": len(scan_cache),
        "rows_by_predicate": {pred: counts[f"predicate:{pred}"] for pred in TARGET_PREDICATES},
        "rows_by_route_role": {
            "primary_observability_then_reliability": counts["route_role:primary_observability_then_reliability"],
            "diagnostic_observability_then_topology": counts["route_role:diagnostic_observability_then_topology"],
        },
        "packet_ready_rows": counts["packet_ready"],
        "contact_sheet_ready_rows": counts["contact_sheet_ready"],
        "mesh_packet_ready_rows": counts["mesh_packet_ready"],
        "multiview_packet_ready_rows": counts["multiview_packet_ready"],
        "both_have_packet_images_rows": counts["both_have_packet_images"],
        "audit_ready_rows": counts["audit_ready_binary"],
        "strong_pair_visual_ready_rows": counts["strong_pair_visual_ready"],
        "connected_rows_without_explicit_topology": counts["connected_rows_without_explicit_topology"],
        "query_counts": {key.split(":", 1)[1]: value for key, value in counts.items() if key.startswith("query:")},
        "visual_context_counts": {key.split(":", 1)[1]: value for key, value in counts.items() if key.startswith("visual_context:")},
        "audit_ready_counts": {key.split(":", 1)[1]: value for key, value in counts.items() if key.startswith("audit_ready:")},
    }
    return summary, predicate_rows, rows


def build_route_readiness(full_summary: dict[str, Any], packet_summary: dict[str, Any], packet_predicate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_by_pred = {row["predicate_label"]: row for row in packet_predicate_rows}
    rows: list[dict[str, Any]] = []
    for pred in TARGET_PREDICATES:
        full_rows = full_summary["rows_by_predicate"].get(pred, 0)
        packet = packet_by_pred.get(pred, {})
        is_connected = pred == "connected to"
        primary_ready = (
            full_rows >= 1000
            and packet.get("packet_ready_rows", 0) >= (80 if is_connected else 160)
            and packet.get("both_have_packet_images", 0) == packet.get("packet_rows", -1)
            and packet.get("mesh_packet_ready_rows", 0) == packet.get("packet_rows", -1)
        )
        topology_ready = packet.get("explicit_topology_source_rows", 0) > 0
        if is_connected and not topology_ready:
            decision = "diagnostic_only_until_explicit_topology_or_functional_evidence"
        elif primary_ready:
            decision = "ready_for_observability_materialization_plan"
        else:
            decision = "limited_needs_additional_source_repair"
        rows.append(
            {
                "predicate_label": pred,
                "route_role": "diagnostic_observability_then_topology" if is_connected else "primary_observability_then_reliability",
                "full_train_candidate_rows": full_rows,
                "packet_rows": packet.get("packet_rows", 0),
                "packet_ready_rows": packet.get("packet_ready_rows", 0),
                "both_have_packet_images": packet.get("both_have_packet_images", 0),
                "mesh_packet_ready_rows": packet.get("mesh_packet_ready_rows", 0),
                "audit_ready_rows": packet.get("audit_ready_rows", 0),
                "strong_pair_visual_ready_rows": packet.get("strong_pair_visual_ready_rows", 0),
                "explicit_topology_source_rows": packet.get("explicit_topology_source_rows", 0),
                "connector_semantic_hint_rows": packet.get("connector_semantic_hint_rows", 0),
                "ready_for_primary_materialization_plan": bool(primary_ready and (not is_connected or topology_ready)),
                "decision": decision,
            }
        )
    return rows


def report_text(summary: dict[str, Any], route_rows: list[dict[str, Any]]) -> str:
    full = summary["full_train_inventory"]
    packets = summary["packet_reuse_inventory"]
    lines = [
        "# Attachment Observability Source Inventory",
        "",
        f"Created: `{summary['created_at_utc']}`",
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
        "## Full Train Candidate Inventory",
        "",
        "```text",
        f"rows_total = {full['rows_total']}",
        f"rows_by_predicate = {full['rows_by_predicate']}",
        f"unique_scans = {full['unique_scans']}",
        f"unique_directed_pairs = {full['unique_directed_pairs']}",
        f"scan_asset_summary = {full['scan_asset_summary']}",
        "```",
        "",
        "All R7 predicates are `unsupported` under the existing geometry verifier. This is expected for the attachment-observability route and means source inventory must use point/mesh/multiview evidence before materialization.",
        "",
        "## Existing Packet Reuse Inventory",
        "",
        "```text",
        f"rows = {packets['rows']}",
        f"rows_by_predicate = {packets['rows_by_predicate']}",
        f"packet_ready_rows = {packets['packet_ready_rows']}",
        f"both_have_packet_images_rows = {packets['both_have_packet_images_rows']}",
        f"mesh_packet_ready_rows = {packets['mesh_packet_ready_rows']}",
        f"multiview_packet_ready_rows = {packets['multiview_packet_ready_rows']}",
        f"audit_ready_rows = {packets['audit_ready_rows']}",
        f"strong_pair_visual_ready_rows = {packets['strong_pair_visual_ready_rows']}",
        f"connected_rows_without_explicit_topology = {packets['connected_rows_without_explicit_topology']}",
        "```",
        "",
        "## Route Decisions",
        "",
        "| Predicate | Decision | Packet Rows | Audit Ready | Strong Pair Visual | Explicit Topology |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in route_rows:
        lines.append(
            f"| `{row['predicate_label']}` | {row['decision']} | {row['packet_rows']} | "
            f"{row['audit_ready_rows']} | {row['strong_pair_visual_ready_rows']} | "
            f"{row['explicit_topology_source_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This stage counts sources only.",
            "- It does not materialize rows.",
            "- It does not run learned smoke.",
            "- It does not use validation/test data.",
            "- Multi-view and mesh remain source-inventory/audit evidence, not deployable model input.",
            "- `connected to` remains diagnostic until explicit topology or functional connection evidence is available.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}` should plan model-safe `G_e` and `Q_e` materialization for `attached to` / `hanging on`, while keeping `connected to` diagnostic.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.target_plan_dir / "summary.json")
    packet_summary = read_json(args.packet_dir / "summary.json")
    candidate_summary = read_json(args.candidate_dir / "summary.json")
    ingestion_summary = read_json(args.ingestion_dir / "summary.json")
    audit_summary = read_json(args.audit_dir / "summary.json")

    validation_errors = validate_inputs(
        plan_summary,
        packet_summary,
        candidate_summary,
        ingestion_summary,
        audit_summary,
        args,
    )

    full_summary, full_predicate_rows, full_class_pair_rows, scan_asset_summary = build_full_train_inventory(
        args.train_rga_dir / "match_rows.jsonl", args.scan_root
    )
    packet_reuse_summary, packet_predicate_rows, packet_rows = build_packet_inventory(
        args.packet_dir, args.candidate_dir, args.scan_root
    )
    route_rows = build_route_readiness(full_summary, packet_reuse_summary, packet_predicate_rows)

    primary_ready = all(
        row["decision"] == "ready_for_observability_materialization_plan"
        for row in route_rows
        if row["predicate_label"] in PRIMARY_PREDICATES
    )
    connected_diagnostic = any(
        row["predicate_label"] == "connected to"
        and row["decision"] == "diagnostic_only_until_explicit_topology_or_functional_evidence"
        for row in route_rows
    )
    if validation_errors:
        status = STATUS_ERROR
        selected_path = "input_errors_block_source_inventory"
        next_todo = NEXT_TODO_ERROR
    elif primary_ready and connected_diagnostic:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO
    else:
        status = STATUS_LIMITED
        selected_path = "source_inventory_limited_needs_path_decision"
        next_todo = "compatibility_dataset_v3_attachment_observability_source_inventory_path_decision"

    output_paths = {
        "summary": output_dir / "summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "report": output_dir / "report.md",
        "full_train_predicate_summary": output_dir / "full_train_predicate_summary.csv",
        "full_train_top_class_pairs": output_dir / "full_train_top_class_pairs.csv",
        "full_train_scan_asset_summary": output_dir / "full_train_scan_asset_summary.json",
        "packet_reuse_predicate_summary": output_dir / "packet_reuse_predicate_summary.csv",
        "packet_reuse_inventory_rows": output_dir / "packet_reuse_inventory_rows.jsonl",
        "packet_reuse_inventory_table": output_dir / "packet_reuse_inventory_table.csv",
        "route_readiness": output_dir / "route_readiness.csv",
        "source_manifest": output_dir / "source_manifest.jsonl",
    }
    source_manifest = [
        {
            "source": "full_train_match_rows",
            "path": rel_path(args.train_rga_dir / "match_rows.jsonl"),
            "role": "candidate capacity and train-side semantic/source distribution",
            "model_input_allowed_now": False,
        },
        {
            "source": "existing_attachment_packets",
            "path": rel_path(args.packet_dir),
            "role": "packet, mesh, and multiview source availability for R7 inventory",
            "model_input_allowed_now": False,
        },
        {
            "source": "3RScan_scan_root",
            "path": rel_path(args.scan_root),
            "role": "scan-level mesh, point, semseg, sequence, and multiview availability",
            "model_input_allowed_now": False,
        },
    ]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "target_plan": rel_path(args.target_plan_dir / "summary.json"),
            "train_match_rows": rel_path(args.train_rga_dir / "match_rows.jsonl"),
            "packet_summary": rel_path(args.packet_dir / "summary.json"),
            "candidate_summary": rel_path(args.candidate_dir / "summary.json"),
            "ingestion_summary": rel_path(args.ingestion_dir / "summary.json"),
            "target_independence_audit": rel_path(args.audit_dir / "summary.json"),
            "scan_root": rel_path(args.scan_root),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "route": {
            "route_id": "R7",
            "family": "attachment_observability",
            "primary_predicates": list(PRIMARY_PREDICATES),
            "diagnostic_predicates": list(DIAGNOSTIC_PREDICATES),
        },
        "full_train_inventory": full_summary,
        "packet_reuse_inventory": packet_reuse_summary,
        "route_readiness": route_rows,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "materializes_rows": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "runs_model": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_or_mesh_as_source_inventory_evidence": True,
            "review_labels_used_for_inventory": False,
        },
    }

    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_csv(output_paths["full_train_predicate_summary"], full_predicate_rows)
    write_csv(output_paths["full_train_top_class_pairs"], full_class_pair_rows)
    write_json(output_paths["full_train_scan_asset_summary"], scan_asset_summary)
    write_csv(output_paths["packet_reuse_predicate_summary"], packet_predicate_rows)
    write_jsonl(output_paths["packet_reuse_inventory_rows"], packet_rows)
    write_csv(output_paths["packet_reuse_inventory_table"], packet_rows)
    write_csv(output_paths["route_readiness"], route_rows)
    write_jsonl(output_paths["source_manifest"], source_manifest)
    output_paths["report"].write_text(report_text(summary, route_rows), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
