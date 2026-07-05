#!/usr/bin/env python3
"""Scan capacity for the H002 v20 endpoint-balanced attachment repair target."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v17_attachment_deferred_witness_schema_capacity_scan as v17


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan"

EXPECTED_PLAN_STATUS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_repair_plan_ready_for_capacity_scan"
)
EXPECTED_PLAN_NEXT = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan"

STATUS_PASS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_capacity_scan_passed_ready_for_candidate_mining"
)
STATUS_FAIL = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_capacity_scan_blocked_capacity_or_controls"
)
STATUS_ERROR = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_capacity_scan_validation_errors"
)
NEXT_TODO_PASS = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining"
NEXT_TODO_FAIL = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_path_decision_after_capacity_scan"

PRIMARY_PREDICATES = {"attached to", "hanging on"}
DIAGNOSTIC_PREDICATES = {"connected to"}
STRUCTURAL_LABELS = {"wall", "floor", "ceiling"}

ROLE_POSITIVE = "primary_positive_anchor_proxy"
ROLE_NEGATIVE = "primary_hard_negative_proxy"
ROLE_UNCERTAIN = "primary_uncertain_proxy"
ROLE_CONNECTED_NEAR = "connected_near_or_overlap_diagnostic"
ROLE_CONNECTED_FAR = "connected_far_or_functional_ambiguous_diagnostic"

SAMPLE_SIZES = [240, 320, 400]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
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
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "expected": EXPECTED_PLAN_STATUS, "actual": plan.get("status")})
    if plan.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "expected": EXPECTED_PLAN_NEXT, "actual": plan.get("next_todo")})
    if plan.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan.get("validation_errors")})
    boundary = plan.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "hidden_fields_as_model_input",
        "uses_source_score_or_rank",
        "uses_p_geom_valid",
        "uses_geometry_status_or_rank_hint",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_violation", "key": key, "actual": boundary.get(key)})
    if plan.get("capacity_scan_required") is not True:
        errors.append({"error_type": "capacity_scan_not_required_by_plan", "actual": plan.get("capacity_scan_required")})
    return errors


def coarse_family(label: Any) -> str:
    text = v17.norm(label)
    if text in {"wall", "floor", "ceiling"}:
        return f"structural_{text}"
    if any(token in text for token in ["cabinet", "shelf", "rack", "wardrobe", "cupboard", "drawer"]):
        return "storage_or_anchor"
    if any(token in text for token in ["chair", "sofa", "bench", "stool", "bed"]):
        return "furniture_body"
    if any(token in text for token in ["table", "desk", "counter"]):
        return "table_or_work_surface"
    if any(token in text for token in ["picture", "mirror", "board", "tv", "screen", "frame"]):
        return "wall_mounted_flat_object"
    if any(token in text for token in ["curtain", "blind", "clothes", "towel", "pillow", "blanket"]):
        return "soft_or_hanging_object"
    if any(token in text for token in ["lamp", "light", "cable", "wire", "pipe", "radiator", "heater"]):
        return "device_connector_or_fixture"
    if any(token in text for token in ["plant", "vase", "decoration", "box", "basket", "book"]):
        return "movable_object"
    return "other_object"


def role_from_witness(predicate: str, witness: dict[str, Any]) -> str:
    cell_id = witness["cell_id"]
    provisional = witness["provisional_status"]
    if predicate in PRIMARY_PREDICATES:
        if provisional == "supported_candidate":
            return ROLE_POSITIVE
        if provisional == "contradicted_candidate":
            return ROLE_NEGATIVE
        return ROLE_UNCERTAIN
    if predicate == "connected to" and cell_id == "C1_connected_near_or_overlap_diagnostic":
        return ROLE_CONNECTED_NEAR
    if predicate == "connected to":
        return ROLE_CONNECTED_FAR
    return "unsupported"


def evidence_tier_from_witness(witness: dict[str, Any]) -> str:
    role = role_from_witness(witness["predicate_label"], witness)
    if role == ROLE_POSITIVE:
        return "E_pos_supported_witness"
    if role == ROLE_NEGATIVE:
        return "E_neg_counterfactual_witness"
    if role == ROLE_UNCERTAIN:
        return "E_uncertain_witness"
    if role in {ROLE_CONNECTED_NEAR, ROLE_CONNECTED_FAR}:
        return "E_connected_diagnostic_witness"
    return "E_other"


def compact_candidate(row: dict[str, Any], witness: dict[str, Any], raw_entry: dict[str, Any] | None) -> dict[str, Any]:
    identity = row.get("identity", {})
    edge = row.get("edge", {})
    semantic = row.get("semantic", {})
    rga = row.get("rga", {})
    predicate = witness["predicate_label"]
    subject_label = v17.norm(edge.get("subject_label"))
    object_label = v17.norm(edge.get("object_label"))
    visible_pair = f"{subject_label}|{object_label}"
    role = role_from_witness(predicate, witness)
    prediction_id = identity.get("prediction_id") or identity.get("row_key")
    return {
        "blind_review_id": v17.stable_id(str(prediction_id), prefix="v20cap"),
        "prediction_id": prediction_id,
        "scan_id": identity.get("scan_id"),
        "subgraph_id": identity.get("subgraph_id"),
        "directed_pair_id": identity.get("directed_pair_id"),
        "subject_id": identity.get("subject_id"),
        "object_id": identity.get("object_id"),
        "subject_label": subject_label,
        "predicate_label": predicate,
        "object_label": object_label,
        "visible_endpoint_pair": visible_pair,
        "subject_family": coarse_family(subject_label),
        "object_family": coarse_family(object_label),
        "object_family_pair": f"{coarse_family(subject_label)}|{coarse_family(object_label)}",
        "proxy_role": role,
        "capacity_evidence_tier": evidence_tier_from_witness(witness),
        "cell_id_hidden": witness["cell_id"],
        "provisional_status_hidden": witness["provisional_status"],
        "anchor_bucket_hidden": witness["anchor_bucket"],
        "rank_band_hidden": rga.get("rank_band"),
        "semantic_rank_hidden": semantic.get("rank_in_context"),
        "raw_feature_join_state": witness["raw_feature_join_state"],
        "near_contact": witness["near_contact"],
        "loose_near_contact": witness["loose_near_contact"],
        "far_separated": witness["far_separated"],
        "projected_overlap_support": witness["projected_overlap_support"],
        "uncertainty_flags": witness["uncertainty_flags"],
        "source_geometry_family": raw_entry.get("source_family") if raw_entry else None,
        "source_geometry_predicate": raw_entry.get("source_predicate") if raw_entry else None,
        "hash_key": v17.stable_int(str(prediction_id)),
    }


def add_capped(bucket: dict[Any, list[dict[str, Any]]], key: Any, row: dict[str, Any], cap: int) -> None:
    rows = bucket[key]
    rows.append(row)
    if len(rows) > cap * 2:
        rows.sort(key=lambda item: item["hash_key"])
        del rows[cap:]


def scan_pool(match_rows: Path) -> dict[str, Any]:
    pair_geometry, raw_join = v17.collect_pair_geometry(match_rows)
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    exact_groups: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    family_groups: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    scan_groups: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    role_pools: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    connected_pools: dict[str, list[dict[str, Any]]] = defaultdict(list)
    distinct: dict[str, set[str]] = defaultdict(set)
    attachment_rows = 0
    primary_rows = 0
    diagnostic_rows = 0
    joined_rows = 0

    for _, row in v17.iter_jsonl(match_rows):
        predicate_info = row.get("predicate", {})
        if predicate_info.get("predicate_family") != "attachment_deferred":
            continue
        predicate = v17.norm(predicate_info.get("predicate_label"))
        if predicate not in PRIMARY_PREDICATES and predicate not in DIAGNOSTIC_PREDICATES:
            continue
        attachment_rows += 1
        identity = row.get("identity", {})
        pair_id = identity.get("directed_pair_id")
        raw_entry = pair_geometry.get(pair_id)
        if raw_entry is not None:
            joined_rows += 1
        witness = v17.classify_attachment(row, raw_entry)
        candidate = compact_candidate(row, witness, raw_entry)
        role = candidate["proxy_role"]
        if predicate in PRIMARY_PREDICATES:
            primary_rows += 1
        else:
            diagnostic_rows += 1

        counts["predicate"][predicate] += 1
        counts["predicate_role"][f"{predicate}|{role}"] += 1
        counts["predicate_evidence_tier"][f"{predicate}|{candidate['capacity_evidence_tier']}"] += 1
        counts["role"][role] += 1
        counts["cell"][candidate["cell_id_hidden"]] += 1
        counts["anchor_bucket"][candidate["anchor_bucket_hidden"]] += 1
        counts["rank_band"][str(candidate["rank_band_hidden"])] += 1
        counts["subject_label"][candidate["subject_label"]] += 1
        counts["object_label"][candidate["object_label"]] += 1
        counts["object_family_pair"][candidate["object_family_pair"]] += 1
        counts["raw_feature_join_state"][candidate["raw_feature_join_state"]] += 1
        distinct["scan_id"].add(str(candidate["scan_id"]))
        distinct["subgraph_id"].add(str(candidate["subgraph_id"]))
        distinct["directed_pair_id"].add(str(candidate["directed_pair_id"]))
        distinct["visible_endpoint_pair"].add(candidate["visible_endpoint_pair"])

        if predicate in PRIMARY_PREDICATES and role in {ROLE_POSITIVE, ROLE_NEGATIVE, ROLE_UNCERTAIN}:
            exact_key = (predicate, candidate["visible_endpoint_pair"])
            family_key = (predicate, candidate["object_family_pair"])
            scan_key = (predicate, str(candidate["scan_id"]))
            add_capped(exact_groups[exact_key], role, candidate, cap=20)
            add_capped(family_groups[family_key], role, candidate, cap=50)
            add_capped(scan_groups[scan_key], role, candidate, cap=30)
            if role in {ROLE_POSITIVE, ROLE_NEGATIVE}:
                add_capped(role_pools, (predicate, role), candidate, cap=25000)
        elif predicate == "connected to":
            add_capped(connected_pools, role, candidate, cap=20000)

    for bucket in [exact_groups, family_groups, scan_groups, role_pools, connected_pools]:
        for rows in bucket.values():
            if isinstance(rows, dict):
                for subrows in rows.values():
                    subrows.sort(key=lambda item: item["hash_key"])
            else:
                rows.sort(key=lambda item: item["hash_key"])

    return {
        "raw_join": raw_join,
        "counts": counts,
        "distinct": {key: len(value) for key, value in distinct.items()},
        "attachment_rows": attachment_rows,
        "primary_rows": primary_rows,
        "diagnostic_rows": diagnostic_rows,
        "joined_rows": joined_rows,
        "exact_groups": exact_groups,
        "family_groups": family_groups,
        "scan_groups": scan_groups,
        "role_pools": role_pools,
        "connected_pools": connected_pools,
    }


def group_capacity_rows(groups: dict[tuple[str, str], dict[str, list[dict[str, Any]]]], group_name: str, limit: int = 200) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mixed_groups = 0
    total_balanced_pairs = 0
    by_predicate: dict[str, Counter[str]] = defaultdict(Counter)
    for (predicate, group_value), role_rows in groups.items():
        pos = len(role_rows.get(ROLE_POSITIVE, []))
        neg = len(role_rows.get(ROLE_NEGATIVE, []))
        unc = len(role_rows.get(ROLE_UNCERTAIN, []))
        balanced = min(pos, neg)
        if balanced > 0:
            mixed_groups += 1
            total_balanced_pairs += balanced
            by_predicate[predicate]["mixed_groups"] += 1
            by_predicate[predicate]["balanced_pairs"] += balanced
        rows.append(
            {
                "group_type": group_name,
                "predicate_label": predicate,
                "group_value": group_value,
                "positive_proxy_rows": pos,
                "negative_proxy_rows": neg,
                "uncertain_proxy_rows": unc,
                "balanced_pair_capacity": balanced,
                "is_mixed": balanced > 0,
            }
        )
    rows.sort(key=lambda row: (-row["balanced_pair_capacity"], row["predicate_label"], row["group_value"]))
    return rows[:limit], {
        "group_type": group_name,
        "groups": len(rows),
        "mixed_groups": mixed_groups,
        "balanced_pair_capacity": total_balanced_pairs,
        "by_predicate": {key: dict(value) for key, value in by_predicate.items()},
    }


def quotas_for_size(size: int) -> dict[str, int]:
    primary_rows = int(size * 0.80)
    primary_rows -= primary_rows % 4
    diagnostic_rows = size - primary_rows
    half_diag = diagnostic_rows // 2
    per_primary_cell = primary_rows // 4
    return {
        "attached to|" + ROLE_POSITIVE: per_primary_cell,
        "attached to|" + ROLE_NEGATIVE: per_primary_cell,
        "hanging on|" + ROLE_POSITIVE: per_primary_cell,
        "hanging on|" + ROLE_NEGATIVE: per_primary_cell,
        "connected to|" + ROLE_CONNECTED_NEAR: half_diag,
        "connected to|" + ROLE_CONNECTED_FAR: diagnostic_rows - half_diag,
    }


def can_select(row: dict[str, Any], state: dict[str, Any], quotas: dict[str, int], caps: dict[str, Any]) -> str | None:
    pred_role = f"{row['predicate_label']}|{row['proxy_role']}"
    if state["quota_counts"][pred_role] >= quotas.get(pred_role, 0):
        return "quota_full"
    if row["prediction_id"] in state["selected_ids"]:
        return "duplicate_prediction"
    if state["scan"][str(row["scan_id"])] >= caps["max_rows_per_scan"]:
        return "max_rows_per_scan"
    if state["subgraph"][str(row["subgraph_id"])] >= caps["max_rows_per_subgraph"]:
        return "max_rows_per_subgraph"
    if state["visible_pair"][row["visible_endpoint_pair"]] >= caps["max_rows_per_visible_endpoint_pair"]:
        return "max_rows_per_visible_endpoint_pair"
    if state["subject_label"][row["subject_label"]] >= caps["max_rows_per_subject_label"]:
        return "max_rows_per_subject_label"
    if state["object_label"][row["object_label"]] >= caps["max_rows_per_object_label"]:
        return "max_rows_per_object_label"
    pred_tier = f"{row['predicate_label']}|{row['capacity_evidence_tier']}"
    if state["predicate_evidence_tier"][pred_tier] >= caps["max_rows_per_predicate_evidence_tier_cell"]:
        return "max_rows_per_predicate_evidence_tier_cell"
    total_after = len(state["selected"]) + 1
    if row["subject_label"] in STRUCTURAL_LABELS:
        structural_subject_after = state["structural_subject_rows"] + 1
        if structural_subject_after / total_after > caps["max_wall_or_floor_or_ceiling_subject_share"]:
            return "max_structural_subject_share"
    if row["object_label"] in STRUCTURAL_LABELS:
        structural_object_after = state["structural_object_rows"] + 1
        if structural_object_after / total_after > caps["max_wall_or_floor_or_ceiling_object_share"]:
            return "max_structural_object_share"
    return None


def select_row(row: dict[str, Any], state: dict[str, Any]) -> None:
    pred_role = f"{row['predicate_label']}|{row['proxy_role']}"
    state["selected"].append(row)
    state["selected_ids"].add(row["prediction_id"])
    state["quota_counts"][pred_role] += 1
    state["scan"][str(row["scan_id"])] += 1
    state["subgraph"][str(row["subgraph_id"])] += 1
    state["visible_pair"][row["visible_endpoint_pair"]] += 1
    state["subject_label"][row["subject_label"]] += 1
    state["object_label"][row["object_label"]] += 1
    state["predicate_evidence_tier"][f"{row['predicate_label']}|{row['capacity_evidence_tier']}"] += 1
    state["role"][row["proxy_role"]] += 1
    state["predicate"][row["predicate_label"]] += 1
    state["route_level"][row["selection_route_level"]] += 1
    if row["subject_label"] in STRUCTURAL_LABELS:
        state["structural_subject_rows"] += 1
    if row["object_label"] in STRUCTURAL_LABELS:
        state["structural_object_rows"] += 1


def init_selection_state() -> dict[str, Any]:
    return {
        "selected": [],
        "selected_ids": set(),
        "quota_counts": Counter(),
        "scan": Counter(),
        "subgraph": Counter(),
        "visible_pair": Counter(),
        "subject_label": Counter(),
        "object_label": Counter(),
        "predicate_evidence_tier": Counter(),
        "role": Counter(),
        "predicate": Counter(),
        "route_level": Counter(),
        "skip_reasons": Counter(),
        "structural_subject_rows": 0,
        "structural_object_rows": 0,
    }


def need_more(state: dict[str, Any], quotas: dict[str, int], pred_role: str) -> bool:
    return state["quota_counts"][pred_role] < quotas.get(pred_role, 0)


def try_add(row: dict[str, Any], state: dict[str, Any], quotas: dict[str, int], caps: dict[str, Any], route_level: str) -> bool:
    row = {**row, "selection_route_level": route_level}
    reason = can_select(row, state, quotas, caps)
    if reason is not None:
        state["skip_reasons"][f"{route_level}:{reason}"] += 1
        return False
    select_row(row, state)
    return True


def select_preview(
    size: int,
    scan: dict[str, Any],
    caps: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    quotas = quotas_for_size(size)
    state = init_selection_state()

    def consume_group_pairs(groups: dict[tuple[str, str], dict[str, list[dict[str, Any]]]], route_level: str) -> None:
        ordered_groups = sorted(
            groups.items(),
            key=lambda item: (
                -min(len(item[1].get(ROLE_POSITIVE, [])), len(item[1].get(ROLE_NEGATIVE, []))),
                item[0][0],
                item[0][1],
            ),
        )
        for (predicate, _), role_rows in ordered_groups:
            pos_key = f"{predicate}|{ROLE_POSITIVE}"
            neg_key = f"{predicate}|{ROLE_NEGATIVE}"
            if not need_more(state, quotas, pos_key) and not need_more(state, quotas, neg_key):
                continue
            positives = role_rows.get(ROLE_POSITIVE, [])
            negatives = role_rows.get(ROLE_NEGATIVE, [])
            for pos, neg in zip(positives, negatives):
                if need_more(state, quotas, pos_key):
                    try_add(pos, state, quotas, caps, route_level)
                if need_more(state, quotas, neg_key):
                    try_add(neg, state, quotas, caps, route_level)
                if not need_more(state, quotas, pos_key) and not need_more(state, quotas, neg_key):
                    break

    consume_group_pairs(scan["exact_groups"], "E1_exact_visible_endpoint_pair")
    consume_group_pairs(scan["family_groups"], "E2_object_family_predicate")
    consume_group_pairs(scan["scan_groups"], "E3_scan_balanced_counterfactual")

    for pred_role, quota in quotas.items():
        predicate, role = pred_role.split("|", 1)
        if role in {ROLE_CONNECTED_NEAR, ROLE_CONNECTED_FAR}:
            rows = scan["connected_pools"].get(role, [])
        else:
            rows = scan["role_pools"].get((predicate, role), [])
        for row in rows:
            if state["quota_counts"][pred_role] >= quota:
                break
            try_add(row, state, quotas, caps, "E4_global_hard_negative_or_diagnostic_fallback")

    deficits = {key: quota - state["quota_counts"][key] for key, quota in quotas.items() if quota - state["quota_counts"][key] > 0}
    selected = state["selected"]
    summary = {
        "sample_size": size,
        "selected_rows": len(selected),
        "quotas": quotas,
        "quota_counts": dict(state["quota_counts"]),
        "quota_deficits": deficits,
        "selected_by_role": dict(state["role"]),
        "selected_by_predicate": dict(state["predicate"]),
        "selected_by_route_level": dict(state["route_level"]),
        "selected_unique_scans": len(state["scan"]),
        "selected_unique_subgraphs": len(state["subgraph"]),
        "selected_unique_visible_pairs": len(state["visible_pair"]),
        "selected_subject_label_top": state["subject_label"].most_common(12),
        "selected_object_label_top": state["object_label"].most_common(12),
        "selected_predicate_evidence_tier": dict(state["predicate_evidence_tier"]),
        "structural_subject_share": round(state["structural_subject_rows"] / len(selected), 6) if selected else 0.0,
        "structural_object_share": round(state["structural_object_rows"] / len(selected), 6) if selected else 0.0,
        "skip_reasons": dict(state["skip_reasons"]),
        "caps": caps,
        "feasible": len(selected) == size and not deficits,
    }
    return selected, summary


def counter_rows(counter: Counter[str], key_name: str = "key", limit: int | None = None) -> list[dict[str, Any]]:
    rows = [{key_name: key, "rows": value} for key, value in counter.most_common(limit)]
    return rows


def build_capacity_tables(scan: dict[str, Any]) -> dict[str, Any]:
    exact_rows, exact_summary = group_capacity_rows(scan["exact_groups"], "exact_visible_endpoint_pair")
    family_rows, family_summary = group_capacity_rows(scan["family_groups"], "object_family_pair")
    scan_rows, scan_summary = group_capacity_rows(scan["scan_groups"], "scan_predicate")
    return {
        "exact_endpoint_pair_rows": exact_rows,
        "exact_endpoint_pair_summary": exact_summary,
        "object_family_rows": family_rows,
        "object_family_summary": family_summary,
        "scan_balanced_rows": scan_rows,
        "scan_balanced_summary": scan_summary,
    }


def capacity_decision(
    validation_errors: list[dict[str, Any]],
    tables: dict[str, Any],
    previews: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    exact = tables["exact_endpoint_pair_summary"]
    family = tables["object_family_summary"]
    scan_balanced = tables["scan_balanced_summary"]
    preview_320 = previews[320]
    checks = {
        "validation_errors_zero": len(validation_errors) == 0,
        "exact_mixed_groups_min_30": exact["mixed_groups"] >= 30,
        "object_family_mixed_groups_min_40": family["mixed_groups"] >= 40,
        "scan_balanced_blocks_min_40": scan_balanced["mixed_groups"] >= 40,
        "preview_320_feasible": preview_320["feasible"],
        "post_label_proxy_accept_min_60": (
            preview_320["selected_by_role"].get(ROLE_POSITIVE, 0) >= 60
            and preview_320["selected_by_role"].get(ROLE_NEGATIVE, 0) >= 60
        ),
        "attached_and_hanging_each_proxy_min_25": all(
            preview_320["quota_counts"].get(f"{predicate}|{role}", 0) >= 25
            for predicate in ["attached to", "hanging on"]
            for role in [ROLE_POSITIVE, ROLE_NEGATIVE]
        ),
        "connected_diagnostic_not_primary": True,
    }
    passed = (
        checks["validation_errors_zero"]
        and checks["preview_320_feasible"]
        and checks["post_label_proxy_accept_min_60"]
        and checks["attached_and_hanging_each_proxy_min_25"]
        and (
            checks["exact_mixed_groups_min_30"]
            or checks["object_family_mixed_groups_min_40"]
            or checks["scan_balanced_blocks_min_40"]
        )
    )
    if checks["exact_mixed_groups_min_30"]:
        selected_route = "exact_endpoint_pair_mixed_contrast_primary"
    elif checks["object_family_mixed_groups_min_40"]:
        selected_route = "object_family_predicate_evidence_tier_fallback"
    elif checks["scan_balanced_blocks_min_40"]:
        selected_route = "scan_balanced_counterfactual_fallback"
    else:
        selected_route = "blocked_no_contrast_route"
    return {
        "capacity_pass": passed,
        "selected_capacity_route": selected_route,
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
        "next_todo": NEXT_TODO_PASS if passed else NEXT_TODO_FAIL,
    }


def sanitize_preview_row(row: dict[str, Any]) -> dict[str, Any]:
    keep = [
        "blind_review_id",
        "prediction_id",
        "scan_id",
        "subgraph_id",
        "directed_pair_id",
        "subject_id",
        "object_id",
        "subject_label",
        "predicate_label",
        "object_label",
        "visible_endpoint_pair",
        "subject_family",
        "object_family",
        "object_family_pair",
        "proxy_role",
        "capacity_evidence_tier",
        "cell_id_hidden",
        "provisional_status_hidden",
        "anchor_bucket_hidden",
        "rank_band_hidden",
        "selection_route_level",
        "near_contact",
        "loose_near_contact",
        "far_separated",
        "projected_overlap_support",
        "uncertainty_flags",
    ]
    return {key: row.get(key) for key in keep}


def write_report(path: Path, summary: dict[str, Any]) -> None:
    decision = summary["capacity_decision"]
    lines = [
        "# H002 V20 Attachment Endpoint-Balanced Capacity Scan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"capacity_pass = {decision['capacity_pass']}",
        f"selected_capacity_route = {decision['selected_capacity_route']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Pool",
        "",
        "```text",
        f"attachment_rows = {summary['counts']['attachment_rows']}",
        f"primary_rows = {summary['counts']['primary_rows']}",
        f"diagnostic_rows = {summary['counts']['diagnostic_rows']}",
        f"raw_feature_join_coverage = {summary['counts']['raw_feature_join_coverage']:.6f}",
        f"distinct_visible_endpoint_pairs = {summary['counts']['distinct']['visible_endpoint_pair']}",
        "```",
        "",
        "## Contrast Capacity",
        "",
        "```text",
        f"exact_endpoint_pair_mixed_groups = {summary['contrast_capacity']['exact_endpoint_pair_summary']['mixed_groups']}",
        f"exact_endpoint_pair_balanced_pairs = {summary['contrast_capacity']['exact_endpoint_pair_summary']['balanced_pair_capacity']}",
        f"object_family_mixed_groups = {summary['contrast_capacity']['object_family_summary']['mixed_groups']}",
        f"object_family_balanced_pairs = {summary['contrast_capacity']['object_family_summary']['balanced_pair_capacity']}",
        f"scan_balanced_mixed_blocks = {summary['contrast_capacity']['scan_balanced_summary']['mixed_groups']}",
        f"scan_balanced_pairs = {summary['contrast_capacity']['scan_balanced_summary']['balanced_pair_capacity']}",
        "```",
        "",
        "## Preview Feasibility",
        "",
    ]
    for size, preview in summary["sample_size_feasibility"].items():
        lines.extend(
            [
                f"### N={size}",
                "",
                "```text",
                f"selected_rows = {preview['selected_rows']}",
                f"feasible = {preview['feasible']}",
                f"quota_deficits = {preview['quota_deficits']}",
                f"selected_by_role = {preview['selected_by_role']}",
                f"selected_by_route_level = {preview['selected_by_route_level']}",
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- Train-only capacity scan.",
            "- No labels were filled.",
            "- No candidate sheet was released.",
            "- No posterior was trained.",
            "- Multi-view/mesh remains audit/confirmation evidence only.",
            "- Hidden fields in preview files are internal capacity-audit fields only.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    plan_dir = as_abs(args.plan_dir)
    match_rows = as_abs(args.match_rows)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plan = read_json(plan_dir / "summary.json")
    validation_errors = validate_plan(plan)
    scan = scan_pool(match_rows)
    tables = build_capacity_tables(scan)

    caps = read_json(plan_dir / "sampling_contract.json")["caps"]
    previews: dict[int, dict[str, Any]] = {}
    preview_rows_by_size: dict[int, list[dict[str, Any]]] = {}
    for size in SAMPLE_SIZES:
        rows, preview = select_preview(size, scan, caps)
        previews[size] = preview
        preview_rows_by_size[size] = [sanitize_preview_row(row) for row in rows]

    decision = capacity_decision(validation_errors, tables, previews)
    status = STATUS_ERROR if validation_errors else (STATUS_PASS if decision["capacity_pass"] else STATUS_FAIL)
    next_todo = decision["next_todo"]

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "capacity_by_predicate_role": output_dir / "capacity_by_predicate_role.csv",
        "exact_endpoint_pair_mixed_capacity": output_dir / "exact_endpoint_pair_mixed_capacity.csv",
        "object_family_mixed_capacity": output_dir / "object_family_mixed_capacity.csv",
        "scan_balanced_counterfactual_capacity": output_dir / "scan_balanced_counterfactual_capacity.csv",
        "sample_size_feasibility": output_dir / "sample_size_feasibility.json",
        "preview_internal_240": output_dir / "preview_internal_240.jsonl",
        "preview_internal_320": output_dir / "preview_internal_320.jsonl",
        "preview_internal_400": output_dir / "preview_internal_400.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    counts = {
        "attachment_rows": scan["attachment_rows"],
        "primary_rows": scan["primary_rows"],
        "diagnostic_rows": scan["diagnostic_rows"],
        "joined_rows": scan["joined_rows"],
        "raw_feature_join_coverage": scan["joined_rows"] / scan["attachment_rows"] if scan["attachment_rows"] else 0.0,
        "predicate_counts": dict(scan["counts"]["predicate"]),
        "predicate_role_counts": dict(scan["counts"]["predicate_role"]),
        "predicate_evidence_tier_counts": dict(scan["counts"]["predicate_evidence_tier"]),
        "role_counts": dict(scan["counts"]["role"]),
        "cell_counts": dict(scan["counts"]["cell"]),
        "anchor_bucket_counts": dict(scan["counts"]["anchor_bucket"]),
        "rank_band_counts": dict(scan["counts"]["rank_band"]),
        "distinct": scan["distinct"],
    }
    summary = {
        "schema_version": "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "repair_plan_summary": rel_path(plan_dir / "summary.json"),
            "match_rows": rel_path(match_rows),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": counts,
        "raw_feature_join_summary": scan["raw_join"],
        "contrast_capacity": {
            "exact_endpoint_pair_summary": tables["exact_endpoint_pair_summary"],
            "object_family_summary": tables["object_family_summary"],
            "scan_balanced_summary": tables["scan_balanced_summary"],
        },
        "sample_size_feasibility": {str(key): value for key, value in previews.items()},
        "capacity_decision": decision,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "candidate_sheet_created": False,
            "internal_capacity_previews_created": True,
            "hidden_fields_as_model_input": False,
            "uses_source_score_or_rank": False,
            "uses_p_geom_valid": False,
            "uses_geometry_status_or_rank_hint": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_or_mesh_as_audit_or_confirmation_evidence_only": True,
        },
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["sample_size_feasibility"], summary["sample_size_feasibility"])
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_csv(output_paths["capacity_by_predicate_role"], counter_rows(scan["counts"]["predicate_role"], "predicate_role"))
    write_csv(output_paths["exact_endpoint_pair_mixed_capacity"], tables["exact_endpoint_pair_rows"])
    write_csv(output_paths["object_family_mixed_capacity"], tables["object_family_rows"])
    write_csv(output_paths["scan_balanced_counterfactual_capacity"], tables["scan_balanced_rows"])
    for size, rows in preview_rows_by_size.items():
        write_jsonl(output_paths[f"preview_internal_{size}"], rows)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    decision = summary["capacity_decision"]
    print(f"status={summary['status']}")
    print(f"capacity_pass={decision['capacity_pass']}")
    print(f"selected_capacity_route={decision['selected_capacity_route']}")
    print(f"exact_mixed_groups={summary['contrast_capacity']['exact_endpoint_pair_summary']['mixed_groups']}")
    print(f"object_family_mixed_groups={summary['contrast_capacity']['object_family_summary']['mixed_groups']}")
    print(f"scan_balanced_mixed_blocks={summary['contrast_capacity']['scan_balanced_summary']['mixed_groups']}")
    print(f"preview_320_feasible={summary['sample_size_feasibility']['320']['feasible']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
