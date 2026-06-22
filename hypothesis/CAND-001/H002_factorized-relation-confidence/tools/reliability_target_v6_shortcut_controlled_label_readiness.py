#!/usr/bin/env python3
"""Validate v6 shortcut-controlled label readiness before label fill."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v6_shortcut_controlled_candidate_mining as mining


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

GAP_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_asset_packet_gap_audit_codex_proxy_user_requested"
DEFAULT_GAP_SUMMARY = GAP_DIR / "summary.json"
DEFAULT_LABEL_READY_SHEET = GAP_DIR / "label_ready_full_label_sheet.tsv"
DEFAULT_LABEL_READY_MANIFEST = GAP_DIR / "label_ready_full_manifest_post_label_only.jsonl"
DEFAULT_EXCLUDED_ROWS = GAP_DIR / "excluded_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_label_readiness_codex_proxy_user_requested"

SCHEMA_VERSION = "h002_reliability_target_v6_shortcut_controlled_label_readiness_v1"
EXPECTED_COLUMNS = mining.VISIBLE_FIELDS + ["packet_gap_decision", "packet_gap_reason"]
REVIEW_FIELDS = mining.COMPLETION_FIELDS
ALLOWED_PACKET_STATUSES = {"ready", "limited_view_evaluable"}
ALLOWED_GAP_DECISIONS = {"label_ready", "limited_view_evaluable", "geometry_only_evaluable"}

ALLOWED_REVIEW_VALUES = {
    "endpoint_identity_v6": ["clear", "uncertain", "wrong_endpoint", "not_evaluable"],
    "pair_evaluability_v6": [
        "evaluable",
        "evidence_limited",
        "predicate_ambiguous",
        "segmentation_limited",
        "not_evaluable",
    ],
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
    "candidate_bucket",
    "cell_contrast",
    "contrast_role",
    "endpoint_flag_pattern",
    "expected_target",
    "geometry_status",
    "h001_verification",
    "hidden",
    "informative_score",
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
]

FORBIDDEN_PACKET_TEXT_TOKENS = [
    "candidate_bucket",
    "cell_contrast",
    "contrast_role",
    "endpoint_flag_pattern",
    "expected_target",
    "geometry_status",
    "h001_verification",
    "informative_score",
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-summary", type=Path, default=DEFAULT_GAP_SUMMARY)
    parser.add_argument("--label-ready-sheet", type=Path, default=DEFAULT_LABEL_READY_SHEET)
    parser.add_argument("--label-ready-manifest", type=Path, default=DEFAULT_LABEL_READY_MANIFEST)
    parser.add_argument("--excluded-rows", type=Path, default=DEFAULT_EXCLUDED_ROWS)
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


def resolve_label_path(value: str, base_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    repo_candidate = as_abs(path)
    if repo_candidate.exists():
        return repo_candidate
    return base_dir / path


def forbidden_header_hits(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    allowed_extra = {"packet_gap_decision", "packet_gap_reason"}
    for field in fieldnames:
        if field in allowed_extra:
            continue
        lower = field.lower()
        for token in FORBIDDEN_VISIBLE_TOKENS:
            if token in lower:
                hits.append({"surface": "field_name", "field": field, "forbidden_token": token})
    return hits


def forbidden_value_hits(rows: list[dict[str, str]], fields: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        for field in fields:
            value = str(row.get(field, ""))
            lower = value.lower()
            for token in FORBIDDEN_VISIBLE_TOKENS:
                if token in lower:
                    hits.append(
                        {
                            "surface": "field_value",
                            "row_number": row_number,
                            "blind_review_id": row.get("blind_review_id", ""),
                            "field": field,
                            "forbidden_token": token,
                            "value_preview": value[:120],
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
            path = resolve_label_path(value, base_dir)
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
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": row.get("blind_review_id", ""),
                        "field": field,
                        "error_type": "empty_packet_path",
                    }
                )
                continue
            resolved = resolve_label_path(value, base_dir)
            if not resolved.exists():
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": row.get("blind_review_id", ""),
                        "field": field,
                        "value": value,
                        "error_type": "packet_path_missing_on_disk",
                    }
                )
    return errors


def validate_inputs(
    gap_summary: dict[str, Any],
    label_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, Any]],
    excluded_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if gap_summary.get("status") != "h002_reliability_target_v6_shortcut_controlled_asset_packet_gap_audit_ready_for_label_readiness":
        errors.append({"error_type": "unexpected_gap_status", "value": gap_summary.get("status")})
    if gap_summary.get("next_todo") != "reliability_target_v6_shortcut_controlled_label_readiness":
        errors.append({"error_type": "unexpected_gap_next_todo", "value": gap_summary.get("next_todo")})
    boundary = gap_summary.get("boundary") or {}
    for key in ["validation_usage", "test_usage", "posterior_trained", "posterior_smoke_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": f"gap_boundary_{key}_not_false", "value": boundary.get(key)})
    expected_rows = gap_summary.get("counts", {}).get("label_ready_rows")
    if len(label_rows) != expected_rows:
        errors.append({"error_type": "label_ready_row_count_mismatch", "expected": expected_rows, "actual": len(label_rows)})
    if len(manifest_rows) != len(label_rows):
        errors.append({"error_type": "manifest_label_row_count_mismatch", "manifest_rows": len(manifest_rows), "label_rows": len(label_rows)})
    if excluded_rows:
        errors.append({"error_type": "unexpected_excluded_rows", "count": len(excluded_rows)})
    return errors


def validate_label_sheet(
    fieldnames: list[str],
    label_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, Any]],
    base_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    if fieldnames != EXPECTED_COLUMNS:
        errors.append({"error_type": "unexpected_header", "expected": EXPECTED_COLUMNS, "observed": fieldnames})

    ids = [row.get("blind_review_id", "") for row in label_rows]
    for blind_id, count in Counter(ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id, "count": count})

    manifest_by_id = {str(row.get("blind_review_id")): row for row in manifest_rows}
    label_id_set = set(ids)
    manifest_id_set = set(manifest_by_id)
    if label_id_set != manifest_id_set:
        errors.append(
            {
                "error_type": "label_manifest_id_mismatch",
                "label_only": sorted(label_id_set - manifest_id_set)[:10],
                "manifest_only": sorted(manifest_id_set - label_id_set)[:10],
            }
        )

    for row_number, row in enumerate(label_rows, start=2):
        for field in REVIEW_FIELDS:
            if str(row.get(field, "")).strip():
                errors.append(
                    {
                        "error_type": "review_field_already_filled",
                        "row_number": row_number,
                        "blind_review_id": row.get("blind_review_id", ""),
                        "field": field,
                    }
                )
        status = row.get("evidence_packet_status")
        decision = row.get("packet_gap_decision")
        if status not in ALLOWED_PACKET_STATUSES:
            errors.append(
                {
                    "error_type": "unexpected_evidence_packet_status",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id", ""),
                    "value": status,
                }
            )
        if decision not in ALLOWED_GAP_DECISIONS:
            errors.append(
                {
                    "error_type": "unexpected_packet_gap_decision",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id", ""),
                    "value": decision,
                }
            )
        if status == "ready" and decision != "label_ready":
            errors.append(
                {
                    "error_type": "ready_status_has_non_ready_gap_decision",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id", ""),
                    "decision": decision,
                }
            )
        if status == "limited_view_evaluable" and decision == "label_ready":
            errors.append(
                {
                    "error_type": "limited_status_has_label_ready_decision",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id", ""),
                }
            )

    hidden_audit_rows: list[dict[str, Any]] = []
    for manifest in manifest_rows:
        forbidden = set(str(field) for field in (manifest.get("forbidden_as_labeler_visible") or []))
        leaked_forbidden = sorted(forbidden & set(fieldnames))
        if leaked_forbidden:
            errors.append(
                {
                    "error_type": "forbidden_manifest_field_visible",
                    "blind_review_id": manifest.get("blind_review_id"),
                    "fields": leaked_forbidden,
                }
            )
        hidden_audit_rows.append(
            {
                "blind_review_id": manifest.get("blind_review_id"),
                "forbidden_field_count": len(forbidden),
                "forbidden_fields_visible": len(leaked_forbidden),
                "candidate_bucket_hidden_present": "candidate_bucket_hidden" in manifest,
                "p_geom_valid_hidden_present": "p_geom_valid_hidden" in manifest,
                "semantic_score_norm_hidden_present": "semantic_score_norm_hidden" in manifest,
            }
        )

    path_errors = row_path_errors(label_rows, base_dir)
    visible_fields_to_check = [
        "review_scope",
        "multiview_packet",
        "pointcloud_or_mesh_packet",
        "contact_or_context_sheet",
    ]
    leakage_hits = forbidden_header_hits(fieldnames)
    leakage_hits.extend(forbidden_value_hits(label_rows, visible_fields_to_check))
    leakage_hits.extend(packet_text_hits(label_rows, base_dir))

    row_summary = []
    manifest_counter = Counter(
        (
            str(row.get("predicate_family")),
            str(row.get("candidate_bucket_hidden")),
            str(row.get("normalized_evidence_status_hidden") or row.get("evidence_packet_status")),
            str(row.get("row_gap_decision_hidden")),
        )
        for row in manifest_rows
    )
    for (family, bucket, evidence_status, gap_decision), count in sorted(manifest_counter.items()):
        row_summary.append(
            {
                "predicate_family": family,
                "candidate_bucket_hidden": bucket,
                "evidence_status_hidden": evidence_status,
                "row_gap_decision_hidden": gap_decision,
                "rows": count,
            }
        )
    return errors, path_errors, leakage_hits, row_summary, hidden_audit_rows


def label_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "visible_fields": EXPECTED_COLUMNS,
        "review_fields": REVIEW_FIELDS,
        "allowed_review_values": ALLOWED_REVIEW_VALUES,
        "primary_target": "relation_reliability_state_v6",
        "primary_target_values": ["accept_reliable", "reject_unreliable", "abstain_uncertain"],
        "target_after_label_fill": "relation_reliability_state_v6_multiclass_target",
        "candidate_bucket_is_not_target": True,
        "hidden_sampling_fields_are_not_label_targets": True,
        "limited_view_policy": {
            "ready": "complete multiview, contact/context, and mesh evidence",
            "limited_view_evaluable": "reviewable with explicit evidence caveat; labeler may choose evidence_limited or abstain_uncertain",
            "geometry_only_evaluable": "reviewable from mesh evidence only; labeler should prefer evidence_limited/abstain unless geometry is decisive",
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    validation = summary["validation"]
    lines = [
        "# H002 Reliability Target V6 Shortcut-Controlled Label Readiness",
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
        "- Candidate bucket remains hidden and is not a target or posterior input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| label-ready rows | {counts['label_ready_rows']} |",
        f"| ready rows | {counts['ready_rows']} |",
        f"| limited-view rows | {counts['limited_view_rows']} |",
        f"| geometry-only rows | {counts['geometry_only_rows']} |",
        f"| support_contact rows | {counts['family_counts'].get('support_contact', 0)} |",
        f"| relative_vertical rows | {counts['family_counts'].get('relative_vertical', 0)} |",
        f"| B1 rows | {counts['bucket_counts_hidden'].get('B1_semantic_high_geometry_high', 0)} |",
        f"| B2 rows | {counts['bucket_counts_hidden'].get('B2_semantic_high_geometry_low', 0)} |",
        f"| B3 rows | {counts['bucket_counts_hidden'].get('B3_semantic_low_geometry_high', 0)} |",
        f"| B4 rows | {counts['bucket_counts_hidden'].get('B4_ambiguous_or_coverage_limited', 0)} |",
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
    gap_summary = read_json(args.gap_summary)
    fieldnames, label_rows = read_tsv(args.label_ready_sheet)
    manifest_rows = read_jsonl(args.label_ready_manifest)
    excluded_rows = read_jsonl(args.excluded_rows)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_errors = validate_inputs(gap_summary, label_rows, manifest_rows, excluded_rows)
    sheet_errors, path_errors, leakage_hits, row_summary, hidden_audit_rows = validate_label_sheet(
        fieldnames,
        label_rows,
        manifest_rows,
        as_abs(args.label_ready_sheet).parent,
    )
    family_counts = Counter(str(row.get("predicate_family")) for row in manifest_rows)
    bucket_counts = Counter(str(row.get("candidate_bucket_hidden")) for row in manifest_rows)
    family_bucket_counts = Counter(
        f"{row.get('predicate_family')}|{row.get('candidate_bucket_hidden')}" for row in manifest_rows
    )
    packet_status_counts = Counter(str(row.get("evidence_packet_status")) for row in label_rows)
    gap_decision_counts = Counter(str(row.get("packet_gap_decision")) for row in label_rows)
    hidden_field_visibility_errors = sum(row["forbidden_fields_visible"] for row in hidden_audit_rows)
    expected = gap_summary.get("counts", {})

    status = (
        "h002_reliability_target_v6_shortcut_controlled_label_readiness_ready_for_label_fill"
        if not input_errors
        and not sheet_errors
        and not path_errors
        and not leakage_hits
        and hidden_field_visibility_errors == 0
        and len(label_rows) == expected.get("label_ready_rows")
        and family_counts == Counter({"relative_vertical": 120, "support_contact": 120})
        and all(bucket_counts.get(bucket, 0) == 60 for bucket in mining.BUCKET_ORDER)
        and all(family_bucket_counts.get(f"{family}|{bucket}", 0) == 30 for family in mining.PRIMARY_FAMILIES for bucket in mining.BUCKET_ORDER)
        else "h002_reliability_target_v6_shortcut_controlled_label_readiness_blocked"
    )
    next_todo = (
        "reliability_target_v6_shortcut_controlled_label_fill"
        if status == "h002_reliability_target_v6_shortcut_controlled_label_readiness_ready_for_label_fill"
        else "fix_reliability_target_v6_shortcut_controlled_label_readiness"
    )
    decision = (
        "The 240-row v6 shortcut-controlled sheet is ready for label fill with explicit limited-view caveats."
        if status == "h002_reliability_target_v6_shortcut_controlled_label_readiness_ready_for_label_fill"
        else "The v6 shortcut-controlled label-ready sheet is blocked by validation errors."
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
        "excluded_rows_snapshot": output_dir / "excluded_rows_snapshot.jsonl",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": {
            "gap_summary": rel_path(args.gap_summary),
            "label_ready_sheet": rel_path(args.label_ready_sheet),
            "label_ready_manifest": rel_path(args.label_ready_manifest),
            "excluded_rows": rel_path(args.excluded_rows),
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
            "candidate_bucket_visible_to_labeler": False,
            "candidate_bucket_posterior_input_allowed": False,
        },
        "counts": {
            "label_ready_rows": len(label_rows),
            "ready_rows": packet_status_counts.get("ready", 0),
            "limited_view_rows": packet_status_counts.get("limited_view_evaluable", 0),
            "geometry_only_rows": gap_decision_counts.get("geometry_only_evaluable", 0),
            "family_counts": dict(sorted(family_counts.items())),
            "bucket_counts_hidden": dict(sorted(bucket_counts.items())),
            "family_bucket_counts_hidden": dict(sorted(family_bucket_counts.items())),
            "packet_status_counts": dict(sorted(packet_status_counts.items())),
            "packet_gap_decision_counts": dict(sorted(gap_decision_counts.items())),
            "excluded_row_count": len(excluded_rows),
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

    write_tsv(output_paths["ready_label_sheet"], label_rows, fieldnames)
    write_jsonl(output_paths["ready_manifest_post_label_only"], manifest_rows)
    write_json(output_paths["label_schema"], label_schema())
    write_csv(output_paths["row_readiness"], row_summary)
    write_jsonl(output_paths["hidden_field_audit"], hidden_audit_rows)
    write_jsonl(output_paths["input_validation_errors"], input_errors)
    write_jsonl(output_paths["sheet_validation_errors"], sheet_errors)
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_jsonl(output_paths["leakage_hits"], leakage_hits)
    write_jsonl(output_paths["excluded_rows_snapshot"], excluded_rows)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} "
        f"rows={summary['counts']['label_ready_rows']} "
        f"ready={summary['counts']['ready_rows']} "
        f"limited_view={summary['counts']['limited_view_rows']} "
        f"geometry_only={summary['counts']['geometry_only_rows']} "
        f"path_errors={summary['validation']['packet_path_errors']} "
        f"leakage={summary['validation']['leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
