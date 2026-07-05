#!/usr/bin/env python3
"""Ingest R7 attachment-observability visible labels into target artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
ARTIFACT_ROOT = H2_ROOT / "artifacts"

DEFAULT_FILL_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill"
)
DEFAULT_PACKET_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization"
)
DEFAULT_OUTPUT_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion"
)

EXPECTED_FILL_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill_completed"
)
EXPECTED_FILL_NEXT = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion"
)
EXPECTED_PACKET_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_ready_for_label_fill"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion_v1"
)
TARGET_SCHEMA_VERSION = (
    "h002_attachment_observability_class_pair_repair_targets_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingested_ready_for_schema_shortcut_audit"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion_errors"
)
NEXT_TODO = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit"
)

TARGET_ROWS = 480
MIN_BINARY_CLASS = 60
RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 8,
    "large_group_purity": 0.90,
}

PREDICTOR_FIELDS = [
    "predicate_label",
    "subject_label",
    "object_label",
    "subject_object_class_pair",
    "predicate_subject_object_class_pair",
    "review_evidence_quality",
    "review_endpoint_identity",
    "decision_reason",
    "evidence_tier",
    "packet_status",
    "image_count_bucket",
    "candidate_id_hidden",
    "scan_id_hidden",
    "exact_class_pair_id_hidden",
    "hidden_proxy_role",
    "geometry_bucket_hidden",
    "coverage_proxy_hidden",
    "gt_label_match_status_hidden",
    "rank_band_hidden",
]

VISIBLE_MODEL_SAFE_CANDIDATES = {
    "subject_label",
    "predicate_label",
    "object_label",
    "subject_object_class_pair",
    "packet_status",
    "evidence_tier",
    "subject_image_count",
    "object_image_count",
    "pair_shared_view_count",
    "pair_shared_frame_count",
    "mesh_ready",
    "sequence_ready",
}

BLOCKED_MODEL_INPUTS = {
    "review_observability_label",
    "review_relation_label",
    "review_evidence_quality",
    "review_endpoint_identity",
    "review_notes",
    "decision_reason",
    "reviewer_id",
    "review_round",
    "label_policy",
    "packet_asset_count",
    "review_row_id",
    "candidate_id_hidden",
    "scan_id_hidden",
    "subgraph_id_hidden",
    "subject_id_hidden",
    "object_id_hidden",
    "directed_pair_id_hidden",
    "prediction_id_hidden",
    "exact_class_pair_id_hidden",
    "hidden_proxy_role",
    "geometry_bucket_hidden",
    "coverage_proxy_hidden",
    "uncertainty_bucket_hidden",
    "gt_label_match_status_hidden",
    "rank_band_hidden",
    "cell_id_hidden",
    "asset_paths_hidden",
    "packet_dir_hidden",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fill-dir", type=Path, default=DEFAULT_FILL_DIR)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fields.append(key)
                    seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def image_count_bucket(subject_count: Any, object_count: Any) -> str:
    total = as_int(subject_count) + as_int(object_count)
    if total >= 12:
        return "images_ge_12"
    if total >= 8:
        return "images_8_11"
    if total >= 4:
        return "images_4_7"
    if total > 0:
        return "images_1_3"
    return "images_0"


def validate_inputs(
    fill_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    filled_rows: list[dict[str, str]],
    decision_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if fill_summary.get("status") != EXPECTED_FILL_STATUS:
        errors.append({"error_type": "unexpected_fill_status", "actual": fill_summary.get("status")})
    if fill_summary.get("next_todo") != EXPECTED_FILL_NEXT:
        errors.append({"error_type": "unexpected_fill_next", "actual": fill_summary.get("next_todo")})
    if fill_summary.get("validation_errors") != 0:
        errors.append({"error_type": "fill_validation_errors_present", "actual": fill_summary.get("validation_errors")})
    if packet_summary.get("status") != EXPECTED_PACKET_STATUS:
        errors.append({"error_type": "unexpected_packet_status", "actual": packet_summary.get("status")})
    if packet_summary.get("validation_errors") != 0:
        errors.append({"error_type": "packet_validation_errors_present", "actual": packet_summary.get("validation_errors")})
    for name, rows in [
        ("filled_rows", filled_rows),
        ("decision_rows", decision_rows),
        ("hidden_rows", hidden_rows),
    ]:
        if len(rows) != TARGET_ROWS:
            errors.append({"error_type": f"{name}_count_mismatch", "actual": len(rows), "expected": TARGET_ROWS})
    filled_ids = {row.get("review_row_id") for row in filled_rows}
    decision_ids = {row.get("review_row_id") for row in decision_rows}
    hidden_ids = {row.get("review_row_id") for row in hidden_rows}
    if filled_ids != decision_ids or filled_ids != hidden_ids:
        errors.append({"error_type": "review_row_id_set_mismatch"})
    fill_boundary = fill_summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "ingests_labels",
        "materializes_model_rows",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
        "used_non_visible_metadata",
        "used_existing_target",
        "multi_view_or_mesh_as_model_input",
    ]
    for key in expected_false:
        if fill_boundary.get(key) is not False:
            errors.append({"error_type": "fill_boundary_not_false", "key": key, "actual": fill_boundary.get(key)})
    if fill_boundary.get("fills_labels") is not True:
        errors.append({"error_type": "fill_labels_boundary_not_true", "actual": fill_boundary.get("fills_labels")})
    return errors


def target_from_labels(filled: dict[str, Any], hidden: dict[str, Any]) -> dict[str, Any]:
    obs_label = filled["review_observability_label"]
    rel_label = filled["review_relation_label"]
    quality = filled["review_evidence_quality"]
    endpoint = filled["review_endpoint_identity"]
    p_obs_target = 1 if obs_label == "observable" else 0
    p_rel_target = {"accept": 1, "reject": 0}.get(rel_label)
    p_rel_usable = obs_label == "observable" and p_rel_target is not None
    quality_ordinal = {"poor": 0, "partial": 1, "sufficient": 2}.get(quality)
    endpoint_binary = {"ambiguous": 0, "wrong_endpoint": 0, "clear": 1}.get(endpoint)
    subject = filled["subject_label"]
    obj = filled["object_label"]
    predicate = filled["predicate_label"]
    return {
        "schema_version": TARGET_SCHEMA_VERSION,
        "review_row_id": filled["review_row_id"],
        "candidate_relation": filled["candidate_relation"],
        "subject_label": subject,
        "predicate_label": predicate,
        "object_label": obj,
        "subject_object_class_pair": f"{subject}->{obj}",
        "predicate_subject_object_class_pair": f"{predicate}::{subject}->{obj}",
        "packet_status": filled["packet_status"],
        "evidence_tier": filled["evidence_tier"],
        "subject_image_count": as_int(filled["subject_image_count"]),
        "object_image_count": as_int(filled["object_image_count"]),
        "pair_shared_view_count": as_int(filled["pair_shared_view_count"]),
        "pair_shared_frame_count": as_int(filled["pair_shared_frame_count"]),
        "image_count_bucket": image_count_bucket(filled["subject_image_count"], filled["object_image_count"]),
        "mesh_ready": filled["mesh_ready"],
        "sequence_ready": filled["sequence_ready"],
        "review_observability_label": obs_label,
        "review_relation_label": rel_label,
        "review_evidence_quality": quality,
        "review_endpoint_identity": endpoint,
        "decision_reason": filled["decision_reason"],
        "label_provenance": filled["reviewer_id"],
        "label_policy": filled["label_policy"],
        "user_requested_codex_fill": True,
        "p_obs_target": p_obs_target,
        "p_obs_usable": True,
        "p_rel_observable_target": p_rel_target,
        "p_rel_observable_usable": p_rel_usable,
        "relation_multiclass_target": rel_label,
        "observability_multiclass_target": obs_label,
        "evidence_quality_target": quality,
        "evidence_quality_ordinal": quality_ordinal,
        "endpoint_identity_binary": endpoint_binary,
        "hidden_join_after_label_lock": True,
        "hidden_fields_used_for_label_fill": False,
        "source_score_or_rank_used_for_label_fill": False,
        "existing_target_used_for_label_fill": False,
        "candidate_id_hidden": hidden.get("candidate_id"),
        "scan_id_hidden": hidden.get("scan_id"),
        "subgraph_id_hidden": hidden.get("subgraph_id"),
        "subject_id_hidden": hidden.get("subject_id"),
        "object_id_hidden": hidden.get("object_id"),
        "directed_pair_id_hidden": hidden.get("directed_pair_id"),
        "prediction_id_hidden": hidden.get("prediction_id"),
        "exact_class_pair_id_hidden": hidden.get("exact_class_pair_id"),
        "hidden_proxy_role": hidden.get("hidden_proxy_role"),
        "geometry_bucket_hidden": hidden.get("geometry_bucket"),
        "coverage_proxy_hidden": hidden.get("coverage_proxy"),
        "uncertainty_bucket_hidden": hidden.get("uncertainty_bucket"),
        "gt_label_match_status_hidden": hidden.get("gt_label_match_status"),
        "rank_band_hidden": hidden.get("rank_band"),
        "cell_id_hidden": hidden.get("cell_id_hidden"),
        "packet_dir_hidden": hidden.get("packet_dir_hidden"),
    }


def entropy(counts: Counter[Any]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    out = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            out -= p * math.log2(p)
    return out


def normalized_mutual_information(rows: list[dict[str, Any]], predictor: str, target: str) -> float:
    x_counts = Counter(str(row.get(predictor)) for row in rows)
    y_counts = Counter(str(row.get(target)) for row in rows)
    joint = Counter((str(row.get(predictor)), str(row.get(target))) for row in rows)
    n = len(rows)
    if n == 0:
        return 0.0
    mi = 0.0
    for (x, y), count in joint.items():
        pxy = count / n
        px = x_counts[x] / n
        py = y_counts[y] / n
        if pxy > 0 and px > 0 and py > 0:
            mi += pxy * math.log2(pxy / (px * py))
    hx = entropy(x_counts)
    hy = entropy(y_counts)
    if hx <= 0 or hy <= 0:
        return 0.0
    return mi / math.sqrt(hx * hy)


def majority_rule_accuracy(rows: list[dict[str, Any]], predictor: str, target: str) -> dict[str, Any]:
    valid = [row for row in rows if row.get(target) is not None]
    if not valid:
        return {
            "predictor": predictor,
            "target": target,
            "rows": 0,
            "accuracy": 0.0,
            "baseline": 0.0,
            "excess": 0.0,
            "nmi": 0.0,
            "max_group_rows": 0,
            "max_group_purity": 0.0,
            "risk_flag": False,
        }
    global_counts = Counter(str(row.get(target)) for row in valid)
    baseline = max(global_counts.values()) / len(valid)
    by_group: dict[str, Counter[str]] = defaultdict(Counter)
    for row in valid:
        by_group[str(row.get(predictor))][str(row.get(target))] += 1
    correct = sum(max(counter.values()) for counter in by_group.values())
    accuracy = correct / len(valid)
    max_group_rows = 0
    max_group_purity = 0.0
    for counter in by_group.values():
        rows_n = sum(counter.values())
        purity = max(counter.values()) / rows_n
        if rows_n > max_group_rows or (rows_n == max_group_rows and purity > max_group_purity):
            max_group_rows = rows_n
            max_group_purity = purity
    nmi = normalized_mutual_information(valid, predictor, target)
    risk_flag = (
        accuracy >= RISK_THRESHOLDS["majority_rule_accuracy"]
        and accuracy - baseline >= RISK_THRESHOLDS["majority_excess_over_baseline"]
    ) or nmi >= RISK_THRESHOLDS["normalized_mutual_information"] or (
        max_group_rows >= RISK_THRESHOLDS["large_group_rows"]
        and max_group_purity >= RISK_THRESHOLDS["large_group_purity"]
        and accuracy - baseline >= 0.05
    )
    return {
        "predictor": predictor,
        "target": target,
        "rows": len(valid),
        "accuracy": accuracy,
        "baseline": baseline,
        "excess": accuracy - baseline,
        "nmi": nmi,
        "max_group_rows": max_group_rows,
        "max_group_purity": max_group_purity,
        "risk_flag": risk_flag,
    }


def target_count_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes = [
        "relation_multiclass_target",
        "observability_multiclass_target",
        "p_obs_target",
        "p_rel_observable_target",
        "p_rel_observable_usable",
        "predicate_label",
        "predicate_label::relation_multiclass_target",
        "predicate_label::p_rel_observable_target",
        "review_evidence_quality",
        "review_endpoint_identity",
        "decision_reason",
        "hidden_proxy_role",
        "geometry_bucket_hidden",
        "gt_label_match_status_hidden",
    ]
    out: list[dict[str, Any]] = []
    for axis in axes:
        if "::" in axis:
            left, right = axis.split("::", 1)
            counts = Counter(f"{row.get(left)}|{row.get(right)}" for row in rows)
        else:
            counts = Counter(str(row.get(axis)) for row in rows)
        total = sum(counts.values()) or 1
        for value, count in counts.most_common():
            out.append({"axis": axis, "value": value, "count": count, "share": count / total})
    return out


def target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    p_rel_rows = [row for row in rows if row["p_rel_observable_usable"]]
    p_obs_counts = Counter(row["p_obs_target"] for row in rows)
    p_rel_counts = Counter(row["p_rel_observable_target"] for row in p_rel_rows)
    predicate_rel: dict[str, dict[str, int]] = {}
    for predicate in sorted({row["predicate_label"] for row in rows}):
        subset = [row for row in rows if row["predicate_label"] == predicate]
        p_rel_subset = [row for row in subset if row["p_rel_observable_usable"]]
        predicate_rel[predicate] = {
            "rows": len(subset),
            "p_obs_positive": sum(1 for row in subset if row["p_obs_target"] == 1),
            "p_obs_negative": sum(1 for row in subset if row["p_obs_target"] == 0),
            "p_rel_rows": len(p_rel_subset),
            "p_rel_accept": sum(1 for row in p_rel_subset if row["p_rel_observable_target"] == 1),
            "p_rel_reject": sum(1 for row in p_rel_subset if row["p_rel_observable_target"] == 0),
            "abstain": sum(1 for row in subset if row["relation_multiclass_target"] == "abstain"),
        }
    return {
        "rows": len(rows),
        "multiclass_relation": dict(Counter(row["relation_multiclass_target"] for row in rows)),
        "observability": dict(Counter(row["observability_multiclass_target"] for row in rows)),
        "p_obs_target": dict(p_obs_counts),
        "p_rel_observable_rows": len(p_rel_rows),
        "p_rel_observable_target": dict(p_rel_counts),
        "p_obs_min_class": min(p_obs_counts.values()) if p_obs_counts else 0,
        "p_rel_observable_min_class": min(p_rel_counts.values()) if p_rel_counts else 0,
        "predicate_summary": predicate_rel,
    }


def target_viability_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "target": "relation_multiclass_accept_reject_abstain",
            "rows": summary["rows"],
            "class_counts": json.dumps(summary["multiclass_relation"], sort_keys=True),
            "min_binary_class": "",
            "viability": "diagnostic_ready_needs_shortcut_audit",
            "note": "multiclass target has all three labels but includes abstain",
        },
        {
            "target": "p_obs_observable_binary",
            "rows": summary["rows"],
            "class_counts": json.dumps(summary["p_obs_target"], sort_keys=True),
            "min_binary_class": summary["p_obs_min_class"],
            "viability": (
                "sparse_negative_diagnostic_only"
                if summary["p_obs_min_class"] < MIN_BINARY_CLASS
                else "ready_needs_shortcut_audit"
            ),
            "note": "observability negatives are sparse because all packets were materialized from T1-ready rows",
        },
        {
            "target": "p_rel_observable_accept_reject",
            "rows": summary["p_rel_observable_rows"],
            "class_counts": json.dumps(summary["p_rel_observable_target"], sort_keys=True),
            "min_binary_class": summary["p_rel_observable_min_class"],
            "viability": (
                "ready_needs_shortcut_audit"
                if summary["p_rel_observable_min_class"] >= MIN_BINARY_CLASS
                else "class_sparse_diagnostic_only"
            ),
            "note": "binary relation target among observable non-abstain rows",
        },
    ]
    for predicate, pred_summary in summary["predicate_summary"].items():
        min_class = min(pred_summary["p_rel_accept"], pred_summary["p_rel_reject"])
        rows.append(
            {
                "target": f"p_rel_observable_{predicate}",
                "rows": pred_summary["p_rel_rows"],
                "class_counts": json.dumps(
                    {"accept": pred_summary["p_rel_accept"], "reject": pred_summary["p_rel_reject"]},
                    sort_keys=True,
                ),
                "min_binary_class": min_class,
                "viability": (
                    "ready_needs_shortcut_audit"
                    if min_class >= MIN_BINARY_CLASS
                    else "class_sparse_or_single_class_diagnostic_only"
                ),
                "note": "predicate-specific observable relation target",
            }
        )
    return rows


def shortcut_preview(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets = ["relation_multiclass_target", "p_obs_target", "p_rel_observable_target"]
    out: list[dict[str, Any]] = []
    for target in targets:
        for predictor in PREDICTOR_FIELDS:
            out.append(majority_rule_accuracy(rows, predictor, target))
    return out


def risk_register(viability: list[dict[str, Any]], shortcut_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in viability:
        if "diagnostic" in row["viability"]:
            rows.append(
                {
                    "risk": f"{row['target']}_not_primary_ready",
                    "severity": "high",
                    "evidence": row["class_counts"],
                    "action": "do not run learned smoke for this target unless repaired or used only as diagnostic",
                }
            )
    for row in shortcut_rows:
        if row["risk_flag"]:
            rows.append(
                {
                    "risk": f"shortcut_{row['target']}_by_{row['predictor']}",
                    "severity": "high" if row["predictor"].endswith("_hidden") or "hidden" in row["predictor"] else "medium",
                    "evidence": (
                        f"acc={row['accuracy']:.3f}, baseline={row['baseline']:.3f}, "
                        f"nmi={row['nmi']:.3f}, max_group={row['max_group_rows']}/{row['max_group_purity']:.3f}"
                    ),
                    "action": "schema/shortcut audit must control or block this predictor before learned smoke",
                }
            )
    rows.append(
        {
            "risk": "attached_to_single_class_observable_relation",
            "severity": "high",
            "evidence": "attached to has accept 172 / reject 0 among observable non-abstain labels",
            "action": "do not use attached-to-only p_rel binary target as a learned claim without repair",
        }
    )
    return rows


def model_input_boundary() -> dict[str, Any]:
    return {
        "schema_version": "h002_attachment_observability_class_pair_repair_model_input_boundary_v1",
        "allowed_model_safe_candidates_after_audit": sorted(VISIBLE_MODEL_SAFE_CANDIDATES),
        "blocked_model_inputs": sorted(BLOCKED_MODEL_INPUTS),
        "strict_rule": (
            "Targets, review decisions, hidden source/proxy/GT/construction fields, ids, and packet paths "
            "must not enter model-safe views. C_e must not use Z_e source confidence."
        ),
        "next_gate": "schema_shortcut_audit_before_any_learned_smoke",
    }


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R7 Attachment Observability Class-Pair Repair Label Ingestion",
            "",
            "## Result",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Target Summary",
            "",
            "```json",
            json.dumps(summary["target_summary"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Decision",
            "",
            "The combined observable relation target has enough accept/reject mass for a schema audit, but learned smoke is still blocked. `p_obs` is negative-sparse and `attached to` is single-class for observable p_rel, so the next step must run schema/shortcut audit and decide whether to use only the combined target, only `hanging on`, or repair `attached to` negatives.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    fill_summary = read_json(args.fill_dir / "summary.json")
    packet_summary = read_json(args.packet_dir / "summary.json")
    filled_rows = read_csv(args.fill_dir / "filled_visible_review_sheet.csv")
    decision_rows = read_jsonl(args.fill_dir / "label_decisions.jsonl")
    hidden_rows = read_jsonl(args.packet_dir / "materialized_hidden_manifest.jsonl")
    validation_errors = validate_inputs(fill_summary, packet_summary, filled_rows, decision_rows, hidden_rows)

    hidden_by_id = {row["review_row_id"]: row for row in hidden_rows}
    target_rows = [target_from_labels(row, hidden_by_id[row["review_row_id"]]) for row in filled_rows]
    t_summary = target_summary(target_rows)
    viability = target_viability_rows(t_summary)
    shortcut_rows = shortcut_preview(target_rows)
    risks = risk_register(viability, shortcut_rows)

    status = STATUS_ERROR if validation_errors else STATUS_READY
    selected_path = (
        "label_ingestion_errors"
        if validation_errors
        else "ingest_visible_packet_labels_run_schema_shortcut_audit_next"
    )
    next_todo = (
        "repair_attachment_observability_class_pair_repair_label_ingestion"
        if validation_errors
        else NEXT_TODO
    )

    output_paths = {
        "ingested_target_rows": output_dir / "ingested_target_rows.jsonl",
        "observable_relation_binary_rows": output_dir / "observable_relation_binary_rows.jsonl",
        "observability_binary_rows": output_dir / "observability_binary_rows.jsonl",
        "multiclass_rows": output_dir / "multiclass_rows.jsonl",
        "target_count_audit": output_dir / "target_count_audit.csv",
        "target_viability": output_dir / "target_viability.csv",
        "shortcut_preview": output_dir / "shortcut_preview.csv",
        "risk_register": output_dir / "risk_register.csv",
        "model_input_boundary": output_dir / "model_input_boundary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
    }

    observable_relation_rows = [row for row in target_rows if row["p_rel_observable_usable"]]
    observability_rows = [row for row in target_rows if row["p_obs_usable"]]
    multiclass_rows = list(target_rows)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "fill_status": fill_summary.get("status"),
        "packet_status": packet_summary.get("status"),
        "target_summary": t_summary,
        "target_viability_summary": {
            row["target"]: row["viability"] for row in viability
        },
        "shortcut_risk_flags": sum(1 for row in shortcut_rows if row["risk_flag"]),
        "risk_register_rows": len(risks),
        "boundary": {
            "split": "train_only_label_ingestion",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "fills_labels": False,
            "ingests_labels": True,
            "materializes_model_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "hidden_join_after_label_lock": True,
            "hidden_fields_used_for_label_fill": False,
            "source_score_or_rank_used_for_label_fill": False,
            "existing_target_used_for_label_fill": False,
            "multi_view_or_mesh_as_audit_evidence": True,
            "multi_view_or_mesh_as_model_input": False,
            "learned_smoke_allowed": False,
        },
        "input_paths": {
            "fill_summary": rel_path(args.fill_dir / "summary.json"),
            "filled_visible_review_sheet": rel_path(args.fill_dir / "filled_visible_review_sheet.csv"),
            "packet_summary": rel_path(args.packet_dir / "summary.json"),
            "materialized_hidden_manifest": rel_path(args.packet_dir / "materialized_hidden_manifest.jsonl"),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_jsonl(output_paths["ingested_target_rows"], target_rows)
    write_jsonl(output_paths["observable_relation_binary_rows"], observable_relation_rows)
    write_jsonl(output_paths["observability_binary_rows"], observability_rows)
    write_jsonl(output_paths["multiclass_rows"], multiclass_rows)
    write_csv(output_paths["target_count_audit"], target_count_rows(target_rows))
    write_csv(output_paths["target_viability"], viability)
    write_csv(output_paths["shortcut_preview"], shortcut_rows)
    write_csv(output_paths["risk_register"], risks)
    write_json(output_paths["model_input_boundary"], model_input_boundary())
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
