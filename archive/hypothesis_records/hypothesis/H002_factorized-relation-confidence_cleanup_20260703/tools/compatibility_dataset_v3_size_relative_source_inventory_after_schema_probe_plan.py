#!/usr/bin/env python3
"""Inventory train-side size-relative anchors before H002 row materialization."""

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

DEFAULT_SCHEMA_PLAN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit"
)
DEFAULT_TRAIN_RELATIONSHIPS = REPO_ROOT / "local_dataset/3DSSG_subset/relationships_train.json"
DEFAULT_FULL_RELATIONSHIPS = REPO_ROOT / "local_dataset/3DSSG/relationships.json"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan"
)

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_ready"
STATUS_DIAGNOSTIC = "h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_diagnostic_only"
STATUS_ERROR = "h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_input_errors"
SELECTED_READY = "size_relative_inventory_ready_for_candidate_materialization_plan"
SELECTED_DIAGNOSTIC = "freeze_size_relative_inventory_as_diagnostic_due_to_capacity_or_join_gap"
NEXT_READY = "compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory"
NEXT_DIAGNOSTIC = "compatibility_dataset_v3_size_relative_path_decision_after_source_inventory"

SIZE_PREDICATES = ("bigger than", "smaller than")
STRUCTURAL_LABELS = {
    "ceiling",
    "door",
    "floor",
    "room",
    "stairs",
    "wall",
    "window",
}

AMBIGUOUS_LOG_RATIO = math.log(1.15)
WEAK_LOG_RATIO = math.log(1.25)
STRONG_LOG_RATIO = math.log(1.50)
EPS = 1e-9

MIN_JOIN_RATE = 0.90
MIN_STRICT_UNIQUE_FLIP_GROUPS = 300
MIN_STRICT_UNIQUE_PER_PREDICATE = 100
MAX_STRUCTURAL_FRACTION_FOR_MAIN = 0.40


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-plan-dir", type=Path, default=DEFAULT_SCHEMA_PLAN_DIR)
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


def validate_inputs(plan_summary: dict[str, Any], plan_errors: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    if plan_errors:
        errors.append({"error_type": "plan_validation_error_rows_present", "rows": len(plan_errors)})
    boundary = plan_summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "materializes_rows", "paper_evidence_allowed", "validation_usage", "test_usage"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": boundary.get(key)})
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


def semseg_path(scan_root: Path, scan_id: str) -> Path:
    return scan_root / scan_id / "semseg.v2.json"


def vertical_extent(axes_lengths: list[float], normalized_axes: list[float] | None) -> float:
    if not normalized_axes or len(normalized_axes) != 9:
        return max(axes_lengths)
    extent = 0.0
    for axis_index, length in enumerate(axes_lengths):
        axis_z = normalized_axes[axis_index * 3 + 2]
        extent += abs(axis_z) * length
    return extent


def horizontal_extents(axes_lengths: list[float], normalized_axes: list[float] | None) -> tuple[float, float]:
    if not normalized_axes or len(normalized_axes) != 9:
        ordered = sorted(axes_lengths, reverse=True)
        return ordered[0], ordered[1] if len(ordered) > 1 else ordered[0]
    extent_x = 0.0
    extent_y = 0.0
    for axis_index, length in enumerate(axes_lengths):
        extent_x += abs(normalized_axes[axis_index * 3]) * length
        extent_y += abs(normalized_axes[axis_index * 3 + 1]) * length
    return extent_x, extent_y


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
    normalized_axes = obb.get("normalizedAxes")
    if not (isinstance(normalized_axes, list) and len(normalized_axes) == 9):
        normalized_axes = None
    centroid = obb.get("centroid")
    if not (isinstance(centroid, list) and len(centroid) == 3):
        centroid = None
    if axes_ok:
        hx, hy = horizontal_extents(axes_lengths, normalized_axes)
        record = {
            "object_id": str(object_id),
            "label": label,
            "obb_available": True,
            "axes_lengths": axes_lengths,
            "centroid": centroid,
            "volume": axes_lengths[0] * axes_lengths[1] * axes_lengths[2],
            "max_extent": max(axes_lengths),
            "min_extent": min(axes_lengths),
            "median_extent": sorted(axes_lengths)[1],
            "vertical_extent": vertical_extent(axes_lengths, normalized_axes),
            "horizontal_extent_x": hx,
            "horizontal_extent_y": hy,
            "footprint_area": max(hx, EPS) * max(hy, EPS),
        }
    else:
        record = {
            "object_id": str(object_id),
            "label": label,
            "obb_available": False,
            "axes_lengths": [],
            "centroid": centroid,
        }
    return record


def load_semseg(scan_root: Path, scan_id: str) -> dict[str, dict[str, Any]]:
    path = semseg_path(scan_root, scan_id)
    if not path.exists():
        return {}
    data = read_json(path)
    objects: dict[str, dict[str, Any]] = {}
    for group in data.get("segGroups", []):
        record = object_record(group)
        if record["object_id"] != "None":
            objects[record["object_id"]] = record
    return objects


def log_ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or a <= 0 or b <= 0:
        return None
    return math.log((a + EPS) / (b + EPS))


def ratio_band(value: float | None) -> str:
    if value is None:
        return "missing"
    abs_value = abs(value)
    if abs_value < AMBIGUOUS_LOG_RATIO:
        return "ambiguous_lt_1.15"
    if abs_value < WEAK_LOG_RATIO:
        return "weak_1.15_1.25"
    if abs_value < STRONG_LOG_RATIO:
        return "medium_1.25_1.50"
    return "strong_ge_1.50"


def signed_direction(value: float | None) -> str:
    if value is None:
        return "missing"
    if value >= AMBIGUOUS_LOG_RATIO:
        return "subject_bigger"
    if value <= -AMBIGUOUS_LOG_RATIO:
        return "subject_smaller"
    return "ambiguous"


def predicate_compatible(predicate: str, direction: str) -> str:
    if direction == "ambiguous":
        return "ambiguous"
    if direction == "missing":
        return "missing"
    if predicate == "bigger than":
        return "compatible" if direction == "subject_bigger" else "opposes"
    if predicate == "smaller than":
        return "compatible" if direction == "subject_smaller" else "opposes"
    return "unsupported"


def pair_features(subject: dict[str, Any] | None, obj: dict[str, Any] | None) -> dict[str, Any]:
    if not subject or not obj:
        return {"pair_obb_status": "missing_object", "direction_by_volume": "missing"}
    if not subject.get("obb_available") or not obj.get("obb_available"):
        return {"pair_obb_status": "missing_obb", "direction_by_volume": "missing"}
    log_volume = log_ratio(subject.get("volume"), obj.get("volume"))
    log_max = log_ratio(subject.get("max_extent"), obj.get("max_extent"))
    log_footprint = log_ratio(subject.get("footprint_area"), obj.get("footprint_area"))
    log_vertical = log_ratio(subject.get("vertical_extent"), obj.get("vertical_extent"))
    vote_counter: Counter[str] = Counter()
    for value in [log_volume, log_max, log_footprint, log_vertical]:
        vote_counter[signed_direction(value)] += 1
    if vote_counter["subject_bigger"] >= 2:
        voted_direction = "subject_bigger"
    elif vote_counter["subject_smaller"] >= 2:
        voted_direction = "subject_smaller"
    else:
        voted_direction = "ambiguous"
    return {
        "pair_obb_status": "both_obb",
        "subject_label_semseg": subject.get("label", ""),
        "object_label_semseg": obj.get("label", ""),
        "subject_volume": subject.get("volume"),
        "object_volume": obj.get("volume"),
        "subject_max_extent": subject.get("max_extent"),
        "object_max_extent": obj.get("max_extent"),
        "subject_footprint_area": subject.get("footprint_area"),
        "object_footprint_area": obj.get("footprint_area"),
        "subject_vertical_extent": subject.get("vertical_extent"),
        "object_vertical_extent": obj.get("vertical_extent"),
        "log_volume_ratio_s_over_o": log_volume,
        "log_max_extent_ratio_s_over_o": log_max,
        "log_footprint_area_ratio_s_over_o": log_footprint,
        "log_vertical_extent_ratio_s_over_o": log_vertical,
        "volume_ratio_band": ratio_band(log_volume),
        "direction_by_volume": signed_direction(log_volume),
        "direction_by_vote": voted_direction,
        "size_vote_subject_bigger": vote_counter["subject_bigger"],
        "size_vote_subject_smaller": vote_counter["subject_smaller"],
        "size_vote_ambiguous": vote_counter["ambiguous"],
    }


def structural_pair(label_a: str, label_b: str) -> bool:
    return label_a.strip().lower() in STRUCTURAL_LABELS or label_b.strip().lower() in STRUCTURAL_LABELS


def collect_anchors(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = read_json(args.train_relationships)
    semseg_cache: dict[str, dict[str, dict[str, Any]]] = {}
    anchors: list[dict[str, Any]] = []
    source_stats = {
        "train_scan_entries": len(data.get("scans", [])),
        "train_relationship_rows": 0,
        "semseg_files_requested": 0,
        "semseg_files_found": 0,
    }
    for scan_entry in data.get("scans", []):
        scan_id = str(scan_entry.get("scan"))
        subgraph_id = str(scan_entry.get("split", "missing"))
        objects = {str(key): str(value).strip().lower() for key, value in (scan_entry.get("objects") or {}).items()}
        for rel in scan_entry.get("relationships", []):
            source_stats["train_relationship_rows"] += 1
            predicate = predicate_from_relation(rel)
            if predicate not in SIZE_PREDICATES:
                continue
            subject_id, object_id = endpoint_from_relation(rel)
            if not subject_id or not object_id:
                continue
            if scan_id not in semseg_cache:
                source_stats["semseg_files_requested"] += 1
                semseg_cache[scan_id] = load_semseg(args.scan_root, scan_id)
                if semseg_cache[scan_id]:
                    source_stats["semseg_files_found"] += 1
            semseg_objects = semseg_cache[scan_id]
            subject = semseg_objects.get(subject_id)
            obj = semseg_objects.get(object_id)
            features = pair_features(subject, obj)
            subject_label = (objects.get(subject_id) or features.get("subject_label_semseg") or "").strip().lower()
            object_label = (objects.get(object_id) or features.get("object_label_semseg") or "").strip().lower()
            direction = features.get("direction_by_volume", "missing")
            compatibility = predicate_compatible(predicate, direction)
            vote_compatibility = predicate_compatible(predicate, features.get("direction_by_vote", "missing"))
            row = {
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
                "pair_obb_status": features.get("pair_obb_status"),
                "volume_ratio_band": features.get("volume_ratio_band", "missing"),
                "direction_by_volume": direction,
                "direction_by_vote": features.get("direction_by_vote", "missing"),
                "gt_compatible_by_volume": compatibility,
                "gt_compatible_by_vote": vote_compatibility,
                "structural_pair": structural_pair(subject_label, object_label),
                "directed_pair_key": f"{scan_id}::{subject_id}->{object_id}",
                "directed_pair_predicate_key": f"{scan_id}::{subject_id}->{object_id}::{predicate}",
                "subgraph_anchor_key": f"{scan_id}::{subgraph_id}::{subject_id}->{object_id}::{predicate}",
            }
            row.update(features)
            anchors.append(row)
    source_stats["unique_scan_ids_with_size_anchors"] = len({row["scan_id"] for row in anchors})
    source_stats["semseg_cache_entries"] = len(semseg_cache)
    return anchors, source_stats


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def top_counter_rows(counter: Counter[Any], name: str, limit: int = 40) -> list[dict[str, Any]]:
    return [{name: key, "count": int(value)} for key, value in counter.most_common(limit)]


def unique_by_key(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        row_key = str(row.get(key))
        if row_key in seen:
            continue
        seen.add(row_key)
        output.append(row)
    return output


def inventory_rows(anchors: list[dict[str, Any]], full_counts: Counter[str], plan_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    plan_counts = plan_summary.get("size_relative_scope", {}).get("gt_counts", {})
    for predicate in SIZE_PREDICATES:
        predicate_rows = [row for row in anchors if row["predicate_label"] == predicate]
        unique_predicate_rows = unique_by_key(predicate_rows, "directed_pair_predicate_key")
        both_obb = [row for row in predicate_rows if row.get("pair_obb_status") == "both_obb"]
        unique_both_obb = unique_by_key(both_obb, "directed_pair_predicate_key")
        compatible = [row for row in both_obb if row.get("gt_compatible_by_volume") == "compatible"]
        unique_compatible = unique_by_key(compatible, "directed_pair_predicate_key")
        ambiguous = [row for row in both_obb if row.get("gt_compatible_by_volume") == "ambiguous"]
        opposing = [row for row in both_obb if row.get("gt_compatible_by_volume") == "opposes"]
        structural = [row for row in predicate_rows if row.get("structural_pair")]
        rows.append(
            {
                "predicate_label": predicate,
                "plan_gt_count": plan_counts.get(predicate),
                "full_3dssg_relationship_count": full_counts.get(predicate, 0),
                "train_anchor_rows": len(predicate_rows),
                "train_unique_directed_pair_predicate": len(unique_predicate_rows),
                "both_obb_rows": len(both_obb),
                "both_obb_unique_directed_pair_predicate": len(unique_both_obb),
                "row_join_rate": round(len(both_obb) / len(predicate_rows), 6) if predicate_rows else 0.0,
                "unique_join_rate": round(len(unique_both_obb) / len(unique_predicate_rows), 6)
                if unique_predicate_rows
                else 0.0,
                "volume_compatible_rows": len(compatible),
                "volume_compatible_unique": len(unique_compatible),
                "volume_ambiguous_rows": len(ambiguous),
                "volume_opposes_rows": len(opposing),
                "structural_pair_rows": len(structural),
                "structural_pair_fraction": round(len(structural) / len(predicate_rows), 6) if predicate_rows else 0.0,
            }
        )
    return rows


def scan_inventory_rows(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in anchors:
        scan_id = row["scan_id"]
        groups[scan_id]["anchor_rows"] += 1
        groups[scan_id][row["predicate_label"]] += 1
        groups[scan_id][row.get("pair_obb_status", "missing")] += 1
    rows: list[dict[str, Any]] = []
    for scan_id, counts in groups.items():
        rows.append(
            {
                "scan_id": scan_id,
                "anchor_rows": counts["anchor_rows"],
                "bigger_than_rows": counts["bigger than"],
                "smaller_than_rows": counts["smaller than"],
                "both_obb_rows": counts["both_obb"],
                "missing_object_rows": counts["missing_object"],
                "missing_obb_rows": counts["missing_obb"],
                "row_join_rate": round(counts["both_obb"] / counts["anchor_rows"], 6) if counts["anchor_rows"] else 0.0,
            }
        )
    rows.sort(key=lambda row: row["anchor_rows"], reverse=True)
    return rows


def margin_inventory_rows(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
    for row in anchors:
        key = (row["predicate_label"], row.get("volume_ratio_band", "missing"), row.get("gt_compatible_by_volume", "missing"))
        groups[key]["rows"] += 1
    unique_sets: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in anchors:
        key = (row["predicate_label"], row.get("volume_ratio_band", "missing"), row.get("gt_compatible_by_volume", "missing"))
        unique_sets[key].add(row["directed_pair_predicate_key"])
    rows: list[dict[str, Any]] = []
    for key, counts in groups.items():
        predicate, band, compatibility = key
        rows.append(
            {
                "predicate_label": predicate,
                "volume_ratio_band": band,
                "gt_compatible_by_volume": compatibility,
                "rows": counts["rows"],
                "unique_directed_pair_predicate": len(unique_sets[key]),
            }
        )
    rows.sort(key=lambda row: (row["predicate_label"], row["volume_ratio_band"], row["gt_compatible_by_volume"]))
    return rows


def class_pair_inventory_rows(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in anchors:
        key = row["class_pair"]
        groups[key]["rows"] += 1
        groups[key][row["predicate_label"]] += 1
        groups[key][row.get("gt_compatible_by_volume", "missing")] += 1
        groups[key]["structural_pair"] += int(bool(row.get("structural_pair")))
    rows: list[dict[str, Any]] = []
    for key, counts in groups.items():
        rows.append(
            {
                "class_pair": key,
                "rows": counts["rows"],
                "bigger_than_rows": counts["bigger than"],
                "smaller_than_rows": counts["smaller than"],
                "compatible_rows": counts["compatible"],
                "ambiguous_rows": counts["ambiguous"],
                "opposes_rows": counts["opposes"],
                "structural_pair_rows": counts["structural_pair"],
                "predicate_balance_rows": 2 * min(counts["bigger than"], counts["smaller than"]),
            }
        )
    rows.sort(key=lambda row: (row["predicate_balance_rows"], row["rows"]), reverse=True)
    return rows


def capacity_summary(anchors: list[dict[str, Any]]) -> dict[str, Any]:
    both = [row for row in anchors if row.get("pair_obb_status") == "both_obb"]
    unique_both = unique_by_key(both, "directed_pair_predicate_key")
    strict = [
        row
        for row in both
        if row.get("gt_compatible_by_volume") == "compatible"
        and row.get("volume_ratio_band") in {"medium_1.25_1.50", "strong_ge_1.50"}
    ]
    strict_unique = unique_by_key(strict, "directed_pair_predicate_key")
    per_predicate = Counter(row["predicate_label"] for row in strict_unique)
    structural_unique = [row for row in strict_unique if row.get("structural_pair")]
    unique_all = unique_by_key(anchors, "directed_pair_predicate_key")
    join_rate = len(unique_both) / len(unique_all) if unique_all else 0.0
    structural_fraction = len(structural_unique) / len(strict_unique) if strict_unique else 0.0
    ready = (
        join_rate >= MIN_JOIN_RATE
        and len(strict_unique) >= MIN_STRICT_UNIQUE_FLIP_GROUPS
        and all(per_predicate[predicate] >= MIN_STRICT_UNIQUE_PER_PREDICATE for predicate in SIZE_PREDICATES)
        and structural_fraction <= MAX_STRUCTURAL_FRACTION_FOR_MAIN
    )
    return {
        "unique_anchor_predicate_pairs": len(unique_all),
        "unique_both_obb_predicate_pairs": len(unique_both),
        "unique_join_rate": round(join_rate, 6),
        "strict_compatible_unique_flip_groups": len(strict_unique),
        "strict_compatible_same_g_predicate_flip_rows": len(strict_unique) * 2,
        "strict_compatible_unique_by_predicate": counter_dict(per_predicate),
        "strict_structural_unique_rows": len(structural_unique),
        "strict_structural_fraction": round(structural_fraction, 6) if strict_unique else 0.0,
        "ready_for_materialization_plan": ready,
        "thresholds": {
            "min_join_rate": MIN_JOIN_RATE,
            "min_strict_unique_flip_groups": MIN_STRICT_UNIQUE_FLIP_GROUPS,
            "min_strict_unique_per_predicate": MIN_STRICT_UNIQUE_PER_PREDICATE,
            "max_structural_fraction_for_main": MAX_STRUCTURAL_FRACTION_FOR_MAIN,
            "ambiguous_log_ratio": AMBIGUOUS_LOG_RATIO,
            "weak_log_ratio": WEAK_LOG_RATIO,
            "strong_log_ratio": STRONG_LOG_RATIO,
        },
    }


def build_report(summary: dict[str, Any], predicate_rows: list[dict[str, Any]], capacity: dict[str, Any]) -> str:
    lines = [
        "# H002 Size-Relative Source Inventory After Schema Probe Plan",
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
        "| predicate | train rows | unique pair-predicate | both OBB rows | row join | compatible rows | ambiguous rows | opposing rows | structural frac |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in predicate_rows:
        lines.append(
            "| {predicate_label} | {train_anchor_rows} | {train_unique_directed_pair_predicate} | "
            "{both_obb_rows} | {row_join_rate:.3f} | {volume_compatible_rows} | "
            "{volume_ambiguous_rows} | {volume_opposes_rows} | {structural_pair_fraction:.3f} |".format(**row)
        )
    lines += [
        "",
        "## Same-G Predicate-Flip Capacity",
        "",
        "- `strict_compatible_unique_flip_groups`: "
        f"{capacity['strict_compatible_unique_flip_groups']}",
        "- `strict_compatible_same_g_predicate_flip_rows`: "
        f"{capacity['strict_compatible_same_g_predicate_flip_rows']}",
        "- `unique_join_rate`: "
        f"{capacity['unique_join_rate']}",
        "- `strict_structural_fraction`: "
        f"{capacity['strict_structural_fraction']}",
        "",
        "## Interpretation",
        "",
        "- This stage did not materialize model rows and did not run learned smoke.",
        "- `G_e_size` remains predicate/source independent: OBB scale ratios only.",
        "- GT predicates are used only for source inventory and same-G flip capacity planning.",
        "- If promoted next, materialization must hide GT/source/construction fields from the model-safe view.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary_path = args.schema_plan_dir / "summary.json"
    plan_errors_path = args.schema_plan_dir / "validation_errors.jsonl"
    plan_summary = read_json(plan_summary_path) if plan_summary_path.exists() else {}
    plan_errors = read_jsonl(plan_errors_path)
    validation_errors = validate_inputs(plan_summary, plan_errors, args)

    full_counts: Counter[str] = Counter()
    anchors: list[dict[str, Any]] = []
    source_stats: dict[str, Any] = {}
    if not validation_errors:
        full_counts = count_predicates(args.full_relationships)
        anchors, source_stats = collect_anchors(args)

    predicate_rows = inventory_rows(anchors, full_counts, plan_summary) if anchors else []
    scan_rows = scan_inventory_rows(anchors) if anchors else []
    margin_rows = margin_inventory_rows(anchors) if anchors else []
    class_rows = class_pair_inventory_rows(anchors) if anchors else []
    capacity = capacity_summary(anchors) if anchors else {
        "ready_for_materialization_plan": False,
        "unique_anchor_predicate_pairs": 0,
        "unique_both_obb_predicate_pairs": 0,
        "unique_join_rate": 0.0,
        "strict_compatible_unique_flip_groups": 0,
        "strict_compatible_same_g_predicate_flip_rows": 0,
        "strict_compatible_unique_by_predicate": {},
        "strict_structural_unique_rows": 0,
        "strict_structural_fraction": 0.0,
        "thresholds": {},
    }

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_by_input_validation_errors"
        next_todo = EXPECTED_PLAN_NEXT
    elif capacity["ready_for_materialization_plan"]:
        status = STATUS_READY
        selected_path = SELECTED_READY
        next_todo = NEXT_READY
    else:
        status = STATUS_DIAGNOSTIC
        selected_path = SELECTED_DIAGNOSTIC
        next_todo = NEXT_DIAGNOSTIC

    output_paths = {
        "source_inventory": args.output_dir / "source_inventory.csv",
        "predicate_anchor_inventory": args.output_dir / "predicate_anchor_inventory.csv",
        "semseg_join_inventory": args.output_dir / "semseg_join_inventory.csv",
        "size_margin_inventory": args.output_dir / "size_margin_inventory.csv",
        "class_pair_inventory": args.output_dir / "class_pair_inventory.csv",
        "anchor_preview": args.output_dir / "anchor_preview.jsonl",
        "next_plan_contract": args.output_dir / "next_plan_contract.json",
        "report": args.output_dir / "report.md",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    source_inventory = [
        {
            "source_id": "3dssg_subset_relationships_train",
            "path": rel_path(args.train_relationships),
            "exists": args.train_relationships.exists(),
            "role": "train-side size-relative GT anchors with object labels",
            "rows_or_files": source_stats.get("train_relationship_rows", ""),
        },
        {
            "source_id": "3dssg_relationships_full_reference",
            "path": rel_path(args.full_relationships),
            "exists": args.full_relationships.exists(),
            "role": "full-count reference only; not used for train materialization",
            "rows_or_files": sum(full_counts.values()) if full_counts else "",
        },
        {
            "source_id": "3rscan_semseg_obb",
            "path": rel_path(args.scan_root),
            "exists": args.scan_root.exists(),
            "role": "predicate-independent OBB scale features for G_e_size",
            "rows_or_files": source_stats.get("semseg_files_found", ""),
        },
    ]

    next_plan_contract = {
        "purpose": "Materialize size-relative same-G predicate-flip candidates only if source inventory is ready.",
        "next_todo": NEXT_READY if status == STATUS_READY else NEXT_DIAGNOSTIC,
        "ready_for_materialization_plan": bool(capacity["ready_for_materialization_plan"]),
        "must_preserve": [
            "train-only source",
            "same-G predicate-flip groups",
            "model-safe view excludes GT/source/construction labels",
            "G_e_size excludes predicate and source confidence",
            "Q_e_size carries OBB availability and ambiguous-size bands",
        ],
        "must_check_before_smoke": [
            "geometry-only view should be chance on same-G compatibility rows",
            "wrong-T control should collapse",
            "shuffled-G control should collapse",
            "class-pair and structural-object strata should not dominate",
        ],
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "schema_plan_dir": rel_path(args.schema_plan_dir),
            "train_relationships": rel_path(args.train_relationships),
            "full_relationships": rel_path(args.full_relationships),
            "scan_root": rel_path(args.scan_root),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "boundary": {
            "split": "train_only_source_inventory",
            "materializes_rows": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "source_stats": source_stats,
        "anchor_counts": {
            "anchor_rows": len(anchors),
            "unique_directed_pair_predicate": len(unique_by_key(anchors, "directed_pair_predicate_key")) if anchors else 0,
            "unique_directed_pairs": len({row["directed_pair_key"] for row in anchors}),
            "predicate_counts": counter_dict(Counter(row["predicate_label"] for row in anchors)),
            "pair_obb_status": counter_dict(Counter(row.get("pair_obb_status", "missing") for row in anchors)),
            "volume_compatibility": counter_dict(Counter(row.get("gt_compatible_by_volume", "missing") for row in anchors)),
            "volume_ratio_band": counter_dict(Counter(row.get("volume_ratio_band", "missing") for row in anchors)),
            "structural_pair_rows": sum(1 for row in anchors if row.get("structural_pair")),
        },
        "capacity": capacity,
        "claim_boundary": {
            "materialization_allowed_now": False,
            "paper_evidence_allowed_now": False,
            "geometry_only_success_counts_as_main_claim": False,
            "no_gt_as_negative_allowed": False,
        },
    }

    write_csv(output_paths["source_inventory"], source_inventory)
    write_csv(output_paths["predicate_anchor_inventory"], predicate_rows)
    write_csv(output_paths["semseg_join_inventory"], scan_rows)
    write_csv(output_paths["size_margin_inventory"], margin_rows)
    write_csv(output_paths["class_pair_inventory"], class_rows[:80])
    write_jsonl(output_paths["anchor_preview"], anchors[:80])
    write_json(output_paths["next_plan_contract"], next_plan_contract)
    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(build_report(summary, predicate_rows, capacity), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
