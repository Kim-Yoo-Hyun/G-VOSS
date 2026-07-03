#!/usr/bin/env python3
"""Materialize richer official-validation support/contact hard-route features."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_support_contact_harder_route_materialization_v1"
EXPECTED_PLAN_STATUS = "h002_support_contact_harder_route_materialization_plan_after_source_inventory_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan"
EXPECTED_SOURCE_SCHEMA = "h002_official_candidate_materialization_v1"

MAIN_PREDICATES = {"standing on", "lying on"}
FAMILY = "support_contact"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--plan-dir",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory"
        ),
    )
    parser.add_argument(
        "--official-materialization-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/official_materialization/latest"),
    )
    parser.add_argument("--scan-dir", type=Path, default=Path("local_dataset/3RScan/scans"))
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def vec3(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    return [safe_float(value[0]), safe_float(value[1]), safe_float(value[2])]


def dot(a: list[float] | None, b: list[float] | None) -> float:
    if a is None or b is None:
        return 0.0
    return sum(a[i] * b[i] for i in range(3))


def norm(a: list[float] | None) -> float:
    if a is None:
        return 0.0
    return math.sqrt(max(dot(a, a), 0.0))


def normalized(a: list[float] | None) -> list[float] | None:
    n = norm(a)
    if n <= 1e-9 or a is None:
        return None
    return [a[i] / n for i in range(3)]


def obb_record(group: dict[str, Any]) -> dict[str, Any] | None:
    obb = group.get("obb")
    if not isinstance(obb, dict):
        return None
    centroid = vec3(obb.get("centroid"))
    lengths = vec3(obb.get("axesLengths"))
    if centroid is None or lengths is None:
        return None
    axes_raw = obb.get("normalizedAxes")
    if isinstance(axes_raw, list) and len(axes_raw) >= 9:
        axes = [
            normalized([safe_float(axes_raw[0]), safe_float(axes_raw[1]), safe_float(axes_raw[2])]) or [1.0, 0.0, 0.0],
            normalized([safe_float(axes_raw[3]), safe_float(axes_raw[4]), safe_float(axes_raw[5])]) or [0.0, 1.0, 0.0],
            normalized([safe_float(axes_raw[6]), safe_float(axes_raw[7]), safe_float(axes_raw[8])]) or [0.0, 0.0, 1.0],
        ]
    else:
        axes = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    half_extents = [
        sum(abs(axes[axis_index][coord]) * max(lengths[axis_index], 1e-9) / 2.0 for axis_index in range(3))
        for coord in range(3)
    ]
    mins = [centroid[i] - half_extents[i] for i in range(3)]
    maxs = [centroid[i] + half_extents[i] for i in range(3)]
    length_order = sorted(range(3), key=lambda i: lengths[i])
    z_axis = [0.0, 0.0, 1.0]
    dominant_normal = normalized(vec3(group.get("dominantNormal")))
    return {
        "centroid": centroid,
        "axes_lengths": lengths,
        "normalized_axes": axes,
        "aabb_min": mins,
        "aabb_max": maxs,
        "volume": max(lengths[0] * lengths[1] * lengths[2], 1e-9),
        "label": group.get("label"),
        "segment_count": len(group.get("segments") or []),
        "dominant_normal": dominant_normal,
        "dominant_normal_upness": abs(dot(dominant_normal, z_axis)) if dominant_normal else 0.0,
        "principal_axis_upness": abs(dot(axes[length_order[-1]], z_axis)),
        "minor_axis_upness": abs(dot(axes[length_order[0]], z_axis)),
    }


def semseg_object_map(scan_dir: Path, scan_id: str) -> dict[int, dict[str, Any]]:
    path = scan_dir / scan_id / "semseg.v2.json"
    payload = read_json(path)
    objects: dict[int, dict[str, Any]] = {}
    for group in payload.get("segGroups", []):
        object_id = group.get("objectId", group.get("id"))
        if object_id is None:
            continue
        record = obb_record(group)
        if record is not None:
            objects[int(object_id)] = record
    return objects


def parse_interest_points(scan_dir: Path, scan_id: str, interest_ids: set[int]) -> dict[int, list[tuple[float, float, float]]]:
    path = scan_dir / scan_id / "labels.instances.align.annotated.v2.ply"
    points: dict[int, list[tuple[float, float, float]]] = {object_id: [] for object_id in interest_ids}
    if not path.exists():
        return points
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        vertex_count = 0
        properties: list[str] = []
        in_vertex = False
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("element vertex"):
                vertex_count = int(stripped.split()[-1])
                in_vertex = True
                continue
            if stripped.startswith("element ") and not stripped.startswith("element vertex"):
                in_vertex = False
            if in_vertex and stripped.startswith("property"):
                properties.append(stripped.split()[-1])
            if stripped == "end_header":
                break
        try:
            x_i = properties.index("x")
            y_i = properties.index("y")
            z_i = properties.index("z")
            object_i = properties.index("objectId")
        except ValueError:
            return points
        for _ in range(vertex_count):
            line = handle.readline()
            if not line:
                break
            parts = line.split()
            if len(parts) <= object_i:
                continue
            try:
                object_id = int(parts[object_i])
            except ValueError:
                continue
            if object_id not in interest_ids:
                continue
            points[object_id].append((float(parts[x_i]), float(parts[y_i]), float(parts[z_i])))
    return points


def interval_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def object_shape_features(record: dict[str, Any], prefix: str) -> dict[str, float]:
    x0, y0, z0 = record["aabb_min"]
    x1, y1, z1 = record["aabb_max"]
    width = max(x1 - x0, 1e-9)
    depth = max(y1 - y0, 1e-9)
    height = max(z1 - z0, 1e-9)
    max_extent = max(width, depth, height, 1e-9)
    min_extent = max(min(width, depth, height), 1e-9)
    return {
        f"{prefix}_height": height,
        f"{prefix}_footprint_area": max(width * depth, 1e-9),
        f"{prefix}_vertical_extent_ratio": height / max_extent,
        f"{prefix}_horizontal_extent_ratio": max(width, depth) / max(height, 1e-9),
        f"{prefix}_flatness_ratio": min_extent / max_extent,
        f"{prefix}_principal_axis_upness": record.get("principal_axis_upness", 0.0),
        f"{prefix}_minor_axis_upness": record.get("minor_axis_upness", 0.0),
        f"{prefix}_normal_upness": record.get("dominant_normal_upness", 0.0),
    }


def contact_point_features(
    subject: dict[str, Any],
    obj: dict[str, Any],
    subject_points: list[tuple[float, float, float]],
    object_points: list[tuple[float, float, float]],
) -> dict[str, float]:
    sx0, sy0, sz0 = subject["aabb_min"]
    sx1, sy1, _sz1 = subject["aabb_max"]
    ox0, oy0, _oz0 = obj["aabb_min"]
    ox1, oy1, oz1 = obj["aabb_max"]
    band = max(0.03, min(subject["aabb_max"][2] - sz0, oz1 - obj["aabb_min"][2]) * 0.05)
    xy_margin = 0.02

    def in_xy(x: float, y: float, x0: float, y0: float, x1: float, y1: float) -> bool:
        return (x0 - xy_margin) <= x <= (x1 + xy_margin) and (y0 - xy_margin) <= y <= (y1 + xy_margin)

    subject_near = sum(
        1
        for x, y, z in subject_points
        if abs(z - oz1) <= band and in_xy(x, y, ox0, oy0, ox1, oy1)
    )
    object_near = sum(
        1
        for x, y, z in object_points
        if abs(z - sz0) <= band and in_xy(x, y, sx0, sy0, sx1, sy1)
    )
    subject_count = len(subject_points)
    object_count = len(object_points)
    pair_min = max(min(subject_count, object_count), 1)
    return {
        "point_subject_count": float(subject_count),
        "point_object_count": float(object_count),
        "point_pair_min_count": float(min(subject_count, object_count)),
        "point_pair_total_count": float(subject_count + object_count),
        "contact_band_width": band,
        "subject_near_object_top_point_count": float(subject_near),
        "object_near_subject_bottom_point_count": float(object_near),
        "subject_near_object_top_point_ratio": subject_near / max(subject_count, 1),
        "object_near_subject_bottom_point_ratio": object_near / max(object_count, 1),
        "local_contact_point_count": float(subject_near + object_near),
        "local_contact_point_density": (subject_near + object_near) / pair_min,
    }


def richer_geometry(
    subject: dict[str, Any],
    obj: dict[str, Any],
    subject_points: list[tuple[float, float, float]],
    object_points: list[tuple[float, float, float]],
) -> tuple[list[str], dict[str, float], dict[str, bool], dict[str, Any]]:
    sc = subject["centroid"]
    oc = obj["centroid"]
    sx0, sy0, sz0 = subject["aabb_min"]
    sx1, sy1, sz1 = subject["aabb_max"]
    ox0, oy0, oz0 = obj["aabb_min"]
    ox1, oy1, oz1 = obj["aabb_max"]
    subject_area = max((sx1 - sx0) * (sy1 - sy0), 1e-9)
    object_area = max((ox1 - ox0) * (oy1 - oy0), 1e-9)
    overlap_x = interval_overlap(sx0, sx1, ox0, ox1)
    overlap_y = interval_overlap(sy0, sy1, oy0, oy1)
    overlap_z = interval_overlap(sz0, sz1, oz0, oz1)
    overlap_xy = overlap_x * overlap_y
    min_area = max(min(subject_area, object_area), 1e-9)
    max_area = max(max(subject_area, object_area), 1e-9)
    vertical_gap = sz0 - oz1
    normal_alignment = abs(dot(subject.get("dominant_normal"), obj.get("dominant_normal")))
    point_features = contact_point_features(subject, obj, subject_points, object_points)
    vector: dict[str, float] = {
        "surface_gap_subject_bottom_to_object_top": vertical_gap,
        "abs_surface_gap_subject_bottom_to_object_top": abs(vertical_gap),
        "center_delta_z": sc[2] - oc[2],
        "xy_center_distance": math.sqrt((sc[0] - oc[0]) ** 2 + (sc[1] - oc[1]) ** 2),
        "xy_overlap_area": overlap_xy,
        "xy_overlap_min_ratio": overlap_xy / min_area,
        "xy_overlap_max_ratio": overlap_xy / max_area,
        "xy_overlap_subject_ratio": overlap_xy / subject_area,
        "xy_overlap_object_ratio": overlap_xy / object_area,
        "vertical_overlap_ratio": overlap_z / max(min(sz1 - sz0, oz1 - oz0), 1e-9),
        "support_contact_likelihood_proxy": (overlap_xy / min_area) / (1.0 + abs(vertical_gap)),
        "aabb_intersection_volume_proxy": overlap_xy * overlap_z,
        "normal_alignment_abs": normal_alignment,
        "surface_alignment_abs": normal_alignment,
        "support_surface_normal_upness": obj.get("dominant_normal_upness", 0.0),
    }
    vector.update(object_shape_features(subject, "subject"))
    vector.update(object_shape_features(obj, "object"))
    vector.update(point_features)
    vector["contact_patch_ratio_proxy"] = (
        vector["xy_overlap_min_ratio"]
        * max(vector["subject_near_object_top_point_ratio"], vector["object_near_subject_bottom_point_ratio"])
    )
    names = sorted(vector)
    mask = {name: math.isfinite(value) for name, value in vector.items()}
    q_e = {
        "semseg_obb_pair_available": True,
        "dominant_normal_pair_available": bool(subject.get("dominant_normal") and obj.get("dominant_normal")),
        "point_pair_available": bool(subject_points and object_points),
        "local_contact_density_available": bool(subject_points and object_points),
        "mesh_gap_intersection_available": False,
        "mesh_gap_intersection_missing_mask": True,
        "geometry_quality_flag": "semseg_obb_plus_point_objectid" if subject_points and object_points else "semseg_obb_only",
    }
    return names, vector, mask, q_e


def validate_plan(plan_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    summary_path = plan_dir / "summary.json"
    if not summary_path.exists():
        return [{"error_type": "missing_plan_summary", "path": str(summary_path)}]
    summary = read_json(summary_path)
    if summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": summary.get("validation_errors")})
    decision = summary.get("decision", {})
    for key in ["z_e_excluded_from_main_c_e", "q_e_excluded_from_main_c_e", "class_labels_excluded_from_primary_view"]:
        if decision.get(key) is not True:
            errors.append({"error_type": "unexpected_plan_decision", "key": key, "actual": decision.get(key)})
    return errors


def load_official_support_rows(materialization_dir: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(materialization_dir / "model_safe_view.jsonl"):
        if row.get("schema_version") != EXPECTED_SOURCE_SCHEMA:
            errors.append({"error_type": "unexpected_source_schema", "candidate_id": row.get("candidate_id")})
            continue
        if row.get("route_family") == FAMILY and row.get("predicate_label") in MAIN_PREDICATES:
            rows.append(row)
    hidden = {row.get("candidate_id"): row for row in iter_jsonl(materialization_dir / "hidden_manifest.jsonl")}
    return rows, hidden, errors


def build_outputs(repo_root: Path, rows: list[dict[str, Any]], hidden_by_id: dict[str, Any], scan_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_scan[str(row.get("scan_id"))].append(row)

    candidate_rows: list[dict[str, Any]] = []
    no_class_rows: list[dict[str, Any]] = []
    class_rows: list[dict[str, Any]] = []
    geometry_rows: list[dict[str, Any]] = []
    qe_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    group_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    feature_presence: Counter[str] = Counter()

    for scan_id, scan_rows in sorted(by_scan.items()):
        interest_ids = {int(row["subject_id"]) for row in scan_rows} | {int(row["object_id"]) for row in scan_rows}
        try:
            objects = semseg_object_map(scan_dir, scan_id)
        except Exception as exc:  # noqa: BLE001
            errors.append({"error_type": "semseg_read_error", "scan_id": scan_id, "message": str(exc)})
            continue
        try:
            points = parse_interest_points(scan_dir, scan_id, interest_ids)
        except Exception as exc:  # noqa: BLE001
            errors.append({"error_type": "ply_read_error", "scan_id": scan_id, "message": str(exc)})
            points = {object_id: [] for object_id in interest_ids}

        for row in scan_rows:
            subject_id = int(row["subject_id"])
            object_id = int(row["object_id"])
            if subject_id not in objects or object_id not in objects:
                errors.append(
                    {
                        "error_type": "missing_semseg_object",
                        "candidate_id": row.get("candidate_id"),
                        "scan_id": scan_id,
                        "subject_id": subject_id,
                        "object_id": object_id,
                    }
                )
                continue
            names, vector, mask, qe = richer_geometry(
                objects[subject_id],
                objects[object_id],
                points.get(subject_id, []),
                points.get(object_id, []),
            )
            for name, available in mask.items():
                if available:
                    feature_presence[name] += 1
            source_t = row.get("feature_blocks", {}).get("T_e", {})
            candidate_id = row["candidate_id"]
            label = {"C_e": int(row["target_y"])}
            base_meta = {
                "schema_version": SCHEMA_VERSION,
                "candidate_id": candidate_id,
                "split": "validation",
                "route_family": FAMILY,
                "predicate_label": row["predicate_label"],
                "labels": label,
                "official_validation_eval_only": True,
                "paper_metric_ready": False,
                "official_test_used": False,
                "feature_use_policy": {
                    "row_identity_not_features": ["candidate_id", "cv_or_group_key"],
                    "label_not_features": ["labels.C_e"],
                    "main_C_e_allowed_blocks": ["T_e", "G_e"],
                    "excluded_from_primary_C_e": ["Z_e", "Q_e", "class labels", "H001 p_geom_valid"],
                },
            }
            t_no_class = {
                "predicate_text": row["predicate_label"],
                "predicate_label": row["predicate_label"],
                "route_family": FAMILY,
                "predicate_family_embedding_key": FAMILY,
            }
            t_with_class = {
                **t_no_class,
                "subject_class_label": source_t.get("subject_class_label"),
                "object_class_label": source_t.get("object_class_label"),
            }
            g_block = {
                "g_e_available": True,
                "g_e_feature_names": names,
                "g_e_feature_vector": vector,
                "g_e_feature_mask": mask,
                "geometry_reference_policy": "semseg_obb_plus_objectid_point_contact_pose_surface_features",
            }
            no_class = {**base_meta, "feature_blocks": {"T_e": t_no_class, "G_e": g_block}}
            with_class = {**base_meta, "feature_blocks": {"T_e": t_with_class, "G_e": g_block}}
            geometry_only = {**base_meta, "feature_blocks": {"G_e": g_block}}
            qe_diag = {**base_meta, "feature_blocks": {"Q_e": qe}}
            full = {
                **base_meta,
                "scan_id": scan_id,
                "subject_id": subject_id,
                "object_id": object_id,
                "cv_or_group_key": row.get("cv_or_group_key"),
                "feature_blocks": {"T_e": t_with_class, "G_e": g_block, "Q_e": qe, "Z_e": {}},
                "hidden_manifest_ref": candidate_id,
                "source_materialization_ref": "official_materialization/latest",
            }
            source_hidden = hidden_by_id.get(candidate_id, {})
            hidden = {
                "schema_version": f"{SCHEMA_VERSION}_hidden_manifest",
                "candidate_id": candidate_id,
                "scan_id": scan_id,
                "subject_id": subject_id,
                "object_id": object_id,
                "cv_or_group_key": row.get("cv_or_group_key"),
                "route_family": FAMILY,
                "candidate_predicate_label": row["predicate_label"],
                "labels": label,
                "subject_class_label": source_t.get("subject_class_label"),
                "object_class_label": source_t.get("object_class_label"),
                "class_pair": f"{source_t.get('subject_class_label')}->{source_t.get('object_class_label')}",
                "source_hidden_manifest": source_hidden,
                "h001_p_geom_valid_policy": "hidden_or_diagnostic_only_not_main_G_e",
                "source_score_policy": "Z_e_hidden_or_future_p_rel_only_not_main_C_e",
            }
            candidate_rows.append(full)
            no_class_rows.append(no_class)
            class_rows.append(with_class)
            geometry_rows.append(geometry_only)
            qe_rows.append(qe_diag)
            hidden_rows.append(hidden)
            group_map[str(row.get("cv_or_group_key"))].append(
                {
                    "candidate_id": candidate_id,
                    "predicate_label": row["predicate_label"],
                    "label_C_e": int(row["target_y"]),
                }
            )

    group_rows: list[dict[str, Any]] = []
    for group_id, group_members in sorted(group_map.items()):
        predicates = sorted(member["predicate_label"] for member in group_members)
        labels = sorted(member["label_C_e"] for member in group_members)
        group_rows.append(
            {
                "schema_version": f"{SCHEMA_VERSION}_group_manifest",
                "cv_or_group_key": group_id,
                "candidate_ids": [member["candidate_id"] for member in group_members],
                "predicates": predicates,
                "labels": labels,
                "pair_integrity_ok": len(group_members) == 2 and predicates == sorted(MAIN_PREDICATES) and labels == [0, 1],
            }
        )
    feature_rows = [
        {
            "feature": name,
            "present_rows": feature_presence[name],
            "total_rows": len(no_class_rows),
            "present_rate": round(feature_presence[name] / len(no_class_rows), 6) if no_class_rows else 0.0,
        }
        for name in sorted(feature_presence)
    ]
    outputs = {
        "candidate_rows": candidate_rows,
        "model_safe_main_no_class": no_class_rows,
        "model_safe_main_with_class_ablation": class_rows,
        "model_safe_geometry_only": geometry_rows,
        "model_safe_qe_diagnostic": qe_rows,
        "hidden_manifest": hidden_rows,
        "group_manifest": group_rows,
        "feature_availability": feature_rows,
    }
    return outputs, errors


def summarize(repo_root: Path, out: Path, outputs: dict[str, list[dict[str, Any]]], validation_errors: list[dict[str, Any]]) -> dict[str, Any]:
    no_class = outputs["model_safe_main_no_class"]
    labels = Counter(str(row.get("labels", {}).get("C_e")) for row in no_class)
    predicates = Counter(row.get("predicate_label") for row in no_class)
    groups = outputs["group_manifest"]
    bad_groups = [row for row in groups if not row.get("pair_integrity_ok")]
    feature_rows = outputs["feature_availability"]
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "h002_support_contact_harder_route_materialization_ready" if not validation_errors else "h002_support_contact_harder_route_materialization_errors",
        "validation_errors": len(validation_errors),
        "paper_metric_produced": False,
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "source_reranking_run": False,
        "p_rel_claim_enabled": False,
        "p_obs_claim_enabled": False,
        "output_artifacts": {
            "candidate_rows": repo_rel(repo_root, out / "candidate_rows.jsonl"),
            "model_safe_main_no_class": repo_rel(repo_root, out / "model_safe_main_no_class.jsonl"),
            "model_safe_main_with_class_ablation": repo_rel(repo_root, out / "model_safe_main_with_class_ablation.jsonl"),
            "model_safe_geometry_only": repo_rel(repo_root, out / "model_safe_geometry_only.jsonl"),
            "model_safe_qe_diagnostic": repo_rel(repo_root, out / "model_safe_qe_diagnostic.jsonl"),
            "hidden_manifest": repo_rel(repo_root, out / "hidden_manifest.jsonl"),
            "group_manifest": repo_rel(repo_root, out / "group_manifest.jsonl"),
            "feature_availability": repo_rel(repo_root, out / "feature_availability.csv"),
            "schema_precheck": repo_rel(repo_root, out / "schema_precheck.json"),
            "row_manifest": repo_rel(repo_root, out / "row_manifest.json"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
        },
        "row_counts": {
            "candidate_rows": len(outputs["candidate_rows"]),
            "model_safe_main_no_class": len(outputs["model_safe_main_no_class"]),
            "model_safe_main_with_class_ablation": len(outputs["model_safe_main_with_class_ablation"]),
            "model_safe_geometry_only": len(outputs["model_safe_geometry_only"]),
            "model_safe_qe_diagnostic": len(outputs["model_safe_qe_diagnostic"]),
            "hidden_manifest": len(outputs["hidden_manifest"]),
            "group_manifest": len(outputs["group_manifest"]),
            "label_counts": dict(sorted(labels.items())),
            "predicate_counts": dict(sorted(predicates.items())),
            "bad_group_count": len(bad_groups),
            "feature_count": len(feature_rows),
        },
        "boundary": {
            "main_view": "model_safe_main_no_class",
            "main_C_e_allowed_blocks": ["T_e", "G_e"],
            "excluded_from_main_C_e": ["Z_e", "Q_e", "class labels", "H001 p_geom_valid", "source score/rank"],
            "h001_artifacts_modified": False,
            "metrics_run": False,
        },
        "next_todo": "compatibility_dataset_v3_support_contact_harder_route_docker_materialization_stage_review",
    }


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    plan_dir = resolve(repo_root, args.plan_dir)
    official_dir = resolve(repo_root, args.official_materialization_dir)
    scan_dir = resolve(repo_root, args.scan_dir)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    validation_errors = validate_plan(plan_dir)
    rows: list[dict[str, Any]] = []
    hidden: dict[str, dict[str, Any]] = {}
    if not validation_errors:
        rows, hidden, load_errors = load_official_support_rows(official_dir)
        validation_errors.extend(load_errors)
    if not rows and not validation_errors:
        validation_errors.append({"error_type": "no_official_support_contact_rows_loaded"})

    outputs = {
        "candidate_rows": [],
        "model_safe_main_no_class": [],
        "model_safe_main_with_class_ablation": [],
        "model_safe_geometry_only": [],
        "model_safe_qe_diagnostic": [],
        "hidden_manifest": [],
        "group_manifest": [],
        "feature_availability": [],
    }
    if rows and not validation_errors:
        outputs, row_errors = build_outputs(repo_root, rows, hidden, scan_dir)
        validation_errors.extend(row_errors)

    write_jsonl(out / "candidate_rows.jsonl", outputs["candidate_rows"])
    write_jsonl(out / "model_safe_main_no_class.jsonl", outputs["model_safe_main_no_class"])
    write_jsonl(out / "model_safe_main_with_class_ablation.jsonl", outputs["model_safe_main_with_class_ablation"])
    write_jsonl(out / "model_safe_geometry_only.jsonl", outputs["model_safe_geometry_only"])
    write_jsonl(out / "model_safe_qe_diagnostic.jsonl", outputs["model_safe_qe_diagnostic"])
    write_jsonl(out / "hidden_manifest.jsonl", outputs["hidden_manifest"])
    write_jsonl(out / "group_manifest.jsonl", outputs["group_manifest"])
    write_csv(out / "feature_availability.csv", outputs["feature_availability"])
    summary = summarize(repo_root, out, outputs, validation_errors)
    write_json(out / "schema_precheck.json", summary)
    write_json(out / "row_manifest.json", summary)
    write_jsonl(out / "validation_errors.jsonl", validation_errors)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
