#!/usr/bin/env python3
"""Materialize exact-stratum repaired H002 independent-validity candidate rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
RGA_ROOT = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PLAN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan"
)
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan_ready"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization_v1"
ROW_SCHEMA_VERSION = "h002_exact_stratum_repaired_independent_validity_row_v1"
MODEL_VIEW_SCHEMA = "h002_exact_stratum_repaired_independent_validity_model_safe_view_v1"
DATASET_NAME = "h002_exact_stratum_repaired_independent_validity_candidates_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization_ready_for_schema_shortcut_audit"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization_input_errors"
)
NEXT_TODO = "compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit"

PRIMARY_FAMILY_PREDICATES = {
    "relative_vertical": {"higher than", "lower than"},
    "support_contact_pose_conditioned": {"standing on", "lying on"},
}
RAW_MATCH_FAMILY_TO_TARGET = {
    "relative_vertical": "relative_vertical",
    "support_contact": "support_contact_pose_conditioned",
}
TARGET_PRIMARY_ROWS = 1600
TARGET_PER_LABEL = 800
MIN_RETAINED_EXACT_STRATA = 30
SCAN_CAP_SHARE = 0.08
RANK_BAND_ORDER = {
    "top20": 0,
    "top50": 1,
    "top100": 2,
    "top100_only": 2,
    "rank_101_200": 3,
    "rank_101_500": 4,
    "rank_201_500": 4,
    "rank_501_1000": 5,
    "rank_gt1000": 6,
    "rank_unknown": 7,
}
FORBIDDEN_MODEL_KEYS = {
    "controls_hidden",
    "directed_pair_id",
    "geometry_axis",
    "geometry_residual_proxy",
    "geometry_status",
    "label_match_status",
    "matched_gt_ids",
    "matched_predicates",
    "object_id",
    "p_geom_valid",
    "prediction_id",
    "provenance",
    "scan_id",
    "scope_role",
    "selection_pass",
    "source_line_no",
    "subject_id",
    "subgraph_id",
    "target_pool",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_quota_plan(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("materialize", "")).lower() != "true":
                continue
            out = dict(row)
            for key in [
                "available_positive",
                "available_negative",
                "raw_balanced_capacity_rows",
                "scan_capped_capacity_rows",
                "positive_scans",
                "negative_scans",
                "available_balanced_pairs_after_scan_cap",
                "max_pairs_per_stratum",
                "eligible_pairs_after_plan_cap",
                "target_positive_quota",
                "target_negative_quota",
                "target_total_rows",
                "selection_order",
            ]:
                out[key] = int(out[key])
            rows.append(out)
    return rows


def stable_hash(payload: Any, length: int = 20) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def safe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def norm_text(value: Any) -> str:
    return str(value or "").strip()


def target_family(row: dict[str, Any]) -> str | None:
    predicate = row.get("predicate", {})
    raw_family = str(predicate.get("predicate_family"))
    label = str(predicate.get("predicate_label"))
    family = RAW_MATCH_FAMILY_TO_TARGET.get(raw_family)
    if family is None:
        return None
    if label not in PRIMARY_FAMILY_PREDICATES[family]:
        return None
    return family


def primary_label(row: dict[str, Any]) -> int | None:
    label_status = row.get("label", {}).get("label_match_status")
    geometry_status = row.get("geometry", {}).get("geometry_status")
    if label_status == "exact_match" and geometry_status == "satisfied":
        return 1
    if label_status in {"family_match", "pair_has_other_predicate"} and geometry_status == "unsatisfied":
        return 0
    return None


def row_stratum_key(row: dict[str, Any]) -> tuple[str, str, str]:
    edge = row.get("edge", {})
    predicate = row.get("predicate", {})
    return (
        norm_text(predicate.get("predicate_label")),
        norm_text(edge.get("subject_label")),
        norm_text(edge.get("object_label")),
    )


def quota_stratum_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        norm_text(row["predicate_label"]),
        norm_text(row["subject_class_label"]),
        norm_text(row["object_class_label"]),
    )


def has_source_z(row: dict[str, Any]) -> bool:
    semantic = row.get("semantic", {})
    return (
        semantic.get("semantic_score_raw") is not None
        and semantic.get("semantic_score_norm") is not None
        and semantic.get("rank_in_context") is not None
    )


def has_raw_g(row: dict[str, Any]) -> bool:
    geometry = row.get("geometry", {})
    return bool(geometry.get("geometry_checkable") is True and isinstance(geometry.get("raw_features"), dict))


def rank_band(row: dict[str, Any]) -> str:
    rga = row.get("rga", {})
    if rga.get("rank_band"):
        return str(rga["rank_band"])
    rank = safe_int(row.get("semantic", {}).get("rank_in_context"))
    if rank is None:
        return "rank_unknown"
    if rank <= 20:
        return "top20"
    if rank <= 50:
        return "top50"
    if rank <= 100:
        return "top100"
    if rank <= 200:
        return "rank_101_200"
    if rank <= 500:
        return "rank_201_500"
    if rank <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def scan_id(row: dict[str, Any]) -> str:
    return str(row.get("identity", {}).get("scan_id"))


def visible_pair(row: dict[str, Any]) -> str:
    edge = row.get("edge", {})
    return f"{norm_text(edge.get('subject_label')).lower()} [REL] {norm_text(edge.get('object_label')).lower()}"


def raw_geometry_feature_vector(row: dict[str, Any]) -> dict[str, float | None]:
    raw = row.get("geometry", {}).get("raw_features")
    if not isinstance(raw, dict):
        return {}
    return {str(key): safe_float(value) for key, value in sorted(raw.items())}


def geometry_feature_groups(raw_g: dict[str, float | None]) -> dict[str, dict[str, float | None] | dict[str, bool]]:
    distance: dict[str, float | None] = {}
    height: dict[str, float | None] = {}
    overlap: dict[str, float | None] = {}
    contact: dict[str, float | None] = {}
    size_pose: dict[str, float | None] = {}
    for key, value in raw_g.items():
        lower = key.lower()
        if "distance" in lower:
            distance[key] = value
        if any(token in lower for token in ["z", "top", "bottom", "vertical", "height"]):
            height[key] = value
        if any(token in lower for token in ["overlap", "iou"]):
            overlap[key] = value
        if any(token in lower for token in ["gap", "contact", "support"]):
            contact[key] = value
        if any(token in lower for token in ["extent", "size", "axis", "pose", "center_delta"]):
            size_pose[key] = value
    return {
        "raw_distance_features": distance,
        "raw_height_features": height,
        "raw_overlap_features": overlap,
        "raw_contact_or_gap_features": contact,
        "raw_object_size_features": size_pose,
        "raw_pair_pose_features": size_pose,
        "raw_geometry_feature_available_mask": {key: value is not None for key, value in raw_g.items()},
        "raw_geometry_feature_vector": raw_g,
    }


def cv_group_id(row: dict[str, Any]) -> str:
    identity = row.get("identity", {})
    payload = {
        "scan_id": identity.get("scan_id"),
        "directed_pair_id": identity.get("directed_pair_id"),
    }
    return f"cv_train_{stable_hash(payload, 16)}"


def validate_plan(plan: dict[str, Any], plan_dir: Path, match_rows: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan.get("status")})
    if plan.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan.get("next_todo")})
    if plan.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan.get("validation_errors")})
    boundary = plan.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("materializes_rows") is not False:
        errors.append({"error_type": "upstream_plan_already_materialized_rows"})
    for name in ["stratum_quota_plan.csv", "row_schema_contract.json", "matching_policy.json"]:
        path = plan_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_plan_artifact", "path": rel_path(path)})
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def validate_quotas(quotas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(quotas) < MIN_RETAINED_EXACT_STRATA:
        errors.append({"error_type": "quota_retained_strata_below_minimum", "actual": len(quotas)})
    total_pos = sum(int(row["target_positive_quota"]) for row in quotas)
    total_neg = sum(int(row["target_negative_quota"]) for row in quotas)
    if total_pos != TARGET_PER_LABEL or total_neg != TARGET_PER_LABEL:
        errors.append({"error_type": "quota_label_totals_unexpected", "positive": total_pos, "negative": total_neg})
    if total_pos + total_neg != TARGET_PRIMARY_ROWS:
        errors.append({"error_type": "quota_total_unexpected", "actual": total_pos + total_neg})
    for row in quotas:
        if row["target_positive_quota"] != row["target_negative_quota"]:
            errors.append({"error_type": "quota_stratum_not_balanced", "stratum_id": row["stratum_id"]})
        if row["target_positive_quota"] > row["available_positive"]:
            errors.append({"error_type": "positive_quota_exceeds_available", "stratum_id": row["stratum_id"]})
        if row["target_negative_quota"] > row["available_negative"]:
            errors.append({"error_type": "negative_quota_exceeds_available", "stratum_id": row["stratum_id"]})
    return errors


def collect_candidate_pools(
    match_rows: Path,
    quota_rows: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str, str], dict[int, list[dict[str, Any]]]], dict[str, Any]]:
    quota_keys = {quota_stratum_key(row) for row in quota_rows}
    pools: dict[tuple[str, str, str], dict[int, list[dict[str, Any]]]] = {
        key: {1: [], 0: []} for key in quota_keys
    }
    skip_counts: Counter[str] = Counter()
    selected_family_rows = 0
    primary_candidate_rows = 0
    scanned_rows = 0
    with match_rows.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            scanned_rows += 1
            row = json.loads(line)
            family = target_family(row)
            if family is None:
                continue
            selected_family_rows += 1
            key = row_stratum_key(row)
            if key not in quota_keys:
                continue
            label_y = primary_label(row)
            if label_y is None:
                skip_counts["not_primary_label_policy"] += 1
                continue
            if not has_source_z(row):
                skip_counts["missing_source_z"] += 1
                continue
            if not has_raw_g(row):
                skip_counts["missing_raw_g"] += 1
                continue
            primary_candidate_rows += 1
            row["_source_line_no"] = line_no
            row["_target_family"] = family
            row["_label_y"] = label_y
            pools[key][label_y].append(row)
    stats = {
        "scanned_rows": scanned_rows,
        "selected_family_rows": selected_family_rows,
        "candidate_rows_in_quota_strata": primary_candidate_rows,
        "skip_counts": dict(skip_counts),
    }
    return pools, stats


def candidate_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    semantic = row.get("semantic", {})
    identity = row.get("identity", {})
    rb = rank_band(row)
    return (
        RANK_BAND_ORDER.get(rb, 99),
        scan_id(row),
        safe_int(semantic.get("rank_in_context")) or 10**9,
        str(identity.get("directed_pair_id")),
        str(identity.get("prediction_id")),
    )


def select_with_scan_cap(candidates: list[dict[str, Any]], quota: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sorted_rows = sorted(candidates, key=candidate_sort_key)
    cap = max(1, int(quota * SCAN_CAP_SHARE))
    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    scan_counts: Counter[str] = Counter()
    for row in sorted_rows:
        sid = scan_id(row)
        if scan_counts[sid] >= cap:
            continue
        selected.append(row)
        used_ids.add(str(row.get("identity", {}).get("prediction_id")))
        scan_counts[sid] += 1
        if len(selected) == quota:
            break
    relaxed_rows = 0
    if len(selected) < quota:
        for row in sorted_rows:
            prediction_id = str(row.get("identity", {}).get("prediction_id"))
            if prediction_id in used_ids:
                continue
            selected.append(row)
            used_ids.add(prediction_id)
            relaxed_rows += 1
            if len(selected) == quota:
                break
    stats = {
        "available": len(candidates),
        "quota": quota,
        "scan_cap_per_label": cap,
        "strict_scan_cap_selected": quota - relaxed_rows if len(selected) == quota else len(selected) - relaxed_rows,
        "relaxed_scan_cap_selected": relaxed_rows,
        "scan_cap_relaxation_used": relaxed_rows > 0,
        "unique_scans": len(set(scan_id(row) for row in selected)),
        "rank_band_counts": dict(Counter(rank_band(row) for row in selected)),
    }
    return selected, stats


def build_candidate_row(
    row: dict[str, Any],
    *,
    quota: dict[str, Any],
    label_y: int,
    label_index: int,
    global_index: int,
    selection_stats: dict[str, Any],
) -> dict[str, Any]:
    identity = row.get("identity", {})
    edge = row.get("edge", {})
    predicate = row.get("predicate", {})
    semantic = row.get("semantic", {})
    geometry = row.get("geometry", {})
    label = row.get("label", {})
    raw_g = raw_geometry_feature_vector(row)
    raw_groups = geometry_feature_groups(raw_g)
    target_role = "positive" if label_y == 1 else "negative"
    target_pool = (
        "positive_exact_gt_satisfied"
        if label_y == 1
        else "strong_negative_gt_pair_other_predicate_unsatisfied"
    )
    row_id = f"isr_{global_index:06d}_{stable_hash(identity.get('prediction_id'), 12)}"
    feature_blocks = {
        "T_e": {
            "object_class_label": edge.get("object_label"),
            "predicate_label": predicate.get("predicate_label"),
            "predicate_text": predicate.get("predicate_label"),
            "relation_family": quota["family"],
            "subject_class_label": edge.get("subject_label"),
        },
        "Z_e_safe": {
            "rank_band": rank_band(row),
            "semantic_rank": safe_int(semantic.get("rank_in_context")),
            "semantic_score_norm": safe_float(semantic.get("semantic_score_norm")),
            "semantic_score_raw": safe_float(semantic.get("semantic_score_raw")),
            "source_id": row.get("source", {}).get("source_id"),
        },
        "G_e_raw": raw_groups,
        "Q_e_safe": {
            "mesh_or_point_availability": geometry.get("geometry_source"),
            "object_pair_feature_coverage": (
                sum(value is not None for value in raw_g.values()) / len(raw_g) if raw_g else 0.0
            ),
            "raw_geometry_available": bool(raw_g),
            "raw_geometry_feature_count": len(raw_g),
        },
    }
    return {
        "row_id": row_id,
        "cv_group_id": cv_group_id(row),
        "dataset_name": DATASET_NAME,
        "schema_version": ROW_SCHEMA_VERSION,
        "split": "train",
        "family": quota["family"],
        "predicate_label": predicate.get("predicate_label"),
        "subject_class_label": edge.get("subject_label"),
        "object_class_label": edge.get("object_label"),
        "stratum_id": quota["stratum_id"],
        "target_role": target_role,
        "target_pool": target_pool,
        "feature_blocks": feature_blocks,
        "labels": {
            "C_e_validity": label_y,
            "p_obs": "observable",
            "p_rel": "accept" if label_y == 1 else "reject",
            "primary_binary": label_y,
            "primary_binary_usable": True,
        },
        "controls_hidden": {
            "directed_pair_id": identity.get("directed_pair_id"),
            "geometry_axis": row.get("rga", {}).get("geometry_axis"),
            "geometry_residual_proxy": safe_float(geometry.get("geometry_residual_proxy")),
            "geometry_status": geometry.get("geometry_status"),
            "label_index_within_stratum": label_index,
            "label_match_status": label.get("label_match_status"),
            "matched_gt_ids": label.get("matched_gt_ids", []),
            "matched_predicates": label.get("matched_predicates", []),
            "object_id": identity.get("object_id"),
            "p_geom_valid": safe_float(geometry.get("p_geom_valid")),
            "prediction_id": identity.get("prediction_id"),
            "quota_negative": quota["target_negative_quota"],
            "quota_positive": quota["target_positive_quota"],
            "scan_id": identity.get("scan_id"),
            "scope_role": quota.get("scope_role"),
            "selection_pass": quota.get("selection_pass"),
            "selection_stats": selection_stats,
            "source_line_no": row.get("_source_line_no"),
            "stratum_key": list(quota_stratum_key(quota)),
            "subject_id": identity.get("subject_id"),
            "subgraph_id": identity.get("subgraph_id"),
            "visible_pair": visible_pair(row),
        },
        "provenance_safe": {
            "materialization_schema": SCHEMA_VERSION,
            "source_split_name": row.get("source", {}).get("split_name"),
        },
        "text": {
            "triple": f"{edge.get('subject_label')} {predicate.get('predicate_label')} {edge.get('object_label')}",
        },
    }


def materialize_rows(
    pools: dict[tuple[str, str, str], dict[int, list[dict[str, Any]]]],
    quota_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    quota_audit: list[dict[str, Any]] = []
    global_index = 0
    for quota in sorted(quota_rows, key=lambda row: int(row["selection_order"])):
        key = quota_stratum_key(quota)
        for label_y, quota_key in [(1, "target_positive_quota"), (0, "target_negative_quota")]:
            quota_n = int(quota[quota_key])
            selected, stats = select_with_scan_cap(pools.get(key, {}).get(label_y, []), quota_n)
            for label_index, row in enumerate(selected, start=1):
                global_index += 1
                candidates.append(
                    build_candidate_row(
                        row,
                        quota=quota,
                        label_y=label_y,
                        label_index=label_index,
                        global_index=global_index,
                        selection_stats=stats,
                    )
                )
            quota_audit.append(
                {
                    "stratum_id": quota["stratum_id"],
                    "family": quota["family"],
                    "predicate_label": quota["predicate_label"],
                    "subject_class_label": quota["subject_class_label"],
                    "object_class_label": quota["object_class_label"],
                    "label_y": label_y,
                    "target_quota": quota_n,
                    "available_after_filters": len(pools.get(key, {}).get(label_y, [])),
                    "materialized": len(selected),
                    "deficit": quota_n - len(selected),
                    "scan_cap_per_label": stats["scan_cap_per_label"],
                    "scan_cap_relaxation_used": stats["scan_cap_relaxation_used"],
                    "unique_scans": stats["unique_scans"],
                    "rank_band_counts": json.dumps(stats["rank_band_counts"], sort_keys=True),
                    "passes": len(selected) == quota_n,
                }
            )
    return candidates, quota_audit


def model_safe_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "cv_group_id": row["cv_group_id"],
        "dataset_name": row["dataset_name"],
        "schema_version": MODEL_VIEW_SCHEMA,
        "split": row["split"],
        "family": row["family"],
        "predicate_label": row["predicate_label"],
        "subject_class_label": row["subject_class_label"],
        "object_class_label": row["object_class_label"],
        "feature_blocks": row["feature_blocks"],
        "target": row["labels"],
        "text": row["text"],
    }


def hidden_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "cv_group_id": row["cv_group_id"],
        "family": row["family"],
        "predicate_label": row["predicate_label"],
        "subject_class_label": row["subject_class_label"],
        "object_class_label": row["object_class_label"],
        "stratum_id": row["stratum_id"],
        "target_role": row["target_role"],
        "target_pool": row["target_pool"],
        "labels": row["labels"],
        "controls_hidden": row["controls_hidden"],
        "provenance_safe": row["provenance_safe"],
    }


def nested_key_hits(payload: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in forbidden:
                hits.append(key)
            hits.extend(nested_key_hits(value, forbidden))
    elif isinstance(payload, list):
        for value in payload:
            hits.extend(nested_key_hits(value, forbidden))
    return hits


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_family = Counter(row["family"] for row in rows)
    by_predicate = Counter(row["predicate_label"] for row in rows)
    by_stratum = Counter(row["stratum_id"] for row in rows)
    labels = Counter(str(row["labels"]["primary_binary"]) for row in rows)
    scan_relax_rows = sum(
        1
        for row in rows
        if row["controls_hidden"]["selection_stats"].get("scan_cap_relaxation_used") is True
    )
    return {
        "materialized_primary_rows": len(rows),
        "positive_rows": labels.get("1", 0),
        "negative_rows": labels.get("0", 0),
        "retained_exact_strata": len(by_stratum),
        "by_family": dict(sorted(by_family.items())),
        "by_predicate": dict(sorted(by_predicate.items())),
        "scan_cap_relaxation_rows": scan_relax_rows,
    }


def schema_precheck(rows: list[dict[str, Any]], model_rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_ids = [row["row_id"] for row in rows]
    labels = Counter(str(row["labels"]["primary_binary"]) for row in rows)
    stratum_balance_failures: list[str] = []
    by_stratum_label: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_stratum_label[row["stratum_id"]][str(row["labels"]["primary_binary"])] += 1
    for stratum_id, counter in by_stratum_label.items():
        if counter["0"] != counter["1"]:
            stratum_balance_failures.append(stratum_id)
    model_hidden_hits = Counter()
    feature_hidden_hits = Counter()
    for row in model_rows:
        model_hidden_hits.update(nested_key_hits(row, FORBIDDEN_MODEL_KEYS))
        feature_hidden_hits.update(nested_key_hits(row.get("feature_blocks", {}), FORBIDDEN_MODEL_KEYS))
    checks = [
        {
            "check": "row_id_unique",
            "value": len(set(row_ids)),
            "expected": len(row_ids),
            "passes": len(set(row_ids)) == len(row_ids),
        },
        {
            "check": "all_train_split",
            "value": sorted(set(row["split"] for row in rows)),
            "expected": ["train"],
            "passes": sorted(set(row["split"] for row in rows)) == ["train"],
        },
        {
            "check": "primary_row_count",
            "value": len(rows),
            "expected": TARGET_PRIMARY_ROWS,
            "passes": len(rows) == TARGET_PRIMARY_ROWS,
        },
        {
            "check": "primary_label_balance",
            "value": dict(sorted(labels.items())),
            "expected": {"0": TARGET_PER_LABEL, "1": TARGET_PER_LABEL},
            "passes": labels == Counter({"0": TARGET_PER_LABEL, "1": TARGET_PER_LABEL}),
        },
        {
            "check": "stratum_internal_balance",
            "value": len(stratum_balance_failures),
            "expected": 0,
            "passes": len(stratum_balance_failures) == 0,
            "failed_strata": stratum_balance_failures[:20],
        },
        {
            "check": "retained_exact_strata",
            "value": len(by_stratum_label),
            "expected_min": MIN_RETAINED_EXACT_STRATA,
            "passes": len(by_stratum_label) >= MIN_RETAINED_EXACT_STRATA,
        },
        {
            "check": "model_safe_view_forbidden_key_hits",
            "value": sum(model_hidden_hits.values()),
            "expected": 0,
            "passes": sum(model_hidden_hits.values()) == 0,
            "hit_keys": dict(sorted(model_hidden_hits.items())),
        },
        {
            "check": "feature_block_forbidden_key_hits",
            "value": sum(feature_hidden_hits.values()),
            "expected": 0,
            "passes": sum(feature_hidden_hits.values()) == 0,
            "hit_keys": dict(sorted(feature_hidden_hits.items())),
        },
    ]
    return {"checks": checks, "validation_passes": all(check["passes"] for check in checks)}


def schema_precheck_csv_rows(precheck: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for check in precheck["checks"]:
        rows.append(
            {
                "check": check["check"],
                "value": json.dumps(check.get("value"), ensure_ascii=False, sort_keys=True),
                "expected": json.dumps(check.get("expected", check.get("expected_min")), ensure_ascii=False, sort_keys=True),
                "passes": check["passes"],
                "detail": json.dumps({k: v for k, v in check.items() if k not in {"check", "value", "expected", "expected_min", "passes"}}, ensure_ascii=False, sort_keys=True),
            }
        )
    return rows


def build_validation_errors(
    input_errors: list[dict[str, Any]],
    quota_errors: list[dict[str, Any]],
    quota_audit: list[dict[str, Any]],
    precheck: dict[str, Any],
) -> list[dict[str, Any]]:
    errors = list(input_errors) + list(quota_errors)
    for row in quota_audit:
        if not row["passes"]:
            errors.append({"error_type": "quota_materialization_deficit", **row})
    for check in precheck["checks"]:
        if not check["passes"]:
            errors.append({"error_type": "schema_precheck_failed", **check})
    return errors


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Audit schema leakage and residual shortcuts on exact-stratum repaired independent-validity rows before any learned smoke.",
        "required_inputs": [
            "candidate_rows.jsonl",
            "model_safe_view.jsonl",
            "hidden_manifest.jsonl",
            "quota_audit.csv",
            "schema_precheck.json",
        ],
        "required_gates": [
            "model-safe view has no forbidden construction fields",
            "exact predicate-class strata remain internally balanced",
            "single-field predicate/class shortcuts are low after exact-stratum repair",
            "construction summaries remain hidden-only",
        ],
        "blocked_actions": [
            "do not run learned smoke before schema shortcut audit",
            "do not use validation/test rows",
            "do not modify H001 artifacts",
            "do not use p_geom_valid or geometry_status as model input",
        ],
    }


def build_manifest(
    *,
    plan: dict[str, Any],
    match_rows: Path,
    output_dir: Path,
    rows: list[dict[str, Any]],
    quotas: list[dict[str, Any]],
    collection_stats: dict[str, Any],
    quota_audit: list[dict[str, Any]],
    precheck: dict[str, Any],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    status = STATUS_ERROR if errors else STATUS_READY
    return {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": True,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_candidate_materialization",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_name": DATASET_NAME,
        "input_match_rows": rel_path(match_rows),
        "input_plan_status": plan.get("status"),
        "input_plan_next_todo": plan.get("next_todo"),
        "materialized_outputs": {
            "candidate_rows": rel_path(output_dir / "candidate_rows.jsonl"),
            "hidden_manifest": rel_path(output_dir / "hidden_manifest.jsonl"),
            "model_safe_view": rel_path(output_dir / "model_safe_view.jsonl"),
            "smoke_ready_view_alias": rel_path(output_dir / "smoke_ready_view.jsonl"),
        },
        "matching_policy": {
            "balance_unit": "exact predicate_label + subject_class_label + object_class_label",
            "negative_policy": "family_match_or_pair_has_other_predicate_and_geometry_unsatisfied",
            "no_gt_negative_allowed": False,
            "positive_policy": "exact_gt_match_and_geometry_satisfied",
            "raw_g_required": True,
            "source_z_required": True,
        },
        "next_plan_contract": next_plan_contract(),
        "next_todo": NEXT_TODO if not errors else "fix_stratum_repair_candidate_materialization",
        "quota_summary": {
            "quota_rows": len(quotas),
            "target_primary_rows": sum(int(row["target_total_rows"]) for row in quotas),
            "target_positive_rows": sum(int(row["target_positive_quota"]) for row in quotas),
            "target_negative_rows": sum(int(row["target_negative_quota"]) for row in quotas),
        },
        "collection_stats": collection_stats,
        "schema_precheck": precheck,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "summary_counts": summarize_rows(rows),
        "validation_errors": len(errors),
    }


def build_report(manifest: dict[str, Any], quota_audit: list[dict[str, Any]]) -> str:
    counts = manifest["summary_counts"]
    lines = [
        "# H002 Independent Validity Stratum Repair Candidate Materialization",
        "",
        "## Status",
        "",
        "```text",
        f"status = {manifest['status']}",
        f"validation_errors = {manifest['validation_errors']}",
        f"next_todo = {manifest['next_todo']}",
        "```",
        "",
        "## Materialized Counts",
        "",
        "```text",
        f"materialized_primary_rows = {counts['materialized_primary_rows']}",
        f"positive_rows = {counts['positive_rows']}",
        f"negative_rows = {counts['negative_rows']}",
        f"retained_exact_strata = {counts['retained_exact_strata']}",
        f"scan_cap_relaxation_rows = {counts['scan_cap_relaxation_rows']}",
        "```",
        "",
        "Family counts:",
        "",
        "| Family | Rows | Interpretation |",
        "| --- | ---: | --- |",
    ]
    for family, count in counts["by_family"].items():
        interpretation = "primary exact-stratum repair slice"
        if family == "support_contact_pose_conditioned" and count < 400:
            interpretation = "diagnostic slice due limited exact-stratum capacity"
        lines.append(f"| `{family}` | {count} | {interpretation} |")
    lines.extend(["", "Predicate counts:", "", "| Predicate | Rows |", "| --- | ---: |"])
    for predicate, count in counts["by_predicate"].items():
        lines.append(f"| `{predicate}` | {count} |")
    lines.extend(
        [
            "",
            "## Schema Precheck",
            "",
            "| Check | Pass | Value |",
            "| --- | --- | --- |",
        ]
    )
    for check in manifest["schema_precheck"]["checks"]:
        lines.append(f"| `{check['check']}` | {check['passes']} | `{check.get('value')}` |")
    lines.extend(
        [
            "",
            "## Quota Audit Preview",
            "",
            "| Stratum | Label | Quota | Materialized | Pass |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in quota_audit[:24]:
        stratum = f"{row['predicate_label']} / {row['subject_class_label']} -> {row['object_class_label']}"
        lines.append(
            f"| `{stratum}` | {row['label_y']} | {row['target_quota']} | {row['materialized']} | {row['passes']} |"
        )
    if len(quota_audit) > 24:
        lines.append(f"| ... | ... | ... | ... | `{len(quota_audit) - 24} more label-strata` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The repaired materialization preserves `T_e` object-class semantics while balancing labels",
            "inside exact predicate/object-class strata. The next schema shortcut audit must check whether",
            "the strongest previous shortcut is actually removed from the model-safe view.",
            "",
            "Support/contact remains a diagnostic slice in this target because exact-stratum capacity is",
            "small after scan caps.",
            "",
            "## Boundary",
            "",
            "- Train split only.",
            "- No validation/test rows were used.",
            "- No learned smoke/model was run.",
            "- `candidate_rows.jsonl` keeps hidden construction fields for audit.",
            "- `model_safe_view.jsonl` excludes construction summaries such as `geometry_status` and `p_geom_valid`.",
            "- No H001 artifact was modified.",
            "- This is not paper evidence.",
            "",
            "## Next",
            "",
            "```text",
            manifest["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_path = args.plan_dir / "summary.json"
    quota_path = args.plan_dir / "stratum_quota_plan.csv"
    input_errors: list[dict[str, Any]] = []
    plan: dict[str, Any] = {}
    quotas: list[dict[str, Any]] = []

    if not plan_path.exists():
        input_errors.append({"error_type": "missing_plan_summary", "path": rel_path(plan_path)})
    else:
        plan = read_json(plan_path)
        input_errors.extend(validate_plan(plan, args.plan_dir, args.match_rows))
    if not quota_path.exists():
        input_errors.append({"error_type": "missing_stratum_quota_plan", "path": rel_path(quota_path)})
    else:
        quotas = read_quota_plan(quota_path)

    quota_errors = validate_quotas(quotas) if quotas else [{"error_type": "empty_quota_plan"}]
    if input_errors or quota_errors:
        pools: dict[tuple[str, str, str], dict[int, list[dict[str, Any]]]] = {}
        collection_stats: dict[str, Any] = {}
        rows: list[dict[str, Any]] = []
        quota_audit: list[dict[str, Any]] = []
    else:
        pools, collection_stats = collect_candidate_pools(args.match_rows, quotas)
        rows, quota_audit = materialize_rows(pools, quotas)

    model_rows = [model_safe_view(row) for row in rows]
    precheck = schema_precheck(rows, model_rows)
    errors = build_validation_errors(input_errors, quota_errors, quota_audit, precheck)
    manifest = build_manifest(
        plan=plan,
        match_rows=args.match_rows,
        output_dir=output_dir,
        rows=rows,
        quotas=quotas,
        collection_stats=collection_stats,
        quota_audit=quota_audit,
        precheck=precheck,
        errors=errors,
    )

    write_jsonl(output_dir / "candidate_rows.jsonl", rows)
    write_jsonl(output_dir / "model_safe_view.jsonl", model_rows)
    write_jsonl(output_dir / "smoke_ready_view.jsonl", model_rows)
    write_jsonl(output_dir / "hidden_manifest.jsonl", [hidden_manifest_row(row) for row in rows])
    write_csv(output_dir / "quota_audit.csv", quota_audit)
    write_json(output_dir / "schema_precheck.json", precheck)
    write_csv(output_dir / "schema_precheck.csv", schema_precheck_csv_rows(precheck))
    write_json(output_dir / "next_plan_contract.json", manifest["next_plan_contract"])
    write_json(output_dir / "materialization_manifest.json", manifest)
    write_json(output_dir / "summary.json", manifest)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(build_report(manifest, quota_audit), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "validation_errors": manifest["validation_errors"],
                **manifest["summary_counts"],
            },
            sort_keys=True,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
