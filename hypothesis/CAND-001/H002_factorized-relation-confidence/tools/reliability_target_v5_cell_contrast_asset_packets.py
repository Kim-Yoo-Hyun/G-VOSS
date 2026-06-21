#!/usr/bin/env python3
"""Generate packets for H002 reliability target v5 cell-contrast rows."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_asset_packets as base_packets
import reliability_target_v5_cell_contrast_candidate_mining as mining


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

CANDIDATE_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_candidate_mining"
DEFAULT_CANDIDATE_SUMMARY = CANDIDATE_DIR / "summary.json"
DEFAULT_SELECTED_CANDIDATES = CANDIDATE_DIR / "selected_candidates_internal.jsonl"
DEFAULT_PREVIOUS_MANIFEST = CANDIDATE_DIR / "cell_contrast_manifest_post_label_only.jsonl"
DEFAULT_ASSET_REQUESTS = CANDIDATE_DIR / "asset_request_plan.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_asset_packets"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"

SCHEMA_VERSION = "h002_reliability_target_v5_cell_contrast_asset_packets_v1"
REVIEW_SCOPE = "h002_reliability_v5_relation_packeted"
PACKET_TEXT_FORBIDDEN_TOKENS = [
    "anchor_category",
    "candidate_proxy",
    "cell_contrast",
    "contrast_role",
    "endpoint_flag_pattern",
    "geometry_status",
    "informative_score",
    "label_geometry_bucket",
    "label_match",
    "machine_hint",
    "matched_predicates",
    "p_geom",
    "queue_kind",
    "rank_band",
    "reason_codes",
    "semantic_rank",
    "semantic_score",
    "source_queue",
    "stratum",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--selected-candidates", type=Path, default=DEFAULT_SELECTED_CANDIDATES)
    parser.add_argument("--previous-manifest", type=Path, default=DEFAULT_PREVIOUS_MANIFEST)
    parser.add_argument("--asset-requests", type=Path, default=DEFAULT_ASSET_REQUESTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--images-per-object", type=int, default=4)
    parser.add_argument("--thumb-size", type=int, default=320)
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
        seen = set()
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


def packet_paths_from_generated(packet_row: dict[str, Any]) -> dict[str, str]:
    return {
        "multiview_packet": str(packet_row.get("multiview_packet") or ""),
        "pointcloud_or_mesh_packet": str(packet_row.get("pointcloud_or_mesh_packet") or ""),
        "contact_or_context_sheet": str(packet_row.get("contact_or_context_sheet") or ""),
    }


def needs_asset_packet(row: dict[str, Any]) -> bool:
    if row.get("packet_ready") is True and row.get("packet_status") == "ready":
        return False
    return any(
        not row.get(field)
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]
    )


def asset_generation_row(seed: dict[str, Any]) -> dict[str, Any]:
    blind_id = mining.blind_review_id(seed)
    return {
        "blind_review_id": blind_id,
        "asset_request_id": blind_id,
        "scan_id": seed.get("scan_id"),
        "subgraph_id": seed.get("scene_context_id") or seed.get("subgraph_id"),
        "subject_id": seed.get("subject_id"),
        "subject_label": seed.get("subject_label"),
        "predicate_label": seed.get("predicate_label"),
        "predicate_family": seed.get("predicate_family"),
        "object_id": seed.get("object_id"),
        "object_label": seed.get("object_label"),
    }


def update_seed_with_packet(seed: dict[str, Any], packet: dict[str, Any] | None) -> dict[str, Any]:
    updated = dict(seed)
    blind_id = mining.blind_review_id(seed)
    if packet is not None:
        updated.update(packet_paths_from_generated(packet))
        updated["packet_ready"] = packet.get("packet_status") == "ready"
        updated["packet_status"] = packet.get("packet_status", "")
        updated["asset_packet_source_hidden"] = "generated_v5_cell_contrast_asset_packet"
    elif updated.get("packet_ready") is True and updated.get("packet_status") == "ready":
        updated["asset_packet_source_hidden"] = "existing_independent_asset_packet"
    else:
        updated["packet_ready"] = False
        updated["packet_status"] = updated.get("packet_status") or "asset_needed"
        updated["asset_packet_source_hidden"] = "missing_v5_cell_contrast_asset_packet"
    updated["generated_blind_review_id_hidden"] = blind_id
    return updated


def label_facing_packet_path(seed: dict[str, Any], field: str, output_dir: Path) -> str:
    value = str(seed.get(field) or "")
    if not value:
        return ""
    abs_path = as_abs(Path(value))
    try:
        return str(abs_path.relative_to(output_dir))
    except ValueError:
        return rel_path(abs_path)


def full_visible_row(seed: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    row = mining.visible_row(seed)
    row["review_scope"] = REVIEW_SCOPE
    row["evidence_packet_status"] = seed.get("packet_status") or row.get("evidence_packet_status", "")
    row["multiview_packet"] = label_facing_packet_path(seed, "multiview_packet", output_dir)
    row["pointcloud_or_mesh_packet"] = label_facing_packet_path(seed, "pointcloud_or_mesh_packet", output_dir)
    row["contact_or_context_sheet"] = label_facing_packet_path(seed, "contact_or_context_sheet", output_dir)
    return row


def full_manifest_row(seed: dict[str, Any], previous_manifest_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    blind_id = mining.blind_review_id(seed)
    row = dict(previous_manifest_by_id.get(blind_id) or mining.manifest_row(seed))
    row["batch_name"] = "reliability_target_v5_cell_contrast_asset_packets"
    row["schema_version"] = "h002_reliability_target_v5_cell_contrast_asset_packet_manifest_v1"
    row["evidence_packet_status"] = seed.get("packet_status", row.get("packet_status_hidden", ""))
    row["packet_status_hidden"] = seed.get("packet_status", row.get("packet_status_hidden", ""))
    row["packet_paths"] = {
        "multiview_packet": seed.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": seed.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": seed.get("contact_or_context_sheet", ""),
    }
    row["asset_packet_source_hidden"] = seed.get("asset_packet_source_hidden", "")
    row["generated_blind_review_id_hidden"] = seed.get("generated_blind_review_id_hidden", "")
    forbidden = list(row.get("forbidden_as_labeler_visible") or [])
    for field in ["asset_packet_source_hidden", "generated_blind_review_id_hidden"]:
        if field not in forbidden:
            forbidden.append(field)
    row["forbidden_as_labeler_visible"] = forbidden
    return row


def resolve_label_packet_path(value: str, output_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    repo_candidate = as_abs(path)
    if repo_candidate.exists():
        return repo_candidate
    return output_dir / path


def packet_path_errors(label_rows: list[dict[str, Any]], output_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(label_rows, start=2):
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(field) or "")
            if not value:
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": row.get("blind_review_id"),
                        "field": field,
                        "error_type": "empty_packet_path",
                    }
                )
            elif not resolve_label_packet_path(value, output_dir).exists():
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": row.get("blind_review_id"),
                        "field": field,
                        "value": value,
                        "error_type": "packet_path_missing_on_disk",
                    }
                )
    return errors


def visible_value_leakage_hits(label_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row_number, row in enumerate(label_rows, start=2):
        for field, value in row.items():
            if field in {"multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"}:
                continue
            lower = str(value).lower()
            for token in mining.FORBIDDEN_VISIBLE_VALUE_TOKENS:
                if token in lower:
                    hits.append(
                        {
                            "row_number": row_number,
                            "blind_review_id": row.get("blind_review_id"),
                            "field": field,
                            "forbidden_token": token,
                        }
                    )
                    break
    return hits


def packet_text_leakage_hits(packet_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for packet in packet_rows:
        for field in ["multiview_packet", "pointcloud_or_mesh_packet"]:
            value = str(packet.get(field) or "")
            if not value:
                continue
            path = as_abs(Path(value))
            if not path.exists() or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8").lower()
            for token in PACKET_TEXT_FORBIDDEN_TOKENS:
                if token in text:
                    hits.append({"surface": rel_path(path), "field": field, "forbidden_token": token})
                    break
    return hits


def pair_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_pair[str(row.get("cell_contrast_pair_id"))].append(row)
    output: list[dict[str, Any]] = []
    for pair_id in sorted(by_pair):
        group = by_pair[pair_id]
        roles = Counter(str(row.get("cell_contrast_role_hidden")) for row in group)
        statuses = Counter(str(row.get("packet_status")) for row in group)
        sources = Counter(str(row.get("asset_packet_source_hidden")) for row in group)
        output.append(
            {
                "cell_contrast_pair_id_hidden": pair_id,
                "rows": len(group),
                "positive_proxy_rows": roles.get("positive_proxy", 0),
                "negative_proxy_rows": roles.get("negative_proxy", 0),
                "ready_rows": statuses.get("ready", 0),
                "partial_rows": statuses.get("partial", 0),
                "missing_rows": statuses.get("missing", 0),
                "generated_rows": sources.get("generated_v5_cell_contrast_asset_packet", 0),
                "existing_rows": sources.get("existing_independent_asset_packet", 0),
                "predicate_label": group[0].get("predicate_label", ""),
                "predicate_family": group[0].get("predicate_family", ""),
                "cell_contrast_level_hidden": group[0].get("cell_contrast_level_hidden", ""),
            }
        )
    return output


def cell_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_cell[str(row.get("cell_contrast_key_hidden"))].append(row)
    output: list[dict[str, Any]] = []
    for cell_key in sorted(by_cell):
        group = by_cell[cell_key]
        statuses = Counter(str(row.get("packet_status")) for row in group)
        sources = Counter(str(row.get("asset_packet_source_hidden")) for row in group)
        roles = Counter(str(row.get("cell_contrast_role_hidden")) for row in group)
        output.append(
            {
                "cell_contrast_key_hidden": cell_key,
                "rows": len(group),
                "pairs": len({row.get("cell_contrast_pair_id") for row in group}),
                "positive_proxy_rows": roles.get("positive_proxy", 0),
                "negative_proxy_rows": roles.get("negative_proxy", 0),
                "ready_rows": statuses.get("ready", 0),
                "partial_rows": statuses.get("partial", 0),
                "missing_rows": statuses.get("missing", 0),
                "generated_rows": sources.get("generated_v5_cell_contrast_asset_packet", 0),
                "existing_rows": sources.get("existing_independent_asset_packet", 0),
                "support_contact_rows": sum(1 for row in group if row.get("predicate_family") == "support_contact"),
                "relative_vertical_rows": sum(1 for row in group if row.get("predicate_family") == "relative_vertical"),
            }
        )
    return output


def validate_inputs(
    candidate_summary: dict[str, Any],
    seeds: list[dict[str, Any]],
    previous_manifest: list[dict[str, Any]],
    asset_requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if candidate_summary.get("next_todo") != "reliability_target_v5_cell_contrast_asset_packets":
        errors.append({"error_type": "unexpected_candidate_next_todo", "value": candidate_summary.get("next_todo")})
    if candidate_summary.get("selected_matching_level") != "strict_predicate_subject_object_endpoint":
        errors.append(
            {
                "error_type": "unexpected_selected_matching_level",
                "value": candidate_summary.get("selected_matching_level"),
            }
        )
    boundary = candidate_summary.get("boundary") or {}
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": f"candidate_boundary_{key}_not_false", "value": boundary.get(key)})
    counts = candidate_summary.get("counts", {})
    if len(seeds) != counts.get("label_rows"):
        errors.append({"error_type": "selected_seed_count_mismatch", "seed_rows": len(seeds), "summary_rows": counts.get("label_rows")})
    if len(previous_manifest) != len(seeds):
        errors.append({"error_type": "previous_manifest_count_mismatch", "manifest_rows": len(previous_manifest), "seed_rows": len(seeds)})
    if len(asset_requests) != counts.get("asset_needed_rows"):
        errors.append(
            {
                "error_type": "asset_request_count_mismatch",
                "asset_request_rows": len(asset_requests),
                "summary_asset_needed_rows": counts.get("asset_needed_rows"),
            }
        )
    needed_ids = {mining.blind_review_id(row) for row in seeds if needs_asset_packet(row)}
    request_ids = {str(row.get("blind_review_id")) for row in asset_requests}
    if needed_ids != request_ids:
        errors.append(
            {
                "error_type": "asset_request_id_set_mismatch",
                "needed_only": sorted(needed_ids - request_ids)[:10],
                "request_only": sorted(request_ids - needed_ids)[:10],
                "needed_count": len(needed_ids),
                "request_count": len(request_ids),
            }
        )
    ids = [mining.blind_review_id(row) for row in seeds]
    for blind_id, count in Counter(ids).items():
        if count > 1:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id, "count": count})
    pair_roles: dict[str, Counter[str]] = defaultdict(Counter)
    for row in seeds:
        pair_roles[str(row.get("cell_contrast_pair_id"))][str(row.get("cell_contrast_role_hidden"))] += 1
    for pair_id, roles in sorted(pair_roles.items()):
        if roles.get("positive_proxy", 0) != 1 or roles.get("negative_proxy", 0) != 1:
            errors.append({"error_type": "invalid_pair_role_counts", "pair_id": pair_id, "roles": dict(roles)})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Reliability Target V5 Cell Contrast Asset Packets",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage artifact.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- Multi-view and mesh packets are audit/label evidence only, not posterior input.",
        "- Cell contrast role, rank, semantic score, geometry status, and proxy fields remain hidden.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| input selected rows | {counts['input_selected_rows']} |",
        f"| asset-needed input rows | {counts['asset_needed_input_rows']} |",
        f"| generated packet rows | {counts['generated_packet_rows']} |",
        f"| generated non-ready rows | {counts['generated_non_ready_rows']} |",
        f"| full label sheet rows | {counts['full_label_sheet_rows']} |",
        f"| ready label rows | {counts['ready_label_rows']} |",
        f"| packet path errors | {counts['packet_path_errors']} |",
        f"| label-surface leakage hits | {counts['label_surface_leakage_hits']} |",
        f"| visible value leakage hits | {counts['visible_value_leakage_hits']} |",
        f"| validation errors | {counts['validation_errors']} |",
        "",
        "## Packet Sources",
        "",
        "| Source | Rows |",
        "| --- | ---: |",
    ]
    for key, value in summary["packet_source_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Family Counts", "", "| Family | Rows |", "| --- | ---: |"])
    for key, value in counts["by_family"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Decision",
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
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    candidate_summary = read_json(args.candidate_summary)
    selected_seeds = read_jsonl(args.selected_candidates)
    previous_manifest = read_jsonl(args.previous_manifest)
    asset_requests = read_jsonl(args.asset_requests)
    validation_errors = validate_inputs(candidate_summary, selected_seeds, previous_manifest, asset_requests)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    asset_needed_seeds = [row for row in selected_seeds if needs_asset_packet(row)]
    packet_args = argparse.Namespace(
        scan_root=as_abs(args.scan_root),
        images_per_object=args.images_per_object,
        thumb_size=args.thumb_size,
    )
    generation_rows = [asset_generation_row(row) for row in asset_needed_seeds]
    generated_packets = [base_packets.generate_packet(row, packet_args, output_dir) for row in generation_rows]
    generated_by_id = {str(row["blind_review_id"]): row for row in generated_packets}

    previous_manifest_by_id = {str(row.get("blind_review_id")): row for row in previous_manifest}
    updated_seeds = [
        update_seed_with_packet(row, generated_by_id.get(mining.blind_review_id(row)))
        for row in selected_seeds
    ]
    label_rows = [full_visible_row(row, output_dir) for row in updated_seeds]
    manifest_rows = [full_manifest_row(row, previous_manifest_by_id) for row in updated_seeds]
    generated_manifest_rows = [
        row for row in manifest_rows if row.get("asset_packet_source_hidden") == "generated_v5_cell_contrast_asset_packet"
    ]

    full_label_sheet = output_dir / "cell_contrast_full_label_sheet.tsv"
    generated_non_ready = [row for row in generated_packets if row.get("packet_status") != "ready"]
    path_errors = packet_path_errors(label_rows, output_dir)
    field_leakage_hits = mining.leakage_hits(mining.VISIBLE_FIELDS)
    value_leakage_hits = visible_value_leakage_hits(label_rows)
    packet_text_hits = packet_text_leakage_hits(generated_packets)
    leakage_hits = field_leakage_hits + value_leakage_hits + packet_text_hits
    leakage = {
        "status": "pass" if not leakage_hits else "fail",
        "forbidden_packet_text_tokens": PACKET_TEXT_FORBIDDEN_TOKENS,
        "field_leakage_hits": len(field_leakage_hits),
        "visible_value_leakage_hits": len(value_leakage_hits),
        "packet_text_leakage_hits": len(packet_text_hits),
        "hits": leakage_hits,
        "output_dir": rel_path(output_dir),
    }

    status_counts = Counter(str(row.get("evidence_packet_status")) for row in label_rows)
    generated_status_counts = Counter(str(row.get("packet_status")) for row in generated_packets)
    family_counts = Counter(str(row.get("predicate_family")) for row in updated_seeds)
    packet_source_counts = Counter(str(row.get("asset_packet_source_hidden")) for row in updated_seeds)
    pair_rows = pair_summary_rows(updated_seeds)
    cell_rows = cell_summary_rows(updated_seeds)

    all_ready = status_counts.get("ready", 0) == len(label_rows)
    status = (
        "h002_reliability_target_v5_cell_contrast_asset_packets_ready"
        if all_ready and not generated_non_ready and not path_errors and not leakage_hits and not validation_errors
        else "h002_reliability_target_v5_cell_contrast_asset_packets_partial"
        if status_counts.get("ready", 0) > 0 and not leakage_hits
        else "h002_reliability_target_v5_cell_contrast_asset_packets_blocked"
    )
    next_todo = (
        "reliability_target_v5_cell_contrast_label_readiness"
        if status == "h002_reliability_target_v5_cell_contrast_asset_packets_ready"
        else "reliability_target_v5_cell_contrast_asset_packet_gap_audit"
        if status == "h002_reliability_target_v5_cell_contrast_asset_packets_partial"
        else "fix_reliability_target_v5_cell_contrast_asset_packets"
    )
    decision = (
        "The full 80-row v5 cell-contrast sheet is packet-complete and can proceed to label-readiness checks."
        if status == "h002_reliability_target_v5_cell_contrast_asset_packets_ready"
        else "V5 cell-contrast packets are partial. Inspect generated non-ready rows or missing paths before label fill."
        if status == "h002_reliability_target_v5_cell_contrast_asset_packets_partial"
        else "V5 cell-contrast packet generation is blocked by validation, leakage, or path errors."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "full_label_sheet": full_label_sheet,
        "full_manifest_post_label_only": output_dir / "cell_contrast_full_manifest_post_label_only.jsonl",
        "generated_packet_manifest": output_dir / "generated_packet_manifest.jsonl",
        "generated_non_ready_packet_rows": output_dir / "generated_non_ready_packet_rows.jsonl",
        "asset_needed_manifest_with_packets_post_label_only": output_dir / "asset_needed_manifest_with_packets_post_label_only.jsonl",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "label_surface_leakage_hits": output_dir / "label_surface_leakage_hits.jsonl",
        "visible_value_leakage_hits": output_dir / "visible_value_leakage_hits.jsonl",
        "label_surface_leakage_audit": output_dir / "label_surface_leakage_audit.json",
        "input_validation_errors": output_dir / "input_validation_errors.jsonl",
        "pair_summary": output_dir / "pair_summary.csv",
        "cell_summary": output_dir / "cell_summary.csv",
        "previous_manifest_snapshot": output_dir / "previous_candidate_manifest_snapshot.jsonl",
        "packets_dir": output_dir / "packets",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": {
            "candidate_summary": rel_path(args.candidate_summary),
            "selected_candidates": rel_path(args.selected_candidates),
            "previous_manifest": rel_path(args.previous_manifest),
            "asset_requests": rel_path(args.asset_requests),
            "scan_root": rel_path(args.scan_root),
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
            "cell_contrast_roles_visible_to_labeler": False,
        },
        "source_candidate_status": candidate_summary.get("status"),
        "counts": {
            "input_selected_rows": len(selected_seeds),
            "previous_manifest_rows": len(previous_manifest),
            "asset_needed_input_rows": len(asset_needed_seeds),
            "generated_packet_rows": len(generated_packets),
            "generated_non_ready_rows": len(generated_non_ready),
            "full_label_sheet_rows": len(label_rows),
            "ready_label_rows": status_counts.get("ready", 0),
            "packet_path_errors": len(path_errors),
            "label_surface_leakage_hits": len(leakage_hits),
            "visible_value_leakage_hits": len(value_leakage_hits),
            "validation_errors": len(validation_errors),
            "by_family": dict(sorted(family_counts.items())),
        },
        "packet_status_counts": dict(sorted(status_counts.items())),
        "generated_packet_status_counts": dict(sorted(generated_status_counts.items())),
        "packet_source_counts": dict(sorted(packet_source_counts.items())),
        "pair_count": len(pair_rows),
        "cell_count": len(cell_rows),
        "label_surface_leakage_audit": leakage,
        "validation_errors": validation_errors,
    }

    write_tsv(output_paths["full_label_sheet"], label_rows, mining.VISIBLE_FIELDS)
    write_jsonl(output_paths["full_manifest_post_label_only"], manifest_rows)
    write_jsonl(output_paths["generated_packet_manifest"], generated_packets)
    write_jsonl(output_paths["generated_non_ready_packet_rows"], generated_non_ready)
    write_jsonl(output_paths["asset_needed_manifest_with_packets_post_label_only"], generated_manifest_rows)
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_jsonl(output_paths["label_surface_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["visible_value_leakage_hits"], value_leakage_hits)
    write_json(output_paths["label_surface_leakage_audit"], leakage)
    write_jsonl(output_paths["input_validation_errors"], validation_errors)
    write_csv(output_paths["pair_summary"], pair_rows)
    write_csv(output_paths["cell_summary"], cell_rows)
    write_jsonl(output_paths["previous_manifest_snapshot"], previous_manifest)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} "
        f"generated={summary['counts']['generated_packet_rows']} "
        f"non_ready={summary['counts']['generated_non_ready_rows']} "
        f"full_sheet={summary['counts']['full_label_sheet_rows']} "
        f"ready={summary['counts']['ready_label_rows']} "
        f"path_errors={summary['counts']['packet_path_errors']} "
        f"leakage={summary['label_surface_leakage_audit']['status']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} "
        f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
