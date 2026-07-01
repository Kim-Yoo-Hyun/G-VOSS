#!/usr/bin/env python3
"""Scan full train-side capacity for the H002 v3 predicate-conditioned dataset."""

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

DEFAULT_CONTRACT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_contract"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_capacity_scan"

EXPECTED_CONTRACT_STATUS = "h002_compatibility_dataset_v3_contract_ready"
EXPECTED_CONTRACT_NEXT = "compatibility_dataset_v3_capacity_scan"
EXPECTED_DATASET_NAME = "h002_compatibility_dataset_v3_predicate_conditioned"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_capacity_scan_v1"
STATUS_PASS = "h002_compatibility_dataset_v3_capacity_scan_passed_ready_for_candidate_materialization"
STATUS_BLOCKED = "h002_compatibility_dataset_v3_capacity_scan_blocked"
STATUS_ERROR = "h002_compatibility_dataset_v3_capacity_scan_input_errors"
NEXT_TODO = "compatibility_dataset_v3_candidate_materialization"

VERTICAL_PREDICATES = {"higher than", "lower than"}
SUPPORT_PREDICATES = {"standing on", "lying on", "supported by"}
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

STRUCTURAL_LABELS = {"floor", "wall", "ceiling", "room", "door", "doorframe", "window"}
PREVIEW_GROUPS_PER_DIRECTION = 20
REQUESTED_GROUPS = 200
MIN_REPORTABLE_GROUPS = 100


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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
                seen.add(key)
                fields.append(key)
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


def visible_pair(subject: str, obj: str) -> str:
    return f"{norm(subject)}|{norm(obj)}"


def endpoint_state(subject: str, obj: str) -> str:
    s = norm(subject)
    o = norm(obj)
    if s in {"floor", "wall", "ceiling"}:
        return "subject_room_surface"
    if o == "floor":
        return "object_floor"
    if o in {"wall", "ceiling"}:
        return "object_wall_or_ceiling"
    if s in STRUCTURAL_LABELS or o in STRUCTURAL_LABELS:
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


def compact_row(row: dict[str, Any], raw_hash: str) -> dict[str, Any]:
    identity = row.get("identity", {})
    predicate = row.get("predicate", {})
    semantic = row.get("semantic", {})
    edge = row.get("edge", {})
    geometry = row.get("geometry", {})
    label = row.get("label", {})
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
        "semantic_score_raw": semantic.get("semantic_score_raw"),
        "semantic_score_norm": semantic.get("semantic_score_norm"),
        "semantic_rank": semantic.get("rank_in_context") or semantic.get("predicate_rank_for_pair"),
        "rank_band": row.get("rga", {}).get("rank_band") or rank_band(semantic.get("rank_in_context")),
        "p_geom_valid": geometry.get("p_geom_valid"),
        "geometry_status": geometry.get("geometry_status"),
        "label_match_status": label.get("label_match_status"),
        "matched_predicates": label.get("matched_predicates", []),
        "geometry_feature_hash": raw_hash,
    }


def validate_inputs(contract_summary: dict[str, Any], contract: dict[str, Any], match_rows: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if contract_summary.get("status") != EXPECTED_CONTRACT_STATUS:
        errors.append({"error_type": "unexpected_contract_status", "actual": contract_summary.get("status")})
    if contract_summary.get("next_todo") != EXPECTED_CONTRACT_NEXT:
        errors.append({"error_type": "unexpected_contract_next_todo", "actual": contract_summary.get("next_todo")})
    if contract_summary.get("validation_errors") != 0:
        errors.append({"error_type": "contract_validation_errors", "actual": contract_summary.get("validation_errors")})
    if contract.get("dataset_name") != EXPECTED_DATASET_NAME:
        errors.append({"error_type": "unexpected_dataset_name", "actual": contract.get("dataset_name")})
    primary = contract.get("primary_family", {})
    if primary.get("family") != "relative_vertical":
        errors.append({"error_type": "unexpected_primary_family", "actual": primary.get("family")})
    if set(primary.get("predicates", [])) != VERTICAL_PREDICATES:
        errors.append({"error_type": "unexpected_primary_predicates", "actual": primary.get("predicates")})
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


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


def scan_match_rows(match_rows: Path, abs_margin: float, norm_margin: float) -> dict[str, Any]:
    vertical_groups: dict[str, dict[str, Any]] = {}
    support_counts: Counter[tuple[str, str]] = Counter()
    support_distinct_pairs: dict[str, set[str]] = defaultdict(set)
    counts = Counter()

    with match_rows.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            counts["match_rows_scanned"] += 1
            row = json.loads(line)
            predicate = row.get("predicate", {})
            family = str(predicate.get("predicate_family") or "")
            predicate_label = str(predicate.get("predicate_label") or "")

            if family == "support_contact" and predicate_label in SUPPORT_PREDICATES:
                identity = row.get("identity", {})
                support_counts[(predicate_label, "rows")] += 1
                if (row.get("geometry") or {}).get("raw_features"):
                    support_counts[(predicate_label, "raw_rows")] += 1
                support_distinct_pairs[predicate_label].add(
                    str(identity.get("directed_pair_id") or directed_pair_id(row))
                )
                continue

            if family != "relative_vertical" or predicate_label not in VERTICAL_PREDICATES:
                continue

            counts["relative_vertical_rows"] += 1
            identity = row.get("identity", {})
            edge = row.get("edge", {})
            geometry = row.get("geometry", {})
            raw = geometry.get("raw_features") or {}
            key = directed_pair_id(row)
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
                    "line_numbers": {},
                },
            )
            if not raw:
                counts["relative_vertical_rows_missing_raw"] += 1
                continue
            counts["relative_vertical_rows_with_raw"] += 1
            raw_hash = geometry_hash(raw)
            entry["raw_hashes"].add(raw_hash)
            entry["raw_by_predicate"][predicate_label] = raw
            entry["rows_by_predicate"][predicate_label] = compact_row(row, raw_hash)
            entry["line_numbers"][predicate_label] = line_no

    group_records: list[dict[str, Any]] = []
    rejection_reasons = Counter()
    direction_counts = Counter()
    axis_counts: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    preview_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for key, entry in vertical_groups.items():
        predicates_present = set(entry["rows_by_predicate"])
        if not VERTICAL_PREDICATES <= predicates_present:
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

        center_delta = safe_float(raw.get("center_delta_z"))
        norm_delta = safe_float(raw.get("normalized_center_delta_z"))
        positive_predicate = "higher than" if direction == "higher_positive" else "lower than"
        negative_predicate = "lower than" if direction == "higher_positive" else "higher than"
        subject = str(entry.get("subject_label") or "")
        obj = str(entry.get("object_label") or "")
        group_id = "v3geom_" + stable_hash(key + "|" + next(iter(entry["raw_hashes"])))
        record = {
            "geometry_group_id": group_id,
            "directed_pair_id": key,
            "scan_id": entry.get("scan_id"),
            "subgraph_id": entry.get("subgraph_id"),
            "subject_id": entry.get("subject_id"),
            "object_id": entry.get("object_id"),
            "subject_label": subject,
            "object_label": obj,
            "visible_pair": visible_pair(subject, obj),
            "endpoint_state": endpoint_state(subject, obj),
            "geometry_feature_hash": next(iter(entry["raw_hashes"])),
            "center_delta_z": center_delta,
            "normalized_center_delta_z": norm_delta,
            "direction_bucket": direction,
            "positive_predicate": positive_predicate,
            "negative_predicate": negative_predicate,
            "higher_prediction_id": entry["rows_by_predicate"]["higher than"].get("prediction_id"),
            "lower_prediction_id": entry["rows_by_predicate"]["lower than"].get("prediction_id"),
            "higher_rank_band": entry["rows_by_predicate"]["higher than"].get("rank_band"),
            "lower_rank_band": entry["rows_by_predicate"]["lower than"].get("rank_band"),
            "higher_semantic_rank": entry["rows_by_predicate"]["higher than"].get("semantic_rank"),
            "lower_semantic_rank": entry["rows_by_predicate"]["lower than"].get("semantic_rank"),
            "higher_semantic_score_norm": entry["rows_by_predicate"]["higher than"].get("semantic_score_norm"),
            "lower_semantic_score_norm": entry["rows_by_predicate"]["lower than"].get("semantic_score_norm"),
        }
        group_records.append(record)
        direction_counts[direction] += 1
        axes = {
            "visible_pair": record["visible_pair"],
            "endpoint_state": record["endpoint_state"],
            "subject_label": norm(subject),
            "object_label": norm(obj),
            "higher_rank_band": str(record["higher_rank_band"]),
            "lower_rank_band": str(record["lower_rank_band"]),
            "rank_band_pair": f"{record['higher_rank_band']}|{record['lower_rank_band']}",
        }
        for axis, value in axes.items():
            axis_counts[axis][(value, direction)] += 1
        if len(preview_buckets[direction]) < PREVIEW_GROUPS_PER_DIRECTION:
            preview_buckets[direction].append(record)

    group_records.sort(key=lambda row: stable_hash(str(row["geometry_group_id"])))

    return {
        "counts": counts,
        "vertical_groups": vertical_groups,
        "group_records": group_records,
        "rejection_reasons": rejection_reasons,
        "direction_counts": direction_counts,
        "axis_counts": axis_counts,
        "preview_rows": preview_buckets["higher_positive"][:PREVIEW_GROUPS_PER_DIRECTION]
        + preview_buckets["lower_positive"][:PREVIEW_GROUPS_PER_DIRECTION],
        "support_counts": support_counts,
        "support_distinct_pairs": support_distinct_pairs,
    }


def margin_sensitivity(match_rows: Path, margins: list[tuple[float, float]]) -> list[dict[str, Any]]:
    # Reuse the full scan output would be faster, but this table is small and easier to audit if it
    # is computed from stored groups in the caller. This function is kept for explicit contract.
    raise NotImplementedError


def build_margin_rows(group_records_all: dict[str, dict[str, Any]], margins: list[tuple[float, float]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for abs_margin, norm_margin in margins:
        counts = Counter()
        for entry in group_records_all.values():
            if not VERTICAL_PREDICATES <= set(entry["rows_by_predicate"]):
                continue
            if len(entry["raw_hashes"]) != 1:
                continue
            raw = entry["raw_by_predicate"]["higher than"]
            state, direction = clear_vertical_state(raw, abs_margin=abs_margin, norm_margin=norm_margin)
            if state == "clear" and direction:
                counts[direction] += 1
            else:
                counts[state] += 1
        clear_total = counts["higher_positive"] + counts["lower_positive"]
        rows.append(
            {
                "abs_center_delta_z_min": abs_margin,
                "normalized_center_delta_z_min": norm_margin,
                "clear_groups": clear_total,
                "higher_positive_groups": counts["higher_positive"],
                "lower_positive_groups": counts["lower_positive"],
                "balanced_group_capacity": min(counts["higher_positive"], counts["lower_positive"]) * 2,
                "ambiguous_or_rejected_groups": sum(count for key, count in counts.items() if key not in {"higher_positive", "lower_positive"}),
                "requested_200_groups_pass": min(counts["higher_positive"], counts["lower_positive"]) >= REQUESTED_GROUPS // 2,
                "minimum_100_groups_pass": min(counts["higher_positive"], counts["lower_positive"]) >= MIN_REPORTABLE_GROUPS // 2,
            }
        )
    return rows


def axis_mixing_rows(axis_counts: dict[str, Counter[tuple[str, str]]], total_groups: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for axis, counter in sorted(axis_counts.items()):
        grouped: dict[str, Counter[str]] = defaultdict(Counter)
        for (value, direction), count in counter.items():
            grouped[value][direction] += count
        majority = sum(max(counts.values()) for counts in grouped.values())
        mixed_values = sum(1 for counts in grouped.values() if counts["higher_positive"] and counts["lower_positive"])
        rows.append(
            {
                "axis": axis,
                "axis_values": len(grouped),
                "mixed_direction_values": mixed_values,
                "clear_groups": total_groups,
                "direction_majority_accuracy_if_axis_only": round(majority / total_groups, 6) if total_groups else None,
                "risk_level": "high" if total_groups and majority / total_groups >= 0.90 else ("medium" if total_groups and majority / total_groups >= 0.75 else "low"),
                "value_counts_preview": json.dumps(
                    {value: dict(counts) for value, counts in sorted(grouped.items())[:30]},
                    ensure_ascii=False,
                    sort_keys=True,
                )[:4000],
            }
        )
    return rows


def vertical_capacity_rows(scan: dict[str, Any]) -> list[dict[str, Any]]:
    counts = scan["counts"]
    directions = scan["direction_counts"]
    total_groups = len(scan["vertical_groups"])
    clear_groups = len(scan["group_records"])
    both_predicate_groups = clear_groups + sum(scan["rejection_reasons"].values()) - scan["rejection_reasons"]["missing_predicate_alternative"]
    return [
        {
            "metric": "match_rows_scanned",
            "value": counts["match_rows_scanned"],
        },
        {
            "metric": "relative_vertical_rows",
            "value": counts["relative_vertical_rows"],
        },
        {
            "metric": "relative_vertical_rows_with_raw",
            "value": counts["relative_vertical_rows_with_raw"],
        },
        {
            "metric": "directed_pair_groups_with_any_vertical_predicate",
            "value": total_groups,
        },
        {
            "metric": "directed_pair_groups_with_both_predicates",
            "value": both_predicate_groups,
        },
        {
            "metric": "clear_same_geometry_groups_at_frozen_margin",
            "value": clear_groups,
        },
        {
            "metric": "higher_positive_groups",
            "value": directions["higher_positive"],
        },
        {
            "metric": "lower_positive_groups",
            "value": directions["lower_positive"],
        },
        {
            "metric": "balanced_group_capacity",
            "value": min(directions["higher_positive"], directions["lower_positive"]) * 2,
        },
        {
            "metric": "requested_200_groups_pass",
            "value": min(directions["higher_positive"], directions["lower_positive"]) >= REQUESTED_GROUPS // 2,
        },
        {
            "metric": "minimum_100_groups_pass",
            "value": min(directions["higher_positive"], directions["lower_positive"]) >= MIN_REPORTABLE_GROUPS // 2,
        },
    ]


def rejection_rows(rejections: Counter[str]) -> list[dict[str, Any]]:
    return [{"rejection_reason": key, "groups": count} for key, count in sorted(rejections.items())]


def support_probe_rows(scan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for predicate in sorted(SUPPORT_PREDICATES):
        rows.append(
            {
                "family": "support_contact",
                "predicate": predicate,
                "rows": scan["support_counts"][(predicate, "rows")],
                "raw_rows": scan["support_counts"][(predicate, "raw_rows")],
                "distinct_directed_pairs": len(scan["support_distinct_pairs"][predicate]),
                "role_orientation_evidence_available": False,
                "mesh_or_multiview_evidence_available": False,
                "primary_v3_allowed": False,
                "reason": "match_rows expose OBB/raw numeric fields but no role/orientation or visual/mesh evidence for support predicate distinction",
            }
        )
    return rows


def materialization_plan(scan: dict[str, Any], margin_rows: list[dict[str, Any]], axis_rows: list[dict[str, Any]]) -> dict[str, Any]:
    directions = scan["direction_counts"]
    requested_pass = min(directions["higher_positive"], directions["lower_positive"]) >= REQUESTED_GROUPS // 2
    minimum_pass = min(directions["higher_positive"], directions["lower_positive"]) >= MIN_REPORTABLE_GROUPS // 2
    high_risk_axes = [row["axis"] for row in axis_rows if row.get("risk_level") == "high"]
    medium_risk_axes = [row["axis"] for row in axis_rows if row.get("risk_level") == "medium"]
    return {
        "candidate_materialization_allowed": requested_pass,
        "minimum_materialization_allowed": minimum_pass,
        "candidate_materialization_requires_axis_controls": bool(high_risk_axes or medium_risk_axes),
        "high_risk_axes": high_risk_axes,
        "medium_risk_axes": medium_risk_axes,
        "recommended_next_todo": NEXT_TODO if requested_pass else "compatibility_dataset_v3_contract_revision",
        "recommended_primary_family": "relative_vertical",
        "recommended_group_quota": REQUESTED_GROUPS if requested_pass else MIN_REPORTABLE_GROUPS,
        "recommended_direction_balance": {
            "higher_positive_groups": REQUESTED_GROUPS // 2 if requested_pass else MIN_REPORTABLE_GROUPS // 2,
            "lower_positive_groups": REQUESTED_GROUPS // 2 if requested_pass else MIN_REPORTABLE_GROUPS // 2,
        },
        "materialization_policy": [
            "sample equal numbers of higher-positive and lower-positive directed-pair groups",
            "prioritize mixed-direction visible-pair cells and cap single-direction visible pairs",
            "avoid a structural-only slice dominated by floor/wall/ceiling endpoints",
            "for each group emit exactly two rows with identical G_e and opposite predicate labels",
            "exclude geometry_group_id, row_id, label_rule_id, construction route, and raw source predicate from model features",
            "use Z_e only for source baselines and later reliability models, never for C_e",
            "report predicate-only, visible-pair-only, predicate+visible-pair, and rank-band shortcut probes",
            "run schema shortcut audit before learned smoke",
        ],
        "frozen_margin": {
            "abs_center_delta_z_min": 0.10,
            "normalized_center_delta_z_min": 0.20,
        },
        "margin_sensitivity_summary": margin_rows,
    }


def write_report(path: Path, summary: dict[str, Any], plan: dict[str, Any]) -> None:
    lines = [
        "# Compatibility Dataset V3 Capacity Scan",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v3_capacity_scan/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"candidate_materialization_allowed = {str(summary['candidate_materialization_allowed']).lower()}",
        f"requires_axis_controls = {str(summary['candidate_materialization_requires_axis_controls']).lower()}",
        f"clear_same_geometry_groups = {summary['clear_same_geometry_groups']}",
        f"higher_positive_groups = {summary['higher_positive_groups']}",
        f"lower_positive_groups = {summary['lower_positive_groups']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Interpretation",
        "",
        "The frozen v3 contract has enough train-side `relative_vertical` capacity. The full train-side",
        "`match_rows.jsonl` scan found same-directed-pair groups where both `higher than` and",
        "`lower than` source rows exist and share the same geometry evidence. Under the frozen margin,",
        "both vertical directions have enough groups for a balanced materialization.",
        "",
        "This means the next dataset can create two rows per group:",
        "",
        "```text",
        "same G_e + higher than",
        "same G_e + lower than",
        "```",
        "",
        "with one compatible and one incompatible label. This is the target shape needed to test",
        "predicate-conditioned compatibility rather than generic geometry perturbation detection.",
        "",
        "## Support/Contact",
        "",
        "Support/contact remains secondary. The scan sees support/contact rows with numeric OBB/raw",
        "features, but not the role/orientation or visual/mesh evidence required to promote",
        "`standing on`, `lying on`, and `supported by` as the primary v3 target.",
        "",
        "## Next Materialization Policy",
        "",
    ]
    for item in plan["materialization_policy"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Axis-control note:",
            "",
            f"- high-risk axes: `{', '.join(plan.get('high_risk_axes', [])) or 'none'}`",
            f"- medium-risk axes: `{', '.join(plan.get('medium_risk_axes', [])) or 'none'}`",
        ]
    )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- train-only capacity scan",
            "- no v3 row materialization in this step",
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

    contract_summary = read_json(args.contract_dir / "summary.json")
    contract = read_json(args.contract_dir / "dataset_contract.json")
    errors = validate_inputs(contract_summary, contract, args.match_rows)

    abs_margin = float(contract["primary_family"]["initial_margin_contract"]["absolute_center_delta_z_m_min"])
    norm_margin = float(contract["primary_family"]["initial_margin_contract"]["normalized_center_delta_z_min"])

    scan = scan_match_rows(args.match_rows, abs_margin=abs_margin, norm_margin=norm_margin) if not errors else {
        "counts": Counter(),
        "vertical_groups": {},
        "group_records": [],
        "rejection_reasons": Counter(),
        "direction_counts": Counter(),
        "axis_counts": defaultdict(Counter),
        "preview_rows": [],
        "support_counts": Counter(),
        "support_distinct_pairs": defaultdict(set),
    }
    margins = [(0.05, 0.10), (0.10, 0.20), (0.15, 0.30), (0.20, 0.40), (0.30, 0.50)]
    margin_rows = build_margin_rows(scan["vertical_groups"], margins) if not errors else []
    axis_rows = axis_mixing_rows(scan["axis_counts"], len(scan["group_records"])) if not errors else []
    support_rows = support_probe_rows(scan) if not errors else []
    capacity_rows = vertical_capacity_rows(scan) if not errors else []
    plan = materialization_plan(scan, margin_rows, axis_rows) if not errors else {
        "candidate_materialization_allowed": False,
        "minimum_materialization_allowed": False,
        "candidate_materialization_requires_axis_controls": False,
        "high_risk_axes": [],
        "medium_risk_axes": [],
        "recommended_next_todo": "compatibility_dataset_v3_capacity_scan_input_repair",
        "materialization_policy": [],
    }

    if errors:
        status = STATUS_ERROR
        next_todo = "compatibility_dataset_v3_capacity_scan_input_repair"
    elif plan["candidate_materialization_allowed"]:
        status = STATUS_PASS
        next_todo = NEXT_TODO
    else:
        status = STATUS_BLOCKED
        next_todo = "compatibility_dataset_v3_contract_revision"

    direction_counts = scan["direction_counts"]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "input_contract_root": rel_path(args.contract_dir),
        "input_match_rows": rel_path(args.match_rows),
        "output_root": rel_path(args.output_dir),
        "dataset_name": EXPECTED_DATASET_NAME,
        "primary_family": "relative_vertical",
        "primary_predicates": ["higher than", "lower than"],
        "frozen_margin": {
            "abs_center_delta_z_min": abs_margin,
            "normalized_center_delta_z_min": norm_margin,
        },
        "match_rows_scanned": scan["counts"]["match_rows_scanned"],
        "relative_vertical_rows": scan["counts"]["relative_vertical_rows"],
        "relative_vertical_rows_with_raw": scan["counts"]["relative_vertical_rows_with_raw"],
        "directed_pair_groups_with_any_vertical_predicate": len(scan["vertical_groups"]),
        "clear_same_geometry_groups": len(scan["group_records"]),
        "higher_positive_groups": direction_counts["higher_positive"],
        "lower_positive_groups": direction_counts["lower_positive"],
        "balanced_group_capacity": min(direction_counts["higher_positive"], direction_counts["lower_positive"]) * 2,
        "requested_primary_geometry_groups": REQUESTED_GROUPS,
        "minimum_reportable_primary_geometry_groups": MIN_REPORTABLE_GROUPS,
        "candidate_materialization_allowed": plan["candidate_materialization_allowed"],
        "candidate_materialization_requires_axis_controls": plan["candidate_materialization_requires_axis_controls"],
        "high_risk_axes": plan["high_risk_axes"],
        "medium_risk_axes": plan["medium_risk_axes"],
        "minimum_materialization_allowed": plan["minimum_materialization_allowed"],
        "support_contact_primary_allowed": False,
        "materializes_dataset": False,
        "runs_learned_smoke": False,
        "paper_evidence_allowed": False,
        "validation_errors": len(errors),
        "boundary": {
            "capacity_scan_only": True,
            "train_only": True,
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "vertical_capacity": rel_path(args.output_dir / "vertical_capacity.csv"),
            "margin_sensitivity": rel_path(args.output_dir / "margin_sensitivity.csv"),
            "axis_mixing": rel_path(args.output_dir / "axis_mixing.csv"),
            "support_contact_probe": rel_path(args.output_dir / "support_contact_probe.csv"),
            "group_preview": rel_path(args.output_dir / "group_preview.jsonl"),
            "rejection_reasons": rel_path(args.output_dir / "rejection_reasons.csv"),
            "materialization_plan": rel_path(args.output_dir / "materialization_plan.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_csv(args.output_dir / "vertical_capacity.csv", capacity_rows)
    write_csv(args.output_dir / "margin_sensitivity.csv", margin_rows)
    write_csv(args.output_dir / "axis_mixing.csv", axis_rows)
    write_csv(args.output_dir / "support_contact_probe.csv", support_rows)
    write_csv(args.output_dir / "rejection_reasons.csv", rejection_rows(scan["rejection_reasons"]))
    write_jsonl(args.output_dir / "group_preview.jsonl", scan["preview_rows"])
    write_json(args.output_dir / "materialization_plan.json", plan)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, plan)


if __name__ == "__main__":
    main()
