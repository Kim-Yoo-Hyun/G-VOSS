#!/usr/bin/env python3
"""Validate label readiness for the restored H002 v8 repair batch."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v8_endpoint_pair_counterfactual_target_repair_and_additional_mining as repair


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

PACKET_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_replacement_asset_packets_codex_proxy_user_requested"
DEFAULT_PACKET_SUMMARY = PACKET_DIR / "summary.json"
DEFAULT_LABEL_SHEET = PACKET_DIR / "repair_replacement_full_label_sheet.tsv"
DEFAULT_MANIFEST = PACKET_DIR / "repair_replacement_full_manifest_post_label_only.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_label_readiness_codex_proxy_user_requested"

SCHEMA_VERSION = "h002_reliability_target_v8_endpoint_pair_counterfactual_repair_label_readiness_v1"
EXPECTED_PACKET_STATUS = "h002_reliability_target_v8_repair_replacement_asset_packets_ready_for_label_readiness"
EXPECTED_NEXT_TODO = "reliability_target_v8_endpoint_pair_counterfactual_repair_label_readiness"
REVIEW_SCOPE = "h002_reliability_v8_endpoint_pair_counterfactual_repair_label_ready_review"
EXPECTED_COLUMNS = repair.VISIBLE_FIELDS
REVIEW_FIELDS = repair.REVIEW_FIELDS
EXPECTED_PREDICATE_COUNTS = {
    "higher than": 60,
    "lower than": 60,
    "standing on": 40,
    "lying on": 40,
}
EXPECTED_ROLE_COUNTS = {
    "vertical_direction_counterfactual": 120,
    "support_pose_counterfactual": 80,
}
EXPECTED_FAMILY_COUNTS = {
    "relative_vertical": 120,
    "support_contact": 80,
}

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
    "object_family_cell",
    "subject_object_family_cell",
    "label_match",
    "machine_hint",
    "h001_verification",
]
FORBIDDEN_VISIBLE_VALUE_TOKENS = [token for token in FORBIDDEN_VISIBLE_FIELD_TOKENS if token != "hidden"]
FORBIDDEN_PACKET_TEXT_TOKENS = [
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
    parser.add_argument("--packet-summary", type=Path, default=DEFAULT_PACKET_SUMMARY)
    parser.add_argument("--label-sheet", type=Path, default=DEFAULT_LABEL_SHEET)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def resolve_packet_path(value: str, input_base: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    repo_candidate = as_abs(path)
    if repo_candidate.exists():
        return repo_candidate
    return input_base / path


def rewrite_blind_id(path: Path, blind_id: str) -> None:
    if path.suffix != ".md" or not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = []
    for line in text.splitlines():
        if line.startswith("Blind review id:"):
            lines.append(f"Blind review id: `{blind_id}`")
        else:
            lines.append(line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def materialize_packet_paths(manifest: dict[str, Any], output_dir: Path, input_base: Path) -> tuple[dict[str, str], list[dict[str, Any]]]:
    blind_id = str(manifest["blind_review_id"])
    dest_dir = output_dir / "packets" / blind_id
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    output_paths: dict[str, str] = {}
    filename_by_field = {
        "multiview_packet": "packet.md",
        "pointcloud_or_mesh_packet": "mesh_packet.md",
    }

    for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
        value = str(manifest.get(field) or "")
        if not value:
            errors.append({"blind_review_id": blind_id, "field": field, "error_type": "empty_source_packet_path"})
            continue
        source = resolve_packet_path(value, input_base)
        if not source.exists() or not source.is_file():
            errors.append({"blind_review_id": blind_id, "field": field, "path": value, "error_type": "source_packet_path_missing"})
            continue
        if field == "contact_or_context_sheet":
            filename = "geometry_only_context.md" if source.suffix == ".md" else "contact_context_sheet.jpg"
        else:
            filename = filename_by_field[field]
        dest = dest_dir / filename
        shutil.copy2(source, dest)
        rewrite_blind_id(dest, blind_id)
        output_paths[field] = f"packets/{blind_id}/{filename}"
    return output_paths, errors


def validate_inputs(summary: dict[str, Any], fieldnames: list[str], label_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_PACKET_STATUS:
        errors.append({"error_type": "unexpected_packet_status", "expected": EXPECTED_PACKET_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": summary.get("next_todo")})
    boundary = summary.get("boundary") or {}
    for key in [
        "validation_usage",
        "test_usage",
        "labels_filled",
        "posterior_trained",
        "posterior_smoke_allowed",
        "multi_view_as_model_input",
        "h001_artifacts_modified",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": f"boundary_{key}_not_false", "actual": boundary.get(key)})
    counts = summary.get("counts") or {}
    if len(label_rows) != counts.get("full_label_sheet_rows"):
        errors.append({"error_type": "label_row_count_mismatch", "expected": counts.get("full_label_sheet_rows"), "actual": len(label_rows)})
    if len(manifest_rows) != counts.get("full_manifest_rows"):
        errors.append({"error_type": "manifest_row_count_mismatch", "expected": counts.get("full_manifest_rows"), "actual": len(manifest_rows)})
    if len(label_rows) != len(manifest_rows):
        errors.append({"error_type": "label_manifest_row_count_mismatch", "labels": len(label_rows), "manifests": len(manifest_rows)})
    if fieldnames != EXPECTED_COLUMNS:
        errors.append({"error_type": "unexpected_header", "expected": EXPECTED_COLUMNS, "actual": fieldnames})
    return errors


def normalize_rows(
    label_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, Any]],
    output_dir: Path,
    input_base: Path,
) -> tuple[list[dict[str, str]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_by_id = {str(row.get("blind_review_id")): row for row in manifest_rows}
    normalized_labels: list[dict[str, str]] = []
    normalized_manifests: list[dict[str, Any]] = []
    materialize_errors: list[dict[str, Any]] = []
    readiness_rows: list[dict[str, Any]] = []

    for row_number, row in enumerate(label_rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        manifest = manifest_by_id.get(blind_id)
        if manifest is None:
            materialize_errors.append({"row_number": row_number, "blind_review_id": blind_id, "error_type": "missing_manifest"})
            continue
        paths, errors = materialize_packet_paths(manifest, output_dir, input_base)
        materialize_errors.extend({"row_number": row_number, **error} for error in errors)

        label = dict(row)
        label["review_scope"] = REVIEW_SCOPE
        label["evidence_packet_status"] = "ready"
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            label[field] = paths.get(field, "")
        for field in REVIEW_FIELDS:
            label[field] = ""
        normalized_labels.append({field: str(label.get(field, "")) for field in EXPECTED_COLUMNS})

        manifest_updated = dict(manifest)
        manifest_updated.update(paths)
        manifest_updated["review_scope"] = REVIEW_SCOPE
        manifest_updated["label_readiness_status_hidden"] = "ready_for_label_fill"
        manifest_updated["label_fill_allowed"] = True
        manifest_updated["posterior_input_allowed"] = False
        forbidden = set(str(field) for field in (manifest_updated.get("forbidden_as_labeler_visible") or []))
        forbidden.update(
            {
                "label_readiness_status_hidden",
                "label_geometry_bucket_hidden",
                "geometry_status_hidden",
                "source_queue_hidden",
                "rank_band_hidden",
                "exact_endpoint_pair_key_hidden",
                "counterfactual_pair_id_hidden",
                "semantic_score_norm_hidden",
                "semantic_score_raw_hidden",
                "semantic_rank_hidden",
                "p_geom_valid_hidden",
                "subject_object_family_cell_hidden",
                "subject_object_label_pair_hidden",
                "machine_hint_hidden",
                "label_match_status_hidden",
                "h001_verification_status_hidden",
            }
        )
        manifest_updated["forbidden_as_labeler_visible"] = sorted(forbidden)
        normalized_manifests.append(manifest_updated)
        readiness_rows.append(
            {
                "blind_review_id": blind_id,
                "predicate_family": manifest.get("predicate_family"),
                "predicate_label": manifest.get("predicate_label"),
                "additional_batch_role_hidden": manifest.get("additional_batch_role_hidden"),
                "label_geometry_bucket_hidden": manifest.get("label_geometry_bucket_hidden"),
                "packet_status_hidden": manifest.get("packet_status_hidden"),
                "label_readiness_status_hidden": "ready_for_label_fill",
                "source_batch": manifest.get("batch_name"),
            }
        )
    return normalized_labels, normalized_manifests, materialize_errors, readiness_rows


def forbidden_header_hits(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    allowed = {"endpoint_pair_note"}
    for field in fieldnames:
        if field in allowed:
            continue
        lower = field.lower()
        for token in FORBIDDEN_VISIBLE_FIELD_TOKENS:
            if token in lower:
                hits.append({"surface": "field_name", "field": field, "forbidden_token": token})
    return hits


def forbidden_value_hits(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    skip_fields = {"multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet", "endpoint_pair_note"}
    for row_number, row in enumerate(rows, start=2):
        for field, value in row.items():
            if field in skip_fields or field in REVIEW_FIELDS:
                continue
            lower = str(value).lower()
            for token in FORBIDDEN_VISIBLE_VALUE_TOKENS:
                if token in lower:
                    hits.append({"surface": "field_value", "row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "field": field, "forbidden_token": token})
                    break
    return hits


def packet_text_hits(rows: list[dict[str, str]], base_dir: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(field, ""))
            if not value:
                continue
            path = resolve_packet_path(value, base_dir)
            key = str(path)
            if key in seen or not path.exists() or not path.is_file() or path.suffix != ".md":
                continue
            seen.add(key)
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            for token in FORBIDDEN_PACKET_TEXT_TOKENS:
                if token in text:
                    hits.append({"surface": "packet_text", "path": rel_path(path), "forbidden_token": token})
                    break
    return hits


def row_path_errors(rows: list[dict[str, str]], base_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(field, ""))
            if not value:
                errors.append({"row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "field": field, "error_type": "empty_packet_path"})
                continue
            if not resolve_packet_path(value, base_dir).exists():
                errors.append({"row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "field": field, "value": value, "error_type": "packet_path_missing_on_disk"})
    return errors


def pair_structure_errors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("counterfactual_pair_id_hidden"))].append(row)
    for pair_id, pair_rows in grouped.items():
        predicates = sorted(str(row.get("predicate_label")) for row in pair_rows)
        roles = {str(row.get("additional_batch_role_hidden")) for row in pair_rows}
        if len(pair_rows) != 2:
            errors.append({"error_type": "pair_size_not_two", "pair_id": pair_id, "rows": len(pair_rows), "predicates": predicates})
            continue
        if roles == {"vertical_direction_counterfactual"} and predicates != ["higher than", "lower than"]:
            errors.append({"error_type": "vertical_pair_predicate_mismatch", "pair_id": pair_id, "predicates": predicates})
        if roles == {"support_pose_counterfactual"} and predicates != ["lying on", "standing on"]:
            errors.append({"error_type": "support_pair_predicate_mismatch", "pair_id": pair_id, "predicates": predicates})
        if len(roles) != 1:
            errors.append({"error_type": "mixed_pair_role", "pair_id": pair_id, "roles": sorted(roles), "predicates": predicates})
    return errors


def validate_ready_sheet(label_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]], base_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    label_ids = [row.get("blind_review_id", "") for row in label_rows]
    manifest_ids = [str(row.get("blind_review_id")) for row in manifest_rows]
    for blind_id, count in Counter(label_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_label_blind_id", "blind_review_id": blind_id, "count": count})
    if set(label_ids) != set(manifest_ids):
        errors.append({"error_type": "label_manifest_id_mismatch", "label_only": sorted(set(label_ids) - set(manifest_ids))[:10], "manifest_only": sorted(set(manifest_ids) - set(label_ids))[:10]})
    for row_number, row in enumerate(label_rows, start=2):
        for field in REVIEW_FIELDS:
            if str(row.get(field, "")).strip():
                errors.append({"error_type": "review_field_already_filled", "row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "field": field})
        if row.get("evidence_packet_status") != "ready":
            errors.append({"error_type": "unexpected_evidence_packet_status", "row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "value": row.get("evidence_packet_status")})
    errors.extend(pair_structure_errors(manifest_rows))

    hidden_audit_rows: list[dict[str, Any]] = []
    visible_fields = set(EXPECTED_COLUMNS)
    for manifest in manifest_rows:
        forbidden = set(str(field) for field in (manifest.get("forbidden_as_labeler_visible") or []))
        visible_forbidden = sorted(forbidden & visible_fields)
        if visible_forbidden:
            errors.append({"error_type": "forbidden_manifest_field_visible", "blind_review_id": manifest.get("blind_review_id"), "fields": visible_forbidden})
        hidden_audit_rows.append(
            {
                "blind_review_id": manifest.get("blind_review_id"),
                "forbidden_field_count": len(forbidden),
                "forbidden_fields_visible": len(visible_forbidden),
                "label_readiness_status_hidden": manifest.get("label_readiness_status_hidden"),
                "semantic_score_norm_hidden_present": "semantic_score_norm_hidden" in manifest,
                "p_geom_valid_hidden_present": "p_geom_valid_hidden" in manifest,
                "exact_endpoint_pair_key_hidden_present": "exact_endpoint_pair_key_hidden" in manifest,
            }
        )
    path_errors = row_path_errors(label_rows, base_dir)
    leakage_hits = forbidden_header_hits(EXPECTED_COLUMNS)
    leakage_hits.extend(forbidden_value_hits(label_rows))
    leakage_hits.extend(packet_text_hits(label_rows, base_dir))
    return errors, path_errors, leakage_hits, hidden_audit_rows


def label_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "visible_fields": EXPECTED_COLUMNS,
        "review_fields": REVIEW_FIELDS,
        "primary_target": "relation_reliability_state_v6",
        "primary_target_values": ["accept_reliable", "reject_unreliable", "abstain_uncertain"],
        "construction": "v8_repair_endpoint_pair_counterfactual",
        "predicate_balance": EXPECTED_PREDICATE_COUNTS,
        "role_balance": EXPECTED_ROLE_COUNTS,
        "all_rows_packet_ready": True,
        "semantic_geometry_bucket_is_not_target": True,
        "hidden_sampling_fields_are_not_label_targets": True,
        "endpoint_pair_group_is_not_labeler_visible": True,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V8 Repair Label Readiness",
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
        "```",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| label-ready rows | {summary['counts']['label_ready_rows']} |",
        f"| ready rows | {summary['counts']['ready_rows']} |",
        f"| exact endpoint pairs | {summary['counts']['exact_endpoint_pairs']} |",
        f"| counterfactual pairs | {summary['counts']['counterfactual_pairs']} |",
        f"| relative_vertical rows | {summary['counts']['family_counts'].get('relative_vertical', 0)} |",
        f"| support_contact rows | {summary['counts']['family_counts'].get('support_contact', 0)} |",
        f"| higher/lower rows | {summary['counts']['predicate_counts'].get('higher than', 0)} / {summary['counts']['predicate_counts'].get('lower than', 0)} |",
        f"| standing/lying rows | {summary['counts']['predicate_counts'].get('standing on', 0)} / {summary['counts']['predicate_counts'].get('lying on', 0)} |",
        "",
        "## Validation",
        "",
        "| Check | Errors |",
        "| --- | ---: |",
        f"| input validation | {summary['validation']['input_validation_errors']} |",
        f"| sheet validation | {summary['validation']['sheet_validation_errors']} |",
        f"| packet paths | {summary['validation']['packet_path_errors']} |",
        f"| leakage hits | {summary['validation']['leakage_hits']} |",
        f"| hidden field exposure | {summary['validation']['hidden_field_visibility_errors']} |",
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
    packet_summary = read_json(args.packet_summary)
    fieldnames, raw_label_rows = read_tsv(args.label_sheet)
    raw_manifest_rows = read_jsonl(args.manifest)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_errors = validate_inputs(packet_summary, fieldnames, raw_label_rows, raw_manifest_rows)
    label_rows, manifest_rows, materialize_errors, row_readiness = normalize_rows(
        raw_label_rows,
        raw_manifest_rows,
        output_dir,
        as_abs(args.label_sheet).parent,
    )
    sheet_errors, path_errors, leakage_hits, hidden_audit_rows = validate_ready_sheet(label_rows, manifest_rows, output_dir)
    path_errors.extend(materialize_errors)

    predicate_counts = Counter(str(row.get("predicate_label")) for row in manifest_rows)
    family_counts = Counter(str(row.get("predicate_family")) for row in manifest_rows)
    role_counts = Counter(str(row.get("additional_batch_role_hidden")) for row in manifest_rows)
    bucket_counts = Counter(str(row.get("label_geometry_bucket_hidden")) for row in manifest_rows)
    packet_status_counts = Counter(str(row.get("evidence_packet_status")) for row in label_rows)
    exact_pairs = {str(row.get("exact_endpoint_pair_key_hidden")) for row in manifest_rows}
    counterfactual_pairs = {str(row.get("counterfactual_pair_id_hidden")) for row in manifest_rows}
    hidden_field_visibility_errors = sum(row["forbidden_fields_visible"] for row in hidden_audit_rows)

    balance_ok = (
        dict(sorted(predicate_counts.items())) == EXPECTED_PREDICATE_COUNTS
        and dict(sorted(family_counts.items())) == EXPECTED_FAMILY_COUNTS
        and dict(sorted(role_counts.items())) == EXPECTED_ROLE_COUNTS
        and len(exact_pairs) == 100
        and len(counterfactual_pairs) == 100
        and packet_status_counts == Counter({"ready": 200})
    )
    if not balance_ok:
        sheet_errors.append(
            {
                "error_type": "balance_contract_failed",
                "predicate_counts": dict(sorted(predicate_counts.items())),
                "family_counts": dict(sorted(family_counts.items())),
                "role_counts": dict(sorted(role_counts.items())),
                "exact_pairs": len(exact_pairs),
                "counterfactual_pairs": len(counterfactual_pairs),
                "packet_status_counts": dict(sorted(packet_status_counts.items())),
            }
        )

    passes_contract = not input_errors and not sheet_errors and not path_errors and not leakage_hits and hidden_field_visibility_errors == 0
    status = (
        "h002_reliability_target_v8_repair_label_readiness_ready_for_label_fill"
        if passes_contract
        else "h002_reliability_target_v8_repair_label_readiness_blocked"
    )
    next_todo = (
        "reliability_target_v8_endpoint_pair_counterfactual_repair_label_fill"
        if passes_contract
        else "fix_reliability_target_v8_endpoint_pair_counterfactual_repair_label_readiness"
    )
    decision = (
        "The restored 200-row v8 repair sheet is label-ready. Proceed to label fill; posterior smoke remains blocked."
        if passes_contract
        else "The restored v8 repair sheet is blocked by readiness validation errors."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "ready_label_sheet": output_dir / "ready_label_sheet.tsv",
        "ready_manifest_post_label_only": output_dir / "ready_manifest_post_label_only.jsonl",
        "label_schema": output_dir / "label_schema.json",
        "row_readiness": output_dir / "row_readiness.csv",
        "hidden_field_audit": output_dir / "hidden_field_audit.jsonl",
        "input_validation_errors": output_dir / "input_validation_errors.jsonl",
        "sheet_validation_errors": output_dir / "sheet_validation_errors.jsonl",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "leakage_hits": output_dir / "leakage_hits.jsonl",
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
            "label_sheet": rel_path(args.label_sheet),
            "manifest": rel_path(args.manifest),
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
            "label_ready_rows": len(label_rows),
            "ready_rows": packet_status_counts.get("ready", 0),
            "exact_endpoint_pairs": len(exact_pairs),
            "counterfactual_pairs": len(counterfactual_pairs),
            "predicate_counts": dict(sorted(predicate_counts.items())),
            "family_counts": dict(sorted(family_counts.items())),
            "role_counts": dict(sorted(role_counts.items())),
            "bucket_counts_hidden": dict(sorted(bucket_counts.items())),
            "packet_status_counts": dict(sorted(packet_status_counts.items())),
            "materialized_packet_rows": len(label_rows),
        },
        "validation": {
            "input_validation_errors": len(input_errors),
            "sheet_validation_errors": len(sheet_errors),
            "packet_path_errors": len(path_errors),
            "leakage_hits": len(leakage_hits),
            "hidden_field_visibility_errors": hidden_field_visibility_errors,
            "expected_columns_match": fieldnames == EXPECTED_COLUMNS,
            "balance_contract_ok": balance_ok,
        },
        "label_schema": label_schema(),
    }

    write_tsv(output_paths["ready_label_sheet"], label_rows, EXPECTED_COLUMNS)
    write_jsonl(output_paths["ready_manifest_post_label_only"], manifest_rows)
    write_json(output_paths["label_schema"], label_schema())
    write_csv(output_paths["row_readiness"], row_readiness)
    write_jsonl(output_paths["hidden_field_audit"], hidden_audit_rows)
    write_jsonl(output_paths["input_validation_errors"], input_errors)
    write_jsonl(output_paths["sheet_validation_errors"], sheet_errors)
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_jsonl(output_paths["leakage_hits"], leakage_hits)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        f"status={summary['status']} "
        f"rows={summary['counts']['label_ready_rows']} "
        f"ready={summary['counts']['ready_rows']} "
        f"pairs={summary['counts']['counterfactual_pairs']} "
        f"path_errors={summary['validation']['packet_path_errors']} "
        f"leakage={summary['validation']['leakage_hits']} "
        f"sheet_errors={summary['validation']['sheet_validation_errors']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
