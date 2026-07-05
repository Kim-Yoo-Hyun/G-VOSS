#!/usr/bin/env python3
"""Audit target independence for H002 v22 hanging-on audit-packet targets."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

INGESTION_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion"
OUTPUT_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit"

EXPECTED_INGESTION_STATUS = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingested_positive_sparse_with_probe_risk"
EXPECTED_NEXT_TODO = "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit"
NEXT_TODO = "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_after_audit"

SCHEMA_VERSION = "h002_reliability_target_v22_hanging_on_target_independence_audit_v1"
STATUS_BLOCKED_POSITIVE_SPARSE_RISK = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
STATUS_BLOCKED_SHORTCUT_RISK = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit_blocked_shortcut_risk"
STATUS_READY = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit_ready"
STATUS_ERROR = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit_errors"

POSTERIOR_MIN_PER_CLASS = 60
STRICT_MIN_ROWS = 160
STRICT_MIN_PER_CLASS = 60
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
    "relation_binary": {
        "field": "relation_reliability_binary_target",
        "usable": "relation_reliability_binary_usable",
        "role": "primary",
    },
    "relation_multiclass": {
        "field": "relation_reliability_multiclass_target",
        "usable": None,
        "role": "diagnostic",
    },
    "geometry_support_binary": {
        "field": "geometry_support_binary_target",
        "usable": "geometry_support_binary_usable",
        "role": "auxiliary",
    },
    "endpoint_identity_binary": {
        "field": "endpoint_identity_binary_target",
        "usable": None,
        "role": "auxiliary",
    },
    "coverage_binary": {
        "field": "coverage_binary_target",
        "usable": None,
        "role": "auxiliary",
    },
    "uncertainty_multiclass": {
        "field": "review_uncertainty",
        "usable": None,
        "role": "diagnostic",
    },
}

RISK_PREDICTORS = [
    "predicate_label",
    "predicate_family",
    "packet_role",
    "relation_family_visible",
    "evidence_tier",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "primary_reason_v22",
    "subject_label",
    "object_label",
    "subject_object_visible_pair",
    "object_family_pair_hidden",
    "scan_id_hidden",
    "subgraph_id_hidden",
    "subject_id_hidden",
    "object_id_hidden",
    "planned_proxy_role_hidden",
    "strict_group_value_hidden",
    "geometry_bucket_hidden",
    "rank_band_hidden",
    "coverage_proxy_hidden",
    "candidate_gt_label_match_status_hidden",
    "gt_label_match_status_hidden",
    "audit_ready_state_hidden",
    "visual_context_state_hidden",
    "shared_crop_rank_bucket",
    "shared_origin_frame_bucket",
    "materialized_image_bucket",
    "uncertainty_bucket_hidden",
]

SLICE_SPECS = {
    "full": [],
    "same_evidence_tier": ["evidence_tier"],
    "same_proxy_role": ["planned_proxy_role_hidden"],
    "same_geometry_bucket": ["geometry_bucket_hidden"],
    "same_rank_band": ["rank_band_hidden"],
    "same_gt_status": ["gt_label_match_status_hidden"],
    "same_scan": ["scan_id_hidden"],
    "same_visible_pair": ["subject_object_visible_pair"],
    "same_strict_group": ["strict_group_value_hidden"],
    "same_reason": ["primary_reason_v22"],
    "same_subject_label": ["subject_label"],
    "same_object_label": ["object_label"],
    "same_object_family_pair": ["object_family_pair_hidden"],
    "same_geometry_support": ["review_geometry_support"],
    "same_endpoint_identity": ["review_endpoint_identity"],
    "same_coverage": ["review_coverage"],
    "same_uncertainty": ["review_uncertainty"],
    "same_proxy_geometry": ["planned_proxy_role_hidden", "geometry_bucket_hidden"],
    "same_rank_geometry": ["rank_band_hidden", "geometry_bucket_hidden"],
    "same_gt_geometry": ["gt_label_match_status_hidden", "geometry_bucket_hidden"],
    "same_rank_proxy": ["rank_band_hidden", "planned_proxy_role_hidden"],
    "same_tier_geometry": ["evidence_tier", "geometry_bucket_hidden"],
    "same_scan_rank": ["scan_id_hidden", "rank_band_hidden"],
}

CONTROL_EQUIVALENCE = {
    "predicate_label": {"predicate_label", "predicate_family", "packet_role", "relation_family_visible"},
    "predicate_family": {"predicate_label", "predicate_family", "packet_role", "relation_family_visible"},
    "packet_role": {"predicate_label", "predicate_family", "packet_role", "relation_family_visible"},
    "relation_family_visible": {"predicate_label", "predicate_family", "packet_role", "relation_family_visible"},
    "evidence_tier": {"evidence_tier", "audit_ready_state_hidden", "visual_context_state_hidden"},
    "planned_proxy_role_hidden": {"planned_proxy_role_hidden"},
    "geometry_bucket_hidden": {"geometry_bucket_hidden"},
    "rank_band_hidden": {"rank_band_hidden"},
    "gt_label_match_status_hidden": {"gt_label_match_status_hidden", "candidate_gt_label_match_status_hidden"},
    "candidate_gt_label_match_status_hidden": {"gt_label_match_status_hidden", "candidate_gt_label_match_status_hidden"},
    "scan_id_hidden": {"scan_id_hidden", "subgraph_id_hidden"},
    "subgraph_id_hidden": {"scan_id_hidden", "subgraph_id_hidden"},
    "subject_object_visible_pair": {"subject_object_visible_pair", "subject_label", "object_label"},
    "subject_label": {"subject_label"},
    "object_label": {"object_label"},
    "object_family_pair_hidden": {"object_family_pair_hidden"},
    "strict_group_value_hidden": {"strict_group_value_hidden", "rank_band_hidden", "geometry_bucket_hidden", "object_family_pair_hidden"},
    "primary_reason_v22": {"primary_reason_v22"},
    "review_geometry_support": {"review_geometry_support"},
    "review_endpoint_identity": {"review_endpoint_identity"},
    "review_coverage": {"review_coverage", "coverage_proxy_hidden"},
    "review_uncertainty": {"review_uncertainty", "uncertainty_bucket_hidden"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=INGESTION_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
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


def validate_ingestion(summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "expected": EXPECTED_INGESTION_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_ingestion_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "ingestion_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "hidden_manifest_used_for_label_fill",
        "existing_gt_match_axis_used_for_label_fill",
        "hidden_fields_as_model_input",
        "uses_source_score_or_rank",
        "uses_geometry_status_or_rank_hint",
        "uses_p_geom_valid",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "ingestion_boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})
    for key in ["ingests_existing_labels", "reads_hidden_manifest_after_label_lock", "existing_gt_match_axis_joined_after_label_lock"]:
        if boundary.get(key) is not True:
            errors.append({"error_type": "ingestion_boundary_violation", "key": key, "expected": True, "actual": boundary.get(key)})
    if summary.get("counts", {}).get("rows") != len(rows):
        errors.append({"error_type": "row_count_mismatch", "expected": summary.get("counts", {}).get("rows"), "actual": len(rows)})
    ids = [str(row.get("packet_id") or "") for row in rows]
    for packet_id, count in Counter(ids).items():
        if not packet_id or count > 1:
            errors.append({"error_type": "packet_id_error", "packet_id": packet_id, "count": count})
    for row in rows:
        packet_id = row.get("packet_id")
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "packet_id": packet_id, "split": row.get("split")})
        if row.get("predicate_family") != "attachment_deferred":
            errors.append({"error_type": "unexpected_family", "packet_id": packet_id, "family": row.get("predicate_family")})
        if row.get("predicate_label") != "hanging on":
            errors.append({"error_type": "unexpected_predicate", "packet_id": packet_id, "predicate": row.get("predicate_label")})
        if row.get("relation_reliability_binary_usable") is True and row.get("review_relation_reliability") == "abstain_uncertain":
            errors.append({"error_type": "abstain_marked_binary_usable", "packet_id": packet_id})
    return errors


def target_rows(rows: list[dict[str, Any]], target_name: str) -> list[dict[str, Any]]:
    usable = TARGET_SPECS[target_name]["usable"]
    if usable is None:
        return list(rows)
    return [row for row in rows if row.get(usable) is True]


def target_value(row: dict[str, Any], target_name: str) -> Any:
    return row.get(TARGET_SPECS[target_name]["field"])


def target_counts(rows: list[dict[str, Any]], target_name: str) -> Counter:
    return Counter(str(target_value(row, target_name)) for row in rows)


def min_class_count(counts: Counter) -> int:
    return min(counts.values()) if counts else 0


def class_mass_pass(counts: Counter, threshold: int) -> bool:
    return len(counts) >= 2 and min_class_count(counts) >= threshold


def entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    return -sum((count / total) * math.log(count / total, 2) for count in counter.values() if count)


def normalized_mutual_information(rows: list[dict[str, Any]], predictor: str, target_name: str) -> float:
    if not rows:
        return 0.0
    label_counts = Counter(str(target_value(row, target_name)) for row in rows)
    group_counts = Counter(str(row.get(predictor, "missing")) for row in rows)
    joint = Counter((str(row.get(predictor, "missing")), str(target_value(row, target_name))) for row in rows)
    total = len(rows)
    mi = 0.0
    for (group, label), count in joint.items():
        pxy = count / total
        px = group_counts[group] / total
        py = label_counts[label] / total
        if pxy and px and py:
            mi += pxy * math.log(pxy / (px * py), 2)
    denom = math.sqrt(entropy(group_counts) * entropy(label_counts))
    return mi / denom if denom else 0.0


def majority_risk(rows: list[dict[str, Any]], predictor: str, target_name: str) -> dict[str, Any]:
    if not rows:
        return {
            "predictor": predictor,
            "target": target_name,
            "rows": 0,
            "groups": 0,
            "risk_flag": False,
            "majority_rule_accuracy": None,
            "majority_baseline_accuracy": None,
            "majority_excess_over_baseline": None,
            "normalized_mutual_information": None,
            "top_groups": [],
        }
    counts = target_counts(rows, target_name)
    baseline = max(counts.values()) / len(rows)
    groups: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        groups[str(row.get(predictor, "missing"))][str(target_value(row, target_name))] += 1
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
        "predictor": predictor,
        "target": target_name,
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
    return str(row.get("packet_id", "")), str(row.get("blind_review_id", ""))


def balanced_slice(rows: list[dict[str, Any]], keys: list[str], target_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[group_key(row, keys)][str(target_value(row, target_name))].append(row)
    selected: list[dict[str, Any]] = []
    mixed_groups = 0
    for by_label in grouped.values():
        if len(by_label) < 2:
            continue
        mixed_groups += 1
        min_count = min(len(items) for items in by_label.values())
        for items in by_label.values():
            selected.extend(sorted(items, key=stable_key)[:min_count])
    return selected, {"groups": len(grouped), "mixed_groups": mixed_groups}


def controlled_predictors(keys: list[str]) -> set[str]:
    controlled = set(keys)
    for key in keys:
        controlled.update(CONTROL_EQUIVALENCE.get(key, set()))
    return controlled


def slice_audit_for_target(rows: list[dict[str, Any]], target_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    audits: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    rows_for_target = target_rows(rows, target_name)
    for slice_name, keys in SLICE_SPECS.items():
        selected, selection = balanced_slice(rows_for_target, keys, target_name)
        counts = target_counts(selected, target_name)
        controlled = controlled_predictors(keys)
        slice_risks = [majority_risk(selected, predictor, target_name) for predictor in RISK_PREDICTORS]
        risks.extend({"slice_name": slice_name, **risk} for risk in slice_risks)
        blocking = [risk for risk in slice_risks if risk.get("risk_flag") and risk["predictor"] not in controlled]
        strict_mass = len(selected) >= STRICT_MIN_ROWS and class_mass_pass(counts, STRICT_MIN_PER_CLASS)
        diagnostic_mass = len(selected) >= DIAGNOSTIC_MIN_ROWS and class_mass_pass(counts, DIAGNOSTIC_MIN_PER_CLASS)
        audits.append(
            {
                "target": target_name,
                "slice_name": slice_name,
                "balanced_keys": "|".join(keys) if keys else "__none__",
                "rows": len(selected),
                "class_counts": dict(counts),
                "min_class_count": min_class_count(counts),
                "groups": selection["groups"],
                "mixed_groups": selection["mixed_groups"],
                "strict_mass": strict_mass,
                "diagnostic_mass": diagnostic_mass,
                "blocking_risk_flags": len(blocking),
                "strict_clear": strict_mass and not blocking,
                "diagnostic_clear": diagnostic_mass and not blocking,
                "top_blocking_predictors": ",".join(risk["predictor"] for risk in blocking[:8]),
            }
        )
    return audits, risks


def audit_target(rows: list[dict[str, Any]], target_name: str) -> dict[str, Any]:
    rows_for_target = target_rows(rows, target_name)
    counts = target_counts(rows_for_target, target_name)
    mass_pass = class_mass_pass(counts, POSTERIOR_MIN_PER_CLASS)
    slice_audits, _ = slice_audit_for_target(rows, target_name)
    strict_clear = [row for row in slice_audits if row["strict_clear"]]
    diagnostic_clear = [row for row in slice_audits if row["diagnostic_clear"]]
    posterior_allowed = target_name == "relation_binary" and mass_pass and bool(strict_clear)
    if len(counts) < 2:
        status = "single_class_or_not_usable"
    elif target_name == "relation_binary" and not mass_pass:
        status = "blocked_positive_sparse"
    elif target_name == "relation_binary" and not strict_clear:
        status = "blocked_no_strict_independent_slice"
    elif target_name == "relation_binary":
        status = "ready_for_posterior_feature_join"
    elif not mass_pass:
        status = "auxiliary_or_diagnostic_class_sparse"
    elif not strict_clear:
        status = "auxiliary_or_diagnostic_no_strict_independent_slice"
    else:
        status = "auxiliary_or_diagnostic_strict_slice_available"
    return {
        "target": target_name,
        "role": TARGET_SPECS[target_name]["role"],
        "rows": len(rows_for_target),
        "class_counts": dict(counts),
        "min_class_count": min_class_count(counts),
        "class_mass_pass": mass_pass,
        "strict_clear_slice_count": len(strict_clear),
        "diagnostic_clear_slice_count": len(diagnostic_clear),
        "strict_clear_slices": [row["slice_name"] for row in strict_clear],
        "diagnostic_clear_slices": [row["slice_name"] for row in diagnostic_clear],
        "posterior_allowed": posterior_allowed,
        "status": status,
    }


def quick_risks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for target_name in TARGET_SPECS:
        target_subset = target_rows(rows, target_name)
        for predictor in RISK_PREDICTORS:
            out.append(majority_risk(target_subset, predictor, target_name))
    return out


def risk_flag_summary(risks: list[dict[str, Any]]) -> dict[str, Any]:
    flags = [risk for risk in risks if risk.get("risk_flag")]
    return {
        "risk_flags": len(flags),
        "by_target": dict(Counter(str(risk["target"]) for risk in flags)),
        "by_predictor": dict(Counter(str(risk["predictor"]) for risk in flags)),
        "top_flags": sorted(
            [
                {
                    "target": risk["target"],
                    "predictor": risk["predictor"],
                    "rows": risk["rows"],
                    "majority_rule_accuracy": risk["majority_rule_accuracy"],
                    "majority_baseline_accuracy": risk["majority_baseline_accuracy"],
                    "normalized_mutual_information": risk["normalized_mutual_information"],
                }
                for risk in flags
            ],
            key=lambda row: (-(row["normalized_mutual_information"] or 0), str(row["target"]), str(row["predictor"])),
        )[:30],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    relation = summary["target_decisions"]["relation_binary"]
    lines = [
        "# H002 V22 Hanging-On Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"decision = {summary['decision']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Target Decisions",
        "",
        "| Target | Role | Rows | Classes | Class Mass | Strict Clear | Diagnostic Clear | Posterior | Status |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | --- | --- |",
    ]
    for name, decision in summary["target_decisions"].items():
        lines.append(
            "| "
            f"`{name}` | `{decision['role']}` | {decision['rows']} | "
            f"`{decision['class_counts']}` | {decision['class_mass_pass']} | "
            f"{decision['strict_clear_slice_count']} | {decision['diagnostic_clear_slice_count']} | "
            f"{decision['posterior_allowed']} | `{decision['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Key Findings",
            "",
            f"- Primary relation target rows/classes: `{relation['rows']}` / `{relation['class_counts']}`.",
            f"- Minimum class mass: `{relation['min_class_count']}`, required `{POSTERIOR_MIN_PER_CLASS}`.",
            f"- Full quick-probe risk flags: `{summary['counts']['full_quick_probe_risk_flags']}`.",
            f"- Slice-level blocking risk flags: `{summary['counts']['slice_blocking_risk_flags']}`.",
            f"- Relation strict clear slices: `{relation['strict_clear_slice_count']}`.",
            f"- Relation diagnostic clear slices: `{relation['diagnostic_clear_slice_count']}`.",
            "- Posterior smoke remains blocked because the primary relation target is positive-sparse and has no strict clear controlled slice.",
            "- This repeats the target-construction bottleneck: reliable positives are rare and visible/hidden grouping fields can still explain many labels.",
            "",
            "## Boundary",
            "",
            "- Train-only rows only.",
            "- No validation/test rows used.",
            "- No posterior trained.",
            "- Hidden GT/rank/geometry/status fields are audit/control fields only.",
            "- Multi-view and mesh remain audit/confirmation evidence only.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_dir = as_abs(args.ingestion_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ingestion_summary = read_json(ingestion_dir / "summary.json")
    rows = read_jsonl(ingestion_dir / "ingested_rows.jsonl")

    validation_errors = validate_ingestion(ingestion_summary, rows)
    target_decisions = {target_name: audit_target(rows, target_name) for target_name in TARGET_SPECS}
    full_risks = quick_risks(rows)
    full_risk_flags = [risk for risk in full_risks if risk.get("risk_flag")]
    full_risk_summary = risk_flag_summary(full_risks)
    slice_audits: list[dict[str, Any]] = []
    slice_risks: list[dict[str, Any]] = []
    for target_name in TARGET_SPECS:
        audit_rows, risk_rows = slice_audit_for_target(rows, target_name)
        slice_audits.extend(audit_rows)
        slice_risks.extend(risk_rows)
    slice_blocking = sum(row["blocking_risk_flags"] for row in slice_audits)

    relation = target_decisions["relation_binary"]
    if validation_errors:
        status = STATUS_ERROR
        decision = "Validation errors remain; posterior smoke is not allowed."
    elif relation["posterior_allowed"]:
        status = STATUS_READY
        decision = "Primary relation target has enough class mass and a strict clear controlled slice."
    elif relation["status"] == "blocked_positive_sparse":
        status = STATUS_BLOCKED_POSITIVE_SPARSE_RISK
        decision = "Primary relation target is positive-sparse and shortcut-risk probes remain high."
    else:
        status = STATUS_BLOCKED_SHORTCUT_RISK
        decision = "Primary relation target has no strict clear independent slice."

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "target_decisions": output_dir / "target_decisions.json",
        "class_mass_audit": output_dir / "class_mass_audit.json",
        "full_shortcut_risks": output_dir / "full_shortcut_risks.json",
        "risk_flag_summary": output_dir / "risk_flag_summary.json",
        "controlled_slice_audit": output_dir / "controlled_slice_audit.csv",
        "slice_risks": output_dir / "slice_risks.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    class_mass_audit = {
        "posterior_min_per_class": POSTERIOR_MIN_PER_CLASS,
        "strict_min_rows": STRICT_MIN_ROWS,
        "strict_min_per_class": STRICT_MIN_PER_CLASS,
        "diagnostic_min_rows": DIAGNOSTIC_MIN_ROWS,
        "diagnostic_min_per_class": DIAGNOSTIC_MIN_PER_CLASS,
        "targets": target_decisions,
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "decision": decision,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "ingested_rows": rel_path(ingestion_dir / "ingested_rows.jsonl"),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "full_quick_probe_risk_flags": len(full_risk_flags),
            "slice_audit_rows": len(slice_audits),
            "slice_risk_rows": len(slice_risks),
            "slice_blocking_risk_flags": slice_blocking,
        },
        "target_decisions": target_decisions,
        "risk_flag_summary": full_risk_summary,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": bool(relation["posterior_allowed"]) and not validation_errors,
            "paper_evidence_allowed": False,
            "hidden_fields_as_model_input": False,
            "existing_gt_match_axis_as_model_input": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "h001_artifacts_modified": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["target_decisions"], target_decisions)
    write_json(output_paths["class_mass_audit"], class_mass_audit)
    write_json(output_paths["full_shortcut_risks"], {"thresholds": RISK_THRESHOLDS, "risks": full_risks})
    write_json(output_paths["risk_flag_summary"], {"thresholds": RISK_THRESHOLDS, **full_risk_summary})
    write_csv(output_paths["controlled_slice_audit"], slice_audits)
    write_json(output_paths["slice_risks"], {"thresholds": RISK_THRESHOLDS, "risks": slice_risks})
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    relation = summary["target_decisions"]["relation_binary"]
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"relation_binary_rows={relation['rows']}")
    print(f"relation_binary_counts={relation['class_counts']}")
    print(f"relation_strict_clear={relation['strict_clear_slice_count']}")
    print(f"relation_diagnostic_clear={relation['diagnostic_clear_slice_count']}")
    print(f"quick_probe_risk_flags={summary['counts']['full_quick_probe_risk_flags']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
