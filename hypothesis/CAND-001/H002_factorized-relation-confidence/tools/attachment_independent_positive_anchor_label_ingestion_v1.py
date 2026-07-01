#!/usr/bin/env python3
"""Ingest H002 positive-anchor packet labels after visible-packet label lock."""

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

FILL_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_label_fill_v1"
PACKET_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_packet_materialization_v1"
OUT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_label_ingestion_v1"

FILL_SUMMARY = FILL_DIR / "summary.json"
FILLED_SHEET = FILL_DIR / "filled_visible_review_sheet.csv"
LABEL_DECISIONS = FILL_DIR / "label_decisions.jsonl"
HIDDEN_MANIFEST = PACKET_DIR / "materialized_hidden_manifest.jsonl"

SCHEMA_VERSION = "h002_attachment_independent_positive_anchor_label_ingestion_v1"
TARGET_SCHEMA_VERSION = "h002_attachment_positive_anchor_target_v1"
EXPECTED_FILL_STATUS = "h002_attachment_independent_positive_anchor_label_fill_v1_completed"
EXPECTED_FILL_NEXT = "attachment_independent_positive_anchor_label_ingestion_v1"
LABEL_SOURCE = "codex_visible_packet_proxy_labeler_v1_user_requested"

STATUS_READY = "h002_attachment_independent_positive_anchor_label_ingested_ready_for_target_independence_audit"
STATUS_SHORTCUT_RISK = "h002_attachment_independent_positive_anchor_label_ingested_class_mass_pass_with_shortcut_risk"
STATUS_POSITIVE_SPARSE = "h002_attachment_independent_positive_anchor_label_ingested_positive_sparse"
STATUS_POSITIVE_SPARSE_WITH_SHORTCUT_RISK = (
    "h002_attachment_independent_positive_anchor_label_ingested_positive_sparse_with_shortcut_risk"
)
STATUS_ERROR = "h002_attachment_independent_positive_anchor_label_ingestion_errors"
NEXT_TODO = "attachment_independent_positive_anchor_target_independence_audit_v1"

PRIMARY_PREDICATES = {"attached to", "hanging on"}
CONNECTED_PREDICATE = "connected to"

RELIABILITY_BINARY = {"accept_reliable": 1, "reject_unreliable": 0}
GEOMETRY_BINARY = {"supported": 1, "unsupported": 0}
COVERAGE_ORDINAL = {"insufficient": 0, "limited": 1, "sufficient": 2}
ENDPOINT_BINARY = {"clear_endpoint_identity": 1, "uncertain_endpoint_identity": 0}

MIN_POSITIVE_FOR_POSTERIOR_SMOKE = 60
MIN_NEGATIVE_FOR_POSTERIOR_SMOKE = 60

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 10,
    "large_group_purity": 0.90,
}

RISK_PREDICTORS = [
    "predicate_label",
    "subject_label",
    "object_label",
    "subject_object_visible_pair",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "decision_reason",
    "query_id_hidden",
    "cell_id_hidden",
    "selection_proxy_role_hidden",
    "anchor_bucket_hidden",
    "rank_band_hidden",
    "semantic_rank_band_hidden",
    "semantic_score_availability_hidden",
    "label_match_status_hidden",
    "selection_route_hidden",
    "capacity_evidence_tier_hidden",
    "provisional_status_hidden",
    "source_artifact_key_hidden",
    "mixed_endpoint_family_rank_coverage_key_hidden",
    "same_scene_family_rank_key_hidden",
    "scan_id_hidden",
    "subgraph_id_hidden",
    "visible_pair_key_hidden",
]

CONSTRUCTION_PROXY_PREDICTORS = {
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
}

VISIBLE_OR_ID_PREDICTORS = {
    "predicate_label",
    "subject_label",
    "object_label",
    "subject_object_visible_pair",
    "scan_id_hidden",
    "subgraph_id_hidden",
    "label_match_status_hidden",
}

LABEL_DERIVED_PREDICTORS = {
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "decision_reason",
}

TABLE_FIELDS = [
    "group_field",
    "group_value",
    "rows",
    "accept_reliable",
    "reject_unreliable",
    "abstain_uncertain",
    "primary_accept",
    "primary_reject",
    "primary_binary_mixed",
    "p_obs_positive",
    "p_obs_negative",
]


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
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
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


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def visible_pair(row: dict[str, Any]) -> str:
    return f"{norm(row.get('subject_label'))}|{norm(row.get('object_label'))}"


def semantic_rank_band(rank: Any) -> str:
    if not isinstance(rank, (int, float)):
        return "rank_missing"
    if rank <= 50:
        return "rank_1_50"
    if rank <= 100:
        return "rank_51_100"
    if rank <= 200:
        return "rank_101_200"
    if rank <= 500:
        return "rank_201_500"
    if rank <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def source_artifact_key(row: dict[str, Any]) -> str:
    artifacts = row.get("source_artifacts_hidden")
    if not artifacts:
        return "missing"
    return "+".join(str(item) for item in artifacts)


def validate_fill_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_FILL_STATUS:
        errors.append({"error_type": "unexpected_fill_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_FILL_NEXT:
        errors.append({"error_type": "unexpected_fill_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "fill_validation_errors_present", "actual": summary.get("validation_errors")})
    counts = summary.get("counts", {})
    if counts.get("rows") != 560:
        errors.append({"error_type": "unexpected_fill_row_count", "actual": counts.get("rows")})
    if counts.get("primary_positive_rows", 0) < MIN_POSITIVE_FOR_POSTERIOR_SMOKE:
        errors.append(
            {
                "error_type": "fill_primary_positive_below_gate",
                "actual": counts.get("primary_positive_rows"),
                "expected_min": MIN_POSITIVE_FOR_POSTERIOR_SMOKE,
            }
        )
    boundary = summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "hidden_manifest_read",
        "used_existing_gt_match_axis",
        "used_p_geom_valid",
        "used_proxy_role_or_cell_id",
        "used_scan_id",
        "used_source_path",
        "used_source_score_or_rank",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def validate_ids(
    label_rows: list[dict[str, str]],
    decision_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    groups = {
        "filled_sheet": [row.get("candidate_id", "") for row in label_rows],
        "label_decisions": [row.get("candidate_id", "") for row in decision_rows],
        "hidden_manifest": [row.get("candidate_id", "") for row in manifest_rows],
    }
    id_sets = {name: {candidate_id for candidate_id in ids if candidate_id} for name, ids in groups.items()}
    for name, ids in groups.items():
        if len(ids) != 560:
            errors.append({"error_type": f"unexpected_{name}_row_count", "expected": 560, "actual": len(ids)})
        for candidate_id, count in Counter(ids).items():
            if candidate_id and count > 1:
                errors.append({"error_type": f"duplicate_{name}_candidate_id", "candidate_id": candidate_id, "count": count})
    for source, target in [
        ("filled_sheet", "label_decisions"),
        ("filled_sheet", "hidden_manifest"),
        ("label_decisions", "filled_sheet"),
        ("hidden_manifest", "filled_sheet"),
    ]:
        for candidate_id in sorted(id_sets[source] - id_sets[target]):
            errors.append({"error_type": f"{source}_candidate_missing_from_{target}", "candidate_id": candidate_id})
    return errors


def validate_decisions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        candidate_id = row.get("candidate_id")
        provenance = row.get("provenance") or {}
        if provenance.get("filled_by") != "codex_visible_packet_proxy_labeler":
            errors.append({"error_type": "unexpected_label_source", "row": idx, "candidate_id": candidate_id})
        expected_false = [
            "used_existing_gt_match_axis",
            "used_hidden_manifest",
            "used_mesh_as_model_input",
            "used_multi_view_as_model_input",
            "used_p_geom_valid",
            "used_proxy_role_or_cell_id",
            "used_scan_id",
            "used_source_path",
            "used_source_score_or_rank",
            "used_validation_or_test",
            "paper_evidence_allowed",
        ]
        for key in expected_false:
            if provenance.get(key) is not False:
                errors.append({"error_type": "decision_boundary_violation", "row": idx, "candidate_id": candidate_id, "key": key})
    return errors


def validate_manifest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = [
        "candidate_id",
        "packet_request_id",
        "scan_id",
        "subgraph_id",
        "subject_id",
        "object_id",
        "prediction_id",
        "query_id",
        "cell_id_hidden",
        "selection_proxy_role_hidden",
        "rank_band_hidden",
        "label_match_status_hidden",
        "packet_status_hidden",
        "subject_image_count_hidden",
        "object_image_count_hidden",
        "contact_sheet_ready_hidden",
        "mesh_packet_ready_hidden",
    ]
    for idx, row in enumerate(rows, start=1):
        candidate_id = row.get("candidate_id")
        for field in required:
            if field not in row:
                errors.append({"error_type": "missing_manifest_field", "row": idx, "candidate_id": candidate_id, "field": field})
        if row.get("packet_status_hidden") != "ready":
            errors.append({"error_type": "manifest_packet_not_ready", "row": idx, "candidate_id": candidate_id})
        if int(row.get("subject_image_count_hidden") or 0) <= 0 or int(row.get("object_image_count_hidden") or 0) <= 0:
            errors.append({"error_type": "manifest_image_count_missing", "row": idx, "candidate_id": candidate_id})
    return errors


def is_primary_scope(row: dict[str, Any]) -> bool:
    return row.get("predicate_label") in PRIMARY_PREDICATES


def is_connected_diagnostic(row: dict[str, Any]) -> bool:
    return row.get("predicate_label") == CONNECTED_PREDICATE


def p_obs_target(row: dict[str, Any]) -> int:
    return 0 if row["review_relation_reliability"] == "abstain_uncertain" else 1


def relation_binary_target(row: dict[str, Any]) -> int | None:
    if not is_primary_scope(row):
        return None
    return RELIABILITY_BINARY.get(row["review_relation_reliability"])


def factor_view(label: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "T_e": {
            "subject_label": label["subject_label"],
            "predicate_label": label["predicate_label"],
            "object_label": label["object_label"],
            "relation_family": "attachment_like",
            "subject_object_visible_pair": visible_pair(label),
        },
        "Z_e_hidden_diagnostic_only": {
            "semantic_score_norm_hidden": manifest.get("semantic_score_norm_hidden"),
            "semantic_rank_hidden": manifest.get("semantic_rank_hidden"),
            "rank_band_hidden": manifest.get("rank_band_hidden"),
            "source_artifact_key_hidden": source_artifact_key(manifest),
        },
        "G_e": {
            "numeric_geometry_materialized": False,
            "predicate_independent_geometry_available": False,
            "geometry_evidence_note": "this ingestion preserves labels/control axes only; numeric G_e must be materialized separately before learned compatibility training",
        },
        "Q_e": {
            "subject_image_count": manifest.get("subject_image_count_hidden"),
            "object_image_count": manifest.get("object_image_count_hidden"),
            "contact_sheet_ready": manifest.get("contact_sheet_ready_hidden"),
            "mesh_packet_ready": manifest.get("mesh_packet_ready_hidden"),
            "review_coverage_target": label["review_coverage"],
            "review_uncertainty_target": label["review_uncertainty"],
            "review_endpoint_identity_target": label["review_endpoint_identity"],
        },
    }


def join_rows(label_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest_by_id = {row["candidate_id"]: row for row in manifest_rows}
    out: list[dict[str, Any]] = []
    for label in label_rows:
        manifest = manifest_by_id[label["candidate_id"]]
        binary_target = relation_binary_target(label)
        semantic_score_available = manifest.get("semantic_score_norm_hidden") is not None
        row = {
            "schema_version": SCHEMA_VERSION,
            "label_source": LABEL_SOURCE,
            "split": "train",
            "paper_evidence_allowed": False,
            "candidate_id": label["candidate_id"],
            "packet_request_id": label["packet_request_id"],
            "candidate_relation": label["reviewer_visible_relation_text"],
            "subject_label": label["subject_label"],
            "predicate_label": label["predicate_label"],
            "object_label": label["object_label"],
            "relation_family": "attachment_like",
            "subject_object_visible_pair": visible_pair(label),
            "reviewer_id": label.get("reviewer_id"),
            "label_policy": label.get("label_policy"),
            "decision_reason": label.get("decision_reason"),
            "packet_image_count": int(label.get("packet_image_count") or 0),
            "packet_status": label.get("packet_status"),
            "review_relation_reliability": label["review_relation_reliability"],
            "review_geometry_support": label["review_geometry_support"],
            "review_endpoint_identity": label["review_endpoint_identity"],
            "review_coverage": label["review_coverage"],
            "review_uncertainty": label["review_uncertainty"],
            "review_notes": label["review_notes"],
            "is_primary_relation_target": is_primary_scope(label),
            "is_connected_diagnostic": is_connected_diagnostic(label),
            "p_obs_target": p_obs_target(label),
            "p_rel_target": binary_target,
            "primary_relation_binary_target": binary_target,
            "primary_relation_binary_usable": binary_target is not None,
            "compatibility_binary_target": binary_target,
            "compatibility_binary_usable": binary_target is not None,
            "geometry_support_binary_target": GEOMETRY_BINARY.get(label["review_geometry_support"]),
            "geometry_support_binary_usable": label["review_geometry_support"] in GEOMETRY_BINARY,
            "coverage_ordinal_target": COVERAGE_ORDINAL.get(label["review_coverage"]),
            "endpoint_identity_binary_target": ENDPOINT_BINARY.get(label["review_endpoint_identity"]),
            "scan_id_hidden": manifest.get("scan_id"),
            "subgraph_id_hidden": manifest.get("subgraph_id"),
            "subject_id_hidden": manifest.get("subject_id"),
            "object_id_hidden": manifest.get("object_id"),
            "prediction_id_hidden": manifest.get("prediction_id"),
            "directed_pair_id_hidden": manifest.get("directed_pair_id"),
            "query_id_hidden": manifest.get("query_id"),
            "cell_id_hidden": manifest.get("cell_id_hidden"),
            "selection_proxy_role_hidden": manifest.get("selection_proxy_role_hidden"),
            "anchor_bucket_hidden": manifest.get("anchor_bucket_hidden"),
            "rank_band_hidden": manifest.get("rank_band_hidden"),
            "semantic_rank_hidden": manifest.get("semantic_rank_hidden"),
            "semantic_rank_band_hidden": semantic_rank_band(manifest.get("semantic_rank_hidden")),
            "semantic_score_norm_hidden": manifest.get("semantic_score_norm_hidden"),
            "semantic_score_availability_hidden": "available" if semantic_score_available else "missing",
            "label_match_status_hidden": manifest.get("label_match_status_hidden"),
            "matched_predicates_hidden": manifest.get("matched_predicates_hidden") or [],
            "selection_route_hidden": manifest.get("selection_route"),
            "capacity_evidence_tier_hidden": manifest.get("capacity_evidence_tier_hidden"),
            "provisional_status_hidden": manifest.get("provisional_status_hidden"),
            "source_artifact_key_hidden": source_artifact_key(manifest),
            "mixed_endpoint_family_rank_coverage_key_hidden": manifest.get("mixed_endpoint_family_rank_coverage_key"),
            "same_scene_family_rank_key_hidden": manifest.get("same_scene_family_rank_key"),
            "visible_pair_key_hidden": manifest.get("visible_pair_key"),
            "subject_image_count_hidden": manifest.get("subject_image_count_hidden"),
            "object_image_count_hidden": manifest.get("object_image_count_hidden"),
            "contact_sheet_ready_hidden": manifest.get("contact_sheet_ready_hidden"),
            "mesh_packet_ready_hidden": manifest.get("mesh_packet_ready_hidden"),
            "factor_view": factor_view(label, manifest),
        }
        out.append(row)
    return out


def target_record(row: dict[str, Any], target_name: str, target_value: Any) -> dict[str, Any]:
    return {
        "schema_version": TARGET_SCHEMA_VERSION,
        "target_name": target_name,
        "target_value": target_value,
        "label_source": LABEL_SOURCE,
        "split": "train",
        "candidate_id": row["candidate_id"],
        "packet_request_id": row["packet_request_id"],
        "candidate_relation": row["candidate_relation"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "object_label": row["object_label"],
        "is_primary_relation_target": row["is_primary_relation_target"],
        "is_connected_diagnostic": row["is_connected_diagnostic"],
        "query_id_hidden_diagnostic_only": row["query_id_hidden"],
        "cell_id_hidden_diagnostic_only": row["cell_id_hidden"],
        "rank_band_hidden_diagnostic_only": row["rank_band_hidden"],
        "selection_proxy_role_hidden_diagnostic_only": row["selection_proxy_role_hidden"],
        "label_match_status_hidden_diagnostic_only": row["label_match_status_hidden"],
    }


def build_targets(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "multiclass_reliability": [
            target_record(row, "relation_reliability_multiclass", row["review_relation_reliability"])
            for row in rows
        ],
        "primary_binary": [
            target_record(row, "primary_relation_reliability_binary", row["primary_relation_binary_target"])
            for row in rows
            if row["primary_relation_binary_usable"]
        ],
        "compatibility_binary": [
            target_record(row, "predicate_geometry_compatibility_binary", row["compatibility_binary_target"])
            for row in rows
            if row["compatibility_binary_usable"]
        ],
        "p_rel": [
            target_record(row, "p_rel_target_given_observable", row["p_rel_target"])
            for row in rows
            if row["primary_relation_binary_usable"]
        ],
        "p_obs": [target_record(row, "p_obs_judgment_observability", row["p_obs_target"]) for row in rows],
        "p_obs_primary": [
            target_record(row, "p_obs_primary_judgment_observability", row["p_obs_target"])
            for row in rows
            if row["is_primary_relation_target"]
        ],
        "geometry_support": [
            target_record(row, "geometry_support_binary", row["geometry_support_binary_target"])
            for row in rows
            if row["geometry_support_binary_usable"]
        ],
        "evidence_quality": [
            {
                **target_record(row, "evidence_quality_observability", None),
                "coverage_ordinal_target": row["coverage_ordinal_target"],
                "endpoint_identity_binary_target": row["endpoint_identity_binary_target"],
                "review_coverage": row["review_coverage"],
                "review_uncertainty": row["review_uncertainty"],
                "review_endpoint_identity": row["review_endpoint_identity"],
            }
            for row in rows
        ],
        "connected_diagnostic": [
            target_record(row, "connected_to_diagnostic_multiclass", row["review_relation_reliability"])
            for row in rows
            if row["is_connected_diagnostic"]
        ],
        "abstain_rows": [
            target_record(row, "abstain_or_unobservable", row["review_relation_reliability"])
            for row in rows
            if row["review_relation_reliability"] == "abstain_uncertain"
        ],
    }


def entropy(counter: Counter[str]) -> float:
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
    for (group_value, target_value), count in joint.items():
        pxy = count / total
        px = group_counts[group_value] / total
        py = label_counts[target_value] / total
        if pxy and px and py:
            mi += pxy * math.log(pxy / (px * py), 2)
    denom = math.sqrt(entropy(label_counts) * entropy(group_counts))
    return mi / denom if denom else 0.0


def majority_risk(rows: list[dict[str, Any]], predictor: str, label: str) -> dict[str, Any]:
    if not rows:
        return {"predictor": predictor, "label": label, "rows": 0, "risk_flag": False}
    label_counts = Counter(str(row.get(label, "missing")) for row in rows)
    baseline = max(label_counts.values()) / len(rows)
    groups: dict[str, Counter[str]] = defaultdict(Counter)
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
        (rows, "review_relation_reliability"),
        ([row for row in rows if row["primary_relation_binary_usable"]], "primary_relation_binary_target"),
        ([row for row in rows if row["is_primary_relation_target"]], "p_obs_target"),
        ([row for row in rows if row["geometry_support_binary_usable"]], "geometry_support_binary_target"),
        (rows, "review_coverage"),
        (rows, "review_uncertainty"),
    ]
    out: list[dict[str, Any]] = []
    for label_rows, label in specs:
        for predictor in RISK_PREDICTORS:
            out.append(majority_risk(label_rows, predictor, label))
    return out


def risk_category(predictor: str) -> str:
    if predictor in CONSTRUCTION_PROXY_PREDICTORS:
        return "construction_proxy_or_source_hidden"
    if predictor in VISIBLE_OR_ID_PREDICTORS:
        return "visible_semantic_or_id"
    if predictor in LABEL_DERIVED_PREDICTORS:
        return "label_derived_auxiliary_target"
    return "other"


def shortcut_flag_summary(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flagged = [risk for risk in risks if risk.get("risk_flag")]
    return [
        {
            "predictor": risk["predictor"],
            "label": risk["label"],
            "rows": risk["rows"],
            "groups": risk.get("groups"),
            "majority_rule_accuracy": risk.get("majority_rule_accuracy"),
            "majority_baseline_accuracy": risk.get("majority_baseline_accuracy"),
            "majority_excess_over_baseline": risk.get("majority_excess_over_baseline"),
            "normalized_mutual_information": risk.get("normalized_mutual_information"),
        }
        for risk in flagged
    ]


def categorized_risk_counts(risks: list[dict[str, Any]]) -> dict[str, int]:
    flagged = [risk for risk in risks if risk.get("risk_flag")]
    return dict(sorted(Counter(risk_category(str(risk.get("predictor"))) for risk in flagged).items()))


def group_table(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(field, "missing"))].append(row)
    out: list[dict[str, Any]] = []
    for value, group_rows in grouped.items():
        rel_counts = Counter(row["review_relation_reliability"] for row in group_rows)
        primary_values = {row["primary_relation_binary_target"] for row in group_rows if row["primary_relation_binary_usable"]}
        out.append(
            {
                "group_field": field,
                "group_value": value,
                "rows": len(group_rows),
                "accept_reliable": rel_counts.get("accept_reliable", 0),
                "reject_unreliable": rel_counts.get("reject_unreliable", 0),
                "abstain_uncertain": rel_counts.get("abstain_uncertain", 0),
                "primary_accept": sum(
                    1 for row in group_rows if row["primary_relation_binary_usable"] and row["primary_relation_binary_target"] == 1
                ),
                "primary_reject": sum(
                    1 for row in group_rows if row["primary_relation_binary_usable"] and row["primary_relation_binary_target"] == 0
                ),
                "primary_binary_mixed": len(primary_values) > 1,
                "p_obs_positive": sum(1 for row in group_rows if row["p_obs_target"] == 1),
                "p_obs_negative": sum(1 for row in group_rows if row["p_obs_target"] == 0),
            }
        )
    out.sort(key=lambda row: (-row["rows"], str(row["group_value"])))
    return out


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    viability = summary["target_viability"]
    lines = [
        "# H002 Attachment Independent Positive Anchor Label Ingestion V1",
        "",
        f"Created at: `{summary['created_at_utc']}`",
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
        "## Target Counts",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"multiclass_rows = {counts['multiclass_rows']}",
        f"primary_binary_rows = {counts['primary_binary_rows']}",
        f"compatibility_binary_rows = {counts['compatibility_binary_rows']}",
        f"p_rel_rows = {counts['p_rel_rows']}",
        f"p_obs_rows = {counts['p_obs_rows']}",
        f"p_obs_primary_rows = {counts['p_obs_primary_rows']}",
        f"geometry_support_rows = {counts['geometry_support_rows']}",
        f"evidence_quality_rows = {counts['evidence_quality_rows']}",
        f"connected_diagnostic_rows = {counts['connected_diagnostic_rows']}",
        f"abstain_rows = {counts['abstain_rows']}",
        f"review_relation_reliability = {counts['review_relation_reliability']}",
        f"primary_binary_target = {counts['primary_binary_target']}",
        f"p_obs_target = {counts['p_obs_target']}",
        f"review_geometry_support = {counts['review_geometry_support']}",
        "```",
        "",
        "## Viability",
        "",
        "```text",
        f"minimum_positive_for_posterior_smoke = {viability['minimum_positive_for_posterior_smoke']}",
        f"minimum_negative_for_posterior_smoke = {viability['minimum_negative_for_posterior_smoke']}",
        f"primary_positive_rows = {viability['primary_positive_rows']}",
        f"primary_negative_rows = {viability['primary_negative_rows']}",
        f"class_mass_pass = {viability['class_mass_pass']}",
        f"quick_probe_risk_flags = {counts['quick_probe_risk_flags']}",
        f"model_shortcut_probe_risk_flags = {counts['model_shortcut_probe_risk_flags']}",
        f"construction_proxy_probe_risk_flags = {counts['construction_proxy_probe_risk_flags']}",
        f"label_derived_probe_risk_flags = {counts['label_derived_probe_risk_flags']}",
        f"same_query_mixed_primary_binary_groups = {viability['same_query_mixed_primary_binary_groups']}",
        f"same_proxy_role_mixed_primary_binary_groups = {viability['same_proxy_role_mixed_primary_binary_groups']}",
        f"same_cell_mixed_primary_binary_groups = {viability['same_cell_mixed_primary_binary_groups']}",
        f"same_rank_band_mixed_primary_binary_groups = {viability['same_rank_band_mixed_primary_binary_groups']}",
        f"same_predicate_mixed_primary_binary_groups = {viability['same_predicate_mixed_primary_binary_groups']}",
        f"same_visible_pair_mixed_primary_binary_groups = {viability['same_visible_pair_mixed_primary_binary_groups']}",
        "```",
        "",
        "## Interpretation",
        "",
        "The positive-anchor label target now has enough primary positive and negative mass for a",
        "diagnostic posterior smoke in terms of class count, but shortcut risks remain. Therefore the",
        "next gate is target-independence audit, not model training.",
        "",
        "## Boundary",
        "",
        "Hidden query/proxy/rank/source/GT fields are joined only after label lock and remain diagnostic",
        "control fields. They are not model inputs for `C_e`, `Q_e`, `p_obs`, or `p_rel`.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fill_summary = read_json(FILL_SUMMARY)
    _, label_rows = read_csv(FILLED_SHEET)
    decision_rows = read_jsonl(LABEL_DECISIONS)
    manifest_rows = read_jsonl(HIDDEN_MANIFEST)

    errors = validate_fill_summary(fill_summary)
    errors.extend(validate_decisions(decision_rows))
    errors.extend(validate_manifest(manifest_rows))
    errors.extend(validate_ids(label_rows, decision_rows, manifest_rows))

    rows = join_rows(label_rows, manifest_rows) if not errors else []
    targets = build_targets(rows)
    risks = probe_risks(rows)
    flagged_risks = [risk for risk in risks if risk.get("risk_flag")]
    model_shortcut_risks = [
        risk for risk in flagged_risks
        if risk_category(str(risk.get("predictor"))) != "label_derived_auxiliary_target"
    ]
    construction_proxy_risks = [
        risk for risk in flagged_risks
        if risk_category(str(risk.get("predictor"))) == "construction_proxy_or_source_hidden"
    ]
    label_derived_risks = [
        risk for risk in flagged_risks
        if risk_category(str(risk.get("predictor"))) == "label_derived_auxiliary_target"
    ]

    by_query = group_table(rows, "query_id_hidden")
    by_proxy = group_table(rows, "selection_proxy_role_hidden")
    by_cell = group_table(rows, "cell_id_hidden")
    by_rank = group_table(rows, "rank_band_hidden")
    by_predicate = group_table(rows, "predicate_label")
    by_visible_pair = group_table(rows, "subject_object_visible_pair")
    by_mixed_endpoint_family_rank_coverage = group_table(rows, "mixed_endpoint_family_rank_coverage_key_hidden")
    by_selection_route = group_table(rows, "selection_route_hidden")
    by_gt = group_table(rows, "label_match_status_hidden")

    rel_counts = Counter(row["review_relation_reliability"] for row in rows)
    primary_counts = Counter(str(row["primary_relation_binary_target"]) for row in rows if row["primary_relation_binary_usable"])
    p_obs_counts = Counter(str(row["p_obs_target"]) for row in rows)
    geom_counts = Counter(row["review_geometry_support"] for row in rows)
    coverage_counts = Counter(row["review_coverage"] for row in rows)
    uncertainty_counts = Counter(row["review_uncertainty"] for row in rows)
    endpoint_counts = Counter(row["review_endpoint_identity"] for row in rows)
    predicate_counts = Counter(row["predicate_label"] for row in rows)
    query_counts = Counter(str(row["query_id_hidden"]) for row in rows)
    proxy_counts = Counter(str(row["selection_proxy_role_hidden"]) for row in rows)
    rank_counts = Counter(str(row["rank_band_hidden"]) for row in rows)
    gt_status_counts = Counter(str(row["label_match_status_hidden"]) for row in rows)

    primary_positive = sum(
        1 for row in rows if row["primary_relation_binary_usable"] and row["primary_relation_binary_target"] == 1
    )
    primary_negative = sum(
        1 for row in rows if row["primary_relation_binary_usable"] and row["primary_relation_binary_target"] == 0
    )
    class_mass_pass = (
        primary_positive >= MIN_POSITIVE_FOR_POSTERIOR_SMOKE
        and primary_negative >= MIN_NEGATIVE_FOR_POSTERIOR_SMOKE
    )

    if errors:
        status = STATUS_ERROR
    elif not class_mass_pass and model_shortcut_risks:
        status = STATUS_POSITIVE_SPARSE_WITH_SHORTCUT_RISK
    elif not class_mass_pass:
        status = STATUS_POSITIVE_SPARSE
    elif model_shortcut_risks:
        status = STATUS_SHORTCUT_RISK
    else:
        status = STATUS_READY

    output_paths = {
        "summary": OUT_DIR / "summary.json",
        "report": OUT_DIR / "report.md",
        "ingested_rows": OUT_DIR / "ingested_rows.jsonl",
        "factor_views": OUT_DIR / "factor_views.jsonl",
        "multiclass_reliability_target": OUT_DIR / "multiclass_reliability_target.jsonl",
        "primary_binary_target": OUT_DIR / "primary_binary_target.jsonl",
        "compatibility_binary_target": OUT_DIR / "compatibility_binary_target.jsonl",
        "p_rel_target": OUT_DIR / "p_rel_target.jsonl",
        "p_obs_target": OUT_DIR / "p_obs_target.jsonl",
        "p_obs_primary_target": OUT_DIR / "p_obs_primary_target.jsonl",
        "geometry_support_target": OUT_DIR / "geometry_support_target.jsonl",
        "evidence_quality_target": OUT_DIR / "evidence_quality_target.jsonl",
        "connected_diagnostic_target": OUT_DIR / "connected_diagnostic_target.jsonl",
        "abstain_rows": OUT_DIR / "abstain_rows.jsonl",
        "shortcut_probe_risks": OUT_DIR / "shortcut_probe_risks.json",
        "shortcut_flag_summary": OUT_DIR / "shortcut_flag_summary.csv",
        "query_vs_label_table": OUT_DIR / "query_vs_label_table.csv",
        "proxy_vs_label_table": OUT_DIR / "proxy_vs_label_table.csv",
        "cell_vs_label_table": OUT_DIR / "cell_vs_label_table.csv",
        "rank_vs_label_table": OUT_DIR / "rank_vs_label_table.csv",
        "predicate_vs_label_table": OUT_DIR / "predicate_vs_label_table.csv",
        "visible_pair_vs_label_table": OUT_DIR / "visible_pair_vs_label_table.csv",
        "mixed_endpoint_family_rank_coverage_vs_label_table": OUT_DIR / "mixed_endpoint_family_rank_coverage_vs_label_table.csv",
        "selection_route_vs_label_table": OUT_DIR / "selection_route_vs_label_table.csv",
        "gt_reliability_mismatch_table": OUT_DIR / "gt_reliability_mismatch_table.csv",
        "validation_errors": OUT_DIR / "validation_errors.jsonl",
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "next_todo": NEXT_TODO,
        "input_paths": {
            "fill_summary": rel_path(FILL_SUMMARY),
            "filled_sheet": rel_path(FILLED_SHEET),
            "label_decisions": rel_path(LABEL_DECISIONS),
            "hidden_manifest": rel_path(HIDDEN_MANIFEST),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "multiclass_rows": len(targets["multiclass_reliability"]),
            "primary_binary_rows": len(targets["primary_binary"]),
            "compatibility_binary_rows": len(targets["compatibility_binary"]),
            "p_rel_rows": len(targets["p_rel"]),
            "p_obs_rows": len(targets["p_obs"]),
            "p_obs_primary_rows": len(targets["p_obs_primary"]),
            "geometry_support_rows": len(targets["geometry_support"]),
            "evidence_quality_rows": len(targets["evidence_quality"]),
            "connected_diagnostic_rows": len(targets["connected_diagnostic"]),
            "abstain_rows": len(targets["abstain_rows"]),
            "review_relation_reliability": dict(sorted(rel_counts.items())),
            "primary_binary_target": dict(sorted(primary_counts.items())),
            "p_obs_target": dict(sorted(p_obs_counts.items())),
            "review_geometry_support": dict(sorted(geom_counts.items())),
            "review_coverage": dict(sorted(coverage_counts.items())),
            "review_uncertainty": dict(sorted(uncertainty_counts.items())),
            "review_endpoint_identity": dict(sorted(endpoint_counts.items())),
            "predicate_label": dict(sorted(predicate_counts.items())),
            "query_id_hidden": dict(sorted(query_counts.items())),
            "selection_proxy_role_hidden": dict(sorted(proxy_counts.items())),
            "rank_band_hidden": dict(sorted(rank_counts.items())),
            "label_match_status_hidden": dict(sorted(gt_status_counts.items())),
            "quick_probe_risk_flags": len(flagged_risks),
            "model_shortcut_probe_risk_flags": len(model_shortcut_risks),
            "construction_proxy_probe_risk_flags": len(construction_proxy_risks),
            "label_derived_probe_risk_flags": len(label_derived_risks),
            "risk_flag_categories": categorized_risk_counts(risks),
        },
        "target_viability": {
            "minimum_positive_for_posterior_smoke": MIN_POSITIVE_FOR_POSTERIOR_SMOKE,
            "minimum_negative_for_posterior_smoke": MIN_NEGATIVE_FOR_POSTERIOR_SMOKE,
            "primary_positive_rows": primary_positive,
            "primary_negative_rows": primary_negative,
            "class_mass_pass": class_mass_pass,
            "same_query_mixed_primary_binary_groups": sum(1 for row in by_query if row["primary_binary_mixed"]),
            "same_proxy_role_mixed_primary_binary_groups": sum(1 for row in by_proxy if row["primary_binary_mixed"]),
            "same_cell_mixed_primary_binary_groups": sum(1 for row in by_cell if row["primary_binary_mixed"]),
            "same_rank_band_mixed_primary_binary_groups": sum(1 for row in by_rank if row["primary_binary_mixed"]),
            "same_predicate_mixed_primary_binary_groups": sum(1 for row in by_predicate if row["primary_binary_mixed"]),
            "same_visible_pair_mixed_primary_binary_groups": sum(1 for row in by_visible_pair if row["primary_binary_mixed"]),
            "same_mixed_endpoint_family_rank_coverage_mixed_primary_binary_groups": sum(
                1 for row in by_mixed_endpoint_family_rank_coverage if row["primary_binary_mixed"]
            ),
            "same_selection_route_mixed_primary_binary_groups": sum(
                1 for row in by_selection_route if row["primary_binary_mixed"]
            ),
            "posterior_smoke_allowed_after_ingestion": False,
        },
        "shortcut_probe": {
            "risk_thresholds": RISK_THRESHOLDS,
            "risk_flags": shortcut_flag_summary(flagged_risks),
            "model_shortcut_risk_flags": shortcut_flag_summary(model_shortcut_risks),
            "construction_proxy_risk_flags": shortcut_flag_summary(construction_proxy_risks),
            "label_derived_auxiliary_target_flags": shortcut_flag_summary(label_derived_risks),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "ingests_locked_labels": True,
            "fills_new_labels": False,
            "reads_hidden_manifest_after_label_lock": True,
            "hidden_manifest_used_for_label_fill": False,
            "hidden_fields_as_model_input": False,
            "source_score_or_rank_as_model_input": False,
            "construction_proxy_as_model_input": False,
            "uses_p_geom_valid": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "numeric_g_e_materialized": False,
        },
        "validation_errors": len(errors),
    }

    write_jsonl(output_paths["ingested_rows"], rows)
    write_jsonl(
        output_paths["factor_views"],
        [
            {
                "candidate_id": row["candidate_id"],
                "packet_request_id": row["packet_request_id"],
                "label_source": row["label_source"],
                "factor_view": row["factor_view"],
                "targets": {
                    "p_obs_target": row["p_obs_target"],
                    "p_rel_target": row["p_rel_target"],
                    "compatibility_binary_target": row["compatibility_binary_target"],
                    "review_relation_reliability": row["review_relation_reliability"],
                },
            }
            for row in rows
        ],
    )
    write_jsonl(output_paths["multiclass_reliability_target"], targets["multiclass_reliability"])
    write_jsonl(output_paths["primary_binary_target"], targets["primary_binary"])
    write_jsonl(output_paths["compatibility_binary_target"], targets["compatibility_binary"])
    write_jsonl(output_paths["p_rel_target"], targets["p_rel"])
    write_jsonl(output_paths["p_obs_target"], targets["p_obs"])
    write_jsonl(output_paths["p_obs_primary_target"], targets["p_obs_primary"])
    write_jsonl(output_paths["geometry_support_target"], targets["geometry_support"])
    write_jsonl(output_paths["evidence_quality_target"], targets["evidence_quality"])
    write_jsonl(output_paths["connected_diagnostic_target"], targets["connected_diagnostic"])
    write_jsonl(output_paths["abstain_rows"], targets["abstain_rows"])
    write_json(output_paths["shortcut_probe_risks"], {"risk_thresholds": RISK_THRESHOLDS, "risks": risks})
    write_csv(output_paths["shortcut_flag_summary"], shortcut_flag_summary(flagged_risks))
    write_csv(output_paths["query_vs_label_table"], by_query, TABLE_FIELDS)
    write_csv(output_paths["proxy_vs_label_table"], by_proxy, TABLE_FIELDS)
    write_csv(output_paths["cell_vs_label_table"], by_cell, TABLE_FIELDS)
    write_csv(output_paths["rank_vs_label_table"], by_rank, TABLE_FIELDS)
    write_csv(output_paths["predicate_vs_label_table"], by_predicate, TABLE_FIELDS)
    write_csv(output_paths["visible_pair_vs_label_table"], by_visible_pair, TABLE_FIELDS)
    write_csv(output_paths["mixed_endpoint_family_rank_coverage_vs_label_table"], by_mixed_endpoint_family_rank_coverage, TABLE_FIELDS)
    write_csv(output_paths["selection_route_vs_label_table"], by_selection_route, TABLE_FIELDS)
    write_csv(output_paths["gt_reliability_mismatch_table"], by_gt, TABLE_FIELDS)
    write_jsonl(output_paths["validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)

    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"primary_binary_rows={summary['counts']['primary_binary_rows']}")
    print(f"primary_binary_target={summary['counts']['primary_binary_target']}")
    print(f"p_obs_target={summary['counts']['p_obs_target']}")
    print(f"model_shortcut_probe_risk_flags={summary['counts']['model_shortcut_probe_risk_flags']}")
    print(f"construction_proxy_probe_risk_flags={summary['counts']['construction_proxy_probe_risk_flags']}")
    print(f"label_derived_probe_risk_flags={summary['counts']['label_derived_probe_risk_flags']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
