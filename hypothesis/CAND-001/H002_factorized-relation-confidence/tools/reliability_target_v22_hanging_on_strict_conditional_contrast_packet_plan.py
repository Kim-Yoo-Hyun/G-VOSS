#!/usr/bin/env python3
"""Plan a strict `hanging on` conditional-contrast packet for H002."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan as v21


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION_DIR = RGA_ROOT / "reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan"

EXPECTED_PATH_STATUS = (
    "h002_reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_"
    "select_v22_hanging_on_strict_packet_plan"
)
EXPECTED_PATH_NEXT = "reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan"

STATUS_READY = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan_ready_for_candidate_mining"
STATUS_BLOCKED = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan_blocked_capacity_or_caps"
STATUS_ERROR = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan_validation_errors"
NEXT_READY = "reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining"
NEXT_BLOCKED = "reliability_target_v22_hanging_on_strict_conditional_contrast_path_decision_after_packet_plan"

PREDICATE = "hanging on"
TARGET_PACKET_ROWS = 240
TARGET_PER_ROLE = TARGET_PACKET_ROWS // 2
STRICT_GROUP_ROLE_CAP = 6
STRICT_GROUP_TOTAL_CAP = STRICT_GROUP_ROLE_CAP * 2
MAX_SCAN_ROWS = math.floor(TARGET_PACKET_ROWS * 0.05)
MAX_VISIBLE_ENDPOINT_ROWS = math.floor(TARGET_PACKET_ROWS * 0.04)
MIN_STRICT_MIXED_GROUPS = 80
MIN_STRICT_BALANCED_CAPACITY = 1000
MIN_SELECTED_STRICT_GROUPS = 20

ROLE_ACCEPT = v21.ROLE_ACCEPT_PROXY
ROLE_REJECT = v21.ROLE_REJECT_PROXY
ROLE_UNCERTAIN = v21.ROLE_UNCERTAIN_PROXY


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
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


def validate_path_decision(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_status", "expected": EXPECTED_PATH_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_next", "expected": EXPECTED_PATH_NEXT, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "path_validation_errors_present", "actual": summary.get("validation_errors")})
    contract = summary.get("next_contract", {})
    if contract.get("selected_primary_relation_scope") != [PREDICATE]:
        errors.append(
            {
                "error_type": "unexpected_primary_scope",
                "expected": [PREDICATE],
                "actual": contract.get("selected_primary_relation_scope"),
            }
        )
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
        "multi_view_as_model_input",
        "mesh_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "path_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def strict_group_key(candidate: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(candidate["rank_band"]),
        str(candidate["geometry_bucket"]),
        str(candidate["object_family_pair"]),
    )


def strict_group_value(key: tuple[str, str, str]) -> str:
    return f"{PREDICATE} | {key[0]} | {key[1]} | {key[2]}"


def add_capped(rows: list[dict[str, Any]], candidate: dict[str, Any], cap: int = 100) -> None:
    rows.append(candidate)
    if len(rows) > cap * 2:
        rows.sort(key=lambda item: item["hash_key"])
        del rows[cap:]


def compact_preview_row(candidate: dict[str, Any], group_value: str, planned_role: str) -> dict[str, Any]:
    return {
        "blind_review_id": candidate["blind_review_id"],
        "prediction_id": candidate["prediction_id"],
        "scan_id": candidate["scan_id"],
        "subgraph_id": candidate["subgraph_id"],
        "directed_pair_id": candidate["directed_pair_id"],
        "subject_id": candidate["subject_id"],
        "object_id": candidate["object_id"],
        "subject_label": candidate["subject_label"],
        "predicate_label": candidate["predicate_label"],
        "object_label": candidate["object_label"],
        "visible_endpoint_pair": candidate["visible_endpoint_pair"],
        "object_family_pair": candidate["object_family_pair"],
        "rank_band": candidate["rank_band"],
        "geometry_bucket": candidate["geometry_bucket"],
        "coverage_proxy": candidate["coverage_proxy"],
        "uncertainty_bucket": candidate["uncertainty_bucket"],
        "gt_label_match_status": candidate["gt_label_match_status"],
        "planned_proxy_role": planned_role,
        "strict_group_value": group_value,
    }


def scan_hanging_on_strict_groups(match_rows: Path) -> dict[str, Any]:
    pair_geometry, raw_join = v21.v17.collect_pair_geometry(match_rows)
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    distinct: dict[str, set[str]] = defaultdict(set)
    total_rows = 0
    joined_rows = 0

    for _, row in v21.v17.iter_jsonl(match_rows):
        predicate_info = row.get("predicate", {})
        if predicate_info.get("predicate_family") != "attachment_deferred":
            continue
        predicate = v21.v17.norm(predicate_info.get("predicate_label"))
        if predicate != PREDICATE:
            continue
        total_rows += 1
        identity = row.get("identity", {})
        raw_entry = pair_geometry.get(identity.get("directed_pair_id"))
        if raw_entry is not None:
            joined_rows += 1
        witness = v21.v17.classify_attachment(row, raw_entry)
        candidate = v21.candidate_from_row(row, witness, raw_entry)
        role = candidate["reliability_proxy_role"]
        key = strict_group_key(candidate)
        group = groups.setdefault(
            key,
            {
                "key": key,
                "group_value": strict_group_value(key),
                "rows": 0,
                "role_counts": Counter(),
                "samples": {ROLE_ACCEPT: [], ROLE_REJECT: [], ROLE_UNCERTAIN: []},
                "rank_band": key[0],
                "geometry_bucket": key[1],
                "object_family_pair": key[2],
            },
        )
        group["rows"] += 1
        group["role_counts"][role] += 1
        if role in group["samples"]:
            add_capped(group["samples"][role], candidate, cap=100)

        counts["role"][role] += 1
        counts["rank_band"][str(candidate["rank_band"])] += 1
        counts["geometry_bucket"][str(candidate["geometry_bucket"])] += 1
        counts["object_family_pair"][str(candidate["object_family_pair"])] += 1
        counts["coverage_proxy"][str(candidate["coverage_proxy"])] += 1
        counts["uncertainty_bucket"][str(candidate["uncertainty_bucket"])] += 1
        distinct["scan_id"].add(str(candidate["scan_id"]))
        distinct["subgraph_id"].add(str(candidate["subgraph_id"]))
        distinct["directed_pair_id"].add(str(candidate["directed_pair_id"]))
        distinct["visible_endpoint_pair"].add(str(candidate["visible_endpoint_pair"]))

    for group in groups.values():
        for role_rows in group["samples"].values():
            role_rows.sort(key=lambda item: item["hash_key"])

    mixed_groups = [
        group
        for group in groups.values()
        if group["role_counts"][ROLE_ACCEPT] > 0 and group["role_counts"][ROLE_REJECT] > 0
    ]
    balanced_capacity = sum(min(group["role_counts"][ROLE_ACCEPT], group["role_counts"][ROLE_REJECT]) for group in mixed_groups)
    return {
        "raw_join": raw_join,
        "total_rows": total_rows,
        "joined_rows": joined_rows,
        "counts": {key: dict(value) for key, value in counts.items()},
        "distinct": {key: len(value) for key, value in distinct.items()},
        "groups": groups,
        "mixed_groups": mixed_groups,
        "mixed_group_count": len(mixed_groups),
        "balanced_capacity": balanced_capacity,
    }


def sort_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        groups,
        key=lambda group: (
            -min(group["role_counts"][ROLE_ACCEPT], group["role_counts"][ROLE_REJECT]),
            group["rank_band"],
            group["geometry_bucket"],
            group["object_family_pair"],
        ),
    )


def select_hidden_preview(groups: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    role_counts: Counter[str] = Counter()
    scan_counts: Counter[str] = Counter()
    visible_pair_counts: Counter[str] = Counter()
    group_counts: Counter[str] = Counter()
    group_role_counts: Counter[tuple[str, str]] = Counter()
    cursors: dict[tuple[str, str], int] = defaultdict(int)
    sorted_groups = sort_groups(
        [
            group
            for group in groups
            if len(group["samples"][ROLE_ACCEPT]) >= STRICT_GROUP_ROLE_CAP
            and len(group["samples"][ROLE_REJECT]) >= STRICT_GROUP_ROLE_CAP
        ]
    )

    def try_take(group: dict[str, Any], role: str) -> bool:
        group_value = group["group_value"]
        if role_counts[role] >= TARGET_PER_ROLE:
            return False
        if group_counts[group_value] >= STRICT_GROUP_TOTAL_CAP:
            return False
        if group_role_counts[(group_value, role)] >= STRICT_GROUP_ROLE_CAP:
            return False
        rows = group["samples"][role]
        cursor_key = (group_value, role)
        start = cursors[cursor_key]
        for idx in range(start, len(rows)):
            candidate = rows[idx]
            cursors[cursor_key] = idx + 1
            prediction_id = str(candidate["prediction_id"])
            scan_id = str(candidate["scan_id"])
            visible_pair = str(candidate["visible_endpoint_pair"])
            if prediction_id in selected_ids:
                continue
            if scan_counts[scan_id] >= MAX_SCAN_ROWS:
                continue
            if visible_pair_counts[visible_pair] >= MAX_VISIBLE_ENDPOINT_ROWS:
                continue
            selected_ids.add(prediction_id)
            scan_counts[scan_id] += 1
            visible_pair_counts[visible_pair] += 1
            group_counts[group_value] += 1
            group_role_counts[(group_value, role)] += 1
            role_counts[role] += 1
            selected.append(compact_preview_row(candidate, group_value, role))
            return True
        return False

    made_progress = True
    while made_progress and (role_counts[ROLE_ACCEPT] < TARGET_PER_ROLE or role_counts[ROLE_REJECT] < TARGET_PER_ROLE):
        made_progress = False
        for group in sorted_groups:
            for role in [ROLE_ACCEPT, ROLE_REJECT]:
                if try_take(group, role):
                    made_progress = True
                if role_counts[ROLE_ACCEPT] >= TARGET_PER_ROLE and role_counts[ROLE_REJECT] >= TARGET_PER_ROLE:
                    break
            if role_counts[ROLE_ACCEPT] >= TARGET_PER_ROLE and role_counts[ROLE_REJECT] >= TARGET_PER_ROLE:
                break

    quota_rows: list[dict[str, Any]] = []
    selected_group_values = set(group_counts)
    groups_by_value = {group["group_value"]: group for group in sorted_groups}
    for group_value in sorted(selected_group_values):
        group = groups_by_value[group_value]
        quota_rows.append(
            {
                "strict_group_value": group_value,
                "rank_band": group["rank_band"],
                "geometry_bucket": group["geometry_bucket"],
                "object_family_pair": group["object_family_pair"],
                "available_accept_proxy_rows": group["role_counts"][ROLE_ACCEPT],
                "available_reject_proxy_rows": group["role_counts"][ROLE_REJECT],
                "available_uncertain_proxy_rows": group["role_counts"][ROLE_UNCERTAIN],
                "planned_accept_proxy_rows": group_role_counts[(group_value, ROLE_ACCEPT)],
                "planned_reject_proxy_rows": group_role_counts[(group_value, ROLE_REJECT)],
                "planned_total_rows": group_counts[group_value],
            }
        )

    selection_summary = {
        "selected_rows": len(selected),
        "selected_role_counts": dict(role_counts),
        "selected_strict_groups": len(selected_group_values),
        "max_rows_per_strict_group": max(group_counts.values()) if group_counts else 0,
        "max_rows_per_scan": max(scan_counts.values()) if scan_counts else 0,
        "max_rows_per_visible_endpoint_pair": max(visible_pair_counts.values()) if visible_pair_counts else 0,
        "scan_count": len(scan_counts),
        "visible_endpoint_pair_count": len(visible_pair_counts),
        "strict_group_role_cap": STRICT_GROUP_ROLE_CAP,
        "strict_group_total_cap": STRICT_GROUP_TOTAL_CAP,
        "max_scan_rows": MAX_SCAN_ROWS,
        "max_visible_endpoint_rows": MAX_VISIBLE_ENDPOINT_ROWS,
        "unfilled_accept_proxy_rows": max(0, TARGET_PER_ROLE - role_counts[ROLE_ACCEPT]),
        "unfilled_reject_proxy_rows": max(0, TARGET_PER_ROLE - role_counts[ROLE_REJECT]),
    }
    return selected, quota_rows, selection_summary


def summarize_selected_preview(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for field in [
            "planned_proxy_role",
            "rank_band",
            "geometry_bucket",
            "object_family_pair",
            "coverage_proxy",
            "uncertainty_bucket",
            "gt_label_match_status",
            "strict_group_value",
            "scan_id",
            "visible_endpoint_pair",
        ]:
            counters[field][str(row.get(field))] += 1
    return {key: dict(value) for key, value in counters.items()}


def build_packet_plan(selection_summary: dict[str, Any], selected_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": EXPECTED_PATH_NEXT,
        "planned_primary_relation_scope": [PREDICATE],
        "diagnostic_relation_scope": ["attached to", "connected to"],
        "planned_rows": TARGET_PACKET_ROWS,
        "planned_role_balance": {
            ROLE_ACCEPT: TARGET_PER_ROLE,
            ROLE_REJECT: TARGET_PER_ROLE,
        },
        "strict_group_policy": {
            "spec": "same_predicate_rank_geometry_family",
            "fields": ["predicate_label", "rank_band", "geometry_bucket", "object_family_pair"],
            "predicate_fixed": PREDICATE,
            "role_cap_per_group": STRICT_GROUP_ROLE_CAP,
            "total_cap_per_group": STRICT_GROUP_TOTAL_CAP,
            "selected_groups": selection_summary["selected_strict_groups"],
        },
        "cap_policy": {
            "max_rows_per_scan": MAX_SCAN_ROWS,
            "max_rows_per_visible_endpoint_pair": MAX_VISIBLE_ENDPOINT_ROWS,
            "max_rows_per_strict_group": STRICT_GROUP_TOTAL_CAP,
        },
        "visible_surface_policy": {
            "allowed": [
                "blind_review_id",
                "subject_label",
                "predicate_label",
                "object_label",
                "neutral_packet_local_assets_after_materialization",
                "review_label_blank",
                "review_reason_blank",
            ],
            "forbidden": [
                "scan_id",
                "subgraph_id",
                "subject_id",
                "object_id",
                "prediction_id",
                "semantic_rank",
                "rank_band",
                "geometry_bucket",
                "object_family_pair",
                "coverage_proxy",
                "uncertainty_bucket",
                "gt_label_match_status",
                "planned_proxy_role",
                "strict_group_value",
                "p_geom_valid",
                "geometry_status",
            ],
        },
        "hidden_manifest_policy": {
            "preserve_for_post_label_audit": [
                "scan_id",
                "subgraph_id",
                "prediction_id",
                "rank_band",
                "geometry_bucket",
                "object_family_pair",
                "coverage_proxy",
                "uncertainty_bucket",
                "gt_label_match_status",
                "planned_proxy_role",
                "strict_group_value",
            ]
        },
        "blocked_until_candidate_mining": [
            "visible packet materialization",
            "label fill",
            "label ingestion",
            "target-independence audit",
            "posterior smoke",
            "multi-view as model input",
        ],
        "selected_distribution_preview": selected_summary,
    }


def decision_from_gates(validation_errors: list[dict[str, Any]], scan: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "validation_errors_zero": len(validation_errors) == 0,
        "strict_mixed_groups_min": scan["mixed_group_count"] >= MIN_STRICT_MIXED_GROUPS,
        "strict_balanced_capacity_min": scan["balanced_capacity"] >= MIN_STRICT_BALANCED_CAPACITY,
        "selected_rows_target": selection["selected_rows"] == TARGET_PACKET_ROWS,
        "selected_role_balance": selection["selected_role_counts"].get(ROLE_ACCEPT) == TARGET_PER_ROLE
        and selection["selected_role_counts"].get(ROLE_REJECT) == TARGET_PER_ROLE,
        "selected_strict_groups_min": selection["selected_strict_groups"] >= MIN_SELECTED_STRICT_GROUPS,
        "scan_cap_pass": selection["max_rows_per_scan"] <= MAX_SCAN_ROWS,
        "visible_endpoint_cap_pass": selection["max_rows_per_visible_endpoint_pair"] <= MAX_VISIBLE_ENDPOINT_ROWS,
        "strict_group_cap_pass": selection["max_rows_per_strict_group"] <= STRICT_GROUP_TOTAL_CAP,
    }
    failed = [key for key, value in checks.items() if not value]
    ready = not failed
    return {
        "packet_plan_pass": ready,
        "checks": checks,
        "failed_checks": failed,
        "selected_route": "candidate_mining" if ready else "path_decision_required",
        "next_todo": NEXT_READY if ready else NEXT_BLOCKED,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    decision = summary["packet_plan_decision"]
    lines = [
        "# H002 V22 Hanging-On Strict Packet Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"packet_plan_pass = {decision['packet_plan_pass']}",
        f"selected_route = {decision['selected_route']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Scope",
        "",
        "```text",
        "primary_relation_scope = hanging on",
        "diagnostic_relation_scope = attached to, connected to",
        "strict_spec = predicate_label + rank_band + geometry_bucket + object_family_pair",
        "planned_rows = 240",
        "planned_proxy_role_balance = 120 / 120",
        "```",
        "",
        "## Capacity And Dry-Run Selection",
        "",
        "```text",
        f"full_train_hanging_on_rows = {summary['scan_summary']['total_rows']}",
        f"strict_mixed_groups = {summary['scan_summary']['mixed_group_count']}",
        f"strict_balanced_capacity = {summary['scan_summary']['balanced_capacity']}",
        f"dry_run_selected_rows = {summary['selection_summary']['selected_rows']}",
        f"dry_run_selected_role_counts = {summary['selection_summary']['selected_role_counts']}",
        f"dry_run_selected_strict_groups = {summary['selection_summary']['selected_strict_groups']}",
        f"max_rows_per_scan = {summary['selection_summary']['max_rows_per_scan']}",
        f"max_rows_per_visible_endpoint_pair = {summary['selection_summary']['max_rows_per_visible_endpoint_pair']}",
        f"max_rows_per_strict_group = {summary['selection_summary']['max_rows_per_strict_group']}",
        "```",
        "",
        "## Interpretation",
        "",
        "v22는 label sheet를 만든 단계가 아니다. Full-train `hanging on` strict strata에서 "
        "240-row hidden-only dry-run preview를 만들 수 있는지 확인하고, 다음 candidate mining에서 "
        "사용할 quota와 visible/hidden field policy를 고정한 단계다.",
        "",
        "이 plan이 통과하면 다음 단계는 candidate mining이다. 그때도 reviewer-visible sheet에는 "
        "rank, geometry bucket, object-family, GT match, planned proxy role 같은 construction field를 "
        "노출하지 않는다.",
        "",
        "## Boundary",
        "",
        "- Train-only rows only.",
        "- No validation/test rows used.",
        "- No label fill or ingestion.",
        "- No posterior trained or evaluated.",
        "- Multi-view and mesh remain audit/confirmation evidence only.",
        "- H001 and paper artifacts were not modified.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_dir = as_abs(args.path_decision_dir)
    match_rows = as_abs(args.match_rows)
    output_dir = as_abs(args.output_dir)
    path_decision = read_json(path_dir / "summary.json")
    validation_errors = validate_path_decision(path_decision)
    scan = scan_hanging_on_strict_groups(match_rows)
    selected_rows, quota_rows, selection_summary = select_hidden_preview(scan["mixed_groups"])
    selected_summary = summarize_selected_preview(selected_rows)
    packet_plan = build_packet_plan(selection_summary, selected_summary)
    decision = decision_from_gates(validation_errors, scan, selection_summary)

    output_paths = {
        "summary": output_dir / "summary.json",
        "packet_plan": output_dir / "packet_plan.json",
        "strict_group_quota": output_dir / "strict_group_quota.csv",
        "hidden_selection_preview": output_dir / "hidden_selection_preview.jsonl",
        "report": output_dir / "report.md",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    status = STATUS_ERROR if validation_errors else (STATUS_READY if decision["packet_plan_pass"] else STATUS_BLOCKED)
    summary = {
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "next_todo": decision["next_todo"],
        "input_artifacts": {
            "path_decision_summary": rel_path(path_dir / "summary.json"),
            "match_rows": rel_path(match_rows),
        },
        "output_artifacts": {key: rel_path(path) for key, path in output_paths.items()},
        "scan_summary": {
            "predicate": PREDICATE,
            "total_rows": scan["total_rows"],
            "joined_rows": scan["joined_rows"],
            "raw_join": scan["raw_join"],
            "counts": scan["counts"],
            "distinct": scan["distinct"],
            "strict_groups": len(scan["groups"]),
            "mixed_group_count": scan["mixed_group_count"],
            "balanced_capacity": scan["balanced_capacity"],
        },
        "selection_summary": selection_summary,
        "selected_distribution_preview": selected_summary,
        "packet_plan_decision": decision,
        "packet_plan": packet_plan,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "creates_visible_label_sheet": False,
            "materializes_packet_assets": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "hidden_selection_preview_only": True,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["packet_plan"], packet_plan)
    write_csv(output_paths["strict_group_quota"], quota_rows)
    write_jsonl(output_paths["hidden_selection_preview"], selected_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"strict_mixed_groups={summary['scan_summary']['mixed_group_count']}")
    print(f"strict_balanced_capacity={summary['scan_summary']['balanced_capacity']}")
    print(f"selected_rows={summary['selection_summary']['selected_rows']}")
    print(f"selected_role_counts={summary['selection_summary']['selected_role_counts']}")
    print(f"selected_strict_groups={summary['selection_summary']['selected_strict_groups']}")
    print(f"packet_plan_pass={summary['packet_plan_decision']['packet_plan_pass']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
