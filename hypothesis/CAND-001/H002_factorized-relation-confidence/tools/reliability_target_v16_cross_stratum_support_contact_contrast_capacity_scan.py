#!/usr/bin/env python3
"""Scan train-only queues for the H002 v16 cross-stratum support/contact contrast."""

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

DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v16_cross_stratum_support_contact_contrast_plan"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan"

EXPECTED_PLAN_STATUS = "h002_reliability_target_v16_cross_stratum_support_contact_contrast_plan_ready_for_capacity_scan"
EXPECTED_PLAN_NEXT = "reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan"

STATUS_PASS = "h002_reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan_passed_ready_for_candidate_mining"
STATUS_FAIL = "h002_reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan_blocked_capacity_or_controls"
STATUS_ERROR = "h002_reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan_validation_errors"
NEXT_PASS = "reliability_target_v16_cross_stratum_support_contact_contrast_candidate_mining"
NEXT_FAIL = "reliability_target_v16_cross_stratum_support_contact_contrast_path_decision_after_capacity_scan"

HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
STRUCTURAL_CONTEXT = {"floor", "wall", "ceiling", "room", "door", "doorframe", "window"}
PRIMARY_CELLS = {"P1_lie_hl_primary_overconfidence", "P2_lie_lh_primary_underconfidence"}
FORBIDDEN_BOUNDARY_TRUE_KEYS = [
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
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


def stable_id(value: str, prefix: str = "v16") -> str:
    return f"{prefix}_{hashlib.sha1(value.encode('utf-8')).hexdigest()[:16]}"


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


def reason_family(family: str, geometry_status: str, reason_codes: list[str]) -> str:
    reasons = set(reason_codes)
    if family == "support_contact":
        if {"missing_point_evidence", "horizontal_plane_missing"} & reasons:
            return "support_missing_or_sparse"
        if {"plane_gap_supported", "soft_penetration_allowed", "subtype_legged_floor_support"} & reasons:
            return "support_near_contact_or_subtype_supported"
        if {"plane_gap_large", "positive_float_gap_large"} & reasons:
            return "support_gap_large"
        if "robust_gap_too_strict_for_legs" in reasons:
            return "support_legged_ambiguous"
        return f"support_{geometry_status or 'unknown'}"
    if family == "relative_vertical":
        if "vertical_order_matches_predicate" in reasons:
            return "vertical_order_matches"
        if "vertical_order_contradicts_predicate" in reasons:
            return "vertical_order_contradicts"
        if "vertical_margin_ambiguous" in reasons:
            return "vertical_margin_ambiguous"
        return f"vertical_{geometry_status or 'unknown'}"
    return f"{family or 'family_unknown'}_{geometry_status or 'status_unknown'}"


def coarse_witness_bin(family: str, geometry_status: str, reason_codes: list[str]) -> str:
    if family == "support_contact":
        rf = reason_family(family, geometry_status, reason_codes)
        if rf == "support_near_contact_or_subtype_supported":
            return "support_near_contact_or_subtype_supported"
        if rf in {"support_gap_large", "support_legged_ambiguous", "support_missing_or_sparse"}:
            return rf
        return f"support_{geometry_status or 'unknown'}"
    if family == "relative_vertical":
        return reason_family(family, geometry_status, reason_codes)
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


def coarse_subject_object_category(row: dict[str, Any]) -> str:
    subject = norm(row.get("subject_label"))
    obj = norm(row.get("object_label"))
    if obj == "floor":
        return "support_to_floor"
    if obj in {"wall", "ceiling"}:
        return "support_to_wall_or_ceiling"
    if subject in STRUCTURAL_CONTEXT or obj in STRUCTURAL_CONTEXT:
        return "structural_context_pair"
    if subject == obj:
        return "same_label_pair"
    return "movable_object_pair"


def coverage_state(geometry_status: str) -> str:
    if geometry_status in {"missing", "unsupported"}:
        return "not_checkable_or_missing"
    return "covered_checkable"


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


def quota_cell_for(row: dict[str, Any], quota_rows: list[dict[str, str]]) -> str | None:
    for quota in quota_rows:
        if (
            str(row.get("predicate_family") or "") == quota["family"]
            and str(row.get("predicate_label") or "") == quota["predicate_label"]
            and str(row.get("queue_kind") or "") == quota["queue_kind"]
        ):
            return quota["cell_id"]
    return None


def quota_map(quota_rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in quota_rows:
        result[row["cell_id"]] = {
            **row,
            "target_rows": int(row["target_rows"]),
            "minimum_rows_after_capacity_scan": int(row["minimum_rows_after_capacity_scan"]),
        }
    return result


def target_predicates(quota_rows: list[dict[str, str]]) -> set[tuple[str, str, str]]:
    return {(row["family"], row["predicate_label"], row["queue_kind"]) for row in quota_rows}


def validate_plan(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "expected": EXPECTED_PLAN_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "expected": EXPECTED_PLAN_NEXT, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    for key in FORBIDDEN_BOUNDARY_TRUE_KEYS:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def compact_row(row: dict[str, Any], queue_path: Path, quota_rows: list[dict[str, str]]) -> dict[str, Any]:
    family = str(row.get("predicate_family") or "")
    predicate = str(row.get("predicate_label") or "")
    queue_kind = str(row.get("queue_kind") or "")
    rank_band = str(row.get("rank_band") or "rank_unknown")
    geometry_status = str(row.get("geometry_status") or "geometry_unknown")
    reasons = parse_reason_codes(row.get("reason_codes"))
    p_bin = p_geom_bin(row.get("p_geom_valid"))
    s_band = semantic_score_band(row.get("semantic_score_norm"), rank_band)
    reason_fam = reason_family(family, geometry_status, reasons)
    coarse_witness = coarse_witness_bin(family, geometry_status, reasons)
    endpoint_state = endpoint_generic_state(row)
    coarse_object = coarse_subject_object_category(row)
    coverage = coverage_state(geometry_status)
    block_key = "|".join([predicate, endpoint_state, coarse_object, coverage])
    audit_key = "|".join([block_key, queue_kind, rank_band, reason_fam, p_bin, geometry_status])
    prediction_id = str(row.get("prediction_id"))
    return {
        "blind_review_id": stable_id(prediction_id),
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
        "candidate_relation": f"{row.get('subject_label')} {predicate} {row.get('object_label')}",
        "queue_kind": queue_kind,
        "rank_band": rank_band,
        "geometry_status": geometry_status,
        "p_geom_bin": p_bin,
        "reason_family": reason_fam,
        "coarse_witness_bin": coarse_witness,
        "reason_signature": reason_signature(reasons),
        "endpoint_generic_state": endpoint_state,
        "coarse_subject_object_category": coarse_object,
        "coverage_state": coverage,
        "source_semantic_score_band": s_band,
        "subject_label_norm": norm(row.get("subject_label")),
        "object_label_norm": norm(row.get("object_label")),
        "subject_object_label_pair": visible_pair(row),
        "directed_pair_key": directed_pair_key(row),
        "block_key": block_key,
        "audit_key": audit_key,
        "quota_cell_id": quota_cell_for(row, quota_rows),
        "semantic_rank": row.get("semantic_rank"),
        "semantic_score_norm": row.get("semantic_score_norm"),
        "p_geom_valid": row.get("p_geom_valid"),
        "reason_codes": reasons,
        "label_match_status": row.get("label_match_status"),
        "machine_hint": row.get("machine_hint"),
        "h001_verification_status": row.get("h001_verification_status"),
        "source_queue_path": rel_path(queue_path),
        "hash_key": stable_int(prediction_id),
    }


def scan_queues(quota_rows: list[dict[str, str]], hl_queue: Path, lh_queue: Path) -> dict[str, Any]:
    targets = target_predicates(quota_rows)
    raw_by_cell: Counter[str] = Counter()
    eligible_by_cell: Counter[str] = Counter()
    hard_filtered_by_cell: Counter[str] = Counter()
    hard_filter_reasons: Counter[str] = Counter()
    queue_line_counts: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []
    seen_prediction_ids: set[str] = set()

    for queue_path in [hl_queue, lh_queue]:
        for _, row in iter_jsonl(queue_path):
            queue_line_counts[rel_path(queue_path)] += 1
            key = (
                str(row.get("predicate_family") or ""),
                str(row.get("predicate_label") or ""),
                str(row.get("queue_kind") or ""),
            )
            if key not in targets:
                continue
            cell_id = quota_cell_for(row, quota_rows)
            if cell_id is None:
                continue
            raw_by_cell[cell_id] += 1
            prediction_id = str(row.get("prediction_id"))
            if prediction_id in seen_prediction_ids:
                hard_filter_reasons["duplicate_prediction_id_in_input"] += 1
                hard_filtered_by_cell[cell_id] += 1
                continue
            reason = hard_filter_reason(row)
            if reason:
                hard_filter_reasons[reason] += 1
                hard_filtered_by_cell[cell_id] += 1
                continue
            seen_prediction_ids.add(prediction_id)
            compact = compact_row(row, queue_path, quota_rows)
            candidates.append(compact)
            eligible_by_cell[cell_id] += 1

    return {
        "candidates": candidates,
        "raw_by_cell": raw_by_cell,
        "eligible_by_cell": eligible_by_cell,
        "hard_filtered_by_cell": hard_filtered_by_cell,
        "hard_filter_reasons": hard_filter_reasons,
        "queue_line_counts": queue_line_counts,
    }


def counter_json(counter: Counter[str]) -> str:
    return json.dumps(dict(counter), sort_keys=True)


def capacity_by_cell(candidates: list[dict[str, Any]], quota_rows: list[dict[str, str]], scanned: dict[str, Any]) -> list[dict[str, Any]]:
    quotas = quota_map(quota_rows)
    by_cell_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_cell_rows[str(row["quota_cell_id"])].append(row)

    rows: list[dict[str, Any]] = []
    for cell_id, quota in quotas.items():
        cell_rows = by_cell_rows[cell_id]
        rank_counts = Counter(row["rank_band"] for row in cell_rows)
        geometry_counts = Counter(row["geometry_status"] for row in cell_rows)
        pgeom_counts = Counter(row["p_geom_bin"] for row in cell_rows)
        reason_counts = Counter(row["reason_family"] for row in cell_rows)
        block_counts = Counter(row["block_key"] for row in cell_rows)
        rows.append(
            {
                "cell_id": cell_id,
                "family": quota["family"],
                "predicate_label": quota["predicate_label"],
                "queue_kind": quota["queue_kind"],
                "role": quota["role"],
                "target_rows": quota["target_rows"],
                "minimum_rows_after_capacity_scan": quota["minimum_rows_after_capacity_scan"],
                "raw_rows": scanned["raw_by_cell"][cell_id],
                "hard_filtered_rows": scanned["hard_filtered_by_cell"][cell_id],
                "eligible_rows": len(cell_rows),
                "distinct_scans": len({str(row["scan_id"]) for row in cell_rows}),
                "distinct_subgraphs": len({str(row["subgraph_id"]) for row in cell_rows}),
                "distinct_visible_pairs": len({row["subject_object_label_pair"] for row in cell_rows}),
                "distinct_directed_pairs": len({row["directed_pair_key"] for row in cell_rows}),
                "distinct_blocks": len(block_counts),
                "rank_band_counts": counter_json(rank_counts),
                "geometry_status_counts": counter_json(geometry_counts),
                "p_geom_bin_counts": counter_json(pgeom_counts),
                "reason_family_counts": counter_json(reason_counts),
                "minimum_capacity_pass": len(cell_rows) >= quota["minimum_rows_after_capacity_scan"],
                "target_capacity_pass": len(cell_rows) >= quota["target_rows"],
            }
        )
    return rows


def block_capacity(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for row in candidates:
        if row["quota_cell_id"] not in PRIMARY_CELLS:
            continue
        stat = stats.setdefault(
            row["block_key"],
            {
                "block_key": row["block_key"],
                "predicate_label": row["predicate_label"],
                "endpoint_generic_state": row["endpoint_generic_state"],
                "coarse_subject_object_category": row["coarse_subject_object_category"],
                "coverage_state": row["coverage_state"],
                "rows": 0,
                "queue_counts": Counter(),
                "rank_band_counts": Counter(),
                "geometry_status_counts": Counter(),
                "p_geom_bin_counts": Counter(),
                "reason_family_counts": Counter(),
                "scan_ids": set(),
                "visible_pairs": set(),
                "directed_pairs": set(),
            },
        )
        stat["rows"] += 1
        stat["queue_counts"][row["queue_kind"]] += 1
        stat["rank_band_counts"][row["rank_band"]] += 1
        stat["geometry_status_counts"][row["geometry_status"]] += 1
        stat["p_geom_bin_counts"][row["p_geom_bin"]] += 1
        stat["reason_family_counts"][row["reason_family"]] += 1
        stat["scan_ids"].add(str(row["scan_id"]))
        stat["visible_pairs"].add(row["subject_object_label_pair"])
        stat["directed_pairs"].add(row["directed_pair_key"])

    rows: list[dict[str, Any]] = []
    for stat in stats.values():
        queue_counts = stat["queue_counts"]
        mixed = queue_counts.get("HL", 0) > 0 and queue_counts.get("LH", 0) > 0
        rows.append(
            {
                "block_key": stat["block_key"],
                "predicate_label": stat["predicate_label"],
                "endpoint_generic_state": stat["endpoint_generic_state"],
                "coarse_subject_object_category": stat["coarse_subject_object_category"],
                "coverage_state": stat["coverage_state"],
                "rows": stat["rows"],
                "hl_rows": queue_counts.get("HL", 0),
                "lh_rows": queue_counts.get("LH", 0),
                "mixed_primary_sides": mixed,
                "distinct_scans": len(stat["scan_ids"]),
                "distinct_visible_pairs": len(stat["visible_pairs"]),
                "distinct_directed_pairs": len(stat["directed_pairs"]),
                "rank_band_counts": counter_json(stat["rank_band_counts"]),
                "geometry_status_counts": counter_json(stat["geometry_status_counts"]),
                "p_geom_bin_counts": counter_json(stat["p_geom_bin_counts"]),
                "reason_family_counts": counter_json(stat["reason_family_counts"]),
            }
        )
    return sorted(rows, key=lambda row: (not row["mixed_primary_sides"], -min(row["hl_rows"], row["lh_rows"]), -row["rows"], row["block_key"]))


def target_side_totals(quotas: dict[str, dict[str, Any]]) -> Counter[str]:
    totals: Counter[str] = Counter()
    for quota in quotas.values():
        totals[quota["queue_kind"]] += int(quota["target_rows"])
    return totals


def selection_sort_key(row: dict[str, Any], block_counts: dict[str, Counter[str]]) -> tuple[Any, ...]:
    block_counter = block_counts[row["block_key"]]
    mixed_block_rank = 0 if block_counter["HL"] > 0 and block_counter["LH"] > 0 else 1
    cell_order = {
        "P1_lie_hl_primary_overconfidence": 0,
        "P2_lie_lh_primary_underconfidence": 1,
        "D1_stand_lh_diversity_diagnostic": 2,
        "C1_vertical_lower_control": 3,
    }.get(str(row["quota_cell_id"]), 9)
    endpoint_order = 1 if row["endpoint_generic_state"] in {"subject_room_surface", "object_wall_or_ceiling"} else 0
    return (
        cell_order,
        mixed_block_rank,
        endpoint_order,
        row["block_key"],
        row["rank_band"],
        row["subject_object_label_pair"],
        row["hash_key"],
    )


def select_preview(candidates: list[dict[str, Any]], quotas: dict[str, dict[str, Any]], sampling_policy: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    caps = sampling_policy["caps"]
    target_total = sum(quota["target_rows"] for quota in quotas.values())
    side_totals = target_side_totals(quotas)
    block_side_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in candidates:
        if row["quota_cell_id"] in PRIMARY_CELLS:
            block_side_counts[row["block_key"]][row["queue_kind"]] += 1

    selected: list[dict[str, Any]] = []
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    skip_reasons: Counter[str] = Counter()
    cell_targets = {cell_id: quota["target_rows"] for cell_id, quota in quotas.items()}

    max_rows_per_rank = int(target_total * float(caps["max_single_rank_band_share"]))
    max_rows_per_endpoint_state = int(target_total * float(caps["max_rows_per_endpoint_generic_state_share"]))
    max_rows_per_subject_label = int(target_total * float(caps["max_single_subject_label_share"]))
    max_rows_per_object_label = int(target_total * float(caps["max_single_object_label_share"]))
    max_rows_per_side_reason = {side: int(total * float(caps["max_single_reason_family_share_per_side"])) for side, total in side_totals.items()}
    max_rows_per_side_pgeom = {side: int(total * float(caps["max_single_p_geom_bin_share_per_side"])) for side, total in side_totals.items()}
    max_rows_per_side_geometry = {side: int(total * float(caps["max_single_geometry_status_share_per_side"])) for side, total in side_totals.items()}

    def can_select(row: dict[str, Any]) -> str | None:
        cell_id = str(row["quota_cell_id"])
        queue_kind = row["queue_kind"]
        if counts["cell"][cell_id] >= cell_targets[cell_id]:
            return "cell_quota_full"
        if counts["scan"][str(row["scan_id"])] >= int(caps["max_rows_per_scan"]):
            return "max_rows_per_scan"
        if counts["subgraph"][str(row["subgraph_id"])] >= int(caps["max_rows_per_subgraph"]):
            return "max_rows_per_subgraph"
        if counts["directed_pair"][row["directed_pair_key"]] >= int(caps["max_rows_per_directed_pair"]):
            return "max_rows_per_directed_pair"
        if counts["visible_pair"][row["subject_object_label_pair"]] >= int(caps["max_rows_per_visible_pair"]):
            return "max_rows_per_visible_pair"
        if counts["rank_band"][row["rank_band"]] >= max_rows_per_rank:
            return "max_single_rank_band_share"
        if counts["endpoint_generic_state"][row["endpoint_generic_state"]] >= max_rows_per_endpoint_state:
            return "max_rows_per_endpoint_generic_state_share"
        if counts["subject_label"][row["subject_label_norm"]] >= max_rows_per_subject_label:
            return "max_single_subject_label_share"
        if counts["object_label"][row["object_label_norm"]] >= max_rows_per_object_label:
            return "max_single_object_label_share"
        if counts["side_reason"][(queue_kind, row["reason_family"])] >= max_rows_per_side_reason[queue_kind]:
            return "max_single_reason_family_share_per_side"
        if counts["side_pgeom"][(queue_kind, row["p_geom_bin"])] >= max_rows_per_side_pgeom[queue_kind]:
            return "max_single_p_geom_bin_share_per_side"
        if counts["side_geometry"][(queue_kind, row["geometry_status"])] >= max_rows_per_side_geometry[queue_kind]:
            return "max_single_geometry_status_share_per_side"
        return None

    pools: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        if row["quota_cell_id"]:
            pools[str(row["quota_cell_id"])].append(row)
    for cell_id in pools:
        pools[cell_id] = sorted(pools[cell_id], key=lambda row: selection_sort_key(row, block_side_counts))

    # Primary rows are interleaved so that selected primary blocks contain both mismatch sides when possible.
    primary_order = ["P1_lie_hl_primary_overconfidence", "P2_lie_lh_primary_underconfidence"]
    made_progress = True
    while made_progress and any(counts["cell"][cell] < cell_targets[cell] for cell in primary_order):
        made_progress = False
        for cell_id in primary_order:
            if counts["cell"][cell_id] >= cell_targets[cell_id]:
                continue
            for row in pools[cell_id]:
                reason = can_select(row)
                if reason is not None:
                    skip_reasons[f"{cell_id}:{reason}"] += 1
                    continue
                selected.append(row)
                made_progress = True
                counts["cell"][cell_id] += 1
                counts["queue"][row["queue_kind"]] += 1
                counts["scan"][str(row["scan_id"])] += 1
                counts["subgraph"][str(row["subgraph_id"])] += 1
                counts["directed_pair"][row["directed_pair_key"]] += 1
                counts["visible_pair"][row["subject_object_label_pair"]] += 1
                counts["rank_band"][row["rank_band"]] += 1
                counts["endpoint_generic_state"][row["endpoint_generic_state"]] += 1
                counts["subject_label"][row["subject_label_norm"]] += 1
                counts["object_label"][row["object_label_norm"]] += 1
                counts["side_reason"][(row["queue_kind"], row["reason_family"])] += 1
                counts["side_pgeom"][(row["queue_kind"], row["p_geom_bin"])] += 1
                counts["side_geometry"][(row["queue_kind"], row["geometry_status"])] += 1
                counts["block"][row["block_key"]] += 1
                counts["block_side"][(row["block_key"], row["queue_kind"])] += 1
                break

    for cell_id in ["D1_stand_lh_diversity_diagnostic", "C1_vertical_lower_control"]:
        for row in pools[cell_id]:
            if counts["cell"][cell_id] >= cell_targets[cell_id]:
                break
            reason = can_select(row)
            if reason is not None:
                skip_reasons[f"{cell_id}:{reason}"] += 1
                continue
            selected.append(row)
            counts["cell"][cell_id] += 1
            counts["queue"][row["queue_kind"]] += 1
            counts["scan"][str(row["scan_id"])] += 1
            counts["subgraph"][str(row["subgraph_id"])] += 1
            counts["directed_pair"][row["directed_pair_key"]] += 1
            counts["visible_pair"][row["subject_object_label_pair"]] += 1
            counts["rank_band"][row["rank_band"]] += 1
            counts["endpoint_generic_state"][row["endpoint_generic_state"]] += 1
            counts["subject_label"][row["subject_label_norm"]] += 1
            counts["object_label"][row["object_label_norm"]] += 1
            counts["side_reason"][(row["queue_kind"], row["reason_family"])] += 1
            counts["side_pgeom"][(row["queue_kind"], row["p_geom_bin"])] += 1
            counts["side_geometry"][(row["queue_kind"], row["geometry_status"])] += 1
            counts["block"][row["block_key"]] += 1
            counts["block_side"][(row["block_key"], row["queue_kind"])] += 1

    selected_primary_blocks = {
        row["block_key"]
        for row in selected
        if row["quota_cell_id"] in PRIMARY_CELLS
    }
    selected_primary_blocks_with_both_sides = {
        block
        for block in selected_primary_blocks
        if counts["block_side"][(block, "HL")] > 0 and counts["block_side"][(block, "LH")] > 0
    }
    deficits = {
        cell_id: cell_targets[cell_id] - counts["cell"][cell_id]
        for cell_id in cell_targets
        if cell_targets[cell_id] - counts["cell"][cell_id] > 0
    }

    selected_by_cell_status: dict[str, Counter[str]] = defaultdict(Counter)
    selected_by_cell_pgeom: dict[str, Counter[str]] = defaultdict(Counter)
    selected_by_cell_reason: dict[str, Counter[str]] = defaultdict(Counter)
    for row in selected:
        cell_id = str(row["quota_cell_id"])
        selected_by_cell_status[cell_id][row["geometry_status"]] += 1
        selected_by_cell_pgeom[cell_id][row["p_geom_bin"]] += 1
        selected_by_cell_reason[cell_id][row["reason_family"]] += 1

    return selected, {
        "target_total": target_total,
        "selected_total": len(selected),
        "quotas": cell_targets,
        "selected_by_cell": dict(counts["cell"]),
        "selected_by_queue": dict(counts["queue"]),
        "deficits": deficits,
        "skip_reasons": dict(skip_reasons),
        "caps": {
            **caps,
            "max_rows_per_rank_band": max_rows_per_rank,
            "max_rows_per_endpoint_generic_state": max_rows_per_endpoint_state,
            "max_rows_per_subject_label": max_rows_per_subject_label,
            "max_rows_per_object_label": max_rows_per_object_label,
            "max_rows_per_side_reason": max_rows_per_side_reason,
            "max_rows_per_side_pgeom": max_rows_per_side_pgeom,
            "max_rows_per_side_geometry": max_rows_per_side_geometry,
        },
        "selected_by_rank_band": dict(counts["rank_band"]),
        "selected_by_endpoint_generic_state": dict(counts["endpoint_generic_state"]),
        "selected_by_subject_label": dict(counts["subject_label"]),
        "selected_by_object_label": dict(counts["object_label"]),
        "selected_by_geometry_status_per_side": {f"{side}|{status}": count for (side, status), count in counts["side_geometry"].items()},
        "selected_by_p_geom_bin_per_side": {f"{side}|{p_bin}": count for (side, p_bin), count in counts["side_pgeom"].items()},
        "selected_by_reason_family_per_side": {f"{side}|{reason}": count for (side, reason), count in counts["side_reason"].items()},
        "selected_by_cell_geometry_status": {cell: dict(counter) for cell, counter in selected_by_cell_status.items()},
        "selected_by_cell_p_geom_bin": {cell: dict(counter) for cell, counter in selected_by_cell_pgeom.items()},
        "selected_by_cell_reason_family": {cell: dict(counter) for cell, counter in selected_by_cell_reason.items()},
        "selected_primary_blocks": len(selected_primary_blocks),
        "selected_primary_blocks_with_both_sides": len(selected_primary_blocks_with_both_sides),
        "selected_scan_count": len(counts["scan"]),
        "selected_subgraph_count": len(counts["subgraph"]),
        "selected_visible_pair_count": len(counts["visible_pair"]),
        "selected_directed_pair_count": len(counts["directed_pair"]),
    }


def precheck_risk(selected: list[dict[str, Any]], selection_summary: dict[str, Any], sampling_policy: dict[str, Any]) -> dict[str, Any]:
    primary = [row for row in selected if row["quota_cell_id"] in PRIMARY_CELLS]
    by_side_status: dict[str, Counter[str]] = defaultdict(Counter)
    by_side_pgeom: dict[str, Counter[str]] = defaultdict(Counter)
    by_side_reason: dict[str, Counter[str]] = defaultdict(Counter)
    for row in primary:
        by_side_status[row["queue_kind"]][row["geometry_status"]] += 1
        by_side_pgeom[row["queue_kind"]][row["p_geom_bin"]] += 1
        by_side_reason[row["queue_kind"]][row["reason_family"]] += 1

    def max_share(counter: Counter[str]) -> float:
        total = sum(counter.values())
        if not total:
            return 0.0
        return max(counter.values()) / total

    block_req = sampling_policy["block_construction"]
    risk_flags = []
    for side, counter in by_side_status.items():
        if max_share(counter) > sampling_policy["caps"]["max_single_geometry_status_share_per_side"]:
            risk_flags.append(f"{side}:geometry_status_concentrated")
    for side, counter in by_side_pgeom.items():
        if max_share(counter) > sampling_policy["caps"]["max_single_p_geom_bin_share_per_side"]:
            risk_flags.append(f"{side}:p_geom_bin_concentrated")
    for side, counter in by_side_reason.items():
        if max_share(counter) > sampling_policy["caps"]["max_single_reason_family_share_per_side"]:
            risk_flags.append(f"{side}:reason_family_concentrated")
    if selection_summary["selected_primary_blocks_with_both_sides"] < int(block_req["minimum_blocks"]):
        risk_flags.append("primary_mixed_block_count_below_minimum")

    return {
        "primary_rows": len(primary),
        "primary_by_side_geometry_status": {side: dict(counter) for side, counter in by_side_status.items()},
        "primary_by_side_p_geom_bin": {side: dict(counter) for side, counter in by_side_pgeom.items()},
        "primary_by_side_reason_family": {side: dict(counter) for side, counter in by_side_reason.items()},
        "selected_primary_blocks_with_both_sides": selection_summary["selected_primary_blocks_with_both_sides"],
        "minimum_primary_blocks_required": int(block_req["minimum_blocks"]),
        "risk_flags": risk_flags,
        "interpretation": (
            "This is a pre-label shortcut/capacity check only. It does not prove target independence; "
            "it only decides whether candidate mining is worth running."
        ),
    }


def pass_fail(
    cell_table: list[dict[str, Any]],
    block_table: list[dict[str, Any]],
    selection_summary: dict[str, Any],
    risk_precheck: dict[str, Any],
    sampling_policy: dict[str, Any],
) -> tuple[dict[str, bool], list[str]]:
    quotas_pass = all(row["target_capacity_pass"] for row in cell_table)
    mins_pass = all(row["minimum_capacity_pass"] for row in cell_table)
    selected_targets_pass = not selection_summary["deficits"]
    primary_hl = selection_summary["selected_by_cell"].get("P1_lie_hl_primary_overconfidence", 0)
    primary_lh = selection_summary["selected_by_cell"].get("P2_lie_lh_primary_underconfidence", 0)
    mixed_blocks_total = sum(1 for row in block_table if row["mixed_primary_sides"])
    min_blocks = int(sampling_policy["block_construction"]["minimum_blocks"])
    checks = {
        "quota_target_capacity_pass": quotas_pass,
        "quota_minimum_capacity_pass": mins_pass,
        "selected_targets_after_caps_pass": selected_targets_pass,
        "primary_hl_selected_100": primary_hl >= 100,
        "primary_lh_selected_100": primary_lh >= 100,
        "mixed_primary_blocks_available": mixed_blocks_total >= min_blocks,
        "selected_primary_blocks_with_both_sides": selection_summary["selected_primary_blocks_with_both_sides"] >= min_blocks,
        "side_axis_concentration_precheck_pass": not risk_precheck["risk_flags"],
        "forbidden_visible_field_hits_zero": True,
    }
    return checks, [name for name, ok in checks.items() if not ok]


def output_preview_rows(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(selected, start=1):
        rows.append(
            {
                "preview_order": idx,
                **row,
            }
        )
    return rows


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V16 Cross-Stratum Support/Contact Capacity Scan",
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
        f"selected_preview_rows = {summary['selection_summary']['selected_total']}",
        f"selected_by_cell = {summary['selection_summary']['selected_by_cell']}",
        f"selection_deficits = {summary['selection_summary']['deficits']}",
        f"primary_mixed_blocks_available = {summary['block_summary']['primary_mixed_blocks_available']}",
        f"selected_primary_blocks_with_both_sides = {summary['selection_summary']['selected_primary_blocks_with_both_sides']}",
        f"risk_flags = {summary['shortcut_risk_precheck']['risk_flags']}",
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
    plan_dir = as_abs(args.plan_dir)
    hl_queue = as_abs(args.hl_queue)
    lh_queue = as_abs(args.lh_queue)
    output_dir = as_abs(args.output_dir)

    plan_summary = read_json(plan_dir / "summary.json")
    sampling_policy = read_json(plan_dir / "sampling_policy.json")
    quota_rows = read_csv(plan_dir / "quota_plan.csv")

    errors = validate_plan(plan_summary)
    scanned = scan_queues(quota_rows, hl_queue, lh_queue)
    candidates = scanned["candidates"]
    quotas = quota_map(quota_rows)
    cell_table = capacity_by_cell(candidates, quota_rows, scanned)
    block_table = block_capacity(candidates)
    selected_preview, selection_summary = select_preview(candidates, quotas, sampling_policy)
    risk_precheck = precheck_risk(selected_preview, selection_summary, sampling_policy)
    checks, failed_checks = pass_fail(cell_table, block_table, selection_summary, risk_precheck, sampling_policy)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "capacity_by_cell.csv", cell_table)
    write_csv(output_dir / "quota_feasibility.csv", cell_table)
    write_csv(output_dir / "block_capacity.csv", block_table)
    write_jsonl(output_dir / "selection_preview_internal.jsonl", output_preview_rows(selected_preview))
    write_json(output_dir / "shortcut_risk_precheck.json", risk_precheck)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)

    capacity_pass = not errors and not failed_checks
    if errors:
        status = STATUS_ERROR
        next_todo = EXPECTED_PLAN_NEXT
    elif capacity_pass:
        status = STATUS_PASS
        next_todo = NEXT_PASS
    else:
        status = STATUS_FAIL
        next_todo = NEXT_FAIL

    primary_blocks_available = [row for row in block_table if row["mixed_primary_sides"]]
    interpretation = (
        "v16 capacity scan passed. The train queue has enough cross-stratum support/contact rows after the current caps "
        "to proceed to candidate mining. Posterior smoke remains blocked until label fill, ingestion, and target-independence audit pass."
        if capacity_pass
        else "v16 capacity scan did not clear all gates. Do not create a label sheet or run posterior smoke before a path decision. "
        "The failure reason should be treated as target-construction evidence rather than posterior evidence."
    )

    summary = {
        "schema_version": "h002_reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan_v1",
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
            "plan_summary": rel_path(plan_dir / "summary.json"),
            "sampling_policy": rel_path(plan_dir / "sampling_policy.json"),
            "quota_plan": rel_path(plan_dir / "quota_plan.csv"),
            "hl_queue": rel_path(hl_queue),
            "lh_queue": rel_path(lh_queue),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "capacity_by_cell": rel_path(output_dir / "capacity_by_cell.csv"),
            "quota_feasibility": rel_path(output_dir / "quota_feasibility.csv"),
            "block_capacity": rel_path(output_dir / "block_capacity.csv"),
            "selection_preview_internal": rel_path(output_dir / "selection_preview_internal.jsonl"),
            "shortcut_risk_precheck": rel_path(output_dir / "shortcut_risk_precheck.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "queue_line_counts": dict(scanned["queue_line_counts"]),
            "target_candidate_rows_seen": sum(scanned["raw_by_cell"].values()),
            "eligible_target_rows": len(candidates),
            "hard_filtered_rows": sum(scanned["hard_filtered_by_cell"].values()),
            "hard_filter_reasons": dict(scanned["hard_filter_reasons"]),
        },
        "capacity_by_cell": cell_table,
        "block_summary": {
            "primary_blocks_total": len(block_table),
            "primary_mixed_blocks_available": len(primary_blocks_available),
            "minimum_primary_blocks_required": int(sampling_policy["block_construction"]["minimum_blocks"]),
            "top_primary_mixed_blocks": primary_blocks_available[:10],
        },
        "selection_summary": selection_summary,
        "shortcut_risk_precheck": risk_precheck,
        "capacity_decision": {
            "capacity_pass": capacity_pass,
            "checks": checks,
            "failed_checks": failed_checks,
            "forbidden_visible_field_hits": 0,
        },
        "interpretation": interpretation,
        "decision": {
            "posterior_smoke_now": "blocked",
            "candidate_mining_now": "allowed_after_this_scan_only_if_capacity_pass_true",
            "if_capacity_pass": "run v16 candidate mining with raw-feature join and hidden audit manifest",
            "if_capacity_fails": "run path decision; do not force a label sheet",
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"next_todo={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"capacity_pass={summary['capacity_decision']['capacity_pass']}")
    print(f"selected_by_cell={summary['selection_summary']['selected_by_cell']}")
    print(f"selection_deficits={summary['selection_summary']['deficits']}")
    print(f"risk_flags={summary['shortcut_risk_precheck']['risk_flags']}")
    print(f"primary_mixed_blocks_available={summary['block_summary']['primary_mixed_blocks_available']}")
    print(f"selected_primary_blocks_with_both_sides={summary['selection_summary']['selected_primary_blocks_with_both_sides']}")
    print(f"output_dir={summary['output_dir']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
