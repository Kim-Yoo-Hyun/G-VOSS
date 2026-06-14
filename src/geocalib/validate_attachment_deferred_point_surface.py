#!/usr/bin/env python3
"""Validate point-contact and surface estimators for attachment-deferred rows.

This is the G1c step for the optional attachment-deferred expansion track. It
updates the G1b evidence-only rows with segmented-point contact and surface
normal evidence, then validates that the output still contains no verifier,
calibration, recall-credit, or reranking fields.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from run_attachment_deferred_extractor_dry_run import (
    FORBIDDEN_OUTPUT_FIELDS,
    PREDICATE_LABELS,
    ROW_SCHEMA_VERSION,
    TARGET_FAMILY,
    ensure_dir,
    iter_jsonl,
    normal_class,
    read_json,
    relpath,
    surface_type,
    utc_now,
    validate_row,
    write_json,
    write_jsonl,
)


SCHEMA_VERSION = "h001_attachment_deferred_point_surface_validation_v1"
EXTRACTOR_VERSION = "h001_attachment_deferred_point_surface_validation_v1"
STATUS_READY = "attachment_deferred_point_surface_validation_ready_no_verifier"
STATUS_PARTIAL = "attachment_deferred_point_surface_validation_partial_no_verifier"
NEXT_GATE_READY = "G2_attachment_verifier_policy_design"
NEXT_GATE_PARTIAL = "G1c_attachment_point_surface_estimator_validation"
DEFAULT_CONTACT_THRESHOLD_M = 0.05
DEFAULT_MAX_POINTS_PER_OBJECT = 5000


def parse_ply_header(path: Path) -> tuple[dict[str, Any], int]:
    properties: list[str] = []
    vertex_count: int | None = None
    face_count: int | None = None
    header_lines = 0
    in_vertex = False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        first_line = handle.readline().strip()
        header_lines += 1
        if first_line != "ply":
            raise ValueError(f"expected_ply_header:{first_line!r}")
        for line in handle:
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


def read_target_points(path: Path, target_ids: set[int]) -> tuple[dict[int, np.ndarray], dict[str, Any]]:
    header, _header_lines = parse_ply_header(path)
    properties = header["properties"]
    for required in ("x", "y", "z", "objectId"):
        if required not in properties:
            raise ValueError(f"missing_ply_property:{required}")
    x_idx = properties.index("x")
    y_idx = properties.index("y")
    z_idx = properties.index("z")
    object_idx = properties.index("objectId")
    max_idx = max(x_idx, y_idx, z_idx, object_idx)

    buffers: dict[int, list[tuple[float, float, float]]] = {object_id: [] for object_id in target_ids}
    rows_read = 0
    rows_kept = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip() == "end_header":
                break
        for _ in range(int(header["vertex_count"])):
            line = handle.readline()
            if not line:
                break
            rows_read += 1
            parts = line.split()
            if len(parts) <= max_idx:
                continue
            object_id = int(parts[object_idx])
            if object_id not in target_ids:
                continue
            buffers[object_id].append((float(parts[x_idx]), float(parts[y_idx]), float(parts[z_idx])))
            rows_kept += 1

    points = {
        object_id: np.asarray(values, dtype=np.float32).reshape((-1, 3))
        for object_id, values in buffers.items()
    }
    stats = {
        "ply_vertex_count_header": header["vertex_count"],
        "ply_face_count_header": header["face_count"],
        "ply_vertex_rows_read": rows_read,
        "target_object_ids": sorted(target_ids),
        "target_vertex_rows_kept": rows_kept,
        "properties": properties,
    }
    return points, stats


def deterministic_sample(points: np.ndarray, max_points: int) -> np.ndarray:
    if len(points) <= max_points:
        return points
    indices = np.linspace(0, len(points) - 1, num=max_points, dtype=np.int64)
    return points[indices]


def estimate_normal(points: np.ndarray, reference_normal: list[float] | None) -> tuple[list[float] | None, str]:
    if len(points) < 3:
        return None, "insufficient_points"
    centered = points - points.mean(axis=0, keepdims=True)
    covariance = np.cov(centered, rowvar=False)
    try:
        values, vectors = np.linalg.eigh(covariance)
    except np.linalg.LinAlgError:
        return None, "eigendecomposition_failed"
    normal = vectors[:, int(np.argmin(values))].astype(float)
    norm = float(np.linalg.norm(normal))
    if norm <= 1e-9:
        return None, "degenerate_normal"
    normal = normal / norm
    if reference_normal and len(reference_normal) == 3:
        ref = np.asarray(reference_normal, dtype=float)
        ref_norm = float(np.linalg.norm(ref))
        if ref_norm > 1e-9 and float(np.dot(normal, ref / ref_norm)) < 0:
            normal = -normal
    elif abs(float(normal[2])) >= 0.75 and normal[2] < 0:
        normal = -normal
    return [round(float(value), 6) for value in normal.tolist()], "pca_segmented_points"


def point_distance_features(
    subject_points: np.ndarray,
    object_points: np.ndarray,
    *,
    contact_threshold_m: float,
    max_points_per_object: int,
) -> dict[str, Any]:
    subject_sample = deterministic_sample(subject_points, max_points_per_object)
    object_sample = deterministic_sample(object_points, max_points_per_object)
    if len(subject_sample) == 0 or len(object_sample) == 0:
        return {
            "min_point_distance_m": None,
            "near_contact_point_count": None,
            "contact_patch_extent_m2": None,
            "contact_patch_score": None,
            "sampled_subject_points": int(len(subject_sample)),
            "sampled_object_points": int(len(object_sample)),
            "sampled": len(subject_points) > max_points_per_object or len(object_points) > max_points_per_object,
        }

    best_distances = np.full((len(subject_sample),), np.inf, dtype=np.float64)
    min_distance = math.inf
    chunk = 512
    for start in range(0, len(subject_sample), chunk):
        subject_chunk = subject_sample[start : start + chunk].astype(np.float64)
        deltas = subject_chunk[:, None, :] - object_sample[None, :, :].astype(np.float64)
        distances = np.sqrt(np.sum(deltas * deltas, axis=2))
        chunk_min = distances.min(axis=1)
        best_distances[start : start + len(chunk_min)] = chunk_min
        min_distance = min(min_distance, float(chunk_min.min()))

    near_mask = best_distances <= contact_threshold_m
    near_points = subject_sample[near_mask]
    near_count = int(near_mask.sum())
    patch_extent = None
    if len(near_points) >= 2:
        spans = np.ptp(near_points.astype(np.float64), axis=0)
        largest_two = sorted([float(value) for value in spans], reverse=True)[:2]
        patch_extent = largest_two[0] * largest_two[1]
    elif len(near_points) == 1:
        patch_extent = 0.0

    distance_score = max(0.0, min(1.0, (contact_threshold_m - min_distance) / contact_threshold_m))
    count_score = max(0.0, min(1.0, near_count / 25.0))
    contact_score = 0.5 * distance_score + 0.5 * count_score if math.isfinite(min_distance) else None

    return {
        "min_point_distance_m": round(float(min_distance), 6) if math.isfinite(min_distance) else None,
        "near_contact_point_count": near_count,
        "contact_patch_extent_m2": round(float(patch_extent), 6) if patch_extent is not None else None,
        "contact_patch_score": round(float(contact_score), 6) if contact_score is not None else None,
        "sampled_subject_points": int(len(subject_sample)),
        "sampled_object_points": int(len(object_sample)),
        "sampled": len(subject_points) > max_points_per_object or len(object_points) > max_points_per_object,
    }


def dry_reference_normal(row: dict[str, Any]) -> list[float] | None:
    candidates = row.get("surface_evidence", {}).get("candidates", [])
    if not candidates:
        return None
    normal = candidates[0].get("normal_xyz")
    if isinstance(normal, list) and len(normal) == 3:
        try:
            return [float(value) for value in normal]
        except (TypeError, ValueError):
            return None
    return None


def update_row_with_points(
    row: dict[str, Any],
    *,
    points_by_object: dict[int, np.ndarray],
    scan_stats: dict[str, Any],
    contact_threshold_m: float,
    max_points_per_object: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = json.loads(json.dumps(row))
    subject_id = int(updated["subject_id"])
    object_id = int(updated["object_id"])
    subject_points = points_by_object.get(subject_id, np.empty((0, 3), dtype=np.float32))
    object_points = points_by_object.get(object_id, np.empty((0, 3), dtype=np.float32))
    subject_count = int(len(subject_points))
    object_count = int(len(object_points))
    distance_features = point_distance_features(
        subject_points,
        object_points,
        contact_threshold_m=contact_threshold_m,
        max_points_per_object=max_points_per_object,
    )
    reference_normal = dry_reference_normal(updated)
    sampled_object_points = deterministic_sample(object_points, max_points_per_object)
    point_normal, normal_source = estimate_normal(sampled_object_points, reference_normal)
    point_normal_class = normal_class(point_normal)

    selected_surface_type = surface_type(updated.get("object_label"))
    if selected_surface_type == "unknown":
        selected_surface_type = updated["surface_evidence"]["selected_surface_type"]

    point_ready = (
        subject_count > 0
        and object_count > 0
        and distance_features["min_point_distance_m"] is not None
        and point_normal is not None
    )
    missing_fields = set(updated.get("missing_fields", []))
    quality_flags = set(updated.get("quality_flags", []))
    notes = [
        note
        for note in updated.get("notes", [])
        if "Dry run uses semseg OBB" not in note
    ]
    quality_flags.discard("dry_run_obb_only_no_point_contact")
    missing_fields.discard("segmented_points")
    missing_fields.discard("point_contact_evidence")
    missing_fields.discard("surface_normal")

    if subject_count <= 0:
        missing_fields.add("subject_segmented_points")
    if object_count <= 0:
        missing_fields.add("object_segmented_points")
    if point_normal is None:
        missing_fields.add("surface_normal")
    if distance_features["min_point_distance_m"] is None:
        missing_fields.add("point_contact_evidence")

    if point_ready:
        extractor_status = "ready"
        quality_flags.add("point_surface_estimator_validated")
    elif subject_count <= 0 or object_count <= 0:
        extractor_status = "missing_points"
        quality_flags.add("missing_segmented_endpoint_points")
    else:
        extractor_status = "partial"
        quality_flags.add("point_surface_estimator_partial")

    near_count = distance_features["near_contact_point_count"]
    if near_count is not None and near_count > 0:
        quality_flags.add("point_contact_within_threshold")
    elif distance_features["min_point_distance_m"] is not None:
        quality_flags.add("point_contact_beyond_threshold")
    if distance_features["sampled"]:
        quality_flags.add("deterministic_point_sampling_applied")
    if normal_source == "pca_segmented_points":
        quality_flags.add("surface_normal_from_segmented_points")

    updated["extractor_version"] = EXTRACTOR_VERSION
    updated["extractor_status"] = extractor_status
    updated["geometry_available"] = {
        "obb": bool(updated.get("geometry_available", {}).get("obb")),
        "points": subject_count > 0 and object_count > 0,
        "surface_candidates": point_normal is not None or bool(updated["surface_evidence"].get("candidates")),
        "normals": point_normal is not None,
    }
    updated["point_contact_evidence"] = {
        "subject_point_count": subject_count,
        "object_point_count": object_count,
        "min_point_distance_m": distance_features["min_point_distance_m"],
        "near_contact_point_count": distance_features["near_contact_point_count"],
        "near_contact_threshold_m": contact_threshold_m,
        "contact_patch_extent_m2": distance_features["contact_patch_extent_m2"],
        "contact_patch_score": distance_features["contact_patch_score"],
    }
    updated["surface_evidence"] = {
        "selected_surface_type": selected_surface_type,
        "selected_surface_normal_class": point_normal_class,
        "candidate_count": 1 if selected_surface_type != "unknown" or point_normal is not None else 0,
        "candidates": [
            {
                "surface_id": f"object:{object_id}",
                "surface_type": selected_surface_type,
                "normal_class": point_normal_class,
                "normal_xyz": point_normal,
                "distance_m": distance_features["min_point_distance_m"],
                "projected_overlap_ratio": updated["obb_evidence"].get("projected_xy_overlap"),
                "point_contact_count": distance_features["near_contact_point_count"],
                "evidence_source": "segmented_points" if point_ready else "missing",
            }
        ],
    }
    notes.append(
        "G1c validates segmented-point contact and PCA surface-normal evidence; no verifier decision is emitted."
    )
    updated["quality_flags"] = sorted(quality_flags)
    updated["missing_fields"] = sorted(missing_fields)
    updated["notes"] = notes

    diagnostic = {
        "row_id": updated["row_id"],
        "scan_id": updated["scan_id"],
        "source_name": updated["source_name"],
        "predicate_label": updated["predicate_label"],
        "subject_id": subject_id,
        "object_id": object_id,
        "subject_point_count": subject_count,
        "object_point_count": object_count,
        "sampled_subject_points": distance_features["sampled_subject_points"],
        "sampled_object_points": distance_features["sampled_object_points"],
        "min_point_distance_m": distance_features["min_point_distance_m"],
        "near_contact_point_count": distance_features["near_contact_point_count"],
        "contact_patch_extent_m2": distance_features["contact_patch_extent_m2"],
        "contact_patch_score": distance_features["contact_patch_score"],
        "surface_type": selected_surface_type,
        "surface_normal_class": point_normal_class,
        "surface_normal_source": normal_source,
        "dry_run_surface_normal_class": row.get("surface_evidence", {}).get("selected_surface_normal_class"),
        "dry_run_surface_type": row.get("surface_evidence", {}).get("selected_surface_type"),
        "extractor_status": extractor_status,
        "ply_vertex_rows_read": scan_stats.get("ply_vertex_rows_read"),
        "target_vertex_rows_kept": scan_stats.get("target_vertex_rows_kept"),
    }
    return updated, diagnostic


def count_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: value for key, value in sorted(counter.items())}


def nested_count_dict(counter: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: count_dict(value) for key, value in sorted(counter.items())}


def report_md(manifest: dict[str, Any], summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    lines = [
        "# Attachment Deferred Point/Surface Validation",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This is the G1c point/surface estimator validation step. It is not a",
        "verifier, not calibration, not source metric evidence, and not part of",
        "the current AAAI main claim.",
        "",
        "## Row Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| input rows | {counts['input_rows']} |",
        f"| output rows | {counts['output_rows']} |",
        f"| validation errors | {counts['validation_errors']} |",
        f"| ready rows | {counts['ready_rows']} |",
        f"| point available rows | {counts['point_available_rows']} |",
        f"| normal available rows | {counts['normal_available_rows']} |",
        f"| near-contact rows | {counts['near_contact_rows']} |",
        "",
        "## Source Rows",
        "",
    ]
    for source, count in counts["source_counts"].items():
        lines.append(f"- `{source}`: {count}")

    lines.extend(["", "## Extractor Status", ""])
    for status, count in counts["extractor_status_counts"].items():
        lines.append(f"- `{status}`: {count}")

    lines.extend(["", "## Surface Normal Classes", ""])
    for status, count in counts["surface_normal_class_counts"].items():
        lines.append(f"- `{status}`: {count}")

    lines.extend(
        [
            "",
            "## Important Boundary",
            "",
            "Rows with point contact are still evidence rows only. They intentionally",
            "omit `verification_status`, `p_geom_valid`, recall credit, and reranking",
            "scores. A later G2 verifier-policy document must define satisfied,",
            "violated, and uncertain states before any source metrics are run.",
            "",
            "## Next Gate",
            "",
            f"`{manifest['next_gate']}`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--dataset-root", type=Path, default=Path("local_dataset"))
    parser.add_argument(
        "--dry-run-dir",
        type=Path,
        default=Path("archive/experiments/H001_geom_reliability/sources/attachment_deferred/extractor_dry_run"),
    )
    parser.add_argument(
        "--contract-dir",
        type=Path,
        default=Path("archive/experiments/H001_geom_reliability/sources/attachment_deferred/evidence_extractor"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("archive/experiments/H001_geom_reliability/sources/attachment_deferred/point_surface_validation"),
    )
    parser.add_argument("--contact-threshold-m", type=float, default=DEFAULT_CONTACT_THRESHOLD_M)
    parser.add_argument("--max-points-per-object", type=int, default=DEFAULT_MAX_POINTS_PER_OBJECT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    dataset_root = args.dataset_root if args.dataset_root.is_absolute() else repo_root / args.dataset_root
    dry_run_dir = args.dry_run_dir if args.dry_run_dir.is_absolute() else repo_root / args.dry_run_dir
    contract_dir = args.contract_dir if args.contract_dir.is_absolute() else repo_root / args.contract_dir
    out = args.out if args.out.is_absolute() else repo_root / args.out

    dry_manifest_path = dry_run_dir / "manifest.json"
    dry_rows_path = dry_run_dir / "rows.jsonl"
    output_schema_path = contract_dir / "output_schema.json"
    for path in [dry_manifest_path, dry_rows_path, output_schema_path]:
        if not path.exists():
            raise FileNotFoundError(f"missing input artifact: {path}")

    dry_manifest = read_json(dry_manifest_path)
    if dry_manifest.get("status") != "attachment_deferred_extractor_dry_run_ready_no_verifier":
        raise ValueError(f"unexpected dry-run status:{dry_manifest.get('status')}")
    output_schema = read_json(output_schema_path)
    required_fields = output_schema["required"]
    allowed_fields = set(output_schema["properties"])

    dry_rows = list(iter_jsonl(dry_rows_path))
    scan_object_ids: dict[str, set[int]] = defaultdict(set)
    for row in dry_rows:
        scan_object_ids[str(row["scan_id"])].update([int(row["subject_id"]), int(row["object_id"])])

    scan_points: dict[str, dict[int, np.ndarray]] = {}
    scan_stats: dict[str, dict[str, Any]] = {}
    scan_errors: list[str] = []
    for scan_id, object_ids in sorted(scan_object_ids.items()):
        ply_path = dataset_root / "3RScan" / "scans" / scan_id / "labels.instances.annotated.v2.ply"
        if not ply_path.exists():
            scan_errors.append(f"missing_ply:{scan_id}:{ply_path}")
            scan_points[scan_id] = {object_id: np.empty((0, 3), dtype=np.float32) for object_id in object_ids}
            scan_stats[scan_id] = {"error": "missing_ply", "target_object_ids": sorted(object_ids)}
            continue
        try:
            points, stats = read_target_points(ply_path, object_ids)
        except Exception as exc:  # pragma: no cover - surfaced in manifest.
            scan_errors.append(f"read_ply_failed:{scan_id}:{type(exc).__name__}:{exc}")
            points = {object_id: np.empty((0, 3), dtype=np.float32) for object_id in object_ids}
            stats = {"error": str(exc), "target_object_ids": sorted(object_ids)}
        scan_points[scan_id] = points
        scan_stats[scan_id] = stats

    output_rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    validation_errors: list[dict[str, Any]] = []
    for row in dry_rows:
        scan_id = str(row["scan_id"])
        updated, diagnostic = update_row_with_points(
            row,
            points_by_object=scan_points.get(scan_id, {}),
            scan_stats=scan_stats.get(scan_id, {}),
            contact_threshold_m=args.contact_threshold_m,
            max_points_per_object=args.max_points_per_object,
        )
        output_rows.append(updated)
        diagnostics.append(diagnostic)
        errors = validate_row(updated, required_fields, allowed_fields)
        if updated.get("predicate_family") != TARGET_FAMILY:
            errors.append("predicate_family_changed")
        if updated.get("predicate_label") not in PREDICATE_LABELS:
            errors.append("predicate_label_out_of_scope")
        if updated.get("schema_version") != ROW_SCHEMA_VERSION:
            errors.append("schema_version_changed")
        if errors:
            validation_errors.append({"row_id": updated.get("row_id"), "errors": sorted(set(errors))})

    forbidden_present = sorted(
        field
        for row in output_rows
        for field in FORBIDDEN_OUTPUT_FIELDS
        if field in row
    )
    if forbidden_present:
        validation_errors.append({"row_id": "*", "errors": [f"forbidden_fields:{forbidden_present}"]})

    status_counts = Counter(row["extractor_status"] for row in output_rows)
    source_counts = Counter(row["source_name"] for row in output_rows)
    label_counts = Counter(row["predicate_label"] for row in output_rows)
    surface_type_counts = Counter(row["surface_evidence"]["selected_surface_type"] for row in output_rows)
    normal_class_counts = Counter(row["surface_evidence"]["selected_surface_normal_class"] for row in output_rows)
    normal_agreement = Counter(
        "same"
        if diag["surface_normal_class"] == diag["dry_run_surface_normal_class"]
        else "changed"
        for diag in diagnostics
    )
    source_ready: dict[str, Counter[str]] = defaultdict(Counter)
    label_ready: dict[str, Counter[str]] = defaultdict(Counter)
    for row in output_rows:
        source_ready[row["source_name"]][row["extractor_status"]] += 1
        label_ready[row["predicate_label"]][row["extractor_status"]] += 1

    ready_rows = status_counts.get("ready", 0)
    point_available_rows = sum(1 for row in output_rows if row["geometry_available"]["points"])
    normal_available_rows = sum(1 for row in output_rows if row["geometry_available"]["normals"])
    near_contact_rows = sum(
        1
        for row in output_rows
        if (row["point_contact_evidence"].get("near_contact_point_count") or 0) > 0
    )
    point_ready = (
        not validation_errors
        and not scan_errors
        and ready_rows == len(output_rows)
        and point_available_rows == len(output_rows)
        and normal_available_rows == len(output_rows)
    )
    status = STATUS_READY if point_ready else STATUS_PARTIAL
    next_gate = NEXT_GATE_READY if point_ready else NEXT_GATE_PARTIAL

    counts = {
        "input_rows": len(dry_rows),
        "output_rows": len(output_rows),
        "validation_errors": len(validation_errors),
        "scan_errors": len(scan_errors),
        "ready_rows": ready_rows,
        "point_available_rows": point_available_rows,
        "normal_available_rows": normal_available_rows,
        "near_contact_rows": near_contact_rows,
        "source_counts": count_dict(source_counts),
        "label_counts": count_dict(label_counts),
        "extractor_status_counts": count_dict(status_counts),
        "surface_type_counts": count_dict(surface_type_counts),
        "surface_normal_class_counts": count_dict(normal_class_counts),
        "normal_class_agreement_with_dry_run": count_dict(normal_agreement),
        "ready_by_source": nested_count_dict(source_ready),
        "ready_by_label": nested_count_dict(label_ready),
    }
    min_distances = [
        row["point_contact_evidence"]["min_point_distance_m"]
        for row in output_rows
        if row["point_contact_evidence"].get("min_point_distance_m") is not None
    ]
    distance_summary = {
        "min": min(min_distances) if min_distances else None,
        "median": float(np.median(min_distances)) if min_distances else None,
        "max": max(min_distances) if min_distances else None,
    }
    warning_counts = Counter()
    for row in output_rows:
        for flag in row.get("quality_flags", []):
            warning_counts[flag] += 1
    for error in scan_errors:
        warning_counts[error.split(":", 1)[0]] += 1

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": utc_now(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "artifact_type": "point_surface_estimator_validation",
            "metric_evidence": False,
            "verifier_evidence": False,
            "forbidden_outputs_absent": not forbidden_present,
        },
        "inputs": {
            "dry_run_manifest": relpath(repo_root, dry_manifest_path),
            "dry_run_rows": relpath(repo_root, dry_rows_path),
            "output_schema": relpath(repo_root, output_schema_path),
            "dataset_root": relpath(repo_root, dataset_root),
        },
        "settings": {
            "contact_threshold_m": args.contact_threshold_m,
            "max_points_per_object": args.max_points_per_object,
            "normal_estimator": "pca_on_segmented_object_points",
            "min_distance_estimator": "deterministic_sampled_pairwise_distance",
        },
        "outputs": {
            "rows": "rows.jsonl",
            "diagnostics": "diagnostics.jsonl",
            "summary": "summary.json",
            "validation": "validation.json",
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "counts": counts,
        "distance_summary": distance_summary,
        "warning_counts": count_dict(warning_counts),
        "scan_stats": {
            scan_id: {
                key: value
                for key, value in stats.items()
                if key
                in {
                    "ply_vertex_count_header",
                    "ply_face_count_header",
                    "ply_vertex_rows_read",
                    "target_vertex_rows_kept",
                    "target_object_ids",
                    "error",
                }
            }
            for scan_id, stats in sorted(scan_stats.items())
        },
        "scan_errors": scan_errors,
        "next_gate": next_gate,
        "blockers": []
        if point_ready
        else [
            "point_surface_validation_not_complete_for_all_rows",
            "do_not_write_verifier_policy_until_missing_points_or_normals_are_resolved",
        ],
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "counts": counts,
        "distance_summary": distance_summary,
        "warning_counts": count_dict(warning_counts),
        "forbidden_output_fields": sorted(FORBIDDEN_OUTPUT_FIELDS),
    }
    validation = {
        "status": "passed" if not validation_errors else "failed",
        "checked_rows": len(output_rows),
        "required_field_count": len(required_fields),
        "validation_errors": validation_errors,
        "forbidden_output_fields_present": sorted(set(forbidden_present)),
        "scan_errors": scan_errors,
    }

    ensure_dir(out)
    write_jsonl(out / "rows.jsonl", output_rows)
    write_jsonl(out / "diagnostics.jsonl", diagnostics)
    write_json(out / "summary.json", summary)
    write_json(out / "validation.json", validation)
    write_json(out / "manifest.json", manifest)
    (out / "report.md").write_text(report_md(manifest, summary), encoding="utf-8")
    print(json.dumps({"status": status, "out": str(out), "rows": len(output_rows)}, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
