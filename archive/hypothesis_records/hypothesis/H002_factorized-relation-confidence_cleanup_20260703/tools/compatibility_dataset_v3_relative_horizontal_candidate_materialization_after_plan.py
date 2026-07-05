#!/usr/bin/env python3
"""Materialize H002 relative-horizontal same-G predicate-flip candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory"
)
DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan"
)
DEFAULT_TRAIN_RELATIONSHIPS = REPO_ROOT / "local_dataset/3DSSG_subset/relationships_train.json"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan"
)
SOURCE_INVENTORY_TOOL = (
    H2_ROOT / "tools/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan.py"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory_ready"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan"
EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_ready"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan_v1"
MODEL_SAFE_MAIN_SCHEMA = "h002_relative_horizontal_model_safe_main_view_v1"
MODEL_SAFE_QE_SCHEMA = "h002_relative_horizontal_model_safe_qe_view_v1"
HIDDEN_SCHEMA = "h002_relative_horizontal_hidden_manifest_v1"
GROUP_SCHEMA = "h002_relative_horizontal_group_manifest_v1"
DATASET_NAME = "h002_relative_horizontal_same_g_predicate_flip_v1"

STATUS_READY = (
    "h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan_ready_for_schema_shortcut_audit"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan_input_errors"
SELECTED_READY = "relative_horizontal_same_g_candidates_ready_for_schema_shortcut_audit"
NEXT_TODO = "compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization"

AXIS_SPECS = {
    "left_right": {
        "predicates": ("left", "right"),
        "axis_field": "delta_x_subject_minus_object",
        "selected_frame": "scene_world_x",
        "first_predicate": "left",
        "first_sign": "negative",
    },
    "front_behind": {
        "predicates": ("front", "behind"),
        "axis_field": "delta_y_subject_minus_object",
        "selected_frame": "scene_world_y",
        "first_predicate": "front",
        "first_sign": "negative",
    },
}
AXIS_PAIRS = tuple(AXIS_SPECS.keys())
PRIMARY_GROUPS_PER_AXIS_PAIR = 600
PRIMARY_GROUPS_PER_POSITIVE_PREDICATE = 300
PRIMARY_GROUPS_TOTAL = 1200
BOUNDARY_GROUPS_PER_AXIS_PAIR = 80
OPPOSING_GROUPS_PER_AXIS_PAIR = 80
MAX_GROUPS_PER_SCAN = 24
MAX_GROUPS_PER_CLASS_PAIR = 160
MAX_GROUPS_PER_CLASS_PAIR_AXIS_PAIR = 80
AXIS_BOUNDARY_MARGIN = 0.10

BLOCKED_MODEL_INPUT_KEYS = {
    "anchor_predicate_label",
    "axis_bucket_x",
    "axis_bucket_y",
    "axis_pair_label",
    "candidate_component",
    "class_pair",
    "compatibility_label",
    "directed_pair_predicate_key",
    "gt_predicate_label",
    "in_front_of_alias_flag",
    "is_original_gt_anchor",
    "object_class_label",
    "object_id",
    "p_obs_label",
    "p_rel_label",
    "scan_id",
    "selected_frame_compatible",
    "source_predicate_label",
    "subgraph_anchor_key",
    "subject_class_label",
    "subject_id",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--train-relationships", type=Path, default=DEFAULT_TRAIN_RELATIONSHIPS)
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
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def stable_hash(payload: Any, length: int = 18) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def finite_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        output = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(output):
        return None
    return output


def axis_bucket(value: float | None) -> str:
    if value is None:
        return "missing"
    if abs(value) < AXIS_BOUNDARY_MARGIN:
        return "boundary"
    return "positive" if value > 0 else "negative"


def load_source_inventory_module() -> Any:
    spec = importlib.util.spec_from_file_location("h002_relative_horizontal_source_inventory", SOURCE_INVENTORY_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load source inventory tool: {SOURCE_INVENTORY_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SourceArgs:
    def __init__(self, train_relationships: Path, scan_root: Path) -> None:
        self.train_relationships = train_relationships
        self.scan_root = scan_root


def validate_inputs(
    plan_summary: dict[str, Any],
    plan_errors: list[dict[str, Any]],
    source_summary: dict[str, Any],
    source_errors: list[dict[str, Any]],
    contract: dict[str, Any],
    selected_axis_rows: list[dict[str, str]],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    if plan_errors:
        errors.append({"error_type": "plan_validation_error_rows_present", "rows": len(plan_errors)})
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_status", "actual": source_summary.get("status")})
    if source_summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_validation_errors_present", "actual": source_summary.get("validation_errors")})
    if source_errors:
        errors.append({"error_type": "source_validation_error_rows_present", "rows": len(source_errors)})
    for summary_name, summary in [("plan", plan_summary), ("source", source_summary)]:
        boundary = summary.get("boundary", {})
        for key in [
            "h001_artifacts_modified",
            "paper_evidence_allowed",
            "runs_new_learned_smoke",
            "trains_new_model",
            "validation_usage",
            "test_usage",
        ]:
            if boundary.get(key) is not False:
                errors.append(
                    {
                        "error_type": "upstream_boundary_not_false",
                        "summary": summary_name,
                        "key": key,
                        "actual": boundary.get(key),
                    }
                )
    if int(contract.get("quota", {}).get("primary_groups", 0)) != PRIMARY_GROUPS_TOTAL:
        errors.append({"error_type": "unexpected_primary_group_quota", "actual": contract.get("quota", {})})
    selected_axis_map = {row.get("axis_pair"): row for row in selected_axis_rows}
    for axis_pair, spec in AXIS_SPECS.items():
        row = selected_axis_map.get(axis_pair)
        if not row:
            errors.append({"error_type": "missing_selected_axis_row", "axis_pair": axis_pair})
            continue
        if row.get("axis_candidate") != spec["selected_frame"]:
            errors.append(
                {
                    "error_type": "selected_frame_mismatch",
                    "axis_pair": axis_pair,
                    "actual": row.get("axis_candidate"),
                    "expected": spec["selected_frame"],
                }
            )
        if row.get("first_predicate_sign") != spec["first_sign"]:
            errors.append(
                {
                    "error_type": "selected_sign_mismatch",
                    "axis_pair": axis_pair,
                    "actual": row.get("first_predicate_sign"),
                    "expected": spec["first_sign"],
                }
            )
    if not args.train_relationships.exists():
        errors.append({"error_type": "missing_train_relationships", "path": rel_path(args.train_relationships)})
    if not args.scan_root.exists():
        errors.append({"error_type": "missing_scan_root", "path": rel_path(args.scan_root)})
    return errors


def signed_axis_value(anchor: dict[str, Any], axis_pair: str) -> float | None:
    return finite_float(anchor.get(AXIS_SPECS[axis_pair]["axis_field"]))


def compatible_predicate_for_axis(axis_pair: str, value: float | None) -> str | None:
    bucket = axis_bucket(value)
    if bucket in {"missing", "boundary"}:
        return None
    first, second = AXIS_SPECS[axis_pair]["predicates"]
    first_sign = AXIS_SPECS[axis_pair]["first_sign"]
    if bucket == first_sign:
        return first
    return second


def anchor_compatibility_state(anchor: dict[str, Any], axis_pair: str) -> str:
    if anchor.get("predicate_label") not in AXIS_SPECS[axis_pair]["predicates"]:
        return "not_axis_pair"
    compatible = compatible_predicate_for_axis(axis_pair, signed_axis_value(anchor, axis_pair))
    if compatible is None:
        return axis_bucket(signed_axis_value(anchor, axis_pair))
    return "compatible" if anchor.get("predicate_label") == compatible else "opposes"


def g_features(anchor: dict[str, Any]) -> dict[str, float | None]:
    dx = finite_float(anchor.get("delta_x_subject_minus_object"))
    dy = finite_float(anchor.get("delta_y_subject_minus_object"))
    distance = finite_float(anchor.get("horizontal_distance"))
    return {
        "delta_x_subject_minus_object": dx,
        "delta_y_subject_minus_object": dy,
        "horizontal_distance": distance,
    }


def geometry_hash(anchor: dict[str, Any]) -> str:
    features = g_features(anchor)
    rounded = {key: None if value is None else round(value, 10) for key, value in features.items()}
    return stable_hash(rounded)


def q_features(anchor: dict[str, Any], axis_pair: str, component: str) -> dict[str, Any]:
    value = signed_axis_value(anchor, axis_pair)
    abs_offset = None if value is None else abs(value)
    if component == "axis_boundary_qe_diagnostic":
        state = "axis_boundary_uncertain"
    elif component == "opposing_frame_diagnostic":
        state = "frame_disagreement_needs_audit"
    else:
        state = "sufficient_world_axis_margin"
    return {
        "axis_boundary_margin_m": AXIS_BOUNDARY_MARGIN,
        "abs_selected_axis_offset": abs_offset,
        "selected_axis_value": value,
        "scene_world_frame_available": bool(anchor.get("scene_world_frame_available")),
        "camera_pose_available": bool(anchor.get("camera_pose_available")),
        "sequence_dir_available": bool(anchor.get("sequence_dir_available")),
        "multi_view_dir_available": bool(anchor.get("multi_view_dir_available")),
        "frame_observability_state": state,
    }


def label_state(component: str, candidate_predicate: str, anchor: dict[str, Any], axis_pair: str) -> dict[str, Any]:
    compatible = compatible_predicate_for_axis(axis_pair, signed_axis_value(anchor, axis_pair))
    if component == "primary_same_g_compatibility":
        label = 1 if candidate_predicate == compatible else 0
        return {
            "C_e": label,
            "p_rel": "accept" if label == 1 else "reject",
            "p_obs": "observable",
            "target_source": "world_frame_same_g_predicate_flip",
        }
    if component == "axis_boundary_qe_diagnostic":
        return {
            "C_e": None,
            "p_rel": "abstain",
            "p_obs": "axis_boundary_uncertain",
            "target_source": "diagnostic_axis_boundary",
        }
    return {
        "C_e": None,
        "p_rel": "audit",
        "p_obs": "frame_disagreement",
        "target_source": "diagnostic_frame_disagreement",
    }


def feature_blocks(anchor: dict[str, Any], candidate_predicate: str, axis_pair: str, component: str) -> dict[str, Any]:
    return {
        "T_e": {
            "predicate_text": candidate_predicate,
            "predicate_label": candidate_predicate,
            "relation_family": "relative_horizontal",
        },
        "G_e_horizontal": g_features(anchor),
        "Q_e_frame": q_features(anchor, axis_pair, component),
    }


def model_safe_main_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if row["subset"] != "primary_compatibility":
        return None
    return {
        "schema_version": MODEL_SAFE_MAIN_SCHEMA,
        "dataset_name": DATASET_NAME,
        "row_id": row["row_id"],
        "group_id": row["group_id"],
        "split": "train",
        "subset": row["subset"],
        "feature_blocks": {
            "T_e": row["feature_blocks"]["T_e"],
            "G_e_horizontal": row["feature_blocks"]["G_e_horizontal"],
        },
        "labels": row["labels"],
        "model_use": "main_train_candidate_if_schema_audit_passes",
    }


def model_safe_qe_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": MODEL_SAFE_QE_SCHEMA,
        "dataset_name": DATASET_NAME,
        "row_id": row["row_id"],
        "group_id": row["group_id"],
        "split": "train",
        "subset": row["subset"],
        "feature_blocks": {"Q_e_frame": row["feature_blocks"]["Q_e_frame"]},
        "labels": {
            "p_obs": row["labels"]["p_obs"],
            "target_source": row["labels"]["target_source"],
        },
        "model_use": "q_e_or_frame_diagnostic_after_schema_audit",
    }


def build_rows_for_group(
    anchor: dict[str, Any],
    axis_pair: str,
    component: str,
    group_index: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    predicates = AXIS_SPECS[axis_pair]["predicates"]
    subset = {
        "primary_same_g_compatibility": "primary_compatibility",
        "axis_boundary_qe_diagnostic": "diagnostic_axis_boundary",
        "opposing_frame_diagnostic": "diagnostic_frame_disagreement",
    }[component]
    positive_predicate = compatible_predicate_for_axis(axis_pair, signed_axis_value(anchor, axis_pair))
    group_id = "h002_rh_group_" + stable_hash(
        {
            "component": component,
            "axis_pair": axis_pair,
            "scan": anchor.get("scan_id"),
            "subgraph": anchor.get("subgraph_id"),
            "subject": anchor.get("subject_id"),
            "object": anchor.get("object_id"),
            "source_predicate": anchor.get("predicate_label"),
            "group_index": group_index,
        }
    )
    g_hash = geometry_hash(anchor)
    rows: list[dict[str, Any]] = []
    for candidate_predicate in predicates:
        row_id = "h002_rh_row_" + stable_hash({"group_id": group_id, "predicate": candidate_predicate})
        labels = label_state(component, candidate_predicate, anchor, axis_pair)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "dataset_name": DATASET_NAME,
                "row_id": row_id,
                "group_id": group_id,
                "group_index": group_index,
                "split": "train",
                "subset": subset,
                "candidate_component": component,
                "axis_pair": axis_pair,
                "selected_frame": AXIS_SPECS[axis_pair]["selected_frame"],
                "candidate_predicate_label": candidate_predicate,
                "candidate_predicate_text": candidate_predicate,
                "relation_family": "relative_horizontal",
                "source_predicate_label": anchor.get("predicate_label"),
                "anchor_predicate_label": anchor.get("predicate_label"),
                "is_original_gt_anchor": candidate_predicate == anchor.get("predicate_label"),
                "selected_frame_compatible": candidate_predicate == positive_predicate
                if positive_predicate is not None
                else None,
                "subject_id": anchor.get("subject_id"),
                "object_id": anchor.get("object_id"),
                "scan_id": anchor.get("scan_id"),
                "subgraph_id": anchor.get("subgraph_id"),
                "subject_class_label": anchor.get("subject_label"),
                "object_class_label": anchor.get("object_label"),
                "class_pair": anchor.get("class_pair"),
                "directed_pair_key": anchor.get("directed_pair_key"),
                "directed_pair_predicate_key": anchor.get("directed_pair_predicate_key"),
                "subgraph_anchor_key": anchor.get("subgraph_anchor_key"),
                "geometry_hash": g_hash,
                "selected_axis_value": signed_axis_value(anchor, axis_pair),
                "selected_axis_bucket": axis_bucket(signed_axis_value(anchor, axis_pair)),
                "x_axis_bucket": anchor.get("x_axis_bucket"),
                "y_axis_bucket": anchor.get("y_axis_bucket"),
                "anchor_compatibility_state": anchor_compatibility_state(anchor, axis_pair),
                "feature_blocks": feature_blocks(anchor, candidate_predicate, axis_pair, component),
                "labels": labels,
                "model_use": "main_train_candidate_if_schema_audit_passes"
                if subset == "primary_compatibility"
                else "diagnostic_only",
            }
        )
    group = {
        "schema_version": GROUP_SCHEMA,
        "dataset_name": DATASET_NAME,
        "group_id": group_id,
        "group_index": group_index,
        "candidate_component": component,
        "subset": subset,
        "split": "train",
        "axis_pair": axis_pair,
        "selected_frame": AXIS_SPECS[axis_pair]["selected_frame"],
        "scan_id": anchor.get("scan_id"),
        "subgraph_id": anchor.get("subgraph_id"),
        "subject_id": anchor.get("subject_id"),
        "object_id": anchor.get("object_id"),
        "class_pair": anchor.get("class_pair"),
        "source_predicate_label": anchor.get("predicate_label"),
        "anchor_compatibility_state": anchor_compatibility_state(anchor, axis_pair),
        "selected_axis_value": signed_axis_value(anchor, axis_pair),
        "selected_axis_bucket": axis_bucket(signed_axis_value(anchor, axis_pair)),
        "geometry_hash": g_hash,
        "row_ids": [row["row_id"] for row in rows],
        "candidate_predicates": list(predicates),
        "primary_positive_predicate": positive_predicate if component == "primary_same_g_compatibility" else None,
    }
    return rows, group


def sorted_anchor_deque(rows: list[dict[str, Any]]) -> deque[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda row: stable_hash(
            {
                "scan": row.get("scan_id"),
                "subgraph": row.get("subgraph_id"),
                "subject": row.get("subject_id"),
                "object": row.get("object_id"),
                "predicate": row.get("predicate_label"),
            }
        ),
    )
    return deque(ordered)


def select_primary_groups(anchors: list[dict[str, Any]]) -> tuple[list[tuple[dict[str, Any], str]], dict[str, Any]]:
    buckets: dict[tuple[str, str], deque[dict[str, Any]]] = {}
    candidate_counts: dict[str, int] = {}
    for axis_pair, spec in AXIS_SPECS.items():
        for positive_predicate in spec["predicates"]:
            subset = [
                anchor
                for anchor in anchors
                if anchor.get("centroid_pair_available")
                and anchor.get("predicate_label") == positive_predicate
                and anchor_compatibility_state(anchor, axis_pair) == "compatible"
            ]
            buckets[(axis_pair, positive_predicate)] = sorted_anchor_deque(subset)
            candidate_counts[f"{axis_pair}:{positive_predicate}"] = len(subset)

    selected: list[tuple[dict[str, Any], str]] = []
    target_counts: Counter[tuple[str, str]] = Counter()
    axis_counts: Counter[str] = Counter()
    scan_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    class_axis_counts: Counter[tuple[str, str]] = Counter()
    selected_pairs: set[tuple[str, str]] = set()
    skipped: Counter[str] = Counter()
    bucket_order = [
        ("left_right", "left"),
        ("left_right", "right"),
        ("front_behind", "front"),
        ("front_behind", "behind"),
    ]

    progress = True
    while progress and any(
        target_counts[(axis_pair, predicate)] < PRIMARY_GROUPS_PER_POSITIVE_PREDICATE
        for axis_pair, predicate in bucket_order
    ):
        progress = False
        for axis_pair, positive_predicate in bucket_order:
            if target_counts[(axis_pair, positive_predicate)] >= PRIMARY_GROUPS_PER_POSITIVE_PREDICATE:
                continue
            bucket = buckets[(axis_pair, positive_predicate)]
            while bucket:
                anchor = bucket.popleft()
                pair_key = (axis_pair, str(anchor.get("directed_pair_key")))
                scan_id = str(anchor.get("scan_id"))
                class_pair = str(anchor.get("class_pair"))
                if pair_key in selected_pairs:
                    skipped["duplicate_directed_pair"] += 1
                    continue
                if scan_counts[scan_id] >= MAX_GROUPS_PER_SCAN:
                    skipped["scan_cap"] += 1
                    continue
                if class_counts[class_pair] >= MAX_GROUPS_PER_CLASS_PAIR:
                    skipped["class_pair_cap"] += 1
                    continue
                if class_axis_counts[(class_pair, axis_pair)] >= MAX_GROUPS_PER_CLASS_PAIR_AXIS_PAIR:
                    skipped["class_pair_axis_pair_cap"] += 1
                    continue
                selected.append((anchor, axis_pair))
                selected_pairs.add(pair_key)
                target_counts[(axis_pair, positive_predicate)] += 1
                axis_counts[axis_pair] += 1
                scan_counts[scan_id] += 1
                class_counts[class_pair] += 1
                class_axis_counts[(class_pair, axis_pair)] += 1
                progress = True
                break

    profile = {
        "candidate_counts": candidate_counts,
        "selected_primary_groups": len(selected),
        "axis_counts": dict(axis_counts),
        "positive_predicate_counts": {f"{k[0]}:{k[1]}": int(v) for k, v in sorted(target_counts.items())},
        "scan_max_groups": max(scan_counts.values(), default=0),
        "class_pair_max_groups": max(class_counts.values(), default=0),
        "class_pair_axis_pair_max_groups": max(class_axis_counts.values(), default=0),
        "selected_scans": len(scan_counts),
        "selected_class_pairs": len(class_counts),
        "skipped": dict(skipped),
    }
    return selected, profile


def select_diagnostic_groups(
    anchors: list[dict[str, Any]],
    component: str,
    per_axis_pair: int,
    excluded_pair_keys: set[tuple[str, str]],
) -> tuple[list[tuple[dict[str, Any], str]], dict[str, Any]]:
    selected: list[tuple[dict[str, Any], str]] = []
    profile: dict[str, Any] = {}
    for axis_pair, spec in AXIS_SPECS.items():
        if component == "axis_boundary_qe_diagnostic":
            subset = [
                anchor
                for anchor in anchors
                if anchor.get("centroid_pair_available")
                and anchor.get("predicate_label") in spec["predicates"]
                and anchor_compatibility_state(anchor, axis_pair) == "boundary"
            ]
        else:
            subset = [
                anchor
                for anchor in anchors
                if anchor.get("centroid_pair_available")
                and anchor.get("predicate_label") in spec["predicates"]
                and anchor_compatibility_state(anchor, axis_pair) == "opposes"
            ]
        buckets: dict[str, deque[dict[str, Any]]] = {}
        for predicate in spec["predicates"]:
            buckets[predicate] = sorted_anchor_deque([anchor for anchor in subset if anchor.get("predicate_label") == predicate])
        target_per_predicate = per_axis_pair // len(spec["predicates"])
        counts: Counter[str] = Counter()
        skipped: Counter[str] = Counter()
        for predicate in spec["predicates"]:
            bucket = buckets[predicate]
            while bucket and counts[predicate] < target_per_predicate:
                anchor = bucket.popleft()
                pair_key = (axis_pair, str(anchor.get("directed_pair_key")))
                if pair_key in excluded_pair_keys:
                    skipped["excluded_directed_pair"] += 1
                    continue
                selected.append((anchor, axis_pair))
                excluded_pair_keys.add(pair_key)
                counts[predicate] += 1
        profile[axis_pair] = {
            "available": len(subset),
            "selected": sum(counts.values()),
            "predicate_counts": dict(counts),
            "skipped": dict(skipped),
        }
    return selected, profile


def build_hidden_manifest(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": HIDDEN_SCHEMA,
        "dataset_name": DATASET_NAME,
        "row_id": row["row_id"],
        "group_id": row["group_id"],
        "split": row["split"],
        "subset": row["subset"],
        "candidate_component": row["candidate_component"],
        "axis_pair": row["axis_pair"],
        "selected_frame": row["selected_frame"],
        "candidate_predicate_label": row["candidate_predicate_label"],
        "source_predicate_label": row["source_predicate_label"],
        "anchor_predicate_label": row["anchor_predicate_label"],
        "is_original_gt_anchor": row["is_original_gt_anchor"],
        "selected_frame_compatible": row["selected_frame_compatible"],
        "labels": row["labels"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "object_id": row["object_id"],
        "subject_class_label": row["subject_class_label"],
        "object_class_label": row["object_class_label"],
        "class_pair": row["class_pair"],
        "directed_pair_key": row["directed_pair_key"],
        "directed_pair_predicate_key": row["directed_pair_predicate_key"],
        "subgraph_anchor_key": row["subgraph_anchor_key"],
        "geometry_hash": row["geometry_hash"],
        "selected_axis_value": row["selected_axis_value"],
        "selected_axis_bucket": row["selected_axis_bucket"],
        "x_axis_bucket": row["x_axis_bucket"],
        "y_axis_bucket": row["y_axis_bucket"],
        "anchor_compatibility_state": row["anchor_compatibility_state"],
    }


def iter_keys(payload: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            keys.append(path)
            keys.extend(iter_keys(value, path))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            keys.extend(iter_keys(value, f"{prefix}[{index}]"))
    return keys


def blocked_model_input_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in rows:
        feature_keys = set(iter_keys(row.get("feature_blocks", {})))
        top_level_keys = set(row.keys()) - {"labels"}
        for key in sorted(top_level_keys | feature_keys):
            terminal = key.split(".")[-1]
            if terminal in BLOCKED_MODEL_INPUT_KEYS:
                hits.append({"row_id": row.get("row_id"), "blocked_key": key})
                break
    return hits


def cap_audit_rows(group_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary = [group for group in group_rows if group["subset"] == "primary_compatibility"]
    class_counts = Counter(group["class_pair"] for group in primary)
    class_axis_counts = Counter((group["class_pair"], group["axis_pair"]) for group in primary)
    scan_counts = Counter(group["scan_id"] for group in primary)
    return [
        {
            "cap_name": "max_groups_per_scan",
            "limit": MAX_GROUPS_PER_SCAN,
            "observed_max": max(scan_counts.values(), default=0),
            "pass": max(scan_counts.values(), default=0) <= MAX_GROUPS_PER_SCAN,
        },
        {
            "cap_name": "max_groups_per_class_pair",
            "limit": MAX_GROUPS_PER_CLASS_PAIR,
            "observed_max": max(class_counts.values(), default=0),
            "pass": max(class_counts.values(), default=0) <= MAX_GROUPS_PER_CLASS_PAIR,
        },
        {
            "cap_name": "max_groups_per_class_pair_axis_pair",
            "limit": MAX_GROUPS_PER_CLASS_PAIR_AXIS_PAIR,
            "observed_max": max(class_axis_counts.values(), default=0),
            "pass": max(class_axis_counts.values(), default=0) <= MAX_GROUPS_PER_CLASS_PAIR_AXIS_PAIR,
        },
    ]


def quota_audit_rows(candidate_rows: list[dict[str, Any]], group_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary_rows = [row for row in candidate_rows if row["subset"] == "primary_compatibility"]
    primary_groups = [group for group in group_rows if group["subset"] == "primary_compatibility"]
    labels = Counter(row["labels"]["C_e"] for row in primary_rows)
    predicates = Counter(row["candidate_predicate_label"] for row in primary_rows)
    axis_groups = Counter(group["axis_pair"] for group in primary_groups)
    positive_predicates = Counter(
        row["candidate_predicate_label"] for row in primary_rows if row["labels"].get("C_e") == 1
    )
    return [
        {"metric": "primary_groups", "expected": PRIMARY_GROUPS_TOTAL, "actual": len(primary_groups)},
        {"metric": "primary_rows", "expected": PRIMARY_GROUPS_TOTAL * 2, "actual": len(primary_rows)},
        {"metric": "primary_positive_rows", "expected": PRIMARY_GROUPS_TOTAL, "actual": labels[1]},
        {"metric": "primary_negative_rows", "expected": PRIMARY_GROUPS_TOTAL, "actual": labels[0]},
        {"metric": "left_right_groups", "expected": PRIMARY_GROUPS_PER_AXIS_PAIR, "actual": axis_groups["left_right"]},
        {"metric": "front_behind_groups", "expected": PRIMARY_GROUPS_PER_AXIS_PAIR, "actual": axis_groups["front_behind"]},
        {"metric": "left_rows", "expected": PRIMARY_GROUPS_PER_AXIS_PAIR, "actual": predicates["left"]},
        {"metric": "right_rows", "expected": PRIMARY_GROUPS_PER_AXIS_PAIR, "actual": predicates["right"]},
        {"metric": "front_rows", "expected": PRIMARY_GROUPS_PER_AXIS_PAIR, "actual": predicates["front"]},
        {"metric": "behind_rows", "expected": PRIMARY_GROUPS_PER_AXIS_PAIR, "actual": predicates["behind"]},
        {"metric": "positive_left_rows", "expected": PRIMARY_GROUPS_PER_POSITIVE_PREDICATE, "actual": positive_predicates["left"]},
        {"metric": "positive_right_rows", "expected": PRIMARY_GROUPS_PER_POSITIVE_PREDICATE, "actual": positive_predicates["right"]},
        {"metric": "positive_front_rows", "expected": PRIMARY_GROUPS_PER_POSITIVE_PREDICATE, "actual": positive_predicates["front"]},
        {"metric": "positive_behind_rows", "expected": PRIMARY_GROUPS_PER_POSITIVE_PREDICATE, "actual": positive_predicates["behind"]},
    ]


def schema_precheck(
    candidate_rows: list[dict[str, Any]],
    model_safe_main_rows: list[dict[str, Any]],
    model_safe_qe_rows: list[dict[str, Any]],
    group_rows: list[dict[str, Any]],
    selection_profile: dict[str, Any],
) -> dict[str, Any]:
    subset_counts = Counter(row["subset"] for row in candidate_rows)
    component_counts = Counter(row["candidate_component"] for row in candidate_rows)
    primary_rows = [row for row in candidate_rows if row["subset"] == "primary_compatibility"]
    primary_groups = [group for group in group_rows if group["subset"] == "primary_compatibility"]
    label_counts = Counter(row["labels"]["C_e"] for row in primary_rows)
    predicate_counts = Counter(row["candidate_predicate_label"] for row in candidate_rows)
    primary_predicate_counts = Counter(row["candidate_predicate_label"] for row in primary_rows)
    model_input_hits = blocked_model_input_hits(model_safe_main_rows)
    cap_rows = cap_audit_rows(group_rows)
    quota_rows = quota_audit_rows(candidate_rows, group_rows)
    group_integrity_errors: list[dict[str, Any]] = []
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_group[row["group_id"]].append(row)
    for group in group_rows:
        rows = by_group[group["group_id"]]
        expected_predicates = set(AXIS_SPECS[group["axis_pair"]]["predicates"])
        predicates = {row["candidate_predicate_label"] for row in rows}
        g_hashes = {row["geometry_hash"] for row in rows}
        if len(rows) != 2 or predicates != expected_predicates or len(g_hashes) != 1:
            group_integrity_errors.append(
                {
                    "group_id": group["group_id"],
                    "rows": len(rows),
                    "predicates": sorted(predicates),
                    "expected_predicates": sorted(expected_predicates),
                    "g_hashes": sorted(g_hashes),
                }
            )
    paired_geometry_control_groups = 0
    diagnostic_c_label_errors = 0
    for group in primary_groups:
        rows = by_group[group["group_id"]]
        if len({row["geometry_hash"] for row in rows}) == 1 and {row["labels"]["C_e"] for row in rows} == {0, 1}:
            paired_geometry_control_groups += 1
    for row in candidate_rows:
        if row["subset"] != "primary_compatibility" and row["labels"].get("C_e") is not None:
            diagnostic_c_label_errors += 1
    return {
        "dataset_name": DATASET_NAME,
        "candidate_rows": len(candidate_rows),
        "model_safe_main_rows": len(model_safe_main_rows),
        "model_safe_qe_rows": len(model_safe_qe_rows),
        "group_rows": len(group_rows),
        "subset_counts": dict(subset_counts),
        "component_counts": dict(component_counts),
        "primary_label_counts": {str(key): value for key, value in label_counts.items()},
        "candidate_predicate_counts": dict(predicate_counts),
        "primary_predicate_counts": dict(primary_predicate_counts),
        "blocked_model_input_hits": len(model_input_hits),
        "blocked_model_input_hit_preview": model_input_hits[:10],
        "group_integrity_errors": len(group_integrity_errors),
        "group_integrity_error_preview": group_integrity_errors[:10],
        "paired_geometry_control_groups": paired_geometry_control_groups,
        "diagnostic_c_label_errors": diagnostic_c_label_errors,
        "cap_audit": cap_rows,
        "quota_audit": quota_rows,
        "selection_profile": selection_profile,
    }


def validation_from_precheck(precheck: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_counts = {
        "primary_compatibility": PRIMARY_GROUPS_TOTAL * 2,
        "diagnostic_axis_boundary": BOUNDARY_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS) * 2,
        "diagnostic_frame_disagreement": OPPOSING_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS) * 2,
    }
    for subset, expected in expected_counts.items():
        actual = precheck["subset_counts"].get(subset, 0)
        if actual != expected:
            errors.append({"error_type": "unexpected_subset_count", "subset": subset, "actual": actual, "expected": expected})
    expected_quota = {
        "primary_groups": PRIMARY_GROUPS_TOTAL,
        "primary_rows": PRIMARY_GROUPS_TOTAL * 2,
        "primary_positive_rows": PRIMARY_GROUPS_TOTAL,
        "primary_negative_rows": PRIMARY_GROUPS_TOTAL,
        "left_right_groups": PRIMARY_GROUPS_PER_AXIS_PAIR,
        "front_behind_groups": PRIMARY_GROUPS_PER_AXIS_PAIR,
        "left_rows": PRIMARY_GROUPS_PER_AXIS_PAIR,
        "right_rows": PRIMARY_GROUPS_PER_AXIS_PAIR,
        "front_rows": PRIMARY_GROUPS_PER_AXIS_PAIR,
        "behind_rows": PRIMARY_GROUPS_PER_AXIS_PAIR,
        "positive_left_rows": PRIMARY_GROUPS_PER_POSITIVE_PREDICATE,
        "positive_right_rows": PRIMARY_GROUPS_PER_POSITIVE_PREDICATE,
        "positive_front_rows": PRIMARY_GROUPS_PER_POSITIVE_PREDICATE,
        "positive_behind_rows": PRIMARY_GROUPS_PER_POSITIVE_PREDICATE,
    }
    quota = {row["metric"]: row["actual"] for row in precheck["quota_audit"]}
    for metric, expected in expected_quota.items():
        if quota.get(metric) != expected:
            errors.append({"error_type": "quota_mismatch", "metric": metric, "actual": quota.get(metric), "expected": expected})
    if precheck["blocked_model_input_hits"] != 0:
        errors.append({"error_type": "blocked_model_input_hits", "hits": precheck["blocked_model_input_hits"]})
    if precheck["group_integrity_errors"] != 0:
        errors.append({"error_type": "group_integrity_errors", "errors": precheck["group_integrity_errors"]})
    if precheck["paired_geometry_control_groups"] != PRIMARY_GROUPS_TOTAL:
        errors.append(
            {
                "error_type": "paired_geometry_control_group_count_mismatch",
                "actual": precheck["paired_geometry_control_groups"],
                "expected": PRIMARY_GROUPS_TOTAL,
            }
        )
    if precheck["diagnostic_c_label_errors"] != 0:
        errors.append({"error_type": "diagnostic_rows_have_binary_c_labels", "actual": precheck["diagnostic_c_label_errors"]})
    for row in precheck["cap_audit"]:
        if row["pass"] is not True:
            errors.append({"error_type": "cap_audit_failed", **row})
    return errors


def build_report(summary: dict[str, Any], precheck: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# H002 Relative-Horizontal Candidate Materialization After Plan",
            "",
            "## Result",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"next_todo = {summary['next_todo']}",
            f"validation_errors = {summary['validation_errors']}",
            "```",
            "",
            "## Counts",
            "",
            "```text",
            f"candidate_rows = {precheck['candidate_rows']}",
            f"model_safe_main_rows = {precheck['model_safe_main_rows']}",
            f"model_safe_qe_rows = {precheck['model_safe_qe_rows']}",
            f"group_rows = {precheck['group_rows']}",
            f"subset_counts = {precheck['subset_counts']}",
            f"primary_label_counts = {precheck['primary_label_counts']}",
            f"primary_predicate_counts = {precheck['primary_predicate_counts']}",
            "```",
            "",
            "## Interpretation",
            "",
            "- Primary rows are same-`G_e_horizontal` predicate-flip pairs for `left/right` and `front/behind`.",
            "- Each main group contains two candidate predicates over identical continuous horizontal geometry.",
            "- Positive labels are balanced by predicate, so predicate-only should not solve the target.",
            "- Axis-boundary and frame-disagreement rows are emitted as `Q_e`/diagnostic rows only.",
            "- No learned smoke was run in this stage; next step is schema/shortcut audit.",
            "",
            "## Boundary",
            "",
            "- Train-only materialization.",
            "- No validation/test source used.",
            "- No H001 artifacts modified.",
            "- Not paper-level evidence.",
        ]
    ) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary_path = args.plan_dir / "summary.json"
    source_summary_path = args.source_inventory_dir / "summary.json"
    contract_path = args.plan_dir / "materialization_contract.json"
    selected_axis_path = args.source_inventory_dir / "selected_axis_candidates.csv"

    plan_summary = read_json(plan_summary_path) if plan_summary_path.exists() else {}
    source_summary = read_json(source_summary_path) if source_summary_path.exists() else {}
    contract = read_json(contract_path) if contract_path.exists() else {}
    selected_axis_rows = read_csv(selected_axis_path)
    validation_errors = validate_inputs(
        plan_summary,
        read_jsonl(args.plan_dir / "validation_errors.jsonl"),
        source_summary,
        read_jsonl(args.source_inventory_dir / "validation_errors.jsonl"),
        contract,
        selected_axis_rows,
        args,
    )

    candidate_rows: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    selection_profile: dict[str, Any] = {}

    if not validation_errors:
        source_module = load_source_inventory_module()
        anchors, source_stats = source_module.collect_anchors(SourceArgs(args.train_relationships, args.scan_root))
        primary_anchors, primary_profile = select_primary_groups(anchors)
        excluded = {(axis_pair, str(anchor.get("directed_pair_key"))) for anchor, axis_pair in primary_anchors}
        boundary_anchors, boundary_profile = select_diagnostic_groups(
            anchors,
            "axis_boundary_qe_diagnostic",
            BOUNDARY_GROUPS_PER_AXIS_PAIR,
            excluded,
        )
        opposing_anchors, opposing_profile = select_diagnostic_groups(
            anchors,
            "opposing_frame_diagnostic",
            OPPOSING_GROUPS_PER_AXIS_PAIR,
            excluded,
        )
        selection_profile = {
            "source_stats": source_stats,
            "primary": primary_profile,
            "axis_boundary": boundary_profile,
            "opposing_frame": opposing_profile,
        }

        group_index = 0
        for anchor, axis_pair in primary_anchors:
            rows, group = build_rows_for_group(anchor, axis_pair, "primary_same_g_compatibility", group_index)
            candidate_rows.extend(rows)
            group_rows.append(group)
            group_index += 1
        for anchor, axis_pair in boundary_anchors:
            rows, group = build_rows_for_group(anchor, axis_pair, "axis_boundary_qe_diagnostic", group_index)
            candidate_rows.extend(rows)
            group_rows.append(group)
            group_index += 1
        for anchor, axis_pair in opposing_anchors:
            rows, group = build_rows_for_group(anchor, axis_pair, "opposing_frame_diagnostic", group_index)
            candidate_rows.extend(rows)
            group_rows.append(group)
            group_index += 1

    model_safe_main_rows = [row for row in (model_safe_main_row(row) for row in candidate_rows) if row is not None]
    model_safe_qe_rows = [model_safe_qe_row(row) for row in candidate_rows]
    hidden_rows = [build_hidden_manifest(row) for row in candidate_rows]
    precheck = schema_precheck(candidate_rows, model_safe_main_rows, model_safe_qe_rows, group_rows, selection_profile)
    validation_errors.extend(validation_from_precheck(precheck))

    status = STATUS_ERROR if validation_errors else STATUS_READY
    selected_path = "blocked_by_validation_errors" if validation_errors else SELECTED_READY
    next_todo = EXPECTED_PLAN_NEXT if validation_errors else NEXT_TODO

    output_paths = {
        "candidate_rows": args.output_dir / "candidate_rows.jsonl",
        "model_safe_main_view": args.output_dir / "model_safe_main_view.jsonl",
        "model_safe_qe_view": args.output_dir / "model_safe_qe_view.jsonl",
        "hidden_manifest": args.output_dir / "hidden_manifest.jsonl",
        "group_manifest": args.output_dir / "group_manifest.jsonl",
        "schema_precheck": args.output_dir / "schema_precheck.json",
        "cap_audit": args.output_dir / "cap_audit.csv",
        "quota_audit": args.output_dir / "quota_audit.csv",
        "selection_profile": args.output_dir / "selection_profile.json",
        "manifest": args.output_dir / "manifest.json",
        "report": args.output_dir / "report.md",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "plan_dir": rel_path(args.plan_dir),
            "source_inventory_dir": rel_path(args.source_inventory_dir),
            "train_relationships": rel_path(args.train_relationships),
            "scan_root": rel_path(args.scan_root),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "boundary": {
            "split": "train_only_candidate_materialization",
            "materializes_rows": True,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "counts": {
            "candidate_rows": len(candidate_rows),
            "model_safe_main_rows": len(model_safe_main_rows),
            "model_safe_qe_rows": len(model_safe_qe_rows),
            "hidden_rows": len(hidden_rows),
            "group_rows": len(group_rows),
            "primary_groups": precheck["subset_counts"].get("primary_compatibility", 0) // 2,
            "primary_rows": precheck["subset_counts"].get("primary_compatibility", 0),
            "axis_boundary_diagnostic_rows": precheck["subset_counts"].get("diagnostic_axis_boundary", 0),
            "frame_disagreement_diagnostic_rows": precheck["subset_counts"].get("diagnostic_frame_disagreement", 0),
        },
        "label_counts": precheck["primary_label_counts"],
        "predicate_counts": precheck["primary_predicate_counts"],
        "claim_boundary": {
            "learned_smoke_allowed_now": False,
            "paper_evidence_allowed_now": False,
            "relative_horizontal_solved": False,
            "frame_alignment_claim_allowed": False,
            "schema_shortcut_audit_required_next": True,
        },
    }

    manifest = {
        "dataset_name": DATASET_NAME,
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": summary["created_at_utc"],
        "files": {key: rel_path(path) for key, path in output_paths.items()},
        "upstream": {
            "plan_summary": rel_path(plan_summary_path),
            "source_summary": rel_path(source_summary_path),
        },
    }

    write_jsonl(output_paths["candidate_rows"], candidate_rows)
    write_jsonl(output_paths["model_safe_main_view"], model_safe_main_rows)
    write_jsonl(output_paths["model_safe_qe_view"], model_safe_qe_rows)
    write_jsonl(output_paths["hidden_manifest"], hidden_rows)
    write_jsonl(output_paths["group_manifest"], group_rows)
    write_json(output_paths["schema_precheck"], precheck)
    write_csv(output_paths["cap_audit"], precheck["cap_audit"])
    write_csv(output_paths["quota_audit"], precheck["quota_audit"])
    write_json(output_paths["selection_profile"], selection_profile)
    write_json(output_paths["manifest"], manifest)
    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(build_report(summary, precheck), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
