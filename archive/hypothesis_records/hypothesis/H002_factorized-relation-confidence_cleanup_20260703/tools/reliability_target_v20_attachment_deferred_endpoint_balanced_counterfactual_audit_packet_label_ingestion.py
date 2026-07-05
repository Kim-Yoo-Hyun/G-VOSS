#!/usr/bin/env python3
"""Ingest H002 v20 attachment audit-packet labels after user label lock."""

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

FILL_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_fill"
MATERIALIZATION_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization"
OUTPUT_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingestion"

FILL_SUMMARY = FILL_DIR / "summary.json"
FILLED_SHEET = FILL_DIR / "filled_visible_review_sheet_v20.tsv"
LABEL_DECISIONS = FILL_DIR / "label_decisions_v20.jsonl"
HIDDEN_MANIFEST = MATERIALIZATION_DIR / "materialized_hidden_manifest.jsonl"

SCHEMA_VERSION = "h002_reliability_target_v20_attachment_endpoint_balanced_label_ingestion_v1"
TARGET_SCHEMA = "h002_reliability_target_v20_attachment_target_record_v1"
EXPECTED_FILL_STATUS = "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_filled_user_visible_packet"
STATUS_POSITIVE_SPARSE_WITH_RISK = "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingested_positive_sparse_with_probe_risk"
STATUS_POSITIVE_SPARSE = "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingested_positive_sparse"
STATUS_WITH_RISK = "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingested_with_probe_risk"
STATUS_READY_FOR_AUDIT = "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingested_ready_for_target_independence_audit"
STATUS_ERROR = "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingestion_errors"
NEXT_TODO = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit"

LABEL_SOURCE = "user_filled_visible_packet_v20"
MIN_CLASS_MASS_FOR_POSTERIOR = 60

MULTICLASS_TARGET = "attachment_deferred_reliability_v20_multiclass"
PRIMARY_BINARY_TARGET = "attachment_deferred_primary_reliability_v20_binary"
CONNECTED_TARGET = "attachment_deferred_connected_diagnostic_v20_multiclass"
GEOMETRY_SUPPORT_TARGET = "attachment_deferred_geometry_support_v20_binary"
ENDPOINT_TARGET = "attachment_deferred_endpoint_identity_v20_binary"
COVERAGE_TARGET = "attachment_deferred_coverage_v20_binary"
UNCERTAINTY_TARGET = "attachment_deferred_uncertainty_v20_multiclass"

PRIMARY_ROLE = "primary_attachment_reliability_candidate"
CONNECTED_ROLE = "connected_diagnostic_only"
PRIMARY_PREDICATES = {"attached to", "hanging on"}

RELIABILITY_BINARY = {"accept_reliable": 1, "reject_unreliable": 0}
GEOMETRY_BINARY = {"supported": 1, "unsupported": 0}
ENDPOINT_BINARY = {"clear_endpoint_identity": 1, "uncertain_endpoint_identity": 0}
COVERAGE_BINARY = {"sufficient": 1, "limited": 0}

RISK_PREDICTORS = [
    "predicate_label",
    "packet_role",
    "evidence_tier",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "gt_label_match_status_hidden",
    "subject_label",
    "object_label",
    "subject_object_visible_pair",
    "scan_id_hidden",
    "subgraph_id_hidden",
    "subject_id_hidden",
    "object_id_hidden",
    "audit_ready_state_hidden",
    "visual_context_state_hidden",
    "capacity_evidence_tier_hidden",
    "cell_id_hidden",
]

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 10,
    "large_group_purity": 0.90,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fill-summary", type=Path, default=FILL_SUMMARY)
    parser.add_argument("--filled-sheet", type=Path, default=FILLED_SHEET)
    parser.add_argument("--label-decisions", type=Path, default=LABEL_DECISIONS)
    parser.add_argument("--hidden-manifest", type=Path, default=HIDDEN_MANIFEST)
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
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def visible_pair(row: dict[str, Any]) -> str:
    return f"{norm(row.get('subject_label'))}|{norm(row.get('object_label'))}"


def validate_fill_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_FILL_STATUS:
        errors.append({"error_type": "unexpected_fill_status", "actual": summary.get("status")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "fill_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "hidden_manifest_read",
        "used_source_path",
        "used_scan_id",
        "used_existing_gt_match_axis",
        "used_geometry_status_or_rank_hint",
        "used_source_score_or_rank",
        "used_p_geom_valid",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "connected_primary_binary_target",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_boundary_violation", "key": key, "actual": boundary.get(key)})
    if boundary.get("locks_user_filled_labels") is not True:
        errors.append({"error_type": "fill_boundary_violation", "key": "locks_user_filled_labels", "actual": boundary.get("locks_user_filled_labels")})
    return errors


def validate_ids(label_rows: list[dict[str, str]], decision_rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    groups = {
        "filled_sheet": [row.get("packet_id", "") for row in label_rows],
        "label_decisions": [row.get("packet_id", "") for row in decision_rows],
        "hidden_manifest": [row.get("packet_id", "") for row in manifest_rows],
    }
    sets = {name: {packet_id for packet_id in ids if packet_id} for name, ids in groups.items()}
    for name, ids in groups.items():
        for packet_id, count in Counter(ids).items():
            if packet_id and count > 1:
                errors.append({"error_type": f"duplicate_{name}_packet_id", "packet_id": packet_id, "count": count})
    for source, target in [("filled_sheet", "label_decisions"), ("filled_sheet", "hidden_manifest"), ("label_decisions", "filled_sheet"), ("hidden_manifest", "filled_sheet")]:
        for packet_id in sorted(sets[source] - sets[target]):
            errors.append({"error_type": f"{source}_packet_missing_from_{target}", "packet_id": packet_id})
    return errors


def validate_manifest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(rows) != 320:
        errors.append({"error_type": "unexpected_manifest_rows", "expected": 320, "actual": len(rows)})
    for idx, row in enumerate(rows, start=1):
        packet_id = row.get("packet_id", "")
        for field in ["scan_id_hidden", "subgraph_id_hidden", "subject_id_hidden", "object_id_hidden", "existing_gt_match_axis_hidden"]:
            if field not in row:
                errors.append({"error_type": "missing_manifest_field", "row_number": idx, "packet_id": packet_id, "field": field})
        if row.get("model_input_allowed_now") is not False:
            errors.append({"error_type": "model_input_allowed_now_not_false", "row_number": idx, "packet_id": packet_id, "actual": row.get("model_input_allowed_now")})
    return errors


def validate_decisions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(rows) != 320:
        errors.append({"error_type": "unexpected_decision_rows", "expected": 320, "actual": len(rows)})
    for idx, row in enumerate(rows, start=1):
        packet_id = row.get("packet_id", "")
        provenance = row.get("provenance", {})
        for key in [
            "used_hidden_manifest",
            "used_source_path",
            "used_scan_id",
            "used_existing_gt_match_axis",
            "used_geometry_status_or_rank_hint",
            "used_source_score_or_rank",
            "used_p_geom_valid",
            "used_validation_or_test",
            "used_multi_view_as_model_input",
            "used_mesh_as_model_input",
            "paper_evidence_allowed",
        ]:
            if provenance.get(key) is not False:
                errors.append({"error_type": "decision_provenance_violation", "row_number": idx, "packet_id": packet_id, "key": key, "actual": provenance.get(key)})
    return errors


def join_rows(label_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest_by_packet = {row["packet_id"]: row for row in manifest_rows}
    out: list[dict[str, Any]] = []
    for label in label_rows:
        manifest = manifest_by_packet[label["packet_id"]]
        gt_axis = manifest.get("existing_gt_match_axis_hidden") or {}
        is_primary = label["packet_role"] == PRIMARY_ROLE and label["predicate_label"] in PRIMARY_PREDICATES
        reliability = label["review_relation_reliability"]
        row = {
            "schema_version": SCHEMA_VERSION,
            "label_source": LABEL_SOURCE,
            "split": "train",
            "packet_id": label["packet_id"],
            "blind_review_id": label["blind_review_id"],
            "candidate_relation": label["candidate_relation"],
            "scan_id_hidden": manifest.get("scan_id_hidden"),
            "subgraph_id_hidden": manifest.get("subgraph_id_hidden"),
            "source_id_hidden": manifest.get("source_id_hidden"),
            "subject_id_hidden": manifest.get("subject_id_hidden"),
            "subject_label": label["subject_label"],
            "predicate_label": label["predicate_label"],
            "predicate_family": "attachment_deferred",
            "object_id_hidden": manifest.get("object_id_hidden"),
            "object_label": label["object_label"],
            "subject_object_visible_pair": visible_pair(label),
            "packet_role": label["packet_role"],
            "evidence_tier": label["evidence_tier"],
            "audit_ready_state_hidden": manifest.get("audit_ready_state_hidden"),
            "visual_context_state_hidden": manifest.get("visual_context_state_hidden"),
            "capacity_evidence_tier_hidden": manifest.get("capacity_evidence_tier_hidden"),
            "cell_id_hidden": manifest.get("cell_id_hidden"),
            "review_relation_reliability": reliability,
            "relation_reliability_multiclass_target": reliability,
            "relation_reliability_binary_target": RELIABILITY_BINARY.get(reliability) if is_primary else None,
            "relation_reliability_binary_usable": is_primary and reliability in RELIABILITY_BINARY,
            "connected_diagnostic_target": reliability if label["packet_role"] == CONNECTED_ROLE else None,
            "connected_diagnostic_usable": label["packet_role"] == CONNECTED_ROLE,
            "review_geometry_support": label["review_geometry_support"],
            "geometry_support_binary_target": GEOMETRY_BINARY.get(label["review_geometry_support"]),
            "geometry_support_binary_usable": label["review_geometry_support"] in GEOMETRY_BINARY,
            "review_endpoint_identity": label["review_endpoint_identity"],
            "endpoint_identity_binary_target": ENDPOINT_BINARY.get(label["review_endpoint_identity"]),
            "review_coverage": label["review_coverage"],
            "coverage_binary_target": COVERAGE_BINARY.get(label["review_coverage"]),
            "review_uncertainty": label["review_uncertainty"],
            "review_notes": label["review_notes"],
            "gt_label_match_status_hidden": gt_axis.get("label_match_status_hidden"),
            "gt_label_match_hidden": gt_axis.get("label_match_hidden"),
            "gt_family_match_hidden": gt_axis.get("family_match_hidden"),
            "gt_matched_predicates_hidden": gt_axis.get("matched_predicates_hidden"),
            "gt_matched_families_hidden": gt_axis.get("matched_families_hidden"),
            "gt_label_source_hidden": gt_axis.get("label_source_hidden"),
        }
        out.append(row)
    return out


def target_record(row: dict[str, Any], target_name: str, value: Any) -> dict[str, Any]:
    return {
        "schema_version": TARGET_SCHEMA,
        "target_name": target_name,
        "target_value": value,
        "label_source": LABEL_SOURCE,
        "split": "train",
        "packet_id": row["packet_id"],
        "blind_review_id": row["blind_review_id"],
        "scan_id_hidden": row["scan_id_hidden"],
        "subgraph_id_hidden": row["subgraph_id_hidden"],
        "subject_id_hidden": row["subject_id_hidden"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id_hidden": row["object_id_hidden"],
        "object_label": row["object_label"],
        "packet_role": row["packet_role"],
        "evidence_tier": row["evidence_tier"],
        "gt_label_match_status_hidden": row["gt_label_match_status_hidden"],
    }


def build_targets(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "multiclass": [target_record(row, MULTICLASS_TARGET, row["relation_reliability_multiclass_target"]) for row in rows],
        "primary_binary": [
            target_record(row, PRIMARY_BINARY_TARGET, row["relation_reliability_binary_target"])
            for row in rows
            if row["relation_reliability_binary_usable"]
        ],
        "connected_diagnostic": [
            target_record(row, CONNECTED_TARGET, row["connected_diagnostic_target"])
            for row in rows
            if row["connected_diagnostic_usable"]
        ],
        "geometry_support": [
            target_record(row, GEOMETRY_SUPPORT_TARGET, row["geometry_support_binary_target"])
            for row in rows
            if row["geometry_support_binary_usable"]
        ],
        "endpoint_identity": [target_record(row, ENDPOINT_TARGET, row["endpoint_identity_binary_target"]) for row in rows],
        "coverage": [target_record(row, COVERAGE_TARGET, row["coverage_binary_target"]) for row in rows],
        "uncertainty": [target_record(row, UNCERTAINTY_TARGET, row["review_uncertainty"]) for row in rows],
        "abstain": [
            {
                **target_record(row, PRIMARY_BINARY_TARGET, None),
                "review_relation_reliability": row["review_relation_reliability"],
                "review_geometry_support": row["review_geometry_support"],
                "review_uncertainty": row["review_uncertainty"],
            }
            for row in rows
            if not row["relation_reliability_binary_usable"]
        ],
    }


def entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    return -sum((count / total) * math.log(count / total, 2) for count in counter.values() if count)


def nmi(rows: list[dict[str, Any]], predictor: str, label: str) -> float:
    if not rows:
        return 0.0
    label_counts = Counter(str(row.get(label, "missing")) for row in rows)
    group_counts = Counter(str(row.get(predictor, "missing")) for row in rows)
    joint = Counter((str(row.get(predictor, "missing")), str(row.get(label, "missing"))) for row in rows)
    total = len(rows)
    mi = 0.0
    for (group, target), count in joint.items():
        pxy = count / total
        px = group_counts[group] / total
        py = label_counts[target] / total
        if pxy and px and py:
            mi += pxy * math.log(pxy / (px * py), 2)
    denom = math.sqrt(entropy(label_counts) * entropy(group_counts))
    return mi / denom if denom else 0.0


def majority_risk(rows: list[dict[str, Any]], predictor: str, label: str) -> dict[str, Any]:
    if not rows:
        return {"predictor": predictor, "label": label, "rows": 0, "risk_flag": False}
    label_counts = Counter(str(row.get(label, "missing")) for row in rows)
    baseline = max(label_counts.values()) / len(rows)
    groups: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        groups[str(row.get(predictor, "missing"))][str(row.get(label, "missing"))] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    accuracy = correct / len(rows)
    nmi_value = nmi(rows, predictor, label)
    large_pure_group = False
    top_groups: list[dict[str, Any]] = []
    for group_value, counter in groups.items():
        total = sum(counter.values())
        majority_label, majority_count = counter.most_common(1)[0]
        majority_rate = majority_count / total
        if total >= RISK_THRESHOLDS["large_group_rows"] and majority_rate >= RISK_THRESHOLDS["large_group_purity"]:
            large_pure_group = True
        top_groups.append({"group_value": group_value, "rows": total, "majority_label": majority_label, "majority_rate": majority_rate, "label_counts": dict(counter)})
    top_groups.sort(key=lambda item: (-item["rows"], str(item["group_value"])))
    risk_flag = (
        accuracy >= RISK_THRESHOLDS["majority_rule_accuracy"]
        and accuracy - baseline >= RISK_THRESHOLDS["majority_excess_over_baseline"]
    ) or nmi_value >= RISK_THRESHOLDS["normalized_mutual_information"] or large_pure_group
    return {
        "predictor": predictor,
        "label": label,
        "rows": len(rows),
        "groups": len(groups),
        "label_counts": dict(label_counts),
        "majority_rule_accuracy": accuracy,
        "majority_baseline_accuracy": baseline,
        "majority_excess_over_baseline": accuracy - baseline,
        "normalized_mutual_information": nmi_value,
        "risk_flag": risk_flag,
        "top_groups": top_groups[:12],
    }


def probe_risks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        (rows, "relation_reliability_multiclass_target"),
        ([row for row in rows if row["relation_reliability_binary_usable"]], "relation_reliability_binary_target"),
        ([row for row in rows if row["geometry_support_binary_usable"]], "geometry_support_binary_target"),
        (rows, "endpoint_identity_binary_target"),
        (rows, "coverage_binary_target"),
        (rows, "review_uncertainty"),
    ]
    out: list[dict[str, Any]] = []
    for label_rows, label in specs:
        for predictor in RISK_PREDICTORS:
            out.append(majority_risk(label_rows, predictor, label))
    return out


def gt_group(row: dict[str, Any]) -> str:
    status = row.get("gt_label_match_status_hidden")
    if status in {"exact_match", "family_match"}:
        return "GT_match"
    if status in {"pair_has_other_predicate", "no_gt_for_pair"}:
        return "No_GT_current_relation"
    return "GT_unknown"


def mismatch_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((gt_group(row), row["review_relation_reliability"]) for row in rows)
    output: list[dict[str, Any]] = []
    for gt_state in ["GT_match", "No_GT_current_relation", "GT_unknown"]:
        for reliability in ["accept_reliable", "reject_unreliable", "abstain_uncertain"]:
            output.append({"gt_group": gt_state, "review_relation_reliability": reliability, "rows": counts.get((gt_state, reliability), 0)})
    return output


def group_contrast(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(field, "missing"))].append(row)
    out: list[dict[str, Any]] = []
    for value, group_rows in grouped.items():
        rel_counts = Counter(row["review_relation_reliability"] for row in group_rows)
        primary_values = {row["relation_reliability_binary_target"] for row in group_rows if row["relation_reliability_binary_usable"]}
        out.append({
            "group_field": field,
            "group_value": value,
            "rows": len(group_rows),
            "accept": rel_counts.get("accept_reliable", 0),
            "reject": rel_counts.get("reject_unreliable", 0),
            "abstain": rel_counts.get("abstain_uncertain", 0),
            "mixed_primary_binary": len(primary_values) > 1,
        })
    out.sort(key=lambda row: (-row["rows"], str(row["group_value"])))
    return out


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    viability = summary["target_viability"]
    lines = [
        "# H002 V20 Attachment Audit Packet Label Ingestion",
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
        "## Counts",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"multiclass_rows = {counts['multiclass_rows']}",
        f"primary_binary_rows = {counts['primary_binary_rows']}",
        f"geometry_support_rows = {counts['geometry_support_rows']}",
        f"endpoint_identity_rows = {counts['endpoint_identity_rows']}",
        f"coverage_rows = {counts['coverage_rows']}",
        f"uncertainty_rows = {counts['uncertainty_rows']}",
        f"review_relation_reliability = {counts['review_relation_reliability']}",
        f"primary_binary_target = {counts['primary_binary_target']}",
        f"gt_label_match_status = {counts['gt_label_match_status']}",
        f"quick_probe_risk_flags = {counts['quick_probe_risk_flags']}",
        "```",
        "",
        "## Target Viability",
        "",
        "```text",
        f"minimum_per_class_for_posterior = {viability['minimum_per_class_for_posterior']}",
        f"reliability_positive_rows = {viability['reliability_positive_rows']}",
        f"reliability_negative_rows = {viability['reliability_negative_rows']}",
        f"class_mass_pass = {viability['class_mass_pass']}",
        f"same_scan_mixed_primary_binary_groups = {viability['same_scan_mixed_primary_binary_groups']}",
        f"same_visible_pair_mixed_primary_binary_groups = {viability['same_visible_pair_mixed_primary_binary_groups']}",
        "```",
        "",
        "Primary reliability remains positive-sparse, so posterior smoke remains blocked before target-independence audit.",
        "",
        "## Boundary",
        "",
        "The hidden materialized manifest and existing GT-match axis were joined only after label lock. They are target/audit metadata, not model input. No posterior was trained.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fill_summary = read_json(args.fill_summary)
    _, label_rows = read_tsv(args.filled_sheet)
    decision_rows = read_jsonl(args.label_decisions)
    manifest_rows = read_jsonl(args.hidden_manifest)

    errors = validate_fill_summary(fill_summary)
    errors.extend(validate_decisions(decision_rows))
    errors.extend(validate_manifest(manifest_rows))
    errors.extend(validate_ids(label_rows, decision_rows, manifest_rows))

    rows = join_rows(label_rows, manifest_rows) if not errors else []
    targets = build_targets(rows)
    risks = probe_risks(rows)
    risk_flags = [risk for risk in risks if risk.get("risk_flag")]
    scan_contrast = group_contrast(rows, "scan_id_hidden")
    pair_contrast = group_contrast(rows, "subject_object_visible_pair")
    predicate_contrast = group_contrast(rows, "predicate_label")
    tier_contrast = group_contrast(rows, "evidence_tier")
    gt_mismatch = mismatch_table(rows)

    rel_counts = Counter(row["review_relation_reliability"] for row in rows)
    primary_counts = Counter(str(row["relation_reliability_binary_target"]) for row in rows if row["relation_reliability_binary_usable"])
    geom_counts = Counter(str(row["geometry_support_binary_target"]) for row in rows if row["geometry_support_binary_usable"])
    endpoint_counts = Counter(str(row["endpoint_identity_binary_target"]) for row in rows)
    coverage_counts = Counter(str(row["coverage_binary_target"]) for row in rows)
    uncertainty_counts = Counter(row["review_uncertainty"] for row in rows)
    gt_status_counts = Counter(str(row["gt_label_match_status_hidden"]) for row in rows)
    predicate_counts = Counter(row["predicate_label"] for row in rows)
    role_counts = Counter(row["packet_role"] for row in rows)
    tier_counts = Counter(row["evidence_tier"] for row in rows)

    positive_rows = sum(1 for row in rows if row["relation_reliability_binary_usable"] and row["relation_reliability_binary_target"] == 1)
    negative_rows = sum(1 for row in rows if row["relation_reliability_binary_usable"] and row["relation_reliability_binary_target"] == 0)
    class_mass_pass = positive_rows >= MIN_CLASS_MASS_FOR_POSTERIOR and negative_rows >= MIN_CLASS_MASS_FOR_POSTERIOR

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "ingested_rows": output_dir / "ingested_rows.jsonl",
        "multiclass_target": output_dir / "multiclass_target.jsonl",
        "primary_binary_target": output_dir / "primary_binary_target.jsonl",
        "connected_diagnostic_target": output_dir / "connected_diagnostic_target.jsonl",
        "geometry_support_target": output_dir / "geometry_support_target.jsonl",
        "endpoint_identity_target": output_dir / "endpoint_identity_target.jsonl",
        "coverage_target": output_dir / "coverage_target.jsonl",
        "uncertainty_target": output_dir / "uncertainty_target.jsonl",
        "abstain_rows": output_dir / "abstain_rows.jsonl",
        "quick_probe_risks": output_dir / "quick_probe_risks.json",
        "gt_reliability_mismatch_table": output_dir / "gt_reliability_mismatch_table.csv",
        "scan_contrast_summary": output_dir / "scan_contrast_summary.csv",
        "visible_pair_contrast_summary": output_dir / "visible_pair_contrast_summary.csv",
        "predicate_contrast_summary": output_dir / "predicate_contrast_summary.csv",
        "tier_contrast_summary": output_dir / "tier_contrast_summary.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    if errors:
        status = STATUS_ERROR
    elif not class_mass_pass and risk_flags:
        status = STATUS_POSITIVE_SPARSE_WITH_RISK
    elif not class_mass_pass:
        status = STATUS_POSITIVE_SPARSE
    elif risk_flags:
        status = STATUS_WITH_RISK
    else:
        status = STATUS_READY_FOR_AUDIT

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "fill_summary": rel_path(args.fill_summary),
            "filled_sheet": rel_path(args.filled_sheet),
            "label_decisions": rel_path(args.label_decisions),
            "hidden_manifest": rel_path(args.hidden_manifest),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "multiclass_rows": len(targets["multiclass"]),
            "primary_binary_rows": len(targets["primary_binary"]),
            "connected_diagnostic_rows": len(targets["connected_diagnostic"]),
            "geometry_support_rows": len(targets["geometry_support"]),
            "endpoint_identity_rows": len(targets["endpoint_identity"]),
            "coverage_rows": len(targets["coverage"]),
            "uncertainty_rows": len(targets["uncertainty"]),
            "abstain_rows": len(targets["abstain"]),
            "review_relation_reliability": dict(sorted(rel_counts.items())),
            "primary_binary_target": dict(sorted(primary_counts.items())),
            "geometry_support_target": dict(sorted(geom_counts.items())),
            "endpoint_identity_target": dict(sorted(endpoint_counts.items())),
            "coverage_target": dict(sorted(coverage_counts.items())),
            "review_uncertainty": dict(sorted(uncertainty_counts.items())),
            "gt_label_match_status": dict(sorted(gt_status_counts.items())),
            "predicate_label": dict(sorted(predicate_counts.items())),
            "packet_role": dict(sorted(role_counts.items())),
            "evidence_tier": dict(sorted(tier_counts.items())),
            "scan_groups": len(scan_contrast),
            "visible_pair_groups": len(pair_contrast),
            "predicate_groups": len(predicate_contrast),
            "evidence_tier_groups": len(tier_contrast),
            "quick_probe_risk_flags": len(risk_flags),
        },
        "target_viability": {
            "minimum_per_class_for_posterior": MIN_CLASS_MASS_FOR_POSTERIOR,
            "reliability_positive_rows": positive_rows,
            "reliability_negative_rows": negative_rows,
            "class_mass_pass": class_mass_pass,
            "same_scan_mixed_primary_binary_groups": sum(1 for row in scan_contrast if row["mixed_primary_binary"]),
            "same_visible_pair_mixed_primary_binary_groups": sum(1 for row in pair_contrast if row["mixed_primary_binary"]),
            "same_predicate_mixed_primary_binary_groups": sum(1 for row in predicate_contrast if row["mixed_primary_binary"]),
            "same_evidence_tier_mixed_primary_binary_groups": sum(1 for row in tier_contrast if row["mixed_primary_binary"]),
            "posterior_smoke_allowed_after_ingestion": False,
        },
        "quick_probe": {
            "risk_thresholds": RISK_THRESHOLDS,
            "risk_flags": [
                {
                    "predictor": risk["predictor"],
                    "label": risk["label"],
                    "rows": risk["rows"],
                    "majority_rule_accuracy": risk.get("majority_rule_accuracy"),
                    "majority_baseline_accuracy": risk.get("majority_baseline_accuracy"),
                    "majority_excess_over_baseline": risk.get("majority_excess_over_baseline"),
                    "normalized_mutual_information": risk.get("normalized_mutual_information"),
                }
                for risk in risk_flags
            ],
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": True,
            "reads_hidden_manifest_after_label_lock": True,
            "hidden_manifest_used_for_label_fill": False,
            "existing_gt_match_axis_used_for_label_fill": False,
            "existing_gt_match_axis_joined_after_label_lock": True,
            "hidden_fields_as_model_input": False,
            "uses_source_score_or_rank": False,
            "uses_geometry_status_or_rank_hint": False,
            "uses_p_geom_valid": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "connected_primary_binary_target": False,
        },
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO,
    }

    write_jsonl(output_paths["ingested_rows"], rows)
    write_jsonl(output_paths["multiclass_target"], targets["multiclass"])
    write_jsonl(output_paths["primary_binary_target"], targets["primary_binary"])
    write_jsonl(output_paths["connected_diagnostic_target"], targets["connected_diagnostic"])
    write_jsonl(output_paths["geometry_support_target"], targets["geometry_support"])
    write_jsonl(output_paths["endpoint_identity_target"], targets["endpoint_identity"])
    write_jsonl(output_paths["coverage_target"], targets["coverage"])
    write_jsonl(output_paths["uncertainty_target"], targets["uncertainty"])
    write_jsonl(output_paths["abstain_rows"], targets["abstain"])
    write_json(output_paths["quick_probe_risks"], {"risk_thresholds": RISK_THRESHOLDS, "risks": risks})
    write_csv(output_paths["gt_reliability_mismatch_table"], gt_mismatch)
    write_csv(output_paths["scan_contrast_summary"], scan_contrast)
    write_csv(output_paths["visible_pair_contrast_summary"], pair_contrast)
    write_csv(output_paths["predicate_contrast_summary"], predicate_contrast)
    write_csv(output_paths["tier_contrast_summary"], tier_contrast)
    write_jsonl(output_paths["validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"primary_binary_rows={summary['counts']['primary_binary_rows']}")
    print(f"primary_binary_target={summary['counts']['primary_binary_target']}")
    print(f"gt_label_match_status={summary['counts']['gt_label_match_status']}")
    print(f"quick_probe_risk_flags={summary['counts']['quick_probe_risk_flags']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
