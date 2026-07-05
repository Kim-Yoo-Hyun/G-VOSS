#!/usr/bin/env python3
"""Audit v7 object-cell evidence-contrast partial asset packets before labels."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

PACKET_DIR = RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_asset_packets_codex_proxy_user_requested"
DEFAULT_PACKET_SUMMARY = PACKET_DIR / "summary.json"
DEFAULT_FULL_LABEL_SHEET = PACKET_DIR / "v7_object_cell_evidence_contrast_full_label_sheet.tsv"
DEFAULT_FULL_MANIFEST = PACKET_DIR / "v7_object_cell_evidence_contrast_full_manifest_post_label_only.jsonl"
DEFAULT_GENERATED_PACKET_MANIFEST = PACKET_DIR / "generated_packet_manifest.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit_codex_proxy_user_requested"

SCHEMA_VERSION = "h002_reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit_v1"
GENERIC_ENDPOINT_LABELS = {"object", "objects", "item", "items", "clutter", "unknown"}
VISIBLE_FORBIDDEN_TOKENS = [
    "candidate_bucket",
    "semantic_score",
    "semantic_rank",
    "p_geom",
    "geometry_status",
    "hidden",
    "h001_verification",
    "label_match",
    "object_family_cell",
    "subject_object_family_cell",
    "rank_band",
    "source_queue",
    "strict_group",
    "b2_semantic",
    "b3_semantic",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-summary", type=Path, default=DEFAULT_PACKET_SUMMARY)
    parser.add_argument("--full-label-sheet", type=Path, default=DEFAULT_FULL_LABEL_SHEET)
    parser.add_argument("--full-manifest", type=Path, default=DEFAULT_FULL_MANIFEST)
    parser.add_argument("--generated-packet-manifest", type=Path, default=DEFAULT_GENERATED_PACKET_MANIFEST)
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
                    seen.add(key)
                    fieldnames.append(key)
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
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def resolve_packet_path(value: str, packet_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    repo_candidate = as_abs(path)
    if repo_candidate.exists():
        return repo_candidate
    return packet_dir / path


def missing_sides(packet_row: dict[str, Any]) -> list[str]:
    sides: list[str] = []
    if int(packet_row.get("subject_image_count") or 0) <= 0:
        sides.append("subject")
    if int(packet_row.get("object_image_count") or 0) <= 0:
        sides.append("object")
    return sides


def has_generic_missing_endpoint(packet_row: dict[str, Any], sides: list[str]) -> bool:
    if "subject" in sides and str(packet_row.get("subject_label", "")).lower() in GENERIC_ENDPOINT_LABELS:
        return True
    if "object" in sides and str(packet_row.get("object_label", "")).lower() in GENERIC_ENDPOINT_LABELS:
        return True
    return False


def synthetic_ready_packet(manifest_row: dict[str, Any]) -> dict[str, Any]:
    packet_paths = {
        "multiview_packet": manifest_row.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": manifest_row.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": manifest_row.get("contact_or_context_sheet", ""),
    }
    return {
        "blind_review_id": manifest_row.get("blind_review_id"),
        "packet_status": manifest_row.get("packet_status_hidden") or "ready",
        "subject_image_count": 1,
        "object_image_count": 1,
        "contact_sheet_ready": True,
        "mesh_packet_ready": True,
        **packet_paths,
    }


def decide_row(packet_row: dict[str, Any], manifest_row: dict[str, Any]) -> dict[str, Any]:
    status = str(packet_row.get("packet_status") or manifest_row.get("packet_status_hidden") or "")
    sides = missing_sides(packet_row)
    contact_ready = bool(packet_row.get("contact_sheet_ready", status == "ready"))
    mesh_ready = bool(packet_row.get("mesh_packet_ready", status == "ready"))
    family = str(manifest_row.get("predicate_family") or packet_row.get("predicate_family") or "")
    generic_missing = has_generic_missing_endpoint(packet_row, sides)

    if status == "ready":
        decision = "label_ready"
        reason = "complete packet"
        normalized_status = "ready"
    elif len(sides) >= 2:
        decision = "replacement_needed"
        reason = "both endpoint crops are missing; endpoint identity cannot be checked independently"
        normalized_status = "replacement_needed"
    elif generic_missing:
        decision = "replacement_needed"
        reason = "the missing endpoint has a generic object/item label, so endpoint identity is underdetermined"
        normalized_status = "replacement_needed"
    elif mesh_ready and contact_ready and len(sides) == 1:
        decision = "limited_view_evaluable"
        reason = "one endpoint crop is missing, but mesh and contact/context evidence are available"
        normalized_status = "limited_view_evaluable"
    elif mesh_ready and family in {"support_contact", "relative_vertical"} and len(sides) == 1:
        decision = "geometry_only_evaluable"
        reason = "one endpoint crop is missing, but mesh evidence is available for a geometric relation family"
        normalized_status = "geometry_only_evaluable"
    else:
        decision = "replacement_needed"
        reason = "insufficient packet evidence for label fill"
        normalized_status = "replacement_needed"

    return {
        "blind_review_id": manifest_row.get("blind_review_id") or packet_row.get("blind_review_id"),
        "predicate_family": family,
        "predicate_label": manifest_row.get("predicate_label") or packet_row.get("predicate_label"),
        "subject_label": manifest_row.get("subject_label") or packet_row.get("subject_label"),
        "object_label": manifest_row.get("object_label") or packet_row.get("object_label"),
        "packet_status": status,
        "normalized_evidence_status": normalized_status,
        "row_gap_decision": decision,
        "row_gap_reason": reason,
        "missing_sides": sides,
        "generic_missing_endpoint": generic_missing,
        "subject_image_count": packet_row.get("subject_image_count"),
        "object_image_count": packet_row.get("object_image_count"),
        "contact_sheet_ready": contact_ready,
        "mesh_packet_ready": mesh_ready,
        "scan_id": manifest_row.get("scan_id") or packet_row.get("scan_id"),
        "scene_context_id": manifest_row.get("scene_context_id"),
        "subject_id": manifest_row.get("subject_id") or packet_row.get("subject_id"),
        "object_id": manifest_row.get("object_id") or packet_row.get("object_id"),
        "semantic_geometry_bucket_hidden": manifest_row.get("semantic_geometry_bucket_hidden"),
        "strict_group_key_hidden": manifest_row.get("strict_group_key_hidden"),
        "subject_object_family_cell_hidden": manifest_row.get("subject_object_family_cell_hidden"),
        "subject_object_label_pair_hidden": manifest_row.get("subject_object_label_pair_hidden"),
    }


def rewrite_blind_id(path: Path, blind_id: str) -> None:
    if path.suffix != ".md" or not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    lines = []
    for line in text.splitlines():
        if line.startswith("Blind review id:"):
            lines.append(f"Blind review id: `{blind_id}`")
        else:
            lines.append(line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def materialize_packet(row: dict[str, Any], output_dir: Path, packet_dir: Path) -> dict[str, str]:
    blind_id = str(row["blind_review_id"])
    dest_dir = output_dir / "packets" / blind_id
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    packet_value = str(row.get("multiview_packet") or "")
    if packet_value:
        packet_src = resolve_packet_path(packet_value, packet_dir)
        if packet_src.exists() and packet_src.parent.is_dir():
            for src in packet_src.parent.iterdir():
                dest = dest_dir / src.name
                if src.is_file():
                    shutil.copy2(src, dest)
                    rewrite_blind_id(dest, blind_id)

    output_paths: dict[str, str] = {}
    for field, filename in [
        ("multiview_packet", "packet.md"),
        ("pointcloud_or_mesh_packet", "mesh_packet.md"),
        ("contact_or_context_sheet", "contact_context_sheet.jpg"),
    ]:
        value = str(row.get(field) or "")
        src = resolve_packet_path(value, packet_dir) if value else None
        dest = dest_dir / filename
        if src is not None and src.exists() and src.is_file() and not dest.exists():
            shutil.copy2(src, dest)
            rewrite_blind_id(dest, blind_id)
        if dest.exists():
            output_paths[field] = f"packets/{blind_id}/{filename}"

    if "contact_or_context_sheet" not in output_paths and output_paths.get("pointcloud_or_mesh_packet"):
        context_path = dest_dir / "geometry_only_context.md"
        context_path.write_text(
            "\n".join(
                [
                    "# Geometry-Only Context Packet",
                    "",
                    f"Blind review id: `{blind_id}`",
                    f"Scan: `{row.get('scan_id', '')}`",
                    f"Scene context: `{row.get('scene_context_id', '')}`",
                    "",
                    "Relation:",
                    "",
                    f"- Subject: `{row.get('subject_label', '')}` (`{row.get('subject_id', '')}`)",
                    f"- Predicate: `{row.get('predicate_label', '')}`",
                    f"- Object: `{row.get('object_label', '')}` (`{row.get('object_id', '')}`)",
                    "",
                    "Boundary:",
                    "",
                    "Multi-view/contact evidence is incomplete for this row. Use the mesh packet as audit evidence only.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        output_paths["contact_or_context_sheet"] = f"packets/{blind_id}/geometry_only_context.md"
    return output_paths


def label_sheet_rows(
    label_rows: list[dict[str, Any]],
    row_decisions_by_id: dict[str, dict[str, Any]],
    output_dir: Path,
    packet_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for row in label_rows:
        blind_id = str(row.get("blind_review_id"))
        decision = row_decisions_by_id[blind_id]
        updated = dict(row)
        updated["packet_gap_decision"] = decision["row_gap_decision"]
        updated["packet_gap_reason"] = decision["row_gap_reason"]
        updated["evidence_packet_status"] = decision["normalized_evidence_status"]
        if decision["row_gap_decision"] == "replacement_needed":
            excluded_rows.append(updated)
            continue
        updated.update(materialize_packet(updated, output_dir, packet_dir))
        ready_rows.append(updated)
    return ready_rows, excluded_rows


def manifest_rows(
    manifests: list[dict[str, Any]],
    row_decisions_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for row in manifests:
        blind_id = str(row.get("blind_review_id"))
        decision = row_decisions_by_id[blind_id]
        updated = dict(row)
        updated["row_gap_decision_hidden"] = decision["row_gap_decision"]
        updated["row_gap_reason_hidden"] = decision["row_gap_reason"]
        updated["normalized_evidence_status_hidden"] = decision["normalized_evidence_status"]
        forbidden = list(updated.get("forbidden_as_labeler_visible") or [])
        for field in ["row_gap_decision_hidden", "row_gap_reason_hidden", "normalized_evidence_status_hidden"]:
            if field not in forbidden:
                forbidden.append(field)
        updated["forbidden_as_labeler_visible"] = forbidden
        if decision["row_gap_decision"] == "replacement_needed":
            excluded_rows.append(updated)
        else:
            ready_rows.append(updated)
    return ready_rows, excluded_rows


def path_errors(rows: list[dict[str, Any]], output_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(field) or "")
            if not value:
                errors.append({"row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "error": "empty_path"})
                continue
            path = Path(value)
            resolved = path if path.is_absolute() else output_dir / path
            if not resolved.exists():
                errors.append({"row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "path": value, "error": "missing_path"})
    return errors


def visible_leakage_hits(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in fields:
        lower = field.lower()
        for token in VISIBLE_FORBIDDEN_TOKENS:
            if token in lower:
                hits.append({"surface": "field_name", "field": field, "forbidden_token": token})
    for row_number, row in enumerate(rows, start=2):
        for field, value in row.items():
            if field in {"packet_gap_decision", "packet_gap_reason"}:
                continue
            lower = str(value).lower()
            for token in VISIBLE_FORBIDDEN_TOKENS:
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


def validate_inputs(packet_summary: dict[str, Any], label_rows: list[dict[str, Any]], manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if packet_summary.get("next_todo") != "reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit":
        errors.append({"error": "unexpected_next_todo", "value": packet_summary.get("next_todo")})
    if packet_summary.get("status") != "h002_reliability_target_v7_object_cell_evidence_contrast_asset_packets_partial_needs_gap_audit":
        errors.append({"error": "unexpected_packet_status", "value": packet_summary.get("status")})
    boundary = packet_summary.get("boundary") or {}
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error": f"boundary_{key}_not_false", "value": boundary.get(key)})
    if len(label_rows) != packet_summary.get("counts", {}).get("full_label_sheet_rows"):
        errors.append({"error": "label_row_count_mismatch", "actual": len(label_rows), "summary": packet_summary.get("counts", {}).get("full_label_sheet_rows")})
    if len(manifests) != len(label_rows):
        errors.append({"error": "manifest_label_count_mismatch", "manifest": len(manifests), "label_rows": len(label_rows)})
    return errors


def bucket_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        counts[(str(row.get("predicate_family")), str(row.get("semantic_geometry_bucket_hidden")), str(row.get("row_gap_decision")))] += 1
    output: list[dict[str, Any]] = []
    for (family, bucket, decision), count in sorted(counts.items()):
        output.append({"predicate_family": family, "semantic_geometry_bucket_hidden": bucket, "row_gap_decision": decision, "rows": count})
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V7 Object-Cell Evidence Contrast Asset Packet Gap Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage audit.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- This decides packet usability before v7 label readiness.",
        "- Rows with generic missing endpoints or both endpoint crops missing are replacement-needed.",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next = {summary['next_todo']}",
        "```",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| input rows | {summary['counts']['input_rows']} |",
        f"| label-ready rows | {summary['counts']['label_ready_rows']} |",
        f"| excluded rows | {summary['counts']['excluded_rows']} |",
        f"| limited-view rows kept | {summary['counts']['limited_view_rows_kept']} |",
        f"| geometry-only rows kept | {summary['counts']['geometry_only_rows_kept']} |",
        f"| replacement-needed rows | {summary['counts']['replacement_needed_rows']} |",
        f"| output path errors | {summary['validation']['output_path_errors']} |",
        f"| visible leakage hits | {summary['validation']['visible_leakage_hits']} |",
        f"| input validation errors | {summary['validation']['input_validation_errors']} |",
        "",
        "## Row Decisions",
        "",
        "| Decision | Rows |",
        "| --- | ---: |",
    ]
    for key, value in summary["row_decision_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Ready Balance", "", "```text"])
    lines.append(f"ready_family_counts = {summary['counts']['ready_family_counts']}")
    lines.append(f"ready_bucket_counts = {summary['counts']['ready_bucket_counts']}")
    lines.append(f"ready_family_bucket_counts = {summary['counts']['ready_family_bucket_counts']}")
    lines.extend(["```", "", "## Decision", "", summary["decision"], "", "## Next TODO", "", "```text", summary["next_todo"], "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    packet_summary = read_json(args.packet_summary)
    label_rows = read_tsv(args.full_label_sheet)
    manifests = read_jsonl(args.full_manifest)
    generated_packets = read_jsonl(args.generated_packet_manifest)
    input_errors = validate_inputs(packet_summary, label_rows, manifests)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    packet_by_id = {str(row["blind_review_id"]): row for row in generated_packets}
    row_decisions: list[dict[str, Any]] = []
    for manifest in manifests:
        blind_id = str(manifest["blind_review_id"])
        packet_row = packet_by_id.get(blind_id) or synthetic_ready_packet(manifest)
        row_decisions.append(decide_row(packet_row, manifest))

    row_by_id = {str(row["blind_review_id"]): row for row in row_decisions}
    ready_label_rows, excluded_label_rows = label_sheet_rows(label_rows, row_by_id, output_dir, PACKET_DIR)
    ready_manifest_rows, excluded_manifest_rows = manifest_rows(manifests, row_by_id)
    fieldnames = list(ready_label_rows[0].keys()) if ready_label_rows else list(label_rows[0].keys())
    output_errors = path_errors(ready_label_rows, output_dir)
    leakage_hits = visible_leakage_hits(ready_label_rows, fieldnames)

    ready_family_counts = Counter(str(row.get("predicate_family")) for row in ready_manifest_rows)
    ready_bucket_counts = Counter(str(row.get("semantic_geometry_bucket_hidden")) for row in ready_manifest_rows)
    ready_family_bucket_counts = Counter(f"{row.get('predicate_family')}|{row.get('semantic_geometry_bucket_hidden')}" for row in ready_manifest_rows)
    excluded_family_bucket_counts = Counter(f"{row.get('predicate_family')}|{row.get('semantic_geometry_bucket_hidden')}" for row in excluded_manifest_rows)
    replacement_requests = [
        {
            "replacement_request_reason": "v7_object_cell_evidence_contrast_row_excluded_by_asset_gap_audit",
            "blind_review_id": row.get("blind_review_id"),
            "predicate_family": row.get("predicate_family"),
            "predicate_label": row.get("predicate_label"),
            "semantic_geometry_bucket_hidden": row.get("semantic_geometry_bucket_hidden"),
            "strict_group_key_hidden": row.get("strict_group_key_hidden"),
            "subject_object_family_cell_hidden": row.get("subject_object_family_cell_hidden"),
            "subject_object_label_pair_hidden": row.get("subject_object_label_pair_hidden"),
            "row_gap_reason": row.get("row_gap_reason"),
        }
        for row in row_decisions
        if row.get("row_gap_decision") == "replacement_needed"
    ]
    bucket_rows = bucket_summary_rows(row_decisions)

    status = (
        "h002_reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit_ready_for_label_readiness"
        if len(ready_label_rows) == len(label_rows) and not output_errors and not leakage_hits and not input_errors
        else "h002_reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit_needs_replacement"
    )
    next_todo = (
        "reliability_target_v7_object_cell_evidence_contrast_label_readiness"
        if status == "h002_reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit_ready_for_label_readiness"
        else "reliability_target_v7_object_cell_evidence_contrast_replacement_mining"
    )
    decision = (
        "Proceed to label readiness with the full 240-row queue; partial rows are kept with explicit limited-view evidence caveats."
        if status == "h002_reliability_target_v7_object_cell_evidence_contrast_asset_packet_gap_audit_ready_for_label_readiness"
        else "Do not proceed to label fill: replacement rows are needed to restore the fixed 240-row object-cell contrast queue without weak endpoint evidence."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "row_gap_decisions": output_dir / "row_gap_decisions.jsonl",
        "partial_row_decisions": output_dir / "partial_row_decisions.jsonl",
        "bucket_gap_summary": output_dir / "bucket_gap_summary.csv",
        "label_ready_partial_label_sheet": output_dir / "label_ready_partial_label_sheet.tsv",
        "label_ready_partial_manifest_post_label_only": output_dir / "label_ready_partial_manifest_post_label_only.jsonl",
        "excluded_rows": output_dir / "excluded_rows.jsonl",
        "excluded_blind_ids": output_dir / "excluded_blind_ids.txt",
        "replacement_request_plan": output_dir / "replacement_request_plan.jsonl",
        "output_path_errors": output_dir / "output_path_errors.jsonl",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "input_validation_errors": output_dir / "input_validation_errors.jsonl",
        "packets_dir": output_dir / "packets",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": {
            "packet_summary": rel_path(args.packet_summary),
            "full_label_sheet": rel_path(args.full_label_sheet),
            "full_manifest": rel_path(args.full_manifest),
            "generated_packet_manifest": rel_path(args.generated_packet_manifest),
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
            "input_rows": len(label_rows),
            "label_ready_rows": len(ready_label_rows),
            "excluded_rows": len(excluded_label_rows),
            "limited_view_rows_kept": sum(1 for row in ready_label_rows if row.get("packet_gap_decision") == "limited_view_evaluable"),
            "geometry_only_rows_kept": sum(1 for row in ready_label_rows if row.get("packet_gap_decision") == "geometry_only_evaluable"),
            "replacement_needed_rows": sum(1 for row in row_decisions if row.get("row_gap_decision") == "replacement_needed"),
            "ready_family_counts": dict(sorted(ready_family_counts.items())),
            "ready_bucket_counts": dict(sorted(ready_bucket_counts.items())),
            "ready_family_bucket_counts": dict(sorted(ready_family_bucket_counts.items())),
            "excluded_family_bucket_counts": dict(sorted(excluded_family_bucket_counts.items())),
        },
        "row_decision_counts": dict(sorted(Counter(row["row_gap_decision"] for row in row_decisions).items())),
        "evidence_status_counts": dict(sorted(Counter(row["evidence_packet_status"] for row in ready_label_rows).items())),
        "validation": {
            "output_path_errors": len(output_errors),
            "visible_leakage_hits": len(leakage_hits),
            "input_validation_errors": len(input_errors),
        },
    }

    write_jsonl(output_paths["row_gap_decisions"], row_decisions)
    write_jsonl(output_paths["partial_row_decisions"], [row for row in row_decisions if row["packet_status"] != "ready"])
    write_csv(output_paths["bucket_gap_summary"], bucket_rows)
    write_tsv(output_paths["label_ready_partial_label_sheet"], ready_label_rows, fieldnames)
    write_jsonl(output_paths["label_ready_partial_manifest_post_label_only"], ready_manifest_rows)
    write_jsonl(output_paths["excluded_rows"], excluded_manifest_rows)
    output_paths["excluded_blind_ids"].write_text(
        "\n".join(str(row.get("blind_review_id")) for row in excluded_manifest_rows) + ("\n" if excluded_manifest_rows else ""),
        encoding="utf-8",
    )
    write_jsonl(output_paths["replacement_request_plan"], replacement_requests)
    write_jsonl(output_paths["output_path_errors"], output_errors)
    write_jsonl(output_paths["visible_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["input_validation_errors"], input_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        f"status={summary['status']} "
        f"rows={summary['counts']['input_rows']} "
        f"label_ready_rows={summary['counts']['label_ready_rows']} "
        f"excluded_rows={summary['counts']['excluded_rows']} "
        f"limited_view={summary['counts']['limited_view_rows_kept']} "
        f"geometry_only={summary['counts']['geometry_only_rows_kept']} "
        f"path_errors={summary['validation']['output_path_errors']} "
        f"leakage={summary['validation']['visible_leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
