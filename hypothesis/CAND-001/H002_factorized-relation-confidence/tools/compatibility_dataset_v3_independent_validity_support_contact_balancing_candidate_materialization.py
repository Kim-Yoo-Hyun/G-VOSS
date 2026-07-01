#!/usr/bin/env python3
"""Materialize support/contact-primary H002 independent-validity candidate rows."""

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
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_plan"
)
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_plan_ready_for_materialization"
)
EXPECTED_PLAN_NEXT = (
    "compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization_v1"
)
ROW_SCHEMA_VERSION = "h002_support_contact_primary_independent_validity_row_v1"
MODEL_VIEW_SCHEMA = "h002_support_contact_primary_independent_validity_model_safe_view_v1"
DATASET_NAME = "h002_support_contact_primary_independent_validity_candidates_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization_ready_for_schema_shortcut_audit"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization_input_errors"
)
NEXT_TODO = "compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit"

SUPPORT_FAMILY = "support_contact_pose_conditioned"
RAW_MATCH_FAMILY = "support_contact"
PREDICATES = {"lying on", "standing on"}
TARGET_ROWS = 1200
MIN_ROWS = 800
PREDICATE_TARGET = {"lying on": 600, "standing on": 600}
BUCKET_TARGETS = {
    ("lying on", 1): 300,
    ("lying on", 0): 300,
    ("standing on", 1): 300,
    ("standing on", 0): 300,
}
GLOBAL_CAPS = {
    "scan": 0.05,
    "directed_pair": 0.01,
    "class_pair": 0.10,
    "rank_band": 0.55,
}
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
    return json.loads(path.read_text(encoding="utf-8"))


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
                fields.append(key)
                seen.add(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


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
    if str(predicate.get("predicate_family")) != RAW_MATCH_FAMILY:
        return None
    if str(predicate.get("predicate_label")) not in PREDICATES:
        return None
    return SUPPORT_FAMILY


def primary_label(row: dict[str, Any]) -> int | None:
    label_status = row.get("label", {}).get("label_match_status")
    geometry_status = row.get("geometry", {}).get("geometry_status")
    if label_status == "exact_match" and geometry_status == "satisfied":
        return 1
    if label_status in {"family_match", "pair_has_other_predicate"} and geometry_status == "unsatisfied":
        return 0
    return None


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


def directed_pair_id(row: dict[str, Any]) -> str:
    return str(row.get("identity", {}).get("directed_pair_id"))


def class_pair(row: dict[str, Any]) -> str:
    edge = row.get("edge", {})
    return f"{norm_text(edge.get('subject_label')).lower()} [REL] {norm_text(edge.get('object_label')).lower()}"


def raw_geometry_feature_vector(row: dict[str, Any]) -> dict[str, float | None]:
    raw = row.get("geometry", {}).get("raw_features")
    if not isinstance(raw, dict):
        return {}
    return {str(key): safe_float(value) for key, value in sorted(raw.items())}


def geometry_feature_groups(raw_g: dict[str, float | None]) -> dict[str, Any]:
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


def validate_plan(plan: dict[str, Any], contract: dict[str, Any], match_rows: Path) -> list[dict[str, Any]]:
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
    if boundary.get("materializes_candidate_rows") is not False:
        errors.append({"error_type": "upstream_plan_already_materialized_rows"})
    if contract.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_contract_next", "actual": contract.get("next_todo")})
    if int(contract.get("target_rows", -1)) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_contract_target_rows", "actual": contract.get("target_rows")})
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def collect_candidate_pools(match_rows: Path) -> tuple[dict[tuple[str, int], list[dict[str, Any]]], dict[str, Any]]:
    pools: dict[tuple[str, int], list[dict[str, Any]]] = {key: [] for key in BUCKET_TARGETS}
    skip_counts: Counter[str] = Counter()
    scanned_rows = 0
    selected_family_rows = 0
    primary_candidate_rows = 0
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
            predicate = str(row.get("predicate", {}).get("predicate_label"))
            label_y = primary_label(row)
            if label_y is None:
                skip_counts["not_primary_label_policy"] += 1
                continue
            key = (predicate, label_y)
            if key not in pools:
                skip_counts["not_requested_bucket"] += 1
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
            pools[key].append(row)
    return pools, {
        "scanned_rows": scanned_rows,
        "selected_family_rows": selected_family_rows,
        "primary_candidate_rows": primary_candidate_rows,
        "skip_counts": dict(skip_counts),
        "available_by_bucket": {f"{predicate}|{label}": len(rows) for (predicate, label), rows in sorted(pools.items())},
    }


def candidate_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    semantic = row.get("semantic", {})
    identity = row.get("identity", {})
    return (
        class_pair(row),
        RANK_BAND_ORDER.get(rank_band(row), 99),
        scan_id(row),
        safe_int(semantic.get("rank_in_context")) or 10**9,
        str(identity.get("prediction_id")),
    )


def round_robin_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[class_pair(row)].append(row)
    for key in groups:
        groups[key].sort(key=candidate_sort_key)
    ordered_groups = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    output: list[dict[str, Any]] = []
    while ordered_groups:
        next_groups: list[tuple[str, list[dict[str, Any]]]] = []
        for key, group_rows in ordered_groups:
            output.append(group_rows.pop(0))
            if group_rows:
                next_groups.append((key, group_rows))
        ordered_groups = next_groups
    return output


def cap_limits() -> dict[str, int]:
    return {
        "scan": max(1, int(TARGET_ROWS * GLOBAL_CAPS["scan"])),
        "directed_pair": max(1, int(TARGET_ROWS * GLOBAL_CAPS["directed_pair"])),
        "class_pair": max(1, int(TARGET_ROWS * GLOBAL_CAPS["class_pair"])),
        "rank_band": max(1, int(TARGET_ROWS * GLOBAL_CAPS["rank_band"])),
    }


def cap_key(row: dict[str, Any], cap_name: str) -> str:
    if cap_name == "scan":
        return scan_id(row)
    if cap_name == "directed_pair":
        return directed_pair_id(row)
    if cap_name == "class_pair":
        return class_pair(row)
    if cap_name == "rank_band":
        return rank_band(row)
    raise ValueError(cap_name)


def select_bucket(
    rows: list[dict[str, Any]],
    quota: int,
    global_counts: dict[str, Counter[str]],
    limits: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    ordered = round_robin_candidates(rows)
    skipped_by_cap: Counter[str] = Counter()
    used_prediction_ids: set[str] = set()
    for row in ordered:
        if len(selected) == quota:
            break
        blocked = False
        for cap_name, limit in limits.items():
            key = cap_key(row, cap_name)
            if global_counts[cap_name][key] >= limit:
                skipped_by_cap[cap_name] += 1
                blocked = True
                break
        if blocked:
            continue
        selected.append(row)
        used_prediction_ids.add(str(row.get("identity", {}).get("prediction_id")))
        for cap_name in limits:
            global_counts[cap_name][cap_key(row, cap_name)] += 1

    relaxed_rows = 0
    if len(selected) < quota:
        for row in ordered:
            if len(selected) == quota:
                break
            prediction_id = str(row.get("identity", {}).get("prediction_id"))
            if prediction_id in used_prediction_ids:
                continue
            # Last-resort fill for materialization. The cap audit records any violation.
            selected.append(row)
            used_prediction_ids.add(prediction_id)
            relaxed_rows += 1
            for cap_name in limits:
                global_counts[cap_name][cap_key(row, cap_name)] += 1

    return selected, {
        "available": len(rows),
        "quota": quota,
        "selected": len(selected),
        "deficit": quota - len(selected),
        "cap_limits": limits,
        "skipped_by_cap": dict(skipped_by_cap),
        "relaxed_rows": relaxed_rows,
        "cap_relaxation_used": relaxed_rows > 0,
        "class_pair_counts": dict(Counter(class_pair(row) for row in selected).most_common(10)),
        "scan_counts": dict(Counter(scan_id(row) for row in selected).most_common(10)),
        "rank_band_counts": dict(Counter(rank_band(row) for row in selected)),
    }


def build_candidate_row(
    row: dict[str, Any],
    *,
    label_y: int,
    global_index: int,
    bucket_stats: dict[str, Any],
) -> dict[str, Any]:
    identity = row.get("identity", {})
    edge = row.get("edge", {})
    predicate = row.get("predicate", {})
    semantic = row.get("semantic", {})
    geometry = row.get("geometry", {})
    label = row.get("label", {})
    raw_g = raw_geometry_feature_vector(row)
    target_role = "positive" if label_y == 1 else "negative"
    target_pool = (
        "positive_exact_gt_satisfied"
        if label_y == 1
        else "strong_negative_gt_pair_other_predicate_unsatisfied"
    )
    row_id = f"sciv_{global_index:06d}_{stable_hash(identity.get('prediction_id'), 12)}"
    feature_blocks = {
        "T_e": {
            "object_class_label": edge.get("object_label"),
            "predicate_label": predicate.get("predicate_label"),
            "predicate_text": predicate.get("predicate_label"),
            "relation_family": SUPPORT_FAMILY,
            "subject_class_label": edge.get("subject_label"),
        },
        "Z_e_safe": {
            "rank_band": rank_band(row),
            "semantic_rank": safe_int(semantic.get("rank_in_context")),
            "semantic_score_norm": safe_float(semantic.get("semantic_score_norm")),
            "semantic_score_raw": safe_float(semantic.get("semantic_score_raw")),
            "source_id": row.get("source", {}).get("source_id"),
        },
        "G_e_raw": geometry_feature_groups(raw_g),
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
        "family": SUPPORT_FAMILY,
        "predicate_label": predicate.get("predicate_label"),
        "subject_class_label": edge.get("subject_label"),
        "object_class_label": edge.get("object_label"),
        "predicate_label_target": predicate.get("predicate_label"),
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
            "class_pair": class_pair(row),
            "directed_pair_id": identity.get("directed_pair_id"),
            "geometry_residual_proxy": safe_float(geometry.get("geometry_residual_proxy")),
            "geometry_status": geometry.get("geometry_status"),
            "label_match_status": label.get("label_match_status"),
            "matched_gt_ids": label.get("matched_gt_ids", []),
            "matched_predicates": label.get("matched_predicates", []),
            "object_id": identity.get("object_id"),
            "p_geom_valid": safe_float(geometry.get("p_geom_valid")),
            "prediction_id": identity.get("prediction_id"),
            "rank_band": rank_band(row),
            "scan_id": identity.get("scan_id"),
            "selection_pass": "predicate_balanced_support_contact_primary",
            "selection_stats": bucket_stats,
            "source_line_no": row.get("_source_line_no"),
            "subject_id": identity.get("subject_id"),
            "subgraph_id": identity.get("subgraph_id"),
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
    pools: dict[tuple[str, int], list[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Counter[str]]]:
    global_counts = {name: Counter() for name in GLOBAL_CAPS}
    limits = cap_limits()
    selected_rows: list[dict[str, Any]] = []
    quota_audit: list[dict[str, Any]] = []
    # Scarcity-first prevents small negative buckets from being starved by global caps.
    ordered_buckets = sorted(BUCKET_TARGETS, key=lambda key: (len(pools.get(key, [])), key[1], key[0]))
    for predicate, label_y in ordered_buckets:
        quota = BUCKET_TARGETS[(predicate, label_y)]
        selected, stats = select_bucket(pools.get((predicate, label_y), []), quota, global_counts, limits)
        start_index = len(selected_rows)
        for row in selected:
            selected_rows.append(
                build_candidate_row(
                    row,
                    label_y=label_y,
                    global_index=len(selected_rows) + 1,
                    bucket_stats=stats,
                )
            )
        quota_audit.append(
            {
                "predicate_label": predicate,
                "label_y": label_y,
                "target_quota": quota,
                "available_after_filters": len(pools.get((predicate, label_y), [])),
                "materialized": len(selected),
                "deficit": quota - len(selected),
                "selection_order": ordered_buckets.index((predicate, label_y)) + 1,
                "cap_relaxation_used": stats["cap_relaxation_used"],
                "relaxed_rows": stats["relaxed_rows"],
                "row_start": start_index + 1,
                "row_end": len(selected_rows),
                "rank_band_counts": json.dumps(stats["rank_band_counts"], sort_keys=True),
                "top_class_pair_counts": json.dumps(stats["class_pair_counts"], sort_keys=True),
                "top_scan_counts": json.dumps(stats["scan_counts"], sort_keys=True),
                "passes": len(selected) == quota,
            }
        )
    return selected_rows, quota_audit, global_counts


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
    labels = Counter(str(row["labels"]["primary_binary"]) for row in rows)
    predicates = Counter(row["predicate_label"] for row in rows)
    predicate_labels: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        predicate_labels[row["predicate_label"]][str(row["labels"]["primary_binary"])] += 1
    class_pairs = Counter(f"{row['subject_class_label']} [REL] {row['object_class_label']}" for row in rows)
    scans = Counter(row["controls_hidden"]["scan_id"] for row in rows)
    directed_pairs = Counter(row["controls_hidden"]["directed_pair_id"] for row in rows)
    rank_bands = Counter(row["controls_hidden"]["rank_band"] for row in rows)
    return {
        "materialized_primary_rows": len(rows),
        "positive_rows": labels.get("1", 0),
        "negative_rows": labels.get("0", 0),
        "by_predicate": dict(sorted(predicates.items())),
        "by_predicate_label": {key: dict(sorted(value.items())) for key, value in sorted(predicate_labels.items())},
        "top_class_pairs": dict(class_pairs.most_common(20)),
        "top_scans": dict(scans.most_common(20)),
        "top_directed_pairs": dict(directed_pairs.most_common(20)),
        "rank_bands": dict(sorted(rank_bands.items())),
        "max_single_class_pair_share": max(class_pairs.values(), default=0) / len(rows) if rows else 0.0,
        "max_single_scan_share": max(scans.values(), default=0) / len(rows) if rows else 0.0,
        "max_single_directed_pair_share": max(directed_pairs.values(), default=0) / len(rows) if rows else 0.0,
        "max_single_rank_band_share": max(rank_bands.values(), default=0) / len(rows) if rows else 0.0,
    }


def cap_audit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(rows)
    audits = []
    for cap_name, limit_share in GLOBAL_CAPS.items():
        if cap_name == "scan":
            counter = Counter(row["controls_hidden"]["scan_id"] for row in rows)
        elif cap_name == "directed_pair":
            counter = Counter(row["controls_hidden"]["directed_pair_id"] for row in rows)
        elif cap_name == "class_pair":
            counter = Counter(f"{row['subject_class_label']} [REL] {row['object_class_label']}" for row in rows)
        elif cap_name == "rank_band":
            counter = Counter(row["controls_hidden"]["rank_band"] for row in rows)
        else:
            continue
        max_count = max(counter.values(), default=0)
        max_share = max_count / total if total else 0.0
        audits.append(
            {
                "cap_name": cap_name,
                "limit_share": limit_share,
                "limit_count": int(TARGET_ROWS * limit_share),
                "observed_max_count": max_count,
                "observed_max_share": max_share,
                "passes": max_share <= limit_share if total else False,
                "top_values": json.dumps(dict(counter.most_common(10)), ensure_ascii=False, sort_keys=True),
            }
        )
    return audits


def class_pair_balance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in rows:
        pair = f"{row['subject_class_label']} [REL] {row['object_class_label']}"
        table[(row["predicate_label"], pair)][str(row["labels"]["primary_binary"])] += 1
    output = []
    for (predicate, pair), counter in sorted(table.items()):
        total = counter["0"] + counter["1"]
        output.append(
            {
                "predicate_label": predicate,
                "class_pair": pair,
                "positive": counter["1"],
                "negative": counter["0"],
                "total": total,
                "positive_share": counter["1"] / total if total else None,
            }
        )
    return output


def schema_precheck(rows: list[dict[str, Any]], model_rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_ids = [row["row_id"] for row in rows]
    labels = Counter(str(row["labels"]["primary_binary"]) for row in rows)
    predicate_label_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        predicate_label_counts[row["predicate_label"]][str(row["labels"]["primary_binary"])] += 1
    model_hidden_hits = Counter()
    feature_hidden_hits = Counter()
    for row in model_rows:
        model_hidden_hits.update(nested_key_hits(row, FORBIDDEN_MODEL_KEYS))
        feature_hidden_hits.update(nested_key_hits(row.get("feature_blocks", {}), FORBIDDEN_MODEL_KEYS))
    caps = cap_audit_rows(rows)
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
            "expected": TARGET_ROWS,
            "minimum": MIN_ROWS,
            "passes": len(rows) == TARGET_ROWS,
        },
        {
            "check": "primary_label_balance",
            "value": dict(sorted(labels.items())),
            "expected": {"0": TARGET_ROWS // 2, "1": TARGET_ROWS // 2},
            "passes": labels == Counter({"0": TARGET_ROWS // 2, "1": TARGET_ROWS // 2}),
        },
        {
            "check": "predicate_internal_label_balance",
            "value": {key: dict(sorted(value.items())) for key, value in sorted(predicate_label_counts.items())},
            "expected": {
                predicate: {"0": BUCKET_TARGETS[(predicate, 0)], "1": BUCKET_TARGETS[(predicate, 1)]}
                for predicate in sorted(PREDICATES)
            },
            "passes": all(
                predicate_label_counts[predicate]["0"] == BUCKET_TARGETS[(predicate, 0)]
                and predicate_label_counts[predicate]["1"] == BUCKET_TARGETS[(predicate, 1)]
                for predicate in PREDICATES
            ),
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
        {
            "check": "global_caps",
            "value": {row["cap_name"]: row["observed_max_share"] for row in caps},
            "expected": GLOBAL_CAPS,
            "passes": all(row["passes"] for row in caps),
            "cap_audit": caps,
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
                "expected": json.dumps(check.get("expected", check.get("minimum")), ensure_ascii=False, sort_keys=True),
                "passes": check["passes"],
                "detail": json.dumps(
                    {
                        key: value
                        for key, value in check.items()
                        if key not in {"check", "value", "expected", "minimum", "passes"}
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
        )
    return rows


def build_validation_errors(
    input_errors: list[dict[str, Any]],
    quota_audit: list[dict[str, Any]],
    precheck: dict[str, Any],
) -> list[dict[str, Any]]:
    errors = list(input_errors)
    for row in quota_audit:
        if not row["passes"]:
            errors.append({"error_type": "quota_materialization_deficit", **row})
        if row["cap_relaxation_used"]:
            errors.append({"error_type": "cap_relaxation_used", **row})
    for check in precheck["checks"]:
        if not check["passes"]:
            errors.append({"error_type": "schema_precheck_failed", **check})
    return errors


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Audit schema leakage and residual shortcuts on support/contact-primary independent-validity rows before learned smoke.",
        "required_inputs": [
            "candidate_rows.jsonl",
            "model_safe_view.jsonl",
            "hidden_manifest.jsonl",
            "quota_audit.csv",
            "class_pair_balance_audit.csv",
            "cap_audit.csv",
            "schema_precheck.json",
        ],
        "required_gates": [
            "model-safe view has no forbidden construction fields",
            "predicate internal label balance is 300/300 for lying on and standing on",
            "single-feature predicate/class/source/rank shortcuts are below risk threshold",
            "class-pair/scan/directed-pair/rank caps pass or are explicitly diagnosed",
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
    contract: dict[str, Any],
    match_rows: Path,
    output_dir: Path,
    rows: list[dict[str, Any]],
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
        "input_contract_next_todo": contract.get("next_todo"),
        "materialized_outputs": {
            "candidate_rows": rel_path(output_dir / "candidate_rows.jsonl"),
            "hidden_manifest": rel_path(output_dir / "hidden_manifest.jsonl"),
            "model_safe_view": rel_path(output_dir / "model_safe_view.jsonl"),
            "smoke_ready_view_alias": rel_path(output_dir / "smoke_ready_view.jsonl"),
        },
        "matching_policy": {
            "balance_unit": "predicate_label with class-pair/scan/directed-pair/rank caps",
            "negative_policy": "family_match_or_pair_has_other_predicate_and_geometry_unsatisfied",
            "no_gt_negative_allowed": False,
            "positive_policy": "exact_gt_match_and_geometry_satisfied",
            "raw_g_required": True,
            "source_z_required": True,
        },
        "next_plan_contract": next_plan_contract(),
        "next_todo": NEXT_TODO if not errors else "fix_support_contact_balancing_candidate_materialization",
        "quota_summary": {
            "target_primary_rows": TARGET_ROWS,
            "target_positive_rows": TARGET_ROWS // 2,
            "target_negative_rows": TARGET_ROWS // 2,
            "predicate_target": PREDICATE_TARGET,
            "bucket_targets": {f"{predicate}|{label}": count for (predicate, label), count in BUCKET_TARGETS.items()},
        },
        "collection_stats": collection_stats,
        "schema_precheck": precheck,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "summary_counts": summarize_rows(rows),
        "validation_errors": len(errors),
    }


def build_report(manifest: dict[str, Any], quota_audit: list[dict[str, Any]], cap_rows: list[dict[str, Any]]) -> str:
    counts = manifest["summary_counts"]
    lines = [
        "# H002 Support/Contact Balancing Candidate Materialization",
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
        f"by_predicate = {json.dumps(counts['by_predicate'], ensure_ascii=False, sort_keys=True)}",
        f"by_predicate_label = {json.dumps(counts['by_predicate_label'], ensure_ascii=False, sort_keys=True)}",
        "```",
        "",
        "## Quota Audit",
        "",
        "| Predicate | Label | Quota | Materialized | Pass |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in quota_audit:
        lines.append(
            f"| `{row['predicate_label']}` | {row['label_y']} | {row['target_quota']} | {row['materialized']} | {row['passes']} |"
        )
    lines.extend(["", "## Cap Audit", "", "| Cap | Limit | Observed | Pass |", "| --- | ---: | ---: | --- |"])
    for row in cap_rows:
        lines.append(
            f"| `{row['cap_name']}` | {row['limit_share']:.3f} | {row['observed_max_share']:.3f} | {row['passes']} |"
        )
    lines.extend(["", "## Schema Precheck", "", "| Check | Pass | Value |", "| --- | --- | --- |"])
    for check in manifest["schema_precheck"]["checks"]:
        lines.append(f"| `{check['check']}` | {check['passes']} | `{check.get('value')}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This materializes the support/contact-primary independent-validity target selected by the",
            "balancing plan. The target is predicate-balanced rather than exact predicate-class balanced,",
            "so the next schema shortcut audit is mandatory before any learned smoke.",
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
    contract_path = args.plan_dir / "materialization_contract.json"
    input_errors: list[dict[str, Any]] = []
    plan: dict[str, Any] = {}
    contract: dict[str, Any] = {}

    if not plan_path.exists():
        input_errors.append({"error_type": "missing_plan_summary", "path": rel_path(plan_path)})
    else:
        plan = read_json(plan_path)
    if not contract_path.exists():
        input_errors.append({"error_type": "missing_materialization_contract", "path": rel_path(contract_path)})
    else:
        contract = read_json(contract_path)
    if plan and contract:
        input_errors.extend(validate_plan(plan, contract, args.match_rows))

    if input_errors:
        pools: dict[tuple[str, int], list[dict[str, Any]]] = {key: [] for key in BUCKET_TARGETS}
        collection_stats: dict[str, Any] = {}
        rows: list[dict[str, Any]] = []
        quota_audit: list[dict[str, Any]] = []
    else:
        pools, collection_stats = collect_candidate_pools(args.match_rows)
        rows, quota_audit, _global_counts = materialize_rows(pools)

    model_rows = [model_safe_view(row) for row in rows]
    hidden_rows = [hidden_manifest_row(row) for row in rows]
    precheck = schema_precheck(rows, model_rows)
    cap_rows = cap_audit_rows(rows)
    class_pair_rows = class_pair_balance_rows(rows)
    errors = build_validation_errors(input_errors, quota_audit, precheck)
    manifest = build_manifest(
        plan=plan,
        contract=contract,
        match_rows=args.match_rows,
        output_dir=output_dir,
        rows=rows,
        collection_stats=collection_stats,
        quota_audit=quota_audit,
        precheck=precheck,
        errors=errors,
    )

    write_jsonl(output_dir / "candidate_rows.jsonl", rows)
    write_jsonl(output_dir / "model_safe_view.jsonl", model_rows)
    write_jsonl(output_dir / "smoke_ready_view.jsonl", model_rows)
    write_jsonl(output_dir / "hidden_manifest.jsonl", hidden_rows)
    write_csv(output_dir / "quota_audit.csv", quota_audit)
    write_csv(output_dir / "cap_audit.csv", cap_rows)
    write_csv(output_dir / "class_pair_balance_audit.csv", class_pair_rows)
    write_json(output_dir / "schema_precheck.json", precheck)
    write_csv(output_dir / "schema_precheck.csv", schema_precheck_csv_rows(precheck))
    write_json(output_dir / "next_plan_contract.json", manifest["next_plan_contract"])
    write_json(output_dir / "materialization_manifest.json", manifest)
    write_json(output_dir / "summary.json", manifest)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(build_report(manifest, quota_audit, cap_rows), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "validation_errors": manifest["validation_errors"],
                "rows": manifest["summary_counts"]["materialized_primary_rows"],
                "by_predicate_label": manifest["summary_counts"]["by_predicate_label"],
                "next_todo": manifest["next_todo"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
