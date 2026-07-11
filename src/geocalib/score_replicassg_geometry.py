#!/usr/bin/env python3
"""Attach frozen H001 geometry features and verifier status to ReplicaSSG rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from plyfile import PlyData


SCHEMA_VERSION = "h001_replicassg_geometry_v1"
FEATURE_NAMES = (
    "distance_3d", "distance_xy", "normalized_distance_3d", "normalized_distance_xy",
    "center_delta_z", "normalized_center_delta_z", "projected_iou_xy",
    "projected_subject_overlap_ratio", "projected_object_overlap_ratio",
    "vertical_gap_subject_on_object", "subject_bottom_z", "subject_top_z",
    "object_bottom_z", "object_top_z",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--docker-service", default="replicassg_geometry")
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0 else None


def intersection(low_a: float, high_a: float, low_b: float, high_b: float) -> float:
    return max(0.0, min(high_a, high_b) - max(low_a, low_b))


def geometry(points: np.ndarray) -> dict[str, Any] | None:
    if points.ndim != 2 or points.shape[1] != 3 or len(points) == 0:
        return None
    # Replica raw y is up. Canonical H001 geometry uses z as up: (x,z,y).
    canonical = points[:, [0, 2, 1]].astype(np.float64, copy=False)
    low, high = canonical.min(axis=0), canonical.max(axis=0)
    size = high - low
    center = (high + low) / 2.0
    return {
        "center_xyz": center.tolist(),
        "aabb_min_xyz": low.tolist(),
        "aabb_max_xyz": high.tolist(),
        "size_xyz": size.tolist(),
        "height_z": float(size[2]),
        "diag_3d": float(np.linalg.norm(size)),
        "diag_xy": float(np.linalg.norm(size[:2])),
        "point_count": int(len(points)),
    }


def compute_features(subject: dict[str, Any], obj: dict[str, Any]) -> dict[str, float | None]:
    s_low, s_high = np.asarray(subject["aabb_min_xyz"]), np.asarray(subject["aabb_max_xyz"])
    o_low, o_high = np.asarray(obj["aabb_min_xyz"]), np.asarray(obj["aabb_max_xyz"])
    delta = np.asarray(subject["center_xyz"]) - np.asarray(obj["center_xyz"])
    distance_3d = float(np.linalg.norm(delta))
    distance_xy = float(np.linalg.norm(delta[:2]))
    mean_diag_3d = (subject["diag_3d"] + obj["diag_3d"]) / 2.0
    mean_diag_xy = (subject["diag_xy"] + obj["diag_xy"]) / 2.0
    mean_height = (subject["height_z"] + obj["height_z"]) / 2.0
    overlap_x = intersection(s_low[0], s_high[0], o_low[0], o_high[0])
    overlap_y = intersection(s_low[1], s_high[1], o_low[1], o_high[1])
    inter_xy = overlap_x * overlap_y
    subject_area = float(np.prod(np.maximum(s_high[:2] - s_low[:2], 0.0)))
    object_area = float(np.prod(np.maximum(o_high[:2] - o_low[:2], 0.0)))
    union = subject_area + object_area - inter_xy
    return {
        "distance_3d": distance_3d,
        "distance_xy": distance_xy,
        "normalized_distance_3d": safe_div(distance_3d, mean_diag_3d),
        "normalized_distance_xy": safe_div(distance_xy, mean_diag_xy),
        "center_delta_z": float(delta[2]),
        "normalized_center_delta_z": safe_div(float(delta[2]), mean_height),
        "projected_iou_xy": safe_div(inter_xy, union),
        "projected_subject_overlap_ratio": safe_div(inter_xy, subject_area),
        "projected_object_overlap_ratio": safe_div(inter_xy, object_area),
        "vertical_gap_subject_on_object": float(s_low[2] - o_high[2]),
        "subject_bottom_z": float(s_low[2]),
        "subject_top_z": float(s_high[2]),
        "object_bottom_z": float(o_low[2]),
        "object_top_z": float(o_high[2]),
    }


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def projected_overlap(features: dict[str, Any]) -> bool:
    return (finite(features.get("projected_subject_overlap_ratio")) or 0.0) > 0.0 or (
        finite(features.get("projected_object_overlap_ratio")) or 0.0
    ) > 0.0


def verify(family: str, label: str, features: dict[str, Any]) -> tuple[str, float, list[str]]:
    """Exact proximity/vertical rules from join_predictions.py's frozen OBB verifier."""
    if family == "proximity":
        norm_xy = finite(features.get("normalized_distance_xy"))
        if norm_xy is None:
            return "uncertain", 0.5, ["missing_normalized_distance_xy"]
        overlap = projected_overlap(features)
        if overlap or norm_xy <= 2.5:
            score = 0.75 if overlap else clamp(1.0 - norm_xy / 5.0, 0.55, 0.9)
            return "satisfied", score, ["near_in_xy_or_projected_overlap"]
        if norm_xy >= 3.5:
            return "violated", clamp(1.0 - norm_xy / 5.0, 0.05, 0.35), ["far_in_normalized_xy"]
        return "uncertain", 0.5, ["proximity_margin_ambiguous"]
    if family == "relative_vertical":
        center_delta = finite(features.get("center_delta_z"))
        normalized_delta = finite(features.get("normalized_center_delta_z"))
        if center_delta is None or normalized_delta is None:
            return "uncertain", 0.5, ["missing_vertical_delta"]
        sign = -1.0 if label == "lower than" else 1.0
        aligned, aligned_norm = sign * center_delta, sign * normalized_delta
        score = clamp((aligned_norm + 0.4) / 0.8, 0.05, 0.95)
        if aligned >= 0.25 and aligned_norm >= 0.15:
            return "satisfied", max(score, 0.75), ["vertical_order_matches_predicate"]
        if aligned <= -0.25 and aligned_norm <= -0.15:
            return "violated", min(score, 0.25), ["vertical_order_contradicts_predicate"]
        return "uncertain", 0.5, ["vertical_margin_ambiguous"]
    raise ValueError(f"unsupported_family:{family}")


def load_scan_geometry(path: Path) -> dict[int, dict[str, Any]]:
    mesh = PlyData.read(str(path))
    vertices = mesh["vertex"]
    points = np.stack([vertices["x"], vertices["y"], vertices["z"]], axis=1)
    ids = np.asarray(vertices["objectId"], dtype=np.int64)
    result: dict[int, dict[str, Any]] = {}
    for object_id in np.unique(ids):
        value = geometry(points[ids == object_id])
        if value is not None:
            result[int(object_id)] = value
    return result


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    predictions_path = resolve(root, args.predictions)
    dataset_root = resolve(root, args.dataset_root)
    protocol_path = resolve(root, args.protocol)
    out = resolve(root, args.out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("status") != "frozen_before_source_prediction":
        raise ValueError("prospective_protocol_not_frozen")

    rows: list[dict[str, Any]] = []
    with predictions_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    scan_set = {str(row["scan_id"]) for row in rows}
    if not scan_set.issubset(set(protocol["dataset"]["test_scans"])):
        raise ValueError("candidate_scan_outside_frozen_test_split")

    geometries = {
        scan: load_scan_geometry(dataset_root / "data" / scan / "labels.instances.annotated.v2.ply")
        for scan in sorted(scan_set)
    }
    status_counts: Counter[str] = Counter()
    family_status: dict[str, Counter[str]] = defaultdict(Counter)
    missing: Counter[str] = Counter()
    output_rows: list[dict[str, Any]] = []
    for row in rows:
        scan = str(row["scan_id"])
        subject_id, object_id = int(row["edge"]["subject_id"]), int(row["edge"]["object_id"])
        subject = geometries[scan].get(subject_id)
        obj = geometries[scan].get(object_id)
        if subject is None or obj is None:
            for name, value in (("subject", subject), ("object", obj)):
                if value is None:
                    missing[f"{scan}:{name}"] += 1
            features = {name: None for name in FEATURE_NAMES}
            status, score, reasons = "uncertain", 0.5, ["missing_endpoint_geometry"]
        else:
            features = compute_features(subject, obj)
            family = str(row["predicate"]["predicate_family"])
            label = str(row["predicate"]["predicate_label"])
            status, score, reasons = verify(family, label, features)
        enriched = dict(row)
        enriched["geometry"] = {
            "source": "ReplicaSSG labels.instances.annotated.v2.ply face-center instance geometry",
            "coordinate_transform": "(x_canonical,y_canonical,z_canonical)=(x_raw,z_raw,y_raw)",
            "features": features,
        }
        enriched["verification_status"] = status
        enriched["verification"] = {
            "verification_status": status,
            "consistency_score": score,
            "policy_name": "h001-prediction-join-v0",
            "policy_version": "frozen_obb_rules",
            "geometry_source": "replicassg_instance_face_centers_aabb_v1",
            "reason_codes": reasons,
        }
        output_rows.append(enriched)
        status_counts[status] += 1
        family_status[row["predicate"]["predicate_family"]][status] += 1

    out.mkdir(parents=True, exist_ok=False)
    verification_path = out / "verification.jsonl"
    with verification_path.open("w", encoding="utf-8") as handle:
        for row in output_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "geometry_ready" if not missing else "geometry_ready_with_missing_endpoints",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "input_rows": len(rows),
            "output_rows": len(output_rows),
            "rows_preserved": len(rows) == len(output_rows),
            "contexts": len(scan_set),
            "by_status": dict(sorted(status_counts.items())),
            "by_family_status": {key: dict(sorted(value.items())) for key, value in sorted(family_status.items())},
            "missing_endpoint_geometry": dict(sorted(missing.items())),
        },
        "firewall": {
            "relationship_annotations_read": False,
            "relation_ground_truth_used": False,
            "geometry_source_is_instance_annotation": True,
        },
        "inputs": {
            "predictions": {"path": relpath(root, predictions_path), "sha256": sha256(predictions_path)},
            "protocol": {"path": relpath(root, protocol_path), "sha256": sha256(protocol_path)},
        },
        "outputs": {
            "verification": {"path": relpath(root, verification_path), "sha256": sha256(verification_path)}
        },
        "docker_command": f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/fross/compose.yaml run --rm {args.docker_service}",
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
