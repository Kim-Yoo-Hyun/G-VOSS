#!/usr/bin/env python3
"""Validate support/vertical v2 factual-axis label-readiness."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_audit_packet as audit_packet


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_POLICY_DIR = RGA_ROOT / "independent_support_vertical_label_policy_revision_codex_ver"
DEFAULT_PACKET_DIR = RGA_ROOT / "independent_support_vertical_audit_packet_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_label_readiness_codex_ver"

SHEET_FILES = {
    "support_vertical": "support_vertical_v2_label_sheet.tsv",
    "support_contact": "support_contact_v2_label_sheet.tsv",
    "relative_vertical": "relative_vertical_v2_label_sheet.tsv",
}

EXPECTED_COUNTS = {
    "support_vertical": 127,
    "support_contact": 72,
    "relative_vertical": 55,
    "proximity_risk": 31,
}

BASE_LABELER_FIELDS = [
    "blind_review_id",
    "audit_scope",
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
    "witness_distance_xy_m",
    "witness_distance_3d_m",
    "witness_center_delta_z_m",
    "witness_vertical_gap_subject_on_object_m",
    "witness_projected_iou_xy",
    "witness_subject_overlap_xy",
    "witness_object_overlap_xy",
    "witness_normalized_distance_xy",
    "witness_support_contact_gap_abs",
    "witness_support_contact_xy_overlap",
    "witness_relative_vertical_signed_margin",
    "witness_relative_vertical_sign_agreement",
]

V2_COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_validity_v2",
    "pair_visibility_v2",
    "relation_geometry_answer_v2",
    "geometry_evidence_strength_v2",
    "relation_informativeness_v2",
    "ontology_fit_v2",
    "uncertainty_reason_v2",
    "audit_notes_v2",
]

EXPECTED_HEADER = BASE_LABELER_FIELDS + V2_COMPLETION_FIELDS

FORBIDDEN_EXACT_HEADERS = {
    "independent_relation_label",
    "label_use",
    "posterior_target",
    "target_y",
    "binary_target",
    "confidence",
    "subject_identity_valid",
    "object_identity_valid",
    "object_pair_visible",
    "relation_visible_or_inferable",
    "visual_3d_support",
    "relation_informativeness",
    "evidence_notes",
}

FORBIDDEN_HEADER_FRAGMENTS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "h001_verification",
    "queue",
    "label_match",
    "proposed",
    "candidate_axis",
    "prediction_id",
    "posterior",
    "target",
    "final_controlled",
    "failure_taxonomy",
    "matched_gt",
    "matched_predicate",
    "bucket",
    "machine_hint",
    "reason_code",
    "consistency",
    "disagreement",
    "underconfidence",
    "overconfidence",
    "label_source",
    "relation_validity_label",
]

FORBIDDEN_VALUE_FRAGMENTS = [
    "relation_validity_label",
    "posterior_target",
    "target_y",
    "label_use_hidden",
    "proposed_audit_role",
    "label_match_status",
    "geometry_status",
    "rank_band",
    "p_geom_valid",
    "semantic_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy-dir", type=Path, default=DEFAULT_POLICY_DIR)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
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
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def nonempty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def path_exists(value: str) -> bool:
    if not value.strip():
        return False
    return as_abs(Path(value)).exists()


def header_leakage(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in fieldnames:
        lower = field.lower()
        if lower in FORBIDDEN_EXACT_HEADERS:
            hits.append({"surface": "header", "field": field, "forbidden": lower, "match_type": "exact"})
        for fragment in FORBIDDEN_HEADER_FRAGMENTS:
            if fragment in lower:
                hits.append({"surface": "header", "field": field, "forbidden": fragment, "match_type": "fragment"})
    return hits


def value_leakage(rows: list[dict[str, str]], fields: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        for field in fields:
            value = str(row.get(field, ""))
            lower = value.lower()
            for fragment in FORBIDDEN_VALUE_FRAGMENTS:
                if fragment in lower:
                    hits.append(
                        {
                            "surface": "value",
                            "row_number": row_number,
                            "blind_review_id": blind_id,
                            "field": field,
                            "forbidden": fragment,
                            "value_preview": value[:120],
                        }
                    )
    return hits


def packet_text_hits(rows: list[dict[str, str]], limit: int = 40) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    paths: list[Path] = []
    seen = set()
    for row in rows:
        for field in ["multiview_packet", "pointcloud_or_mesh_packet"]:
            value = str(row.get(field, ""))
            if not value:
                continue
            path = as_abs(Path(value))
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            paths.append(path)
        if len(paths) >= limit:
            break
    for path in paths[:limit]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for fragment in audit_packet.FORBIDDEN_PACKET_TEXT_SUBSTRINGS:
            if fragment in text:
                hits.append(
                    {
                        "surface": "packet_text",
                        "path": rel_path(path),
                        "forbidden": fragment,
                    }
                )
    return hits


def validate_schema(schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = schema.get("required_completion_fields", [])
    optional = schema.get("optional_completion_fields", [])
    allowed = schema.get("allowed_review_values", {})
    if schema.get("boundary", {}).get("direct_reliability_label_removed") is not True:
        errors.append({"error_type": "schema_direct_reliability_label_not_removed"})
    if schema.get("boundary", {}).get("binary_target_not_labeler_visible") is not True:
        errors.append({"error_type": "schema_binary_target_visibility_not_blocked"})
    if "independent_relation_label" in required or "independent_relation_label" in optional:
        errors.append({"error_type": "schema_contains_direct_relation_label"})
    for field in required:
        if field not in V2_COMPLETION_FIELDS:
            errors.append({"error_type": "schema_unexpected_required_field", "field": field})
    for field in required:
        if field in {"reviewer_id", "review_round"}:
            continue
        if field not in allowed:
            errors.append({"error_type": "schema_required_field_missing_allowed_values", "field": field})
    if "target_derivation_policy_post_label_only" not in schema:
        errors.append({"error_type": "schema_missing_post_label_target_derivation_policy"})
    return errors


def validate_sheet(
    name: str,
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    *,
    expected_count: int,
    expected_families: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    leakage: list[dict[str, Any]] = []
    if fieldnames != EXPECTED_HEADER:
        errors.append(
            {
                "error_type": "unexpected_header",
                "sheet": name,
                "expected": EXPECTED_HEADER,
                "observed": fieldnames,
            }
        )
    if len(rows) != expected_count:
        errors.append(
            {
                "error_type": "unexpected_row_count",
                "sheet": name,
                "expected": expected_count,
                "observed": len(rows),
            }
        )
    leakage.extend(header_leakage(fieldnames))

    blind_counts = Counter(str(row.get("blind_review_id", "")) for row in rows)
    for blind_id, count in blind_counts.items():
        if not blind_id:
            errors.append({"error_type": "missing_blind_review_id", "sheet": name})
        elif count > 1:
            errors.append(
                {
                    "error_type": "duplicate_blind_review_id",
                    "sheet": name,
                    "blind_review_id": blind_id,
                    "count": count,
                }
            )

    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        family = row.get("predicate_family", "")
        if family not in expected_families:
            errors.append(
                {
                    "error_type": "unexpected_family",
                    "sheet": name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "family": family,
                    "expected": sorted(expected_families),
                }
            )
        if row.get("audit_scope") != "selected_support_vertical_label_policy_v2":
            errors.append(
                {
                    "error_type": "invalid_audit_scope",
                    "sheet": name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "value": row.get("audit_scope"),
                }
            )
        if row.get("evidence_packet_status") not in {"ready", "ready_with_packet_caveat"}:
            errors.append(
                {
                    "error_type": "invalid_evidence_packet_status",
                    "sheet": name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "value": row.get("evidence_packet_status"),
                }
            )
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            if not path_exists(str(row.get(field, ""))):
                errors.append(
                    {
                        "error_type": "missing_packet_path",
                        "sheet": name,
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "value": row.get(field),
                    }
                )
        filled = [field for field in V2_COMPLETION_FIELDS if nonempty(row.get(field))]
        if filled:
            errors.append(
                {
                    "error_type": "v2_completion_field_filled_before_label_fill",
                    "sheet": name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "filled_fields": filled,
                }
            )

    text_fields = [
        "endpoint_pair_note",
        "family_question",
        "positive_cues",
        "negative_cues",
        "multiview_packet",
        "pointcloud_or_mesh_packet",
        "contact_or_context_sheet",
    ]
    leakage.extend(value_leakage(rows, text_fields))
    coverage = {
        "path": rel_path(path),
        "rows": len(rows),
        "unique_blind_ids": len(blind_counts),
        "unique_scans": len({row.get("scan_id", "") for row in rows}),
        "by_family": dict(sorted(Counter(row.get("predicate_family", "") for row in rows).items())),
        "by_predicate": dict(sorted(Counter(row.get("predicate_label", "") for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row.get("evidence_packet_status", "") for row in rows).items())),
    }
    return coverage, errors, leakage


def validate_sheet_sets(all_rows: list[dict[str, str]], support_rows: list[dict[str, str]], vertical_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    all_ids = {row["blind_review_id"] for row in all_rows}
    support_ids = {row["blind_review_id"] for row in support_rows}
    vertical_ids = {row["blind_review_id"] for row in vertical_rows}
    if support_ids & vertical_ids:
        errors.append(
            {
                "error_type": "family_sheet_id_overlap",
                "count": len(support_ids & vertical_ids),
                "sample": sorted(support_ids & vertical_ids)[:20],
            }
        )
    if support_ids | vertical_ids != all_ids:
        errors.append(
            {
                "error_type": "family_sheets_do_not_partition_all_sheet",
                "missing_from_family_sheets": sorted(all_ids - (support_ids | vertical_ids))[:20],
                "extra_in_family_sheets": sorted((support_ids | vertical_ids) - all_ids)[:20],
            }
        )
    return errors


def validate_proximity_risk(packet_dir: Path, selected_ids: set[str]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    risk_rows = read_jsonl(packet_dir / "proximity_risk_slice_post_label_only.jsonl")
    risk_ids = {str(row.get("blind_review_id", "")) for row in risk_rows}
    if len(risk_rows) != EXPECTED_COUNTS["proximity_risk"]:
        errors.append(
            {
                "error_type": "unexpected_proximity_risk_count",
                "expected": EXPECTED_COUNTS["proximity_risk"],
                "observed": len(risk_rows),
            }
        )
    overlap = selected_ids & risk_ids
    if overlap:
        errors.append(
            {
                "error_type": "proximity_risk_overlaps_v2_sheet",
                "count": len(overlap),
                "sample": sorted(overlap)[:20],
            }
        )
    return errors


def manifest_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "schema_version": "h002_support_vertical_v2_label_ready_row",
                "blind_review_id": row["blind_review_id"],
                "audit_scope": row["audit_scope"],
                "scan_id": row["scan_id"],
                "scene_context_id": row["scene_context_id"],
                "subject_id": row["subject_id"],
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "predicate_family": row["predicate_family"],
                "object_id": row["object_id"],
                "object_label": row["object_label"],
                "evidence_packet_status": row["evidence_packet_status"],
                "allowed_use": "train-only support/vertical v2 factual-axis label fill",
            }
        )
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Support/Vertical V2 Label Readiness",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage readiness.",
        "- This stage validates v2 label-fill readiness; it does not fill labels.",
        "- Direct reliability labels and posterior targets must not be labeler-visible.",
        "- Hidden metadata is joined only after label lock.",
        "- Multi-view/mesh packets remain audit evidence only.",
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
        "| Sheet | Rows | Scans | Status |",
        "| --- | ---: | ---: | --- |",
    ]
    for name, sheet in summary["sheets"].items():
        lines.append(
            f"| `{name}` | {sheet['coverage']['rows']} | {sheet['coverage']['unique_scans']} | `{sheet['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Check | Count |",
            "| --- | ---: |",
            f"| readiness errors | {summary['counts']['errors']} |",
            f"| leakage hits | {summary['counts']['leakage_hits']} |",
            f"| selected rows | {summary['counts']['selected_rows']} |",
            f"| support_contact rows | {summary['counts']['support_contact_rows']} |",
            f"| relative_vertical rows | {summary['counts']['relative_vertical_rows']} |",
            f"| v2 completion started rows | {summary['counts']['v2_completion_started_rows']} |",
            "",
            "## V2 Schema",
            "",
            "V2 removes direct `independent_relation_label` and derives targets only after label lock.",
            "",
            "```text",
            summary["output_paths"]["v2_completion_schema"],
            "```",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    policy_dir = as_abs(args.policy_dir)
    packet_dir = as_abs(args.packet_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    policy_summary = read_json(policy_dir / "summary.json")
    schema = read_json(policy_dir / "v2_completion_schema.json")
    feature_contract = read_json(policy_dir / "v2_feature_contract.json")

    all_errors: list[dict[str, Any]] = []
    all_leakage: list[dict[str, Any]] = []
    all_errors.extend(validate_schema(schema))

    sheet_results: dict[str, Any] = {}
    sheet_rows: dict[str, list[dict[str, str]]] = {}
    sheet_specs = {
        "support_vertical": (EXPECTED_COUNTS["support_vertical"], {"support_contact", "relative_vertical"}),
        "support_contact": (EXPECTED_COUNTS["support_contact"], {"support_contact"}),
        "relative_vertical": (EXPECTED_COUNTS["relative_vertical"], {"relative_vertical"}),
    }

    for name, filename in SHEET_FILES.items():
        path = policy_dir / filename
        fieldnames, rows = read_tsv(path)
        expected_count, expected_families = sheet_specs[name]
        coverage, errors, leakage = validate_sheet(
            name,
            path,
            fieldnames,
            rows,
            expected_count=expected_count,
            expected_families=expected_families,
        )
        all_errors.extend(errors)
        all_leakage.extend(leakage)
        sheet_rows[name] = rows
        sheet_results[name] = {
            "path": rel_path(path),
            "coverage": coverage,
            "status": "pass" if not errors and not leakage else "fail",
        }

    all_errors.extend(validate_sheet_sets(sheet_rows["support_vertical"], sheet_rows["support_contact"], sheet_rows["relative_vertical"]))
    selected_ids = {row["blind_review_id"] for row in sheet_rows["support_vertical"]}
    all_errors.extend(validate_proximity_risk(packet_dir, selected_ids))
    all_leakage.extend(packet_text_hits(sheet_rows["support_vertical"]))

    started_rows = sum(
        any(nonempty(row.get(field)) for field in V2_COMPLETION_FIELDS)
        for row in sheet_rows["support_vertical"]
    )
    all_errors.extend(
        [
            {
                "error_type": "feature_contract_allows_audit_only_field_as_input",
                "field": field,
            }
            for field in V2_COMPLETION_FIELDS
            if field in feature_contract.get("allowed_deployable_inputs_after_label_lock", [])
        ]
    )

    status = (
        "full_train_independent_support_vertical_v2_label_readiness_ready_for_fill"
        if not all_errors and not all_leakage
        else "full_train_independent_support_vertical_v2_label_readiness_blocked"
    )
    decision = (
        "V2 support/vertical sheet passes schema, leakage, path, family partition, and proximity-exclusion checks. "
        "V2 factual-axis label fill may proceed."
        if status.endswith("ready_for_fill")
        else "V2 support/vertical sheet is blocked by schema, leakage, path, family partition, or proximity-exclusion errors."
    )
    next_todo = (
        "full_train_independent_support_vertical_v2_label_fill"
        if status.endswith("ready_for_fill")
        else "fix_full_train_independent_support_vertical_v2_label_readiness"
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "v2_completion_schema": output_dir / "v2_completion_schema.json",
        "v2_feature_contract": output_dir / "v2_feature_contract.json",
        "v2_label_ready_manifest": output_dir / "v2_label_ready_manifest.jsonl",
        "readiness_errors": output_dir / "readiness_errors.jsonl",
        "leakage_hits": output_dir / "leakage_hits.jsonl",
        "support_vertical_v2_label_fill_sheet": output_dir / "support_vertical_v2_label_fill_sheet.tsv",
    }

    summary = {
        "schema_version": "h002_support_vertical_v2_label_readiness_summary",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "policy_dir": rel_path(policy_dir),
            "policy_summary": rel_path(policy_dir / "summary.json"),
            "policy_status": policy_summary.get("status"),
            "packet_dir": rel_path(packet_dir),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_labels": False,
            "trains_new_posterior": False,
            "direct_reliability_label_removed": True,
            "binary_target_not_labeler_visible": True,
            "hidden_metadata_join_before_label_lock": False,
            "multi_view_as_model_input": False,
        },
        "counts": {
            "selected_rows": len(sheet_rows["support_vertical"]),
            "support_contact_rows": len(sheet_rows["support_contact"]),
            "relative_vertical_rows": len(sheet_rows["relative_vertical"]),
            "errors": len(all_errors),
            "leakage_hits": len(all_leakage),
            "v2_completion_started_rows": started_rows,
        },
        "sheets": sheet_results,
        "decision": decision,
        "next_todo": next_todo,
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["v2_completion_schema"], schema)
    write_json(output_paths["v2_feature_contract"], feature_contract)
    write_jsonl(output_paths["v2_label_ready_manifest"], manifest_rows(sheet_rows["support_vertical"]))
    write_jsonl(output_paths["readiness_errors"], all_errors)
    write_jsonl(output_paths["leakage_hits"], all_leakage)
    write_tsv(output_paths["support_vertical_v2_label_fill_sheet"], EXPECTED_HEADER, sheet_rows["support_vertical"])
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(
        f"status={summary['status']} rows={counts['selected_rows']} "
        f"support={counts['support_contact_rows']} vertical={counts['relative_vertical_rows']} "
        f"errors={counts['errors']} leakage={counts['leakage_hits']} "
        f"started={counts['v2_completion_started_rows']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
