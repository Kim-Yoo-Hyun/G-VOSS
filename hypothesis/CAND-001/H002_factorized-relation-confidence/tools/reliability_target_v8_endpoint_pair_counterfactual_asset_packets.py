#!/usr/bin/env python3
"""Generate packets for H002 v8 endpoint-pair counterfactual candidates."""

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
import reliability_target_v8_endpoint_pair_counterfactual_candidate_mining as mining


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

CANDIDATE_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_codex_proxy_user_requested"
DEFAULT_CANDIDATE_SUMMARY = CANDIDATE_DIR / "summary.json"
DEFAULT_SELECTED_CANDIDATES = CANDIDATE_DIR / "selected_candidates_internal.jsonl"
DEFAULT_ASSET_REQUESTS = CANDIDATE_DIR / "asset_request_manifest.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_asset_packets_codex_proxy_user_requested"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"

SCHEMA_VERSION = "h002_reliability_target_v8_endpoint_pair_counterfactual_asset_packets_v1"
REVIEW_SCOPE = "h002_reliability_v8_endpoint_pair_counterfactual_packeted_review"
GENERATED_PACKET_SOURCE = "generated_v8_endpoint_pair_counterfactual_asset_packet"
EXISTING_PACKET_SOURCE = "existing_prior_asset_packet"
MISSING_PACKET_SOURCE = "missing_v8_endpoint_pair_counterfactual_asset_packet"

PACKET_TEXT_FORBIDDEN_TOKENS = [
    "candidate_bucket",
    "semantic_score",
    "semantic_rank",
    "p_geom",
    "geometry_status",
    "rank_band",
    "source_queue",
    "strict_group",
    "endpoint_pair_key",
    "v8_group",
    "object_family_cell",
    "subject_object_family_cell",
    "label_match",
    "h001_verification",
    "expected_target",
    "machine_hint",
    "reason_codes",
    "b2_semantic",
    "b3_semantic",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--selected-candidates", type=Path, default=DEFAULT_SELECTED_CANDIDATES)
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


def packet_paths_from_generated(packet_row: dict[str, Any]) -> dict[str, str]:
    return {
        "multiview_packet": str(packet_row.get("multiview_packet") or ""),
        "pointcloud_or_mesh_packet": str(packet_row.get("pointcloud_or_mesh_packet") or ""),
        "contact_or_context_sheet": str(packet_row.get("contact_or_context_sheet") or ""),
    }


def packet_status(row: dict[str, Any]) -> str:
    return str(row.get("packet_status_hidden") or row.get("packet_status") or "")


def needs_asset_packet(row: dict[str, Any]) -> bool:
    if packet_status(row) == "ready" and all(row.get(field) for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]):
        return False
    return True


def asset_generation_row(seed: dict[str, Any]) -> dict[str, Any]:
    blind_id = str(seed["blind_review_id"])
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
    blind_id = str(seed["blind_review_id"])
    if packet is not None:
        updated.update(packet_paths_from_generated(packet))
        updated["packet_status_hidden"] = packet.get("packet_status", "")
        updated["asset_packet_source_hidden"] = GENERATED_PACKET_SOURCE
    elif packet_status(updated) == "ready":
        updated["asset_packet_source_hidden"] = EXISTING_PACKET_SOURCE
    else:
        updated["packet_status_hidden"] = packet_status(updated) or "asset_needed"
        updated["asset_packet_source_hidden"] = MISSING_PACKET_SOURCE
    updated["generated_blind_review_id_hidden"] = blind_id
    updated["label_fill_allowed"] = False
    updated["posterior_input_allowed"] = False
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
    row["evidence_packet_status"] = packet_status(seed)
    if packet_status(seed) == "ready":
        row["multiview_packet"] = label_facing_packet_path(seed, "multiview_packet", output_dir)
        row["pointcloud_or_mesh_packet"] = label_facing_packet_path(seed, "pointcloud_or_mesh_packet", output_dir)
        row["contact_or_context_sheet"] = label_facing_packet_path(seed, "contact_or_context_sheet", output_dir)
    else:
        row["multiview_packet"] = label_facing_packet_path(seed, "multiview_packet", output_dir)
        row["pointcloud_or_mesh_packet"] = label_facing_packet_path(seed, "pointcloud_or_mesh_packet", output_dir)
        row["contact_or_context_sheet"] = label_facing_packet_path(seed, "contact_or_context_sheet", output_dir)
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
        if row.get("evidence_packet_status") != "ready":
            continue
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(field) or "")
            if not value:
                errors.append({"row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "error_type": "empty_packet_path"})
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
                    hits.append({"row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "forbidden_token": token})
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


def bucket_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_cell[(str(row.get("predicate_family")), str(row.get("semantic_geometry_bucket_hidden")))].append(row)
    output: list[dict[str, Any]] = []
    for (family, bucket), group in sorted(by_cell.items()):
        statuses = Counter(packet_status(row) for row in group)
        sources = Counter(str(row.get("asset_packet_source_hidden")) for row in group)
        output.append(
            {
                "predicate_family": family,
                "semantic_geometry_bucket_hidden": bucket,
                "rows": len(group),
                "ready_rows": statuses.get("ready", 0),
                "partial_rows": statuses.get("partial", 0),
                "missing_rows": statuses.get("missing", 0),
                "asset_needed_rows": statuses.get("asset_needed", 0),
                "generated_rows": sources.get(GENERATED_PACKET_SOURCE, 0),
                "existing_rows": sources.get(EXISTING_PACKET_SOURCE, 0),
                "missing_source_rows": sources.get(MISSING_PACKET_SOURCE, 0),
            }
        )
    return output


def status_audit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if packet_status(row) == "ready":
            continue
        output.append(
            {
                "blind_review_id": row.get("blind_review_id"),
                "predicate_family": row.get("predicate_family"),
                "predicate_label": row.get("predicate_label"),
                "scan_id": row.get("scan_id"),
                "scene_context_id": row.get("scene_context_id"),
                "subject_id": row.get("subject_id"),
                "subject_label": row.get("subject_label"),
                "object_id": row.get("object_id"),
                "object_label": row.get("object_label"),
                "semantic_geometry_bucket_hidden": row.get("semantic_geometry_bucket_hidden"),
                "packet_status": packet_status(row),
                "asset_packet_source_hidden": row.get("asset_packet_source_hidden"),
                "multiview_packet_present": bool(row.get("multiview_packet")),
                "pointcloud_or_mesh_packet_present": bool(row.get("pointcloud_or_mesh_packet")),
                "contact_or_context_sheet_present": bool(row.get("contact_or_context_sheet")),
            }
        )
    return output


def validate_inputs(
    candidate_summary: dict[str, Any],
    seeds: list[dict[str, Any]],
    asset_requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if candidate_summary.get("status") != "h002_reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_ready_needs_asset_packets":
        errors.append({"error_type": "unexpected_candidate_status", "value": candidate_summary.get("status")})
    if candidate_summary.get("next_todo") != "reliability_target_v8_endpoint_pair_counterfactual_asset_packets":
        errors.append({"error_type": "unexpected_candidate_next_todo", "value": candidate_summary.get("next_todo")})
    for field in [
        "posterior_allowed",
        "label_fill_allowed",
        "validation_used",
        "test_used",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "paper_metric_evidence",
    ]:
        if candidate_summary.get(field) is not False:
            errors.append({"error_type": "candidate_boundary_not_false", "field": field, "value": candidate_summary.get(field)})
    counts = candidate_summary.get("counts", {})
    if len(seeds) != counts.get("selected_rows"):
        errors.append({"error_type": "selected_seed_count_mismatch", "seed_rows": len(seeds), "summary_rows": counts.get("selected_rows")})
    if len(asset_requests) != counts.get("asset_needed_rows"):
        errors.append({"error_type": "asset_request_count_mismatch", "asset_request_rows": len(asset_requests), "summary_asset_needed_rows": counts.get("asset_needed_rows")})
    needed_ids = {str(row["blind_review_id"]) for row in seeds if needs_asset_packet(row)}
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
    for blind_id, count in Counter(str(row["blind_review_id"]) for row in seeds).items():
        if count > 1:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id, "count": count})
    selected_cells = Counter((str(row.get("predicate_family")), str(row.get("semantic_geometry_bucket_hidden"))) for row in seeds)
    for family in mining.PRIMARY_FAMILIES:
        for bucket in mining.BUCKETS:
            if selected_cells[(family, bucket)] != mining.TARGET_PER_FAMILY_BUCKET:
                errors.append(
                    {
                        "error_type": "unexpected_family_bucket_count",
                        "predicate_family": family,
                        "semantic_geometry_bucket_hidden": bucket,
                        "count": selected_cells[(family, bucket)],
                        "expected": mining.TARGET_PER_FAMILY_BUCKET,
                    }
                )
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V8 Endpoint-Pair Counterfactual Asset Packets",
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
        "- Semantic score/rank, geometry score/status, queue kind, endpoint-pair key, v8 group key, and object-cell metadata remain hidden.",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next = {summary['next_todo']}",
        f"validation_errors = {counts['validation_errors']}",
        "```",
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
        f"| label-ready sheet rows | {counts['label_ready_sheet_rows']} |",
        f"| packet path errors | {counts['packet_path_errors']} |",
        f"| label-surface leakage hits | {counts['label_surface_leakage_hits']} |",
        f"| visible value leakage hits | {counts['visible_value_leakage_hits']} |",
        f"| packet text leakage hits | {counts['packet_text_leakage_hits']} |",
        f"| validation errors | {counts['validation_errors']} |",
        "",
        "## Packet Sources",
        "",
        "| Source | Rows |",
        "| --- | ---: |",
    ]
    for key, value in summary["packet_source_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Status Counts", "", "| Status | Rows |", "| --- | ---: |"])
    for key, value in summary["packet_status_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Decision", "", summary["decision"], "", "## Next TODO", "", "```text", summary["next_todo"], "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    candidate_summary = read_json(args.candidate_summary)
    selected_seeds = read_jsonl(args.selected_candidates)
    asset_requests = read_jsonl(args.asset_requests)
    validation_errors = validate_inputs(candidate_summary, selected_seeds, asset_requests)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    asset_needed_seeds = [row for row in selected_seeds if needs_asset_packet(row)]
    packet_args = argparse.Namespace(scan_root=as_abs(args.scan_root), images_per_object=args.images_per_object, thumb_size=args.thumb_size)
    generation_rows = [asset_generation_row(row) for row in asset_needed_seeds]
    generated_packets = [base_packets.generate_packet(row, packet_args, output_dir) for row in generation_rows]
    generated_by_id = {str(row["blind_review_id"]): row for row in generated_packets}

    updated_seeds = [update_seed_with_packet(row, generated_by_id.get(str(row["blind_review_id"]))) for row in selected_seeds]
    label_rows = [full_visible_row(row, output_dir) for row in updated_seeds]
    label_ready_rows = [row for row in label_rows if row.get("evidence_packet_status") == "ready"]
    label_ready_manifest_rows = [row for row in updated_seeds if packet_status(row) == "ready"]
    generated_manifest_rows = [row for row in updated_seeds if row.get("asset_packet_source_hidden") == GENERATED_PACKET_SOURCE]
    generated_non_ready = [row for row in generated_packets if row.get("packet_status") != "ready"]

    path_errors = packet_path_errors(label_rows, output_dir)
    field_leakage_hits = mining.field_leakage_hits(mining.VISIBLE_FIELDS)
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
    bucket_counts = Counter(str(row.get("semantic_geometry_bucket_hidden")) for row in updated_seeds)
    family_bucket_counts = Counter(f"{row.get('predicate_family')}|{row.get('semantic_geometry_bucket_hidden')}" for row in updated_seeds)
    packet_source_counts = Counter(str(row.get("asset_packet_source_hidden")) for row in updated_seeds)
    bucket_rows = bucket_summary_rows(updated_seeds)
    gap_rows = status_audit_rows(updated_seeds)

    all_ready = status_counts.get("ready", 0) == len(label_rows)
    has_errors = bool(validation_errors or path_errors or leakage_hits)
    if all_ready and not generated_non_ready and not has_errors:
        status = "h002_reliability_target_v8_endpoint_pair_counterfactual_asset_packets_ready_for_label_readiness"
        next_todo = "reliability_target_v8_endpoint_pair_counterfactual_label_readiness"
        decision = "The full 240-row v8 endpoint-pair counterfactual sheet is packet-complete and can proceed to label-readiness checks."
    elif status_counts.get("ready", 0) > 0 and not validation_errors and not leakage_hits:
        status = "h002_reliability_target_v8_endpoint_pair_counterfactual_asset_packets_partial_needs_gap_audit"
        next_todo = "reliability_target_v8_endpoint_pair_counterfactual_asset_packet_gap_audit"
        decision = "V8 endpoint-pair counterfactual packets are partial. Inspect non-ready rows or missing paths before label fill."
    else:
        status = "h002_reliability_target_v8_endpoint_pair_counterfactual_asset_packets_blocked"
        next_todo = "fix_reliability_target_v8_endpoint_pair_counterfactual_asset_packets"
        decision = "V8 endpoint-pair counterfactual packet generation is blocked by validation, leakage, or path errors."

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "full_label_sheet": output_dir / "v8_endpoint_pair_counterfactual_full_label_sheet.tsv",
        "label_ready_sheet": output_dir / "v8_endpoint_pair_counterfactual_label_ready_sheet.tsv",
        "full_manifest_post_label_only": output_dir / "v8_endpoint_pair_counterfactual_full_manifest_post_label_only.jsonl",
        "label_ready_manifest_post_label_only": output_dir / "v8_endpoint_pair_counterfactual_label_ready_manifest_post_label_only.jsonl",
        "generated_packet_manifest": output_dir / "generated_packet_manifest.jsonl",
        "generated_non_ready_packet_rows": output_dir / "generated_non_ready_packet_rows.jsonl",
        "asset_needed_manifest_with_packets_post_label_only": output_dir / "asset_needed_manifest_with_packets_post_label_only.jsonl",
        "packet_gap_audit": output_dir / "packet_gap_audit.csv",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "label_surface_leakage_hits": output_dir / "label_surface_leakage_hits.jsonl",
        "visible_value_leakage_hits": output_dir / "visible_value_leakage_hits.jsonl",
        "packet_text_leakage_hits": output_dir / "packet_text_leakage_hits.jsonl",
        "label_surface_leakage_audit": output_dir / "label_surface_leakage_audit.json",
        "input_validation_errors": output_dir / "input_validation_errors.jsonl",
        "bucket_packet_summary": output_dir / "bucket_packet_summary.csv",
        "asset_request_snapshot": output_dir / "asset_request_snapshot.jsonl",
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
            "semantic_geometry_bucket_visible_to_labeler": False,
            "semantic_geometry_bucket_posterior_input_allowed": False,
            "h001_artifacts_modified": False,
        },
        "source_candidate_status": candidate_summary.get("status"),
        "counts": {
            "input_selected_rows": len(selected_seeds),
            "asset_needed_input_rows": len(asset_needed_seeds),
            "generated_packet_rows": len(generated_packets),
            "generated_non_ready_rows": len(generated_non_ready),
            "full_label_sheet_rows": len(label_rows),
            "ready_label_rows": status_counts.get("ready", 0),
            "label_ready_sheet_rows": len(label_ready_rows),
            "full_manifest_rows": len(updated_seeds),
            "label_ready_manifest_rows": len(label_ready_manifest_rows),
            "packet_path_errors": len(path_errors),
            "label_surface_leakage_hits": len(leakage_hits),
            "visible_value_leakage_hits": len(value_leakage_hits),
            "packet_text_leakage_hits": len(packet_text_hits),
            "validation_errors": len(validation_errors),
            "by_family": dict(sorted(family_counts.items())),
            "by_bucket": dict(sorted(bucket_counts.items())),
            "by_family_bucket": dict(sorted(family_bucket_counts.items())),
        },
        "packet_status_counts": dict(sorted(status_counts.items())),
        "generated_packet_status_counts": dict(sorted(generated_status_counts.items())),
        "packet_source_counts": dict(sorted(packet_source_counts.items())),
        "label_surface_leakage_audit": leakage,
        "validation_errors": validation_errors,
    }

    write_tsv(output_paths["full_label_sheet"], label_rows, mining.VISIBLE_FIELDS)
    write_tsv(output_paths["label_ready_sheet"], label_ready_rows, mining.VISIBLE_FIELDS)
    write_jsonl(output_paths["full_manifest_post_label_only"], updated_seeds)
    write_jsonl(output_paths["label_ready_manifest_post_label_only"], label_ready_manifest_rows)
    write_jsonl(output_paths["generated_packet_manifest"], generated_packets)
    write_jsonl(output_paths["generated_non_ready_packet_rows"], generated_non_ready)
    write_jsonl(output_paths["asset_needed_manifest_with_packets_post_label_only"], generated_manifest_rows)
    write_csv(output_paths["packet_gap_audit"], gap_rows)
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_jsonl(output_paths["label_surface_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["visible_value_leakage_hits"], value_leakage_hits)
    write_jsonl(output_paths["packet_text_leakage_hits"], packet_text_hits)
    write_json(output_paths["label_surface_leakage_audit"], leakage)
    write_jsonl(output_paths["input_validation_errors"], validation_errors)
    write_csv(output_paths["bucket_packet_summary"], bucket_rows)
    write_jsonl(output_paths["asset_request_snapshot"], asset_requests)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
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
