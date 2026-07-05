#!/usr/bin/env python3
"""Materialize R6 supported-by decomposition candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
ARTIFACT_ROOT = H2_ROOT / "artifacts"

DEFAULT_PLAN_DIR = ARTIFACT_ROOT / "compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan"
DEFAULT_RGA_DIR = ARTIFACT_ROOT / "train_rga_full/open3dsg_train_full/rga"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/route_specific_targets/r6_superordinate_support"

SUPPORT_CONTACT_MATERIALIZER = (
    H2_ROOT / "tools/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization.py"
)

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_supported_by_decomposition_candidate_materialization"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_v1"
MODEL_SAFE_SCHEMA = "h002_r6_supported_by_decomposition_model_safe_rows_v1"
HIDDEN_SCHEMA = "h002_r6_supported_by_decomposition_hidden_manifest_v1"
DATASET_NAME = "h002_r6_supported_by_decomposition_candidates_v1"
STATUS_READY = "h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_ready_for_schema_shortcut_audit"
STATUS_ERROR = "h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_input_or_gate_errors"
NEXT_TODO = "compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit"

ROUTE_LABELS = ["accept_broad_support", "relabel_to_subtype", "reject_no_support", "abstain"]
SUPPORT_PREDICATES = {"standing on", "lying on", "supported by"}
GENERIC_LABELS = {"object", "objects", "item", "items", "thing", "things", "stuff", "unknown", "other", "others", "furniture"}
HARD_SURFACE_LABELS = {"floor", "wall", "ceiling", "room", "window", "door"}

MAX_ROWS_PER_SCAN = 12
MAX_ROWS_PER_DIRECTED_PAIR = 1
MAX_ROWS_PER_CLASS_PAIR = 16
MAX_HARD_SURFACE_SHARE = 0.55
MAX_GENERIC_ABSTAIN_SHARE = 0.50
MIN_MIXED_CLASS_PAIR_CELLS = 12

BLOCKED_MODEL_SAFE_FIELDS = {
    "audit_status",
    "candidate_role",
    "construction_bucket",
    "directed_pair_id",
    "geometry_status",
    "h001_verification_status",
    "hidden_schema",
    "label_match_status",
    "machine_hint",
    "matched_gt_ids",
    "matched_predicates",
    "object_id",
    "p_geom_valid",
    "prediction_id",
    "queue_kind",
    "rank_band",
    "reason_codes",
    "scan_id",
    "semantic_rank",
    "semantic_score_norm",
    "semantic_score_raw",
    "source_id",
    "subgraph_id",
    "subject_id",
}


def load_support_module() -> Any:
    spec = importlib.util.spec_from_file_location("support_contact_materializer", SUPPORT_CONTACT_MATERIALIZER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load support materializer: {SUPPORT_CONTACT_MATERIALIZER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCMAT = load_support_module()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--rga-dir", type=Path, default=DEFAULT_RGA_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
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
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def stable_hash(payload: Any, length: int = 20) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def matched_set(row: dict[str, Any]) -> set[str]:
    return {str(value) for value in row.get("matched_predicates") or []}


def class_pair(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')}->{row.get('object_label')}"


def directed_pair(row: dict[str, Any]) -> str:
    return f"{row.get('scan_id')}::{row.get('subgraph_id')}::{row.get('subject_id')}->{row.get('object_id')}"


def hard_surface_pair(row: dict[str, Any]) -> bool:
    return norm(row.get("subject_label")) in HARD_SURFACE_LABELS or norm(row.get("object_label")) in HARD_SURFACE_LABELS


def generic_endpoint(row: dict[str, Any]) -> bool:
    return norm(row.get("subject_label")) in GENERIC_LABELS or norm(row.get("object_label")) in GENERIC_LABELS


def support_subtype(row: dict[str, Any]) -> str:
    matched = matched_set(row)
    if "standing on" in matched:
        return "standing on"
    if "lying on" in matched:
        return "lying on"
    return "none"


def geometry_contradiction(g_e: dict[str, Any]) -> bool:
    overlap = g_e.get("xy_overlap_min_ratio")
    gap = g_e.get("surface_gap_subject_bottom_to_object_top")
    dz = g_e.get("center_delta_z")
    return (
        (finite(overlap) and float(overlap) < 0.02)
        or (finite(gap) and float(gap) > 0.35)
        or (finite(dz) and float(dz) <= 0.0)
    )


def route_label_for(row: dict[str, Any], g_e: dict[str, Any]) -> str:
    matched = matched_set(row)
    status = row.get("label_match_status")
    if status == "exact_match" or "supported by" in matched:
        return "accept_broad_support"
    if matched & {"standing on", "lying on"}:
        return "relabel_to_subtype"
    if status == "pair_has_other_predicate" and not (matched & SUPPORT_PREDICATES) and geometry_contradiction(g_e):
        return "reject_no_support"
    return "abstain"


def evidence_reason(row: dict[str, Any], route_label: str, g_e: dict[str, Any]) -> str:
    if route_label == "accept_broad_support":
        return "exact_supported_by_with_stable_support_evidence"
    if route_label == "relabel_to_subtype":
        return f"support_present_but_{support_subtype(row).replace(' ', '_')}_is_more_specific"
    if route_label == "reject_no_support":
        reasons = []
        if finite(g_e.get("xy_overlap_min_ratio")) and float(g_e["xy_overlap_min_ratio"]) < 0.02:
            reasons.append("low_xy_overlap")
        if finite(g_e.get("surface_gap_subject_bottom_to_object_top")) and float(g_e["surface_gap_subject_bottom_to_object_top"]) > 0.35:
            reasons.append("large_positive_surface_gap")
        if finite(g_e.get("center_delta_z")) and float(g_e["center_delta_z"]) <= 0.0:
            reasons.append("subject_not_above_object")
        return "geometry_contradiction_" + "_".join(reasons or ["no_support"])
    if generic_endpoint(row):
        return "generic_endpoint_or_ontology_overlap"
    if row.get("label_match_status") == "no_gt_for_pair":
        return "no_gt_not_negative_ambiguous_support"
    return "ambiguous_or_insufficient_support_subtype_evidence"


def read_semseg_cache_for_scan(scan_id: str, scan_root: Path, cache: dict[str, dict[int, dict[str, Any]]]) -> dict[int, dict[str, Any]]:
    if scan_id not in cache:
        path = scan_root / scan_id / "semseg.v2.json"
        cache[scan_id] = SCMAT.read_semseg(path) if path.exists() else {}
    return cache[scan_id]


def row_key(row: dict[str, Any]) -> str:
    return stable_hash(
        {
            "matched_gt_ids": row.get("matched_gt_ids") or [],
            "prediction_id": row.get("prediction_id"),
            "queue_kind": row.get("queue_kind"),
        }
    )


def validate_inputs(plan_summary: dict[str, Any], plan_errors: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0 or plan_errors:
        errors.append(
            {
                "error_type": "plan_validation_errors_present",
                "summary_count": plan_summary.get("validation_errors"),
                "rows": len(plan_errors),
            }
        )
    boundary = plan_summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "materializes_rows", "runs_learned_smoke", "test_usage", "validation_usage"]:
        expected = False
        if boundary.get(key) is not expected:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = args.rga_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_rga_queue", "path": rel_path(path)})
    if not args.scan_root.exists():
        errors.append({"error_type": "missing_scan_root", "path": rel_path(args.scan_root)})
    return errors


def scan_supported_by_candidates(rga_dir: Path, scan_root: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    line_counts: dict[str, int] = {}
    semseg_cache: dict[str, dict[int, dict[str, Any]]] = {}
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = rga_dir / name
        line_count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                line_count += 1
                row = json.loads(line)
                if row.get("predicate_label") != "supported by" or row.get("predicate_family") != "support_contact":
                    continue
                objects = read_semseg_cache_for_scan(str(row.get("scan_id")), scan_root, semseg_cache)
                g_e = SCMAT.semseg_features(row, objects)
                if not g_e or not all(finite(value) for value in g_e.values()):
                    continue
                route_label = route_label_for(row, g_e)
                if route_label not in ROUTE_LABELS:
                    continue
                subtype = support_subtype(row)
                candidate = {
                    "_source": row,
                    "class_pair": class_pair(row),
                    "directed_pair_id": directed_pair(row),
                    "evidence_reason": evidence_reason(row, route_label, g_e),
                    "g_e": g_e,
                    "generic_endpoint_visible": generic_endpoint(row),
                    "geometry_contradiction": geometry_contradiction(g_e),
                    "hard_surface_pair": hard_surface_pair(row),
                    "predicate_class_pair_rank": f"supported by::{class_pair(row)}::{row.get('rank_band')}",
                    "rank_band": row.get("rank_band"),
                    "route_label": route_label,
                    "row_key": row_key(row),
                    "scan_id": row.get("scan_id"),
                    "subtype_relabel_target": subtype,
                    "sort_key": (
                        1 if hard_surface_pair(row) else 0,
                        1 if route_label == "abstain" and generic_endpoint(row) else 0,
                        stable_hash(row_key(row)),
                    ),
                }
                buckets[route_label].append(candidate)
        line_counts[rel_path(path)] = line_count
    for rows in buckets.values():
        rows.sort(key=lambda item: item["sort_key"])
    return buckets, line_counts


def can_select(
    row: dict[str, Any],
    quotas: dict[str, int],
    counts: Counter[str],
    scan_counts: Counter[str],
    directed_pair_counts: Counter[str],
    class_pair_counts: Counter[str],
    selected_prediction_ids: set[str],
    hard_surface_count: int,
    generic_abstain_count: int,
    total_quota: int,
) -> bool:
    label = row["route_label"]
    source = row["_source"]
    if counts[label] >= quotas[label]:
        return False
    if source.get("prediction_id") in selected_prediction_ids:
        return False
    if scan_counts[str(row["scan_id"])] >= MAX_ROWS_PER_SCAN:
        return False
    if directed_pair_counts[str(row["directed_pair_id"])] >= MAX_ROWS_PER_DIRECTED_PAIR:
        return False
    if class_pair_counts[str(row["class_pair"])] >= MAX_ROWS_PER_CLASS_PAIR:
        return False
    if row["hard_surface_pair"] and hard_surface_count + 1 > int(MAX_HARD_SURFACE_SHARE * total_quota):
        return False
    if label == "abstain" and row["generic_endpoint_visible"]:
        if generic_abstain_count + 1 > int(MAX_GENERIC_ABSTAIN_SHARE * quotas["abstain"]):
            return False
    return True


def add_selection(
    row: dict[str, Any],
    selected: list[dict[str, Any]],
    counts: Counter[str],
    scan_counts: Counter[str],
    directed_pair_counts: Counter[str],
    class_pair_counts: Counter[str],
    selected_prediction_ids: set[str],
) -> None:
    selected.append(row)
    counts[row["route_label"]] += 1
    scan_counts[str(row["scan_id"])] += 1
    directed_pair_counts[str(row["directed_pair_id"])] += 1
    class_pair_counts[str(row["class_pair"])] += 1
    selected_prediction_ids.add(str(row["_source"].get("prediction_id")))


def materialize_selection(
    buckets: dict[str, list[dict[str, Any]]],
    per_label_quota: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    quotas = {label: per_label_quota for label in ROUTE_LABELS}
    total_quota = per_label_quota * len(ROUTE_LABELS)
    selected: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    scan_counts: Counter[str] = Counter()
    directed_pair_counts: Counter[str] = Counter()
    class_pair_counts: Counter[str] = Counter()
    selected_prediction_ids: set[str] = set()

    by_class_pair: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {label: [] for label in ROUTE_LABELS})
    for label, rows in buckets.items():
        for row in rows:
            by_class_pair[str(row["class_pair"])][label].append(row)

    class_pair_order = sorted(
        by_class_pair,
        key=lambda key: (
            sum(bool(by_class_pair[key][label]) for label in ROUTE_LABELS),
            min(sum(len(by_class_pair[key][label]) for label in ROUTE_LABELS), MAX_ROWS_PER_CLASS_PAIR),
            key,
        ),
        reverse=True,
    )

    def current_hard() -> int:
        return sum(1 for item in selected if item["hard_surface_pair"])

    def current_generic_abstain() -> int:
        return sum(1 for item in selected if item["route_label"] == "abstain" and item["generic_endpoint_visible"])

    # First pass: prefer class pairs where multiple labels can coexist.
    made_progress = True
    while made_progress and any(counts[label] < quotas[label] for label in ROUTE_LABELS):
        made_progress = False
        for class_pair_key in class_pair_order:
            available_labels = [label for label in ROUTE_LABELS if by_class_pair[class_pair_key][label]]
            if len(available_labels) < 2:
                continue
            for label in available_labels:
                if counts[label] >= quotas[label]:
                    continue
                rows = by_class_pair[class_pair_key][label]
                while rows:
                    row = rows.pop(0)
                    if can_select(
                        row,
                        quotas,
                        counts,
                        scan_counts,
                        directed_pair_counts,
                        class_pair_counts,
                        selected_prediction_ids,
                        current_hard(),
                        current_generic_abstain(),
                        total_quota,
                    ):
                        add_selection(row, selected, counts, scan_counts, directed_pair_counts, class_pair_counts, selected_prediction_ids)
                        made_progress = True
                        break

    # Second pass: fill any remaining quota label-wise.
    for label in ROUTE_LABELS:
        for row in buckets[label]:
            if counts[label] >= quotas[label]:
                break
            if can_select(
                row,
                quotas,
                counts,
                scan_counts,
                directed_pair_counts,
                class_pair_counts,
                selected_prediction_ids,
                current_hard(),
                current_generic_abstain(),
                total_quota,
            ):
                add_selection(row, selected, counts, scan_counts, directed_pair_counts, class_pair_counts, selected_prediction_ids)

    diagnostics = {
        "quota": quotas,
        "counts": dict(counts),
        "hard_surface_rows": current_hard(),
        "generic_abstain_rows": current_generic_abstain(),
        "total_quota": total_quota,
    }
    return selected, diagnostics


def pick_selection(buckets: dict[str, list[dict[str, Any]]], preferred: int, minimum: int) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    selected, diagnostics = materialize_selection(buckets, preferred)
    if all(diagnostics["counts"].get(label, 0) >= preferred for label in ROUTE_LABELS):
        return selected, "preferred_320row_target", diagnostics
    selected, diagnostics = materialize_selection(buckets, minimum)
    if all(diagnostics["counts"].get(label, 0) >= minimum for label in ROUTE_LABELS):
        return selected, "minimum_240row_fallback_target", diagnostics
    return selected, "failed_minimum_target", diagnostics


def q_e_from_g(row: dict[str, Any], g_e: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(key for key, value in g_e.items() if value is None)
    return {
        "evidence_axis": "semseg_obb_mesh_pose_contact",
        "generic_endpoint_visible": row["generic_endpoint_visible"],
        "geometry_contradiction": row["geometry_contradiction"],
        "mesh_semseg_obb_available": not missing,
        "missing_g_e_count": len(missing),
        "missing_g_e_fields": missing,
        "multi_view_feature_available": False,
        "observability_status": "ambiguous_or_low_observability" if row["route_label"] == "abstain" else "sufficient_for_route_label",
        "point_feature_available": False,
    }


def label_payload(row: dict[str, Any]) -> dict[str, Any]:
    route_label = row["route_label"]
    if route_label == "reject_no_support":
        p_rel = "reject"
        p_obs = "observable"
        p_obs_target = 1
    elif route_label == "abstain":
        p_rel = "undefined"
        p_obs = "abstain"
        p_obs_target = 0
    elif route_label == "relabel_to_subtype":
        p_rel = "accept_with_relabel"
        p_obs = "observable"
        p_obs_target = 1
    else:
        p_rel = "accept"
        p_obs = "observable"
        p_obs_target = 1
    return {
        "p_obs": p_obs,
        "p_obs_target": p_obs_target,
        "p_rel": p_rel,
        "supported_by_decomposition_label": route_label,
        "subtype_relabel_target": row["subtype_relabel_target"],
        "target_source": "train_gt_relation_role_plus_route_aware_materialization",
    }


def make_rows(selected: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    model_safe_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected, start=1):
        source = row["_source"]
        row_id = f"h002_r6_{stable_hash({'index': index, 'row_key': row['row_key']}, 16)}"
        g_e = row["g_e"]
        q_e = q_e_from_g(row, g_e)
        labels = label_payload(row)
        feature_blocks = {
            "G_e_mesh_pose_contact": g_e,
            "Q_e": q_e,
            "T_e": {
                "object_class_text": source.get("object_label"),
                "predicate_family": "superordinate_support",
                "predicate_label": "supported by",
                "predicate_text": "supported by",
                "subject_class_text": source.get("subject_label"),
            },
        }
        safe_row = {
            "dataset_name": DATASET_NAME,
            "feature_blocks": feature_blocks,
            "labels": labels,
            "model_use": "route_candidate_if_schema_audit_passes",
            "row_id": row_id,
            "schema_version": MODEL_SAFE_SCHEMA,
            "split": "train",
            "subset": "r6_superordinate_support_decomposition",
        }
        hidden_row = {
            "audit_status": source.get("audit_status"),
            "candidate_role": source.get("label_match_status"),
            "class_pair": row["class_pair"],
            "decomposition_label": row["route_label"],
            "directed_pair_id": row["directed_pair_id"],
            "evidence_reason": row["evidence_reason"],
            "generic_endpoint_visible": row["generic_endpoint_visible"],
            "geometry_status": source.get("geometry_status"),
            "h001_verification_status": source.get("h001_verification_status"),
            "hard_surface_pair": row["hard_surface_pair"],
            "hidden_schema": HIDDEN_SCHEMA,
            "label_match_status": source.get("label_match_status"),
            "machine_hint": source.get("machine_hint"),
            "matched_gt_ids": source.get("matched_gt_ids", []),
            "matched_predicates": source.get("matched_predicates", []),
            "object_id": source.get("object_id"),
            "object_label": source.get("object_label"),
            "p_geom_valid": source.get("p_geom_valid"),
            "predicate_class_pair": f"supported by::{row['class_pair']}",
            "predicate_class_pair_rank": row["predicate_class_pair_rank"],
            "predicate_label": "supported by",
            "prediction_id": source.get("prediction_id"),
            "queue_kind": source.get("queue_kind"),
            "rank_band": source.get("rank_band"),
            "reason_codes": source.get("reason_codes", []),
            "row_id": row_id,
            "row_key": row["row_key"],
            "scan_id": source.get("scan_id"),
            "semantic_rank": source.get("semantic_rank"),
            "semantic_score_norm": source.get("semantic_score_norm"),
            "semantic_score_raw": source.get("semantic_score_raw"),
            "source_id": source.get("source_id"),
            "subgraph_id": source.get("subgraph_id"),
            "subject_id": source.get("subject_id"),
            "subject_label": source.get("subject_label"),
            "subtype_relabel_target": row["subtype_relabel_target"],
        }
        audit_row = {
            "evidence_reason": row["evidence_reason"],
            "feature_summary": {
                "center_delta_z": g_e.get("center_delta_z"),
                "surface_gap_subject_bottom_to_object_top": g_e.get("surface_gap_subject_bottom_to_object_top"),
                "xy_overlap_min_ratio": g_e.get("xy_overlap_min_ratio"),
            },
            "generic_endpoint_visible": row["generic_endpoint_visible"],
            "object_class_text": source.get("object_label"),
            "route_label": row["route_label"],
            "row_id": row_id,
            "subject_class_text": source.get("subject_label"),
            "subtype_relabel_target": row["subtype_relabel_target"],
        }
        model_safe_rows.append(safe_row)
        candidate_rows.append(safe_row)
        hidden_rows.append(hidden_row)
        audit_rows.append(audit_row)
    return candidate_rows, model_safe_rows, hidden_rows, audit_rows


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


def quota_audit_rows(hidden_rows: list[dict[str, Any]], per_label_quota: int) -> list[dict[str, Any]]:
    counts = Counter(row["decomposition_label"] for row in hidden_rows)
    return [
        {
            "route_label": label,
            "expected": per_label_quota,
            "actual": counts[label],
            "passed": counts[label] == per_label_quota,
        }
        for label in ROUTE_LABELS
    ]


def cell_balance_audit_rows(hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_class_pair: dict[str, Counter[str]] = defaultdict(Counter)
    for row in hidden_rows:
        by_class_pair[str(row["class_pair"])][str(row["decomposition_label"])] += 1
    rows: list[dict[str, Any]] = []
    for class_pair_key, counts in sorted(by_class_pair.items()):
        labels = [label for label, count in counts.items() if count > 0]
        if len(labels) >= 2:
            rows.append(
                {
                    "class_pair": class_pair_key,
                    "labels_present": ";".join(sorted(labels)),
                    "num_labels": len(labels),
                    "rows": sum(counts.values()),
                    **{f"count_{label}": counts.get(label, 0) for label in ROUTE_LABELS},
                }
            )
    return rows


def selection_profile_rows(hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes = [
        ("decomposition_label", lambda row: row["decomposition_label"]),
        ("subtype_relabel_target", lambda row: row.get("subtype_relabel_target")),
        ("rank_band", lambda row: row.get("rank_band")),
        ("label_match_status", lambda row: row.get("label_match_status")),
        ("hard_surface_pair", lambda row: str(bool(row.get("hard_surface_pair")))),
        ("generic_endpoint_visible", lambda row: str(bool(row.get("generic_endpoint_visible")))),
    ]
    rows: list[dict[str, Any]] = []
    for axis, getter in axes:
        counts = Counter(str(getter(row)) for row in hidden_rows)
        for value, count in sorted(counts.items()):
            rows.append({"axis": axis, "value": value, "rows": count})
    return rows


def schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_name": DATASET_NAME,
        "model_safe_schema": MODEL_SAFE_SCHEMA,
        "hidden_schema": HIDDEN_SCHEMA,
        "route": {
            "route_id": "R6",
            "family": "superordinate_support",
            "relation": "supported by",
            "route_type": "superordinate_support_decomposition_route",
            "target_axis": "accept_relabel_abstain",
        },
        "labels": ROUTE_LABELS,
        "model_safe_blocks": ["T_e", "G_e_mesh_pose_contact", "Q_e", "labels"],
        "hidden_only_fields": sorted(BLOCKED_MODEL_SAFE_FIELDS),
    }


def control_manifest() -> dict[str, Any]:
    return {
        "required_next_controls": [
            "class_pair_only",
            "source_score_rank_hidden",
            "generic_endpoint_only",
            "hard_surface_slice",
            "wrong_pair_geometry",
            "shuffled_G_within_class_pair",
            "no_GT_not_negative",
            "subtype_relabel_consistency",
        ],
        "blocked_before_schema_audit_passes": ["learned_smoke", "paper_evidence", "calibrated_p_rel_p_obs_claim"],
    }


def validate_materialized_rows(
    model_safe_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    per_label_quota: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    quota_rows = quota_audit_rows(hidden_rows, per_label_quota)
    cell_rows = cell_balance_audit_rows(hidden_rows)
    hidden_ids = {row["row_id"] for row in hidden_rows}
    safe_ids = {row["row_id"] for row in model_safe_rows}
    blocked_hits = Counter()
    finite_rows = 0
    for row in model_safe_rows:
        blocked_hits.update(nested_key_hits(row, BLOCKED_MODEL_SAFE_FIELDS))
        features = row.get("feature_blocks", {}).get("G_e_mesh_pose_contact", {})
        if features and all(finite(value) for value in features.values()):
            finite_rows += 1
    counts = Counter(row["decomposition_label"] for row in hidden_rows)
    hard_surface_rows = sum(1 for row in hidden_rows if row.get("hard_surface_pair"))
    abstain_rows = [row for row in hidden_rows if row.get("decomposition_label") == "abstain"]
    generic_abstain_rows = sum(1 for row in abstain_rows if row.get("generic_endpoint_visible"))
    class_pair_counts = Counter(row["class_pair"] for row in hidden_rows)
    scan_counts = Counter(row["scan_id"] for row in hidden_rows)
    directed_pair_counts = Counter(row["directed_pair_id"] for row in hidden_rows)

    checks = [
        ("row_count", len(model_safe_rows), per_label_quota * len(ROUTE_LABELS), len(model_safe_rows) == per_label_quota * len(ROUTE_LABELS)),
        ("hidden_manifest_count", len(hidden_rows), per_label_quota * len(ROUTE_LABELS), len(hidden_rows) == per_label_quota * len(ROUTE_LABELS)),
        ("row_id_join_integrity", len(safe_ids & hidden_ids), len(model_safe_rows), safe_ids == hidden_ids),
        ("blocked_fields_absent_from_model_safe", sum(blocked_hits.values()), 0, not blocked_hits),
        ("finite_G_e_rows", finite_rows, len(model_safe_rows), finite_rows == len(model_safe_rows)),
        ("mixed_class_pair_cells", len(cell_rows), MIN_MIXED_CLASS_PAIR_CELLS, len(cell_rows) >= MIN_MIXED_CLASS_PAIR_CELLS),
        ("max_rows_per_scan", max(scan_counts.values(), default=0), MAX_ROWS_PER_SCAN, max(scan_counts.values(), default=0) <= MAX_ROWS_PER_SCAN),
        (
            "max_rows_per_directed_pair",
            max(directed_pair_counts.values(), default=0),
            MAX_ROWS_PER_DIRECTED_PAIR,
            max(directed_pair_counts.values(), default=0) <= MAX_ROWS_PER_DIRECTED_PAIR,
        ),
        (
            "max_rows_per_subject_object_class_pair",
            max(class_pair_counts.values(), default=0),
            MAX_ROWS_PER_CLASS_PAIR,
            max(class_pair_counts.values(), default=0) <= MAX_ROWS_PER_CLASS_PAIR,
        ),
        (
            "hard_surface_share",
            hard_surface_rows / max(len(hidden_rows), 1),
            MAX_HARD_SURFACE_SHARE,
            hard_surface_rows / max(len(hidden_rows), 1) <= MAX_HARD_SURFACE_SHARE,
        ),
        (
            "generic_endpoint_abstain_share",
            generic_abstain_rows / max(len(abstain_rows), 1),
            MAX_GENERIC_ABSTAIN_SHARE,
            generic_abstain_rows / max(len(abstain_rows), 1) <= MAX_GENERIC_ABSTAIN_SHARE,
        ),
    ]
    schema_rows = [
        {
            "check": name,
            "observed": observed,
            "expected": expected,
            "passed": passed,
            "details": json.dumps(dict(blocked_hits), sort_keys=True) if name == "blocked_fields_absent_from_model_safe" else "",
        }
        for name, observed, expected, passed in checks
    ]
    for row in quota_rows:
        if row["passed"] is not True:
            errors.append({"error_type": "quota_failed", **row})
    for row in schema_rows:
        if row["passed"] is not True:
            errors.append({"error_type": "schema_or_balance_check_failed", **row})
    summary_counts = {
        "decomposition_label_counts": dict(sorted(counts.items())),
        "finite_g_e_rows": finite_rows,
        "generic_abstain_rows": generic_abstain_rows,
        "hard_surface_rows": hard_surface_rows,
        "max_rows_per_class_pair": max(class_pair_counts.values(), default=0),
        "max_rows_per_directed_pair": max(directed_pair_counts.values(), default=0),
        "max_rows_per_scan": max(scan_counts.values(), default=0),
        "mixed_class_pair_cells": len(cell_rows),
        "model_safe_rows": len(model_safe_rows),
        "total_rows": len(model_safe_rows),
        "unique_class_pairs": len(class_pair_counts),
        "unique_scans": len(scan_counts),
    }
    return errors, quota_rows, schema_rows, {"cell_rows": cell_rows, "counts": summary_counts}


def report_text(summary: dict[str, Any]) -> str:
    counts = summary.get("counts", {})
    return "\n".join(
        [
            "# H002 R6 Supported-By Decomposition Candidate Materialization",
            "",
            "## Status",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Materialized Rows",
            "",
            f"- total rows: `{counts.get('total_rows')}`",
            f"- label counts: `{counts.get('decomposition_label_counts')}`",
            f"- unique scans: `{counts.get('unique_scans')}`",
            f"- unique class pairs: `{counts.get('unique_class_pairs')}`",
            f"- mixed class-pair cells: `{counts.get('mixed_class_pair_cells')}`",
            f"- hard surface rows: `{counts.get('hard_surface_rows')}`",
            f"- generic abstain rows: `{counts.get('generic_abstain_rows')}`",
            "",
            "## Boundary",
            "",
            "- Train-only candidate materialization.",
            "- No learned smoke/model training.",
            "- No validation/test usage.",
            "- H001 artifacts are not modified.",
            "- No paper-level evidence is claimed.",
            "",
            "## Next",
            "",
            "```text",
            str(summary["next_todo"]),
            "```",
        ]
    )


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    validation_errors = validate_inputs(plan_summary, plan_errors, args)

    selected: list[dict[str, Any]] = []
    line_counts: dict[str, int] = {}
    selection_mode = "blocked_input_errors"
    diagnostics: dict[str, Any] = {}
    candidate_rows: list[dict[str, Any]] = []
    model_safe_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    quota_rows: list[dict[str, Any]] = []
    schema_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    selection_profile: list[dict[str, Any]] = []
    counts: dict[str, Any] = {}

    if not validation_errors:
        buckets, line_counts = scan_supported_by_candidates(args.rga_dir, args.scan_root)
        selected, selection_mode, diagnostics = pick_selection(buckets, preferred=80, minimum=60)
        if selection_mode == "failed_minimum_target":
            validation_errors.append(
                {
                    "error_type": "minimum_quota_not_met",
                    "diagnostics": diagnostics,
                }
            )
        else:
            per_label_quota = 80 if selection_mode == "preferred_320row_target" else 60
            candidate_rows, model_safe_rows, hidden_rows, audit_rows = make_rows(selected)
            materialization_errors, quota_rows, schema_rows, extra = validate_materialized_rows(
                model_safe_rows,
                hidden_rows,
                per_label_quota,
            )
            validation_errors.extend(materialization_errors)
            cell_rows = extra["cell_rows"]
            counts = extra["counts"]
            selection_profile = selection_profile_rows(hidden_rows)

    status = STATUS_ERROR if validation_errors else STATUS_READY
    selected_path = "blocked_input_or_materialization_errors" if validation_errors else f"materialized_{selection_mode}"
    next_todo = EXPECTED_PLAN_NEXT if validation_errors else NEXT_TODO
    output_paths = {
        "audit_view": rel_path(args.output_dir / "audit_view.jsonl"),
        "candidate_rows": rel_path(args.output_dir / "candidate_rows.jsonl"),
        "cell_balance_audit": rel_path(args.output_dir / "cell_balance_audit.csv"),
        "control_manifest": rel_path(args.output_dir / "control_manifest.json"),
        "hidden_manifest": rel_path(args.output_dir / "hidden_manifest.jsonl"),
        "model_safe_rows": rel_path(args.output_dir / "model_safe_rows.jsonl"),
        "quota_audit": rel_path(args.output_dir / "quota_audit.csv"),
        "report": rel_path(args.output_dir / "report.md"),
        "schema": rel_path(args.output_dir / "schema.json"),
        "schema_precheck": rel_path(args.output_dir / "schema_precheck.csv"),
        "selection_profile": rel_path(args.output_dir / "selection_profile.csv"),
        "summary": rel_path(args.output_dir / "summary.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }
    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": True,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_candidate_materialization",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "counts": counts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_name": DATASET_NAME,
        "diagnostics": diagnostics,
        "input_paths": {
            "plan_summary": rel_path(args.plan_dir / "summary.json"),
            "rga_dir": rel_path(args.rga_dir),
            "scan_root": rel_path(args.scan_root),
        },
        "line_counts": line_counts,
        "next_todo": next_todo,
        "output_paths": output_paths,
        "route": {
            "route_id": "R6",
            "family": "superordinate_support",
            "relation": "supported by",
            "route_type": "superordinate_support_decomposition_route",
            "target_axis": "accept_relabel_abstain",
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "selection_mode": selection_mode,
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_jsonl(args.output_dir / "candidate_rows.jsonl", candidate_rows)
    write_jsonl(args.output_dir / "model_safe_rows.jsonl", model_safe_rows)
    write_jsonl(args.output_dir / "hidden_manifest.jsonl", hidden_rows)
    write_jsonl(args.output_dir / "audit_view.jsonl", audit_rows)
    write_csv(args.output_dir / "quota_audit.csv", quota_rows)
    write_csv(args.output_dir / "schema_precheck.csv", schema_rows)
    write_csv(args.output_dir / "cell_balance_audit.csv", cell_rows)
    write_csv(args.output_dir / "selection_profile.csv", selection_profile)
    write_json(args.output_dir / "schema.json", schema())
    write_json(args.output_dir / "control_manifest.json", control_manifest())
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(report_text(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
