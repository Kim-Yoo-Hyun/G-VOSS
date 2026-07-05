#!/usr/bin/env python3
"""Mine replacement rows for H002 v7 object-cell evidence-contrast queue."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v7_object_cell_evidence_contrast_candidate_mining as mining
import reliability_target_v7_object_cell_evidence_contrast_feasibility_scan as feasibility


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_GAP_DIR = (
    RGA_ROOT
    / "reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit_codex_proxy_user_requested"
)
DEFAULT_CANDIDATE_DIR = (
    RGA_ROOT
    / "reliability_target_v7_object_cell_evidence_contrast_candidate_mining_codex_proxy_user_requested"
)
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = (
    RGA_ROOT
    / "reliability_target_v7_object_cell_evidence_contrast_replacement_mining_codex_proxy_user_requested"
)

SCHEMA_VERSION = "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_mining_v1"
TARGET_PER_FAMILY_BUCKET = 60
TARGET_ROWS = 240
GENERIC_ENDPOINT_LABELS = {"object", "objects", "item", "items", "clutter", "unknown"}
EXPECTED_GAP_STATUS = "h002_reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit_needs_replacement"
EXPECTED_GAP_NEXT = "reliability_target_v7_object_cell_evidence_contrast_replacement_mining"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-dir", type=Path, default=DEFAULT_GAP_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--packet-manifest", type=Path, action="append", default=list(mining.DEFAULT_PACKET_MANIFESTS))
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
    with as_abs(path).open("r", encoding="utf-8") as handle:
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
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def family_bucket_key(row: dict[str, Any], bucket_field: str = "semantic_geometry_bucket_hidden") -> str:
    return f"{row.get('predicate_family')}|{row.get(bucket_field)}"


def target_family_bucket_counts() -> dict[str, int]:
    return {
        f"{family}|{bucket}": TARGET_PER_FAMILY_BUCKET
        for family in mining.PRIMARY_FAMILIES
        for bucket in mining.BUCKETS
    }


def validate_gap_inputs(gap_summary: dict[str, Any], ready_rows: list[dict[str, Any]], excluded_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if gap_summary.get("status") != EXPECTED_GAP_STATUS:
        errors.append({"error_type": "unexpected_gap_status", "actual": gap_summary.get("status")})
    if gap_summary.get("next_todo") != EXPECTED_GAP_NEXT:
        errors.append({"error_type": "unexpected_gap_next_todo", "actual": gap_summary.get("next_todo")})
    boundary = gap_summary.get("boundary") or {}
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "gap_boundary_not_false", "field": key, "actual": boundary.get(key)})
    counts = gap_summary.get("counts") or {}
    if len(ready_rows) != counts.get("label_ready_rows"):
        errors.append({"error_type": "ready_manifest_count_mismatch", "actual": len(ready_rows), "summary": counts.get("label_ready_rows")})
    if len(excluded_rows) != counts.get("excluded_rows"):
        errors.append({"error_type": "excluded_manifest_count_mismatch", "actual": len(excluded_rows), "summary": counts.get("excluded_rows")})
    if counts.get("replacement_needed_rows") != len(excluded_rows):
        errors.append(
            {
                "error_type": "replacement_needed_count_mismatch",
                "actual": len(excluded_rows),
                "summary": counts.get("replacement_needed_rows"),
            }
        )
    return errors


def count_existing(rows: list[dict[str, Any]]) -> dict[str, Counter]:
    return {
        "family_bucket": Counter(family_bucket_key(row) for row in rows),
        "strict_group": Counter(row.get("strict_group_key_hidden") for row in rows),
        "scan": Counter(str(row.get("scan_id")) for row in rows),
        "pair": Counter(row.get("subject_object_label_pair_hidden") for row in rows),
        "cell": Counter(row.get("subject_object_family_cell_hidden") for row in rows),
    }


def strict_group_key_for_enriched(row: dict[str, Any]) -> str:
    return " || ".join(str(part) for part in feasibility.strict_key(row))


def row_has_generic_endpoint(row: dict[str, Any]) -> bool:
    return str(row.get("subject_label_norm", "")).lower() in GENERIC_ENDPOINT_LABELS or str(row.get("object_label_norm", "")).lower() in GENERIC_ENDPOINT_LABELS


def row_allowed_by_caps(
    row: dict[str, Any],
    counters: dict[str, Counter],
    group_key: str,
    max_pair_rows: int,
    max_cell_rows: int,
) -> bool:
    if counters["strict_group"][group_key] + 1 > mining.MAX_ROWS_PER_STRICT_GROUP:
        return False
    if counters["scan"][str(row.get("scan_id"))] + 1 > mining.MAX_ROWS_PER_SCAN:
        return False
    if counters["pair"][row.get("subject_object_label_pair")] + 1 > max_pair_rows:
        return False
    if counters["cell"][row.get("subject_object_family_cell")] + 1 > max_cell_rows:
        return False
    return True


def is_disallowed_structure(row: dict[str, Any]) -> bool:
    return bool(row.get("hard_room_surface_pair"))


def add_counter_row(counters: dict[str, Counter], row: dict[str, Any]) -> None:
    counters["family_bucket"][family_bucket_key(row)] += 1
    counters["strict_group"][row.get("strict_group_key_hidden")] += 1
    counters["scan"][str(row.get("scan_id"))] += 1
    counters["pair"][row.get("subject_object_label_pair_hidden")] += 1
    counters["cell"][row.get("subject_object_family_cell_hidden")] += 1


def candidate_priority(row: dict[str, Any], group_summary: dict[str, Any], packet_ready: bool, current_group_count: int) -> tuple[Any, ...]:
    return (
        0 if packet_ready else 1,
        current_group_count,
        feasibility.group_priority(group_summary),
        feasibility.row_priority(row),
    )


def visible_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    return fields


def visible_leakage_hits(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in fields:
        lower = field.lower()
        for token in mining.FORBIDDEN_VISIBLE_FIELD_TOKENS:
            if token in lower:
                hits.append({"surface": "field_name", "field": field, "forbidden_token": token})
    for row_number, row in enumerate(rows, start=2):
        for field, value in row.items():
            if field in {"multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"}:
                continue
            lower = str(value).lower()
            for token in mining.FORBIDDEN_VISIBLE_VALUE_TOKENS:
                if token in lower:
                    hits.append(
                        {
                            "surface": "field_value",
                            "row_number": row_number,
                            "blind_review_id": row.get("blind_review_id"),
                            "field": field,
                            "forbidden_token": token,
                        }
                    )
                    break
    return hits


def build_cap_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters = count_existing(rows)
    limits = {
        "strict_group": mining.MAX_ROWS_PER_STRICT_GROUP,
        "scan": mining.MAX_ROWS_PER_SCAN,
        "pair": math.floor(TARGET_ROWS * mining.MAX_OBJECT_PAIR_SHARE),
        "cell": math.floor(TARGET_ROWS * mining.MAX_OBJECT_CELL_SHARE),
    }
    output: list[dict[str, Any]] = []
    for cap_name, counter in counters.items():
        if cap_name == "family_bucket":
            continue
        max_key, max_count = counter.most_common(1)[0] if counter else ("", 0)
        output.append(
            {
                "cap_name": cap_name,
                "limit": limits[cap_name],
                "max_observed": max_count,
                "max_key": max_key,
                "unique_values": len(counter),
                "violates_cap": max_count > limits[cap_name],
            }
        )
    output.extend(
        [
            {
                "cap_name": "structural_pair_rows",
                "limit": mining.MAX_STRUCTURAL_ROWS,
                "max_observed": sum(1 for row in rows if row.get("structural_pair_hidden")),
                "max_key": "structural_pair",
                "unique_values": 1,
                "violates_cap": sum(1 for row in rows if row.get("structural_pair_hidden")) > mining.MAX_STRUCTURAL_ROWS,
            },
            {
                "cap_name": "hard_room_surface_pair_rows",
                "limit": mining.MAX_HARD_ROOM_SURFACE_ROWS,
                "max_observed": sum(1 for row in rows if row.get("hard_room_surface_pair_hidden")),
                "max_key": "hard_room_surface_pair",
                "unique_values": 1,
                "violates_cap": sum(1 for row in rows if row.get("hard_room_surface_pair_hidden")) > mining.MAX_HARD_ROOM_SURFACE_ROWS,
            },
        ]
    )
    return output


def bucket_rows(rows: list[dict[str, Any]], replacements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_counts = Counter(family_bucket_key(row) for row in rows)
    replacement_counts = Counter(family_bucket_key(row) for row in replacements)
    output: list[dict[str, Any]] = []
    for key, target in target_family_bucket_counts().items():
        family, bucket = key.split("|", 1)
        output.append(
            {
                "predicate_family": family,
                "semantic_geometry_bucket": bucket,
                "target_rows": target,
                "combined_rows": all_counts.get(key, 0),
                "replacement_rows": replacement_counts.get(key, 0),
                "deficit_after_replacement": max(0, target - all_counts.get(key, 0)),
            }
        )
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V7 Object-Cell Evidence Contrast Replacement Mining",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage mining.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- H001 artifacts are not modified.",
        "- The step replaces rows excluded by the v7 asset packet gap audit.",
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
        f"excluded_input_rows = {summary['counts']['excluded_input_rows']}",
        f"replacement_rows_selected = {summary['counts']['replacement_rows_selected']}",
        f"combined_rows = {summary['counts']['combined_rows']}",
        f"replacement_packet_ready_rows = {summary['counts']['replacement_packet_ready_rows']}",
        f"replacement_asset_needed_rows = {summary['counts']['replacement_asset_needed_rows']}",
        f"combined_family_bucket_counts = {summary['counts']['combined_family_bucket_counts']}",
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
    candidate_dir = as_abs(args.candidate_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gap_summary = read_json(gap_dir / "summary.json")
    ready_rows = read_jsonl(gap_dir / "label_ready_partial_manifest_post_label_only.jsonl")
    excluded_rows = read_jsonl(gap_dir / "excluded_rows.jsonl")
    ready_label_rows = read_tsv(gap_dir / "label_ready_partial_label_sheet.tsv")
    original_selected = read_jsonl(candidate_dir / "selected_candidates_internal.jsonl")
    validation_errors = validate_gap_inputs(gap_summary, ready_rows, excluded_rows)

    target_counts = target_family_bucket_counts()
    ready_counts = Counter(family_bucket_key(row) for row in ready_rows)
    deficits = {key: target - ready_counts.get(key, 0) for key, target in target_counts.items()}
    deficits = {key: value for key, value in deficits.items() if value > 0}

    original_prediction_ids = {str(row.get("prediction_id")) for row in original_selected}
    original_blind_ids = {str(row.get("blind_review_id")) for row in original_selected}
    ready_packets = mining.load_ready_packets([as_abs(path) for path in args.packet_manifest])

    source_rows, source_counts, source_errors = feasibility.read_rows(as_abs(args.hl_queue), as_abs(args.lh_queue))
    validation_errors.extend(source_errors)
    grouped = feasibility.build_groups(source_rows)
    _, inventory = feasibility.level_summaries(grouped, source_rows)
    strict_summaries = {
        row["group_key"]: row
        for row in inventory
        if row["level"] == "strict_object_cell" and row["eligible_mixed"]
    }

    max_pair_rows = math.floor(TARGET_ROWS * mining.MAX_OBJECT_PAIR_SHARE)
    max_cell_rows = math.floor(TARGET_ROWS * mining.MAX_OBJECT_CELL_SHARE)
    counters = count_existing(ready_rows)
    candidates_by_key: dict[str, list[tuple[tuple[Any, ...], dict[str, Any], dict[str, Any] | None, dict[str, Any]]]] = {
        key: [] for key in deficits
    }
    rejected_pool_reasons: Counter = Counter()

    for row in source_rows:
        prediction_id = str(row.get("prediction_id"))
        if prediction_id in original_prediction_ids:
            rejected_pool_reasons["already_in_original_queue"] += 1
            continue
        if row.get("predicate_family") not in mining.PRIMARY_FAMILIES:
            rejected_pool_reasons["not_primary_family"] += 1
            continue
        if row.get("semantic_geometry_bucket") not in mining.BUCKETS:
            rejected_pool_reasons["not_target_bucket"] += 1
            continue
        family_bucket = f"{row.get('predicate_family')}|{row.get('semantic_geometry_bucket')}"
        if family_bucket not in deficits:
            rejected_pool_reasons["not_deficit_cell"] += 1
            continue
        if row_has_generic_endpoint(row):
            rejected_pool_reasons["generic_endpoint_label"] += 1
            continue
        if is_disallowed_structure(row):
            rejected_pool_reasons["hard_room_surface_pair"] += 1
            continue
        group_key = strict_group_key_for_enriched(row)
        group_summary = strict_summaries.get(group_key)
        if not group_summary:
            rejected_pool_reasons["not_strict_mixed_group"] += 1
            continue
        packet = ready_packets.get(mining.packet_key(row))
        priority = candidate_priority(row, group_summary, mining.packet_ready(packet), counters["strict_group"][group_key])
        candidates_by_key[family_bucket].append((priority, row, packet, group_summary))

    for key in candidates_by_key:
        candidates_by_key[key].sort(key=lambda item: item[0])

    replacements: list[dict[str, Any]] = []
    replacement_sources: list[dict[str, Any]] = []
    selected_prediction_ids: set[str] = set()
    deficit_fill_errors: list[dict[str, Any]] = []
    for family_bucket, needed in sorted(deficits.items()):
        selected_for_cell = 0
        for _, row, packet, group_summary in candidates_by_key.get(family_bucket, []):
            if selected_for_cell >= needed:
                break
            prediction_id = str(row.get("prediction_id"))
            if prediction_id in selected_prediction_ids:
                continue
            group_key = strict_group_key_for_enriched(row)
            if not row_allowed_by_caps(row, counters, group_key, max_pair_rows, max_cell_rows):
                continue
            preview = feasibility.preview_row(row, group_key, group_summary)
            internal = mining.internal_row(preview, packet)
            if str(internal["blind_review_id"]) in original_blind_ids:
                continue
            internal["batch_name"] = "reliability_target_v7_object_cell_evidence_contrast_replacement_mining"
            internal["replacement_source_hidden"] = "v7_asset_gap_audit_replacement_mining"
            internal["replacement_for_family_bucket_hidden"] = family_bucket
            internal["row_gap_decision_hidden"] = "replacement_candidate"
            internal["row_gap_reason_hidden"] = "mined to replace weak endpoint evidence row from v7 gap audit"
            internal["normalized_evidence_status_hidden"] = internal["packet_status_hidden"]
            forbidden = list(internal.get("forbidden_as_labeler_visible") or [])
            for field in [
                "replacement_source_hidden",
                "replacement_for_family_bucket_hidden",
                "row_gap_decision_hidden",
                "row_gap_reason_hidden",
                "normalized_evidence_status_hidden",
            ]:
                if field not in forbidden:
                    forbidden.append(field)
            internal["forbidden_as_labeler_visible"] = forbidden
            replacements.append(internal)
            replacement_sources.append(preview)
            selected_prediction_ids.add(prediction_id)
            add_counter_row(counters, internal)
            selected_for_cell += 1
        if selected_for_cell != needed:
            deficit_fill_errors.append(
                {
                    "family_bucket": family_bucket,
                    "needed": needed,
                    "selected": selected_for_cell,
                    "available_after_filters": len(candidates_by_key.get(family_bucket, [])),
                }
            )

    combined_rows = sorted(
        ready_rows + replacements,
        key=lambda row: (
            str(row.get("predicate_family")),
            str(row.get("semantic_geometry_bucket_hidden")),
            str(row.get("blind_review_id")),
        ),
    )
    replacement_visible_rows = [mining.visible_row(row) for row in replacements]
    combined_visible_rows = ready_label_rows + replacement_visible_rows
    fieldnames = visible_fieldnames(combined_visible_rows)
    leakage_hits = visible_leakage_hits(combined_visible_rows, fieldnames)
    cap_rows = build_cap_rows(combined_rows)
    bucket_audit_rows = bucket_rows(combined_rows, replacements)

    replacement_asset_needed = [row for row in replacements if row.get("packet_status_hidden") != "ready"]
    replacement_packet_ready = [row for row in replacements if row.get("packet_status_hidden") == "ready"]
    asset_requests = [mining.asset_request_row(row) for row in replacement_asset_needed]

    combined_family_bucket_counts = Counter(family_bucket_key(row) for row in combined_rows)
    if len(replacements) != len(excluded_rows):
        validation_errors.append({"error_type": "replacement_count_mismatch", "selected": len(replacements), "excluded": len(excluded_rows)})
    if len(combined_rows) != TARGET_ROWS:
        validation_errors.append({"error_type": "combined_row_count_mismatch", "actual": len(combined_rows), "expected": TARGET_ROWS})
    for key, target in target_counts.items():
        if combined_family_bucket_counts.get(key, 0) != target:
            validation_errors.append(
                {
                    "error_type": "combined_family_bucket_count_mismatch",
                    "family_bucket": key,
                    "actual": combined_family_bucket_counts.get(key, 0),
                    "expected": target,
                }
            )
    if any(row["violates_cap"] for row in cap_rows):
        validation_errors.append({"error_type": "cap_violation", "rows": [row for row in cap_rows if row["violates_cap"]]})
    if leakage_hits:
        validation_errors.append({"error_type": "visible_label_surface_leakage", "count": len(leakage_hits)})
    validation_errors.extend(deficit_fill_errors)

    status = (
        "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_mining_ready_needs_replacement_asset_packets"
        if not validation_errors and replacement_asset_needed
        else "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_mining_ready_for_label_readiness"
        if not validation_errors
        else "h002_reliability_target_v7_object_cell_evidence_contrast_replacement_mining_errors"
    )
    next_todo = (
        "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets"
        if status.endswith("needs_replacement_asset_packets")
        else "reliability_target_v7_object_cell_evidence_contrast_label_readiness"
        if status.endswith("ready_for_label_readiness")
        else "fix_reliability_target_v7_object_cell_evidence_contrast_replacement_mining_errors"
    )
    decision = (
        "Replacement mining restored the fixed 240-row object-cell evidence-contrast queue and preserved 60 rows per family/bucket cell. "
        "Because some replacement rows still need evidence packets, label fill and posterior smoke remain blocked."
        if status.endswith("needs_replacement_asset_packets")
        else "Replacement mining restored the fixed 240-row object-cell evidence-contrast queue with packet-ready replacements. Proceed to label readiness."
        if status.endswith("ready_for_label_readiness")
        else "Replacement mining did not satisfy the fixed queue contract; inspect validation_errors.json before proceeding."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "replacement_candidates_internal": output_dir / "replacement_candidates_internal.jsonl",
        "replacement_sources_preview": output_dir / "replacement_sources_preview.jsonl",
        "replacement_packet_ready_candidates": output_dir / "replacement_packet_ready_candidates.jsonl",
        "replacement_asset_needed_candidates": output_dir / "replacement_asset_needed_candidates.jsonl",
        "replacement_asset_request_manifest": output_dir / "replacement_asset_request_manifest.jsonl",
        "combined_manifest_pre_asset_packet": output_dir / "combined_manifest_pre_asset_packet.jsonl",
        "combined_label_sheet_pre_asset_packet": output_dir / "combined_label_sheet_pre_asset_packet.tsv",
        "bucket_balance_audit": output_dir / "bucket_balance_audit.csv",
        "cap_audit": output_dir / "cap_audit.csv",
        "pool_filter_summary": output_dir / "pool_filter_summary.csv",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "validation_errors": output_dir / "validation_errors.json",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": {
            "gap_summary": rel_path(gap_dir / "summary.json"),
            "gap_ready_manifest": rel_path(gap_dir / "label_ready_partial_manifest_post_label_only.jsonl"),
            "gap_excluded_rows": rel_path(gap_dir / "excluded_rows.jsonl"),
            "candidate_selected": rel_path(candidate_dir / "selected_candidates_internal.jsonl"),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
            "packet_manifests": [rel_path(path) for path in args.packet_manifest],
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "labels_filled": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "paper_metric_evidence": False,
            "semantic_geometry_bucket_visible_to_labeler": False,
            "semantic_geometry_bucket_posterior_input_allowed": False,
            "h001_artifacts_modified": False,
        },
        "counts": {
            "ready_input_rows": len(ready_rows),
            "excluded_input_rows": len(excluded_rows),
            "replacement_deficits": deficits,
            "replacement_rows_selected": len(replacements),
            "replacement_packet_ready_rows": len(replacement_packet_ready),
            "replacement_asset_needed_rows": len(replacement_asset_needed),
            "combined_rows": len(combined_rows),
            "combined_family_counts": dict(sorted(Counter(row.get("predicate_family") for row in combined_rows).items())),
            "combined_bucket_counts": dict(sorted(Counter(row.get("semantic_geometry_bucket_hidden") for row in combined_rows).items())),
            "combined_family_bucket_counts": dict(sorted(combined_family_bucket_counts.items())),
            "replacement_family_bucket_counts": dict(sorted(Counter(family_bucket_key(row) for row in replacements).items())),
            "source_primary_rows": len(source_rows),
            "candidate_pool_after_filters": {key: len(value) for key, value in sorted(candidates_by_key.items())},
            "replacement_structural_pair_rows": sum(1 for row in replacements if row.get("structural_pair_hidden")),
            "replacement_hard_room_surface_pair_rows": sum(1 for row in replacements if row.get("hard_room_surface_pair_hidden")),
        },
        "validation": {
            "visible_leakage_hits": len(leakage_hits),
            "cap_violations": sum(1 for row in cap_rows if row["violates_cap"]),
            "deficit_fill_errors": len(deficit_fill_errors),
            "validation_error_count": len(validation_errors),
        },
        "source_counts": {
            key: dict(value) if isinstance(value, Counter) else value
            for key, value in source_counts.items()
        },
        "pool_filter_summary": dict(sorted(rejected_pool_reasons.items())),
        "target_family_bucket_counts": target_counts,
        "replacement_filter_policy": {
            "generic_endpoint_labels_excluded": sorted(GENERIC_ENDPOINT_LABELS),
            "hard_room_surface_pairs_excluded": True,
            "non_hard_structural_context_allowed": True,
            "non_hard_structural_context_reason": "relative_vertical B2 has only three non-generic/non-structural strict-mixed replacement candidates after excluding the original queue; controlled non-hard structural context is less risky than generic endpoints or floor/wall/ceiling pairs.",
        },
        "validation_error_count": len(validation_errors),
        "label_fill_allowed": False,
        "posterior_allowed": False,
    }

    write_jsonl(output_paths["replacement_candidates_internal"], replacements)
    write_jsonl(output_paths["replacement_sources_preview"], replacement_sources)
    write_jsonl(output_paths["replacement_packet_ready_candidates"], replacement_packet_ready)
    write_jsonl(output_paths["replacement_asset_needed_candidates"], replacement_asset_needed)
    write_jsonl(output_paths["replacement_asset_request_manifest"], asset_requests)
    write_jsonl(output_paths["combined_manifest_pre_asset_packet"], combined_rows)
    write_tsv(output_paths["combined_label_sheet_pre_asset_packet"], combined_visible_rows, fieldnames)
    write_csv(output_paths["bucket_balance_audit"], bucket_audit_rows)
    write_csv(output_paths["cap_audit"], cap_rows)
    write_csv(
        output_paths["pool_filter_summary"],
        [{"filter_reason": key, "rows": value} for key, value in sorted(rejected_pool_reasons.items())],
    )
    write_jsonl(output_paths["visible_leakage_hits"], leakage_hits)
    write_json(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        f"status={summary['status']} "
        f"ready_input={summary['counts']['ready_input_rows']} "
        f"excluded_input={summary['counts']['excluded_input_rows']} "
        f"replacement_selected={summary['counts']['replacement_rows_selected']} "
        f"combined_rows={summary['counts']['combined_rows']} "
        f"replacement_asset_needed={summary['counts']['replacement_asset_needed_rows']} "
        f"errors={summary['validation_error_count']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
