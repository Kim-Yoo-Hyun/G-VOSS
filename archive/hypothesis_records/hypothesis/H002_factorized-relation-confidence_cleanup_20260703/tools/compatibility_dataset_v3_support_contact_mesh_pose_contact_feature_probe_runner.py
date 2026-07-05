#!/usr/bin/env python3
"""Derive and audit support/contact mesh-pose-contact feature candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan"
DEFAULT_SOURCE_INVENTORY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory"
DEFAULT_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner"
EXPECTED_SOURCE_STATUS = "h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_ready_for_mesh_pose_contact_probe"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner_ready_for_result_review"
STATUS_DIAGNOSTIC = "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner_diagnostic_only"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner_input_errors"
SELECTED_PATH_READY = "review_mesh_pose_contact_features_before_materialization"
NEXT_READY = "compatibility_dataset_v3_support_contact_feature_probe_result_review"
NEXT_DIAGNOSTIC = "compatibility_dataset_v3_support_contact_feature_probe_diagnostic_freeze"

SUPPORT_PREDICATES = {"standing on", "lying on", "supported by"}
HARD_SURFACES = {"floor", "wall", "ceiling", "room", "window", "door"}
TIER_B_TARGET_ROWS = 1200
TIER_B_CELL_TARGET = 100
TIER_B_SCAN_CAP = 4
TIER_B_VISIBLE_PAIR_CAP = 12
PREVIEW_LIMIT = 240
EPS = 1e-9

BLOCKED_MODEL_KEYS = {
    "source_score",
    "semantic_rank",
    "rank_band",
    "queue_kind",
    "geometry_status",
    "h001_verification_status",
    "label_match_status",
    "machine_hint",
    "counterfactual_type",
    "row_role",
    "human_label",
    "p_geom_valid",
    "consistency_score",
    "disagreement_score",
    "underconfidence_score",
}

TIER_A_FEATURES = [
    "center_delta_z",
    "surface_gap_subject_bottom_to_object_top",
    "abs_surface_gap_subject_bottom_to_object_top",
    "xy_overlap_min_ratio",
    "xy_overlap_subject_ratio",
    "xy_overlap_object_ratio",
    "support_area_proxy",
    "center_distance_xy",
    "normalized_center_distance_xy",
    "subject_major_axis_upness",
    "subject_minor_axis_upness",
    "subject_vertical_extent_ratio",
    "subject_flatness_ratio",
    "object_major_axis_upness",
    "object_minor_axis_upness",
    "object_vertical_extent_ratio",
    "object_flatness_ratio",
    "subject_normal_upness",
    "object_normal_upness",
    "normal_alignment",
    "support_normal_verticality",
    "obb_contact_likelihood_proxy",
]

TIER_B_FEATURES = [
    "point_subject_count",
    "point_object_count",
    "point_surface_gap_subject_bottom_to_object_top",
    "point_abs_surface_gap",
    "point_xy_overlap_min_ratio",
    "point_xy_overlap_subject_ratio",
    "point_xy_overlap_object_ratio",
    "point_subject_z_extent",
    "point_object_z_extent",
    "point_subject_vertical_extent_ratio",
    "point_object_vertical_extent_ratio",
    "point_subject_bottom_band_density",
    "point_object_top_band_density",
    "point_contact_candidate_ratio",
    "point_center_distance_xy",
]

OLD_NUMERIC_FIELDS = ["p_geom_valid", "consistency_score", "disagreement_score", "underconfidence_score", "geometry_satisfied_binary"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--rga-dir", type=Path, default=DEFAULT_RGA_DIR)
    parser.add_argument("--three-rscan-root", type=Path, default=DEFAULT_3RSCAN_ROOT)
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


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
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


def validate_inputs(
    plan_summary: dict[str, Any],
    source_summary: dict[str, Any],
    plan_errors: list[dict[str, Any]],
    source_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan_summary.get("validation_errors")})
    if plan_errors:
        errors.append({"error_type": "plan_validation_error_rows_present", "rows": len(plan_errors)})
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_status", "actual": source_summary.get("status")})
    if source_summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_validation_errors", "actual": source_summary.get("validation_errors")})
    if source_errors:
        errors.append({"error_type": "source_validation_error_rows_present", "rows": len(source_errors)})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified"]:
        if plan_summary.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": plan_summary.get("boundary", {}).get(key)})
        if source_summary.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "source_boundary_not_false", "key": key, "actual": source_summary.get("boundary", {}).get(key)})
    return errors


def support_family(row: dict[str, Any]) -> bool:
    return row.get("predicate_family") == "support_contact" and row.get("predicate_label") in SUPPORT_PREDICATES


def hard_surface(label: Any) -> bool:
    return str(label or "").lower() in HARD_SURFACES


def hard_surface_pair(row: dict[str, Any]) -> bool:
    return hard_surface(row.get("subject_label")) or hard_surface(row.get("object_label"))


def visible_pair(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')} [REL] {row.get('object_label')}"


def feature_id(row: dict[str, Any]) -> str:
    raw = f"{row.get('prediction_id')}|{row.get('scan_id')}|{row.get('subject_id')}|{row.get('object_id')}|{row.get('predicate_label')}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def stable_hash(row: dict[str, Any]) -> str:
    return hashlib.sha1(str(row.get("prediction_id", "")).encode("utf-8")).hexdigest()


def scan_support_queues(rga_dir: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    support_rows: list[dict[str, Any]] = []
    line_counts: dict[str, int] = {}
    for path in [rga_dir / "train_hl_queue.jsonl", rga_dir / "train_lh_queue.jsonl"]:
        count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                count += 1
                row = json.loads(line)
                if support_family(row):
                    support_rows.append(row)
        line_counts[rel_path(path)] = count
    support_rows.sort(key=stable_hash)
    return support_rows, line_counts


def normalize(vec: list[float] | tuple[float, ...] | None) -> list[float] | None:
    if not vec or len(vec) < 3:
        return None
    x, y, z = float(vec[0]), float(vec[1]), float(vec[2])
    norm = math.sqrt(x * x + y * y + z * z)
    if norm <= EPS:
        return None
    return [x / norm, y / norm, z / norm]


def dot_abs(a: list[float] | None, b: list[float] | None) -> float | None:
    if a is None or b is None:
        return None
    return abs(a[0] * b[0] + a[1] * b[1] + a[2] * b[2])


def read_semseg(path: Path) -> dict[int, dict[str, Any]]:
    payload = read_json(path)
    objects: dict[int, dict[str, Any]] = {}
    for group in payload.get("segGroups", []):
        oid = group.get("objectId", group.get("id"))
        if oid is None:
            continue
        try:
            oid_int = int(oid)
        except (TypeError, ValueError):
            continue
        objects[oid_int] = {
            "label": group.get("label"),
            "dominantNormal": normalize(group.get("dominantNormal")),
            "obb": group.get("obb") or {},
        }
    return objects


def axis_triples(obb: dict[str, Any]) -> list[list[float]] | None:
    axes = obb.get("normalizedAxes")
    if not isinstance(axes, list) or len(axes) != 9:
        return None
    return [
        [float(axes[0]), float(axes[1]), float(axes[2])],
        [float(axes[3]), float(axes[4]), float(axes[5])],
        [float(axes[6]), float(axes[7]), float(axes[8])],
    ]


def obb_world_box(obb: dict[str, Any]) -> dict[str, Any] | None:
    centroid = obb.get("centroid")
    lengths = obb.get("axesLengths")
    axes = axis_triples(obb)
    if not isinstance(centroid, list) or not isinstance(lengths, list) or axes is None:
        return None
    if len(centroid) != 3 or len(lengths) != 3:
        return None
    c = [float(centroid[0]), float(centroid[1]), float(centroid[2])]
    lens = [abs(float(value)) for value in lengths]
    half = []
    for dim in range(3):
        half.append(0.5 * sum(abs(axes[i][dim]) * lens[i] for i in range(3)))
    mins = [c[i] - half[i] for i in range(3)]
    maxs = [c[i] + half[i] for i in range(3)]
    extents = [maxs[i] - mins[i] for i in range(3)]
    upness = [abs(axis[2]) for axis in axes]
    major_idx = max(range(3), key=lambda idx: lens[idx])
    minor_idx = min(range(3), key=lambda idx: lens[idx])
    return {
        "centroid": c,
        "lengths": lens,
        "axes": axes,
        "mins": mins,
        "maxs": maxs,
        "extents": extents,
        "xy_area": max(extents[0], 0.0) * max(extents[1], 0.0),
        "volume": max(extents[0], 0.0) * max(extents[1], 0.0) * max(extents[2], 0.0),
        "major_axis_upness": upness[major_idx],
        "minor_axis_upness": upness[minor_idx],
        "vertical_extent_ratio": extents[2] / (max(extents[0], extents[1], EPS)),
        "flatness_ratio": min(lens) / max(max(lens), EPS),
    }


def overlap_1d(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def box_xy_overlap(a: dict[str, Any], b: dict[str, Any]) -> tuple[float, float, float]:
    ox = overlap_1d(a["mins"][0], a["maxs"][0], b["mins"][0], b["maxs"][0])
    oy = overlap_1d(a["mins"][1], a["maxs"][1], b["mins"][1], b["maxs"][1])
    area = ox * oy
    a_area = max(float(a["xy_area"]), EPS)
    b_area = max(float(b["xy_area"]), EPS)
    return area / max(min(a_area, b_area), EPS), area / a_area, area / b_area


def semseg_features(row: dict[str, Any], objects: dict[int, dict[str, Any]]) -> dict[str, float | None]:
    subject = objects.get(int(row["subject_id"]))
    obj = objects.get(int(row["object_id"]))
    if subject is None or obj is None:
        return {key: None for key in TIER_A_FEATURES}
    subj_box = obb_world_box(subject.get("obb") or {})
    obj_box = obb_world_box(obj.get("obb") or {})
    if subj_box is None or obj_box is None:
        return {key: None for key in TIER_A_FEATURES}
    xy_min, xy_subj, xy_obj = box_xy_overlap(subj_box, obj_box)
    gap = subj_box["mins"][2] - obj_box["maxs"][2]
    dz = subj_box["centroid"][2] - obj_box["centroid"][2]
    dx = subj_box["centroid"][0] - obj_box["centroid"][0]
    dy = subj_box["centroid"][1] - obj_box["centroid"][1]
    center_xy = math.sqrt(dx * dx + dy * dy)
    diag_norm = math.sqrt(max(subj_box["xy_area"], 0.0)) + math.sqrt(max(obj_box["xy_area"], 0.0)) + EPS
    subj_normal = subject.get("dominantNormal")
    obj_normal = obj.get("dominantNormal")
    subject_normal_upness = abs(subj_normal[2]) if subj_normal else None
    object_normal_upness = abs(obj_normal[2]) if obj_normal else None
    normal_alignment = dot_abs(subj_normal, obj_normal)
    support_normal_verticality = object_normal_upness
    contact_likelihood = xy_min / (1.0 + abs(gap))
    values: dict[str, float | None] = {
        "center_delta_z": dz,
        "surface_gap_subject_bottom_to_object_top": gap,
        "abs_surface_gap_subject_bottom_to_object_top": abs(gap),
        "xy_overlap_min_ratio": xy_min,
        "xy_overlap_subject_ratio": xy_subj,
        "xy_overlap_object_ratio": xy_obj,
        "support_area_proxy": xy_min,
        "center_distance_xy": center_xy,
        "normalized_center_distance_xy": center_xy / diag_norm,
        "subject_major_axis_upness": subj_box["major_axis_upness"],
        "subject_minor_axis_upness": subj_box["minor_axis_upness"],
        "subject_vertical_extent_ratio": subj_box["vertical_extent_ratio"],
        "subject_flatness_ratio": subj_box["flatness_ratio"],
        "object_major_axis_upness": obj_box["major_axis_upness"],
        "object_minor_axis_upness": obj_box["minor_axis_upness"],
        "object_vertical_extent_ratio": obj_box["vertical_extent_ratio"],
        "object_flatness_ratio": obj_box["flatness_ratio"],
        "subject_normal_upness": subject_normal_upness,
        "object_normal_upness": object_normal_upness,
        "normal_alignment": normal_alignment,
        "support_normal_verticality": support_normal_verticality,
        "obb_contact_likelihood_proxy": contact_likelihood,
    }
    return values


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


class Stats:
    def __init__(self) -> None:
        self.count = 0
        self.finite_count = 0
        self.missing_count = 0
        self.sum = 0.0
        self.sum_sq = 0.0
        self.min: float | None = None
        self.max: float | None = None

    def add(self, value: Any) -> None:
        self.count += 1
        if not finite(value):
            self.missing_count += 1
            return
        x = float(value)
        self.finite_count += 1
        self.sum += x
        self.sum_sq += x * x
        self.min = x if self.min is None else min(self.min, x)
        self.max = x if self.max is None else max(self.max, x)

    def mean(self) -> float | None:
        return self.sum / self.finite_count if self.finite_count else None

    def std(self) -> float | None:
        if self.finite_count <= 1:
            return 0.0 if self.finite_count == 1 else None
        mean = self.sum / self.finite_count
        variance = max(0.0, self.sum_sq / self.finite_count - mean * mean)
        return math.sqrt(variance)

    def row(self, feature: str, tier: str) -> dict[str, Any]:
        return {
            "tier": tier,
            "feature": feature,
            "rows": self.count,
            "non_missing_count": self.finite_count,
            "missing_count": self.missing_count,
            "non_missing_rate": self.finite_count / self.count if self.count else 0.0,
            "finite_count": self.finite_count,
            "finite_rate": self.finite_count / self.count if self.count else 0.0,
            "mean": self.mean(),
            "std": self.std(),
            "min": self.min,
            "max": self.max,
        }


def collect_stats(feature_rows: list[dict[str, Any]], features: list[str], tier: str) -> list[dict[str, Any]]:
    stats = {feature: Stats() for feature in features}
    for row in feature_rows:
        vals = row.get("features", {})
        for feature in features:
            stats[feature].add(vals.get(feature))
    return [stats[feature].row(feature, tier) for feature in features]


def group_stats(feature_rows: list[dict[str, Any]], features: list[str], group_getter: Any, group_name: str, tier: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], Stats] = defaultdict(Stats)
    for row in feature_rows:
        group_value = str(group_getter(row))
        vals = row.get("features", {})
        for feature in features:
            grouped[(feature, group_value)].add(vals.get(feature))
    rows: list[dict[str, Any]] = []
    for (feature, group_value), stat in sorted(grouped.items()):
        payload = stat.row(feature, tier)
        payload["group_axis"] = group_name
        payload["group_value"] = group_value
        rows.append(payload)
    return rows


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= EPS or vy <= EPS:
        return None
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    return cov / math.sqrt(vx * vy)


def numeric_old_values(row: dict[str, Any]) -> dict[str, float | None]:
    values: dict[str, float | None] = {}
    for key in ["p_geom_valid", "consistency_score", "disagreement_score", "underconfidence_score"]:
        value = row.get("audit", {}).get(key)
        values[key] = float(value) if finite(value) else None
    values["geometry_satisfied_binary"] = 1.0 if row.get("audit", {}).get("geometry_status") == "satisfied" else 0.0
    return values


def old_numeric_diagnostics(feature_rows: list[dict[str, Any]], features: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feature in features:
        for old_key in OLD_NUMERIC_FIELDS:
            xs: list[float] = []
            ys: list[float] = []
            for row in feature_rows:
                value = row.get("features", {}).get(feature)
                old_value = numeric_old_values(row).get(old_key)
                if finite(value) and finite(old_value):
                    xs.append(float(value))
                    ys.append(float(old_value))
            corr = pearson(xs, ys)
            rows.append(
                {
                    "feature": feature,
                    "old_numeric_field": old_key,
                    "paired_rows": len(xs),
                    "pearson": corr,
                    "abs_pearson": abs(corr) if corr is not None else None,
                    "dominance_risk": "high" if corr is not None and abs(corr) >= 0.95 else "low",
                }
            )
    return rows


def standardized_effect(group_a: list[float], group_b: list[float]) -> float | None:
    if len(group_a) < 2 or len(group_b) < 2:
        return None
    ma = sum(group_a) / len(group_a)
    mb = sum(group_b) / len(group_b)
    va = sum((x - ma) ** 2 for x in group_a) / max(len(group_a) - 1, 1)
    vb = sum((x - mb) ** 2 for x in group_b) / max(len(group_b) - 1, 1)
    pooled = math.sqrt(max(EPS, (va + vb) / 2.0))
    return (ma - mb) / pooled


def shortcut_risks(feature_rows: list[dict[str, Any]], features: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total = len(feature_rows)
    hard_rate = sum(1 for row in feature_rows if row["audit"]["hard_surface_pair"]) / total if total else 0.0
    queue_counts = Counter(row["audit"]["queue_kind"] for row in feature_rows)
    rows.append(
        {
            "risk": "hard_surface_dominance",
            "scope": "all_feature_rows",
            "value": hard_rate,
            "severity": "high" if hard_rate > 0.70 else "medium" if hard_rate > 0.40 else "low",
            "mitigation": "cap hard-surface rows before materialization",
        }
    )
    rows.append(
        {
            "risk": "queue_imbalance",
            "scope": "all_feature_rows",
            "value": json.dumps(dict(sorted(queue_counts.items())), sort_keys=True),
            "severity": "high",
            "mitigation": "queue_kind remains audit-only and must not become model input",
        }
    )
    for feature in features:
        hard_values: list[float] = []
        non_hard_values: list[float] = []
        hl_values: list[float] = []
        lh_values: list[float] = []
        for row in feature_rows:
            value = row.get("features", {}).get(feature)
            if not finite(value):
                continue
            if row["audit"]["hard_surface_pair"]:
                hard_values.append(float(value))
            else:
                non_hard_values.append(float(value))
            if row["audit"]["queue_kind"] == "HL":
                hl_values.append(float(value))
            elif row["audit"]["queue_kind"] == "LH":
                lh_values.append(float(value))
        hard_effect = standardized_effect(hard_values, non_hard_values)
        queue_effect = standardized_effect(hl_values, lh_values)
        rows.append(
            {
                "risk": "feature_hard_surface_shift",
                "feature": feature,
                "scope": "hard_vs_non_hard",
                "value": hard_effect,
                "severity": "high" if hard_effect is not None and abs(hard_effect) > 1.0 else "medium" if hard_effect is not None and abs(hard_effect) > 0.5 else "low",
                "mitigation": "report and cap hard-surface cells before target materialization",
            }
        )
        rows.append(
            {
                "risk": "feature_queue_shift",
                "feature": feature,
                "scope": "HL_vs_LH",
                "value": queue_effect,
                "severity": "high" if queue_effect is not None and abs(queue_effect) > 1.0 else "medium" if queue_effect is not None and abs(queue_effect) > 0.5 else "low",
                "mitigation": "do not use queue as label; report queue sensitivity only",
            }
        )
    return rows


def select_tier_b_sample(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    cell_counts: Counter[str] = Counter()
    scan_counts: Counter[str] = Counter()
    visible_counts: Counter[str] = Counter()

    def cell(row: dict[str, Any]) -> str:
        return f"{row.get('predicate_label')}|{hard_surface_pair(row)}|{row.get('geometry_status')}"

    def can_add(row: dict[str, Any], relaxed: bool = False) -> bool:
        if row.get("prediction_id") in selected_ids:
            return False
        if len(selected) >= TIER_B_TARGET_ROWS:
            return False
        if not relaxed and cell_counts[cell(row)] >= TIER_B_CELL_TARGET:
            return False
        if scan_counts[str(row.get("scan_id"))] >= TIER_B_SCAN_CAP:
            return False
        if visible_counts[visible_pair(row)] >= TIER_B_VISIBLE_PAIR_CAP:
            return False
        return True

    priority_rows = sorted(rows, key=lambda row: (hard_surface_pair(row), stable_hash(row)))
    for row in priority_rows:
        if can_add(row, relaxed=False):
            selected.append(row)
            selected_ids.add(str(row.get("prediction_id")))
            cell_counts[cell(row)] += 1
            scan_counts[str(row.get("scan_id"))] += 1
            visible_counts[visible_pair(row)] += 1
    for row in priority_rows:
        if can_add(row, relaxed=True):
            selected.append(row)
            selected_ids.add(str(row.get("prediction_id")))
            cell_counts[cell(row)] += 1
            scan_counts[str(row.get("scan_id"))] += 1
            visible_counts[visible_pair(row)] += 1
    return selected


def read_ply_points_for_objects(path: Path, object_ids: set[int]) -> dict[int, list[tuple[float, float, float]]]:
    points: dict[int, list[tuple[float, float, float]]] = {oid: [] for oid in object_ids}
    if not path.exists() or not object_ids:
        return points
    vertex_count = None
    properties: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        in_vertex_props = False
        for line in handle:
            line = line.strip()
            if line.startswith("element vertex "):
                vertex_count = int(line.split()[-1])
                in_vertex_props = True
                continue
            if line.startswith("element face "):
                in_vertex_props = False
                continue
            if in_vertex_props and line.startswith("property "):
                properties.append(line.split()[-1])
                continue
            if line == "end_header":
                break
        if vertex_count is None:
            return points
        try:
            x_idx = properties.index("x")
            y_idx = properties.index("y")
            z_idx = properties.index("z")
            object_idx = properties.index("objectId")
        except ValueError:
            return points
        for _ in range(vertex_count):
            raw = handle.readline()
            if not raw:
                break
            parts = raw.strip().split()
            if len(parts) <= max(x_idx, y_idx, z_idx, object_idx):
                continue
            try:
                oid = int(parts[object_idx])
            except ValueError:
                continue
            if oid not in object_ids:
                continue
            try:
                points[oid].append((float(parts[x_idx]), float(parts[y_idx]), float(parts[z_idx])))
            except ValueError:
                continue
    return points


def point_box(points: list[tuple[float, float, float]]) -> dict[str, Any] | None:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    mins = [min(xs), min(ys), min(zs)]
    maxs = [max(xs), max(ys), max(zs)]
    extents = [maxs[i] - mins[i] for i in range(3)]
    centroid = [sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)]
    return {
        "mins": mins,
        "maxs": maxs,
        "extents": extents,
        "centroid": centroid,
        "xy_area": max(extents[0], 0.0) * max(extents[1], 0.0),
    }


def fraction(points: list[tuple[float, float, float]], predicate: Any) -> float | None:
    if not points:
        return None
    return sum(1 for point in points if predicate(point)) / len(points)


def point_features(row: dict[str, Any], point_cache: dict[str, dict[int, list[tuple[float, float, float]]]]) -> dict[str, float | None]:
    scan_points = point_cache.get(str(row.get("scan_id")), {})
    subject_points = scan_points.get(int(row["subject_id"]), [])
    object_points = scan_points.get(int(row["object_id"]), [])
    subj_box = point_box(subject_points)
    obj_box = point_box(object_points)
    values: dict[str, float | None] = {feature: None for feature in TIER_B_FEATURES}
    values["point_subject_count"] = float(len(subject_points))
    values["point_object_count"] = float(len(object_points))
    if subj_box is None or obj_box is None:
        return values
    xy_min, xy_subj, xy_obj = box_xy_overlap(subj_box, obj_box)
    gap = subj_box["mins"][2] - obj_box["maxs"][2]
    dx = subj_box["centroid"][0] - obj_box["centroid"][0]
    dy = subj_box["centroid"][1] - obj_box["centroid"][1]
    subj_z_extent = max(subj_box["extents"][2], EPS)
    obj_z_extent = max(obj_box["extents"][2], EPS)
    subj_bottom_band = max(0.02, 0.10 * subj_z_extent)
    obj_top_band = max(0.02, 0.10 * obj_z_extent)
    contact_band = 0.05
    values.update(
        {
            "point_surface_gap_subject_bottom_to_object_top": gap,
            "point_abs_surface_gap": abs(gap),
            "point_xy_overlap_min_ratio": xy_min,
            "point_xy_overlap_subject_ratio": xy_subj,
            "point_xy_overlap_object_ratio": xy_obj,
            "point_subject_z_extent": subj_box["extents"][2],
            "point_object_z_extent": obj_box["extents"][2],
            "point_subject_vertical_extent_ratio": subj_box["extents"][2] / max(subj_box["extents"][0], subj_box["extents"][1], EPS),
            "point_object_vertical_extent_ratio": obj_box["extents"][2] / max(obj_box["extents"][0], obj_box["extents"][1], EPS),
            "point_subject_bottom_band_density": fraction(subject_points, lambda point: point[2] <= subj_box["mins"][2] + subj_bottom_band),
            "point_object_top_band_density": fraction(object_points, lambda point: point[2] >= obj_box["maxs"][2] - obj_top_band),
            "point_contact_candidate_ratio": fraction(
                subject_points,
                lambda point: (
                    obj_box["mins"][0] <= point[0] <= obj_box["maxs"][0]
                    and obj_box["mins"][1] <= point[1] <= obj_box["maxs"][1]
                    and abs(point[2] - obj_box["maxs"][2]) <= contact_band
                ),
            ),
            "point_center_distance_xy": math.sqrt(dx * dx + dy * dy),
        }
    )
    return values


def audit_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "predicate_label": row.get("predicate_label"),
        "queue_kind": row.get("queue_kind"),
        "geometry_status": row.get("geometry_status"),
        "hard_surface_pair": hard_surface_pair(row),
        "visible_pair": visible_pair(row),
        "scan_id": row.get("scan_id"),
        "p_geom_valid": row.get("p_geom_valid"),
        "consistency_score": row.get("consistency_score"),
        "disagreement_score": row.get("disagreement_score"),
        "underconfidence_score": row.get("underconfidence_score"),
    }


def feature_record(row: dict[str, Any], features: dict[str, Any], tier: str) -> dict[str, Any]:
    return {
        "feature_id": feature_id(row),
        "tier": tier,
        "features": features,
        "audit": audit_payload(row),
    }


def load_semseg_cache(rows: list[dict[str, Any]], root: Path) -> dict[str, dict[int, dict[str, Any]]]:
    cache: dict[str, dict[int, dict[str, Any]]] = {}
    for scan_id in sorted({str(row.get("scan_id")) for row in rows}):
        cache[scan_id] = read_semseg(root / scan_id / "semseg.v2.json")
    return cache


def build_point_cache(sample_rows: list[dict[str, Any]], root: Path) -> dict[str, dict[int, list[tuple[float, float, float]]]]:
    needed: dict[str, set[int]] = defaultdict(set)
    for row in sample_rows:
        needed[str(row.get("scan_id"))].add(int(row["subject_id"]))
        needed[str(row.get("scan_id"))].add(int(row["object_id"]))
    cache: dict[str, dict[int, list[tuple[float, float, float]]]] = {}
    for scan_id, object_ids in sorted(needed.items()):
        path = root / scan_id / "labels.instances.align.annotated.v2.ply"
        cache[scan_id] = read_ply_points_for_objects(path, object_ids)
    return cache


def model_safe_preview(records: list[dict[str, Any]], features: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records[:PREVIEW_LIMIT]:
        rows.append(
            {
                "feature_id": record["feature_id"],
                "tier": record["tier"],
                "G_e_mesh_pose_contact": {feature: record["features"].get(feature) for feature in features if feature in record["features"]},
            }
        )
    return rows


def audit_preview(records: list[dict[str, Any]], features: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records[:PREVIEW_LIMIT]:
        rows.append(
            {
                "feature_id": record["feature_id"],
                "tier": record["tier"],
                "audit": record["audit"],
                "feature_subset": {feature: record["features"].get(feature) for feature in features[:8] if feature in record["features"]},
            }
        )
    return rows


def model_safe_blocked_absent(rows: list[dict[str, Any]]) -> bool:
    serialized_keys: set[str] = set()

    def collect_keys(prefix: str, payload: Any) -> None:
        if isinstance(payload, dict):
            for key, value in payload.items():
                serialized_keys.add(key)
                collect_keys(f"{prefix}.{key}" if prefix else key, value)
        elif isinstance(payload, list):
            for value in payload:
                collect_keys(prefix, value)

    for row in rows:
        collect_keys("", row)
    return not any(key in serialized_keys for key in BLOCKED_MODEL_KEYS)


def feature_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_support_contact_mesh_pose_contact_features_v1",
        "model_safe_roots": ["feature_id", "tier", "G_e_mesh_pose_contact"],
        "blocked_model_inputs": sorted(BLOCKED_MODEL_KEYS),
        "tier_a_features": TIER_A_FEATURES,
        "tier_b_features": TIER_B_FEATURES,
        "audit_only_fields": [
            "predicate_label",
            "queue_kind",
            "geometry_status",
            "hard_surface_pair",
            "visible_pair",
            "scan_id",
            "p_geom_valid",
            "consistency_score",
            "disagreement_score",
            "underconfidence_score",
        ],
    }


def path_decision(
    errors: list[dict[str, Any]],
    derivability_rows: list[dict[str, Any]],
    old_rows: list[dict[str, Any]],
    model_safe_ok: bool,
    tier_b_records: list[dict[str, Any]],
) -> dict[str, Any]:
    if errors:
        return {
            "status": STATUS_ERRORS,
            "selected_path": "fix_inputs_before_feature_probe_runner",
            "next_todo": "fix_mesh_pose_contact_feature_probe_runner_inputs",
            "validation_errors": len(errors),
        }
    tier_a = [row for row in derivability_rows if row["tier"] == "A_full_rows"]
    tier_b = [row for row in derivability_rows if row["tier"] == "B_stratified_sample"]
    tier_a_derivable = all(float(row["non_missing_rate"]) >= 0.95 for row in tier_a)
    tier_a_finite = all(float(row["finite_rate"]) >= 0.99 for row in tier_a)
    tier_b_has_rows = len(tier_b_records) >= min(600, TIER_B_TARGET_ROWS)
    high_old_corr = [
        row
        for row in old_rows
        if row.get("dominance_risk") == "high" and row.get("feature") not in {"obb_contact_likelihood_proxy", "xy_overlap_min_ratio"}
    ]
    new_features_not_old_proxy = len(high_old_corr) < 5
    ready = tier_a_derivable and tier_a_finite and tier_b_has_rows and model_safe_ok and new_features_not_old_proxy
    return {
        "status": STATUS_READY if ready else STATUS_DIAGNOSTIC,
        "selected_path": SELECTED_PATH_READY if ready else "keep_feature_probe_diagnostic_until_feature_quality_fixed",
        "next_todo": NEXT_READY if ready else NEXT_DIAGNOSTIC,
        "validation_errors": 0,
        "feature_probe_result_review_allowed": ready,
        "candidate_materialization_allowed": False,
        "learned_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "tier_a_derivability_pass": tier_a_derivable,
        "tier_a_finite_pass": tier_a_finite,
        "tier_b_sample_pass": tier_b_has_rows,
        "model_safe_blocked_fields_absent": model_safe_ok,
        "new_features_not_old_proxy_pass": new_features_not_old_proxy,
        "high_old_numeric_correlations_excluding_contact_proxy": high_old_corr[:20],
        "rationale": (
            "Feature derivability and leakage controls passed; review the diagnostics before any materialization."
            if ready
            else "At least one feature-probe gate failed; keep as diagnostic until repaired."
        ),
    }


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    decision = summary["path_decision"]
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Mesh-Pose-Contact Feature Probe Runner",
            "",
            "## Status",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"next_todo = {summary['next_todo']}",
            f"validation_errors = {summary['validation_errors']}",
            "```",
            "",
            "## Counts",
            "",
            "```text",
            f"support_rows = {counts['support_rows']}",
            f"tier_a_records = {counts['tier_a_records']}",
            f"tier_b_records = {counts['tier_b_records']}",
            f"tier_b_distinct_scans = {counts['tier_b_distinct_scans']}",
            "```",
            "",
            "## Gate Summary",
            "",
            "```text",
            f"tier_a_derivability_pass = {decision.get('tier_a_derivability_pass')}",
            f"tier_a_finite_pass = {decision.get('tier_a_finite_pass')}",
            f"tier_b_sample_pass = {decision.get('tier_b_sample_pass')}",
            f"model_safe_blocked_fields_absent = {decision.get('model_safe_blocked_fields_absent')}",
            f"new_features_not_old_proxy_pass = {decision.get('new_features_not_old_proxy_pass')}",
            f"candidate_materialization_allowed = {decision.get('candidate_materialization_allowed')}",
            f"learned_smoke_allowed = {decision.get('learned_smoke_allowed')}",
            "```",
            "",
            "## Interpretation",
            "",
            "This runner derives geometry evidence candidates only. It does not build a target, train a",
            "model, or authorize support/contact learned smoke. The next step should review whether the",
            "new mesh/pose/contact evidence is strong and independent enough to justify a later",
            "shortcut-controlled materialization plan.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    source_summary = read_json(args.source_inventory_dir / "summary.json")
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    source_errors = read_jsonl(args.source_inventory_dir / "validation_errors.jsonl")
    errors = validate_inputs(plan_summary, source_summary, plan_errors, source_errors)

    support_rows, line_counts = scan_support_queues(args.rga_dir)
    semseg_cache = load_semseg_cache(support_rows, args.three_rscan_root)

    tier_a_records: list[dict[str, Any]] = []
    for row in support_rows:
        objects = semseg_cache.get(str(row.get("scan_id")), {})
        features = semseg_features(row, objects)
        tier_a_records.append(feature_record(row, features, "A_full_rows"))

    tier_b_source_rows = select_tier_b_sample(support_rows)
    point_cache = build_point_cache(tier_b_source_rows, args.three_rscan_root)
    tier_b_records: list[dict[str, Any]] = []
    for row in tier_b_source_rows:
        features = point_features(row, point_cache)
        tier_b_records.append(feature_record(row, features, "B_stratified_sample"))

    derivability_rows = collect_stats(tier_a_records, TIER_A_FEATURES, "A_full_rows") + collect_stats(
        tier_b_records, TIER_B_FEATURES, "B_stratified_sample"
    )
    distribution_rows: list[dict[str, Any]] = []
    distribution_rows.extend(group_stats(tier_a_records, TIER_A_FEATURES[:10], lambda row: row["audit"]["predicate_label"], "predicate_label", "A_full_rows"))
    distribution_rows.extend(group_stats(tier_a_records, TIER_A_FEATURES[:10], lambda row: row["audit"]["hard_surface_pair"], "hard_surface_pair", "A_full_rows"))
    distribution_rows.extend(group_stats(tier_a_records, TIER_A_FEATURES[:10], lambda row: row["audit"]["queue_kind"], "queue_kind", "A_full_rows"))
    distribution_rows.extend(group_stats(tier_b_records, TIER_B_FEATURES, lambda row: row["audit"]["predicate_label"], "predicate_label", "B_stratified_sample"))
    distribution_rows.extend(group_stats(tier_b_records, TIER_B_FEATURES, lambda row: row["audit"]["hard_surface_pair"], "hard_surface_pair", "B_stratified_sample"))
    distribution_rows.extend(group_stats(tier_b_records, TIER_B_FEATURES, lambda row: row["audit"]["queue_kind"], "queue_kind", "B_stratified_sample"))

    old_rows = old_numeric_diagnostics(tier_a_records, TIER_A_FEATURES)
    shortcut_rows = shortcut_risks(tier_a_records, TIER_A_FEATURES[:12])
    model_preview = model_safe_preview(tier_a_records + tier_b_records, TIER_A_FEATURES + TIER_B_FEATURES)
    audit_preview_rows = audit_preview(tier_a_records + tier_b_records, TIER_A_FEATURES + TIER_B_FEATURES)
    model_safe_ok = model_safe_blocked_absent(model_preview)
    decision = path_decision(errors, derivability_rows, old_rows, model_safe_ok, tier_b_records)

    counts = {
        "support_rows": len(support_rows),
        "tier_a_records": len(tier_a_records),
        "tier_b_records": len(tier_b_records),
        "tier_b_distinct_scans": len({row["audit"]["scan_id"] for row in tier_b_records}),
        "tier_b_hard_surface_rows": sum(1 for row in tier_b_records if row["audit"]["hard_surface_pair"]),
        "tier_b_non_hard_surface_rows": sum(1 for row in tier_b_records if not row["audit"]["hard_surface_pair"]),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": decision["status"],
        "selected_path": decision["selected_path"],
        "next_todo": decision["next_todo"],
        "validation_errors": len(errors),
        "plan_status": plan_summary.get("status"),
        "source_inventory_status": source_summary.get("status"),
        "line_counts": line_counts,
        "counts": counts,
        "path_decision": decision,
        "output_paths": {
            "feature_schema": rel_path(output_dir / "feature_schema.json"),
            "tier_a_semseg_feature_summary": rel_path(output_dir / "tier_a_semseg_feature_summary.csv"),
            "tier_b_ply_mesh_probe_summary": rel_path(output_dir / "tier_b_ply_mesh_probe_summary.csv"),
            "feature_derivability": rel_path(output_dir / "feature_derivability.csv"),
            "feature_distribution_diagnostics": rel_path(output_dir / "feature_distribution_diagnostics.csv"),
            "old_numeric_dominance_diagnostics": rel_path(output_dir / "old_numeric_dominance_diagnostics.csv"),
            "shortcut_risk_diagnostics": rel_path(output_dir / "shortcut_risk_diagnostics.csv"),
            "model_safe_feature_preview": rel_path(output_dir / "model_safe_feature_preview.jsonl"),
            "audit_feature_preview": rel_path(output_dir / "audit_feature_preview.jsonl"),
            "path_decision": rel_path(output_dir / "path_decision.json"),
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_feature_probe_runner",
            "validation_usage": False,
            "test_usage": False,
            "materializes_candidate_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "full_match_rows_scanned": False,
        },
    }

    tier_a_summary = [row for row in derivability_rows if row["tier"] == "A_full_rows"]
    tier_b_summary = [row for row in derivability_rows if row["tier"] == "B_stratified_sample"]
    write_json(output_dir / "feature_schema.json", feature_schema())
    write_csv(output_dir / "tier_a_semseg_feature_summary.csv", tier_a_summary)
    write_csv(output_dir / "tier_b_ply_mesh_probe_summary.csv", tier_b_summary)
    write_csv(output_dir / "feature_derivability.csv", derivability_rows)
    write_csv(output_dir / "feature_distribution_diagnostics.csv", distribution_rows)
    write_csv(output_dir / "old_numeric_dominance_diagnostics.csv", old_rows)
    write_csv(output_dir / "shortcut_risk_diagnostics.csv", shortcut_rows)
    write_jsonl(output_dir / "model_safe_feature_preview.jsonl", model_preview)
    write_jsonl(output_dir / "audit_feature_preview.jsonl", audit_preview_rows)
    write_json(output_dir / "path_decision.json", decision)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(report_text(summary), encoding="utf-8")

    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
