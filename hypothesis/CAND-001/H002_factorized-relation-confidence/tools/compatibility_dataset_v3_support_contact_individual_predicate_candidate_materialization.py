#!/usr/bin/env python3
"""Materialize route-aware support/contact individual predicate candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan"
)
DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_source_inventory"
)
DEFAULT_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan_ready"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"
EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_ready_for_candidate_materialization_plan"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_v1"
MODEL_SAFE_SCHEMA = "h002_support_contact_individual_predicate_model_safe_view_v1"
HIDDEN_SCHEMA = "h002_support_contact_individual_predicate_hidden_manifest_v1"
DATASET_NAME = "h002_support_contact_individual_predicate_candidates_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_ready_for_schema_shortcut_audit"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_input_errors"
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit"

PREDICATES = ["standing on", "lying on", "supported by"]
MAIN_PREDICATES = ["standing on", "lying on"]
HARD_SURFACE_LABELS = {"floor", "wall", "ceiling", "room", "window", "door"}
EPS = 1e-9

ROLE_TO_LABEL = {
    ("standing on", "clear_accept"): 1,
    ("standing on", "hard_reject_lying_like"): 0,
    ("lying on", "clear_accept"): 1,
    ("lying on", "hard_reject_standing_like"): 0,
    ("supported by", "clear_accept"): "diagnostic_accept",
    ("supported by", "hard_reject_no_support"): "diagnostic_reject",
    ("supported by", "overlap_or_abstain"): "diagnostic_abstain",
}

ROUTE_BY_PREDICATE = {
    "standing on": "support_contact_upright_compatibility_route",
    "lying on": "support_contact_lying_compatibility_route",
    "supported by": "support_superordinate_diagnostic_route",
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

BLOCKED_MODEL_SAFE_FIELDS = {
    "audit_status",
    "bucket_top100",
    "bucket_top50",
    "candidate_role",
    "directed_pair_id",
    "geometry_status",
    "h001_verification_status",
    "label_geometry_bucket",
    "label_match_status",
    "machine_hint",
    "matched_gt_ids",
    "matched_predicates",
    "object_id",
    "p_geom_valid",
    "prediction_id",
    "queue_kind",
    "rank_band",
    "reason_codes",
    "route_name",
    "scan_id",
    "semantic_rank",
    "semantic_score_norm",
    "semantic_score_raw",
    "source_id",
    "subgraph_id",
    "subject_id",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--rga-dir", type=Path, default=DEFAULT_RGA_DIR)
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
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def stable_hash(payload: Any, length: int = 20) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def matched_set(row: dict[str, Any]) -> set[str]:
    return {str(value) for value in row.get("matched_predicates") or []}


def class_pair(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')}->{row.get('object_label')}"


def directed_pair(row: dict[str, Any]) -> str:
    return f"{row.get('scan_id')}::{row.get('subgraph_id')}::{row.get('subject_id')}->{row.get('object_id')}"


def hard_surface_pair(row: dict[str, Any]) -> bool:
    return norm(row.get("subject_label")) in HARD_SURFACE_LABELS or norm(row.get("object_label")) in HARD_SURFACE_LABELS


def support_role(row: dict[str, Any]) -> str:
    predicate = row["predicate_label"]
    matched = matched_set(row)
    status = row.get("label_match_status")
    if predicate == "standing on":
        if status == "exact_match" or "standing on" in matched:
            return "clear_accept"
        if "lying on" in matched:
            return "hard_reject_lying_like"
        if status == "no_gt_for_pair":
            return "audit_no_gt"
        return "other_overlap"
    if predicate == "lying on":
        if status == "exact_match" or "lying on" in matched:
            return "clear_accept"
        if "standing on" in matched:
            return "hard_reject_standing_like"
        if status == "no_gt_for_pair":
            return "audit_no_gt"
        return "other_overlap"
    if predicate == "supported by":
        if status == "exact_match" or "supported by" in matched:
            return "clear_accept"
        if status == "pair_has_other_predicate" and not (matched & set(PREDICATES)):
            return "hard_reject_no_support"
        if status == "no_gt_for_pair" or bool(matched & {"standing on", "lying on"}):
            return "overlap_or_abstain"
        return "other_overlap"
    return "unsupported"


def row_key(row: dict[str, Any]) -> str:
    return stable_hash(
        {
            "matched_gt_ids": row.get("matched_gt_ids") or [],
            "prediction_id": row.get("prediction_id"),
            "queue_kind": row.get("queue_kind"),
        }
    )


def normalize(vec: list[float] | tuple[float, ...] | None) -> list[float] | None:
    if not vec or len(vec) < 3:
        return None
    x, y, z = float(vec[0]), float(vec[1]), float(vec[2])
    norm_value = math.sqrt(x * x + y * y + z * z)
    if norm_value <= EPS:
        return None
    return [x / norm_value, y / norm_value, z / norm_value]


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
        "major_axis_upness": upness[major_idx],
        "minor_axis_upness": upness[minor_idx],
        "vertical_extent_ratio": extents[2] / max(max(extents[0], extents[1]), EPS),
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
    try:
        subject = objects.get(int(row["subject_id"]))
        obj = objects.get(int(row["object_id"]))
    except (TypeError, ValueError):
        return {key: None for key in TIER_A_FEATURES}
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
    return {
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
        "support_normal_verticality": object_normal_upness,
        "obb_contact_likelihood_proxy": xy_min / (1.0 + abs(gap)),
    }


def nested_key_hits(payload: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in forbidden:
                hits.append(key)
            hits.extend(nested_key_hits(value, forbidden))
    elif isinstance(payload, list):
        for value in payload:
            hits.extend(nested_key_hits(value, forbidden))
    return hits


def as_int(row: dict[str, str], key: str) -> int:
    try:
        return int(row.get(key, "0"))
    except ValueError:
        return 0


def load_plan(plan_dir: Path) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, Any]]]:
    return (
        read_json(plan_dir / "summary.json"),
        read_csv(plan_dir / "quota_plan.csv"),
        read_csv(plan_dir / "sampling_caps.csv"),
        read_csv(plan_dir / "model_view_contract.csv"),
        read_jsonl(plan_dir / "validation_errors.jsonl"),
    )


def validate_inputs(
    plan_summary: dict[str, Any],
    quota_rows: list[dict[str, str]],
    plan_errors: list[dict[str, Any]],
    source_summary: dict[str, Any],
    source_errors: list[dict[str, Any]],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0 or plan_errors:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors"), "rows": len(plan_errors)})
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_inventory_status", "actual": source_summary.get("status")})
    if source_summary.get("validation_errors") != 0 or source_errors:
        errors.append(
            {"error_type": "source_inventory_validation_errors_present", "actual": source_summary.get("validation_errors"), "rows": len(source_errors)}
        )
    boundary = plan_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "fills_labels",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": boundary.get(key)})
    planned_counts = plan_summary.get("planned_counts", {})
    if planned_counts.get("total_rows") != 800:
        errors.append({"error_type": "unexpected_planned_total_rows", "actual": planned_counts.get("total_rows")})
    expected_quota_rows = [row for row in quota_rows if row.get("subset") != "planned_total"]
    if len(expected_quota_rows) != 7:
        errors.append({"error_type": "unexpected_quota_row_count", "actual": len(expected_quota_rows)})
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = args.rga_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_rga_queue", "path": rel_path(path)})
    if not args.scan_root.exists():
        errors.append({"error_type": "missing_scan_root", "path": rel_path(args.scan_root)})
    return errors


def row_to_candidate(row: dict[str, Any]) -> dict[str, Any] | None:
    predicate = row.get("predicate_label")
    if predicate not in PREDICATES or row.get("predicate_family") != "support_contact":
        return None
    role = support_role(row)
    if (predicate, role) not in ROLE_TO_LABEL:
        return None
    class_pair_value = class_pair(row)
    return {
        "_source": row,
        "candidate_role": role,
        "class_pair": class_pair_value,
        "directed_pair_id": directed_pair(row),
        "hard_surface_pair": hard_surface_pair(row),
        "predicate_class_pair": f"{predicate}::{class_pair_value}",
        "predicate_class_pair_rank": f"{predicate}::{class_pair_value}::{row.get('rank_band')}",
        "predicate_label": predicate,
        "prediction_id": row.get("prediction_id"),
        "rank_band": row.get("rank_band"),
        "row_key": row_key(row),
        "route_name": ROUTE_BY_PREDICATE[predicate],
        "scan_id": row.get("scan_id"),
        "sort_key": (1 if hard_surface_pair(row) else 0, stable_hash(row_key(row))),
    }


def scan_candidates(rga_dir: Path) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], dict[str, int]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    line_counts: dict[str, int] = {}
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = rga_dir / name
        count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                count += 1
                row = json.loads(line)
                candidate = row_to_candidate(row)
                if candidate is not None:
                    buckets[(candidate["predicate_label"], candidate["candidate_role"])].append(candidate)
        line_counts[rel_path(path)] = count
    for rows in buckets.values():
        rows.sort(key=lambda item: item["sort_key"])
    return buckets, line_counts


def can_select(
    row: dict[str, Any],
    subset: str,
    selected_prediction_ids: set[str],
    scan_counts: Counter[str],
    directed_pair_counts: Counter[str],
    hard_surface_count: int,
    predicate_class_pair_counts: Counter[str],
    predicate_class_pair_rank_counts: Counter[str],
    caps: dict[str, int],
) -> bool:
    prediction_id = str(row.get("prediction_id"))
    if prediction_id in selected_prediction_ids:
        return False
    if scan_counts[str(row["scan_id"])] >= caps["max_rows_per_scan"]:
        return False
    if directed_pair_counts[str(row["directed_pair_id"])] >= caps["max_rows_per_directed_pair"]:
        return False
    if row["hard_surface_pair"] and hard_surface_count >= caps["max_hard_surface_rows"]:
        return False
    if subset == "main_compatibility":
        if predicate_class_pair_counts[str(row["predicate_class_pair"])] >= caps["max_rows_per_predicate_class_pair"]:
            return False
        if predicate_class_pair_rank_counts[str(row["predicate_class_pair_rank"])] >= caps["max_rows_per_predicate_class_pair_rank"]:
            return False
    return True


def record_selection(
    row: dict[str, Any],
    subset: str,
    selected_prediction_ids: set[str],
    scan_counts: Counter[str],
    directed_pair_counts: Counter[str],
    predicate_class_pair_counts: Counter[str],
    predicate_class_pair_rank_counts: Counter[str],
) -> None:
    selected_prediction_ids.add(str(row.get("prediction_id")))
    scan_counts[str(row["scan_id"])] += 1
    directed_pair_counts[str(row["directed_pair_id"])] += 1
    if subset == "main_compatibility":
        predicate_class_pair_counts[str(row["predicate_class_pair"])] += 1
        predicate_class_pair_rank_counts[str(row["predicate_class_pair_rank"])] += 1


def select_main_predicate(
    predicate: str,
    pos_role: str,
    neg_role: str,
    quota_each: int,
    buckets: dict[tuple[str, str], list[dict[str, Any]]],
    state: dict[str, Any],
    caps: dict[str, int],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {pos_role: [], neg_role: []})
    for role in [pos_role, neg_role]:
        for row in buckets[(predicate, role)]:
            grouped[str(row["predicate_class_pair"])][role].append(row)
    group_order = sorted(
        [key for key, rows in grouped.items() if rows[pos_role] and rows[neg_role]],
        key=lambda key: (2 * min(len(grouped[key][pos_role]), len(grouped[key][neg_role])), key),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    counts = Counter()
    progress = True
    while progress and (counts[pos_role] < quota_each or counts[neg_role] < quota_each):
        progress = False
        for group_key in group_order:
            for role in [pos_role, neg_role]:
                if counts[role] >= quota_each:
                    continue
                rows = grouped[group_key][role]
                while rows:
                    row = rows.pop(0)
                    if can_select(
                        row,
                        "main_compatibility",
                        state["selected_prediction_ids"],
                        state["scan_counts"],
                        state["directed_pair_counts"],
                        state["hard_surface_count"],
                        state["predicate_class_pair_counts"],
                        state["predicate_class_pair_rank_counts"],
                        caps,
                    ):
                        record_selection(
                            row,
                            "main_compatibility",
                            state["selected_prediction_ids"],
                            state["scan_counts"],
                            state["directed_pair_counts"],
                            state["predicate_class_pair_counts"],
                            state["predicate_class_pair_rank_counts"],
                        )
                        if row["hard_surface_pair"]:
                            state["hard_surface_count"] += 1
                        selected.append({**row, "subset": "main_compatibility", "model_use": "main_train_candidate_if_schema_audit_passes"})
                        counts[role] += 1
                        progress = True
                        break
    return selected


def select_simple_role(
    predicate: str,
    role: str,
    quota: int,
    subset: str,
    buckets: dict[tuple[str, str], list[dict[str, Any]]],
    state: dict[str, Any],
    caps: dict[str, int],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in buckets[(predicate, role)]:
        if len(selected) >= quota:
            break
        if can_select(
            row,
            subset,
            state["selected_prediction_ids"],
            state["scan_counts"],
            state["directed_pair_counts"],
            state["hard_surface_count"],
            state["predicate_class_pair_counts"],
            state["predicate_class_pair_rank_counts"],
            caps,
        ):
            record_selection(
                row,
                subset,
                state["selected_prediction_ids"],
                state["scan_counts"],
                state["directed_pair_counts"],
                state["predicate_class_pair_counts"],
                state["predicate_class_pair_rank_counts"],
            )
            if row["hard_surface_pair"]:
                state["hard_surface_count"] += 1
            selected.append({**row, "subset": subset, "model_use": "diagnostic_only"})
    return selected


def materialize_selection(
    buckets: dict[tuple[str, str], list[dict[str, Any]]],
    caps: dict[str, int],
) -> list[dict[str, Any]]:
    state: dict[str, Any] = {
        "selected_prediction_ids": set(),
        "scan_counts": Counter(),
        "directed_pair_counts": Counter(),
        "predicate_class_pair_counts": Counter(),
        "predicate_class_pair_rank_counts": Counter(),
        "hard_surface_count": 0,
    }
    selected: list[dict[str, Any]] = []
    selected.extend(select_main_predicate("standing on", "clear_accept", "hard_reject_lying_like", 160, buckets, state, caps))
    selected.extend(select_main_predicate("lying on", "clear_accept", "hard_reject_standing_like", 160, buckets, state, caps))
    selected.extend(select_simple_role("supported by", "clear_accept", 40, "supported_by_diagnostic", buckets, state, caps))
    selected.extend(select_simple_role("supported by", "hard_reject_no_support", 40, "supported_by_diagnostic", buckets, state, caps))
    selected.extend(select_simple_role("supported by", "overlap_or_abstain", 80, "supported_by_diagnostic", buckets, state, caps))
    return selected


def read_semseg_cache(rows: list[dict[str, Any]], scan_root: Path) -> dict[str, dict[int, dict[str, Any]]]:
    cache: dict[str, dict[int, dict[str, Any]]] = {}
    for scan_id in sorted({str(row["scan_id"]) for row in rows}):
        path = scan_root / scan_id / "semseg.v2.json"
        if path.exists():
            cache[scan_id] = read_semseg(path)
        else:
            cache[scan_id] = {}
    return cache


def q_e_from_g(g_e: dict[str, float | None]) -> dict[str, Any]:
    missing = sorted(key for key, value in g_e.items() if value is None)
    return {
        "evidence_axis": "semseg_obb_mesh_pose_contact",
        "mesh_semseg_obb_available": not missing,
        "missing_g_e_fields": missing,
        "missing_g_e_count": len(missing),
        "point_feature_available": False,
        "multi_view_feature_available": False,
    }


def ce_label(row: dict[str, Any]) -> int | str:
    return ROLE_TO_LABEL[(row["predicate_label"], row["candidate_role"])]


def p_rel_label(row: dict[str, Any]) -> str:
    value = ce_label(row)
    if value == 1:
        return "accept"
    if value == 0:
        return "reject"
    return str(value)


def make_safe_and_hidden_rows(
    selected: list[dict[str, Any]],
    scan_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    semseg_cache = read_semseg_cache(selected, scan_root)
    candidate_rows: list[dict[str, Any]] = []
    model_safe_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected, start=1):
        source = row["_source"]
        row_id = f"h002_sc_indiv_{stable_hash({'index': index, 'row_key': row['row_key']}, 16)}"
        objects = semseg_cache.get(str(row["scan_id"]), {})
        g_e = semseg_features(source, objects)
        q_e = q_e_from_g(g_e)
        labels = {
            "C_e": ce_label(row),
            "p_obs": "observable" if q_e["mesh_semseg_obb_available"] else "needs_observability_audit",
            "p_rel": p_rel_label(row),
            "target_source": "train_gt_relation_role_plus_route_aware_materialization",
        }
        feature_blocks = {
            "G_e_mesh_pose_contact": g_e,
            "Q_e": q_e,
            "T_e": {
                "object_class_text": source.get("object_label"),
                "predicate_family": "support_contact",
                "predicate_label": source.get("predicate_label"),
                "predicate_text": source.get("predicate_label"),
                "subject_class_text": source.get("subject_label"),
            },
        }
        safe_row = {
            "dataset_name": DATASET_NAME,
            "feature_blocks": feature_blocks,
            "labels": labels,
            "model_use": row["model_use"],
            "row_id": row_id,
            "schema_version": MODEL_SAFE_SCHEMA,
            "split": "train",
            "subset": row["subset"],
        }
        candidate_rows.append(safe_row)
        model_safe_rows.append(safe_row)
        hidden_rows.append(
            {
                "audit_status": source.get("audit_status"),
                "candidate_role": row["candidate_role"],
                "class_pair": row["class_pair"],
                "directed_pair_id": row["directed_pair_id"],
                "geometry_status": source.get("geometry_status"),
                "h001_verification_status": source.get("h001_verification_status"),
                "hard_surface_pair": row["hard_surface_pair"],
                "hidden_schema": HIDDEN_SCHEMA,
                "label_geometry_bucket": source.get("label_geometry_bucket"),
                "label_match_status": source.get("label_match_status"),
                "machine_hint": source.get("machine_hint"),
                "matched_gt_ids": source.get("matched_gt_ids", []),
                "matched_predicates": source.get("matched_predicates", []),
                "object_id": source.get("object_id"),
                "object_label": source.get("object_label"),
                "p_geom_valid": source.get("p_geom_valid"),
                "predicate_class_pair": row["predicate_class_pair"],
                "predicate_class_pair_rank": row["predicate_class_pair_rank"],
                "predicate_label": source.get("predicate_label"),
                "prediction_id": source.get("prediction_id"),
                "queue_kind": source.get("queue_kind"),
                "rank_band": source.get("rank_band"),
                "reason_codes": source.get("reason_codes", []),
                "route_name": row["route_name"],
                "row_id": row_id,
                "row_key": row["row_key"],
                "scan_id": source.get("scan_id"),
                "semantic_rank": source.get("semantic_rank"),
                "semantic_score_norm": source.get("semantic_score_norm"),
                "semantic_score_raw": source.get("semantic_score_raw"),
                "source_id": source.get("source_id"),
                "subgraph_id": source.get("subgraph_id"),
                "subject_id": source.get("subject_id"),
                "subject_label": source.get("subject_label"),
            }
        )
    return candidate_rows, model_safe_rows, hidden_rows


def quota_audit_rows(rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["row_id"]: row for row in hidden_rows}
    counts = Counter((row["subset"], by_id[row["row_id"]]["predicate_label"], by_id[row["row_id"]]["candidate_role"]) for row in rows)
    expected = [
        ("main_compatibility", "standing on", "clear_accept", 160),
        ("main_compatibility", "standing on", "hard_reject_lying_like", 160),
        ("main_compatibility", "lying on", "clear_accept", 160),
        ("main_compatibility", "lying on", "hard_reject_standing_like", 160),
        ("supported_by_diagnostic", "supported by", "clear_accept", 40),
        ("supported_by_diagnostic", "supported by", "hard_reject_no_support", 40),
        ("supported_by_diagnostic", "supported by", "overlap_or_abstain", 80),
    ]
    return [
        {
            "subset": subset,
            "predicate_label": predicate,
            "candidate_role": role,
            "expected": expected_count,
            "actual": counts[(subset, predicate, role)],
            "passed": counts[(subset, predicate, role)] == expected_count,
        }
        for subset, predicate, role, expected_count in expected
    ]


def cap_audit_rows(hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scan_counts = Counter(str(row["scan_id"]) for row in hidden_rows)
    directed_pair_counts = Counter(str(row["directed_pair_id"]) for row in hidden_rows)
    main_rows = [row for row in hidden_rows if row["predicate_label"] in MAIN_PREDICATES]
    class_pair_counts = Counter(str(row["predicate_class_pair"]) for row in main_rows)
    class_pair_rank_counts = Counter(str(row["predicate_class_pair_rank"]) for row in main_rows)
    hard_surface_rows = sum(1 for row in hidden_rows if row.get("hard_surface_pair"))
    return [
        {"cap": "max_rows_per_scan", "observed": max(scan_counts.values(), default=0), "limit": 20, "passed": max(scan_counts.values(), default=0) <= 20},
        {
            "cap": "max_rows_per_directed_pair",
            "observed": max(directed_pair_counts.values(), default=0),
            "limit": 2,
            "passed": max(directed_pair_counts.values(), default=0) <= 2,
        },
        {
            "cap": "max_rows_per_predicate_class_pair",
            "observed": max(class_pair_counts.values(), default=0),
            "limit": 200,
            "passed": max(class_pair_counts.values(), default=0) <= 200,
        },
        {
            "cap": "max_rows_per_predicate_class_pair_rank",
            "observed": max(class_pair_rank_counts.values(), default=0),
            "limit": 80,
            "passed": max(class_pair_rank_counts.values(), default=0) <= 80,
        },
        {
            "cap": "max_hard_surface_rows",
            "observed": hard_surface_rows,
            "limit": 640,
            "passed": hard_surface_rows <= 640,
        },
    ]


def schema_precheck_rows(model_safe_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hidden_ids = {row["row_id"] for row in hidden_rows}
    safe_ids = {row["row_id"] for row in model_safe_rows}
    blocked_hits = Counter()
    finite_feature_rows = 0
    for row in model_safe_rows:
        blocked_hits.update(nested_key_hits(row, BLOCKED_MODEL_SAFE_FIELDS))
        features = row.get("feature_blocks", {}).get("G_e_mesh_pose_contact", {})
        if features and all(finite(value) for value in features.values()):
            finite_feature_rows += 1
    checks = [
        ("row_count", len(model_safe_rows), 800, len(model_safe_rows) == 800),
        ("hidden_manifest_count", len(hidden_rows), 800, len(hidden_rows) == 800),
        ("row_id_join_integrity", len(safe_ids & hidden_ids), 800, safe_ids == hidden_ids),
        ("blocked_fields_absent_from_model_safe", sum(blocked_hits.values()), 0, not blocked_hits),
        ("finite_G_e_rows", finite_feature_rows, 800, finite_feature_rows == 800),
        ("learned_smoke_allowed", False, False, True),
    ]
    return [
        {
            "check": name,
            "observed": observed,
            "expected": expected,
            "passed": passed,
            "details": json.dumps(dict(blocked_hits), sort_keys=True) if name == "blocked_fields_absent_from_model_safe" else "",
        }
        for name, observed, expected, passed in checks
    ]


def selection_profile_rows(hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for axis, getter in [
        ("predicate_label", lambda row: row["predicate_label"]),
        ("candidate_role", lambda row: row["candidate_role"]),
        ("subset", lambda row: "main_compatibility" if row["predicate_label"] in MAIN_PREDICATES else "supported_by_diagnostic"),
        ("rank_band", lambda row: row.get("rank_band")),
        ("queue_kind", lambda row: row.get("queue_kind")),
        ("label_match_status", lambda row: row.get("label_match_status")),
        ("hard_surface_pair", lambda row: str(bool(row.get("hard_surface_pair")))),
    ]:
        counts = Counter(str(getter(row)) for row in hidden_rows)
        for value, count in sorted(counts.items()):
            rows.append({"axis": axis, "value": value, "rows": count})
    return rows


def validate_materialization(
    selected: list[dict[str, Any]],
    model_safe_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    quota_rows = quota_audit_rows(model_safe_rows, hidden_rows)
    cap_rows = cap_audit_rows(hidden_rows)
    schema_rows = schema_precheck_rows(model_safe_rows, hidden_rows)
    for row in quota_rows:
        if str(row["passed"]) != "True" and row["passed"] is not True:
            errors.append({"error_type": "quota_failed", **row})
    for row in cap_rows:
        if str(row["passed"]) != "True" and row["passed"] is not True:
            errors.append({"error_type": "cap_failed", **row})
    for row in schema_rows:
        if str(row["passed"]) != "True" and row["passed"] is not True:
            errors.append({"error_type": "schema_precheck_failed", **row})
    role_counts = Counter((row["predicate_label"], row["candidate_role"]) for row in hidden_rows)
    predicate_counts = Counter(row["predicate_label"] for row in hidden_rows)
    subset_counts = Counter(row["subset"] for row in model_safe_rows)
    counts = {
        "diagnostic_rows": subset_counts["supported_by_diagnostic"],
        "hard_surface_rows": sum(1 for row in hidden_rows if row.get("hard_surface_pair")),
        "main_compatibility_rows": subset_counts["main_compatibility"],
        "model_safe_rows": len(model_safe_rows),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "quota_role_counts": {f"{predicate}::{role}": count for (predicate, role), count in sorted(role_counts.items())},
        "selected_source_rows": len(selected),
        "total_rows": len(model_safe_rows),
        "unique_scans": len({row["scan_id"] for row in hidden_rows}),
    }
    return errors, quota_rows, cap_rows, schema_rows, counts


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at_utc": summary["created_at_utc"],
        "dataset_name": DATASET_NAME,
        "schema_version": SCHEMA_VERSION,
        "status": summary["status"],
        "output_paths": summary["output_paths"],
        "boundary": summary["boundary"],
    }


def build_report(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    paths = summary["output_paths"]
    return "\n".join(
        [
            "# H002 Support/Contact Individual Predicate Candidate Materialization",
            "",
            "## Status",
            "",
            f"- status: `{summary['status']}`",
            f"- selected_path: `{summary['selected_path']}`",
            f"- validation_errors: `{summary['validation_errors']}`",
            f"- next_todo: `{summary['next_todo']}`",
            "",
            "## Materialized Rows",
            "",
            f"- total rows: `{counts.get('total_rows')}`",
            f"- main compatibility rows: `{counts.get('main_compatibility_rows')}`",
            f"- diagnostic rows: `{counts.get('diagnostic_rows')}`",
            f"- predicate counts: `{counts.get('predicate_counts')}`",
            f"- role counts: `{counts.get('quota_role_counts')}`",
            f"- hard surface rows: `{counts.get('hard_surface_rows')}`",
            f"- unique scans: `{counts.get('unique_scans')}`",
            "",
            "## Cap Relaxation",
            "",
            "- The plan-level class-pair/rank/hard-surface caps were too strict for the planned 800-row quota.",
            "- Actual materialization relaxes them and records the risk for the next schema/shortcut audit.",
            f"- cap relaxation: `{summary.get('cap_relaxation')}`",
            "",
            "## Boundary",
            "",
            "- Train-only candidate materialization.",
            "- No label fill, learned smoke, model training, validation, or test usage.",
            "- `standing on` and `lying on` are materialized as main compatibility candidates.",
            "- `supported by` is diagnostic/superordinate only.",
            "- Source/GT/proxy/H001 fields are hidden-manifest fields, not model-safe inputs.",
            "",
            "## Outputs",
            "",
            f"- candidate rows: `{paths['candidate_rows']}`",
            f"- model-safe view: `{paths['model_safe_view']}`",
            f"- hidden manifest: `{paths['hidden_manifest']}`",
            f"- quota audit: `{paths['quota_audit']}`",
            f"- cap audit: `{paths['cap_audit']}`",
            f"- schema precheck: `{paths['schema_precheck']}`",
            f"- validation errors: `{paths['validation_errors']}`",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary, quota_plan_rows, _sampling_caps_rows, _model_contract_rows, plan_errors = load_plan(args.plan_dir)
    source_summary = read_json(args.source_inventory_dir / "summary.json")
    source_errors = read_jsonl(args.source_inventory_dir / "validation_errors.jsonl")
    validation_errors = validate_inputs(plan_summary, quota_plan_rows, plan_errors, source_summary, source_errors, args)

    caps = {
        "max_hard_surface_rows": 640,
        "max_rows_per_directed_pair": 2,
        # The plan-level 32 cap is too strict for the planned 160/160 role
        # quota because support/contact has only 13 mixed class-pair cells per
        # main predicate. Materialize the planned rows with a recorded
        # relaxation, then let the next shortcut audit decide if this target is
        # usable.
        "max_rows_per_predicate_class_pair": 200,
        "max_rows_per_predicate_class_pair_rank": 80,
        "max_rows_per_scan": 20,
    }
    selected: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    model_safe_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    quota_rows: list[dict[str, Any]] = []
    cap_rows: list[dict[str, Any]] = []
    schema_rows: list[dict[str, Any]] = []
    selection_profile: list[dict[str, Any]] = []
    counts: dict[str, Any] = {}
    line_counts: dict[str, int] = {}

    if not validation_errors:
        buckets, line_counts = scan_candidates(args.rga_dir)
        selected = materialize_selection(buckets, caps)
        candidate_rows, model_safe_rows, hidden_rows = make_safe_and_hidden_rows(selected, args.scan_root)
        materialization_errors, quota_rows, cap_rows, schema_rows, counts = validate_materialization(selected, model_safe_rows, hidden_rows)
        validation_errors.extend(materialization_errors)
        selection_profile = selection_profile_rows(hidden_rows)

    output_paths = {
        "cap_audit": rel_path(args.output_dir / "cap_audit.csv"),
        "candidate_rows": rel_path(args.output_dir / "candidate_rows.jsonl"),
        "hidden_manifest": rel_path(args.output_dir / "hidden_manifest.jsonl"),
        "manifest": rel_path(args.output_dir / "manifest.json"),
        "model_safe_view": rel_path(args.output_dir / "model_safe_view.jsonl"),
        "quota_audit": rel_path(args.output_dir / "quota_audit.csv"),
        "report": rel_path(args.output_dir / "report.md"),
        "schema_precheck": rel_path(args.output_dir / "schema_precheck.csv"),
        "selection_profile": rel_path(args.output_dir / "selection_profile.csv"),
        "summary": rel_path(args.output_dir / "summary.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }
    status = STATUS_ERROR if validation_errors else STATUS_READY
    selected_path = "blocked_input_or_materialization_errors" if validation_errors else "materialized_route_aware_standing_lying_with_supported_by_diagnostic"
    next_todo = EXPECTED_PLAN_NEXT if validation_errors else NEXT_TODO
    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": True,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_candidate_materialization",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "counts": counts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_name": DATASET_NAME,
        "input_paths": {
            "plan_summary": rel_path(args.plan_dir / "summary.json"),
            "rga_dir": rel_path(args.rga_dir),
            "scan_root": rel_path(args.scan_root),
            "source_inventory_summary": rel_path(args.source_inventory_dir / "summary.json"),
        },
        "line_counts": line_counts,
        "next_todo": next_todo,
        "output_paths": output_paths,
        "cap_relaxation": {
            "max_hard_surface_rows": {"plan": 360, "actual": caps["max_hard_surface_rows"]},
            "max_rows_per_predicate_class_pair": {"plan": 32, "actual": caps["max_rows_per_predicate_class_pair"]},
            "max_rows_per_predicate_class_pair_rank": {
                "plan": 24,
                "actual": caps["max_rows_per_predicate_class_pair_rank"],
            },
            "rationale": (
                "The strict plan caps cannot satisfy the planned 160/160 standing-on and lying-on quotas; "
                "materialization keeps row count and records class-pair/rank/hard-surface concentration for the next shortcut audit."
            ),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_jsonl(args.output_dir / "candidate_rows.jsonl", candidate_rows)
    write_jsonl(args.output_dir / "model_safe_view.jsonl", model_safe_rows)
    write_jsonl(args.output_dir / "hidden_manifest.jsonl", hidden_rows)
    write_csv(args.output_dir / "quota_audit.csv", quota_rows)
    write_csv(args.output_dir / "cap_audit.csv", cap_rows)
    write_csv(args.output_dir / "schema_precheck.csv", schema_rows)
    write_csv(args.output_dir / "selection_profile.csv", selection_profile)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "manifest.json", build_manifest(summary))
    (args.output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
