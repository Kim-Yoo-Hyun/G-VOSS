#!/usr/bin/env python3
"""Generate endpoint-controlled evidence packets and full label sheet."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_asset_packets as base_packets


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
CANDIDATE_ROOT = RGA_ROOT / "endpoint_controlled_candidate_mining"
DEFAULT_ASSET_REQUESTS = CANDIDATE_ROOT / "asset_request_manifest.jsonl"
DEFAULT_ASSET_NEEDED_MANIFEST = CANDIDATE_ROOT / "asset_needed_manifest_post_label_only.jsonl"
DEFAULT_PACKET_READY_MANIFEST = CANDIDATE_ROOT / "endpoint_controlled_packet_ready_manifest_post_label_only.jsonl"
DEFAULT_SELECTED_ALL_MANIFEST = CANDIDATE_ROOT / "selected_all_candidates_manifest_post_label_only.jsonl"
DEFAULT_PACKET_READY_SHEET = CANDIDATE_ROOT / "endpoint_controlled_packet_ready_label_sheet.tsv"
DEFAULT_CANDIDATE_SUMMARY = CANDIDATE_ROOT / "summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "endpoint_controlled_asset_packets"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"

LABEL_FIELDS = [
    "blind_review_id",
    "review_scope",
    "scan_id",
    "scene_context_id",
    "subject_id",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_id",
    "object_label",
    "family_question",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "external_reviewer_id",
    "external_review_round",
    "endpoint_identity_external",
    "visual_pair_evaluability_external",
    "mesh_pair_evaluability_external",
    "visual_geometry_answer_external",
    "mesh_geometry_answer_external",
    "relation_informativeness_external",
    "final_relation_reliability_external",
    "uncertainty_reason_external",
    "external_label_notes",
]

FAMILY_QUESTIONS = {
    "support_contact": "Does the subject physically contact or support/attach to the object in the packet evidence?",
    "relative_vertical": "Is the subject clearly higher/lower than the object in the packet evidence?",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-requests", type=Path, default=DEFAULT_ASSET_REQUESTS)
    parser.add_argument("--asset-needed-manifest", type=Path, default=DEFAULT_ASSET_NEEDED_MANIFEST)
    parser.add_argument("--packet-ready-manifest", type=Path, default=DEFAULT_PACKET_READY_MANIFEST)
    parser.add_argument("--selected-all-manifest", type=Path, default=DEFAULT_SELECTED_ALL_MANIFEST)
    parser.add_argument("--packet-ready-sheet", type=Path, default=DEFAULT_PACKET_READY_SHEET)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
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
    rows = []
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fieldnames or (list(rows[0].keys()) if rows else LABEL_FIELDS)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def packet_paths_from_packet_row(packet_row: dict[str, Any]) -> dict[str, str]:
    return {
        "multiview_packet": packet_row.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": packet_row.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": packet_row.get("contact_or_context_sheet", ""),
    }


def update_manifest_row(row: dict[str, Any], packet_row: dict[str, Any] | None) -> dict[str, Any]:
    updated = dict(row)
    paths = dict(updated.get("packet_paths") or {})
    if packet_row is not None:
        paths.update(packet_paths_from_packet_row(packet_row))
        updated["packet_status"] = packet_row.get("packet_status", "")
        updated["asset_packet_source"] = "generated_endpoint_asset_packet"
    elif not updated.get("packet_status"):
        updated["packet_status"] = "missing_packet_row"
    updated["packet_paths"] = paths
    return updated


def build_label_row(row: dict[str, Any]) -> dict[str, Any]:
    paths = row.get("packet_paths") or {}
    family = str(row.get("predicate_family", ""))
    return {
        "blind_review_id": row.get("blind_review_id", ""),
        "review_scope": "endpoint_controlled_support_vertical_v1",
        "scan_id": row.get("scan_id", ""),
        "scene_context_id": row.get("subgraph_id", ""),
        "subject_id": row.get("subject_id", ""),
        "subject_label": row.get("subject_label", ""),
        "predicate_label": row.get("predicate_label", ""),
        "predicate_family": family,
        "object_id": row.get("object_id", ""),
        "object_label": row.get("object_label", ""),
        "family_question": FAMILY_QUESTIONS.get(family, "Does the packet evidence support the relation?"),
        "evidence_packet_status": row.get("packet_status", ""),
        "multiview_packet": paths.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": paths.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": paths.get("contact_or_context_sheet", ""),
        "external_reviewer_id": "",
        "external_review_round": "",
        "endpoint_identity_external": "",
        "visual_pair_evaluability_external": "",
        "mesh_pair_evaluability_external": "",
        "visual_geometry_answer_external": "",
        "mesh_geometry_answer_external": "",
        "relation_informativeness_external": "",
        "final_relation_reliability_external": "",
        "uncertainty_reason_external": "",
        "external_label_notes": "",
    }


def path_errors(label_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors = []
    for row in label_rows:
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = row.get(field, "")
            if not value:
                errors.append(
                    {
                        "blind_review_id": row.get("blind_review_id"),
                        "field": field,
                        "error": "empty_packet_path",
                    }
                )
                continue
            if not as_abs(Path(value)).exists():
                errors.append(
                    {
                        "blind_review_id": row.get("blind_review_id"),
                        "field": field,
                        "value": value,
                        "error": "packet_path_missing_on_disk",
                    }
                )
    return errors


def label_surface_leakage_audit(packet_rows: list[dict[str, Any]], label_sheet: Path, output_dir: Path) -> dict[str, Any]:
    sheet_output = {"output_sheet": rel_path(label_sheet), "rows": 0, "status_counts": {}}
    audit = base_packets.label_surface_leakage_audit(packet_rows, [sheet_output], output_dir)
    return audit


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Endpoint-Controlled Asset Packets",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage artifact.",
        "- No validation/test rows are used.",
        "- Multi-view/mesh evidence is audit support only, not posterior input.",
        "- Endpoint fields remain hidden sampling/audit controls.",
        "- No posterior is trained.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| packet-ready input rows | {summary['counts']['packet_ready_input_rows']} |",
        f"| asset-needed input rows | {summary['counts']['asset_needed_input_rows']} |",
        f"| generated packet rows | {summary['counts']['generated_packet_rows']} |",
        f"| full label sheet rows | {summary['counts']['full_label_sheet_rows']} |",
        f"| packet path errors | {summary['counts']['packet_path_errors']} |",
        "",
        "## Packet Status",
        "",
        "| Status | Rows |",
        "| --- | ---: |",
    ]
    for key, value in summary["packet_status_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Label Surface",
            "",
            f"Leakage audit: `{summary['label_surface_leakage_audit']['status']}`",
            "",
            "## Outputs",
            "",
            f"- Full label sheet: `{summary['outputs']['full_label_sheet']}`",
            f"- Full post-label-only manifest: `{summary['outputs']['full_manifest_post_label_only']}`",
            f"- Generated packet manifest: `{summary['outputs']['generated_packet_manifest']}`",
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
    asset_requests = read_jsonl(args.asset_requests)
    asset_needed_manifest = read_jsonl(args.asset_needed_manifest)
    packet_ready_manifest = read_jsonl(args.packet_ready_manifest)
    selected_all = read_jsonl(args.selected_all_manifest)
    candidate_summary = read_json(args.candidate_summary)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    packet_args = argparse.Namespace(
        scan_root=as_abs(args.scan_root),
        images_per_object=args.images_per_object,
        thumb_size=args.thumb_size,
    )
    generated_rows = [
        base_packets.generate_packet(row, packet_args, output_dir)
        for row in asset_requests
    ]
    generated_by_id = {str(row["blind_review_id"]): row for row in generated_rows}
    packet_ready_by_id = {str(row["blind_review_id"]): row for row in packet_ready_manifest}

    write_jsonl(output_dir / "generated_packet_manifest.jsonl", generated_rows)
    non_ready_generated = [row for row in generated_rows if row.get("packet_status") != "ready"]
    write_jsonl(output_dir / "generated_non_ready_packet_rows.jsonl", non_ready_generated)

    full_manifest = []
    for row in selected_all:
        blind_id = str(row.get("blind_review_id"))
        if blind_id in generated_by_id:
            full_manifest.append(update_manifest_row(row, generated_by_id[blind_id]))
        elif blind_id in packet_ready_by_id:
            full_manifest.append(update_manifest_row(row, None))
        else:
            missing = dict(row)
            missing["packet_status"] = "missing_packet_row"
            full_manifest.append(missing)

    # Preserve existing packet-ready paths exactly, then fill generated paths for new rows.
    ready_path_by_id = {str(row["blind_review_id"]): row.get("packet_paths", {}) for row in packet_ready_manifest}
    for row in full_manifest:
        blind_id = str(row.get("blind_review_id"))
        if blind_id in ready_path_by_id:
            row["packet_paths"] = dict(ready_path_by_id[blind_id])
            row["packet_status"] = "ready"
            row["asset_packet_source"] = "existing_independent_asset_packet"

    label_rows = [build_label_row(row) for row in full_manifest]
    full_label_sheet = output_dir / "endpoint_controlled_full_label_sheet.tsv"
    write_tsv(full_label_sheet, label_rows, LABEL_FIELDS)

    full_manifest_path = output_dir / "endpoint_controlled_full_manifest_post_label_only.jsonl"
    write_jsonl(full_manifest_path, full_manifest)
    generated_manifest_path = output_dir / "asset_needed_manifest_with_packets_post_label_only.jsonl"
    write_jsonl(
        generated_manifest_path,
        [row for row in full_manifest if str(row.get("blind_review_id")) in generated_by_id],
    )

    errors = path_errors(label_rows)
    write_jsonl(output_dir / "packet_path_errors.jsonl", errors)
    all_packet_rows_for_audit = []
    for row in label_rows:
        all_packet_rows_for_audit.append(
            {
                "blind_review_id": row["blind_review_id"],
                "multiview_packet": row["multiview_packet"],
                "pointcloud_or_mesh_packet": row["pointcloud_or_mesh_packet"],
            }
        )
    leakage = label_surface_leakage_audit(all_packet_rows_for_audit, full_label_sheet, output_dir)

    status_counts = Counter(row.get("evidence_packet_status", "") for row in label_rows)
    family_counts = Counter(row.get("predicate_family", "") for row in label_rows)
    generated_status_counts = Counter(row.get("packet_status", "") for row in generated_rows)
    all_ready = status_counts.get("ready", 0) == len(label_rows)
    leakage_pass = leakage["status"] == "pass"
    status = (
        "h002_endpoint_controlled_asset_packets_ready"
        if all_ready and not errors and leakage_pass
        else "h002_endpoint_controlled_asset_packets_partial"
        if any(count for key, count in status_counts.items() if key in {"ready", "partial"}) and leakage_pass
        else "h002_endpoint_controlled_asset_packets_blocked"
    )
    next_todo = (
        "endpoint_controlled_label_fill"
        if status == "h002_endpoint_controlled_asset_packets_ready"
        else "endpoint_controlled_asset_packet_gap_audit"
        if status == "h002_endpoint_controlled_asset_packets_partial"
        else "fix_endpoint_controlled_asset_packet_generation"
    )
    decision = (
        "Endpoint-controlled asset packets are ready. The full 62-row label sheet can be filled before ingestion and target-independence audit."
        if status == "h002_endpoint_controlled_asset_packets_ready"
        else "Endpoint-controlled asset packet generation produced partial evidence. Inspect packet gaps before label fill."
        if status == "h002_endpoint_controlled_asset_packets_partial"
        else "Endpoint-controlled asset packet generation is blocked by leakage or missing paths. Fix before label fill."
    )
    summary = {
        "schema_version": "h002_endpoint_controlled_asset_packet_generation_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "asset_requests": rel_path(args.asset_requests),
            "asset_needed_manifest": rel_path(args.asset_needed_manifest),
            "packet_ready_manifest": rel_path(args.packet_ready_manifest),
            "selected_all_manifest": rel_path(args.selected_all_manifest),
            "packet_ready_sheet": rel_path(args.packet_ready_sheet),
            "candidate_summary": rel_path(args.candidate_summary),
            "scan_root": rel_path(args.scan_root),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split_policy": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "posterior_trained": False,
            "multi_view_as_model_input": False,
            "endpoint_as_model_input": False,
            "paper_metric_evidence": False,
        },
        "source_candidate_status": candidate_summary.get("status"),
        "counts": {
            "packet_ready_input_rows": len(packet_ready_manifest),
            "asset_needed_input_rows": len(asset_needed_manifest),
            "asset_request_rows": len(asset_requests),
            "generated_packet_rows": len(generated_rows),
            "generated_non_ready_rows": len(non_ready_generated),
            "full_label_sheet_rows": len(label_rows),
            "packet_path_errors": len(errors),
        },
        "packet_status_counts": dict(sorted(status_counts.items())),
        "generated_packet_status_counts": dict(sorted(generated_status_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "label_surface_leakage_audit": leakage,
        "outputs": {
            "full_label_sheet": rel_path(full_label_sheet),
            "full_manifest_post_label_only": rel_path(full_manifest_path),
            "generated_packet_manifest": rel_path(output_dir / "generated_packet_manifest.jsonl"),
            "generated_non_ready_packet_rows": rel_path(output_dir / "generated_non_ready_packet_rows.jsonl"),
            "asset_needed_manifest_with_packets_post_label_only": rel_path(generated_manifest_path),
            "packet_path_errors": rel_path(output_dir / "packet_path_errors.jsonl"),
            "packets_dir": rel_path(output_dir / "packets"),
        },
        "decision": decision,
        "next_todo": next_todo,
        "validation_errors": [] if not errors and leakage_pass else errors + leakage.get("hits", []),
    }
    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} "
        f"generated={summary['counts']['generated_packet_rows']} "
        f"full_sheet={summary['counts']['full_label_sheet_rows']} "
        f"packet_status_counts={summary['packet_status_counts']} "
        f"path_errors={summary['counts']['packet_path_errors']} "
        f"leakage={summary['label_surface_leakage_audit']['status']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
