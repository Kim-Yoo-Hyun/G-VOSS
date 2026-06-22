#!/usr/bin/env python3
"""Validate H002 v8 endpoint-pair counterfactual label readiness."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v8_endpoint_pair_counterfactual_candidate_mining as mining


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

REPLACEMENT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_replacement_mining_codex_proxy_user_requested"
DEFAULT_REPLACEMENT_SUMMARY = REPLACEMENT_DIR / "summary.json"
DEFAULT_RESTORED_LABEL_SHEET = REPLACEMENT_DIR / "combined_label_sheet_pre_asset_packet.tsv"
DEFAULT_RESTORED_MANIFEST = REPLACEMENT_DIR / "combined_manifest_pre_asset_packet.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_label_readiness_codex_proxy_user_requested"

SCHEMA_VERSION = "h002_reliability_target_v8_endpoint_pair_counterfactual_label_readiness_v1"
EXPECTED_REPLACEMENT_STATUS = "h002_reliability_target_v8_endpoint_pair_counterfactual_replacement_mining_ready_for_label_readiness"
EXPECTED_NEXT_TODO = "reliability_target_v8_endpoint_pair_counterfactual_label_readiness"
EXPECTED_COLUMNS = mining.VISIBLE_FIELDS + ["packet_gap_decision", "packet_gap_reason"]
REVIEW_FIELDS = mining.COMPLETION_FIELDS
ALLOWED_PACKET_STATUSES = {"ready", "limited_view_evaluable"}
ALLOWED_GAP_DECISIONS = {"label_ready", "limited_view_evaluable", "replacement_candidate"}
EXPECTED_FAMILY_BUCKET_COUNTS = {
    "relative_vertical|B2_semantic_high_geometry_low": 60,
    "relative_vertical|B3_semantic_low_geometry_high": 60,
    "support_contact|B2_semantic_high_geometry_low": 60,
    "support_contact|B3_semantic_low_geometry_high": 60,
}

ALLOWED_REVIEW_VALUES = {
    "endpoint_identity_v6": ["clear", "uncertain", "wrong_endpoint", "not_evaluable"],
    "pair_evaluability_v6": ["evaluable", "evidence_limited", "predicate_ambiguous", "segmentation_limited", "not_evaluable"],
    "geometry_support_v6": ["supports", "contradicts", "ambiguous", "not_evaluable"],
    "relation_usefulness_v6": ["useful_nontrivial", "trivial_or_redundant", "not_a_relation", "uncertain"],
    "relation_reliability_state_v6": ["accept_reliable", "reject_unreliable", "abstain_uncertain"],
    "primary_reason_v6": [
        "geometric_support",
        "geometric_contradiction",
        "semantic_ontology_mismatch",
        "annotation_sparsity_candidate",
        "dense_relation_noise",
        "endpoint_identity_issue",
        "predicate_definition_ambiguous",
        "insufficient_evidence",
        "trivial_room_surface_or_structure",
        "other",
    ],
    "uncertainty_reason_v6": [
        "",
        "occlusion_or_view_limit",
        "mesh_or_pointcloud_limit",
        "ambiguous_contact",
        "ambiguous_vertical_order",
        "object_segmentation_issue",
        "predicate_definition_ambiguous",
        "coverage_limited",
        "other",
    ],
}

FORBIDDEN_VISIBLE_TOKENS = [
    "bucket",
    "expected_target",
    "geometry_status",
    "h001_verification",
    "hidden",
    "label_geometry_bucket",
    "label_match",
    "machine_hint",
    "matched_predicates",
    "object_family_cell",
    "p_geom",
    "queue_kind",
    "rank_band",
    "reason_codes",
    "semantic_rank",
    "semantic_score",
    "source_queue",
    "strict_group",
    "endpoint_pair_key",
    "v8_group",
    "subject_object_family_cell",
]

FORBIDDEN_VISIBLE_VALUE_TOKENS = [token for token in FORBIDDEN_VISIBLE_TOKENS if token != "bucket"]

FORBIDDEN_PACKET_TEXT_TOKENS = [
    "candidate_bucket",
    "expected_target",
    "geometry_status",
    "h001_verification",
    "label_geometry_bucket",
    "label_match",
    "machine_hint",
    "matched_predicates",
    "object_family_cell",
    "p_geom",
    "queue_kind",
    "rank_band",
    "reason_codes",
    "semantic_rank",
    "semantic_score",
    "source_queue",
    "strict_group",
    "exact_endpoint_pair",
    "v8_group",
    "subject_object_family_cell",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replacement-summary", type=Path, default=DEFAULT_REPLACEMENT_SUMMARY)
    parser.add_argument("--restored-label-sheet", type=Path, default=DEFAULT_RESTORED_LABEL_SHEET)
    parser.add_argument("--restored-manifest", type=Path, default=DEFAULT_RESTORED_MANIFEST)
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
                    fieldnames.append(key)
                    seen.add(key)
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

    source_paths: dict[str, Path] = {}
    source_dirs: set[Path] = set()
    for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
        value = str(manifest.get(field) or "")
        if not value:
            errors.append({"blind_review_id": blind_id, "field": field, "error_type": "empty_source_packet_path"})
            continue
        source = resolve_packet_path(value, input_base)
        source_paths[field] = source
        if not source.exists():
            errors.append({"blind_review_id": blind_id, "field": field, "path": value, "error_type": "source_packet_path_missing"})
            continue
        source_dirs.add(source.parent)

    for source_dir in sorted(source_dirs, key=str):
        for source in source_dir.iterdir():
            dest = dest_dir / source.name
            if source.is_file():
                shutil.copy2(source, dest)
                rewrite_blind_id(dest, blind_id)

    output_paths: dict[str, str] = {}
    filename_by_field = {
        "multiview_packet": "packet.md",
        "pointcloud_or_mesh_packet": "mesh_packet.md",
    }
    for field, source in source_paths.items():
        if not source.exists() or not source.is_file():
            continue
        if field == "contact_or_context_sheet":
            filename = "geometry_only_context.md" if source.suffix == ".md" else "contact_context_sheet.jpg"
        else:
            filename = filename_by_field[field]
        dest = dest_dir / filename
        if source.resolve() != dest.resolve():
            shutil.copy2(source, dest)
            rewrite_blind_id(dest, blind_id)
        output_paths[field] = f"packets/{blind_id}/{filename}"
    return output_paths, errors


def forbidden_header_hits(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    allowed = {"packet_gap_decision", "packet_gap_reason", "endpoint_pair_note"}
    for field in fieldnames:
        if field in allowed:
            continue
        lower = field.lower()
        for token in FORBIDDEN_VISIBLE_TOKENS:
            if token in lower:
                hits.append({"surface": "field_name", "field": field, "forbidden_token": token})
    return hits


def forbidden_value_hits(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    skip_fields = {"multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet", "endpoint_pair_note"}
    for row_number, row in enumerate(rows, start=2):
        for field, value in row.items():
            if field in skip_fields or field in REVIEW_FIELDS or field == "label_notes_v6":
                continue
            lower = str(value).lower()
            for token in FORBIDDEN_VISIBLE_VALUE_TOKENS:
                if token in lower:
                    hits.append(
                        {
                            "surface": "field_value",
                            "row_number": row_number,
                            "blind_review_id": row.get("blind_review_id", ""),
                            "field": field,
                            "forbidden_token": token,
                        }
                    )
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
            resolved = resolve_packet_path(value, base_dir)
            if not resolved.exists():
                errors.append({"row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "field": field, "value": value, "error_type": "packet_path_missing_on_disk"})
    return errors


def validate_inputs(
    replacement_summary: dict[str, Any],
    fieldnames: list[str],
    label_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if replacement_summary.get("status") != EXPECTED_REPLACEMENT_STATUS:
        errors.append({"error_type": "unexpected_replacement_status", "actual": replacement_summary.get("status")})
    if replacement_summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_replacement_next_todo", "actual": replacement_summary.get("next_todo")})
    boundary = replacement_summary.get("boundary") or {}
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed", "multi_view_as_model_input", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": f"replacement_boundary_{key}_not_false", "actual": boundary.get(key)})
    counts = replacement_summary.get("counts") or {}
    if len(label_rows) != counts.get("combined_rows"):
        errors.append({"error_type": "label_row_count_mismatch", "expected": counts.get("combined_rows"), "actual": len(label_rows)})
    if len(manifest_rows) != len(label_rows):
        errors.append({"error_type": "manifest_label_row_count_mismatch", "manifest_rows": len(manifest_rows), "label_rows": len(label_rows)})
    if fieldnames != EXPECTED_COLUMNS:
        errors.append({"error_type": "unexpected_header", "expected": EXPECTED_COLUMNS, "observed": fieldnames})
    return errors


def evidence_status(manifest: dict[str, Any]) -> str:
    return str(manifest.get("normalized_evidence_status_hidden") or manifest.get("packet_status_hidden") or "")


def normalize_label_rows(
    label_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, Any]],
    output_dir: Path,
    input_base: Path,
) -> tuple[list[dict[str, str]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_by_id = {str(row.get("blind_review_id")): row for row in manifest_rows}
    ready_rows: list[dict[str, str]] = []
    updated_manifests: list[dict[str, Any]] = []
    path_errors: list[dict[str, Any]] = []
    row_readiness: list[dict[str, Any]] = []

    for row_number, row in enumerate(label_rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        manifest = manifest_by_id.get(blind_id)
        if manifest is None:
            path_errors.append({"row_number": row_number, "blind_review_id": blind_id, "error_type": "missing_manifest"})
            continue
        paths, materialize_errors = materialize_packet_paths(manifest, output_dir, input_base)
        path_errors.extend({"row_number": row_number, **error} for error in materialize_errors)
        status = evidence_status(manifest)
        gap_decision = str(manifest.get("row_gap_decision_hidden") or row.get("packet_gap_decision") or "")
        gap_reason = str(manifest.get("row_gap_reason_hidden") or row.get("packet_gap_reason") or "")
        updated = dict(row)
        updated["evidence_packet_status"] = status
        updated["packet_gap_decision"] = gap_decision
        updated["packet_gap_reason"] = gap_reason
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            updated[field] = paths.get(field, "")
        for field in REVIEW_FIELDS + ["label_notes_v6"]:
            updated[field] = ""
        ready_rows.append(updated)

        manifest_updated = dict(manifest)
        manifest_updated.update(paths)
        manifest_updated["label_readiness_status_hidden"] = "ready_for_label_fill"
        forbidden = list(manifest_updated.get("forbidden_as_labeler_visible") or [])
        if "label_readiness_status_hidden" not in forbidden:
            forbidden.append("label_readiness_status_hidden")
        manifest_updated["forbidden_as_labeler_visible"] = forbidden
        updated_manifests.append(manifest_updated)
        row_readiness.append(
            {
                "blind_review_id": blind_id,
                "predicate_family": manifest.get("predicate_family"),
                "semantic_geometry_bucket_hidden": manifest.get("semantic_geometry_bucket_hidden"),
                "evidence_packet_status": status,
                "packet_gap_decision": gap_decision,
                "packet_gap_reason": gap_reason,
                "source_batch": manifest.get("batch_name"),
            }
        )
    return ready_rows, updated_manifests, path_errors, row_readiness


def validate_label_sheet(
    label_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, Any]],
    base_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    ids = [row.get("blind_review_id", "") for row in label_rows]
    for blind_id, count in Counter(ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id, "count": count})

    manifest_by_id = {str(row.get("blind_review_id")): row for row in manifest_rows}
    label_id_set = set(ids)
    manifest_id_set = set(manifest_by_id)
    if label_id_set != manifest_id_set:
        errors.append({"error_type": "label_manifest_id_mismatch", "label_only": sorted(label_id_set - manifest_id_set)[:10], "manifest_only": sorted(manifest_id_set - label_id_set)[:10]})

    for row_number, row in enumerate(label_rows, start=2):
        for field in REVIEW_FIELDS + ["label_notes_v6"]:
            if str(row.get(field, "")).strip():
                errors.append({"error_type": "review_field_already_filled", "row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "field": field})
        status = row.get("evidence_packet_status")
        decision = row.get("packet_gap_decision")
        if status not in ALLOWED_PACKET_STATUSES:
            errors.append({"error_type": "unexpected_evidence_packet_status", "row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "value": status})
        if decision not in ALLOWED_GAP_DECISIONS:
            errors.append({"error_type": "unexpected_packet_gap_decision", "row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "value": decision})
        if status == "limited_view_evaluable" and decision != "limited_view_evaluable":
            errors.append({"error_type": "limited_status_has_wrong_gap_decision", "row_number": row_number, "blind_review_id": row.get("blind_review_id", ""), "decision": decision})

    hidden_audit_rows: list[dict[str, Any]] = []
    fieldnames = EXPECTED_COLUMNS
    for manifest in manifest_rows:
        forbidden = set(str(field) for field in (manifest.get("forbidden_as_labeler_visible") or []))
        leaked_forbidden = sorted(forbidden & set(fieldnames))
        if leaked_forbidden:
            errors.append({"error_type": "forbidden_manifest_field_visible", "blind_review_id": manifest.get("blind_review_id"), "fields": leaked_forbidden})
        hidden_audit_rows.append(
            {
                "blind_review_id": manifest.get("blind_review_id"),
                "forbidden_field_count": len(forbidden),
                "forbidden_fields_visible": len(leaked_forbidden),
                "semantic_geometry_bucket_hidden_present": "semantic_geometry_bucket_hidden" in manifest,
                "p_geom_valid_hidden_present": "p_geom_valid_hidden" in manifest,
                "semantic_score_norm_hidden_present": "semantic_score_norm_hidden" in manifest,
                "exact_endpoint_pair_key_hidden_present": "exact_endpoint_pair_key_hidden" in manifest,
                "v8_group_key_hidden_present": "v8_group_key_hidden" in manifest,
            }
        )

    leakage_hits = forbidden_header_hits(fieldnames)
    leakage_hits.extend(forbidden_value_hits(label_rows))
    leakage_hits.extend(packet_text_hits(label_rows, base_dir))
    path_errors = row_path_errors(label_rows, base_dir)
    return errors, path_errors, leakage_hits, hidden_audit_rows


def label_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "visible_fields": EXPECTED_COLUMNS,
        "review_fields": REVIEW_FIELDS,
        "allowed_review_values": ALLOWED_REVIEW_VALUES,
        "primary_target": "relation_reliability_state_v6",
        "primary_target_values": ["accept_reliable", "reject_unreliable", "abstain_uncertain"],
        "target_after_label_fill": "relation_reliability_state_v8_multiclass_target",
        "construction": "v8_endpoint_pair_counterfactual",
        "semantic_geometry_bucket_is_not_target": True,
        "hidden_sampling_fields_are_not_label_targets": True,
        "endpoint_pair_group_is_not_labeler_visible": True,
        "limited_view_policy": {
            "ready": "complete endpoint, contact/context, and mesh evidence",
            "limited_view_evaluable": "reviewable with explicit evidence caveat; labeler may choose evidence_limited or abstain_uncertain",
            "replacement_candidate": "packet-ready replacement row selected after endpoint evidence gap audit",
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    validation = summary["validation"]
    lines = [
        "# H002 V8 Endpoint-Pair Counterfactual Label Readiness",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage gate.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- Multi-view and mesh packets are audit/label evidence only, not posterior input.",
        "- Semantic/geometry score, bucket, rank, endpoint-pair key, and v8 group metadata remain hidden from the label sheet.",
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
        f"| label-ready rows | {counts['label_ready_rows']} |",
        f"| ready rows | {counts['ready_rows']} |",
        f"| limited-view rows | {counts['limited_view_rows']} |",
        f"| replacement-candidate rows | {counts['replacement_candidate_rows']} |",
        f"| support_contact rows | {counts['family_counts'].get('support_contact', 0)} |",
        f"| relative_vertical rows | {counts['family_counts'].get('relative_vertical', 0)} |",
        f"| B2 rows | {counts['bucket_counts_hidden'].get('B2_semantic_high_geometry_low', 0)} |",
        f"| B3 rows | {counts['bucket_counts_hidden'].get('B3_semantic_low_geometry_high', 0)} |",
        "",
        "## Validation",
        "",
        "| Check | Errors |",
        "| --- | ---: |",
        f"| input validation | {validation['input_validation_errors']} |",
        f"| schema/row validation | {validation['sheet_validation_errors']} |",
        f"| packet paths | {validation['packet_path_errors']} |",
        f"| visible/packet leakage | {validation['leakage_hits']} |",
        f"| hidden field exposure | {validation['hidden_field_visibility_errors']} |",
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
    fieldnames, raw_label_rows = read_tsv(args.restored_label_sheet)
    raw_manifest_rows = read_jsonl(args.restored_manifest)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_errors = validate_inputs(replacement_summary, fieldnames, raw_label_rows, raw_manifest_rows)
    label_rows, manifest_rows, materialize_errors, row_readiness = normalize_label_rows(
        raw_label_rows,
        raw_manifest_rows,
        output_dir,
        as_abs(args.restored_label_sheet).parent,
    )
    sheet_errors, path_errors, leakage_hits, hidden_audit_rows = validate_label_sheet(label_rows, manifest_rows, output_dir)
    path_errors.extend(materialize_errors)

    family_counts = Counter(str(row.get("predicate_family")) for row in manifest_rows)
    bucket_counts = Counter(str(row.get("semantic_geometry_bucket_hidden")) for row in manifest_rows)
    family_bucket_counts = Counter(f"{row.get('predicate_family')}|{row.get('semantic_geometry_bucket_hidden')}" for row in manifest_rows)
    packet_status_counts = Counter(str(row.get("evidence_packet_status")) for row in label_rows)
    gap_decision_counts = Counter(str(row.get("packet_gap_decision")) for row in label_rows)
    hidden_field_visibility_errors = sum(row["forbidden_fields_visible"] for row in hidden_audit_rows)

    passes_contract = (
        not input_errors
        and not sheet_errors
        and not path_errors
        and not leakage_hits
        and hidden_field_visibility_errors == 0
        and len(label_rows) == 240
        and packet_status_counts == Counter({"ready": 219, "limited_view_evaluable": 21})
        and gap_decision_counts == Counter({"label_ready": 211, "limited_view_evaluable": 21, "replacement_candidate": 8})
        and family_counts == Counter({"relative_vertical": 120, "support_contact": 120})
        and bucket_counts == Counter({"B2_semantic_high_geometry_low": 120, "B3_semantic_low_geometry_high": 120})
        and dict(sorted(family_bucket_counts.items())) == EXPECTED_FAMILY_BUCKET_COUNTS
    )
    status = (
        "h002_reliability_target_v8_endpoint_pair_counterfactual_label_readiness_ready_for_label_fill"
        if passes_contract
        else "h002_reliability_target_v8_endpoint_pair_counterfactual_label_readiness_blocked"
    )
    next_todo = (
        "reliability_target_v8_endpoint_pair_counterfactual_label_fill"
        if passes_contract
        else "fix_reliability_target_v8_endpoint_pair_counterfactual_label_readiness"
    )
    decision = (
        "The restored 240-row v8 endpoint-pair counterfactual sheet is ready for label fill with explicit limited-view and replacement-candidate caveats."
        if passes_contract
        else "The v8 label-ready sheet is blocked by validation errors."
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
            "replacement_summary": rel_path(args.replacement_summary),
            "restored_label_sheet": rel_path(args.restored_label_sheet),
            "restored_manifest": rel_path(args.restored_manifest),
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
            "limited_view_rows": packet_status_counts.get("limited_view_evaluable", 0),
            "replacement_candidate_rows": gap_decision_counts.get("replacement_candidate", 0),
            "family_counts": dict(sorted(family_counts.items())),
            "bucket_counts_hidden": dict(sorted(bucket_counts.items())),
            "family_bucket_counts_hidden": dict(sorted(family_bucket_counts.items())),
            "packet_status_counts": dict(sorted(packet_status_counts.items())),
            "packet_gap_decision_counts": dict(sorted(gap_decision_counts.items())),
            "materialized_packet_rows": len(label_rows),
        },
        "validation": {
            "input_validation_errors": len(input_errors),
            "sheet_validation_errors": len(sheet_errors),
            "packet_path_errors": len(path_errors),
            "leakage_hits": len(leakage_hits),
            "hidden_field_visibility_errors": hidden_field_visibility_errors,
            "expected_columns_match": fieldnames == EXPECTED_COLUMNS,
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
        f"limited={summary['counts']['limited_view_rows']} "
        f"replacement={summary['counts']['replacement_candidate_rows']} "
        f"path_errors={summary['validation']['packet_path_errors']} "
        f"leakage={summary['validation']['leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
