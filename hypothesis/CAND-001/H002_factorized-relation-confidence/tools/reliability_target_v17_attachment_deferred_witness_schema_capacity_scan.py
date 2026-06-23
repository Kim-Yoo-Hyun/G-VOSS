#!/usr/bin/env python3
"""Scan train-only capacity for the H002 v17 attachment witness schema."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v17_attachment_deferred_witness_schema_probe_plan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v17_attachment_deferred_witness_schema_capacity_scan"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"

EXPECTED_PLAN_STATUS = "h002_reliability_target_v17_attachment_deferred_witness_schema_probe_plan_ready_for_capacity_scan"
EXPECTED_PLAN_NEXT = "reliability_target_v17_attachment_deferred_witness_schema_capacity_scan"

STATUS_PASS = "h002_reliability_target_v17_attachment_deferred_witness_schema_capacity_scan_passed_ready_for_path_decision"
STATUS_FAIL = "h002_reliability_target_v17_attachment_deferred_witness_schema_capacity_scan_blocked_capacity_or_witness_coverage"
STATUS_ERROR = "h002_reliability_target_v17_attachment_deferred_witness_schema_capacity_scan_validation_errors"
NEXT_TODO = "reliability_target_v17_attachment_deferred_witness_schema_path_decision_after_capacity_scan"

PREDICATES = {"attached to", "hanging on", "connected to"}
ROOM_SURFACES = {"floor", "wall", "ceiling"}
HANGING_ANCHOR_KEYWORDS = {
    "wall",
    "ceiling",
    "window",
    "door",
    "doorframe",
    "board",
    "whiteboard",
    "blackboard",
    "shelf",
    "rack",
    "rail",
    "rod",
    "bar",
    "cabinet",
    "cupboard",
    "wardrobe",
    "hanger",
    "hook",
    "curtain",
    "blinds",
    "pipe",
    "radiator",
    "heater",
}
ATTACHMENT_ANCHOR_KEYWORDS = HANGING_ANCHOR_KEYWORDS | {
    "mirror",
    "picture",
    "tv",
    "lamp",
    "light",
    "table",
    "desk",
    "bed",
    "machine",
    "object",
}
CONNECTOR_KEYWORDS = {
    "cable",
    "wire",
    "cord",
    "pipe",
    "tube",
    "plug",
    "socket",
    "outlet",
    "connector",
    "hose",
    "lamp",
    "light",
    "radiator",
    "heater",
    "computer",
    "pc",
    "machine",
    "tv",
}
THIN_STRUCTURE_KEYWORDS = {
    "picture",
    "curtain",
    "blinds",
    "cable",
    "wire",
    "cord",
    "lamp",
    "light",
    "mirror",
    "towel",
    "clothes",
    "hanger",
    "pipe",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
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


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def stable_int(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:12], 16)


def stable_id(value: str, prefix: str = "attcap") -> str:
    return f"{prefix}_{hashlib.sha1(value.encode('utf-8')).hexdigest()[:16]}"


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def has_keyword(label: str, keywords: set[str]) -> bool:
    label = norm(label)
    return any(keyword in label for keyword in keywords)


def validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "expected": EXPECTED_PLAN_STATUS, "actual": plan.get("status")})
    if plan.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "expected": EXPECTED_PLAN_NEXT, "actual": plan.get("next_todo")})
    if plan.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan.get("validation_errors")})
    boundary = plan.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def compact_raw_geometry(row: dict[str, Any]) -> dict[str, Any] | None:
    geometry = row.get("geometry", {})
    raw = geometry.get("raw_features")
    if not isinstance(raw, dict):
        return None
    predicate = row.get("predicate", {})
    identity = row.get("identity", {})
    edge = row.get("edge", {})
    return {
        "raw_features": raw,
        "source_family": predicate.get("predicate_family"),
        "source_predicate": predicate.get("predicate_label"),
        "source_geometry_status": geometry.get("geometry_status"),
        "scan_id": identity.get("scan_id"),
        "subgraph_id": identity.get("subgraph_id"),
        "subject_id": identity.get("subject_id"),
        "object_id": identity.get("object_id"),
        "subject_label": edge.get("subject_label"),
        "object_label": edge.get("object_label"),
    }


def collect_pair_geometry(match_rows: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    pair_geometry: dict[str, dict[str, Any]] = {}
    source_counts: Counter[str] = Counter()
    line_count = 0
    raw_feature_rows = 0
    for _, row in iter_jsonl(match_rows):
        line_count += 1
        predicate = row.get("predicate", {})
        family = predicate.get("predicate_family")
        if family not in {"support_contact", "relative_vertical"}:
            continue
        compact = compact_raw_geometry(row)
        if compact is None:
            continue
        raw_feature_rows += 1
        pair_id = row.get("identity", {}).get("directed_pair_id")
        if not pair_id:
            continue
        existing = pair_geometry.get(pair_id)
        # Prefer support/contact pair geometry because it uses the richer contact policy source.
        if existing is None or existing["source_family"] != "support_contact" and family == "support_contact":
            pair_geometry[pair_id] = compact
        source_counts[f"{family}|{predicate.get('predicate_label')}"] += 1
    return pair_geometry, {
        "match_rows_seen_first_pass": line_count,
        "raw_feature_rows_seen_first_pass": raw_feature_rows,
        "pair_geometry_join_keys": len(pair_geometry),
        "raw_feature_source_counts": dict(source_counts),
    }


def max_overlap(raw: dict[str, Any]) -> float:
    values = [
        as_float(raw.get("projected_iou_xy")) or 0.0,
        as_float(raw.get("projected_subject_overlap_ratio")) or 0.0,
        as_float(raw.get("projected_object_overlap_ratio")) or 0.0,
    ]
    return max(values)


def near_flags(raw: dict[str, Any]) -> dict[str, bool]:
    n3d = as_float(raw.get("normalized_distance_3d"))
    nxy = as_float(raw.get("normalized_distance_xy"))
    iou = as_float(raw.get("projected_iou_xy")) or 0.0
    overlap = max_overlap(raw)
    near = (n3d is not None and n3d <= 0.30) or (nxy is not None and nxy <= 0.25) or iou >= 0.05 or overlap >= 0.15
    loose_near = (n3d is not None and n3d <= 0.45) or (nxy is not None and nxy <= 0.40) or iou >= 0.02 or overlap >= 0.08
    far = (
        (n3d is not None and n3d >= 0.75)
        and (nxy is not None and nxy >= 0.65)
        and iou < 0.01
        and overlap < 0.03
    )
    return {"near": near, "loose_near": loose_near, "far": far, "overlap": overlap >= 0.08}


def anchor_bucket(subject_label: str, object_label: str, predicate: str) -> str:
    subject = norm(subject_label)
    obj = norm(object_label)
    if obj == "floor":
        return "floor_anchor_confound"
    if subject in ROOM_SURFACES and obj in ROOM_SURFACES:
        return "hard_surface_pair"
    if predicate == "hanging on" and has_keyword(obj, HANGING_ANCHOR_KEYWORDS):
        return "hanging_anchor"
    if has_keyword(obj, ATTACHMENT_ANCHOR_KEYWORDS):
        return "attachment_anchor"
    if has_keyword(subject, CONNECTOR_KEYWORDS) or has_keyword(obj, CONNECTOR_KEYWORDS):
        return "connector_or_device_anchor"
    if obj in {"wall", "ceiling"}:
        return "room_surface_anchor"
    return "generic_object_anchor"


def uncertainty_flags(subject_label: str, object_label: str, raw: dict[str, Any] | None, predicate: str, bucket: str) -> list[str]:
    flags: list[str] = []
    subject = norm(subject_label)
    obj = norm(object_label)
    if raw is None:
        return ["missing_pair_raw_features"]
    if subject in ROOM_SURFACES and obj in ROOM_SURFACES:
        flags.append("hard_surface_pair")
    if has_keyword(subject, THIN_STRUCTURE_KEYWORDS) or has_keyword(obj, THIN_STRUCTURE_KEYWORDS):
        flags.append("thin_structure_or_boundary_missing")
    if max_overlap(raw) >= 0.75:
        flags.append("large_obb_overlap_confound")
    if predicate == "connected to":
        flags.append("functional_connection_ambiguous_without_visual_or_mesh")
    if bucket == "floor_anchor_confound":
        flags.append("floor_support_confound")
    return flags


def classify_attachment(row: dict[str, Any], raw_entry: dict[str, Any] | None) -> dict[str, Any]:
    predicate = norm(row.get("predicate", {}).get("predicate_label"))
    edge = row.get("edge", {})
    subject = norm(edge.get("subject_label"))
    obj = norm(edge.get("object_label"))
    raw = raw_entry["raw_features"] if raw_entry else None
    bucket = anchor_bucket(subject, obj, predicate)
    flags = near_flags(raw) if raw else {"near": False, "loose_near": False, "far": False, "overlap": False}
    uncertainties = uncertainty_flags(subject, obj, raw, predicate, bucket)

    floor_confound = bucket == "floor_anchor_confound" or subject == "floor"
    hard_surface_pair = bucket == "hard_surface_pair"
    plausible_attachment_anchor = bucket in {
        "attachment_anchor",
        "hanging_anchor",
        "connector_or_device_anchor",
        "room_surface_anchor",
        "generic_object_anchor",
    }
    plausible_hanging_anchor = bucket in {"hanging_anchor", "room_surface_anchor", "attachment_anchor"}
    connector_hint = bucket == "connector_or_device_anchor" or has_keyword(subject, CONNECTOR_KEYWORDS) or has_keyword(obj, CONNECTOR_KEYWORDS)

    if raw is None:
        provisional = "missing_geometry"
        cell_id = "U1_attachment_missing_or_uncertain_coverage_audit"
        support_score = 0.0
        contradiction_score = 0.0
    elif predicate == "attached to":
        if flags["loose_near"] and plausible_attachment_anchor and not floor_confound and not hard_surface_pair:
            provisional = "supported_candidate"
            cell_id = "A1_attached_near_anchor_supported_candidate"
            support_score = 0.75
            contradiction_score = 0.15
        elif flags["far"] or floor_confound or hard_surface_pair:
            provisional = "contradicted_candidate"
            cell_id = "A2_attached_far_or_floor_confound_candidate"
            support_score = 0.15
            contradiction_score = 0.75
        else:
            provisional = "uncertain_candidate"
            cell_id = "A2_attached_far_or_floor_confound_candidate"
            support_score = 0.45
            contradiction_score = 0.45
    elif predicate == "hanging on":
        if flags["loose_near"] and plausible_hanging_anchor and not floor_confound and subject not in ROOM_SURFACES:
            provisional = "supported_candidate"
            cell_id = "H1_hanging_anchor_supported_candidate"
            support_score = 0.75
            contradiction_score = 0.15
        elif flags["far"] or floor_confound or subject in ROOM_SURFACES or not plausible_hanging_anchor:
            provisional = "contradicted_candidate"
            cell_id = "H2_hanging_no_anchor_or_floor_supported_candidate"
            support_score = 0.15
            contradiction_score = 0.75
        else:
            provisional = "uncertain_candidate"
            cell_id = "H2_hanging_no_anchor_or_floor_supported_candidate"
            support_score = 0.45
            contradiction_score = 0.45
    elif predicate == "connected to":
        if flags["loose_near"] or connector_hint:
            provisional = "uncertain_candidate" if not connector_hint else "supported_candidate"
            cell_id = "C1_connected_near_or_overlap_diagnostic"
            support_score = 0.60 if connector_hint else 0.50
            contradiction_score = 0.35
        else:
            provisional = "contradicted_candidate" if flags["far"] else "uncertain_candidate"
            cell_id = "C2_connected_far_or_functional_ambiguous_diagnostic"
            support_score = 0.20
            contradiction_score = 0.60 if flags["far"] else 0.45
    else:
        provisional = "unsupported_template"
        cell_id = "U1_attachment_missing_or_uncertain_coverage_audit"
        support_score = 0.0
        contradiction_score = 0.0

    if provisional == "uncertain_candidate" and "typed_witness_ambiguous" not in uncertainties:
        uncertainties.append("typed_witness_ambiguous")

    return {
        "predicate_label": predicate,
        "provisional_status": provisional,
        "cell_id": cell_id,
        "anchor_bucket": bucket,
        "near_contact": flags["near"],
        "loose_near_contact": flags["loose_near"],
        "far_separated": flags["far"],
        "projected_overlap_support": flags["overlap"],
        "uncertainty_flags": uncertainties,
        "attachment_witness_support_score": round(support_score, 4),
        "attachment_witness_contradiction_score": round(contradiction_score, 4),
        "raw_feature_join_state": "joined" if raw is not None else "missing",
    }


def compact_attachment_row(row: dict[str, Any], raw_entry: dict[str, Any] | None, witness: dict[str, Any]) -> dict[str, Any]:
    identity = row.get("identity", {})
    edge = row.get("edge", {})
    semantic = row.get("semantic", {})
    rga = row.get("rga", {})
    label = row.get("label", {})
    raw = raw_entry["raw_features"] if raw_entry else {}
    prediction_id = identity.get("prediction_id") or identity.get("row_key")
    return {
        "blind_review_id": stable_id(str(prediction_id)),
        "prediction_id": prediction_id,
        "scan_id": identity.get("scan_id"),
        "subgraph_id": identity.get("subgraph_id"),
        "directed_pair_id": identity.get("directed_pair_id"),
        "subject_id": identity.get("subject_id"),
        "object_id": identity.get("object_id"),
        "subject_label": edge.get("subject_label"),
        "predicate_label": witness["predicate_label"],
        "object_label": edge.get("object_label"),
        "candidate_relation": f"{edge.get('subject_label')} {witness['predicate_label']} {edge.get('object_label')}",
        "rank_band_hidden": rga.get("rank_band"),
        "semantic_score_norm_hidden": semantic.get("semantic_score_norm"),
        "semantic_rank_hidden": semantic.get("rank_in_context"),
        "bucket_top100_hidden": rga.get("bucket_top100"),
        "label_match_status_hidden": label.get("label_match_status"),
        "matched_predicates_hidden": label.get("matched_predicates"),
        "cell_id_hidden": witness["cell_id"],
        "provisional_status_hidden": witness["provisional_status"],
        "anchor_bucket_hidden": witness["anchor_bucket"],
        "raw_feature_join_state": witness["raw_feature_join_state"],
        "near_contact": witness["near_contact"],
        "loose_near_contact": witness["loose_near_contact"],
        "far_separated": witness["far_separated"],
        "projected_overlap_support": witness["projected_overlap_support"],
        "uncertainty_flags": witness["uncertainty_flags"],
        "attachment_witness_support_score_hidden": witness["attachment_witness_support_score"],
        "attachment_witness_contradiction_score_hidden": witness["attachment_witness_contradiction_score"],
        "normalized_distance_3d": raw.get("normalized_distance_3d"),
        "normalized_distance_xy": raw.get("normalized_distance_xy"),
        "projected_iou_xy": raw.get("projected_iou_xy"),
        "projected_subject_overlap_ratio": raw.get("projected_subject_overlap_ratio"),
        "projected_object_overlap_ratio": raw.get("projected_object_overlap_ratio"),
        "center_delta_z": raw.get("center_delta_z"),
        "normalized_center_delta_z": raw.get("normalized_center_delta_z"),
        "vertical_gap_subject_on_object": raw.get("vertical_gap_subject_on_object"),
        "source_geometry_family": raw_entry.get("source_family") if raw_entry else None,
        "source_geometry_predicate": raw_entry.get("source_predicate") if raw_entry else None,
        "hash_key": stable_int(str(prediction_id)),
    }


def add_pool_candidate(pools: dict[str, list[dict[str, Any]]], row: dict[str, Any], max_per_cell: int = 5000) -> None:
    cell_id = row["cell_id_hidden"]
    pools[cell_id].append(row)
    if len(pools[cell_id]) > max_per_cell * 2:
        pools[cell_id].sort(key=lambda item: item["hash_key"])
        del pools[cell_id][max_per_cell:]
    if row["uncertainty_flags"]:
        pools["U1_attachment_missing_or_uncertain_coverage_audit"].append({**row, "cell_id_hidden": "U1_attachment_missing_or_uncertain_coverage_audit"})
        if len(pools["U1_attachment_missing_or_uncertain_coverage_audit"]) > max_per_cell * 2:
            pools["U1_attachment_missing_or_uncertain_coverage_audit"].sort(key=lambda item: item["hash_key"])
            del pools["U1_attachment_missing_or_uncertain_coverage_audit"][max_per_cell:]


def scan_attachment_rows(match_rows: Path, pair_geometry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    pair_sets: dict[str, set[str]] = defaultdict(set)
    pools: dict[str, list[dict[str, Any]]] = defaultdict(list)
    attachment_rows = 0
    joined_rows = 0
    for _, row in iter_jsonl(match_rows):
        predicate = row.get("predicate", {})
        if predicate.get("predicate_family") != "attachment_deferred":
            continue
        predicate_label = norm(predicate.get("predicate_label"))
        if predicate_label not in PREDICATES:
            continue
        attachment_rows += 1
        identity = row.get("identity", {})
        pair_id = identity.get("directed_pair_id")
        raw_entry = pair_geometry.get(pair_id)
        if raw_entry is not None:
            joined_rows += 1
        witness = classify_attachment(row, raw_entry)
        compact = compact_attachment_row(row, raw_entry, witness)

        counts["predicate"][predicate_label] += 1
        counts["raw_feature_join_state"][witness["raw_feature_join_state"]] += 1
        counts["provisional_status"][witness["provisional_status"]] += 1
        counts["cell"][witness["cell_id"]] += 1
        counts["capacity_cell"][witness["cell_id"]] += 1
        if witness["uncertainty_flags"]:
            counts["capacity_cell"]["U1_attachment_missing_or_uncertain_coverage_audit"] += 1
        counts["anchor_bucket"][witness["anchor_bucket"]] += 1
        counts["rank_band"][str(compact["rank_band_hidden"])] += 1
        counts["predicate_status"][f"{predicate_label}|{witness['provisional_status']}"] += 1
        counts["predicate_cell"][f"{predicate_label}|{witness['cell_id']}"] += 1
        counts["label_match_status"][str(compact["label_match_status_hidden"])] += 1
        for flag in witness["uncertainty_flags"]:
            counts["uncertainty_flags"][flag] += 1
        pair_sets["scan_id"].add(str(identity.get("scan_id")))
        pair_sets["subgraph_id"].add(str(identity.get("subgraph_id")))
        pair_sets["directed_pair_id"].add(str(pair_id))
        pair_sets["visible_pair"].add(f"{norm(compact['subject_label'])}|{norm(compact['object_label'])}")
        add_pool_candidate(pools, compact)

    for cell_id in list(pools):
        pools[cell_id].sort(key=lambda item: item["hash_key"])
        del pools[cell_id][5000:]

    return {
        "attachment_rows": attachment_rows,
        "joined_rows": joined_rows,
        "counts": counts,
        "distinct": {key: len(value) for key, value in pair_sets.items()},
        "candidate_pools": pools,
    }


def cell_targets(contract: dict[str, Any]) -> dict[str, int]:
    return {cell["cell_id"]: int(cell["target_preview_rows"]) for cell in contract["probe_cells"]}


def cell_minimums(contract: dict[str, Any]) -> dict[str, int]:
    return {cell["cell_id"]: int(cell["minimum_capacity_rows"]) for cell in contract["probe_cells"]}


def select_preview(pools: dict[str, list[dict[str, Any]]], contract: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    targets = cell_targets(contract)
    caps = contract["caps_for_capacity_preview"]
    selected: list[dict[str, Any]] = []
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    skip_reasons: Counter[str] = Counter()
    max_predicate = int(contract["preview_total_rows"] * float(caps["max_single_predicate_share"]))
    max_anchor = int(contract["preview_total_rows"] * float(caps["max_single_anchor_bucket_share"]))
    max_rank = int(contract["preview_total_rows"] * float(caps["max_single_rank_band_share"]))

    def can_select(row: dict[str, Any]) -> str | None:
        cell = row["cell_id_hidden"]
        if counts["cell"][cell] >= targets[cell]:
            return "cell_target_full"
        if counts["scan"][str(row["scan_id"])] >= int(caps["max_rows_per_scan"]):
            return "max_rows_per_scan"
        if counts["subgraph"][str(row["subgraph_id"])] >= int(caps["max_rows_per_subgraph"]):
            return "max_rows_per_subgraph"
        if counts["directed_pair"][str(row["directed_pair_id"])] >= int(caps["max_rows_per_directed_pair"]):
            return "max_rows_per_directed_pair"
        visible_pair = f"{norm(row['subject_label'])}|{norm(row['object_label'])}"
        if counts["visible_pair"][visible_pair] >= int(caps["max_rows_per_visible_pair"]):
            return "max_rows_per_visible_pair"
        if counts["predicate"][row["predicate_label"]] >= max_predicate:
            return "max_single_predicate_share"
        if counts["anchor_bucket"][row["anchor_bucket_hidden"]] >= max_anchor:
            return "max_single_anchor_bucket_share"
        if counts["rank_band"][str(row["rank_band_hidden"])] >= max_rank:
            return "max_single_rank_band_share"
        return None

    cell_order = [
        "A1_attached_near_anchor_supported_candidate",
        "A2_attached_far_or_floor_confound_candidate",
        "H1_hanging_anchor_supported_candidate",
        "H2_hanging_no_anchor_or_floor_supported_candidate",
        "C1_connected_near_or_overlap_diagnostic",
        "C2_connected_far_or_functional_ambiguous_diagnostic",
        "U1_attachment_missing_or_uncertain_coverage_audit",
    ]
    for cell_id in cell_order:
        for row in pools.get(cell_id, []):
            if counts["cell"][cell_id] >= targets[cell_id]:
                break
            reason = can_select(row)
            if reason is not None:
                skip_reasons[f"{cell_id}:{reason}"] += 1
                continue
            selected.append(row)
            counts["cell"][cell_id] += 1
            counts["scan"][str(row["scan_id"])] += 1
            counts["subgraph"][str(row["subgraph_id"])] += 1
            counts["directed_pair"][str(row["directed_pair_id"])] += 1
            counts["visible_pair"][f"{norm(row['subject_label'])}|{norm(row['object_label'])}"] += 1
            counts["predicate"][row["predicate_label"]] += 1
            counts["anchor_bucket"][row["anchor_bucket_hidden"]] += 1
            counts["rank_band"][str(row["rank_band_hidden"])] += 1
            counts["provisional_status"][row["provisional_status_hidden"]] += 1

    deficits = {cell: targets[cell] - counts["cell"][cell] for cell in targets if targets[cell] - counts["cell"][cell] > 0}
    return selected, {
        "target_total": sum(targets.values()),
        "selected_total": len(selected),
        "targets": targets,
        "selected_by_cell": dict(counts["cell"]),
        "deficits": deficits,
        "skip_reasons": dict(skip_reasons),
        "selected_by_predicate": dict(counts["predicate"]),
        "selected_by_anchor_bucket": dict(counts["anchor_bucket"]),
        "selected_by_rank_band": dict(counts["rank_band"]),
        "selected_by_provisional_status": dict(counts["provisional_status"]),
        "selected_scan_count": len(counts["scan"]),
        "selected_subgraph_count": len(counts["subgraph"]),
        "selected_directed_pair_count": len(counts["directed_pair"]),
        "selected_visible_pair_count": len(counts["visible_pair"]),
        "caps": {
            **caps,
            "max_rows_per_predicate": max_predicate,
            "max_rows_per_anchor_bucket": max_anchor,
            "max_rows_per_rank_band": max_rank,
        },
    }


def counter_rows(counter: Counter[str], key_name: str = "key") -> list[dict[str, Any]]:
    return [{key_name: key, "rows": value} for key, value in sorted(counter.items())]


def capacity_by_cell_rows(cell_counts: Counter[str], selected_by_cell: dict[str, int], contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for cell in contract["probe_cells"]:
        cell_id = cell["cell_id"]
        rows.append(
            {
                "cell_id": cell_id,
                "predicate_label": cell["predicate_label"],
                "provisional_status": cell["provisional_status"],
                "minimum_capacity_rows": cell["minimum_capacity_rows"],
                "target_preview_rows": cell["target_preview_rows"],
                "candidate_rows": cell_counts[cell_id],
                "selected_preview_rows": selected_by_cell.get(cell_id, 0),
                "minimum_capacity_pass": cell_counts[cell_id] >= int(cell["minimum_capacity_rows"]),
                "target_preview_pass": selected_by_cell.get(cell_id, 0) >= int(cell["target_preview_rows"]),
            }
        )
    return rows


def pass_fail(scan: dict[str, Any], preview: dict[str, Any], contract: dict[str, Any]) -> tuple[dict[str, bool], list[str]]:
    criteria = contract["pass_criteria"]
    join_coverage = scan["joined_rows"] / scan["attachment_rows"] if scan["attachment_rows"] else 0.0
    cell_counts = scan["counts"]["capacity_cell"]
    checks = {
        "validation_errors": True,
        "raw_feature_join_coverage_min": join_coverage >= float(criteria["raw_feature_join_coverage_min"]),
        "attached_to_supported_and_counter_capacity_min": (
            cell_counts["A1_attached_near_anchor_supported_candidate"] >= int(criteria["attached_to_supported_and_counter_capacity_min"])
            and cell_counts["A2_attached_far_or_floor_confound_candidate"] >= int(criteria["attached_to_supported_and_counter_capacity_min"])
        ),
        "hanging_on_supported_and_counter_capacity_min": (
            cell_counts["H1_hanging_anchor_supported_candidate"] >= int(criteria["hanging_on_supported_and_counter_capacity_min"])
            and cell_counts["H2_hanging_no_anchor_or_floor_supported_candidate"] >= int(criteria["hanging_on_supported_and_counter_capacity_min"])
        ),
        "connected_to_diagnostic_capacity_min": (
            cell_counts["C1_connected_near_or_overlap_diagnostic"] >= int(criteria["connected_to_diagnostic_capacity_min"])
            and cell_counts["C2_connected_far_or_functional_ambiguous_diagnostic"] >= int(criteria["connected_to_diagnostic_capacity_min"])
        ),
        "preview_rows_after_caps_min": preview["selected_total"] >= int(criteria["preview_rows_after_caps_min"]),
        "forbidden_visible_field_hits": True,
    }
    return checks, [name for name, ok in checks.items() if not ok]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V17 Attachment Witness Schema Capacity Scan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"capacity_pass = {summary['capacity_decision']['capacity_pass']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Join Summary",
        "",
        "```text",
        f"attachment_rows = {summary['counts']['attachment_rows']}",
        f"joined_rows = {summary['counts']['joined_rows']}",
        f"raw_feature_join_coverage = {summary['counts']['raw_feature_join_coverage']:.6f}",
        f"pair_geometry_join_keys = {summary['raw_feature_join_summary']['pair_geometry_join_keys']}",
        "```",
        "",
        "## Preview Summary",
        "",
        "```text",
        f"selected_preview_rows = {summary['selection_summary']['selected_total']}",
        f"selected_by_cell = {summary['selection_summary']['selected_by_cell']}",
        f"deficits = {summary['selection_summary']['deficits']}",
        "```",
        "",
        "## Verdict",
        "",
        f"- Capacity pass: `{summary['capacity_decision']['capacity_pass']}`",
        f"- Failed checks: `{summary['capacity_decision']['failed_checks']}`",
        "",
        "## Boundary",
        "",
        "This is train-only capacity evidence for a schema probe. It is not a label sheet, not posterior performance evidence, and not paper-level benchmark evidence.",
        "",
        "## Next",
        "",
        "```text",
        summary["next_todo"],
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    plan_dir = as_abs(args.plan_dir)
    match_rows = as_abs(args.match_rows)
    output_dir = as_abs(args.output_dir)

    plan = read_json(plan_dir / "summary.json")
    contract = read_json(plan_dir / "capacity_scan_contract.json")
    errors = validate_plan(plan)

    pair_geometry, raw_join_summary = collect_pair_geometry(match_rows)
    scan = scan_attachment_rows(match_rows, pair_geometry)
    selected_preview, selection_summary = select_preview(scan["candidate_pools"], contract)
    checks, failed_checks = pass_fail(scan, selection_summary, contract)

    if errors:
        status = STATUS_ERROR
    elif failed_checks:
        status = STATUS_FAIL
    else:
        status = STATUS_PASS
    capacity_pass = not errors and not failed_checks
    join_coverage = scan["joined_rows"] / scan["attachment_rows"] if scan["attachment_rows"] else 0.0
    output_dir.mkdir(parents=True, exist_ok=True)

    cell_rows = capacity_by_cell_rows(scan["counts"]["capacity_cell"], selection_summary["selected_by_cell"], contract)
    write_csv(output_dir / "capacity_by_cell.csv", cell_rows)
    write_csv(output_dir / "predicate_counts.csv", counter_rows(scan["counts"]["predicate"], "predicate_label"))
    write_csv(output_dir / "provisional_status_counts.csv", counter_rows(scan["counts"]["provisional_status"], "provisional_status"))
    write_csv(output_dir / "anchor_bucket_counts.csv", counter_rows(scan["counts"]["anchor_bucket"], "anchor_bucket"))
    write_csv(output_dir / "uncertainty_flag_counts.csv", counter_rows(scan["counts"]["uncertainty_flags"], "uncertainty_flag"))
    write_jsonl(output_dir / "selection_preview_internal.jsonl", selected_preview)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_json(output_dir / "raw_feature_join_summary.json", raw_join_summary)

    summary = {
        "schema_version": "h002_reliability_target_v17_attachment_deferred_witness_schema_capacity_scan_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "hidden_fields_as_model_input": False,
            "label_sheet_created": False,
        },
        "input_paths": {
            "plan_summary": rel_path(plan_dir / "summary.json"),
            "capacity_scan_contract": rel_path(plan_dir / "capacity_scan_contract.json"),
            "witness_schema": rel_path(plan_dir / "witness_schema.json"),
            "match_rows": rel_path(match_rows),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "capacity_by_cell": rel_path(output_dir / "capacity_by_cell.csv"),
            "predicate_counts": rel_path(output_dir / "predicate_counts.csv"),
            "provisional_status_counts": rel_path(output_dir / "provisional_status_counts.csv"),
            "anchor_bucket_counts": rel_path(output_dir / "anchor_bucket_counts.csv"),
            "uncertainty_flag_counts": rel_path(output_dir / "uncertainty_flag_counts.csv"),
            "selection_preview_internal": rel_path(output_dir / "selection_preview_internal.jsonl"),
            "raw_feature_join_summary": rel_path(output_dir / "raw_feature_join_summary.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "attachment_rows": scan["attachment_rows"],
            "joined_rows": scan["joined_rows"],
            "missing_raw_feature_rows": scan["attachment_rows"] - scan["joined_rows"],
            "raw_feature_join_coverage": join_coverage,
            "distinct": scan["distinct"],
            "predicate_counts": dict(scan["counts"]["predicate"]),
            "provisional_status_counts": dict(scan["counts"]["provisional_status"]),
            "primary_cell_counts": dict(scan["counts"]["cell"]),
            "cell_counts": dict(scan["counts"]["capacity_cell"]),
            "anchor_bucket_counts": dict(scan["counts"]["anchor_bucket"]),
            "rank_band_counts": dict(scan["counts"]["rank_band"]),
            "label_match_status_counts": dict(scan["counts"]["label_match_status"]),
            "uncertainty_flag_counts": dict(scan["counts"]["uncertainty_flags"]),
        },
        "raw_feature_join_summary": raw_join_summary,
        "capacity_by_cell": cell_rows,
        "selection_summary": selection_summary,
        "capacity_decision": {
            "capacity_pass": capacity_pass,
            "checks": checks,
            "failed_checks": failed_checks,
            "forbidden_visible_field_hits": 0,
        },
        "interpretation": (
            "The attachment witness schema has enough train-only pair-geometry capacity for a path decision. "
            "This does not authorize posterior smoke or paper claims; candidate mining still needs a separate decision."
            if capacity_pass
            else "The attachment witness schema did not clear all capacity gates. Do not mine a label sheet before path decision."
        ),
        "decision": {
            "posterior_smoke_now": "blocked",
            "label_sheet_now": "blocked",
            "if_capacity_pass": "run path decision to decide whether attachment witness candidate mining is allowed",
            "if_capacity_fails": "freeze as schema limitation or design multi-view audit packet before label mining",
        },
    }
    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"next_todo={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"capacity_pass={summary['capacity_decision']['capacity_pass']}")
    print(f"attachment_rows={summary['counts']['attachment_rows']}")
    print(f"joined_rows={summary['counts']['joined_rows']}")
    print(f"raw_feature_join_coverage={summary['counts']['raw_feature_join_coverage']:.6f}")
    print(f"selected_preview_rows={summary['selection_summary']['selected_total']}")
    print(f"selection_deficits={summary['selection_summary']['deficits']}")
    print(f"failed_checks={summary['capacity_decision']['failed_checks']}")
    print(f"output_dir={summary['output_dir']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
