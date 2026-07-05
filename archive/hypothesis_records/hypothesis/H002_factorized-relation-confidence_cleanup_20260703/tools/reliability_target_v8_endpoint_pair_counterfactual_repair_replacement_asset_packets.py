#!/usr/bin/env python3
"""Generate packets for H002 v8 repair replacement rows."""

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
import reliability_target_v8_endpoint_pair_counterfactual_target_repair_and_additional_mining as repair


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

REPLACEMENT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_mining_codex_proxy_user_requested"
DEFAULT_REPLACEMENT_SUMMARY = REPLACEMENT_DIR / "summary.json"
DEFAULT_COMBINED_CANDIDATES = REPLACEMENT_DIR / "repaired_200_manifest_pre_label_readiness.jsonl"
DEFAULT_ASSET_REQUESTS = REPLACEMENT_DIR / "replacement_asset_request_manifest.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_asset_packets_codex_proxy_user_requested"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"

EXPECTED_REPLACEMENT_STATUS = "h002_reliability_target_v8_repair_replacement_mining_ready_needs_asset_packets"
EXPECTED_NEXT_TODO = "reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_asset_packets"
SCHEMA_VERSION = "h002_reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_asset_packets_v1"
REVIEW_SCOPE = "h002_reliability_v8_endpoint_pair_counterfactual_repair_replacement_packeted_review"
GENERATED_PACKET_SOURCE = "generated_v8_endpoint_pair_counterfactual_repair_replacement_asset_packet"
EXISTING_PACKET_SOURCE = "existing_prior_or_repair_packet"
MISSING_PACKET_SOURCE = "missing_v8_endpoint_pair_counterfactual_repair_replacement_asset_packet"

PACKET_TEXT_FORBIDDEN_TOKENS = [
    "candidate_bucket",
    "semantic_score",
    "semantic_rank",
    "p_geom",
    "geometry_status",
    "rank_band",
    "source_queue",
    "endpoint_pair_key",
    "counterfactual_pair_id",
    "object_family_cell",
    "subject_object_family_cell",
    "label_match",
    "h001_verification",
    "expected_target",
    "machine_hint",
    "reason_codes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replacement-summary", type=Path, default=DEFAULT_REPLACEMENT_SUMMARY)
    parser.add_argument("--combined-candidates", type=Path, default=DEFAULT_COMBINED_CANDIDATES)
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


def packet_status(row: dict[str, Any]) -> str:
    return str(row.get("packet_status_hidden") or row.get("packet_status") or "")


def needs_asset_packet(row: dict[str, Any]) -> bool:
    return not (
        packet_status(row) == "ready"
        and all(row.get(field) for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"])
    )


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


def packet_paths(packet_row: dict[str, Any]) -> dict[str, str]:
    return {
        "multiview_packet": str(packet_row.get("multiview_packet") or ""),
        "pointcloud_or_mesh_packet": str(packet_row.get("pointcloud_or_mesh_packet") or ""),
        "contact_or_context_sheet": str(packet_row.get("contact_or_context_sheet") or ""),
    }


def update_seed_with_packet(seed: dict[str, Any], packet: dict[str, Any] | None) -> dict[str, Any]:
    updated = dict(seed)
    if packet is not None:
        updated.update(packet_paths(packet))
        updated["packet_status_hidden"] = packet.get("packet_status", "")
        updated["asset_packet_source_hidden"] = GENERATED_PACKET_SOURCE
    elif packet_status(updated) == "ready":
        updated["asset_packet_source_hidden"] = updated.get("asset_packet_source_hidden") or EXISTING_PACKET_SOURCE
    else:
        updated["packet_status_hidden"] = packet_status(updated) or "asset_needed"
        updated["asset_packet_source_hidden"] = MISSING_PACKET_SOURCE
    updated["label_fill_allowed"] = False
    updated["posterior_input_allowed"] = False
    return updated


def label_packet_path(seed: dict[str, Any], field: str, output_dir: Path) -> str:
    value = str(seed.get(field) or "")
    if not value:
        return ""
    abs_path = as_abs(Path(value))
    try:
        return str(abs_path.relative_to(output_dir))
    except ValueError:
        return rel_path(abs_path)


def label_row(seed: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    row = repair.visible_row(seed)
    row["review_scope"] = REVIEW_SCOPE
    row["evidence_packet_status"] = packet_status(seed)
    row["multiview_packet"] = label_packet_path(seed, "multiview_packet", output_dir)
    row["pointcloud_or_mesh_packet"] = label_packet_path(seed, "pointcloud_or_mesh_packet", output_dir)
    row["contact_or_context_sheet"] = label_packet_path(seed, "contact_or_context_sheet", output_dir)
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
    forbidden = [
        "semantic_score",
        "semantic_rank",
        "p_geom",
        "geometry_status",
        "rank_band",
        "source_queue",
        "endpoint_pair_key",
        "counterfactual_pair_id",
        "subject_object_family_cell",
        "label_match",
        "h001_verification",
        "machine_hint",
    ]
    for row_number, row in enumerate(label_rows, start=2):
        for field, value in row.items():
            if field in {"multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"}:
                continue
            lower = str(value).lower()
            for token in forbidden:
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


def status_audit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        output.append(
            {
                "blind_review_id": row.get("blind_review_id"),
                "batch_role": row.get("additional_batch_role_hidden"),
                "pair_type": row.get("counterfactual_pair_type_hidden"),
                "predicate_family": row.get("predicate_family"),
                "predicate_label": row.get("predicate_label"),
                "scan_id": row.get("scan_id"),
                "scene_context_id": row.get("scene_context_id"),
                "subject_id": row.get("subject_id"),
                "subject_label": row.get("subject_label"),
                "object_id": row.get("object_id"),
                "object_label": row.get("object_label"),
                "packet_status": packet_status(row),
                "asset_packet_source_hidden": row.get("asset_packet_source_hidden"),
                "multiview_packet_present": bool(row.get("multiview_packet")),
                "pointcloud_or_mesh_packet_present": bool(row.get("pointcloud_or_mesh_packet")),
                "contact_or_context_sheet_present": bool(row.get("contact_or_context_sheet")),
            }
        )
    return output


def bucket_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("additional_batch_role_hidden")), str(row.get("predicate_family")), str(row.get("predicate_label")))].append(row)
    output: list[dict[str, Any]] = []
    for (role, family, predicate), group in sorted(grouped.items()):
        statuses = Counter(packet_status(row) for row in group)
        sources = Counter(str(row.get("asset_packet_source_hidden")) for row in group)
        output.append(
            {
                "batch_role": role,
                "predicate_family": family,
                "predicate_label": predicate,
                "rows": len(group),
                "ready_rows": statuses.get("ready", 0),
                "partial_rows": statuses.get("partial", 0),
                "asset_needed_rows": statuses.get("asset_needed", 0),
                "generated_rows": sources.get(GENERATED_PACKET_SOURCE, 0),
                "existing_rows": sum(count for source, count in sources.items() if source not in {GENERATED_PACKET_SOURCE, MISSING_PACKET_SOURCE}),
                "missing_source_rows": sources.get(MISSING_PACKET_SOURCE, 0),
            }
        )
    return output


def validate_inputs(replacement_summary: dict[str, Any], seeds: list[dict[str, Any]], asset_requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if replacement_summary.get("status") != EXPECTED_REPLACEMENT_STATUS:
        errors.append({"error_type": "unexpected_replacement_status", "value": replacement_summary.get("status")})
    if replacement_summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_replacement_next_todo", "value": replacement_summary.get("next_todo")})
    boundary = replacement_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "labels_filled",
        "posterior_trained",
        "posterior_smoke_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "replacement_boundary_not_false", "field": key, "value": boundary.get(key)})
    counts = replacement_summary.get("counts", {})
    if len(seeds) != counts.get("combined_rows"):
        errors.append({"error_type": "combined_seed_count_mismatch", "seed_rows": len(seeds), "summary_rows": counts.get("combined_rows")})
    if len(asset_requests) != counts.get("replacement_asset_needed_rows"):
        errors.append({"error_type": "asset_request_count_mismatch", "asset_request_rows": len(asset_requests), "summary_rows": counts.get("replacement_asset_needed_rows")})
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
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V8 Repair Replacement Asset Packets",
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
        f"validation_errors = {counts['validation_errors']}",
        "```",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| combined input rows | {counts['combined_input_rows']} |",
        f"| asset-needed input rows | {counts['asset_needed_input_rows']} |",
        f"| generated packet rows | {counts['generated_packet_rows']} |",
        f"| generated non-ready rows | {counts['generated_non_ready_rows']} |",
        f"| ready label rows | {counts['ready_label_rows']} |",
        f"| packet path errors | {counts['packet_path_errors']} |",
        f"| leakage hits | {counts['label_surface_leakage_hits']} |",
        f"| validation errors | {counts['validation_errors']} |",
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
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    replacement_summary = read_json(args.replacement_summary)
    seeds = read_jsonl(args.combined_candidates)
    asset_requests = read_jsonl(args.asset_requests)
    validation_errors = validate_inputs(replacement_summary, seeds, asset_requests)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    asset_needed = [row for row in seeds if needs_asset_packet(row)]
    packet_args = argparse.Namespace(scan_root=as_abs(args.scan_root), images_per_object=args.images_per_object, thumb_size=args.thumb_size)
    generated_packets = [base_packets.generate_packet(asset_generation_row(row), packet_args, output_dir) for row in asset_needed]
    generated_by_id = {str(row["blind_review_id"]): row for row in generated_packets}
    updated = [update_seed_with_packet(row, generated_by_id.get(str(row["blind_review_id"]))) for row in seeds]

    label_rows = [label_row(row, output_dir) for row in updated]
    label_ready_rows = [row for row in label_rows if row.get("evidence_packet_status") == "ready"]
    label_ready_manifest = [row for row in updated if packet_status(row) == "ready"]
    generated_manifest_rows = [row for row in updated if row.get("asset_packet_source_hidden") == GENERATED_PACKET_SOURCE]
    generated_non_ready = [row for row in generated_packets if row.get("packet_status") != "ready"]

    path_errors = packet_path_errors(label_rows, output_dir)
    value_hits = visible_value_leakage_hits(label_rows)
    packet_hits = packet_text_leakage_hits(generated_packets)
    leakage_hits = value_hits + packet_hits

    status_counts = Counter(str(row.get("evidence_packet_status")) for row in label_rows)
    generated_status_counts = Counter(str(row.get("packet_status")) for row in generated_packets)
    source_counts = Counter(str(row.get("asset_packet_source_hidden")) for row in updated)
    role_counts = Counter(str(row.get("additional_batch_role_hidden")) for row in updated)
    predicate_counts = Counter(str(row.get("predicate_label")) for row in updated)

    if validation_errors or path_errors or leakage_hits:
        status = "h002_reliability_target_v8_repair_replacement_asset_packets_blocked"
        next_todo = "fix_reliability_target_v8_repair_replacement_asset_packets"
        decision = "Replacement packet generation is blocked by validation, leakage, or path errors."
    elif status_counts.get("ready", 0) == len(label_rows):
        status = "h002_reliability_target_v8_repair_replacement_asset_packets_ready_for_label_readiness"
        next_todo = "reliability_target_v8_endpoint_pair_counterfactual_repair_label_readiness"
        decision = "The restored 200-row repair batch is packet-complete and can proceed to label readiness."
    else:
        status = "h002_reliability_target_v8_repair_replacement_asset_packets_partial_needs_gap_audit"
        next_todo = "reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_asset_packet_gap_audit"
        decision = "Some replacement packets are partial. Inspect non-ready rows before label readiness/fill."

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "full_label_sheet": output_dir / "repair_replacement_full_label_sheet.tsv",
        "label_ready_sheet": output_dir / "repair_replacement_label_ready_sheet.tsv",
        "full_manifest_post_label_only": output_dir / "repair_replacement_full_manifest_post_label_only.jsonl",
        "label_ready_manifest_post_label_only": output_dir / "repair_replacement_label_ready_manifest_post_label_only.jsonl",
        "generated_packet_manifest": output_dir / "generated_replacement_packet_manifest.jsonl",
        "generated_non_ready_packet_rows": output_dir / "generated_replacement_non_ready_packet_rows.jsonl",
        "asset_needed_manifest_with_packets_post_label_only": output_dir / "replacement_asset_needed_manifest_with_packets_post_label_only.jsonl",
        "packet_gap_audit": output_dir / "replacement_packet_gap_audit.csv",
        "bucket_packet_summary": output_dir / "replacement_bucket_packet_summary.csv",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "visible_value_leakage_hits": output_dir / "visible_value_leakage_hits.jsonl",
        "packet_text_leakage_hits": output_dir / "packet_text_leakage_hits.jsonl",
        "input_validation_errors": output_dir / "input_validation_errors.jsonl",
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
            "replacement_summary": rel_path(args.replacement_summary),
            "combined_candidates": rel_path(args.combined_candidates),
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
            "h001_artifacts_modified": False,
        },
        "source_replacement_status": replacement_summary.get("status"),
        "counts": {
            "combined_input_rows": len(seeds),
            "asset_needed_input_rows": len(asset_needed),
            "generated_packet_rows": len(generated_packets),
            "generated_non_ready_rows": len(generated_non_ready),
            "full_label_sheet_rows": len(label_rows),
            "ready_label_rows": status_counts.get("ready", 0),
            "label_ready_sheet_rows": len(label_ready_rows),
            "full_manifest_rows": len(updated),
            "label_ready_manifest_rows": len(label_ready_manifest),
            "packet_path_errors": len(path_errors),
            "label_surface_leakage_hits": len(leakage_hits),
            "visible_value_leakage_hits": len(value_hits),
            "packet_text_leakage_hits": len(packet_hits),
            "validation_errors": len(validation_errors),
            "by_batch_role": dict(sorted(role_counts.items())),
            "by_predicate_label": dict(sorted(predicate_counts.items())),
        },
        "packet_status_counts": dict(sorted(status_counts.items())),
        "generated_packet_status_counts": dict(sorted(generated_status_counts.items())),
        "packet_source_counts": dict(sorted(source_counts.items())),
        "validation_errors": validation_errors,
    }

    write_tsv(output_paths["full_label_sheet"], label_rows, repair.VISIBLE_FIELDS)
    write_tsv(output_paths["label_ready_sheet"], label_ready_rows, repair.VISIBLE_FIELDS)
    write_jsonl(output_paths["full_manifest_post_label_only"], updated)
    write_jsonl(output_paths["label_ready_manifest_post_label_only"], label_ready_manifest)
    write_jsonl(output_paths["generated_packet_manifest"], generated_packets)
    write_jsonl(output_paths["generated_non_ready_packet_rows"], generated_non_ready)
    write_jsonl(output_paths["asset_needed_manifest_with_packets_post_label_only"], generated_manifest_rows)
    write_csv(output_paths["packet_gap_audit"], status_audit_rows(updated))
    write_csv(output_paths["bucket_packet_summary"], bucket_summary_rows(updated))
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_jsonl(output_paths["visible_value_leakage_hits"], value_hits)
    write_jsonl(output_paths["packet_text_leakage_hits"], packet_hits)
    write_jsonl(output_paths["input_validation_errors"], validation_errors)
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
        f"leakage_hits={summary['counts']['label_surface_leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} "
        f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']} "
        f"next={summary['next_todo']}"
    )
    return 0 if summary["counts"]["validation_errors"] == 0 and summary["counts"]["packet_path_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
