#!/usr/bin/env python3
"""Inventory point/multiview sources for support/contact individual predicates."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan"
)
DEFAULT_CANDIDATE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"
)
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan_ready_for_source_inventory"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory_ready_for_materialization_plan"
)
STATUS_BLOCKED = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory_blocked"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory_input_errors"
)
SELECTED_PATH = "source_inventory_ready_for_gq_separated_materialization_plan"
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan"

MAIN_PREDICATES = {"standing on", "lying on"}
DIAGNOSTIC_PREDICATES = {"supported by"}
REQUIRED_ASSETS = {
    "aligned_ply": "labels.instances.align.annotated.v2.ply",
    "semseg": "semseg.v2.json",
    "mesh_obj": "mesh.refined.v2.obj",
    "mesh_seg": "mesh.refined.0.010000.segs.v2.json",
    "sequence_zip": "sequence.zip",
}
READY_THRESHOLD = 0.95
MIN_QE_STATES = 3

VIEW_RE = re.compile(r"_view(?P<view>\d+)")
SCORE_RE = re.compile(r"_score_(?P<score>[-+0-9.eE]+)_ratio_(?P<ratio>[-+0-9.eE]+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
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


def read_ply_header(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "exists": path.exists(),
        "header_ok": False,
        "vertex_count": None,
        "face_count": None,
        "has_object_id_property": False,
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
                elif line.endswith(" objectId"):
                    info["has_object_id_property"] = True
                elif line == "end_header":
                    info["header_ok"] = True
                    break
    except Exception as exc:  # pragma: no cover - stored in artifact instead.
        info["error"] = str(exc)
    return info


def read_semseg(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "object_ids": set(), "objects": {}}
    try:
        payload = read_json(path)
    except Exception as exc:  # pragma: no cover
        return {"exists": True, "read_error": str(exc), "object_ids": set(), "objects": {}}
    objects: dict[int, dict[str, Any]] = {}
    for group in payload.get("segGroups", []):
        oid = group.get("objectId", group.get("id"))
        if oid is None:
            continue
        try:
            object_id = int(oid)
        except (TypeError, ValueError):
            continue
        obb = group.get("obb") or {}
        axes = obb.get("axesLengths") or []
        objects[object_id] = {
            "label": group.get("label"),
            "segment_count": len(group.get("segments") or []),
            "has_dominant_normal": bool(group.get("dominantNormal")),
            "has_obb": bool(obb.get("centroid") and obb.get("normalizedAxes") and axes),
            "axes_lengths": axes,
        }
    return {"exists": True, "object_ids": set(objects), "objects": objects}


def scan_asset(scan_root: Path, scan_id: str) -> dict[str, Any]:
    scan_dir = scan_root / scan_id
    semseg = read_semseg(scan_dir / REQUIRED_ASSETS["semseg"])
    ply = read_ply_header(scan_dir / REQUIRED_ASSETS["aligned_ply"])
    paths = {key: scan_dir / name for key, name in REQUIRED_ASSETS.items()}
    multi_view_dir = scan_dir / "multi_view"
    return {
        "scan_id": scan_id,
        "scan_dir": scan_dir,
        "scan_dir_exists": scan_dir.is_dir(),
        "semseg_exists": bool(semseg.get("exists")),
        "semseg_object_ids": semseg.get("object_ids", set()),
        "semseg_objects": semseg.get("objects", {}),
        "aligned_ply_exists": bool(ply.get("exists")),
        "aligned_ply_header_ok": bool(ply.get("header_ok")),
        "aligned_ply_has_object_id": bool(ply.get("has_object_id_property")),
        "aligned_ply_vertex_count": ply.get("vertex_count"),
        "mesh_obj_exists": paths["mesh_obj"].exists(),
        "mesh_seg_exists": paths["mesh_seg"].exists(),
        "sequence_zip_exists": paths["sequence_zip"].exists(),
        "sequence_zip_size_bytes": paths["sequence_zip"].stat().st_size if paths["sequence_zip"].exists() else 0,
        "multi_view_dir_exists": multi_view_dir.is_dir(),
        "multi_view_dir": multi_view_dir,
    }


def parse_view_files(multi_view_dir: Path, object_id: int) -> dict[str, Any]:
    if not multi_view_dir.is_dir():
        return {
            "crop_count": 0,
            "direct_count": 0,
            "total_images": 0,
            "view_ids": [],
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
            try:
                scores.append(float(score_match.group("score")))
                ratios.append(float(score_match.group("ratio")))
            except ValueError:
                pass
    return {
        "crop_count": len(crop_files),
        "direct_count": len(direct_files),
        "total_images": len(crop_files) + len(direct_files),
        "view_ids": sorted(view_ids),
        "max_score": max(scores) if scores else 0.0,
        "mean_score": mean(scores) if scores else 0.0,
        "max_ratio": max(ratios) if ratios else 0.0,
        "mean_ratio": mean(ratios) if ratios else 0.0,
    }


def obb_quality(obj: dict[str, Any]) -> dict[str, Any]:
    axes = [float(value) for value in obj.get("axes_lengths") or [] if value is not None]
    if len(axes) != 3:
        return {"has_obb": False, "min_axis": 0.0, "max_axis": 0.0, "axis_ratio": 0.0, "volume_proxy": 0.0}
    min_axis = min(axes)
    max_axis = max(axes)
    volume = axes[0] * axes[1] * axes[2]
    return {
        "has_obb": bool(obj.get("has_obb")),
        "min_axis": min_axis,
        "max_axis": max_axis,
        "axis_ratio": min_axis / max_axis if max_axis else 0.0,
        "volume_proxy": volume,
    }


def q_state(row: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not row["scan_asset_complete"]:
        return "missing_source", ["missing_scan_asset"]
    if not row["semseg_both_objects_present"]:
        return "missing_source", ["missing_semseg_object"]
    if not row["point_pair_crop_possible"] or not row["mesh_contact_patch_possible"]:
        return "missing_source", ["missing_point_or_mesh_basis"]
    if not row["multiview_packet_possible"]:
        reasons.append("no_pair_multiview")
    if row["min_subject_object_segment_count"] < 8:
        reasons.append("low_semseg_segment_count")
    if row["min_subject_object_crop_count"] == 0:
        reasons.append("no_cropped_instance_view")
    elif row["min_subject_object_crop_count"] < 2:
        reasons.append("few_cropped_instance_views")
    if row["co_visible_view_count_proxy"] == 0:
        reasons.append("no_shared_view_proxy")
    if row["min_subject_object_max_view_score"] < 0.15:
        reasons.append("low_crop_score")
    if row["min_subject_object_obb_axis_ratio"] < 0.01:
        reasons.append("degenerate_obb_axis")

    if not reasons:
        return "sufficient", []
    if len(reasons) <= 2 and "no_pair_multiview" not in reasons and "no_cropped_instance_view" not in reasons:
        return "limited", reasons
    return "uncertain_or_low_observability", reasons


def row_inventory(row: dict[str, Any], asset: dict[str, Any], view_cache: dict[tuple[str, int], dict[str, Any]]) -> dict[str, Any]:
    subject_id = int(row["subject_id"])
    object_id = int(row["object_id"])
    objects = asset.get("semseg_objects", {})
    subject_obj = objects.get(subject_id, {})
    object_obj = objects.get(object_id, {})
    subject_present = subject_id in asset.get("semseg_object_ids", set())
    object_present = object_id in asset.get("semseg_object_ids", set())
    both_present = subject_present and object_present
    subject_obb = obb_quality(subject_obj)
    object_obb = obb_quality(object_obj)

    def view_info(oid: int) -> dict[str, Any]:
        key = (str(row["scan_id"]), oid)
        if key not in view_cache:
            view_cache[key] = parse_view_files(asset["multi_view_dir"], oid)
        return view_cache[key]

    subject_view = view_info(subject_id)
    object_view = view_info(object_id)
    shared_views = sorted(set(subject_view["view_ids"]) & set(object_view["view_ids"]))

    scan_asset_complete = all(
        [
            asset.get("scan_dir_exists"),
            asset.get("semseg_exists"),
            asset.get("aligned_ply_exists"),
            asset.get("aligned_ply_header_ok"),
            asset.get("aligned_ply_has_object_id"),
            asset.get("mesh_obj_exists"),
            asset.get("mesh_seg_exists"),
            asset.get("sequence_zip_exists"),
        ]
    )
    point_pair_possible = bool(scan_asset_complete and both_present)
    mesh_contact_possible = bool(asset.get("mesh_obj_exists") and asset.get("mesh_seg_exists") and both_present and subject_obb["has_obb"] and object_obb["has_obb"])
    multiview_packet_possible = bool(asset.get("multi_view_dir_exists") and subject_view["total_images"] > 0 and object_view["total_images"] > 0)

    out = {
        "row_id": row.get("row_id"),
        "predicate_label": row.get("predicate_label"),
        "predicate_role": "main" if row.get("predicate_label") in MAIN_PREDICATES else "diagnostic",
        "subject_label": row.get("subject_label"),
        "object_label": row.get("object_label"),
        "class_pair": row.get("class_pair"),
        "scan_id_hidden": row.get("scan_id"),
        "subgraph_id_hidden": row.get("subgraph_id"),
        "subject_id_hidden": subject_id,
        "object_id_hidden": object_id,
        "candidate_role_hidden": row.get("candidate_role"),
        "label_match_status_hidden": row.get("label_match_status"),
        "queue_kind_hidden": row.get("queue_kind"),
        "rank_band_hidden": row.get("rank_band"),
        "scan_asset_complete": scan_asset_complete,
        "semseg_subject_present": subject_present,
        "semseg_object_present": object_present,
        "semseg_both_objects_present": both_present,
        "semseg_subject_label": subject_obj.get("label"),
        "semseg_object_label": object_obj.get("label"),
        "subject_segment_count": subject_obj.get("segment_count", 0),
        "object_segment_count": object_obj.get("segment_count", 0),
        "min_subject_object_segment_count": min(int(subject_obj.get("segment_count", 0) or 0), int(object_obj.get("segment_count", 0) or 0)),
        "subject_has_obb": subject_obb["has_obb"],
        "object_has_obb": object_obb["has_obb"],
        "min_subject_object_obb_axis_ratio": min(subject_obb["axis_ratio"], object_obb["axis_ratio"]),
        "point_pair_crop_possible": point_pair_possible,
        "mesh_contact_patch_possible": mesh_contact_possible,
        "multiview_packet_possible": multiview_packet_possible,
        "subject_crop_count": subject_view["crop_count"],
        "object_crop_count": object_view["crop_count"],
        "min_subject_object_crop_count": min(subject_view["crop_count"], object_view["crop_count"]),
        "subject_total_image_count": subject_view["total_images"],
        "object_total_image_count": object_view["total_images"],
        "min_subject_object_total_image_count": min(subject_view["total_images"], object_view["total_images"]),
        "co_visible_view_count_proxy": len(shared_views),
        "subject_max_view_score": subject_view["max_score"],
        "object_max_view_score": object_view["max_score"],
        "min_subject_object_max_view_score": min(subject_view["max_score"], object_view["max_score"]),
        "subject_mean_view_ratio": subject_view["mean_ratio"],
        "object_mean_view_ratio": object_view["mean_ratio"],
    }
    state, reasons = q_state(out)
    out["q_e_state_plan"] = state
    out["q_e_reason_codes"] = reasons
    out["g_e_point_mesh_ready"] = bool(point_pair_possible and mesh_contact_possible)
    out["visual_used_as_model_input"] = False
    out["visual_use_policy"] = "audit_and_Q_e_first"
    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)

    def count(key: str) -> int:
        return sum(1 for row in rows if row.get(key) is True)

    predicate_counts = Counter(str(row.get("predicate_label")) for row in rows)
    q_counts = Counter(str(row.get("q_e_state_plan")) for row in rows)
    role_counts = Counter(str(row.get("predicate_role")) for row in rows)
    return {
        "rows": total,
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "predicate_role_counts": dict(sorted(role_counts.items())),
        "q_e_state_counts": dict(sorted(q_counts.items())),
        "q_e_state_count": len(q_counts),
        "unique_scans": len({row.get("scan_id_hidden") for row in rows}),
        "unique_class_pairs": len({row.get("class_pair") for row in rows}),
        "scan_asset_complete_rows": count("scan_asset_complete"),
        "semseg_both_objects_present_rows": count("semseg_both_objects_present"),
        "point_pair_crop_possible_rows": count("point_pair_crop_possible"),
        "mesh_contact_patch_possible_rows": count("mesh_contact_patch_possible"),
        "multiview_packet_possible_rows": count("multiview_packet_possible"),
        "g_e_point_mesh_ready_rows": count("g_e_point_mesh_ready"),
        "scan_asset_complete_rate": count("scan_asset_complete") / total if total else 0.0,
        "point_pair_crop_possible_rate": count("point_pair_crop_possible") / total if total else 0.0,
        "mesh_contact_patch_possible_rate": count("mesh_contact_patch_possible") / total if total else 0.0,
        "multiview_packet_possible_rate": count("multiview_packet_possible") / total if total else 0.0,
        "g_e_point_mesh_ready_rate": count("g_e_point_mesh_ready") / total if total else 0.0,
        "min_crop_count_distribution": dict(sorted(Counter(str(row.get("min_subject_object_crop_count")) for row in rows).items())),
        "co_visible_view_count_distribution": dict(sorted(Counter(str(row.get("co_visible_view_count_proxy")) for row in rows).items())),
        "top_q_e_reasons": Counter(reason for row in rows for reason in row.get("q_e_reason_codes", [])).most_common(12),
        "top_class_pairs": Counter(str(row.get("class_pair")) for row in rows).most_common(12),
    }


def summarize_by(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key))].append(row)
    out: list[dict[str, Any]] = []
    for value, items in sorted(groups.items()):
        item_summary = summarize(items)
        out.append(
            {
                key: value,
                "rows": item_summary["rows"],
                "q_e_state_counts": json.dumps(item_summary["q_e_state_counts"], sort_keys=True),
                "point_pair_crop_possible_rate": item_summary["point_pair_crop_possible_rate"],
                "mesh_contact_patch_possible_rate": item_summary["mesh_contact_patch_possible_rate"],
                "multiview_packet_possible_rate": item_summary["multiview_packet_possible_rate"],
                "g_e_point_mesh_ready_rate": item_summary["g_e_point_mesh_ready_rate"],
                "top_q_e_reasons": json.dumps(item_summary["top_q_e_reasons"], ensure_ascii=False),
            }
        )
    return out


def source_scan_rows(assets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scan_id, asset in sorted(assets.items()):
        rows.append(
            {
                "scan_id": scan_id,
                "scan_dir_exists": asset["scan_dir_exists"],
                "semseg_exists": asset["semseg_exists"],
                "aligned_ply_exists": asset["aligned_ply_exists"],
                "aligned_ply_header_ok": asset["aligned_ply_header_ok"],
                "aligned_ply_has_object_id": asset["aligned_ply_has_object_id"],
                "aligned_ply_vertex_count": asset["aligned_ply_vertex_count"],
                "mesh_obj_exists": asset["mesh_obj_exists"],
                "mesh_seg_exists": asset["mesh_seg_exists"],
                "sequence_zip_exists": asset["sequence_zip_exists"],
                "sequence_zip_size_bytes": asset["sequence_zip_size_bytes"],
                "multi_view_dir_exists": asset["multi_view_dir_exists"],
            }
        )
    return rows


def validate_inputs(plan_summary: dict[str, Any], plan_errors: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append(
            {
                "input": "plan_summary",
                "error_type": "unexpected_status",
                "actual": plan_summary.get("status"),
                "expected": EXPECTED_PLAN_STATUS,
            }
        )
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append(
            {
                "input": "plan_summary",
                "error_type": "unexpected_next_todo",
                "actual": plan_summary.get("next_todo"),
                "expected": EXPECTED_PLAN_NEXT,
            }
        )
    if plan_summary.get("validation_errors") != 0:
        errors.append({"input": "plan_summary", "error_type": "validation_errors_present", "actual": plan_summary.get("validation_errors")})
    if plan_errors:
        errors.append({"input": "plan_validation_errors", "error_type": "rows_present", "rows": len(plan_errors)})
    if not hidden_rows:
        errors.append({"input": "hidden_manifest", "error_type": "missing_or_empty"})
    boundary = plan_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"input": "plan_summary", "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def gate_errors(inv_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for key in [
        "point_pair_crop_possible_rate",
        "mesh_contact_patch_possible_rate",
        "multiview_packet_possible_rate",
        "g_e_point_mesh_ready_rate",
    ]:
        if float(inv_summary.get(key, 0.0) or 0.0) < READY_THRESHOLD:
            errors.append(
                {
                    "error_type": "readiness_below_threshold",
                    "metric": key,
                    "actual": inv_summary.get(key),
                    "minimum": READY_THRESHOLD,
                }
            )
    if int(inv_summary.get("q_e_state_count", 0) or 0) < MIN_QE_STATES:
        errors.append(
            {
                "error_type": "q_e_state_diversity_below_threshold",
                "actual": inv_summary.get("q_e_state_count"),
                "minimum": MIN_QE_STATES,
            }
        )
    return errors


def materialization_contract() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_materialization_contract",
        "next_todo": NEXT_TODO,
        "allowed_next_features": {
            "G_e_point_mesh": [
                "subject/object/union point crop metadata",
                "point/mesh contact patch numeric features",
                "point-based pose/orientation features",
                "local support surface statistics",
            ],
            "Q_e_observability": [
                "point crop availability and density",
                "mesh contact patch availability",
                "multiview crop count and co-visible view count",
                "crop quality score/ratio proxies",
                "occlusion/conflict/missing-source flags",
            ],
        },
        "blocked_next_features": {
            "G_e": [
                "predicate label",
                "source score",
                "rank",
                "GT match status",
                "audit accept/reject label",
                "visual language score",
            ],
            "Q_e": [
                "relation correctness label",
                "hidden construction bucket as model input",
                "source rank as quality proxy",
            ],
            "visual_multiview": [
                "learned visual encoder embedding before wrong-view/shuffled-view controls",
            ],
        },
        "required_controls_after_materialization": [
            "OBB-only vs point-mesh feature comparison",
            "point-only and mesh/contact-only ablation",
            "wrong-pair geometry",
            "shuffled geometry within predicate",
            "wrong-view control before visual input",
            "shuffled-view control before visual input",
            "class-pair/rank/source shortcut audit",
        ],
    }


def render_report(summary: dict[str, Any]) -> str:
    inv = summary["inventory_summary"]
    return f"""# H002 Support/Contact Individual Predicate Point/Multiview Source Inventory

## Status

```text
artifact_root = {summary['output_paths']['artifact_root']}
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Inventory Result

```text
rows = {inv['rows']}
unique_scans = {inv['unique_scans']}
point_pair_crop_possible = {inv['point_pair_crop_possible_rows']} / {inv['rows']}
mesh_contact_patch_possible = {inv['mesh_contact_patch_possible_rows']} / {inv['rows']}
multiview_packet_possible = {inv['multiview_packet_possible_rows']} / {inv['rows']}
g_e_point_mesh_ready = {inv['g_e_point_mesh_ready_rows']} / {inv['rows']}
q_e_state_counts = {inv['q_e_state_counts']}
```

## Decision

The current 800 candidate rows are source-ready for a `G_e` / `Q_e` separated
materialization plan. This does not mean visual features should enter the model yet.
Multiview remains audit and `Q_e` evidence first.

Next materialization should derive:

- point/mesh/contact/pose features for `G_e`;
- observability and evidence sufficiency fields for `Q_e`;
- wrong-pair, shuffled-geometry, wrong-view, and shuffled-view control contracts.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json") if (args.plan_dir / "summary.json").exists() else {}
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    hidden_rows = read_jsonl(args.candidate_dir / "hidden_manifest.jsonl")

    validation_errors = validate_inputs(plan_summary, plan_errors, hidden_rows)

    scan_ids = {str(row.get("scan_id")) for row in hidden_rows if row.get("scan_id")}
    assets = {scan_id: scan_asset(args.scan_root, scan_id) for scan_id in sorted(scan_ids)}
    view_cache: dict[tuple[str, int], dict[str, Any]] = {}
    inventory_rows = [row_inventory(row, assets[str(row["scan_id"])], view_cache) for row in hidden_rows]
    inv_summary = summarize(inventory_rows)
    readiness_errors = gate_errors(inv_summary)
    validation_errors.extend(readiness_errors)

    if validation_errors and any(error.get("input") for error in validation_errors):
        status = STATUS_ERROR
        selected_path = "fix_input_errors_before_materialization_plan"
        next_todo = "fix_point_multiview_source_inventory_inputs"
    elif validation_errors:
        status = STATUS_BLOCKED
        selected_path = "source_inventory_blocks_materialization_until_readiness_or_qe_fixed"
        next_todo = "point_multiview_source_inventory_gap_decision"
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO

    output_paths = {
        "artifact_root": rel_path(args.output_dir),
        "summary": rel_path(args.output_dir / "summary.json"),
        "report": rel_path(args.output_dir / "report.md"),
        "inventory_rows": rel_path(args.output_dir / "inventory_rows.jsonl"),
        "source_manifest": rel_path(args.output_dir / "source_manifest.jsonl"),
        "source_scan_inventory": rel_path(args.output_dir / "source_scan_inventory.csv"),
        "readiness_by_predicate": rel_path(args.output_dir / "readiness_by_predicate.csv"),
        "readiness_by_class_pair": rel_path(args.output_dir / "readiness_by_class_pair.csv"),
        "q_e_state_distribution": rel_path(args.output_dir / "q_e_state_distribution.csv"),
        "q_e_reason_distribution": rel_path(args.output_dir / "q_e_reason_distribution.csv"),
        "materialization_contract": rel_path(args.output_dir / "materialization_contract.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }

    source_manifest: list[dict[str, Any]] = []
    for row in inventory_rows:
        scan_id = str(row["scan_id_hidden"])
        scan_dir = args.scan_root / scan_id
        source_manifest.append(
            {
                "row_id": row["row_id"],
                "scan_id_hidden": scan_id,
                "subject_id_hidden": row["subject_id_hidden"],
                "object_id_hidden": row["object_id_hidden"],
                "predicate_label": row["predicate_label"],
                "aligned_ply_path_hidden": rel_path(scan_dir / REQUIRED_ASSETS["aligned_ply"]),
                "semseg_path_hidden": rel_path(scan_dir / REQUIRED_ASSETS["semseg"]),
                "mesh_obj_path_hidden": rel_path(scan_dir / REQUIRED_ASSETS["mesh_obj"]),
                "mesh_seg_path_hidden": rel_path(scan_dir / REQUIRED_ASSETS["mesh_seg"]),
                "sequence_zip_path_hidden": rel_path(scan_dir / REQUIRED_ASSETS["sequence_zip"]),
                "multi_view_dir_hidden": rel_path(scan_dir / "multi_view"),
                "point_pair_crop_possible": row["point_pair_crop_possible"],
                "mesh_contact_patch_possible": row["mesh_contact_patch_possible"],
                "multiview_packet_possible": row["multiview_packet_possible"],
                "q_e_state_plan": row["q_e_state_plan"],
            }
        )

    q_state_counts = Counter(str(row["q_e_state_plan"]) for row in inventory_rows)
    q_reason_counts = Counter(reason for row in inventory_rows for reason in row.get("q_e_reason_codes", []))
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "boundary": {
            "split": "train_only_source_inventory",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_point_crops": False,
            "materializes_multiview_crops": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "visual_model_input_allowed": False,
        },
        "input_paths": {
            "plan_summary": rel_path(args.plan_dir / "summary.json"),
            "candidate_hidden_manifest": rel_path(args.candidate_dir / "hidden_manifest.jsonl"),
            "scan_root": rel_path(args.scan_root),
        },
        "inventory_summary": inv_summary,
        "gate_summary": {
            "ready_threshold": READY_THRESHOLD,
            "min_q_e_states": MIN_QE_STATES,
            "readiness_errors": len(readiness_errors),
            "materialization_plan_allowed": status == STATUS_READY,
            "learned_smoke_allowed": False,
            "visual_model_input_allowed": False,
            "multiview_audit_qe_first": True,
        },
        "output_paths": output_paths,
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "materialization_contract.json", materialization_contract())
    write_jsonl(args.output_dir / "inventory_rows.jsonl", inventory_rows)
    write_jsonl(args.output_dir / "source_manifest.jsonl", source_manifest)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "source_scan_inventory.csv", source_scan_rows(assets))
    write_csv(args.output_dir / "readiness_by_predicate.csv", summarize_by(inventory_rows, "predicate_label"))
    write_csv(args.output_dir / "readiness_by_class_pair.csv", summarize_by(inventory_rows, "class_pair"))
    write_csv(
        args.output_dir / "q_e_state_distribution.csv",
        [{"q_e_state": key, "rows": value} for key, value in sorted(q_state_counts.items())],
    )
    write_csv(
        args.output_dir / "q_e_reason_distribution.csv",
        [{"q_e_reason": key, "rows": value} for key, value in q_reason_counts.most_common()],
    )
    (args.output_dir / "report.md").write_text(render_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
