#!/usr/bin/env python3
"""Inventory source availability for the H002 support/contact harder route."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan"
DEFAULT_OFFICIAL_MAT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_materialization/latest"
DEFAULT_OFFICIAL_SCHEMA_AUDIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_schema_audit/latest"
DEFAULT_TRAIN_POINT_INV_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory"
DEFAULT_TRAIN_POINT_MAT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol"

EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol_input_errors"
SELECTED_PATH = "support_contact_harder_route_source_inventory_ready_select_materialization_plan"
NEXT_TODO = "compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory"

MAIN_PREDICATES = ["standing on", "lying on"]
DIAGNOSTIC_PREDICATES = ["supported by"]
SUPPORT_FAMILY = "support_contact"

REQUIRED_FEATURES = [
    "g_vertical_gap",
    "g_xy_support_overlap",
    "g_contact_patch_ratio",
    "g_support_surface_normal_alignment",
    "g_subject_principal_axis",
    "g_bottom_surface_proximity",
    "g_local_contact_point_density",
    "g_mesh_gap_intersection",
    "g_surface_alignment",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--official-materialization-dir", type=Path, default=DEFAULT_OFFICIAL_MAT_DIR)
    parser.add_argument("--official-schema-audit-dir", type=Path, default=DEFAULT_OFFICIAL_SCHEMA_AUDIT_DIR)
    parser.add_argument("--train-point-inventory-dir", type=Path, default=DEFAULT_TRAIN_POINT_INV_DIR)
    parser.add_argument("--train-point-materialization-dir", type=Path, default=DEFAULT_TRAIN_POINT_MAT_DIR)
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


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


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
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def validate_inputs(protocol_summary: dict[str, Any], protocol_contract: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol_summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol_summary.get("status")})
    if protocol_summary.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol_summary.get("next_todo")})
    if protocol_summary.get("validation_errors") != 0:
        errors.append({"error_type": "protocol_validation_errors", "actual": protocol_summary.get("validation_errors")})
    if line_count(args.protocol_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "protocol_validation_errors_file_not_empty"})
    if protocol_contract.get("main_predicates") != MAIN_PREDICATES:
        errors.append({"error_type": "unexpected_main_predicates", "actual": protocol_contract.get("main_predicates")})
    if protocol_contract.get("diagnostic_predicates") != DIAGNOSTIC_PREDICATES:
        errors.append({"error_type": "unexpected_diagnostic_predicates", "actual": protocol_contract.get("diagnostic_predicates")})
    if protocol_contract.get("required_geometry_evidence") != REQUIRED_FEATURES:
        errors.append({"error_type": "unexpected_required_geometry_evidence", "actual": protocol_contract.get("required_geometry_evidence")})

    required_files = [
        args.official_materialization_dir / "model_safe_view.jsonl",
        args.official_materialization_dir / "hidden_manifest.jsonl",
        args.official_materialization_dir / "row_manifest.json",
        args.official_schema_audit_dir / "shortcut_risk_table.csv",
        args.official_schema_audit_dir / "label_balance.csv",
        args.official_schema_audit_dir / "control_readiness.csv",
        args.train_point_inventory_dir / "summary.json",
        args.train_point_materialization_dir / "summary.json",
        args.train_point_materialization_dir / "feature_stats_summary.csv",
        args.train_point_materialization_dir / "model_safe_view.jsonl",
        args.scan_root,
    ]
    for path in required_files:
        if not path.exists():
            errors.append({"error_type": "missing_required_input", "path": rel_path(path)})
    return errors


def official_support_rows(model_safe_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(model_safe_path):
        if row.get("route_family") == SUPPORT_FAMILY and row.get("predicate_label") in MAIN_PREDICATES:
            rows.append(row)
    return rows


def train_point_rows(model_safe_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(model_safe_path):
        t_e = row.get("feature_blocks", {}).get("T_e", {})
        if t_e.get("predicate_family") == SUPPORT_FAMILY and t_e.get("predicate_label") in MAIN_PREDICATES + DIAGNOSTIC_PREDICATES:
            rows.append(row)
    return rows


def get_class_pair_from_official(row: dict[str, Any]) -> str:
    t_e = row.get("feature_blocks", {}).get("T_e", {})
    return f"{t_e.get('subject_class_label')}->{t_e.get('object_class_label')}"


def get_class_pair_from_train(row: dict[str, Any]) -> str:
    t_e = row.get("feature_blocks", {}).get("T_e", {})
    return f"{t_e.get('subject_class_text')}->{t_e.get('object_class_text')}"


def official_row_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    predicate_counts = Counter(row.get("predicate_label") for row in rows)
    label_counts = Counter(str(row.get("target_y")) for row in rows)
    class_pair_counts = Counter(get_class_pair_from_official(row) for row in rows)
    predicate_label_counts = Counter(f"{row.get('predicate_label')}|{row.get('target_y')}" for row in rows)
    scans = {row.get("scan_id") for row in rows}
    feature_names: set[str] = set()
    feature_present_counts: Counter[str] = Counter()
    for row in rows:
        g_e = row.get("feature_blocks", {}).get("G_e", {})
        names = g_e.get("g_e_feature_names") or []
        feature_names.update(names)
        vector = g_e.get("g_e_feature_vector") or {}
        for name in names:
            if name in vector and vector[name] is not None:
                feature_present_counts[name] += 1
    return {
        "rows": len(rows),
        "unique_scans": len(scans),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "predicate_label_counts": dict(sorted(predicate_label_counts.items())),
        "unique_class_pairs": len(class_pair_counts),
        "largest_class_pair_rows": max(class_pair_counts.values(), default=0),
        "top_class_pairs": class_pair_counts.most_common(12),
        "feature_names": sorted(feature_names),
        "feature_complete_counts": dict(sorted(feature_present_counts.items())),
    }


def train_point_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    predicate_counts = Counter(row.get("feature_blocks", {}).get("T_e", {}).get("predicate_label") for row in rows)
    model_use_counts = Counter(row.get("model_use") for row in rows)
    label_counts = Counter(str(row.get("labels", {}).get("C_e")) for row in rows)
    class_pair_counts = Counter(get_class_pair_from_train(row) for row in rows)
    feature_complete_counts: Counter[str] = Counter()
    all_features: set[str] = set()
    for row in rows:
        for block_name, block in row.get("feature_blocks", {}).items():
            if not block_name.startswith("G_e_"):
                continue
            for feature_name, value in block.items():
                full_name = f"{block_name}.{feature_name}"
                all_features.add(full_name)
                if value is not None:
                    feature_complete_counts[full_name] += 1
    return {
        "rows": len(rows),
        "main_rows": model_use_counts.get("main_train_candidate_if_schema_audit_passes", 0),
        "diagnostic_rows": model_use_counts.get("diagnostic_only", 0),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "unique_class_pairs": len(class_pair_counts),
        "largest_class_pair_rows": max(class_pair_counts.values(), default=0),
        "top_class_pairs": class_pair_counts.most_common(12),
        "feature_count": len(all_features),
        "feature_names": sorted(all_features),
        "feature_complete_counts": dict(sorted(feature_complete_counts.items())),
    }


def scan_semseg(scan_root: Path, scan_id: str) -> dict[str, Any]:
    scan_dir = scan_root / scan_id
    semseg_path = scan_dir / "semseg.v2.json"
    info = {
        "scan_id": scan_id,
        "semseg_exists": semseg_path.exists(),
        "mesh_seg_exists": (scan_dir / "mesh.refined.0.010000.segs.v2.json").exists(),
        "mesh_obj_exists": (scan_dir / "mesh.refined.v2.obj").exists(),
        "aligned_ply_exists": (scan_dir / "labels.instances.align.annotated.v2.ply").exists(),
        "sequence_zip_exists": (scan_dir / "sequence.zip").exists(),
        "multi_view_dir_exists": (scan_dir / "multi_view").exists(),
        "objects": {},
    }
    if not semseg_path.exists():
        return info
    try:
        payload = read_json(semseg_path)
    except json.JSONDecodeError as exc:
        info["semseg_error"] = str(exc)
        return info
    objects: dict[int, dict[str, Any]] = {}
    for group in payload.get("segGroups", []):
        object_id = group.get("objectId", group.get("id"))
        if object_id is None:
            continue
        try:
            oid = int(object_id)
        except (TypeError, ValueError):
            continue
        obb = group.get("obb") or {}
        objects[oid] = {
            "has_obb": bool(obb.get("centroid") and obb.get("axesLengths") and obb.get("normalizedAxes")),
            "has_dominant_normal": bool(group.get("dominantNormal")),
            "segment_count": len(group.get("segments") or []),
            "label": group.get("label"),
        }
    info["objects"] = objects
    return info


def official_asset_inventory(rows: list[dict[str, Any]], scan_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cache: dict[str, dict[str, Any]] = {}
    pair_rows: list[dict[str, Any]] = []
    counters = Counter()
    for row in rows:
        scan_id = str(row.get("scan_id"))
        if scan_id not in cache:
            cache[scan_id] = scan_semseg(scan_root, scan_id)
        scan_info = cache[scan_id]
        subject_id = int(row.get("subject_id"))
        object_id = int(row.get("object_id"))
        objects = scan_info.get("objects", {})
        subject = objects.get(subject_id, {})
        obj = objects.get(object_id, {})
        pair_obb = bool(subject.get("has_obb") and obj.get("has_obb"))
        pair_normal = bool(subject.get("has_dominant_normal") and obj.get("has_dominant_normal"))
        pair_segments = bool(subject.get("segment_count", 0) > 0 and obj.get("segment_count", 0) > 0)
        asset_row = {
            "candidate_id": row.get("candidate_id"),
            "scan_id": scan_id,
            "predicate_label": row.get("predicate_label"),
            "target_y": row.get("target_y"),
            "class_pair": get_class_pair_from_official(row),
            "semseg_exists": scan_info.get("semseg_exists"),
            "aligned_ply_exists": scan_info.get("aligned_ply_exists"),
            "mesh_seg_exists": scan_info.get("mesh_seg_exists"),
            "mesh_obj_exists": scan_info.get("mesh_obj_exists"),
            "sequence_zip_exists": scan_info.get("sequence_zip_exists"),
            "multi_view_dir_exists": scan_info.get("multi_view_dir_exists"),
            "pair_obb_available": pair_obb,
            "pair_dominant_normal_available": pair_normal,
            "pair_segment_membership_available": pair_segments,
            "subject_segment_count": subject.get("segment_count", 0),
            "object_segment_count": obj.get("segment_count", 0),
        }
        pair_rows.append(asset_row)
        for key, value in asset_row.items():
            if isinstance(value, bool) and value:
                counters[key] += 1
    scan_counters = Counter()
    for scan_info in cache.values():
        for key in ["semseg_exists", "aligned_ply_exists", "mesh_seg_exists", "mesh_obj_exists", "sequence_zip_exists", "multi_view_dir_exists"]:
            if scan_info.get(key):
                scan_counters[key] += 1
    summary = {
        "support_contact_rows": len(rows),
        "unique_scans": len(cache),
        "scan_asset_counts": dict(sorted(scan_counters.items())),
        "pair_asset_counts": dict(sorted(counters.items())),
    }
    return summary, pair_rows


def shortcut_rows(official_schema_dir: Path) -> list[dict[str, Any]]:
    rows = read_csv(official_schema_dir / "shortcut_risk_table.csv")
    out = []
    for row in rows:
        if row.get("family") == SUPPORT_FAMILY:
            out.append(
                {
                    "family": row.get("family"),
                    "probe": row.get("probe"),
                    "majority_accuracy": row.get("majority_accuracy"),
                    "risk": row.get("risk"),
                    "blocks_family_main_claim": row.get("blocks_family_main_claim"),
                }
            )
    return out


def class_pair_balance_rows(official_rows: list[dict[str, Any]], train_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stats: dict[str, Counter[str]] = defaultdict(Counter)
    for row in official_rows:
        key = f"official_validation::{get_class_pair_from_official(row)}"
        stats[key][f"{row.get('predicate_label')}|{row.get('target_y')}"] += 1
        stats[key]["rows"] += 1
    for row in train_rows:
        t_e = row.get("feature_blocks", {}).get("T_e", {})
        labels = row.get("labels", {})
        key = f"train_point_multiview::{get_class_pair_from_train(row)}"
        stats[key][f"{t_e.get('predicate_label')}|{labels.get('C_e')}"] += 1
        stats[key]["rows"] += 1
    output = []
    for key, counts in sorted(stats.items(), key=lambda item: (-item[1]["rows"], item[0]))[:80]:
        source, class_pair = key.split("::", 1)
        label_counts = {k: v for k, v in counts.items() if k != "rows"}
        output.append(
            {
                "source": source,
                "class_pair": class_pair,
                "rows": counts["rows"],
                "label_distribution": json.dumps(label_counts, ensure_ascii=False, sort_keys=True),
            }
        )
    return output


def feature_availability_rows(
    official_summary: dict[str, Any],
    official_asset_summary: dict[str, Any],
    train_point_summary_payload: dict[str, Any],
    train_feature_stats: list[dict[str, str]],
) -> list[dict[str, Any]]:
    official_features = set(official_summary.get("feature_names", []))
    train_features = {row.get("feature") for row in train_feature_stats}
    pair_counts = official_asset_summary.get("pair_asset_counts", {})
    total_official = official_asset_summary.get("support_contact_rows", 0)
    train_rows = train_point_summary_payload.get("materialized_counts", {}).get("rows", 0)

    def count_for_feature(feature: str) -> tuple[int, str, str]:
        if feature == "g_vertical_gap":
            return (
                official_summary["feature_complete_counts"].get("surface_gap_subject_bottom_to_object_top", 0),
                "current_official_G_e",
                "direct",
            )
        if feature == "g_xy_support_overlap":
            return (
                max(
                    official_summary["feature_complete_counts"].get("xy_overlap_min_ratio", 0),
                    official_summary["feature_complete_counts"].get("xy_overlap_max_ratio", 0),
                ),
                "current_official_G_e",
                "direct",
            )
        if feature == "g_contact_patch_ratio":
            return (
                official_summary["feature_complete_counts"].get("support_contact_likelihood_proxy", 0),
                "current_official_proxy_plus_point_extraction_available",
                "proxy_current_true_patch_requires_extraction",
            )
        if feature == "g_support_surface_normal_alignment":
            return (
                pair_counts.get("pair_dominant_normal_available", 0),
                "semseg_dominant_normal_derivable",
                "requires_materializer_update",
            )
        if feature == "g_subject_principal_axis":
            return (
                official_summary["feature_complete_counts"].get("subject_vertical_extent_ratio", 0),
                "current_official_partial_plus_obb_axes_derivable",
                "partial_current",
            )
        if feature == "g_bottom_surface_proximity":
            return (
                official_summary["feature_complete_counts"].get("abs_surface_gap_subject_bottom_to_object_top", 0),
                "current_official_G_e",
                "direct",
            )
        if feature == "g_local_contact_point_density":
            return (
                min(pair_counts.get("aligned_ply_exists", 0), pair_counts.get("pair_segment_membership_available", 0)),
                "aligned_ply_and_segments_available",
                "requires_point_extraction",
            )
        if feature == "g_mesh_gap_intersection":
            return (
                min(pair_counts.get("mesh_obj_exists", 0), pair_counts.get("mesh_seg_exists", 0), pair_counts.get("pair_segment_membership_available", 0)),
                "mesh_and_segments_available",
                "requires_mesh_extraction",
            )
        if feature == "g_surface_alignment":
            return (
                pair_counts.get("pair_dominant_normal_available", 0),
                "semseg_normals_or_obb_axes_derivable",
                "requires_materializer_update",
            )
        return (0, "unknown", "unknown")

    train_feature_map = {
        "g_vertical_gap": ["G_e_contact_patch.point_surface_gap_subject_bottom_to_object_top", "G_e_obb_baseline.surface_gap_subject_bottom_to_object_top"],
        "g_xy_support_overlap": ["G_e_contact_patch.point_xy_overlap_min_ratio", "G_e_obb_baseline.xy_overlap_min_ratio"],
        "g_contact_patch_ratio": ["G_e_contact_patch.point_support_contact_likelihood_proxy", "G_e_contact_patch.point_object_top_near_subject_bottom"],
        "g_support_surface_normal_alignment": ["G_e_obb_baseline.normal_alignment", "G_e_obb_baseline.support_normal_verticality"],
        "g_subject_principal_axis": ["G_e_obb_baseline.subject_major_axis_upness", "G_e_obb_baseline.subject_minor_axis_upness", "G_e_point_pose.subject_vertical_extent_ratio"],
        "g_bottom_surface_proximity": ["G_e_contact_patch.point_abs_surface_gap_subject_bottom_to_object_top", "G_e_obb_baseline.abs_surface_gap_subject_bottom_to_object_top"],
        "g_local_contact_point_density": ["G_e_point_pose.pair_min_point_count", "G_e_point_pose.subject_point_count", "G_e_point_pose.object_point_count"],
        "g_mesh_gap_intersection": [],
        "g_surface_alignment": ["G_e_obb_baseline.normal_alignment", "G_e_obb_baseline.subject_normal_upness", "G_e_obb_baseline.object_normal_upness"],
    }

    rows = []
    for feature in REQUIRED_FEATURES:
        official_count, official_source, implementation_status = count_for_feature(feature)
        train_candidates = train_feature_map[feature]
        train_available = bool(set(train_candidates) & train_features)
        if feature == "g_mesh_gap_intersection":
            train_status = "q_e_mesh_possible_only_no_numeric_mesh_gap"
        elif train_available:
            train_status = "train_point_multiview_numeric_available"
        else:
            train_status = "not_materialized"
        official_rate = official_count / total_official if total_official else 0.0
        rows.append(
            {
                "required_feature": feature,
                "official_available_or_derivable_rows": official_count,
                "official_support_rows": total_official,
                "official_available_or_derivable_rate": round(official_rate, 6),
                "official_source_status": official_source,
                "train_point_rows": train_rows,
                "train_status": train_status,
                "implementation_status": implementation_status,
                "materialization_decision": "include_now" if implementation_status in {"direct", "partial_current"} else "include_after_extractor_update",
            }
        )
    return rows


def source_split_rows(
    official_summary: dict[str, Any],
    official_asset_summary: dict[str, Any],
    train_point_inv_summary: dict[str, Any],
    train_point_mat_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    inv = train_point_inv_summary.get("inventory_summary", {})
    mat = train_point_mat_summary.get("materialized_counts", {})
    return [
        {
            "source_split": "official_validation_current_materialization",
            "rows": official_summary.get("rows"),
            "main_rows": official_summary.get("rows"),
            "unique_scans": official_summary.get("unique_scans"),
            "feature_status": "OBB proxy G_e currently materialized",
            "metric_status": "validation_result_exists_not_test",
            "next_use": "needs harder G_e materializer update",
        },
        {
            "source_split": "official_validation_source_assets",
            "rows": official_asset_summary.get("support_contact_rows"),
            "main_rows": official_asset_summary.get("support_contact_rows"),
            "unique_scans": official_asset_summary.get("unique_scans"),
            "feature_status": "semseg/PLY/mesh assets available for extractor",
            "metric_status": "inventory_only",
            "next_use": "materialize richer predicate-independent G_e",
        },
        {
            "source_split": "train_point_multiview_inventory",
            "rows": inv.get("rows"),
            "main_rows": inv.get("predicate_role_counts", {}).get("main"),
            "unique_scans": inv.get("unique_scans"),
            "feature_status": "point/mesh/multiview ready rate recorded",
            "metric_status": "train_only_inventory",
            "next_use": "schema reference for harder G_e materializer",
        },
        {
            "source_split": "train_point_multiview_materialization",
            "rows": mat.get("rows"),
            "main_rows": mat.get("main_rows"),
            "unique_scans": mat.get("scans_parsed"),
            "feature_status": "numeric point/OBB support-contact features materialized",
            "metric_status": "train_only_not_paper_metric",
            "next_use": "feature template and sanity source",
        },
    ]


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "selected_path": SELECTED_PATH,
        "purpose": "Plan and implement richer support/contact hard-route materialization after source inventory.",
        "main_predicates": MAIN_PREDICATES,
        "diagnostic_predicates": DIAGNOSTIC_PREDICATES,
        "must_preserve": [
            "T_e + G_e only for main C_e",
            "Z_e excluded from main C_e",
            "Q_e excluded from main C_e",
            "hidden construction fields excluded from model-safe view",
            "official test unused",
        ],
        "materialization_requirements": [
            "carry over direct OBB features: vertical gap, XY overlap, bottom proximity",
            "add OBB/semseg normal-derived support surface and surface-alignment features",
            "add point/segment-derived local contact density features where PLY and segment membership exist",
            "keep mesh gap/intersection as optional extractor or explicit missing-mask if not implemented",
            "write model_safe_view and hidden_manifest separately",
            "repeat predicate/class-pair shortcut audit before metric runner",
        ],
        "blocked_actions": [
            "do not run official test",
            "do not promote validation metric as test result",
            "do not use source score/rank in C_e",
            "do not use Q_e as truth label",
            "do not claim support_contact solved before controls pass",
        ],
    }


def write_report(
    path: Path,
    summary: dict[str, Any],
    source_rows: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    shortcut_rows_payload: list[dict[str, Any]],
    contract: dict[str, Any],
) -> None:
    lines = [
        "# H002 Support/Contact Harder Route Source Inventory After Protocol",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {summary['output_artifacts']['artifact_root']}",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Judgment",
        "",
        "The source inventory supports continuing to a harder support/contact materialization plan.",
        "The current official validation materialization has balanced `standing on` / `lying on` rows,",
        "but its current `G_e` is still mostly OBB proxy geometry. The train-side point/multiview",
        "artifact already shows that richer point/pose/contact features can be materialized, and",
        "official validation scan assets contain the semseg, PLY, mesh, segment, and normal fields",
        "needed for an extractor update.",
        "",
        "This is still not a new metric run and not a paper result.",
        "",
        "## Source Splits",
        "",
        "| Source | Rows | Main Rows | Scans | Feature Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in source_rows:
        lines.append(
            f"| `{row['source_split']}` | {row.get('rows')} | {row.get('main_rows')} | {row.get('unique_scans')} | {row.get('feature_status')} |"
        )
    lines.extend(["", "## Required G_e Availability", "", "| Feature | Official Rate | Official Status | Train Status | Decision |", "| --- | ---: | --- | --- | --- |"])
    for row in feature_rows:
        lines.append(
            f"| `{row['required_feature']}` | {row['official_available_or_derivable_rate']:.6f} | {row['official_source_status']} | {row['train_status']} | {row['materialization_decision']} |"
        )
    lines.extend(["", "## Shortcut Caveat", "", "| Probe | Majority Acc. | Risk | Blocks Family Main Claim |", "| --- | ---: | --- | --- |"])
    for row in shortcut_rows_payload:
        if row.get("probe") in {"predicate_only", "predicate_x_class_pair", "class_pair"}:
            lines.append(
                f"| `{row['probe']}` | {row.get('majority_accuracy')} | {row.get('risk')} | {row.get('blocks_family_main_claim')} |"
            )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Proceed to a harder-route materialization plan.",
            "- Reuse official validation only as eval/materialization source; official test remains unused.",
            "- Treat current support/contact validation metric as diagnostic until richer `G_e` is materialized and shortcut controls pass.",
            "- Keep `Z_e` and `Q_e` out of the main `C_e` input.",
            "",
            "## Next Contract",
            "",
            "```json",
            json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir

    protocol_summary = read_json(args.protocol_dir / "summary.json")
    protocol_contract = read_json(args.protocol_dir / "next_contract.json")
    validation_errors = validate_inputs(protocol_summary, protocol_contract, args)

    official_rows = official_support_rows(args.official_materialization_dir / "model_safe_view.jsonl") if not validation_errors else []
    train_rows = train_point_rows(args.train_point_materialization_dir / "model_safe_view.jsonl") if not validation_errors else []

    official_summary = official_row_summary(official_rows)
    train_summary = train_point_summary(train_rows)
    official_asset_summary, official_pair_assets = official_asset_inventory(official_rows, args.scan_root) if official_rows else ({}, [])
    train_point_inv_summary = read_json(args.train_point_inventory_dir / "summary.json") if (args.train_point_inventory_dir / "summary.json").exists() else {}
    train_point_mat_summary = read_json(args.train_point_materialization_dir / "summary.json") if (args.train_point_materialization_dir / "summary.json").exists() else {}
    train_feature_stats = read_csv(args.train_point_materialization_dir / "feature_stats_summary.csv")
    shortcuts = shortcut_rows(args.official_schema_audit_dir)

    source_rows = source_split_rows(official_summary, official_asset_summary, train_point_inv_summary, train_point_mat_summary)
    feature_rows = feature_availability_rows(official_summary, official_asset_summary, train_point_mat_summary, train_feature_stats)
    class_pair_rows = class_pair_balance_rows(official_rows, train_rows)
    contract = next_contract()

    protocol_ready = not validation_errors
    status = STATUS_READY if protocol_ready else STATUS_ERRORS
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if protocol_ready else "blocked_fix_protocol_inputs_before_source_inventory",
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO if protocol_ready else EXPECTED_PROTOCOL_NEXT,
        "input_artifacts": {
            "protocol_summary": rel_path(args.protocol_dir / "summary.json"),
            "protocol_next_contract": rel_path(args.protocol_dir / "next_contract.json"),
            "official_model_safe_view": rel_path(args.official_materialization_dir / "model_safe_view.jsonl"),
            "official_hidden_manifest": rel_path(args.official_materialization_dir / "hidden_manifest.jsonl"),
            "official_schema_shortcut_risk": rel_path(args.official_schema_audit_dir / "shortcut_risk_table.csv"),
            "train_point_inventory_summary": rel_path(args.train_point_inventory_dir / "summary.json"),
            "train_point_materialization_summary": rel_path(args.train_point_materialization_dir / "summary.json"),
            "train_point_feature_stats": rel_path(args.train_point_materialization_dir / "feature_stats_summary.csv"),
            "scan_root": rel_path(args.scan_root),
        },
        "decision": {
            "source_inventory_ready": protocol_ready,
            "official_validation_rows": official_summary.get("rows", 0),
            "official_validation_unique_scans": official_summary.get("unique_scans", 0),
            "train_point_multiview_rows": train_summary.get("rows", 0),
            "train_point_multiview_main_rows": train_summary.get("main_rows", 0),
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "current_official_g_e_is_hard_route_complete": False,
            "materialization_plan_allowed": protocol_ready,
            "support_contact_shortcut_caveat": "predicate_x_class_pair_high_risk",
            "z_e_excluded_from_main_c_e": True,
            "q_e_excluded_from_main_c_e": True,
        },
        "inventory_summary": {
            "official": official_summary,
            "official_assets": official_asset_summary,
            "train_point_multiview": train_summary,
        },
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "source_split_inventory": rel_path(output_dir / "source_split_inventory.csv"),
            "geometry_evidence_availability": rel_path(output_dir / "geometry_evidence_availability.csv"),
            "official_pair_asset_inventory": rel_path(output_dir / "official_pair_asset_inventory.jsonl"),
            "class_pair_balance": rel_path(output_dir / "class_pair_balance.csv"),
            "shortcut_caveat": rel_path(output_dir / "shortcut_caveat.csv"),
            "next_contract": rel_path(output_dir / "next_contract.json"),
            "report": rel_path(output_dir / "report.md"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(output_dir / "source_split_inventory.csv", source_rows)
    write_csv(output_dir / "geometry_evidence_availability.csv", feature_rows)
    write_jsonl(output_dir / "official_pair_asset_inventory.jsonl", official_pair_assets)
    write_csv(output_dir / "class_pair_balance.csv", class_pair_rows)
    write_csv(output_dir / "shortcut_caveat.csv", shortcuts)
    write_json(output_dir / "next_contract.json", contract)
    write_report(output_dir / "report.md", summary, source_rows, feature_rows, shortcuts, contract)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
