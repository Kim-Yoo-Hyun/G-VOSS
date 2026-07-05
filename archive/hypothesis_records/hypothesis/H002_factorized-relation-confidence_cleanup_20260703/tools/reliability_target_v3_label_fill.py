#!/usr/bin/env python3
"""Fill the H002 reliability target v3 sheet as a Codex proxy."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_external_review_fill as visible_fill


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
PLAN_DIR = RGA_ROOT / "reliability_target_v3_positive_anchor_plan"
DEFAULT_INPUT_SHEET = PLAN_DIR / "v3_positive_anchor_label_sheet.tsv"
DEFAULT_SCHEMA = PLAN_DIR / "v3_label_schema.json"
DEFAULT_MANIFEST = PLAN_DIR / "v3_positive_anchor_manifest_post_label_only.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_label_fill_codex_proxy_user_requested"

REVIEWER_ID = "(codex_proxy_v3_user_requested_visible_heuristic)"
REVIEW_ROUND = "1"

COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_v3",
    "pair_evaluability_v3",
    "geometry_support_v3",
    "relation_usefulness_v3",
    "relation_reliability_v3",
    "primary_reason_v3",
    "uncertainty_reason_v3",
]

GENERIC_LABELS = {
    "item",
    "object",
    "objects",
    "furniture",
    "thing",
    "stuff",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
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
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def packet_paths_exist(row: dict[str, str]) -> bool:
    for key in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
        value = row.get(key)
        if not value or not as_abs(Path(value)).exists():
            return False
    return True


def endpoint_identity(row: dict[str, str]) -> str:
    labels = {row.get("subject_label", "").strip().lower(), row.get("object_label", "").strip().lower()}
    if labels & GENERIC_LABELS:
        return "uncertain"
    if not row.get("subject_id") or not row.get("object_id"):
        return "pair_invalid"
    return "both_valid"


def map_visible_geometry(row: dict[str, str]) -> tuple[str, str, str]:
    family = row.get("predicate_family", "")
    predicate = row.get("predicate_label", "")
    subject = row.get("subject_label", "")
    obj = row.get("object_label", "")
    if family == "relative_vertical":
        geometry, _mesh_geometry, usefulness, uncertainty = visible_fill.vertical_answer(predicate, subject, obj)
    elif family == "support_contact":
        geometry, _mesh_geometry, usefulness, uncertainty = visible_fill.support_answer(predicate, subject, obj)
    else:
        geometry, usefulness, uncertainty = "uncertain", "uncertain", "ambiguous_relation"

    if usefulness == "ontology_mismatch":
        usefulness_v3 = "ontology_mismatch"
    elif usefulness == "trivial_dense_or_room_structure":
        usefulness_v3 = "trivial_dense_or_room_structure"
    elif usefulness == "informative":
        usefulness_v3 = "informative"
    else:
        usefulness_v3 = "uncertain"

    if geometry == "uncertain":
        geometry_v3 = "ambiguous"
    elif geometry in {"supports_predicate", "contradicts_predicate"}:
        geometry_v3 = geometry
    else:
        geometry_v3 = "ambiguous"
    return geometry_v3, usefulness_v3, uncertainty


def reliability_from_axes(
    endpoint: str,
    evaluability: str,
    geometry: str,
    usefulness: str,
    uncertainty_hint: str,
) -> tuple[str, str, str]:
    if endpoint != "both_valid":
        return "uncertain", "identity_or_segmentation_issue", "other"
    if evaluability == "not_evaluable":
        return "uncertain", "insufficient_evidence", "missing_or_partial_packet"
    if geometry == "not_evaluable":
        return "uncertain", "insufficient_evidence", "missing_or_partial_packet"
    if geometry == "ambiguous":
        reason = "ambiguous_predicate" if uncertainty_hint == "ambiguous_relation" else "ambiguous_geometry"
        return "uncertain", "insufficient_evidence", reason
    if geometry == "contradicts_predicate":
        return "unreliable_geometry", "geometry_contradiction", "none"
    if usefulness == "trivial_dense_or_room_structure":
        return "unreliable_trivial", "trivial_dense_relation", "none"
    if usefulness == "ontology_mismatch":
        return "unreliable_ontology", "ontology_or_predicate_granularity_mismatch", "none"
    if geometry == "supports_predicate" and usefulness == "informative":
        return "reliable", "physical_relation_supported_and_informative", "none"
    return "uncertain", "insufficient_evidence", "other"


def fill_row(row: dict[str, str]) -> dict[str, Any]:
    filled: dict[str, Any] = dict(row)
    paths_ready = packet_paths_exist(row)
    endpoint = endpoint_identity(row)
    geometry, usefulness, uncertainty_hint = map_visible_geometry(row)

    if not paths_ready:
        evaluability = "not_evaluable"
        geometry = "not_evaluable"
        usefulness = "uncertain"
    elif endpoint != "both_valid":
        evaluability = "partially_evaluable"
    else:
        evaluability = "evaluable"

    reliability, primary_reason, uncertainty_reason = reliability_from_axes(
        endpoint=endpoint,
        evaluability=evaluability,
        geometry=geometry,
        usefulness=usefulness,
        uncertainty_hint=uncertainty_hint,
    )

    filled.update(
        {
            "reviewer_id": REVIEWER_ID,
            "review_round": REVIEW_ROUND,
            "endpoint_identity_v3": endpoint,
            "pair_evaluability_v3": evaluability,
            "geometry_support_v3": geometry,
            "relation_usefulness_v3": usefulness,
            "relation_reliability_v3": reliability,
            "primary_reason_v3": primary_reason,
            "uncertainty_reason_v3": uncertainty_reason,
            "label_notes_v3": (
                "codex proxy v3 fill; visible identity and packet-availability heuristic only; "
                "not an independent visual human audit"
            ),
        }
    )
    return filled


def validate_rows(rows: list[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = {key: set(value) for key, value in schema.get("allowed_values", {}).items()}
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id")
        for field in COMPLETION_FIELDS:
            value = row.get(field)
            if value is None or value == "":
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "error_type": "missing_completion_field",
                    }
                )
            elif field in allowed and value not in allowed[field]:
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "value": value,
                        "error_type": "invalid_completion_value",
                    }
                )
        for packet_field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = row.get(packet_field, "")
            if not value or not as_abs(Path(value)).exists():
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": packet_field,
                        "value": value,
                        "error_type": "packet_path_missing",
                    }
                )
    return errors


def label_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v3_proxy_label_v1",
        "blind_review_id": row["blind_review_id"],
        "review_scope": row["review_scope"],
        "scan_id": row["scan_id"],
        "scene_context_id": row["scene_context_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "evidence_packet_status": row["evidence_packet_status"],
        "v3_review_fields": {
            "reviewer_id": row["reviewer_id"],
            "review_round": row["review_round"],
            "endpoint_identity_v3": row["endpoint_identity_v3"],
            "pair_evaluability_v3": row["pair_evaluability_v3"],
            "geometry_support_v3": row["geometry_support_v3"],
            "relation_usefulness_v3": row["relation_usefulness_v3"],
            "relation_reliability_v3": row["relation_reliability_v3"],
            "primary_reason_v3": row["primary_reason_v3"],
            "uncertainty_reason_v3": row["uncertainty_reason_v3"],
            "label_notes_v3": row["label_notes_v3"],
        },
        "provenance": {
            "filled_by": "codex_proxy",
            "user_requested_proxy_fill": True,
            "actual_user_reviewer": False,
            "paper_evidence_allowed": False,
            "used_hidden_manifest_for_label_decision": False,
            "used_sampling_category_for_label_decision": False,
            "used_expected_role_for_label_decision": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "used_geometry_status": False,
            "used_label_match_status": False,
            "used_numeric_witness_values": False,
            "validation_usage": False,
            "test_usage": False,
            "multi_view_as_model_input": False,
        },
    }


def post_label_bucket_diagnostics(
    filled_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manifest_by_id = {row["blind_review_id"]: row for row in manifest_rows}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in filled_rows:
        manifest = manifest_by_id.get(row["blind_review_id"], {})
        category = manifest.get("sampling_category_hidden", "missing_manifest")
        grouped[category].append(row)

    diagnostics: list[dict[str, Any]] = []
    for category, rows in sorted(grouped.items()):
        reliability = Counter(row["relation_reliability_v3"] for row in rows)
        geometry = Counter(row["geometry_support_v3"] for row in rows)
        usefulness = Counter(row["relation_usefulness_v3"] for row in rows)
        primary = Counter(row["primary_reason_v3"] for row in rows)
        diagnostics.append(
            {
                "sampling_category_hidden_post_label_only": category,
                "rows": len(rows),
                "reliable": reliability.get("reliable", 0),
                "unreliable_geometry": reliability.get("unreliable_geometry", 0),
                "unreliable_trivial": reliability.get("unreliable_trivial", 0),
                "unreliable_ontology": reliability.get("unreliable_ontology", 0),
                "uncertain": reliability.get("uncertain", 0),
                "geometry_counts": dict(sorted(geometry.items())),
                "usefulness_counts": dict(sorted(usefulness.items())),
                "primary_reason_counts": dict(sorted(primary.items())),
            }
        )
    return diagnostics


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    reliability = counts["relation_reliability_v3"]
    geometry = counts["geometry_support_v3"]
    usefulness = counts["relation_usefulness_v3"]
    lines = [
        "# H002 Reliability Target V3 Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage fill.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Filled by Codex proxy at user request; this is not independent human annotation.",
        "- Label decisions use labeler-visible identity fields and packet path availability.",
        "- Hidden sampling category, expected role, source score/rank, `p_geom_valid`, geometry status, label-match status, and numeric witness values are not used for label decisions.",
        "- Hidden manifest is joined only after label fill for diagnostic bucket counts.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {counts['rows']} |",
        f"| reliable | {reliability.get('reliable', 0)} |",
        f"| unreliable_geometry | {reliability.get('unreliable_geometry', 0)} |",
        f"| unreliable_trivial | {reliability.get('unreliable_trivial', 0)} |",
        f"| unreliable_ontology | {reliability.get('unreliable_ontology', 0)} |",
        f"| uncertain | {reliability.get('uncertain', 0)} |",
        f"| validation errors | {counts['validation_errors']} |",
        "",
        "## Geometry Support",
        "",
        "| Geometry support | Count |",
        "| --- | ---: |",
    ]
    for key, value in geometry.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Relation Usefulness", "", "| Usefulness | Count |", "| --- | ---: |"])
    for key, value in usefulness.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Interpretation",
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
    input_sheet = as_abs(args.input_sheet)
    schema_path = as_abs(args.schema)
    manifest_path = as_abs(args.manifest)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    fieldnames, rows = read_tsv(input_sheet)
    schema = read_json(schema_path)
    manifest_rows = read_jsonl(manifest_path)
    filled_rows = [fill_row(row) for row in rows]
    errors = validate_rows(filled_rows, schema)
    label_rows = [label_record(row) for row in filled_rows]
    bucket_diagnostics = post_label_bucket_diagnostics(filled_rows, manifest_rows)

    reliability_counts = Counter(row["relation_reliability_v3"] for row in filled_rows)
    geometry_counts = Counter(row["geometry_support_v3"] for row in filled_rows)
    usefulness_counts = Counter(row["relation_usefulness_v3"] for row in filled_rows)
    family_counts = Counter(row["predicate_family"] for row in filled_rows)
    endpoint_counts = Counter(row["endpoint_identity_v3"] for row in filled_rows)
    evaluability_counts = Counter(row["pair_evaluability_v3"] for row in filled_rows)
    primary_counts = Counter(row["primary_reason_v3"] for row in filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "completed_sheet": output_dir / "completed_v3_positive_anchor_label_sheet_codex_proxy_user_requested.tsv",
        "v3_proxy_labels": output_dir / "v3_proxy_labels.jsonl",
        "bucket_diagnostics_post_label_only": output_dir / "bucket_diagnostics_post_label_only.csv",
        "bucket_diagnostics_post_label_only_json": output_dir / "bucket_diagnostics_post_label_only.json",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
    }

    status = "h002_reliability_target_v3_label_filled_codex_proxy_user_requested"
    if errors:
        status = "h002_reliability_target_v3_label_fill_errors"

    summary = {
        "schema_version": "h002_reliability_target_v3_label_fill_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": (
            "Filled v3 label fields as a user-requested Codex proxy. This increases "
            "hypothesis-stage supervision coverage, but it is not independent human "
            "annotation and must be ingested/audited before any posterior smoke."
        ),
        "input_paths": {
            "v3_positive_anchor_label_sheet": rel_path(input_sheet),
            "v3_label_schema": rel_path(schema_path),
            "post_label_manifest": rel_path(manifest_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "filled_by": "codex_proxy",
            "user_requested_proxy_fill": True,
            "actual_user_reviewer": False,
            "paper_evidence_allowed": False,
            "used_hidden_manifest_for_label_decision": False,
            "used_sampling_category_for_label_decision": False,
            "used_expected_role_for_label_decision": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "used_geometry_status": False,
            "used_label_match_status": False,
            "used_numeric_witness_values": False,
            "post_label_hidden_manifest_diagnostic_join": True,
            "multi_view_as_model_input": False,
            "posterior_smoke_allowed": False,
        },
        "counts": {
            "rows": len(filled_rows),
            "validation_errors": len(errors),
            "by_family": dict(sorted(family_counts.items())),
            "endpoint_identity_v3": dict(sorted(endpoint_counts.items())),
            "pair_evaluability_v3": dict(sorted(evaluability_counts.items())),
            "geometry_support_v3": dict(sorted(geometry_counts.items())),
            "relation_usefulness_v3": dict(sorted(usefulness_counts.items())),
            "relation_reliability_v3": dict(sorted(reliability_counts.items())),
            "primary_reason_v3": dict(sorted(primary_counts.items())),
        },
        "bucket_diagnostics_post_label_only": bucket_diagnostics,
        "next_todo": "reliability_target_v3_label_ingestion",
    }

    write_tsv(output_paths["completed_sheet"], filled_rows, fieldnames)
    write_jsonl(output_paths["v3_proxy_labels"], label_rows)
    write_jsonl(output_paths["fill_validation_errors"], errors)
    write_csv(output_paths["bucket_diagnostics_post_label_only"], bucket_diagnostics)
    write_json(output_paths["bucket_diagnostics_post_label_only_json"], {"buckets": bucket_diagnostics})
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    reliability = counts["relation_reliability_v3"]
    print(
        f"status={summary['status']} rows={counts['rows']} "
        f"reliable={reliability.get('reliable', 0)} "
        f"unreliable_geometry={reliability.get('unreliable_geometry', 0)} "
        f"unreliable_trivial={reliability.get('unreliable_trivial', 0)} "
        f"unreliable_ontology={reliability.get('unreliable_ontology', 0)} "
        f"uncertain={reliability.get('uncertain', 0)} "
        f"errors={counts['validation_errors']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
