#!/usr/bin/env python3
"""Mine controlled R7 attachment-observability repair candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v17_attachment_deferred_witness_schema_capacity_scan as v17
import reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan as v21


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
ARTIFACT_ROOT = H2_ROOT / "artifacts"
RGA_ROOT = ARTIFACT_ROOT / "train_rga_full/open3dsg_train_full/rga"

DEFAULT_CAPACITY_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan"
)
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining"
)

EXPECTED_CAPACITY_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_ready_for_candidate_mining"
)
EXPECTED_CAPACITY_NEXT = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining"
)
EXPECTED_SELECTED_PATH = "exact_predicate_class_pair_repair_candidate_mining"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining_ready_for_packet_materialization_plan"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining_input_or_output_errors"
)
NEXT_TODO = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan"
)

PRIMARY_PREDICATES = ("attached to", "hanging on")
DIAGNOSTIC_PREDICATES = ("connected to",)
ROLE_ACCEPT = v21.ROLE_ACCEPT_PROXY
ROLE_REJECT = v21.ROLE_REJECT_PROXY
ROLE_UNCERTAIN = v21.ROLE_UNCERTAIN_PROXY
TARGET_ROLE_QUOTAS = {
    "attached to": {ROLE_ACCEPT: 80, ROLE_REJECT: 120, ROLE_UNCERTAIN: 40},
    "hanging on": {ROLE_ACCEPT: 80, ROLE_REJECT: 120, ROLE_UNCERTAIN: 40},
}

MAX_ROWS_PER_EXACT_CLASS_PAIR = 8
MAX_ROWS_PER_SCAN = 10
MAX_ROWS_PER_DIRECTED_PAIR = 2
MAX_ROWS_PER_VISIBLE_ENDPOINT_PAIR = 8
MAX_ROWS_PER_SUBJECT_LABEL = 80
MAX_ROWS_PER_OBJECT_LABEL = 120
MAX_ROLE_ROWS_PER_EXACT_CLASS_PAIR = 4
GROUP_ROLE_BUFFER_CAP = 24

ANCHOR_LABELS = {
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
    "mirror",
    "picture",
    "frame",
    "tv",
    "lamp",
    "light",
}
ROOM_SURFACES = {"floor", "wall", "ceiling"}
LOW_PRIORITY_LABELS = {"floor", "object", "item", "thing"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def stable_int(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:12], 16)


def stable_id(value: str, prefix: str = "r7cand") -> str:
    return f"{prefix}_{hashlib.sha1(value.encode('utf-8')).hexdigest()[:16]}"


def validate_capacity(summary: dict[str, Any], match_rows: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_CAPACITY_NEXT:
        errors.append({"error_type": "unexpected_capacity_next", "actual": summary.get("next_todo")})
    if summary.get("selected_path") != EXPECTED_SELECTED_PATH:
        errors.append({"error_type": "unexpected_capacity_selected_path", "actual": summary.get("selected_path")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors_present", "actual": summary.get("validation_errors")})
    if summary.get("capacity_decision", {}).get("capacity_pass") is not True:
        errors.append({"error_type": "capacity_not_passed", "actual": summary.get("capacity_decision", {})})
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "fills_labels",
        "materializes_rows",
        "packet_materialization_started",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "capacity_boundary_not_false", "key": key, "actual": boundary.get(key)})
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def anchor_priority(candidate: dict[str, Any]) -> int:
    subject = str(candidate["subject_label"])
    obj = str(candidate["object_label"])
    predicate = str(candidate["predicate_label"])
    score = 0
    if obj in ANCHOR_LABELS:
        score += 6
    if subject in ANCHOR_LABELS:
        score += 3
    if obj in ROOM_SURFACES and obj != "floor":
        score += 3
    if subject in LOW_PRIORITY_LABELS or obj in LOW_PRIORITY_LABELS:
        score -= 4
    if subject == obj:
        score -= 2
    if predicate == "hanging on" and obj in {"wall", "ceiling", "door", "window", "rack", "rail", "rod", "hook"}:
        score += 3
    if predicate == "attached to" and obj in {"wall", "door", "window", "cabinet", "shelf", "lamp", "light"}:
        score += 2
    return score


def candidate_from_row(row: dict[str, Any], witness: dict[str, Any], raw_entry: dict[str, Any] | None) -> dict[str, Any]:
    candidate = v21.candidate_from_row(row, witness, raw_entry)
    prediction_id = str(candidate["prediction_id"])
    candidate["candidate_id"] = stable_id(prediction_id)
    candidate["exact_class_pair_key"] = (
        str(candidate["predicate_label"]),
        str(candidate["subject_label"]),
        str(candidate["object_label"]),
    )
    candidate["exact_class_pair_id"] = "|".join(candidate["exact_class_pair_key"])
    candidate["selection_hash"] = stable_int(prediction_id)
    candidate["anchor_priority"] = anchor_priority(candidate)
    return candidate


def add_to_group(groups: dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]], candidate: dict[str, Any]) -> None:
    role = candidate["reliability_proxy_role"]
    if role not in {ROLE_ACCEPT, ROLE_REJECT, ROLE_UNCERTAIN}:
        return
    group = groups[candidate["exact_class_pair_key"]]
    bucket = group[role]
    bucket.append(candidate)
    if len(bucket) > GROUP_ROLE_BUFFER_CAP:
        bucket.sort(key=lambda row: (-int(row["anchor_priority"]), int(row["selection_hash"])))
        del bucket[GROUP_ROLE_BUFFER_CAP:]


def scan_candidates(match_rows: Path) -> tuple[dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]], dict[str, Any]]:
    pair_geometry, raw_join = v17.collect_pair_geometry(match_rows)
    groups: dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    distinct: dict[str, set[str]] = defaultdict(set)
    primary_rows = 0
    diagnostic_rows = 0
    joined_rows = 0
    for _, row in v17.iter_jsonl(match_rows):
        predicate_info = row.get("predicate", {})
        if predicate_info.get("predicate_family") != "attachment_deferred":
            continue
        predicate = v17.norm(predicate_info.get("predicate_label"))
        if predicate not in PRIMARY_PREDICATES and predicate not in DIAGNOSTIC_PREDICATES:
            continue
        identity = row.get("identity", {})
        raw_entry = pair_geometry.get(identity.get("directed_pair_id"))
        witness = v17.classify_attachment(row, raw_entry)
        if raw_entry is not None:
            joined_rows += 1
        if predicate in DIAGNOSTIC_PREDICATES:
            diagnostic_rows += 1
            counts["diagnostic_predicate"][predicate] += 1
            counts["diagnostic_cell"][witness["cell_id"]] += 1
            continue
        primary_rows += 1
        candidate = candidate_from_row(row, witness, raw_entry)
        role = candidate["reliability_proxy_role"]
        counts["predicate"][predicate] += 1
        counts["role"][role] += 1
        counts["predicate_role"][f"{predicate}|{role}"] += 1
        counts["rank_band"][candidate["rank_band"]] += 1
        counts["geometry_bucket"][candidate["geometry_bucket"]] += 1
        counts["coverage_proxy"][candidate["coverage_proxy"]] += 1
        counts["uncertainty_bucket"][candidate["uncertainty_bucket"]] += 1
        counts["class_pair"][candidate["visible_endpoint_pair"]] += 1
        distinct["scan_id"].add(str(candidate["scan_id"]))
        distinct["directed_pair_id"].add(str(candidate["directed_pair_id"]))
        distinct["visible_endpoint_pair"].add(str(candidate["visible_endpoint_pair"]))
        add_to_group(groups, candidate)
    for role_rows in groups.values():
        for rows in role_rows.values():
            rows.sort(key=lambda row: (-int(row["anchor_priority"]), int(row["selection_hash"])))
    return groups, {
        "raw_join": raw_join,
        "counts": {key: dict(value) for key, value in counts.items()},
        "diagnostic_rows": diagnostic_rows,
        "distinct": {key: len(value) for key, value in distinct.items()},
        "joined_rows": joined_rows,
        "primary_rows": primary_rows,
    }


def group_score(key: tuple[str, str, str], roles: dict[str, list[dict[str, Any]]]) -> tuple[int, int, int, str]:
    predicate, subject, obj = key
    accept = len(roles.get(ROLE_ACCEPT, []))
    reject = len(roles.get(ROLE_REJECT, []))
    uncertain = len(roles.get(ROLE_UNCERTAIN, []))
    anchor = max([row["anchor_priority"] for rows in roles.values() for row in rows] or [0])
    mixed = min(accept, reject)
    return (-anchor, -mixed, -(accept + reject + uncertain), f"{predicate}|{subject}|{obj}")


def add_selected(
    row: dict[str, Any],
    selected: list[dict[str, Any]],
    state: dict[str, Counter[str]],
    role_targets: dict[str, int],
) -> bool:
    predicate = row["predicate_label"]
    role = row["reliability_proxy_role"]
    if state["predicate_role"][f"{predicate}|{role}"] >= role_targets[role]:
        return False
    prediction_id = str(row["prediction_id"])
    if state["prediction_id"][prediction_id]:
        return False
    if state["scan_id"][str(row["scan_id"])] >= MAX_ROWS_PER_SCAN:
        return False
    if state["directed_pair_id"][str(row["directed_pair_id"])] >= MAX_ROWS_PER_DIRECTED_PAIR:
        return False
    if state["exact_class_pair_id"][row["exact_class_pair_id"]] >= MAX_ROWS_PER_EXACT_CLASS_PAIR:
        return False
    if state["class_pair_role"][f"{row['exact_class_pair_id']}|{role}"] >= MAX_ROLE_ROWS_PER_EXACT_CLASS_PAIR:
        return False
    if state["visible_endpoint_pair"][row["visible_endpoint_pair"]] >= MAX_ROWS_PER_VISIBLE_ENDPOINT_PAIR:
        return False
    if state["subject_label"][row["subject_label"]] >= MAX_ROWS_PER_SUBJECT_LABEL:
        return False
    if state["object_label"][row["object_label"]] >= MAX_ROWS_PER_OBJECT_LABEL:
        return False
    selected.append(row)
    state["predicate"][predicate] += 1
    state["role"][role] += 1
    state["predicate_role"][f"{predicate}|{role}"] += 1
    state["prediction_id"][prediction_id] += 1
    state["scan_id"][str(row["scan_id"])] += 1
    state["directed_pair_id"][str(row["directed_pair_id"])] += 1
    state["exact_class_pair_id"][row["exact_class_pair_id"]] += 1
    state["class_pair_role"][f"{row['exact_class_pair_id']}|{role}"] += 1
    state["visible_endpoint_pair"][row["visible_endpoint_pair"]] += 1
    state["subject_label"][row["subject_label"]] += 1
    state["object_label"][row["object_label"]] += 1
    state["rank_band"][row["rank_band"]] += 1
    state["geometry_bucket"][row["geometry_bucket"]] += 1
    state["coverage_proxy"][row["coverage_proxy"]] += 1
    state["uncertainty_bucket"][row["uncertainty_bucket"]] += 1
    state["gt_label_match_status"][row["gt_label_match_status"]] += 1
    return True


def mine_for_predicate(
    predicate: str,
    groups: dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]],
) -> tuple[list[dict[str, Any]], dict[str, Counter[str]], list[dict[str, Any]]]:
    state: dict[str, Counter[str]] = defaultdict(Counter)
    selected: list[dict[str, Any]] = []
    selected_groups: set[str] = set()
    group_rows: list[dict[str, Any]] = []
    role_targets = TARGET_ROLE_QUOTAS[predicate]
    eligible = [
        (key, roles)
        for key, roles in groups.items()
        if key[0] == predicate and roles.get(ROLE_ACCEPT) and roles.get(ROLE_REJECT)
    ]
    eligible.sort(key=lambda item: group_score(item[0], item[1]))

    # First pass: force mixed accept/reject evidence within exact predicate/class-pair cells.
    for key, roles in eligible:
        if state["predicate_role"][f"{predicate}|{ROLE_ACCEPT}"] >= role_targets[ROLE_ACCEPT]:
            break
        added_in_group = 0
        for role in (ROLE_ACCEPT, ROLE_REJECT):
            for row in roles.get(role, []):
                if add_selected(row, selected, state, role_targets):
                    selected_groups.add(row["exact_class_pair_id"])
                    added_in_group += 1
                    break
        if added_in_group:
            group_rows.append(group_manifest_row(key, roles, "primary_mixed_pair_seed"))

    # Second pass: fill extra reject rows from the same controlled cells where possible.
    for key, roles in eligible:
        if state["predicate_role"][f"{predicate}|{ROLE_REJECT}"] >= role_targets[ROLE_REJECT]:
            break
        for row in roles.get(ROLE_REJECT, []):
            if row["exact_class_pair_id"] not in selected_groups:
                continue
            if add_selected(row, selected, state, role_targets):
                break

    # Third pass: include uncertain rows from already selected exact cells for p_obs/Q_e stress.
    for key, roles in eligible:
        if state["predicate_role"][f"{predicate}|{ROLE_UNCERTAIN}"] >= role_targets[ROLE_UNCERTAIN]:
            break
        for row in roles.get(ROLE_UNCERTAIN, []):
            if row["exact_class_pair_id"] not in selected_groups:
                continue
            if add_selected(row, selected, state, role_targets):
                break

    # Fallback pass: fill any remaining role quota from eligible cells while preserving exact-cell mixture.
    for role in (ROLE_ACCEPT, ROLE_REJECT, ROLE_UNCERTAIN):
        while state["predicate_role"][f"{predicate}|{role}"] < role_targets[role]:
            progressed = False
            for key, roles in eligible:
                if role == ROLE_UNCERTAIN and key[0] != predicate:
                    continue
                for row in roles.get(role, []):
                    if role == ROLE_UNCERTAIN and row["exact_class_pair_id"] not in selected_groups:
                        continue
                    if add_selected(row, selected, state, role_targets):
                        progressed = True
                        break
                if state["predicate_role"][f"{predicate}|{role}"] >= role_targets[role]:
                    break
            if not progressed:
                break

    selected.sort(key=lambda row: (row["predicate_label"], row["reliability_proxy_role"], row["exact_class_pair_id"], row["selection_hash"]))
    return selected, state, group_rows


def group_manifest_row(key: tuple[str, str, str], roles: dict[str, list[dict[str, Any]]], selection_role: str) -> dict[str, Any]:
    predicate, subject, obj = key
    return {
        "predicate_label": predicate,
        "subject_label": subject,
        "object_label": obj,
        "exact_class_pair_id": "|".join(key),
        "selection_role": selection_role,
        "accept_proxy_available": len(roles.get(ROLE_ACCEPT, [])),
        "reject_proxy_available": len(roles.get(ROLE_REJECT, [])),
        "uncertain_proxy_available": len(roles.get(ROLE_UNCERTAIN, [])),
        "anchor_priority": max([row["anchor_priority"] for rows in roles.values() for row in rows] or [0]),
    }


def internal_candidate(row: dict[str, Any], selection_index: int) -> dict[str, Any]:
    keep = [
        "candidate_id",
        "prediction_id",
        "scan_id",
        "subgraph_id",
        "directed_pair_id",
        "subject_id",
        "object_id",
        "subject_label",
        "predicate_label",
        "object_label",
        "visible_endpoint_pair",
        "reliability_proxy_role",
        "rank_band",
        "semantic_rank",
        "geometry_bucket",
        "coverage_proxy",
        "uncertainty_bucket",
        "capacity_evidence_tier",
        "cell_id_hidden",
        "provisional_status_hidden",
        "anchor_bucket_hidden",
        "gt_label_match_status",
        "raw_feature_join_state",
        "near_contact",
        "loose_near_contact",
        "far_separated",
        "projected_overlap_support",
        "uncertainty_flags",
        "exact_class_pair_id",
        "anchor_priority",
        "source_geometry_family",
        "source_geometry_predicate",
        "hash_key",
    ]
    out = {key: row.get(key) for key in keep}
    out.update(
        {
            "schema_version": "h002_r7_attachment_observability_candidate_internal_v1",
            "selection_index": selection_index,
            "split": "train_only",
            "source_id": "open3dsg_train_full",
            "candidate_role": "primary_attachment_observability_repair",
            "hidden_proxy_fields_not_model_input": True,
            "requires_packet_materialization_before_label": True,
        }
    )
    return out


def packet_request(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "packet_request_id": row["candidate_id"].replace("r7cand", "r7pkt", 1),
        "candidate_id": row["candidate_id"],
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "directed_pair_id": row["directed_pair_id"],
        "subject_id": row["subject_id"],
        "object_id": row["object_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "object_label": row["object_label"],
        "packet_scope": "pair_multiview_mesh_contact_if_available",
        "labeler_visible_relation": f"{row['subject_label']} {row['predicate_label']} {row['object_label']}",
        "hidden_proxy_role": row["reliability_proxy_role"],
        "hidden_exact_class_pair_id": row["exact_class_pair_id"],
        "do_not_show_hidden_fields_to_labeler": True,
    }


def quota_rows(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counts = Counter(f"{row['predicate_label']}|{row['reliability_proxy_role']}" for row in selected)
    for predicate, role_targets in TARGET_ROLE_QUOTAS.items():
        for role, target in role_targets.items():
            actual = counts[f"{predicate}|{role}"]
            rows.append(
                {
                    "predicate_label": predicate,
                    "proxy_role": role,
                    "target_rows": target,
                    "selected_rows": actual,
                    "pass": actual == target,
                }
            )
    return rows


def validate_outputs(selected: list[dict[str, Any]], quota_audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_total = sum(sum(targets.values()) for targets in TARGET_ROLE_QUOTAS.values())
    if len(selected) != expected_total:
        errors.append({"error_type": "selected_count_mismatch", "expected": expected_total, "actual": len(selected)})
    if len({row["prediction_id"] for row in selected}) != len(selected):
        errors.append({"error_type": "duplicate_prediction_id"})
    if len({row["candidate_id"] for row in selected}) != len(selected):
        errors.append({"error_type": "duplicate_candidate_id"})
    for row in quota_audit:
        if row["pass"] is not True:
            errors.append({"error_type": "quota_not_met", **row})
    for predicate in PRIMARY_PREDICATES:
        groups = defaultdict(set)
        for row in selected:
            if row["predicate_label"] != predicate:
                continue
            groups[row["exact_class_pair_id"]].add(row["reliability_proxy_role"])
        mixed = sum(1 for roles in groups.values() if ROLE_ACCEPT in roles and ROLE_REJECT in roles)
        if mixed < 50:
            errors.append({"error_type": "too_few_selected_mixed_exact_class_pair_groups", "predicate": predicate, "actual": mixed, "minimum": 50})
    return errors


def summarize_selection(selected: list[dict[str, Any]], group_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in selected:
        counts["predicate"][row["predicate_label"]] += 1
        counts["role"][row["reliability_proxy_role"]] += 1
        counts["predicate_role"][f"{row['predicate_label']}|{row['reliability_proxy_role']}"] += 1
        counts["scan_id"][str(row["scan_id"])] += 1
        counts["exact_class_pair_id"][row["exact_class_pair_id"]] += 1
        counts["subject_label"][row["subject_label"]] += 1
        counts["object_label"][row["object_label"]] += 1
        counts["rank_band"][row["rank_band"]] += 1
        counts["geometry_bucket"][row["geometry_bucket"]] += 1
        counts["coverage_proxy"][row["coverage_proxy"]] += 1
        counts["uncertainty_bucket"][row["uncertainty_bucket"]] += 1
        counts["gt_label_match_status"][row["gt_label_match_status"]] += 1
    mixed_by_predicate: dict[str, int] = {}
    for predicate in PRIMARY_PREDICATES:
        groups = defaultdict(set)
        for row in selected:
            if row["predicate_label"] == predicate:
                groups[row["exact_class_pair_id"]].add(row["reliability_proxy_role"])
        mixed_by_predicate[predicate] = sum(1 for roles in groups.values() if ROLE_ACCEPT in roles and ROLE_REJECT in roles)
    return {
        "selected_rows": len(selected),
        "predicate_counts": dict(counts["predicate"]),
        "role_counts": dict(counts["role"]),
        "predicate_role_counts": dict(counts["predicate_role"]),
        "unique_scans": len(counts["scan_id"]),
        "unique_exact_class_pairs": len(counts["exact_class_pair_id"]),
        "mixed_exact_class_pair_groups_by_predicate": mixed_by_predicate,
        "top_scans": counts["scan_id"].most_common(10),
        "top_exact_class_pairs": counts["exact_class_pair_id"].most_common(12),
        "top_subject_labels": counts["subject_label"].most_common(12),
        "top_object_labels": counts["object_label"].most_common(12),
        "rank_band_counts": dict(counts["rank_band"]),
        "geometry_bucket_counts": dict(counts["geometry_bucket"]),
        "coverage_proxy_counts": dict(counts["coverage_proxy"]),
        "uncertainty_bucket_counts": dict(counts["uncertainty_bucket"]),
        "gt_label_match_status_counts": dict(counts["gt_label_match_status"]),
        "selected_group_manifest_rows": len(group_rows),
    }


def build_report(summary: dict[str, Any]) -> str:
    counts = summary["selection_summary"]
    lines = [
        "# H002 R7 Attachment Observability Class-Pair Repair Candidate Mining",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Selection",
        "",
        "```text",
        f"selected_rows = {counts['selected_rows']}",
        f"predicate_counts = {counts['predicate_counts']}",
        f"predicate_role_counts = {counts['predicate_role_counts']}",
        f"unique_scans = {counts['unique_scans']}",
        f"unique_exact_class_pairs = {counts['unique_exact_class_pairs']}",
        f"mixed_exact_class_pair_groups_by_predicate = {counts['mixed_exact_class_pair_groups_by_predicate']}",
        "```",
        "",
        "## Interpretation",
        "",
        "The capacity-passed R7 full-train pool can provide controlled candidate rows for both primary attachment predicates.",
        "Rows are selected from exact predicate/class-pair cells that contain both accept and reject proxy candidates.",
        "Uncertain proxy rows are included from selected cells to stress the later `Q_e`/`p_obs` label path.",
        "",
        "This is not yet a learned result or a reliability label artifact. The next step is packet materialization planning,",
        "then packet creation, label ingestion, and schema/shortcut audit before learned smoke.",
        "",
        "## Boundary",
        "",
        "- Train-only candidate mining.",
        "- No validation/test rows used.",
        "- No H001 artifacts modified.",
        "- No human labels filled or ingested.",
        "- No packet files created.",
        "- No learned model or posterior smoke.",
        "- Proxy roles, source rank/score, geometry bucket, coverage proxy, and GT status are hidden construction/audit fields.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    capacity_summary_path = args.capacity_dir / "summary.json"
    capacity_summary = read_json(capacity_summary_path) if capacity_summary_path.exists() else {}
    validation_errors = validate_capacity(capacity_summary, args.match_rows)

    groups, inventory = scan_candidates(args.match_rows) if args.match_rows.exists() else ({}, {})
    selected: list[dict[str, Any]] = []
    states: dict[str, dict[str, Counter[str]]] = {}
    group_rows: list[dict[str, Any]] = []
    for predicate in PRIMARY_PREDICATES:
        pred_selected, state, pred_group_rows = mine_for_predicate(predicate, groups)
        selected.extend(pred_selected)
        states[predicate] = state
        group_rows.extend(pred_group_rows)

    selected.sort(key=lambda row: (row["predicate_label"], row["reliability_proxy_role"], row["exact_class_pair_id"], row["selection_hash"]))
    internal_rows = [internal_candidate(row, idx) for idx, row in enumerate(selected)]
    packet_rows = [packet_request(row) for row in internal_rows]
    quota_audit = quota_rows(selected)
    validation_errors.extend(validate_outputs(selected, quota_audit))

    status = STATUS_READY if not validation_errors else STATUS_ERROR
    next_todo = NEXT_TODO if not validation_errors else "fix_attachment_observability_class_pair_repair_candidate_mining"
    output_paths = {
        "candidate_rows_internal": args.output_dir / "candidate_rows_internal.jsonl",
        "packet_request_manifest": args.output_dir / "packet_request_manifest.jsonl",
        "quota_audit": args.output_dir / "quota_audit.csv",
        "selection_group_manifest": args.output_dir / "selection_group_manifest.csv",
        "report": args.output_dir / "report.md",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": True,
            "materializes_model_rows": False,
            "packet_materialization_started": False,
            "paper_evidence_allowed": False,
            "proxy_capacity_only": False,
            "runs_learned_smoke": False,
            "split": "train_only_candidate_mining",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "candidate_contract": {
            "primary_predicates": PRIMARY_PREDICATES,
            "diagnostic_predicates": DIAGNOSTIC_PREDICATES,
            "role_quotas": TARGET_ROLE_QUOTAS,
            "connected_to_primary_rows": 0,
            "hidden_fields_not_model_input": [
                "reliability_proxy_role",
                "rank_band",
                "semantic_rank",
                "geometry_bucket",
                "coverage_proxy",
                "uncertainty_bucket",
                "gt_label_match_status",
                "source score/rank",
            ],
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "capacity_summary": rel_path(capacity_summary_path),
            "match_rows": rel_path(args.match_rows),
        },
        "inventory": inventory,
        "next_todo": next_todo,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "schema_version": SCHEMA_VERSION,
        "selection_summary": summarize_selection(selected, group_rows),
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_jsonl(output_paths["candidate_rows_internal"], internal_rows)
    write_jsonl(output_paths["packet_request_manifest"], packet_rows)
    write_csv(output_paths["quota_audit"], quota_audit)
    write_csv(output_paths["selection_group_manifest"], group_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
                "selection_summary": summary["selection_summary"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
