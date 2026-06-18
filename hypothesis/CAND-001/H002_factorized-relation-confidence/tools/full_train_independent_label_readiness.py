#!/usr/bin/env python3
"""Validate H002 full-train independent label-ready sheets before label fill."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_GAP_DIR = RGA_ROOT / "asset_packet_gap_audit"
DEFAULT_PROTOCOL_DIR = RGA_ROOT / "independent_label_protocol"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_label_readiness"

SHEET_FILES = {
    "all": "label_ready_all_sheet_with_packets.tsv",
    "priority": "label_ready_priority_sheet_with_packets.tsv",
    "support_contact": "label_ready_support_contact_sheet_with_packets.tsv",
    "relative_vertical": "label_ready_relative_vertical_sheet_with_packets.tsv",
    "proximity": "label_ready_proximity_sheet_with_packets.tsv",
}

BASE_LABEL_COLUMNS = [
    "blind_review_id",
    "asset_request_id",
    "scan_id",
    "scene_context_id",
    "subject_id",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_id",
    "object_label",
    "endpoint_pair_note",
    "family_question",
    "positive_cues",
    "negative_cues",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "reviewer_id",
    "review_round",
    "subject_identity_valid",
    "object_identity_valid",
    "object_pair_visible",
    "relation_visible_or_inferable",
    "visual_3d_support",
    "relation_informativeness",
    "independent_relation_label",
    "confidence",
    "evidence_notes",
]
GAP_AUDIT_COLUMNS = ["packet_gap_decision", "packet_gap_reason"]
EXPECTED_COLUMNS = BASE_LABEL_COLUMNS + GAP_AUDIT_COLUMNS

REVIEW_FIELDS = [
    "reviewer_id",
    "review_round",
    "subject_identity_valid",
    "object_identity_valid",
    "object_pair_visible",
    "relation_visible_or_inferable",
    "visual_3d_support",
    "relation_informativeness",
    "independent_relation_label",
    "confidence",
    "evidence_notes",
]

FORBIDDEN_LABEL_SURFACE_FRAGMENTS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "h001_verification",
    "queue",
    "label_match",
    "proposed",
    "role",
    "candidate_axis",
    "prediction_id",
    "final_controlled",
    "failure_taxonomy",
    "matched_gt",
    "matched_predicate",
    "bucket",
    "machine_hint",
    "reason_code",
    "semantic",
    "consistency",
    "disagreement",
    "underconfidence",
]

ALLOWED_REVIEW_VALUES = {
    "subject_identity_valid": ["yes", "no", "uncertain"],
    "object_identity_valid": ["yes", "no", "uncertain"],
    "object_pair_visible": ["yes", "no", "partial", "uncertain"],
    "relation_visible_or_inferable": ["yes", "no", "uncertain"],
    "visual_3d_support": ["supports", "contradicts", "uncertain", "not_evaluable"],
    "relation_informativeness": ["informative", "trivial_dense", "uncertain", "not_evaluable"],
    "independent_relation_label": [
        "reliable_informative",
        "valid_but_trivial_dense",
        "annotation_sparsity_candidate",
        "ontology_mismatch",
        "invalid_relation",
        "invalid_pair",
        "visibility_or_geometry_artifact",
        "abstain_uncertain",
    ],
    "confidence": ["high", "medium", "low"],
}

LABEL_TO_BINARY_POLICY = {
    "positive": [
        "reliable_informative",
        "annotation_sparsity_candidate",
    ],
    "negative": [
        "valid_but_trivial_dense",
        "invalid_relation",
        "invalid_pair",
        "visibility_or_geometry_artifact",
    ],
    "exclude_or_multiclass_only": [
        "ontology_mismatch",
        "abstain_uncertain",
    ],
}

MIN_COVERAGE = {
    "all": 300,
    "priority": 150,
    "support_contact": 150,
    "relative_vertical": 80,
    "proximity": 30,
}

TEXT_SURFACE_COLUMNS = [
    "endpoint_pair_note",
    "family_question",
    "positive_cues",
    "negative_cues",
    "packet_gap_reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-dir", type=Path, default=DEFAULT_GAP_DIR)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        return fieldnames, [dict(row) for row in reader]


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


def nonempty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def path_exists(value: str) -> bool:
    if not value.strip():
        return False
    return as_abs(Path(value)).exists()


def forbidden_hits(value: str) -> list[str]:
    lower = value.lower()
    return [fragment for fragment in FORBIDDEN_LABEL_SURFACE_FRAGMENTS if fragment in lower]


def validate_header(sheet_name: str, fieldnames: list[str]) -> list[dict[str, Any]]:
    errors = []
    if fieldnames != EXPECTED_COLUMNS:
        errors.append(
            {
                "error_type": "unexpected_header",
                "sheet": sheet_name,
                "expected": EXPECTED_COLUMNS,
                "observed": fieldnames,
            }
        )
    for field in fieldnames:
        hits = forbidden_hits(field)
        if hits:
            errors.append(
                {
                    "error_type": "forbidden_header_fragment",
                    "sheet": sheet_name,
                    "field": field,
                    "matches": hits,
                }
            )
    return errors


def validate_rows(
    sheet_name: str,
    rows: list[dict[str, str]],
    internal_ids: set[str],
    excluded_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    leakage_hits: list[dict[str, Any]] = []
    seen = Counter(str(row.get("blind_review_id") or "") for row in rows)
    for blind_id, count in seen.items():
        if count > 1:
            errors.append(
                {
                    "error_type": "duplicate_blind_review_id",
                    "sheet": sheet_name,
                    "blind_review_id": blind_id,
                    "count": count,
                }
            )

    for row_number, row in enumerate(rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        if not blind_id:
            errors.append({"error_type": "missing_blind_review_id", "sheet": sheet_name, "row_number": row_number})
        elif blind_id not in internal_ids:
            errors.append(
                {
                    "error_type": "blind_id_not_in_internal_key",
                    "sheet": sheet_name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                }
            )
        if blind_id in excluded_ids:
            errors.append(
                {
                    "error_type": "excluded_blind_id_in_label_ready_sheet",
                    "sheet": sheet_name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                }
            )

        status = str(row.get("evidence_packet_status") or "")
        if status not in {"ready", "ready_with_packet_caveat"}:
            errors.append(
                {
                    "error_type": "invalid_evidence_packet_status",
                    "sheet": sheet_name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "value": status,
                }
            )
        decision = str(row.get("packet_gap_decision") or "")
        if decision not in {"label_ready", "label_ready_with_packet_caveat"}:
            errors.append(
                {
                    "error_type": "invalid_packet_gap_decision",
                    "sheet": sheet_name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "value": decision,
                }
            )

        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            if not path_exists(str(row.get(field) or "")):
                errors.append(
                    {
                        "error_type": "missing_packet_path",
                        "sheet": sheet_name,
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "value": row.get(field),
                    }
                )

        if any(nonempty(row.get(field)) for field in REVIEW_FIELDS):
            errors.append(
                {
                    "error_type": "review_field_filled_before_label_fill",
                    "sheet": sheet_name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "filled_fields": [field for field in REVIEW_FIELDS if nonempty(row.get(field))],
                }
            )

        for field in TEXT_SURFACE_COLUMNS:
            value = str(row.get(field) or "")
            hits = forbidden_hits(value)
            if hits:
                leakage_hits.append(
                    {
                        "surface": "sheet_text",
                        "sheet": sheet_name,
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "matches": hits,
                        "value": value,
                    }
                )
    return errors, leakage_hits


def scan_packet_text(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    checked: set[str] = set()
    for row in rows:
        blind_id = str(row.get("blind_review_id") or "")
        for field in ["multiview_packet", "pointcloud_or_mesh_packet"]:
            value = str(row.get(field) or "")
            if not value:
                continue
            path = as_abs(Path(value))
            key = str(path)
            if key in checked or not path.exists():
                continue
            checked.add(key)
            text = path.read_text(encoding="utf-8", errors="replace")
            matches = forbidden_hits(text)
            if matches:
                hits.append(
                    {
                        "surface": "packet_text",
                        "blind_review_id": blind_id,
                        "field": field,
                        "path": rel_path(path),
                        "matches": matches,
                    }
                )
    return hits


def sheet_coverage(rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "unique_blind_ids": len({str(row.get("blind_review_id")) for row in rows}),
        "unique_scans": len({str(row.get("scan_id")) for row in rows}),
        "by_family": dict(sorted(Counter(str(row.get("predicate_family")) for row in rows).items())),
        "by_predicate": dict(sorted(Counter(str(row.get("predicate_label")) for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(str(row.get("evidence_packet_status")) for row in rows).items())),
        "by_packet_gap_decision": dict(sorted(Counter(str(row.get("packet_gap_decision")) for row in rows).items())),
    }


def readiness_manifest_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "schema_version": "h002_full_train_independent_label_ready_row_v0",
                "blind_review_id": row["blind_review_id"],
                "asset_request_id": row["asset_request_id"],
                "scan_id": row["scan_id"],
                "scene_context_id": row["scene_context_id"],
                "subject_id": row["subject_id"],
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "predicate_family": row["predicate_family"],
                "object_id": row["object_id"],
                "object_label": row["object_label"],
                "evidence_packet_status": row["evidence_packet_status"],
                "packet_gap_decision": row["packet_gap_decision"],
                "multiview_packet": row["multiview_packet"],
                "pointcloud_or_mesh_packet": row["pointcloud_or_mesh_packet"],
                "contact_or_context_sheet": row["contact_or_context_sheet"],
                "allowed_use": "train-only independent label fill before posterior diagnostics",
            }
        )
    return output


def build_ingestion_schema(protocol: dict[str, Any], protocol_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": "h002_full_train_independent_label_ingestion_schema_v0",
        "join_key": "blind_review_id",
        "input_sheet": "label_ready_all_sheet_with_packets.tsv after reviewer fields are filled",
        "required_completion_fields": [
            "reviewer_id",
            "review_round",
            "subject_identity_valid",
            "object_identity_valid",
            "object_pair_visible",
            "relation_visible_or_inferable",
            "visual_3d_support",
            "relation_informativeness",
            "independent_relation_label",
            "confidence",
        ],
        "optional_completion_fields": ["evidence_notes"],
        "allowed_review_values": ALLOWED_REVIEW_VALUES,
        "label_to_binary_policy": protocol.get("label_to_binary_policy", LABEL_TO_BINARY_POLICY),
        "post_label_join_only": {
            "internal_key": rel_path(protocol_dir / "internal_key.jsonl"),
            "hidden_fields_allowed_after_label_lock": [
                "prediction_id_hidden",
                "queue_kind_hidden",
                "candidate_axis_hidden",
                "proposed_audit_role_hidden",
                "label_match_status_hidden",
                "geometry_status_hidden",
                "semantic_rank_hidden",
                "rank_band_hidden",
                "semantic_score_raw_hidden",
                "semantic_score_norm_hidden",
                "p_geom_valid_hidden",
                "consistency_score_hidden",
                "disagreement_score_hidden",
                "underconfidence_score_hidden",
            ],
            "hidden_fields_must_not_be_model_inputs_before_label_lock": True,
        },
        "target_outputs_after_ingestion": {
            "validated_labels.jsonl": "all completed labels joined to hidden provenance for post-label analysis only",
            "binary_targets.jsonl": "positive/negative independent labels for train-only posterior diagnostics",
            "multiclass_targets.jsonl": "all independent label classes for taxonomy and error analysis",
            "ingestion_errors.jsonl": "schema, duplicate-id, invalid-label, or incomplete-row errors",
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "vmv_model_input_allowed": False,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Independent Label Readiness",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage readiness check.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- This stage does not fill labels.",
        "- Multi-view and mesh packets remain audit evidence only.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Coverage",
        "",
        "| Sheet | Rows | Scans | Minimum | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name, item in summary["sheets"].items():
        coverage = item["coverage"]
        threshold = summary["coverage_thresholds"].get(name, 0)
        status = "pass" if coverage["rows"] >= threshold else "fail"
        lines.append(
            f"| `{name}` | {coverage['rows']} | {coverage['unique_scans']} | {threshold} | `{status}` |"
        )
    lines.extend(
        [
            "",
            "All-sheet family coverage:",
            "",
            "| Family | Rows |",
            "| --- | ---: |",
        ]
    )
    for key, value in summary["sheets"]["all"]["coverage"]["by_family"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "All-sheet predicate coverage:",
            "",
            "| Predicate | Rows |",
            "| --- | ---: |",
        ]
    )
    for key, value in summary["sheets"]["all"]["coverage"]["by_predicate"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Check | Count |",
            "| --- | ---: |",
            f"| schema/path/review-field errors | {summary['counts']['errors']} |",
            f"| leakage hits | {summary['counts']['leakage_hits']} |",
            f"| label-ready rows | {summary['counts']['label_ready_rows']} |",
            f"| excluded rows | {summary['counts']['excluded_rows']} |",
            "",
            "## Ingestion Schema",
            "",
            "Prepared:",
            "",
            "```text",
            summary["artifacts"]["label_ingestion_schema"],
            "```",
            "",
            "The hidden internal key is joined only after independent labels are locked.",
            "",
            "## Output Artifacts",
            "",
            "```text",
            summary["artifacts"]["summary"],
            summary["artifacts"]["report"],
            summary["artifacts"]["readiness_manifest"],
            summary["artifacts"]["readiness_errors"],
            summary["artifacts"]["leakage_hits"],
            summary["artifacts"]["coverage"],
            summary["artifacts"]["label_ingestion_schema"],
            "```",
            "",
            "## Next TODO",
            "",
            summary["next_todo"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    gap_dir = as_abs(args.gap_dir)
    protocol_dir = as_abs(args.protocol_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    protocol = read_json(protocol_dir / "protocol.json")
    internal_rows = read_jsonl(protocol_dir / "internal_key.jsonl")
    internal_ids = {str(row["blind_review_id"]) for row in internal_rows}
    excluded_ids = {
        line.strip()
        for line in (gap_dir / "excluded_blind_ids.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    sheets: dict[str, Any] = {}
    all_errors: list[dict[str, Any]] = []
    leakage_hits: list[dict[str, Any]] = []
    all_rows: list[dict[str, str]] = []
    coverage_failures: list[dict[str, Any]] = []

    for name, filename in SHEET_FILES.items():
        path = gap_dir / filename
        fieldnames, rows = read_tsv(path)
        header_errors = validate_header(name, fieldnames)
        row_errors, row_leakage = validate_rows(name, rows, internal_ids, excluded_ids)
        all_errors.extend(header_errors + row_errors)
        leakage_hits.extend(row_leakage)
        coverage = sheet_coverage(rows)
        threshold = MIN_COVERAGE[name]
        if coverage["rows"] < threshold:
            coverage_failures.append(
                {
                    "sheet": name,
                    "rows": coverage["rows"],
                    "minimum": threshold,
                }
            )
        sheets[name] = {
            "path": rel_path(path),
            "header": fieldnames,
            "coverage": coverage,
            "minimum_rows": threshold,
        }
        if name == "all":
            all_rows = rows

    leakage_hits.extend(scan_packet_text(all_rows))

    if coverage_failures:
        all_errors.extend({"error_type": "coverage_below_minimum", **item} for item in coverage_failures)

    label_ready_ids = {str(row["blind_review_id"]) for row in all_rows}
    missing_from_all = internal_ids - label_ready_ids - excluded_ids
    if missing_from_all:
        all_errors.append(
            {
                "error_type": "internal_ids_neither_label_ready_nor_excluded",
                "count": len(missing_from_all),
                "sample": sorted(missing_from_all)[:20],
            }
        )

    manifest_rows = readiness_manifest_rows(all_rows)
    schema = build_ingestion_schema(protocol, protocol_dir)
    coverage = {
        "schema_version": "h002_full_train_independent_label_readiness_coverage_v0",
        "coverage_thresholds": MIN_COVERAGE,
        "sheets": {name: item["coverage"] for name, item in sheets.items()},
    }

    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    manifest_path = output_dir / "label_ready_manifest.jsonl"
    errors_path = output_dir / "readiness_errors.jsonl"
    leakage_path = output_dir / "leakage_hits.jsonl"
    coverage_path = output_dir / "coverage.json"
    schema_path = output_dir / "label_ingestion_schema.json"

    status = (
        "full_train_independent_label_readiness_ready_for_label_fill"
        if not all_errors and not leakage_hits
        else "full_train_independent_label_readiness_blocked"
    )
    decision = (
        "The label-ready sheets pass schema, leakage, packet-path, excluded-id, and coverage checks. "
        "Independent label fill can proceed on the 355-row all sheet or the 179-row priority sheet."
        if status.endswith("ready_for_label_fill")
        else "The label-ready sheets still have readiness errors or leakage hits. Fix those before label fill."
    )
    next_todo = (
        "full_train_independent_label_fill: fill independent_relation_label and supporting review fields, "
        "then run ingestion before any posterior smoke."
        if status.endswith("ready_for_label_fill")
        else "fix_full_train_independent_label_readiness_errors"
    )

    summary = {
        "schema_version": "h002_full_train_independent_label_readiness_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "gap_dir": rel_path(gap_dir),
            "protocol_dir": rel_path(protocol_dir),
            "protocol": rel_path(protocol_dir / "protocol.json"),
            "internal_key": rel_path(protocol_dir / "internal_key.jsonl"),
            "excluded_blind_ids": rel_path(gap_dir / "excluded_blind_ids.txt"),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "fills_labels": False,
            "vmv_model_input_allowed": False,
        },
        "counts": {
            "internal_key_rows": len(internal_rows),
            "label_ready_rows": len(all_rows),
            "excluded_rows": len(excluded_ids),
            "errors": len(all_errors),
            "leakage_hits": len(leakage_hits),
            "review_started_rows": sum(any(nonempty(row.get(field)) for field in REVIEW_FIELDS) for row in all_rows),
        },
        "coverage_thresholds": MIN_COVERAGE,
        "sheets": sheets,
        "artifacts": {
            "summary": rel_path(summary_path),
            "report": rel_path(report_path),
            "readiness_manifest": rel_path(manifest_path),
            "readiness_errors": rel_path(errors_path),
            "leakage_hits": rel_path(leakage_path),
            "coverage": rel_path(coverage_path),
            "label_ingestion_schema": rel_path(schema_path),
        },
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(summary_path, summary)
    write_json(coverage_path, coverage)
    write_json(schema_path, schema)
    write_jsonl(manifest_path, manifest_rows)
    write_jsonl(errors_path, all_errors)
    write_jsonl(leakage_path, leakage_hits)
    write_report(report_path, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} rows={summary['counts']['label_ready_rows']} "
        f"excluded={summary['counts']['excluded_rows']} errors={summary['counts']['errors']} "
        f"leakage={summary['counts']['leakage_hits']} validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
