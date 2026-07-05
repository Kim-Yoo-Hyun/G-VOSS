#!/usr/bin/env python3
"""Materialize separated G_e/Q_e rows for support/contact individual predicates."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan"
)
DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory"
)
DEFAULT_CANDIDATE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan_ready"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_ready_for_schema_shortcut_audit"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_input_errors"
)
SELECTED_PATH = "materialized_gq_separated_point_mesh_view_audit_rows"
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit"

MAIN_PREDICATES = {"standing on", "lying on"}
DIAGNOSTIC_PREDICATES = {"supported by"}

PLY_NAME = "labels.instances.align.annotated.v2.ply"
VIEW_RE = re.compile(r"_view(?P<view>\d+)")
SCORE_RE = re.compile(r"_score_(?P<score>[-+0-9.eE]+)_ratio_(?P<ratio>[-+0-9.eE]+)")

FORBIDDEN_MODEL_SAFE_KEYS = {
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "source_id",
    "prediction_id",
    "directed_pair_id",
    "row_key",
    "candidate_role",
    "label_match_status",
    "queue_kind",
    "machine_hint",
    "matched_gt_ids",
    "matched_predicates",
    "geometry_status",
    "p_geom_valid",
    "semantic_rank",
    "semantic_score",
    "semantic_score_norm",
    "semantic_score_raw",
}
FORBIDDEN_KEY_SUBSTRINGS = ("_hidden", "path_hidden", "_path", "source_path")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def path_from_repo(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not fields:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(out):
        return default
    return out


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def bool01(value: Any) -> int:
    return 1 if bool(value) else 0


class ObjectPointStats:
    def __init__(self) -> None:
        self.count = 0
        self.sum_x = 0.0
        self.sum_y = 0.0
        self.sum_z = 0.0
        self.min_x = math.inf
        self.min_y = math.inf
        self.min_z = math.inf
        self.max_x = -math.inf
        self.max_y = -math.inf
        self.max_z = -math.inf

    def add(self, x: float, y: float, z: float) -> None:
        self.count += 1
        self.sum_x += x
        self.sum_y += y
        self.sum_z += z
        self.min_x = min(self.min_x, x)
        self.min_y = min(self.min_y, y)
        self.min_z = min(self.min_z, z)
        self.max_x = max(self.max_x, x)
        self.max_y = max(self.max_y, y)
        self.max_z = max(self.max_z, z)

    def to_features(self, prefix: str) -> dict[str, float]:
        if self.count <= 0:
            return {
                f"{prefix}_point_count": 0.0,
                f"{prefix}_centroid_x": 0.0,
                f"{prefix}_centroid_y": 0.0,
                f"{prefix}_centroid_z": 0.0,
                f"{prefix}_extent_x": 0.0,
                f"{prefix}_extent_y": 0.0,
                f"{prefix}_extent_z": 0.0,
                f"{prefix}_vertical_extent_ratio": 0.0,
                f"{prefix}_horizontal_extent_ratio": 0.0,
                f"{prefix}_flatness_proxy": 0.0,
                f"{prefix}_bottom_z": 0.0,
                f"{prefix}_top_z": 0.0,
                f"{prefix}_xy_area": 0.0,
                f"{prefix}_box_volume_proxy": 0.0,
            }
        extent_x = max(0.0, self.max_x - self.min_x)
        extent_y = max(0.0, self.max_y - self.min_y)
        extent_z = max(0.0, self.max_z - self.min_z)
        max_extent = max(extent_x, extent_y, extent_z, 1e-9)
        min_extent = min(value for value in [extent_x, extent_y, extent_z] if value >= 0.0)
        horizontal = max(extent_x, extent_y)
        xy_area = extent_x * extent_y
        volume = extent_x * extent_y * extent_z
        return {
            f"{prefix}_point_count": float(self.count),
            f"{prefix}_centroid_x": self.sum_x / self.count,
            f"{prefix}_centroid_y": self.sum_y / self.count,
            f"{prefix}_centroid_z": self.sum_z / self.count,
            f"{prefix}_extent_x": extent_x,
            f"{prefix}_extent_y": extent_y,
            f"{prefix}_extent_z": extent_z,
            f"{prefix}_vertical_extent_ratio": extent_z / max_extent,
            f"{prefix}_horizontal_extent_ratio": horizontal / max(extent_z, 1e-9),
            f"{prefix}_flatness_proxy": min_extent / max_extent,
            f"{prefix}_bottom_z": self.min_z,
            f"{prefix}_top_z": self.max_z,
            f"{prefix}_xy_area": xy_area,
            f"{prefix}_box_volume_proxy": volume,
        }


def parse_ply_object_stats(ply_path: Path, wanted_object_ids: set[int]) -> dict[int, ObjectPointStats]:
    stats = {object_id: ObjectPointStats() for object_id in wanted_object_ids}
    if not ply_path.exists() or not wanted_object_ids:
        return stats
    vertex_count = 0
    properties: list[str] = []
    in_vertex = False
    with ply_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if line.startswith("element vertex "):
                vertex_count = int(line.split()[-1])
                in_vertex = True
            elif line.startswith("element ") and not line.startswith("element vertex "):
                in_vertex = False
            elif in_vertex and line.startswith("property "):
                parts = line.split()
                if len(parts) >= 3:
                    properties.append(parts[-1])
            elif line == "end_header":
                break
        object_index = properties.index("objectId") if "objectId" in properties else -1
        if object_index < 0 or vertex_count <= 0:
            return stats
        for _ in range(vertex_count):
            raw = handle.readline()
            if not raw:
                break
            parts = raw.split()
            if len(parts) <= object_index or len(parts) < 3:
                continue
            try:
                object_id = int(parts[object_index])
            except ValueError:
                continue
            if object_id not in stats:
                continue
            try:
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
            except ValueError:
                continue
            stats[object_id].add(x, y, z)
    return stats


def xy_overlap(subject: ObjectPointStats, obj: ObjectPointStats) -> dict[str, float]:
    if subject.count <= 0 or obj.count <= 0:
        return {
            "point_xy_overlap_area": 0.0,
            "point_xy_overlap_subject_ratio": 0.0,
            "point_xy_overlap_object_ratio": 0.0,
            "point_xy_overlap_min_ratio": 0.0,
        }
    ix = max(0.0, min(subject.max_x, obj.max_x) - max(subject.min_x, obj.min_x))
    iy = max(0.0, min(subject.max_y, obj.max_y) - max(subject.min_y, obj.min_y))
    overlap_area = ix * iy
    subject_area = max((subject.max_x - subject.min_x) * (subject.max_y - subject.min_y), 1e-9)
    object_area = max((obj.max_x - obj.min_x) * (obj.max_y - obj.min_y), 1e-9)
    subject_ratio = overlap_area / subject_area
    object_ratio = overlap_area / object_area
    return {
        "point_xy_overlap_area": overlap_area,
        "point_xy_overlap_subject_ratio": subject_ratio,
        "point_xy_overlap_object_ratio": object_ratio,
        "point_xy_overlap_min_ratio": min(subject_ratio, object_ratio),
    }


def point_contact_features(subject: ObjectPointStats, obj: ObjectPointStats) -> dict[str, float]:
    if subject.count <= 0 or obj.count <= 0:
        base = {
            "point_surface_gap_subject_bottom_to_object_top": 0.0,
            "point_abs_surface_gap_subject_bottom_to_object_top": 0.0,
            "point_center_delta_z": 0.0,
            "point_center_distance_xy": 0.0,
            "point_subject_above_object_center": 0.0,
            "point_object_top_near_subject_bottom": 0.0,
            "point_support_contact_likelihood_proxy": 0.0,
        }
        base.update(xy_overlap(subject, obj))
        return base
    subject_cx = subject.sum_x / subject.count
    subject_cy = subject.sum_y / subject.count
    subject_cz = subject.sum_z / subject.count
    object_cx = obj.sum_x / obj.count
    object_cy = obj.sum_y / obj.count
    object_cz = obj.sum_z / obj.count
    gap = subject.min_z - obj.max_z
    abs_gap = abs(gap)
    center_delta_z = subject_cz - object_cz
    center_distance_xy = math.hypot(subject_cx - object_cx, subject_cy - object_cy)
    overlap = xy_overlap(subject, obj)
    near_contact = max(0.0, 1.0 - min(abs_gap / 0.25, 1.0))
    support_contact = overlap["point_xy_overlap_min_ratio"] * near_contact
    return {
        "point_surface_gap_subject_bottom_to_object_top": gap,
        "point_abs_surface_gap_subject_bottom_to_object_top": abs_gap,
        "point_center_delta_z": center_delta_z,
        "point_center_distance_xy": center_distance_xy,
        "point_subject_above_object_center": 1.0 if center_delta_z > 0.0 else 0.0,
        "point_object_top_near_subject_bottom": near_contact,
        "point_support_contact_likelihood_proxy": support_contact,
        **overlap,
    }


def parse_view_files(multi_view_dir: Path | None, object_id: int) -> dict[str, Any]:
    if multi_view_dir is None or not multi_view_dir.is_dir():
        return {
            "crop_paths": [],
            "direct_paths": [],
            "view_ids": [],
            "crop_count": 0,
            "direct_count": 0,
            "max_score": 0.0,
            "mean_score": 0.0,
            "max_ratio": 0.0,
            "mean_ratio": 0.0,
        }
    prefix = f"instance_{object_id}_class_"
    crop_files = sorted(multi_view_dir.glob(f"{prefix}*_croped_view*_*.jpg"))
    direct_files = [
        path
        for path in sorted(multi_view_dir.glob(f"{prefix}*_view*_*.jpg"))
        if "_croped_" not in path.name
    ]
    view_ids: set[int] = set()
    scores: list[float] = []
    ratios: list[float] = []
    for path in crop_files + direct_files:
        view_match = VIEW_RE.search(path.name)
        if view_match:
            view_ids.add(int(view_match.group("view")))
        score_match = SCORE_RE.search(path.name)
        if score_match:
            scores.append(as_float(score_match.group("score")))
            ratios.append(as_float(score_match.group("ratio")))
    return {
        "crop_paths": [rel_path(path) for path in crop_files[:8]],
        "direct_paths": [rel_path(path) for path in direct_files[:8]],
        "view_ids": sorted(view_ids),
        "crop_count": len(crop_files),
        "direct_count": len(direct_files),
        "max_score": max(scores) if scores else 0.0,
        "mean_score": sum(scores) / len(scores) if scores else 0.0,
        "max_ratio": max(ratios) if ratios else 0.0,
        "mean_ratio": sum(ratios) / len(ratios) if ratios else 0.0,
    }


def q_e_features(row: dict[str, Any]) -> dict[str, Any]:
    reasons = {str(code) for code in row.get("q_e_reason_codes") or []}
    state = str(row.get("q_e_state_plan") or "unknown")
    return {
        "point_pair_crop_possible": bool01(row.get("point_pair_crop_possible")),
        "mesh_contact_patch_possible": bool01(row.get("mesh_contact_patch_possible")),
        "multiview_packet_possible": bool01(row.get("multiview_packet_possible")),
        "scan_asset_complete": bool01(row.get("scan_asset_complete")),
        "semseg_both_objects_present": bool01(row.get("semseg_both_objects_present")),
        "subject_has_obb": bool01(row.get("subject_has_obb")),
        "object_has_obb": bool01(row.get("object_has_obb")),
        "visual_used_as_model_input": 0,
        "min_subject_object_segment_count": as_float(row.get("min_subject_object_segment_count")),
        "min_subject_object_crop_count": as_float(row.get("min_subject_object_crop_count")),
        "min_subject_object_total_image_count": as_float(row.get("min_subject_object_total_image_count")),
        "co_visible_view_count_proxy": as_float(row.get("co_visible_view_count_proxy")),
        "min_subject_object_max_view_score": as_float(row.get("min_subject_object_max_view_score")),
        "min_subject_object_obb_axis_ratio": as_float(row.get("min_subject_object_obb_axis_ratio")),
        "q_e_state_sufficient": 1 if state == "sufficient" else 0,
        "q_e_state_limited": 1 if state == "limited" else 0,
        "q_e_state_uncertain": 1 if state == "uncertain_or_low_observability" else 0,
        "q_e_state_code": {"uncertain_or_low_observability": 0.0, "limited": 0.5, "sufficient": 1.0}.get(state, 0.0),
        "q_e_reason_count": float(len(reasons)),
        "q_e_reason_low_crop_score": 1 if "low_crop_score" in reasons else 0,
        "q_e_reason_few_cropped_instance_views": 1 if "few_cropped_instance_views" in reasons else 0,
        "q_e_reason_low_semseg_segment_count": 1 if "low_semseg_segment_count" in reasons else 0,
        "q_e_reason_low_obb_axis_ratio": 1 if "low_obb_axis_ratio" in reasons else 0,
    }


def collect_key_paths(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    paths: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, subvalue in value.items():
            path = f"{prefix}.{key}" if prefix else key
            paths.append((key, path))
            paths.extend(collect_key_paths(subvalue, path))
    elif isinstance(value, list):
        for idx, subvalue in enumerate(value):
            paths.extend(collect_key_paths(subvalue, f"{prefix}[{idx}]"))
    return paths


def blocked_key_hits(row: dict[str, Any]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for key, path in collect_key_paths(row):
        if key in FORBIDDEN_MODEL_SAFE_KEYS:
            hits.append({"path": path, "key": key, "reason": "forbidden_exact_key"})
            continue
        if any(fragment in key for fragment in FORBIDDEN_KEY_SUBSTRINGS):
            hits.append({"path": path, "key": key, "reason": "forbidden_key_substring"})
    return hits


def numeric_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values: dict[str, list[float]] = defaultdict(list)
    missing: Counter[str] = Counter()
    for row in rows:
        blocks = row.get("feature_blocks", {})
        for block_name, block in blocks.items():
            if not isinstance(block, dict):
                continue
            for key, value in block.items():
                stat_key = f"{block_name}.{key}"
                if isinstance(value, bool):
                    values[stat_key].append(1.0 if value else 0.0)
                elif isinstance(value, (int, float)):
                    if math.isfinite(float(value)):
                        values[stat_key].append(float(value))
                    else:
                        missing[stat_key] += 1
                elif value is None:
                    missing[stat_key] += 1
    out: dict[str, Any] = {}
    for key in sorted(set(values) | set(missing)):
        vals = values.get(key, [])
        out[key] = {
            "count": len(vals),
            "missing_or_nonfinite": missing.get(key, 0),
            "min": min(vals) if vals else None,
            "max": max(vals) if vals else None,
            "mean": sum(vals) / len(vals) if vals else None,
        }
    return out


def validate_inputs(
    plan_summary: dict[str, Any],
    plan_errors: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
    source_manifest: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append(
            {
                "input": "materialization_plan_summary",
                "error_type": "unexpected_status",
                "actual": plan_summary.get("status"),
                "expected": EXPECTED_PLAN_STATUS,
            }
        )
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append(
            {
                "input": "materialization_plan_summary",
                "error_type": "unexpected_next_todo",
                "actual": plan_summary.get("next_todo"),
                "expected": EXPECTED_PLAN_NEXT,
            }
        )
    if plan_summary.get("validation_errors") != 0:
        errors.append(
            {
                "input": "materialization_plan_summary",
                "error_type": "validation_errors_present",
                "actual": plan_summary.get("validation_errors"),
            }
        )
    if plan_errors:
        errors.append({"input": "plan_validation_errors", "error_type": "rows_present", "rows": len(plan_errors)})
    expected = 800
    for name, rows in [
        ("inventory_rows", inventory_rows),
        ("source_manifest", source_manifest),
        ("candidate_rows", candidate_rows),
        ("hidden_rows", hidden_rows),
    ]:
        if len(rows) != expected:
            errors.append({"input": name, "error_type": "unexpected_row_count", "actual": len(rows), "expected": expected})
    boundary = plan_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
        "visual_model_input_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append(
                {
                    "input": "materialization_plan_summary",
                    "error_type": "boundary_not_false",
                    "key": key,
                    "actual": boundary.get(key),
                }
            )
    row_ids = [set(str(row.get("row_id")) for row in rows) for rows in [inventory_rows, source_manifest, candidate_rows, hidden_rows]]
    if len({frozenset(ids) for ids in row_ids}) != 1:
        errors.append({"input": "row_ids", "error_type": "row_id_sets_do_not_match"})
    return errors


def build_control_manifest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_predicate: dict[str, list[int]] = defaultdict(list)
    by_class_pair: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        by_predicate[str(row.get("predicate_label"))].append(idx)
        by_class_pair[str(row.get("class_pair"))].append(idx)

    def pick_global(idx: int, offset: int) -> int:
        n = len(rows)
        if n <= 1:
            return idx
        return (idx + offset) % n

    def pick_from(indices: list[int], idx: int, offset: int = 1) -> int:
        if len(indices) <= 1:
            return pick_global(idx, offset + 97)
        pos = indices.index(idx)
        picked = indices[(pos + offset) % len(indices)]
        return picked if picked != idx else indices[(pos + offset + 1) % len(indices)]

    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        predicate = str(row.get("predicate_label"))
        class_pair = str(row.get("class_pair"))
        predicate_indices = by_predicate[predicate]
        different_class_same_predicate = [
            other_idx
            for other_idx in predicate_indices
            if other_idx != idx and str(rows[other_idx].get("class_pair")) != class_pair
        ]
        wrong_pair_idx = different_class_same_predicate[0] if different_class_same_predicate else pick_from(predicate_indices, idx, 3)
        global_idx = pick_global(idx, 137)
        within_pred_idx = pick_from(predicate_indices, idx, 11)
        wrong_view_idx = pick_from(predicate_indices, idx, 17)
        class_pair_indices = by_class_pair[class_pair]
        class_pair_view_idx = pick_from(class_pair_indices, idx, 5) if len(class_pair_indices) > 1 else wrong_view_idx
        out.append(
            {
                "row_id": row["row_id"],
                "wrong_pair_geometry_row_id": rows[wrong_pair_idx]["row_id"],
                "wrong_pair_match_scope": "same_predicate_different_class_pair"
                if rows[wrong_pair_idx].get("class_pair") != class_pair
                else "same_predicate_fallback",
                "shuffled_geometry_global_row_id": rows[global_idx]["row_id"],
                "shuffled_geometry_within_predicate_row_id": rows[within_pred_idx]["row_id"],
                "wrong_view_row_id": rows[wrong_view_idx]["row_id"],
                "shuffled_view_within_predicate_or_class_pair_row_id": rows[class_pair_view_idx]["row_id"],
                "control_use_policy": "control_only_not_training_label",
            }
        )
    return out


def render_report(summary: dict[str, Any]) -> str:
    counts = summary["materialized_counts"]
    q_counts = counts["q_e_state_counts"]
    pred_counts = counts["predicate_counts"]
    return f"""# H002 Support/Contact Individual Predicate Point/Multiview Materialization

## Status

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
artifact_root = {summary["output_paths"]["artifact_root"]}
next_todo = {summary["next_todo"]}
```

## What This Step Did

이 단계는 support/contact individual predicate branch에서 `G_e`와 `Q_e`를 실제
row-level artifact로 분리했다. 실제 point crop/image crop 파일을 새로 복사하지 않고,
train-only source asset에서 object별 point extent, support/contact proxy, multi-view
metadata, observability metadata를 materialized feature/manifest로 저장했다.

중요한 boundary는 다음과 같다.

- `G_e`: predicate/source score/target label 없이 point/OBB/contact numeric evidence만 둔다.
- `Q_e`: evidence availability, view count, crop quality, missing/limited evidence만 둔다.
- `V_mv`: learned visual input이 아니라 audit/`Q_e` manifest로만 둔다.
- `Z_e`: source score/rank는 model-safe C_e input이 아니라 hidden source manifest에만 둔다.

## Counts

```text
rows = {counts["rows"]}
main_rows = {counts["main_rows"]}
diagnostic_rows = {counts["diagnostic_rows"]}
predicate_counts = {json.dumps(pred_counts, ensure_ascii=False, sort_keys=True)}
q_e_state_counts = {json.dumps(q_counts, ensure_ascii=False, sort_keys=True)}
point_stats_found_rows = {counts["point_stats_found_rows"]}
validation_errors = {summary["validation_errors"]}
```

## Outputs

- `model_safe_view.jsonl`: `T_e`, `G_e_obb_baseline`, `G_e_point_pose`, `G_e_contact_patch`, `Q_e_observability`, labels.
- `source_manifest.jsonl`: scan/object/source confidence/provenance hidden manifest.
- `visual_audit_manifest.jsonl`: multi-view crop metadata and paths for audit/control only.
- `control_manifest.jsonl`: wrong-pair geometry, shuffled geometry, wrong-view, shuffled-view pairings.
- `feature_stats.json`: numeric feature finite/range audit.
- `validation_errors.jsonl`: materialization validation errors.

## Interpretation

이 산출물은 아직 learned smoke가 아니다. 다음 단계는 schema/shortcut audit이며, 여기서
`predicate`, `class_pair`, `rank/source`, raw geometry or Q-state가 target을 너무 쉽게
맞추는지 확인해야 한다. 통과하지 못하면 point/multiview feature를 붙였더라도 main
learned target으로 올리지 않는다.
"""


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    inventory_rows = read_jsonl(args.source_inventory_dir / "inventory_rows.jsonl")
    source_rows = read_jsonl(args.source_inventory_dir / "source_manifest.jsonl")
    candidate_rows = read_jsonl(args.candidate_dir / "model_safe_view.jsonl")
    hidden_rows = read_jsonl(args.candidate_dir / "hidden_manifest.jsonl")

    validation_errors = validate_inputs(
        plan_summary,
        plan_errors,
        inventory_rows,
        source_rows,
        candidate_rows,
        hidden_rows,
    )

    inventory_by_id = {str(row.get("row_id")): row for row in inventory_rows}
    source_by_id = {str(row.get("row_id")): row for row in source_rows}
    candidate_by_id = {str(row.get("row_id")): row for row in candidate_rows}
    hidden_by_id = {str(row.get("row_id")): row for row in hidden_rows}

    scan_object_ids: dict[str, set[int]] = defaultdict(set)
    for row in inventory_rows:
        scan_id = str(row.get("scan_id_hidden"))
        scan_object_ids[scan_id].add(as_int(row.get("subject_id_hidden")))
        scan_object_ids[scan_id].add(as_int(row.get("object_id_hidden")))

    point_stats_by_scan: dict[str, dict[int, ObjectPointStats]] = {}
    for scan_id, object_ids in sorted(scan_object_ids.items()):
        source_row = next((row for row in source_rows if str(row.get("scan_id_hidden")) == scan_id), None)
        ply_path = path_from_repo(str(source_row.get("aligned_ply_path_hidden"))) if source_row else None
        if ply_path is None:
            point_stats_by_scan[scan_id] = {object_id: ObjectPointStats() for object_id in object_ids}
            continue
        point_stats_by_scan[scan_id] = parse_ply_object_stats(ply_path, object_ids)

    materialized_rows: list[dict[str, Any]] = []
    source_manifest: list[dict[str, Any]] = []
    visual_manifest: list[dict[str, Any]] = []
    point_found_rows = 0

    for row in inventory_rows:
        row_id = str(row.get("row_id"))
        candidate = candidate_by_id[row_id]
        hidden = hidden_by_id[row_id]
        source = source_by_id[row_id]
        scan_id = str(row.get("scan_id_hidden"))
        subject_id = as_int(row.get("subject_id_hidden"))
        object_id = as_int(row.get("object_id_hidden"))
        subject_stats = point_stats_by_scan.get(scan_id, {}).get(subject_id, ObjectPointStats())
        object_stats = point_stats_by_scan.get(scan_id, {}).get(object_id, ObjectPointStats())
        if subject_stats.count > 0 and object_stats.count > 0:
            point_found_rows += 1

        t_e = dict(candidate.get("feature_blocks", {}).get("T_e", {}))
        g_obb = dict(candidate.get("feature_blocks", {}).get("G_e_mesh_pose_contact", {}))
        g_point = {
            **subject_stats.to_features("subject"),
            **object_stats.to_features("object"),
            "pair_min_point_count": float(min(subject_stats.count, object_stats.count)),
            "pair_total_point_count": float(subject_stats.count + object_stats.count),
        }
        g_contact = point_contact_features(subject_stats, object_stats)
        q_e = q_e_features(row)

        materialized = {
            "dataset_name": "h002_support_contact_individual_predicate_point_multiview_v1",
            "schema_version": f"{SCHEMA_VERSION}_model_safe_view",
            "row_id": row_id,
            "split": "train",
            "subset": candidate.get("subset"),
            "model_use": candidate.get("model_use"),
            "feature_blocks": {
                "T_e": t_e,
                "G_e_obb_baseline": g_obb,
                "G_e_point_pose": g_point,
                "G_e_contact_patch": g_contact,
                "Q_e_observability": q_e,
            },
            "labels": candidate.get("labels", {}),
        }
        for hit in blocked_key_hits(materialized):
            validation_errors.append(
                {
                    "row_id": row_id,
                    "error_type": "model_safe_blocked_key",
                    **hit,
                }
            )
        materialized_rows.append(materialized)

        multi_view_dir = path_from_repo(source.get("multi_view_dir_hidden"))
        subject_views = parse_view_files(multi_view_dir, subject_id)
        object_views = parse_view_files(multi_view_dir, object_id)
        subject_view_ids = set(subject_views["view_ids"])
        object_view_ids = set(object_views["view_ids"])
        visual_manifest.append(
            {
                "schema_version": f"{SCHEMA_VERSION}_visual_audit_manifest",
                "row_id": row_id,
                "predicate_label": row.get("predicate_label"),
                "subject_label": row.get("subject_label"),
                "object_label": row.get("object_label"),
                "q_e_state_plan": row.get("q_e_state_plan"),
                "visual_use_policy": "audit_and_Q_e_first_not_learned_visual_input",
                "visual_model_input_allowed": False,
                "multi_view_dir_hidden": rel_path(multi_view_dir) if multi_view_dir else "",
                "sequence_zip_path_hidden": source.get("sequence_zip_path_hidden", ""),
                "subject_crop_count": subject_views["crop_count"],
                "object_crop_count": object_views["crop_count"],
                "subject_direct_view_count": subject_views["direct_count"],
                "object_direct_view_count": object_views["direct_count"],
                "subject_view_ids_hidden": sorted(subject_view_ids),
                "object_view_ids_hidden": sorted(object_view_ids),
                "co_visible_view_ids_hidden": sorted(subject_view_ids & object_view_ids),
                "subject_crop_paths_hidden": subject_views["crop_paths"],
                "object_crop_paths_hidden": object_views["crop_paths"],
                "subject_direct_paths_hidden": subject_views["direct_paths"],
                "object_direct_paths_hidden": object_views["direct_paths"],
                "subject_max_view_score": subject_views["max_score"],
                "object_max_view_score": object_views["max_score"],
                "subject_mean_view_ratio": subject_views["mean_ratio"],
                "object_mean_view_ratio": object_views["mean_ratio"],
            }
        )

        source_manifest.append(
            {
                "schema_version": f"{SCHEMA_VERSION}_source_manifest",
                "row_id": row_id,
                "scan_id_hidden": scan_id,
                "subgraph_id_hidden": hidden.get("subgraph_id"),
                "subject_id_hidden": subject_id,
                "object_id_hidden": object_id,
                "predicate_label": row.get("predicate_label"),
                "class_pair_hidden": hidden.get("class_pair"),
                "candidate_role_hidden": hidden.get("candidate_role"),
                "label_match_status_hidden": hidden.get("label_match_status"),
                "queue_kind_hidden": hidden.get("queue_kind"),
                "rank_band_hidden": hidden.get("rank_band"),
                "source_id_hidden": hidden.get("source_id"),
                "semantic_rank_hidden": hidden.get("semantic_rank"),
                "semantic_score_norm_hidden": hidden.get("semantic_score_norm"),
                "semantic_score_raw_hidden": hidden.get("semantic_score_raw"),
                "p_geom_valid_hidden": hidden.get("p_geom_valid"),
                "machine_hint_hidden": hidden.get("machine_hint"),
                "source_confidence_policy": "Z_e_hidden_for_later_p_rel_ablation_excluded_from_C_e",
                "aligned_ply_path_hidden": source.get("aligned_ply_path_hidden"),
                "semseg_path_hidden": source.get("semseg_path_hidden"),
                "mesh_obj_path_hidden": source.get("mesh_obj_path_hidden"),
                "mesh_seg_path_hidden": source.get("mesh_seg_path_hidden"),
                "multi_view_dir_hidden": source.get("multi_view_dir_hidden"),
                "sequence_zip_path_hidden": source.get("sequence_zip_path_hidden"),
                "point_subject_count": subject_stats.count,
                "point_object_count": object_stats.count,
            }
        )

    materialization_input_rows = [
        {
            "row_id": str(row.get("row_id")),
            "predicate_label": str(row.get("predicate_label")),
            "class_pair": str(row.get("class_pair")),
        }
        for row in inventory_rows
    ]
    control_manifest = build_control_manifest(materialization_input_rows)

    for output_name, rows in [
        ("model_safe_view", materialized_rows),
        ("source_manifest", source_manifest),
        ("visual_audit_manifest", visual_manifest),
        ("control_manifest", control_manifest),
    ]:
        if len(rows) != 800:
            validation_errors.append(
                {
                    "output": output_name,
                    "error_type": "unexpected_row_count",
                    "actual": len(rows),
                    "expected": 800,
                }
            )

    for row in control_manifest:
        for key, value in row.items():
            if key.endswith("_row_id") and value == row["row_id"]:
                validation_errors.append(
                    {
                        "row_id": row["row_id"],
                        "error_type": "self_control_pairing",
                        "field": key,
                    }
                )

    feature_stats = numeric_stats(materialized_rows)
    for key, stat in feature_stats.items():
        if stat["count"] != len(materialized_rows) and key.startswith(("G_e_", "Q_e_")):
            validation_errors.append(
                {
                    "feature": key,
                    "error_type": "numeric_feature_incomplete",
                    "count": stat["count"],
                    "expected": len(materialized_rows),
                    "missing_or_nonfinite": stat["missing_or_nonfinite"],
                }
            )

    pred_counts = Counter(str(row.get("predicate_label")) for row in inventory_rows)
    q_counts = Counter(str(row.get("q_e_state_plan")) for row in inventory_rows)
    model_use_counts = Counter(str(row.get("model_use")) for row in materialized_rows)
    now = datetime.now(timezone.utc).isoformat()
    status = STATUS_READY if not validation_errors else STATUS_ERROR

    output_paths = {
        "artifact_root": rel_path(args.output_dir),
        "model_safe_view": rel_path(args.output_dir / "model_safe_view.jsonl"),
        "source_manifest": rel_path(args.output_dir / "source_manifest.jsonl"),
        "visual_audit_manifest": rel_path(args.output_dir / "visual_audit_manifest.jsonl"),
        "control_manifest": rel_path(args.output_dir / "control_manifest.jsonl"),
        "feature_stats": rel_path(args.output_dir / "feature_stats.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        "summary": rel_path(args.output_dir / "summary.json"),
        "report": rel_path(args.output_dir / "report.md"),
        "model_safe_preview": rel_path(args.output_dir / "model_safe_preview.jsonl"),
        "feature_stats_summary": rel_path(args.output_dir / "feature_stats_summary.csv"),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": now,
        "status": status,
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "boundary": {
            "split": "train_only_materialization",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "materializes_point_crop_files": False,
            "materializes_multiview_crop_files": False,
            "materializes_point_numeric_features": True,
            "visual_model_input_allowed": False,
            "multiview_used_as_audit_and_Q_e_metadata_only": True,
            "source_confidence_in_model_safe_C_e": False,
        },
        "input_paths": {
            "plan_summary": rel_path(args.plan_dir / "summary.json"),
            "source_inventory_rows": rel_path(args.source_inventory_dir / "inventory_rows.jsonl"),
            "candidate_model_safe_view": rel_path(args.candidate_dir / "model_safe_view.jsonl"),
            "candidate_hidden_manifest": rel_path(args.candidate_dir / "hidden_manifest.jsonl"),
        },
        "output_paths": output_paths,
        "materialized_counts": {
            "rows": len(materialized_rows),
            "main_rows": sum(1 for row in materialized_rows if row.get("model_use") == "main_train_candidate_if_schema_audit_passes"),
            "diagnostic_rows": sum(1 for row in materialized_rows if row.get("model_use") != "main_train_candidate_if_schema_audit_passes"),
            "predicate_counts": dict(sorted(pred_counts.items())),
            "q_e_state_counts": dict(sorted(q_counts.items())),
            "model_use_counts": dict(sorted(model_use_counts.items())),
            "scans_parsed": len(point_stats_by_scan),
            "objects_requested": sum(len(ids) for ids in scan_object_ids.values()),
            "point_stats_found_rows": point_found_rows,
        },
        "feature_block_policy": {
            "T_e": "semantic content only",
            "G_e_obb_baseline": "existing semseg OBB numeric geometry baseline",
            "G_e_point_pose": "predicate-independent point extent/pose features",
            "G_e_contact_patch": "predicate-independent support/contact numeric proxies",
            "Q_e_observability": "availability/coverage/quality only, not truth label",
            "V_mv": "visual audit manifest only",
            "Z_e": "hidden source manifest only, excluded from C_e",
        },
        "control_manifest": {
            "rows": len(control_manifest),
            "controls": [
                "wrong_pair_geometry",
                "shuffled_geometry_global",
                "shuffled_geometry_within_predicate",
                "wrong_view",
                "shuffled_view_within_predicate_or_class_pair",
            ],
        },
        "validation_errors": len(validation_errors),
    }

    write_jsonl(args.output_dir / "model_safe_view.jsonl", materialized_rows)
    write_jsonl(args.output_dir / "source_manifest.jsonl", source_manifest)
    write_jsonl(args.output_dir / "visual_audit_manifest.jsonl", visual_manifest)
    write_jsonl(args.output_dir / "control_manifest.jsonl", control_manifest)
    write_json(args.output_dir / "feature_stats.json", feature_stats)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    write_jsonl(args.output_dir / "model_safe_preview.jsonl", materialized_rows[:20])
    write_csv(
        args.output_dir / "feature_stats_summary.csv",
        [
            {"feature": feature, **stats}
            for feature, stats in sorted(feature_stats.items())
        ],
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
