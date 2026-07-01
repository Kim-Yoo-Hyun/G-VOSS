#!/usr/bin/env python3
"""Materialize planned train-only close-by candidate rows for H002."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan"
DEFAULT_TRAIN_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_proximity_close_by_candidate_materialization"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_v1"
MODEL_SAFE_SCHEMA = "h002_close_by_model_safe_view_v1"
HIDDEN_SCHEMA = "h002_close_by_hidden_manifest_v1"
STATUS_READY = "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_ready_for_schema_shortcut_audit"
STATUS_ERROR = "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_input_errors"
NEXT_TODO = "compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit"

NEAR_NORM_XY = 0.80
FAR_NORM_XY = 2.50
RAW_DISTANCE_BIN_WIDTH = 0.50
NORM_DISTANCE_BIN_WIDTH = 0.25

PRIMARY_ACCEPT_QUOTA = 400
PRIMARY_REJECT_QUOTA = 400
ABSTAIN_NEAR_NONGT_QUOTA = 120
ABSTAIN_AMBIGUOUS_QUOTA = 80
ABSTAIN_UNCERTAIN_QUOTA = 40
RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA = 120
RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA = 120
GT_CONFLICT_AUDIT_QUOTA = 4

MAX_ROWS_PER_SCAN = 18
MAX_ROWS_PER_CLASS_PAIR = 48
MAX_ROWS_PER_CLASS_PAIR_RANK = 24
MAX_ROWS_PER_DIRECTED_PAIR = 2
MAX_ROWS_PER_RAW_DISTANCE_BIN = 80

G_E_FIELDS = [
    "distance_3d",
    "distance_xy",
    "normalized_distance_3d",
    "normalized_distance_xy",
    "projected_iou_xy",
    "projected_subject_overlap_ratio",
    "projected_object_overlap_ratio",
    "center_delta_z",
    "normalized_center_delta_z",
    "subject_top_z",
    "subject_bottom_z",
    "object_top_z",
    "object_bottom_z",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--train-rga-dir", type=Path, default=DEFAULT_TRAIN_RGA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
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


def stable_hash(value: Any, length: int = 16) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def nested_get(row: dict[str, Any], *keys: str) -> Any:
    value: Any = row
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def predicate_label(row: dict[str, Any]) -> str | None:
    predicate = row.get("predicate")
    if isinstance(predicate, dict):
        return predicate.get("predicate_label")
    return row.get("predicate_label")


def distance_bucket(norm_xy: float | None) -> str:
    if norm_xy is None:
        return "missing"
    if norm_xy <= NEAR_NORM_XY:
        return "near"
    if norm_xy >= FAR_NORM_XY:
        return "far"
    return "ambiguous"


def metric_bin(value: float | None, width: float) -> str:
    if value is None:
        return "missing"
    start = int(value / width) * width
    return f"{start:.2f}-{start + width:.2f}"


def candidate_bucket(label_status: str, geometry_status: str, bucket: str) -> str:
    if label_status == "exact_match" and geometry_status == "satisfied" and bucket == "near":
        return "accept_anchor"
    if label_status == "exact_match" and bucket == "far":
        return "gt_geometry_conflict"
    if label_status != "exact_match" and geometry_status == "unsatisfied" and bucket == "far":
        return "reject_far_geometry"
    if label_status != "exact_match" and geometry_status == "satisfied" and bucket == "near":
        return "near_nonexact_satisfied"
    if geometry_status == "uncertain":
        return "geometry_uncertain"
    if bucket == "ambiguous":
        return "ambiguous_distance"
    return "other"


def class_pair(row: dict[str, Any]) -> str:
    edge = row.get("edge") or {}
    return f"{edge.get('subject_label')}->{edge.get('object_label')}"


def row_to_candidate(row: dict[str, Any]) -> dict[str, Any] | None:
    raw_features = nested_get(row, "geometry", "raw_features") or {}
    if not isinstance(raw_features, dict):
        raw_features = {}
    norm_xy = safe_float(raw_features.get("normalized_distance_xy"))
    raw_xy = safe_float(raw_features.get("distance_xy"))
    bucket = distance_bucket(norm_xy)
    label_status = str(nested_get(row, "label", "label_match_status"))
    geometry_status = str(nested_get(row, "geometry", "geometry_status"))
    cand = candidate_bucket(label_status, geometry_status, bucket)
    if cand == "other":
        return None
    identity = row.get("identity") or {}
    edge = row.get("edge") or {}
    semantic = row.get("semantic") or {}
    source = row.get("source") or {}
    class_pair_key = class_pair(row)
    rank_band = str(nested_get(row, "rga", "rank_band"))
    return {
        "candidate_bucket": cand,
        "row_key": identity.get("row_key"),
        "prediction_id": identity.get("prediction_id"),
        "scan_id": identity.get("scan_id"),
        "subgraph_id": identity.get("subgraph_id"),
        "directed_pair_id": identity.get("directed_pair_id"),
        "subject_id": identity.get("subject_id"),
        "object_id": identity.get("object_id"),
        "subject_class": edge.get("subject_label"),
        "object_class": edge.get("object_label"),
        "class_pair": class_pair_key,
        "rank_band": rank_band,
        "class_pair_rank": f"{class_pair_key}::{rank_band}",
        "label_match_status": label_status,
        "geometry_status": geometry_status,
        "distance_bucket": bucket,
        "raw_distance_bin": metric_bin(raw_xy, RAW_DISTANCE_BIN_WIDTH),
        "norm_distance_bin": metric_bin(norm_xy, NORM_DISTANCE_BIN_WIDTH),
        "semantic": semantic,
        "source": source,
        "geometry": row.get("geometry") or {},
        "raw_features": raw_features,
        "sort_key": stable_hash(identity.get("row_key")),
    }


def validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan.get("status")})
    if plan.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan.get("next_todo")})
    if plan.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan.get("validation_errors")})
    boundary = plan.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "materializes_rows", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def scan_candidates(match_rows_path: Path) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with match_rows_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if predicate_label(row) != "close by":
                continue
            candidate = row_to_candidate(row)
            if candidate is not None:
                buckets[candidate["candidate_bucket"]].append(candidate)
    for rows in buckets.values():
        rows.sort(key=lambda row: row["sort_key"])
    return buckets


def can_select(
    row: dict[str, Any],
    subset: str,
    selected_keys: set[str],
    global_scan_counts: Counter[str],
    global_directed_pair_counts: Counter[str],
    primary_class_pair_counts: Counter[str],
    primary_class_pair_rank_counts: Counter[str],
    raw_diag_bin_counts: Counter[str],
) -> bool:
    if row["row_key"] in selected_keys:
        return False
    if global_scan_counts[row["scan_id"]] >= MAX_ROWS_PER_SCAN:
        return False
    if global_directed_pair_counts[row["directed_pair_id"]] >= MAX_ROWS_PER_DIRECTED_PAIR:
        return False
    if subset == "primary_binary":
        if primary_class_pair_counts[row["class_pair"]] >= MAX_ROWS_PER_CLASS_PAIR:
            return False
        if primary_class_pair_rank_counts[row["class_pair_rank"]] >= MAX_ROWS_PER_CLASS_PAIR_RANK:
            return False
    if subset == "raw_distance_diagnostic" and raw_diag_bin_counts[row["raw_distance_bin"]] >= MAX_ROWS_PER_RAW_DISTANCE_BIN:
        return False
    return True


def record_selection(
    row: dict[str, Any],
    selected_keys: set[str],
    global_scan_counts: Counter[str],
    global_directed_pair_counts: Counter[str],
    primary_class_pair_counts: Counter[str],
    primary_class_pair_rank_counts: Counter[str],
    raw_diag_bin_counts: Counter[str],
    subset: str,
) -> None:
    selected_keys.add(row["row_key"])
    global_scan_counts[row["scan_id"]] += 1
    global_directed_pair_counts[row["directed_pair_id"]] += 1
    if subset == "primary_binary":
        primary_class_pair_counts[row["class_pair"]] += 1
        primary_class_pair_rank_counts[row["class_pair_rank"]] += 1
    if subset == "raw_distance_diagnostic":
        raw_diag_bin_counts[row["raw_distance_bin"]] += 1


def select_raw_distance_diagnostic(
    buckets: dict[str, list[dict[str, Any]]],
    selected_keys: set[str],
    global_scan_counts: Counter[str],
    global_directed_pair_counts: Counter[str],
    primary_class_pair_counts: Counter[str],
    primary_class_pair_rank_counts: Counter[str],
    raw_diag_bin_counts: Counter[str],
) -> list[dict[str, Any]]:
    by_bin: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"accept": [], "reject": []})
    for row in buckets["accept_anchor"]:
        by_bin[row["raw_distance_bin"]]["accept"].append(row)
    for row in buckets["reject_far_geometry"]:
        by_bin[row["raw_distance_bin"]]["reject"].append(row)
    bin_order = sorted(
        [key for key, value in by_bin.items() if value["accept"] and value["reject"]],
        key=lambda key: 2 * min(len(by_bin[key]["accept"]), len(by_bin[key]["reject"])),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    counts = Counter()
    progress = True
    while progress and (counts["accept"] < RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA or counts["reject"] < RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA):
        progress = False
        for raw_bin in bin_order:
            for label_name, quota in [
                ("accept", RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA),
                ("reject", RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA),
            ]:
                if counts[label_name] >= quota:
                    continue
                rows = by_bin[raw_bin][label_name]
                while rows:
                    row = rows.pop(0)
                    if can_select(
                        row,
                        "raw_distance_diagnostic",
                        selected_keys,
                        global_scan_counts,
                        global_directed_pair_counts,
                        primary_class_pair_counts,
                        primary_class_pair_rank_counts,
                        raw_diag_bin_counts,
                    ):
                        record_selection(
                            row,
                            selected_keys,
                            global_scan_counts,
                            global_directed_pair_counts,
                            primary_class_pair_counts,
                            primary_class_pair_rank_counts,
                            raw_diag_bin_counts,
                            "raw_distance_diagnostic",
                        )
                        selected.append({**row, "subset": "raw_distance_diagnostic", "role": f"{label_name}_diagnostic"})
                        counts[label_name] += 1
                        progress = True
                        break
    return selected


def select_primary(
    buckets: dict[str, list[dict[str, Any]]],
    selected_keys: set[str],
    global_scan_counts: Counter[str],
    global_directed_pair_counts: Counter[str],
    primary_class_pair_counts: Counter[str],
    primary_class_pair_rank_counts: Counter[str],
    raw_diag_bin_counts: Counter[str],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"accept": [], "reject": []})
    for row in buckets["accept_anchor"]:
        grouped[row["class_pair_rank"]]["accept"].append(row)
    for row in buckets["reject_far_geometry"]:
        grouped[row["class_pair_rank"]]["reject"].append(row)
    group_order = sorted(
        [key for key, value in grouped.items() if value["accept"] and value["reject"]],
        key=lambda key: 2 * min(len(grouped[key]["accept"]), len(grouped[key]["reject"])),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    counts = Counter()
    progress = True
    while progress and (counts["accept"] < PRIMARY_ACCEPT_QUOTA or counts["reject"] < PRIMARY_REJECT_QUOTA):
        progress = False
        for group_key in group_order:
            for label_name, quota in [("accept", PRIMARY_ACCEPT_QUOTA), ("reject", PRIMARY_REJECT_QUOTA)]:
                if counts[label_name] >= quota:
                    continue
                rows = grouped[group_key][label_name]
                while rows:
                    row = rows.pop(0)
                    if can_select(
                        row,
                        "primary_binary",
                        selected_keys,
                        global_scan_counts,
                        global_directed_pair_counts,
                        primary_class_pair_counts,
                        primary_class_pair_rank_counts,
                        raw_diag_bin_counts,
                    ):
                        record_selection(
                            row,
                            selected_keys,
                            global_scan_counts,
                            global_directed_pair_counts,
                            primary_class_pair_counts,
                            primary_class_pair_rank_counts,
                            raw_diag_bin_counts,
                            "primary_binary",
                        )
                        role = "accept" if label_name == "accept" else "reject"
                        selected.append({**row, "subset": "primary_binary", "role": role})
                        counts[label_name] += 1
                        progress = True
                        break
    return selected


def select_simple_pool(
    rows: list[dict[str, Any]],
    quota: int,
    subset: str,
    role: str,
    selected_keys: set[str],
    global_scan_counts: Counter[str],
    global_directed_pair_counts: Counter[str],
    primary_class_pair_counts: Counter[str],
    primary_class_pair_rank_counts: Counter[str],
    raw_diag_bin_counts: Counter[str],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in rows:
        if len(selected) >= quota:
            break
        if can_select(
            row,
            subset,
            selected_keys,
            global_scan_counts,
            global_directed_pair_counts,
            primary_class_pair_counts,
            primary_class_pair_rank_counts,
            raw_diag_bin_counts,
        ):
            record_selection(
                row,
                selected_keys,
                global_scan_counts,
                global_directed_pair_counts,
                primary_class_pair_counts,
                primary_class_pair_rank_counts,
                raw_diag_bin_counts,
                subset,
            )
            selected.append({**row, "subset": subset, "role": role})
    return selected


def materialize_selection(buckets: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    selected_keys: set[str] = set()
    global_scan_counts: Counter[str] = Counter()
    global_directed_pair_counts: Counter[str] = Counter()
    primary_class_pair_counts: Counter[str] = Counter()
    primary_class_pair_rank_counts: Counter[str] = Counter()
    raw_diag_bin_counts: Counter[str] = Counter()
    selected: list[dict[str, Any]] = []
    selected.extend(
        select_raw_distance_diagnostic(
            buckets,
            selected_keys,
            global_scan_counts,
            global_directed_pair_counts,
            primary_class_pair_counts,
            primary_class_pair_rank_counts,
            raw_diag_bin_counts,
        )
    )
    selected.extend(
        select_primary(
            buckets,
            selected_keys,
            global_scan_counts,
            global_directed_pair_counts,
            primary_class_pair_counts,
            primary_class_pair_rank_counts,
            raw_diag_bin_counts,
        )
    )
    selected.extend(
        select_simple_pool(
            buckets["near_nonexact_satisfied"],
            ABSTAIN_NEAR_NONGT_QUOTA,
            "abstain_qe",
            "near_nonexact_satisfied",
            selected_keys,
            global_scan_counts,
            global_directed_pair_counts,
            primary_class_pair_counts,
            primary_class_pair_rank_counts,
            raw_diag_bin_counts,
        )
    )
    selected.extend(
        select_simple_pool(
            buckets["ambiguous_distance"],
            ABSTAIN_AMBIGUOUS_QUOTA,
            "abstain_qe",
            "ambiguous_distance",
            selected_keys,
            global_scan_counts,
            global_directed_pair_counts,
            primary_class_pair_counts,
            primary_class_pair_rank_counts,
            raw_diag_bin_counts,
        )
    )
    selected.extend(
        select_simple_pool(
            buckets["geometry_uncertain"],
            ABSTAIN_UNCERTAIN_QUOTA,
            "abstain_qe",
            "geometry_uncertain",
            selected_keys,
            global_scan_counts,
            global_directed_pair_counts,
            primary_class_pair_counts,
            primary_class_pair_rank_counts,
            raw_diag_bin_counts,
        )
    )
    selected.extend(
        select_simple_pool(
            buckets["gt_geometry_conflict"],
            GT_CONFLICT_AUDIT_QUOTA,
            "diagnostic_only",
            "gt_geometry_conflict_audit",
            selected_keys,
            global_scan_counts,
            global_directed_pair_counts,
            primary_class_pair_counts,
            primary_class_pair_rank_counts,
            raw_diag_bin_counts,
        )
    )
    return selected


def c_e_label(row: dict[str, Any]) -> int | str:
    if row["role"] in {"accept", "accept_diagnostic"}:
        return 1
    if row["role"] in {"reject", "reject_diagnostic"}:
        return 0
    if row["role"] == "gt_geometry_conflict_audit":
        return "audit_required"
    return "abstain"


def p_rel_label(row: dict[str, Any]) -> str:
    label = c_e_label(row)
    if label == 1:
        return "accept"
    if label == 0:
        return "reject"
    return str(label)


def p_obs_label(row: dict[str, Any]) -> str:
    if row["role"] == "geometry_uncertain":
        return "uncertain_or_unobservable"
    if row["role"] == "ambiguous_distance":
        return "ambiguous"
    if row["role"] == "near_nonexact_satisfied":
        return "observable_but_unlabeled"
    return "observable"


def make_model_safe_row(row: dict[str, Any], row_id: str) -> dict[str, Any]:
    raw = row["raw_features"]
    g_e = {field: safe_float(raw.get(field)) for field in G_E_FIELDS}
    missing = sorted(field for field, value in g_e.items() if value is None)
    return {
        "schema_version": MODEL_SAFE_SCHEMA,
        "row_id": row_id,
        "split": "train",
        "subset": row["subset"],
        "role": row["role"],
        "feature_blocks": {
            "T_e": {
                "predicate_label": "close by",
                "predicate_text": "close by",
                "predicate_family": "proximity",
                "subject_class_text": row["subject_class"],
                "object_class_text": row["object_class"],
            },
            "Z_e_safe": {
                "semantic_score_raw": safe_float(row["semantic"].get("semantic_score_raw")),
                "semantic_score_norm": safe_float(row["semantic"].get("semantic_score_norm")),
                "rank_band": row["rank_band"],
                "rank_in_context": row["semantic"].get("rank_in_context"),
                "predicate_rank_for_pair": row["semantic"].get("predicate_rank_for_pair"),
                "source_id": row["source"].get("source_id"),
            },
            "G_e": g_e,
            "Q_e_safe": {
                "geometry_available": row["geometry"].get("geometry_available") is True,
                "geometry_checkable": row["geometry"].get("geometry_checkable") is True,
                "feature_missing_count": len(missing),
                "feature_complete": not missing,
            },
        },
        "targets": {
            "C_e_label": c_e_label(row),
            "p_rel_label": p_rel_label(row),
            "p_obs_label": p_obs_label(row),
            "is_primary_binary": row["subset"] == "primary_binary",
            "is_raw_distance_diagnostic": row["subset"] == "raw_distance_diagnostic",
            "is_abstain_or_audit": row["subset"] in {"abstain_qe", "diagnostic_only"},
        },
    }


def make_hidden_row(row: dict[str, Any], row_id: str) -> dict[str, Any]:
    return {
        "schema_version": HIDDEN_SCHEMA,
        "row_id": row_id,
        "identity": {
            "row_key": row["row_key"],
            "prediction_id": row["prediction_id"],
            "scan_id": row["scan_id"],
            "subgraph_id": row["subgraph_id"],
            "directed_pair_id": row["directed_pair_id"],
            "subject_id": row["subject_id"],
            "object_id": row["object_id"],
        },
        "hidden_controls": {
            "subject_object_class_pair": row["class_pair"],
            "class_pair_rank_key": row["class_pair_rank"],
            "rank_band": row["rank_band"],
            "label_match_status": row["label_match_status"],
            "geometry_status": row["geometry_status"],
            "distance_bucket": row["distance_bucket"],
            "candidate_bucket": row["candidate_bucket"],
            "raw_distance_bin": row["raw_distance_bin"],
            "norm_distance_bin": row["norm_distance_bin"],
            "p_geom_valid": safe_float(row["geometry"].get("p_geom_valid")),
            "p_geom_invalid": safe_float(row["geometry"].get("p_geom_invalid")),
            "geometry_residual_proxy": safe_float(row["geometry"].get("geometry_residual_proxy")),
        },
        "control_tags": {
            "use_for_primary_binary": row["subset"] == "primary_binary",
            "use_for_raw_distance_diagnostic": row["subset"] == "raw_distance_diagnostic",
            "use_for_abstain_qe": row["subset"] == "abstain_qe",
            "use_for_gt_conflict_audit": row["role"] == "gt_geometry_conflict_audit",
        },
        "source_feature_snapshot": {
            "semantic_score_raw": safe_float(row["semantic"].get("semantic_score_raw")),
            "semantic_score_norm": safe_float(row["semantic"].get("semantic_score_norm")),
            "rank_in_context": row["semantic"].get("rank_in_context"),
            "source_id": row["source"].get("source_id"),
        },
        "target_construction": {
            "near_threshold_normalized_distance_xy": NEAR_NORM_XY,
            "far_threshold_normalized_distance_xy": FAR_NORM_XY,
            "raw_distance_bin_width": RAW_DISTANCE_BIN_WIDTH,
            "norm_distance_bin_width": NORM_DISTANCE_BIN_WIDTH,
        },
    }


def build_rows(selected: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    model_safe: list[dict[str, Any]] = []
    hidden: list[dict[str, Any]] = []
    index_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(selected, start=1):
        row_id = f"h002_close_by_{idx:05d}_{stable_hash(row['row_key'], length=10)}"
        safe_row = make_model_safe_row(row, row_id)
        hidden_row = make_hidden_row(row, row_id)
        model_safe.append(safe_row)
        hidden.append(hidden_row)
        index_rows.append(
            {
                "row_id": row_id,
                "subset": row["subset"],
                "role": row["role"],
                "target_C_e": safe_row["targets"]["C_e_label"],
                "target_p_rel": safe_row["targets"]["p_rel_label"],
                "target_p_obs": safe_row["targets"]["p_obs_label"],
                "subject_class": row["subject_class"],
                "object_class": row["object_class"],
                "rank_band_hidden": row["rank_band"],
                "raw_distance_bin_hidden": row["raw_distance_bin"],
                "candidate_bucket_hidden": row["candidate_bucket"],
            }
        )
    return model_safe, hidden, index_rows


def count_rows(rows: list[dict[str, Any]], key_fn) -> Counter[Any]:
    counter: Counter[Any] = Counter()
    for row in rows:
        counter[key_fn(row)] += 1
    return counter


def quota_audit(model_safe: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    subset_role = count_rows(model_safe, lambda row: (row["subset"], row["role"]))
    expected = {
        ("primary_binary", "accept"): PRIMARY_ACCEPT_QUOTA,
        ("primary_binary", "reject"): PRIMARY_REJECT_QUOTA,
        ("abstain_qe", "near_nonexact_satisfied"): ABSTAIN_NEAR_NONGT_QUOTA,
        ("abstain_qe", "ambiguous_distance"): ABSTAIN_AMBIGUOUS_QUOTA,
        ("abstain_qe", "geometry_uncertain"): ABSTAIN_UNCERTAIN_QUOTA,
        ("raw_distance_diagnostic", "accept_diagnostic"): RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA,
        ("raw_distance_diagnostic", "reject_diagnostic"): RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA,
        ("diagnostic_only", "gt_geometry_conflict_audit"): GT_CONFLICT_AUDIT_QUOTA,
    }
    for key, quota in expected.items():
        rows.append({"subset": key[0], "role": key[1], "observed": subset_role.get(key, 0), "expected": quota, "passed": subset_role.get(key, 0) == quota})
    rows.append({"subset": "all", "role": "total", "observed": len(model_safe), "expected": sum(expected.values()), "passed": len(model_safe) == sum(expected.values())})
    return rows


def cap_audit(hidden: list[dict[str, Any]], model_safe_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    scan_counts = Counter(row["identity"]["scan_id"] for row in hidden)
    directed_counts = Counter(row["identity"]["directed_pair_id"] for row in hidden)
    primary_hidden = [row for row in hidden if model_safe_by_id[row["row_id"]]["subset"] == "primary_binary"]
    raw_diag_hidden = [row for row in hidden if model_safe_by_id[row["row_id"]]["subset"] == "raw_distance_diagnostic"]
    class_pair_counts = Counter(row["hidden_controls"]["subject_object_class_pair"] for row in primary_hidden)
    class_pair_rank_counts = Counter(row["hidden_controls"]["class_pair_rank_key"] for row in primary_hidden)
    raw_bin_counts = Counter(row["hidden_controls"]["raw_distance_bin"] for row in raw_diag_hidden)
    audits = [
        {"cap_axis": "scan_id", "max_observed": max(scan_counts.values()) if scan_counts else 0, "limit": MAX_ROWS_PER_SCAN},
        {"cap_axis": "directed_pair_id", "max_observed": max(directed_counts.values()) if directed_counts else 0, "limit": MAX_ROWS_PER_DIRECTED_PAIR},
        {"cap_axis": "primary_subject_object_class_pair", "max_observed": max(class_pair_counts.values()) if class_pair_counts else 0, "limit": MAX_ROWS_PER_CLASS_PAIR},
        {"cap_axis": "primary_class_pair_rank", "max_observed": max(class_pair_rank_counts.values()) if class_pair_rank_counts else 0, "limit": MAX_ROWS_PER_CLASS_PAIR_RANK},
        {"cap_axis": "raw_distance_bin", "max_observed": max(raw_bin_counts.values()) if raw_bin_counts else 0, "limit": MAX_ROWS_PER_RAW_DISTANCE_BIN},
    ]
    for row in audits:
        row["passed"] = row["max_observed"] <= row["limit"]
    return audits


def feature_schema_precheck(model_safe: list[dict[str, Any]]) -> list[dict[str, Any]]:
    forbidden = [
        "label_match_status",
        "geometry_status",
        "candidate_bucket",
        "distance_bucket",
        "scan_id",
        "directed_pair_id",
        "row_key",
        "prediction_id",
        "p_geom_valid",
        "p_geom_invalid",
    ]
    rows: list[dict[str, Any]] = []
    hit_count = 0
    for row in model_safe:
        text = json.dumps(row.get("feature_blocks", {}), ensure_ascii=False, sort_keys=True)
        hits = [fragment for fragment in forbidden if fragment in text]
        if hits:
            hit_count += 1
            if len(rows) < 20:
                rows.append({"row_id": row["row_id"], "hits": ";".join(hits)})
    rows.append({"row_id": "__summary__", "hits": hit_count, "passed": hit_count == 0})
    return rows


def build_report(summary: dict[str, Any], quota_rows: list[dict[str, Any]], cap_rows: list[dict[str, Any]]) -> str:
    failed_quota = [row for row in quota_rows if not row["passed"]]
    failed_caps = [row for row in cap_rows if not row["passed"]]
    return f"""# H002 Proximity Close-By Candidate Materialization

## Status

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
validation_errors = {summary["validation_errors"]}
next_todo = {summary["next_todo"]}
```

## Materialized Rows

```text
total_rows = {summary["row_counts"]["total_rows"]}
primary_binary_rows = {summary["row_counts"]["primary_binary_rows"]}
raw_distance_diagnostic_rows = {summary["row_counts"]["raw_distance_diagnostic_rows"]}
abstain_qe_rows = {summary["row_counts"]["abstain_qe_rows"]}
gt_geometry_conflict_audit_rows = {summary["row_counts"]["gt_geometry_conflict_audit_rows"]}
```

Quota failures: {len(failed_quota)}
Cap failures: {len(failed_caps)}

## Interpretation

The planned close-by rows were materialized as train-only candidate artifacts.
Model-safe fields exclude `label_match_status`, `geometry_status`, candidate
buckets, distance buckets, identity fields, and `p_geom_valid`. These fields are
kept only in the hidden manifest for audit and controls.

The next stage must run schema and shortcut audit before learned smoke.
"""


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary_path = args.plan_dir / "summary.json"
    plan = read_json(plan_summary_path) if plan_summary_path.exists() else {}
    validation_errors = validate_plan(plan)

    if not (args.train_rga_dir / "match_rows.jsonl").exists():
        validation_errors.append({"error_type": "missing_match_rows", "path": rel_path(args.train_rga_dir / "match_rows.jsonl")})

    if validation_errors:
        selected: list[dict[str, Any]] = []
    else:
        buckets = scan_candidates(args.train_rga_dir / "match_rows.jsonl")
        selected = materialize_selection(buckets)

    model_safe, hidden, index_rows = build_rows(selected)
    model_safe_by_id = {row["row_id"]: row for row in model_safe}
    quota_rows = quota_audit(model_safe)
    cap_rows = cap_audit(hidden, model_safe_by_id)
    schema_precheck = feature_schema_precheck(model_safe)

    for row in quota_rows:
        if not row["passed"]:
            validation_errors.append({"error_type": "quota_audit_failed", **row})
    for row in cap_rows:
        if not row["passed"]:
            validation_errors.append({"error_type": "cap_audit_failed", **row})
    if schema_precheck[-1]["passed"] is not True:
        validation_errors.append({"error_type": "schema_precheck_failed", "hits": schema_precheck[-1]["hits"]})

    status = STATUS_READY if not validation_errors else STATUS_ERROR
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": "materialized_close_by_controlled_candidates" if status == STATUS_READY else "blocked_materialization_errors",
        "next_todo": NEXT_TODO if status == STATUS_READY else "fix_materialization_errors",
        "validation_errors": len(validation_errors),
        "input_plan_summary": rel_path(plan_summary_path),
        "row_counts": {
            "total_rows": len(model_safe),
            "primary_binary_rows": sum(1 for row in model_safe if row["subset"] == "primary_binary"),
            "raw_distance_diagnostic_rows": sum(1 for row in model_safe if row["subset"] == "raw_distance_diagnostic"),
            "abstain_qe_rows": sum(1 for row in model_safe if row["subset"] == "abstain_qe"),
            "gt_geometry_conflict_audit_rows": sum(1 for row in model_safe if row["subset"] == "diagnostic_only"),
        },
        "boundary": {
            "split": "train_only_candidate_materialization",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "model_safe_view": rel_path(args.output_dir / "model_safe_view.jsonl"),
            "hidden_manifest": rel_path(args.output_dir / "hidden_manifest.jsonl"),
            "row_index": rel_path(args.output_dir / "row_index.csv"),
            "quota_audit": rel_path(args.output_dir / "quota_audit.csv"),
            "cap_audit": rel_path(args.output_dir / "cap_audit.csv"),
            "schema_precheck": rel_path(args.output_dir / "schema_precheck.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "model_safe_view.jsonl", model_safe)
    write_jsonl(args.output_dir / "hidden_manifest.jsonl", hidden)
    write_csv(args.output_dir / "row_index.csv", index_rows)
    write_csv(args.output_dir / "quota_audit.csv", quota_rows)
    write_csv(args.output_dir / "cap_audit.csv", cap_rows)
    write_csv(args.output_dir / "schema_precheck.csv", schema_precheck)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    (args.output_dir / "report.md").write_text(build_report(summary, quota_rows, cap_rows), encoding="utf-8")


if __name__ == "__main__":
    main()
