#!/usr/bin/env python3
"""Validate selected support/vertical label-readiness before independent label fill."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke
import full_train_independent_support_vertical_audit_packet as audit_packet


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_PACKET_DIR = RGA_ROOT / "independent_support_vertical_audit_packet_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_label_readiness_codex_ver"

SHEET_FILES = {
    "support_vertical": "support_vertical_audit_sheet.tsv",
    "support_contact": "support_contact_audit_sheet.tsv",
    "relative_vertical": "relative_vertical_audit_sheet.tsv",
}

REQUIRED_REVIEW_FIELDS = [
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
]
OPTIONAL_REVIEW_FIELDS = ["evidence_notes"]
REVIEW_FIELDS = REQUIRED_REVIEW_FIELDS + OPTIONAL_REVIEW_FIELDS

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

EXPECTED_COUNTS = {
    "support_vertical": 127,
    "support_contact": 72,
    "relative_vertical": 55,
    "proximity_risk": 31,
}

FORBIDDEN_LABELER_SURFACE_SUBSTRINGS = audit_packet.FORBIDDEN_LABELER_SURFACE_SUBSTRINGS
FORBIDDEN_PACKET_TEXT_SUBSTRINGS = audit_packet.FORBIDDEN_PACKET_TEXT_SUBSTRINGS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = smoke.as_abs(path)
    try:
        return str(path.relative_to(smoke.REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
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
    with smoke.as_abs(path).open("r", newline="", encoding="utf-8") as handle:
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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
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
    return smoke.as_abs(Path(value)).exists()


def forbidden_header_hits(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits = []
    for field in fieldnames:
        lowered = field.lower()
        for token in FORBIDDEN_LABELER_SURFACE_SUBSTRINGS:
            if token in lowered:
                hits.append({"surface": "header", "field": field, "forbidden_token": token})
    return hits


def forbidden_value_hits(rows: list[dict[str, str]], fields: list[str]) -> list[dict[str, Any]]:
    hits = []
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        for field in fields:
            value = str(row.get(field, ""))
            lowered = value.lower()
            for token in FORBIDDEN_LABELER_SURFACE_SUBSTRINGS:
                if token in lowered:
                    hits.append(
                        {
                            "surface": "value",
                            "row_number": row_number,
                            "blind_review_id": blind_id,
                            "field": field,
                            "forbidden_token": token,
                            "value_preview": value[:120],
                        }
                    )
    return hits


def packet_text_hits(rows: list[dict[str, str]], limit: int = 40) -> list[dict[str, Any]]:
    hits = []
    paths: list[Path] = []
    seen = set()
    for row in rows:
        for field in ["multiview_packet", "pointcloud_or_mesh_packet"]:
            value = row.get(field, "")
            if not value:
                continue
            path = smoke.as_abs(Path(value))
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
        for token in FORBIDDEN_PACKET_TEXT_SUBSTRINGS:
            if token in text:
                hits.append(
                    {
                        "surface": "packet_text",
                        "path": rel_path(path),
                        "forbidden_token": token,
                    }
                )
    return hits


def validate_sheet(
    name: str,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    *,
    expected_count: int,
    expected_families: set[str],
    internal_ids: set[str],
    risk_ids: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    errors = []
    leakage = []
    if fieldnames != audit_packet.LABELER_FIELDS:
        errors.append(
            {
                "error_type": "unexpected_header",
                "sheet": name,
                "expected": audit_packet.LABELER_FIELDS,
                "observed": fieldnames,
            }
        )
    leakage.extend(forbidden_header_hits(fieldnames))
    if len(rows) != expected_count:
        errors.append(
            {
                "error_type": "unexpected_row_count",
                "sheet": name,
                "expected": expected_count,
                "observed": len(rows),
            }
        )
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
        elif blind_id not in internal_ids:
            errors.append(
                {
                    "error_type": "blind_id_missing_from_internal_reference",
                    "sheet": name,
                    "blind_review_id": blind_id,
                }
            )
        if blind_id in risk_ids:
            errors.append(
                {
                    "error_type": "proximity_risk_id_in_labeler_sheet",
                    "sheet": name,
                    "blind_review_id": blind_id,
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
        if row.get("audit_scope") != "selected_support_vertical_claim_scope":
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
        filled_review = [field for field in REVIEW_FIELDS if nonempty(row.get(field))]
        if filled_review:
            errors.append(
                {
                    "error_type": "review_field_filled_before_label_fill",
                    "sheet": name,
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "filled_fields": filled_review,
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
    leakage.extend(forbidden_value_hits(rows, text_fields))
    coverage = {
        "rows": len(rows),
        "unique_blind_ids": len(blind_counts),
        "unique_scans": len({row.get("scan_id", "") for row in rows}),
        "by_family": dict(sorted(Counter(row.get("predicate_family", "") for row in rows).items())),
        "by_predicate": dict(sorted(Counter(row.get("predicate_label", "") for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row.get("evidence_packet_status", "") for row in rows).items())),
    }
    return coverage, errors, leakage


def validate_internal_reference(
    internal_rows: list[dict[str, Any]],
    selected_ids: set[str],
) -> list[dict[str, Any]]:
    errors = []
    counts = Counter(str(row.get("blind_review_id", "")) for row in internal_rows)
    for blind_id, count in counts.items():
        if count > 1:
            errors.append({"error_type": "duplicate_internal_reference_id", "blind_review_id": blind_id, "count": count})
    missing = selected_ids - set(counts)
    extra = set(counts) - selected_ids
    if missing:
        errors.append({"error_type": "selected_ids_missing_from_internal_reference", "count": len(missing), "sample": sorted(missing)[:20]})
    if extra:
        errors.append({"error_type": "internal_reference_has_extra_ids", "count": len(extra), "sample": sorted(extra)[:20]})
    for row in internal_rows:
        if row.get("post_label_join_only") is not True:
            errors.append(
                {
                    "error_type": "internal_reference_not_marked_post_label_only",
                    "blind_review_id": row.get("blind_review_id"),
                }
            )
    return errors


def validate_risk_slice(risk_rows: list[dict[str, Any]], selected_ids: set[str]) -> list[dict[str, Any]]:
    errors = []
    risk_ids = {str(row.get("blind_review_id", "")) for row in risk_rows}
    if len(risk_rows) != EXPECTED_COUNTS["proximity_risk"]:
        errors.append(
            {
                "error_type": "unexpected_proximity_risk_count",
                "expected": EXPECTED_COUNTS["proximity_risk"],
                "observed": len(risk_rows),
            }
        )
    overlap = risk_ids & selected_ids
    if overlap:
        errors.append(
            {
                "error_type": "proximity_risk_overlaps_selected_labeler_sheet",
                "count": len(overlap),
                "sample": sorted(overlap)[:20],
            }
        )
    for row in risk_rows:
        if row.get("predicate_family") != "proximity":
            errors.append(
                {
                    "error_type": "non_proximity_row_in_risk_slice",
                    "blind_review_id": row.get("blind_review_id"),
                    "predicate_family": row.get("predicate_family"),
                }
            )
    return errors


def build_completion_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_support_vertical_label_completion_schema_v1",
        "join_key": "blind_review_id",
        "input_sheet": "support_vertical_audit_sheet.tsv",
        "family_specific_sheets": [
            "support_contact_audit_sheet.tsv",
            "relative_vertical_audit_sheet.tsv",
        ],
        "required_completion_fields": REQUIRED_REVIEW_FIELDS,
        "optional_completion_fields": OPTIONAL_REVIEW_FIELDS,
        "allowed_review_values": ALLOWED_REVIEW_VALUES,
        "label_to_binary_policy": LABEL_TO_BINARY_POLICY,
        "post_label_join_only": {
            "internal_reference": "internal_reference_post_label_only.jsonl",
            "hidden_fields_must_not_be_visible_before_label_lock": True,
            "hidden_fields_must_not_be_model_inputs": True,
        },
        "excluded_from_main_label_fill": {
            "proximity_risk_slice": "proximity_risk_slice_post_label_only.jsonl",
            "reason": "proximity failed revised-factor claim-boundary controls",
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_labels": False,
            "trains_new_posterior": False,
            "multi_view_as_model_input": False,
        },
    }


def manifest_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "schema_version": "h002_support_vertical_label_ready_row_v1",
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
                "multiview_packet": row["multiview_packet"],
                "pointcloud_or_mesh_packet": row["pointcloud_or_mesh_packet"],
                "contact_or_context_sheet": row["contact_or_context_sheet"],
                "allowed_use": "train-only selected support/vertical independent label fill",
            }
        )
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full-Train Support/Vertical Label Readiness",
        "",
        "## Boundary",
        "",
        "- Split: Open3DSG train-only.",
        "- This stage validates label-fill readiness; it does not fill labels.",
        "- Selected scope: support_contact + relative_vertical.",
        "- Proximity remains excluded from the main label-fill path.",
        "- Hidden metadata is joined only after label lock.",
        "- Multi-view/mesh packets are audit evidence only, not posterior input.",
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
            "Support/vertical family coverage:",
            "",
            "| Family | Rows |",
            "| --- | ---: |",
        ]
    )
    for family, count in summary["sheets"]["support_vertical"]["coverage"]["by_family"].items():
        lines.append(f"| `{family}` | {count} |")
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Check | Count |",
            "| --- | ---: |",
            f"| readiness errors | {summary['counts']['errors']} |",
            f"| leakage hits | {summary['counts']['leakage_hits']} |",
            f"| selected label-ready rows | {summary['counts']['selected_rows']} |",
            f"| internal reference rows | {summary['counts']['internal_reference_rows']} |",
            f"| proximity risk rows | {summary['counts']['proximity_risk_rows']} |",
            "",
            "## Completion Schema",
            "",
            "Prepared:",
            "",
            "```text",
            summary["output_paths"]["completion_schema"],
            "```",
            "",
            "Allowed review values are frozen in the schema. The hidden internal reference must be joined only after label lock.",
            "",
            "## Output Files",
            "",
            "```text",
            summary["output_paths"]["summary_json"],
            summary["output_paths"]["report_md"],
            summary["output_paths"]["label_ready_manifest"],
            summary["output_paths"]["completion_schema"],
            summary["output_paths"]["readiness_errors"],
            summary["output_paths"]["leakage_hits"],
            "```",
            "",
            "## Next TODO",
            "",
            summary["next_todo"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    packet_dir = smoke.as_abs(args.packet_dir)
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    packet_summary = read_json(packet_dir / "summary.json")
    internal_rows = read_jsonl(packet_dir / "internal_reference_post_label_only.jsonl")
    risk_rows = read_jsonl(packet_dir / "proximity_risk_slice_post_label_only.jsonl")
    internal_ids = {str(row.get("blind_review_id", "")) for row in internal_rows}
    risk_ids = {str(row.get("blind_review_id", "")) for row in risk_rows}

    sheet_results: dict[str, Any] = {}
    all_errors: list[dict[str, Any]] = []
    all_leakage: list[dict[str, Any]] = []
    all_rows: list[dict[str, str]] = []

    sheet_specs = {
        "support_vertical": (EXPECTED_COUNTS["support_vertical"], {"support_contact", "relative_vertical"}),
        "support_contact": (EXPECTED_COUNTS["support_contact"], {"support_contact"}),
        "relative_vertical": (EXPECTED_COUNTS["relative_vertical"], {"relative_vertical"}),
    }

    for name, filename in SHEET_FILES.items():
        fieldnames, rows = read_tsv(packet_dir / filename)
        expected_count, expected_families = sheet_specs[name]
        coverage, errors, leakage = validate_sheet(
            name,
            fieldnames,
            rows,
            expected_count=expected_count,
            expected_families=expected_families,
            internal_ids=internal_ids,
            risk_ids=risk_ids,
        )
        all_errors.extend(errors)
        all_leakage.extend(leakage)
        if name == "support_vertical":
            all_rows = rows
        sheet_results[name] = {
            "path": rel_path(packet_dir / filename),
            "coverage": coverage,
            "status": "pass" if not errors and not leakage else "fail",
        }

    selected_ids = {str(row.get("blind_review_id", "")) for row in all_rows}
    all_errors.extend(validate_internal_reference(internal_rows, selected_ids))
    all_errors.extend(validate_risk_slice(risk_rows, selected_ids))
    all_leakage.extend(packet_text_hits(all_rows))

    status = (
        "full_train_independent_support_vertical_label_readiness_ready_for_label_fill"
        if not all_errors and not all_leakage
        else "full_train_independent_support_vertical_label_readiness_blocked"
    )
    decision = (
        "Selected support/vertical audit sheets pass schema, path, leakage, internal-reference, and risk-slice checks. "
        "Independent label fill can proceed on the 127-row support_vertical sheet."
        if status.endswith("ready_for_label_fill")
        else "Readiness is blocked by schema, leakage, path, internal-reference, or risk-slice errors."
    )
    next_todo = (
        "full_train_independent_support_vertical_label_fill"
        if status.endswith("ready_for_label_fill")
        else "fix_full_train_independent_support_vertical_label_readiness"
    )

    output_paths = {
        "summary_json": output_dir / "summary.json",
        "report_md": output_dir / "report.md",
        "label_ready_manifest": output_dir / "label_ready_manifest.jsonl",
        "completion_schema": output_dir / "completion_schema.json",
        "readiness_errors": output_dir / "readiness_errors.jsonl",
        "leakage_hits": output_dir / "leakage_hits.jsonl",
        "support_vertical_label_fill_sheet": output_dir / "support_vertical_label_fill_sheet.tsv",
    }
    completion_schema = build_completion_schema()
    summary = {
        "schema_version": "h002_full_train_independent_support_vertical_label_readiness_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation_used": False,
        "input": {
            "packet_dir": rel_path(packet_dir),
            "packet_summary": rel_path(packet_dir / "summary.json"),
            "packet_status": packet_summary.get("status"),
        },
        "boundary": {
            "split": "train_only",
            "selected_scope": ["support_contact", "relative_vertical"],
            "excluded_from_main_label_fill": ["proximity"],
            "fills_labels": False,
            "validation_usage": False,
            "test_usage": False,
            "multi_view_as_model_input": False,
            "hidden_metadata_join_before_label_lock": False,
        },
        "counts": {
            "selected_rows": len(all_rows),
            "internal_reference_rows": len(internal_rows),
            "proximity_risk_rows": len(risk_rows),
            "errors": len(all_errors),
            "leakage_hits": len(all_leakage),
            "review_started_rows": sum(any(nonempty(row.get(field)) for field in REVIEW_FIELDS) for row in all_rows),
        },
        "allowed_review_values": ALLOWED_REVIEW_VALUES,
        "label_to_binary_policy": LABEL_TO_BINARY_POLICY,
        "sheets": sheet_results,
        "decision": decision,
        "next_todo": next_todo,
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
    }

    write_json(output_paths["summary_json"], summary)
    write_json(output_paths["completion_schema"], completion_schema)
    write_jsonl(output_paths["label_ready_manifest"], manifest_rows(all_rows))
    write_jsonl(output_paths["readiness_errors"], all_errors)
    write_jsonl(output_paths["leakage_hits"], all_leakage)
    write_tsv(output_paths["support_vertical_label_fill_sheet"], all_rows, audit_packet.LABELER_FIELDS)
    write_report(output_paths["report_md"], summary)

    print(
        "status={status} validation_used={validation_used} rows={rows} errors={errors} "
        "leakage={leakage} next={next_todo}".format(
            status=summary["status"],
            validation_used=summary["validation_used"],
            rows=summary["counts"]["selected_rows"],
            errors=summary["counts"]["errors"],
            leakage=summary["counts"]["leakage_hits"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
