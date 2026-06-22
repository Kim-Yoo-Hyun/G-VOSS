#!/usr/bin/env python3
"""Validate v5 cell-contrast label readiness before label fill."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v5_cell_contrast_candidate_mining as mining


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

GAP_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_asset_packet_gap_audit"
DEFAULT_GAP_SUMMARY = GAP_DIR / "summary.json"
DEFAULT_LABEL_READY_SHEET = GAP_DIR / "label_ready_full_label_sheet.tsv"
DEFAULT_LABEL_READY_MANIFEST = GAP_DIR / "label_ready_full_manifest_post_label_only.jsonl"
DEFAULT_EXCLUDED_PAIR_IDS = GAP_DIR / "excluded_pair_ids.txt"
DEFAULT_EXCLUDED_PAIR_ROWS = GAP_DIR / "excluded_pair_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_readiness"

SCHEMA_VERSION = "h002_reliability_target_v5_cell_contrast_label_readiness_v1"
EXPECTED_COLUMNS = mining.VISIBLE_FIELDS + ["packet_gap_decision", "packet_gap_reason"]
REVIEW_FIELDS = mining.COMPLETION_FIELDS

ALLOWED_REVIEW_VALUES = {
    "endpoint_identity_v5": ["same_endpoints", "endpoint_identity_issue", "uncertain"],
    "pair_evaluability_v5": ["evaluable", "not_evaluable", "needs_more_evidence"],
    "geometry_support_v5": ["supports", "contradicts", "ambiguous", "not_evaluable"],
    "relation_usefulness_v5": ["useful_nontrivial", "trivial_or_redundant", "not_a_relation", "uncertain"],
    "relation_reliability_v5": ["reliable", "unreliable", "uncertain"],
    "primary_reason_v5": [
        "geometric_support",
        "geometric_contradiction",
        "semantic_ontology_mismatch",
        "annotation_sparsity_candidate",
        "dense_relation_noise",
        "endpoint_identity_issue",
        "insufficient_evidence",
        "trivial_room_surface_or_structure",
        "other",
    ],
    "uncertainty_reason_v5": [
        "",
        "occlusion_or_view_limit",
        "mesh_or_pointcloud_limit",
        "ambiguous_contact",
        "ambiguous_vertical_order",
        "object_segmentation_issue",
        "predicate_definition_ambiguous",
        "other",
    ],
}

LABEL_TO_BINARY_POLICY = {
    "positive": ["reliable"],
    "negative": ["unreliable"],
    "exclude_or_multiclass_only": ["uncertain"],
}

FORBIDDEN_VISIBLE_TOKENS = [
    "anchor_category",
    "candidate_proxy",
    "cell_contrast",
    "contrast_role",
    "endpoint_flag_pattern",
    "geometry_status",
    "hidden",
    "informative_score",
    "label_geometry_bucket",
    "label_match",
    "machine_hint",
    "matched_predicates",
    "p_geom",
    "proxy",
    "queue_kind",
    "rank_band",
    "reason_codes",
    "semantic_rank",
    "semantic_score",
    "source_queue",
    "stratum",
]

FORBIDDEN_PACKET_TEXT_TOKENS = [
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
    parser.add_argument("--gap-summary", type=Path, default=DEFAULT_GAP_SUMMARY)
    parser.add_argument("--label-ready-sheet", type=Path, default=DEFAULT_LABEL_READY_SHEET)
    parser.add_argument("--label-ready-manifest", type=Path, default=DEFAULT_LABEL_READY_MANIFEST)
    parser.add_argument("--excluded-pair-ids", type=Path, default=DEFAULT_EXCLUDED_PAIR_IDS)
    parser.add_argument("--excluded-pair-rows", type=Path, default=DEFAULT_EXCLUDED_PAIR_ROWS)
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


def read_excluded_pair_ids(path: Path) -> set[str]:
    abs_path = as_abs(path)
    if not abs_path.exists():
        return set()
    return {line.strip() for line in abs_path.read_text(encoding="utf-8").splitlines() if line.strip()}


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
        for field in ["multiview_packet", "pointcloud_or_mesh_packet"]:
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
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if gap_summary.get("status") != "h002_reliability_target_v5_cell_contrast_asset_packet_gap_audit_ready_for_label_readiness":
        errors.append({"error_type": "unexpected_gap_status", "value": gap_summary.get("status")})
    if gap_summary.get("next_todo") != "reliability_target_v5_cell_contrast_label_readiness":
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
    return errors


def validate_label_sheet(
    fieldnames: list[str],
    label_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, Any]],
    excluded_pair_ids: set[str],
    base_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
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
        if row.get("evidence_packet_status") not in {"ready", "limited_view_evaluable"}:
            errors.append(
                {
                    "error_type": "unexpected_evidence_packet_status",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id", ""),
                    "value": row.get("evidence_packet_status"),
                }
            )
        if row.get("packet_gap_decision") not in {"label_ready", "limited_view_evaluable"}:
            errors.append(
                {
                    "error_type": "unexpected_packet_gap_decision",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id", ""),
                    "value": row.get("packet_gap_decision"),
                }
            )

    pair_roles: dict[str, Counter[str]] = defaultdict(Counter)
    pair_rows: dict[str, list[str]] = defaultdict(list)
    for manifest in manifest_rows:
        pair_id = str(manifest.get("cell_contrast_pair_id_hidden"))
        if pair_id in excluded_pair_ids:
            errors.append({"error_type": "excluded_pair_present", "cell_contrast_pair_id_hidden": pair_id})
        pair_roles[pair_id][str(manifest.get("cell_contrast_role_hidden"))] += 1
        pair_rows[pair_id].append(str(manifest.get("blind_review_id")))

    for pair_id, roles in sorted(pair_roles.items()):
        if roles.get("positive_proxy", 0) != 1 or roles.get("negative_proxy", 0) != 1 or len(pair_rows[pair_id]) != 2:
            errors.append(
                {
                    "error_type": "invalid_cell_contrast_pair_role_counts",
                    "cell_contrast_pair_id_hidden": pair_id,
                    "roles": dict(roles),
                    "row_count": len(pair_rows[pair_id]),
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
    pair_summary = [
        {
            "cell_contrast_pair_id_hidden": pair_id,
            "row_count": len(pair_rows[pair_id]),
            "positive_proxy_rows": roles.get("positive_proxy", 0),
            "negative_proxy_rows": roles.get("negative_proxy", 0),
        }
        for pair_id, roles in sorted(pair_roles.items())
    ]
    return errors, path_errors, leakage_hits, pair_summary


def label_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "visible_fields": EXPECTED_COLUMNS,
        "review_fields": REVIEW_FIELDS,
        "allowed_review_values": ALLOWED_REVIEW_VALUES,
        "label_to_binary_policy": LABEL_TO_BINARY_POLICY,
        "target_after_label_fill": "relation_reliability_v5_binary_target",
        "hidden_fields_not_labeler_visible": True,
        "limited_view_policy": {
            "limited_view_evaluable": "labeler can review but should choose needs_more_evidence or uncertain when endpoint identity is unclear",
            "excluded_pairs": "excluded before label fill to preserve cell-contrast pair integrity",
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    validation = summary["validation"]
    lines = [
        "# H002 Reliability Target V5 Cell Contrast Label Readiness",
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
        f"| label-ready pairs | {counts['label_ready_pairs']} |",
        f"| ready rows | {counts['ready_rows']} |",
        f"| limited-view rows | {counts['limited_view_rows']} |",
        f"| support_contact rows | {counts['family_counts'].get('support_contact', 0)} |",
        f"| relative_vertical rows | {counts['family_counts'].get('relative_vertical', 0)} |",
        f"| positive proxy rows | {counts['role_counts_hidden'].get('positive_proxy', 0)} |",
        f"| negative proxy rows | {counts['role_counts_hidden'].get('negative_proxy', 0)} |",
        "",
        "## Validation",
        "",
        "| Check | Errors |",
        "| --- | ---: |",
        f"| input validation | {validation['input_validation_errors']} |",
        f"| schema/row validation | {validation['sheet_validation_errors']} |",
        f"| packet paths | {validation['packet_path_errors']} |",
        f"| visible/packet leakage | {validation['leakage_hits']} |",
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
    excluded_pair_ids = read_excluded_pair_ids(args.excluded_pair_ids)
    excluded_pair_rows = read_jsonl(args.excluded_pair_rows)

    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_errors = validate_inputs(gap_summary, label_rows, manifest_rows)
    sheet_errors, path_errors, leakage_hits, pair_summary = validate_label_sheet(
        fieldnames,
        label_rows,
        manifest_rows,
        excluded_pair_ids,
        as_abs(args.label_ready_sheet).parent,
    )
    role_counts = Counter(str(row.get("cell_contrast_role_hidden")) for row in manifest_rows)
    family_counts = Counter(str(row.get("predicate_family")) for row in manifest_rows)
    packet_status_counts = Counter(str(row.get("evidence_packet_status")) for row in label_rows)
    gap_decision_counts = Counter(str(row.get("packet_gap_decision")) for row in label_rows)
    pair_count = len({row["cell_contrast_pair_id_hidden"] for row in manifest_rows})
    expected = gap_summary.get("counts", {})

    status = (
        "h002_reliability_target_v5_cell_contrast_label_readiness_ready_for_label_fill"
        if not input_errors
        and not sheet_errors
        and not path_errors
        and not leakage_hits
        and pair_count == expected.get("label_ready_pairs")
        and len(label_rows) == expected.get("label_ready_rows")
        and role_counts.get("positive_proxy", 0) == role_counts.get("negative_proxy", 0)
        else "h002_reliability_target_v5_cell_contrast_label_readiness_blocked"
    )
    next_todo = (
        "reliability_target_v5_cell_contrast_label_fill"
        if status == "h002_reliability_target_v5_cell_contrast_label_readiness_ready_for_label_fill"
        else "fix_reliability_target_v5_cell_contrast_label_readiness"
    )
    decision = (
        "The 72-row / 36-pair v5 cell-contrast sheet is ready for label fill."
        if status == "h002_reliability_target_v5_cell_contrast_label_readiness_ready_for_label_fill"
        else "The v5 cell-contrast label-ready sheet is blocked by validation errors."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "ready_label_sheet": output_dir / "ready_label_sheet.tsv",
        "ready_manifest_post_label_only": output_dir / "ready_manifest_post_label_only.jsonl",
        "label_schema": output_dir / "label_schema.json",
        "pair_readiness": output_dir / "pair_readiness.csv",
        "input_validation_errors": output_dir / "input_validation_errors.jsonl",
        "sheet_validation_errors": output_dir / "sheet_validation_errors.jsonl",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "leakage_hits": output_dir / "leakage_hits.jsonl",
        "excluded_pair_ids": output_dir / "excluded_pair_ids.txt",
        "excluded_pair_rows_snapshot": output_dir / "excluded_pair_rows_snapshot.jsonl",
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
            "excluded_pair_ids": rel_path(args.excluded_pair_ids),
            "excluded_pair_rows": rel_path(args.excluded_pair_rows),
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
            "label_ready_rows": len(label_rows),
            "label_ready_pairs": pair_count,
            "ready_rows": packet_status_counts.get("ready", 0),
            "limited_view_rows": packet_status_counts.get("limited_view_evaluable", 0),
            "family_counts": dict(sorted(family_counts.items())),
            "role_counts_hidden": dict(sorted(role_counts.items())),
            "packet_status_counts": dict(sorted(packet_status_counts.items())),
            "packet_gap_decision_counts": dict(sorted(gap_decision_counts.items())),
            "excluded_pair_count": len(excluded_pair_ids),
            "excluded_pair_row_count": len(excluded_pair_rows),
        },
        "validation": {
            "input_validation_errors": len(input_errors),
            "sheet_validation_errors": len(sheet_errors),
            "packet_path_errors": len(path_errors),
            "leakage_hits": len(leakage_hits),
            "expected_columns_match": fieldnames == EXPECTED_COLUMNS,
        },
        "label_to_binary_policy": LABEL_TO_BINARY_POLICY,
    }

    write_tsv(output_paths["ready_label_sheet"], label_rows, fieldnames)
    write_jsonl(output_paths["ready_manifest_post_label_only"], manifest_rows)
    write_json(output_paths["label_schema"], label_schema())
    write_csv(output_paths["pair_readiness"], pair_summary)
    write_jsonl(output_paths["input_validation_errors"], input_errors)
    write_jsonl(output_paths["sheet_validation_errors"], sheet_errors)
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_jsonl(output_paths["leakage_hits"], leakage_hits)
    output_paths["excluded_pair_ids"].write_text(
        "\n".join(sorted(excluded_pair_ids)) + ("\n" if excluded_pair_ids else ""),
        encoding="utf-8",
    )
    write_jsonl(output_paths["excluded_pair_rows_snapshot"], excluded_pair_rows)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} "
        f"rows={summary['counts']['label_ready_rows']} "
        f"pairs={summary['counts']['label_ready_pairs']} "
        f"limited_view={summary['counts']['limited_view_rows']} "
        f"path_errors={summary['validation']['packet_path_errors']} "
        f"leakage={summary['validation']['leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
