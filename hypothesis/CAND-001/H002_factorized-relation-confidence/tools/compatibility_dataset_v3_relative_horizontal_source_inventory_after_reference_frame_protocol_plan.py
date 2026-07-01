#!/usr/bin/env python3
"""Inventory train-side relative-horizontal sources before row materialization."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan"
DEFAULT_TRAIN_RELATIONSHIPS = REPO_ROOT / "local_dataset/3DSSG_subset/relationships_train.json"
DEFAULT_FULL_RELATIONSHIPS = REPO_ROOT / "local_dataset/3DSSG/relationships.json"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan"
)

EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_ready"
STATUS_DIAGNOSTIC = (
    "h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_diagnostic_only"
)
STATUS_ERRORS = "h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_input_errors"
SELECTED_READY = "relative_horizontal_inventory_ready_for_candidate_materialization_plan_with_frame_qe_controls"
SELECTED_DIAGNOSTIC = "freeze_relative_horizontal_as_diagnostic_due_to_frame_or_capacity_gap"
NEXT_READY = "compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory"
NEXT_DIAGNOSTIC = "compatibility_dataset_v3_relative_horizontal_path_decision_after_source_inventory"

PREDICATES = ("left", "right", "front", "behind", "in front of")
AXIS_PAIRS = {
    "left_right": ("left", "right"),
    "front_behind": ("front", "behind"),
}

MIN_CENTROID_JOIN_RATE = 0.90
MIN_OBB_JOIN_RATE = 0.90
MIN_BEST_ALIGNMENT_RATE = 0.70
MIN_COMPATIBLE_UNIQUE_PER_AXIS_PAIR = 1000
MAX_TOP_SCAN_FRACTION = 0.05
MAX_TOP_CLASS_PAIR_FRACTION = 0.15
AXIS_BOUNDARY_MARGIN = 0.10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--train-relationships", type=Path, default=DEFAULT_TRAIN_RELATIONSHIPS)
    parser.add_argument("--full-relationships", type=Path, default=DEFAULT_FULL_RELATIONSHIPS)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(protocol_summary: dict[str, Any], protocol_errors: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol_summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol_summary.get("status")})
    if protocol_summary.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol_summary.get("next_todo")})
    if protocol_summary.get("validation_errors") != 0:
        errors.append({"error_type": "protocol_validation_errors_present", "actual": protocol_summary.get("validation_errors")})
    if protocol_errors:
        errors.append({"error_type": "protocol_validation_error_rows_present", "rows": len(protocol_errors)})
    boundary = protocol_summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "materializes_rows", "paper_evidence_allowed", "validation_usage", "test_usage"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "protocol_boundary_not_false", "key": key, "actual": boundary.get(key)})
    for path in [args.train_relationships, args.full_relationships]:
        if not path.exists():
            errors.append({"error_type": "missing_relationship_source", "path": rel_path(path)})
    if not args.scan_root.exists():
        errors.append({"error_type": "missing_scan_root", "path": rel_path(args.scan_root)})
    return errors


def predicate_from_relation(rel: Any) -> str | None:
    if isinstance(rel, dict):
        for key in ["predicate_label", "relationship", "predicate", "name"]:
            value = rel.get(key)
            if isinstance(value, str):
                return value
        return None
    if isinstance(rel, list):
        for value in reversed(rel):
            if isinstance(value, str):
                return value
    return None


def endpoint_from_relation(rel: Any) -> tuple[str | None, str | None]:
    if isinstance(rel, dict):
        subject = rel.get("subject_id") or rel.get("subject") or rel.get("source_id")
        obj = rel.get("object_id") or rel.get("object") or rel.get("target_id")
        return str(subject) if subject is not None else None, str(obj) if obj is not None else None
    if isinstance(rel, list) and len(rel) >= 2:
        return str(rel[0]), str(rel[1])
    return None, None


def count_predicates(path: Path) -> Counter[str]:
    data = read_json(path)
    counts: Counter[str] = Counter()
    for scan in data.get("scans", []):
        for rel in scan.get("relationships", []):
            predicate = predicate_from_relation(rel)
            if predicate:
                counts[predicate] += 1
    return counts


def object_record(group: dict[str, Any]) -> dict[str, Any]:
    object_id = group.get("objectId", group.get("id"))
    label = str(group.get("label", "")).strip().lower()
    obb = group.get("obb") or {}
    axes_raw = obb.get("axesLengths") or []
    axes_lengths: list[float] = []
    for value in axes_raw:
        try:
            axes_lengths.append(float(value))
        except (TypeError, ValueError):
            pass
    axes_ok = len(axes_lengths) == 3 and all(value > 0 for value in axes_lengths)
    centroid = obb.get("centroid")
    if not (isinstance(centroid, list) and len(centroid) == 3):
        centroid = None
    return {
        "object_id": str(object_id),
        "label": label,
        "centroid": centroid,
        "centroid_available": centroid is not None,
        "obb_available": axes_ok,
    }


def load_semseg(scan_root: Path, scan_id: str) -> dict[str, dict[str, Any]]:
    path = scan_root / scan_id / "semseg.v2.json"
    if not path.exists():
        return {}
    data = read_json(path)
    objects: dict[str, dict[str, Any]] = {}
    for group in data.get("segGroups", []):
        record = object_record(group)
        if record["object_id"] != "None":
            objects[record["object_id"]] = record
    return objects


def view_source_record(scan_root: Path, scan_id: str) -> dict[str, Any]:
    root = scan_root / scan_id
    sequence = root / "sequence"
    multi_view = root / "multi_view"
    has_sequence = sequence.exists()
    has_multi_view = multi_view.exists()
    color_count = 0
    pose_count = 0
    if has_sequence:
        color_count = len(list(sequence.glob("*.color.jpg")))
        pose_count = len(list(sequence.glob("*.pose.txt")))
    return {
        "sequence_dir_available": has_sequence,
        "multi_view_dir_available": has_multi_view,
        "sequence_color_count": color_count,
        "sequence_pose_count": pose_count,
        "camera_pose_available": has_sequence and color_count > 0 and pose_count > 0,
    }


def signed_axis_value(row: dict[str, Any], axis: str) -> float | None:
    value = row.get(axis)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def axis_bucket(value: float | None) -> str:
    if value is None:
        return "missing"
    if abs(value) < AXIS_BOUNDARY_MARGIN:
        return "boundary"
    return "positive" if value > 0 else "negative"


def is_compatible(predicate: str, axis_value: float | None, first_predicate: str, first_predicate_sign: str) -> str:
    bucket = axis_bucket(axis_value)
    if bucket in {"missing", "boundary"}:
        return bucket
    first_positive = first_predicate_sign == "positive"
    if predicate == first_predicate:
        return "compatible" if (bucket == "positive") == first_positive else "opposes"
    return "compatible" if (bucket == "positive") != first_positive else "opposes"


def collect_anchors(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = read_json(args.train_relationships)
    semseg_cache: dict[str, dict[str, dict[str, Any]]] = {}
    view_cache: dict[str, dict[str, Any]] = {}
    anchors: list[dict[str, Any]] = []
    source_stats = {
        "train_scan_entries": len(data.get("scans", [])),
        "train_relationship_rows": 0,
        "semseg_files_requested": 0,
        "semseg_files_found": 0,
        "view_source_scan_entries": 0,
        "sequence_scan_entries": 0,
        "multi_view_scan_entries": 0,
    }
    for scan_entry in data.get("scans", []):
        scan_id = str(scan_entry.get("scan"))
        subgraph_id = str(scan_entry.get("split", "missing"))
        objects = {str(key): str(value).strip().lower() for key, value in (scan_entry.get("objects") or {}).items()}
        for rel in scan_entry.get("relationships", []):
            source_stats["train_relationship_rows"] += 1
            predicate = predicate_from_relation(rel)
            if predicate not in PREDICATES:
                continue
            subject_id, object_id = endpoint_from_relation(rel)
            if not subject_id or not object_id:
                continue
            if scan_id not in semseg_cache:
                source_stats["semseg_files_requested"] += 1
                semseg_cache[scan_id] = load_semseg(args.scan_root, scan_id)
                if semseg_cache[scan_id]:
                    source_stats["semseg_files_found"] += 1
            if scan_id not in view_cache:
                view_cache[scan_id] = view_source_record(args.scan_root, scan_id)
            semseg_objects = semseg_cache[scan_id]
            subject = semseg_objects.get(subject_id)
            obj = semseg_objects.get(object_id)
            subject_centroid = subject.get("centroid") if subject else None
            object_centroid = obj.get("centroid") if obj else None
            has_centroids = subject_centroid is not None and object_centroid is not None
            has_obb_pair = bool(subject and obj and subject.get("obb_available") and obj.get("obb_available"))
            dx = None
            dy = None
            horizontal_distance = None
            if has_centroids:
                dx = float(subject_centroid[0]) - float(object_centroid[0])
                dy = float(subject_centroid[1]) - float(object_centroid[1])
                horizontal_distance = math.sqrt(dx * dx + dy * dy)
            subject_label = (objects.get(subject_id) or (subject or {}).get("label") or "").strip().lower()
            object_label = (objects.get(object_id) or (obj or {}).get("label") or "").strip().lower()
            view = view_cache[scan_id]
            anchors.append(
                {
                    "scan_id": scan_id,
                    "subgraph_id": subgraph_id,
                    "subject_id": subject_id,
                    "object_id": object_id,
                    "predicate_label": predicate,
                    "subject_label": subject_label,
                    "object_label": object_label,
                    "class_pair": f"{subject_label}->{object_label}",
                    "has_semseg_subject": subject is not None,
                    "has_semseg_object": obj is not None,
                    "centroid_pair_available": has_centroids,
                    "obb_pair_available": has_obb_pair,
                    "delta_x_subject_minus_object": dx,
                    "delta_y_subject_minus_object": dy,
                    "horizontal_distance": horizontal_distance,
                    "x_axis_bucket": axis_bucket(dx),
                    "y_axis_bucket": axis_bucket(dy),
                    "scene_world_frame_available": has_centroids,
                    "sequence_dir_available": view["sequence_dir_available"],
                    "multi_view_dir_available": view["multi_view_dir_available"],
                    "camera_pose_available": view["camera_pose_available"],
                    "sequence_color_count": view["sequence_color_count"],
                    "sequence_pose_count": view["sequence_pose_count"],
                    "directed_pair_key": f"{scan_id}::{subject_id}->{object_id}",
                    "directed_pair_predicate_key": f"{scan_id}::{subject_id}->{object_id}::{predicate}",
                    "subgraph_anchor_key": f"{scan_id}::{subgraph_id}::{subject_id}->{object_id}::{predicate}",
                }
            )
    source_stats["unique_scan_ids_with_horizontal_anchors"] = len({row["scan_id"] for row in anchors})
    source_stats["semseg_cache_entries"] = len(semseg_cache)
    source_stats["view_source_scan_entries"] = len(view_cache)
    source_stats["sequence_scan_entries"] = sum(1 for view in view_cache.values() if view["sequence_dir_available"])
    source_stats["multi_view_scan_entries"] = sum(1 for view in view_cache.values() if view["multi_view_dir_available"])
    return anchors, source_stats


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def top_counter_rows(counter: Counter[Any], name: str, total: int, limit: int = 40) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in counter.most_common(limit):
        rows.append({name: key, "count": int(value), "fraction": round(value / total, 6) if total else 0.0})
    return rows


def unique_count(rows: list[dict[str, Any]], key: str) -> int:
    return len({str(row.get(key)) for row in rows})


def predicate_inventory_rows(anchors: list[dict[str, Any]], full_counts: Counter[str], train_counts: Counter[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for predicate in PREDICATES:
        subset = [row for row in anchors if row["predicate_label"] == predicate]
        centroid = [row for row in subset if row.get("centroid_pair_available")]
        obb = [row for row in subset if row.get("obb_pair_available")]
        camera = [row for row in subset if row.get("camera_pose_available")]
        rows.append(
            {
                "predicate_label": predicate,
                "full_3dssg_relationship_count": full_counts.get(predicate, 0),
                "train_relationship_count": train_counts.get(predicate, 0),
                "train_anchor_rows": len(subset),
                "unique_directed_pair_predicate": unique_count(subset, "directed_pair_predicate_key"),
                "centroid_pair_rows": len(centroid),
                "centroid_pair_join_rate": round(len(centroid) / len(subset), 6) if subset else 0.0,
                "obb_pair_rows": len(obb),
                "obb_pair_join_rate": round(len(obb) / len(subset), 6) if subset else 0.0,
                "camera_pose_rows": len(camera),
                "camera_pose_rate": round(len(camera) / len(subset), 6) if subset else 0.0,
                "x_boundary_rows": sum(1 for row in subset if row.get("x_axis_bucket") == "boundary"),
                "y_boundary_rows": sum(1 for row in subset if row.get("y_axis_bucket") == "boundary"),
                "status": "observed" if subset else "not_observed_keep_diagnostic",
            }
        )
    return rows


def axis_alignment_rows(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for axis_pair, predicates in AXIS_PAIRS.items():
        first, second = predicates
        subset = [row for row in anchors if row["predicate_label"] in predicates and row.get("centroid_pair_available")]
        for axis_name, field in [("scene_world_x", "delta_x_subject_minus_object"), ("scene_world_y", "delta_y_subject_minus_object")]:
            nonboundary = [row for row in subset if axis_bucket(signed_axis_value(row, field)) not in {"missing", "boundary"}]
            boundary = len(subset) - len(nonboundary)
            for first_sign in ["positive", "negative"]:
                compatible = [
                    row
                    for row in nonboundary
                    if is_compatible(row["predicate_label"], signed_axis_value(row, field), first, first_sign) == "compatible"
                ]
                opposing = len(nonboundary) - len(compatible)
                rows.append(
                    {
                        "axis_pair": axis_pair,
                        "predicates": f"{first}/{second}",
                        "axis_candidate": axis_name,
                        "first_predicate": first,
                        "first_predicate_sign": first_sign,
                        "total_centroid_rows": len(subset),
                        "nonboundary_rows": len(nonboundary),
                        "boundary_rows": boundary,
                        "compatible_rows": len(compatible),
                        "opposing_rows": opposing,
                        "alignment_rate": round(len(compatible) / len(nonboundary), 6) if nonboundary else 0.0,
                        "compatible_unique_directed_pair_predicate": unique_count(compatible, "directed_pair_predicate_key"),
                        "same_g_predicate_flip_rows": len(compatible) * 2,
                        "route_role": "candidate" if nonboundary else "unavailable",
                    }
                )
    rows.sort(key=lambda row: (row["axis_pair"], -float(row["alignment_rate"]), row["axis_candidate"], row["first_predicate_sign"]))
    return rows


def selected_axis_rows(axis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for axis_pair in AXIS_PAIRS:
        candidates = [row for row in axis_rows if row["axis_pair"] == axis_pair]
        if not candidates:
            continue
        best = max(
            candidates,
            key=lambda row: (
                float(row["alignment_rate"]),
                int(row["compatible_unique_directed_pair_predicate"]),
                -int(row["boundary_rows"]),
            ),
        )
        selected = dict(best)
        selected["selected_for_next_plan"] = True
        selected["selection_scope"] = "source_inventory_candidate_not_paper_evidence"
        selected["required_qe_filter"] = "frame_disagreement_or_axis_boundary_rows_must_not_be_forced_binary"
        rows.append(selected)
    return rows


def alias_inventory_rows(full_counts: Counter[str], train_counts: Counter[str]) -> list[dict[str, Any]]:
    return [
        {
            "alias_group": "front_alias",
            "predicate": "front",
            "full_3dssg_relationship_count": full_counts.get("front", 0),
            "train_relationship_count": train_counts.get("front", 0),
            "alias_merge_allowed": False,
            "reason": "`in front of` must be checked separately before alias merge",
        },
        {
            "alias_group": "front_alias",
            "predicate": "in front of",
            "full_3dssg_relationship_count": full_counts.get("in front of", 0),
            "train_relationship_count": train_counts.get("in front of", 0),
            "alias_merge_allowed": False,
            "reason": "not observed in current 3DSSG train/full sources; keep diagnostic",
        },
        {
            "alias_group": "behind_opposite",
            "predicate": "behind",
            "full_3dssg_relationship_count": full_counts.get("behind", 0),
            "train_relationship_count": train_counts.get("behind", 0),
            "alias_merge_allowed": False,
            "reason": "opposite relation for front-axis contrast, not alias",
        },
    ]


def frame_availability_rows(anchors: list[dict[str, Any]], source_stats: dict[str, Any]) -> list[dict[str, Any]]:
    total = len(anchors)
    centroid = sum(1 for row in anchors if row.get("centroid_pair_available"))
    obb = sum(1 for row in anchors if row.get("obb_pair_available"))
    camera = sum(1 for row in anchors if row.get("camera_pose_available"))
    multi_view = sum(1 for row in anchors if row.get("multi_view_dir_available"))
    unique_scans = len({row["scan_id"] for row in anchors})
    return [
        {
            "frame_source": "scene_aligned_world_xy",
            "available_rows": centroid,
            "total_rows": total,
            "row_rate": round(centroid / total, 6) if total else 0.0,
            "available_scans": source_stats.get("semseg_files_found", 0),
            "unique_anchor_scans": unique_scans,
            "route_role": "first_candidate",
            "risk": "GT labels may use a different reference frame; wrong-frame controls required",
        },
        {
            "frame_source": "obb_pair_geometry",
            "available_rows": obb,
            "total_rows": total,
            "row_rate": round(obb / total, 6) if total else 0.0,
            "available_scans": source_stats.get("semseg_files_found", 0),
            "unique_anchor_scans": unique_scans,
            "route_role": "geometry_support",
            "risk": "OBB does not define semantic front direction",
        },
        {
            "frame_source": "view_or_camera_frame",
            "available_rows": camera,
            "total_rows": total,
            "row_rate": round(camera / total, 6) if total else 0.0,
            "available_scans": source_stats.get("sequence_scan_entries", 0),
            "unique_anchor_scans": unique_scans,
            "route_role": "audit_qe_first",
            "risk": "multiple views can disagree; cannot choose view post hoc",
        },
        {
            "frame_source": "multi_view_assets",
            "available_rows": multi_view,
            "total_rows": total,
            "row_rate": round(multi_view / total, 6) if total else 0.0,
            "available_scans": source_stats.get("multi_view_scan_entries", 0),
            "unique_anchor_scans": unique_scans,
            "route_role": "audit_qe_first",
            "risk": "crop availability is observability, not relation truth",
        },
    ]


def concentration_rows(anchors: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    total = len(anchors)
    return {
        "scan_concentration": top_counter_rows(Counter(row["scan_id"] for row in anchors), "scan_id", total),
        "class_pair_concentration": top_counter_rows(Counter(row["class_pair"] for row in anchors), "class_pair", total),
        "endpoint_pair_concentration": top_counter_rows(Counter(row["directed_pair_key"] for row in anchors), "directed_pair_key", total),
    }


def capacity_summary(
    anchors: list[dict[str, Any]],
    predicate_rows: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    concentrations: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    total = len(anchors)
    centroid_rows = sum(1 for row in anchors if row.get("centroid_pair_available"))
    obb_rows = sum(1 for row in anchors if row.get("obb_pair_available"))
    centroid_rate = centroid_rows / total if total else 0.0
    obb_rate = obb_rows / total if total else 0.0
    selected_by_pair = {row["axis_pair"]: row for row in selected_rows}
    pair_ready: dict[str, bool] = {}
    for axis_pair in AXIS_PAIRS:
        row = selected_by_pair.get(axis_pair)
        pair_ready[axis_pair] = bool(
            row
            and float(row["alignment_rate"]) >= MIN_BEST_ALIGNMENT_RATE
            and int(row["compatible_unique_directed_pair_predicate"]) >= MIN_COMPATIBLE_UNIQUE_PER_AXIS_PAIR
        )
    top_scan_fraction = concentrations["scan_concentration"][0]["fraction"] if concentrations["scan_concentration"] else 0.0
    top_class_pair_fraction = (
        concentrations["class_pair_concentration"][0]["fraction"] if concentrations["class_pair_concentration"] else 0.0
    )
    in_front_observed = any(row["predicate_label"] == "in front of" and row["train_anchor_rows"] > 0 for row in predicate_rows)
    ready = (
        centroid_rate >= MIN_CENTROID_JOIN_RATE
        and obb_rate >= MIN_OBB_JOIN_RATE
        and all(pair_ready.values())
        and top_scan_fraction <= MAX_TOP_SCAN_FRACTION
        and top_class_pair_fraction <= MAX_TOP_CLASS_PAIR_FRACTION
    )
    return {
        "train_anchor_rows": total,
        "centroid_pair_rows": centroid_rows,
        "centroid_pair_join_rate": round(centroid_rate, 6),
        "obb_pair_rows": obb_rows,
        "obb_pair_join_rate": round(obb_rate, 6),
        "selected_axis_candidates": selected_by_pair,
        "axis_pair_ready": pair_ready,
        "in_front_of_observed": in_front_observed,
        "in_front_of_policy": "diagnostic_not_merged" if not in_front_observed else "requires_alias_audit_before_merge",
        "top_scan_fraction": top_scan_fraction,
        "top_class_pair_fraction": top_class_pair_fraction,
        "ready_for_materialization_plan": ready,
        "thresholds": {
            "min_centroid_join_rate": MIN_CENTROID_JOIN_RATE,
            "min_obb_join_rate": MIN_OBB_JOIN_RATE,
            "min_best_alignment_rate": MIN_BEST_ALIGNMENT_RATE,
            "min_compatible_unique_per_axis_pair": MIN_COMPATIBLE_UNIQUE_PER_AXIS_PAIR,
            "max_top_scan_fraction": MAX_TOP_SCAN_FRACTION,
            "max_top_class_pair_fraction": MAX_TOP_CLASS_PAIR_FRACTION,
            "axis_boundary_margin_meters": AXIS_BOUNDARY_MARGIN,
        },
    }


def build_report(summary: dict[str, Any], predicate_rows: list[dict[str, Any]], selected_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Relative-Horizontal Source Inventory After Reference-Frame Protocol Plan",
        "",
        "## Result",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Predicate Inventory",
        "",
        "| predicate | train rows | full rows | centroid join | OBB join | camera pose | status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in predicate_rows:
        lines.append(
            "| {predicate_label} | {train_anchor_rows} | {full_3dssg_relationship_count} | "
            "{centroid_pair_join_rate} | {obb_pair_join_rate} | {camera_pose_rate} | {status} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Selected Axis Candidates",
            "",
            "| axis pair | axis | first predicate sign | alignment | compatible unique | same-G rows |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in selected_rows:
        lines.append(
            "| {axis_pair} | {axis_candidate} | {first_predicate_sign} | {alignment_rate} | "
            "{compatible_unique_directed_pair_predicate} | {same_g_predicate_flip_rows} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `left/right` and `front/behind` have enough train-side material for a materialization plan.",
            "- The alignment is not perfect, so frame-disagreement and axis-boundary rows must be handled through `Q_e` or diagnostics.",
            "- `in front of` is not observed in the current train/full 3DSSG sources and must not be merged with `front`.",
            "- This inventory does not create model rows, train a model, or use validation/test.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    protocol_summary = read_json(args.protocol_dir / "summary.json")
    protocol_errors = read_jsonl(args.protocol_dir / "validation_errors.jsonl")
    validation_errors = validate_inputs(protocol_summary, protocol_errors, args)

    anchors: list[dict[str, Any]] = []
    source_stats: dict[str, Any] = {}
    full_counts: Counter[str] = Counter()
    train_counts: Counter[str] = Counter()
    if not validation_errors:
        anchors, source_stats = collect_anchors(args)
        full_counts = count_predicates(args.full_relationships)
        train_counts = count_predicates(args.train_relationships)

    predicate_rows = predicate_inventory_rows(anchors, full_counts, train_counts)
    axis_rows = axis_alignment_rows(anchors)
    selected_rows = selected_axis_rows(axis_rows)
    alias_rows = alias_inventory_rows(full_counts, train_counts)
    frame_rows = frame_availability_rows(anchors, source_stats)
    concentrations = concentration_rows(anchors)
    capacity = capacity_summary(anchors, predicate_rows, axis_rows, selected_rows, concentrations)

    if not anchors and not validation_errors:
        validation_errors.append({"error_type": "no_relative_horizontal_anchors_found"})
    if capacity["ready_for_materialization_plan"]:
        status = STATUS_READY
        selected_path = SELECTED_READY
        next_todo = NEXT_READY
    elif validation_errors:
        status = STATUS_ERRORS
        selected_path = None
        next_todo = None
    else:
        status = STATUS_DIAGNOSTIC
        selected_path = SELECTED_DIAGNOSTIC
        next_todo = NEXT_DIAGNOSTIC

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "protocol_plan": rel_path(args.protocol_dir),
            "protocol_summary": rel_path(args.protocol_dir / "summary.json"),
            "train_relationships": rel_path(args.train_relationships),
            "full_relationships": rel_path(args.full_relationships),
            "scan_root": rel_path(args.scan_root),
        },
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "predicate_inventory": rel_path(args.output_dir / "predicate_inventory.csv"),
            "axis_alignment_inventory": rel_path(args.output_dir / "axis_alignment_inventory.csv"),
            "selected_axis_candidates": rel_path(args.output_dir / "selected_axis_candidates.csv"),
            "alias_inventory": rel_path(args.output_dir / "alias_inventory.csv"),
            "frame_availability_inventory": rel_path(args.output_dir / "frame_availability_inventory.csv"),
            "scan_concentration": rel_path(args.output_dir / "scan_concentration.csv"),
            "class_pair_concentration": rel_path(args.output_dir / "class_pair_concentration.csv"),
            "endpoint_pair_concentration": rel_path(args.output_dir / "endpoint_pair_concentration.csv"),
            "anchor_preview": rel_path(args.output_dir / "anchor_preview.jsonl"),
            "capacity_summary": rel_path(args.output_dir / "capacity_summary.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "anchor_rows": len(anchors),
            "predicate_inventory_rows": len(predicate_rows),
            "axis_alignment_rows": len(axis_rows),
            "selected_axis_rows": len(selected_rows),
            "alias_rows": len(alias_rows),
            "frame_availability_rows": len(frame_rows),
            "scan_concentration_rows": len(concentrations["scan_concentration"]),
            "class_pair_concentration_rows": len(concentrations["class_pair_concentration"]),
            "endpoint_pair_concentration_rows": len(concentrations["endpoint_pair_concentration"]),
        },
        "source_stats": source_stats,
        "capacity_summary": capacity,
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "materializes_rows": False,
            "split": "train_only_source_inventory",
            "test_usage": False,
            "validation_usage": False,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "predicate_inventory.csv", predicate_rows)
    write_csv(args.output_dir / "axis_alignment_inventory.csv", axis_rows)
    write_csv(args.output_dir / "selected_axis_candidates.csv", selected_rows)
    write_csv(args.output_dir / "alias_inventory.csv", alias_rows)
    write_csv(args.output_dir / "frame_availability_inventory.csv", frame_rows)
    write_csv(args.output_dir / "scan_concentration.csv", concentrations["scan_concentration"])
    write_csv(args.output_dir / "class_pair_concentration.csv", concentrations["class_pair_concentration"])
    write_csv(args.output_dir / "endpoint_pair_concentration.csv", concentrations["endpoint_pair_concentration"])
    write_jsonl(args.output_dir / "anchor_preview.jsonl", anchors[:200])
    write_json(args.output_dir / "capacity_summary.json", capacity)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    (args.output_dir / "report.md").write_text(build_report(summary, predicate_rows, selected_rows), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
