#!/usr/bin/env python3
"""Audit v5 cell-contrast partial asset packets before label fill."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

PACKET_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_asset_packets"
DEFAULT_PACKET_SUMMARY = PACKET_DIR / "summary.json"
DEFAULT_FULL_LABEL_SHEET = PACKET_DIR / "cell_contrast_full_label_sheet.tsv"
DEFAULT_FULL_MANIFEST = PACKET_DIR / "cell_contrast_full_manifest_post_label_only.jsonl"
DEFAULT_GENERATED_PACKET_MANIFEST = PACKET_DIR / "generated_packet_manifest.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_asset_packet_gap_audit"

SCHEMA_VERSION = "h002_reliability_target_v5_cell_contrast_asset_packet_gap_audit_v1"
GENERIC_ENDPOINT_LABELS = {"object", "objects", "item", "items", "clutter", "unknown"}
VISIBLE_FORBIDDEN_TOKENS = [
    "anchor_category",
    "candidate_proxy",
    "cell_contrast",
    "contrast_role",
    "endpoint_flag_pattern",
    "geometry_status",
    "hidden",
    "label_match",
    "p_geom",
    "proxy",
    "queue_kind",
    "rank_band",
    "semantic_rank",
    "semantic_score",
    "source_queue",
    "stratum",
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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
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


def decide_row(packet_row: dict[str, Any], manifest_row: dict[str, Any]) -> dict[str, Any]:
    status = str(packet_row.get("packet_status") or manifest_row.get("evidence_packet_status") or "")
    sides = missing_sides(packet_row) if packet_row else []
    contact_ready = bool(packet_row.get("contact_sheet_ready", status == "ready"))
    mesh_ready = bool(packet_row.get("mesh_packet_ready", status == "ready"))
    family = str(manifest_row.get("predicate_family") or packet_row.get("predicate_family") or "")

    if status == "ready":
        decision = "label_ready"
        reason = "complete packet"
    elif len(sides) >= 2:
        decision = "replacement_needed"
        reason = "both endpoint crops are missing"
    elif has_generic_missing_endpoint(packet_row, sides):
        decision = "replacement_needed"
        reason = "missing endpoint has generic object label, so endpoint identity cannot be checked independently"
    elif mesh_ready and contact_ready and len(sides) == 1:
        decision = "limited_view_evaluable"
        reason = "one endpoint crop is missing, but mesh packet and contact/context sheet are available"
    elif mesh_ready and family == "relative_vertical" and len(sides) == 1:
        decision = "limited_view_evaluable"
        reason = "one endpoint crop is missing, but relative vertical ordering can still be audited from mesh"
    else:
        decision = "replacement_needed"
        reason = "insufficient packet evidence for independent label fill"

    return {
        "blind_review_id": manifest_row.get("blind_review_id") or packet_row.get("blind_review_id"),
        "cell_contrast_pair_id_hidden": manifest_row.get("cell_contrast_pair_id_hidden"),
        "cell_contrast_role_hidden": manifest_row.get("cell_contrast_role_hidden"),
        "predicate_family": family,
        "predicate_label": manifest_row.get("predicate_label") or packet_row.get("predicate_label"),
        "subject_label": manifest_row.get("subject_label") or packet_row.get("subject_label"),
        "object_label": manifest_row.get("object_label") or packet_row.get("object_label"),
        "packet_status": status,
        "row_gap_decision": decision,
        "row_gap_reason": reason,
        "missing_sides": sides,
        "subject_image_count": packet_row.get("subject_image_count") if packet_row else "",
        "object_image_count": packet_row.get("object_image_count") if packet_row else "",
        "contact_sheet_ready": contact_ready,
        "mesh_packet_ready": mesh_ready,
        "scan_id": manifest_row.get("scan_id") or packet_row.get("scan_id"),
        "scene_context_id": manifest_row.get("scene_context_id"),
        "subject_id": manifest_row.get("subject_id") or packet_row.get("subject_id"),
        "object_id": manifest_row.get("object_id") or packet_row.get("object_id"),
    }


def pair_decisions(row_decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in row_decisions:
        by_pair[str(row["cell_contrast_pair_id_hidden"])].append(row)

    output: dict[str, dict[str, Any]] = {}
    for pair_id, rows in by_pair.items():
        row_decision_set = {row["row_gap_decision"] for row in rows}
        if "replacement_needed" in row_decision_set:
            decision = "exclude_pair_before_label_fill"
            reason = "at least one row in the cell-contrast pair needs replacement"
        elif "limited_view_evaluable" in row_decision_set:
            decision = "pair_ready_with_limited_view_caveat"
            reason = "pair is usable, but at least one row has one missing endpoint crop"
        else:
            decision = "pair_ready"
            reason = "both rows have complete packet evidence"
        output[pair_id] = {
            "cell_contrast_pair_id_hidden": pair_id,
            "pair_gap_decision": decision,
            "pair_gap_reason": reason,
            "rows": len(rows),
            "positive_proxy_rows": sum(1 for row in rows if row.get("cell_contrast_role_hidden") == "positive_proxy"),
            "negative_proxy_rows": sum(1 for row in rows if row.get("cell_contrast_role_hidden") == "negative_proxy"),
            "limited_view_rows": sum(1 for row in rows if row.get("row_gap_decision") == "limited_view_evaluable"),
            "replacement_needed_rows": sum(1 for row in rows if row.get("row_gap_decision") == "replacement_needed"),
            "predicate_family": rows[0].get("predicate_family"),
            "predicate_label": rows[0].get("predicate_label"),
        }
    return output


def materialize_packet(row: dict[str, Any], output_dir: Path, packet_dir: Path) -> dict[str, str]:
    blind_id = str(row["blind_review_id"])
    dest_dir = output_dir / "packets" / blind_id
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    output_paths: dict[str, str] = {}
    for field, filename in [
        ("multiview_packet", "packet.md"),
        ("pointcloud_or_mesh_packet", "mesh_packet.md"),
        ("contact_or_context_sheet", "contact_context_sheet.jpg"),
    ]:
        value = str(row.get(field) or "")
        if not value:
            continue
        src = resolve_packet_path(value, packet_dir)
        dest = dest_dir / filename
        if src.exists() and src.is_file():
            shutil.copy2(src, dest)
            if dest.suffix == ".md":
                text = dest.read_text(encoding="utf-8")
                lines = []
                for line in text.splitlines():
                    if line.startswith("Blind review id:"):
                        lines.append(f"Blind review id: `{blind_id}`")
                    else:
                        lines.append(line)
                dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
            output_paths[field] = f"packets/{blind_id}/{filename}"
    return output_paths


def label_sheet_rows(
    label_rows: list[dict[str, Any]],
    row_decisions_by_id: dict[str, dict[str, Any]],
    pair_decisions_by_id: dict[str, dict[str, Any]],
    output_dir: Path,
    packet_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for row in label_rows:
        blind_id = str(row.get("blind_review_id"))
        row_decision = row_decisions_by_id[blind_id]
        pair_decision = pair_decisions_by_id[str(row_decision["cell_contrast_pair_id_hidden"])]
        updated = dict(row)
        updated["packet_gap_decision"] = row_decision["row_gap_decision"]
        updated["packet_gap_reason"] = row_decision["row_gap_reason"]
        if pair_decision["pair_gap_decision"] == "exclude_pair_before_label_fill":
            updated["evidence_packet_status"] = "pair_replacement_needed"
            excluded_rows.append(updated)
            continue
        if row_decision["row_gap_decision"] == "limited_view_evaluable":
            updated["evidence_packet_status"] = "limited_view_evaluable"
        else:
            updated["evidence_packet_status"] = "ready"
        updated.update(materialize_packet(updated, output_dir, packet_dir))
        ready_rows.append(updated)
    return ready_rows, excluded_rows


def manifest_rows(
    manifests: list[dict[str, Any]],
    row_decisions_by_id: dict[str, dict[str, Any]],
    pair_decisions_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for row in manifests:
        blind_id = str(row.get("blind_review_id"))
        row_decision = row_decisions_by_id[blind_id]
        pair_decision = pair_decisions_by_id[str(row_decision["cell_contrast_pair_id_hidden"])]
        updated = dict(row)
        updated["row_gap_decision_hidden"] = row_decision["row_gap_decision"]
        updated["row_gap_reason_hidden"] = row_decision["row_gap_reason"]
        updated["pair_gap_decision_hidden"] = pair_decision["pair_gap_decision"]
        updated["pair_gap_reason_hidden"] = pair_decision["pair_gap_reason"]
        forbidden = list(updated.get("forbidden_as_labeler_visible") or [])
        for field in [
            "row_gap_decision_hidden",
            "row_gap_reason_hidden",
            "pair_gap_decision_hidden",
            "pair_gap_reason_hidden",
        ]:
            if field not in forbidden:
                forbidden.append(field)
        updated["forbidden_as_labeler_visible"] = forbidden
        if pair_decision["pair_gap_decision"] == "exclude_pair_before_label_fill":
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
    if packet_summary.get("next_todo") != "reliability_target_v5_cell_contrast_asset_packet_gap_audit":
        errors.append({"error": "unexpected_next_todo", "value": packet_summary.get("next_todo")})
    if packet_summary.get("status") != "h002_reliability_target_v5_cell_contrast_asset_packets_partial":
        errors.append({"error": "unexpected_packet_status", "value": packet_summary.get("status")})
    boundary = packet_summary.get("boundary") or {}
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error": f"boundary_{key}_not_false", "value": boundary.get(key)})
    if len(label_rows) != packet_summary.get("counts", {}).get("full_label_sheet_rows"):
        errors.append({"error": "label_row_count_mismatch", "actual": len(label_rows), "summary": packet_summary.get("counts", {}).get("full_label_sheet_rows")})
    if len(manifests) != len(label_rows):
        errors.append({"error": "manifest_label_count_mismatch", "manifest": len(manifests), "label_rows": len(label_rows)})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Reliability Target V5 Cell Contrast Asset Packet Gap Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage audit.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- This decides packet usability before v5 label fill.",
        "- Pair integrity is preserved: if one row needs replacement, the whole cell-contrast pair is excluded.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| input rows | {summary['counts']['input_rows']} |",
        f"| input pairs | {summary['counts']['input_pairs']} |",
        f"| label-ready rows | {summary['counts']['label_ready_rows']} |",
        f"| label-ready pairs | {summary['counts']['label_ready_pairs']} |",
        f"| excluded rows | {summary['counts']['excluded_rows']} |",
        f"| excluded pairs | {summary['counts']['excluded_pairs']} |",
        f"| limited-view rows kept | {summary['counts']['limited_view_rows_kept']} |",
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
    lines.extend(["", "## Pair Decisions", "", "| Decision | Pairs |", "| --- | ---: |"])
    for key, value in summary["pair_decision_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Excluded Pairs", "", "| Pair | Reason |", "| --- | --- |"])
    for row in summary["excluded_pair_decisions"]:
        lines.append(f"| `{row['cell_contrast_pair_id_hidden']}` | {row['pair_gap_reason']} |")
    lines.extend(["", "## Next TODO", "", "```text", summary["next_todo"], "```", ""])
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
    manifest_by_id = {str(row["blind_review_id"]): row for row in manifests}

    row_decisions: list[dict[str, Any]] = []
    for manifest in manifests:
        blind_id = str(manifest["blind_review_id"])
        packet_row = packet_by_id.get(blind_id)
        if packet_row is None:
            packet_row = {
                "blind_review_id": blind_id,
                "packet_status": manifest.get("evidence_packet_status", "ready"),
                "subject_image_count": 1,
                "object_image_count": 1,
                "contact_sheet_ready": True,
                "mesh_packet_ready": True,
            }
        row_decisions.append(decide_row(packet_row, manifest))

    pair_by_id = pair_decisions(row_decisions)
    row_by_id = {str(row["blind_review_id"]): row for row in row_decisions}
    ready_label_rows, excluded_label_rows = label_sheet_rows(label_rows, row_by_id, pair_by_id, output_dir, PACKET_DIR)
    ready_manifest_rows, excluded_manifest_rows = manifest_rows(manifests, row_by_id, pair_by_id)
    output_errors = path_errors(ready_label_rows, output_dir)
    fieldnames = list(ready_label_rows[0].keys()) if ready_label_rows else list(label_rows[0].keys())
    leakage_hits = visible_leakage_hits(ready_label_rows, fieldnames)

    pair_rows = list(pair_by_id.values())
    ready_pairs = [row for row in pair_rows if row["pair_gap_decision"] != "exclude_pair_before_label_fill"]
    excluded_pairs = [row for row in pair_rows if row["pair_gap_decision"] == "exclude_pair_before_label_fill"]
    replacement_requests = [
        {
            "replacement_request_reason": "v5_cell_contrast_pair_excluded_by_asset_gap_audit",
            "cell_contrast_pair_id_hidden": pair["cell_contrast_pair_id_hidden"],
            "predicate_family": pair["predicate_family"],
            "predicate_label": pair["predicate_label"],
            "pair_gap_reason": pair["pair_gap_reason"],
        }
        for pair in excluded_pairs
    ]
    role_counts = Counter(
        str(manifest_by_id[str(row["blind_review_id"])].get("cell_contrast_role_hidden"))
        for row in ready_manifest_rows
    )
    family_counts = Counter(str(row.get("predicate_family")) for row in ready_manifest_rows)
    status = (
        "h002_reliability_target_v5_cell_contrast_asset_packet_gap_audit_ready_for_label_readiness"
        if len(ready_pairs) >= 20
        and role_counts.get("positive_proxy", 0) == role_counts.get("negative_proxy", 0)
        and not output_errors
        and not leakage_hits
        and not input_errors
        else "h002_reliability_target_v5_cell_contrast_asset_packet_gap_audit_needs_replacement"
    )
    next_todo = (
        "reliability_target_v5_cell_contrast_label_readiness"
        if status == "h002_reliability_target_v5_cell_contrast_asset_packet_gap_audit_ready_for_label_readiness"
        else "reliability_target_v5_cell_contrast_replacement_mining"
    )
    decision = (
        "Proceed with label-ready cell-contrast pairs while keeping replacement-needed pairs out of label fill."
        if status == "h002_reliability_target_v5_cell_contrast_asset_packet_gap_audit_ready_for_label_readiness"
        else "Do not proceed to label fill until replacement pairs are mined."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "row_gap_decisions": output_dir / "row_gap_decisions.jsonl",
        "partial_row_decisions": output_dir / "partial_row_decisions.jsonl",
        "pair_gap_decisions": output_dir / "pair_gap_decisions.csv",
        "label_ready_full_label_sheet": output_dir / "label_ready_full_label_sheet.tsv",
        "label_ready_full_manifest_post_label_only": output_dir / "label_ready_full_manifest_post_label_only.jsonl",
        "excluded_pair_rows": output_dir / "excluded_pair_rows.jsonl",
        "excluded_pair_ids": output_dir / "excluded_pair_ids.txt",
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
            "cell_contrast_roles_visible_to_labeler": False,
        },
        "counts": {
            "input_rows": len(label_rows),
            "input_pairs": len(pair_rows),
            "label_ready_rows": len(ready_label_rows),
            "label_ready_pairs": len(ready_pairs),
            "excluded_rows": len(excluded_label_rows),
            "excluded_pairs": len(excluded_pairs),
            "limited_view_rows_kept": sum(1 for row in ready_label_rows if row.get("packet_gap_decision") == "limited_view_evaluable"),
            "replacement_needed_rows": sum(1 for row in row_decisions if row.get("row_gap_decision") == "replacement_needed"),
            "ready_role_counts_hidden": dict(sorted(role_counts.items())),
            "ready_family_counts": dict(sorted(family_counts.items())),
        },
        "row_decision_counts": dict(sorted(Counter(row["row_gap_decision"] for row in row_decisions).items())),
        "pair_decision_counts": dict(sorted(Counter(row["pair_gap_decision"] for row in pair_rows).items())),
        "excluded_pair_decisions": excluded_pairs,
        "validation": {
            "output_path_errors": len(output_errors),
            "visible_leakage_hits": len(leakage_hits),
            "input_validation_errors": len(input_errors),
            "role_balance_after_gap_audit": dict(sorted(role_counts.items())),
        },
    }

    write_jsonl(output_paths["row_gap_decisions"], row_decisions)
    write_jsonl(output_paths["partial_row_decisions"], [row for row in row_decisions if row["packet_status"] != "ready"])
    write_csv(output_paths["pair_gap_decisions"], pair_rows)
    write_tsv(output_paths["label_ready_full_label_sheet"], ready_label_rows, fieldnames)
    write_jsonl(output_paths["label_ready_full_manifest_post_label_only"], ready_manifest_rows)
    write_jsonl(output_paths["excluded_pair_rows"], excluded_manifest_rows)
    output_paths["excluded_pair_ids"].write_text(
        "\n".join(row["cell_contrast_pair_id_hidden"] for row in excluded_pairs) + ("\n" if excluded_pairs else ""),
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
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} "
        f"rows={summary['counts']['input_rows']} "
        f"label_ready_rows={summary['counts']['label_ready_rows']} "
        f"label_ready_pairs={summary['counts']['label_ready_pairs']} "
        f"excluded_pairs={summary['counts']['excluded_pairs']} "
        f"limited_view={summary['counts']['limited_view_rows_kept']} "
        f"path_errors={summary['validation']['output_path_errors']} "
        f"leakage={summary['validation']['visible_leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
