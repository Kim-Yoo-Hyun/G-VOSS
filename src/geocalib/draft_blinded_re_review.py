#!/usr/bin/env python3
"""Run a second leakage-safe Codex geometry review without reading pass v1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = "h001_codex_blinded_rereview_v2"
LABELS = ("physically_valid", "physically_invalid", "ambiguous", "unobservable")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--public-queue", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, path: Path | str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else root / value


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_pair_ply(path: Path) -> tuple[np.ndarray, np.ndarray]:
    properties: list[str] = []
    vertex_count = 0
    in_vertex = False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        if handle.readline().strip() != "ply":
            raise ValueError("not_ascii_ply")
        for line in handle:
            value = line.strip()
            if value.startswith("element vertex"):
                vertex_count = int(value.split()[-1])
                in_vertex = True
            elif value.startswith("element "):
                in_vertex = False
            elif value.startswith("property") and in_vertex:
                properties.append(value.split()[-1])
            elif value == "end_header":
                break
        index = {name: properties.index(name) for name in ("x", "y", "z", "roleId")}
        subject: list[list[float]] = []
        obj: list[list[float]] = []
        for _ in range(vertex_count):
            values = handle.readline().split()
            if not values:
                break
            point = [float(values[index[axis]]) for axis in ("x", "y", "z")]
            role = int(values[index["roleId"]])
            if role == 1:
                subject.append(point)
            elif role == 2:
                obj.append(point)
    return np.asarray(subject, dtype=np.float64), np.asarray(obj, dtype=np.float64)


def sample_points(points: np.ndarray, limit: int = 512) -> np.ndarray:
    if len(points) <= limit:
        return points
    return points[np.linspace(0, len(points) - 1, limit, dtype=int)]


def nearest_surface_distance(subject: np.ndarray, obj: np.ndarray) -> tuple[float, float]:
    a = sample_points(subject)
    b = sample_points(obj)
    nearest_a = np.full(len(a), np.inf, dtype=np.float64)
    nearest_b = np.full(len(b), np.inf, dtype=np.float64)
    for start in range(0, len(a), 64):
        block = a[start : start + 64]
        squared = np.sum((block[:, None, :] - b[None, :, :]) ** 2, axis=2)
        nearest_a[start : start + len(block)] = np.sqrt(squared.min(axis=1))
        nearest_b = np.minimum(nearest_b, np.sqrt(squared.min(axis=0)))
    both = np.concatenate([nearest_a, nearest_b])
    return float(np.percentile(both, 2)), float(np.percentile(both, 10))


def robust_features(subject: np.ndarray, obj: np.ndarray) -> dict[str, Any]:
    if len(subject) < 20 or len(obj) < 20:
        return {"sufficient": False, "subject_points": len(subject), "object_points": len(obj)}
    sub_low, sub_high = np.percentile(subject, [2, 98], axis=0)
    obj_low, obj_high = np.percentile(obj, [2, 98], axis=0)
    sub_extent = np.maximum(sub_high - sub_low, 1e-6)
    obj_extent = np.maximum(obj_high - obj_low, 1e-6)
    sub_center = np.median(subject, axis=0)
    obj_center = np.median(obj, axis=0)
    pair_scale = max(
        0.25,
        0.5 * (float(np.linalg.norm(sub_extent)) + float(np.linalg.norm(obj_extent))),
    )
    axis_gap = np.maximum(np.maximum(sub_low - obj_high, obj_low - sub_high), 0.0)
    xy_axis_gap = axis_gap[:2]
    intersection_xy = np.maximum(
        np.minimum(sub_high[:2], obj_high[:2]) - np.maximum(sub_low[:2], obj_low[:2]),
        0.0,
    )
    intersection_area = float(np.prod(intersection_xy))
    min_area = max(min(float(np.prod(sub_extent[:2])), float(np.prod(obj_extent[:2]))), 1e-8)
    xy_overlap = intersection_area / min_area

    horizontal_margin = 0.05 * pair_scale
    local = obj[
        (obj[:, 0] >= sub_low[0] - horizontal_margin)
        & (obj[:, 0] <= sub_high[0] + horizontal_margin)
        & (obj[:, 1] >= sub_low[1] - horizontal_margin)
        & (obj[:, 1] <= sub_high[1] + horizontal_margin)
    ]
    object_top_local = float(np.percentile(local[:, 2], 98)) if len(local) >= 12 else None
    subject_bottom = float(np.percentile(subject[:, 2], 2))
    support_gap = subject_bottom - object_top_local if object_top_local is not None else None
    surface_p02, surface_p10 = nearest_surface_distance(subject, obj)
    return {
        "sufficient": True,
        "subject_points": len(subject),
        "object_points": len(obj),
        "pair_scale_m": pair_scale,
        "center_dz_norm": float((sub_center[2] - obj_center[2]) / pair_scale),
        "bbox_gap_norm": float(np.linalg.norm(axis_gap) / pair_scale),
        "xy_bbox_gap_norm": float(np.linalg.norm(xy_axis_gap) / pair_scale),
        "xy_overlap_ratio": xy_overlap,
        "local_object_points": int(len(local)),
        "support_gap_norm": support_gap / pair_scale if support_gap is not None else None,
        "surface_p02_norm": surface_p02 / pair_scale,
        "surface_p10_norm": surface_p10 / pair_scale,
        "subject_vertical_aspect": float(sub_extent[2] / max(sub_extent[0], sub_extent[1], 1e-6)),
    }


def decision(label: str, confidence: str, reason: str) -> dict[str, str]:
    return {"label": label, "confidence": confidence, "reason": reason}


def classify(predicate: str, f: dict[str, Any]) -> dict[str, str]:
    if not f.get("sufficient"):
        return decision("unobservable", "low", "insufficient_pair_geometry")

    dz = float(f["center_dz_norm"])
    bbox_gap = float(f["bbox_gap_norm"])
    xy_gap = float(f["xy_bbox_gap_norm"])
    overlap = float(f["xy_overlap_ratio"])
    surface = float(f["surface_p02_norm"])
    support_gap = f.get("support_gap_norm")
    aspect = float(f["subject_vertical_aspect"])

    if predicate in {"higher than", "lower than"}:
        directed = dz if predicate == "higher than" else -dz
        if directed >= 0.55:
            return decision("physically_valid", "high", "clear_directed_vertical_order")
        if directed >= 0.20:
            return decision("physically_valid", "medium", "moderate_directed_vertical_order")
        if directed <= -0.35:
            return decision("physically_invalid", "high", "clear_reversed_vertical_order")
        if directed <= -0.10:
            return decision("physically_invalid", "medium", "moderate_reversed_vertical_order")
        return decision("ambiguous", "low", "near_tied_vertical_extent")

    if predicate == "close by":
        # Use visible surface separation first; bbox gap is a secondary guard.
        if surface <= 0.12 or bbox_gap <= 0.12:
            return decision("physically_valid", "high", "near_visible_surfaces")
        if surface <= 0.32 and bbox_gap <= 0.48:
            return decision("physically_valid", "medium", "moderate_relative_proximity")
        if surface >= 0.90 and bbox_gap >= 0.75:
            return decision("physically_invalid", "high", "large_relative_separation")
        if surface >= 0.58 and bbox_gap >= 0.50:
            return decision("physically_invalid", "medium", "separated_relative_to_pair_scale")
        return decision("ambiguous", "low", "proximity_requires_scene_context")

    has_local_surface = support_gap is not None and int(f["local_object_points"]) >= 12
    vertical_contact = has_local_surface and -0.15 <= float(support_gap) <= 0.18
    footprint = overlap >= 0.06 or xy_gap <= 0.05
    direct_contact = surface <= 0.10
    support_consistent = vertical_contact and footprint and direct_contact
    support_possible = (
        has_local_surface
        and -0.25 <= float(support_gap) <= 0.30
        and (overlap >= 0.02 or xy_gap <= 0.12)
        and surface <= 0.22
    )
    support_missing = (
        bbox_gap >= 0.60
        or xy_gap >= 0.50
        or (support_gap is not None and float(support_gap) >= 0.42)
        or surface >= 0.58
    )

    if predicate == "supported by":
        if support_consistent:
            return decision("physically_valid", "high", "direct_support_contact")
        if support_possible:
            return decision("physically_valid", "medium", "plausible_support_contact")
        if support_missing:
            return decision("physically_invalid", "high" if bbox_gap >= 0.90 else "medium", "support_contact_absent")
        return decision("ambiguous", "low", "support_surface_or_contact_unclear")

    if predicate == "standing on":
        if support_consistent and aspect >= 0.45:
            return decision("physically_valid", "high", "contact_with_upright_pose")
        if support_possible and aspect >= 0.25:
            return decision("physically_valid", "medium", "plausible_contact_with_upright_pose")
        if support_missing:
            return decision("physically_invalid", "high" if bbox_gap >= 0.90 else "medium", "standing_support_absent")
        if (support_consistent or support_possible) and aspect <= 0.13:
            return decision("physically_invalid", "medium", "contact_but_flat_pose")
        return decision("ambiguous", "low", "standing_pose_or_contact_unclear")

    if predicate == "lying on":
        if support_consistent and aspect <= 0.50:
            return decision("physically_valid", "high", "contact_with_flat_pose")
        if support_possible and aspect <= 0.75:
            return decision("physically_valid", "medium", "plausible_contact_with_flat_pose")
        if support_missing:
            return decision("physically_invalid", "high" if bbox_gap >= 0.90 else "medium", "lying_support_absent")
        if (support_consistent or support_possible) and aspect >= 1.15:
            return decision("physically_invalid", "medium", "contact_but_upright_pose")
        return decision("ambiguous", "low", "lying_pose_or_contact_unclear")

    return decision("unobservable", "low", "predicate_outside_frozen_scope")


def feature_text(f: dict[str, Any]) -> str:
    keys = (
        "center_dz_norm",
        "bbox_gap_norm",
        "xy_bbox_gap_norm",
        "xy_overlap_ratio",
        "support_gap_norm",
        "surface_p02_norm",
        "surface_p10_norm",
        "subject_vertical_aspect",
        "local_object_points",
    )
    values = []
    for key in keys:
        value = f.get(key)
        values.append(f"{key}={value:.4f}" if isinstance(value, float) else f"{key}={value}")
    return ";".join(values)


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    queue_path = resolve(root, args.public_queue)
    out = resolve(root, args.out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    rows = read_jsonl(queue_path)
    outputs: list[dict[str, Any]] = []
    features_out: list[dict[str, Any]] = []
    evidence_hashes: dict[str, str] = {}
    errors: list[str] = []
    for row in rows:
        ply = resolve(root, row["pair_ply_path"])
        evidence_hashes[row["audit_id"]] = sha256_file(ply)
        try:
            subject, obj = load_pair_ply(ply)
            features = robust_features(subject, obj)
            result = classify(str(row["predicate_label"]), features)
        except Exception as exc:
            features = {"sufficient": False, "error": type(exc).__name__}
            result = decision("unobservable", "low", "public_geometry_load_error")
            errors.append(f"{row['audit_id']}:{type(exc).__name__}")
        outputs.append(
            {
                "audit_id": row["audit_id"],
                "relation": row["relation"],
                "predicate_label": row["predicate_label"],
                "predicate_family": row["predicate_family"],
                "geometry_projection_path": row["geometry_projection_path"],
                "rgb_pair_crop_path": row["rgb_pair_crop_path"],
                "pair_ply_path": row["pair_ply_path"],
                "physical_validity_label": result["label"],
                "confidence": result["confidence"],
                "primary_reason_code": result["reason"],
                "evidence_sufficient": bool(features.get("sufficient")),
                "notes": f"codex_blinded_rereview_v2:{feature_text(features)}",
                "reviewer_id": "codex_blinded_rereview_v2",
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        features_out.append({"audit_id": row["audit_id"], **features})

    label_counts = Counter(row["physical_validity_label"] for row in outputs)
    confidence_counts = Counter(row["confidence"] for row in outputs)
    status = "codex_blinded_rereview_v2_locked" if not errors and len(outputs) == 488 else "blocked_rereview"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "counts": {
            "rows": len(outputs),
            "by_label": dict(sorted(label_counts.items())),
            "by_confidence": dict(sorted(confidence_counts.items())),
            "load_errors": len(errors),
        },
        "blinding_contract": {
            "files_read": [
                relpath(root, queue_path),
                "488 public pair PLY paths named by public_queue.jsonl",
            ],
            "files_not_read": [
                "private_sidecar.jsonl",
                "annotator_a.csv",
                "annotator_b.csv",
                "adjudication.csv",
                "codex_proxy_v1/codex_proxy_draft.csv",
                "any source identity, semantic score/rank, verifier output, sampling stratum, or GT membership",
            ],
            "decision_lock_precedes_pass_comparison": True,
            "same_agent_not_independent_annotator": True,
        },
        "method": {
            "name": "conservative robust-surface geometry rubric",
            "evidence": "public pair PLY only",
            "features": [
                "2-98 percentile boxes",
                "directed center height",
                "visible nearest-surface separation",
                "XY overlap and separation",
                "local support-surface gap",
                "subject pose aspect",
            ],
            "manual_visual_followup": "performed only after this pass is locked, focusing on disagreement and low-confidence rows",
        },
        "inputs": {
            "public_queue": {"path": relpath(root, queue_path), "sha256": sha256_file(queue_path)},
            "public_pair_ply_hashes": evidence_hashes,
        },
        "errors": errors,
        "claim_boundary": "Codex blinded re-review; not a human annotator and not independent of Codex pass v1",
        "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm physical_validity_codex_rereview_v2",
    }
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "labels.csv", outputs)
    write_csv(out / "visible_geometry_features.csv", features_out)
    write_json(out / "manifest.json", manifest)
    print(json.dumps({"status": status, "counts": manifest["counts"], "out": relpath(root, out)}))
    return 0 if status.endswith("locked") else 2


if __name__ == "__main__":
    raise SystemExit(main())
