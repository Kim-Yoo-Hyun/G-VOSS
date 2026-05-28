#!/usr/bin/env python3
"""Run a small evidence-only dry run for attachment-deferred rows.

This script intentionally does not assign verification status, p_geom_valid,
recall credit, or reranking scores. It only emits rows matching the frozen
attachment-deferred evidence extractor contract.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h001_attachment_deferred_extractor_dry_run_v1"
ROW_SCHEMA_VERSION = "h001_attachment_deferred_evidence_row_v1"
EXTRACTOR_VERSION = "h001_attachment_deferred_extractor_dry_run_v1"
STATUS = "attachment_deferred_extractor_dry_run_ready_no_verifier"
TARGET_FAMILY = "attachment_deferred"
PREDICATE_LABELS = ("attached to", "hanging on", "connected to")
FORBIDDEN_OUTPUT_FIELDS = {
    "verification_status",
    "p_geom_valid",
    "satisfied",
    "violated",
    "recall_credit",
    "reranked_score",
}

HYPOTHESIS_ROOT = Path("hypothesis/CAND-001/H001_geometry-grounded-verification")
HARDENED_ROOT = HYPOTHESIS_ROOT / "artifacts/evaluation/vlsat_closed_set/hardened"
HARDENED_GEOM_ROOT = HYPOTHESIS_ROOT / "artifacts/evaluation/vlsat_closed_set/hardened_geometry"
EXPERIMENT_ROOT = Path("experiments/H001_geom_reliability")

WALL_LABELS = {"wall", "window", "door", "doorframe"}
CEILING_LABELS = {"ceiling"}
FLOOR_LABELS = {"floor"}
FURNITURE_LABELS = {
    "table",
    "desk",
    "counter",
    "kitchen counter",
    "shelf",
    "cabinet",
    "sofa",
    "chair",
    "bed",
    "stool",
    "bench",
    "wardrobe",
}
FIXTURE_LABELS = {
    "picture",
    "tv",
    "monitor",
    "lamp",
    "curtain",
    "mirror",
    "sink",
    "toilet",
    "radiator",
    "light",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def finite(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def vector_sub(a: list[float], b: list[float]) -> list[float]:
    return [a[idx] - b[idx] for idx in range(3)]


def euclidean(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def interval_intersection(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def volume(a_min: list[float], a_max: list[float], dims: tuple[int, ...]) -> float:
    result = 1.0
    for dim in dims:
        result *= max(0.0, a_max[dim] - a_min[dim])
    return result


def safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def as_float_list(value: Any, expected_len: int) -> list[float] | None:
    if not isinstance(value, list) or len(value) != expected_len:
        return None
    result = [finite(item) for item in value]
    if any(item is None for item in result):
        return None
    return [float(item) for item in result if item is not None]


def derive_aabb_from_obb(item: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    obb = item.get("obb", {})
    centroid = as_float_list(obb.get("centroid"), 3)
    axes_lengths = as_float_list(obb.get("axesLengths"), 3)
    normalized_axes = as_float_list(obb.get("normalizedAxes"), 9)
    warnings: list[str] = []
    if centroid is None:
        return None, ["missing_or_invalid_centroid"]
    if axes_lengths is None:
        return None, ["missing_or_invalid_axes_lengths"]
    if normalized_axes is None:
        return None, ["missing_or_invalid_normalized_axes"]
    if any(length <= 0 for length in axes_lengths):
        return None, ["non_positive_axes_length"]

    rows = [normalized_axes[0:3], normalized_axes[3:6], normalized_axes[6:9]]
    for idx, row in enumerate(rows):
        norm = euclidean(row)
        if abs(norm - 1.0) > 0.05:
            warnings.append(f"obb_axis_{idx}_norm_{norm:.4f}")

    half_lengths = [length / 2.0 for length in axes_lengths]
    half_extent_world = [
        sum(abs(rows[i][j]) * half_lengths[j] for j in range(3))
        for i in range(3)
    ]
    aabb_min = [centroid[i] - half_extent_world[i] for i in range(3)]
    aabb_max = [centroid[i] + half_extent_world[i] for i in range(3)]
    size_xyz = [aabb_max[i] - aabb_min[i] for i in range(3)]
    if any(size <= 0 for size in size_xyz):
        return None, warnings + ["non_positive_aabb_extent"]

    normal = as_float_list(item.get("dominantNormal"), 3)
    return {
        "object_label": str(item.get("label") or ""),
        "center_xyz": centroid,
        "aabb_min_xyz": aabb_min,
        "aabb_max_xyz": aabb_max,
        "size_xyz": size_xyz,
        "height_z": size_xyz[2],
        "diag_3d": euclidean(size_xyz),
        "diag_xy": math.sqrt(size_xyz[0] * size_xyz[0] + size_xyz[1] * size_xyz[1]),
        "dominant_normal": normal,
    }, warnings


def load_scan_geometries(dataset_root: Path, scan_id: str) -> tuple[dict[int, dict[str, Any]], list[str], list[str]]:
    semseg_path = dataset_root / "3RScan" / "scans" / scan_id / "semseg.v2.json"
    if not semseg_path.exists():
        return {}, [], [f"missing_semseg:{scan_id}:{semseg_path}"]
    payload = read_json(semseg_path)
    geometries: dict[int, dict[str, Any]] = {}
    warnings: list[str] = []
    errors: list[str] = []
    for item in payload.get("segGroups", []):
        try:
            object_id = int(item["objectId"])
        except (KeyError, TypeError, ValueError):
            warnings.append("invalid_object_id_in_semseg")
            continue
        geometry, geom_warnings = derive_aabb_from_obb(item)
        if geometry is None:
            warnings.append(f"invalid_obb:{scan_id}:{object_id}:{','.join(geom_warnings)}")
            continue
        geometries[object_id] = geometry
        warnings.extend(f"obb_warning:{scan_id}:{object_id}:{warning}" for warning in geom_warnings)
    if not geometries:
        errors.append(f"zero_valid_geometries:{scan_id}")
    return geometries, warnings, errors


def compute_obb_features(subject: dict[str, Any], obj: dict[str, Any]) -> dict[str, float | None]:
    s_min = subject["aabb_min_xyz"]
    s_max = subject["aabb_max_xyz"]
    o_min = obj["aabb_min_xyz"]
    o_max = obj["aabb_max_xyz"]
    delta = vector_sub(subject["center_xyz"], obj["center_xyz"])
    distance_3d = euclidean(delta)
    distance_xy = math.sqrt(delta[0] * delta[0] + delta[1] * delta[1])
    mean_diag_3d = (subject["diag_3d"] + obj["diag_3d"]) / 2.0
    mean_diag_xy = (subject["diag_xy"] + obj["diag_xy"]) / 2.0
    inter_xy = interval_intersection(s_min[0], s_max[0], o_min[0], o_max[0]) * interval_intersection(
        s_min[1], s_max[1], o_min[1], o_max[1]
    )
    subject_xy_area = volume(s_min, s_max, (0, 1))
    object_xy_area = volume(o_min, o_max, (0, 1))
    projected_overlap = max(
        safe_div(inter_xy, subject_xy_area) or 0.0,
        safe_div(inter_xy, object_xy_area) or 0.0,
    )
    return {
        "distance_3d_m": distance_3d,
        "distance_xy_m": distance_xy,
        "normalized_distance_3d": safe_div(distance_3d, mean_diag_3d),
        "normalized_distance_xy": safe_div(distance_xy, mean_diag_xy),
        "projected_xy_overlap": projected_overlap,
        "vertical_gap_m": s_min[2] - o_max[2],
        "center_delta_z_m": delta[2],
    }


def aabb_gap(subject: dict[str, Any], obj: dict[str, Any]) -> float:
    gaps = []
    for dim in range(3):
        s_min = subject["aabb_min_xyz"][dim]
        s_max = subject["aabb_max_xyz"][dim]
        o_min = obj["aabb_min_xyz"][dim]
        o_max = obj["aabb_max_xyz"][dim]
        gaps.append(max(0.0, max(o_min - s_max, s_min - o_max)))
    return euclidean(gaps)


def label_norm(value: Any) -> str:
    return str(value or "").strip().lower()


def surface_type(label: str) -> str:
    normalized = label_norm(label)
    if normalized in WALL_LABELS:
        return "wall"
    if normalized in CEILING_LABELS:
        return "ceiling"
    if normalized in FLOOR_LABELS:
        return "floor"
    if normalized in FURNITURE_LABELS:
        return "furniture"
    if normalized in FIXTURE_LABELS:
        return "fixture"
    return "unknown"


def normal_class(normal: list[float] | None) -> str:
    if normal is None or len(normal) != 3:
        return "unknown"
    z_value = normal[2]
    if z_value >= 0.75:
        return "horizontal_up"
    if z_value <= -0.75:
        return "horizontal_down"
    if abs(z_value) <= 0.35:
        return "vertical"
    return "slanted"


def subtype_hint(predicate_label: str, obj_geom: dict[str, Any], features: dict[str, Any]) -> str:
    s_type = surface_type(obj_geom.get("object_label", ""))
    n_class = normal_class(obj_geom.get("dominant_normal"))
    norm_distance = features.get("normalized_distance_3d")
    near = norm_distance is not None and norm_distance <= 1.0
    if predicate_label == "attached to":
        if s_type in {"wall", "ceiling"} or n_class in {"vertical", "horizontal_down"}:
            return "attached_to_vertical_or_overhead_surface"
        if s_type in {"furniture", "fixture"}:
            return "attached_to_furniture_or_fixture"
        return "ambiguous_functional_attachment"
    if predicate_label == "hanging on":
        if s_type == "ceiling" or n_class == "horizontal_down":
            return "hanging_from_overhead_or_fixture"
        if s_type == "wall" or n_class == "vertical":
            return "hanging_from_vertical_surface"
        return "ambiguous_draped_or_occluded_hanging"
    if predicate_label == "connected to":
        if near:
            return "connected_adjacent_or_contiguous"
        if s_type in {"fixture", "furniture"}:
            return "connected_by_fixture_or_part"
        return "ambiguous_functional_connection"
    return "unknown"


def class_pair_prior(subject_label: str | None, object_label: str | None, predicate_label: str) -> str:
    subj = label_norm(subject_label)
    obj = label_norm(object_label)
    if predicate_label == "attached to":
        if obj in WALL_LABELS | CEILING_LABELS | FURNITURE_LABELS | FIXTURE_LABELS:
            return "plausible"
        if obj in FLOOR_LABELS:
            return "implausible"
    if predicate_label == "hanging on":
        if obj in WALL_LABELS | CEILING_LABELS | FIXTURE_LABELS or subj in {"curtain", "clothes", "towel", "picture"}:
            return "plausible"
        if obj in FLOOR_LABELS:
            return "implausible"
    if predicate_label == "connected to":
        if obj in WALL_LABELS | FURNITURE_LABELS | FIXTURE_LABELS or subj in FIXTURE_LABELS:
            return "plausible"
    return "unknown"


def support_proxy(subject: dict[str, Any], geometries: dict[int, dict[str, Any]]) -> tuple[bool | None, float | None, list[str]]:
    subject_bottom = subject["aabb_min_xyz"][2]
    best_score = 0.0
    reasons: list[str] = []
    for object_id, obj in geometries.items():
        if obj is subject:
            continue
        obj_label = label_norm(obj.get("object_label"))
        if obj_label not in FLOOR_LABELS | FURNITURE_LABELS:
            continue
        vertical_gap = abs(subject_bottom - obj["aabb_max_xyz"][2])
        inter_xy = interval_intersection(subject["aabb_min_xyz"][0], subject["aabb_max_xyz"][0], obj["aabb_min_xyz"][0], obj["aabb_max_xyz"][0]) * interval_intersection(
            subject["aabb_min_xyz"][1], subject["aabb_max_xyz"][1], obj["aabb_min_xyz"][1], obj["aabb_max_xyz"][1]
        )
        subj_area = volume(subject["aabb_min_xyz"], subject["aabb_max_xyz"], (0, 1))
        overlap = safe_div(inter_xy, subj_area) or 0.0
        if vertical_gap <= 0.20 and overlap > 0:
            score = clamp((0.20 - vertical_gap) / 0.20) * clamp(overlap)
            if score > best_score:
                best_score = score
                reasons = [f"near_{obj_label}_support_proxy:{object_id}"]
    if best_score > 0:
        return True, round(best_score, 4), reasons
    return False, 0.0, []


def row_family(row: dict[str, Any]) -> str | None:
    if "predicate_family" in row:
        return row.get("predicate_family")
    predicate = row.get("predicate")
    if isinstance(predicate, dict):
        return predicate.get("predicate_family")
    return None


def row_label(row: dict[str, Any]) -> str | None:
    if "predicate_label" in row:
        return row.get("predicate_label")
    predicate = row.get("predicate")
    if isinstance(predicate, dict):
        return predicate.get("predicate_label")
    return None


def row_edge(row: dict[str, Any]) -> dict[str, Any]:
    if isinstance(row.get("edge"), dict):
        return row["edge"]
    return row


def normalize_input_row(row: dict[str, Any], source_name: str) -> dict[str, Any]:
    edge = row_edge(row)
    label = row_label(row)
    return {
        "source_name": source_name,
        "scan_id": str(row.get("scan_id")),
        "subgraph_id": str(row.get("subgraph_id")),
        "subject_id": int(edge.get("subject_id")),
        "object_id": int(edge.get("object_id")),
        "subject_label": edge.get("subject_label"),
        "object_label": edge.get("object_label"),
        "predicate_label": str(label),
    }


def selected_rows_by_label(path: Path, source_name: str, limit_per_label: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for row in iter_jsonl(path):
        if row_family(row) != TARGET_FAMILY:
            continue
        label = row_label(row)
        if label not in PREDICATE_LABELS or counts[label] >= limit_per_label:
            continue
        rows.append(normalize_input_row(row, source_name))
        counts[label] += 1
        if all(counts[label] >= limit_per_label for label in PREDICATE_LABELS):
            break
    return rows


def make_counterfactuals(
    gt_rows: list[dict[str, Any]],
    *,
    dataset_root: Path,
    limit_per_label: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    geometry_cache: dict[str, tuple[dict[int, dict[str, Any]], list[str], list[str]]] = {}
    for row in gt_rows:
        label = row["predicate_label"]
        if counts[label] >= limit_per_label:
            continue
        scan_id = row["scan_id"]
        if scan_id not in geometry_cache:
            geometry_cache[scan_id] = load_scan_geometries(dataset_root, scan_id)
        geometries, _warnings, errors = geometry_cache[scan_id]
        if errors or row["subject_id"] not in geometries:
            continue
        subject = geometries[row["subject_id"]]
        candidates = [
            (euclidean(vector_sub(subject["center_xyz"], geom["center_xyz"])), object_id, geom)
            for object_id, geom in geometries.items()
            if object_id not in {row["subject_id"], row["object_id"]}
        ]
        if not candidates:
            continue
        _distance, object_id, object_geom = max(candidates, key=lambda item: item[0])
        counterfactual = dict(row)
        counterfactual["source_name"] = "counterfactual"
        counterfactual["object_id"] = int(object_id)
        counterfactual["object_label"] = object_geom.get("object_label")
        rows.append(counterfactual)
        counts[label] += 1
    return rows


def build_evidence_row(
    source_row: dict[str, Any],
    *,
    dataset_root: Path,
    geometry_cache: dict[str, tuple[dict[int, dict[str, Any]], list[str], list[str]]],
) -> tuple[dict[str, Any], list[str]]:
    scan_id = source_row["scan_id"]
    if scan_id not in geometry_cache:
        geometry_cache[scan_id] = load_scan_geometries(dataset_root, scan_id)
    geometries, scan_warnings, scan_errors = geometry_cache[scan_id]
    missing_fields: list[str] = []
    quality_flags: list[str] = []
    notes: list[str] = []
    if scan_warnings:
        quality_flags.extend(scan_warnings[:5])
    if scan_errors:
        quality_flags.extend(scan_errors)

    subject_id = source_row["subject_id"]
    object_id = source_row["object_id"]
    subject_geom = geometries.get(subject_id)
    object_geom = geometries.get(object_id)
    if subject_geom is None:
        missing_fields.append("subject_obb")
    if object_geom is None:
        missing_fields.append("object_obb")

    subject_label = source_row.get("subject_label") or (subject_geom or {}).get("object_label")
    object_label = source_row.get("object_label") or (object_geom or {}).get("object_label")
    predicate_label = source_row["predicate_label"]

    if subject_geom is None or object_geom is None:
        features = {
            "distance_3d_m": None,
            "distance_xy_m": None,
            "normalized_distance_3d": None,
            "normalized_distance_xy": None,
            "projected_xy_overlap": None,
            "vertical_gap_m": None,
            "center_delta_z_m": None,
        }
        extractor_status = "missing_geometry"
        selected_surface_type = "unknown"
        selected_normal_class = "unknown"
        candidates: list[dict[str, Any]] = []
        floor_clearance = None
        near_vertical_or_overhead = None
        hanging_score = None
        floor_supported = None
        support_score = None
        support_reasons: list[str] = []
        subtype = "unknown"
    else:
        features = compute_obb_features(subject_geom, object_geom)
        extractor_status = "partial"
        selected_surface_type = surface_type(object_label or object_geom.get("object_label"))
        selected_normal_class = normal_class(object_geom.get("dominant_normal"))
        gap = aabb_gap(subject_geom, object_geom)
        candidates = [
            {
                "surface_id": f"object:{object_id}",
                "surface_type": selected_surface_type,
                "normal_class": selected_normal_class,
                "normal_xyz": object_geom.get("dominant_normal"),
                "distance_m": gap,
                "projected_overlap_ratio": features["projected_xy_overlap"],
                "point_contact_count": None,
                "evidence_source": "obb_plane_proxy",
            }
        ]
        scene_floor_z = min((geom["aabb_min_xyz"][2] for geom in geometries.values()), default=None)
        floor_clearance = (
            subject_geom["aabb_min_xyz"][2] - scene_floor_z if scene_floor_z is not None else None
        )
        near_vertical_or_overhead = selected_normal_class in {"vertical", "horizontal_down"} or selected_surface_type in {"wall", "ceiling"}
        if predicate_label == "hanging on" and floor_clearance is not None:
            hanging_score = round(clamp((floor_clearance - 0.05) / 1.0) if near_vertical_or_overhead else 0.0, 4)
        else:
            hanging_score = 0.0
        floor_supported, support_score, support_reasons = support_proxy(subject_geom, geometries)
        subtype = subtype_hint(predicate_label, object_geom, features)
        missing_fields.extend(["segmented_points", "point_contact_evidence"])
        quality_flags.append("dry_run_obb_only_no_point_contact")
        notes.append("Dry run uses semseg OBB and dominantNormal only; no verifier decision is emitted.")

    if not candidates:
        missing_fields.append("surface_candidates")
    if selected_normal_class == "unknown":
        missing_fields.append("surface_normal")

    row_id = (
        f"{source_row['source_name']}::{scan_id}::{source_row['subgraph_id']}::"
        f"{subject_id}::{object_id}::{predicate_label}"
    )
    return {
        "schema_version": ROW_SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "row_id": row_id,
        "source_name": source_row["source_name"],
        "scan_id": scan_id,
        "subgraph_id": source_row["subgraph_id"],
        "subject_id": subject_id,
        "object_id": object_id,
        "subject_label": subject_label,
        "object_label": object_label,
        "predicate_label": predicate_label,
        "predicate_family": TARGET_FAMILY,
        "extractor_status": extractor_status,
        "subtype_hint": subtype,
        "geometry_available": {
            "obb": subject_geom is not None and object_geom is not None,
            "points": False,
            "surface_candidates": bool(candidates),
            "normals": selected_normal_class != "unknown",
        },
        "obb_evidence": features,
        "point_contact_evidence": {
            "subject_point_count": None,
            "object_point_count": None,
            "min_point_distance_m": None,
            "near_contact_point_count": None,
            "near_contact_threshold_m": None,
            "contact_patch_extent_m2": None,
            "contact_patch_score": None,
        },
        "surface_evidence": {
            "selected_surface_type": selected_surface_type,
            "selected_surface_normal_class": selected_normal_class,
            "candidate_count": len(candidates),
            "candidates": candidates,
        },
        "gravity_evidence": {
            "floor_clearance_m": floor_clearance,
            "near_vertical_or_overhead_surface": near_vertical_or_overhead,
            "hanging_geometry_score": hanging_score,
        },
        "contradictory_support_evidence": {
            "floor_or_table_supported": floor_supported,
            "support_explanation_score": support_score,
            "reason_codes": support_reasons,
        },
        "affordance_context": {
            "class_pair_prior": class_pair_prior(subject_label, object_label, predicate_label),
            "class_pair_prior_source": "fixed_list",
            "allowed_as_proof": False,
        },
        "quality_flags": sorted(set(quality_flags)),
        "missing_fields": sorted(set(missing_fields)),
        "notes": notes,
    }, quality_flags + missing_fields


def validate_row(row: dict[str, Any], required_fields: list[str], allowed_fields: set[str]) -> list[str]:
    errors: list[str] = []
    missing = [field for field in required_fields if field not in row]
    errors.extend(f"missing_required:{field}" for field in missing)
    extra = [field for field in row if field not in allowed_fields]
    errors.extend(f"extra_field:{field}" for field in extra)
    forbidden = [field for field in FORBIDDEN_OUTPUT_FIELDS if field in row]
    errors.extend(f"forbidden_field:{field}" for field in sorted(forbidden))
    if row.get("predicate_family") != TARGET_FAMILY:
        errors.append("predicate_family_not_attachment_deferred")
    if row.get("predicate_label") not in PREDICATE_LABELS:
        errors.append("predicate_label_not_in_attachment_labels")
    if row.get("affordance_context", {}).get("allowed_as_proof") is not False:
        errors.append("affordance_allowed_as_proof_not_false")
    return errors


def report_md(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    return f"""# Attachment Deferred Extractor Dry Run

Status: `{manifest['status']}`
Created at: `{manifest['created_at']}`

## Claim Boundary

This is a G1b evidence-only dry run. It is not a verifier, not calibration, not
source metric evidence, and not part of the current AAAI main claim.

## Row Counts

| Item | Count |
| --- | ---: |
| input rows | {counts['input_rows']} |
| output rows | {counts['output_rows']} |
| validation errors | {counts['validation_errors']} |

## Source Rows

""" + "\n".join(
        f"- `{source}`: {count}" for source, count in counts["source_counts"].items()
    ) + f"""

## Extractor Status

""" + "\n".join(
        f"- `{status}`: {count}" for status, count in counts["extractor_status_counts"].items()
    ) + f"""

## Important Boundary

The dry run uses semseg OBB and dominantNormal proxies only. Point-contact and
surface-normal estimation from segmented points are not validated yet. The
output intentionally omits `verification_status`, `p_geom_valid`, recall credit,
and reranking scores.

## Next Gate

`{manifest['next_gate']}`
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--dataset-root", type=Path, default=Path("local_dataset"))
    parser.add_argument(
        "--contract-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/attachment_deferred/evidence_extractor"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/attachment_deferred/extractor_dry_run"),
    )
    parser.add_argument("--limit-per-label", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    dataset_root = args.dataset_root if args.dataset_root.is_absolute() else repo_root / args.dataset_root
    contract_dir = args.contract_dir if args.contract_dir.is_absolute() else repo_root / args.contract_dir
    out = args.out if args.out.is_absolute() else repo_root / args.out

    output_schema_path = contract_dir / "output_schema.json"
    field_catalog_path = contract_dir / "field_catalog.json"
    contract_manifest_path = contract_dir / "manifest.json"
    for path in [output_schema_path, field_catalog_path, contract_manifest_path]:
        if not path.exists():
            raise FileNotFoundError(f"missing contract artifact: {path}")

    output_schema = read_json(output_schema_path)
    field_catalog = read_json(field_catalog_path)
    contract_manifest = read_json(contract_manifest_path)
    if contract_manifest.get("status") != "attachment_deferred_extractor_contract_ready_no_extraction":
        raise ValueError(f"unexpected contract status:{contract_manifest.get('status')}")

    gt_path = repo_root / HARDENED_ROOT / "ground_truth.jsonl"
    vlsat_path = repo_root / HARDENED_GEOM_ROOT / "verification.jsonl"
    open3dsg_path = repo_root / EXPERIMENT_ROOT / "sources/open3dsg/geometry/verification.jsonl"
    gt_rows = selected_rows_by_label(gt_path, "gt_positive", args.limit_per_label)
    counterfactual_rows = make_counterfactuals(
        gt_rows,
        dataset_root=dataset_root,
        limit_per_label=args.limit_per_label,
    )
    vlsat_rows = selected_rows_by_label(vlsat_path, "vlsat_closed_set", args.limit_per_label)
    open3dsg_rows = selected_rows_by_label(open3dsg_path, "open3dsg_ov", args.limit_per_label)
    input_rows = gt_rows + counterfactual_rows + vlsat_rows + open3dsg_rows

    required_fields = output_schema["required"]
    allowed_fields = set(output_schema["properties"])
    geometry_cache: dict[str, tuple[dict[int, dict[str, Any]], list[str], list[str]]] = {}
    output_rows: list[dict[str, Any]] = []
    validation_errors: list[dict[str, Any]] = []
    warnings: Counter[str] = Counter()
    for source_row in input_rows:
        output_row, row_warnings = build_evidence_row(
            source_row,
            dataset_root=dataset_root,
            geometry_cache=geometry_cache,
        )
        output_rows.append(output_row)
        for warning in row_warnings:
            warnings[str(warning)] += 1
        errors = validate_row(output_row, required_fields, allowed_fields)
        if errors:
            validation_errors.append({"row_id": output_row.get("row_id"), "errors": errors})

    source_counts = Counter(row["source_name"] for row in output_rows)
    label_counts = Counter(row["predicate_label"] for row in output_rows)
    status_counts = Counter(row["extractor_status"] for row in output_rows)
    surface_counts = Counter(row["surface_evidence"]["selected_surface_type"] for row in output_rows)
    subtype_counts = Counter(row["subtype_hint"] for row in output_rows)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS if not validation_errors else "attachment_deferred_extractor_dry_run_failed_validation",
        "created_at": utc_now(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "artifact_type": "evidence_only_dry_run",
            "metric_evidence": False,
            "verifier_evidence": False,
            "forbidden_outputs_absent": not validation_errors,
        },
        "inputs": {
            "contract_manifest": relpath(repo_root, contract_manifest_path),
            "output_schema": relpath(repo_root, output_schema_path),
            "field_catalog": relpath(repo_root, field_catalog_path),
            "ground_truth_jsonl": relpath(repo_root, gt_path),
            "vlsat_verification_jsonl": relpath(repo_root, vlsat_path),
            "open3dsg_verification_jsonl": relpath(repo_root, open3dsg_path),
            "dataset_root": relpath(repo_root, dataset_root),
        },
        "settings": {
            "limit_per_label": args.limit_per_label,
            "predicate_labels": list(PREDICATE_LABELS),
        },
        "outputs": {
            "rows": "rows.jsonl",
            "summary": "summary.json",
            "validation": "validation.json",
            "report": "report.md",
        },
        "counts": {
            "input_rows": len(input_rows),
            "output_rows": len(output_rows),
            "validation_errors": len(validation_errors),
            "source_counts": dict(sorted(source_counts.items())),
            "label_counts": dict(sorted(label_counts.items())),
            "extractor_status_counts": dict(sorted(status_counts.items())),
            "surface_type_counts": dict(sorted(surface_counts.items())),
            "subtype_hint_counts": dict(sorted(subtype_counts.items())),
        },
        "warning_counts": dict(sorted(warnings.items())),
        "next_gate": "G1c_attachment_point_surface_estimator_validation",
        "blockers": [
            "point_contact_estimator_not_validated",
            "surface_candidate_estimator_not_validated_beyond_obb_proxy",
            "normal_classification_not_validated_beyond_semseg_dominantNormal",
            "attachment_verifier_policy_not_frozen",
            "train_dev_calibration_not_built",
            "source_metrics_not_run",
        ],
    }

    if validation_errors:
        ensure_dir(out)
        write_json(out / "manifest.json", manifest)
        write_json(out / "validation.json", {"status": "failed", "errors": validation_errors})
        raise SystemExit("dry_run_validation_failed")

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": manifest["status"],
        "counts": manifest["counts"],
        "warning_counts": manifest["warning_counts"],
        "forbidden_output_fields": sorted(FORBIDDEN_OUTPUT_FIELDS),
        "contract_forbidden_output_fields": field_catalog.get("forbidden_extractor_outputs", []),
    }
    validation = {
        "status": "passed",
        "checked_rows": len(output_rows),
        "required_field_count": len(required_fields),
        "validation_errors": [],
        "forbidden_output_fields_present": [],
    }

    ensure_dir(out)
    write_jsonl(out / "rows.jsonl", output_rows)
    write_json(out / "summary.json", summary)
    write_json(out / "validation.json", validation)
    write_json(out / "manifest.json", manifest)
    (out / "report.md").write_text(report_md(manifest), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "out": str(out), "rows": len(output_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
