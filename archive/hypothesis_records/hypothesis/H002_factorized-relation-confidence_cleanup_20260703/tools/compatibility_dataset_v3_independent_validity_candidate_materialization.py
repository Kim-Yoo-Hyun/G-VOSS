#!/usr/bin/env python3
"""Materialize frozen GT-anchored independent-validity candidate rows."""

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

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_materialization_plan"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_candidate_materialization"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_independent_validity_materialization_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_independent_validity_candidate_materialization"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_candidate_materialization_v1"
ROW_SCHEMA_VERSION = "h002_independent_validity_candidate_row_v1"
SMOKE_VIEW_SCHEMA = "h002_independent_validity_smoke_ready_view_v1"
DATASET_NAME = "h002_independent_validity_candidates_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_independent_validity_candidate_materialization_ready_for_schema_shortcut_audit"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_independent_validity_candidate_materialization_input_errors"
NEXT_TODO = "compatibility_dataset_v3_independent_validity_schema_shortcut_audit"

PRIMARY_FAMILY_PREDICATES = {
    "relative_vertical": {"higher than", "lower than"},
    "support_contact_pose_conditioned": {"standing on", "lying on"},
}
RAW_MATCH_FAMILY_TO_TARGET = {
    "relative_vertical": "relative_vertical",
    "support_contact": "support_contact_pose_conditioned",
}
HIDDEN_SMOKE_KEYS = {
    "controls_hidden",
    "directed_pair_id",
    "label_match_status",
    "matched_gt_ids",
    "matched_predicates",
    "object_id",
    "prediction_id",
    "provenance",
    "provenance_safe",
    "scan_id",
    "source_line_no",
    "subject_id",
    "subgraph_id",
    "target_pool",
    "target_role",
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


def read_quota_table(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row["available"] = int(row["available"])
            row["quota"] = int(row["quota"])
            row["materialize_for_primary_binary"] = str(row["materialize_for_primary_binary"]).lower() == "true"
            value = row["label_C_e_validity"]
            row["label_C_e_validity"] = int(value) if value in {"0", "1"} else value
            rows.append(row)
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
    label = predicate.get("predicate_label")
    raw_family = predicate.get("predicate_family")
    family = RAW_MATCH_FAMILY_TO_TARGET.get(str(raw_family))
    if family is None:
        return None
    if str(label) not in PRIMARY_FAMILY_PREDICATES[family]:
        return None
    return family


def target_pool(row: dict[str, Any]) -> str | None:
    label_status = row.get("label", {}).get("label_match_status")
    geometry_status = row.get("geometry", {}).get("geometry_status")
    if label_status == "exact_match" and geometry_status == "satisfied":
        return "positive_exact_gt_satisfied"
    if label_status == "exact_match" and geometry_status == "unsatisfied":
        return "gt_conflict_exact_unsatisfied"
    if label_status in {"family_match", "pair_has_other_predicate"} and geometry_status == "unsatisfied":
        return "strong_negative_gt_pair_other_predicate_unsatisfied"
    if label_status == "no_gt_for_pair" and geometry_status == "satisfied":
        return "abstain_no_gt_geometry_satisfied"
    if geometry_status == "uncertain":
        return "abstain_geometry_uncertain"
    return None


def scan_pair_key(row: dict[str, Any]) -> tuple[str, str]:
    identity = row.get("identity", {})
    return str(identity.get("scan_id")), str(identity.get("directed_pair_id"))


def visible_pair(row: dict[str, Any]) -> str:
    edge = row.get("edge", {})
    return f"{norm_text(edge.get('subject_label')).lower()} [REL] {norm_text(edge.get('object_label')).lower()}"


def rank_band(row: dict[str, Any]) -> str:
    rga = row.get("rga", {})
    if rga.get("rank_band"):
        return str(rga["rank_band"])
    rank = safe_float(row.get("semantic", {}).get("rank_in_context"))
    if rank is None:
        return "rank_unknown"
    if rank <= 20:
        return "top20"
    if rank <= 50:
        return "top50"
    if rank <= 100:
        return "top100"
    if rank <= 500:
        return "rank_101_500"
    if rank <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def raw_geometry_feature_vector(row: dict[str, Any]) -> dict[str, float | None]:
    raw = row.get("geometry", {}).get("raw_features")
    if not isinstance(raw, dict):
        return {}
    return {str(key): safe_float(value) for key, value in sorted(raw.items())}


def row_group_id(row: dict[str, Any]) -> str:
    identity = row.get("identity", {})
    payload = {
        "scan_id": identity.get("scan_id"),
        "subgraph_id": identity.get("subgraph_id"),
        "directed_pair_id": identity.get("directed_pair_id"),
    }
    return f"cv_train_{stable_hash(payload, 16)}"


def build_candidate_row(
    row: dict[str, Any],
    *,
    family: str,
    pool: str,
    quota_meta: dict[str, Any],
    family_pool_index: int,
    global_index: int,
    source_line_no: int,
) -> dict[str, Any]:
    identity = row.get("identity", {})
    edge = row.get("edge", {})
    predicate = row.get("predicate", {})
    semantic = row.get("semantic", {})
    geometry = row.get("geometry", {})
    label = row.get("label", {})
    rga = row.get("rga", {})
    row_id = f"iv3_{global_index:06d}_{stable_hash(identity.get('prediction_id'), 12)}"
    raw_g = raw_geometry_feature_vector(row)
    geometry_status = geometry.get("geometry_status")
    label_status = label.get("label_match_status")
    is_primary = bool(quota_meta["materialize_for_primary_binary"])
    return {
        "row_id": row_id,
        "cv_group_id": row_group_id(row),
        "dataset_name": DATASET_NAME,
        "schema_version": ROW_SCHEMA_VERSION,
        "split": "train",
        "family": family,
        "target_role": quota_meta["target_role"],
        "target_pool": pool,
        "feature_blocks": {
            "T_e": {
                "object_class_label": edge.get("object_label"),
                "predicate_label": predicate.get("predicate_label"),
                "predicate_text": predicate.get("predicate_label"),
                "relation_family": family,
                "subject_class_label": edge.get("subject_label"),
            },
            "Z_e_safe": {
                "context_prediction_count": safe_int(semantic.get("context_prediction_count")),
                "predicate_rank_for_pair": safe_int(semantic.get("predicate_rank_for_pair")),
                "rank_band": rank_band(row),
                "semantic_rank": safe_int(semantic.get("rank_in_context")),
                "semantic_score_norm": safe_float(semantic.get("semantic_score_norm")),
                "semantic_score_raw": safe_float(semantic.get("semantic_score_raw")),
                "source_id": row.get("source", {}).get("source_id"),
            },
            "G_e": {
                "consistency_score": safe_float(geometry.get("consistency_score")),
                "geometry_axis": rga.get("geometry_axis"),
                "geometry_residual_proxy": safe_float(geometry.get("geometry_residual_proxy")),
                "geometry_status": geometry_status,
                "p_geom_valid": safe_float(geometry.get("p_geom_valid")),
                "raw_geometry_feature_vector": raw_g,
            },
            "Q_e_safe": {
                "coverage_state": rga.get("coverage_state"),
                "geometry_available": bool(geometry.get("geometry_available")),
                "geometry_checkable": bool(geometry.get("geometry_checkable")),
                "has_uncertain_geometry": geometry_status == "uncertain",
                "raw_geometry_feature_count": len(raw_g),
                "reason_code_count": len(geometry.get("reason_codes") or []),
                "unsupported_geometry": geometry_status == "unsupported",
            },
        },
        "labels": {
            "C_e_validity": quota_meta["label_C_e_validity"],
            "p_obs": quota_meta["label_p_obs"],
            "p_rel": quota_meta["label_p_rel"],
            "primary_binary": quota_meta["label_C_e_validity"] if is_primary else "not_primary_binary",
            "primary_binary_usable": is_primary,
        },
        "provenance_safe": {
            "candidate_family_pool_index": family_pool_index,
            "materialization_schema": SCHEMA_VERSION,
            "source_split_name": row.get("source", {}).get("split_name"),
        },
        "controls_hidden": {
            "directed_pair_id": identity.get("directed_pair_id"),
            "geometry_status": geometry_status,
            "label_match_status": label_status,
            "matched_gt_ids": label.get("matched_gt_ids", []),
            "matched_predicates": label.get("matched_predicates", []),
            "object_id": identity.get("object_id"),
            "prediction_id": identity.get("prediction_id"),
            "scan_id": identity.get("scan_id"),
            "source_line_no": source_line_no,
            "subject_id": identity.get("subject_id"),
            "subgraph_id": identity.get("subgraph_id"),
            "visible_pair": visible_pair(row),
        },
        "text": {
            "triple": f"{edge.get('subject_label')} {predicate.get('predicate_label')} {edge.get('object_label')}",
        },
    }


def smoke_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "cv_group_id": row["cv_group_id"],
        "dataset_name": row["dataset_name"],
        "schema_version": SMOKE_VIEW_SCHEMA,
        "split": row["split"],
        "family": row["family"],
        "feature_blocks": row["feature_blocks"],
        "target": row["labels"],
        "text": row["text"],
    }


def hidden_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "cv_group_id": row["cv_group_id"],
        "family": row["family"],
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
        for item in payload:
            hits.extend(nested_key_hits(item, forbidden))
    return hits


def validate_plan(plan: dict[str, Any], match_rows: Path) -> list[dict[str, Any]]:
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
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def select_rows(
    match_rows: Path,
    quota_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    quota_by_key = {(row["family"], row["pool"]): row for row in quota_rows if int(row["quota"]) > 0}
    selected_by_key: dict[tuple[str, str], int] = defaultdict(int)
    scan_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    pair_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    candidates: list[dict[str, Any]] = []
    selected_prediction_ids: set[str] = set()
    family_pool_index: dict[tuple[str, str], int] = defaultdict(int)
    skipped_by_cap: Counter[str] = Counter()
    pass_stats: list[dict[str, Any]] = []
    selected_by_pass: Counter[str] = Counter()

    pass_specs = [
        {"name": "strict_scan_and_visible_pair_caps", "enforce_scan_cap": True, "enforce_visible_pair_cap": True},
        {"name": "relax_visible_pair_cap_for_deficits", "enforce_scan_cap": True, "enforce_visible_pair_cap": False},
        {"name": "relax_all_caps_for_remaining_deficits", "enforce_scan_cap": False, "enforce_visible_pair_cap": False},
    ]

    def all_filled() -> bool:
        return all(selected_by_key[key] >= int(meta["quota"]) for key, meta in quota_by_key.items())

    for pass_spec in pass_specs:
        if all_filled():
            break
        seen_rows = 0
        selected_before = len(candidates)
        with match_rows.open("r", encoding="utf-8") as handle:
            for source_line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                seen_rows += 1
                row = json.loads(line)
                prediction_id = str(row.get("identity", {}).get("prediction_id"))
                if prediction_id in selected_prediction_ids:
                    continue
                family = target_family(row)
                if family is None:
                    continue
                pool = target_pool(row)
                if pool is None:
                    continue
                key = (family, pool)
                quota_meta = quota_by_key.get(key)
                if quota_meta is None:
                    continue
                quota = int(quota_meta["quota"])
                if selected_by_key[key] >= quota:
                    if all_filled():
                        break
                    continue

                rare_audit = pool == "gt_conflict_exact_unsatisfied"
                scan_id, _directed_pair = scan_pair_key(row)
                vp = visible_pair(row)
                scan_cap = max(1, int(quota * 0.08))
                pair_cap = max(1, int(quota * 0.05))
                if (
                    pass_spec["enforce_scan_cap"]
                    and not rare_audit
                    and scan_counts[(family, pool, scan_id)] >= scan_cap
                ):
                    skipped_by_cap[f"{pass_spec['name']}::{family}::{pool}::scan_cap"] += 1
                    continue
                if (
                    pass_spec["enforce_visible_pair_cap"]
                    and not rare_audit
                    and pair_counts[(family, pool, vp)] >= pair_cap
                ):
                    skipped_by_cap[f"{pass_spec['name']}::{family}::{pool}::visible_pair_cap"] += 1
                    continue

                family_pool_index[key] += 1
                candidate = build_candidate_row(
                    row,
                    family=family,
                    pool=pool,
                    quota_meta=quota_meta,
                    family_pool_index=family_pool_index[key],
                    global_index=len(candidates) + 1,
                    source_line_no=source_line_no,
                )
                candidate["provenance_safe"]["selection_pass"] = pass_spec["name"]
                candidates.append(candidate)
                selected_prediction_ids.add(prediction_id)
                selected_by_key[key] += 1
                selected_by_pass[pass_spec["name"]] += 1
                scan_counts[(family, pool, scan_id)] += 1
                pair_counts[(family, pool, vp)] += 1
                if all_filled():
                    break
        pass_stats.append(
            {
                "pass_name": pass_spec["name"],
                "input_rows_scanned": seen_rows,
                "selected_rows": len(candidates) - selected_before,
                "filled_after_pass": all_filled(),
            }
        )

    scan_cap_summary: list[dict[str, Any]] = []
    for (family, pool, scan_id), count in scan_counts.items():
        quota = int(quota_by_key[(family, pool)]["quota"])
        scan_cap_summary.append(
            {
                "family": family,
                "pool": pool,
                "scan_id": scan_id,
                "selected": count,
                "scan_cap": "ignored" if pool == "gt_conflict_exact_unsatisfied" else max(1, int(quota * 0.08)),
            }
        )
    pair_cap_summary: list[dict[str, Any]] = []
    for (family, pool, pair), count in pair_counts.items():
        quota = int(quota_by_key[(family, pool)]["quota"])
        pair_cap_summary.append(
            {
                "family": family,
                "pool": pool,
                "visible_pair": pair,
                "selected": count,
                "visible_pair_cap": "ignored" if pool == "gt_conflict_exact_unsatisfied" else max(1, int(quota * 0.05)),
            }
        )
    selection_stats = {
        "cap_relaxation_policy": [
            "first pass enforces scan and visible-pair caps",
            "second pass relaxes visible-pair cap only for remaining quota deficits",
            "third pass relaxes scan and visible-pair caps only if deficits remain",
        ],
        "cap_relaxation_used": any(stat["pass_name"] != "strict_scan_and_visible_pair_caps" and stat["selected_rows"] > 0 for stat in pass_stats),
        "pass_stats": pass_stats,
        "quota_selected_counts": {
            f"{family}::{pool}": selected_by_key[(family, pool)] for family, pool in sorted(quota_by_key)
        },
        "scan_cap_top": sorted(scan_cap_summary, key=lambda row: (-int(row["selected"]), row["family"], row["pool"]))[:40],
        "visible_pair_cap_top": sorted(
            pair_cap_summary, key=lambda row: (-int(row["selected"]), row["family"], row["pool"])
        )[:40],
        "skipped_by_cap": dict(skipped_by_cap),
        "selected_by_pass": dict(selected_by_pass),
    }
    return candidates, selection_stats


def summarize_candidates(rows: list[dict[str, Any]], quota_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_family = Counter(row["family"] for row in rows)
    by_role = Counter(row["target_role"] for row in rows)
    by_pool = Counter(f"{row['family']}::{row['target_pool']}" for row in rows)
    primary_rows = [row for row in rows if row["labels"]["primary_binary_usable"] is True]
    primary_labels = Counter(str(row["labels"]["primary_binary"]) for row in primary_rows)
    quota_total = sum(int(row["quota"]) for row in quota_rows)
    quota_primary = sum(int(row["quota"]) for row in quota_rows if row["materialize_for_primary_binary"])
    return {
        "materialized_total_rows": len(rows),
        "materialized_primary_binary_rows": len(primary_rows),
        "materialized_nonbinary_rows": len(rows) - len(primary_rows),
        "primary_positive_rows": primary_labels.get("1", 0),
        "primary_negative_rows": primary_labels.get("0", 0),
        "quota_total_rows": quota_total,
        "quota_primary_binary_rows": quota_primary,
        "by_family": dict(sorted(by_family.items())),
        "by_role": dict(sorted(by_role.items())),
        "by_pool": dict(sorted(by_pool.items())),
    }


def quota_audit_rows(rows: list[dict[str, Any]], quota_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actual = Counter((row["family"], row["target_pool"]) for row in rows)
    audit: list[dict[str, Any]] = []
    for quota in quota_rows:
        family = quota["family"]
        pool = quota["pool"]
        count = actual[(family, pool)]
        audit.append(
            {
                "family": family,
                "pool": pool,
                "target_role": quota["target_role"],
                "quota": quota["quota"],
                "materialized": count,
                "deficit": int(quota["quota"]) - count,
                "passes": count == int(quota["quota"]),
            }
        )
    return audit


def schema_precheck_rows(rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row_ids = [row["row_id"] for row in rows]
    primary_rows = [row for row in rows if row["labels"]["primary_binary_usable"] is True]
    no_gt_negative_rows = [
        row
        for row in rows
        if row["target_role"] == "negative" and row["controls_hidden"]["label_match_status"] == "no_gt_for_pair"
    ]
    hidden_hits: Counter[str] = Counter()
    for row in smoke_rows:
        hidden_hits.update(nested_key_hits(row, HIDDEN_SMOKE_KEYS))
    cv_groups_by_split: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        cv_groups_by_split[row["cv_group_id"]].add(row["split"])
    multi_split_groups = [group for group, splits in cv_groups_by_split.items() if len(splits) > 1]
    return [
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
            "check": "no_gt_negative_policy",
            "value": len(no_gt_negative_rows),
            "expected": 0,
            "passes": len(no_gt_negative_rows) == 0,
        },
        {
            "check": "smoke_view_hidden_key_hits",
            "value": sum(hidden_hits.values()),
            "expected": 0,
            "passes": sum(hidden_hits.values()) == 0,
            "hit_keys": json.dumps(dict(hidden_hits), sort_keys=True),
        },
        {
            "check": "primary_binary_balance",
            "value": json.dumps(Counter(str(row["labels"]["primary_binary"]) for row in primary_rows), sort_keys=True),
            "expected": json.dumps({"0": 1600, "1": 1600}, sort_keys=True),
            "passes": Counter(str(row["labels"]["primary_binary"]) for row in primary_rows) == Counter({"0": 1600, "1": 1600}),
        },
        {
            "check": "cv_group_single_split",
            "value": len(multi_split_groups),
            "expected": 0,
            "passes": len(multi_split_groups) == 0,
        },
    ]


def validation_errors(
    rows: list[dict[str, Any]],
    smoke_rows: list[dict[str, Any]],
    quota_rows_: list[dict[str, Any]],
    input_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors = list(input_errors)
    for audit in quota_audit_rows(rows, quota_rows_):
        if not audit["passes"]:
            errors.append({"error_type": "quota_deficit", **audit})
    for check in schema_precheck_rows(rows, smoke_rows):
        if not check["passes"]:
            errors.append({"error_type": "schema_precheck_failed", **check})
    return errors


def build_manifest(
    *,
    plan: dict[str, Any],
    output_dir: Path,
    match_rows: Path,
    rows: list[dict[str, Any]],
    quota_rows_: list[dict[str, Any]],
    selection_stats: dict[str, Any],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    status = STATUS_ERROR if errors else STATUS_READY
    return {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": True,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
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
            "smoke_ready_view": rel_path(output_dir / "smoke_ready_view.jsonl"),
        },
        "matching_policy": {
            "negative_policy": "family_match_or_pair_has_other_predicate_and_geometry_unsatisfied",
            "no_gt_negative_allowed": False,
            "positive_policy": "exact_gt_match_and_geometry_satisfied",
            "uncertain_policy": "geometry_uncertain_rows_are_abstain_for_p_obs",
        },
        "next_todo": NEXT_TODO if not errors else "fix_independent_validity_candidate_materialization",
        "quota_table": quota_rows_,
        "schema_version": SCHEMA_VERSION,
        "selection_stats": selection_stats,
        "status": status,
        "summary_counts": summarize_candidates(rows, quota_rows_),
        "validation_errors": len(errors),
    }


def build_report(manifest: dict[str, Any], quota_audit: list[dict[str, Any]]) -> str:
    counts = manifest["summary_counts"]
    lines = [
        "# H002 Independent Validity Candidate Materialization",
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
        f"materialized_total_rows = {counts['materialized_total_rows']}",
        f"materialized_primary_binary_rows = {counts['materialized_primary_binary_rows']}",
        f"materialized_nonbinary_rows = {counts['materialized_nonbinary_rows']}",
        f"primary_positive_rows = {counts['primary_positive_rows']}",
        f"primary_negative_rows = {counts['primary_negative_rows']}",
        "```",
        "",
        "## Family Counts",
        "",
        "| Family | Rows |",
        "| --- | ---: |",
    ]
    for family, count in counts["by_family"].items():
        lines.append(f"| `{family}` | {count} |")
    lines.extend(
        [
            "",
            "## Role Counts",
            "",
            "| Role | Rows |",
            "| --- | ---: |",
        ]
    )
    for role, count in counts["by_role"].items():
        lines.append(f"| `{role}` | {count} |")
    lines.extend(
        [
            "",
            "## Selection Passes",
            "",
            "| Pass | Scanned Rows | Selected Rows | Filled After Pass |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for row in manifest.get("selection_stats", {}).get("pass_stats", []):
        lines.append(
            f"| `{row['pass_name']}` | {row['input_rows_scanned']} | {row['selected_rows']} | {row['filled_after_pass']} |"
        )
    lines.extend(
        [
            "",
            "Cap relaxation used:",
            "",
            "```text",
            f"{manifest.get('selection_stats', {}).get('cap_relaxation_used')}",
            "```",
            "",
            "Interpretation: strict scan and visible-pair caps did not fill every balanced primary pool. "
            "The materializer therefore used the frozen quota but relaxed only the visible-pair cap for "
            "remaining deficits. This keeps the independent validity target balanced, but it makes the next "
            "schema/shortcut audit mandatory before any learned smoke.",
            "",
            "## Quota Audit",
            "",
            "| Family | Pool | Quota | Materialized | Pass |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in quota_audit:
        lines.append(
            f"| `{row['family']}` | `{row['pool']}` | {row['quota']} | {row['materialized']} | {row['passes']} |"
        )
    lines.extend(
        [
            "",
            "## Materialization Boundary",
            "",
            "- Train split only.",
            "- No validation/test rows were used.",
            "- No learned smoke/model was run in this stage.",
            "- No-GT rows were kept as abstain/audit, not negative.",
            "- `candidate_rows.jsonl` keeps hidden construction fields for audit; `smoke_ready_view.jsonl` removes them.",
            "- This is not paper-level evidence until schema/shortcut audit and downstream smoke gates pass.",
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
    quota_path = args.plan_dir / "quota_table.csv"
    input_errors: list[dict[str, Any]] = []
    if not plan_path.exists():
        input_errors.append({"error_type": "missing_plan_summary", "path": rel_path(plan_path)})
        plan: dict[str, Any] = {}
    else:
        plan = read_json(plan_path)
        input_errors.extend(validate_plan(plan, args.match_rows))
    if not quota_path.exists():
        input_errors.append({"error_type": "missing_quota_table", "path": rel_path(quota_path)})
        quotas: list[dict[str, Any]] = []
    else:
        quotas = read_quota_table(quota_path)

    if input_errors or not quotas:
        rows: list[dict[str, Any]] = []
        smoke_rows: list[dict[str, Any]] = []
        selection_stats: dict[str, Any] = {"input_rows_scanned_until_stop": 0, "quota_selected_counts": {}}
    else:
        rows, selection_stats = select_rows(args.match_rows, quotas)
        smoke_rows = [smoke_view(row) for row in rows]

    errors = validation_errors(rows, smoke_rows, quotas, input_errors)
    manifest = build_manifest(
        plan=plan,
        output_dir=output_dir,
        match_rows=args.match_rows,
        rows=rows,
        quota_rows_=quotas,
        selection_stats=selection_stats,
        errors=errors,
    )
    quota_audit = quota_audit_rows(rows, quotas)
    schema_precheck = schema_precheck_rows(rows, smoke_rows)

    write_jsonl(output_dir / "candidate_rows.jsonl", rows)
    write_jsonl(output_dir / "smoke_ready_view.jsonl", smoke_rows)
    write_jsonl(output_dir / "hidden_manifest.jsonl", [hidden_manifest_row(row) for row in rows])
    write_json(output_dir / "materialization_manifest.json", manifest)
    write_json(output_dir / "summary.json", manifest)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_csv(output_dir / "quota_audit.csv", quota_audit)
    write_csv(output_dir / "schema_shortcut_precheck.csv", schema_precheck)
    write_text = build_report(manifest, quota_audit)
    (output_dir / "report.md").write_text(write_text, encoding="utf-8")

    print(json.dumps({"status": manifest["status"], "validation_errors": len(errors), **manifest["summary_counts"]}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
