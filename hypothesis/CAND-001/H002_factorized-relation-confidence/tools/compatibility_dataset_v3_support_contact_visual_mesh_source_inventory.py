#!/usr/bin/env python3
"""Inventory visual/mesh sources for support/contact H002 v3 extension."""

from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan"
DEFAULT_PROBE_RUNNER_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_evidence_probe_runner"
DEFAULT_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_VISUAL_AUDIT_ROOT = H2_ROOT / "artifacts/visual_annotation_audit"
DEFAULT_ATTACHMENT_PACKET_ROOT = H2_ROOT / "artifacts/attachment_independent_positive_anchor_packet_materialization_v1"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_visual_mesh_source_inventory"
EXPECTED_PROBE_STATUS = "h002_compatibility_dataset_v3_support_contact_evidence_probe_runner_blocks_numeric_support_smoke"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_ready_for_mesh_pose_contact_probe"
STATUS_BLOCKED = "h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_blocked"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_input_errors"
SELECTED_PATH_READY = "mesh_pose_contact_feature_probe_before_materialization"
NEXT_READY = "compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan"
NEXT_BLOCKED = "compatibility_dataset_v3_support_contact_diagnostic_freeze_decision"

SUPPORT_PREDICATES = {"standing on", "lying on", "supported by"}
HARD_SURFACES = {"floor", "wall", "ceiling", "room", "window", "door"}
JOIN_READY_THRESHOLD = 0.95
PREVIEW_LIMIT = 160
ZIP_SAMPLE_LIMIT = 24


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--probe-runner-dir", type=Path, default=DEFAULT_PROBE_RUNNER_DIR)
    parser.add_argument("--rga-dir", type=Path, default=DEFAULT_RGA_DIR)
    parser.add_argument("--three-rscan-root", type=Path, default=DEFAULT_3RSCAN_ROOT)
    parser.add_argument("--visual-audit-root", type=Path, default=DEFAULT_VISUAL_AUDIT_ROOT)
    parser.add_argument("--attachment-packet-root", type=Path, default=DEFAULT_ATTACHMENT_PACKET_ROOT)
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


def support_family(row: dict[str, Any]) -> bool:
    return row.get("predicate_family") == "support_contact" and row.get("predicate_label") in SUPPORT_PREDICATES


def hard_surface(label: Any) -> bool:
    return str(label or "").lower() in HARD_SURFACES


def hard_surface_pair(row: dict[str, Any]) -> bool:
    return hard_surface(row.get("subject_label")) or hard_surface(row.get("object_label"))


def pair_key(row: dict[str, Any]) -> str:
    return f"{row.get('scan_id')}::{row.get('subgraph_id')}::{row.get('subject_id')}->{row.get('object_id')}"


def visible_pair(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')} [REL] {row.get('object_label')}"


def scan_support_queues(rga_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = [rga_dir / "train_hl_queue.jsonl", rga_dir / "train_lh_queue.jsonl"]
    support_rows: list[dict[str, Any]] = []
    line_counts: dict[str, int] = {}
    for path in paths:
        count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                count += 1
                row = json.loads(line)
                if support_family(row):
                    support_rows.append(row)
        line_counts[rel_path(path)] = count
    return support_rows, {"line_counts": line_counts}


def validate_inputs(plan: dict[str, Any], probe: dict[str, Any], plan_errors: list[dict[str, Any]], probe_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan.get("status")})
    if plan.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan.get("next_todo")})
    if plan.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan.get("validation_errors")})
    if plan_errors:
        errors.append({"error_type": "plan_validation_error_rows_present", "rows": len(plan_errors)})
    if probe.get("status") != EXPECTED_PROBE_STATUS:
        errors.append({"error_type": "unexpected_probe_status", "actual": probe.get("status")})
    if probe.get("validation_errors") != 0:
        errors.append({"error_type": "probe_validation_errors", "actual": probe.get("validation_errors")})
    if probe_errors:
        errors.append({"error_type": "probe_validation_error_rows_present", "rows": len(probe_errors)})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified"]:
        if plan.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": plan.get("boundary", {}).get(key)})
        if probe.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "probe_boundary_not_false", "key": key, "actual": probe.get("boundary", {}).get(key)})
    return errors


def read_ply_header(path: Path) -> dict[str, Any]:
    info = {
        "exists": path.exists(),
        "vertex_count": None,
        "face_count": None,
        "has_object_id_property": False,
        "header_ok": False,
    }
    if not path.exists():
        return info
    try:
        with path.open("rb") as handle:
            for raw in handle:
                line = raw.decode("utf-8", errors="replace").strip()
                if line.startswith("element vertex "):
                    info["vertex_count"] = int(line.split()[-1])
                elif line.startswith("element face "):
                    info["face_count"] = int(line.split()[-1])
                elif line == "property ushort objectId" or line.endswith(" objectId"):
                    info["has_object_id_property"] = True
                elif line == "end_header":
                    info["header_ok"] = True
                    break
    except Exception as exc:  # pragma: no cover - recorded in artifact instead of raising.
        info["error"] = str(exc)
    return info


def read_semseg_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "object_ids": set(), "objects": {}, "object_count": 0}
    try:
        payload = read_json(path)
    except Exception as exc:  # pragma: no cover
        return {"exists": True, "read_error": str(exc), "object_ids": set(), "objects": {}, "object_count": 0}
    objects: dict[int, dict[str, Any]] = {}
    for group in payload.get("segGroups", []):
        oid = group.get("objectId", group.get("id"))
        if oid is None:
            continue
        try:
            oid_int = int(oid)
        except (TypeError, ValueError):
            continue
        obb = group.get("obb") or {}
        objects[oid_int] = {
            "label": group.get("label"),
            "dominantNormal": group.get("dominantNormal"),
            "obb": obb,
            "has_obb": bool(obb.get("centroid") and obb.get("axesLengths") and obb.get("normalizedAxes")),
            "has_dominant_normal": bool(group.get("dominantNormal")),
            "segment_count": len(group.get("segments") or []),
        }
    return {"exists": True, "object_ids": set(objects), "objects": objects, "object_count": len(objects)}


def sequence_zip_sample(path: Path) -> dict[str, Any]:
    info = {
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "member_count": None,
        "has_color": False,
        "has_depth": False,
        "has_pose": False,
        "has_info": False,
        "sampled": False,
    }
    if not path.exists():
        return info
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            info["member_count"] = len(names)
            info["has_color"] = any(name.endswith(".color.jpg") for name in names)
            info["has_depth"] = any(name.endswith(".depth.pgm") for name in names)
            info["has_pose"] = any(name.endswith(".pose.txt") for name in names)
            info["has_info"] = any(name.endswith("_info.txt") for name in names)
            info["sampled"] = True
    except Exception as exc:  # pragma: no cover
        info["error"] = str(exc)
    return info


def build_scan_assets(scan_ids: set[str], root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    assets: dict[str, dict[str, Any]] = {}
    scan_rows: list[dict[str, Any]] = []
    zip_samples: list[dict[str, Any]] = []
    for idx, scan_id in enumerate(sorted(scan_ids)):
        scan_dir = root / scan_id
        semseg = read_semseg_index(scan_dir / "semseg.v2.json")
        aligned_ply = read_ply_header(scan_dir / "labels.instances.align.annotated.v2.ply")
        annotated_ply = read_ply_header(scan_dir / "labels.instances.annotated.v2.ply")
        mesh_obj = scan_dir / "mesh.refined.v2.obj"
        mesh_seg = scan_dir / "mesh.refined.0.010000.segs.v2.json"
        texture = scan_dir / "mesh.refined_0.png"
        sequence = scan_dir / "sequence.zip"
        sequence_sample = sequence_zip_sample(sequence) if idx < ZIP_SAMPLE_LIMIT else {
            "exists": sequence.exists(),
            "size_bytes": sequence.stat().st_size if sequence.exists() else 0,
            "member_count": None,
            "has_color": None,
            "has_depth": None,
            "has_pose": None,
            "has_info": None,
            "sampled": False,
        }
        asset = {
            "scan_id": scan_id,
            "scan_dir_exists": scan_dir.exists(),
            "semseg_exists": semseg.get("exists", False),
            "semseg_object_count": semseg.get("object_count", 0),
            "semseg_objects": semseg.get("objects", {}),
            "semseg_object_ids": semseg.get("object_ids", set()),
            "aligned_ply_exists": aligned_ply.get("exists", False),
            "aligned_ply_header_ok": aligned_ply.get("header_ok", False),
            "aligned_ply_has_object_id": aligned_ply.get("has_object_id_property", False),
            "aligned_ply_vertex_count": aligned_ply.get("vertex_count"),
            "annotated_ply_exists": annotated_ply.get("exists", False),
            "mesh_obj_exists": mesh_obj.exists(),
            "mesh_seg_exists": mesh_seg.exists(),
            "mesh_texture_exists": texture.exists(),
            "sequence_zip_exists": sequence_sample.get("exists", False),
            "sequence_zip_size_bytes": sequence_sample.get("size_bytes", 0),
            "sequence_member_count_sample": sequence_sample.get("member_count"),
            "sequence_has_color_sample": sequence_sample.get("has_color"),
            "sequence_has_depth_sample": sequence_sample.get("has_depth"),
            "sequence_has_pose_sample": sequence_sample.get("has_pose"),
            "sequence_has_info_sample": sequence_sample.get("has_info"),
            "sequence_sampled": sequence_sample.get("sampled", False),
        }
        assets[scan_id] = asset
        scan_rows.append({k: v for k, v in asset.items() if k not in {"semseg_objects", "semseg_object_ids"}})
        if sequence_sample.get("sampled"):
            zip_row = {"scan_id": scan_id}
            zip_row.update(sequence_sample)
            zip_samples.append(zip_row)
    return assets, scan_rows, zip_samples


def row_join_info(row: dict[str, Any], assets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    scan_id = str(row.get("scan_id"))
    asset = assets.get(scan_id, {})
    subject_id = int(row.get("subject_id"))
    object_id = int(row.get("object_id"))
    objects = asset.get("semseg_objects", {})
    subject = objects.get(subject_id, {})
    obj = objects.get(object_id, {})
    subject_present = subject_id in asset.get("semseg_object_ids", set())
    object_present = object_id in asset.get("semseg_object_ids", set())
    both_present = subject_present and object_present
    both_obb = bool(subject.get("has_obb")) and bool(obj.get("has_obb"))
    both_normals = bool(subject.get("has_dominant_normal")) and bool(obj.get("has_dominant_normal"))
    scan_asset_complete = all(
        [
            asset.get("scan_dir_exists"),
            asset.get("semseg_exists"),
            asset.get("aligned_ply_exists"),
            asset.get("aligned_ply_has_object_id"),
            asset.get("mesh_obj_exists"),
            asset.get("mesh_seg_exists"),
            asset.get("sequence_zip_exists"),
        ]
    )
    return {
        "scan_id": scan_id,
        "prediction_id": row.get("prediction_id"),
        "subgraph_id": row.get("subgraph_id"),
        "queue_kind": row.get("queue_kind"),
        "predicate_label": row.get("predicate_label"),
        "geometry_status": row.get("geometry_status"),
        "label_match_status": row.get("label_match_status"),
        "semantic_rank": row.get("semantic_rank"),
        "rank_band": row.get("rank_band"),
        "subject_id": subject_id,
        "object_id": object_id,
        "subject_label": row.get("subject_label"),
        "object_label": row.get("object_label"),
        "semseg_subject_label": subject.get("label"),
        "semseg_object_label": obj.get("label"),
        "hard_surface_pair": hard_surface_pair(row),
        "scan_asset_complete": scan_asset_complete,
        "semseg_subject_present": subject_present,
        "semseg_object_present": object_present,
        "semseg_both_objects_present": both_present,
        "semseg_both_obb_present": both_obb,
        "semseg_both_dominant_normals_present": both_normals,
        "aligned_ply_object_points_possible": bool(asset.get("aligned_ply_exists") and asset.get("aligned_ply_has_object_id") and both_present),
        "mesh_contact_surface_possible": bool(asset.get("mesh_obj_exists") and asset.get("mesh_seg_exists") and both_present),
        "sequence_multiview_possible": bool(asset.get("sequence_zip_exists")),
        "role_orientation_pose_possible": bool(both_obb),
        "source_score_hidden_from_future_model": True,
        "construction_proxy_hidden_from_future_model": True,
    }


def summarize_join(join_rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(join_rows)

    def count(key: str) -> int:
        return sum(1 for row in join_rows if row.get(key) is True)

    predicate_counts = Counter(str(row.get("predicate_label")) for row in join_rows)
    queue_counts = Counter(str(row.get("queue_kind")) for row in join_rows)
    geometry_counts = Counter(str(row.get("geometry_status")) for row in join_rows)
    hard_surface_count = count("hard_surface_pair")
    top_scan_counts = Counter(str(row.get("scan_id")) for row in join_rows).most_common(10)
    top_visible_pair_counts = Counter(f"{row.get('subject_label')} [REL] {row.get('object_label')}" for row in join_rows).most_common(10)
    return {
        "rows": total,
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "queue_counts": dict(sorted(queue_counts.items())),
        "geometry_status_counts": dict(sorted(geometry_counts.items())),
        "distinct_scans": len({row.get("scan_id") for row in join_rows}),
        "distinct_directed_pairs": len({f"{row.get('scan_id')}::{row.get('subgraph_id')}::{row.get('subject_id')}->{row.get('object_id')}" for row in join_rows}),
        "distinct_visible_pairs": len({f"{row.get('subject_label')} [REL] {row.get('object_label')}" for row in join_rows}),
        "hard_surface_pair_rows": hard_surface_count,
        "non_hard_surface_pair_rows": total - hard_surface_count,
        "scan_asset_complete_rows": count("scan_asset_complete"),
        "semseg_both_objects_present_rows": count("semseg_both_objects_present"),
        "semseg_both_obb_present_rows": count("semseg_both_obb_present"),
        "semseg_both_dominant_normals_present_rows": count("semseg_both_dominant_normals_present"),
        "aligned_ply_object_points_possible_rows": count("aligned_ply_object_points_possible"),
        "mesh_contact_surface_possible_rows": count("mesh_contact_surface_possible"),
        "sequence_multiview_possible_rows": count("sequence_multiview_possible"),
        "role_orientation_pose_possible_rows": count("role_orientation_pose_possible"),
        "scan_asset_complete_rate": count("scan_asset_complete") / total if total else 0.0,
        "semseg_both_objects_present_rate": count("semseg_both_objects_present") / total if total else 0.0,
        "mesh_contact_surface_possible_rate": count("mesh_contact_surface_possible") / total if total else 0.0,
        "sequence_multiview_possible_rate": count("sequence_multiview_possible") / total if total else 0.0,
        "top_scan_counts": top_scan_counts,
        "top_visible_pair_counts": top_visible_pair_counts,
    }


def preview_rows(join_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per_cell: Counter[str] = Counter()
    for row in join_rows:
        cell = f"{row.get('predicate_label')}|{row.get('queue_kind')}|{row.get('hard_surface_pair')}"
        if per_cell[cell] >= 12:
            continue
        selected.append(row)
        per_cell[cell] += 1
        if len(selected) >= PREVIEW_LIMIT:
            break
    return selected


def mesh_pose_contact_feasibility(join_summary: dict[str, Any]) -> list[dict[str, Any]]:
    total = int(join_summary.get("rows", 0) or 0)

    def row(axis: str, possible_key: str, verdict: str, reason: str) -> dict[str, Any]:
        count = int(join_summary.get(possible_key, 0) or 0)
        return {
            "axis": axis,
            "possible_rows": count,
            "total_rows": total,
            "coverage_rate": count / total if total else 0.0,
            "verdict": verdict,
            "reason": reason,
        }

    return [
        row("scan_asset_complete", "scan_asset_complete_rows", "required_join_check", "All source files needed for later feature extraction exist at scan level."),
        row("instance_obb_pose", "semseg_both_obb_present_rows", "primary_Ge_candidate", "OBB axes and extents support pose/uprightness/horizontalness features."),
        row("dominant_normal", "semseg_both_dominant_normals_present_rows", "primary_Ge_candidate", "Dominant normals can seed contact-direction and surface-orientation checks."),
        row("aligned_ply_object_points", "aligned_ply_object_points_possible_rows", "primary_Ge_candidate", "Aligned PLY has objectId and both candidate objects are present."),
        row("mesh_contact_surface", "mesh_contact_surface_possible_rows", "primary_Ge_candidate", "Mesh and segmentation assets can support contact patch / surface gap features."),
        row("sequence_multiview", "sequence_multiview_possible_rows", "Qe_audit_first", "Sequence frames can support co-visibility/crop quality, but not immediate model input."),
    ]


def multiview_packet_feasibility(join_summary: dict[str, Any], visual_root: Path, packet_root: Path, zip_samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contact_sheet_dir = visual_root / "contact_sheets"
    contact_sheets = sorted(contact_sheet_dir.glob("*.jpg")) if contact_sheet_dir.exists() else []
    support_sheets = [path for path in contact_sheets if path.stem.split("_")[-2] in {"standing-on", "lying-on", "supported-by"}]
    packets_root = packet_root / "packets"
    packet_dirs = [path for path in packets_root.iterdir() if path.is_dir()] if packets_root.exists() else []
    sampled = len(zip_samples)
    color_ok = sum(1 for row in zip_samples if row.get("has_color") is True)
    depth_ok = sum(1 for row in zip_samples if row.get("has_depth") is True)
    pose_ok = sum(1 for row in zip_samples if row.get("has_pose") is True)
    return [
        {
            "source": "sequence_zip",
            "role": "Q_e_audit_first",
            "candidate_rows_with_sequence": join_summary.get("sequence_multiview_possible_rows"),
            "candidate_total_rows": join_summary.get("rows"),
            "sampled_zips": sampled,
            "sampled_color_ok": color_ok,
            "sampled_depth_ok": depth_ok,
            "sampled_pose_ok": pose_ok,
            "model_input_allowed_now": False,
            "next_use": "source_inventory_then_optional_crop_quality_Qe",
        },
        {
            "source": "visual_annotation_contact_sheets",
            "role": "audit_reference",
            "contact_sheet_count": len(contact_sheets),
            "support_contact_sheet_count": len(support_sheets),
            "model_input_allowed_now": False,
            "next_use": "review_template_and_label_confirmation_reference",
        },
        {
            "source": "attachment_packet_template",
            "role": "renderer_template_only",
            "packet_dirs": len(packet_dirs),
            "contact_context_sheets": len(list(packets_root.glob("*/contact_context_sheet.jpg"))) if packets_root.exists() else 0,
            "mesh_packet_md": len(list(packets_root.glob("*/mesh_packet.md"))) if packets_root.exists() else 0,
            "model_input_allowed_now": False,
            "next_use": "reuse_packet_builder_pattern_not_labels",
        },
    ]


def shortcut_and_scope_risks(join_rows: list[dict[str, Any]], join_summary: dict[str, Any], probe_summary: dict[str, Any]) -> list[dict[str, Any]]:
    total = len(join_rows)
    risks: list[dict[str, Any]] = []

    def add(name: str, severity: str, value: Any, threshold: Any, reason: str, mitigation: str) -> None:
        risks.append(
            {
                "risk": name,
                "severity": severity,
                "value": value,
                "threshold": threshold,
                "reason": reason,
                "mitigation": mitigation,
            }
        )

    hard_rate = (join_summary.get("hard_surface_pair_rows", 0) / total) if total else 0.0
    add(
        "hard_surface_dominance",
        "high" if hard_rate > 0.70 else "medium" if hard_rate > 0.40 else "low",
        hard_rate,
        "<=0.70 preferred before smoke",
        "support/contact often involves floor/wall/ceiling, which can become an object-category shortcut.",
        "cap hard-surface rows and require non-hard-surface anchors in materialization.",
    )

    pred_counts = Counter(str(row.get("predicate_label")) for row in join_rows)
    max_pred_rate = max(pred_counts.values()) / total if total and pred_counts else 0.0
    add(
        "predicate_imbalance",
        "high" if max_pred_rate > 0.85 else "medium" if max_pred_rate > 0.70 else "low",
        dict(sorted(pred_counts.items())),
        "max predicate share <=0.70 preferred",
        "A single support/contact predicate can dominate target construction.",
        "stratify by predicate and report per-predicate feasibility.",
    )

    queue_counts = Counter(str(row.get("queue_kind")) for row in join_rows)
    min_queue_rate = min(queue_counts.values()) / total if total and len(queue_counts) >= 2 else 0.0
    add(
        "HL_LH_queue_imbalance",
        "high" if min_queue_rate < 0.05 else "medium" if min_queue_rate < 0.20 else "low",
        dict(sorted(queue_counts.items())),
        "minority queue >=0.20 preferred for direct smoke",
        "Direct HL/LH balance failed earlier; queue kind can proxy label construction.",
        "do not use queue kind as target; build mesh/pose/contact evidence first.",
    )

    visible_pair_counts = join_summary.get("top_visible_pair_counts", [])
    top_visible_rate = visible_pair_counts[0][1] / total if total and visible_pair_counts else 0.0
    add(
        "visible_pair_dominance",
        "high" if top_visible_rate > 0.30 else "medium" if top_visible_rate > 0.15 else "low",
        visible_pair_counts[:5],
        "top visible pair share <=0.15 preferred",
        "A small set of object-label pairs may dominate support/contact.",
        "cap visible-pair cells and audit object-pair shortcut baselines.",
    )

    non_hard_exact = probe_summary.get("path_decision", {}).get("candidate_non_hard_surface_exact_pair_groups")
    add(
        "same_exact_pair_clean_capacity",
        "high",
        non_hard_exact,
        ">=60 required for prior same-pair target",
        "The previous exact-pair route had only 4 non-hard-surface candidate groups.",
        "do not return to exact-pair numeric target; use mesh/pose/contact evidence probe.",
    )
    return risks


def path_decision(join_summary: dict[str, Any], risks: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    if errors:
        return {
            "status": STATUS_ERRORS,
            "selected_path": "fix_inputs_before_source_inventory_decision",
            "next_todo": "fix_support_contact_visual_mesh_source_inventory_inputs",
            "validation_errors": len(errors),
            "source_inventory_ready": False,
        }
    mesh_rate = float(join_summary.get("mesh_contact_surface_possible_rate", 0.0) or 0.0)
    semseg_rate = float(join_summary.get("semseg_both_objects_present_rate", 0.0) or 0.0)
    sequence_rate = float(join_summary.get("sequence_multiview_possible_rate", 0.0) or 0.0)
    ready = mesh_rate >= JOIN_READY_THRESHOLD and semseg_rate >= JOIN_READY_THRESHOLD and sequence_rate >= JOIN_READY_THRESHOLD
    materialization_or_smoke_blocking_risks = [risk for risk in risks if risk["severity"] == "high"]
    # These high risks block immediate materialization/smoke, but not source-level mesh/pose/contact
    # feature probing. The feature probe only derives predicate-independent evidence candidates.
    return {
        "status": STATUS_READY if ready else STATUS_BLOCKED,
        "selected_path": SELECTED_PATH_READY if ready else "keep_support_contact_diagnostic_until_join_gap_fixed",
        "next_todo": NEXT_READY if ready else NEXT_BLOCKED,
        "validation_errors": 0,
        "source_inventory_ready": ready,
        "mesh_contact_surface_possible_rate": mesh_rate,
        "semseg_both_objects_present_rate": semseg_rate,
        "sequence_multiview_possible_rate": sequence_rate,
        "join_ready_threshold": JOIN_READY_THRESHOLD,
        "numeric_only_smoke_allowed": False,
        "learned_smoke_allowed": False,
        "candidate_materialization_allowed": False,
        "mesh_pose_contact_feature_probe_allowed": ready,
        "multiview_model_input_allowed_now": False,
        "multiview_qe_audit_first": True,
        "high_risks": [risk for risk in risks if risk["severity"] == "high"],
        "blocking_risks_for_materialization_or_smoke": materialization_or_smoke_blocking_risks,
        "rationale": (
            "Scan-level and object-level assets are joinable enough for a feature feasibility probe, "
            "but support/contact still needs shortcut-controlled materialization before any learned smoke."
            if ready
            else "Required mesh/semseg/sequence joins did not meet the source-inventory threshold."
        ),
    }


def report_text(summary: dict[str, Any], decision: dict[str, Any]) -> str:
    js = summary["join_summary"]
    ss = summary["source_inventory_summary"]
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Visual-Mesh Source Inventory",
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
            "## Candidate Join Coverage",
            "",
            "```text",
            f"support_rows = {js['rows']}",
            f"distinct_scans = {js['distinct_scans']}",
            f"scan_asset_complete_rate = {js['scan_asset_complete_rate']:.6f}",
            f"semseg_both_objects_present_rate = {js['semseg_both_objects_present_rate']:.6f}",
            f"mesh_contact_surface_possible_rate = {js['mesh_contact_surface_possible_rate']:.6f}",
            f"sequence_multiview_possible_rate = {js['sequence_multiview_possible_rate']:.6f}",
            "```",
            "",
            "## Source Snapshot",
            "",
            "```text",
            f"candidate_scans = {ss['candidate_scans']}",
            f"scan_dirs_present = {ss['scan_dirs_present']}",
            f"mesh_obj_present = {ss['mesh_obj_present']}",
            f"aligned_ply_present = {ss['aligned_ply_present']}",
            f"sequence_zip_present = {ss['sequence_zip_present']}",
            f"sampled_sequence_zips = {ss['sampled_sequence_zips']}",
            f"sampled_sequence_color_depth_pose_ok = {ss['sampled_sequence_color_depth_pose_ok']}",
            "```",
            "",
            "## Decision",
            "",
            "```text",
            f"mesh_pose_contact_feature_probe_allowed = {decision['mesh_pose_contact_feature_probe_allowed']}",
            f"candidate_materialization_allowed = {decision['candidate_materialization_allowed']}",
            f"learned_smoke_allowed = {decision['learned_smoke_allowed']}",
            f"multiview_model_input_allowed_now = {decision['multiview_model_input_allowed_now']}",
            f"multiview_qe_audit_first = {decision['multiview_qe_audit_first']}",
            "```",
            "",
            "## Interpretation",
            "",
            "The source join is strong enough to proceed to a mesh/pose/contact feature feasibility probe.",
            "This does not authorize learned smoke or candidate materialization. It only means the next",
            "step can derive predicate-independent `G_e` candidates from semseg OBBs, aligned PLY object",
            "points, mesh surfaces, and sequence availability while keeping multi-view as audit/`Q_e` first.",
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
    probe_summary = read_json(args.probe_runner_dir / "summary.json")
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    probe_errors = read_jsonl(args.probe_runner_dir / "validation_errors.jsonl")
    errors = validate_inputs(plan_summary, probe_summary, plan_errors, probe_errors)

    support_rows, queue_meta = scan_support_queues(args.rga_dir)
    scan_ids = {str(row.get("scan_id")) for row in support_rows}
    assets, scan_asset_rows, zip_samples = build_scan_assets(scan_ids, args.three_rscan_root)
    join_rows = [row_join_info(row, assets) for row in support_rows]
    join_summary = summarize_join(join_rows)
    preview = preview_rows(join_rows)
    feasibility_rows = mesh_pose_contact_feasibility(join_summary)
    multiview_rows = multiview_packet_feasibility(join_summary, args.visual_audit_root, args.attachment_packet_root, zip_samples)
    risk_rows = shortcut_and_scope_risks(join_rows, join_summary, probe_summary)
    decision = path_decision(join_summary, risk_rows, errors)

    status = decision["status"]
    selected_path = decision["selected_path"]
    next_todo = decision["next_todo"]
    source_inventory_summary = {
        "candidate_scans": len(scan_ids),
        "scan_dirs_present": sum(1 for row in scan_asset_rows if row.get("scan_dir_exists")),
        "semseg_present": sum(1 for row in scan_asset_rows if row.get("semseg_exists")),
        "mesh_obj_present": sum(1 for row in scan_asset_rows if row.get("mesh_obj_exists")),
        "mesh_seg_present": sum(1 for row in scan_asset_rows if row.get("mesh_seg_exists")),
        "aligned_ply_present": sum(1 for row in scan_asset_rows if row.get("aligned_ply_exists")),
        "aligned_ply_has_object_id": sum(1 for row in scan_asset_rows if row.get("aligned_ply_has_object_id")),
        "sequence_zip_present": sum(1 for row in scan_asset_rows if row.get("sequence_zip_exists")),
        "sampled_sequence_zips": len(zip_samples),
        "sampled_sequence_color_depth_pose_ok": sum(
            1 for row in zip_samples if row.get("has_color") and row.get("has_depth") and row.get("has_pose")
        ),
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "plan_status": plan_summary.get("status"),
        "probe_status": probe_summary.get("status"),
        "queue_meta": queue_meta,
        "join_summary": join_summary,
        "source_inventory_summary": source_inventory_summary,
        "path_decision": decision,
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "scan_asset_inventory": rel_path(output_dir / "scan_asset_inventory.csv"),
            "support_contact_candidate_source_join_preview": rel_path(output_dir / "support_contact_candidate_source_join_preview.jsonl"),
            "mesh_pose_contact_feature_feasibility": rel_path(output_dir / "mesh_pose_contact_feature_feasibility.csv"),
            "multiview_packet_feasibility": rel_path(output_dir / "multiview_packet_feasibility.csv"),
            "shortcut_and_scope_risk": rel_path(output_dir / "shortcut_and_scope_risk.csv"),
            "sequence_zip_sample": rel_path(output_dir / "sequence_zip_sample.csv"),
            "path_decision": rel_path(output_dir / "path_decision.json"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_source_inventory",
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

    write_json(output_dir / "summary.json", summary)
    write_csv(output_dir / "scan_asset_inventory.csv", scan_asset_rows)
    write_jsonl(output_dir / "support_contact_candidate_source_join_preview.jsonl", preview)
    write_csv(output_dir / "mesh_pose_contact_feature_feasibility.csv", feasibility_rows)
    write_csv(output_dir / "multiview_packet_feasibility.csv", multiview_rows)
    write_csv(output_dir / "shortcut_and_scope_risk.csv", risk_rows)
    write_csv(output_dir / "sequence_zip_sample.csv", zip_samples)
    write_json(output_dir / "path_decision.json", decision)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(report_text(summary, decision), encoding="utf-8")

    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
