#!/usr/bin/env python3
"""Apply h001-verifier-v2 to one-scan H001 artifacts.

This is a hypothesis-stage smoke test. It revises only support/contact
verification by adding subtype assignment and soft geometry consistency scores.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RULE_VERSION = "h001-verifier-v2"
PREVIOUS_RULE_VERSION = "h001-rules-v1"
PRIMARY_FAMILIES = {"support_contact", "proximity", "relative_vertical"}
ALLOWED_STATUSES = {"satisfied", "violated", "uncertain", "unsupported"}
STATUS_ALIAS = {
    "satisfied": "pass",
    "violated": "fail",
    "uncertain": "uncertain",
    "unsupported": "not_applicable",
}

SOFT_LABELS = {"pillow", "cushion", "blanket", "clothes", "towel"}
FURNITURE_SUPPORT_LABELS = {
    "table",
    "desk",
    "kitchen counter",
    "counter",
    "cabinet",
    "shelf",
    "sofa",
    "chair",
    "bed",
    "stool",
    "bench",
}
GEOMETRY_QUALITY_LABELS = {"segmentation_or_instance_issue"}
LOCAL_SURFACE_LABELS = {"local_surface_estimator_issue"}
RULE_TOO_STRICT_LABELS = {"rule_too_strict"}

DEFAULT_THRESHOLDS = {
    "rule_version": RULE_VERSION,
    "previous_rule_version": PREVIOUS_RULE_VERSION,
    "satisfied_score_min": 0.70,
    "uncertain_score_min": 0.40,
    "low_gap_pass_abs_m": 0.08,
    "low_gap_fail_abs_m": 0.18,
    "robust_gap_pass_abs_m": 0.10,
    "soft_penetration_pass_m": 0.15,
    "soft_penetration_max_m": 0.45,
    "positive_float_pass_m": 0.08,
    "positive_float_fail_m": 0.20,
    "support_density_good_count": 50,
    "plane_expansion_m": 0.20,
    "plane_bin_m": 0.04,
    "plane_search_below_m": 0.25,
    "plane_search_above_m": 0.12,
    "plane_gap_pass_abs_m": 0.08,
    "plane_gap_fail_abs_m": 0.22,
    "plane_min_inlier_count": 10,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply subtype-aware H001 verifier v2 to one-scan artifacts."
    )
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--scan-id")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            stripped = line.strip()
            if stripped:
                record = json.loads(stripped)
                record["_source_line"] = line_number
                records.append(record)
    return records


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def count_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def nested_count_dict(counter: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: count_dict(counter[key]) for key in sorted(counter)}


def label(value: Any) -> str:
    return str(value or "").strip().lower()


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def score_abs(value: float | None, pass_abs: float, fail_abs: float) -> float:
    if value is None:
        return 0.0
    distance = abs(float(value))
    if distance <= pass_abs:
        return 1.0
    if distance >= fail_abs:
        return 0.0
    return clamp(1.0 - (distance - pass_abs) / (fail_abs - pass_abs))


def score_count(count: int | None, good_count: int) -> float:
    if count is None or good_count <= 0:
        return 0.0
    return clamp(float(count) / float(good_count))


def status_from_score(score: float | None, thresholds: dict[str, Any]) -> str:
    if score is None:
        return "uncertain"
    if score >= float(thresholds["satisfied_score_min"]):
        return "satisfied"
    if score >= float(thresholds["uncertain_score_min"]):
        return "uncertain"
    return "violated"


def parse_ply_header(path: Path) -> tuple[dict[str, Any], int]:
    properties: list[str] = []
    vertex_count: int | None = None
    face_count: int | None = None
    header_lines = 0
    in_vertex = False
    with path.open("r", encoding="utf-8", errors="replace") as f:
        first_line = f.readline().strip()
        header_lines += 1
        if first_line != "ply":
            raise ValueError(f"expected_ply_header:{first_line!r}")
        for line in f:
            header_lines += 1
            stripped = line.strip()
            if stripped.startswith("format") and stripped != "format ascii 1.0":
                raise ValueError(f"unsupported_ply_format:{stripped}")
            if stripped.startswith("element vertex"):
                vertex_count = int(stripped.split()[-1])
                in_vertex = True
            elif stripped.startswith("element face"):
                face_count = int(stripped.split()[-1])
                in_vertex = False
            elif stripped.startswith("property") and in_vertex:
                properties.append(stripped.split()[-1])
            elif stripped == "end_header":
                break
    if vertex_count is None:
        raise ValueError("missing_vertex_count")
    return {
        "vertex_count": vertex_count,
        "face_count": face_count,
        "properties": properties,
    }, header_lines


def read_target_points(
    path: Path,
    object_ids: set[int],
) -> tuple[dict[int, dict[str, list[float]]], dict[str, Any]]:
    header, _ = parse_ply_header(path)
    properties = header["properties"]
    for required in ("x", "y", "z", "objectId"):
        if required not in properties:
            raise ValueError(f"missing_ply_property:{required}")
    x_idx = properties.index("x")
    y_idx = properties.index("y")
    z_idx = properties.index("z")
    object_id_idx = properties.index("objectId")
    max_idx = max(x_idx, y_idx, z_idx, object_id_idx)

    points = {object_id: {"x": [], "y": [], "z": []} for object_id in object_ids}
    rows_read = 0
    rows_kept = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip() == "end_header":
                break
        for _ in range(int(header["vertex_count"])):
            line = f.readline()
            if not line:
                break
            rows_read += 1
            parts = line.split()
            if len(parts) <= max_idx:
                continue
            object_id = int(parts[object_id_idx])
            if object_id not in object_ids:
                continue
            points[object_id]["x"].append(float(parts[x_idx]))
            points[object_id]["y"].append(float(parts[y_idx]))
            points[object_id]["z"].append(float(parts[z_idx]))
            rows_kept += 1

    stats = {
        "ply_vertex_count_header": header["vertex_count"],
        "ply_face_count_header": header["face_count"],
        "ply_vertex_rows_read": rows_read,
        "target_vertex_rows_kept": rows_kept,
        "target_object_ids": sorted(object_ids),
    }
    return points, stats


def local_support_z_values(
    subject_stats: dict[str, Any],
    support_points: dict[str, list[float]] | None,
    expansion_m: float,
) -> list[float]:
    if support_points is None:
        return []
    required = ("x_p05", "x_p95", "y_p05", "y_p95")
    if any(subject_stats.get(key) is None for key in required):
        return []
    x_min = float(subject_stats["x_p05"]) - expansion_m
    x_max = float(subject_stats["x_p95"]) + expansion_m
    y_min = float(subject_stats["y_p05"]) - expansion_m
    y_max = float(subject_stats["y_p95"]) + expansion_m
    values: list[float] = []
    for x, y, z in zip(support_points["x"], support_points["y"], support_points["z"]):
        if x_min <= x <= x_max and y_min <= y <= y_max:
            values.append(z)
    return values


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def estimate_horizontal_plane(
    local_z: list[float],
    subject_stats: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    if not local_z:
        return {
            "plane_available": False,
            "plane_z_m": None,
            "plane_inlier_count": 0,
            "plane_inlier_ratio": 0.0,
            "plane_residual_m": None,
            "plane_normal_z_abs": None,
            "plane_gap_m": None,
            "plane_confidence": 0.0,
        }

    subject_bottom = subject_stats.get("z_p05")
    if subject_bottom is None:
        return {
            "plane_available": False,
            "plane_z_m": None,
            "plane_inlier_count": 0,
            "plane_inlier_ratio": 0.0,
            "plane_residual_m": None,
            "plane_normal_z_abs": None,
            "plane_gap_m": None,
            "plane_confidence": 0.0,
        }

    bin_size = float(thresholds["plane_bin_m"])
    search_low = float(subject_bottom) - float(thresholds["plane_search_below_m"])
    search_high = float(subject_bottom) + float(thresholds["plane_search_above_m"])
    bins: dict[int, list[float]] = defaultdict(list)
    for z in local_z:
        if search_low <= z <= search_high:
            bins[math.floor(z / bin_size)].append(z)

    if not bins:
        # Fall back to all local support z values. This should usually produce
        # low confidence, but it prevents silent missing fields.
        for z in local_z:
            bins[math.floor(z / bin_size)].append(z)

    best_bin, best_values = max(
        bins.items(),
        key=lambda item: (
            len(item[1]),
            -abs((median(item[1]) or 0.0) - float(subject_bottom)),
        ),
    )
    _ = best_bin
    plane_z = median(best_values)
    if plane_z is None:
        plane_z = sum(best_values) / len(best_values)
    residual = sum(abs(z - plane_z) for z in best_values) / len(best_values)
    inlier_count = len(best_values)
    inlier_ratio = inlier_count / len(local_z)
    plane_gap = float(subject_bottom) - plane_z

    count_score = score_count(inlier_count, int(thresholds["plane_min_inlier_count"]))
    ratio_score = clamp(inlier_ratio / 0.15)
    residual_score = score_abs(residual, 0.015, 0.060)
    plane_confidence = 0.40 * count_score + 0.30 * ratio_score + 0.30 * residual_score

    return {
        "plane_available": inlier_count >= int(thresholds["plane_min_inlier_count"]),
        "plane_z_m": plane_z,
        "plane_inlier_count": inlier_count,
        "plane_inlier_ratio": inlier_ratio,
        "plane_residual_m": residual,
        "plane_normal_z_abs": 1.0,
        "plane_gap_m": plane_gap,
        "plane_confidence": clamp(plane_confidence),
    }


def load_visual_labels(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return {record["edge_id"]: record for record in read_jsonl(path)}


def assign_subtype(
    edge: dict[str, Any],
    point_record: dict[str, Any] | None,
    visual_label: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    subject_label = label(edge.get("subject_label") or (point_record or {}).get("subject_label"))
    object_label = label(edge.get("object_label") or (point_record or {}).get("object_label"))
    predicate_label = label(edge.get("predicate_label") or (point_record or {}).get("predicate_label"))
    visual_kind = label((visual_label or {}).get("inspection_label"))
    reasons: list[str] = []

    if visual_kind in GEOMETRY_QUALITY_LABELS or bool(
        (visual_label or {}).get("segmentation_or_instance_issue")
    ):
        reasons.append("subtype_geometry_quality_uncertain")
        return "geometry_quality_uncertain", reasons
    if predicate_label == "lying on" or subject_label in SOFT_LABELS or object_label in SOFT_LABELS:
        reasons.append("subtype_soft_support_contact")
        return "soft_support_contact", reasons
    if object_label == "floor":
        reasons.append("subtype_legged_floor_support")
        return "legged_floor_support", reasons
    reasons.append("subtype_rigid_object_on_furniture")
    if object_label in FURNITURE_SUPPORT_LABELS:
        reasons.append("furniture_support_object")
    return "rigid_object_on_furniture", reasons


def point_metrics(point_record: dict[str, Any] | None) -> dict[str, Any]:
    best = (point_record or {}).get("best_local_support_evidence") or {}
    return {
        "support_points_under_subject_count": best.get("support_points_under_subject_count"),
        "xy_expansion_m": best.get("xy_expansion_m"),
        "local_vertical_gap_p05_p95": best.get("local_vertical_gap_p05_p95"),
        "local_vertical_gap_p01_p99": best.get("local_vertical_gap_p01_p99"),
        "subject_point_stats": (point_record or {}).get("subject_point_stats"),
        "object_point_stats": (point_record or {}).get("object_point_stats"),
    }


def visual_reason_codes(visual_label: dict[str, Any] | None) -> list[str]:
    if not visual_label:
        return []
    kind = label(visual_label.get("inspection_label"))
    codes: list[str] = []
    if kind in RULE_TOO_STRICT_LABELS:
        codes.append("visual_rule_too_strict")
    if kind in LOCAL_SURFACE_LABELS:
        codes.append("visual_local_surface_issue")
    if kind in GEOMETRY_QUALITY_LABELS:
        codes.append("visual_geometry_quality_issue")
    return codes


def legged_score(
    point_record: dict[str, Any] | None,
    thresholds: dict[str, Any],
    visual_label: dict[str, Any] | None,
) -> tuple[float, dict[str, Any], list[str], list[str], list[str], list[str]]:
    metrics = point_metrics(point_record)
    low_gap = metrics["local_vertical_gap_p01_p99"]
    robust_gap = metrics["local_vertical_gap_p05_p95"]
    count = metrics["support_points_under_subject_count"]

    leg_contact_score = score_abs(
        low_gap,
        float(thresholds["low_gap_pass_abs_m"]),
        float(thresholds["low_gap_fail_abs_m"]),
    )
    support_density_score = score_count(
        count,
        int(thresholds["support_density_good_count"]),
    )
    contact_fraction_score = leg_contact_score
    score = clamp(0.70 * leg_contact_score + 0.30 * support_density_score)

    reason_codes = ["subtype_legged_floor_support"]
    passed: list[str] = []
    failed: list[str] = []
    uncertain: list[str] = []
    if leg_contact_score >= 0.70:
        passed.append("leg_contact_score")
        reason_codes.append("leg_contact_low_percentile_supported")
    else:
        uncertain.append("leg_contact_score")
    if support_density_score >= 0.70:
        passed.append("support_density_score")
    else:
        uncertain.append("support_density_score")
    if robust_gap is not None and abs(float(robust_gap)) > float(thresholds["robust_gap_pass_abs_m"]):
        reason_codes.append("robust_gap_too_strict_for_legs")

    # v2 policy: do not call legged floor support violated from one-scan
    # low-percentile evidence alone unless stronger evidence exists.
    if score < float(thresholds["uncertain_score_min"]):
        score = float(thresholds["uncertain_score_min"])
        uncertain.append("legged_floor_single_scan_violation")

    score_components = {
        "low_percentile_gap_m": low_gap,
        "robust_gap_m": robust_gap,
        "support_density_score": support_density_score,
        "contact_fraction_score": contact_fraction_score,
        "leg_contact_score": leg_contact_score,
        "visual_label": (visual_label or {}).get("inspection_label"),
    }
    return score, score_components, reason_codes, passed, failed, uncertain


def soft_score(
    point_record: dict[str, Any] | None,
    thresholds: dict[str, Any],
    visual_label: dict[str, Any] | None,
) -> tuple[float, dict[str, Any], list[str], list[str], list[str], list[str]]:
    metrics = point_metrics(point_record)
    signed_gap = metrics["local_vertical_gap_p05_p95"]
    count = metrics["support_points_under_subject_count"]
    penetration = max(0.0, -float(signed_gap)) if signed_gap is not None else None
    positive_float = max(0.0, float(signed_gap)) if signed_gap is not None else None
    soft_prior = 1.0

    if signed_gap is None:
        soft_gap_score = 0.0
    elif float(signed_gap) < 0:
        if penetration <= float(thresholds["soft_penetration_pass_m"]):
            soft_gap_score = 1.0
        elif penetration >= float(thresholds["soft_penetration_max_m"]):
            soft_gap_score = 0.55
        else:
            span = float(thresholds["soft_penetration_max_m"]) - float(
                thresholds["soft_penetration_pass_m"]
            )
            soft_gap_score = 1.0 - 0.45 * (
                (penetration - float(thresholds["soft_penetration_pass_m"])) / span
            )
    else:
        soft_gap_score = score_abs(
            positive_float,
            float(thresholds["positive_float_pass_m"]),
            float(thresholds["positive_float_fail_m"]),
        )

    support_density_score = score_count(
        count,
        int(thresholds["support_density_good_count"]),
    )
    score = clamp(0.55 * soft_gap_score + 0.30 * support_density_score + 0.15 * soft_prior)

    reason_codes = ["subtype_soft_support_contact"]
    passed: list[str] = []
    failed: list[str] = []
    uncertain: list[str] = []
    if signed_gap is not None and float(signed_gap) < 0:
        reason_codes.append("soft_penetration_allowed")
    if positive_float is not None and positive_float > float(thresholds["positive_float_fail_m"]):
        reason_codes.append("positive_float_gap_large")
        failed.append("positive_float_gap")
    else:
        passed.append("soft_gap_score")
    if support_density_score >= 0.70:
        passed.append("support_density_score")
    else:
        uncertain.append("support_density_score")

    score_components = {
        "signed_gap_m": signed_gap,
        "penetration_depth_m": penetration,
        "positive_float_gap_m": positive_float,
        "soft_prior": soft_prior,
        "soft_gap_score": soft_gap_score,
        "support_density_score": support_density_score,
        "visual_label": (visual_label or {}).get("inspection_label"),
    }
    return score, score_components, reason_codes, passed, failed, uncertain


def rigid_score(
    point_record: dict[str, Any] | None,
    points_by_object: dict[int, dict[str, list[float]]],
    thresholds: dict[str, Any],
    visual_label: dict[str, Any] | None,
) -> tuple[float | None, dict[str, Any], list[str], list[str], list[str], list[str]]:
    metrics = point_metrics(point_record)
    subject_stats = metrics.get("subject_point_stats") or {}
    object_id = int((point_record or {}).get("object_id") or -1)
    local_z = local_support_z_values(
        subject_stats,
        points_by_object.get(object_id),
        float(thresholds["plane_expansion_m"]),
    )
    plane = estimate_horizontal_plane(local_z, subject_stats, thresholds)
    plane_gap = plane["plane_gap_m"]
    plane_gap_score = score_abs(
        plane_gap,
        float(thresholds["plane_gap_pass_abs_m"]),
        float(thresholds["plane_gap_fail_abs_m"]),
    )
    support_density_score = score_count(
        len(local_z),
        int(thresholds["support_density_good_count"]),
    )
    score = clamp(
        0.55 * plane_gap_score
        + 0.35 * float(plane["plane_confidence"])
        + 0.10 * support_density_score
    )

    reason_codes = ["subtype_rigid_object_on_furniture"]
    passed: list[str] = []
    failed: list[str] = []
    uncertain: list[str] = []
    if plane["plane_available"] and plane["plane_confidence"] >= 0.40:
        reason_codes.append("horizontal_plane_found")
        passed.append("horizontal_plane")
    else:
        reason_codes.append("horizontal_plane_missing")
        uncertain.append("horizontal_plane")
    if plane_gap_score >= 0.70:
        reason_codes.append("plane_gap_supported")
        passed.append("plane_gap")
    elif plane_gap_score <= 0.20:
        reason_codes.append("plane_gap_large")
        failed.append("plane_gap")
    else:
        uncertain.append("plane_gap")

    if label((visual_label or {}).get("inspection_label")) in LOCAL_SURFACE_LABELS:
        reason_codes.append("surface_estimator_uncertain")
        # Keep visual local-surface failures out of hard violation at this
        # one-scan stage. If a horizontal plane cannot be recovered, uncertainty
        # is the correct smoke-test outcome.
        if score < float(thresholds["uncertain_score_min"]):
            score = float(thresholds["uncertain_score_min"])

    score_components = {
        **plane,
        "plane_gap_score": plane_gap_score,
        "support_density_score": support_density_score,
        "local_support_point_count": len(local_z),
        "visual_label": (visual_label or {}).get("inspection_label"),
    }
    return score, score_components, reason_codes, passed, failed, uncertain


def geometry_quality_record(
    visual_label: dict[str, Any] | None,
) -> tuple[None, dict[str, Any], list[str], list[str], list[str], list[str]]:
    return (
        None,
        {
            "geometry_issue_source": "visual_inspection",
            "point_density_flag": None,
            "instance_completeness_flag": None,
            "visual_ambiguity_flag": True,
            "visual_label": (visual_label or {}).get("inspection_label"),
        },
        ["subtype_geometry_quality_uncertain", "visual_geometry_quality_issue"],
        [],
        [],
        ["geometry_quality"],
    )


def support_v2_record(
    edge: dict[str, Any],
    point_record: dict[str, Any] | None,
    visual_label: dict[str, Any] | None,
    points_by_object: dict[int, dict[str, list[float]]],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    old_verification = edge.get("verification") or {}
    subtype, subtype_reason_codes = assign_subtype(edge, point_record, visual_label)

    if subtype == "geometry_quality_uncertain":
        score, components, reason_codes, passed, failed, uncertain = geometry_quality_record(
            visual_label
        )
        status = "uncertain"
    elif subtype == "legged_floor_support":
        score, components, reason_codes, passed, failed, uncertain = legged_score(
            point_record, thresholds, visual_label
        )
        status = status_from_score(score, thresholds)
    elif subtype == "soft_support_contact":
        score, components, reason_codes, passed, failed, uncertain = soft_score(
            point_record, thresholds, visual_label
        )
        status = status_from_score(score, thresholds)
    else:
        score, components, reason_codes, passed, failed, uncertain = rigid_score(
            point_record, points_by_object, thresholds, visual_label
        )
        if not components.get("plane_available"):
            status = "uncertain"
        else:
            status = status_from_score(score, thresholds)

    all_reason_codes = sorted(
        set(subtype_reason_codes + reason_codes + visual_reason_codes(visual_label))
    )
    geometry_quality_flags = {
        "visual_label": (visual_label or {}).get("inspection_label"),
        "relation_visually_plausible": (visual_label or {}).get("relation_visually_plausible"),
        "local_surface_correct": (visual_label or {}).get("local_surface_correct"),
        "segmentation_or_instance_issue": (visual_label or {}).get(
            "segmentation_or_instance_issue"
        ),
    }
    metrics = point_metrics(point_record)

    return {
        "edge_id": edge.get("edge_id"),
        "subject_id": edge.get("subject_id"),
        "object_id": edge.get("object_id"),
        "subject_label": edge.get("subject_label"),
        "predicate_label": edge.get("predicate_label"),
        "object_label": edge.get("object_label"),
        "previous_status": old_verification.get("status"),
        "previous_rule_version": old_verification.get("rule_version"),
        "subtype": subtype,
        "subtype_reason_codes": sorted(set(subtype_reason_codes)),
        "point_evidence_available": bool((point_record or {}).get("point_evidence_available")),
        "visual_label": (visual_label or {}).get("inspection_label"),
        "geometry_quality_flags": geometry_quality_flags,
        "consistency_score": score,
        "score_components": components,
        "status": status,
        "reason_codes": all_reason_codes,
        **metrics,
    }


def support_verification_object(
    edge: dict[str, Any],
    support_record: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    previous = edge.get("verification") or {}
    status = support_record["status"]
    checked = ["subtype_assignment", "subtype_evidence", "consistency_score"]
    return {
        "rule_version": RULE_VERSION,
        "previous_rule_version": previous.get("rule_version", PREVIOUS_RULE_VERSION),
        "previous_status": previous.get("status"),
        "status": status,
        "status_alias": STATUS_ALIAS[status],
        "predicate_family": edge.get("predicate_family"),
        "primary_metric_eligible": edge.get("predicate_family") in PRIMARY_FAMILIES
        and status in {"satisfied", "violated"},
        "diagnostic_only": False,
        "support_subtype": support_record["subtype"],
        "consistency_score": support_record["consistency_score"],
        "geometry_score": support_record["consistency_score"],
        "score_components": support_record["score_components"],
        "checked_constraints": checked,
        "passed_constraints": (
            checked
            if status == "satisfied"
            else ["subtype_assignment"]
        ),
        "failed_constraints": ["consistency_score"] if status == "violated" else [],
        "uncertain_constraints": checked if status == "uncertain" else [],
        "reason_codes": support_record["reason_codes"],
        "threshold_config": thresholds,
        "visual_label": support_record["visual_label"],
        "geometry_quality_flags": support_record["geometry_quality_flags"],
    }


def carried_verification_object(edge: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    previous = dict(edge.get("verification") or {})
    old_rule_version = previous.get("rule_version", PREVIOUS_RULE_VERSION)
    status = previous.get("status", "uncertain")
    reason_codes = set(previous.get("reason_codes", []))
    reason_codes.add("carried_from_v1")
    previous["rule_version"] = RULE_VERSION
    previous["previous_rule_version"] = old_rule_version
    previous["previous_status"] = status
    previous["status"] = status
    previous["status_alias"] = STATUS_ALIAS.get(status, "uncertain")
    previous["support_subtype"] = None
    previous["consistency_score"] = previous.get("geometry_score")
    previous["reason_codes"] = sorted(reason_codes)
    previous["threshold_config"] = thresholds
    return previous


def make_transition(edge: dict[str, Any], support_record: dict[str, Any]) -> dict[str, Any]:
    previous = support_record["previous_status"]
    status = support_record["status"]
    return {
        "edge_id": edge.get("edge_id"),
        "subject_label": edge.get("subject_label"),
        "predicate_label": edge.get("predicate_label"),
        "object_label": edge.get("object_label"),
        "subtype": support_record["subtype"],
        "v1_status": previous,
        "v2_status": status,
        "status_transition": f"v1_{previous}_to_v2_{status}",
        "v2_consistency_score": support_record["consistency_score"],
        "visual_label": support_record["visual_label"],
        "reason_codes": support_record["reason_codes"],
    }


def make_review_record(edge: dict[str, Any], support_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "edge_id": edge.get("edge_id"),
        "subject_label": edge.get("subject_label"),
        "predicate_label": edge.get("predicate_label"),
        "object_label": edge.get("object_label"),
        "subtype": support_record["subtype"],
        "v1_status": support_record["previous_status"],
        "v2_status": support_record["status"],
        "consistency_score": support_record["consistency_score"],
        "visual_label": support_record["visual_label"],
        "reason_codes": support_record["reason_codes"],
        "review_question": "Is this remaining v2 support/contact uncertainty a geometry-source issue, subtype rule issue, or true relation inconsistency?",
    }


def summarize(
    artifact_dir: Path,
    output_dir: Path,
    outputs: dict[str, Path],
    scan_id: str,
    decisions: list[dict[str, Any]],
    support_records: list[dict[str, Any]],
    transitions: list[dict[str, Any]],
    review: list[dict[str, Any]],
    visual_labels: dict[str, dict[str, Any]],
    ply_stats: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = ["h001_verifier_v2_smoke_test_only_not_benchmark_evidence"]

    if len(decisions) != 772:
        warnings.append(f"unexpected_edge_count:{len(decisions)}")
    if any(record["subtype"] is None for record in support_records):
        errors.append("support_contact_edge_without_subtype")
    for record in support_records:
        score = record["consistency_score"]
        if score is not None and not (0.0 <= float(score) <= 1.0):
            errors.append(f"consistency_score_out_of_range:{record['edge_id']}:{score}")
        if record["status"] not in ALLOWED_STATUSES:
            errors.append(f"unsupported_status:{record['edge_id']}:{record['status']}")

    visually_plausible_violations = [
        record
        for record in support_records
        if record["status"] == "violated"
        and record["geometry_quality_flags"].get("relation_visually_plausible") is True
    ]
    if visually_plausible_violations:
        warnings.append(f"visually_plausible_v2_violations:{len(visually_plausible_violations)}")

    support_status_counts = Counter(record["status"] for record in support_records)
    subtype_counts = Counter(record["subtype"] for record in support_records)
    subtype_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    visual_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    scores_by_subtype: dict[str, list[float]] = defaultdict(list)
    for record in support_records:
        subtype_status_counts[record["subtype"]][record["status"]] += 1
        visual_status_counts[str(record.get("visual_label"))][record["status"]] += 1
        if record["consistency_score"] is not None:
            scores_by_subtype[record["subtype"]].append(float(record["consistency_score"]))

    mean_scores = {
        subtype: sum(values) / len(values)
        for subtype, values in sorted(scores_by_subtype.items())
        if values
    }
    v1_to_v2 = Counter(record["status_transition"] for record in transitions)

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "script_name": Path(__file__).name,
        "rule_version": RULE_VERSION,
        "previous_rule_version": PREVIOUS_RULE_VERSION,
        "scan_id": scan_id,
        "artifact_dir": str(artifact_dir),
        "output_dir": str(output_dir),
        "counts": {
            "all_edge_count": len(decisions),
            "support_contact_edge_count": len(support_records),
            "visual_label_count": len(visual_labels),
            "review_count": len(review),
            "geometry_quality_uncertain_count": subtype_counts["geometry_quality_uncertain"],
            "visually_plausible_v2_violation_count": len(visually_plausible_violations),
        },
        "support_contact_status_counts": count_dict(support_status_counts),
        "support_subtype_counts": count_dict(subtype_counts),
        "support_subtype_status_counts": nested_count_dict(subtype_status_counts),
        "visual_label_to_v2_status_counts": nested_count_dict(visual_status_counts),
        "v1_to_v2_status_transitions": count_dict(v1_to_v2),
        "mean_consistency_score_by_subtype": mean_scores,
        "diagnostic_metrics": {
            "violation_rate_on_support_contact": (
                support_status_counts["violated"] / len(support_records)
                if support_records
                else None
            ),
            "uncertain_rate_on_support_contact": (
                support_status_counts["uncertain"] / len(support_records)
                if support_records
                else None
            ),
            "visually_plausible_violation_count": len(visually_plausible_violations),
        },
        "threshold_config": thresholds,
        "ply_stats": ply_stats,
        "output_paths": {name: str(path) for name, path in outputs.items()},
        "validation": {
            "passed": not errors,
            "errors": errors,
            "warnings": warnings,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Verifier v2 Report",
        "",
        f"Created at: `{summary['created_at']}`",
        f"Scan id: `{summary['scan_id']}`",
        "",
        "## Role",
        "",
        "`h001-verifier-v2` is a subtype-aware support/contact smoke-test verifier.",
        "It is not benchmark evidence.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| all edges | {summary['counts']['all_edge_count']} |",
        f"| support/contact edges | {summary['counts']['support_contact_edge_count']} |",
        f"| review count | {summary['counts']['review_count']} |",
        f"| visually plausible v2 violations | {summary['counts']['visually_plausible_v2_violation_count']} |",
        "",
        "## Support Status",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status, count in summary["support_contact_status_counts"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Subtypes", "", "| Subtype | Count |", "| --- | ---: |"])
    for subtype, count in summary["support_subtype_counts"].items():
        lines.append(f"| `{subtype}` | {count} |")
    lines.extend(["", "## Transitions", "", "| Transition | Count |", "| --- | ---: |"])
    for transition, count in summary["v1_to_v2_status_transitions"].items():
        lines.append(f"| `{transition}` | {count} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Inference:",
            "",
            "v2 should be judged by whether it reduces visually plausible false violations while preserving inspectable support/contact evidence.",
            "",
            "## Validation",
            "",
            f"- passed: `{summary['validation']['passed']}`",
            f"- errors: `{len(summary['validation']['errors'])}`",
            f"- warnings: `{len(summary['validation']['warnings'])}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def infer_scan_id(artifact_dir: Path, records: list[dict[str, Any]], explicit: str | None) -> str:
    if explicit:
        return explicit
    scan_ids = {str(record.get("scan_id")) for record in records if record.get("scan_id")}
    if len(scan_ids) == 1:
        return next(iter(scan_ids))
    return artifact_dir.name


def main() -> None:
    args = parse_args()
    artifact_dir = args.artifact_dir
    v1_path = artifact_dir / "v1_decisions.jsonl"
    point_path = artifact_dir / "point_evidence.jsonl"
    thresholds_path = artifact_dir / "thresholds.json"
    visual_path = artifact_dir / "visual_inspection" / "labels.jsonl"

    v1_edges = read_jsonl(v1_path)
    point_records = read_jsonl(point_path)
    visual_labels = load_visual_labels(visual_path)
    source_thresholds = load_json(thresholds_path)
    scan_id = infer_scan_id(artifact_dir, v1_edges, args.scan_id)
    thresholds = {
        **DEFAULT_THRESHOLDS,
        "source_threshold_config": source_thresholds,
    }

    point_by_edge = {record["edge_id"]: record for record in point_records}
    support_edges = [
        edge for edge in v1_edges if edge.get("predicate_family") == "support_contact"
    ]
    object_ids = {
        int(edge["subject_id"]) for edge in support_edges
    } | {
        int(edge["object_id"]) for edge in support_edges
    }
    ply_path = (
        args.dataset_root
        / "3RScan"
        / "scans"
        / scan_id
        / "labels.instances.annotated.v2.ply"
    )
    points_by_object, ply_stats = read_target_points(ply_path, object_ids)

    output_dir = artifact_dir / "v2"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "decisions": output_dir / "decisions.jsonl",
        "support": output_dir / "support.jsonl",
        "transitions": output_dir / "transitions.jsonl",
        "review": output_dir / "review.jsonl",
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
    }

    decisions: list[dict[str, Any]] = []
    support_records: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []

    for edge in v1_edges:
        clean_edge = {key: value for key, value in edge.items() if not key.startswith("_")}
        if clean_edge.get("predicate_family") != "support_contact":
            clean_edge["verification"] = carried_verification_object(clean_edge, thresholds)
            decisions.append(clean_edge)
            continue

        point_record = point_by_edge.get(str(clean_edge.get("edge_id")))
        visual_label = visual_labels.get(str(clean_edge.get("edge_id")))
        support_record = support_v2_record(
            clean_edge,
            point_record,
            visual_label,
            points_by_object,
            thresholds,
        )
        clean_edge["verification"] = support_verification_object(
            clean_edge,
            support_record,
            thresholds,
        )
        support_records.append(support_record)
        transitions.append(make_transition(clean_edge, support_record))
        if support_record["status"] != "satisfied" or support_record["subtype"] == "geometry_quality_uncertain":
            review.append(make_review_record(clean_edge, support_record))
        decisions.append(clean_edge)

    summary = summarize(
        artifact_dir=artifact_dir,
        output_dir=output_dir,
        outputs=outputs,
        scan_id=scan_id,
        decisions=decisions,
        support_records=support_records,
        transitions=transitions,
        review=review,
        visual_labels=visual_labels,
        ply_stats=ply_stats,
        thresholds=thresholds,
    )

    write_jsonl(outputs["decisions"], decisions)
    write_jsonl(outputs["support"], support_records)
    write_jsonl(outputs["transitions"], transitions)
    write_jsonl(outputs["review"], review)
    write_json(outputs["summary"], summary)
    write_report(outputs["report"], summary)

    if not summary["validation"]["passed"]:
        raise SystemExit(f"validation_failed:{summary['validation']['errors']}")


if __name__ == "__main__":
    main()
