#!/usr/bin/env python3
"""Scan full-train conditional contrast capacity for H002 attachment reliability."""

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


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION_DIR = RGA_ROOT / (
    "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_"
    "audit_packet_path_decision_after_audit"
)
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan"

EXPECTED_PATH_STATUS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_"
    "audit_packet_path_decision_select_v21_conditional_contrast_capacity_scan"
)
EXPECTED_PATH_NEXT = "reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan"

STATUS_READY = "h002_reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan_ready_for_packet_plan"
STATUS_BLOCKED = "h002_reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan_blocked_predicate_imbalanced_strict_capacity"
STATUS_ERROR = "h002_reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan_validation_errors"
NEXT_TODO_READY = "reliability_target_v21_attachment_deferred_conditional_contrast_packet_plan"
NEXT_TODO_BLOCKED = "reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan"

PRIMARY_PREDICATES = {"attached to", "hanging on"}
DIAGNOSTIC_PREDICATES = {"connected to"}

ROLE_ACCEPT_PROXY = "accept_proxy_supported_candidate"
ROLE_REJECT_PROXY = "reject_proxy_contradicted_candidate"
ROLE_UNCERTAIN_PROXY = "uncertain_proxy"

GROUP_SPECS: list[tuple[str, list[str]]] = [
    ("same_predicate", ["predicate_label"]),
    ("same_predicate_rank", ["predicate_label", "rank_band"]),
    ("same_predicate_geometry", ["predicate_label", "geometry_bucket"]),
    ("same_predicate_geometry_rank", ["predicate_label", "geometry_bucket", "rank_band"]),
    ("same_predicate_geometry_family", ["predicate_label", "geometry_bucket", "object_family_pair"]),
    ("same_predicate_rank_family", ["predicate_label", "rank_band", "object_family_pair"]),
    ("same_predicate_rank_anchor", ["predicate_label", "rank_band", "anchor_bucket"]),
    ("same_predicate_rank_coverage", ["predicate_label", "rank_band", "coverage_proxy"]),
    ("same_predicate_rank_uncertainty", ["predicate_label", "rank_band", "uncertainty_bucket"]),
    ("same_predicate_rank_geometry_family", ["predicate_label", "rank_band", "geometry_bucket", "object_family_pair"]),
    ("same_predicate_visible_pair", ["predicate_label", "visible_endpoint_pair"]),
    ("same_predicate_rank_visible_pair", ["predicate_label", "rank_band", "visible_endpoint_pair"]),
    ("same_predicate_scan_rank", ["predicate_label", "scan_id", "rank_band"]),
    ("same_predicate_gt_status_rank", ["predicate_label", "gt_label_match_status", "rank_band"]),
    ("same_predicate_evidence_tier_coverage", ["predicate_label", "capacity_evidence_tier", "coverage_proxy"]),
]

STRICT_SPEC = "same_predicate_rank_geometry_family"
DIAGNOSTIC_SPEC = "same_predicate_rank_family"


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
    boundary = summary.get("boundary", {})
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
            errors.append({"error_type": "path_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def reliability_proxy_role(witness: dict[str, Any]) -> str:
    status = witness["provisional_status"]
    if status == "supported_candidate":
        return ROLE_ACCEPT_PROXY
    if status == "contradicted_candidate":
        return ROLE_REJECT_PROXY
    return ROLE_UNCERTAIN_PROXY


def geometry_bucket(witness: dict[str, Any]) -> str:
    if witness["raw_feature_join_state"] != "joined":
        return "geometry_missing"
    if witness["near_contact"] and witness["projected_overlap_support"]:
        return "near_overlap"
    if witness["near_contact"]:
        return "near_no_overlap"
    if witness["loose_near_contact"] and witness["projected_overlap_support"]:
        return "loose_near_overlap"
    if witness["loose_near_contact"]:
        return "loose_near_no_overlap"
    if witness["far_separated"]:
        return "far_separated"
    return "mid_or_ambiguous"


def uncertainty_bucket(flags: list[str]) -> str:
    if not flags:
        return "none"
    flag_set = set(flags)
    if "functional_connection_ambiguous_without_visual_or_mesh" in flag_set:
        return "functional_connection_ambiguous"
    if "floor_support_confound" in flag_set or "hard_surface_pair" in flag_set:
        return "geometry_confound"
    if "thin_structure_or_boundary_missing" in flag_set or "large_obb_overlap_confound" in flag_set:
        return "visual_or_mesh_needed"
    if "typed_witness_ambiguous" in flag_set:
        return "typed_witness_ambiguous"
    return "other_uncertainty"


def coverage_proxy(witness: dict[str, Any]) -> str:
    if witness["raw_feature_join_state"] != "joined":
        return "missing_raw_geometry"
    if witness["uncertainty_flags"]:
        return "joined_with_uncertainty_flags"
    return "joined_no_uncertainty_flags"


def serialize_group_values(values: tuple[str, ...]) -> str:
    return " | ".join(values)


def candidate_from_row(row: dict[str, Any], witness: dict[str, Any], raw_entry: dict[str, Any] | None) -> dict[str, Any]:
    compact = v20.compact_candidate(row, witness, raw_entry)
    label = row.get("label", {})
    compact["gt_label_match_status"] = str(label.get("label_match_status"))
    compact["geometry_bucket"] = geometry_bucket(witness)
    compact["coverage_proxy"] = coverage_proxy(witness)
    compact["uncertainty_bucket"] = uncertainty_bucket(witness["uncertainty_flags"])
    compact["rank_band"] = str(compact.get("rank_band_hidden"))
    compact["reliability_proxy_role"] = reliability_proxy_role(witness)
    compact["semantic_rank"] = compact.get("semantic_rank_hidden")
    return compact


def add_sample(group: dict[str, Any], role: str, candidate: dict[str, Any]) -> None:
    samples = group["samples"][role]
    if len(samples) >= 3:
        return
    samples.append(
        {
            "prediction_id": candidate["prediction_id"],
            "scan_id": candidate["scan_id"],
            "subgraph_id": candidate["subgraph_id"],
            "predicate_label": candidate["predicate_label"],
            "subject_label": candidate["subject_label"],
            "object_label": candidate["object_label"],
            "rank_band": candidate["rank_band"],
            "geometry_bucket": candidate["geometry_bucket"],
            "object_family_pair": candidate["object_family_pair"],
            "anchor_bucket": candidate["anchor_bucket_hidden"],
            "coverage_proxy": candidate["coverage_proxy"],
            "uncertainty_bucket": candidate["uncertainty_bucket"],
            "gt_label_match_status": candidate["gt_label_match_status"],
        }
    )


def make_empty_group(spec_name: str, fields: list[str], values: tuple[str, ...]) -> dict[str, Any]:
    return {
        "spec_name": spec_name,
        "fields": fields,
        "values": values,
        "rows": 0,
        "role_counts": Counter(),
        "predicate_counts": Counter(),
        "rank_counts": Counter(),
        "geometry_counts": Counter(),
        "samples": defaultdict(list),
    }


def update_group(group: dict[str, Any], candidate: dict[str, Any]) -> None:
    role = candidate["reliability_proxy_role"]
    group["rows"] += 1
    group["role_counts"][role] += 1
    group["predicate_counts"][candidate["predicate_label"]] += 1
    group["rank_counts"][candidate["rank_band"]] += 1
    group["geometry_counts"][candidate["geometry_bucket"]] += 1
    add_sample(group, role, candidate)


def finalize_group(group: dict[str, Any]) -> dict[str, Any]:
    role_counts = dict(group["role_counts"])
    accept = int(role_counts.get(ROLE_ACCEPT_PROXY, 0))
    reject = int(role_counts.get(ROLE_REJECT_PROXY, 0))
    uncertain = int(role_counts.get(ROLE_UNCERTAIN_PROXY, 0))
    balanced = min(accept, reject)
    return {
        "spec_name": group["spec_name"],
        "fields": group["fields"],
        "group_value": serialize_group_values(group["values"]),
        "rows": group["rows"],
        "accept_proxy_rows": accept,
        "reject_proxy_rows": reject,
        "uncertain_proxy_rows": uncertain,
        "balanced_pair_capacity": balanced,
        "is_accept_reject_mixed": balanced > 0,
        "has_uncertain": uncertain > 0,
        "predicate_counts": dict(group["predicate_counts"]),
        "rank_counts": dict(group["rank_counts"]),
        "geometry_counts": dict(group["geometry_counts"]),
        "samples": {key: value for key, value in group["samples"].items()},
    }


def scan_full_train(match_rows: Path) -> dict[str, Any]:
    pair_geometry, raw_join = v17.collect_pair_geometry(match_rows)
    groups: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    distinct: dict[str, set[str]] = defaultdict(set)
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
        identity = row.get("identity", {})
        pair_id = identity.get("directed_pair_id")
        raw_entry = pair_geometry.get(pair_id)
        witness = v17.classify_attachment(row, raw_entry)
        if raw_entry is not None:
            joined_rows += 1

        if predicate in DIAGNOSTIC_PREDICATES:
            diagnostic_rows += 1
            counts["diagnostic_predicate"][predicate] += 1
            counts["diagnostic_cell"][witness["cell_id"]] += 1
            continue

        primary_rows += 1
        candidate = candidate_from_row(row, witness, raw_entry)
        role = candidate["reliability_proxy_role"]
        counts["predicate"][predicate] += 1
        counts["role"][role] += 1
        counts["predicate_role"][f"{predicate}|{role}"] += 1
        counts["rank_band"][candidate["rank_band"]] += 1
        counts["geometry_bucket"][candidate["geometry_bucket"]] += 1
        counts["anchor_bucket"][candidate["anchor_bucket_hidden"]] += 1
        counts["coverage_proxy"][candidate["coverage_proxy"]] += 1
        counts["uncertainty_bucket"][candidate["uncertainty_bucket"]] += 1
        counts["gt_label_match_status"][candidate["gt_label_match_status"]] += 1
        counts["object_family_pair"][candidate["object_family_pair"]] += 1
        counts["visible_endpoint_pair"][candidate["visible_endpoint_pair"]] += 1
        distinct["scan_id"].add(str(candidate["scan_id"]))
        distinct["subgraph_id"].add(str(candidate["subgraph_id"]))
        distinct["directed_pair_id"].add(str(candidate["directed_pair_id"]))
        distinct["visible_endpoint_pair"].add(candidate["visible_endpoint_pair"])

        for spec_name, fields in GROUP_SPECS:
            values = tuple(str(candidate.get(field)) for field in fields)
            key = (spec_name, values)
            group = groups.get(key)
            if group is None:
                group = make_empty_group(spec_name, fields, values)
                groups[key] = group
            update_group(group, candidate)

    finalized = [finalize_group(group) for group in groups.values()]
    return {
        "raw_join": raw_join,
        "counts": counts,
        "distinct": {key: len(value) for key, value in distinct.items()},
        "primary_rows": primary_rows,
        "diagnostic_rows": diagnostic_rows,
        "joined_rows": joined_rows,
        "groups": finalized,
    }


def summarize_specs(groups: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in groups:
        by_spec[group["spec_name"]].append(group)

    summaries: list[dict[str, Any]] = []
    top_rows: list[dict[str, Any]] = []
    for spec_name, rows in by_spec.items():
        mixed = [row for row in rows if row["is_accept_reject_mixed"]]
        by_predicate: dict[str, Counter[str]] = defaultdict(Counter)
        balanced_capacity = 0
        mixed_with_uncertain = 0
        for row in mixed:
            balanced_capacity += int(row["balanced_pair_capacity"])
            if row["has_uncertain"]:
                mixed_with_uncertain += 1
            for predicate, value in row["predicate_counts"].items():
                by_predicate[predicate]["mixed_groups"] += 1
                by_predicate[predicate]["balanced_pair_capacity"] += int(row["balanced_pair_capacity"])
                by_predicate[predicate]["rows"] += int(row["rows"])
        summaries.append(
            {
                "spec_name": spec_name,
                "fields": rows[0]["fields"] if rows else [],
                "groups": len(rows),
                "rows": sum(int(row["rows"]) for row in rows),
                "mixed_accept_reject_groups": len(mixed),
                "mixed_with_uncertain_groups": mixed_with_uncertain,
                "balanced_pair_capacity": balanced_capacity,
                "groups_with_uncertain": sum(1 for row in rows if row["has_uncertain"]),
                "by_predicate": {key: dict(value) for key, value in by_predicate.items()},
            }
        )
        top_rows.extend(sorted(mixed, key=lambda row: (-row["balanced_pair_capacity"], -row["rows"], row["group_value"]))[:30])

    summaries.sort(key=lambda row: (-row["balanced_pair_capacity"], row["spec_name"]))
    top_rows.sort(key=lambda row: (-row["balanced_pair_capacity"], -row["rows"], row["spec_name"], row["group_value"]))
    return summaries, top_rows[:240]


def counter_rows(counter: Counter[str], key_name: str, limit: int = 100) -> list[dict[str, Any]]:
    return [{key_name: key, "rows": value} for key, value in counter.most_common(limit)]


def relation_scope_status() -> dict[str, Any]:
    return {
        "close by": {
            "full_train_checked": True,
            "status": "diagnostic_generality_evidence",
            "evidence": "v10-v13 proximity branch",
            "key_counts": {"total_rows": 185346, "RGA_HL": 0, "RGA_LH": 171324},
            "reason_not_active_primary": "current RGA queue is LH-only, not bidirectional HL/LH.",
        },
        "standing on": {
            "full_train_checked": True,
            "status": "diagnostic_support_contact_branch",
            "evidence": "v14-v16 support_contact branch",
            "reason_not_active_primary": "eligible HL rows collapse under hard room-surface filters; later branch had side/geometry shortcut.",
        },
        "lying on": {
            "full_train_checked": True,
            "status": "diagnostic_support_contact_branch",
            "evidence": "v14-v16 support_contact branch",
            "reason_not_active_primary": "row mass is sufficient, but HL/LH aligns too strongly with geometry_status.",
        },
        "supported by": {
            "full_train_checked": True,
            "status": "excluded_from_current_primary",
            "evidence": "v14 physical relation-family feasibility and sampling plan",
            "reason_not_active_primary": "LH-only/outside narrow current core for the controlled support/contact target.",
        },
        "higher than": {
            "full_train_checked": True,
            "status": "relative_vertical_control_examined",
            "evidence": "v14 physical relation-family branch",
            "reason_not_active_primary": "HL capacity was too small for the intended controlled target.",
        },
        "lower than": {
            "full_train_checked": True,
            "status": "relative_vertical_control_used",
            "evidence": "v14-v16 control branch",
            "reason_not_active_primary": "geometry-easy control family, not the current novelty-primary target.",
        },
        "attached to": {
            "full_train_checked": True,
            "status": "active_v21_primary",
            "evidence": "v17-v21 attachment_deferred branch",
            "reason_active": "v20 packet may have been sampling-biased; full-train conditional contrast capacity is being scanned.",
        },
        "hanging on": {
            "full_train_checked": True,
            "status": "active_v21_primary",
            "evidence": "v17-v21 attachment_deferred branch",
            "reason_active": "v20 packet may have been sampling-biased; full-train conditional contrast capacity is being scanned.",
        },
        "connected to": {
            "full_train_checked": True,
            "status": "diagnostic_only",
            "evidence": "v17-v21 attachment_deferred branch",
            "reason_not_active_primary": "functional connection is ambiguous without stronger visual/mesh criterion.",
        },
    }


def capacity_decision(
    validation_errors: list[dict[str, Any]],
    scan: dict[str, Any],
    spec_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    specs = {row["spec_name"]: row for row in spec_summaries}
    strict = specs.get(STRICT_SPEC, {})
    diagnostic = specs.get(DIAGNOSTIC_SPEC, {})

    def pred_mixed(spec: dict[str, Any], predicate: str) -> int:
        return int(spec.get("by_predicate", {}).get(predicate, {}).get("mixed_groups", 0))

    checks = {
        "validation_errors_zero": len(validation_errors) == 0,
        "primary_rows_min_1000": int(scan["primary_rows"]) >= 1000,
        "joined_coverage_full": int(scan["joined_rows"]) >= int(scan["primary_rows"]) + int(scan["diagnostic_rows"]),
        "strict_spec_mixed_groups_min_40": int(strict.get("mixed_accept_reject_groups", 0)) >= 40,
        "strict_spec_balanced_capacity_min_1000": int(strict.get("balanced_pair_capacity", 0)) >= 1000,
        "strict_spec_each_primary_predicate_mixed_min_10": all(
            pred_mixed(strict, predicate) >= 10 for predicate in ["attached to", "hanging on"]
        ),
        "diagnostic_spec_mixed_groups_min_80": int(diagnostic.get("mixed_accept_reject_groups", 0)) >= 80,
        "uncertain_groups_exist": any(int(row.get("groups_with_uncertain", 0)) >= 40 for row in spec_summaries),
        "connected_to_remains_diagnostic": True,
    }
    ready = (
        checks["validation_errors_zero"]
        and checks["primary_rows_min_1000"]
        and checks["joined_coverage_full"]
        and checks["strict_spec_mixed_groups_min_40"]
        and checks["strict_spec_balanced_capacity_min_1000"]
        and checks["strict_spec_each_primary_predicate_mixed_min_10"]
    )
    return {
        "capacity_pass": ready,
        "decision": "ready_for_packet_plan" if ready else "blocked_or_needs_path_decision",
        "selected_route": STRICT_SPEC if ready else "path_decision_required",
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
        "next_todo": NEXT_TODO_READY if ready else NEXT_TODO_BLOCKED,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    decision = summary["capacity_decision"]
    strict = summary["spec_summary_by_name"].get(STRICT_SPEC, {})
    diagnostic = summary["spec_summary_by_name"].get(DIAGNOSTIC_SPEC, {})
    lines = [
        "# H002 V21 Attachment Conditional Contrast Capacity Scan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"capacity_pass = {decision['capacity_pass']}",
        f"selected_route = {decision['selected_route']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "posterior_smoke_allowed = false",
        "```",
        "",
        "## Full-Train Attachment Scope",
        "",
        "```text",
        f"primary_rows = {summary['counts']['primary_rows']}",
        f"diagnostic_connected_rows = {summary['counts']['diagnostic_rows']}",
        f"joined_rows = {summary['counts']['joined_rows']}",
        f"unique_scans = {summary['counts']['distinct']['scan_id']}",
        f"unique_subgraphs = {summary['counts']['distinct']['subgraph_id']}",
        f"unique_visible_pairs = {summary['counts']['distinct']['visible_endpoint_pair']}",
        "```",
        "",
        "Primary proxy role counts:",
        "",
        "```text",
    ]
    for key, value in summary["counts"]["role_counts"].items():
        lines.append(f"{key} = {value}")
    lines.extend(
        [
            "```",
            "",
            "## Conditional Capacity",
            "",
            "Strict selected spec:",
            "",
            "```text",
            f"spec = {STRICT_SPEC}",
            f"mixed_groups = {strict.get('mixed_accept_reject_groups')}",
            f"balanced_pair_capacity = {strict.get('balanced_pair_capacity')}",
            f"by_predicate = {strict.get('by_predicate')}",
            "```",
            "",
            "Diagnostic comparison spec:",
            "",
            "```text",
            f"spec = {DIAGNOSTIC_SPEC}",
            f"mixed_groups = {diagnostic.get('mixed_accept_reject_groups')}",
            f"balanced_pair_capacity = {diagnostic.get('balanced_pair_capacity')}",
            f"by_predicate = {diagnostic.get('by_predicate')}",
            "```",
            "",
            "## Interpretation",
            "",
            "이 scan은 human accept/reject label을 새로 만든 것이 아니다. Full-train attachment pool에서 "
            "same/similar predicate, rank, geometry bucket, object-family 조건 안에 supported/contradicted "
            "proxy가 충분히 함께 존재하는지 확인한 capacity scan이다.",
            "",
        ]
    )
    if decision["capacity_pass"]:
        lines.append(
            "결과적으로 v20 320-row packet이 reject-heavy였다는 사실만으로 attachment route나 H002 "
            "factorization을 기각하면 안 된다. Full train에는 조건부 contrast 후보가 충분히 존재하므로 "
            "다음 단계는 이 strata를 노출하지 않는 packet plan이다."
        )
    else:
        lines.append(
            "조건부 contrast capacity가 충분하지 않으므로, 추가 label packet 전에 path decision이 필요하다."
        )
    lines.extend(
        [
            "",
            "## Relation Scope Answer",
            "",
            "다른 relation들도 train-only/full-train artifact에서 확인했다. 다만 모두 현재 active primary target은 아니다.",
            "",
            "| Relation | Full-Train Checked | Current Status | Reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    for relation, info in summary["relation_scope_status"].items():
        reason = info.get("reason_active") or info.get("reason_not_active_primary")
        lines.append(f"| `{relation}` | {info['full_train_checked']} | `{info['status']}` | {reason} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only rows only.",
            "- No validation/test rows used.",
            "- No labels filled or ingested.",
            "- No posterior trained or evaluated.",
            "- Multi-view and mesh remain audit/confirmation evidence only.",
            "- H001 and paper artifacts were not modified.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_decision_dir = as_abs(args.path_decision_dir)
    output_dir = as_abs(args.output_dir)
    path_summary = read_json(path_decision_dir / "summary.json")
    validation_errors = validate_path_decision(path_summary)
    scan = scan_full_train(args.match_rows)
    spec_summaries, top_strata = summarize_specs(scan["groups"])
    decision = capacity_decision(validation_errors, scan, spec_summaries)
    status = STATUS_ERROR if validation_errors else (STATUS_READY if decision["capacity_pass"] else STATUS_BLOCKED)
    next_todo = decision["next_todo"]

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "spec_capacity": output_dir / "conditional_strata_capacity.csv",
        "top_strata": output_dir / "top_conditional_strata.jsonl",
        "relation_scope_status": output_dir / "relation_scope_full_train_status.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    spec_by_name = {row["spec_name"]: row for row in spec_summaries}
    relation_status = relation_scope_status()
    summary = {
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "next_todo": next_todo,
        "input_artifacts": {
            "path_decision_summary": rel_path(path_decision_dir / "summary.json"),
            "match_rows": rel_path(args.match_rows),
        },
        "output_artifacts": {key: rel_path(path) for key, path in output_paths.items()},
        "counts": {
            "primary_rows": scan["primary_rows"],
            "diagnostic_rows": scan["diagnostic_rows"],
            "joined_rows": scan["joined_rows"],
            "distinct": scan["distinct"],
            "predicate_counts": dict(scan["counts"]["predicate"]),
            "role_counts": dict(scan["counts"]["role"]),
            "predicate_role_counts": dict(scan["counts"]["predicate_role"]),
            "rank_band_counts": dict(scan["counts"]["rank_band"]),
            "geometry_bucket_counts": dict(scan["counts"]["geometry_bucket"]),
            "coverage_proxy_counts": dict(scan["counts"]["coverage_proxy"]),
            "uncertainty_bucket_counts": dict(scan["counts"]["uncertainty_bucket"]),
            "diagnostic_connected_counts": dict(scan["counts"]["diagnostic_cell"]),
        },
        "raw_feature_join_summary": scan["raw_join"],
        "spec_summaries": spec_summaries,
        "spec_summary_by_name": spec_by_name,
        "capacity_decision": decision,
        "relation_scope_status": relation_status,
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
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "human_label_claim": False,
            "proxy_capacity_only": True,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["relation_scope_status"], relation_status)
    write_jsonl(output_paths["top_strata"], top_strata)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_csv(
        output_paths["spec_capacity"],
        spec_summaries,
        fieldnames=[
            "spec_name",
            "fields",
            "groups",
            "rows",
            "mixed_accept_reject_groups",
            "mixed_with_uncertain_groups",
            "balanced_pair_capacity",
            "groups_with_uncertain",
            "by_predicate",
        ],
    )
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    decision = summary["capacity_decision"]
    strict = summary["spec_summary_by_name"].get(STRICT_SPEC, {})
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"primary_rows={summary['counts']['primary_rows']}")
    print(f"diagnostic_rows={summary['counts']['diagnostic_rows']}")
    print(f"strict_spec={STRICT_SPEC}")
    print(f"strict_mixed_groups={strict.get('mixed_accept_reject_groups')}")
    print(f"strict_balanced_capacity={strict.get('balanced_pair_capacity')}")
    print(f"capacity_pass={decision['capacity_pass']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
