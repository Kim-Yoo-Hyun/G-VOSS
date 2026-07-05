#!/usr/bin/env python3
"""Create a hidden-field-safe candidate sheet for the H002 v22 hanging-on route."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PACKET_PLAN_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining"

EXPECTED_PLAN_STATUS = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan_ready_for_candidate_mining"
EXPECTED_PLAN_NEXT = "reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining"

STATUS_READY = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining_ready_for_source_inventory"
STATUS_ERRORS = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining_errors"
NEXT_TODO = "reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory"

TARGET_ROWS = 240
PREDICATE = "hanging on"
ROLE_ACCEPT = "accept_proxy_supported_candidate"
ROLE_REJECT = "reject_proxy_contradicted_candidate"

VISIBLE_FIELDS = [
    "blind_review_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "review_focus_v22",
    "scene_evidence_request_v22",
    "relation_question_v22",
    "relation_reliability_state_v22",
    "geometry_support_state_v22",
    "relation_usefulness_state_v22",
    "coverage_state_v22",
    "primary_reason_v22",
    "uncertainty_reason_v22",
    "review_notes_v22",
]

FORBIDDEN_VISIBLE_PATTERNS = [
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "prediction_id",
    "directed_pair_id",
    "rank_band",
    "rank band",
    "semantic_rank",
    "semantic score",
    "source score",
    "geometry_bucket",
    "geometry bucket",
    "object_family",
    "object family",
    "coverage_proxy",
    "uncertainty_bucket",
    "gt_label",
    "gt match",
    "planned_proxy",
    "proxy role",
    "strict_group",
    "strict group",
    "p_geom",
    "geometry_status",
    "geometry status",
    "accept_proxy",
    "reject_proxy",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-plan-dir", type=Path, default=DEFAULT_PACKET_PLAN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
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


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def blind_id(row: dict[str, Any]) -> str:
    return "v22hang_" + stable_hash(str(row["prediction_id"]))[:14]


def validate_packet_plan(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "expected": EXPECTED_PLAN_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "expected": EXPECTED_PLAN_NEXT, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": summary.get("validation_errors")})
    decision = summary.get("packet_plan_decision", {})
    if decision.get("packet_plan_pass") is not True:
        errors.append({"error_type": "packet_plan_not_passed", "actual": decision.get("packet_plan_pass")})
    selection = summary.get("selection_summary", {})
    if selection.get("selected_rows") != TARGET_ROWS:
        errors.append({"error_type": "unexpected_selected_rows", "expected": TARGET_ROWS, "actual": selection.get("selected_rows")})
    role_counts = selection.get("selected_role_counts", {})
    if role_counts.get(ROLE_ACCEPT) != TARGET_ROWS // 2 or role_counts.get(ROLE_REJECT) != TARGET_ROWS // 2:
        errors.append({"error_type": "unexpected_role_balance", "actual": role_counts})
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "creates_visible_label_sheet",
        "materializes_packet_assets",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def visible_row(row: dict[str, Any]) -> dict[str, str]:
    subject = str(row["subject_label"])
    predicate = str(row["predicate_label"])
    obj = str(row["object_label"])
    return {
        "blind_review_id": blind_id(row),
        "candidate_relation": f"{subject} {predicate} {obj}",
        "subject_label": subject,
        "predicate_label": predicate,
        "object_label": obj,
        "relation_family_visible": "hanging or mounted relation",
        "review_focus_v22": "Assess whether the directed relation describes a reliable hanging or mounted scene-graph edge.",
        "scene_evidence_request_v22": "Use only the neutral packet-local visual or mesh evidence after source inventory and packet materialization.",
        "relation_question_v22": "Should this directed relation be accepted as reliable, rejected as unreliable, or left uncertain?",
        "relation_reliability_state_v22": "",
        "geometry_support_state_v22": "",
        "relation_usefulness_state_v22": "",
        "coverage_state_v22": "",
        "primary_reason_v22": "",
        "uncertainty_reason_v22": "",
        "review_notes_v22": "",
    }


def hidden_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload["blind_review_id"] = blind_id(row)
    payload["candidate_relation"] = f"{row['subject_label']} {row['predicate_label']} {row['object_label']}"
    payload["source_stage"] = "v22_hanging_on_strict_conditional_contrast_packet_plan"
    return payload


def candidate_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": blind_id(row),
        "candidate_relation": f"{row['subject_label']} {row['predicate_label']} {row['object_label']}",
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "object_label": row["object_label"],
        "visible_endpoint_pair": row["visible_endpoint_pair"],
        "planned_proxy_role_hidden": row["planned_proxy_role"],
        "strict_group_value_hidden": row["strict_group_value"],
        "rank_band_hidden": row["rank_band"],
        "geometry_bucket_hidden": row["geometry_bucket"],
        "object_family_pair_hidden": row["object_family_pair"],
        "coverage_proxy_hidden": row["coverage_proxy"],
        "uncertainty_bucket_hidden": row["uncertainty_bucket"],
        "gt_label_match_status_hidden": row["gt_label_match_status"],
        "scan_id_hidden": row["scan_id"],
        "subgraph_id_hidden": row["subgraph_id"],
        "prediction_id_hidden": row["prediction_id"],
        "subject_id_hidden": row["subject_id"],
        "object_id_hidden": row["object_id"],
    }


def count_rows(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field)) for row in rows))


def visible_leakage_hits(visible_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for row in visible_rows:
        for field, value in row.items():
            text = str(value).lower()
            for pattern in FORBIDDEN_VISIBLE_PATTERNS:
                if pattern in text:
                    hits.append(
                        {
                            "blind_review_id": row["blind_review_id"],
                            "field": field,
                            "pattern": pattern,
                            "value": str(value),
                        }
                    )
    return hits


def validate_rows(preview_rows: list[dict[str, Any]], visible_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(preview_rows) != TARGET_ROWS:
        errors.append({"error_type": "preview_row_count_mismatch", "expected": TARGET_ROWS, "actual": len(preview_rows)})
    if len(visible_rows) != TARGET_ROWS:
        errors.append({"error_type": "visible_row_count_mismatch", "expected": TARGET_ROWS, "actual": len(visible_rows)})
    blind_ids = [row["blind_review_id"] for row in visible_rows]
    duplicate_blind_ids = [item for item, count in Counter(blind_ids).items() if count > 1]
    if duplicate_blind_ids:
        errors.append({"error_type": "duplicate_blind_review_ids", "actual": duplicate_blind_ids[:10]})
    predicates = Counter(str(row.get("predicate_label")) for row in preview_rows)
    if predicates != Counter({PREDICATE: TARGET_ROWS}):
        errors.append({"error_type": "unexpected_predicate_counts", "actual": dict(predicates)})
    roles = Counter(str(row.get("planned_proxy_role")) for row in preview_rows)
    expected_roles = Counter({ROLE_ACCEPT: TARGET_ROWS // 2, ROLE_REJECT: TARGET_ROWS // 2})
    if roles != expected_roles:
        errors.append({"error_type": "unexpected_proxy_role_counts", "expected": dict(expected_roles), "actual": dict(roles)})
    header_extra = [field for field in VISIBLE_FIELDS if field not in visible_rows[0]] if visible_rows else VISIBLE_FIELDS
    if header_extra:
        errors.append({"error_type": "visible_fields_missing", "actual": header_extra})
    leakage = visible_leakage_hits(visible_rows)
    for hit in leakage[:50]:
        errors.append({"error_type": "visible_leakage_hit", **hit})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V22 Hanging-On Strict Candidate Mining",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"candidate_rows = {summary['counts']['candidate_rows']}",
        f"visible_rows = {summary['counts']['visible_rows']}",
        f"hidden_rows = {summary['counts']['hidden_rows']}",
        f"visible_leakage_hits = {summary['counts']['visible_leakage_hits']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Scope",
        "",
        "```text",
        "primary_relation_scope = hanging on",
        "candidate_rows = 240",
        "proxy_role_balance_hidden = 120 / 120",
        "visible_candidate_sheet_created = true",
        "packet_assets_materialized = false",
        "label_fill_allowed = false",
        "```",
        "",
        "## Field Boundary",
        "",
        "Reviewer-visible rows expose only relation text and blank review fields. Source ids, rank bands, geometry buckets, object-family pairs, GT-match status, proxy roles, and strict-group ids are preserved only in the hidden manifest for post-label audit.",
        "",
        "## Boundary",
        "",
        "- Train-only rows only.",
        "- No validation/test rows used.",
        "- No labels filled or ingested.",
        "- No posterior trained or evaluated.",
        "- Multi-view and mesh remain audit/confirmation evidence only.",
        "- H001 and paper artifacts were not modified.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    plan_dir = as_abs(args.packet_plan_dir)
    output_dir = as_abs(args.output_dir)
    plan_summary = read_json(plan_dir / "summary.json")
    preview_rows = read_jsonl(plan_dir / "hidden_selection_preview.jsonl")
    validation_errors = validate_packet_plan(plan_summary)

    visible_rows = [visible_row(row) for row in preview_rows]
    hidden_rows = [hidden_row(row) for row in preview_rows]
    candidate_rows = [candidate_row(row) for row in preview_rows]
    validation_errors.extend(validate_rows(preview_rows, visible_rows))
    leakage_hits = visible_leakage_hits(visible_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "visible_candidate_sheet": output_dir / "visible_candidate_sheet.tsv",
        "hidden_candidate_manifest": output_dir / "hidden_candidate_manifest.jsonl",
        "candidate_rows": output_dir / "candidate_rows.jsonl",
        "visible_schema": output_dir / "visible_schema.json",
        "leakage_report": output_dir / "visible_leakage_report.json",
        "report": output_dir / "report.md",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    visible_schema = {
        "visible_fields": VISIBLE_FIELDS,
        "forbidden_visible_patterns": FORBIDDEN_VISIBLE_PATTERNS,
        "hidden_fields_preserved_in_manifest": [
            "scan_id",
            "subgraph_id",
            "prediction_id",
            "subject_id",
            "object_id",
            "rank_band",
            "geometry_bucket",
            "object_family_pair",
            "coverage_proxy",
            "uncertainty_bucket",
            "gt_label_match_status",
            "planned_proxy_role",
            "strict_group_value",
        ],
    }

    counts = {
        "candidate_rows": len(candidate_rows),
        "visible_rows": len(visible_rows),
        "hidden_rows": len(hidden_rows),
        "visible_leakage_hits": len(leakage_hits),
        "predicate_counts": count_rows(preview_rows, "predicate_label"),
        "planned_proxy_role_counts_hidden": count_rows(preview_rows, "planned_proxy_role"),
        "rank_band_counts_hidden": count_rows(preview_rows, "rank_band"),
        "geometry_bucket_counts_hidden": count_rows(preview_rows, "geometry_bucket"),
        "coverage_proxy_counts_hidden": count_rows(preview_rows, "coverage_proxy"),
        "uncertainty_bucket_counts_hidden": count_rows(preview_rows, "uncertainty_bucket"),
        "gt_label_match_status_counts_hidden": count_rows(preview_rows, "gt_label_match_status"),
        "strict_group_count_hidden": len(set(str(row.get("strict_group_value")) for row in preview_rows)),
        "scan_count_hidden": len(set(str(row.get("scan_id")) for row in preview_rows)),
        "visible_endpoint_pair_count_hidden": len(set(str(row.get("visible_endpoint_pair")) for row in preview_rows)),
    }

    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    summary = {
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "next_todo": NEXT_TODO if not validation_errors else EXPECTED_PLAN_NEXT,
        "input_artifacts": {
            "packet_plan_summary": rel_path(plan_dir / "summary.json"),
            "hidden_selection_preview": rel_path(plan_dir / "hidden_selection_preview.jsonl"),
        },
        "output_artifacts": {key: rel_path(path) for key, path in output_paths.items()},
        "counts": counts,
        "visible_schema": visible_schema,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "creates_visible_candidate_sheet": True,
            "materializes_packet_assets": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_tsv(output_paths["visible_candidate_sheet"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["hidden_candidate_manifest"], hidden_rows)
    write_jsonl(output_paths["candidate_rows"], candidate_rows)
    write_json(output_paths["visible_schema"], visible_schema)
    write_json(output_paths["leakage_report"], {"visible_leakage_hits": leakage_hits, "count": len(leakage_hits)})
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"candidate_rows={summary['counts']['candidate_rows']}")
    print(f"visible_rows={summary['counts']['visible_rows']}")
    print(f"hidden_rows={summary['counts']['hidden_rows']}")
    print(f"visible_leakage_hits={summary['counts']['visible_leakage_hits']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
