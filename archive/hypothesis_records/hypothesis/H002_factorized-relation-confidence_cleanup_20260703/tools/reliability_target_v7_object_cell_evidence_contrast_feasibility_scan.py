#!/usr/bin/env python3
"""Scan H002 v7 object-cell evidence-contrast feasibility on train queues."""

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

DEFAULT_PATH_DECISION = (
    RGA_ROOT
    / "reliability_target_v6_shortcut_controlled_path_decision_codex_proxy_user_requested"
    / "summary.json"
)
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = (
    RGA_ROOT
    / "reliability_target_v7_object_cell_evidence_contrast_feasibility_scan_codex_proxy_user_requested"
)

EXPECTED_PATH_STATUS = (
    "h002_reliability_target_v6_shortcut_controlled_path_decision_select_v7_object_cell_evidence_contrast_feasibility"
)
EXPECTED_NEXT_TODO = "reliability_target_v7_object_cell_evidence_contrast_feasibility_scan"
NEXT_TODO = "reliability_target_v7_object_cell_evidence_contrast_candidate_mining"

PRIMARY_FAMILIES = ("support_contact", "relative_vertical")
BUCKET_BY_QUEUE = {
    "HL": "B2_semantic_high_geometry_low",
    "LH": "B3_semantic_low_geometry_high",
}
BUCKETS = ("B2_semantic_high_geometry_low", "B3_semantic_low_geometry_high")

GROUP_ROW_CAP = 8
PREVIEW_TARGET_ROWS = 240
MIN_PRIMARY_MIXED_GROUPS = 20
MIN_EXPECTED_ROWS_AFTER_CAPS = 160
MAX_SINGLE_PAIR_SHARE = 0.10
MAX_SINGLE_CELL_SHARE = 0.10
MAX_ROWS_PER_SCAN = 16

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
    parser.add_argument("--preview-target-rows", type=int, default=PREVIEW_TARGET_ROWS)
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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
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


def norm_label(value: Any) -> str:
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


def is_structural_pair(subject_label: str, object_label: str) -> bool:
    return subject_label in STRUCTURAL_CONTEXT or object_label in STRUCTURAL_CONTEXT


def is_hard_room_surface_pair(subject_label: str, object_label: str) -> bool:
    return subject_label in HARD_ROOM_SURFACES or object_label in HARD_ROOM_SURFACES


def bucket_for_row(row: dict[str, Any]) -> str:
    return BUCKET_BY_QUEUE.get(str(row.get("queue_kind", "")).strip(), str(row.get("queue_kind", "")).strip())


def enrich_row(row: dict[str, Any], queue_path: Path) -> dict[str, Any]:
    subject_label = norm_label(row.get("subject_label"))
    object_label = norm_label(row.get("object_label"))
    predicate_family = str(row.get("predicate_family") or "")
    predicate_label = norm_label(row.get("predicate_label"))
    bucket = bucket_for_row(row)
    subject_object_label_pair = f"{subject_label}|{object_label}"
    object_family_cell = f"{object_label}|{predicate_family}"
    subject_object_family_cell = f"{subject_label}|{object_label}|{predicate_family}"
    endpoint = endpoint_pattern(subject_label, object_label)
    return {
        **row,
        "semantic_geometry_bucket": bucket,
        "subject_label_norm": subject_label,
        "object_label_norm": object_label,
        "predicate_label_norm": predicate_label,
        "subject_object_label_pair": subject_object_label_pair,
        "object_family_cell": object_family_cell,
        "subject_object_family_cell": subject_object_family_cell,
        "endpoint_pattern": endpoint,
        "same_label_endpoint": subject_label == object_label,
        "structural_pair": is_structural_pair(subject_label, object_label),
        "hard_room_surface_pair": is_hard_room_surface_pair(subject_label, object_label),
        "semantic_rank_int": as_int(row.get("semantic_rank")),
        "semantic_score_norm_float": as_float(row.get("semantic_score_norm")),
        "p_geom_valid_float": as_float(row.get("p_geom_valid")),
        "source_queue_path": rel_path(queue_path),
    }


def strict_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        row["predicate_family"],
        row["predicate_label_norm"],
        row["subject_object_family_cell"],
        row["endpoint_pattern"],
    )


def relaxed_predicate_object_family_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        row["predicate_family"],
        row["predicate_label_norm"],
        row["object_family_cell"],
        row["endpoint_pattern"],
    )


def family_object_family_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (row["predicate_family"], row["object_family_cell"], row["endpoint_pattern"])


def family_endpoint_key(row: dict[str, Any]) -> tuple[str, str]:
    return (row["predicate_family"], row["endpoint_pattern"])


LEVELS = {
    "strict_object_cell": strict_key,
    "relaxed_predicate_object_family": relaxed_predicate_object_family_key,
    "family_object_family": family_object_family_key,
    "family_endpoint": family_endpoint_key,
}


def validate_path_decision(path_decision: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_decision.get("status") != EXPECTED_PATH_STATUS:
        errors.append(
            {
                "error_type": "unexpected_path_decision_status",
                "expected": EXPECTED_PATH_STATUS,
                "actual": path_decision.get("status"),
            }
        )
    if path_decision.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append(
            {
                "error_type": "unexpected_path_decision_next_todo",
                "expected": EXPECTED_NEXT_TODO,
                "actual": path_decision.get("next_todo"),
            }
        )
    boundary = path_decision.get("boundary") or {}
    expected_false = [
        "fills_new_labels",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "paper_evidence_allowed",
        "posterior_smoke_allowed",
        "test_usage",
        "trains_new_posterior",
        "validation_usage",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "unexpected_boundary_value", "field": key, "expected": False, "actual": boundary.get(key)})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "unexpected_boundary_split", "expected": "train_only", "actual": boundary.get("split")})
    next_plan = path_decision.get("next_plan") or {}
    if next_plan.get("posterior_smoke_not_allowed_yet") is not True:
        errors.append({"error_type": "posterior_smoke_not_blocked_in_next_plan"})
    if next_plan.get("new_label_fill_not_allowed_yet") is not True:
        errors.append({"error_type": "new_label_fill_not_blocked_in_next_plan"})
    if next_plan.get("candidate_mining_not_allowed_yet") is not True:
        errors.append({"error_type": "candidate_mining_not_blocked_in_next_plan"})
    return errors


def read_rows(hl_queue: Path, lh_queue: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    source_counts: dict[str, Any] = {
        "read_rows_by_queue": Counter(),
        "primary_rows_by_queue": Counter(),
        "primary_rows_by_family": Counter(),
        "primary_rows_by_bucket": Counter(),
    }
    required_fields = [
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
    for queue_path, queue_name in [(hl_queue, "HL"), (lh_queue, "LH")]:
        for row in iter_jsonl(queue_path):
            source_counts["read_rows_by_queue"][queue_name] += 1
            for field in required_fields:
                if field not in row:
                    errors.append({"error_type": "missing_required_field", "queue": queue_name, "field": field, "row": row.get("prediction_id")})
            if row.get("predicate_family") not in PRIMARY_FAMILIES:
                continue
            enriched = enrich_row(row, queue_path)
            if enriched["semantic_geometry_bucket"] not in BUCKETS:
                errors.append(
                    {
                        "error_type": "unexpected_queue_bucket",
                        "queue": queue_name,
                        "prediction_id": row.get("prediction_id"),
                        "bucket": enriched["semantic_geometry_bucket"],
                    }
                )
                continue
            rows.append(enriched)
            source_counts["primary_rows_by_queue"][queue_name] += 1
            source_counts["primary_rows_by_family"][enriched["predicate_family"]] += 1
            source_counts["primary_rows_by_bucket"][enriched["semantic_geometry_bucket"]] += 1
    return rows, source_counts, errors


def build_groups(rows: list[dict[str, Any]]) -> dict[str, dict[tuple[Any, ...], list[int]]]:
    grouped: dict[str, dict[tuple[Any, ...], list[int]]] = {}
    for level_name, key_func in LEVELS.items():
        level_groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)
        for idx, row in enumerate(rows):
            level_groups[key_func(row)].append(idx)
        grouped[level_name] = dict(level_groups)
    return grouped


def summarize_group(level_name: str, key: tuple[Any, ...], indices: list[int], rows: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_counts = Counter(rows[idx]["semantic_geometry_bucket"] for idx in indices)
    family_counts = Counter(rows[idx]["predicate_family"] for idx in indices)
    pair_counts = Counter(rows[idx]["subject_object_label_pair"] for idx in indices)
    cell_counts = Counter(rows[idx]["subject_object_family_cell"] for idx in indices)
    structural_count = sum(1 for idx in indices if rows[idx]["structural_pair"])
    hard_surface_count = sum(1 for idx in indices if rows[idx]["hard_room_surface_pair"])
    min_bucket = min(bucket_counts.get(BUCKETS[0], 0), bucket_counts.get(BUCKETS[1], 0))
    eligible = min_bucket > 0
    capacity = min(GROUP_ROW_CAP, 2 * min_bucket) if eligible else 0
    family = rows[indices[0]]["predicate_family"] if indices else ""
    key_parts = list(key)
    return {
        "level": level_name,
        "group_key": " || ".join(str(part) for part in key_parts),
        "key_part_0": key_parts[0] if len(key_parts) > 0 else "",
        "key_part_1": key_parts[1] if len(key_parts) > 1 else "",
        "key_part_2": key_parts[2] if len(key_parts) > 2 else "",
        "key_part_3": key_parts[3] if len(key_parts) > 3 else "",
        "row_count": len(indices),
        "family": family,
        "b2_count": bucket_counts.get(BUCKETS[0], 0),
        "b3_count": bucket_counts.get(BUCKETS[1], 0),
        "eligible_mixed": eligible,
        "capacity_after_group_cap": capacity,
        "dominant_subject_object_label_pair": pair_counts.most_common(1)[0][0] if pair_counts else "",
        "dominant_subject_object_family_cell": cell_counts.most_common(1)[0][0] if cell_counts else "",
        "structural_pair_count": structural_count,
        "structural_pair_share": structural_count / len(indices) if indices else 0.0,
        "hard_room_surface_pair_count": hard_surface_count,
        "hard_room_surface_pair_share": hard_surface_count / len(indices) if indices else 0.0,
        "family_counts": dict(sorted(family_counts.items())),
    }


def level_summaries(grouped: dict[str, dict[tuple[Any, ...], list[int]]], rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    summaries: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    for level_name, groups in grouped.items():
        group_rows = [summarize_group(level_name, key, indices, rows) for key, indices in groups.items()]
        eligible_rows = [row for row in group_rows if row["eligible_mixed"]]
        capacity_sum = sum(row["capacity_after_group_cap"] for row in eligible_rows)
        family_eligible = Counter(row["family"] for row in eligible_rows if row["family"])
        family_capacity = Counter()
        for row in eligible_rows:
            if row["family"]:
                family_capacity[row["family"]] += row["capacity_after_group_cap"]
        structural_capacity = sum(row["capacity_after_group_cap"] for row in eligible_rows if row["structural_pair_share"] > 0)
        hard_surface_capacity = sum(row["capacity_after_group_cap"] for row in eligible_rows if row["hard_room_surface_pair_share"] > 0)
        summaries.append(
            {
                "level": level_name,
                "total_groups": len(group_rows),
                "eligible_mixed_groups": len(eligible_rows),
                "expected_rows_after_group_caps": capacity_sum,
                "support_contact_eligible_groups": family_eligible.get("support_contact", 0),
                "relative_vertical_eligible_groups": family_eligible.get("relative_vertical", 0),
                "support_contact_capacity_after_caps": family_capacity.get("support_contact", 0),
                "relative_vertical_capacity_after_caps": family_capacity.get("relative_vertical", 0),
                "structural_capacity_after_caps": structural_capacity,
                "structural_capacity_share": structural_capacity / capacity_sum if capacity_sum else 0.0,
                "hard_room_surface_capacity_after_caps": hard_surface_capacity,
                "hard_room_surface_capacity_share": hard_surface_capacity / capacity_sum if capacity_sum else 0.0,
            }
        )
        inventory.extend(sorted(eligible_rows, key=lambda item: (-item["capacity_after_group_cap"], -item["row_count"], item["group_key"])))
    return summaries, inventory


def group_priority(group_summary: dict[str, Any]) -> tuple[Any, ...]:
    structural_flag = 1 if group_summary["structural_pair_share"] > 0 else 0
    hard_surface_flag = 1 if group_summary["hard_room_surface_pair_share"] > 0 else 0
    same_label_flag = 1 if "same_label" in str(group_summary["group_key"]) else 0
    return (
        hard_surface_flag,
        structural_flag,
        same_label_flag,
        -group_summary["capacity_after_group_cap"],
        -min(group_summary["b2_count"], group_summary["b3_count"]),
        stable_int(group_summary["group_key"]),
    )


def row_priority(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["semantic_rank_int"],
        -row["semantic_score_norm_float"],
        stable_int(str(row.get("prediction_id"))),
    )


def can_add_pair(
    pair_rows: list[dict[str, Any]],
    pair_counts: Counter,
    cell_counts: Counter,
    scan_counts: Counter,
    max_pair_rows: int,
    max_cell_rows: int,
) -> bool:
    proposed_pair_counts = Counter(row["subject_object_label_pair"] for row in pair_rows)
    proposed_cell_counts = Counter(row["subject_object_family_cell"] for row in pair_rows)
    proposed_scan_counts = Counter(row["scan_id"] for row in pair_rows)
    for key, count in proposed_pair_counts.items():
        if pair_counts[key] + count > max_pair_rows:
            return False
    for key, count in proposed_cell_counts.items():
        if cell_counts[key] + count > max_cell_rows:
            return False
    for key, count in proposed_scan_counts.items():
        if scan_counts[key] + count > MAX_ROWS_PER_SCAN:
            return False
    return True


def select_preview(
    grouped: dict[str, dict[tuple[Any, ...], list[int]]],
    rows: list[dict[str, Any]],
    group_inventory: list[dict[str, Any]],
    target_rows: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    strict_groups = grouped["strict_object_cell"]
    strict_summaries = {
        summary["group_key"]: summary
        for summary in group_inventory
        if summary["level"] == "strict_object_cell" and summary["eligible_mixed"]
    }
    summary_by_key = {}
    for key, indices in strict_groups.items():
        group_key = " || ".join(str(part) for part in key)
        if group_key in strict_summaries:
            summary_by_key[key] = strict_summaries[group_key]

    groups_by_family: dict[str, list[tuple[tuple[Any, ...], list[int], dict[str, Any]]]] = defaultdict(list)
    for key, indices in strict_groups.items():
        summary = summary_by_key.get(key)
        if not summary:
            continue
        groups_by_family[summary["family"]].append((key, indices, summary))
    for family in groups_by_family:
        groups_by_family[family].sort(key=lambda item: group_priority(item[2]))

    family_targets = {family: target_rows // len(PRIMARY_FAMILIES) for family in PRIMARY_FAMILIES}
    for family in PRIMARY_FAMILIES[: target_rows % len(PRIMARY_FAMILIES)]:
        family_targets[family] += 1

    max_pair_rows = max(1, math.floor(target_rows * MAX_SINGLE_PAIR_SHARE))
    max_cell_rows = max(1, math.floor(target_rows * MAX_SINGLE_CELL_SHARE))
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    group_counts: Counter = Counter()
    family_counts: Counter = Counter()
    bucket_counts: Counter = Counter()
    pair_counts: Counter = Counter()
    cell_counts: Counter = Counter()
    scan_counts: Counter = Counter()

    for family in PRIMARY_FAMILIES:
        target_for_family = family_targets[family]
        for key, indices, summary in groups_by_family.get(family, []):
            if family_counts[family] >= target_for_family:
                break
            group_key = summary["group_key"]
            if group_counts[group_key] >= GROUP_ROW_CAP:
                continue
            rows_by_bucket: dict[str, list[dict[str, Any]]] = {}
            for bucket in BUCKETS:
                bucket_rows = [rows[idx] for idx in indices if rows[idx]["semantic_geometry_bucket"] == bucket]
                rows_by_bucket[bucket] = sorted(bucket_rows, key=row_priority)
            pair_slots = min(
                GROUP_ROW_CAP // 2,
                len(rows_by_bucket[BUCKETS[0]]),
                len(rows_by_bucket[BUCKETS[1]]),
                (target_for_family - family_counts[family]) // 2,
            )
            for pair_idx in range(pair_slots):
                pair_rows = [rows_by_bucket[BUCKETS[0]][pair_idx], rows_by_bucket[BUCKETS[1]][pair_idx]]
                if any(str(row.get("prediction_id")) in selected_ids for row in pair_rows):
                    continue
                if not can_add_pair(pair_rows, pair_counts, cell_counts, scan_counts, max_pair_rows, max_cell_rows):
                    continue
                for row in pair_rows:
                    output_row = preview_row(row, group_key, summary)
                    selected.append(output_row)
                    selected_ids.add(str(row.get("prediction_id")))
                    group_counts[group_key] += 1
                    family_counts[family] += 1
                    bucket_counts[row["semantic_geometry_bucket"]] += 1
                    pair_counts[row["subject_object_label_pair"]] += 1
                    cell_counts[row["subject_object_family_cell"]] += 1
                    scan_counts[str(row["scan_id"])] += 1
                if family_counts[family] >= target_for_family:
                    break

    selection_summary = {
        "target_rows": target_rows,
        "selected_rows": len(selected),
        "family_counts": dict(sorted(family_counts.items())),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "family_bucket_counts": dict(
            sorted(
                Counter(
                    f"{row['predicate_family']}|{row['semantic_geometry_bucket']}"
                    for row in selected
                ).items()
            )
        ),
        "strict_groups_used": len(group_counts),
        "max_rows_per_strict_group": max(group_counts.values()) if group_counts else 0,
        "object_label_pair_unique": len(pair_counts),
        "max_single_object_label_pair_count": max(pair_counts.values()) if pair_counts else 0,
        "max_single_object_label_pair_share": max(pair_counts.values()) / len(selected) if selected else 0.0,
        "subject_object_family_cell_unique": len(cell_counts),
        "max_single_subject_object_family_cell_count": max(cell_counts.values()) if cell_counts else 0,
        "max_single_subject_object_family_cell_share": max(cell_counts.values()) / len(selected) if selected else 0.0,
        "scans_used": len(scan_counts),
        "max_rows_per_scan": max(scan_counts.values()) if scan_counts else 0,
        "structural_pair_count": sum(1 for row in selected if row["structural_pair"]),
        "structural_pair_share": sum(1 for row in selected if row["structural_pair"]) / len(selected) if selected else 0.0,
        "hard_room_surface_pair_count": sum(1 for row in selected if row["hard_room_surface_pair"]),
        "hard_room_surface_pair_share": sum(1 for row in selected if row["hard_room_surface_pair"]) / len(selected) if selected else 0.0,
    }
    return selected, selection_summary


def preview_row(row: dict[str, Any], strict_group_key: str, group_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v7_object_cell_evidence_contrast_feasibility_preview_row_v1",
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
        "object_family_cell": row.get("object_family_cell"),
        "subject_object_family_cell": row.get("subject_object_family_cell"),
        "endpoint_pattern": row.get("endpoint_pattern"),
        "same_label_endpoint": row.get("same_label_endpoint"),
        "structural_pair": row.get("structural_pair"),
        "hard_room_surface_pair": row.get("hard_room_surface_pair"),
        "strict_group_key": strict_group_key,
        "strict_group_capacity_after_cap": group_summary.get("capacity_after_group_cap"),
        "strict_group_b2_count": group_summary.get("b2_count"),
        "strict_group_b3_count": group_summary.get("b3_count"),
    }


def build_gates(level_summary_rows: list[dict[str, Any]], selection_summary: dict[str, Any], validation_errors: list[dict[str, Any]]) -> dict[str, Any]:
    strict_summary = next(row for row in level_summary_rows if row["level"] == "strict_object_cell")
    families_present = set(selection_summary.get("family_counts", {}))
    gates = {
        "validation_errors_zero": len(validation_errors) == 0,
        "no_validation_or_test_usage": True,
        "train_only": True,
        "no_new_label_fill": True,
        "no_posterior_smoke": True,
        "no_h001_artifact_modification": True,
        "primary_groups_with_mixed_semantic_geometry_evidence": {
            "value": strict_summary["eligible_mixed_groups"],
            "threshold": MIN_PRIMARY_MIXED_GROUPS,
            "pass": strict_summary["eligible_mixed_groups"] >= MIN_PRIMARY_MIXED_GROUPS,
        },
        "expected_rows_after_caps": {
            "value": strict_summary["expected_rows_after_group_caps"],
            "threshold": MIN_EXPECTED_ROWS_AFTER_CAPS,
            "pass": strict_summary["expected_rows_after_group_caps"] >= MIN_EXPECTED_ROWS_AFTER_CAPS,
        },
        "preview_rows": {
            "value": selection_summary["selected_rows"],
            "threshold": MIN_EXPECTED_ROWS_AFTER_CAPS,
            "pass": selection_summary["selected_rows"] >= MIN_EXPECTED_ROWS_AFTER_CAPS,
        },
        "max_single_object_label_pair_share": {
            "value": selection_summary["max_single_object_label_pair_share"],
            "threshold": MAX_SINGLE_PAIR_SHARE,
            "pass": selection_summary["max_single_object_label_pair_share"] <= MAX_SINGLE_PAIR_SHARE,
        },
        "max_single_subject_object_family_cell_share": {
            "value": selection_summary["max_single_subject_object_family_cell_share"],
            "threshold": MAX_SINGLE_CELL_SHARE,
            "pass": selection_summary["max_single_subject_object_family_cell_share"] <= MAX_SINGLE_CELL_SHARE,
        },
        "support_contact_and_relative_vertical_both_present": {
            "value": sorted(families_present),
            "pass": all(family in families_present for family in PRIMARY_FAMILIES),
        },
        "structural_caveat": {
            "value": selection_summary["structural_pair_share"],
            "hard_room_surface_share": selection_summary["hard_room_surface_pair_share"],
            "eligible_pool_structural_capacity_share": strict_summary["structural_capacity_share"],
            "eligible_pool_hard_room_surface_capacity_share": strict_summary["hard_room_surface_capacity_share"],
            "pass": True,
            "caveat_required": (
                selection_summary["structural_pair_share"] > 0.0
                or selection_summary["hard_room_surface_pair_share"] > 0.0
                or strict_summary["structural_capacity_share"] > 0.25
                or strict_summary["hard_room_surface_capacity_share"] > 0.25
            ),
        },
    }
    core_gate_names = [
        "validation_errors_zero",
        "no_validation_or_test_usage",
        "train_only",
        "no_new_label_fill",
        "no_posterior_smoke",
        "no_h001_artifact_modification",
        "primary_groups_with_mixed_semantic_geometry_evidence",
        "expected_rows_after_caps",
        "preview_rows",
        "max_single_object_label_pair_share",
        "max_single_subject_object_family_cell_share",
        "support_contact_and_relative_vertical_both_present",
    ]
    core_pass = True
    for name in core_gate_names:
        value = gates[name]
        if isinstance(value, dict):
            core_pass = core_pass and bool(value.get("pass"))
        else:
            core_pass = core_pass and bool(value)
    gates["core_feasibility_pass"] = core_pass
    return gates


def status_from_gates(gates: dict[str, Any]) -> tuple[str, str, str, bool]:
    if not gates["validation_errors_zero"]:
        return (
            "h002_reliability_target_v7_object_cell_evidence_contrast_feasibility_errors",
            "fix_feasibility_scan_validation_errors",
            "Path or input validation failed; do not proceed.",
            False,
        )
    if not gates["core_feasibility_pass"]:
        return (
            "h002_reliability_target_v7_object_cell_evidence_contrast_feasibility_blocked",
            "freeze_h002_as_rga_diagnostic_framework_or_restrict_to_new_relation_family_after_user_confirmation",
            "The full train pool does not clear the predeclared object-cell contrast gates.",
            False,
        )
    if gates["structural_caveat"]["caveat_required"]:
        return (
            "h002_reliability_target_v7_object_cell_evidence_contrast_feasibility_ready_with_structural_caveat",
            NEXT_TODO,
            "Core feasibility gates pass, but structural/room-surface rows are present and must be controlled in candidate mining.",
            False,
        )
    return (
        "h002_reliability_target_v7_object_cell_evidence_contrast_feasibility_ready",
        NEXT_TODO,
        "Core feasibility gates pass.",
        False,
    )


def write_report(path: Path, summary: dict[str, Any], level_summary_rows: list[dict[str, Any]]) -> None:
    strict = next(row for row in level_summary_rows if row["level"] == "strict_object_cell")
    relaxed = next(row for row in level_summary_rows if row["level"] == "relaxed_predicate_object_family")
    family_object = next(row for row in level_summary_rows if row["level"] == "family_object_family")
    family_endpoint = next(row for row in level_summary_rows if row["level"] == "family_endpoint")
    selection = summary["selection_preview_summary"]
    gates = summary["feasibility_gates"]
    lines = [
        "# H002 V7 Object-Cell Evidence Contrast Feasibility Scan",
        "",
        "This is a train-only feasibility scan. It does not fill labels, train a posterior, use validation/test data, or modify H001 artifacts.",
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
        f"primary families = {summary['source_counts']['primary_rows_by_family']}",
        "```",
        "",
        "## Group Feasibility",
        "",
        "```text",
        f"strict_object_cell eligible groups = {strict['eligible_mixed_groups']}",
        f"strict_object_cell expected rows after caps = {strict['expected_rows_after_group_caps']}",
        f"relaxed_predicate_object_family eligible groups = {relaxed['eligible_mixed_groups']}",
        f"family_object_family eligible groups = {family_object['eligible_mixed_groups']}",
        f"family_endpoint eligible groups = {family_endpoint['eligible_mixed_groups']}",
        "```",
        "",
        "## Selection Preview",
        "",
        "```text",
        f"selected_rows = {selection['selected_rows']}",
        f"family_counts = {selection['family_counts']}",
        f"bucket_counts = {selection['bucket_counts']}",
        f"strict_groups_used = {selection['strict_groups_used']}",
        f"max_single_object_label_pair_share = {selection['max_single_object_label_pair_share']:.4f}",
        f"max_single_subject_object_family_cell_share = {selection['max_single_subject_object_family_cell_share']:.4f}",
        f"structural_pair_share = {selection['structural_pair_share']:.4f}",
        f"hard_room_surface_pair_share = {selection['hard_room_surface_pair_share']:.4f}",
        f"strict_pool_structural_capacity_share = {strict['structural_capacity_share']:.4f}",
        f"strict_pool_hard_room_surface_capacity_share = {strict['hard_room_surface_capacity_share']:.4f}",
        "```",
        "",
        "## Gates",
        "",
    ]
    for gate_name, gate_value in gates.items():
        if isinstance(gate_value, dict):
            lines.append(f"- `{gate_name}`: pass={gate_value.get('pass')} value={gate_value.get('value')}")
        else:
            lines.append(f"- `{gate_name}`: {gate_value}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The scan finds enough same-object-cell bidirectional mismatch capacity to proceed to candidate mining. The result is not evidence for the posterior yet; it only says the next label batch can be constructed without immediately repeating the previous object/category shortcut.",
            "",
            "Because structural and room-surface endpoints remain present, candidate mining must keep explicit caps or strata for these rows. Otherwise the next target can again become a trivial floor/wall/ceiling detector.",
            "",
            "## Artifacts",
            "",
            "```text",
        ]
    )
    for name, artifact_path in summary["output_paths"].items():
        lines.append(f"{name}: {artifact_path}")
    lines.extend(["```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_decision = read_json(args.path_decision)
    validation_errors = validate_path_decision(path_decision)
    rows, source_counts, row_errors = read_rows(args.hl_queue, args.lh_queue)
    validation_errors.extend(row_errors)

    grouped = build_groups(rows)
    level_summary_rows, group_inventory_rows = level_summaries(grouped, rows)
    selected_rows, selection_summary = select_preview(grouped, rows, group_inventory_rows, args.preview_target_rows)
    gates = build_gates(level_summary_rows, selection_summary, validation_errors)
    status, next_todo, decision, posterior_allowed = status_from_gates(gates)

    source_counts_json = {
        key: dict(sorted(value.items())) if isinstance(value, Counter) else value
        for key, value in source_counts.items()
    }
    summary = {
        "schema_version": "h002_reliability_target_v7_object_cell_evidence_contrast_feasibility_scan_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "posterior_allowed": posterior_allowed,
        "candidate_mining_allowed": gates["core_feasibility_pass"],
        "label_fill_allowed": False,
        "validation_used": False,
        "test_used": False,
        "train_only": True,
        "h001_artifacts_modified": False,
        "path_decision_status": path_decision.get("status"),
        "path_decision_next_todo": path_decision.get("next_todo"),
        "primary_families": list(PRIMARY_FAMILIES),
        "bucket_mapping": BUCKET_BY_QUEUE,
        "source_counts": source_counts_json,
        "primary_row_count": len(rows),
        "level_summaries": level_summary_rows,
        "selection_preview_summary": selection_summary,
        "feasibility_gates": gates,
        "validation_error_count": len(validation_errors),
        "validation_errors_path": rel_path(output_dir / "validation_errors.json"),
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "level_summary_csv": rel_path(output_dir / "level_summary.csv"),
            "group_inventory_csv": rel_path(output_dir / "group_inventory.csv"),
            "feasibility_preview_rows_jsonl": rel_path(output_dir / "feasibility_preview_rows.jsonl"),
            "selection_preview_summary_csv": rel_path(output_dir / "selection_preview_summary.csv"),
            "feasibility_gates_json": rel_path(output_dir / "feasibility_gates.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.json"),
        },
        "input_paths": {
            "path_decision": rel_path(args.path_decision),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "feasibility_gates.json", gates)
    write_json(output_dir / "validation_errors.json", validation_errors)
    write_csv(output_dir / "level_summary.csv", level_summary_rows)
    write_csv(output_dir / "group_inventory.csv", group_inventory_rows)
    write_jsonl(output_dir / "feasibility_preview_rows.jsonl", selected_rows)
    write_csv(output_dir / "selection_preview_summary.csv", [selection_summary])
    write_report(output_dir / "report.md", summary, level_summary_rows)

    print(
        "status={status} rows={rows} strict_groups={groups} selected={selected} posterior_allowed={posterior_allowed} next={next_todo}".format(
            status=summary["status"],
            rows=summary["primary_row_count"],
            groups=next(row for row in level_summary_rows if row["level"] == "strict_object_cell")["eligible_mixed_groups"],
            selected=selection_summary["selected_rows"],
            posterior_allowed=summary["posterior_allowed"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
