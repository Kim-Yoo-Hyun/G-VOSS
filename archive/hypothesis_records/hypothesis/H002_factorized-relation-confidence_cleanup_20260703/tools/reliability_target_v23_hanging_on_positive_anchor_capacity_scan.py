#!/usr/bin/env python3
"""Scan full-train capacity for the H002 v23 hanging-on positive-anchor route."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v17_attachment_deferred_witness_schema_capacity_scan as v17
import reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan as v20
import reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan as v21


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v23_hanging_on_positive_anchor_repair_plan"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v23_hanging_on_positive_anchor_capacity_scan"

EXPECTED_PLAN_STATUS = "h002_reliability_target_v23_hanging_on_positive_anchor_repair_plan_ready_for_capacity_scan"
EXPECTED_PLAN_NEXT = "reliability_target_v23_hanging_on_positive_anchor_capacity_scan"

STATUS_READY = "h002_reliability_target_v23_hanging_on_positive_anchor_capacity_scan_ready_for_candidate_mining"
STATUS_BLOCKED = "h002_reliability_target_v23_hanging_on_positive_anchor_capacity_scan_blocked_no_matched_positive_anchor_capacity"
STATUS_ERROR = "h002_reliability_target_v23_hanging_on_positive_anchor_capacity_scan_validation_errors"

NEXT_TODO_READY = "reliability_target_v23_hanging_on_positive_anchor_candidate_mining"
NEXT_TODO_BLOCKED = "reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis"

PRIMARY_PREDICATE = "hanging on"
DIAGNOSTIC_PREDICATES = {"attached to", "connected to"}

ROLE_POSITIVE = "positive_anchor_proxy"
ROLE_NEGATIVE = "hard_negative_proxy"
ROLE_UNCERTAIN = "uncertain_or_out_of_scope_proxy"

SOFT_HANGING_SUBJECTS = {
    "backpack",
    "bag",
    "blinds",
    "cloth",
    "clothes",
    "coat",
    "curtain",
    "jacket",
    "towel",
}
HANGING_ANCHORS = {
    "blinds",
    "cabinet",
    "door",
    "doorframe",
    "handle",
    "hook",
    "rack",
    "rail",
    "rod",
    "stand",
    "window",
}
SUPPORT_CONFOUND_ANCHORS = {"bed", "bench", "chair", "couch", "desk", "floor", "shelf", "sofa", "table"}
GENERIC_LABELS = {"item", "object", "thing"}

SELECTED_SPEC = "same_affordance_rank_coverage"
STRICT_GEOMETRY_SPEC = "same_affordance_rank_geometry_coverage"
PREVIEW_TARGET_ROWS = 240

GROUP_SPECS: list[tuple[str, list[str]]] = [
    ("same_affordance", ["subject_affordance_family", "anchor_affordance_family"]),
    ("same_affordance_rank", ["subject_affordance_family", "anchor_affordance_family", "rank_band"]),
    ("same_affordance_rank_coverage", ["subject_affordance_family", "anchor_affordance_family", "rank_band", "coverage_proxy"]),
    (
        "same_affordance_rank_geometry",
        ["subject_affordance_family", "anchor_affordance_family", "rank_band", "geometry_bucket"],
    ),
    (
        "same_affordance_rank_geometry_coverage",
        ["subject_affordance_family", "anchor_affordance_family", "rank_band", "geometry_bucket", "coverage_proxy"],
    ),
    ("same_subject_label_anchor_rank_coverage", ["subject_label", "anchor_affordance_family", "rank_band", "coverage_proxy"]),
    ("same_object_label_subject_rank_coverage", ["object_label", "subject_affordance_family", "rank_band", "coverage_proxy"]),
    ("same_subject_object_rank", ["subject_label", "object_label", "rank_band"]),
    ("same_visible_endpoint_pair", ["visible_endpoint_pair"]),
    ("same_scan_affordance_rank", ["scan_id", "subject_affordance_family", "anchor_affordance_family", "rank_band"]),
]


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
        seen: set[str] = set()
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_plan(plan_summary: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "expected": EXPECTED_PLAN_STATUS, "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "expected": EXPECTED_PLAN_NEXT, "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    boundary = plan_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "fills_new_labels",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_violation", "key": key, "actual": boundary.get(key)})
    if contract.get("primary_predicate") != PRIMARY_PREDICATE:
        errors.append({"error_type": "unexpected_primary_predicate", "expected": PRIMARY_PREDICATE, "actual": contract.get("primary_predicate")})
    if contract.get("validation_or_test_allowed") is not False:
        errors.append({"error_type": "validation_or_test_not_blocked", "actual": contract.get("validation_or_test_allowed")})
    if contract.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "posterior_smoke_not_blocked", "actual": contract.get("posterior_smoke_allowed")})
    return errors


def subject_affordance(label: str) -> str:
    label = v17.norm(label)
    if label in SOFT_HANGING_SUBJECTS:
        return "soft_hanging_subject"
    if label in GENERIC_LABELS:
        return "generic_subject"
    return "non_hanging_or_uncertain_subject"


def anchor_affordance(label: str) -> str:
    label = v17.norm(label)
    if label in HANGING_ANCHORS:
        return "hanging_anchor_candidate"
    if label in SUPPORT_CONFOUND_ANCHORS:
        return "support_or_furniture_confound_anchor"
    if label in GENERIC_LABELS:
        return "generic_anchor"
    return "uncertain_anchor"


def is_nonfar_joined_geometry(candidate: dict[str, Any]) -> bool:
    return candidate["raw_feature_join_state"] == "joined" and candidate["geometry_bucket"] not in {
        "far_separated",
        "geometry_missing",
    }


def v23_proxy_role(candidate: dict[str, Any]) -> str:
    if candidate["predicate_label"] != PRIMARY_PREDICATE:
        return ROLE_UNCERTAIN
    positive_cell = candidate["is_positive_anchor_candidate_cell"]
    base_role = candidate["reliability_proxy_role"]
    if positive_cell and base_role == v21.ROLE_ACCEPT_PROXY and is_nonfar_joined_geometry(candidate):
        return ROLE_POSITIVE
    if positive_cell and base_role == v21.ROLE_REJECT_PROXY:
        return ROLE_NEGATIVE
    return ROLE_UNCERTAIN


def candidate_from_row(row: dict[str, Any], witness: dict[str, Any], raw_entry: dict[str, Any] | None) -> dict[str, Any]:
    candidate = v21.candidate_from_row(row, witness, raw_entry)
    subj_aff = subject_affordance(candidate["subject_label"])
    anch_aff = anchor_affordance(candidate["object_label"])
    candidate["subject_affordance_family"] = subj_aff
    candidate["anchor_affordance_family"] = anch_aff
    candidate["is_positive_anchor_candidate_cell"] = (
        subj_aff == "soft_hanging_subject" and anch_aff == "hanging_anchor_candidate"
    )
    candidate["v23_proxy_role"] = v23_proxy_role(candidate)
    candidate["v23_selection_role"] = candidate["v23_proxy_role"]
    candidate["v23_capacity_evidence"] = (
        "positive_anchor_nonfar_joined"
        if candidate["v23_proxy_role"] == ROLE_POSITIVE
        else "positive_anchor_hard_negative"
        if candidate["v23_proxy_role"] == ROLE_NEGATIVE
        else "not_capacity_role"
    )
    return candidate


def group_key(candidate: dict[str, Any], fields: list[str]) -> tuple[str, ...]:
    return tuple(str(candidate.get(field)) for field in fields)


def add_group_sample(group: dict[str, Any], candidate: dict[str, Any]) -> None:
    role = candidate["v23_proxy_role"]
    if role not in {ROLE_POSITIVE, ROLE_NEGATIVE}:
        return
    samples = group["samples"][role]
    if len(samples) >= 3:
        return
    samples.append(
        {
            "prediction_id": candidate["prediction_id"],
            "scan_id": candidate["scan_id"],
            "subject_label": candidate["subject_label"],
            "predicate_label": candidate["predicate_label"],
            "object_label": candidate["object_label"],
            "rank_band": candidate["rank_band"],
            "geometry_bucket": candidate["geometry_bucket"],
            "coverage_proxy": candidate["coverage_proxy"],
            "anchor_bucket": candidate["anchor_bucket_hidden"],
            "subject_affordance_family": candidate["subject_affordance_family"],
            "anchor_affordance_family": candidate["anchor_affordance_family"],
            "gt_label_match_status": candidate["gt_label_match_status"],
        }
    )


def update_group(group: dict[str, Any], candidate: dict[str, Any]) -> None:
    role = candidate["v23_proxy_role"]
    group["rows"] += 1
    group["role_counts"][role] += 1
    group["rank_counts"][candidate["rank_band"]] += 1
    group["geometry_counts"][candidate["geometry_bucket"]] += 1
    group["coverage_counts"][candidate["coverage_proxy"]] += 1
    group["subject_counts"][candidate["subject_label"]] += 1
    group["object_counts"][candidate["object_label"]] += 1
    add_group_sample(group, candidate)


def finalize_group(spec_name: str, fields: list[str], values: tuple[str, ...], group: dict[str, Any]) -> dict[str, Any]:
    positive = int(group["role_counts"].get(ROLE_POSITIVE, 0))
    negative = int(group["role_counts"].get(ROLE_NEGATIVE, 0))
    uncertain = int(group["role_counts"].get(ROLE_UNCERTAIN, 0))
    balanced_pairs = min(positive, negative)
    return {
        "spec_name": spec_name,
        "fields": ",".join(fields),
        "group_value": " | ".join(values),
        "rows": int(group["rows"]),
        "positive_anchor_proxy_rows": positive,
        "hard_negative_proxy_rows": negative,
        "uncertain_or_out_of_scope_rows": uncertain,
        "balanced_pair_capacity": balanced_pairs,
        "balanced_proxy_row_capacity": balanced_pairs * 2,
        "is_positive_negative_mixed": balanced_pairs > 0,
        "rank_counts": dict(group["rank_counts"]),
        "geometry_counts": dict(group["geometry_counts"]),
        "coverage_counts": dict(group["coverage_counts"]),
        "subject_top": group["subject_counts"].most_common(5),
        "object_top": group["object_counts"].most_common(5),
        "samples": {key: value for key, value in group["samples"].items()},
    }


def sanitize_selection_row(row: dict[str, Any]) -> dict[str, Any]:
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
        "subject_affordance_family",
        "anchor_affordance_family",
        "v23_proxy_role",
        "v23_capacity_evidence",
        "rank_band",
        "rank_band_hidden",
        "semantic_rank",
        "geometry_bucket",
        "coverage_proxy",
        "uncertainty_bucket",
        "capacity_evidence_tier",
        "cell_id_hidden",
        "provisional_status_hidden",
        "anchor_bucket_hidden",
        "gt_label_match_status",
        "raw_feature_join_state",
        "near_contact",
        "loose_near_contact",
        "far_separated",
        "projected_overlap_support",
        "uncertainty_flags",
        "hash_key",
    ]
    return {key: row.get(key) for key in keep}


def add_if_allowed(row: dict[str, Any], selected: list[dict[str, Any]], state: dict[str, Counter[str]], caps: dict[str, int]) -> bool:
    role = row["v23_proxy_role"]
    prediction_id = str(row["prediction_id"])
    if state["prediction_id"][prediction_id] >= 1:
        return False
    if state["role"][role] >= caps["per_role"]:
        return False
    if state["subject_label"][row["subject_label"]] >= caps["subject_label"]:
        return False
    if state["object_label"][row["object_label"]] >= caps["object_label"]:
        return False
    if state["scan_id"][str(row["scan_id"])] >= caps["scan_id"]:
        return False
    if state["visible_endpoint_pair"][row["visible_endpoint_pair"]] >= caps["visible_endpoint_pair"]:
        return False
    selected.append(row)
    state["role"][role] += 1
    state["subject_label"][row["subject_label"]] += 1
    state["object_label"][row["object_label"]] += 1
    state["scan_id"][str(row["scan_id"])] += 1
    state["visible_endpoint_pair"][row["visible_endpoint_pair"]] += 1
    state["rank_band"][row["rank_band"]] += 1
    state["geometry_bucket"][row["geometry_bucket"]] += 1
    state["coverage_proxy"][row["coverage_proxy"]] += 1
    state["gt_label_match_status"][row["gt_label_match_status"]] += 1
    state["prediction_id"][prediction_id] += 1
    return True


def build_selection_preview(
    selected_groups: dict[tuple[str, ...], dict[str, list[dict[str, Any]]]],
    gates: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target = PREVIEW_TARGET_ROWS
    caps = {
        "per_role": target // 2,
        "subject_label": max(1, int(target * float(gates["max_single_subject_label_share"]))),
        "object_label": max(1, int(target * float(gates["max_single_object_label_share"]))),
        "scan_id": max(1, int(target * float(gates["max_single_scan_share"]))),
        "visible_endpoint_pair": max(1, int(target * float(gates["max_visible_endpoint_pair_share"]))),
    }
    state: dict[str, Counter[str]] = defaultdict(Counter)
    selected: list[dict[str, Any]] = []

    sortable_groups = []
    for values, roles in selected_groups.items():
        pos = sorted(roles.get(ROLE_POSITIVE, []), key=lambda row: row["hash_key"])
        neg = sorted(roles.get(ROLE_NEGATIVE, []), key=lambda row: row["hash_key"])
        if not pos or not neg:
            continue
        sortable_groups.append((min(len(pos), len(neg)), values, pos, neg))
    sortable_groups.sort(key=lambda item: (-item[0], item[1]))

    exhausted = False
    while len(selected) < target and not exhausted:
        exhausted = True
        for _, _, pos_rows, neg_rows in sortable_groups:
            if len(selected) >= target:
                break
            for role_rows in (pos_rows, neg_rows):
                if len(selected) >= target:
                    break
                for row in role_rows:
                    if add_if_allowed(row, selected, state, caps):
                        exhausted = False
                        break

    role_counts = dict(state["role"])
    geometry_counts = dict(state["geometry_bucket"])
    rank_counts = dict(state["rank_band"])
    summary = {
        "target_rows": target,
        "selected_rows": len(selected),
        "selected_by_role": role_counts,
        "selected_rank_band_counts": rank_counts,
        "selected_geometry_bucket_counts": geometry_counts,
        "selected_coverage_proxy_counts": dict(state["coverage_proxy"]),
        "selected_gt_label_match_status_counts": dict(state["gt_label_match_status"]),
        "selected_subject_label_top": state["subject_label"].most_common(12),
        "selected_object_label_top": state["object_label"].most_common(12),
        "selected_scan_top": state["scan_id"].most_common(8),
        "selected_visible_endpoint_pair_top": state["visible_endpoint_pair"].most_common(8),
        "cap_rows": caps,
        "geometry_bucket_coverage": len(geometry_counts),
        "rank_band_coverage": len(rank_counts),
        "role_balance_min": min(role_counts.get(ROLE_POSITIVE, 0), role_counts.get(ROLE_NEGATIVE, 0)),
        "feasible_min_160_rows": len(selected) >= int(gates["balanced_proxy_capacity_min"]),
    }
    return [sanitize_selection_row(row) for row in selected], summary


def scan_full_train(match_rows: Path) -> dict[str, Any]:
    pair_geometry, raw_join = v17.collect_pair_geometry(match_rows)
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    distinct: dict[str, set[str]] = defaultdict(set)
    groups: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    selected_groups: dict[tuple[str, ...], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    diagnostic_rows = 0
    primary_rows = 0

    for _, row in v17.iter_jsonl(match_rows):
        predicate = v17.norm(row.get("predicate", {}).get("predicate_label"))
        family = row.get("predicate", {}).get("predicate_family")
        if family != "attachment_deferred":
            continue
        if predicate != PRIMARY_PREDICATE and predicate not in DIAGNOSTIC_PREDICATES:
            continue
        identity = row.get("identity", {})
        raw_entry = pair_geometry.get(identity.get("directed_pair_id"))
        witness = v17.classify_attachment(row, raw_entry)
        if predicate in DIAGNOSTIC_PREDICATES:
            diagnostic_rows += 1
            counts["diagnostic_predicate"][predicate] += 1
            counts["diagnostic_cell"][witness["cell_id"]] += 1
            continue

        primary_rows += 1
        candidate = candidate_from_row(row, witness, raw_entry)
        role = candidate["v23_proxy_role"]
        counts["predicate"][predicate] += 1
        counts["v23_proxy_role"][role] += 1
        counts["base_reliability_proxy_role"][candidate["reliability_proxy_role"]] += 1
        counts["subject_affordance_family"][candidate["subject_affordance_family"]] += 1
        counts["anchor_affordance_family"][candidate["anchor_affordance_family"]] += 1
        counts["positive_anchor_cell"][str(candidate["is_positive_anchor_candidate_cell"])] += 1
        counts["rank_band"][candidate["rank_band"]] += 1
        counts["geometry_bucket"][candidate["geometry_bucket"]] += 1
        counts["coverage_proxy"][candidate["coverage_proxy"]] += 1
        counts["uncertainty_bucket"][candidate["uncertainty_bucket"]] += 1
        counts["gt_label_match_status"][candidate["gt_label_match_status"]] += 1
        counts["subject_label"][candidate["subject_label"]] += 1
        counts["object_label"][candidate["object_label"]] += 1
        counts["subject_object_label"][f"{candidate['subject_label']}|{candidate['object_label']}"] += 1
        if candidate["is_positive_anchor_candidate_cell"]:
            counts["positive_anchor_cell_role"][role] += 1
            counts["positive_anchor_cell_subject_label"][candidate["subject_label"]] += 1
            counts["positive_anchor_cell_object_label"][candidate["object_label"]] += 1
            counts["positive_anchor_cell_rank_band"][candidate["rank_band"]] += 1
            counts["positive_anchor_cell_geometry_bucket"][candidate["geometry_bucket"]] += 1
        if role in {ROLE_POSITIVE, ROLE_NEGATIVE}:
            distinct["selected_role_scan_id"].add(str(candidate["scan_id"]))
            distinct["selected_role_visible_endpoint_pair"].add(candidate["visible_endpoint_pair"])
            distinct["selected_role_directed_pair_id"].add(str(candidate["directed_pair_id"]))
        distinct["scan_id"].add(str(candidate["scan_id"]))
        distinct["visible_endpoint_pair"].add(candidate["visible_endpoint_pair"])
        distinct["directed_pair_id"].add(str(candidate["directed_pair_id"]))

        for spec_name, fields in GROUP_SPECS:
            values = group_key(candidate, fields)
            group_id = (spec_name, values)
            group = groups.get(group_id)
            if group is None:
                group = {
                    "rows": 0,
                    "role_counts": Counter(),
                    "rank_counts": Counter(),
                    "geometry_counts": Counter(),
                    "coverage_counts": Counter(),
                    "subject_counts": Counter(),
                    "object_counts": Counter(),
                    "samples": defaultdict(list),
                }
                groups[group_id] = group
            update_group(group, candidate)
            if spec_name == SELECTED_SPEC and role in {ROLE_POSITIVE, ROLE_NEGATIVE}:
                selected_groups[values][role].append(candidate)

    finalized_groups = [
        finalize_group(spec_name, dict(GROUP_SPECS)[spec_name], values, group)
        for (spec_name, values), group in groups.items()
    ]
    return {
        "raw_join": raw_join,
        "primary_rows": primary_rows,
        "diagnostic_rows": diagnostic_rows,
        "counts": counts,
        "distinct": {key: len(value) for key, value in distinct.items()},
        "groups": finalized_groups,
        "selected_groups": selected_groups,
    }


def summarize_specs(groups: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in groups:
        by_spec[row["spec_name"]].append(row)

    summary_rows: list[dict[str, Any]] = []
    mixed_rows: list[dict[str, Any]] = []
    for spec_name, rows in by_spec.items():
        mixed = [row for row in rows if row["is_positive_negative_mixed"]]
        summary_rows.append(
            {
                "spec_name": spec_name,
                "fields": rows[0]["fields"] if rows else "",
                "groups": len(rows),
                "rows": sum(int(row["rows"]) for row in rows),
                "mixed_groups": len(mixed),
                "mixed_rows": sum(int(row["rows"]) for row in mixed),
                "balanced_pair_capacity": sum(int(row["balanced_pair_capacity"]) for row in mixed),
                "balanced_proxy_row_capacity": sum(int(row["balanced_proxy_row_capacity"]) for row in mixed),
                "max_group_positive_proxy_rows": max([int(row["positive_anchor_proxy_rows"]) for row in rows] or [0]),
                "max_group_hard_negative_rows": max([int(row["hard_negative_proxy_rows"]) for row in rows] or [0]),
            }
        )
        for row in mixed:
            out = {key: value for key, value in row.items() if key != "samples"}
            out["sample_count"] = sum(len(value) for value in row.get("samples", {}).values())
            mixed_rows.append(out)
    summary_rows.sort(key=lambda row: (row["spec_name"]))
    mixed_rows.sort(key=lambda row: (-int(row["balanced_proxy_row_capacity"]), row["spec_name"], row["group_value"]))
    return summary_rows, mixed_rows


def counter_rows(counter: Counter[str], key_name: str, limit: int | None = None) -> list[dict[str, Any]]:
    items = counter.most_common(limit)
    return [{key_name: key, "count": value} for key, value in items]


def evaluate_capacity(
    validation_errors: list[dict[str, Any]],
    gates: dict[str, Any],
    spec_rows: list[dict[str, Any]],
    counts: dict[str, Counter[str]],
    preview_summary: dict[str, Any],
) -> dict[str, Any]:
    specs = {row["spec_name"]: row for row in spec_rows}
    selected = specs.get(SELECTED_SPEC, {})
    strict = specs.get(STRICT_GEOMETRY_SPEC, {})
    positive_rows = int(counts["v23_proxy_role"].get(ROLE_POSITIVE, 0))
    checks = {
        "validation_errors_zero": len(validation_errors) == 0,
        "positive_anchor_proxy_rows_min_300": positive_rows >= int(gates["positive_anchor_candidate_rows_min"]),
        "selected_spec_mixed_groups_min_30": int(selected.get("mixed_groups", 0)) >= int(gates["matched_positive_negative_cells_min"]),
        "selected_spec_balanced_proxy_rows_min_160": int(selected.get("balanced_proxy_row_capacity", 0)) >= int(gates["balanced_proxy_capacity_min"]),
        "preview_rows_min_160_after_caps": int(preview_summary.get("selected_rows", 0)) >= int(gates["balanced_proxy_capacity_min"]),
        "preview_positive_negative_each_min_60": (
            int(preview_summary.get("selected_by_role", {}).get(ROLE_POSITIVE, 0)) >= 60
            and int(preview_summary.get("selected_by_role", {}).get(ROLE_NEGATIVE, 0)) >= 60
        ),
        "rank_band_coverage_min_2": int(preview_summary.get("rank_band_coverage", 0)) >= int(gates["min_rank_band_coverage"]),
        "geometry_bucket_coverage_min_2": int(preview_summary.get("geometry_bucket_coverage", 0)) >= int(gates["min_geometry_bucket_coverage"]),
        "predicate_fixed_to_hanging_on": True,
    }
    passed = all(checks.values())
    return {
        "capacity_pass": passed,
        "selected_capacity_route": SELECTED_SPEC if passed else "blocked_no_positive_anchor_contrast_route",
        "selected_spec": selected,
        "strict_geometry_spec": strict,
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
        "next_todo": NEXT_TODO_READY if passed else NEXT_TODO_BLOCKED,
    }


def build_report(summary: dict[str, Any]) -> str:
    decision = summary["decision"]
    counts = summary["counts"]
    selected_spec = decision.get("selected_spec", {})
    strict_spec = decision.get("strict_geometry_spec", {})
    preview = summary["selection_preview_summary"]
    lines = [
        "# V78 Hanging-On Positive-Anchor Capacity Scan",
        "",
        "## Purpose",
        "",
        "Scan the full train-side Open3DSG relation pool for the v23 `hanging on` positive-anchor route.",
        "This is a capacity scan only: no new labels, no posterior smoke, no validation/test use.",
        "",
        "## Decision",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"capacity_pass = {decision['capacity_pass']}",
        f"failed_checks = {', '.join(decision['failed_checks']) if decision['failed_checks'] else 'none'}",
        "```",
        "",
        "## Capacity Counts",
        "",
        "```text",
        f"primary_predicate = {PRIMARY_PREDICATE}",
        f"primary_rows = {summary['primary_rows']}",
        f"diagnostic_rows = {summary['diagnostic_rows']}",
        f"positive_anchor_cell_rows = {counts['positive_anchor_cell'].get('True', 0)}",
        f"positive_anchor_proxy_rows = {counts['v23_proxy_role'].get(ROLE_POSITIVE, 0)}",
        f"hard_negative_proxy_rows = {counts['v23_proxy_role'].get(ROLE_NEGATIVE, 0)}",
        f"selected_spec_mixed_groups = {selected_spec.get('mixed_groups', 0)}",
        f"selected_spec_balanced_proxy_row_capacity = {selected_spec.get('balanced_proxy_row_capacity', 0)}",
        f"strict_geometry_mixed_groups = {strict_spec.get('mixed_groups', 0)}",
        f"strict_geometry_balanced_proxy_row_capacity = {strict_spec.get('balanced_proxy_row_capacity', 0)}",
        f"preview_selected_rows_after_caps = {preview.get('selected_rows', 0)}",
        "```",
        "",
        "## Interpretation",
        "",
    ]
    if decision["capacity_pass"]:
        lines.extend(
            [
                "The route has enough train-side proxy capacity to proceed to candidate mining.",
                "`same_affordance_rank_coverage` is selected because it keeps predicate fixed to `hanging on`,",
                "matches the subject/anchor affordance families, rank band, and coverage tier, and treats geometry as a balanced/capped axis.",
                "The strict geometry-exact route is reported as a diagnostic because exact geometry matching is expected to be too restrictive for this positive-anchor repair route.",
            ]
        )
    else:
        lines.extend(
            [
                "The route does not have enough controlled positive-anchor proxy capacity yet.",
                "Candidate mining, packet materialization, label fill, target-independence audit, posterior smoke, and multi-view-as-input remain blocked.",
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only H002 hypothesis artifact.",
            "- No validation/test rows were used.",
            "- No H001 artifact was modified.",
            "- No human label was created or changed.",
            "- Existing GT match status is reported only as audit metadata, not as model input.",
            "- Multi-view and mesh remain audit/confirmation evidence only.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    plan_dir = as_abs(args.plan_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(plan_dir / "summary.json")
    repair_plan = read_json(plan_dir / "repair_plan.json")
    contract = read_json(plan_dir / "capacity_scan_contract.json")
    gates = contract["pre_label_gates"]
    validation_errors = validate_plan(plan_summary, contract)

    scan = scan_full_train(as_abs(args.match_rows))
    spec_rows, mixed_rows = summarize_specs(scan["groups"])
    selection_preview, preview_summary = build_selection_preview(scan["selected_groups"], gates)
    decision = evaluate_capacity(validation_errors, gates, spec_rows, scan["counts"], preview_summary)

    status = STATUS_ERROR if validation_errors else STATUS_READY if decision["capacity_pass"] else STATUS_BLOCKED
    next_todo = NEXT_TODO_READY if decision["capacity_pass"] else NEXT_TODO_BLOCKED
    if validation_errors:
        next_todo = EXPECTED_PLAN_NEXT

    summary = {
        "schema_version": "h002_reliability_target_v23_hanging_on_positive_anchor_capacity_scan_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "split": "train_only",
        "primary_predicate": PRIMARY_PREDICATE,
        "diagnostic_predicates": sorted(DIAGNOSTIC_PREDICATES),
        "primary_rows": scan["primary_rows"],
        "diagnostic_rows": scan["diagnostic_rows"],
        "raw_join_summary": scan["raw_join"],
        "distinct": scan["distinct"],
        "counts": {key: dict(value) for key, value in scan["counts"].items()},
        "decision": decision,
        "selection_preview_summary": preview_summary,
        "boundary": {
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "fills_new_labels": False,
            "existing_gt_match_axis_as_model_input": False,
            "hidden_fields_as_model_input": False,
        },
        "inputs": {
            "plan_summary": rel_path(plan_dir / "summary.json"),
            "repair_plan": rel_path(plan_dir / "repair_plan.json"),
            "capacity_scan_contract": rel_path(plan_dir / "capacity_scan_contract.json"),
            "match_rows": rel_path(as_abs(args.match_rows)),
        },
        "outputs": {
            "summary": rel_path(output_dir / "summary.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
            "capacity_by_spec": rel_path(output_dir / "capacity_by_spec.csv"),
            "mixed_capacity_top": rel_path(output_dir / "mixed_capacity_top.csv"),
            "selection_preview_internal": rel_path(output_dir / "selection_preview_internal.jsonl"),
            "positive_anchor_cell_counts": rel_path(output_dir / "positive_anchor_cell_counts.csv"),
            "report": rel_path(output_dir / "report.md"),
        },
        "repair_plan_snapshot": {
            "selected_route": repair_plan.get("selected_route"),
            "repair_principle": repair_plan.get("repair_principle"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(output_dir / "capacity_by_spec.csv", spec_rows)
    write_csv(output_dir / "mixed_capacity_top.csv", mixed_rows[:500])
    write_jsonl(output_dir / "selection_preview_internal.jsonl", selection_preview)
    write_csv(output_dir / "positive_anchor_cell_counts.csv", counter_rows(scan["counts"]["positive_anchor_cell_subject_label"], "subject_label"))
    write_csv(output_dir / "positive_anchor_cell_object_counts.csv", counter_rows(scan["counts"]["positive_anchor_cell_object_label"], "object_label"))
    write_csv(output_dir / "positive_anchor_cell_geometry_counts.csv", counter_rows(scan["counts"]["positive_anchor_cell_geometry_bucket"], "geometry_bucket"))
    write_csv(output_dir / "positive_anchor_cell_rank_counts.csv", counter_rows(scan["counts"]["positive_anchor_cell_rank_band"], "rank_band"))
    (output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(f"status={status}")
    print(f"next_todo={next_todo}")
    print(f"validation_errors={len(validation_errors)}")
    print(f"capacity_pass={decision['capacity_pass']}")
    print(f"positive_anchor_proxy_rows={scan['counts']['v23_proxy_role'].get(ROLE_POSITIVE, 0)}")
    print(f"hard_negative_proxy_rows={scan['counts']['v23_proxy_role'].get(ROLE_NEGATIVE, 0)}")
    print(f"selected_spec_mixed_groups={decision['selected_spec'].get('mixed_groups', 0)}")
    print(f"preview_selected_rows={preview_summary.get('selected_rows', 0)}")
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
