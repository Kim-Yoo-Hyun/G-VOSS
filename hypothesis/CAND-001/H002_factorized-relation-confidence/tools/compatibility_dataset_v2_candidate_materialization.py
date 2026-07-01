#!/usr/bin/env python3
"""Materialize controlled H002 compatibility dataset v2 candidate rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
RGA_ROOT = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_capacity_scan"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_candidate_materialization"

EXPECTED_CAPACITY_STATUS = "h002_compatibility_dataset_v2_capacity_scan_passed_with_controls_ready_for_candidate_materialization"
EXPECTED_CAPACITY_NEXT = "compatibility_dataset_v2_candidate_materialization"

SCHEMA_VERSION = "h002_compatibility_dataset_v2_candidate_materialization_v1"
ROW_SCHEMA_VERSION = "h002_compatibility_dataset_v2_candidate_row_v1"
STATUS_READY = "h002_compatibility_dataset_v2_candidate_materialization_ready_for_schema_shortcut_audit"
STATUS_ERROR = "h002_compatibility_dataset_v2_candidate_materialization_input_errors"
NEXT_TODO = "compatibility_dataset_v2_schema_shortcut_audit"

PRIMARY_QUOTAS = {
    "support_contact": {
        "positive": 120,
        "negative": 120,
        "per_predicate_positive": {"lying on": 40, "standing on": 40, "supported by": 40},
    },
    "relative_vertical": {
        "positive": 80,
        "negative": 80,
        "per_predicate_positive": {"higher than": 40, "lower than": 40},
    },
}

RAW_FIELDS = [
    "center_delta_z",
    "distance_3d",
    "distance_xy",
    "normalized_center_delta_z",
    "normalized_distance_3d",
    "normalized_distance_xy",
    "object_bottom_z",
    "object_top_z",
    "projected_iou_xy",
    "projected_object_overlap_ratio",
    "projected_subject_overlap_ratio",
    "subject_bottom_z",
    "subject_top_z",
    "vertical_gap_subject_on_object",
]

BLOCKED_G_FEATURE_FRAGMENTS = (
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
    "p_geom",
    "queue",
    "machine",
    "match",
)

HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
BUFFER_MULTIPLIER = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if line:
                yield line_no, json.loads(line)


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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validation_count(value: Any) -> int:
    if value in (None, 0, [], {}):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, list):
        return len(value)
    return 1


def stable_hash(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:16], 16)


def stable_id(value: str, prefix: str = "h002v2") -> str:
    return f"{prefix}_{hashlib.sha1(value.encode('utf-8')).hexdigest()[:16]}"


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def feature_mask(features: dict[str, Any]) -> dict[str, bool]:
    return {key: value is not None for key, value in features.items()}


def source_score_band(rank: Any) -> str:
    rank_value = safe_float(rank)
    if rank_value is None:
        return "not_available"
    if rank_value <= 20:
        return "top_20"
    if rank_value <= 100:
        return "top_100"
    if rank_value <= 200:
        return "rank_101_200"
    if rank_value <= 500:
        return "rank_201_500"
    return "rank_over_500"


def hard_filter_reason(row: dict[str, Any]) -> str | None:
    family = str(row.get("predicate_family") or "")
    subject = norm(row.get("subject_label"))
    obj = norm(row.get("object_label"))
    if not row.get("prediction_id"):
        return "missing_prediction_id"
    if family == "support_contact":
        if subject in HARD_ROOM_SURFACES:
            return "support_subject_hard_room_surface"
        if obj in {"wall", "ceiling"}:
            return "support_object_wall_or_ceiling"
    if family == "relative_vertical" and subject in HARD_ROOM_SURFACES and obj in HARD_ROOM_SURFACES:
        return "vertical_both_endpoints_hard_room_surface"
    return None


def is_positive_candidate(row: dict[str, Any]) -> bool:
    return str(row.get("queue_kind")) == "LH" and str(row.get("geometry_status")) == "satisfied"


def target_key(row: dict[str, Any]) -> tuple[str, str] | None:
    family = str(row.get("predicate_family") or "")
    predicate = str(row.get("predicate_label") or "")
    quota = PRIMARY_QUOTAS.get(family, {}).get("per_predicate_positive", {})
    if predicate in quota:
        return family, predicate
    return None


def directed_pair_id(row: dict[str, Any]) -> str:
    return f"{row.get('scan_id')}::{row.get('subject_id')}->{row.get('object_id')}"


def visible_pair(row: dict[str, Any]) -> str:
    return f"{norm(row.get('subject_label'))}|{norm(row.get('object_label'))}"


def compact_source_row(row: dict[str, Any], line_no: int, queue_path: Path) -> dict[str, Any]:
    prediction_id = str(row.get("prediction_id") or "")
    return {
        "prediction_id": prediction_id,
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_label": row.get("object_label"),
        "candidate_relation_text": f"{row.get('subject_label')} {row.get('predicate_label')} {row.get('object_label')}",
        "source_id": row.get("source_id", "open3dsg_train_full"),
        "semantic_score_raw": row.get("semantic_score_raw"),
        "semantic_score_norm": row.get("semantic_score_norm"),
        "semantic_rank": row.get("semantic_rank"),
        "rank_band": row.get("rank_band"),
        "p_geom_valid": row.get("p_geom_valid"),
        "geometry_status": row.get("geometry_status"),
        "queue_kind": row.get("queue_kind"),
        "reason_codes": row.get("reason_codes", []),
        "label_match_status": row.get("label_match_status"),
        "matched_predicates": row.get("matched_predicates", []),
        "machine_hint": row.get("machine_hint"),
        "directed_pair_id": directed_pair_id(row),
        "visible_pair": visible_pair(row),
        "source_queue_path": rel_path(queue_path),
        "source_line_no": line_no,
        "stable_hash": stable_hash(prediction_id),
    }


def select_diverse(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    rows = sorted(rows, key=lambda row: (row["stable_hash"], str(row["prediction_id"])))
    selected: list[dict[str, Any]] = []
    seen_scans: set[str] = set()
    seen_pairs: set[str] = set()
    for row in rows:
        scan = str(row["scan_id"])
        pair = str(row["visible_pair"])
        if scan in seen_scans or pair in seen_pairs:
            continue
        selected.append(row)
        seen_scans.add(scan)
        seen_pairs.add(pair)
        if len(selected) == count:
            return selected
    for row in rows:
        if row in selected:
            continue
        selected.append(row)
        if len(selected) == count:
            return selected
    return selected


def scan_anchor_buffers(lh_queue: Path) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], dict[str, Any]]:
    buffers: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    raw_counts: Counter[str] = Counter()
    hard_filter_counts: Counter[str] = Counter()
    for line_no, row in iter_jsonl(lh_queue):
        key = target_key(row)
        if key is None:
            continue
        raw_counts["candidate_target_rows_seen"] += 1
        if not is_positive_candidate(row):
            hard_filter_counts["not_positive_lh_satisfied"] += 1
            continue
        hard_reason = hard_filter_reason(row)
        if hard_reason:
            hard_filter_counts[hard_reason] += 1
            continue
        family, predicate = key
        needed = PRIMARY_QUOTAS[family]["per_predicate_positive"][predicate] * BUFFER_MULTIPLIER
        if len(buffers[key]) < needed:
            buffers[key].append(compact_source_row(row, line_no, lh_queue))
        else:
            candidate = compact_source_row(row, line_no, lh_queue)
            worst_index = max(range(len(buffers[key])), key=lambda idx: buffers[key][idx]["stable_hash"])
            if candidate["stable_hash"] < buffers[key][worst_index]["stable_hash"]:
                buffers[key][worst_index] = candidate
    return buffers, {"raw_counts": dict(raw_counts), "hard_filter_counts": dict(hard_filter_counts)}


def raw_feature_row(match_row: dict[str, Any]) -> dict[str, float | None]:
    raw = match_row.get("geometry", {}).get("raw_features") or {}
    out: dict[str, float | None] = {field: safe_float(raw.get(field)) for field in RAW_FIELDS}
    if out["center_delta_z"] is not None:
        out["abs_center_delta_z"] = abs(float(out["center_delta_z"]))
    if out["vertical_gap_subject_on_object"] is not None:
        out["abs_vertical_gap_subject_on_object"] = abs(float(out["vertical_gap_subject_on_object"]))
    overlaps = [
        safe_float(out.get("projected_subject_overlap_ratio"), 0.0),
        safe_float(out.get("projected_object_overlap_ratio"), 0.0),
        safe_float(out.get("projected_iou_xy"), 0.0),
    ]
    out["projected_overlap_max"] = max(value for value in overlaps if value is not None)
    out["projected_overlap_min"] = min(value for value in overlaps if value is not None)
    return out


def load_raw_witness(match_rows: Path, prediction_ids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    matched: dict[str, dict[str, Any]] = {}
    rows_scanned = 0
    matched_by_family: Counter[str] = Counter()
    with match_rows.open("r", encoding="utf-8") as handle:
        for line in handle:
            rows_scanned += 1
            row = json.loads(line)
            prediction_id = str(row.get("identity", {}).get("prediction_id") or "")
            if prediction_id not in prediction_ids:
                continue
            family = str(row.get("predicate", {}).get("predicate_family") or "")
            matched_by_family[family] += 1
            matched[prediction_id] = {
                "raw_features": raw_feature_row(row),
                "geometry": row.get("geometry", {}),
                "semantic": row.get("semantic", {}),
                "identity": row.get("identity", {}),
                "predicate": row.get("predicate", {}),
                "source": row.get("source", {}),
                "label": row.get("label", {}),
            }
            if len(matched) == len(prediction_ids):
                break
    return matched, {
        "match_rows": rel_path(match_rows),
        "requested_prediction_ids": len(prediction_ids),
        "matched_prediction_ids": len(matched),
        "rows_scanned_until_complete": rows_scanned,
        "matched_by_family": dict(sorted(matched_by_family.items())),
        "raw_fields": RAW_FIELDS,
    }


def clean_geometry_features(features: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, value in features.items():
        lowered = key.lower()
        if any(fragment in lowered for fragment in BLOCKED_G_FEATURE_FRAGMENTS):
            continue
        numeric = safe_float(value)
        if numeric is not None:
            out[key] = numeric
    return out


def perturbed_support_features(features: dict[str, Any]) -> dict[str, float]:
    out = clean_geometry_features(features)
    out["vertical_gap_subject_on_object"] = 2.0
    out["abs_vertical_gap_subject_on_object"] = 2.0
    out["distance_xy"] = max(float(out.get("distance_xy", 0.0)), 2.0)
    out["normalized_distance_xy"] = max(float(out.get("normalized_distance_xy", 0.0)), 2.0)
    out["projected_iou_xy"] = 0.0
    out["projected_subject_overlap_ratio"] = 0.0
    out["projected_object_overlap_ratio"] = 0.0
    out["projected_overlap_max"] = 0.0
    out["projected_overlap_min"] = 0.0
    return out


def make_t_block(source: dict[str, Any], predicate: str | None = None, subject: str | None = None, obj: str | None = None) -> dict[str, Any]:
    pred = predicate or str(source["predicate_label"])
    subj = subject or str(source["subject_label"])
    object_label = obj or str(source["object_label"])
    return {
        "predicate_label": pred,
        "predicate_text": pred,
        "relation_family": source["predicate_family"],
        "subject_label": subj,
        "object_label": object_label,
        "subject_object_text": f"{subj} [REL] {object_label}",
        "predicate_embedding_id": None,
        "subject_class_embedding_id": None,
        "object_class_embedding_id": None,
    }


def make_z_block(source: dict[str, Any], generated: bool) -> dict[str, Any]:
    return {
        "source_id": source.get("source_id", "open3dsg_train_full"),
        "source_score_raw": safe_float(source.get("semantic_score_raw")),
        "source_score_normalized": safe_float(source.get("semantic_score_norm")),
        "source_rank": safe_float(source.get("semantic_rank")),
        "source_rank_band": source.get("rank_band") or source_score_band(source.get("semantic_rank")),
        "source_score_available": source.get("semantic_score_norm") is not None or source.get("semantic_score_raw") is not None,
        "source_score_inherited_for_counterfactual": generated,
    }


def make_g_block(features: dict[str, Any], source_name: str) -> dict[str, Any]:
    clean = clean_geometry_features(features)
    return {
        "geometry_features": clean,
        "geometry_feature_mask": feature_mask(clean),
        "geometry_feature_units": {
            "center_delta_z": "meter",
            "distance_3d": "meter",
            "distance_xy": "meter",
            "vertical_gap_subject_on_object": "meter",
        },
        "geometry_normalization": "raw_witness_v2_numeric_features",
        "geometry_source": source_name,
    }


def make_q_block(raw_match: dict[str, Any] | None, generated: bool, counterfactual_type: str) -> dict[str, Any]:
    features = raw_match.get("raw_features", {}) if raw_match else {}
    missing = [field for field in RAW_FIELDS if safe_float(features.get(field)) is None]
    geometry = raw_match.get("geometry", {}) if raw_match else {}
    return {
        "asset_tier": "raw_witness_numeric_geometry",
        "coverage_features": {
            "coverage_has_raw_witness": 1.0 if raw_match else 0.0,
            "raw_witness_missing_flag": 0.0 if raw_match else 1.0,
            "raw_feature_available_ratio": (len(RAW_FIELDS) - len(missing)) / len(RAW_FIELDS),
            "generated_counterfactual": 1.0 if generated else 0.0,
        },
        "missing_geometry_flag": raw_match is None,
        "low_coverage_flag": bool(missing),
        "unsupported_family_flag": False,
        "evidence_conflict_flag": generated and counterfactual_type != "none",
        "raw_feature_missing_count": len(missing),
        "geometry_available": geometry.get("geometry_available"),
        "geometry_checkable": geometry.get("geometry_checkable"),
    }


def flip_vertical_predicate(predicate: str) -> str:
    if predicate == "higher than":
        return "lower than"
    if predicate == "lower than":
        return "higher than"
    return predicate


def make_row(
    *,
    row_id: str,
    group_id: str,
    role: str,
    source: dict[str, Any],
    raw_match: dict[str, Any],
    g_features: dict[str, Any],
    g_source_name: str,
    compatibility_label: str,
    counterfactual_type: str,
    generated: bool,
    predicate_override: str | None = None,
    subject_override: str | None = None,
    object_override: str | None = None,
    subject_id_override: Any = None,
    object_id_override: Any = None,
    donor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    predicate = predicate_override or str(source["predicate_label"])
    subject_label = subject_override or str(source["subject_label"])
    object_label = object_override or str(source["object_label"])
    subject_id = source["subject_id"] if subject_id_override is None else subject_id_override
    object_id = source["object_id"] if object_id_override is None else object_id_override
    t_block = make_t_block(source, predicate=predicate, subject=subject_label, obj=object_label)
    z_block = make_z_block(source, generated=generated)
    g_block = make_g_block(g_features, g_source_name)
    q_block = make_q_block(raw_match, generated=generated, counterfactual_type=counterfactual_type)
    p_geom = safe_float(source.get("p_geom_valid")) if not generated else None
    if counterfactual_type == "contact_gap_or_overlap_perturbation":
        p_geom = 0.0
    return {
        "schema_version": ROW_SCHEMA_VERSION,
        "row_id": row_id,
        "group_id": group_id,
        "row_role": role,
        "split": "train",
        "source_dataset": "Open3DSG_train",
        "relation_source": "open3dsg_train_full_generated_v2" if generated else "open3dsg_train_full_raw_witness_v2",
        "scan_id": source["scan_id"],
        "scene_id": source["scan_id"],
        "subject_instance_id": subject_id,
        "object_instance_id": object_id,
        "directed_pair_id": f"{source['scan_id']}::{subject_id}->{object_id}",
        "candidate_relation_text": f"{subject_label} {predicate} {object_label}",
        "T_e": t_block,
        "Z_e": z_block,
        "G_e": g_block,
        "Q_e": q_block,
        "p_geom_valid_baseline": p_geom,
        "geometry_status_baseline": source.get("geometry_status") if not generated else "generated_counterfactual",
        "official_gt_axis": {
            "gt_match_status": "not_joined_for_v2_candidate",
            "gt_predicates_for_pair": [],
            "gt_family_for_pair": [],
            "gt_used_as_model_input": False,
        },
        "audit_axis": {
            "audit_label": "not_human_audited_candidate",
            "geometry_support_label": "generated_candidate" if generated else "raw_witness_supported_candidate",
            "audit_evidence_tier": "raw_witness_numeric_geometry",
            "audit_provenance": "capacity_scan_materialized_candidate",
            "audit_hidden_fields_exposed": False,
        },
        "counterfactual_axis": {
            "compatibility_label": compatibility_label,
            "positive_tier": "P2_high_precision_geometry_supported" if compatibility_label == "positive" else "none",
            "negative_tier": "none" if compatibility_label == "positive" else "N_generated_counterfactual",
            "counterfactual_type": counterfactual_type,
            "anchor_row_id": None if compatibility_label == "positive" else group_id.replace("group_", "pos_"),
            "matching_fields": ["relation_family", "predicate_label", "source_score_rank_inherited", "raw_witness_available"],
            "relaxed_matching_fields": ["scan_id", "source_score_band"],
        },
        "observability_axis": {
            "observability_label": "observable" if not q_block["missing_geometry_flag"] else "insufficient",
            "observability_reason": "raw_witness_available" if not q_block["missing_geometry_flag"] else "missing_raw_witness",
            "p_obs_target_usable": True,
        },
        "reliability_eval_axis": {
            "reliability_label": "not_primary_for_v2_candidate",
            "label_source": "generated_compatibility_candidate_not_human_reliability_label",
            "binary_usable": False,
            "multiclass_usable": False,
        },
        "model_views": {
            "compatibility_main": {"T_e": t_block, "G_e": g_block},
            "source_only": {"Z_e": z_block},
            "semantic_source": {"T_e": t_block, "Z_e": z_block},
            "geometry_only": {"G_e": g_block},
            "obs_head": {"Q_e": q_block},
            "full_factorized": {"T_e": t_block, "Z_e": z_block, "G_e": g_block, "Q_e": q_block},
        },
        "hidden_control": {
            "anchor_prediction_id": source["prediction_id"],
            "donor_prediction_id": donor["prediction_id"] if donor else None,
            "source_queue_kind": source.get("queue_kind"),
            "source_geometry_status": source.get("geometry_status"),
            "source_rank_band": source.get("rank_band"),
            "source_label_match_status": source.get("label_match_status"),
            "source_machine_hint": source.get("machine_hint"),
            "source_matched_predicates": source.get("matched_predicates"),
            "source_reason_codes": source.get("reason_codes"),
            "counterfactual_type": counterfactual_type,
            "generated": generated,
            "hidden_fields_as_model_input": False,
        },
    }


def final_anchor_selection(buffers: dict[tuple[str, str], list[dict[str, Any]]], raw_matches: dict[str, dict[str, Any]]) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], list[dict[str, Any]]]:
    selected: dict[tuple[str, str], list[dict[str, Any]]] = {}
    errors: list[dict[str, Any]] = []
    for family, spec in PRIMARY_QUOTAS.items():
        for predicate, needed in spec["per_predicate_positive"].items():
            key = (family, predicate)
            matched = [row for row in buffers.get(key, []) if row["prediction_id"] in raw_matches]
            rows = select_diverse(matched, needed)
            selected[key] = rows
            if len(rows) < needed:
                errors.append({"error_type": "insufficient_matched_anchor_rows", "family": family, "predicate": predicate, "needed": needed, "actual": len(rows)})
    return selected, errors


def build_materialized_rows(selected: dict[tuple[str, str], list[dict[str, Any]]], raw_matches: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []

    support_anchors = (
        selected[("support_contact", "lying on")]
        + selected[("support_contact", "standing on")]
        + selected[("support_contact", "supported by")]
    )
    vertical_anchors = selected[("relative_vertical", "higher than")] + selected[("relative_vertical", "lower than")]

    for index, source in enumerate(support_anchors):
        group_id = f"group_support_{index:04d}"
        pos_row_id = f"pos_support_{index:04d}"
        neg_row_id = f"neg_support_{index:04d}"
        raw_match = raw_matches[source["prediction_id"]]
        raw_features = raw_match["raw_features"]
        positive = make_row(
            row_id=pos_row_id,
            group_id=group_id,
            role="anchor_positive",
            source=source,
            raw_match=raw_match,
            g_features=raw_features,
            g_source_name="raw_witness_v2_anchor_geometry",
            compatibility_label="positive",
            counterfactual_type="none",
            generated=False,
        )
        neg_type_selector = index % 3
        donor: dict[str, Any] | None = None
        if neg_type_selector == 0:
            counterfactual_type = "wrong_pair_geometry"
            donor = vertical_anchors[index % len(vertical_anchors)]
            neg_raw_match = raw_matches[donor["prediction_id"]]
            neg_features = neg_raw_match["raw_features"]
            neg_source_name = "raw_witness_v2_wrong_pair_geometry"
        elif neg_type_selector == 1:
            counterfactual_type = "shuffled_geometry"
            donor = support_anchors[(index + 41) % len(support_anchors)]
            neg_raw_match = raw_matches[donor["prediction_id"]]
            neg_features = neg_raw_match["raw_features"]
            neg_source_name = "raw_witness_v2_shuffled_geometry"
        else:
            counterfactual_type = "contact_gap_or_overlap_perturbation"
            neg_raw_match = raw_match
            neg_features = perturbed_support_features(raw_features)
            neg_source_name = "raw_witness_v2_contact_gap_or_overlap_perturbation"
        negative = make_row(
            row_id=neg_row_id,
            group_id=group_id,
            role="counterfactual_negative",
            source=source,
            raw_match=neg_raw_match,
            g_features=neg_features,
            g_source_name=neg_source_name,
            compatibility_label="counterfactual_negative",
            counterfactual_type=counterfactual_type,
            generated=True,
            donor=donor,
        )
        rows.extend([positive, negative])
        groups.append(
            {
                "group_id": group_id,
                "relation_family": "support_contact",
                "anchor_row_id": pos_row_id,
                "negative_row_id": neg_row_id,
                "counterfactual_type": counterfactual_type,
                "anchor_prediction_id": source["prediction_id"],
                "donor_prediction_id": donor["prediction_id"] if donor else None,
            }
        )

    vertical_by_predicate = {
        "higher than": selected[("relative_vertical", "higher than")],
        "lower than": selected[("relative_vertical", "lower than")],
    }
    v_index = 0
    for predicate, anchors in vertical_by_predicate.items():
        for local_index, source in enumerate(anchors):
            group_id = f"group_vertical_{v_index:04d}"
            pos_row_id = f"pos_vertical_{v_index:04d}"
            neg_row_id = f"neg_vertical_{v_index:04d}"
            raw_match = raw_matches[source["prediction_id"]]
            raw_features = raw_match["raw_features"]
            positive = make_row(
                row_id=pos_row_id,
                group_id=group_id,
                role="anchor_positive",
                source=source,
                raw_match=raw_match,
                g_features=raw_features,
                g_source_name="raw_witness_v2_anchor_geometry",
                compatibility_label="positive",
                counterfactual_type="none",
                generated=False,
            )
            if local_index < len(anchors) // 2:
                counterfactual_type = "predicate_flip"
                negative = make_row(
                    row_id=neg_row_id,
                    group_id=group_id,
                    role="counterfactual_negative",
                    source=source,
                    raw_match=raw_match,
                    g_features=raw_features,
                    g_source_name="raw_witness_v2_predicate_flip_geometry",
                    compatibility_label="counterfactual_negative",
                    counterfactual_type=counterfactual_type,
                    generated=True,
                    predicate_override=flip_vertical_predicate(str(source["predicate_label"])),
                )
            else:
                counterfactual_type = "subject_object_swap"
                negative = make_row(
                    row_id=neg_row_id,
                    group_id=group_id,
                    role="counterfactual_negative",
                    source=source,
                    raw_match=raw_match,
                    g_features=raw_features,
                    g_source_name="raw_witness_v2_subject_object_swap_geometry",
                    compatibility_label="counterfactual_negative",
                    counterfactual_type=counterfactual_type,
                    generated=True,
                    subject_override=str(source["object_label"]),
                    object_override=str(source["subject_label"]),
                    subject_id_override=source["object_id"],
                    object_id_override=source["subject_id"],
                )
            rows.extend([positive, negative])
            groups.append(
                {
                    "group_id": group_id,
                    "relation_family": "relative_vertical",
                    "anchor_row_id": pos_row_id,
                    "negative_row_id": neg_row_id,
                    "counterfactual_type": counterfactual_type,
                    "anchor_prediction_id": source["prediction_id"],
                    "donor_prediction_id": None,
                }
            )
            v_index += 1
    return rows, groups


def baseline_row(row: dict[str, Any]) -> dict[str, Any]:
    g_features = row["G_e"]["geometry_features"]
    base = {
        "row_id": row["row_id"],
        "group_id": row["group_id"],
        "y_compatibility": 1 if row["counterfactual_axis"]["compatibility_label"] == "positive" else 0,
        "relation_family": row["T_e"]["relation_family"],
        "predicate_label": row["T_e"]["predicate_label"],
        "row_role": row["row_role"],
        "counterfactual_type": row["counterfactual_axis"]["counterfactual_type"],
        "source_score_normalized": row["Z_e"]["source_score_normalized"],
        "source_rank": row["Z_e"]["source_rank"],
        "source_rank_band": row["Z_e"]["source_rank_band"],
        "p_geom_valid_baseline": row["p_geom_valid_baseline"],
        "q_raw_feature_available_ratio": row["Q_e"]["coverage_features"]["raw_feature_available_ratio"],
        "q_generated_counterfactual": row["Q_e"]["coverage_features"]["generated_counterfactual"],
    }
    for key, value in g_features.items():
        base[f"g_{key}"] = value
    return base


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "group_id": row["group_id"],
        "compatibility_label": row["counterfactual_axis"]["compatibility_label"],
        "relation_family": row["T_e"]["relation_family"],
        "predicate_label": row["T_e"]["predicate_label"],
        "subject_label": row["T_e"]["subject_label"],
        "object_label": row["T_e"]["object_label"],
        "counterfactual_type": row["counterfactual_axis"]["counterfactual_type"],
        "anchor_prediction_id": row["hidden_control"]["anchor_prediction_id"],
        "donor_prediction_id": row["hidden_control"]["donor_prediction_id"],
        "source_queue_kind": row["hidden_control"]["source_queue_kind"],
        "source_geometry_status": row["hidden_control"]["source_geometry_status"],
        "source_rank_band": row["hidden_control"]["source_rank_band"],
        "hidden_fields_as_model_input": row["hidden_control"]["hidden_fields_as_model_input"],
    }


def feature_range_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for key, value in row["G_e"]["geometry_features"].items():
            numeric = safe_float(value)
            if numeric is not None:
                values[key].append(numeric)
    out = []
    for key, nums in sorted(values.items()):
        out.append({"feature": key, "count": len(nums), "min": min(nums), "max": max(nums), "mean": sum(nums) / len(nums)})
    return out


def balance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters = {
        "family_label": Counter(),
        "predicate_label": Counter(),
        "counterfactual_type": Counter(),
        "role": Counter(),
    }
    for row in rows:
        label = row["counterfactual_axis"]["compatibility_label"]
        counters["family_label"][(row["T_e"]["relation_family"], label)] += 1
        counters["predicate_label"][(row["T_e"]["relation_family"], row["T_e"]["predicate_label"], label)] += 1
        counters["counterfactual_type"][(row["T_e"]["relation_family"], row["counterfactual_axis"]["counterfactual_type"], label)] += 1
        counters["role"][(row["row_role"], label)] += 1
    out: list[dict[str, Any]] = []
    for axis, counter in counters.items():
        for key, count in sorted(counter.items()):
            if not isinstance(key, tuple):
                key = (key,)
            out.append({"axis": axis, "key": "|".join(str(part) for part in key), "count": count})
    return out


def schema_contract() -> dict[str, Any]:
    return {
        "schema_version": ROW_SCHEMA_VERSION,
        "task": "compatibility_candidate_dataset_v2",
        "model_safe_views": ["source_only", "semantic_source", "geometry_only", "compatibility_main", "obs_head", "full_factorized"],
        "main_training_target": "counterfactual_axis.compatibility_label",
        "blocked_from_C_e": [
            "Z_e",
            "source score",
            "source rank",
            "queue_kind",
            "geometry_status",
            "rank_band",
            "label_match_status",
            "machine_hint",
            "target construction fields",
            "p_geom_valid_baseline",
        ],
        "G_e_policy": {
            "allowed": "predicate-independent numeric raw witness geometry",
            "blocked_feature_key_fragments": list(BLOCKED_G_FEATURE_FRAGMENTS),
            "p_geom_valid_role": "baseline only, not G_e main input",
        },
        "split_policy": "train_only_hypothesis_candidate",
        "paper_evidence_allowed": False,
    }


def validate_materialized(rows: list[dict[str, Any]], groups: list[dict[str, Any]], raw_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    counts = Counter()
    predicate_counts = Counter()
    ctype_counts = Counter()
    row_ids: set[str] = set()
    for row in rows:
        row_id = row["row_id"]
        if row_id in row_ids:
            errors.append({"error_type": "duplicate_row_id", "row_id": row_id})
        row_ids.add(row_id)
        label = row["counterfactual_axis"]["compatibility_label"]
        family = row["T_e"]["relation_family"]
        predicate = row["T_e"]["predicate_label"]
        counts[(family, label)] += 1
        predicate_counts[(family, predicate, label)] += 1
        ctype_counts[(family, row["counterfactual_axis"]["counterfactual_type"], label)] += 1
        if "Z_e" in row["model_views"]["compatibility_main"]:
            errors.append({"error_type": "z_e_in_compatibility_main", "row_id": row_id})
        for key in row["G_e"]["geometry_features"]:
            lowered = key.lower()
            if any(fragment in lowered for fragment in BLOCKED_G_FEATURE_FRAGMENTS):
                errors.append({"error_type": "blocked_g_feature_key", "row_id": row_id, "feature": key})
    expected = {
        ("support_contact", "positive"): 120,
        ("support_contact", "counterfactual_negative"): 120,
        ("relative_vertical", "positive"): 80,
        ("relative_vertical", "counterfactual_negative"): 80,
    }
    for key, value in expected.items():
        if counts[key] != value:
            errors.append({"error_type": "unexpected_family_label_count", "key": "|".join(key), "expected": value, "actual": counts[key]})
    expected_predicates = {
        ("support_contact", "lying on", "positive"): 40,
        ("support_contact", "standing on", "positive"): 40,
        ("support_contact", "supported by", "positive"): 40,
        ("support_contact", "lying on", "counterfactual_negative"): 40,
        ("support_contact", "standing on", "counterfactual_negative"): 40,
        ("support_contact", "supported by", "counterfactual_negative"): 40,
        ("relative_vertical", "higher than", "positive"): 40,
        ("relative_vertical", "lower than", "positive"): 40,
        ("relative_vertical", "higher than", "counterfactual_negative"): 40,
        ("relative_vertical", "lower than", "counterfactual_negative"): 40,
    }
    for key, value in expected_predicates.items():
        if predicate_counts[key] != value:
            errors.append({"error_type": "unexpected_predicate_label_count", "key": "|".join(key), "expected": value, "actual": predicate_counts[key]})
    required_counterfactuals = {
        ("support_contact", "wrong_pair_geometry", "counterfactual_negative"): 40,
        ("support_contact", "shuffled_geometry", "counterfactual_negative"): 40,
        ("support_contact", "contact_gap_or_overlap_perturbation", "counterfactual_negative"): 40,
        ("relative_vertical", "predicate_flip", "counterfactual_negative"): 40,
        ("relative_vertical", "subject_object_swap", "counterfactual_negative"): 40,
    }
    for key, value in required_counterfactuals.items():
        if ctype_counts[key] != value:
            errors.append({"error_type": "unexpected_counterfactual_count", "key": "|".join(key), "expected": value, "actual": ctype_counts[key]})
    if len(groups) != 200:
        errors.append({"error_type": "unexpected_group_count", "expected": 200, "actual": len(groups)})
    if raw_summary["matched_prediction_ids"] < 200:
        errors.append({"error_type": "raw_witness_match_count_too_low", "expected_min": 200, "actual": raw_summary["matched_prediction_ids"]})
    return errors


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# H002 Compatibility Dataset V2 Candidate Materialization",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"groups = {summary['counts']['groups']}",
        f"compatibility positive / negative = {summary['counts']['compatibility_positive']} / {summary['counts']['compatibility_negative']}",
        f"raw_witness matched / requested = {summary['raw_witness_join']['matched_prediction_ids']} / {summary['raw_witness_join']['requested_prediction_ids']}",
        f"learned_smoke_allowed = {str(summary['learned_smoke_allowed']).lower()}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Family Counts",
        "",
        "| Family | Positive | Negative |",
        "| --- | ---: | ---: |",
    ]
    for family in ["support_contact", "relative_vertical"]:
        pos = summary["counts"]["by_family_label"].get(f"{family}|positive", 0)
        neg = summary["counts"]["by_family_label"].get(f"{family}|counterfactual_negative", 0)
        lines.append(f"| `{family}` | {pos} | {neg} |")
    lines.extend(
        [
            "",
            "## Counterfactuals",
            "",
            "```text",
        ]
    )
    for key, value in sorted(summary["counts"]["by_counterfactual_type"].items()):
        lines.append(f"{key} = {value}")
    lines.extend(
        [
            "```",
            "",
            "## Boundary",
            "",
            "- This is a train-only hypothesis candidate dataset.",
            "- Direct HL/LH construction fields remain hidden controls and are not `C_e` inputs.",
            "- `C_e` uses `T_e + G_e` only.",
            "- Human reliability and paper evidence claims remain blocked until schema/shortcut audit and later smoke pass.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    capacity_summary = read_json(args.capacity_dir / "summary.json")
    errors: list[dict[str, Any]] = []
    if capacity_summary.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "actual": capacity_summary.get("status")})
    if capacity_summary.get("next_todo") != EXPECTED_CAPACITY_NEXT:
        errors.append({"error_type": "unexpected_capacity_next", "actual": capacity_summary.get("next_todo")})
    if validation_count(capacity_summary.get("validation_errors")) != 0:
        errors.append({"error_type": "capacity_validation_errors", "actual": capacity_summary.get("validation_errors")})
    if capacity_summary.get("row_materialization_allowed_with_controls") is not True:
        errors.append({"error_type": "capacity_does_not_allow_materialization", "actual": capacity_summary.get("row_materialization_allowed_with_controls")})
    if capacity_summary.get("direct_hl_lh_target_allowed") is not False:
        errors.append({"error_type": "capacity_direct_hl_lh_not_blocked", "actual": capacity_summary.get("direct_hl_lh_target_allowed")})

    buffers: dict[tuple[str, str], list[dict[str, Any]]] = {}
    scan_summary: dict[str, Any] = {}
    raw_matches: dict[str, dict[str, Any]] = {}
    raw_summary: dict[str, Any] = {
        "match_rows": rel_path(args.match_rows),
        "requested_prediction_ids": 0,
        "matched_prediction_ids": 0,
        "rows_scanned_until_complete": 0,
        "matched_by_family": {},
        "raw_fields": RAW_FIELDS,
    }
    rows: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    selected: dict[tuple[str, str], list[dict[str, Any]]] = {}

    if not errors:
        buffers, scan_summary = scan_anchor_buffers(args.lh_queue)
        buffer_ids = {row["prediction_id"] for values in buffers.values() for row in values}
        raw_matches, raw_summary = load_raw_witness(args.match_rows, buffer_ids)
        selected, selection_errors = final_anchor_selection(buffers, raw_matches)
        errors.extend(selection_errors)
    if not errors:
        rows, groups = build_materialized_rows(selected, raw_matches)
        errors.extend(validate_materialized(rows, groups, raw_summary))

    counts = Counter()
    predicate_counts = Counter()
    ctype_counts = Counter()
    for row in rows:
        label = row["counterfactual_axis"]["compatibility_label"]
        family = row["T_e"]["relation_family"]
        predicate = row["T_e"]["predicate_label"]
        counts[(family, label)] += 1
        predicate_counts[(family, predicate, label)] += 1
        ctype_counts[(family, row["counterfactual_axis"]["counterfactual_type"])] += 1

    status = STATUS_READY if not errors else STATUS_ERROR
    next_todo = NEXT_TODO if status == STATUS_READY else "fix_compatibility_dataset_v2_candidate_materialization"
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation_errors": len(errors),
        "next_todo": next_todo,
        "learned_smoke_allowed": False,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "counts": {
            "rows": len(rows),
            "groups": len(groups),
            "compatibility_positive": sum(1 for row in rows if row.get("counterfactual_axis", {}).get("compatibility_label") == "positive"),
            "compatibility_negative": sum(1 for row in rows if row.get("counterfactual_axis", {}).get("compatibility_label") == "counterfactual_negative"),
            "by_family_label": {f"{family}|{label}": count for (family, label), count in sorted(counts.items())},
            "by_predicate_label": {f"{family}|{predicate}|{label}": count for (family, predicate, label), count in sorted(predicate_counts.items())},
            "by_counterfactual_type": {f"{family}|{ctype}": count for (family, ctype), count in sorted(ctype_counts.items())},
            "selected_anchor_buffers": {f"{family}|{predicate}": len(values) for (family, predicate), values in sorted(buffers.items())},
            "selected_anchor_final": {f"{family}|{predicate}": len(values) for (family, predicate), values in sorted(selected.items())},
        },
        "raw_witness_join": raw_summary,
        "selection_scan": scan_summary,
        "boundary": {
            "split": "train_only_candidate_materialization",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_model": False,
            "runs_learned_smoke": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "direct_hl_lh_target_used": False,
            "generated_counterfactuals_used": True,
        },
        "input_roots": {
            "capacity_scan": rel_path(args.capacity_dir),
            "lh_queue": rel_path(args.lh_queue),
            "hl_queue": rel_path(args.hl_queue),
            "match_rows": rel_path(args.match_rows),
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "compatibility_rows": rel_path(args.output_dir / "compatibility_rows.jsonl"),
            "counterfactual_groups": rel_path(args.output_dir / "counterfactual_groups.jsonl"),
            "baseline_view": rel_path(args.output_dir / "baseline_view.jsonl"),
            "audit_view": rel_path(args.output_dir / "audit_view.jsonl"),
            "selection_manifest": rel_path(args.output_dir / "selection_manifest.jsonl"),
            "schema": rel_path(args.output_dir / "schema.json"),
            "split_manifest": rel_path(args.output_dir / "split_manifest.json"),
            "feature_ranges": rel_path(args.output_dir / "feature_ranges.csv"),
            "control_balance": rel_path(args.output_dir / "control_balance.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "compatibility_rows.jsonl", rows)
    write_jsonl(args.output_dir / "counterfactual_groups.jsonl", groups)
    write_jsonl(args.output_dir / "baseline_view.jsonl", [baseline_row(row) for row in rows])
    write_jsonl(args.output_dir / "audit_view.jsonl", [audit_row(row) for row in rows])
    selection_rows = [row for values in selected.values() for row in values]
    write_jsonl(args.output_dir / "selection_manifest.jsonl", selection_rows)
    write_json(args.output_dir / "schema.json", schema_contract())
    write_json(
        args.output_dir / "split_manifest.json",
        {
            "split": "train",
            "validation_usage": False,
            "test_usage": False,
            "source": "Open3DSG_train_full_H002_capacity_pool",
            "row_count": len(rows),
            "group_count": len(groups),
        },
    )
    write_csv(args.output_dir / "feature_ranges.csv", feature_range_rows(rows))
    write_csv(args.output_dir / "control_balance.csv", balance_rows(rows))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    (args.output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(f"status={status}")
    print(f"rows={len(rows)}")
    print(f"groups={len(groups)}")
    print(f"raw_matched={raw_summary['matched_prediction_ids']}/{raw_summary['requested_prediction_ids']}")
    print(f"next={next_todo}")
    print(f"validation_errors={len(errors)}")


if __name__ == "__main__":
    main()
