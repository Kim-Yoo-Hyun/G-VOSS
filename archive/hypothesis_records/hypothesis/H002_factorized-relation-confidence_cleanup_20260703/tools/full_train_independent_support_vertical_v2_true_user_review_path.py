#!/usr/bin/env python3
"""Create the true user/external review path after proxy target audit failure."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PROTOCOL_DIR = RGA_ROOT / "independent_support_vertical_v2_external_review_protocol"
DEFAULT_AUDIT_DIR = RGA_ROOT / "independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_true_user_review_path"

DEFAULT_EXTERNAL_SHEET = DEFAULT_PROTOCOL_DIR / "external_evidence_review_sheet.tsv"
DEFAULT_EXTERNAL_SCHEMA = DEFAULT_PROTOCOL_DIR / "external_review_schema.json"
DEFAULT_EXTERNAL_MANIFEST = DEFAULT_PROTOCOL_DIR / "external_manifest_post_label_only.jsonl"
DEFAULT_AUDIT_SUMMARY = DEFAULT_AUDIT_DIR / "summary.json"
DEFAULT_DIAGNOSTIC_SLICE = DEFAULT_AUDIT_DIR / "target_slices/relation_reliability_external_target/rank_band_balanced_external.jsonl"

COMPLETION_FIELDS = [
    "external_reviewer_id",
    "external_review_round",
    "endpoint_identity_external",
    "visual_pair_evaluability_external",
    "mesh_pair_evaluability_external",
    "visual_geometry_answer_external",
    "mesh_geometry_answer_external",
    "relation_informativeness_external",
    "final_relation_reliability_external",
    "uncertainty_reason_external",
    "external_label_notes",
]

FORBIDDEN_HEADER_SUBSTRINGS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "target_y",
    "label_use",
    "relation_validity_label",
    "posterior",
    "v2",
    "witness",
    "positive_cues",
    "negative_cues",
    "proxy",
    "human",
    "codex",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-sheet", type=Path, default=DEFAULT_EXTERNAL_SHEET)
    parser.add_argument("--external-schema", type=Path, default=DEFAULT_EXTERNAL_SCHEMA)
    parser.add_argument("--external-manifest", type=Path, default=DEFAULT_EXTERNAL_MANIFEST)
    parser.add_argument("--audit-summary", type=Path, default=DEFAULT_AUDIT_SUMMARY)
    parser.add_argument("--diagnostic-slice", type=Path, default=DEFAULT_DIAGNOSTIC_SLICE)
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


def blank_completion(row: dict[str, str], scope: str) -> dict[str, Any]:
    output = dict(row)
    output["review_scope"] = scope
    for field in COMPLETION_FIELDS:
        output[field] = ""
    return output


def leakage_hits(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in fieldnames:
        lowered = field.lower()
        for token in FORBIDDEN_HEADER_SUBSTRINGS:
            if token in lowered:
                hits.append({"field": field, "forbidden_substring": token})
    return hits


def packet_path_errors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row in rows:
        for key in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(key) or "")
            if not value:
                errors.append({"blind_review_id": row.get("blind_review_id"), "field": key, "error_type": "missing_path", "path": ""})
                continue
            if not as_abs(Path(value)).exists():
                errors.append({"blind_review_id": row.get("blind_review_id"), "field": key, "error_type": "path_not_found", "path": value})
    return errors


def manifest_for_ids(manifest_rows: list[dict[str, Any]], ids: set[str], batch_name: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in manifest_rows:
        blind_id = str(row["blind_review_id"])
        if blind_id not in ids:
            continue
        output.append(
            {
                "schema_version": "h002_support_vertical_v2_true_user_review_manifest_v1",
                "blind_review_id": blind_id,
                "batch_name": batch_name,
                "scan_id": row.get("scan_id"),
                "subgraph_id": row.get("subgraph_id"),
                "subject_id": row.get("subject_id"),
                "subject_label": row.get("subject_label"),
                "predicate_label": row.get("predicate_label"),
                "predicate_family": row.get("predicate_family"),
                "object_id": row.get("object_id"),
                "object_label": row.get("object_label"),
                "packet_paths": row.get("packet_paths", {}),
                "post_label_only_hidden_audit_metadata": row.get("hidden_audit_metadata_post_label_only", {}),
                "post_label_only_previous_proxy_human_fields": row.get("previous_codex_proxy_human_fields_post_label_only", {}),
                "forbidden_as_labeler_visible": row.get("forbidden_as_labeler_visible", []),
            }
        )
    return output


def batch_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "by_family": dict(sorted(Counter(row["predicate_family"] for row in rows).items())),
        "by_predicate": dict(sorted(Counter(row["predicate_label"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["evidence_packet_status"] for row in rows).items())),
    }


def proxy_target_counts(slice_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(int(row["target_y"]) for row in slice_rows)
    return {"proxy_positive": counts[1], "proxy_negative": counts[0], "proxy_binary_rows": counts[1] + counts[0]}


def write_instructions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# H002 True User Review Instructions",
                "",
                "## Goal",
                "",
                "Fill the sheet by inspecting only the packet evidence. Do not use previous Codex/proxy labels, numeric witness values, hidden target metadata, source rank, source score, `p_geom_valid`, or deterministic geometry status.",
                "",
                "## Recommended First Pass",
                "",
                "Start with `true_user_review_sheet_rank_band70.tsv`. It is the controlled 70-row diagnostic batch where proxy-based visible/construction shortcuts were reduced, but harmful prior carryover still needs true user review.",
                "",
                "## Optional Full Pass",
                "",
                "Use `true_user_review_sheet_full127.tsv` after the first pass if the 70-row target becomes too uncertain or class-imbalanced.",
                "",
                "## Labeling Rule",
                "",
                "1. Confirm subject/object identity from packet evidence.",
                "2. Judge visual evidence and mesh evidence separately.",
                "3. Mark geometry support/contradiction/uncertainty without numeric residuals.",
                "4. Mark whether the relation is informative, trivial dense/room-structure, or ontology mismatch.",
                "5. Set final reliability to `reliable`, `unreliable`, or `uncertain`.",
                "",
                "## Hard Boundary",
                "",
                "A completed true-user sheet becomes evidence only after the user has actually reviewed the packet evidence. Codex proxy fills are diagnostic only.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 True User Review Path",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Why Proxy Stops Here",
        "",
        "- The revised external surface removed visible and construction shortcuts from the diagnostic slice.",
        "- The target still carries harmful prior-label correlation.",
        "- Continuing proxy fills would be diagnostic only and cannot validate a posterior method.",
        "",
        "## Recommended Batch",
        "",
        "| Batch | Rows | Role | Proxy Planning Balance |",
        "| --- | ---: | --- | --- |",
        f"| `rank_band70` | {summary['counts']['rank_band70']['rows']} | recommended first pass | {summary['planning_estimates']['rank_band70_proxy_balance']} |",
        f"| `full127` | {summary['counts']['full127']['rows']} | optional expansion | {summary['planning_estimates']['full127_proxy_balance']} |",
        "",
        "## Leakage Checks",
        "",
        "| Check | Count |",
        "| --- | ---: |",
        f"| rank-band header leakage | {summary['counts']['rank_band70_header_leakage_hits']} |",
        f"| full header leakage | {summary['counts']['full127_header_leakage_hits']} |",
        f"| rank-band packet path errors | {summary['counts']['rank_band70_packet_path_errors']} |",
        f"| full packet path errors | {summary['counts']['full127_packet_path_errors']} |",
        "",
        "## Next TODO",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    external_sheet_path = as_abs(args.external_sheet)
    external_schema_path = as_abs(args.external_schema)
    external_manifest_path = as_abs(args.external_manifest)
    audit_summary_path = as_abs(args.audit_summary)
    diagnostic_slice_path = as_abs(args.diagnostic_slice)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    fieldnames, sheet_rows = read_tsv(external_sheet_path)
    schema = read_json(external_schema_path)
    manifest_rows = read_jsonl(external_manifest_path)
    audit_summary = read_json(audit_summary_path)
    slice_rows = read_jsonl(diagnostic_slice_path)

    row_by_id = {str(row["blind_review_id"]): row for row in sheet_rows}
    manifest_ids = {str(row["blind_review_id"]) for row in manifest_rows}
    rank_band_ids = [str(row["blind_review_id"]) for row in slice_rows]
    missing_rank_ids = [blind_id for blind_id in rank_band_ids if blind_id not in row_by_id or blind_id not in manifest_ids]

    full_rows = [blank_completion(row, "selected_support_vertical_true_user_full_review_v1") for row in sheet_rows]
    rank_rows = [blank_completion(row_by_id[blind_id], "selected_support_vertical_true_user_rank_band70_review_v1") for blind_id in rank_band_ids if blind_id in row_by_id]
    full_ids = {str(row["blind_review_id"]) for row in full_rows}
    rank_ids = {str(row["blind_review_id"]) for row in rank_rows}

    rank_manifest = manifest_for_ids(manifest_rows, rank_ids, "rank_band70_true_user_first_pass")
    full_manifest = manifest_for_ids(manifest_rows, full_ids, "full127_true_user_optional_expansion")

    rank_leakage = leakage_hits(fieldnames)
    full_leakage = leakage_hits(fieldnames)
    rank_packet_errors = packet_path_errors(rank_rows)
    full_packet_errors = packet_path_errors(full_rows)

    relation_decision = audit_summary["target_decisions"]["relation_reliability_external_target"]
    construction = relation_decision.get("recommended_construction_slice")
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "true_user_review_sheet_rank_band70": output_dir / "true_user_review_sheet_rank_band70.tsv",
        "true_user_review_sheet_full127": output_dir / "true_user_review_sheet_full127.tsv",
        "true_user_manifest_rank_band70_post_label_only": output_dir / "true_user_manifest_rank_band70_post_label_only.jsonl",
        "true_user_manifest_full127_post_label_only": output_dir / "true_user_manifest_full127_post_label_only.jsonl",
        "true_user_review_schema": output_dir / "true_user_review_schema.json",
        "reviewer_instructions": output_dir / "reviewer_instructions.md",
        "rank_band70_header_leakage_hits": output_dir / "rank_band70_header_leakage_hits.jsonl",
        "full127_header_leakage_hits": output_dir / "full127_header_leakage_hits.jsonl",
        "rank_band70_packet_path_errors": output_dir / "rank_band70_packet_path_errors.jsonl",
        "full127_packet_path_errors": output_dir / "full127_packet_path_errors.jsonl",
        "missing_rank_band_ids": output_dir / "missing_rank_band_ids.jsonl",
    }

    status = "full_train_independent_support_vertical_v2_true_user_review_path_ready"
    if missing_rank_ids or rank_leakage or full_leakage or rank_packet_errors or full_packet_errors:
        status = "full_train_independent_support_vertical_v2_true_user_review_path_ready_with_warnings"

    rank_proxy = proxy_target_counts(slice_rows)
    full_relation = audit_summary["input_counts"]["relation_reliability_external_target"]
    summary = {
        "schema_version": "h002_support_vertical_v2_true_user_review_path_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": "Stop proxy labels as method-validation evidence and collect true user/external labels on the controlled rank-band batch first.",
        "input_paths": {
            "external_evidence_review_sheet": rel_path(external_sheet_path),
            "external_review_schema": rel_path(external_schema_path),
            "external_manifest_post_label_only": rel_path(external_manifest_path),
            "external_target_independence_audit_summary": rel_path(audit_summary_path),
            "rank_band_balanced_external_slice": rel_path(diagnostic_slice_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "fills_labels": False,
            "uses_proxy_labels_as_method_evidence": False,
            "posterior_smoke_allowed": False,
            "true_user_review_required": True,
            "multi_view_as_model_input": False,
            "source_score_feature_join_pending": True,
        },
        "previous_audit": {
            "status": audit_summary["status"],
            "relation_target_status": relation_decision["status"],
            "recommended_strict_slice": relation_decision.get("recommended_strict_slice"),
            "recommended_construction_slice": construction,
            "reason_proxy_insufficient": "visible/construction risks were reduced, but harmful prior carryover remains.",
        },
        "counts": {
            "rank_band70": batch_counts(rank_rows),
            "full127": batch_counts(full_rows),
            "rank_band70_manifest_rows": len(rank_manifest),
            "full127_manifest_rows": len(full_manifest),
            "missing_rank_band_ids": len(missing_rank_ids),
            "rank_band70_header_leakage_hits": len(rank_leakage),
            "full127_header_leakage_hits": len(full_leakage),
            "rank_band70_packet_path_errors": len(rank_packet_errors),
            "full127_packet_path_errors": len(full_packet_errors),
        },
        "planning_estimates": {
            "rank_band70_proxy_balance": f"{rank_proxy['proxy_positive']} positive / {rank_proxy['proxy_negative']} negative by proxy target; planning only",
            "full127_proxy_balance": f"{full_relation['positive']} positive / {full_relation['negative']} negative among {full_relation['rows']} binary rows by proxy target; planning only",
            "proxy_estimates_are_labeler_visible": False,
        },
        "schema_completion_fields": schema.get("completion_fields", COMPLETION_FIELDS),
        "allowed_review_values": schema.get("allowed_review_values", {}),
        "next_todo": "fill_true_user_review_sheet_rank_band70_or_user_confirmed_labels",
    }

    write_tsv(output_paths["true_user_review_sheet_rank_band70"], rank_rows, fieldnames)
    write_tsv(output_paths["true_user_review_sheet_full127"], full_rows, fieldnames)
    write_jsonl(output_paths["true_user_manifest_rank_band70_post_label_only"], rank_manifest)
    write_jsonl(output_paths["true_user_manifest_full127_post_label_only"], full_manifest)
    write_json(
        output_paths["true_user_review_schema"],
        {
            "schema_version": "h002_support_vertical_v2_true_user_review_schema_v1",
            "visible_fields": fieldnames,
            "completion_fields": schema.get("completion_fields", COMPLETION_FIELDS),
            "allowed_review_values": schema.get("allowed_review_values", {}),
            "target_derivation_contract": schema.get("target_derivation_contract", {}),
            "recommended_first_pass": "true_user_review_sheet_rank_band70.tsv",
            "optional_expansion": "true_user_review_sheet_full127.tsv",
            "proxy_labels_allowed_for_method_validation": False,
        },
    )
    write_instructions(output_paths["reviewer_instructions"])
    write_jsonl(output_paths["rank_band70_header_leakage_hits"], rank_leakage)
    write_jsonl(output_paths["full127_header_leakage_hits"], full_leakage)
    write_jsonl(output_paths["rank_band70_packet_path_errors"], rank_packet_errors)
    write_jsonl(output_paths["full127_packet_path_errors"], full_packet_errors)
    write_jsonl(output_paths["missing_rank_band_ids"], [{"blind_review_id": blind_id} for blind_id in missing_rank_ids])
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(
        f"status={summary['status']} rank_rows={counts['rank_band70']['rows']} "
        f"full_rows={counts['full127']['rows']} missing_rank_ids={counts['missing_rank_band_ids']} "
        f"rank_header_leaks={counts['rank_band70_header_leakage_hits']} "
        f"rank_packet_errors={counts['rank_band70_packet_path_errors']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
