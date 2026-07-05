#!/usr/bin/env python3
"""Generate packets for H002 reliability target v3 informative-anchor rows."""

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
import reliability_target_v3_informative_anchor_candidate_mining as mining


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
CANDIDATE_DIR = RGA_ROOT / "reliability_target_v3_informative_anchor_candidate_mining"
DEFAULT_CANDIDATE_SUMMARY = CANDIDATE_DIR / "summary.json"
DEFAULT_SELECTED_CANDIDATES = CANDIDATE_DIR / "selected_candidates_internal.jsonl"
DEFAULT_PREVIOUS_MANIFEST = CANDIDATE_DIR / "informative_anchor_manifest_post_label_only.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_informative_anchor_asset_packets"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"

SCHEMA_VERSION = "h002_reliability_target_v3_informative_anchor_asset_packets_v1"
REVIEW_SCOPE = "h002_reliability_v3_informative_anchor_full_packeted"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--selected-candidates", type=Path, default=DEFAULT_SELECTED_CANDIDATES)
    parser.add_argument("--previous-manifest", type=Path, default=DEFAULT_PREVIOUS_MANIFEST)
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
    paths = [
        row.get("multiview_packet"),
        row.get("pointcloud_or_mesh_packet"),
        row.get("contact_or_context_sheet"),
    ]
    return any(not value for value in paths)


def asset_generation_row(seed: dict[str, Any]) -> dict[str, Any]:
    blind_id = mining.blind_review_id(seed)
    return {
        "blind_review_id": blind_id,
        "asset_request_id": seed.get("original_blind_review_id") or blind_id,
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
        paths = packet_paths_from_generated(packet)
        updated.update(paths)
        updated["packet_ready"] = packet.get("packet_status") == "ready"
        updated["packet_status"] = packet.get("packet_status", "")
        updated["asset_packet_source_hidden"] = "generated_informative_anchor_asset_packet"
        updated["generated_blind_review_id_hidden"] = blind_id
    elif updated.get("packet_ready") is True and updated.get("packet_status") == "ready":
        updated["asset_packet_source_hidden"] = "existing_independent_asset_packet"
        updated["generated_blind_review_id_hidden"] = blind_id
    else:
        updated["packet_ready"] = False
        updated["packet_status"] = updated.get("packet_status") or "asset_needed"
        updated["asset_packet_source_hidden"] = "missing_informative_anchor_asset_packet"
        updated["generated_blind_review_id_hidden"] = blind_id
    return updated


def full_visible_row(seed: dict[str, Any]) -> dict[str, Any]:
    row = mining.visible_row(seed)
    row["review_scope"] = REVIEW_SCOPE
    if seed.get("packet_status"):
        row["evidence_packet_status"] = seed["packet_status"]
    return row


def full_manifest_row(seed: dict[str, Any]) -> dict[str, Any]:
    row = mining.manifest_row(seed)
    row["batch_name"] = "reliability_target_v3_informative_anchor_asset_packets"
    row["evidence_packet_status"] = seed.get("packet_status", row.get("evidence_packet_status", ""))
    row["packet_paths"] = {
        "multiview_packet": seed.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": seed.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": seed.get("contact_or_context_sheet", ""),
    }
    hidden = dict(row.get("hidden_sampling_axes_post_label_only") or {})
    hidden["asset_packet_source_hidden"] = seed.get("asset_packet_source_hidden", "")
    hidden["generated_blind_review_id_hidden"] = seed.get("generated_blind_review_id_hidden", "")
    row["hidden_sampling_axes_post_label_only"] = hidden
    return row


def path_errors(label_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
            elif not as_abs(Path(value)).exists():
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


def category_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for category in sorted({str(row.get("anchor_category_hidden")) for row in rows}):
        group = [row for row in rows if str(row.get("anchor_category_hidden")) == category]
        families = Counter(str(row.get("predicate_family")) for row in group)
        statuses = Counter(str(row.get("packet_status")) for row in group)
        sources = Counter(str(row.get("asset_packet_source_hidden", "")) for row in group)
        output.append(
            {
                "anchor_category": category,
                "rows": len(group),
                "ready": statuses.get("ready", 0),
                "partial": statuses.get("partial", 0),
                "missing": statuses.get("missing", 0),
                "support_contact": families.get("support_contact", 0),
                "relative_vertical": families.get("relative_vertical", 0),
                "existing_packet_rows": sources.get("existing_independent_asset_packet", 0),
                "generated_packet_rows": sources.get("generated_informative_anchor_asset_packet", 0),
                "unique_scans": len({str(row.get("scan_id")) for row in group}),
            }
        )
    return output


def validate_inputs(candidate_summary: dict[str, Any], seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if candidate_summary.get("next_todo") != "reliability_target_v3_informative_anchor_asset_packets":
        errors.append({"error_type": "unexpected_candidate_next_todo", "value": candidate_summary.get("next_todo")})
    boundary = candidate_summary.get("boundary") or {}
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": f"candidate_boundary_{key}_not_false", "value": boundary.get(key)})
    if len(seeds) != candidate_summary.get("counts", {}).get("full_label_sheet_rows"):
        errors.append(
            {
                "error_type": "selected_seed_count_mismatch",
                "seed_rows": len(seeds),
                "summary_rows": candidate_summary.get("counts", {}).get("full_label_sheet_rows"),
            }
        )
    ids = [mining.blind_review_id(row) for row in seeds]
    for blind_id, count in Counter(ids).items():
        if count > 1:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id, "count": count})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Reliability Target V3 Informative Anchor Asset Packets",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage artifact.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- Multi-view and mesh packets are audit/label evidence only, not posterior input.",
        "- Hidden proxy/sampling fields remain in the post-label-only manifest.",
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
        f"| validation errors | {counts['validation_errors']} |",
        "",
        "## Category Summary",
        "",
        "| Category | Rows | Ready | Generated | Existing | support_contact | relative_vertical | Unique Scans |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["category_summary"]:
        lines.append(
            f"| `{row['anchor_category']}` | {row['rows']} | {row['ready']} | "
            f"{row['generated_packet_rows']} | {row['existing_packet_rows']} | "
            f"{row['support_contact']} | {row['relative_vertical']} | {row['unique_scans']} |"
        )
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
    validation_errors = validate_inputs(candidate_summary, selected_seeds)

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

    updated_seeds = [
        update_seed_with_packet(row, generated_by_id.get(mining.blind_review_id(row)))
        for row in selected_seeds
    ]
    label_rows = [full_visible_row(row) for row in updated_seeds]
    manifest_rows = [full_manifest_row(row) for row in updated_seeds]
    generated_manifest_rows = [
        row for row in manifest_rows if row["hidden_sampling_axes_post_label_only"].get("asset_packet_source_hidden")
        == "generated_informative_anchor_asset_packet"
    ]

    full_label_sheet = output_dir / "informative_anchor_full_label_sheet.tsv"
    write_tsv(full_label_sheet, label_rows, mining.VISIBLE_FIELDS)

    generated_non_ready = [row for row in generated_packets if row.get("packet_status") != "ready"]
    packet_errors = path_errors(label_rows)
    leakage = base_packets.label_surface_leakage_audit(
        generated_packets,
        [
            {
                "source_sheet": rel_path(args.selected_candidates),
                "output_sheet": rel_path(full_label_sheet),
                "rows": len(label_rows),
                "status_counts": dict(sorted(Counter(row["evidence_packet_status"] for row in label_rows).items())),
            }
        ],
        output_dir,
    )
    leakage_hits = leakage.get("hits", [])
    surface_field_hits = mining.surface_leakage_hits(mining.VISIBLE_FIELDS)
    if surface_field_hits:
        leakage_hits.extend(surface_field_hits)
        leakage["status"] = "fail"
        leakage["hits"] = leakage_hits

    status_counts = Counter(str(row.get("evidence_packet_status")) for row in label_rows)
    generated_status_counts = Counter(str(row.get("packet_status")) for row in generated_packets)
    family_counts = Counter(str(row.get("predicate_family")) for row in updated_seeds)
    packet_source_counts = Counter(str(row.get("asset_packet_source_hidden")) for row in updated_seeds)
    category_rows = category_summary(updated_seeds)

    all_ready = status_counts.get("ready", 0) == len(label_rows)
    status = (
        "h002_reliability_target_v3_informative_anchor_asset_packets_ready"
        if all_ready and not generated_non_ready and not packet_errors and not leakage_hits and not validation_errors
        else "h002_reliability_target_v3_informative_anchor_asset_packets_partial"
        if status_counts.get("ready", 0) > 0 and not leakage_hits
        else "h002_reliability_target_v3_informative_anchor_asset_packets_blocked"
    )
    next_todo = (
        "reliability_target_v3_informative_anchor_label_fill"
        if status == "h002_reliability_target_v3_informative_anchor_asset_packets_ready"
        else "reliability_target_v3_informative_anchor_asset_packet_gap_audit"
        if status == "h002_reliability_target_v3_informative_anchor_asset_packets_partial"
        else "fix_reliability_target_v3_informative_anchor_asset_packets"
    )
    decision = (
        "The full 160-row informative-anchor sheet is packet-complete and can proceed to label fill."
        if status == "h002_reliability_target_v3_informative_anchor_asset_packets_ready"
        else "Informative-anchor packets are partial. Inspect generated non-ready rows or missing paths before label fill."
        if status == "h002_reliability_target_v3_informative_anchor_asset_packets_partial"
        else "Informative-anchor packet generation is blocked by validation, leakage, or path errors."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "full_label_sheet": full_label_sheet,
        "full_manifest_post_label_only": output_dir / "informative_anchor_full_manifest_post_label_only.jsonl",
        "generated_packet_manifest": output_dir / "generated_packet_manifest.jsonl",
        "generated_non_ready_packet_rows": output_dir / "generated_non_ready_packet_rows.jsonl",
        "asset_needed_manifest_with_packets_post_label_only": output_dir
        / "asset_needed_manifest_with_packets_post_label_only.jsonl",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "label_surface_leakage_hits": output_dir / "label_surface_leakage_hits.jsonl",
        "label_surface_leakage_audit": output_dir / "label_surface_leakage_audit.json",
        "category_summary": output_dir / "category_summary.csv",
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
            "packet_path_errors": len(packet_errors),
            "label_surface_leakage_hits": len(leakage_hits),
            "validation_errors": len(validation_errors),
            "by_family": dict(sorted(family_counts.items())),
        },
        "packet_status_counts": dict(sorted(status_counts.items())),
        "generated_packet_status_counts": dict(sorted(generated_status_counts.items())),
        "packet_source_counts": dict(sorted(packet_source_counts.items())),
        "category_summary": category_rows,
        "label_surface_leakage_audit": leakage,
        "validation_errors": validation_errors,
    }

    write_tsv(output_paths["full_label_sheet"], label_rows, mining.VISIBLE_FIELDS)
    write_jsonl(output_paths["full_manifest_post_label_only"], manifest_rows)
    write_jsonl(output_paths["generated_packet_manifest"], generated_packets)
    write_jsonl(output_paths["generated_non_ready_packet_rows"], generated_non_ready)
    write_jsonl(output_paths["asset_needed_manifest_with_packets_post_label_only"], generated_manifest_rows)
    write_jsonl(output_paths["packet_path_errors"], packet_errors)
    write_jsonl(output_paths["label_surface_leakage_hits"], leakage_hits)
    write_json(output_paths["label_surface_leakage_audit"], leakage)
    write_csv(output_paths["category_summary"], category_rows)
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
