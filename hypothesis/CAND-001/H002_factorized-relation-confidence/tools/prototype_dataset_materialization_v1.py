#!/usr/bin/env python3
"""Materialize the H002 prototype dataset v1.

This is a hypothesis-stage adapter. It reads train-only H002 artifacts, maps them
to the current T/Z/G/Q contract, and writes a new artifact root without modifying
the source artifacts.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H002_ROOT.parents[2]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_SUPPORT_ROWS = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready"
    / "posterior_ready_rows.jsonl"
)
DEFAULT_V20_ROWS = (
    RGA_ROOT
    / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingestion"
    / "ingested_rows.jsonl"
)
DEFAULT_V22_ROWS = (
    RGA_ROOT
    / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion"
    / "ingested_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/prototype_dataset_v1"

GEOMETRY_BLOCKED_FRAGMENTS = (
    "predicate",
    "family",
    "source",
    "rank",
    "label",
    "hidden",
    "status",
    "bucket",
    "target",
    "semantic",
    "expected_z_sign",
    "gate",
    "sign_agreement",
    "signed_margin",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-rows", type=Path, default=DEFAULT_SUPPORT_ROWS)
    parser.add_argument("--v20-rows", type=Path, default=DEFAULT_V20_ROWS)
    parser.add_argument("--v22-rows", type=Path, default=DEFAULT_V22_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_geometry_features(features: dict[str, Any]) -> dict[str, float]:
    output: dict[str, float] = {}
    for key, value in features.items():
        lowered = key.lower()
        if any(fragment in lowered for fragment in GEOMETRY_BLOCKED_FRAGMENTS):
            continue
        numeric = safe_float(value)
        if numeric is not None:
            output[key] = numeric
    return output


def feature_mask(features: dict[str, Any]) -> dict[str, bool]:
    return {key: value is not None for key, value in features.items()}


def split_candidate_relation(text: str, predicate: str) -> tuple[str, str]:
    if predicate and predicate in text:
        left, right = text.split(predicate, 1)
        return left.strip(), right.strip()
    return "", ""


def source_score_band(rank: Any) -> str:
    rank_value = safe_float(rank)
    if rank_value is None:
        return "not_available"
    if rank_value <= 20:
        return "top_20"
    if rank_value <= 100:
        return "top_100"
    if rank_value <= 200:
        return "rank_101_200"
    if rank_value <= 500:
        return "rank_201_500"
    return "rank_over_500"


def observability_label_from_review(row: dict[str, Any]) -> str:
    review = str(row.get("review_coverage", "")).lower()
    if review == "sufficient":
        return "observable"
    if review == "limited":
        return "limited"
    if str(row.get("review_relation_reliability")) == "abstain_uncertain":
        return "limited"
    return "insufficient"


def reliability_label_from_review(value: Any) -> str:
    mapping = {
        "accept_reliable": "accept",
        "reject_unreliable": "reject",
        "abstain_uncertain": "abstain",
    }
    return mapping.get(str(value), "unavailable")


def make_t_block(predicate: str, family: str, subject: str, obj: str) -> dict[str, Any]:
    return {
        "predicate_label": predicate,
        "predicate_text": predicate,
        "relation_family": family,
        "subject_label": subject,
        "object_label": obj,
        "subject_object_text": f"{subject} [REL] {obj}",
        "predicate_embedding_id": None,
        "subject_class_embedding_id": None,
        "object_class_embedding_id": None,
    }


def make_z_block(
    source_id: str,
    score_raw: Any = None,
    score_norm: Any = None,
    rank: Any = None,
    rank_band: str | None = None,
) -> dict[str, Any]:
    norm = safe_float(score_norm)
    raw = safe_float(score_raw, norm)
    rank_value = safe_float(rank)
    return {
        "source_id": source_id,
        "source_score_raw": raw,
        "source_score_normalized": norm,
        "source_rank": rank_value,
        "source_rank_band": rank_band or source_score_band(rank),
        "source_score_available": norm is not None or raw is not None,
    }


def support_row_to_prototype(row: dict[str, Any], index: int) -> dict[str, Any]:
    identity = row["identity"]
    baseline_inputs = row.get("baseline_inputs", {})
    semantic = baseline_inputs.get("semantic_only", {})
    legacy_geometry = baseline_inputs.get("legacy_geometry_only", {})
    raw_witness = baseline_inputs.get("raw_witness_only_v2", {})
    geometry_features = clean_geometry_features(raw_witness)
    coverage = {key: value for key, value in raw_witness.items() if key.startswith("coverage_") or key.endswith("_missing_flag")}
    target = row.get("target", {})
    y = int(target.get("y"))
    row_id = f"h002_proto_v1_support_{index:06d}"
    compatibility_label = "positive" if y == 1 else "counterfactual_negative"
    reliability_label = "accept" if y == 1 else "reject"
    positive_tier = "P1" if y == 1 else "none"
    negative_tier = "none" if y == 1 else "N6"
    rank = semantic.get("semantic_rank")
    t_block = make_t_block(
        str(identity["predicate_label"]),
        str(identity["predicate_family"]),
        str(identity["subject_label"]),
        str(identity["object_label"]),
    )
    z_block = make_z_block(
        source_id="open3dsg_train_full",
        score_raw=semantic.get("semantic_score_raw"),
        score_norm=semantic.get("semantic_score_norm"),
        rank=rank,
    )
    g_block = {
        "geometry_features": geometry_features,
        "geometry_feature_mask": feature_mask(geometry_features),
        "geometry_feature_units": {},
        "geometry_normalization": "train_family_local_raw_witness_v2",
        "geometry_source": "raw_witness_v2",
    }
    q_block = {
        "subject_point_count": None,
        "object_point_count": None,
        "pair_point_count": None,
        "mesh_available": None,
        "normal_available": None,
        "same_frame_visible": None,
        "multi_view_count": None,
        "subject_crop_available": None,
        "object_crop_available": None,
        "pair_crop_available": None,
        "low_coverage_flag": bool(safe_float(coverage.get("coverage_evidence_ready"), 1.0) == 0.0),
        "missing_geometry_flag": bool(safe_float(coverage.get("raw_witness_missing_flag"), 0.0) == 1.0),
        "unsupported_family_flag": False,
        "evidence_conflict_flag": False,
        "asset_tier": "geometry_raw_witness",
        "coverage_features": coverage,
    }
    return {
        "schema_version": "h002_prototype_dataset_v1_row",
        "row_id": row_id,
        "group_id": None,
        "row_role": "anchor_positive" if y == 1 else "counterfactual_negative",
        "split": "train",
        "source_dataset": "Open3DSG_train",
        "relation_source": "open3dsg_raw_witness_user_confirmed",
        "scan_id": identity.get("scan_id"),
        "scene_id": identity.get("scan_id"),
        "subject_instance_id": identity.get("subject_id"),
        "object_instance_id": identity.get("object_id"),
        "directed_pair_id": f"{identity.get('scan_id')}::{identity.get('subject_id')}->{identity.get('object_id')}",
        "candidate_relation_text": f"{identity.get('subject_label')} {identity.get('predicate_label')} {identity.get('object_label')}",
        "T_e": t_block,
        "Z_e": z_block,
        "G_e": g_block,
        "Q_e": q_block,
        "p_geom_valid_baseline": safe_float(legacy_geometry.get("p_geom_valid")),
        "geometry_status_baseline": None,
        "official_gt_axis": {
            "gt_match_status": "unavailable",
            "gt_predicates_for_pair": [],
            "gt_family_for_pair": [],
            "gt_source": "not_joined_for_raw_witness_v2",
            "gt_used_as_model_input": False,
        },
        "audit_axis": {
            "audit_label": reliability_label_from_review("accept_reliable" if y == 1 else "reject_unreliable"),
            "geometry_support_label": "not_audited",
            "audit_evidence_tier": "geometry_raw_witness",
            "audit_provenance": "user_confirmed_raw_witness_v2",
            "audit_hidden_fields_exposed": False,
        },
        "counterfactual_axis": {
            "compatibility_label": compatibility_label,
            "positive_tier": positive_tier,
            "negative_tier": negative_tier,
            "counterfactual_type": "none" if y == 1 else "same_family_rank_coverage_hard_negative",
            "anchor_row_id": None,
            "matching_fields": ["relation_family", "source_rank_band", "geometry_raw_witness_available"],
            "relaxed_matching_fields": ["scan_id"],
        },
        "observability_axis": {
            "observability_label": "observable" if not q_block["missing_geometry_flag"] else "insufficient",
            "observability_reason": "raw_witness_available" if not q_block["missing_geometry_flag"] else "missing_raw_witness",
            "p_obs_target_usable": True,
        },
        "reliability_eval_axis": {
            "reliability_label": reliability_label,
            "label_source": "user_confirmed_raw_witness_v2",
            "binary_usable": True,
            "multiclass_usable": True,
        },
        "model_views": {
            "compatibility_main": {"T_e": t_block, "G_e": g_block},
            "source_only": {"Z_e": z_block},
            "semantic_source": {"T_e": t_block, "Z_e": z_block},
            "geometry_rule": {
                "p_geom_valid_baseline": safe_float(legacy_geometry.get("p_geom_valid")),
                "geometry_status_baseline": None,
            },
            "semantic_x_geometry_rule": {
                "source_score_normalized": z_block["source_score_normalized"],
                "p_geom_valid_baseline": safe_float(legacy_geometry.get("p_geom_valid")),
                "score": (
                    z_block["source_score_normalized"] * safe_float(legacy_geometry.get("p_geom_valid"))
                    if z_block["source_score_normalized"] is not None and safe_float(legacy_geometry.get("p_geom_valid")) is not None
                    else None
                ),
            },
            "obs_head": {"Q_e": q_block},
            "full_factorized": {"Z_e": z_block, "Q_e": q_block, "C_e_input": {"T_e": t_block, "G_e": g_block}},
        },
        "hidden_control": {
            "source_artifact": "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready",
            "prediction_id": identity.get("prediction_id"),
            "target": target,
            "provenance": row.get("provenance", {}),
        },
    }


def audit_row_to_prototype(row: dict[str, Any], index: int, source_name: str) -> dict[str, Any]:
    predicate = str(row.get("predicate_label", ""))
    family = str(row.get("predicate_family", "attachment_deferred"))
    subject = str(row.get("subject_label", ""))
    obj = str(row.get("object_label", ""))
    relation_text = str(row.get("candidate_relation") or f"{subject} {predicate} {obj}")
    if not subject or not obj:
        subject, obj = split_candidate_relation(relation_text, predicate)
    row_id = f"h002_proto_v1_{source_name}_{index:06d}"
    review_reliability = str(row.get("review_relation_reliability", ""))
    reliability_label = reliability_label_from_review(review_reliability)
    t_block = make_t_block(predicate, family, subject, obj)
    z_block = make_z_block(
        source_id=str(row.get("source_id_hidden", "open3dsg_train_full")),
        score_norm=row.get("gt_semantic_score_norm_hidden"),
        rank=row.get("gt_rank_in_context_hidden"),
        rank_band=str(row.get("rank_band_hidden") or "not_available"),
    )
    g_block = {
        "geometry_features": {},
        "geometry_feature_mask": {},
        "geometry_feature_units": {},
        "geometry_normalization": "not_materialized_for_attachment_audit_v1",
        "geometry_source": "audit_packet_no_numeric_g",
    }
    q_block = {
        "subject_point_count": None,
        "object_point_count": None,
        "pair_point_count": None,
        "mesh_available": row.get("mesh_ready_hidden"),
        "normal_available": None,
        "same_frame_visible": str(row.get("visual_context_state_hidden", "")).startswith("same_frame"),
        "multi_view_count": row.get("shared_origin_frame_count"),
        "subject_crop_available": row.get("shared_crop_rank_count") is not None,
        "object_crop_available": row.get("shared_crop_rank_count") is not None,
        "pair_crop_available": str(row.get("visual_context_state_hidden", "")).startswith("same_frame"),
        "low_coverage_flag": str(row.get("review_coverage")) == "limited",
        "missing_geometry_flag": True,
        "unsupported_family_flag": predicate == "connected to",
        "evidence_conflict_flag": str(row.get("review_geometry_support")) == "ambiguous",
        "asset_tier": str(row.get("evidence_tier") or "audit_packet"),
    }
    gt_predicates = row.get("gt_matched_predicates_hidden") or []
    gt_families = row.get("gt_matched_families_hidden") or []
    audit_label = review_reliability if review_reliability else "not_audited"
    compatibility_label = "unknown"
    positive_tier = "none"
    if reliability_label == "accept" and not q_block["missing_geometry_flag"]:
        compatibility_label = "positive"
        positive_tier = "P1"
    return {
        "schema_version": "h002_prototype_dataset_v1_row",
        "row_id": row_id,
        "group_id": None,
        "row_role": "source_unknown" if reliability_label != "abstain" else "observability_probe",
        "split": "train",
        "source_dataset": "Open3DSG_train",
        "relation_source": f"{source_name}_audit_ingestion",
        "scan_id": row.get("scan_id_hidden"),
        "scene_id": row.get("scan_id_hidden"),
        "subject_instance_id": row.get("subject_id_hidden"),
        "object_instance_id": row.get("object_id_hidden"),
        "directed_pair_id": f"{row.get('scan_id_hidden')}::{row.get('subject_id_hidden')}->{row.get('object_id_hidden')}",
        "candidate_relation_text": relation_text,
        "T_e": t_block,
        "Z_e": z_block,
        "G_e": g_block,
        "Q_e": q_block,
        "p_geom_valid_baseline": safe_float(row.get("gt_p_geom_valid_hidden")),
        "geometry_status_baseline": row.get("gt_geometry_status_hidden"),
        "official_gt_axis": {
            "gt_match_status": row.get("gt_label_match_status_hidden", "unavailable"),
            "gt_predicates_for_pair": gt_predicates,
            "gt_family_for_pair": gt_families,
            "gt_source": row.get("gt_label_source_hidden", "official_train_annotation"),
            "gt_used_as_model_input": False,
        },
        "audit_axis": {
            "audit_label": audit_label,
            "geometry_support_label": row.get("review_geometry_support", "not_audited"),
            "audit_evidence_tier": row.get("evidence_tier", "not_available"),
            "audit_provenance": row.get("label_source", source_name),
            "audit_hidden_fields_exposed": False,
        },
        "counterfactual_axis": {
            "compatibility_label": compatibility_label,
            "positive_tier": positive_tier,
            "negative_tier": "none",
            "counterfactual_type": "none",
            "anchor_row_id": None,
            "matching_fields": [],
            "relaxed_matching_fields": [],
        },
        "observability_axis": {
            "observability_label": observability_label_from_review(row),
            "observability_reason": str(row.get("review_uncertainty") or row.get("review_coverage") or "audit_packet"),
            "p_obs_target_usable": True,
        },
        "reliability_eval_axis": {
            "reliability_label": reliability_label,
            "label_source": row.get("label_source", source_name),
            "binary_usable": reliability_label in {"accept", "reject"},
            "multiclass_usable": reliability_label in {"accept", "reject", "abstain"},
        },
        "model_views": {
            "compatibility_main": {"T_e": t_block, "G_e": g_block},
            "source_only": {"Z_e": z_block},
            "semantic_source": {"T_e": t_block, "Z_e": z_block},
            "geometry_rule": {
                "p_geom_valid_baseline": safe_float(row.get("gt_p_geom_valid_hidden")),
                "geometry_status_baseline": row.get("gt_geometry_status_hidden"),
            },
            "semantic_x_geometry_rule": {
                "source_score_normalized": z_block["source_score_normalized"],
                "p_geom_valid_baseline": safe_float(row.get("gt_p_geom_valid_hidden")),
                "score": None,
            },
            "obs_head": {"Q_e": q_block},
            "full_factorized": {"Z_e": z_block, "Q_e": q_block, "C_e_input": {"T_e": t_block, "G_e": g_block}},
        },
        "hidden_control": {
            "source_artifact": source_name,
            "packet_id": row.get("packet_id"),
            "blind_review_id": row.get("blind_review_id"),
            "planned_proxy_role_hidden": row.get("planned_proxy_role_hidden"),
            "rank_band_hidden": row.get("rank_band_hidden"),
            "geometry_bucket_hidden": row.get("geometry_bucket_hidden"),
            "strict_group_value_hidden": row.get("strict_group_value_hidden"),
            "review_notes": row.get("review_notes"),
        },
    }


def assign_counterfactual_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positives = [row for row in rows if row["counterfactual_axis"]["compatibility_label"] == "positive"]
    negatives_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["counterfactual_axis"]["compatibility_label"] == "counterfactual_negative":
            negatives_by_family[str(row["T_e"]["relation_family"])].append(row)
    groups: list[dict[str, Any]] = []
    used_index: dict[str, int] = defaultdict(int)
    for idx, pos in enumerate(positives):
        family = str(pos["T_e"]["relation_family"])
        negs = negatives_by_family.get(family, [])
        if not negs:
            continue
        neg = negs[used_index[family] % len(negs)]
        used_index[family] += 1
        group_id = f"h002_proto_v1_group_{idx:06d}"
        pos["group_id"] = group_id
        neg.setdefault("counterfactual_axis", {})["anchor_row_id"] = pos["row_id"]
        if neg["group_id"] is None:
            neg["group_id"] = group_id
        groups.append(
            {
                "group_id": group_id,
                "anchor_row_id": pos["row_id"],
                "anchor_positive_tier": pos["counterfactual_axis"]["positive_tier"],
                "counterfactual_row_ids": [neg["row_id"]],
                "negative_tiers_present": [neg["counterfactual_axis"]["negative_tier"]],
                "matching_fields": {
                    "split": "train",
                    "relation_family": family,
                    "source_id": pos["Z_e"]["source_id"],
                    "source_rank_band": pos["Z_e"]["source_rank_band"],
                    "asset_tier": pos["Q_e"]["asset_tier"],
                },
                "relaxed_matching_fields": ["scan_id"],
            }
        )
    return groups


def flatten_baseline(row: dict[str, Any]) -> dict[str, Any]:
    z = row["Z_e"]
    return {
        "row_id": row["row_id"],
        "family": row["T_e"]["relation_family"],
        "predicate_label": row["T_e"]["predicate_label"],
        "source_id": z["source_id"],
        "source_score_normalized": z["source_score_normalized"],
        "source_rank_band": z["source_rank_band"],
        "p_geom_valid_baseline": row["p_geom_valid_baseline"],
        "geometry_status_baseline": row["geometry_status_baseline"],
        "geometry_feature_count": len(row["G_e"]["geometry_features"]),
        "observability_label": row["observability_axis"]["observability_label"],
        "compatibility_label": row["counterfactual_axis"]["compatibility_label"],
        "positive_tier": row["counterfactual_axis"]["positive_tier"],
        "negative_tier": row["counterfactual_axis"]["negative_tier"],
        "reliability_label": row["reliability_eval_axis"]["reliability_label"],
        "binary_usable": row["reliability_eval_axis"]["binary_usable"],
        "multiclass_usable": row["reliability_eval_axis"]["multiclass_usable"],
        "hidden_control_available": bool(row.get("hidden_control")),
    }


def audit_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "split": row["split"],
        "scan_id": row["scan_id"],
        "directed_pair_id": row["directed_pair_id"],
        "candidate_relation_text": row["candidate_relation_text"],
        "official_gt_axis": row["official_gt_axis"],
        "audit_axis": row["audit_axis"],
        "counterfactual_axis": row["counterfactual_axis"],
        "observability_axis": row["observability_axis"],
        "reliability_eval_axis": row["reliability_eval_axis"],
        "hidden_control": row["hidden_control"],
    }


def source_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "split": row["split"],
        "source_dataset": row["source_dataset"],
        "relation_source": row["relation_source"],
        "candidate_relation_text": row["candidate_relation_text"],
        "scan_id": row["scan_id"],
        "subject_instance_id": row["subject_instance_id"],
        "object_instance_id": row["object_instance_id"],
        "predicate_label": row["T_e"]["predicate_label"],
        "relation_family": row["T_e"]["relation_family"],
        "source_score_normalized": row["Z_e"]["source_score_normalized"],
        "source_rank": row["Z_e"]["source_rank"],
    }


def schema_payload() -> dict[str, Any]:
    return {
        "schema_version": "h002_prototype_dataset_v1_schema",
        "row_file": "prototype_rows.jsonl",
        "factor_blocks": ["T_e", "Z_e", "G_e", "Q_e"],
        "label_axes": [
            "official_gt_axis",
            "audit_axis",
            "counterfactual_axis",
            "observability_axis",
            "reliability_eval_axis",
        ],
        "model_views": [
            "compatibility_main",
            "source_only",
            "semantic_source",
            "geometry_rule",
            "semantic_x_geometry_rule",
            "obs_head",
            "full_factorized",
        ],
        "blocked_model_inputs": [
            "official_gt_axis",
            "audit_axis",
            "counterfactual_axis",
            "observability_axis",
            "reliability_eval_axis",
            "hidden_control",
        ],
        "compatibility_main_forbidden_blocks": ["Z_e"],
        "G_e_blocked_fragments": list(GEOMETRY_BLOCKED_FRAGMENTS),
    }


def validate_rows(rows: list[dict[str, Any]], groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    row_ids = set()
    for idx, row in enumerate(rows, start=1):
        row_id = row.get("row_id")
        if row_id in row_ids:
            errors.append({"error_type": "duplicate_row_id", "row_number": idx, "row_id": row_id})
        row_ids.add(row_id)
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row_id, "split": row.get("split")})
        compatibility_view = row.get("model_views", {}).get("compatibility_main", {})
        if "Z_e" in compatibility_view:
            errors.append({"error_type": "z_in_compatibility_main", "row_id": row_id})
        for key in row.get("G_e", {}).get("geometry_features", {}):
            lowered = key.lower()
            for fragment in GEOMETRY_BLOCKED_FRAGMENTS:
                if fragment in lowered:
                    errors.append({"error_type": "blocked_geometry_feature", "row_id": row_id, "feature": key, "fragment": fragment})
                    break
        gt_status = row.get("official_gt_axis", {}).get("gt_match_status")
        comp_label = row.get("counterfactual_axis", {}).get("compatibility_label")
        neg_tier = row.get("counterfactual_axis", {}).get("negative_tier")
        if gt_status == "no_gt_for_pair" and comp_label == "counterfactual_negative" and neg_tier == "none":
            errors.append({"error_type": "no_gt_as_negative_without_tier", "row_id": row_id})
    group_ids = set()
    for group in groups:
        group_id = group.get("group_id")
        if group_id in group_ids:
            errors.append({"error_type": "duplicate_group_id", "group_id": group_id})
        group_ids.add(group_id)
        if group.get("anchor_row_id") not in row_ids:
            errors.append({"error_type": "group_anchor_missing", "group_id": group_id})
        for cf_id in group.get("counterfactual_row_ids", []):
            if cf_id not in row_ids:
                errors.append({"error_type": "group_counterfactual_missing", "group_id": group_id, "row_id": cf_id})
    return errors


def count_dict(rows: list[dict[str, Any]], getter) -> dict[str, int]:
    return dict(sorted(Counter(str(getter(row)) for row in rows).items()))


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Prototype Dataset Materialization V1",
        "",
        f"Date: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        f"- prototype rows: `{summary['counts']['prototype_rows']}`",
        f"- counterfactual groups: `{summary['counts']['counterfactual_groups']}`",
        f"- validation errors: `{summary['counts']['validation_errors']}`",
        "",
        "## Label Counts",
        "",
        f"- compatibility: `{summary['counts']['compatibility_label']}`",
        f"- reliability: `{summary['counts']['reliability_label']}`",
        f"- observability: `{summary['counts']['observability_label']}`",
        "",
        "## Boundary",
        "",
        "- train-only materialization",
        "- no validation/test rows",
        "- no model training",
        "- existing H002 artifacts are read-only inputs",
        "- H001 artifacts are not modified",
        "- attachment audit rows are reliability/observability diagnostic unless numeric `G_e` is added",
        "",
        "## Next TODO",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def materialize(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    support_rows = read_jsonl(args.support_rows)
    for idx, row in enumerate(support_rows):
        rows.append(support_row_to_prototype(row, idx))

    v20_rows = read_jsonl(args.v20_rows)
    for idx, row in enumerate(v20_rows):
        rows.append(audit_row_to_prototype(row, idx, "v20_attachment_audit"))

    v22_rows = read_jsonl(args.v22_rows)
    for idx, row in enumerate(v22_rows):
        rows.append(audit_row_to_prototype(row, idx, "v22_hanging_audit"))

    groups = assign_counterfactual_groups(rows)
    baseline_rows = [flatten_baseline(row) for row in rows]
    audit_rows = [audit_view(row) for row in rows]
    source_rows = [source_candidate(row) for row in rows]
    errors = validate_rows(rows, groups)

    summary = {
        "schema_version": "h002_prototype_dataset_materialization_v1_summary",
        "status": "h002_prototype_dataset_v1_ready" if not errors else "h002_prototype_dataset_v1_has_validation_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "support_rows": rel_path(args.support_rows),
            "v20_rows": rel_path(args.v20_rows),
            "v22_rows": rel_path(args.v22_rows),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "source_candidates": rel_path(output_dir / "source_candidates.jsonl"),
            "prototype_rows": rel_path(output_dir / "prototype_rows.jsonl"),
            "counterfactual_groups": rel_path(output_dir / "counterfactual_groups.jsonl"),
            "baseline_view": rel_path(output_dir / "baseline_view.jsonl"),
            "audit_view": rel_path(output_dir / "audit_view.jsonl"),
            "split_manifest": rel_path(output_dir / "split_manifest.json"),
            "schema": rel_path(output_dir / "schema.json"),
            "summary": rel_path(output_dir / "summary.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
            "report": rel_path(output_dir / "report.md"),
        },
        "counts": {
            "input_support_rows": len(support_rows),
            "input_v20_rows": len(v20_rows),
            "input_v22_rows": len(v22_rows),
            "prototype_rows": len(rows),
            "source_candidates": len(source_rows),
            "counterfactual_groups": len(groups),
            "baseline_rows": len(baseline_rows),
            "audit_rows": len(audit_rows),
            "validation_errors": len(errors),
            "by_family": count_dict(rows, lambda row: row["T_e"]["relation_family"]),
            "by_predicate": count_dict(rows, lambda row: row["T_e"]["predicate_label"]),
            "by_relation_source": count_dict(rows, lambda row: row["relation_source"]),
            "compatibility_label": count_dict(rows, lambda row: row["counterfactual_axis"]["compatibility_label"]),
            "positive_tier": count_dict(rows, lambda row: row["counterfactual_axis"]["positive_tier"]),
            "negative_tier": count_dict(rows, lambda row: row["counterfactual_axis"]["negative_tier"]),
            "observability_label": count_dict(rows, lambda row: row["observability_axis"]["observability_label"]),
            "reliability_label": count_dict(rows, lambda row: row["reliability_eval_axis"]["reliability_label"]),
            "geometry_feature_count": count_dict(rows, lambda row: len(row["G_e"]["geometry_features"])),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_model": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "source_artifacts_modified": False,
            "compatibility_main_uses_Z_e": False,
            "hidden_control_as_model_input": False,
        },
        "interpretation": {
            "compatibility_smoke_ready_scope": "support_contact and relative_vertical rows with numeric raw-witness G_e",
            "attachment_rows_scope": "reliability/observability diagnostic until numeric attachment G_e is materialized",
            "no_gt_policy": "no-GT rows remain unknown unless another label axis supplies a valid target",
        },
        "next_todo": "smoke_baseline_runner_v1" if not errors else "prototype_dataset_materialization_v1_repair",
    }

    split_manifest = {
        "schema_version": "h002_prototype_dataset_v1_split_manifest",
        "split": "train_only",
        "validation_usage": False,
        "test_usage": False,
        "row_count": len(rows),
        "group_count": len(groups),
        "source_input_paths": summary["input_paths"],
        "group_policy": "scan-group-compatible; counterfactual group rows must stay in the same internal fold",
    }

    write_jsonl(output_dir / "source_candidates.jsonl", source_rows)
    write_jsonl(output_dir / "prototype_rows.jsonl", rows)
    write_jsonl(output_dir / "counterfactual_groups.jsonl", groups)
    write_jsonl(output_dir / "baseline_view.jsonl", baseline_rows)
    write_jsonl(output_dir / "audit_view.jsonl", audit_rows)
    write_json(output_dir / "split_manifest.json", split_manifest)
    write_json(output_dir / "schema.json", schema_payload())
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    summary = materialize(parse_args())
    print(
        "status={status} rows={rows} groups={groups} compatibility={compatibility} "
        "validation_errors={errors} next={next_todo}".format(
            status=summary["status"],
            rows=summary["counts"]["prototype_rows"],
            groups=summary["counts"]["counterfactual_groups"],
            compatibility=summary["counts"]["compatibility_label"],
            errors=summary["counts"]["validation_errors"],
            next_todo=summary["next_todo"],
        )
    )
    return 0 if summary["counts"]["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
