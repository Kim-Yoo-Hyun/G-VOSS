#!/usr/bin/env python3
"""Scan H002 v14 physical relation-family feasibility on train-only rows."""

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

DEFAULT_PATH_DECISION = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_path_decision_after_audit/summary.json"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_feasibility_scan"

EXPECTED_PATH_STATUS = "h002_reliability_target_v13_proximity_lh_scene_geometry_path_decision_select_physical_relation_feasibility"
EXPECTED_PATH_NEXT = "reliability_target_v14_physical_relation_family_feasibility_scan"

STATUS_READY = "h002_reliability_target_v14_physical_relation_family_feasibility_scan_ready_support_primary_attachment_schema_deferred"
STATUS_ERRORS = "h002_reliability_target_v14_physical_relation_family_feasibility_scan_errors"
NEXT_TODO_READY = "reliability_target_v14_physical_relation_family_sampling_plan"
NEXT_TODO_BLOCKED = "reliability_target_v14_physical_relation_family_path_decision"

TARGET_FAMILIES = ("support_contact", "attachment_deferred", "relative_vertical")
FAMILY_PREDICATES = {
    "support_contact": ("standing on", "lying on", "supported by"),
    "attachment_deferred": ("attached to", "hanging on", "connected to"),
    "relative_vertical": ("higher than", "lower than"),
}
FAMILY_ROLES = {
    "support_contact": "primary_anchor_candidate",
    "attachment_deferred": "novelty_candidate_requires_witness_schema",
    "relative_vertical": "geometry_easy_control_candidate",
}
QUEUE_BUCKET = {
    "HL": "B2_semantic_high_geometry_low",
    "LH": "B3_semantic_low_geometry_high",
}
PREVIEW_PER_CELL = 12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision", type=Path, default=DEFAULT_PATH_DECISION)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
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


def nested_get(row: dict[str, Any], path: tuple[str, ...], default: Any = None) -> Any:
    value: Any = row
    for part in path:
        if not isinstance(value, dict):
            return default
        value = value.get(part)
        if value is None:
            return default
    return value


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stable_int(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:12], 16)


def empty_stats() -> dict[str, Any]:
    return {
        "rows": 0,
        "predicates": Counter(),
        "geometry_status": Counter(),
        "coverage_state": Counter(),
        "bucket_top100": Counter(),
        "rank_band": Counter(),
        "semantic_axis_top100": Counter(),
        "geometry_axis": Counter(),
        "label_match_status": Counter(),
        "reason_codes": Counter(),
        "subject_object_label_pair": Counter(),
        "scan_ids": set(),
        "subgraph_ids": set(),
        "directed_pair_ids": set(),
        "raw_feature_rows": 0,
        "p_geom_count": 0,
        "p_geom_sum": 0.0,
        "consistency_count": 0,
        "consistency_sum": 0.0,
    }


def update_match_stats(stats: dict[str, Any], row: dict[str, Any]) -> None:
    predicate = row.get("predicate", {})
    geometry = row.get("geometry", {})
    identity = row.get("identity", {})
    edge = row.get("edge", {})
    rga = row.get("rga", {})
    label = row.get("label", {})
    subject_label = norm(edge.get("subject_label"))
    object_label = norm(edge.get("object_label"))

    stats["rows"] += 1
    stats["predicates"][norm(predicate.get("predicate_label"))] += 1
    stats["geometry_status"][norm(geometry.get("geometry_status"))] += 1
    stats["coverage_state"][norm(rga.get("coverage_state"))] += 1
    stats["bucket_top100"][norm(rga.get("bucket_top100"))] += 1
    stats["rank_band"][norm(rga.get("rank_band"))] += 1
    stats["semantic_axis_top100"][norm(rga.get("semantic_axis_top100"))] += 1
    stats["geometry_axis"][norm(rga.get("geometry_axis"))] += 1
    stats["label_match_status"][norm(label.get("label_match_status"))] += 1
    stats["subject_object_label_pair"][f"{subject_label}|{object_label}"] += 1
    stats["scan_ids"].add(str(identity.get("scan_id")))
    stats["subgraph_ids"].add(str(identity.get("subgraph_id")))
    stats["directed_pair_ids"].add(str(identity.get("directed_pair_id")))
    for reason in geometry.get("reason_codes") or []:
        stats["reason_codes"][norm(reason)] += 1
    if geometry.get("raw_features") is not None:
        stats["raw_feature_rows"] += 1
    p_geom = as_float(geometry.get("p_geom_valid"))
    if p_geom is not None:
        stats["p_geom_count"] += 1
        stats["p_geom_sum"] += p_geom
    consistency = as_float(geometry.get("consistency_score"))
    if consistency is not None:
        stats["consistency_count"] += 1
        stats["consistency_sum"] += consistency


def queue_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("scan_id")),
            str(row.get("subgraph_id")),
            str(row.get("subject_id")),
            str(row.get("object_id")),
        ]
    )


def update_queue_stats(
    row: dict[str, Any],
    queue_path: Path,
    queue_stats: dict[str, dict[str, Counter]],
    exact_masks: dict[str, dict[str, int]],
    label_pair_masks: dict[str, dict[str, int]],
    rank_to_queue: dict[str, dict[str, Counter]],
    predicate_to_queue: dict[str, dict[str, Counter]],
    predicate_rank_to_queue: dict[str, dict[str, Counter]],
    predicate_queue_counts: dict[str, dict[str, Counter]],
    samples: dict[str, list[tuple[int, dict[str, Any]]]],
) -> None:
    family = norm(row.get("predicate_family"))
    if family not in TARGET_FAMILIES:
        return
    predicate = norm(row.get("predicate_label"))
    queue_kind = str(row.get("queue_kind"))
    rank_band = str(row.get("rank_band"))
    label_pair = f"{norm(row.get('subject_label'))}|{norm(row.get('object_label'))}"
    mask = 1 if queue_kind == "HL" else 2 if queue_kind == "LH" else 0

    queue_stats[family]["queue_kind"][queue_kind] += 1
    queue_stats[family]["predicate"][predicate] += 1
    queue_stats[family]["geometry_status"][norm(row.get("geometry_status"))] += 1
    queue_stats[family]["rank_band"][rank_band] += 1
    queue_stats[family]["label_match_status"][norm(row.get("label_match_status"))] += 1
    queue_stats[family]["machine_hint"][norm(row.get("machine_hint"))] += 1
    queue_stats[family]["subject_object_label_pair"][label_pair] += 1
    predicate_queue_counts[family][predicate][queue_kind] += 1
    exact_masks[family][queue_key(row)] |= mask
    label_pair_masks[family][label_pair] |= mask
    rank_to_queue[family][rank_band][queue_kind] += 1
    predicate_to_queue[family][predicate][queue_kind] += 1
    predicate_rank_to_queue[family][f"{predicate}|{rank_band}"][queue_kind] += 1

    cell = f"{family}|{predicate}|{queue_kind}"
    sample = {
        "source_queue_path": rel_path(queue_path),
        "queue_kind": queue_kind,
        "semantic_geometry_bucket": QUEUE_BUCKET.get(queue_kind, queue_kind),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "subject_label": row.get("subject_label"),
        "predicate_family": family,
        "predicate_label": predicate,
        "object_label": row.get("object_label"),
        "geometry_status": row.get("geometry_status"),
        "p_geom_valid": row.get("p_geom_valid"),
        "consistency_score": row.get("consistency_score"),
        "rank_band": rank_band,
        "semantic_rank": row.get("semantic_rank"),
        "label_match_status": row.get("label_match_status"),
        "machine_hint": row.get("machine_hint"),
        "reason_codes": row.get("reason_codes"),
        "selection_note": "preview_only_not_label_ready",
    }
    score = stable_int(str(row.get("prediction_id", "")) + "|" + cell)
    bucket = samples[cell]
    if len(bucket) < PREVIEW_PER_CELL:
        bucket.append((score, sample))
    else:
        max_idx, max_item = max(enumerate(bucket), key=lambda item: item[1][0])
        if score < max_item[0]:
            bucket[max_idx] = (score, sample)


def majority_accuracy(groups: dict[str, Counter]) -> dict[str, Any]:
    total = 0
    correct = 0
    label_counts: Counter[str] = Counter()
    for counter in groups.values():
        if not counter:
            continue
        total += sum(counter.values())
        correct += counter.most_common(1)[0][1]
        label_counts.update(counter)
    baseline = None
    if total and label_counts:
        baseline = label_counts.most_common(1)[0][1] / total
    return {
        "groups": len(groups),
        "rows": total,
        "majority_accuracy": correct / total if total else None,
        "global_majority_baseline": baseline,
    }


def top_items(counter: Counter, limit: int = 8) -> dict[str, int]:
    return dict(counter.most_common(limit))


def match_inventory_rows(match_stats: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in TARGET_FAMILIES:
        stats = match_stats[family]
        total = stats["rows"]
        unsupported = stats["geometry_status"].get("unsupported", 0)
        missing = stats["geometry_status"].get("missing", 0)
        checkable = total - unsupported - missing
        rows.append(
            {
                "family": family,
                "role": FAMILY_ROLES[family],
                "rows": total,
                "unique_scans": len(stats["scan_ids"]),
                "unique_subgraphs": len(stats["subgraph_ids"]),
                "unique_directed_pairs": len(stats["directed_pair_ids"]),
                "checkable_rows": checkable,
                "raw_feature_rows": stats["raw_feature_rows"],
                "unsupported_rows": unsupported,
                "unsupported_share": unsupported / total if total else None,
                "p_geom_rows": stats["p_geom_count"],
                "p_geom_mean": stats["p_geom_sum"] / stats["p_geom_count"] if stats["p_geom_count"] else None,
                "consistency_rows": stats["consistency_count"],
                "consistency_mean": stats["consistency_sum"] / stats["consistency_count"] if stats["consistency_count"] else None,
                "top_predicates": json.dumps(top_items(stats["predicates"]), sort_keys=True),
                "geometry_status_counts": json.dumps(dict(stats["geometry_status"]), sort_keys=True),
                "bucket_top100_counts": json.dumps(dict(stats["bucket_top100"]), sort_keys=True),
                "rank_band_counts": json.dumps(dict(stats["rank_band"]), sort_keys=True),
                "label_match_status_counts": json.dumps(top_items(stats["label_match_status"]), sort_keys=True),
                "top_label_pairs": json.dumps(top_items(stats["subject_object_label_pair"]), sort_keys=True),
                "top_reason_codes": json.dumps(top_items(stats["reason_codes"], limit=12), sort_keys=True),
            }
        )
    return rows


def predicate_inventory_rows(
    match_stats: dict[str, dict[str, Any]],
    predicate_queue_counts: dict[str, dict[str, Counter]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in TARGET_FAMILIES:
        for predicate in FAMILY_PREDICATES[family]:
            predicate = norm(predicate)
            match_rows = match_stats[family]["predicates"].get(predicate, 0)
            hl_rows = predicate_queue_counts[family][predicate].get("HL", 0)
            lh_rows = predicate_queue_counts[family][predicate].get("LH", 0)
            balanced_pairs = min(hl_rows, lh_rows)
            rows.append(
                {
                    "family": family,
                    "predicate": predicate,
                    "match_rows": match_rows,
                    "hl_queue_rows": hl_rows,
                    "lh_queue_rows": lh_rows,
                    "same_predicate_hl_lh_balanced_capacity": balanced_pairs * 2,
                    "same_predicate_hl_lh_pair_units": balanced_pairs,
                    "route_note": predicate_route_note(family, predicate, hl_rows, lh_rows, match_rows),
                }
            )
    return rows


def predicate_route_note(family: str, predicate: str, hl_rows: int, lh_rows: int, match_rows: int) -> str:
    if family == "attachment_deferred":
        return "present_in_match_rows_but_geometry_unsupported_needs_witness_schema"
    if not match_rows:
        return "absent"
    if hl_rows and lh_rows:
        return "same_predicate_bidirectional_queue_capacity_available"
    if lh_rows and not hl_rows:
        return "lh_only_under_current_queue"
    if hl_rows and not lh_rows:
        return "hl_only_under_current_queue"
    return "not_in_hl_lh_queue"


def queue_inventory_rows(
    queue_stats: dict[str, dict[str, Counter]],
    exact_masks: dict[str, dict[str, int]],
    label_pair_masks: dict[str, dict[str, int]],
    rank_to_queue: dict[str, dict[str, Counter]],
    predicate_to_queue: dict[str, dict[str, Counter]],
    predicate_rank_to_queue: dict[str, dict[str, Counter]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in TARGET_FAMILIES:
        exact_mixed = sum(1 for value in exact_masks[family].values() if value == 3)
        label_mixed = sum(1 for value in label_pair_masks[family].values() if value == 3)
        rows.append(
            {
                "family": family,
                "hl_rows": queue_stats[family]["queue_kind"].get("HL", 0),
                "lh_rows": queue_stats[family]["queue_kind"].get("LH", 0),
                "hl_lh_balance_ratio": balance_ratio(
                    queue_stats[family]["queue_kind"].get("HL", 0),
                    queue_stats[family]["queue_kind"].get("LH", 0),
                ),
                "queue_predicate_counts": json.dumps(dict(queue_stats[family]["predicate"]), sort_keys=True),
                "queue_geometry_status_counts": json.dumps(dict(queue_stats[family]["geometry_status"]), sort_keys=True),
                "queue_rank_band_counts": json.dumps(dict(queue_stats[family]["rank_band"]), sort_keys=True),
                "queue_label_match_status_counts": json.dumps(top_items(queue_stats[family]["label_match_status"]), sort_keys=True),
                "exact_endpoint_mixed_hl_lh_groups": exact_mixed,
                "visible_label_pair_mixed_hl_lh_groups": label_mixed,
                "rank_to_queue_majority": majority_accuracy(rank_to_queue[family])["majority_accuracy"],
                "rank_to_queue_global_baseline": majority_accuracy(rank_to_queue[family])["global_majority_baseline"],
                "predicate_to_queue_majority": majority_accuracy(predicate_to_queue[family])["majority_accuracy"],
                "predicate_rank_to_queue_majority": majority_accuracy(predicate_rank_to_queue[family])["majority_accuracy"],
                "top_machine_hints": json.dumps(top_items(queue_stats[family]["machine_hint"]), sort_keys=True),
                "top_label_pairs": json.dumps(top_items(queue_stats[family]["subject_object_label_pair"]), sort_keys=True),
            }
        )
    return rows


def balance_ratio(a: int, b: int) -> float | None:
    if not a and not b:
        return None
    return min(a, b) / max(a, b)


def route_matrix(
    match_rows: list[dict[str, Any]],
    predicate_rows: list[dict[str, Any]],
    queue_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    match_by_family = {row["family"]: row for row in match_rows}
    queue_by_family = {row["family"]: row for row in queue_rows}
    predicates_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in predicate_rows:
        predicates_by_family[row["family"]].append(row)

    matrix: list[dict[str, Any]] = []
    for family in TARGET_FAMILIES:
        match = match_by_family[family]
        queue = queue_by_family[family]
        pred_rows = predicates_by_family[family]
        same_predicate_capacity = sum(row["same_predicate_hl_lh_balanced_capacity"] for row in pred_rows)
        same_predicate_pair_units = sum(row["same_predicate_hl_lh_pair_units"] for row in pred_rows)
        dominant_predicate_pair_units = max((row["same_predicate_hl_lh_pair_units"] for row in pred_rows), default=0)
        dominant_capacity_share = (
            dominant_predicate_pair_units / same_predicate_pair_units if same_predicate_pair_units else None
        )
        unsupported_share = match["unsupported_share"] or 0.0
        risk_flags: list[str] = []
        if unsupported_share >= 0.95:
            risk_flags.append("geometry_unsupported_under_current_policy")
        if queue["hl_lh_balance_ratio"] is not None and queue["hl_lh_balance_ratio"] < 0.05:
            risk_flags.append("severe_hl_lh_queue_imbalance")
        rank_lift = majority_lift(queue["rank_to_queue_majority"], queue["rank_to_queue_global_baseline"])
        predicate_lift = majority_lift(queue["predicate_to_queue_majority"], queue["rank_to_queue_global_baseline"])
        if rank_lift is not None and rank_lift >= 0.03:
            risk_flags.append("rank_band_adds_queue_shortcut_beyond_class_imbalance")
        if predicate_lift is not None and predicate_lift >= 0.03:
            risk_flags.append("predicate_adds_queue_shortcut_beyond_class_imbalance")
        if dominant_capacity_share is not None and dominant_capacity_share >= 0.90:
            risk_flags.append("same_predicate_capacity_dominated_by_one_predicate")
        if queue["hl_rows"] == 0 or queue["lh_rows"] == 0:
            risk_flags.append("not_bidirectional_in_current_hl_lh_queue")

        if family == "support_contact":
            verdict = "select_primary_anchor_for_sampling_plan"
            next_action = (
                "Build a same-family/same-predicate controlled sampling plan, "
                "using lying on as the high-capacity anchor and standing on/supported by as limited diversity cells."
            )
            allowed_role = "primary_target_candidate_after_new_sampling_and_label_audit"
        elif family == "attachment_deferred":
            verdict = "defer_until_geometry_witness_schema_exists"
            next_action = (
                "Do not sample as posterior target yet; first define attachment/hanging/connection witnesses "
                "or use multi-view only as audit evidence."
            )
            allowed_role = "future_schema_probe_not_current_posterior_target"
        else:
            verdict = "keep_as_control_family_not_primary_novelty"
            next_action = (
                "Use lower than / higher than as a geometry-easy control after support_contact sampling is repaired; "
                "avoid claiming novelty from vertical order alone."
            )
            allowed_role = "control_candidate_after_new_sampling_and_label_audit"

        matrix.append(
            {
                "family": family,
                "role": FAMILY_ROLES[family],
                "verdict": verdict,
                "allowed_role": allowed_role,
                "match_rows": match["rows"],
                "checkable_rows": match["checkable_rows"],
                "raw_feature_rows": match["raw_feature_rows"],
                "unsupported_share": unsupported_share,
                "hl_rows": queue["hl_rows"],
                "lh_rows": queue["lh_rows"],
                "hl_lh_balance_ratio": queue["hl_lh_balance_ratio"],
                "same_predicate_hl_lh_balanced_capacity": same_predicate_capacity,
                "dominant_same_predicate_capacity_share": dominant_capacity_share,
                "exact_endpoint_mixed_hl_lh_groups": queue["exact_endpoint_mixed_hl_lh_groups"],
                "visible_label_pair_mixed_hl_lh_groups": queue["visible_label_pair_mixed_hl_lh_groups"],
                "risk_flags": risk_flags,
                "construction_caveat": "HL/LH queue bucket is a sampling/control axis derived from semantic rank and geometry status, not a reliability target label.",
                "next_action": next_action,
                "posterior_smoke_allowed": False,
            }
        )
    return matrix


def majority_lift(accuracy: float | None, baseline: float | None) -> float | None:
    if accuracy is None or baseline is None:
        return None
    return accuracy - baseline


def validate_inputs(path_decision: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_decision.get("status") != EXPECTED_PATH_STATUS:
        errors.append(
            {
                "error_type": "unexpected_path_decision_status",
                "expected": EXPECTED_PATH_STATUS,
                "actual": path_decision.get("status"),
            }
        )
    if path_decision.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append(
            {
                "error_type": "unexpected_path_decision_next_todo",
                "expected": EXPECTED_PATH_NEXT,
                "actual": path_decision.get("next_todo"),
            }
        )
    for key in ["match_rows", "hl_queue", "lh_queue"]:
        path = as_abs(getattr(args, key))
        if not path.exists():
            errors.append({"error_type": "missing_input", "key": key, "path": rel_path(path)})
    boundary = path_decision.get("boundary", {})
    if boundary.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "previous_boundary_posterior_unexpectedly_allowed"})
    if boundary.get("validation_usage") is not False or boundary.get("test_usage") is not False:
        errors.append({"error_type": "previous_boundary_not_train_only"})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V14 Physical Relation-Family Feasibility Scan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        "Proceed to a new sampling plan with `support_contact` as the primary anchor, keep `relative_vertical` as a control family, and defer `attachment_deferred` until a relation-specific witness schema exists.",
        "",
        "```text",
        f"selected_route = {summary['selected_route']}",
        f"next_todo = {summary['next_todo']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Route Matrix",
        "",
        "| Family | Verdict | HL | LH | Same-predicate capacity | Risk flags |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in summary["route_matrix"]:
        risks = ", ".join(f"`{risk}`" for risk in row["risk_flags"]) or "none"
        lines.append(
            f"| `{row['family']}` | `{row['verdict']}` | {row['hl_rows']} | {row['lh_rows']} | "
            f"{row['same_predicate_hl_lh_balanced_capacity']} | {risks} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `support_contact` has both HL and LH capacity, but the next construction must not reuse the old exact endpoint-pair route.",
            "- `relative_vertical` also has capacity, but it is geometry-easy and should be used as a control rather than the main novelty target.",
            "- `attachment_deferred` exists in the full train row inventory, but current geometry policy marks it as unsupported; it is not ready as a posterior target without a new witness schema.",
            "- The scan does not train a posterior model and does not use validation/test rows.",
            "",
            "## Outputs",
            "",
        ]
    )
    for key, value in summary["output_paths"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Next", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_decision = read_json(args.path_decision)
    validation_errors = validate_inputs(path_decision, args)

    match_stats = {family: empty_stats() for family in TARGET_FAMILIES}
    for _, row in iter_jsonl(args.match_rows):
        family = norm(nested_get(row, ("predicate", "predicate_family")))
        if family in match_stats:
            update_match_stats(match_stats[family], row)

    queue_stats = {
        family: {
            "queue_kind": Counter(),
            "predicate": Counter(),
            "geometry_status": Counter(),
            "rank_band": Counter(),
            "label_match_status": Counter(),
            "machine_hint": Counter(),
            "subject_object_label_pair": Counter(),
        }
        for family in TARGET_FAMILIES
    }
    exact_masks: dict[str, dict[str, int]] = {family: defaultdict(int) for family in TARGET_FAMILIES}
    label_pair_masks: dict[str, dict[str, int]] = {family: defaultdict(int) for family in TARGET_FAMILIES}
    rank_to_queue: dict[str, dict[str, Counter]] = {family: defaultdict(Counter) for family in TARGET_FAMILIES}
    predicate_to_queue: dict[str, dict[str, Counter]] = {family: defaultdict(Counter) for family in TARGET_FAMILIES}
    predicate_rank_to_queue: dict[str, dict[str, Counter]] = {family: defaultdict(Counter) for family in TARGET_FAMILIES}
    predicate_queue_counts: dict[str, dict[str, Counter]] = {family: defaultdict(Counter) for family in TARGET_FAMILIES}
    samples: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)

    for queue_path in [args.hl_queue, args.lh_queue]:
        for _, row in iter_jsonl(queue_path):
            update_queue_stats(
                row=row,
                queue_path=queue_path,
                queue_stats=queue_stats,
                exact_masks=exact_masks,
                label_pair_masks=label_pair_masks,
                rank_to_queue=rank_to_queue,
                predicate_to_queue=predicate_to_queue,
                predicate_rank_to_queue=predicate_rank_to_queue,
                predicate_queue_counts=predicate_queue_counts,
                samples=samples,
            )

    family_inventory = match_inventory_rows(match_stats)
    predicate_inventory = predicate_inventory_rows(match_stats, predicate_queue_counts)
    queue_inventory = queue_inventory_rows(
        queue_stats,
        exact_masks,
        label_pair_masks,
        rank_to_queue,
        predicate_to_queue,
        predicate_rank_to_queue,
    )
    routes = route_matrix(family_inventory, predicate_inventory, queue_inventory)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "family_inventory": output_dir / "family_inventory.csv",
        "predicate_inventory": output_dir / "predicate_inventory.csv",
        "queue_inventory": output_dir / "queue_inventory.csv",
        "route_matrix": output_dir / "route_matrix.jsonl",
        "preview_candidates": output_dir / "preview_candidates.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    preview_rows: list[dict[str, Any]] = []
    for cell in sorted(samples):
        for _, row in sorted(samples[cell], key=lambda item: item[0]):
            preview_rows.append(row)

    selected_route = "support_contact_primary_anchor_with_relative_vertical_control_attachment_schema_probe"
    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    summary = {
        "schema_version": "h002_reliability_target_v14_physical_relation_family_feasibility_scan_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selected_route": selected_route,
        "input_paths": {
            "path_decision_summary": rel_path(as_abs(args.path_decision)),
            "match_rows": rel_path(as_abs(args.match_rows)),
            "hl_queue": rel_path(as_abs(args.hl_queue)),
            "lh_queue": rel_path(as_abs(args.lh_queue)),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "family_inventory": family_inventory,
        "route_matrix": routes,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "hidden_fields_as_model_input": False,
        },
        "interpretation": {
            "support_contact": "best immediate feasibility-to-payoff route, but needs a new sampling plan and target-independence audit",
            "relative_vertical": "useful control, not the main novelty target because geometry witness almost directly determines the relation",
            "attachment_deferred": "important future novelty family, but current rows are unsupported by the geometry policy and need witness schema before sampling",
            "posterior": "blocked until the next sampled target passes class-mass and shortcut-control gates",
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO_READY if not validation_errors else NEXT_TODO_BLOCKED,
    }

    write_csv(output_paths["family_inventory"], family_inventory)
    write_csv(output_paths["predicate_inventory"], predicate_inventory)
    write_csv(output_paths["queue_inventory"], queue_inventory)
    write_jsonl(output_paths["route_matrix"], routes)
    write_jsonl(output_paths["preview_candidates"], preview_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_route']}")
    for row in summary["route_matrix"]:
        print(
            f"{row['family']}: verdict={row['verdict']} hl={row['hl_rows']} "
            f"lh={row['lh_rows']} same_predicate_capacity={row['same_predicate_hl_lh_balanced_capacity']} "
            f"risk_flags={','.join(row['risk_flags']) or 'none'}"
        )
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
