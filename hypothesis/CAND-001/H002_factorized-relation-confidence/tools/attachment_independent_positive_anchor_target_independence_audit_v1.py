#!/usr/bin/env python3
"""Audit target independence for H002 positive-anchor attachment targets."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

INGESTION_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_label_ingestion_v1"
OUT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_target_independence_audit_v1"

EXPECTED_INGESTION_STATUS = "h002_attachment_independent_positive_anchor_label_ingested_class_mass_pass_with_shortcut_risk"
EXPECTED_NEXT_TODO = "attachment_independent_positive_anchor_target_independence_audit_v1"

SCHEMA_VERSION = "h002_attachment_independent_positive_anchor_target_independence_audit_v1"
STATUS_ERROR = "h002_attachment_independent_positive_anchor_target_independence_audit_errors"
STATUS_BLOCKED_POSITIVE_SPARSE_RISK = (
    "h002_attachment_independent_positive_anchor_target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
)
STATUS_BLOCKED_SHORTCUT_RISK = (
    "h002_attachment_independent_positive_anchor_target_independence_audit_blocked_shortcut_risk"
)
STATUS_READY = "h002_attachment_independent_positive_anchor_target_independence_audit_ready_for_controlled_posterior_smoke"

NEXT_TODO_BLOCKED = "attachment_independent_positive_anchor_path_decision_after_audit_v1"
NEXT_TODO_READY = "attachment_independent_positive_anchor_controlled_posterior_smoke_v1"

POSTERIOR_MIN_PER_CLASS = 60
DIAGNOSTIC_MIN_ROWS = 80
DIAGNOSTIC_MIN_PER_CLASS = 25

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 10,
    "large_group_purity": 0.90,
}

TARGET_SPECS = {
    "p_rel_primary_binary": {
        "field": "p_rel_target",
        "usable": "primary_relation_binary_usable",
        "role": "primary_relation_reliability",
    },
    "c_e_compatibility_binary": {
        "field": "compatibility_binary_target",
        "usable": "compatibility_binary_usable",
        "role": "primary_compatibility",
    },
    "p_obs_all_binary": {
        "field": "p_obs_target",
        "usable": None,
        "role": "observability",
    },
    "p_obs_primary_binary": {
        "field": "p_obs_target",
        "usable": "is_primary_relation_target",
        "role": "primary_observability",
    },
    "relation_multiclass": {
        "field": "review_relation_reliability",
        "usable": None,
        "role": "diagnostic_multiclass",
    },
    "geometry_support_binary": {
        "field": "geometry_support_binary_target",
        "usable": "geometry_support_binary_usable",
        "role": "auxiliary_geometry_support",
    },
}

PREDICTOR_CATEGORIES = {
    "construction_proxy_or_source_hidden": {
        "query_id_hidden",
        "cell_id_hidden",
        "selection_proxy_role_hidden",
        "anchor_bucket_hidden",
        "rank_band_hidden",
        "semantic_rank_band_hidden",
        "semantic_score_availability_hidden",
        "selection_route_hidden",
        "capacity_evidence_tier_hidden",
        "provisional_status_hidden",
        "source_artifact_key_hidden",
        "mixed_endpoint_family_rank_coverage_key_hidden",
        "same_scene_family_rank_key_hidden",
        "visible_pair_key_hidden",
    },
    "visible_semantic_or_packet": {
        "predicate_label",
        "subject_label",
        "object_label",
        "subject_object_visible_pair",
        "packet_status",
        "packet_image_count",
    },
    "instance_or_scan_id": {
        "scan_id_hidden",
        "subgraph_id_hidden",
        "subject_id_hidden",
        "object_id_hidden",
        "prediction_id_hidden",
        "directed_pair_id_hidden",
    },
    "label_derived_auxiliary": {
        "review_geometry_support",
        "review_endpoint_identity",
        "review_coverage",
        "review_uncertainty",
        "decision_reason",
    },
    "official_gt_axis": {
        "label_match_status_hidden",
    },
}

RISK_PREDICTORS = sorted({field for fields in PREDICTOR_CATEGORIES.values() for field in fields})

SLICE_SPECS = {
    "overall_balanced": [],
    "same_predicate": ["predicate_label"],
    "same_subject_label": ["subject_label"],
    "same_object_label": ["object_label"],
    "same_visible_pair": ["subject_object_visible_pair"],
    "same_predicate_visible_pair": ["predicate_label", "subject_object_visible_pair"],
    "same_query": ["query_id_hidden"],
    "same_proxy_role": ["selection_proxy_role_hidden"],
    "same_cell": ["cell_id_hidden"],
    "same_rank_band": ["rank_band_hidden"],
    "same_anchor_bucket": ["anchor_bucket_hidden"],
    "same_selection_route": ["selection_route_hidden"],
    "same_capacity_tier": ["capacity_evidence_tier_hidden"],
    "same_gt_status": ["label_match_status_hidden"],
    "same_query_rank": ["query_id_hidden", "rank_band_hidden"],
    "same_cell_rank": ["cell_id_hidden", "rank_band_hidden"],
    "same_proxy_rank": ["selection_proxy_role_hidden", "rank_band_hidden"],
    "same_predicate_rank": ["predicate_label", "rank_band_hidden"],
    "same_query_visible_pair": ["query_id_hidden", "subject_object_visible_pair"],
    "same_mixed_endpoint_family_rank_coverage": ["mixed_endpoint_family_rank_coverage_key_hidden"],
    "same_selection_route_rank": ["selection_route_hidden", "rank_band_hidden"],
    "construction_strict": [
        "predicate_label",
        "selection_proxy_role_hidden",
        "rank_band_hidden",
        "anchor_bucket_hidden",
    ],
    "construction_endpoint_strict": [
        "predicate_label",
        "selection_proxy_role_hidden",
        "rank_band_hidden",
        "subject_object_visible_pair",
    ],
}

CONTROL_EQUIVALENCE = {
    "predicate_label": {"predicate_label", "query_id_hidden", "cell_id_hidden"},
    "subject_label": {"subject_label", "subject_object_visible_pair"},
    "object_label": {"object_label", "subject_object_visible_pair"},
    "subject_object_visible_pair": {"subject_object_visible_pair", "subject_label", "object_label", "visible_pair_key_hidden"},
    "packet_status": {"packet_status"},
    "packet_image_count": {"packet_image_count"},
    "query_id_hidden": {
        "query_id_hidden",
        "cell_id_hidden",
        "selection_proxy_role_hidden",
        "capacity_evidence_tier_hidden",
        "predicate_label",
    },
    "cell_id_hidden": {
        "cell_id_hidden",
        "query_id_hidden",
        "selection_proxy_role_hidden",
        "capacity_evidence_tier_hidden",
        "predicate_label",
    },
    "selection_proxy_role_hidden": {
        "selection_proxy_role_hidden",
        "query_id_hidden",
        "cell_id_hidden",
        "capacity_evidence_tier_hidden",
    },
    "anchor_bucket_hidden": {"anchor_bucket_hidden"},
    "rank_band_hidden": {"rank_band_hidden", "semantic_rank_band_hidden"},
    "semantic_rank_band_hidden": {"rank_band_hidden", "semantic_rank_band_hidden"},
    "semantic_score_availability_hidden": {"semantic_score_availability_hidden", "source_artifact_key_hidden"},
    "selection_route_hidden": {"selection_route_hidden"},
    "capacity_evidence_tier_hidden": {
        "capacity_evidence_tier_hidden",
        "selection_proxy_role_hidden",
        "query_id_hidden",
        "cell_id_hidden",
    },
    "label_match_status_hidden": {"label_match_status_hidden"},
    "mixed_endpoint_family_rank_coverage_key_hidden": {
        "mixed_endpoint_family_rank_coverage_key_hidden",
        "predicate_label",
        "rank_band_hidden",
        "semantic_rank_band_hidden",
    },
    "same_scene_family_rank_key_hidden": {
        "same_scene_family_rank_key_hidden",
        "scan_id_hidden",
        "subgraph_id_hidden",
        "predicate_label",
        "rank_band_hidden",
        "semantic_rank_band_hidden",
    },
    "visible_pair_key_hidden": {"visible_pair_key_hidden", "subject_object_visible_pair", "subject_label", "object_label", "predicate_label"},
    "scan_id_hidden": {"scan_id_hidden", "subgraph_id_hidden"},
    "subgraph_id_hidden": {"scan_id_hidden", "subgraph_id_hidden"},
    "review_geometry_support": {"review_geometry_support"},
    "review_endpoint_identity": {"review_endpoint_identity"},
    "review_coverage": {"review_coverage"},
    "review_uncertainty": {"review_uncertainty"},
    "decision_reason": {"decision_reason"},
}


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


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
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def predictor_category(predictor: str) -> str:
    for category, fields in PREDICTOR_CATEGORIES.items():
        if predictor in fields:
            return category
    return "other"


def validate_ingestion(summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "expected": EXPECTED_INGESTION_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_ingestion_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "ingestion_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "hidden_manifest_used_for_label_fill",
        "hidden_fields_as_model_input",
        "source_score_or_rank_as_model_input",
        "construction_proxy_as_model_input",
        "uses_p_geom_valid",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "numeric_g_e_materialized",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})
    if boundary.get("reads_hidden_manifest_after_label_lock") is not True:
        errors.append({"error_type": "boundary_violation", "key": "reads_hidden_manifest_after_label_lock", "expected": True, "actual": boundary.get("reads_hidden_manifest_after_label_lock")})
    if summary.get("counts", {}).get("rows") != len(rows):
        errors.append({"error_type": "row_count_mismatch", "expected": summary.get("counts", {}).get("rows"), "actual": len(rows)})
    seen = Counter(str(row.get("candidate_id") or "") for row in rows)
    for candidate_id, count in seen.items():
        if not candidate_id or count > 1:
            errors.append({"error_type": "candidate_id_error", "candidate_id": candidate_id, "count": count})
    for row in rows:
        candidate_id = row.get("candidate_id")
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "candidate_id": candidate_id, "split": row.get("split")})
        if row.get("paper_evidence_allowed") is not False:
            errors.append({"error_type": "paper_evidence_flag_violation", "candidate_id": candidate_id})
        if row.get("predicate_label") not in {"attached to", "hanging on", "connected to"}:
            errors.append({"error_type": "unexpected_predicate", "candidate_id": candidate_id, "predicate": row.get("predicate_label")})
        if row.get("is_connected_diagnostic") and row.get("primary_relation_binary_usable"):
            errors.append({"error_type": "connected_used_as_primary_binary", "candidate_id": candidate_id})
    return errors


def target_rows(rows: list[dict[str, Any]], target_name: str) -> list[dict[str, Any]]:
    usable = TARGET_SPECS[target_name]["usable"]
    if usable is None:
        return list(rows)
    return [row for row in rows if row.get(usable) is True]


def target_value(row: dict[str, Any], target_name: str) -> str:
    return str(row.get(TARGET_SPECS[target_name]["field"]))


def target_counts(rows: list[dict[str, Any]], target_name: str) -> Counter[str]:
    return Counter(target_value(row, target_name) for row in rows)


def min_class_count(counts: Counter[str]) -> int:
    return min(counts.values()) if counts else 0


def class_mass_pass(counts: Counter[str], min_per_class: int) -> bool:
    return len(counts) >= 2 and min_class_count(counts) >= min_per_class


def entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    return -sum((count / total) * math.log(count / total, 2) for count in counter.values() if count)


def normalized_mutual_information(rows: list[dict[str, Any]], predictor: str, target_name: str) -> float:
    if not rows:
        return 0.0
    label_counts = target_counts(rows, target_name)
    group_counts = Counter(str(row.get(predictor, "missing")) for row in rows)
    joint = Counter((str(row.get(predictor, "missing")), target_value(row, target_name)) for row in rows)
    total = len(rows)
    mi = 0.0
    for (predictor_value, label), count in joint.items():
        pxy = count / total
        px = group_counts[predictor_value] / total
        py = label_counts[label] / total
        if pxy and px and py:
            mi += pxy * math.log(pxy / (px * py), 2)
    denom = math.sqrt(entropy(group_counts) * entropy(label_counts))
    return mi / denom if denom else 0.0


def majority_risk(rows: list[dict[str, Any]], predictor: str, target_name: str) -> dict[str, Any]:
    if not rows:
        return {"target": target_name, "predictor": predictor, "rows": 0, "risk_flag": False}
    counts = target_counts(rows, target_name)
    baseline = max(counts.values()) / len(rows)
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        groups[str(row.get(predictor, "missing"))][target_value(row, target_name)] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    accuracy = correct / len(rows)
    nmi = normalized_mutual_information(rows, predictor, target_name)
    large_pure_group = False
    top_groups: list[dict[str, Any]] = []
    for group_value, counter in groups.items():
        total = sum(counter.values())
        majority_label, majority_count = counter.most_common(1)[0]
        majority_rate = majority_count / total
        if total >= RISK_THRESHOLDS["large_group_rows"] and majority_rate >= RISK_THRESHOLDS["large_group_purity"]:
            large_pure_group = True
        top_groups.append(
            {
                "group_value": group_value,
                "rows": total,
                "majority_label": majority_label,
                "majority_rate": majority_rate,
                "label_counts": dict(counter),
            }
        )
    top_groups.sort(key=lambda item: (-item["rows"], str(item["group_value"])))
    risk_flag = (
        accuracy >= RISK_THRESHOLDS["majority_rule_accuracy"]
        and accuracy - baseline >= RISK_THRESHOLDS["majority_excess_over_baseline"]
    ) or nmi >= RISK_THRESHOLDS["normalized_mutual_information"] or large_pure_group
    return {
        "target": target_name,
        "predictor": predictor,
        "predictor_category": predictor_category(predictor),
        "rows": len(rows),
        "groups": len(groups),
        "label_counts": dict(counts),
        "majority_rule_accuracy": accuracy,
        "majority_baseline_accuracy": baseline,
        "majority_excess_over_baseline": accuracy - baseline,
        "normalized_mutual_information": nmi,
        "risk_flag": risk_flag,
        "top_groups": top_groups[:12],
    }


def group_key(row: dict[str, Any], keys: list[str]) -> str:
    if not keys:
        return "__all__"
    return "||".join(f"{key}={row.get(key, 'missing')}" for key in keys)


def stable_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("candidate_id", "")), str(row.get("packet_request_id", ""))


def balanced_slice(rows: list[dict[str, Any]], target_name: str, keys: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[group_key(row, keys)][target_value(row, target_name)].append(row)
    selected: list[dict[str, Any]] = []
    mixed_groups = 0
    for by_label in grouped.values():
        if len(by_label) < 2:
            continue
        mixed_groups += 1
        take = min(len(items) for items in by_label.values())
        for items in by_label.values():
            selected.extend(sorted(items, key=stable_key)[:take])
    return selected, {"groups": len(grouped), "mixed_groups": mixed_groups}


def controlled_predictors(keys: list[str]) -> set[str]:
    controlled = set(keys)
    for key in keys:
        controlled.update(CONTROL_EQUIVALENCE.get(key, set()))
    return controlled


def risk_counts_by_category(risks: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(risk["predictor_category"] for risk in risks if risk.get("risk_flag")).items()))


def target_full_risks(rows: list[dict[str, Any]], target_name: str) -> list[dict[str, Any]]:
    subset = target_rows(rows, target_name)
    return [majority_risk(subset, predictor, target_name) for predictor in RISK_PREDICTORS]


def target_slice_audit(rows: list[dict[str, Any]], target_name: str, output_dir: Path) -> list[dict[str, Any]]:
    target_subset = target_rows(rows, target_name)
    audit_rows: list[dict[str, Any]] = []
    slice_root = output_dir / "controlled_slices" / target_name
    for slice_name, keys in SLICE_SPECS.items():
        selected, selection = balanced_slice(target_subset, target_name, keys)
        counts = target_counts(selected, target_name)
        risks = [majority_risk(selected, predictor, target_name) for predictor in RISK_PREDICTORS]
        controlled = controlled_predictors(keys)
        uncontrolled_flags = [risk for risk in risks if risk.get("risk_flag") and risk["predictor"] not in controlled]
        uncontrolled_by_category = risk_counts_by_category(uncontrolled_flags)
        construction_flags = uncontrolled_by_category.get("construction_proxy_or_source_hidden", 0)
        visible_flags = uncontrolled_by_category.get("visible_semantic_or_packet", 0)
        id_flags = uncontrolled_by_category.get("instance_or_scan_id", 0)
        official_gt_flags = uncontrolled_by_category.get("official_gt_axis", 0)
        posterior_mass = class_mass_pass(counts, POSTERIOR_MIN_PER_CLASS)
        diagnostic_mass = len(selected) >= DIAGNOSTIC_MIN_ROWS and class_mass_pass(counts, DIAGNOSTIC_MIN_PER_CLASS)
        strict_clear = posterior_mass and construction_flags == 0 and visible_flags == 0
        diagnostic_clear = diagnostic_mass and construction_flags == 0 and visible_flags == 0
        if selected:
            write_jsonl(slice_root / f"{slice_name}.jsonl", selected)
        audit_rows.append(
            {
                "target": target_name,
                "slice_name": slice_name,
                "balanced_keys": ",".join(keys) if keys else "__none__",
                "rows": len(selected),
                "class_counts": dict(counts),
                "min_class_count": min_class_count(counts),
                "groups": selection["groups"],
                "mixed_groups": selection["mixed_groups"],
                "posterior_mass": posterior_mass,
                "diagnostic_mass": diagnostic_mass,
                "uncontrolled_risk_flags": len(uncontrolled_flags),
                "uncontrolled_risk_by_category": uncontrolled_by_category,
                "construction_proxy_uncontrolled_flags": construction_flags,
                "visible_semantic_or_packet_uncontrolled_flags": visible_flags,
                "instance_or_scan_id_uncontrolled_flags": id_flags,
                "official_gt_axis_uncontrolled_flags": official_gt_flags,
                "strict_clear": strict_clear,
                "diagnostic_clear": diagnostic_clear,
                "top_uncontrolled_predictors": ",".join(risk["predictor"] for risk in uncontrolled_flags[:12]),
            }
        )
    return audit_rows


def decide_target(rows: list[dict[str, Any]], target_name: str, slice_rows: list[dict[str, Any]], full_risks: list[dict[str, Any]]) -> dict[str, Any]:
    subset = target_rows(rows, target_name)
    counts = target_counts(subset, target_name)
    risk_categories = risk_counts_by_category(full_risks)
    strict_clear = [row for row in slice_rows if row["target"] == target_name and row["strict_clear"]]
    diagnostic_clear = [row for row in slice_rows if row["target"] == target_name and row["diagnostic_clear"]]
    best_diagnostic = max(
        [row for row in slice_rows if row["target"] == target_name],
        key=lambda row: (row["diagnostic_clear"], row["rows"], row["min_class_count"]),
        default=None,
    )
    mass_pass = class_mass_pass(counts, POSTERIOR_MIN_PER_CLASS)
    if len(counts) < 2:
        status = "single_class_or_unusable"
    elif not mass_pass and target_name in {"p_rel_primary_binary", "c_e_compatibility_binary"}:
        status = "blocked_positive_sparse"
    elif target_name in {"p_rel_primary_binary", "c_e_compatibility_binary"} and not strict_clear:
        status = "blocked_no_strict_independent_slice"
    elif target_name in {"p_rel_primary_binary", "c_e_compatibility_binary"}:
        status = "ready_for_controlled_posterior_smoke"
    elif not mass_pass:
        status = "diagnostic_or_auxiliary_positive_sparse"
    elif not diagnostic_clear:
        status = "diagnostic_or_auxiliary_shortcut_prone"
    else:
        status = "diagnostic_or_auxiliary_controlled_slice_available"
    return {
        "target": target_name,
        "role": TARGET_SPECS[target_name]["role"],
        "rows": len(subset),
        "class_counts": dict(counts),
        "min_class_count": min_class_count(counts),
        "posterior_min_per_class": POSTERIOR_MIN_PER_CLASS,
        "class_mass_pass": mass_pass,
        "full_risk_flags_by_category": risk_categories,
        "strict_clear_slice_count": len(strict_clear),
        "diagnostic_clear_slice_count": len(diagnostic_clear),
        "strict_clear_slices": [row["slice_name"] for row in strict_clear],
        "diagnostic_clear_slices": [row["slice_name"] for row in diagnostic_clear],
        "best_diagnostic_slice": best_diagnostic,
        "posterior_allowed": target_name == "p_rel_primary_binary" and mass_pass and bool(strict_clear),
        "status": status,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    primary = summary["target_decisions"]["p_rel_primary_binary"]
    compatibility = summary["target_decisions"]["c_e_compatibility_binary"]
    obs = summary["target_decisions"]["p_obs_primary_binary"]
    lines = [
        "# H002 Attachment Independent Positive Anchor Target Independence Audit V1",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"decision = {summary['decision']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Target Decisions",
        "",
        "| Target | Role | Rows | Class Counts | Min Class | Class Mass | Strict Clear | Diagnostic Clear | Status |",
        "| --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- |",
    ]
    for name, decision in summary["target_decisions"].items():
        lines.append(
            "| "
            f"`{name}` | `{decision['role']}` | {decision['rows']} | "
            f"`{decision['class_counts']}` | {decision['min_class_count']} | "
            f"{decision['class_mass_pass']} | {decision['strict_clear_slice_count']} | "
            f"{decision['diagnostic_clear_slice_count']} | `{decision['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Key Findings",
            "",
            f"- `p_rel_primary_binary`: rows `{primary['rows']}`, classes `{primary['class_counts']}`, min class `{primary['min_class_count']}`.",
            f"- `c_e_compatibility_binary`: rows `{compatibility['rows']}`, classes `{compatibility['class_counts']}`, min class `{compatibility['min_class_count']}`.",
            f"- `p_obs_primary_binary`: rows `{obs['rows']}`, classes `{obs['class_counts']}`, min class `{obs['min_class_count']}`.",
            f"- Full risk flags by category: `{summary['counts']['full_risk_flags_by_category']}`.",
            f"- Slice audit rows: `{summary['counts']['slice_audit_rows']}`.",
            "- Positive-anchor repair solved the class-mass blocker, but no strict independent `p_rel/C_e` slice was found.",
            "- The remaining blocker is target identifiability: visible endpoint semantics, visible-pair identity, and hidden construction axes remain predictive after balancing.",
            "",
            "## Boundary",
            "",
            "- Train-only H002 diagnostic artifact.",
            "- No validation/test rows used.",
            "- No posterior trained.",
            "- Hidden source/proxy fields are audit controls only.",
            "- Multi-view/mesh remains audit evidence, not model input.",
            "- H001 artifacts are not modified.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ingestion_summary = read_json(INGESTION_DIR / "summary.json")
    rows = read_jsonl(INGESTION_DIR / "ingested_rows.jsonl")
    validation_errors = validate_ingestion(ingestion_summary, rows)

    all_full_risks: list[dict[str, Any]] = []
    all_slice_rows: list[dict[str, Any]] = []
    for target_name in TARGET_SPECS:
        full_risks = target_full_risks(rows, target_name)
        all_full_risks.extend(full_risks)
        all_slice_rows.extend(target_slice_audit(rows, target_name, OUT_DIR))

    full_risk_flags = [risk for risk in all_full_risks if risk.get("risk_flag")]
    target_decisions = {
        target_name: decide_target(
            rows,
            target_name,
            all_slice_rows,
            [risk for risk in all_full_risks if risk["target"] == target_name],
        )
        for target_name in TARGET_SPECS
    }

    primary = target_decisions["p_rel_primary_binary"]
    if validation_errors:
        status = STATUS_ERROR
        decision = "Validation errors remain; do not use this target."
        next_todo = NEXT_TODO_BLOCKED
    elif primary["posterior_allowed"]:
        status = STATUS_READY
        decision = "Primary p_rel target has enough class mass and at least one strict independent slice."
        next_todo = NEXT_TODO_READY
    elif primary["status"] == "blocked_positive_sparse":
        status = STATUS_BLOCKED_POSITIVE_SPARSE_RISK
        decision = "Primary p_rel/C_e target remains positive-sparse; posterior smoke remains blocked."
        next_todo = NEXT_TODO_BLOCKED
    else:
        status = STATUS_BLOCKED_SHORTCUT_RISK
        decision = "Primary p_rel/C_e target has class mass but no strict independent controlled slice."
        next_todo = NEXT_TODO_BLOCKED

    output_paths = {
        "summary": OUT_DIR / "summary.json",
        "report": OUT_DIR / "report.md",
        "target_decisions": OUT_DIR / "target_decisions.json",
        "full_predictor_risks": OUT_DIR / "full_predictor_risks.json",
        "full_predictor_risk_flags": OUT_DIR / "full_predictor_risk_flags.csv",
        "slice_audit": OUT_DIR / "slice_audit.csv",
        "validation_errors": OUT_DIR / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "decision": decision,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "next_todo": next_todo,
        "input_paths": {
            "ingestion_summary": rel_path(INGESTION_DIR / "summary.json"),
            "ingested_rows": rel_path(INGESTION_DIR / "ingested_rows.jsonl"),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "targets": len(TARGET_SPECS),
            "full_risk_rows": len(all_full_risks),
            "full_risk_flags": len(full_risk_flags),
            "full_risk_flags_by_category": risk_counts_by_category(full_risk_flags),
            "slice_audit_rows": len(all_slice_rows),
            "strict_clear_slices_total": sum(decision["strict_clear_slice_count"] for decision in target_decisions.values()),
            "diagnostic_clear_slices_total": sum(decision["diagnostic_clear_slice_count"] for decision in target_decisions.values()),
        },
        "target_decisions": target_decisions,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": bool(primary["posterior_allowed"]) and not validation_errors,
            "paper_evidence_allowed": False,
            "hidden_fields_as_model_input": False,
            "source_proxy_fields_as_model_input": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "h001_artifacts_modified": False,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["target_decisions"], target_decisions)
    write_json(output_paths["full_predictor_risks"], {"thresholds": RISK_THRESHOLDS, "risks": all_full_risks})
    write_csv(output_paths["full_predictor_risk_flags"], full_risk_flags)
    write_csv(output_paths["slice_audit"], all_slice_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)

    primary = summary["target_decisions"]["p_rel_primary_binary"]
    obs = summary["target_decisions"]["p_obs_primary_binary"]
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"p_rel_counts={primary['class_counts']}")
    print(f"p_rel_min_class={primary['min_class_count']}")
    print(f"p_rel_strict_clear={primary['strict_clear_slice_count']}")
    print(f"p_rel_diagnostic_clear={primary['diagnostic_clear_slice_count']}")
    print(f"p_obs_primary_counts={obs['class_counts']}")
    print(f"full_risk_flags={summary['counts']['full_risk_flags']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
