#!/usr/bin/env python3
"""Materialize numeric attachment geometry evidence for H002.

This hypothesis-stage runner reads the train-only v18 attachment-deferred
ingestion artifact, extracts only predicate-independent numeric geometry from
the locked hidden raw-feature block, and writes a separate artifact root. It
does not modify prototype_dataset_v1 or any upstream target artifact.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H002_ROOT.parents[2]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_INPUT_ROWS = (
    RGA_ROOT
    / "reliability_target_v18_attachment_deferred_label_ingestion"
    / "ingested_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/attachment_numeric_geometry_v1"

GEOMETRY_ALLOWED_RAW_KEYS = (
    "center_delta_z",
    "normalized_center_delta_z",
    "normalized_distance_3d",
    "normalized_distance_xy",
    "projected_iou_xy",
    "projected_subject_overlap_ratio",
    "projected_object_overlap_ratio",
    "vertical_gap_subject_on_object",
    "near_contact",
    "loose_near_contact",
    "far_separated",
    "projected_overlap_support",
)

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
    "machine",
    "hint",
    "cell",
    "review",
    "reason",
    "witness_score",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
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
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def bool_float(value: Any) -> float:
    return 1.0 if value is True else 0.0


def closeness(value: float | None) -> float:
    if value is None:
        return 0.0
    return 1.0 / (1.0 + max(abs(value), 0.0))


def source_rank_band(rank: Any) -> str:
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
    if rank_value <= 1000:
        return "rank_501_1000"
    return "rank_over_1000"


def make_t_block(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "predicate_label": row.get("predicate_label"),
        "predicate_text": row.get("predicate_label"),
        "relation_family": row.get("predicate_family", "attachment_deferred"),
        "subject_label": row.get("subject_label"),
        "object_label": row.get("object_label"),
        "subject_object_text": f"{row.get('subject_label')} [REL] {row.get('object_label')}",
        "predicate_embedding_id": None,
        "subject_class_embedding_id": None,
        "object_class_embedding_id": None,
    }


def make_z_block(row: dict[str, Any]) -> dict[str, Any]:
    rank = safe_float(row.get("semantic_rank_hidden"))
    score = safe_float(row.get("semantic_score_norm_hidden"))
    return {
        "source_id": row.get("source_id", "open3dsg_train_full"),
        "source_score_raw": None,
        "source_score_normalized": score,
        "source_rank": rank,
        "source_rank_band": source_rank_band(rank),
        "source_score_available": score is not None,
    }


def attachment_geometry_features(row: dict[str, Any]) -> tuple[dict[str, float], dict[str, bool]]:
    raw = row.get("raw_features_hidden") or {}
    features: dict[str, float] = {}
    mask: dict[str, bool] = {}
    for key in GEOMETRY_ALLOWED_RAW_KEYS:
        raw_value = raw.get(key)
        value = safe_float(raw_value)
        if value is None:
            mask[key] = False
            continue
        out_key = "projected_overlap_indicator" if key == "projected_overlap_support" else key
        features[out_key] = value
        mask[out_key] = True

    d3 = safe_float(raw.get("normalized_distance_3d"))
    dxy = safe_float(raw.get("normalized_distance_xy"))
    dz = safe_float(raw.get("normalized_center_delta_z"))
    gap = safe_float(raw.get("vertical_gap_subject_on_object"))
    subject_overlap = safe_float(raw.get("projected_subject_overlap_ratio"), 0.0) or 0.0
    object_overlap = safe_float(raw.get("projected_object_overlap_ratio"), 0.0) or 0.0
    iou = safe_float(raw.get("projected_iou_xy"), 0.0) or 0.0

    derived = {
        "distance_closeness_3d": closeness(d3),
        "distance_closeness_xy": closeness(dxy),
        "abs_normalized_center_delta_z": abs(dz) if dz is not None else 0.0,
        "vertical_gap_abs": abs(gap) if gap is not None else 0.0,
        "vertical_gap_closeness": closeness(gap),
        "overlap_max_ratio": max(subject_overlap, object_overlap, iou),
        "overlap_min_subject_object_ratio": min(subject_overlap, object_overlap),
        "near_contact_indicator": bool_float(raw.get("near_contact")),
        "loose_near_contact_indicator": bool_float(raw.get("loose_near_contact")),
        "far_separated_indicator": bool_float(raw.get("far_separated")),
    }
    features.update(derived)
    mask.update({key: True for key in derived})
    return features, mask


def make_g_block(row: dict[str, Any]) -> dict[str, Any]:
    features, mask = attachment_geometry_features(row)
    return {
        "geometry_features": features,
        "geometry_feature_mask": mask,
        "geometry_feature_units": {
            "center_delta_z": "meters_or_dataset_coordinate_units",
            "vertical_gap_subject_on_object": "meters_or_dataset_coordinate_units",
            "normalized_distance_3d": "scale_normalized",
            "normalized_distance_xy": "scale_normalized",
            "normalized_center_delta_z": "scale_normalized",
            "projected_iou_xy": "ratio_0_1",
            "projected_subject_overlap_ratio": "ratio_0_1",
            "projected_object_overlap_ratio": "ratio_0_1",
        },
        "geometry_normalization": "v18_attachment_raw_pair_features_scale_normalized",
        "geometry_source": "v18_raw_features_hidden_geometry_only",
    }


def make_q_block(row: dict[str, Any]) -> dict[str, Any]:
    coverage = str(row.get("coverage_state_v18") or "unknown")
    raw_state = str(row.get("raw_feature_join_state_hidden") or "unknown")
    uncertainty_flags = row.get("uncertainty_flags_hidden") or []
    if not isinstance(uncertainty_flags, list):
        uncertainty_flags = [str(uncertainty_flags)]
    uncertainty_reason = str(row.get("uncertainty_reason_v18") or "unknown")
    return {
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
        "low_coverage_flag": coverage != "sufficient",
        "missing_geometry_flag": raw_state != "joined",
        "unsupported_family_flag": row.get("predicate_label") == "connected to",
        "evidence_conflict_flag": "mixed_3d_cues" in uncertainty_flags or uncertainty_reason == "mixed_3d_cues",
        "asset_tier": "numeric_3d_pair_geometry_only",
        "coverage_features": {
            "raw_feature_joined": 1.0 if raw_state == "joined" else 0.0,
            "coverage_sufficient": 1.0 if coverage == "sufficient" else 0.0,
            "coverage_limited": 1.0 if coverage == "limited" else 0.0,
            "uncertainty_flag_count": float(len(uncertainty_flags)),
            "uncertainty_none": 1.0 if uncertainty_reason == "none" else 0.0,
            "uncertainty_large_box_overlap": 1.0 if uncertainty_reason == "large_box_overlap" else 0.0,
            "uncertainty_thin_structure_missing": 1.0 if uncertainty_reason == "thin_structure_missing" else 0.0,
            "uncertainty_functional_connection_needs_visual": 1.0
            if uncertainty_reason == "functional_connection_needs_visual"
            else 0.0,
            "uncertainty_support_contact_confound": 1.0 if uncertainty_reason == "support_contact_confound" else 0.0,
        },
    }


def reliability_label(row: dict[str, Any]) -> str:
    value = str(row.get("relation_reliability_multiclass_target") or "")
    if value == "accept_reliable_attachment":
        return "accept"
    if value == "reject_unreliable_attachment":
        return "reject"
    if value == "abstain_uncertain":
        return "abstain"
    if value == "diagnostic_connected_possible":
        return "diagnostic_connected_possible"
    if value == "diagnostic_connected_ambiguous":
        return "diagnostic_connected_ambiguous"
    return "unavailable"


def compatibility_label(row: dict[str, Any]) -> tuple[str, str]:
    predicate = row.get("predicate_label")
    usable = bool(row.get("geometry_support_binary_usable"))
    target = row.get("geometry_support_binary_target")
    if predicate == "connected to":
        return "unknown", "none"
    if usable and target == 1:
        return "positive", "P1_geometry_support"
    if usable and target == 0:
        return "counterfactual_negative", "N1_geometry_contradiction"
    return "unknown", "none"


def row_to_materialized(row: dict[str, Any], index: int) -> dict[str, Any]:
    row_id = f"h002_attach_num_v1_{index:06d}"
    t_block = make_t_block(row)
    z_block = make_z_block(row)
    g_block = make_g_block(row)
    q_block = make_q_block(row)
    comp_label, tier = compatibility_label(row)
    rel_label = reliability_label(row)
    return {
        "schema_version": "h002_attachment_numeric_geometry_v1_row",
        "row_id": row_id,
        "group_id": None,
        "row_role": "attachment_numeric_geometry_candidate",
        "split": row.get("split"),
        "source_dataset": "Open3DSG_train",
        "relation_source": "v18_attachment_deferred_label_ingestion",
        "scan_id": row.get("scan_id"),
        "scene_id": row.get("scan_id"),
        "subject_instance_id": row.get("subject_id"),
        "object_instance_id": row.get("object_id"),
        "directed_pair_id": row.get("directed_pair_id_hidden"),
        "candidate_relation_text": f"{row.get('subject_label')} {row.get('predicate_label')} {row.get('object_label')}",
        "T_e": t_block,
        "Z_e": z_block,
        "G_e": g_block,
        "Q_e": q_block,
        "p_geom_valid_baseline": None,
        "geometry_status_baseline": None,
        "official_gt_axis": {
            "gt_match_status": row.get("label_match_status_hidden", "unavailable"),
            "gt_predicates_for_pair": row.get("matched_predicates_hidden") or [],
            "gt_family_for_pair": [],
            "gt_source": "direct_join_relationships_train_full",
            "gt_used_as_model_input": False,
        },
        "audit_axis": {
            "audit_label": row.get("relation_reliability_multiclass_target"),
            "geometry_support_label": row.get("geometry_support_state_v18"),
            "geometry_support_binary_target": row.get("geometry_support_binary_target"),
            "connected_diagnostic_target": row.get("connected_diagnostic_target"),
            "coverage_state": row.get("coverage_state_v18"),
            "uncertainty_reason": row.get("uncertainty_reason_v18"),
            "audit_provenance": row.get("label_source"),
            "audit_hidden_fields_exposed": False,
        },
        "counterfactual_axis": {
            "compatibility_label": comp_label,
            "positive_tier": tier if comp_label == "positive" else "none",
            "negative_tier": tier if comp_label == "counterfactual_negative" else "none",
            "counterfactual_type": "geometry_support_binary_attachment" if comp_label != "unknown" else "none",
            "anchor_row_id": None,
            "matching_fields": ["predicate_label", "numeric_attachment_geometry_available"],
            "relaxed_matching_fields": ["relation_family"],
        },
        "observability_axis": {
            "observability_label": "observable" if row.get("coverage_state_v18") == "sufficient" else "limited",
            "observability_reason": row.get("coverage_state_v18") or "unknown",
            "p_obs_target_usable": True,
        },
        "reliability_eval_axis": {
            "reliability_label": rel_label,
            "native_reliability_label": row.get("relation_reliability_multiclass_target"),
            "label_source": row.get("label_source"),
            "binary_usable": rel_label in {"accept", "reject"},
            "multiclass_usable": rel_label
            in {"accept", "reject", "abstain", "diagnostic_connected_possible", "diagnostic_connected_ambiguous"},
        },
        "model_views": {
            "compatibility_main": {"T_e": t_block, "G_e": g_block},
            "source_only": {"Z_e": z_block},
            "semantic_source": {"T_e": t_block, "Z_e": z_block},
            "geometry_only": {"G_e": g_block},
            "obs_head": {"Q_e": q_block},
            "full_factorized": {"Z_e": z_block, "Q_e": q_block, "C_e_input": {"T_e": t_block, "G_e": g_block}},
        },
        "hidden_control": {
            "blind_review_id": row.get("blind_review_id"),
            "prediction_id": row.get("prediction_id"),
            "cell_id_hidden": row.get("cell_id_hidden"),
            "machine_hint_hidden": row.get("machine_hint_hidden"),
            "geometry_status_hidden": row.get("geometry_status_hidden"),
            "provisional_status_hidden": row.get("provisional_status_hidden"),
            "reason_family_hidden": row.get("reason_family_hidden"),
            "rank_band_hidden": row.get("rank_band_hidden"),
            "bucket_top100_hidden": row.get("bucket_top100_hidden"),
            "attachment_witness_support_score_hidden": row.get("attachment_witness_support_score_hidden"),
            "attachment_witness_contradiction_score_hidden": row.get("attachment_witness_contradiction_score_hidden"),
            "raw_feature_join_state_hidden": row.get("raw_feature_join_state_hidden"),
            "source_geometry_family_hidden": row.get("source_geometry_family_hidden"),
            "source_geometry_predicate_hidden": row.get("source_geometry_predicate_hidden"),
        },
    }


def assign_counterfactual_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positives_by_predicate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    negatives_by_predicate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        predicate = str(row["T_e"]["predicate_label"])
        label = row["counterfactual_axis"]["compatibility_label"]
        if label == "positive":
            positives_by_predicate[predicate].append(row)
        elif label == "counterfactual_negative":
            negatives_by_predicate[predicate].append(row)
    groups: list[dict[str, Any]] = []
    group_index = 0
    used: dict[str, int] = defaultdict(int)
    for predicate, positives in sorted(positives_by_predicate.items()):
        negatives = negatives_by_predicate.get(predicate, [])
        if not negatives:
            continue
        for positive in positives:
            negative = negatives[used[predicate] % len(negatives)]
            used[predicate] += 1
            group_id = f"h002_attach_num_v1_group_{group_index:06d}"
            group_index += 1
            positive["group_id"] = group_id
            negative["group_id"] = negative["group_id"] or group_id
            negative["counterfactual_axis"]["anchor_row_id"] = positive["row_id"]
            groups.append(
                {
                    "group_id": group_id,
                    "anchor_row_id": positive["row_id"],
                    "anchor_positive_tier": positive["counterfactual_axis"]["positive_tier"],
                    "counterfactual_row_ids": [negative["row_id"]],
                    "negative_tiers_present": [negative["counterfactual_axis"]["negative_tier"]],
                    "matching_fields": {
                        "split": "train",
                        "predicate_label": predicate,
                        "relation_family": "attachment_deferred",
                        "numeric_attachment_geometry_available": True,
                    },
                }
            )
    return groups


def baseline_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "predicate_label": row["T_e"]["predicate_label"],
        "relation_family": row["T_e"]["relation_family"],
        "source_score_normalized": row["Z_e"]["source_score_normalized"],
        "source_rank": row["Z_e"]["source_rank"],
        "source_rank_band": row["Z_e"]["source_rank_band"],
        "geometry_feature_count": len(row["G_e"]["geometry_features"]),
        "compatibility_label": row["counterfactual_axis"]["compatibility_label"],
        "reliability_label": row["reliability_eval_axis"]["reliability_label"],
        "observability_label": row["observability_axis"]["observability_label"],
        "raw_feature_joined": row["Q_e"]["coverage_features"]["raw_feature_joined"],
    }


def audit_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "candidate_relation_text": row["candidate_relation_text"],
        "scan_id": row["scan_id"],
        "directed_pair_id": row["directed_pair_id"],
        "official_gt_axis": row["official_gt_axis"],
        "audit_axis": row["audit_axis"],
        "counterfactual_axis": row["counterfactual_axis"],
        "observability_axis": row["observability_axis"],
        "reliability_eval_axis": row["reliability_eval_axis"],
        "hidden_control": row["hidden_control"],
    }


def validate_rows(rows: list[dict[str, Any]], groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    row_ids = set()
    group_row_ids = set()
    for idx, row in enumerate(rows, start=1):
        row_id = row.get("row_id")
        if row_id in row_ids:
            errors.append({"error_type": "duplicate_row_id", "row_id": row_id})
        row_ids.add(row_id)
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row_id, "split": row.get("split")})
        if "Z_e" in row.get("model_views", {}).get("compatibility_main", {}):
            errors.append({"error_type": "z_in_compatibility_main", "row_id": row_id})
        for feature in row.get("G_e", {}).get("geometry_features", {}):
            lowered = feature.lower()
            for fragment in GEOMETRY_BLOCKED_FRAGMENTS:
                if fragment in lowered:
                    errors.append(
                        {
                            "error_type": "blocked_geometry_feature_name",
                            "row_id": row_id,
                            "feature": feature,
                            "fragment": fragment,
                        }
                    )
                    break
    for group in groups:
        for key in ["anchor_row_id", *group.get("counterfactual_row_ids", [])]:
            value = group["anchor_row_id"] if key == "anchor_row_id" else key
            if value not in row_ids:
                errors.append({"error_type": "group_references_missing_row", "group_id": group["group_id"], "row_id": value})
            group_row_ids.add(value)
    return errors


def count_by(rows: list[dict[str, Any]], getter: Any) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[str(getter(row))] += 1
    return dict(sorted(counts.items()))


def write_report(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# H002 Attachment Numeric Geometry V1

Date: {summary['created_at']}

## Status

`{summary['status']}`

## Input

```text
{summary['input_rows']}
```

## Counts

```text
rows = {summary['counts']['rows']}
numeric_g_rows = {summary['counts']['numeric_g_rows']}
compatibility_binary_rows = {summary['counts']['compatibility_binary_rows']}
compatibility_positive = {summary['counts']['compatibility_positive']}
compatibility_negative = {summary['counts']['compatibility_negative']}
counterfactual_groups = {summary['counts']['counterfactual_groups']}
validation_errors = {summary['counts']['validation_errors']}
```

## Predicate Counts

```json
{json.dumps(summary['predicate_counts'], ensure_ascii=False, indent=2, sort_keys=True)}
```

## Compatibility Counts By Predicate

```json
{json.dumps(summary['compatibility_counts_by_predicate'], ensure_ascii=False, indent=2, sort_keys=True)}
```

## Boundary

- train-only hypothesis artifact;
- no validation/test usage;
- no paper-level evidence;
- raw numeric geometry features are used from the locked v18 raw feature block;
- source score/rank, cell id, machine hint, geometry status, witness score, and label fields are excluded from `G_e`;
- `connected to` is materialized as numeric geometry diagnostic, not binary compatibility training.

## Next TODO

`{summary['next_todo']}`
"""
    path.write_text(text, encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_rows = args.input_rows
    output_dir = args.output_dir
    source_rows = read_jsonl(input_rows)
    rows = [row_to_materialized(row, idx) for idx, row in enumerate(source_rows)]
    groups = assign_counterfactual_groups(rows)
    errors = validate_rows(rows, groups)

    compatibility_rows = [
        row for row in rows if row["counterfactual_axis"]["compatibility_label"] in {"positive", "counterfactual_negative"}
    ]
    connected_rows = [row for row in rows if row["T_e"]["predicate_label"] == "connected to"]
    summary = {
        "schema_version": "h002_attachment_numeric_geometry_v1_summary",
        "status": "h002_attachment_numeric_geometry_v1_ready" if not errors else "h002_attachment_numeric_geometry_v1_input_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_rows": rel_path(input_rows),
        "output_dir": rel_path(output_dir),
        "counts": {
            "source_rows": len(source_rows),
            "rows": len(rows),
            "numeric_g_rows": sum(1 for row in rows if row["G_e"]["geometry_features"]),
            "compatibility_binary_rows": len(compatibility_rows),
            "compatibility_positive": sum(1 for row in compatibility_rows if row["counterfactual_axis"]["compatibility_label"] == "positive"),
            "compatibility_negative": sum(
                1 for row in compatibility_rows if row["counterfactual_axis"]["compatibility_label"] == "counterfactual_negative"
            ),
            "connected_diagnostic_rows": len(connected_rows),
            "counterfactual_groups": len(groups),
            "validation_errors": len(errors),
        },
        "predicate_counts": count_by(rows, lambda row: row["T_e"]["predicate_label"]),
        "compatibility_counts_by_predicate": {
            predicate: dict(Counter(row["counterfactual_axis"]["compatibility_label"] for row in rows if row["T_e"]["predicate_label"] == predicate))
            for predicate in sorted({str(row["T_e"]["predicate_label"]) for row in rows})
        },
        "reliability_counts": count_by(rows, lambda row: row["reliability_eval_axis"]["reliability_label"]),
        "observability_counts": count_by(rows, lambda row: row["observability_axis"]["observability_label"]),
        "geometry_feature_keys": sorted({key for row in rows for key in row["G_e"]["geometry_features"]}),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "modifies_upstream_artifacts": False,
            "connected_to_binary_compatibility": False,
        },
        "next_todo": "attachment_numeric_geometry_smoke_v1" if not errors else "attachment_numeric_geometry_v1_error_analysis",
    }

    write_jsonl(output_dir / "attachment_rows.jsonl", rows)
    write_jsonl(output_dir / "compatibility_rows.jsonl", compatibility_rows)
    write_jsonl(output_dir / "diagnostic_connected_rows.jsonl", connected_rows)
    write_jsonl(output_dir / "counterfactual_groups.jsonl", groups)
    write_jsonl(output_dir / "baseline_view.jsonl", [baseline_view(row) for row in rows])
    write_jsonl(output_dir / "audit_view.jsonl", [audit_view(row) for row in rows])
    write_json(output_dir / "summary.json", summary)
    write_json(
        output_dir / "schema.json",
        {
            "schema_version": "h002_attachment_numeric_geometry_v1_schema",
            "row_file": "attachment_rows.jsonl",
            "compatibility_file": "compatibility_rows.jsonl",
            "factor_blocks": ["T_e", "Z_e", "G_e", "Q_e"],
            "compatibility_main_forbidden_blocks": ["Z_e"],
            "G_e_allowed_raw_keys": list(GEOMETRY_ALLOWED_RAW_KEYS),
            "G_e_blocked_fragments": list(GEOMETRY_BLOCKED_FRAGMENTS),
            "blocked_model_inputs": ["official_gt_axis", "audit_axis", "counterfactual_axis", "observability_axis", "reliability_eval_axis", "hidden_control"],
        },
    )
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        "status={status} rows={rows} compat={compat} pos={pos} neg={neg} groups={groups} "
        "errors={errors} next={next}".format(
            status=summary["status"],
            rows=summary["counts"]["rows"],
            compat=summary["counts"]["compatibility_binary_rows"],
            pos=summary["counts"]["compatibility_positive"],
            neg=summary["counts"]["compatibility_negative"],
            groups=summary["counts"]["counterfactual_groups"],
            errors=summary["counts"]["validation_errors"],
            next=summary["next_todo"],
        )
    )
    return 0 if summary["counts"]["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
