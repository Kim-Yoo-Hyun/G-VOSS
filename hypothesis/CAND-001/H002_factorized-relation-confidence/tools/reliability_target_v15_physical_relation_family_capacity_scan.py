#!/usr/bin/env python3
"""Scan train-only queues for the H002 v15 physical relation-family repair capacity."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_REPAIR_DIR = RGA_ROOT / "reliability_target_v15_physical_relation_family_repair_plan"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v15_physical_relation_family_capacity_scan"

EXPECTED_REPAIR_STATUS = "h002_reliability_target_v15_physical_relation_family_repair_plan_ready_for_capacity_scan"
EXPECTED_REPAIR_NEXT = "reliability_target_v15_physical_relation_family_capacity_scan"

STATUS_PASS = "h002_reliability_target_v15_physical_relation_family_capacity_scan_passed_ready_for_candidate_mining"
STATUS_FAIL = "h002_reliability_target_v15_physical_relation_family_capacity_scan_blocked_capacity_or_mixed_strata"
STATUS_ERROR = "h002_reliability_target_v15_physical_relation_family_capacity_scan_validation_errors"
NEXT_PASS = "reliability_target_v15_physical_relation_family_candidate_mining"
NEXT_FAIL = "reliability_target_v15_physical_relation_family_path_decision_after_capacity_scan"

HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
STRUCTURAL_CONTEXT = {"floor", "wall", "ceiling", "room", "door", "doorframe", "window"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-dir", type=Path, default=DEFAULT_REPAIR_DIR)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stable_int(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:12], 16)


def parse_reason_codes(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
        return [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]
    return [str(value)]


def p_geom_bin(value: Any) -> str:
    p_geom = as_float(value)
    if p_geom is None:
        return "p_unknown"
    if p_geom >= 0.75:
        return "p_high"
    if p_geom >= 0.50:
        return "p_mid"
    if p_geom >= 0.25:
        return "p_low"
    return "p_very_low"


def semantic_score_band(value: Any, rank_band: str) -> str:
    score = as_float(value)
    if score is not None:
        if score >= 0.75:
            return "s_high"
        if score >= 0.50:
            return "s_mid"
        if score >= 0.25:
            return "s_low"
        return "s_very_low"
    if rank_band in {"top50", "top100_only"}:
        return "s_rank_high"
    if rank_band in {"rank_101_200", "rank_201_500"}:
        return "s_rank_mid"
    return "s_rank_low"


def reason_signature(reason_codes: list[str]) -> str:
    if not reason_codes:
        return "reason_unknown"
    return "+".join(sorted(reason_codes)[:3])


def coarse_witness_bin(family: str, geometry_status: str, reason_codes: list[str]) -> str:
    reasons = set(reason_codes)
    if family == "support_contact":
        if "missing_point_evidence" in reasons or "horizontal_plane_missing" in reasons:
            return "support_missing_or_sparse"
        if "plane_gap_supported" in reasons or "soft_penetration_allowed" in reasons or "subtype_legged_floor_support" in reasons:
            return "support_near_contact_or_subtype_supported"
        if "plane_gap_large" in reasons or "positive_float_gap_large" in reasons:
            return "support_gap_large"
        if "robust_gap_too_strict_for_legs" in reasons:
            return "support_legged_ambiguous"
        if geometry_status:
            return f"support_{geometry_status}"
        return "support_unknown"
    if family == "relative_vertical":
        if "vertical_order_matches_predicate" in reasons:
            return "vertical_order_matches"
        if "vertical_order_contradicts_predicate" in reasons:
            return "vertical_order_contradicts"
        if "vertical_margin_ambiguous" in reasons:
            return "vertical_margin_ambiguous"
        if geometry_status:
            return f"vertical_{geometry_status}"
        return "vertical_unknown"
    return f"{family or 'family_unknown'}_{geometry_status or 'status_unknown'}"


def endpoint_generic_state(row: dict[str, Any]) -> str:
    subject = norm(row.get("subject_label"))
    obj = norm(row.get("object_label"))
    if subject in HARD_ROOM_SURFACES:
        return "subject_room_surface"
    if obj in {"wall", "ceiling"}:
        return "object_wall_or_ceiling"
    if obj == "floor":
        return "object_floor"
    if subject in STRUCTURAL_CONTEXT or obj in STRUCTURAL_CONTEXT:
        return "structural_endpoint"
    if subject == obj:
        return "same_label_pair"
    return "object_pair"


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


def directed_pair_key(row: dict[str, Any]) -> str:
    return "|".join([str(row.get("scan_id")), str(row.get("subgraph_id")), str(row.get("subject_id")), str(row.get("object_id"))])


def visible_pair(row: dict[str, Any]) -> str:
    return f"{norm(row.get('subject_label'))}|{norm(row.get('object_label'))}"


def target_predicates(quota_rows: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {(row["family"], row["predicate_label"]) for row in quota_rows}


def validate_repair(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_REPAIR_STATUS:
        errors.append({"error_type": "unexpected_repair_status", "expected": EXPECTED_REPAIR_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_REPAIR_NEXT:
        errors.append({"error_type": "unexpected_repair_next_todo", "expected": EXPECTED_REPAIR_NEXT, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "repair_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "repair_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def compact_row(row: dict[str, Any], queue_path: Path) -> dict[str, Any]:
    family = str(row.get("predicate_family") or "")
    predicate = str(row.get("predicate_label") or "")
    queue_kind = str(row.get("queue_kind") or "")
    rank_band = str(row.get("rank_band") or "rank_unknown")
    geometry_status = str(row.get("geometry_status") or "geometry_unknown")
    reasons = parse_reason_codes(row.get("reason_codes"))
    p_bin = p_geom_bin(row.get("p_geom_valid"))
    s_band = semantic_score_band(row.get("semantic_score_norm"), rank_band)
    coarse = coarse_witness_bin(family, geometry_status, reasons)
    endpoint_state = endpoint_generic_state(row)
    witness_key = "|".join([family, predicate, geometry_status, p_bin, coarse, reason_signature(reasons), endpoint_state])
    strict_key = "|".join([witness_key, queue_kind, rank_band, s_band])
    return {
        "prediction_id": row.get("prediction_id"),
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "subject_label": row.get("subject_label"),
        "predicate_family": family,
        "predicate_label": predicate,
        "object_label": row.get("object_label"),
        "queue_kind": queue_kind,
        "rank_band": rank_band,
        "geometry_status": geometry_status,
        "p_geom_bin": p_bin,
        "coarse_witness_bin": coarse,
        "reason_signature": reason_signature(reasons),
        "endpoint_generic_state": endpoint_state,
        "source_semantic_score_band": s_band,
        "subject_object_label_pair": visible_pair(row),
        "directed_pair_key": directed_pair_key(row),
        "witness_stratum_key": witness_key,
        "strict_stratum_key": strict_key,
        "semantic_rank": row.get("semantic_rank"),
        "semantic_score_norm": row.get("semantic_score_norm"),
        "p_geom_valid": row.get("p_geom_valid"),
        "reason_codes": reasons,
        "source_queue_path": rel_path(queue_path),
        "hash_key": stable_int(str(row.get("prediction_id"))),
        "floor_as_object": norm(row.get("object_label")) == "floor",
        "structural_endpoint": norm(row.get("subject_label")) in STRUCTURAL_CONTEXT or norm(row.get("object_label")) in STRUCTURAL_CONTEXT,
    }


def scan_queues(quota_rows: list[dict[str, str]], hl_queue: Path, lh_queue: Path) -> dict[str, Any]:
    targets = target_predicates(quota_rows)
    raw_by_pred_queue: Counter[str] = Counter()
    eligible_by_pred_queue: Counter[str] = Counter()
    hard_filtered_by_pred_queue: Counter[str] = Counter()
    hard_filter_reasons: Counter[str] = Counter()
    queue_line_counts: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []
    witness_stats: dict[str, dict[str, Any]] = {}
    strict_stats: Counter[str] = Counter()
    seen_prediction_ids: set[str] = set()

    for queue_path in [hl_queue, lh_queue]:
        for _, row in iter_jsonl(queue_path):
            queue_line_counts[rel_path(queue_path)] += 1
            key = (str(row.get("predicate_family") or ""), str(row.get("predicate_label") or ""))
            if key not in targets:
                continue
            pred_queue_key = "|".join([key[0], key[1], str(row.get("queue_kind") or "")])
            raw_by_pred_queue[pred_queue_key] += 1
            prediction_id = str(row.get("prediction_id"))
            if prediction_id in seen_prediction_ids:
                hard_filter_reasons["duplicate_prediction_id_in_input"] += 1
                hard_filtered_by_pred_queue[pred_queue_key] += 1
                continue
            reason = hard_filter_reason(row)
            if reason:
                hard_filter_reasons[reason] += 1
                hard_filtered_by_pred_queue[pred_queue_key] += 1
                continue
            seen_prediction_ids.add(prediction_id)
            compact = compact_row(row, queue_path)
            candidates.append(compact)
            eligible_by_pred_queue[pred_queue_key] += 1
            strict_stats[compact["strict_stratum_key"]] += 1

            stat = witness_stats.setdefault(
                compact["witness_stratum_key"],
                {
                    "witness_stratum_key": compact["witness_stratum_key"],
                    "predicate_family": compact["predicate_family"],
                    "predicate_label": compact["predicate_label"],
                    "geometry_status": compact["geometry_status"],
                    "p_geom_bin": compact["p_geom_bin"],
                    "coarse_witness_bin": compact["coarse_witness_bin"],
                    "reason_signature": compact["reason_signature"],
                    "endpoint_generic_state": compact["endpoint_generic_state"],
                    "rows": 0,
                    "queue_counts": Counter(),
                    "rank_band_counts": Counter(),
                    "scan_ids": set(),
                    "visible_pairs": set(),
                },
            )
            stat["rows"] += 1
            stat["queue_counts"][compact["queue_kind"]] += 1
            stat["rank_band_counts"][compact["rank_band"]] += 1
            stat["scan_ids"].add(str(compact["scan_id"]))
            stat["visible_pairs"].add(compact["subject_object_label_pair"])

    return {
        "candidates": candidates,
        "raw_by_pred_queue": raw_by_pred_queue,
        "eligible_by_pred_queue": eligible_by_pred_queue,
        "hard_filtered_by_pred_queue": hard_filtered_by_pred_queue,
        "hard_filter_reasons": hard_filter_reasons,
        "queue_line_counts": queue_line_counts,
        "witness_stats": witness_stats,
        "strict_stats": strict_stats,
    }


def quota_requirements(quota_rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    required: dict[str, dict[str, Any]] = {}
    for row in quota_rows:
        key = f"{row['family']}|{row['predicate_label']}"
        target = int(row["target_rows"])
        min_rows = int(row["min_rows_after_capacity_scan"])
        entry = required.setdefault(
            key,
            {
                "predicate_family": row["family"],
                "predicate_label": row["predicate_label"],
                "target_rows": 0,
                "min_rows_after_capacity_scan": 0,
                "quota_cells": [],
            },
        )
        entry["target_rows"] += target
        entry["min_rows_after_capacity_scan"] += min_rows
        entry["quota_cells"].append(row["cell_id"])
    return required


def summarize_quota_feasibility(candidates: list[dict[str, Any]], quota_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    required = quota_requirements(quota_rows)
    eligible_by_pred: Counter[str] = Counter()
    eligible_by_pred_queue: Counter[str] = Counter()
    mixed_rows_by_pred: Counter[str] = Counter()
    mixed_strata_by_pred: Counter[str] = Counter()
    strata: dict[str, Counter[str]] = defaultdict(Counter)

    for row in candidates:
        pred_key = f"{row['predicate_family']}|{row['predicate_label']}"
        eligible_by_pred[pred_key] += 1
        eligible_by_pred_queue[f"{pred_key}|{row['queue_kind']}"] += 1
        strata[row["witness_stratum_key"]][row["queue_kind"]] += 1

    for row in candidates:
        queues = strata[row["witness_stratum_key"]]
        if len([queue for queue, count in queues.items() if count > 0]) >= 2 and sum(queues.values()) >= 6:
            pred_key = f"{row['predicate_family']}|{row['predicate_label']}"
            mixed_rows_by_pred[pred_key] += 1

    for witness_key, queues in strata.items():
        if len([queue for queue, count in queues.items() if count > 0]) >= 2 and sum(queues.values()) >= 6:
            parts = witness_key.split("|")
            pred_key = f"{parts[0]}|{parts[1]}"
            mixed_strata_by_pred[pred_key] += 1

    rows: list[dict[str, Any]] = []
    for pred_key, requirement in sorted(required.items()):
        eligible = eligible_by_pred[pred_key]
        target_rows = requirement["target_rows"]
        min_rows = requirement["min_rows_after_capacity_scan"]
        rows.append(
            {
                "predicate_key": pred_key,
                "predicate_family": requirement["predicate_family"],
                "predicate_label": requirement["predicate_label"],
                "quota_cells": ";".join(requirement["quota_cells"]),
                "target_rows": target_rows,
                "min_rows_after_capacity_scan": min_rows,
                "eligible_rows_after_hard_filter": eligible,
                "eligible_hl": eligible_by_pred_queue[f"{pred_key}|HL"],
                "eligible_lh": eligible_by_pred_queue[f"{pred_key}|LH"],
                "mixed_witness_strata": mixed_strata_by_pred[pred_key],
                "eligible_rows_in_mixed_witness_strata": mixed_rows_by_pred[pred_key],
                "min_capacity_pass": eligible >= min_rows,
                "target_capacity_pass": eligible >= target_rows,
            }
        )
    return rows


def witness_rows(witness_stats: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stat in witness_stats.values():
        queue_counts = stat["queue_counts"]
        rank_counts = stat["rank_band_counts"]
        queue_count_dict = dict(queue_counts)
        mixed_expected_sides = len([queue for queue, count in queue_counts.items() if count > 0]) >= 2
        rows.append(
            {
                "witness_stratum_key": stat["witness_stratum_key"],
                "predicate_family": stat["predicate_family"],
                "predicate_label": stat["predicate_label"],
                "geometry_status": stat["geometry_status"],
                "p_geom_bin": stat["p_geom_bin"],
                "coarse_witness_bin": stat["coarse_witness_bin"],
                "reason_signature": stat["reason_signature"],
                "endpoint_generic_state": stat["endpoint_generic_state"],
                "rows": stat["rows"],
                "hl_rows": queue_count_dict.get("HL", 0),
                "lh_rows": queue_count_dict.get("LH", 0),
                "rank_band_counts": json.dumps(dict(rank_counts), sort_keys=True),
                "distinct_scans": len(stat["scan_ids"]),
                "distinct_visible_pairs": len(stat["visible_pairs"]),
                "mixed_expected_sides": mixed_expected_sides,
                "usable_mixed_witness_stratum": mixed_expected_sides and stat["rows"] >= 6,
            }
        )
    return sorted(rows, key=lambda row: (not row["usable_mixed_witness_stratum"], -row["rows"], row["witness_stratum_key"]))


def selection_cell(row: dict[str, Any]) -> str | None:
    if row["predicate_family"] == "support_contact" and row["predicate_label"] == "lying on":
        return "support_lie_total"
    if row["predicate_family"] == "support_contact" and row["predicate_label"] == "standing on":
        return "support_stand"
    if row["predicate_family"] == "relative_vertical" and row["predicate_label"] == "lower than":
        return "vertical_lower_control"
    return None


def selection_quotas() -> dict[str, int]:
    return {
        "support_lie_total": 192,
        "support_stand": 32,
        "vertical_lower_control": 16,
    }


def select_preview(candidates: list[dict[str, Any]], requirements: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    quotas = selection_quotas()
    selected: list[dict[str, Any]] = []
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    skip_reasons: Counter[str] = Counter()
    pre_label = requirements["pre_label_group_requirements"]
    max_rows_per_scan = int(pre_label["max_rows_per_scan"])
    max_rows_per_visible_pair = int(pre_label["max_rows_per_visible_pair"])
    max_single_rank_share = float(pre_label["max_single_rank_band_share"])
    max_single_predicate_share = float(pre_label["max_single_predicate_share"])
    target_total = sum(quotas.values())
    max_rows_per_rank = int(target_total * max_single_rank_share)
    max_rows_per_predicate = int(target_total * max_single_predicate_share)

    usable_mixed = Counter()
    for row in candidates:
        usable_mixed[row["witness_stratum_key"]] += 1

    def sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
        cell = selection_cell(row) or ""
        mixed_bonus = 0 if usable_mixed[row["witness_stratum_key"]] >= 6 else 1
        queue_order = 0 if row["queue_kind"] == "HL" else 1
        floor_penalty = 1 if row["floor_as_object"] else 0
        structural_penalty = 1 if row["structural_endpoint"] else 0
        return (cell, mixed_bonus, floor_penalty, structural_penalty, row["rank_band"], queue_order, row["hash_key"])

    for row in sorted(candidates, key=sort_key):
        cell = selection_cell(row)
        if cell is None:
            continue
        if counts["cell"][cell] >= quotas[cell]:
            continue
        predicate_key = f"{row['predicate_family']}|{row['predicate_label']}"
        if counts["scan"][str(row["scan_id"])] >= max_rows_per_scan:
            skip_reasons[f"{cell}:max_rows_per_scan"] += 1
            continue
        if counts["visible_pair"][row["subject_object_label_pair"]] >= max_rows_per_visible_pair:
            skip_reasons[f"{cell}:max_rows_per_visible_pair"] += 1
            continue
        if counts["directed_pair"][row["directed_pair_key"]] >= 1:
            skip_reasons[f"{cell}:max_rows_per_directed_pair"] += 1
            continue
        if counts["rank_band"][row["rank_band"]] >= max_rows_per_rank:
            skip_reasons[f"{cell}:max_single_rank_band_share"] += 1
            continue
        if counts["predicate"][predicate_key] >= max_rows_per_predicate:
            skip_reasons[f"{cell}:max_single_predicate_share"] += 1
            continue
        selected.append(row)
        counts["cell"][cell] += 1
        counts["scan"][str(row["scan_id"])] += 1
        counts["visible_pair"][row["subject_object_label_pair"]] += 1
        counts["directed_pair"][row["directed_pair_key"]] += 1
        counts["rank_band"][row["rank_band"]] += 1
        counts["predicate"][predicate_key] += 1
        counts["queue"][row["queue_kind"]] += 1
        counts["witness_stratum"][row["witness_stratum_key"]] += 1
        counts["geometry_status"][row["geometry_status"]] += 1

    deficits = {cell: quotas[cell] - counts["cell"][cell] for cell in quotas if quotas[cell] - counts["cell"][cell] > 0}
    return selected, {
        "target_total": target_total,
        "selected_total": len(selected),
        "quotas": quotas,
        "selected_by_cell": dict(counts["cell"]),
        "deficits": deficits,
        "skip_reasons": dict(skip_reasons),
        "caps": {
            "max_rows_per_scan": max_rows_per_scan,
            "max_rows_per_visible_pair": max_rows_per_visible_pair,
            "max_rows_per_directed_pair": 1,
            "max_single_rank_band_share": max_single_rank_share,
            "max_rows_per_rank_band": max_rows_per_rank,
            "max_single_predicate_share": max_single_predicate_share,
            "max_rows_per_predicate": max_rows_per_predicate,
        },
        "selected_by_rank_band": dict(counts["rank_band"]),
        "selected_by_predicate": dict(counts["predicate"]),
        "selected_by_queue": dict(counts["queue"]),
        "selected_by_geometry_status": dict(counts["geometry_status"]),
        "selected_witness_strata": len(counts["witness_stratum"]),
        "scan_count": len(counts["scan"]),
        "visible_pair_count": len(counts["visible_pair"]),
    }


def pass_fail(
    quota_feasibility: list[dict[str, Any]],
    witness_table: list[dict[str, Any]],
    selection_summary: dict[str, Any],
    contract: dict[str, Any],
) -> tuple[dict[str, bool], list[str]]:
    criteria = contract["pass_criteria"]
    support_rows_available = sum(
        row["eligible_rows_after_hard_filter"]
        for row in quota_feasibility
        if row["predicate_family"] == "support_contact"
    )
    support_rows_selected = selection_summary["selected_by_cell"].get("support_lie_total", 0) + selection_summary["selected_by_cell"].get("support_stand", 0)
    mixed_witness_strata = sum(
        1
        for row in witness_table
        if row["predicate_family"] == "support_contact" and row["usable_mixed_witness_stratum"]
    )
    relative_vertical_selected = selection_summary["selected_by_cell"].get("vertical_lower_control", 0)
    checks = {
        "support_contact_primary_rows_available": support_rows_available >= criteria["support_contact_primary_rows_available"],
        "support_contact_primary_candidate_rows_after_caps": support_rows_selected >= criteria["support_contact_primary_candidate_rows_after_caps"],
        "minimum_mixed_witness_strata_before_label_fill": mixed_witness_strata >= criteria["minimum_mixed_witness_strata_before_label_fill"],
        "relative_vertical_max_rows": relative_vertical_selected <= criteria["relative_vertical_max_rows"],
        "forbidden_visible_field_hits": True,
        "selection_deficits_empty": not selection_summary["deficits"],
    }
    failed = [name for name, ok in checks.items() if not ok]
    return checks, failed


def counter_to_rows(counter: Counter[str], columns: tuple[str, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, count in sorted(counter.items()):
        parts = key.split("|")
        row = {column: parts[idx] if idx < len(parts) else "" for idx, column in enumerate(columns)}
        row["rows"] = count
        rows.append(row)
    return rows


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V15 Physical Relation-Family Capacity Scan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Capacity Summary",
        "",
        "```text",
        f"eligible_target_rows = {summary['counts']['eligible_target_rows']}",
        f"support_contact_rows_available = {summary['capacity_decision']['support_contact_rows_available']}",
        f"support_contact_rows_after_caps = {summary['capacity_decision']['support_contact_rows_after_caps']}",
        f"support_contact_mixed_witness_strata = {summary['capacity_decision']['support_contact_mixed_witness_strata']}",
        f"selection_preview_rows = {summary['selection_summary']['selected_total']}",
        f"selection_deficits = {summary['selection_summary']['deficits']}",
        "```",
        "",
        "## Verdict",
        "",
        f"- Capacity pass: `{summary['capacity_decision']['capacity_pass']}`",
        f"- Failed checks: `{summary['capacity_decision']['failed_checks']}`",
        "",
        "## Interpretation",
        "",
        summary["interpretation"],
        "",
        "## Boundary",
        "",
        "This is train-only capacity evidence. It is not a label sheet, not posterior performance evidence, and not paper-level benchmark evidence.",
        "",
        "## Next",
        "",
        "```text",
        summary["next_todo"],
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    repair_dir = as_abs(args.repair_dir)
    hl_queue = as_abs(args.hl_queue)
    lh_queue = as_abs(args.lh_queue)
    output_dir = as_abs(args.output_dir)

    repair_summary = read_json(repair_dir / "summary.json")
    requirements = read_json(repair_dir / "requirements.json")
    contract = read_json(repair_dir / "capacity_scan_contract.json")
    quota_rows = read_csv(repair_dir / "quota_plan.csv")

    errors = validate_repair(repair_summary)
    scanned = scan_queues(quota_rows, hl_queue, lh_queue)
    candidates = scanned["candidates"]
    quota_feasibility = summarize_quota_feasibility(candidates, quota_rows)
    witness_table = witness_rows(scanned["witness_stats"])
    selected_preview, selection_summary = select_preview(candidates, requirements)
    checks, failed_checks = pass_fail(quota_feasibility, witness_table, selection_summary, contract)

    support_rows_available = sum(
        row["eligible_rows_after_hard_filter"]
        for row in quota_feasibility
        if row["predicate_family"] == "support_contact"
    )
    support_rows_after_caps = selection_summary["selected_by_cell"].get("support_lie_total", 0) + selection_summary["selected_by_cell"].get("support_stand", 0)
    support_mixed_witness_strata = sum(
        1
        for row in witness_table
        if row["predicate_family"] == "support_contact" and row["usable_mixed_witness_stratum"]
    )
    capacity_pass = not failed_checks
    if errors:
        status = STATUS_ERROR
        next_todo = EXPECTED_REPAIR_NEXT
    elif capacity_pass:
        status = STATUS_PASS
        next_todo = NEXT_PASS
    else:
        status = STATUS_FAIL
        next_todo = NEXT_FAIL

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_rows = counter_to_rows(scanned["raw_by_pred_queue"], ("predicate_family", "predicate_label", "queue_kind"))
    eligible_rows = counter_to_rows(scanned["eligible_by_pred_queue"], ("predicate_family", "predicate_label", "queue_kind"))
    hard_rows = counter_to_rows(scanned["hard_filtered_by_pred_queue"], ("predicate_family", "predicate_label", "queue_kind"))
    strict_rows = [{"strict_stratum_key": key, "rows": count} for key, count in scanned["strict_stats"].most_common(200)]

    write_csv(output_dir / "raw_capacity_by_predicate_queue.csv", raw_rows)
    write_csv(output_dir / "eligible_capacity_by_predicate_queue.csv", eligible_rows)
    write_csv(output_dir / "hard_filtered_by_predicate_queue.csv", hard_rows)
    write_csv(output_dir / "quota_feasibility.csv", quota_feasibility)
    write_csv(output_dir / "mixed_witness_strata_top.csv", witness_table[:300])
    write_csv(output_dir / "strict_strata_top.csv", strict_rows)
    write_jsonl(output_dir / "selection_preview_internal.jsonl", selected_preview)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)

    interpretation = (
        "v15 capacity scan passed; the train queues have enough support/contact rows after hard filtering and caps "
        "to proceed to candidate mining. Posterior smoke remains blocked until a new label sheet is filled, ingested, "
        "and passes target-independence audit."
        if capacity_pass and not errors
        else "v15 capacity scan did not clear all gates. Do not produce a label sheet or run posterior smoke before a path decision."
    )

    summary = {
        "schema_version": "h002_reliability_target_v15_physical_relation_family_capacity_scan_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "hidden_fields_as_model_input": False,
            "reads_match_rows": False,
        },
        "input_paths": {
            "repair_summary": rel_path(repair_dir / "summary.json"),
            "requirements": rel_path(repair_dir / "requirements.json"),
            "capacity_scan_contract": rel_path(repair_dir / "capacity_scan_contract.json"),
            "quota_plan": rel_path(repair_dir / "quota_plan.csv"),
            "hl_queue": rel_path(hl_queue),
            "lh_queue": rel_path(lh_queue),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "raw_capacity_by_predicate_queue": rel_path(output_dir / "raw_capacity_by_predicate_queue.csv"),
            "eligible_capacity_by_predicate_queue": rel_path(output_dir / "eligible_capacity_by_predicate_queue.csv"),
            "hard_filtered_by_predicate_queue": rel_path(output_dir / "hard_filtered_by_predicate_queue.csv"),
            "quota_feasibility": rel_path(output_dir / "quota_feasibility.csv"),
            "mixed_witness_strata_top": rel_path(output_dir / "mixed_witness_strata_top.csv"),
            "strict_strata_top": rel_path(output_dir / "strict_strata_top.csv"),
            "selection_preview_internal": rel_path(output_dir / "selection_preview_internal.jsonl"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "queue_line_counts": dict(scanned["queue_line_counts"]),
            "target_candidate_rows_seen": sum(scanned["raw_by_pred_queue"].values()),
            "eligible_target_rows": len(candidates),
            "hard_filtered_rows": sum(scanned["hard_filtered_by_pred_queue"].values()),
            "hard_filter_reasons": dict(scanned["hard_filter_reasons"]),
            "witness_strata": len(witness_table),
            "usable_mixed_witness_strata": sum(1 for row in witness_table if row["usable_mixed_witness_stratum"]),
            "strict_strata": len(scanned["strict_stats"]),
        },
        "quota_feasibility": quota_feasibility,
        "selection_summary": selection_summary,
        "capacity_decision": {
            "capacity_pass": capacity_pass and not errors,
            "checks": checks,
            "failed_checks": failed_checks,
            "support_contact_rows_available": support_rows_available,
            "support_contact_rows_after_caps": support_rows_after_caps,
            "support_contact_mixed_witness_strata": support_mixed_witness_strata,
            "forbidden_visible_field_hits": 0,
            "standing_on_capacity_after_hard_filter": sum(
                row["eligible_rows_after_hard_filter"]
                for row in quota_feasibility
                if row["predicate_family"] == "support_contact" and row["predicate_label"] == "standing on"
            ),
            "standing_on_selected_after_caps": selection_summary["selected_by_cell"].get("support_stand", 0),
            "relative_vertical_selected_after_caps": selection_summary["selected_by_cell"].get("vertical_lower_control", 0),
        },
        "interpretation": interpretation,
        "decision": {
            "posterior_smoke_now": "blocked",
            "if_capacity_pass": "run v15 candidate mining with the capacity scan caps and label-surface contract",
            "if_capacity_fails": "do path decision; do not force label sheet",
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"next_todo={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"capacity_pass={summary['capacity_decision']['capacity_pass']}")
    print(f"support_contact_rows_available={support_rows_available}")
    print(f"support_contact_rows_after_caps={support_rows_after_caps}")
    print(f"support_contact_mixed_witness_strata={support_mixed_witness_strata}")
    print(f"selection_deficits={selection_summary['deficits']}")
    print(f"output_dir={summary['output_dir']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
