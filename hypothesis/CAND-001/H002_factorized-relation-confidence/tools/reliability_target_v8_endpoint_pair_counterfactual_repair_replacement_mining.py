#!/usr/bin/env python3
"""Mine replacements for partial rows in the H002 v8 repair batch."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v8_endpoint_pair_counterfactual_target_repair_and_additional_mining as repair


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

GAP_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_asset_packet_gap_audit_codex_proxy_user_requested"
REPAIR_SOURCE_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_target_repair_and_additional_mining_codex_proxy_user_requested"
OLD_V8_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_codex_proxy_user_requested"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_mining_codex_proxy_user_requested"
DEFAULT_PACKET_MANIFESTS = list(repair.DEFAULT_PACKET_MANIFESTS) + [
    RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_asset_packets_codex_proxy_user_requested/generated_packet_manifest.jsonl",
]

SCHEMA_VERSION = "h002_reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_mining_v1"
EXPECTED_GAP_STATUS = "h002_reliability_target_v8_repair_asset_packet_gap_audit_needs_replacement"
EXPECTED_GAP_NEXT = "reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_mining"

TARGET_PREDICATE_COUNTS = {
    "higher than": 60,
    "lower than": 60,
    "standing on": 40,
    "lying on": 40,
}
TARGET_ROLE_COUNTS = {
    "vertical_direction_counterfactual": 120,
    "support_pose_counterfactual": 80,
}
MAX_ROWS_PER_SCAN = 6
MAX_ROWS_PER_LABEL_PAIR = 8
MAX_ROWS_PER_FAMILY_CELL = 6
FORBIDDEN_VISIBLE_FIELD_TOKENS = [
    "hidden",
    "semantic_score",
    "semantic_rank",
    "p_geom",
    "geometry_status",
    "rank_band",
    "source_queue",
    "endpoint_pair_key",
    "counterfactual_pair_id",
    "bucket",
    "label_match",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-dir", type=Path, default=GAP_DIR)
    parser.add_argument("--repair-source-dir", type=Path, default=REPAIR_SOURCE_DIR)
    parser.add_argument("--old-v8-candidate-dir", type=Path, default=OLD_V8_CANDIDATE_DIR)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--packet-manifest", type=Path, action="append", default=list(DEFAULT_PACKET_MANIFESTS))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    abs_path = as_abs(path)
    if not abs_path.exists():
        return rows
    with abs_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def read_tsv(path: Path) -> list[dict[str, Any]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


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
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_gap(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_GAP_STATUS:
        errors.append({"error_type": "unexpected_gap_status", "expected": EXPECTED_GAP_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_GAP_NEXT:
        errors.append({"error_type": "unexpected_gap_next", "expected": EXPECTED_GAP_NEXT, "actual": summary.get("next_todo")})
    boundary = summary.get("boundary") or {}
    for key in [
        "validation_usage",
        "test_usage",
        "posterior_trained",
        "posterior_smoke_allowed",
        "multi_view_as_model_input",
        "h001_artifacts_modified",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "gap_boundary_not_false", "field": key, "actual": boundary.get(key)})
    return errors


def sanitize_visible_row(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in repair.VISIBLE_FIELDS}


def load_used_rows(repair_source_dir: Path, old_v8_candidate_dir: Path) -> tuple[set[str], set[str]]:
    used_prediction_ids: set[str] = set()
    used_exact_keys: set[str] = set()
    for path in [
        repair_source_dir / "selected_primary_candidates.jsonl",
        old_v8_candidate_dir / "selected_candidates_internal.jsonl",
    ]:
        for row in read_jsonl(path):
            if row.get("prediction_id"):
                used_prediction_ids.add(str(row.get("prediction_id")))
            exact_key = row.get("exact_endpoint_pair_key_hidden") or row.get("exact_endpoint_pair_key")
            if exact_key:
                used_exact_keys.add(str(exact_key))
    return used_prediction_ids, used_exact_keys


def current_counters(rows: list[dict[str, Any]]) -> dict[str, Counter]:
    return {
        "scan": Counter(str(row.get("scan_id")) for row in rows),
        "label_pair": Counter(str(row.get("subject_object_label_pair_hidden")) for row in rows),
        "family_cell": Counter(str(row.get("subject_object_family_cell_hidden")) for row in rows),
        "exact": Counter(str(row.get("exact_endpoint_pair_key_hidden")) for row in rows),
    }


def pair_ready(rows: list[dict[str, Any]], packets: dict[tuple[str, str, str, str], dict[str, Any]]) -> int:
    return sum(1 for row in rows if repair.is_packet_ready(packets.get(repair.packet_key(row))))


def can_add_pair(rows: list[dict[str, Any]], counters: dict[str, Counter], selected_prediction_ids: set[str], used_exact_keys: set[str]) -> bool:
    if len(rows) != 2:
        return False
    if any(str(row.get("prediction_id")) in selected_prediction_ids for row in rows):
        return False
    exact_key = str(rows[0].get("exact_endpoint_pair_key"))
    if exact_key in used_exact_keys or counters["exact"][exact_key] > 0:
        return False
    scan = str(rows[0].get("scan_id"))
    label_pair = str(rows[0].get("subject_object_label_pair"))
    if counters["scan"][scan] + 2 > MAX_ROWS_PER_SCAN:
        return False
    if counters["label_pair"][label_pair] + 2 > MAX_ROWS_PER_LABEL_PAIR:
        return False
    future_family_cells = Counter(str(row.get("subject_object_family_cell")) for row in rows)
    for cell, add_count in future_family_cells.items():
        if counters["family_cell"][cell] + add_count > MAX_ROWS_PER_FAMILY_CELL:
            return False
    return True


def add_pair_counters(rows: list[dict[str, Any]], counters: dict[str, Counter]) -> None:
    exact_key = str(rows[0].get("exact_endpoint_pair_key"))
    for row in rows:
        counters["scan"][str(row.get("scan_id"))] += 1
        counters["label_pair"][str(row.get("subject_object_label_pair"))] += 1
        counters["family_cell"][str(row.get("subject_object_family_cell"))] += 1
        counters["exact"][exact_key] += 1


def replacement_row(source: dict[str, Any], role: str, pair_id: str, pair_type: str, packet: dict[str, Any] | None) -> dict[str, Any]:
    row = repair.selected_candidate_row(source, role, pair_id, packet, pair_type)
    row["batch_name"] = "v8_target_repair_replacement_mining"
    row["replacement_source_hidden"] = "v8_repair_gap_audit_replacement_mining"
    row["replacement_reason_hidden"] = "replace_partial_packet_row_excluded_from_primary_target"
    row["primary_gap_decision_hidden"] = "primary_label_ready"
    row["diagnostic_status_hidden"] = "replacement_packet_ready" if row["packet_status_hidden"] == "ready" else "replacement_asset_needed"
    row["diagnostic_reason_hidden"] = "replacement mined after conservative partial packet exclusion"
    row["label_fill_allowed"] = False
    row["posterior_input_allowed"] = False
    forbidden = list(row.get("forbidden_as_labeler_visible") or [])
    for field in [
        "replacement_source_hidden",
        "replacement_reason_hidden",
        "primary_gap_decision_hidden",
        "diagnostic_status_hidden",
        "diagnostic_reason_hidden",
    ]:
        if field not in forbidden:
            forbidden.append(field)
    row["forbidden_as_labeler_visible"] = forbidden
    return row


def select_replacement_pairs(
    inventory: list[dict[str, Any]],
    by_exact: dict[str, list[dict[str, Any]]],
    packets: dict[tuple[str, str, str, str], dict[str, Any]],
    ready_rows: list[dict[str, Any]],
    used_prediction_ids: set[str],
    used_exact_keys: set[str],
    vertical_pairs_needed: int,
    support_pairs_needed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int], Counter]:
    counters = current_counters(ready_rows)
    selected_prediction_ids = set(used_prediction_ids)
    selected_exact_keys = set(used_exact_keys)
    replacements: list[dict[str, Any]] = []
    source_preview: list[dict[str, Any]] = []
    rejected = Counter()

    def add_group(item: dict[str, Any], predicates: tuple[str, str], role: str, pair_type: str) -> bool:
        group_rows = by_exact[item["group_key"]]
        pair_sources: list[dict[str, Any]] = []
        for predicate in predicates:
            row = repair.choose_predicate_row(group_rows, predicate)
            if row is None:
                rejected[f"missing_{predicate}"] += 1
                return False
            pair_sources.append(row)
        if not can_add_pair(pair_sources, counters, selected_prediction_ids, selected_exact_keys):
            rejected["cap_or_duplicate_blocked"] += 1
            return False
        pair_id = "ftv8r_repl_pair_" + repair.stable_hash("|".join(str(row.get("prediction_id")) for row in pair_sources))[:12]
        for source in pair_sources:
            packet = packets.get(repair.packet_key(source))
            row = replacement_row(source, role, pair_id, pair_type, packet)
            replacements.append(row)
            source_preview.append(source)
            selected_prediction_ids.add(str(source.get("prediction_id")))
        selected_exact_keys.add(str(pair_sources[0].get("exact_endpoint_pair_key")))
        add_pair_counters(pair_sources, counters)
        return True

    def eligible_items(flag: str, predicates: tuple[str, str]) -> list[tuple[tuple[Any, ...], dict[str, Any]]]:
        output: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        for item in inventory:
            if not item[flag]:
                continue
            if item["structural_pair"] or item["generic_endpoint_pair"] or item["has_current_v8_label"]:
                rejected["ineligible_group"] += 1
                continue
            group_rows = by_exact[item["group_key"]]
            pair_sources = [repair.choose_predicate_row(group_rows, predicate) for predicate in predicates]
            if any(row is None for row in pair_sources):
                rejected["missing_pair_predicate"] += 1
                continue
            ready_count = pair_ready([row for row in pair_sources if row is not None], packets)
            priority = (-ready_count, repair.group_priority(item))
            output.append((priority, item))
        return sorted(output, key=lambda entry: entry[0])

    vertical_selected = 0
    for _priority, item in eligible_items("vertical_direction_counterfactual", ("lower than", "higher than")):
        if vertical_selected >= vertical_pairs_needed:
            break
        if add_group(item, ("lower than", "higher than"), "vertical_direction_counterfactual", "same_endpoint_higher_lower_replacement"):
            vertical_selected += 1

    support_selected = 0
    for _priority, item in eligible_items("support_pose_counterfactual", ("standing on", "lying on")):
        if support_selected >= support_pairs_needed:
            break
        if add_group(item, ("standing on", "lying on"), "support_pose_counterfactual", "same_endpoint_standing_lying_replacement"):
            support_selected += 1

    selected_counts = {"vertical_pairs_selected": vertical_selected, "support_pairs_selected": support_selected}
    return replacements, source_preview, selected_counts, rejected


def visible_leakage_hits(rows: list[dict[str, Any]], fieldnames: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in fieldnames:
        lower = field.lower()
        for token in FORBIDDEN_VISIBLE_FIELD_TOKENS:
            if token in lower:
                hits.append({"surface": "field_name", "field": field, "forbidden_token": token})
    for row_number, row in enumerate(rows, start=2):
        for field, value in row.items():
            if field not in {"blind_review_id", "review_scope", "multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"}:
                continue
            lower = str(value).lower()
            for token in ["semantic_score", "p_geom_valid", "geometry_status_hidden", "source_queue_hidden"]:
                if token in lower:
                    hits.append({"surface": "field_value", "row_number": row_number, "field": field, "forbidden_token": token})
    return hits


def balance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    predicate_counts = Counter(str(row.get("predicate_label")) for row in rows)
    role_counts = Counter(str(row.get("additional_batch_role_hidden")) for row in rows)
    output: list[dict[str, Any]] = []
    for key, target in TARGET_PREDICATE_COUNTS.items():
        output.append({"group": "predicate_label", "key": key, "target_rows": target, "actual_rows": predicate_counts.get(key, 0), "delta": predicate_counts.get(key, 0) - target})
    for key, target in TARGET_ROLE_COUNTS.items():
        output.append({"group": "additional_batch_role", "key": key, "target_rows": target, "actual_rows": role_counts.get(key, 0), "delta": role_counts.get(key, 0) - target})
    return output


def cap_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters = {
        "scan_id": Counter(str(row.get("scan_id")) for row in rows),
        "subject_object_label_pair_hidden": Counter(str(row.get("subject_object_label_pair_hidden")) for row in rows),
        "subject_object_family_cell_hidden": Counter(str(row.get("subject_object_family_cell_hidden")) for row in rows),
        "exact_endpoint_pair_key_hidden": Counter(str(row.get("exact_endpoint_pair_key_hidden")) for row in rows),
        "prediction_id": Counter(str(row.get("prediction_id")) for row in rows),
        "blind_review_id": Counter(str(row.get("blind_review_id")) for row in rows),
    }
    rows_out: list[dict[str, Any]] = []
    for group, counter in counters.items():
        limit = {
            "scan_id": MAX_ROWS_PER_SCAN,
            "subject_object_label_pair_hidden": MAX_ROWS_PER_LABEL_PAIR,
            "subject_object_family_cell_hidden": MAX_ROWS_PER_FAMILY_CELL,
            "exact_endpoint_pair_key_hidden": 2,
            "prediction_id": 1,
            "blind_review_id": 1,
        }[group]
        for key, count in sorted(counter.items()):
            rows_out.append({"group": group, "key": key, "rows": count, "limit": limit, "violates_cap": count > limit})
    return rows_out


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V8 Repair Replacement Mining",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "```text",
        "split = train_only",
        "validation_usage = False",
        "test_usage = False",
        "labels_filled = False",
        "posterior_trained = False",
        "posterior_smoke_allowed = False",
        "multi_view_as_model_input = False",
        "h001_artifacts_modified = False",
        "```",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next = {summary['next_todo']}",
        f"validation_errors = {summary['validation_error_count']}",
        "```",
        "",
        "## Counts",
        "",
        "```text",
        f"ready_input_rows = {summary['counts']['ready_input_rows']}",
        f"replacement_rows_requested = {summary['counts']['replacement_rows_requested']}",
        f"replacement_rows_selected = {summary['counts']['replacement_rows_selected']}",
        f"combined_rows = {summary['counts']['combined_rows']}",
        f"replacement_packet_ready_rows = {summary['counts']['replacement_packet_ready_rows']}",
        f"replacement_asset_needed_rows = {summary['counts']['replacement_asset_needed_rows']}",
        f"vertical_pairs_selected = {summary['counts']['vertical_pairs_selected']}",
        f"support_pairs_selected = {summary['counts']['support_pairs_selected']}",
        "```",
        "",
        "## Predicate Balance",
        "",
        "```text",
        f"combined_predicate_counts = {summary['counts']['combined_predicate_counts']}",
        f"combined_role_counts = {summary['counts']['combined_role_counts']}",
        "```",
        "",
        "## Interpretation",
        "",
        summary["decision"],
        "",
        "## Next TODO",
        "",
        "```text",
        summary["next_todo"],
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    gap_dir = as_abs(args.gap_dir)
    repair_source_dir = as_abs(args.repair_source_dir)
    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gap_summary = read_json(gap_dir / "summary.json")
    validation_errors = validate_gap(gap_summary)
    ready_rows = read_jsonl(gap_dir / "primary_label_ready_manifest_post_label_only.jsonl")
    ready_label_rows = [sanitize_visible_row(row) for row in read_tsv(gap_dir / "primary_label_ready_sheet.tsv")]
    replacement_plan = read_jsonl(gap_dir / "replacement_request_plan.jsonl")

    replacement_predicate_counts = Counter(str(row.get("predicate_label")) for row in replacement_plan)
    vertical_pairs_needed = min(replacement_predicate_counts.get("lower than", 0), replacement_predicate_counts.get("higher than", 0))
    support_pairs_needed = min(replacement_predicate_counts.get("standing on", 0), replacement_predicate_counts.get("lying on", 0))

    used_prediction_ids, used_exact_keys = load_used_rows(repair_source_dir, as_abs(args.old_v8_candidate_dir))
    train_rows, _train_counts, train_errors = repair.read_train_rows(as_abs(args.hl_queue), as_abs(args.lh_queue))
    validation_errors.extend(train_errors)
    inventory, by_exact, inventory_counts = repair.group_inventory(train_rows, used_exact_keys)
    packets = repair.load_ready_packets([as_abs(path) for path in args.packet_manifest])

    replacements, replacement_sources, selected_pair_counts, rejected = select_replacement_pairs(
        inventory=inventory,
        by_exact=by_exact,
        packets=packets,
        ready_rows=ready_rows,
        used_prediction_ids=used_prediction_ids,
        used_exact_keys=used_exact_keys,
        vertical_pairs_needed=vertical_pairs_needed,
        support_pairs_needed=support_pairs_needed,
    )
    replacement_visible_rows = [repair.visible_row(row) for row in replacements]
    combined_rows = sorted(
        ready_rows + replacements,
        key=lambda row: (
            str(row.get("predicate_family")),
            str(row.get("predicate_label")),
            str(row.get("scan_id")),
            str(row.get("subject_id")),
            str(row.get("object_id")),
            str(row.get("blind_review_id")),
        ),
    )
    combined_visible_rows = ready_label_rows + replacement_visible_rows
    fieldnames = list(repair.VISIBLE_FIELDS)

    replacement_packet_ready = [row for row in replacements if row.get("packet_status_hidden") == "ready"]
    replacement_asset_needed = [row for row in replacements if row.get("packet_status_hidden") != "ready"]
    asset_requests = [repair.asset_request_row(row) for row in replacement_asset_needed]
    balance_audit = balance_rows(combined_rows)
    cap_audit = cap_rows(combined_rows)
    leakage_hits = visible_leakage_hits(combined_visible_rows, fieldnames)

    if len(replacements) != len(replacement_plan):
        validation_errors.append({"error_type": "replacement_count_mismatch", "expected": len(replacement_plan), "actual": len(replacements)})
    if len(combined_rows) != 200:
        validation_errors.append({"error_type": "combined_row_count_mismatch", "expected": 200, "actual": len(combined_rows)})
    for row in balance_audit:
        if row["actual_rows"] != row["target_rows"]:
            validation_errors.append({"error_type": "balance_mismatch", **row})
    cap_violations = [row for row in cap_audit if row["violates_cap"]]
    if cap_violations:
        validation_errors.append({"error_type": "cap_violation", "violations": cap_violations[:20], "violation_count": len(cap_violations)})
    if leakage_hits:
        validation_errors.append({"error_type": "visible_label_surface_leakage", "count": len(leakage_hits)})

    predicate_counts = dict(sorted(Counter(str(row.get("predicate_label")) for row in combined_rows).items()))
    role_counts = dict(sorted(Counter(str(row.get("additional_batch_role_hidden")) for row in combined_rows).items()))
    if validation_errors:
        status = "h002_reliability_target_v8_repair_replacement_mining_errors"
        next_todo = "fix_reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_mining_errors"
        decision = "Replacement mining did not satisfy the repair target contract; inspect validation_errors.jsonl."
    elif replacement_asset_needed:
        status = "h002_reliability_target_v8_repair_replacement_mining_ready_needs_asset_packets"
        next_todo = "reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_asset_packets"
        decision = "Replacement mining restored the 200-row repair batch, but some replacement rows need evidence packets before label readiness."
    else:
        status = "h002_reliability_target_v8_repair_replacement_mining_ready_for_label_readiness"
        next_todo = "reliability_target_v8_endpoint_pair_counterfactual_repair_label_readiness"
        decision = "Replacement mining restored the 200-row repair batch with packet-ready replacements. Proceed to label readiness, not posterior smoke."

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "replacement_candidates_internal": output_dir / "replacement_candidates_internal.jsonl",
        "replacement_sources_preview": output_dir / "replacement_sources_preview.jsonl",
        "replacement_packet_ready_candidates": output_dir / "replacement_packet_ready_candidates.jsonl",
        "replacement_asset_needed_candidates": output_dir / "replacement_asset_needed_candidates.jsonl",
        "replacement_asset_request_manifest": output_dir / "replacement_asset_request_manifest.jsonl",
        "repaired_200_manifest_pre_label_readiness": output_dir / "repaired_200_manifest_pre_label_readiness.jsonl",
        "repaired_200_label_sheet_pre_label_readiness": output_dir / "repaired_200_label_sheet_pre_label_readiness.tsv",
        "predicate_balance_audit": output_dir / "predicate_balance_audit.csv",
        "cap_audit": output_dir / "cap_audit.csv",
        "pool_filter_summary": output_dir / "pool_filter_summary.csv",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "labels_filled": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "paper_metric_evidence": False,
            "h001_artifacts_modified": False,
        },
        "input_paths": {
            "gap_summary": rel_path(gap_dir / "summary.json"),
            "ready_manifest": rel_path(gap_dir / "primary_label_ready_manifest_post_label_only.jsonl"),
            "ready_label_sheet": rel_path(gap_dir / "primary_label_ready_sheet.tsv"),
            "replacement_request_plan": rel_path(gap_dir / "replacement_request_plan.jsonl"),
            "repair_source_selected_primary": rel_path(repair_source_dir / "selected_primary_candidates.jsonl"),
            "old_v8_candidate_dir": rel_path(args.old_v8_candidate_dir),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
            "packet_manifests": [rel_path(path) for path in args.packet_manifest],
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "inventory_counts": inventory_counts,
        "counts": {
            "ready_input_rows": len(ready_rows),
            "replacement_rows_requested": len(replacement_plan),
            "replacement_rows_selected": len(replacements),
            "combined_rows": len(combined_rows),
            "replacement_packet_ready_rows": len(replacement_packet_ready),
            "replacement_asset_needed_rows": len(replacement_asset_needed),
            "vertical_pairs_needed": vertical_pairs_needed,
            "support_pairs_needed": support_pairs_needed,
            **selected_pair_counts,
            "combined_predicate_counts": predicate_counts,
            "combined_role_counts": role_counts,
            "replacement_predicate_counts": dict(sorted(Counter(str(row.get("predicate_label")) for row in replacements).items())),
            "replacement_role_counts": dict(sorted(Counter(str(row.get("additional_batch_role_hidden")) for row in replacements).items())),
            "combined_scans": len({row.get("scan_id") for row in combined_rows}),
            "combined_exact_endpoint_pairs": len({row.get("exact_endpoint_pair_key_hidden") for row in combined_rows}),
            "max_rows_per_scan": max(Counter(str(row.get("scan_id")) for row in combined_rows).values()) if combined_rows else 0,
            "max_rows_per_label_pair": max(Counter(str(row.get("subject_object_label_pair_hidden")) for row in combined_rows).values()) if combined_rows else 0,
            "max_rows_per_family_cell": max(Counter(str(row.get("subject_object_family_cell_hidden")) for row in combined_rows).values()) if combined_rows else 0,
            "visible_leakage_hits": len(leakage_hits),
            "validation_errors": len(validation_errors),
        },
        "replacement_policy": {
            "select_pair_level_counterfactuals": True,
            "prefer_packet_ready_pairs": True,
            "avoid_original_repair_exact_pairs": True,
            "avoid_old_v8_candidate_exact_pairs": True,
            "max_rows_per_scan": MAX_ROWS_PER_SCAN,
            "max_rows_per_label_pair": MAX_ROWS_PER_LABEL_PAIR,
            "max_rows_per_family_cell": MAX_ROWS_PER_FAMILY_CELL,
        },
        "pool_filter_summary": dict(sorted(rejected.items())),
        "label_fill_allowed": False,
        "posterior_allowed": False,
        "validation_error_count": len(validation_errors),
    }

    write_jsonl(output_paths["replacement_candidates_internal"], replacements)
    write_jsonl(output_paths["replacement_sources_preview"], replacement_sources)
    write_jsonl(output_paths["replacement_packet_ready_candidates"], replacement_packet_ready)
    write_jsonl(output_paths["replacement_asset_needed_candidates"], replacement_asset_needed)
    write_jsonl(output_paths["replacement_asset_request_manifest"], asset_requests)
    write_jsonl(output_paths["repaired_200_manifest_pre_label_readiness"], combined_rows)
    write_tsv(output_paths["repaired_200_label_sheet_pre_label_readiness"], combined_visible_rows, fieldnames)
    write_csv(output_paths["predicate_balance_audit"], balance_audit)
    write_csv(output_paths["cap_audit"], cap_audit)
    write_csv(output_paths["pool_filter_summary"], [{"reason": key, "rows": value} for key, value in sorted(rejected.items())], ["reason", "rows"])
    write_jsonl(output_paths["visible_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        f"status={summary['status']} "
        f"ready={summary['counts']['ready_input_rows']} "
        f"requested={summary['counts']['replacement_rows_requested']} "
        f"selected={summary['counts']['replacement_rows_selected']} "
        f"combined={summary['counts']['combined_rows']} "
        f"replacement_ready={summary['counts']['replacement_packet_ready_rows']} "
        f"asset_needed={summary['counts']['replacement_asset_needed_rows']} "
        f"errors={summary['validation_error_count']} "
        f"next={summary['next_todo']}"
    )
    return 0 if summary["validation_error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
