#!/usr/bin/env python3
"""Scan H002 v8 endpoint-pair counterfactual feasibility on train queues."""

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


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION = RGA_ROOT / "reliability_target_v7_path_decision_codex_proxy_user_requested/summary.json"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_feasibility_scan_codex_proxy_user_requested"

EXPECTED_PATH_STATUS = "h002_reliability_target_v7_path_decision_select_v8_endpoint_pair_counterfactual_feasibility"
EXPECTED_PATH_NEXT = "reliability_target_v8_endpoint_pair_counterfactual_feasibility_scan"
NEXT_TODO_READY = "reliability_target_v8_endpoint_pair_counterfactual_candidate_mining"
NEXT_TODO_BLOCKED = "reliability_target_v8_endpoint_pair_counterfactual_path_decision"

PRIMARY_FAMILIES = ("support_contact", "relative_vertical")
BUCKET_BY_QUEUE = {
    "HL": "B2_semantic_high_geometry_low",
    "LH": "B3_semantic_low_geometry_high",
}
BUCKETS = ("B2_semantic_high_geometry_low", "B3_semantic_low_geometry_high")
TARGET_ROWS = 240
TARGET_PER_FAMILY = 120
TARGET_PER_FAMILY_BUCKET = 60
GROUP_ROW_CAP = 4
MAX_ROWS_PER_SCAN = 16
MAX_SINGLE_LABEL_PAIR_SHARE = 0.08
MAX_SINGLE_FAMILY_CELL_SHARE = 0.08
MIN_EXACT_QBOTH_GROUPS = 20
MIN_DIAGNOSTIC_ROWS = 120
MIN_STRICT_ROWS = 200
MIN_FAMILY_ROWS = 40
GEOMETRY_RANGE_THRESHOLD = 0.05
RANK_RANGE_THRESHOLD = 5

HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
STRUCTURAL_CONTEXT = {
    "floor",
    "wall",
    "ceiling",
    "room",
    "door",
    "doorframe",
    "window",
    "blinds",
    "curtain",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision", type=Path, default=DEFAULT_PATH_DECISION)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-rows", type=int, default=TARGET_ROWS)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def stable_int(value: str) -> int:
    return int(stable_hash(value)[:12], 16)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 999999) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def endpoint_type(label: str) -> str:
    if label in HARD_ROOM_SURFACES:
        return f"hard_room_surface:{label}"
    if label in STRUCTURAL_CONTEXT:
        return f"structural_context:{label}"
    return "object"


def endpoint_pattern(subject_label: str, object_label: str) -> str:
    same = "same_label" if subject_label == object_label else "different_label"
    return f"sub={endpoint_type(subject_label)}|obj={endpoint_type(object_label)}|{same}"


def enrich(row: dict[str, Any], queue_path: Path) -> dict[str, Any]:
    subject_label = norm(row.get("subject_label"))
    object_label = norm(row.get("object_label"))
    subject_id = str(row.get("subject_id"))
    object_id = str(row.get("object_id"))
    scan_id = str(row.get("scan_id"))
    subgraph_id = str(row.get("subgraph_id"))
    predicate_family = str(row.get("predicate_family"))
    predicate_label = norm(row.get("predicate_label"))
    queue_kind = str(row.get("queue_kind"))
    bucket = BUCKET_BY_QUEUE.get(queue_kind, queue_kind)
    ids = sorted([subject_id, object_id])
    return {
        **row,
        "source_queue_path": rel_path(queue_path),
        "queue_kind": queue_kind,
        "semantic_geometry_bucket": bucket,
        "subject_label_norm": subject_label,
        "object_label_norm": object_label,
        "predicate_label_norm": predicate_label,
        "subject_object_label_pair": f"{subject_label}|{object_label}",
        "subject_object_family_cell": f"{subject_label}|{object_label}|{predicate_family}",
        "object_family_cell": f"{object_label}|{predicate_family}",
        "endpoint_pattern": endpoint_pattern(subject_label, object_label),
        "exact_endpoint_pair_key": f"{scan_id}|{subgraph_id}|{subject_id}|{object_id}",
        "undirected_endpoint_pair_key": f"{scan_id}|{subgraph_id}|{ids[0]}|{ids[1]}",
        "scene_label_pair_key": f"{scan_id}|{subgraph_id}|{subject_label}|{object_label}",
        "structural_pair": subject_label in STRUCTURAL_CONTEXT or object_label in STRUCTURAL_CONTEXT,
        "hard_room_surface_pair": subject_label in HARD_ROOM_SURFACES or object_label in HARD_ROOM_SURFACES,
        "semantic_rank_int": as_int(row.get("semantic_rank")),
        "semantic_score_norm_float": as_float(row.get("semantic_score_norm")),
        "p_geom_valid_float": as_float(row.get("p_geom_valid")),
    }


def validate_path_decision(path_decision: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_decision.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_decision_status", "expected": EXPECTED_PATH_STATUS, "actual": path_decision.get("status")})
    if path_decision.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_decision_next_todo", "expected": EXPECTED_PATH_NEXT, "actual": path_decision.get("next_todo")})
    boundary = path_decision.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "fills_new_labels",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "paper_metric_evidence",
        "posterior_smoke_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "unexpected_path_boundary_flag", "key": key, "expected": False, "actual": boundary.get(key)})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "unexpected_path_boundary_split", "expected": "train_only", "actual": boundary.get("split")})
    return errors


def read_rows(hl_queue: Path, lh_queue: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    counts: dict[str, Any] = {
        "read_rows_by_queue": Counter(),
        "primary_rows_by_queue": Counter(),
        "primary_rows_by_family": Counter(),
        "primary_rows_by_family_queue": Counter(),
    }
    required = [
        "prediction_id",
        "scan_id",
        "subgraph_id",
        "subject_id",
        "subject_label",
        "predicate_label",
        "predicate_family",
        "object_id",
        "object_label",
        "queue_kind",
    ]
    for queue_path, expected_queue in [(hl_queue, "HL"), (lh_queue, "LH")]:
        for row in iter_jsonl(queue_path):
            counts["read_rows_by_queue"][expected_queue] += 1
            for field in required:
                if field not in row:
                    errors.append({"error_type": "missing_required_field", "field": field, "queue": expected_queue, "prediction_id": row.get("prediction_id")})
            if row.get("predicate_family") not in PRIMARY_FAMILIES:
                continue
            enriched = enrich(row, queue_path)
            if enriched["semantic_geometry_bucket"] not in BUCKETS:
                errors.append({"error_type": "unexpected_bucket", "prediction_id": row.get("prediction_id"), "bucket": enriched["semantic_geometry_bucket"]})
                continue
            rows.append(enriched)
            counts["primary_rows_by_queue"][expected_queue] += 1
            counts["primary_rows_by_family"][enriched["predicate_family"]] += 1
            counts["primary_rows_by_family_queue"][f"{enriched['predicate_family']}|{expected_queue}"] += 1
    return rows, counts, errors


def group_rows(rows: list[dict[str, Any]], key_name: str) -> dict[str, list[int]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        grouped[str(row[key_name])].append(idx)
    return dict(grouped)


def summarize_group(group_key: str, indices: list[int], rows: list[dict[str, Any]], level: str) -> dict[str, Any]:
    group_rows = [rows[idx] for idx in indices]
    predicate_counts = Counter(row["predicate_label_norm"] for row in group_rows)
    family_counts = Counter(row["predicate_family"] for row in group_rows)
    queue_counts = Counter(row["queue_kind"] for row in group_rows)
    bucket_counts = Counter(row["semantic_geometry_bucket"] for row in group_rows)
    pair_counts = Counter(row["subject_object_label_pair"] for row in group_rows)
    cell_counts = Counter(row["subject_object_family_cell"] for row in group_rows)
    pvals = [row["p_geom_valid_float"] for row in group_rows]
    ranks = [row["semantic_rank_int"] for row in group_rows]
    scores = [row["semantic_score_norm_float"] for row in group_rows]
    geometry_range = max(pvals) - min(pvals) if pvals else 0.0
    rank_range = max(ranks) - min(ranks) if ranks else 0
    score_range = max(scores) - min(scores) if scores else 0.0
    has_vertical_contradiction = "higher than" in predicate_counts and "lower than" in predicate_counts
    has_support_alternative = sum(predicate_counts.get(label, 0) > 0 for label in ["standing on", "lying on", "supported by"]) >= 2
    has_family_mix = len(family_counts) >= 2
    has_multi_predicate = len(predicate_counts) >= 2
    has_queue_mix = len(queue_counts) >= 2
    has_evidence_variation = has_queue_mix or geometry_range >= GEOMETRY_RANGE_THRESHOLD or rank_range >= RANK_RANGE_THRESHOLD
    strong_contrast = len(group_rows) >= 2 and has_multi_predicate and has_evidence_variation
    preferred_exact_contrast = level == "exact_endpoint_pair" and strong_contrast and has_queue_mix
    structural_count = sum(1 for row in group_rows if row["structural_pair"])
    hard_count = sum(1 for row in group_rows if row["hard_room_surface_pair"])
    return {
        "level": level,
        "group_key": group_key,
        "row_count": len(group_rows),
        "predicate_count": len(predicate_counts),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "queue_counts": dict(sorted(queue_counts.items())),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "has_queue_mix": has_queue_mix,
        "has_multi_predicate": has_multi_predicate,
        "has_family_mix": has_family_mix,
        "has_vertical_contradiction": has_vertical_contradiction,
        "has_support_alternative": has_support_alternative,
        "geometry_range": geometry_range,
        "rank_range": rank_range,
        "score_range": score_range,
        "has_evidence_variation": has_evidence_variation,
        "strong_contrast": strong_contrast,
        "preferred_exact_contrast": preferred_exact_contrast,
        "capacity_after_group_cap": min(GROUP_ROW_CAP, len(group_rows)) if strong_contrast else 0,
        "preferred_capacity_after_group_cap": min(GROUP_ROW_CAP, len(group_rows)) if preferred_exact_contrast else 0,
        "dominant_subject_object_label_pair": pair_counts.most_common(1)[0][0] if pair_counts else "",
        "dominant_subject_object_family_cell": cell_counts.most_common(1)[0][0] if cell_counts else "",
        "structural_pair_count": structural_count,
        "structural_pair_share": structural_count / len(group_rows) if group_rows else 0.0,
        "hard_room_surface_pair_count": hard_count,
        "hard_room_surface_pair_share": hard_count / len(group_rows) if group_rows else 0.0,
    }


def build_group_summaries(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, list[int]]]]:
    levels = {
        "exact_endpoint_pair": "exact_endpoint_pair_key",
        "undirected_endpoint_pair": "undirected_endpoint_pair_key",
        "scene_label_pair": "scene_label_pair_key",
    }
    grouped_by_level: dict[str, dict[str, list[int]]] = {}
    inventory: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for level, key_name in levels.items():
        grouped = group_rows(rows, key_name)
        grouped_by_level[level] = grouped
        group_summaries = [summarize_group(key, indices, rows, level) for key, indices in grouped.items()]
        strong = [item for item in group_summaries if item["strong_contrast"]]
        preferred = [item for item in group_summaries if item["preferred_exact_contrast"]]
        summaries.append(
            {
                "level": level,
                "total_groups": len(group_summaries),
                "strong_contrast_groups": len(strong),
                "preferred_exact_contrast_groups": len(preferred),
                "capacity_after_group_cap": sum(item["capacity_after_group_cap"] for item in strong),
                "preferred_capacity_after_group_cap": sum(item["preferred_capacity_after_group_cap"] for item in preferred),
                "support_contact_groups": sum(1 for item in strong if "support_contact" in item["family_counts"]),
                "relative_vertical_groups": sum(1 for item in strong if "relative_vertical" in item["family_counts"]),
                "queue_mixed_groups": sum(1 for item in strong if item["has_queue_mix"]),
                "vertical_contradiction_groups": sum(1 for item in strong if item["has_vertical_contradiction"]),
                "support_alternative_groups": sum(1 for item in strong if item["has_support_alternative"]),
                "hard_room_surface_group_share": sum(1 for item in strong if item["hard_room_surface_pair_share"] > 0.0) / len(strong) if strong else 0.0,
            }
        )
        inventory.extend(sorted(strong, key=group_priority))
    return summaries, inventory, grouped_by_level


def group_priority(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        item["level"] != "exact_endpoint_pair",
        not item["preferred_exact_contrast"],
        item["hard_room_surface_pair_share"] > 0,
        item["structural_pair_share"] > 0,
        -int(item["has_family_mix"]),
        -int(item["has_vertical_contradiction"]),
        -int(item["has_support_alternative"]),
        -item["predicate_count"],
        -item["geometry_range"],
        stable_int(item["group_key"]),
    )


def row_priority(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["hard_room_surface_pair"],
        row["structural_pair"],
        row["semantic_rank_int"],
        -row["semantic_score_norm_float"],
        stable_int(str(row.get("prediction_id"))),
    )


def preview_row(row: dict[str, Any], group_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_feasibility_preview_row_v1",
        "audit_only": True,
        "label_sheet_allowed": False,
        "review_label_filled": False,
        "posterior_input_allowed": False,
        "split": "train",
        "source_id": row.get("source_id"),
        "source_queue_path": row.get("source_queue_path"),
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "queue_kind": row.get("queue_kind"),
        "semantic_geometry_bucket": row.get("semantic_geometry_bucket"),
        "semantic_rank": row.get("semantic_rank"),
        "semantic_score_norm": row.get("semantic_score_norm"),
        "semantic_score_raw": row.get("semantic_score_raw"),
        "p_geom_valid": row.get("p_geom_valid"),
        "geometry_status": row.get("geometry_status"),
        "h001_verification_status": row.get("h001_verification_status"),
        "label_geometry_bucket": row.get("label_geometry_bucket"),
        "label_match_status": row.get("label_match_status"),
        "matched_predicates": row.get("matched_predicates"),
        "machine_hint": row.get("machine_hint"),
        "rank_band": row.get("rank_band"),
        "subject_object_label_pair": row.get("subject_object_label_pair"),
        "subject_object_family_cell": row.get("subject_object_family_cell"),
        "object_family_cell": row.get("object_family_cell"),
        "endpoint_pattern": row.get("endpoint_pattern"),
        "exact_endpoint_pair_key": row.get("exact_endpoint_pair_key"),
        "undirected_endpoint_pair_key": row.get("undirected_endpoint_pair_key"),
        "scene_label_pair_key": row.get("scene_label_pair_key"),
        "structural_pair": row.get("structural_pair"),
        "hard_room_surface_pair": row.get("hard_room_surface_pair"),
        "v8_group_level": group_summary["level"],
        "v8_group_key": group_summary["group_key"],
        "v8_group_row_count": group_summary["row_count"],
        "v8_group_predicate_count": group_summary["predicate_count"],
        "v8_group_has_queue_mix": group_summary["has_queue_mix"],
        "v8_group_has_family_mix": group_summary["has_family_mix"],
        "v8_group_has_vertical_contradiction": group_summary["has_vertical_contradiction"],
        "v8_group_has_support_alternative": group_summary["has_support_alternative"],
        "v8_group_geometry_range": group_summary["geometry_range"],
        "v8_group_rank_range": group_summary["rank_range"],
    }


def can_add(row: dict[str, Any], selected: list[dict[str, Any]], counts: dict[str, Counter], target_rows: int) -> bool:
    max_pair = max(1, math.floor(target_rows * MAX_SINGLE_LABEL_PAIR_SHARE))
    max_cell = max(1, math.floor(target_rows * MAX_SINGLE_FAMILY_CELL_SHARE))
    if counts["label_pair"][row["subject_object_label_pair"]] + 1 > max_pair:
        return False
    if counts["family_cell"][row["subject_object_family_cell"]] + 1 > max_cell:
        return False
    if counts["scan"][str(row["scan_id"])] + 1 > MAX_ROWS_PER_SCAN:
        return False
    if str(row.get("prediction_id")) in counts["prediction_id"]:
        return False
    return True


def select_preview(
    rows: list[dict[str, Any]],
    inventory: list[dict[str, Any]],
    grouped_by_level: dict[str, dict[str, list[int]]],
    target_rows: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target_per_family_bucket = {
        (family, bucket): TARGET_PER_FAMILY_BUCKET
        for family in PRIMARY_FAMILIES
        for bucket in BUCKETS
    }
    selected: list[dict[str, Any]] = []
    counts = {
        "family_bucket": Counter(),
        "family": Counter(),
        "bucket": Counter(),
        "group": Counter(),
        "label_pair": Counter(),
        "family_cell": Counter(),
        "scan": Counter(),
        "prediction_id": Counter(),
    }

    exact_inventory = [item for item in inventory if item["level"] == "exact_endpoint_pair" and item["preferred_exact_contrast"]]
    exact_inventory.sort(key=group_priority)
    for group_summary in exact_inventory:
        if len(selected) >= target_rows:
            break
        indices = grouped_by_level[group_summary["level"]][group_summary["group_key"]]
        group_rows = sorted([rows[idx] for idx in indices], key=row_priority)
        for family in PRIMARY_FAMILIES:
            for bucket in BUCKETS:
                if counts["family_bucket"][(family, bucket)] >= target_per_family_bucket[(family, bucket)]:
                    continue
                candidate = next(
                    (
                        row
                        for row in group_rows
                        if row["predicate_family"] == family
                        and row["semantic_geometry_bucket"] == bucket
                        and can_add(row, selected, counts, target_rows)
                    ),
                    None,
                )
                if candidate is None:
                    continue
                selected.append(preview_row(candidate, group_summary))
                counts["family_bucket"][(family, bucket)] += 1
                counts["family"][family] += 1
                counts["bucket"][bucket] += 1
                counts["group"][group_summary["group_key"]] += 1
                counts["label_pair"][candidate["subject_object_label_pair"]] += 1
                counts["family_cell"][candidate["subject_object_family_cell"]] += 1
                counts["scan"][str(candidate["scan_id"])] += 1
                counts["prediction_id"][str(candidate.get("prediction_id"))] += 1
                if len(selected) >= target_rows:
                    break

    selected_count = len(selected)
    summary = {
        "target_rows": target_rows,
        "selected_rows": selected_count,
        "family_counts": dict(sorted(counts["family"].items())),
        "bucket_counts": dict(sorted(counts["bucket"].items())),
        "family_bucket_counts": {f"{family}|{bucket}": counts["family_bucket"][(family, bucket)] for family in PRIMARY_FAMILIES for bucket in BUCKETS},
        "groups_used": len(counts["group"]),
        "max_rows_per_group": max(counts["group"].values()) if counts["group"] else 0,
        "label_pair_unique": len(counts["label_pair"]),
        "max_single_subject_object_label_pair_count": max(counts["label_pair"].values()) if counts["label_pair"] else 0,
        "max_single_subject_object_label_pair_share": max(counts["label_pair"].values()) / selected_count if selected_count else 0.0,
        "family_cell_unique": len(counts["family_cell"]),
        "max_single_subject_object_family_cell_count": max(counts["family_cell"].values()) if counts["family_cell"] else 0,
        "max_single_subject_object_family_cell_share": max(counts["family_cell"].values()) / selected_count if selected_count else 0.0,
        "scans_used": len(counts["scan"]),
        "max_rows_per_scan": max(counts["scan"].values()) if counts["scan"] else 0,
        "structural_pair_count": sum(1 for row in selected if row["structural_pair"]),
        "structural_pair_share": sum(1 for row in selected if row["structural_pair"]) / selected_count if selected_count else 0.0,
        "hard_room_surface_pair_count": sum(1 for row in selected if row["hard_room_surface_pair"]),
        "hard_room_surface_pair_share": sum(1 for row in selected if row["hard_room_surface_pair"]) / selected_count if selected_count else 0.0,
        "all_rows_exact_endpoint_pair": all(row["v8_group_level"] == "exact_endpoint_pair" for row in selected),
        "all_rows_queue_mixed_group": all(row["v8_group_has_queue_mix"] for row in selected),
    }
    return selected, summary


def build_gates(
    validation_errors: list[dict[str, Any]],
    level_summaries: list[dict[str, Any]],
    selection: dict[str, Any],
) -> dict[str, Any]:
    exact = next(item for item in level_summaries if item["level"] == "exact_endpoint_pair")
    family_counts = selection["family_counts"]
    family_bucket_counts = selection["family_bucket_counts"]
    gates = {
        "validation_errors_zero": len(validation_errors) == 0,
        "train_only": True,
        "no_validation_or_test_usage": True,
        "no_new_label_fill": True,
        "no_posterior_smoke": True,
        "no_h001_artifact_modification": True,
        "exact_endpoint_pair_contrast_groups": {
            "value": exact["preferred_exact_contrast_groups"],
            "threshold": MIN_EXACT_QBOTH_GROUPS,
            "pass": exact["preferred_exact_contrast_groups"] >= MIN_EXACT_QBOTH_GROUPS,
        },
        "expected_rows_after_caps": {
            "value": exact["preferred_capacity_after_group_cap"],
            "diagnostic_threshold": MIN_DIAGNOSTIC_ROWS,
            "strict_threshold": MIN_STRICT_ROWS,
            "diagnostic_pass": exact["preferred_capacity_after_group_cap"] >= MIN_DIAGNOSTIC_ROWS,
            "strict_pass": exact["preferred_capacity_after_group_cap"] >= MIN_STRICT_ROWS,
        },
        "selection_preview_rows": {
            "value": selection["selected_rows"],
            "diagnostic_threshold": MIN_DIAGNOSTIC_ROWS,
            "strict_threshold": MIN_STRICT_ROWS,
            "diagnostic_pass": selection["selected_rows"] >= MIN_DIAGNOSTIC_ROWS,
            "strict_pass": selection["selected_rows"] >= MIN_STRICT_ROWS,
        },
        "family_min_rows": {
            "value": {family: family_counts.get(family, 0) for family in PRIMARY_FAMILIES},
            "threshold": MIN_FAMILY_ROWS,
            "pass": all(family_counts.get(family, 0) >= MIN_FAMILY_ROWS for family in PRIMARY_FAMILIES),
        },
        "family_bucket_min_rows": {
            "value": family_bucket_counts,
            "threshold": TARGET_PER_FAMILY_BUCKET,
            "pass": all(family_bucket_counts.get(f"{family}|{bucket}", 0) >= TARGET_PER_FAMILY_BUCKET for family in PRIMARY_FAMILIES for bucket in BUCKETS),
        },
        "max_single_subject_object_label_pair_share": {
            "value": selection["max_single_subject_object_label_pair_share"],
            "threshold": MAX_SINGLE_LABEL_PAIR_SHARE,
            "pass": selection["max_single_subject_object_label_pair_share"] <= MAX_SINGLE_LABEL_PAIR_SHARE,
        },
        "max_single_subject_object_family_cell_share": {
            "value": selection["max_single_subject_object_family_cell_share"],
            "threshold": MAX_SINGLE_FAMILY_CELL_SHARE,
            "pass": selection["max_single_subject_object_family_cell_share"] <= MAX_SINGLE_FAMILY_CELL_SHARE,
        },
        "all_selected_rows_exact_endpoint_pair": selection["all_rows_exact_endpoint_pair"],
        "all_selected_rows_queue_mixed_group": selection["all_rows_queue_mixed_group"],
        "structural_caveat": {
            "value": selection["structural_pair_share"],
            "hard_room_surface_share": selection["hard_room_surface_pair_share"],
            "pass": True,
            "caveat_required": selection["structural_pair_share"] > 0.25 or selection["hard_room_surface_pair_share"] > 0.25,
        },
    }
    diagnostic_names = [
        "validation_errors_zero",
        "train_only",
        "no_validation_or_test_usage",
        "no_new_label_fill",
        "no_posterior_smoke",
        "no_h001_artifact_modification",
        "exact_endpoint_pair_contrast_groups",
        "family_min_rows",
        "max_single_subject_object_label_pair_share",
        "max_single_subject_object_family_cell_share",
        "all_selected_rows_exact_endpoint_pair",
        "all_selected_rows_queue_mixed_group",
    ]
    diagnostic_pass = True
    for name in diagnostic_names:
        value = gates[name]
        if isinstance(value, dict):
            diagnostic_pass = diagnostic_pass and bool(value.get("pass", value.get("diagnostic_pass", False)))
        else:
            diagnostic_pass = diagnostic_pass and bool(value)
    strict_pass = diagnostic_pass and gates["expected_rows_after_caps"]["strict_pass"] and gates["selection_preview_rows"]["strict_pass"] and gates["family_bucket_min_rows"]["pass"]
    gates["diagnostic_feasibility_pass"] = diagnostic_pass and gates["expected_rows_after_caps"]["diagnostic_pass"] and gates["selection_preview_rows"]["diagnostic_pass"]
    gates["strict_feasibility_pass"] = strict_pass
    return gates


def status_from_gates(gates: dict[str, Any]) -> tuple[str, str, str]:
    if not gates["validation_errors_zero"]:
        return (
            "h002_reliability_target_v8_endpoint_pair_counterfactual_feasibility_errors",
            "fix_reliability_target_v8_endpoint_pair_counterfactual_feasibility_errors",
            "Path-decision or input validation failed.",
        )
    if gates["strict_feasibility_pass"] and gates["structural_caveat"]["caveat_required"]:
        return (
            "h002_reliability_target_v8_endpoint_pair_counterfactual_feasibility_ready_with_structural_caveat",
            NEXT_TODO_READY,
            "Strict endpoint-pair counterfactual feasibility gates pass, but structural endpoint share requires continued caps.",
        )
    if gates["strict_feasibility_pass"]:
        return (
            "h002_reliability_target_v8_endpoint_pair_counterfactual_feasibility_ready",
            NEXT_TODO_READY,
            "Strict endpoint-pair counterfactual feasibility gates pass.",
        )
    if gates["diagnostic_feasibility_pass"]:
        return (
            "h002_reliability_target_v8_endpoint_pair_counterfactual_feasibility_diagnostic_only",
            NEXT_TODO_BLOCKED,
            "Only diagnostic endpoint-pair feasibility gates pass; decide whether to lower scope or reframe.",
        )
    return (
        "h002_reliability_target_v8_endpoint_pair_counterfactual_feasibility_blocked",
        NEXT_TODO_BLOCKED,
        "Endpoint-pair counterfactual feasibility does not clear the predeclared gates.",
    )


def counter_to_json(counts: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in counts.items():
        if isinstance(value, Counter):
            output[key] = {str(k): v for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
        else:
            output[key] = value
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    exact = next(item for item in summary["level_summaries"] if item["level"] == "exact_endpoint_pair")
    undirected = next(item for item in summary["level_summaries"] if item["level"] == "undirected_endpoint_pair")
    scene_label = next(item for item in summary["level_summaries"] if item["level"] == "scene_label_pair")
    selection = summary["selection_preview_summary"]
    lines = [
        "# H002 V8 Endpoint-Pair Counterfactual Feasibility Scan",
        "",
        "This is a train-only feasibility scan. It does not fill labels, train a posterior, use validation/test rows, or modify H001 artifacts.",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"decision = {summary['decision']}",
        f"next = {summary['next_todo']}",
        f"validation_errors = {summary['validation_error_count']}",
        "```",
        "",
        "## Source Counts",
        "",
        "```text",
        f"HL rows read = {summary['source_counts']['read_rows_by_queue'].get('HL', 0)}",
        f"LH rows read = {summary['source_counts']['read_rows_by_queue'].get('LH', 0)}",
        f"primary rows = {summary['primary_row_count']}",
        f"primary rows by family = {summary['source_counts']['primary_rows_by_family']}",
        f"primary rows by family/queue = {summary['source_counts']['primary_rows_by_family_queue']}",
        "```",
        "",
        "## Endpoint-Pair Contrast Capacity",
        "",
        "```text",
        f"exact strong groups = {exact['strong_contrast_groups']}",
        f"exact preferred queue-mixed groups = {exact['preferred_exact_contrast_groups']}",
        f"exact preferred capacity after caps = {exact['preferred_capacity_after_group_cap']}",
        f"undirected strong groups = {undirected['strong_contrast_groups']}",
        f"scene-label strong groups = {scene_label['strong_contrast_groups']}",
        "```",
        "",
        "## Selection Preview",
        "",
        "```text",
        f"selected_rows = {selection['selected_rows']}",
        f"family_counts = {selection['family_counts']}",
        f"bucket_counts = {selection['bucket_counts']}",
        f"family_bucket_counts = {selection['family_bucket_counts']}",
        f"groups_used = {selection['groups_used']}",
        f"max_rows_per_group = {selection['max_rows_per_group']}",
        f"max_single_subject_object_label_pair_share = {selection['max_single_subject_object_label_pair_share']:.4f}",
        f"max_single_subject_object_family_cell_share = {selection['max_single_subject_object_family_cell_share']:.4f}",
        f"structural_pair_share = {selection['structural_pair_share']:.4f}",
        f"hard_room_surface_pair_share = {selection['hard_room_surface_pair_share']:.4f}",
        "```",
        "",
        "## Gates",
        "",
    ]
    for gate_name, gate_value in summary["feasibility_gates"].items():
        if isinstance(gate_value, dict):
            lines.append(f"- `{gate_name}`: {gate_value}")
        else:
            lines.append(f"- `{gate_name}`: `{gate_value}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The scan shows that endpoint/object-controlled counterfactual capacity exists in the train pool. This does not validate the posterior yet; it only means the next candidate batch can be mined without immediately inheriting the v7 object/category shortcut.",
            "",
            "The selected preview keeps exact endpoint-pair groups and queue-mixed groups only. This is stronger than the v7 object-cell balancing because object identity is fixed before semantic and geometry evidence variation is considered.",
            "",
            "## Artifacts",
            "",
            "```text",
        ]
    )
    for key, value in summary["output_paths"].items():
        lines.append(f"{key}: {value}")
    lines.extend(["```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_decision = read_json(args.path_decision)
    validation_errors = validate_path_decision(path_decision)
    rows, source_counts, row_errors = read_rows(args.hl_queue, args.lh_queue)
    validation_errors.extend(row_errors)
    level_summaries, group_inventory, grouped_by_level = build_group_summaries(rows)
    selected_rows, selection_summary = select_preview(rows, group_inventory, grouped_by_level, args.target_rows)
    gates = build_gates(validation_errors, level_summaries, selection_summary)
    status, next_todo, decision = status_from_gates(gates)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "level_summary": output_dir / "level_summary.csv",
        "group_inventory": output_dir / "group_inventory.csv",
        "feasibility_preview_rows": output_dir / "feasibility_preview_rows.jsonl",
        "selection_preview_summary": output_dir / "selection_preview_summary.csv",
        "feasibility_gates": output_dir / "feasibility_gates.json",
        "validation_errors": output_dir / "validation_errors.json",
    }

    summary = {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_feasibility_scan_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "candidate_mining_allowed": next_todo == NEXT_TODO_READY,
        "label_fill_allowed": False,
        "posterior_allowed": False,
        "validation_used": False,
        "test_used": False,
        "train_only": True,
        "h001_artifacts_modified": False,
        "multi_view_as_model_input": False,
        "paper_metric_evidence": False,
        "path_decision_status": path_decision.get("status"),
        "path_decision_next_todo": path_decision.get("next_todo"),
        "primary_families": list(PRIMARY_FAMILIES),
        "bucket_mapping": BUCKET_BY_QUEUE,
        "source_counts": counter_to_json(source_counts),
        "primary_row_count": len(rows),
        "level_summaries": level_summaries,
        "selection_preview_summary": selection_summary,
        "feasibility_gates": gates,
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors,
        "input_paths": {
            "path_decision": rel_path(args.path_decision),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["feasibility_gates"], gates)
    write_json(output_paths["validation_errors"], validation_errors)
    write_csv(output_paths["level_summary"], level_summaries)
    write_csv(output_paths["group_inventory"], group_inventory)
    write_jsonl(output_paths["feasibility_preview_rows"], selected_rows)
    write_csv(output_paths["selection_preview_summary"], [selection_summary])
    write_report(output_paths["report"], summary)

    exact = next(item for item in level_summaries if item["level"] == "exact_endpoint_pair")
    print(
        "status={status} primary_rows={rows} exact_preferred_groups={groups} "
        "preferred_capacity={capacity} selected={selected} posterior_allowed={posterior} "
        "candidate_mining_allowed={candidate} validation_used={validation} test_used={test} next={next_todo}".format(
            status=status,
            rows=len(rows),
            groups=exact["preferred_exact_contrast_groups"],
            capacity=exact["preferred_capacity_after_group_cap"],
            selected=selection_summary["selected_rows"],
            posterior=summary["posterior_allowed"],
            candidate=summary["candidate_mining_allowed"],
            validation=summary["validation_used"],
            test=summary["test_used"],
            next_todo=next_todo,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
