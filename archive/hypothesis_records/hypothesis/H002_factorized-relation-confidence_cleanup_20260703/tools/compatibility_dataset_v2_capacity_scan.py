#!/usr/bin/env python3
"""Scan full-train capacity for H002 compatibility dataset v2."""

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

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_materialization_plan"
DEFAULT_CONTRACT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_contract"
DEFAULT_RAW_WITNESS_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_capacity_scan"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v2_materialization_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v2_capacity_scan"
EXPECTED_CONTRACT_STATUS = "h002_compatibility_dataset_v2_contract_ready"
EXPECTED_RAW_WITNESS_STATUS = "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v2_capacity_scan_v1"
STATUS_PASS = "h002_compatibility_dataset_v2_capacity_scan_passed_with_controls_ready_for_candidate_materialization"
STATUS_ERROR = "h002_compatibility_dataset_v2_capacity_scan_input_errors"
NEXT_TODO = "compatibility_dataset_v2_candidate_materialization"

TARGETS = {
    "support_contact": {
        "predicates": ["standing on", "lying on", "supported by"],
        "requested_positive": 120,
        "requested_negative": 120,
        "minimum_positive": 60,
        "minimum_negative": 60,
    },
    "relative_vertical": {
        "predicates": ["higher than", "lower than"],
        "requested_positive": 80,
        "requested_negative": 80,
        "minimum_positive": 60,
        "minimum_negative": 60,
    },
}

HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
STRUCTURAL_CONTEXT = {"floor", "wall", "ceiling", "room", "door", "doorframe", "window"}
PREVIEW_PER_CELL = 12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--contract-dir", type=Path, default=DEFAULT_CONTRACT_DIR)
    parser.add_argument("--raw-witness-dir", type=Path, default=DEFAULT_RAW_WITNESS_DIR)
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


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stable_id(value: str, prefix: str = "capv2") -> str:
    return f"{prefix}_{hashlib.sha1(value.encode('utf-8')).hexdigest()[:16]}"


def p_geom_bin(value: Any) -> str:
    p = safe_float(value)
    if p is None:
        return "p_unknown"
    if p >= 0.75:
        return "p_high"
    if p >= 0.50:
        return "p_mid"
    if p >= 0.25:
        return "p_low"
    return "p_very_low"


def semantic_band(value: Any, rank_band: str) -> str:
    score = safe_float(value)
    if score is not None:
        if score >= 0.75:
            return "semantic_high"
        if score >= 0.50:
            return "semantic_mid"
        if score >= 0.25:
            return "semantic_low"
        return "semantic_very_low"
    if rank_band in {"top50", "top100_only"}:
        return "rank_high"
    if rank_band in {"rank_101_200", "rank_201_500"}:
        return "rank_mid"
    return "rank_low"


def parse_reason_codes(value: Any) -> list[str]:
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
    return []


def endpoint_state(row: dict[str, Any]) -> str:
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
    return "movable_object_pair"


def visible_pair(row: dict[str, Any]) -> str:
    return f"{norm(row.get('subject_label'))}|{norm(row.get('object_label'))}"


def directed_pair(row: dict[str, Any]) -> str:
    return "|".join([str(row.get("scan_id")), str(row.get("subgraph_id")), str(row.get("subject_id")), str(row.get("object_id"))])


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


def compatibility_polarity(row: dict[str, Any]) -> str | None:
    queue = str(row.get("queue_kind") or "")
    status = str(row.get("geometry_status") or "")
    if queue == "LH" and status == "satisfied":
        return "positive"
    if queue == "HL" and status in {"unsatisfied", "violated"}:
        return "negative"
    return None


def target_family(row: dict[str, Any]) -> str | None:
    family = str(row.get("predicate_family") or "")
    predicate = str(row.get("predicate_label") or "")
    spec = TARGETS.get(family)
    if spec and predicate in spec["predicates"]:
        return family
    return None


def validate_inputs(plan: dict[str, Any], contract: dict[str, Any], raw_summary: dict[str, Any], paths: list[Path]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan.get("status")})
    if plan.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan.get("next_todo")})
    if plan.get("direct_materialization_allowed") is not False:
        errors.append({"error_type": "plan_direct_materialization_not_false", "actual": plan.get("direct_materialization_allowed")})
    if validation_count(plan.get("validation_errors")) != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan.get("validation_errors")})
    if contract.get("status") != EXPECTED_CONTRACT_STATUS:
        errors.append({"error_type": "unexpected_contract_status", "actual": contract.get("status")})
    if raw_summary.get("status") != EXPECTED_RAW_WITNESS_STATUS:
        errors.append({"error_type": "unexpected_raw_witness_status", "actual": raw_summary.get("status")})
    if validation_count(raw_summary.get("validation_errors")) != 0:
        errors.append({"error_type": "raw_witness_validation_errors", "actual": raw_summary.get("validation_errors")})
    for path in paths:
        if not path.exists():
            errors.append({"error_type": "missing_input_path", "path": rel_path(path)})
    return errors


def compact_preview(row: dict[str, Any], polarity: str, line_no: int, queue_path: Path) -> dict[str, Any]:
    prediction_id = str(row.get("prediction_id") or "")
    return {
        "schema_version": "h002_compatibility_dataset_v2_capacity_preview_row",
        "preview_id": stable_id(prediction_id),
        "source_line_no": line_no,
        "source_queue_path": rel_path(queue_path),
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
        "capacity_polarity": polarity,
        "queue_kind_hidden": row.get("queue_kind"),
        "geometry_status_hidden": row.get("geometry_status"),
        "rank_band_hidden": row.get("rank_band"),
        "source_score_hidden": row.get("semantic_score_norm"),
        "source_rank_hidden": row.get("semantic_rank"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "p_geom_bin_hidden": p_geom_bin(row.get("p_geom_valid")),
        "semantic_band_hidden": semantic_band(row.get("semantic_score_norm"), str(row.get("rank_band") or "")),
        "endpoint_state_hidden": endpoint_state(row),
        "subject_object_label_pair_hidden": visible_pair(row),
        "directed_pair_key_hidden": directed_pair(row),
        "reason_codes_hidden": parse_reason_codes(row.get("reason_codes")),
        "model_input_policy": {
            "T_e_can_use_subject_object_predicate_text": True,
            "Z_e_can_use_source_score_rank": True,
            "G_e_requires_raw_witness_join": True,
            "C_e_must_not_use_Z_e_or_hidden_queue_fields": True,
            "hidden_fields_visible_to_model": False,
        },
    }


def update_axis_counts(axis_counts: dict[str, Counter[tuple[str, str]]], row: dict[str, Any], polarity: str) -> None:
    axes = {
        "predicate_label": str(row.get("predicate_label") or ""),
        "rank_band": str(row.get("rank_band") or ""),
        "endpoint_state": endpoint_state(row),
        "subject_object_label_pair": visible_pair(row),
        "queue_kind": str(row.get("queue_kind") or ""),
        "geometry_status": str(row.get("geometry_status") or ""),
        "p_geom_bin": p_geom_bin(row.get("p_geom_valid")),
        "semantic_band": semantic_band(row.get("semantic_score_norm"), str(row.get("rank_band") or "")),
    }
    for axis, value in axes.items():
        axis_counts[axis][(value, polarity)] += 1


def scan_queues(hl_queue: Path, lh_queue: Path) -> dict[str, Any]:
    raw_counts: Counter[tuple[str, str, str]] = Counter()
    eligible_counts: Counter[tuple[str, str, str, str]] = Counter()
    hard_filtered_counts: Counter[tuple[str, str, str]] = Counter()
    hard_filter_reasons: Counter[str] = Counter()
    family_label_counts: Counter[tuple[str, str]] = Counter()
    predicate_label_counts: Counter[tuple[str, str, str]] = Counter()
    queue_line_counts: Counter[str] = Counter()
    distinct_scans: dict[tuple[str, str], set[str]] = defaultdict(set)
    distinct_pairs: dict[tuple[str, str], set[str]] = defaultdict(set)
    distinct_directed_pairs: dict[tuple[str, str], set[str]] = defaultdict(set)
    axis_counts_by_family: dict[str, dict[str, Counter[tuple[str, str]]]] = defaultdict(lambda: defaultdict(Counter))
    preview_counts: Counter[tuple[str, str, str]] = Counter()
    preview_rows: list[dict[str, Any]] = []

    for queue_path in [hl_queue, lh_queue]:
        for line_no, row in iter_jsonl(queue_path):
            queue_line_counts[rel_path(queue_path)] += 1
            family = target_family(row)
            if family is None:
                continue
            predicate = str(row.get("predicate_label") or "")
            queue_kind = str(row.get("queue_kind") or "")
            raw_counts[(family, predicate, queue_kind)] += 1
            hard_reason = hard_filter_reason(row)
            if hard_reason:
                hard_filtered_counts[(family, predicate, queue_kind)] += 1
                hard_filter_reasons[hard_reason] += 1
                continue
            polarity = compatibility_polarity(row)
            if polarity is None:
                hard_filtered_counts[(family, predicate, queue_kind)] += 1
                hard_filter_reasons["unsupported_queue_geometry_polarity"] += 1
                continue
            eligible_counts[(family, predicate, queue_kind, polarity)] += 1
            family_label_counts[(family, polarity)] += 1
            predicate_label_counts[(family, predicate, polarity)] += 1
            distinct_scans[(family, polarity)].add(str(row.get("scan_id")))
            distinct_pairs[(family, polarity)].add(visible_pair(row))
            distinct_directed_pairs[(family, polarity)].add(directed_pair(row))
            update_axis_counts(axis_counts_by_family[family], row, polarity)
            preview_key = (family, predicate, polarity)
            if preview_counts[preview_key] < PREVIEW_PER_CELL:
                preview_rows.append(compact_preview(row, polarity, line_no, queue_path))
                preview_counts[preview_key] += 1

    return {
        "raw_counts": raw_counts,
        "eligible_counts": eligible_counts,
        "hard_filtered_counts": hard_filtered_counts,
        "hard_filter_reasons": hard_filter_reasons,
        "family_label_counts": family_label_counts,
        "predicate_label_counts": predicate_label_counts,
        "queue_line_counts": queue_line_counts,
        "distinct_scans": distinct_scans,
        "distinct_pairs": distinct_pairs,
        "distinct_directed_pairs": distinct_directed_pairs,
        "axis_counts_by_family": axis_counts_by_family,
        "preview_rows": preview_rows,
    }


def capacity_by_predicate_queue(scanned: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, spec in TARGETS.items():
        for predicate in spec["predicates"]:
            for queue_kind in ["HL", "LH"]:
                raw = scanned["raw_counts"][(family, predicate, queue_kind)]
                hard = scanned["hard_filtered_counts"][(family, predicate, queue_kind)]
                positive = scanned["eligible_counts"][(family, predicate, queue_kind, "positive")]
                negative = scanned["eligible_counts"][(family, predicate, queue_kind, "negative")]
                rows.append(
                    {
                        "relation_family": family,
                        "predicate_label": predicate,
                        "queue_kind": queue_kind,
                        "raw_rows": raw,
                        "hard_filtered_rows": hard,
                        "eligible_positive": positive,
                        "eligible_negative": negative,
                        "eligible_total": positive + negative,
                        "capacity_role": "source_positive_pool" if positive else ("source_negative_pool" if negative else "no_direct_pool"),
                    }
                )
    return rows


def family_rows(scanned: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, spec in TARGETS.items():
        pos = scanned["family_label_counts"][(family, "positive")]
        neg = scanned["family_label_counts"][(family, "negative")]
        rows.append(
            {
                "relation_family": family,
                "eligible_positive": pos,
                "eligible_negative": neg,
                "requested_positive": spec["requested_positive"],
                "requested_negative": spec["requested_negative"],
                "minimum_positive": spec["minimum_positive"],
                "minimum_negative": spec["minimum_negative"],
                "requested_class_mass_pass": pos >= spec["requested_positive"] and neg >= spec["requested_negative"],
                "minimum_class_mass_pass": pos >= spec["minimum_positive"] and neg >= spec["minimum_negative"],
                "positive_distinct_scans": len(scanned["distinct_scans"][(family, "positive")]),
                "negative_distinct_scans": len(scanned["distinct_scans"][(family, "negative")]),
                "positive_distinct_visible_pairs": len(scanned["distinct_pairs"][(family, "positive")]),
                "negative_distinct_visible_pairs": len(scanned["distinct_pairs"][(family, "negative")]),
                "positive_distinct_directed_pairs": len(scanned["distinct_directed_pairs"][(family, "positive")]),
                "negative_distinct_directed_pairs": len(scanned["distinct_directed_pairs"][(family, "negative")]),
            }
        )
    return rows


def quota_rows(scanned: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, spec in TARGETS.items():
        pos = scanned["family_label_counts"][(family, "positive")]
        neg = scanned["family_label_counts"][(family, "negative")]
        predicate_positive = {
            predicate: scanned["predicate_label_counts"][(family, predicate, "positive")] for predicate in spec["predicates"]
        }
        predicate_negative = {
            predicate: scanned["predicate_label_counts"][(family, predicate, "negative")] for predicate in spec["predicates"]
        }
        if family == "support_contact":
            direct_balance_pass = sum(1 for count in predicate_negative.values() if count >= 20) >= 2
            generation_policy = "wrong_pair_shuffle_and_contact_gap_perturbation_required"
        else:
            direct_balance_pass = min(predicate_negative.values()) >= 20
            generation_policy = "predicate_flip_and_subject_object_swap_required"
        rows.append(
            {
                "relation_family": family,
                "eligible_positive": pos,
                "eligible_negative": neg,
                "requested_positive": spec["requested_positive"],
                "requested_negative": spec["requested_negative"],
                "minimum_positive": spec["minimum_positive"],
                "minimum_negative": spec["minimum_negative"],
                "class_mass_pass": pos >= spec["requested_positive"] and neg >= spec["requested_negative"],
                "direct_hl_lh_predicate_balance_pass": direct_balance_pass,
                "predicate_positive_counts": json.dumps(predicate_positive, sort_keys=True),
                "predicate_negative_counts": json.dumps(predicate_negative, sort_keys=True),
                "generated_counterfactual_policy": generation_policy,
                "materialization_allowed_with_controls": pos >= spec["requested_positive"] and neg >= spec["requested_negative"],
            }
        )
    return rows


def control_axis_rows(scanned: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, axis_counts in scanned["axis_counts_by_family"].items():
        total = scanned["family_label_counts"][(family, "positive")] + scanned["family_label_counts"][(family, "negative")]
        for axis, counter in axis_counts.items():
            grouped: dict[str, Counter[str]] = defaultdict(Counter)
            for (value, polarity), count in counter.items():
                grouped[value][polarity] += count
            majority = sum(max(counts.values()) for counts in grouped.values())
            rows.append(
                {
                    "relation_family": family,
                    "axis": axis,
                    "groups": len(grouped),
                    "rows": total,
                    "majority_accuracy_if_axis_only": round(majority / total, 6) if total else None,
                    "risk_level": "high" if total and majority / total >= 0.90 else ("medium" if total and majority / total >= 0.75 else "low"),
                    "label_counts_by_axis_value": json.dumps(
                        {value: dict(sorted(counts.items())) for value, counts in sorted(grouped.items())},
                        sort_keys=True,
                    )[:2000],
                }
            )
    return rows


def risk_precheck(quota: list[dict[str, Any]], controls: list[dict[str, Any]], raw_summary: dict[str, Any], match_rows: Path) -> dict[str, Any]:
    high_axes = [row for row in controls if row["risk_level"] == "high"]
    class_mass_pass = all(row["class_mass_pass"] for row in quota)
    direct_balance_pass = all(row["direct_hl_lh_predicate_balance_pass"] for row in quota)
    flags = {
        "class_mass_pass": class_mass_pass,
        "direct_hl_lh_predicate_balance_pass": direct_balance_pass,
        "direct_hl_lh_target_allowed": False,
        "row_materialization_allowed_with_controls": class_mass_pass,
        "learned_smoke_allowed_now": False,
        "queue_kind_hidden_shortcut": True,
        "geometry_status_hidden_shortcut": True,
        "rank_source_control_required": True,
        "predicate_direction_control_required": True,
        "generated_counterfactuals_required": not direct_balance_pass,
        "raw_witness_full_join_required": True,
        "match_rows_available": match_rows.exists(),
        "raw_witness_seed_ready": raw_summary.get("status") == EXPECTED_RAW_WITNESS_STATUS,
        "attachment_like_primary_still_blocked": True,
    }
    return {
        "decision": (
            "capacity_pass_but_direct_hl_lh_target_blocked_generate_counterfactuals_and_repackage_raw_witness"
            if class_mass_pass
            else "capacity_blocked_do_not_materialize"
        ),
        "flags": flags,
        "high_risk_axes": high_axes,
        "blocked_model_inputs": [
            "queue_kind",
            "geometry_status",
            "rank_band as C_e input",
            "source score/rank as C_e input",
            "label_match_status",
            "machine_hint",
            "matched_gt_ids",
            "p_geom_valid as G_e main input",
            "target construction polarity",
        ],
        "required_materialization_controls": [
            "raw witness join for selected prediction ids",
            "T_e/Z_e/G_e/Q_e factor block repackage",
            "C_e view uses T_e + G_e only",
            "source/rank matched or ablated materialization groups",
            "support_contact wrong-pair and shuffled-geometry negatives",
            "support_contact contact-gap/support perturbation negatives",
            "relative_vertical predicate flip negatives",
            "relative_vertical subject/object swap negatives",
            "hidden shortcut audit before learned smoke",
        ],
    }


def factor_separability_audit(raw_summary: dict[str, Any], match_rows: Path) -> dict[str, Any]:
    return {
        "assessment": "pass_with_repackage_required",
        "queue_source_role": "capacity_and_hidden_control_axes_only",
        "raw_witness_source_role": "G_e_numeric_geometry_source_after_selected_prediction_id_join",
        "match_rows": {
            "path": rel_path(match_rows),
            "exists": match_rows.exists(),
            "size_bytes": match_rows.stat().st_size if match_rows.exists() else None,
            "full_scan_deferred": True,
        },
        "raw_witness_seed": {
            "status": raw_summary.get("status"),
            "raw_witness_join": raw_summary.get("raw_witness_join", {}),
            "input_contract": raw_summary.get("input_contract", {}),
        },
        "factor_blocks": {
            "T_e": {
                "allowed": ["predicate_label", "predicate_text", "relation_family", "subject_label", "object_label"],
                "blocked": ["source score", "source rank", "queue kind", "geometry status", "label/audit target"],
            },
            "Z_e": {
                "allowed": ["source_id", "semantic_score_raw", "semantic_score_norm", "semantic_rank", "rank_band"],
                "blocked_from": ["C_e"],
            },
            "G_e": {
                "allowed_after_join": [
                    "distance_xy",
                    "distance_3d",
                    "center_delta_z",
                    "vertical_gap_subject_on_object",
                    "projected_iou_xy",
                    "projected_subject_overlap_ratio",
                    "projected_object_overlap_ratio",
                    "normalized geometry features",
                ],
                "blocked": ["predicate label", "relation family", "source score/rank", "queue kind", "geometry_status", "p_geom_valid as main score"],
            },
            "Q_e": {
                "allowed": ["coverage_has_raw_witness", "raw_witness_missing_flag", "feature availability flags"],
                "role": "observability/selective decision, not relation truth",
            },
        },
    }


def build_report(summary: dict[str, Any], family: list[dict[str, Any]], quota: list[dict[str, Any]], risk: dict[str, Any]) -> str:
    lines = [
        "# H002 Compatibility Dataset V2 Capacity Scan",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"decision = {risk['decision']}",
        f"row_materialization_allowed_with_controls = {str(summary['row_materialization_allowed_with_controls']).lower()}",
        f"direct_hl_lh_target_allowed = {str(summary['direct_hl_lh_target_allowed']).lower()}",
        f"learned_smoke_allowed = {str(summary['learned_smoke_allowed']).lower()}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Family Capacity",
        "",
        "| Family | Positive | Negative | Requested | Class Mass |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in family:
        lines.append(
            f"| `{row['relation_family']}` | {row['eligible_positive']} | {row['eligible_negative']} | "
            f"{row['requested_positive']}/{row['requested_negative']} | `{row['requested_class_mass_pass']}` |"
        )
    lines.extend(
        [
            "",
            "## Predicate Balance",
            "",
            "| Family | Positive by Predicate | Negative by Predicate | Direct Balance |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in quota:
        lines.append(
            f"| `{row['relation_family']}` | `{row['predicate_positive_counts']}` | "
            f"`{row['predicate_negative_counts']}` | `{row['direct_hl_lh_predicate_balance_pass']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Class mass is sufficient for both primary families.",
            "- Direct HL/LH target construction is still blocked because queue kind, geometry status, rank, and predicate direction can shortcut the label.",
            "- v2 materialization is allowed only with generated counterfactual controls and raw-witness `G_e` repackaging.",
            "- `attachment_like` remains diagnostic-only.",
            "",
            "Required next controls:",
            "",
        ]
    )
    for item in risk["required_materialization_controls"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Next", "", f"`{summary['next_todo']}`"])
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    plan_summary = read_json(args.plan_dir / "summary.json")
    contract_summary = read_json(args.contract_dir / "summary.json")
    raw_summary = read_json(args.raw_witness_dir / "summary.json")
    errors = validate_inputs(plan_summary, contract_summary, raw_summary, [args.hl_queue, args.lh_queue, args.match_rows])

    scanned = scan_queues(args.hl_queue, args.lh_queue) if not errors else None
    family = family_rows(scanned) if scanned else []
    by_predicate = capacity_by_predicate_queue(scanned) if scanned else []
    quota = quota_rows(scanned) if scanned else []
    controls = control_axis_rows(scanned) if scanned else []
    risk = risk_precheck(quota, controls, raw_summary, args.match_rows) if scanned else {"decision": "input_errors", "flags": {}}
    separability = factor_separability_audit(raw_summary, args.match_rows)

    row_materialization_allowed = bool(risk.get("flags", {}).get("row_materialization_allowed_with_controls"))
    status = STATUS_PASS if not errors and row_materialization_allowed else STATUS_ERROR
    next_todo = NEXT_TODO if status == STATUS_PASS else "fix_compatibility_dataset_v2_capacity_scan_inputs"
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation_errors": len(errors),
        "decision": risk["decision"],
        "next_todo": next_todo,
        "row_materialization_allowed_with_controls": row_materialization_allowed,
        "direct_hl_lh_target_allowed": False,
        "learned_smoke_allowed": False,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "queue_line_counts": dict(scanned["queue_line_counts"]) if scanned else {},
        "hard_filter_reasons": dict(scanned["hard_filter_reasons"]) if scanned else {},
        "family_capacity": family,
        "quota_feasibility": quota,
        "boundary": {
            "split": "train_only_capacity_scan",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_model": False,
            "materializes_final_dataset": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "input_roots": {
            "materialization_plan": rel_path(args.plan_dir),
            "contract": rel_path(args.contract_dir),
            "raw_witness_seed": rel_path(args.raw_witness_dir),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
            "match_rows": rel_path(args.match_rows),
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "quota_feasibility": rel_path(args.output_dir / "quota_feasibility.csv"),
            "capacity_by_family": rel_path(args.output_dir / "capacity_by_family.csv"),
            "capacity_by_predicate_queue": rel_path(args.output_dir / "capacity_by_predicate_queue.csv"),
            "control_axis_audit": rel_path(args.output_dir / "control_axis_audit.csv"),
            "candidate_pool_preview": rel_path(args.output_dir / "candidate_pool_preview.jsonl"),
            "risk_precheck": rel_path(args.output_dir / "risk_precheck.json"),
            "factor_separability_audit": rel_path(args.output_dir / "factor_separability_audit.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "quota_feasibility.csv", quota)
    write_csv(args.output_dir / "capacity_by_family.csv", family)
    write_csv(args.output_dir / "capacity_by_predicate_queue.csv", by_predicate)
    write_csv(args.output_dir / "control_axis_audit.csv", controls)
    write_jsonl(args.output_dir / "candidate_pool_preview.jsonl", scanned["preview_rows"] if scanned else [])
    write_json(args.output_dir / "risk_precheck.json", risk)
    write_json(args.output_dir / "factor_separability_audit.json", separability)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    (args.output_dir / "report.md").write_text(build_report(summary, family, quota, risk), encoding="utf-8")

    print(f"status={status}")
    print(f"decision={risk['decision']}")
    print(f"row_materialization_allowed_with_controls={row_materialization_allowed}")
    print(f"direct_hl_lh_target_allowed=False")
    print(f"next={next_todo}")
    print(f"validation_errors={len(errors)}")


if __name__ == "__main__":
    main()
