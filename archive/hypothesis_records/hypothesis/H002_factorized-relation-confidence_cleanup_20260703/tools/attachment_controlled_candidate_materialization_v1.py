#!/usr/bin/env python3
"""Materialize the H002 attachment controlled candidate dataset.

This runner repackages the v20 endpoint-balanced 400-row preview into the
current H002 compatibility-learning schema and joins predicate-independent raw
pair geometry through the selected directed pair.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H002_ROOT.parents[2]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PLAN_DIR = H002_ROOT / "artifacts/attachment_controlled_expansion_plan_v1"
DEFAULT_PREVIEW_ROWS = (
    RGA_ROOT
    / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan"
    / "preview_internal_400.jsonl"
)
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/attachment_controlled_candidates_v1"

STATUS_READY = "h002_attachment_controlled_candidate_materialization_v1_ready"
STATUS_ERRORS = "h002_attachment_controlled_candidate_materialization_v1_input_errors"
NEXT_TODO = "attachment_controlled_candidate_smoke_v1"

PRIMARY_PREDICATES = {"attached to", "hanging on"}
DIAGNOSTIC_PREDICATES = {"connected to"}
POSITIVE_PROXY = "primary_positive_anchor_proxy"
NEGATIVE_PROXY = "primary_hard_negative_proxy"
CONNECTED_NEAR_PROXY = "connected_near_or_overlap_diagnostic"
CONNECTED_FAR_PROXY = "connected_far_or_functional_ambiguous_diagnostic"

GEOMETRY_ALLOWED_RAW_KEYS = (
    "center_delta_z",
    "normalized_center_delta_z",
    "normalized_distance_3d",
    "normalized_distance_xy",
    "projected_iou_xy",
    "projected_subject_overlap_ratio",
    "projected_object_overlap_ratio",
    "vertical_gap_subject_on_object",
    "near_contact",
    "loose_near_contact",
    "far_separated",
    "projected_overlap_support",
)

GEOMETRY_BLOCKED_FRAGMENTS = (
    "predicate",
    "family",
    "source",
    "rank",
    "label",
    "hidden",
    "status",
    "bucket",
    "target",
    "semantic",
    "machine",
    "hint",
    "cell",
    "review",
    "reason",
    "witness_score",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--preview-rows", type=Path, default=DEFAULT_PREVIEW_ROWS)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force-python-scan", action="store_true")
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
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


def stable_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def stable_group_id(*parts: Any) -> str:
    return "h002_attach_ctrlcand_v1_group_" + stable_hash("|".join(str(part) for part in parts))[:16]


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def bool_float(value: Any) -> float:
    return 1.0 if value is True else 0.0


def closeness(value: float | None) -> float:
    if value is None:
        return 0.0
    return 1.0 / (1.0 + max(abs(value), 0.0))


def normalize_rank_band(rank: Any, fallback: str | None = None) -> str:
    value = safe_float(rank)
    if value is None:
        return fallback or "not_available"
    if value <= 20:
        return "top_20"
    if value <= 100:
        return "top_100"
    if value <= 200:
        return "rank_101_200"
    if value <= 500:
        return "rank_201_500"
    if value <= 1000:
        return "rank_501_1000"
    return "rank_over_1000"


def max_overlap(raw: dict[str, Any]) -> float:
    return max(
        safe_float(raw.get("projected_iou_xy"), 0.0) or 0.0,
        safe_float(raw.get("projected_subject_overlap_ratio"), 0.0) or 0.0,
        safe_float(raw.get("projected_object_overlap_ratio"), 0.0) or 0.0,
    )


def derived_near_flags(raw: dict[str, Any]) -> dict[str, bool]:
    n3d = safe_float(raw.get("normalized_distance_3d"))
    nxy = safe_float(raw.get("normalized_distance_xy"))
    iou = safe_float(raw.get("projected_iou_xy"), 0.0) or 0.0
    overlap = max_overlap(raw)
    near = (n3d is not None and n3d <= 0.30) or (nxy is not None and nxy <= 0.25) or iou >= 0.05 or overlap >= 0.15
    loose_near = (n3d is not None and n3d <= 0.45) or (nxy is not None and nxy <= 0.40) or iou >= 0.02 or overlap >= 0.08
    far = (
        (n3d is not None and n3d >= 0.75)
        and (nxy is not None and nxy >= 0.65)
        and iou < 0.01
        and overlap < 0.03
    )
    return {"near_contact": near, "loose_near_contact": loose_near, "far_separated": far, "projected_overlap_support": overlap >= 0.08}


def validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != "h002_attachment_controlled_expansion_plan_v1_ready":
        errors.append({"error_type": "unexpected_plan_status", "actual": plan.get("status")})
    if plan.get("next_todo") != "attachment_controlled_candidate_materialization_v1":
        errors.append({"error_type": "unexpected_plan_next", "actual": plan.get("next_todo")})
    if plan.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan.get("validation_errors")})
    contract = plan.get("target_contract", {})
    if contract.get("target_rows") != 400 or contract.get("primary_binary_rows") != 320:
        errors.append({"error_type": "unexpected_target_contract", "actual": contract})
    boundary = plan.get("boundary", {})
    for key in ["validation_usage", "test_usage", "paper_evidence_allowed", "trains_paper_model", "modifies_h001"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def write_patterns(path: Path, preview_rows: list[dict[str, Any]]) -> None:
    patterns: set[str] = set()
    for row in preview_rows:
        patterns.add(str(row["directed_pair_id"]))
        patterns.add(str(row["prediction_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(patterns)) + "\n", encoding="utf-8")


def run_rg_cache(match_rows: Path, patterns: Path, cache: Path) -> dict[str, Any]:
    rg = shutil.which("rg")
    if rg is None:
        return {"used_rg": False, "reason": "rg_not_found", "returncode": None}
    cache.parent.mkdir(parents=True, exist_ok=True)
    with cache.open("w", encoding="utf-8") as out:
        completed = subprocess.run(
            [rg, "-F", "-f", str(patterns), str(match_rows)],
            stdout=out,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    return {
        "used_rg": True,
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip()[:2000],
    }


def stream_source_rows(match_rows: Path, cache: Path, use_cache: bool) -> tuple[Path, dict[str, Any]]:
    if use_cache and cache.exists() and cache.stat().st_size > 0:
        return cache, {"source": "rg_cache", "cache_rows_available": True, "cache_bytes": cache.stat().st_size}
    return match_rows, {"source": "full_match_rows_python_scan", "cache_rows_available": False, "cache_bytes": 0}


def compact_raw_geometry(row: dict[str, Any]) -> dict[str, Any] | None:
    raw = row.get("geometry", {}).get("raw_features")
    if not isinstance(raw, dict):
        return None
    return {
        "raw_features": raw,
        "source_family": row.get("predicate", {}).get("predicate_family"),
        "source_predicate": row.get("predicate", {}).get("predicate_label"),
        "source_geometry_status": row.get("geometry", {}).get("geometry_status"),
        "source_prediction_id": row.get("identity", {}).get("prediction_id"),
    }


def scan_join_rows(
    source_rows: Path,
    selected_prediction_ids: set[str],
    selected_pair_ids: set[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    selected_matches: dict[str, dict[str, Any]] = {}
    pair_geometry: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    lines_seen = 0
    json_errors = 0
    with source_rows.open("r", encoding="utf-8") as handle:
        for line in handle:
            lines_seen += 1
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                json_errors += 1
                continue
            identity = row.get("identity") or {}
            prediction_id = identity.get("prediction_id") or row.get("prediction_id")
            pair_id = identity.get("directed_pair_id")
            if prediction_id in selected_prediction_ids:
                selected_matches[str(prediction_id)] = row
                counts["selected_prediction_match"] += 1
            if pair_id in selected_pair_ids:
                predicate = row.get("predicate", {})
                family = predicate.get("predicate_family")
                if family in {"support_contact", "relative_vertical"}:
                    compact = compact_raw_geometry(row)
                    if compact is not None:
                        existing = pair_geometry.get(str(pair_id))
                        if existing is None or existing["source_family"] != "support_contact" and family == "support_contact":
                            pair_geometry[str(pair_id)] = compact
                        counts[f"raw_geometry_source|{family}|{predicate.get('predicate_label')}"] += 1
    return selected_matches, pair_geometry, {
        "join_source_rows": rel_path(source_rows),
        "lines_seen": lines_seen,
        "json_errors": json_errors,
        "selected_prediction_matches": len(selected_matches),
        "pair_geometry_matches": len(pair_geometry),
        "raw_match_counts": dict(counts),
    }


def make_t_block(preview: dict[str, Any], selected: dict[str, Any] | None) -> dict[str, Any]:
    predicate = preview["predicate_label"]
    return {
        "predicate_label": predicate,
        "predicate_text": predicate,
        "relation_family": "attachment_deferred",
        "subject_label": preview["subject_label"],
        "object_label": preview["object_label"],
        "subject_object_text": f"{preview['subject_label']} [REL] {preview['object_label']}",
        "predicate_embedding_id": None,
        "subject_class_embedding_id": None,
        "object_class_embedding_id": None,
    }


def make_z_block(preview: dict[str, Any], selected: dict[str, Any] | None) -> dict[str, Any]:
    semantic = selected.get("semantic", {}) if selected else {}
    source = selected.get("source", {}) if selected else {}
    rank = safe_float(semantic.get("rank_in_context"))
    predicate_rank = safe_float(semantic.get("predicate_rank_for_pair"))
    score_norm = safe_float(semantic.get("semantic_score_norm"))
    score_raw = safe_float(semantic.get("semantic_score_raw"))
    return {
        "source_id": source.get("source_id", "open3dsg_train_full"),
        "source_score_raw": score_raw,
        "source_score_normalized": score_norm,
        "source_rank": rank,
        "source_predicate_rank_for_pair": predicate_rank,
        "source_rank_band": normalize_rank_band(rank, str(preview.get("rank_band_hidden") or "not_available")),
        "source_score_available": score_raw is not None or score_norm is not None,
    }


def attachment_geometry_features(preview: dict[str, Any], raw_entry: dict[str, Any] | None) -> tuple[dict[str, float], dict[str, bool]]:
    raw = dict(raw_entry.get("raw_features", {})) if raw_entry else {}
    derived_flags = derived_near_flags(raw) if raw else {}
    for key in ["near_contact", "loose_near_contact", "far_separated", "projected_overlap_support"]:
        if key not in raw:
            raw[key] = bool(preview.get(key)) if preview.get(key) is not None else derived_flags.get(key)

    features: dict[str, float] = {}
    mask: dict[str, bool] = {}
    for key in GEOMETRY_ALLOWED_RAW_KEYS:
        value = safe_float(raw.get(key))
        out_key = "projected_overlap_indicator" if key == "projected_overlap_support" else key
        if value is None:
            mask[out_key] = False
            continue
        features[out_key] = value
        mask[out_key] = True

    d3 = safe_float(raw.get("normalized_distance_3d"))
    dxy = safe_float(raw.get("normalized_distance_xy"))
    dz = safe_float(raw.get("normalized_center_delta_z"))
    gap = safe_float(raw.get("vertical_gap_subject_on_object"))
    subject_overlap = safe_float(raw.get("projected_subject_overlap_ratio"), 0.0) or 0.0
    object_overlap = safe_float(raw.get("projected_object_overlap_ratio"), 0.0) or 0.0
    iou = safe_float(raw.get("projected_iou_xy"), 0.0) or 0.0
    derived = {
        "distance_closeness_3d": closeness(d3),
        "distance_closeness_xy": closeness(dxy),
        "abs_normalized_center_delta_z": abs(dz) if dz is not None else 0.0,
        "vertical_gap_abs": abs(gap) if gap is not None else 0.0,
        "vertical_gap_closeness": closeness(gap),
        "overlap_max_ratio": max(subject_overlap, object_overlap, iou),
        "overlap_min_subject_object_ratio": min(subject_overlap, object_overlap),
        "near_contact_indicator": bool_float(raw.get("near_contact")),
        "loose_near_contact_indicator": bool_float(raw.get("loose_near_contact")),
        "far_separated_indicator": bool_float(raw.get("far_separated")),
    }
    features.update(derived)
    mask.update({key: True for key in derived})
    return features, mask


def make_g_block(preview: dict[str, Any], raw_entry: dict[str, Any] | None) -> dict[str, Any]:
    features, mask = attachment_geometry_features(preview, raw_entry)
    return {
        "geometry_features": features,
        "geometry_feature_mask": mask,
        "geometry_feature_units": {
            "center_delta_z": "meters_or_dataset_coordinate_units",
            "vertical_gap_subject_on_object": "meters_or_dataset_coordinate_units",
            "normalized_distance_3d": "scale_normalized",
            "normalized_distance_xy": "scale_normalized",
            "normalized_center_delta_z": "scale_normalized",
            "projected_iou_xy": "ratio_0_1",
            "projected_subject_overlap_ratio": "ratio_0_1",
            "projected_object_overlap_ratio": "ratio_0_1",
        },
        "geometry_normalization": "v20_pair_geometry_from_support_or_vertical_raw_features",
        "geometry_source": raw_entry.get("source_family") if raw_entry else "missing_pair_geometry",
        "geometry_source_predicate": raw_entry.get("source_predicate") if raw_entry else None,
    }


def make_q_block(preview: dict[str, Any], raw_entry: dict[str, Any] | None) -> dict[str, Any]:
    flags = preview.get("uncertainty_flags") or []
    if not isinstance(flags, list):
        flags = [str(flags)]
    predicate = preview["predicate_label"]
    return {
        "subject_point_count": None,
        "object_point_count": None,
        "pair_point_count": None,
        "mesh_available": None,
        "normal_available": None,
        "same_frame_visible": None,
        "multi_view_count": None,
        "subject_crop_available": None,
        "object_crop_available": None,
        "pair_crop_available": None,
        "low_coverage_flag": False,
        "missing_geometry_flag": raw_entry is None,
        "unsupported_family_flag": predicate == "connected to",
        "evidence_conflict_flag": bool(flags),
        "asset_tier": "numeric_3d_pair_geometry_only",
        "coverage_features": {
            "raw_feature_joined": 1.0 if raw_entry else 0.0,
            "uncertainty_flag_count": float(len(flags)),
            "uncertainty_none": 1.0 if not flags else 0.0,
            "uncertainty_visual_or_mesh_needed": 1.0
            if "functional_connection_ambiguous_without_visual_or_mesh" in flags
            or "thin_structure_or_boundary_missing" in flags
            else 0.0,
            "connected_to_diagnostic": 1.0 if predicate == "connected to" else 0.0,
        },
    }


def compatibility_label(preview: dict[str, Any]) -> tuple[str, str, str]:
    predicate = preview["predicate_label"]
    proxy = preview.get("proxy_role")
    if predicate in PRIMARY_PREDICATES and proxy == POSITIVE_PROXY:
        return "positive", "P2_v20_endpoint_balanced_supported_proxy", "primary_binary"
    if predicate in PRIMARY_PREDICATES and proxy == NEGATIVE_PROXY:
        return "counterfactual_negative", "N2_v20_endpoint_balanced_counterfactual_proxy", "primary_binary"
    if predicate == "connected to" and proxy == CONNECTED_NEAR_PROXY:
        return "unknown", "D1_connected_near_or_overlap_diagnostic", "connected_diagnostic"
    if predicate == "connected to" and proxy == CONNECTED_FAR_PROXY:
        return "unknown", "D2_connected_far_or_functional_ambiguous_diagnostic", "connected_diagnostic"
    return "unknown", "unsupported_proxy", "unknown"


def official_gt_axis(selected: dict[str, Any] | None) -> dict[str, Any]:
    label = selected.get("label", {}) if selected else {}
    return {
        "gt_match_status": label.get("label_match_status", "unavailable"),
        "gt_predicates_for_pair": label.get("matched_predicates") or [],
        "gt_family_for_pair": label.get("matched_families") or [],
        "gt_source": label.get("label_source", "direct_join_relationships_train_full"),
        "gt_used_as_model_input": False,
    }


def row_to_materialized(
    preview: dict[str, Any],
    index: int,
    selected: dict[str, Any] | None,
    raw_entry: dict[str, Any] | None,
) -> dict[str, Any]:
    row_id = f"h002_attach_ctrlcand_v1_{index:06d}"
    t_block = make_t_block(preview, selected)
    z_block = make_z_block(preview, selected)
    g_block = make_g_block(preview, raw_entry)
    q_block = make_q_block(preview, raw_entry)
    comp_label, tier, role = compatibility_label(preview)
    group_id = stable_group_id(preview["predicate_label"], preview["visible_endpoint_pair"])
    relation_text = f"{preview['subject_label']} {preview['predicate_label']} {preview['object_label']}"
    return {
        "schema_version": "h002_attachment_controlled_candidates_v1_row",
        "row_id": row_id,
        "group_id": group_id,
        "row_role": role,
        "split": "train",
        "source_dataset": "Open3DSG_train",
        "relation_source": "v20_endpoint_balanced_preview_400",
        "scan_id": preview.get("scan_id"),
        "scene_id": preview.get("scan_id"),
        "subgraph_id": preview.get("subgraph_id"),
        "subject_instance_id": preview.get("subject_id"),
        "object_instance_id": preview.get("object_id"),
        "directed_pair_id": preview.get("directed_pair_id"),
        "prediction_id": preview.get("prediction_id"),
        "candidate_relation_text": relation_text,
        "T_e": t_block,
        "Z_e": z_block,
        "G_e": g_block,
        "Q_e": q_block,
        "p_geom_valid_baseline": None,
        "geometry_status_baseline": None,
        "official_gt_axis": official_gt_axis(selected),
        "audit_axis": {
            "audit_label": None,
            "geometry_support_label": None,
            "geometry_support_binary_target": 1 if comp_label == "positive" else 0 if comp_label == "counterfactual_negative" else None,
            "connected_diagnostic_target": tier if role == "connected_diagnostic" else None,
            "audit_provenance": "v20_proxy_from_geometry_capacity_not_human_label",
            "audit_hidden_fields_exposed": False,
        },
        "counterfactual_axis": {
            "compatibility_label": comp_label,
            "positive_tier": tier if comp_label == "positive" else "none",
            "negative_tier": tier if comp_label == "counterfactual_negative" else "none",
            "diagnostic_tier": tier if role == "connected_diagnostic" else "none",
            "counterfactual_type": "v20_endpoint_balanced_attachment" if comp_label != "unknown" else "none",
            "anchor_row_id": None,
            "matching_fields": ["predicate_label", "visible_endpoint_pair", "numeric_pair_geometry_available"],
            "relaxed_matching_fields": ["relation_family", "object_family_pair"],
        },
        "observability_axis": {
            "observability_label": "observable" if raw_entry else "missing_geometry",
            "observability_reason": "raw_pair_geometry_joined" if raw_entry else "raw_pair_geometry_missing",
            "p_obs_target_usable": True,
        },
        "reliability_eval_axis": {
            "reliability_label": "unavailable_proxy_only",
            "native_reliability_label": None,
            "label_source": "no_human_label_v20_proxy_only",
            "binary_usable": False,
            "multiclass_usable": False,
        },
        "model_views": {
            "compatibility_main": {"T_e": t_block, "G_e": g_block},
            "source_only": {"Z_e": z_block},
            "semantic_source": {"T_e": t_block, "Z_e": z_block},
            "geometry_only": {"G_e": g_block},
            "obs_head": {"Q_e": q_block},
            "full_factorized": {"Z_e": z_block, "Q_e": q_block, "C_e_input": {"T_e": t_block, "G_e": g_block}},
        },
        "hidden_control": {
            "blind_review_id": preview.get("blind_review_id"),
            "cell_id_hidden": preview.get("cell_id_hidden"),
            "proxy_role_hidden": preview.get("proxy_role"),
            "provisional_status_hidden": preview.get("provisional_status_hidden"),
            "capacity_evidence_tier_hidden": preview.get("capacity_evidence_tier"),
            "anchor_bucket_hidden": preview.get("anchor_bucket_hidden"),
            "rank_band_hidden": preview.get("rank_band_hidden"),
            "selection_route_level_hidden": preview.get("selection_route_level"),
            "visible_endpoint_pair_hidden": preview.get("visible_endpoint_pair"),
            "object_family_pair_hidden": preview.get("object_family_pair"),
            "source_geometry_family_hidden": raw_entry.get("source_family") if raw_entry else None,
            "source_geometry_predicate_hidden": raw_entry.get("source_predicate") if raw_entry else None,
            "source_geometry_status_hidden": raw_entry.get("source_geometry_status") if raw_entry else None,
            "uncertainty_flags_hidden": preview.get("uncertainty_flags") or [],
        },
    }


def make_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        group_id = row["group_id"]
        group = groups.setdefault(
            group_id,
            {
                "group_id": group_id,
                "predicate_label": row["T_e"]["predicate_label"],
                "visible_endpoint_pair": row["hidden_control"]["visible_endpoint_pair_hidden"],
                "row_ids": [],
                "compatibility_counts": Counter(),
                "matching_fields": {
                    "predicate_label": row["T_e"]["predicate_label"],
                    "visible_endpoint_pair": row["hidden_control"]["visible_endpoint_pair_hidden"],
                },
            },
        )
        group["row_ids"].append(row["row_id"])
        group["compatibility_counts"][row["counterfactual_axis"]["compatibility_label"]] += 1
    output = []
    for group in groups.values():
        group = dict(group)
        group["compatibility_counts"] = dict(group["compatibility_counts"])
        output.append(group)
    return sorted(output, key=lambda item: item["group_id"])


def baseline_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "group_id": row["group_id"],
        "predicate_label": row["T_e"]["predicate_label"],
        "relation_family": row["T_e"]["relation_family"],
        "source_score_normalized": row["Z_e"]["source_score_normalized"],
        "source_score_raw": row["Z_e"]["source_score_raw"],
        "source_rank": row["Z_e"]["source_rank"],
        "source_rank_band": row["Z_e"]["source_rank_band"],
        "geometry_feature_count": len(row["G_e"]["geometry_features"]),
        "compatibility_label": row["counterfactual_axis"]["compatibility_label"],
        "diagnostic_tier": row["counterfactual_axis"]["diagnostic_tier"],
        "raw_feature_joined": row["Q_e"]["coverage_features"]["raw_feature_joined"],
    }


def audit_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "candidate_relation_text": row["candidate_relation_text"],
        "scan_id": row["scan_id"],
        "directed_pair_id": row["directed_pair_id"],
        "official_gt_axis": row["official_gt_axis"],
        "audit_axis": row["audit_axis"],
        "counterfactual_axis": row["counterfactual_axis"],
        "observability_axis": row["observability_axis"],
        "reliability_eval_axis": row["reliability_eval_axis"],
        "hidden_control": row["hidden_control"],
    }


def count_by(rows: list[dict[str, Any]], getter: Any) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[str(getter(row))] += 1
    return dict(sorted(counts.items()))


def validate_rows(
    rows: list[dict[str, Any]],
    preview_rows: list[dict[str, Any]],
    selected_matches: dict[str, dict[str, Any]],
    pair_geometry: dict[str, dict[str, Any]],
    plan: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(preview_rows) != 400:
        errors.append({"error_type": "preview_row_count_not_400", "actual": len(preview_rows)})
    if len(rows) != 400:
        errors.append({"error_type": "materialized_row_count_not_400", "actual": len(rows)})
    if len(selected_matches) != len(preview_rows):
        errors.append({"error_type": "selected_match_count_mismatch", "expected": len(preview_rows), "actual": len(selected_matches)})
    if len(pair_geometry) != len({row["directed_pair_id"] for row in preview_rows}):
        errors.append(
            {
                "error_type": "pair_geometry_count_mismatch",
                "expected": len({row["directed_pair_id"] for row in preview_rows}),
                "actual": len(pair_geometry),
            }
        )

    row_ids: set[str] = set()
    for row in rows:
        row_id = row["row_id"]
        if row_id in row_ids:
            errors.append({"error_type": "duplicate_row_id", "row_id": row_id})
        row_ids.add(row_id)
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row_id, "split": row.get("split")})
        if not row.get("G_e", {}).get("geometry_features"):
            errors.append({"error_type": "missing_g_features", "row_id": row_id})
        if "Z_e" in row.get("model_views", {}).get("compatibility_main", {}):
            errors.append({"error_type": "z_in_compatibility_main", "row_id": row_id})
        for feature_name in row.get("G_e", {}).get("geometry_features", {}):
            lowered = feature_name.lower()
            for fragment in GEOMETRY_BLOCKED_FRAGMENTS:
                if fragment in lowered:
                    errors.append(
                        {
                            "error_type": "blocked_geometry_feature_name",
                            "row_id": row_id,
                            "feature": feature_name,
                            "fragment": fragment,
                        }
                    )
                    break

    primary = [row for row in rows if row["T_e"]["predicate_label"] in PRIMARY_PREDICATES]
    diagnostic = [row for row in rows if row["T_e"]["predicate_label"] in DIAGNOSTIC_PREDICATES]
    if len(primary) != plan.get("target_contract", {}).get("primary_binary_rows"):
        errors.append({"error_type": "primary_binary_count_mismatch", "actual": len(primary)})
    if len(diagnostic) != plan.get("target_contract", {}).get("diagnostic_connected_rows"):
        errors.append({"error_type": "diagnostic_connected_count_mismatch", "actual": len(diagnostic)})
    for predicate in sorted(PRIMARY_PREDICATES):
        pred_rows = [row for row in primary if row["T_e"]["predicate_label"] == predicate]
        labels = Counter(row["counterfactual_axis"]["compatibility_label"] for row in pred_rows)
        if labels.get("positive") != 80 or labels.get("counterfactual_negative") != 80:
            errors.append({"error_type": "primary_predicate_quota_mismatch", "predicate": predicate, "actual": dict(labels)})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Attachment Controlled Candidates V1",
        "",
        f"Date: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "```text",
        f"rows = {summary['counts']['rows']}",
        f"primary_binary_rows = {summary['counts']['primary_binary_rows']}",
        f"diagnostic_connected_rows = {summary['counts']['diagnostic_connected_rows']}",
        f"numeric_g_rows = {summary['counts']['numeric_g_rows']}",
        f"groups = {summary['counts']['groups']}",
        f"validation_errors = {summary['counts']['validation_errors']}",
        "```",
        "",
        "## Predicate Counts",
        "",
        "```json",
        json.dumps(summary["predicate_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Compatibility Counts",
        "",
        "```json",
        json.dumps(summary["compatibility_counts_by_predicate"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Join Summary",
        "",
        "```json",
        json.dumps(summary["join_summary"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Boundary",
        "",
        "- train-only hypothesis artifact.",
        "- no validation/test usage.",
        "- no paper model training.",
        "- no H001 artifact modification.",
        "- hidden construction fields are audit/control only, not model input.",
        "- `connected to` remains diagnostic rather than primary binary compatibility.",
        "",
        "## Next TODO",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    plan = read_json(args.plan_dir / "summary.json")
    preview_rows = read_jsonl(args.preview_rows)
    patterns = output_dir / "selected_patterns.txt"
    cache = output_dir / "matched_source_rows.jsonl"
    write_patterns(patterns, preview_rows)
    rg_summary = {"used_rg": False, "returncode": None, "stderr": ""}
    if not args.force_python_scan:
        rg_summary = run_rg_cache(args.match_rows, patterns, cache)
    source_rows, source_summary = stream_source_rows(args.match_rows, cache, rg_summary.get("used_rg") is True and rg_summary.get("returncode") in {0, 1})

    selected_prediction_ids = {str(row["prediction_id"]) for row in preview_rows}
    selected_pair_ids = {str(row["directed_pair_id"]) for row in preview_rows}
    selected_matches, pair_geometry, join_summary = scan_join_rows(source_rows, selected_prediction_ids, selected_pair_ids)

    rows = [
        row_to_materialized(
            preview,
            index,
            selected_matches.get(str(preview["prediction_id"])),
            pair_geometry.get(str(preview["directed_pair_id"])),
        )
        for index, preview in enumerate(preview_rows)
    ]
    groups = make_groups(rows)
    compatibility_rows = [row for row in rows if row["counterfactual_axis"]["compatibility_label"] in {"positive", "counterfactual_negative"}]
    diagnostic_rows = [row for row in rows if row["row_role"] == "connected_diagnostic"]

    errors = []
    errors.extend(validate_plan(plan))
    errors.extend(validate_rows(rows, preview_rows, selected_matches, pair_geometry, plan))
    if rg_summary.get("used_rg") is True and rg_summary.get("returncode") not in {0, 1}:
        errors.append({"error_type": "rg_failed", "returncode": rg_summary.get("returncode"), "stderr": rg_summary.get("stderr")})

    summary = {
        "schema_version": "h002_attachment_controlled_candidates_v1_summary",
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_plan": rel_path(args.plan_dir / "summary.json"),
        "input_preview_rows": rel_path(args.preview_rows),
        "input_match_rows": rel_path(args.match_rows),
        "output_dir": rel_path(output_dir),
        "counts": {
            "preview_rows": len(preview_rows),
            "rows": len(rows),
            "primary_binary_rows": len(compatibility_rows),
            "diagnostic_connected_rows": len(diagnostic_rows),
            "numeric_g_rows": sum(1 for row in rows if row["G_e"]["geometry_features"]),
            "raw_pair_geometry_joined_rows": sum(1 for row in rows if row["Q_e"]["coverage_features"]["raw_feature_joined"] == 1.0),
            "selected_prediction_matches": len(selected_matches),
            "pair_geometry_matches": len(pair_geometry),
            "groups": len(groups),
            "validation_errors": len(errors),
        },
        "predicate_counts": count_by(rows, lambda row: row["T_e"]["predicate_label"]),
        "compatibility_counts_by_predicate": {
            predicate: dict(
                Counter(row["counterfactual_axis"]["compatibility_label"] for row in rows if row["T_e"]["predicate_label"] == predicate)
            )
            for predicate in sorted({str(row["T_e"]["predicate_label"]) for row in rows})
        },
        "diagnostic_counts": count_by(diagnostic_rows, lambda row: row["counterfactual_axis"]["diagnostic_tier"]),
        "source_rank_band_counts": count_by(rows, lambda row: row["Z_e"]["source_rank_band"]),
        "raw_geometry_source_counts": count_by(rows, lambda row: row["G_e"]["geometry_source"]),
        "geometry_feature_keys": sorted({key for row in rows for key in row["G_e"]["geometry_features"]}),
        "join_summary": {**source_summary, **join_summary, "rg_summary": rg_summary},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "trains_paper_model": False,
            "modifies_h001": False,
            "hidden_fields_as_model_input": False,
            "connected_to_binary_compatibility": False,
        },
        "next_todo": NEXT_TODO if not errors else "attachment_controlled_candidate_materialization_error_analysis_v1",
    }

    write_jsonl(output_dir / "candidate_rows.jsonl", rows)
    write_jsonl(output_dir / "compatibility_rows.jsonl", compatibility_rows)
    write_jsonl(output_dir / "diagnostic_connected_rows.jsonl", diagnostic_rows)
    write_jsonl(output_dir / "counterfactual_groups.jsonl", groups)
    write_jsonl(output_dir / "baseline_view.jsonl", [baseline_view(row) for row in rows])
    write_jsonl(output_dir / "audit_view.jsonl", [audit_view(row) for row in rows])
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_json(output_dir / "summary.json", summary)
    write_json(
        output_dir / "schema.json",
        {
            "T_e": "semantic relation content",
            "Z_e": "source confidence/rank",
            "G_e": "predicate-independent numeric pair geometry",
            "Q_e": "observability and evidence quality",
            "compatibility_main": "T_e + G_e only",
            "hidden_control": "sampling/control/probe only",
        },
    )
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        "status={status} rows={rows} primary={primary} diagnostic={diagnostic} numeric_g={numeric_g} "
        "prediction_matches={pred_matches} pair_geometry={pair_geometry} errors={errors} next={next}".format(
            status=summary["status"],
            rows=summary["counts"]["rows"],
            primary=summary["counts"]["primary_binary_rows"],
            diagnostic=summary["counts"]["diagnostic_connected_rows"],
            numeric_g=summary["counts"]["numeric_g_rows"],
            pred_matches=summary["counts"]["selected_prediction_matches"],
            pair_geometry=summary["counts"]["pair_geometry_matches"],
            errors=summary["counts"]["validation_errors"],
            next=summary["next_todo"],
        )
    )
    return 0 if summary["counts"]["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

