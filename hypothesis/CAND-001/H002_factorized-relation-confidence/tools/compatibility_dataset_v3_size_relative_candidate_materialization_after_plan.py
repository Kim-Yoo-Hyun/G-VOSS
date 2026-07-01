#!/usr/bin/env python3
"""Materialize H002 size-relative same-G predicate-flip candidates."""

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
    H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory"
)
DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan"
)
DEFAULT_TRAIN_RELATIONSHIPS = REPO_ROOT / "local_dataset/3DSSG_subset/relationships_train.json"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_after_plan"
SOURCE_INVENTORY_TOOL = H2_ROOT / "tools/compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan.py"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_size_relative_candidate_materialization_after_plan"
EXPECTED_SOURCE_STATUS = "h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_size_relative_candidate_materialization_after_plan_v1"
MODEL_SAFE_MAIN_SCHEMA = "h002_size_relative_model_safe_main_view_v1"
MODEL_SAFE_QE_SCHEMA = "h002_size_relative_model_safe_qe_view_v1"
HIDDEN_SCHEMA = "h002_size_relative_hidden_manifest_v1"
GROUP_SCHEMA = "h002_size_relative_group_manifest_v1"
DATASET_NAME = "h002_size_relative_same_g_predicate_flip_v1"

STATUS_READY = "h002_compatibility_dataset_v3_size_relative_candidate_materialization_after_plan_ready_for_schema_shortcut_audit"
STATUS_ERROR = "h002_compatibility_dataset_v3_size_relative_candidate_materialization_after_plan_input_errors"
NEXT_TODO = "compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization"

SIZE_PREDICATES = ("bigger than", "smaller than")
PRIMARY_GROUPS_TOTAL = 1200
PRIMARY_GROUPS_PER_DIRECTION = 600
AMBIGUOUS_GROUPS_TOTAL = 50
GT_CONFLICT_GROUPS_TOTAL = 36
CLASS_PAIR_GROUP_CAP = 240
CLASS_PAIR_DIRECTION_CAP = 120
SCAN_GROUP_CAP = 24

PRIMARY_BANDS = {"medium_1.25_1.50", "strong_ge_1.50"}
BLOCKED_MODEL_INPUT_KEYS = {
    "anchor_predicate_label",
    "candidate_component",
    "class_pair",
    "compatibility_label",
    "direction_by_volume",
    "direction_by_vote",
    "directed_pair_predicate_key",
    "gt_compatible_by_volume",
    "gt_compatible_by_vote",
    "gt_predicate_label",
    "is_original_gt_anchor",
    "object_class_label",
    "object_id",
    "p_obs_label",
    "p_rel_label",
    "scan_id",
    "source_predicate_label",
    "subgraph_anchor_key",
    "subject_class_label",
    "subject_id",
    "volume_ratio_band",
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


def load_source_inventory_module() -> Any:
    spec = importlib.util.spec_from_file_location("h002_size_source_inventory", SOURCE_INVENTORY_TOOL)
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
    quota = contract.get("quota", {})
    if int(quota.get("subject_bigger_groups", 0)) != PRIMARY_GROUPS_PER_DIRECTION:
        errors.append({"error_type": "unexpected_subject_bigger_quota", "actual": quota.get("subject_bigger_groups")})
    if int(quota.get("subject_smaller_groups", 0)) != PRIMARY_GROUPS_PER_DIRECTION:
        errors.append({"error_type": "unexpected_subject_smaller_quota", "actual": quota.get("subject_smaller_groups")})
    if not args.train_relationships.exists():
        errors.append({"error_type": "missing_train_relationships", "path": rel_path(args.train_relationships)})
    if not args.scan_root.exists():
        errors.append({"error_type": "missing_scan_root", "path": rel_path(args.scan_root)})
    return errors


def finite_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def g_features(anchor: dict[str, Any]) -> dict[str, float | None]:
    return {
        "log_volume_ratio_s_over_o": finite_float(anchor.get("log_volume_ratio_s_over_o")),
        "log_max_extent_ratio_s_over_o": finite_float(anchor.get("log_max_extent_ratio_s_over_o")),
        "log_footprint_area_ratio_s_over_o": finite_float(anchor.get("log_footprint_area_ratio_s_over_o")),
        "log_vertical_extent_ratio_s_over_o": finite_float(anchor.get("log_vertical_extent_ratio_s_over_o")),
    }


def g_hash(anchor: dict[str, Any]) -> str:
    features = g_features(anchor)
    rounded = {key: None if value is None else round(value, 10) for key, value in features.items()}
    return stable_hash(rounded)


def primary_label(candidate_predicate: str, direction: str) -> int:
    if direction == "subject_bigger":
        return 1 if candidate_predicate == "bigger than" else 0
    if direction == "subject_smaller":
        return 1 if candidate_predicate == "smaller than" else 0
    raise ValueError(f"unsupported primary direction: {direction}")


def candidate_label_state(component: str, candidate_predicate: str, anchor: dict[str, Any]) -> dict[str, Any]:
    if component == "primary_same_g_compatibility":
        label = primary_label(candidate_predicate, anchor["direction_by_volume"])
        return {
            "C_e": label,
            "p_rel": "accept" if label == 1 else "reject",
            "p_obs": "observable",
            "target_source": "gt_anchor_same_g_predicate_flip",
        }
    if component == "ambiguous_size_qe_diagnostic":
        return {
            "C_e": None,
            "p_rel": "abstain",
            "p_obs": "ambiguous_size",
            "target_source": "diagnostic_ambiguous_size_margin",
        }
    return {
        "C_e": None,
        "p_rel": "audit",
        "p_obs": "needs_gt_geometry_conflict_audit",
        "target_source": "diagnostic_gt_geometry_conflict",
    }


def q_features(anchor: dict[str, Any], component: str) -> dict[str, Any]:
    log_volume = finite_float(anchor.get("log_volume_ratio_s_over_o"))
    return {
        "abs_log_volume_ratio": abs(log_volume) if log_volume is not None else None,
        "pair_obb_available": anchor.get("pair_obb_status") == "both_obb",
        "evidence_axis": "semseg_obb_size_ratio",
        "size_observability_state": {
            "primary_same_g_compatibility": "sufficient",
            "ambiguous_size_qe_diagnostic": "ambiguous_margin",
            "gt_geometry_conflict_audit": "source_geometry_conflict",
        }[component],
    }


def full_feature_blocks(anchor: dict[str, Any], candidate_predicate: str, component: str) -> dict[str, Any]:
    return {
        "T_e": {
            "predicate_text": candidate_predicate,
            "predicate_label": candidate_predicate,
            "predicate_family": "size_relative",
            "relation_family": "size_relative",
        },
        "G_e_size": g_features(anchor),
        "Q_e_size": q_features(anchor, component),
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
            "T_e": {
                "predicate_text": row["candidate_predicate_label"],
                "predicate_label": row["candidate_predicate_label"],
                "relation_family": "size_relative",
            },
            "G_e_size": row["feature_blocks"]["G_e_size"],
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
        "feature_blocks": {"Q_e_size": row["feature_blocks"]["Q_e_size"]},
        "labels": {
            "p_obs": row["labels"]["p_obs"],
            "target_source": row["labels"]["target_source"],
        },
        "model_use": "q_e_or_abstain_diagnostic_after_schema_audit",
    }


def build_rows_for_group(anchor: dict[str, Any], component: str, group_index: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    subset = {
        "primary_same_g_compatibility": "primary_compatibility",
        "ambiguous_size_qe_diagnostic": "diagnostic_ambiguous_size",
        "gt_geometry_conflict_audit": "audit_gt_geometry_conflict",
    }[component]
    direction = anchor.get("direction_by_volume")
    group_id = "h002_size_group_" + stable_hash(
        {
            "component": component,
            "scan": anchor.get("scan_id"),
            "subgraph": anchor.get("subgraph_id"),
            "subject": anchor.get("subject_id"),
            "object": anchor.get("object_id"),
            "source_predicate": anchor.get("predicate_label"),
            "group_index": group_index,
        }
    )
    geometry_hash = g_hash(anchor)
    rows: list[dict[str, Any]] = []
    for candidate_predicate in SIZE_PREDICATES:
        row_id = "h002_size_row_" + stable_hash({"group_id": group_id, "predicate": candidate_predicate})
        labels = candidate_label_state(component, candidate_predicate, anchor)
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
                "candidate_predicate_label": candidate_predicate,
                "candidate_predicate_text": candidate_predicate,
                "relation_family": "size_relative",
                "source_predicate_label": anchor.get("predicate_label"),
                "anchor_predicate_label": anchor.get("predicate_label"),
                "is_original_gt_anchor": candidate_predicate == anchor.get("predicate_label"),
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
                "geometry_hash": geometry_hash,
                "direction_by_volume": direction,
                "direction_by_vote": anchor.get("direction_by_vote"),
                "gt_compatible_by_volume": anchor.get("gt_compatible_by_volume"),
                "gt_compatible_by_vote": anchor.get("gt_compatible_by_vote"),
                "volume_ratio_band": anchor.get("volume_ratio_band"),
                "pair_obb_status": anchor.get("pair_obb_status"),
                "feature_blocks": full_feature_blocks(anchor, candidate_predicate, component),
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
        "scan_id": anchor.get("scan_id"),
        "subgraph_id": anchor.get("subgraph_id"),
        "subject_id": anchor.get("subject_id"),
        "object_id": anchor.get("object_id"),
        "class_pair": anchor.get("class_pair"),
        "source_predicate_label": anchor.get("predicate_label"),
        "direction_by_volume": direction,
        "volume_ratio_band": anchor.get("volume_ratio_band"),
        "gt_compatible_by_volume": anchor.get("gt_compatible_by_volume"),
        "geometry_hash": geometry_hash,
        "row_ids": [row["row_id"] for row in rows],
        "candidate_predicates": list(SIZE_PREDICATES),
        "primary_positive_predicate": None
        if component != "primary_same_g_compatibility"
        else ("bigger than" if direction == "subject_bigger" else "smaller than"),
    }
    return rows, group


def select_primary_groups(anchors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    strict = [
        anchor
        for anchor in anchors
        if anchor.get("pair_obb_status") == "both_obb"
        and anchor.get("gt_compatible_by_volume") == "compatible"
        and anchor.get("volume_ratio_band") in PRIMARY_BANDS
        and anchor.get("direction_by_volume") in {"subject_bigger", "subject_smaller"}
    ]
    buckets: dict[tuple[str, str], deque[dict[str, Any]]] = defaultdict(deque)
    class_pairs: set[str] = set()
    for anchor in strict:
        class_pair = str(anchor.get("class_pair"))
        direction = str(anchor.get("direction_by_volume"))
        class_pairs.add(class_pair)
        buckets[(direction, class_pair)].append(anchor)
    for key, values in buckets.items():
        ordered = sorted(
            values,
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
        buckets[key] = deque(ordered)
    class_order = sorted(
        class_pairs,
        key=lambda class_pair: (
            -sum(len(buckets[(direction, class_pair)]) for direction in ["subject_bigger", "subject_smaller"]),
            class_pair,
        ),
    )
    selected: list[dict[str, Any]] = []
    direction_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    class_direction_counts: Counter[tuple[str, str]] = Counter()
    scan_counts: Counter[str] = Counter()
    skipped: Counter[str] = Counter()

    progress = True
    while progress and (
        direction_counts["subject_bigger"] < PRIMARY_GROUPS_PER_DIRECTION
        or direction_counts["subject_smaller"] < PRIMARY_GROUPS_PER_DIRECTION
    ):
        progress = False
        for class_pair in class_order:
            for direction in ["subject_bigger", "subject_smaller"]:
                if direction_counts[direction] >= PRIMARY_GROUPS_PER_DIRECTION:
                    continue
                if class_counts[class_pair] >= CLASS_PAIR_GROUP_CAP:
                    continue
                if class_direction_counts[(class_pair, direction)] >= CLASS_PAIR_DIRECTION_CAP:
                    continue
                bucket = buckets[(direction, class_pair)]
                while bucket:
                    anchor = bucket.popleft()
                    scan_id = str(anchor.get("scan_id"))
                    if scan_counts[scan_id] >= SCAN_GROUP_CAP:
                        skipped["scan_cap"] += 1
                        continue
                    selected.append(anchor)
                    direction_counts[direction] += 1
                    class_counts[class_pair] += 1
                    class_direction_counts[(class_pair, direction)] += 1
                    scan_counts[scan_id] += 1
                    progress = True
                    break
    profile = {
        "strict_candidates": len(strict),
        "selected_primary_groups": len(selected),
        "direction_counts": dict(direction_counts),
        "class_pair_max_groups": max(class_counts.values(), default=0),
        "class_pair_direction_max_groups": max(class_direction_counts.values(), default=0),
        "scan_max_groups": max(scan_counts.values(), default=0),
        "skipped": dict(skipped),
        "selected_class_pairs": len(class_counts),
        "selected_scans": len(scan_counts),
    }
    return selected, profile


def select_diagnostic_groups(anchors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ambiguous = [
        anchor
        for anchor in anchors
        if anchor.get("pair_obb_status") == "both_obb" and anchor.get("gt_compatible_by_volume") == "ambiguous"
    ]
    conflicts = [
        anchor
        for anchor in anchors
        if anchor.get("pair_obb_status") == "both_obb" and anchor.get("gt_compatible_by_volume") == "opposes"
    ]
    sort_key = lambda row: stable_hash(
        {
            "scan": row.get("scan_id"),
            "subgraph": row.get("subgraph_id"),
            "subject": row.get("subject_id"),
            "object": row.get("object_id"),
            "predicate": row.get("predicate_label"),
        }
    )
    return sorted(ambiguous, key=sort_key)[:AMBIGUOUS_GROUPS_TOTAL], sorted(conflicts, key=sort_key)[
        :GT_CONFLICT_GROUPS_TOTAL
    ]


def build_hidden_manifest(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": HIDDEN_SCHEMA,
        "dataset_name": DATASET_NAME,
        "row_id": row["row_id"],
        "group_id": row["group_id"],
        "split": row["split"],
        "subset": row["subset"],
        "candidate_component": row["candidate_component"],
        "candidate_predicate_label": row["candidate_predicate_label"],
        "source_predicate_label": row["source_predicate_label"],
        "anchor_predicate_label": row["anchor_predicate_label"],
        "is_original_gt_anchor": row["is_original_gt_anchor"],
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
        "direction_by_volume": row["direction_by_volume"],
        "direction_by_vote": row["direction_by_vote"],
        "gt_compatible_by_volume": row["gt_compatible_by_volume"],
        "gt_compatible_by_vote": row["gt_compatible_by_vote"],
        "volume_ratio_band": row["volume_ratio_band"],
        "pair_obb_status": row["pair_obb_status"],
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
    class_direction_counts = Counter((group["class_pair"], group["direction_by_volume"]) for group in primary)
    scan_counts = Counter(group["scan_id"] for group in primary)
    return [
        {
            "cap_name": "max_groups_per_class_pair",
            "limit": CLASS_PAIR_GROUP_CAP,
            "observed_max": max(class_counts.values(), default=0),
            "pass": max(class_counts.values(), default=0) <= CLASS_PAIR_GROUP_CAP,
        },
        {
            "cap_name": "max_groups_per_class_pair_direction",
            "limit": CLASS_PAIR_DIRECTION_CAP,
            "observed_max": max(class_direction_counts.values(), default=0),
            "pass": max(class_direction_counts.values(), default=0) <= CLASS_PAIR_DIRECTION_CAP,
        },
        {
            "cap_name": "max_groups_per_scan",
            "limit": SCAN_GROUP_CAP,
            "observed_max": max(scan_counts.values(), default=0),
            "pass": max(scan_counts.values(), default=0) <= SCAN_GROUP_CAP,
        },
    ]


def quota_audit_rows(candidate_rows: list[dict[str, Any]], group_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary_rows = [row for row in candidate_rows if row["subset"] == "primary_compatibility"]
    primary_groups = [group for group in group_rows if group["subset"] == "primary_compatibility"]
    labels = Counter(row["labels"]["C_e"] for row in primary_rows)
    predicates = Counter(row["candidate_predicate_label"] for row in primary_rows)
    directions = Counter(group["direction_by_volume"] for group in primary_groups)
    return [
        {"metric": "primary_groups", "expected": PRIMARY_GROUPS_TOTAL, "actual": len(primary_groups)},
        {"metric": "primary_rows", "expected": PRIMARY_GROUPS_TOTAL * 2, "actual": len(primary_rows)},
        {"metric": "primary_positive_rows", "expected": PRIMARY_GROUPS_TOTAL, "actual": labels[1]},
        {"metric": "primary_negative_rows", "expected": PRIMARY_GROUPS_TOTAL, "actual": labels[0]},
        {"metric": "subject_bigger_groups", "expected": PRIMARY_GROUPS_PER_DIRECTION, "actual": directions["subject_bigger"]},
        {"metric": "subject_smaller_groups", "expected": PRIMARY_GROUPS_PER_DIRECTION, "actual": directions["subject_smaller"]},
        {"metric": "bigger_than_rows", "expected": PRIMARY_GROUPS_TOTAL, "actual": predicates["bigger than"]},
        {"metric": "smaller_than_rows", "expected": PRIMARY_GROUPS_TOTAL, "actual": predicates["smaller than"]},
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
    model_input_hits = blocked_model_input_hits(model_safe_main_rows)
    cap_rows = cap_audit_rows(group_rows)
    quota_rows = quota_audit_rows(candidate_rows, group_rows)
    group_integrity_errors: list[dict[str, Any]] = []
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_group[row["group_id"]].append(row)
    for group_id, rows in by_group.items():
        predicates = {row["candidate_predicate_label"] for row in rows}
        g_hashes = {row["geometry_hash"] for row in rows}
        if len(rows) != 2 or predicates != set(SIZE_PREDICATES) or len(g_hashes) != 1:
            group_integrity_errors.append(
                {
                    "group_id": group_id,
                    "rows": len(rows),
                    "predicates": sorted(predicates),
                    "g_hashes": sorted(g_hashes),
                }
            )
    paired_geometry_control_groups = 0
    for group in primary_groups:
        rows = by_group[group["group_id"]]
        if len({row["geometry_hash"] for row in rows}) == 1 and {row["labels"]["C_e"] for row in rows} == {0, 1}:
            paired_geometry_control_groups += 1
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
        "blocked_model_input_hits": len(model_input_hits),
        "blocked_model_input_hit_preview": model_input_hits[:10],
        "group_integrity_errors": len(group_integrity_errors),
        "group_integrity_error_preview": group_integrity_errors[:10],
        "paired_geometry_control_groups": paired_geometry_control_groups,
        "cap_audit": cap_rows,
        "quota_audit": quota_rows,
        "selection_profile": selection_profile,
    }


def validation_from_precheck(precheck: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_counts = {
        "primary_compatibility": PRIMARY_GROUPS_TOTAL * 2,
        "diagnostic_ambiguous_size": AMBIGUOUS_GROUPS_TOTAL * 2,
        "audit_gt_geometry_conflict": GT_CONFLICT_GROUPS_TOTAL * 2,
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
        "subject_bigger_groups": PRIMARY_GROUPS_PER_DIRECTION,
        "subject_smaller_groups": PRIMARY_GROUPS_PER_DIRECTION,
        "bigger_than_rows": PRIMARY_GROUPS_TOTAL,
        "smaller_than_rows": PRIMARY_GROUPS_TOTAL,
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
    for row in precheck["cap_audit"]:
        if row["pass"] is not True:
            errors.append({"error_type": "cap_audit_failed", **row})
    return errors


def build_report(summary: dict[str, Any], precheck: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# H002 Size-Relative Candidate Materialization After Plan",
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
            "```",
            "",
            "## Interpretation",
            "",
            "- Primary rows are same-G predicate-flip pairs: each group contains `bigger than` and `smaller than` over identical `G_e_size`.",
            "- The main model-safe feature blocks contain predicate text and continuous size-ratio geometry only.",
            "- Class/source/GT/construction/discretized direction fields are hidden for audit/control use.",
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
    plan_errors_path = args.plan_dir / "validation_errors.jsonl"
    source_summary_path = args.source_inventory_dir / "summary.json"
    source_errors_path = args.source_inventory_dir / "validation_errors.jsonl"
    contract_path = args.plan_dir / "materialization_contract.json"

    plan_summary = read_json(plan_summary_path) if plan_summary_path.exists() else {}
    source_summary = read_json(source_summary_path) if source_summary_path.exists() else {}
    contract = read_json(contract_path) if contract_path.exists() else {}
    validation_errors = validate_inputs(
        plan_summary,
        read_jsonl(plan_errors_path),
        source_summary,
        read_jsonl(source_errors_path),
        contract,
        args,
    )

    candidate_rows: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    selection_profile: dict[str, Any] = {}

    if not validation_errors:
        source_module = load_source_inventory_module()
        anchors, source_stats = source_module.collect_anchors(SourceArgs(args.train_relationships, args.scan_root))
        primary_anchors, selection_profile = select_primary_groups(anchors)
        ambiguous_anchors, conflict_anchors = select_diagnostic_groups(anchors)
        selection_profile["source_stats"] = source_stats
        for index, anchor in enumerate(primary_anchors):
            rows, group = build_rows_for_group(anchor, "primary_same_g_compatibility", index)
            candidate_rows.extend(rows)
            group_rows.append(group)
        offset = len(group_rows)
        for index, anchor in enumerate(ambiguous_anchors, start=offset):
            rows, group = build_rows_for_group(anchor, "ambiguous_size_qe_diagnostic", index)
            candidate_rows.extend(rows)
            group_rows.append(group)
        offset = len(group_rows)
        for index, anchor in enumerate(conflict_anchors, start=offset):
            rows, group = build_rows_for_group(anchor, "gt_geometry_conflict_audit", index)
            candidate_rows.extend(rows)
            group_rows.append(group)

    model_safe_main_rows = [row for row in (model_safe_main_row(row) for row in candidate_rows) if row is not None]
    model_safe_qe_rows = [model_safe_qe_row(row) for row in candidate_rows]
    hidden_rows = [build_hidden_manifest(row) for row in candidate_rows]
    precheck = schema_precheck(candidate_rows, model_safe_main_rows, model_safe_qe_rows, group_rows, selection_profile)
    validation_errors.extend(validation_from_precheck(precheck))

    status = STATUS_ERROR if validation_errors else STATUS_READY
    selected_path = "blocked_by_validation_errors" if validation_errors else "size_relative_same_g_candidates_ready_for_schema_shortcut_audit"
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
            "ambiguous_diagnostic_rows": precheck["subset_counts"].get("diagnostic_ambiguous_size", 0),
            "gt_geometry_conflict_audit_rows": precheck["subset_counts"].get("audit_gt_geometry_conflict", 0),
        },
        "label_counts": precheck["primary_label_counts"],
        "predicate_counts": precheck["candidate_predicate_counts"],
        "claim_boundary": {
            "learned_smoke_allowed_now": False,
            "paper_evidence_allowed_now": False,
            "size_relative_solved": False,
            "geometry_only_success_counts_as_main_claim": False,
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
