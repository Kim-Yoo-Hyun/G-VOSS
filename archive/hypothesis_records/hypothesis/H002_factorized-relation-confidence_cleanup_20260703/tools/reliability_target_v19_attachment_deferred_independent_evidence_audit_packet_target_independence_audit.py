#!/usr/bin/env python3
"""Audit target independence for H002 v19 attachment audit-packet targets."""

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

DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit"

EXPECTED_INGESTION_STATUS = (
    "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingested_positive_sparse_with_probe_risk"
)
EXPECTED_NEXT_TODO = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit"
NEXT_TODO = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_path_decision_after_audit"

SCHEMA_VERSION = "h002_reliability_target_v19_attachment_packet_target_independence_audit_v1"

POSTERIOR_MIN_PER_CLASS = 50
STRICT_MIN_ROWS = 80
STRICT_MIN_PER_CLASS = 40
DIAGNOSTIC_MIN_ROWS = 40
DIAGNOSTIC_MIN_PER_CLASS = 15

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 8,
    "large_group_purity": 0.90,
}

TARGET_SPECS = {
    "relation_binary": {
        "field": "relation_reliability_binary_target",
        "usable": "relation_reliability_binary_usable",
        "role": "primary",
    },
    "geometry_support_binary": {
        "field": "geometry_support_binary_target",
        "usable": "geometry_support_binary_usable",
        "role": "auxiliary",
    },
    "connected_diagnostic": {
        "field": "connected_diagnostic_target",
        "usable": "connected_diagnostic_usable",
        "role": "diagnostic",
    },
    "relation_multiclass": {
        "field": "relation_reliability_multiclass_target",
        "usable": None,
        "role": "diagnostic",
    },
    "uncertainty_multiclass": {
        "field": "review_uncertainty",
        "usable": None,
        "role": "diagnostic",
    },
    "evidence_tier_multiclass": {
        "field": "evidence_tier",
        "usable": None,
        "role": "provenance",
    },
}

RISK_PREDICTORS = [
    "predicate_label",
    "packet_role",
    "evidence_tier",
    "audit_ready_state_hidden",
    "visual_context_state_hidden",
    "subject_label",
    "object_label",
    "subject_object_visible_pair",
    "scan_id_hidden",
    "subgraph_id_hidden",
    "subject_id_hidden",
    "object_id_hidden",
    "shared_origin_frame_bucket",
    "shared_crop_rank_bucket",
    "materialized_image_bucket",
    "mesh_ready_hidden",
    "sequence_ready_hidden",
    "primary_reason_v19",
]

SLICE_SPECS = {
    "full": [],
    "same_predicate": ["predicate_label"],
    "same_packet_role": ["packet_role"],
    "same_evidence_tier": ["evidence_tier"],
    "same_audit_ready_state": ["audit_ready_state_hidden"],
    "same_visual_context_state": ["visual_context_state_hidden"],
    "same_shared_origin_bucket": ["shared_origin_frame_bucket"],
    "same_shared_crop_rank_bucket": ["shared_crop_rank_bucket"],
    "same_materialized_image_bucket": ["materialized_image_bucket"],
    "same_subject_label": ["subject_label"],
    "same_object_label": ["object_label"],
    "same_visible_pair": ["subject_object_visible_pair"],
    "same_scan": ["scan_id_hidden"],
    "same_subgraph": ["subgraph_id_hidden"],
    "same_predicate_tier": ["predicate_label", "evidence_tier"],
    "same_predicate_role": ["predicate_label", "packet_role"],
    "same_predicate_visual_context": ["predicate_label", "visual_context_state_hidden"],
    "same_role_tier": ["packet_role", "evidence_tier"],
    "same_role_visual_context": ["packet_role", "visual_context_state_hidden"],
    "same_tier_shared_origin": ["evidence_tier", "shared_origin_frame_bucket"],
    "same_predicate_subject": ["predicate_label", "subject_label"],
    "same_predicate_object": ["predicate_label", "object_label"],
    "same_predicate_visible_pair": ["predicate_label", "subject_object_visible_pair"],
    "same_reason": ["primary_reason_v19"],
}

CONTROL_EQUIVALENCE = {
    "predicate_label": {"predicate_label"},
    "packet_role": {"packet_role"},
    "evidence_tier": {"evidence_tier", "audit_ready_state_hidden", "visual_context_state_hidden"},
    "audit_ready_state_hidden": {"evidence_tier", "audit_ready_state_hidden", "visual_context_state_hidden"},
    "visual_context_state_hidden": {"evidence_tier", "audit_ready_state_hidden", "visual_context_state_hidden"},
    "subject_label": {"subject_label"},
    "object_label": {"object_label"},
    "subject_object_visible_pair": {"subject_object_visible_pair", "subject_label", "object_label"},
    "scan_id_hidden": {"scan_id_hidden", "subgraph_id_hidden"},
    "subgraph_id_hidden": {"scan_id_hidden", "subgraph_id_hidden"},
    "shared_origin_frame_bucket": {"shared_origin_frame_bucket"},
    "shared_crop_rank_bucket": {"shared_crop_rank_bucket"},
    "materialized_image_bucket": {"materialized_image_bucket"},
    "primary_reason_v19": {"primary_reason_v19"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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
    fieldnames: list[str] = []
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
        "connected_primary_binary_target",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "ingestion_boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})
    for key in ["ingests_existing_labels", "reads_hidden_manifest_after_label_lock"]:
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
        if row.get("predicate_label") not in {"attached to", "hanging on", "connected to"}:
            errors.append({"error_type": "unexpected_predicate", "packet_id": packet_id, "predicate": row.get("predicate_label")})
        if row.get("packet_role") == "connected_diagnostic_only" and row.get("relation_reliability_binary_usable"):
            errors.append({"error_type": "connected_used_as_primary_binary", "packet_id": packet_id})
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
    if total == 0:
        return 0.0
    value = 0.0
    for count in counter.values():
        if count:
            p = count / total
            value -= p * math.log(p, 2)
    return value


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


def stable_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("packet_id")), str(row.get("blind_review_id"))


def group_key(row: dict[str, Any], keys: list[str]) -> str:
    if not keys:
        return "__all__"
    return "||".join(f"{key}={row.get(key, 'missing')}" for key in keys)


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
            selected.extend(sorted(items, key=stable_sort_key)[:min_count])
    counts = target_counts(selected, target_name)
    return selected, {
        "balanced_keys": keys,
        "groups": len(grouped),
        "mixed_groups": mixed_groups,
        "selected_rows": len(selected),
        "selected_counts": dict(counts),
    }


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
        blocking_risks = [risk for risk in slice_risks if risk.get("risk_flag") and risk["predictor"] not in controlled]
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
                "blocking_risk_flags": len(blocking_risks),
                "strict_clear": strict_mass and not blocking_risks,
                "diagnostic_clear": diagnostic_mass and not blocking_risks,
                "top_blocking_predictors": ",".join(risk["predictor"] for risk in blocking_risks[:8]),
            }
        )
    return audits, risks


def audit_target(rows: list[dict[str, Any]], target_name: str) -> dict[str, Any]:
    rows_for_target = target_rows(rows, target_name)
    counts = target_counts(rows_for_target, target_name)
    mass_pass = class_mass_pass(counts, POSTERIOR_MIN_PER_CLASS)
    slice_audits, _ = slice_audit_for_target(rows, target_name)
    strict_clear_slices = [item for item in slice_audits if item["strict_clear"]]
    diagnostic_clear_slices = [item for item in slice_audits if item["diagnostic_clear"]]
    posterior_allowed = target_name == "relation_binary" and mass_pass and bool(strict_clear_slices)
    if len(counts) < 2:
        status = "single_class_or_not_usable"
    elif target_name == "relation_binary" and not mass_pass:
        status = "blocked_positive_sparse"
    elif target_name == "relation_binary" and not strict_clear_slices:
        status = "blocked_no_strict_independent_slice"
    elif target_name == "relation_binary":
        status = "ready_for_posterior_feature_join"
    elif not mass_pass:
        status = "auxiliary_or_diagnostic_class_sparse"
    elif not strict_clear_slices:
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
        "strict_clear_slice_count": len(strict_clear_slices),
        "diagnostic_clear_slice_count": len(diagnostic_clear_slices),
        "strict_clear_slices": [item["slice_name"] for item in strict_clear_slices],
        "diagnostic_clear_slices": [item["slice_name"] for item in diagnostic_clear_slices],
        "posterior_allowed": posterior_allowed,
        "status": status,
    }


def quick_risks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    risks = []
    for target_name in TARGET_SPECS:
        rows_for_target = target_rows(rows, target_name)
        for predictor in RISK_PREDICTORS:
            risks.append(majority_risk(rows_for_target, predictor, target_name))
    return risks


def write_report(path: Path, summary: dict[str, Any]) -> None:
    relation = summary["target_decisions"]["relation_binary"]
    geometry = summary["target_decisions"]["geometry_support_binary"]
    connected = summary["target_decisions"]["connected_diagnostic"]
    lines = [
        "# H002 V19 Attachment Audit Packet Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        summary["decision"],
        "",
        "## Target Decisions",
        "",
        "| Target | Role | Rows | Classes | Class Mass | Strict Clear | Diagnostic Clear | Posterior | Status |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | --- | --- |",
    ]
    for target_name, decision in summary["target_decisions"].items():
        lines.append(
            "| "
            f"`{target_name}` | `{decision['role']}` | {decision['rows']} | "
            f"`{decision['class_counts']}` | {decision['class_mass_pass']} | "
            f"{decision['strict_clear_slice_count']} | {decision['diagnostic_clear_slice_count']} | "
            f"{decision['posterior_allowed']} | `{decision['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Key Findings",
            "",
            f"- Primary relation target: rows `{relation['rows']}`, classes `{relation['class_counts']}`, min class `{relation['min_class_count']}`.",
            f"- Geometry-support target: rows `{geometry['rows']}`, classes `{geometry['class_counts']}`, min class `{geometry['min_class_count']}`.",
            f"- Connected diagnostic target: rows `{connected['rows']}`, classes `{connected['class_counts']}`, min class `{connected['min_class_count']}`.",
            f"- Full quick-probe risk flags: `{summary['counts']['full_quick_probe_risk_flags']}`.",
            f"- Slice-level blocking risk flags: `{summary['counts']['slice_blocking_risk_flags']}`.",
            f"- Relation strict clear slices: `{relation['strict_clear_slice_count']}`.",
            f"- Relation diagnostic clear slices: `{relation['diagnostic_clear_slice_count']}`.",
            "- The primary relation target remains blocked because positive class mass is below the predeclared gate.",
            "",
            "## Boundary",
            "",
            "- Train-only rows.",
            "- No validation/test rows.",
            "- No posterior trained.",
            "- Hidden fields, evidence tier, and packet role are audit/control fields only, not model inputs.",
            "- Multi-view and mesh are not used as model inputs.",
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

    slice_audits: list[dict[str, Any]] = []
    slice_risks: list[dict[str, Any]] = []
    for target_name in TARGET_SPECS:
        target_slice_audits, target_slice_risks = slice_audit_for_target(rows, target_name)
        slice_audits.extend(target_slice_audits)
        slice_risks.extend(target_slice_risks)
    slice_blocking_risk_flags = sum(item["blocking_risk_flags"] for item in slice_audits)

    relation = target_decisions["relation_binary"]
    if validation_errors:
        status = "h002_reliability_target_v19_attachment_deferred_audit_packet_target_independence_audit_errors"
        decision = "Validation errors remain; posterior smoke is not allowed."
    elif relation["posterior_allowed"]:
        status = "h002_reliability_target_v19_attachment_deferred_audit_packet_target_independence_audit_ready"
        decision = "Primary relation reliability target has enough class mass and a strict clear controlled slice."
    elif relation["status"] == "blocked_positive_sparse":
        status = "h002_reliability_target_v19_attachment_deferred_audit_packet_target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
        decision = "Primary relation reliability target is blocked by positive sparsity; shortcut-risk probes also remain high."
    else:
        status = "h002_reliability_target_v19_attachment_deferred_audit_packet_target_independence_audit_blocked_shortcut_risk"
        decision = "Primary relation reliability target has no strict clear independent slice; posterior smoke remains blocked."

    posterior_allowed = bool(relation["posterior_allowed"]) and not validation_errors
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "target_decisions": output_dir / "target_decisions.json",
        "full_shortcut_risks": output_dir / "full_shortcut_risks.json",
        "slice_audit": output_dir / "slice_audit.csv",
        "slice_risks": output_dir / "slice_risks.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
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
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "full_quick_probe_risk_flags": len(full_risk_flags),
            "slice_audit_rows": len(slice_audits),
            "slice_risk_rows": len(slice_risks),
            "slice_blocking_risk_flags": slice_blocking_risk_flags,
        },
        "target_decisions": target_decisions,
        "risk_thresholds": RISK_THRESHOLDS,
        "slice_thresholds": {
            "posterior_min_per_class": POSTERIOR_MIN_PER_CLASS,
            "strict_min_rows": STRICT_MIN_ROWS,
            "strict_min_per_class": STRICT_MIN_PER_CLASS,
            "diagnostic_min_rows": DIAGNOSTIC_MIN_ROWS,
            "diagnostic_min_per_class": DIAGNOSTIC_MIN_PER_CLASS,
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "reads_hidden_manifest_after_label_lock": True,
            "hidden_fields_as_model_input": False,
            "uses_source_score_or_rank": False,
            "uses_geometry_status_or_rank_hint": False,
            "uses_p_geom_valid": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": posterior_allowed,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_json(output_paths["target_decisions"], target_decisions)
    write_json(output_paths["full_shortcut_risks"], full_risks)
    write_csv(output_paths["slice_audit"], slice_audits)
    write_json(output_paths["slice_risks"], slice_risks)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    relation = summary["target_decisions"]["relation_binary"]
    geometry = summary["target_decisions"]["geometry_support_binary"]
    connected = summary["target_decisions"]["connected_diagnostic"]
    print(f"status={summary['status']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"relation_binary_rows={relation['rows']}")
    print(f"relation_binary_counts={relation['class_counts']}")
    print(f"relation_class_mass_pass={relation['class_mass_pass']}")
    print(f"relation_strict_clear_slices={relation['strict_clear_slice_count']}")
    print(f"relation_diagnostic_clear_slices={relation['diagnostic_clear_slice_count']}")
    print(f"geometry_support_rows={geometry['rows']}")
    print(f"geometry_support_counts={geometry['class_counts']}")
    print(f"connected_diagnostic_rows={connected['rows']}")
    print(f"connected_diagnostic_counts={connected['class_counts']}")
    print(f"full_quick_probe_risk_flags={summary['counts']['full_quick_probe_risk_flags']}")
    print(f"slice_blocking_risk_flags={summary['counts']['slice_blocking_risk_flags']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
