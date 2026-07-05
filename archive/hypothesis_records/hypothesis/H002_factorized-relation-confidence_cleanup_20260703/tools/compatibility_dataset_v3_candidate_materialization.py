#!/usr/bin/env python3
"""Materialize the H002 v3 predicate-conditioned compatibility candidate dataset."""

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

DEFAULT_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_capacity_scan"
DEFAULT_CONTRACT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_contract"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_candidate_materialization"

EXPECTED_CAPACITY_STATUS = "h002_compatibility_dataset_v3_capacity_scan_passed_ready_for_candidate_materialization"
EXPECTED_CAPACITY_NEXT = "compatibility_dataset_v3_candidate_materialization"
EXPECTED_CONTRACT_STATUS = "h002_compatibility_dataset_v3_contract_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_candidate_materialization_v1"
ROW_SCHEMA_VERSION = "h002_compatibility_dataset_v3_candidate_row_v1"
STATUS_READY = "h002_compatibility_dataset_v3_candidate_materialization_ready_for_schema_shortcut_audit"
STATUS_ERROR = "h002_compatibility_dataset_v3_candidate_materialization_input_errors"
NEXT_TODO = "compatibility_dataset_v3_schema_shortcut_audit"

VERTICAL_PREDICATES = {"higher than", "lower than"}
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

GROUP_QUOTA = 200
VISIBLE_PAIR_QUOTA = GROUP_QUOTA // 2
GROUPS_PER_DIRECTION = GROUP_QUOTA // 2
STRUCTURAL_ENDPOINTS = {"subject_room_surface", "object_floor", "object_wall_or_ceiling", "structural_endpoint"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--contract-dir", type=Path, default=DEFAULT_CONTRACT_DIR)
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
    if not fields:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def stable_hash(value: str, length: int = 16) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]


def stable_sort_key(value: str) -> str:
    return stable_hash(value, 24)


def geometry_hash(raw: dict[str, Any]) -> str:
    values = {}
    for field in RAW_FIELDS:
        value = safe_float(raw.get(field))
        values[field] = None if value is None else round(value, 8)
    return stable_hash(json.dumps(values, sort_keys=True), 20)


def directed_pair_id(row: dict[str, Any]) -> str:
    identity = row.get("identity", {})
    if identity.get("directed_pair_id"):
        return str(identity["directed_pair_id"])
    return "::".join(
        [
            str(identity.get("scan_id")),
            str(identity.get("subgraph_id")),
            str(identity.get("subject_id")),
            str(identity.get("object_id")),
        ]
    )


def visible_pair(subject: Any, obj: Any) -> str:
    return f"{norm(subject)}|{norm(obj)}"


def endpoint_state(subject: Any, obj: Any) -> str:
    s = norm(subject)
    o = norm(obj)
    if s in {"floor", "wall", "ceiling"}:
        return "subject_room_surface"
    if o == "floor":
        return "object_floor"
    if o in {"wall", "ceiling"}:
        return "object_wall_or_ceiling"
    if s in {"floor", "wall", "ceiling", "room", "door", "doorframe", "window"} or o in {
        "floor",
        "wall",
        "ceiling",
        "room",
        "door",
        "doorframe",
        "window",
    }:
        return "structural_endpoint"
    if s == o:
        return "same_label_pair"
    return "movable_object_pair"


def rank_band(rank: Any) -> str:
    value = safe_float(rank)
    if value is None:
        return "rank_unknown"
    if value <= 20:
        return "top20"
    if value <= 50:
        return "top50"
    if value <= 100:
        return "top100"
    if value <= 500:
        return "rank_101_500"
    if value <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def endpoint_priority(state: str) -> int:
    order = {
        "movable_object_pair": 0,
        "same_label_pair": 1,
        "structural_endpoint": 2,
        "object_floor": 3,
        "object_wall_or_ceiling": 3,
        "subject_room_surface": 3,
    }
    return order.get(state, 4)


def clear_vertical_state(raw: dict[str, Any], abs_margin: float, norm_margin: float) -> tuple[str, str | None]:
    center_delta = safe_float(raw.get("center_delta_z"))
    norm_delta = safe_float(raw.get("normalized_center_delta_z"))
    if center_delta is None or norm_delta is None:
        return "raw_missing_margin", None
    if center_delta == 0.0 or norm_delta == 0.0 or (center_delta > 0) != (norm_delta > 0):
        return "sign_mismatch_or_zero", None
    if abs(center_delta) < abs_margin:
        return "below_absolute_margin", None
    if abs(norm_delta) < norm_margin:
        return "below_normalized_margin", None
    if center_delta > 0:
        return "clear", "higher_positive"
    return "clear", "lower_positive"


def compact_source_row(row: dict[str, Any], raw_hash: str, line_no: int) -> dict[str, Any]:
    identity = row.get("identity", {})
    predicate = row.get("predicate", {})
    semantic = row.get("semantic", {})
    edge = row.get("edge", {})
    geometry = row.get("geometry", {})
    label = row.get("label", {})
    semantic_rank = semantic.get("rank_in_context") or semantic.get("predicate_rank_for_pair")
    return {
        "prediction_id": identity.get("prediction_id"),
        "scan_id": identity.get("scan_id"),
        "subgraph_id": identity.get("subgraph_id"),
        "subject_id": identity.get("subject_id"),
        "object_id": identity.get("object_id"),
        "subject_label": edge.get("subject_label"),
        "predicate_label": predicate.get("predicate_label"),
        "predicate_family": predicate.get("predicate_family"),
        "object_label": edge.get("object_label"),
        "source_id": row.get("source", {}).get("source_id", "open3dsg_train_full"),
        "semantic_score_raw": semantic.get("semantic_score_raw"),
        "semantic_score_norm": semantic.get("semantic_score_norm"),
        "semantic_rank": semantic_rank,
        "rank_band": row.get("rga", {}).get("rank_band") or rank_band(semantic_rank),
        "p_geom_valid_hidden": geometry.get("p_geom_valid"),
        "geometry_status_hidden": geometry.get("geometry_status"),
        "label_match_status_hidden": label.get("label_match_status"),
        "matched_predicates_hidden": label.get("matched_predicates", []),
        "geometry_feature_hash": raw_hash,
        "source_line_no": line_no,
    }


def validate_inputs(capacity: dict[str, Any], contract: dict[str, Any], match_rows: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if capacity.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "actual": capacity.get("status")})
    if capacity.get("next_todo") != EXPECTED_CAPACITY_NEXT:
        errors.append({"error_type": "unexpected_capacity_next_todo", "actual": capacity.get("next_todo")})
    if capacity.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors", "actual": capacity.get("validation_errors")})
    if capacity.get("candidate_materialization_allowed") is not True:
        errors.append({"error_type": "capacity_does_not_allow_materialization", "actual": capacity.get("candidate_materialization_allowed")})
    if contract.get("status") != EXPECTED_CONTRACT_STATUS:
        errors.append({"error_type": "unexpected_contract_status", "actual": contract.get("status")})
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def scan_candidates(match_rows: Path, abs_margin: float, norm_margin: float) -> dict[str, Any]:
    vertical_groups: dict[str, dict[str, Any]] = {}
    counters = Counter()

    with match_rows.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            counters["match_rows_scanned"] += 1
            row = json.loads(line)
            predicate = row.get("predicate", {})
            if predicate.get("predicate_family") != "relative_vertical":
                continue
            predicate_label = str(predicate.get("predicate_label") or "")
            if predicate_label not in VERTICAL_PREDICATES:
                continue
            counters["relative_vertical_rows"] += 1
            geometry = row.get("geometry", {})
            raw = geometry.get("raw_features") or {}
            if not raw:
                counters["relative_vertical_missing_raw"] += 1
                continue
            counters["relative_vertical_rows_with_raw"] += 1
            key = directed_pair_id(row)
            edge = row.get("edge", {})
            identity = row.get("identity", {})
            raw_hash = geometry_hash(raw)
            entry = vertical_groups.setdefault(
                key,
                {
                    "directed_pair_id": key,
                    "scan_id": identity.get("scan_id"),
                    "subgraph_id": identity.get("subgraph_id"),
                    "subject_id": identity.get("subject_id"),
                    "object_id": identity.get("object_id"),
                    "subject_label": edge.get("subject_label"),
                    "object_label": edge.get("object_label"),
                    "rows_by_predicate": {},
                    "raw_by_predicate": {},
                    "raw_hashes": set(),
                },
            )
            entry["rows_by_predicate"][predicate_label] = compact_source_row(row, raw_hash, line_no)
            entry["raw_by_predicate"][predicate_label] = raw
            entry["raw_hashes"].add(raw_hash)

    candidates: list[dict[str, Any]] = []
    rejection_reasons = Counter()
    for key, entry in vertical_groups.items():
        if not VERTICAL_PREDICATES <= set(entry["rows_by_predicate"]):
            rejection_reasons["missing_predicate_alternative"] += 1
            continue
        if len(entry["raw_hashes"]) != 1:
            rejection_reasons["geometry_hash_mismatch"] += 1
            continue
        raw = entry["raw_by_predicate"]["higher than"]
        state, direction = clear_vertical_state(raw, abs_margin=abs_margin, norm_margin=norm_margin)
        if state != "clear" or direction is None:
            rejection_reasons[state] += 1
            continue
        subject = entry["subject_label"]
        obj = entry["object_label"]
        candidate = {
            **entry,
            "raw": raw,
            "geometry_feature_hash": next(iter(entry["raw_hashes"])),
            "direction_bucket": direction,
            "positive_predicate": "higher than" if direction == "higher_positive" else "lower than",
            "negative_predicate": "lower than" if direction == "higher_positive" else "higher than",
            "visible_pair": visible_pair(subject, obj),
            "endpoint_state": endpoint_state(subject, obj),
            "stable_key": stable_sort_key(key + "|" + next(iter(entry["raw_hashes"]))),
        }
        candidates.append(candidate)

    return {
        "counters": counters,
        "vertical_groups": vertical_groups,
        "candidates": candidates,
        "rejection_reasons": rejection_reasons,
    }


def select_candidates(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_pair: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for candidate in candidates:
        by_pair[candidate["visible_pair"]][candidate["direction_bucket"]].append(candidate)

    mixed_pairs = []
    for pair, by_direction in by_pair.items():
        if by_direction["higher_positive"] and by_direction["lower_positive"]:
            representative = by_direction["higher_positive"][0]
            mixed_pairs.append(
                {
                    "visible_pair": pair,
                    "endpoint_state": representative["endpoint_state"],
                    "higher_count": len(by_direction["higher_positive"]),
                    "lower_count": len(by_direction["lower_positive"]),
                    "priority": endpoint_priority(representative["endpoint_state"]),
                    "stable_key": stable_sort_key(pair),
                }
            )

    mixed_pairs.sort(key=lambda row: (row["priority"], row["stable_key"]))
    endpoint_caps = {
        "movable_object_pair": 70,
        "same_label_pair": 20,
        "structural_endpoint": 30,
        "object_floor": 20,
        "object_wall_or_ceiling": 20,
        "subject_room_surface": 20,
    }

    selected_pairs: list[dict[str, Any]] = []
    endpoint_counts = Counter()
    for pair in mixed_pairs:
        state = pair["endpoint_state"]
        if endpoint_counts[state] >= endpoint_caps.get(state, 20):
            continue
        selected_pairs.append(pair)
        endpoint_counts[state] += 1
        if len(selected_pairs) == VISIBLE_PAIR_QUOTA:
            break

    if len(selected_pairs) < VISIBLE_PAIR_QUOTA:
        selected_ids = {row["visible_pair"] for row in selected_pairs}
        for pair in mixed_pairs:
            if pair["visible_pair"] in selected_ids:
                continue
            selected_pairs.append(pair)
            endpoint_counts[pair["endpoint_state"]] += 1
            if len(selected_pairs) == VISIBLE_PAIR_QUOTA:
                break

    selected_groups: list[dict[str, Any]] = []
    for pair in selected_pairs:
        pair_id = pair["visible_pair"]
        higher_pool = sorted(by_pair[pair_id]["higher_positive"], key=lambda row: row["stable_key"])
        lower_pool = sorted(by_pair[pair_id]["lower_positive"], key=lambda row: row["stable_key"])
        selected_groups.append(higher_pool[0])
        selected_groups.append(lower_pool[0])

    selected_groups.sort(key=lambda row: (row["visible_pair"], row["direction_bucket"], row["stable_key"]))
    diagnostics = {
        "mixed_visible_pair_cells_available": len(mixed_pairs),
        "selected_visible_pair_cells": len(selected_pairs),
        "selected_groups": len(selected_groups),
        "endpoint_pair_counts": dict(sorted(endpoint_counts.items())),
        "selection_policy": (
            "one higher-positive and one lower-positive geometry group per selected visible_pair; "
            "endpoint caps applied first, then relaxed if needed"
        ),
    }
    return selected_groups, diagnostics


def raw_geometry_block(raw: dict[str, Any], geometry_feature_hash: str) -> dict[str, Any]:
    subject_top = safe_float(raw.get("subject_top_z"))
    subject_bottom = safe_float(raw.get("subject_bottom_z"))
    object_top = safe_float(raw.get("object_top_z"))
    object_bottom = safe_float(raw.get("object_bottom_z"))
    center_delta = safe_float(raw.get("center_delta_z"))
    projected_subject = safe_float(raw.get("projected_subject_overlap_ratio")) or 0.0
    projected_object = safe_float(raw.get("projected_object_overlap_ratio")) or 0.0
    return {
        "center_delta_z_m": center_delta,
        "abs_center_delta_z_m": abs(center_delta) if center_delta is not None else None,
        "normalized_center_delta_z": safe_float(raw.get("normalized_center_delta_z")),
        "subject_center_z": ((subject_top + subject_bottom) / 2.0) if subject_top is not None and subject_bottom is not None else None,
        "object_center_z": ((object_top + object_bottom) / 2.0) if object_top is not None and object_bottom is not None else None,
        "subject_top_z": subject_top,
        "subject_bottom_z": subject_bottom,
        "object_top_z": object_top,
        "object_bottom_z": object_bottom,
        "distance_xy_m": safe_float(raw.get("distance_xy")),
        "distance_3d_m": safe_float(raw.get("distance_3d")),
        "normalized_distance_xy": safe_float(raw.get("normalized_distance_xy")),
        "bbox_iou_xy": safe_float(raw.get("projected_iou_xy")),
        "projected_overlap_max": max(projected_subject, projected_object),
        "projected_subject_overlap_ratio": projected_subject,
        "projected_object_overlap_ratio": projected_object,
        "vertical_gap_subject_on_object": safe_float(raw.get("vertical_gap_subject_on_object")),
        "geometry_feature_hash": geometry_feature_hash,
    }


def q_block() -> dict[str, Any]:
    missing = ["mesh", "multi_view"]
    return {
        "geometry_available": True,
        "obb_available": True,
        "mesh_available": False,
        "view_packet_available": False,
        "evidence_availability_count": 2,
        "missing_evidence_types": missing,
    }


def make_candidate_rows(selected_groups: list[dict[str, Any]], abs_margin: float, norm_margin: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    group_manifest: list[dict[str, Any]] = []
    for index, group in enumerate(selected_groups, start=1):
        group_id = "v3geom_" + stable_hash(group["directed_pair_id"] + "|" + group["geometry_feature_hash"])
        raw_block = raw_geometry_block(group["raw"], group["geometry_feature_hash"])
        group_manifest.append(
            {
                "geometry_group_id": group_id,
                "selection_index": index,
                "direction_bucket": group["direction_bucket"],
                "visible_pair": group["visible_pair"],
                "endpoint_state": group["endpoint_state"],
                "positive_predicate": group["positive_predicate"],
                "negative_predicate": group["negative_predicate"],
                "directed_pair_id": group["directed_pair_id"],
                "scan_id": group["scan_id"],
                "subgraph_id": group["subgraph_id"],
                "subject_id": group["subject_id"],
                "object_id": group["object_id"],
                "subject_label": group["subject_label"],
                "object_label": group["object_label"],
                "geometry_feature_hash": group["geometry_feature_hash"],
                "center_delta_z_m": raw_block["center_delta_z_m"],
                "normalized_center_delta_z": raw_block["normalized_center_delta_z"],
                "higher_prediction_id": group["rows_by_predicate"]["higher than"]["prediction_id"],
                "lower_prediction_id": group["rows_by_predicate"]["lower than"]["prediction_id"],
            }
        )
        for predicate_label in ["higher than", "lower than"]:
            source_row = group["rows_by_predicate"][predicate_label]
            y = 1 if predicate_label == group["positive_predicate"] else 0
            row_id = "h002v3_" + stable_hash(group_id + "|" + predicate_label)
            rows.append(
                {
                    "schema_version": ROW_SCHEMA_VERSION,
                    "row_id": row_id,
                    "geometry_group_id": group_id,
                    "split": "train",
                    "source_dataset": "open3dsg_train_full",
                    "scan_id": group["scan_id"],
                    "subgraph_id": group["subgraph_id"],
                    "subject_instance_id": group["subject_id"],
                    "object_instance_id": group["object_id"],
                    "directed_pair_id": group["directed_pair_id"],
                    "T_e": {
                        "predicate_label": predicate_label,
                        "predicate_text": predicate_label,
                        "relation_family": "relative_vertical",
                        "subject_class_label": group["subject_label"],
                        "object_class_label": group["object_label"],
                        "subject_object_text": f"{group['subject_label']} [REL] {group['object_label']}",
                    },
                    "Z_e_safe": {
                        "source_id": source_row["source_id"],
                        "source_score_available": source_row["semantic_score_norm"] is not None,
                        "source_score_raw": source_row["semantic_score_raw"],
                        "source_score_normalized": source_row["semantic_score_norm"],
                        "source_rank": source_row["semantic_rank"],
                        "source_rank_band": source_row["rank_band"],
                    },
                    "G_e_numeric": raw_block,
                    "Q_e_safe": q_block(),
                    "labels": {
                        "compatibility_label": y,
                        "compatibility_label_name": "compatible" if y else "incompatible",
                        "label_rule_id": "signed_vertical_order_margin_v3",
                        "label_margin_id": f"abs{abs_margin:.2f}_norm{norm_margin:.2f}",
                        "is_primary_same_geometry_predicate_contrast": True,
                    },
                    "controls_hidden": {
                        "raw_source_predicate": source_row["predicate_label"],
                        "construction_route": "v3_same_geometry_multi_predicate",
                        "counterfactual_type": "predicate_alternative_same_G",
                        "anchor_row_id": group_id,
                        "materialization_policy_id": "v3_matched_visible_pair_axis_control_v1",
                        "audit_only_geometry_status": source_row["geometry_status_hidden"],
                        "direction_bucket": group["direction_bucket"],
                        "positive_predicate": group["positive_predicate"],
                        "visible_pair": group["visible_pair"],
                        "endpoint_state": group["endpoint_state"],
                        "source_prediction_id": source_row["prediction_id"],
                        "source_line_no": source_row["source_line_no"],
                        "p_geom_valid_hidden": source_row["p_geom_valid_hidden"],
                        "label_match_status_hidden": source_row["label_match_status_hidden"],
                        "matched_predicates_hidden": source_row["matched_predicates_hidden"],
                    },
                }
            )
    rows.sort(key=lambda row: row["row_id"])
    group_manifest.sort(key=lambda row: row["geometry_group_id"])
    return rows, group_manifest


def sanitized_model_view(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "row_id": row["row_id"],
                "geometry_group_id_for_cv_only": row["geometry_group_id"],
                "target_y": row["labels"]["compatibility_label"],
                "target_name": "C_e_predicate_geometry_compatibility",
                "T_e": row["T_e"],
                "Z_e_safe": row["Z_e_safe"],
                "G_e_numeric": row["G_e_numeric"],
                "Q_e_safe": row["Q_e_safe"],
                "allowed_views": {
                    "semantic_only_T": ["T_e"],
                    "source_only_Z_safe": ["Z_e_safe"],
                    "geometry_only_G": ["G_e_numeric"],
                    "compatibility_TG": ["T_e", "G_e_numeric"],
                    "factorized_sanitized_TZGQ": ["T_e", "Z_e_safe", "G_e_numeric", "Q_e_safe"],
                },
                "blocked_as_features": [
                    "row_id",
                    "geometry_group_id_for_cv_only",
                    "target_y",
                    "labels",
                    "controls_hidden",
                ],
            }
        )
    return output


def axis_balance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes: dict[str, Counter[tuple[str, int]]] = defaultdict(Counter)
    for row in rows:
        y = int(row["labels"]["compatibility_label"])
        t = row["T_e"]
        z = row["Z_e_safe"]
        hidden = row["controls_hidden"]
        axis_values = {
            "predicate_label": t["predicate_label"],
            "visible_pair_hidden_control": hidden["visible_pair"],
            "predicate_visible_pair_hidden_control": f"{t['predicate_label']}|{hidden['visible_pair']}",
            "endpoint_state_hidden_control": hidden["endpoint_state"],
            "predicate_endpoint_state_hidden_control": f"{t['predicate_label']}|{hidden['endpoint_state']}",
            "subject_label": norm(t["subject_class_label"]),
            "object_label": norm(t["object_class_label"]),
            "source_rank_band": str(z["source_rank_band"]),
        }
        for axis, value in axis_values.items():
            axes[axis][(value, y)] += 1

    output = []
    total = len(rows)
    for axis, counter in sorted(axes.items()):
        grouped: dict[str, Counter[int]] = defaultdict(Counter)
        for (value, y), count in counter.items():
            grouped[value][y] += count
        majority = sum(max(counts.values()) for counts in grouped.values())
        mixed_values = sum(1 for counts in grouped.values() if counts[0] and counts[1])
        output.append(
            {
                "axis": axis,
                "axis_values": len(grouped),
                "mixed_label_values": mixed_values,
                "rows": total,
                "majority_accuracy_if_axis_only": round(majority / total, 6) if total else None,
                "risk_level": "high" if total and majority / total >= 0.90 else ("medium" if total and majority / total >= 0.75 else "low"),
                "value_counts_preview": json.dumps(
                    {value: {str(k): v for k, v in counts.items()} for value, counts in sorted(grouped.items())[:25]},
                    ensure_ascii=False,
                    sort_keys=True,
                )[:4000],
            }
        )
    return output


def group_integrity_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group[row["geometry_group_id"]].append(row)
    output = []
    for group_id, group_rows in sorted(by_group.items()):
        labels = [int(row["labels"]["compatibility_label"]) for row in group_rows]
        predicates = [row["T_e"]["predicate_label"] for row in group_rows]
        hashes = {row["G_e_numeric"]["geometry_feature_hash"] for row in group_rows}
        output.append(
            {
                "geometry_group_id": group_id,
                "rows": len(group_rows),
                "predicates": ";".join(sorted(predicates)),
                "label_sum": sum(labels),
                "geometry_hashes": len(hashes),
                "same_geometry_hash_pass": len(hashes) == 1,
                "one_positive_one_negative_pass": sorted(labels) == [0, 1],
                "higher_lower_predicates_pass": set(predicates) == VERTICAL_PREDICATES,
            }
        )
    return output


def selection_rows(diagnostics: dict[str, Any], group_manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    direction_counts = Counter(row["direction_bucket"] for row in group_manifest)
    endpoint_counts = Counter(row["endpoint_state"] for row in group_manifest)
    return [
        {"metric": "mixed_visible_pair_cells_available", "value": diagnostics["mixed_visible_pair_cells_available"]},
        {"metric": "selected_visible_pair_cells", "value": diagnostics["selected_visible_pair_cells"]},
        {"metric": "selected_groups", "value": diagnostics["selected_groups"]},
        {"metric": "candidate_rows", "value": len(group_manifest) * 2},
        {"metric": "higher_positive_groups", "value": direction_counts["higher_positive"]},
        {"metric": "lower_positive_groups", "value": direction_counts["lower_positive"]},
        {"metric": "endpoint_pair_counts", "value": json.dumps(dict(sorted(endpoint_counts.items())), sort_keys=True)},
    ]


def validate_outputs(rows: list[dict[str, Any]], group_manifest: list[dict[str, Any]], axis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(group_manifest) != GROUP_QUOTA:
        errors.append({"error_type": "unexpected_group_count", "actual": len(group_manifest), "expected": GROUP_QUOTA})
    if len(rows) != GROUP_QUOTA * 2:
        errors.append({"error_type": "unexpected_row_count", "actual": len(rows), "expected": GROUP_QUOTA * 2})
    direction_counts = Counter(row["direction_bucket"] for row in group_manifest)
    if direction_counts["higher_positive"] != GROUPS_PER_DIRECTION or direction_counts["lower_positive"] != GROUPS_PER_DIRECTION:
        errors.append({"error_type": "direction_balance_failed", "counts": dict(direction_counts)})
    for row in group_integrity_rows(rows):
        if not row["same_geometry_hash_pass"] or not row["one_positive_one_negative_pass"] or not row["higher_lower_predicates_pass"]:
            errors.append({"error_type": "group_integrity_failed", **row})
    high_axes = [row for row in axis_rows if row["risk_level"] == "high"]
    if high_axes:
        errors.append({"error_type": "high_axis_shortcut_after_selection", "axes": [row["axis"] for row in high_axes]})
    return errors


def write_report(path: Path, summary: dict[str, Any], axis_rows: list[dict[str, Any]]) -> None:
    risky = [row for row in axis_rows if row["risk_level"] != "low"]
    lines = [
        "# Compatibility Dataset V3 Candidate Materialization",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v3_candidate_materialization/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"candidate_rows = {summary['candidate_rows']}",
        f"geometry_groups = {summary['geometry_groups']}",
        f"higher_positive_groups = {summary['higher_positive_groups']}",
        f"lower_positive_groups = {summary['lower_positive_groups']}",
        f"axis_high_risk_after_selection = {summary['axis_high_risk_after_selection']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Selection Policy",
        "",
        "The materializer selected one `higher_positive` group and one `lower_positive` group from each",
        "selected visible-pair cell. This directly controls the high-risk `visible_pair` axis found in",
        "the capacity scan and prevents a `predicate + visible_pair` shortcut from solving the target.",
        "",
        "## Result",
        "",
        "- 100 mixed visible-pair cells",
        "- 200 geometry groups",
        "- 400 rows",
        "- each group has identical `G_e` for `higher than` and `lower than`",
        "- each group has exactly one compatible and one incompatible predicate row",
        "",
        "## Remaining Shortcut Risk",
        "",
    ]
    if risky:
        for row in risky:
            lines.append(f"- `{row['axis']}`: {row['risk_level']} ({row['majority_accuracy_if_axis_only']})")
    else:
        lines.append("- no high/medium axis shortcut remained in the materialized row-level audit")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- train-only candidate materialization",
            "- no learned smoke",
            "- no validation/test usage",
            "- no paper evidence promotion",
            "- no H001 artifact modification",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    capacity = read_json(args.capacity_dir / "summary.json")
    contract_summary = read_json(args.contract_dir / "summary.json")
    contract = read_json(args.contract_dir / "dataset_contract.json")
    input_errors = validate_inputs(capacity, contract_summary, args.match_rows)

    abs_margin = float(capacity["frozen_margin"]["abs_center_delta_z_min"])
    norm_margin = float(capacity["frozen_margin"]["normalized_center_delta_z_min"])

    if input_errors:
        rows: list[dict[str, Any]] = []
        group_manifest: list[dict[str, Any]] = []
        diagnostics = {"mixed_visible_pair_cells_available": 0, "selected_visible_pair_cells": 0, "selected_groups": 0}
        scan = {"counters": Counter(), "candidates": [], "rejection_reasons": Counter()}
    else:
        scan = scan_candidates(args.match_rows, abs_margin=abs_margin, norm_margin=norm_margin)
        selected_groups, diagnostics = select_candidates(scan["candidates"])
        rows, group_manifest = make_candidate_rows(selected_groups, abs_margin=abs_margin, norm_margin=norm_margin)

    model_view = sanitized_model_view(rows)
    axis_rows = axis_balance_rows(rows)
    group_integrity = group_integrity_rows(rows)
    selection = selection_rows(diagnostics, group_manifest)
    output_errors = validate_outputs(rows, group_manifest, axis_rows)
    errors = input_errors + output_errors

    direction_counts = Counter(row["direction_bucket"] for row in group_manifest)
    status = STATUS_READY if not errors else STATUS_ERROR
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO if not errors else "compatibility_dataset_v3_candidate_materialization_repair",
        "input_capacity_root": rel_path(args.capacity_dir),
        "input_contract_root": rel_path(args.contract_dir),
        "input_match_rows": rel_path(args.match_rows),
        "output_root": rel_path(args.output_dir),
        "dataset_name": "h002_compatibility_dataset_v3_predicate_conditioned",
        "candidate_rows": len(rows),
        "geometry_groups": len(group_manifest),
        "selected_visible_pair_cells": diagnostics.get("selected_visible_pair_cells", 0),
        "mixed_visible_pair_cells_available": diagnostics.get("mixed_visible_pair_cells_available", 0),
        "higher_positive_groups": direction_counts["higher_positive"],
        "lower_positive_groups": direction_counts["lower_positive"],
        "predicate_counts": dict(sorted(Counter(row["T_e"]["predicate_label"] for row in rows).items())),
        "compatibility_label_counts": dict(sorted(Counter(str(row["labels"]["compatibility_label"]) for row in rows).items())),
        "axis_high_risk_after_selection": [row["axis"] for row in axis_rows if row["risk_level"] == "high"],
        "axis_medium_risk_after_selection": [row["axis"] for row in axis_rows if row["risk_level"] == "medium"],
        "frozen_margin": {
            "abs_center_delta_z_min": abs_margin,
            "normalized_center_delta_z_min": norm_margin,
        },
        "materializes_dataset": True,
        "runs_learned_smoke": False,
        "paper_evidence_allowed": False,
        "validation_errors": len(errors),
        "boundary": {
            "candidate_materialization_only": True,
            "train_only": True,
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "candidate_rows": rel_path(args.output_dir / "candidate_rows.jsonl"),
            "sanitized_model_view": rel_path(args.output_dir / "sanitized_model_view.jsonl"),
            "group_manifest": rel_path(args.output_dir / "group_manifest.jsonl"),
            "group_integrity": rel_path(args.output_dir / "group_integrity.csv"),
            "axis_balance": rel_path(args.output_dir / "axis_balance.csv"),
            "selection_diagnostics": rel_path(args.output_dir / "selection_diagnostics.csv"),
            "rejection_reasons": rel_path(args.output_dir / "rejection_reasons.csv"),
            "model_view_contract": rel_path(args.output_dir / "model_view_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    model_view_contract = {
        "schema_version": "h002_v3_candidate_model_view_contract_v1",
        "allowed_model_view_file": "sanitized_model_view.jsonl",
        "target": "target_y",
        "group_key_for_cv_only": "geometry_group_id_for_cv_only",
        "primary_view": "compatibility_TG",
        "views": {
            "semantic_only_T": ["T_e"],
            "source_only_Z_safe": ["Z_e_safe"],
            "geometry_only_G": ["G_e_numeric"],
            "compatibility_TG": ["T_e", "G_e_numeric"],
            "factorized_sanitized_TZGQ": ["T_e", "Z_e_safe", "G_e_numeric", "Q_e_safe"],
        },
        "blocked_as_features": [
            "row_id",
            "geometry_group_id_for_cv_only",
            "target_y",
            "labels",
            "controls_hidden",
            "raw_source_predicate",
            "direction_bucket",
            "positive_predicate",
            "visible_pair",
            "endpoint_state",
        ],
    }

    write_jsonl(args.output_dir / "candidate_rows.jsonl", rows)
    write_jsonl(args.output_dir / "sanitized_model_view.jsonl", model_view)
    write_jsonl(args.output_dir / "group_manifest.jsonl", group_manifest)
    write_csv(args.output_dir / "group_integrity.csv", group_integrity)
    write_csv(args.output_dir / "axis_balance.csv", axis_rows)
    write_csv(args.output_dir / "selection_diagnostics.csv", selection)
    write_csv(args.output_dir / "rejection_reasons.csv", [{"reason": key, "groups": value} for key, value in sorted(scan["rejection_reasons"].items())])
    write_json(args.output_dir / "model_view_contract.json", model_view_contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, axis_rows)


if __name__ == "__main__":
    main()
