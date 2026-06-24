#!/usr/bin/env python3
"""Materialize the H002 v20 endpoint-balanced attachment candidate set."""

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

DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining"

EXPECTED_CAPACITY_STATUS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_capacity_scan_passed_ready_for_candidate_mining"
)
EXPECTED_CAPACITY_NEXT = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining"
EXPECTED_SELECTED_ROUTE = "exact_endpoint_pair_mixed_contrast_primary"

STATUS_READY = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_candidate_mining_ready_for_source_inventory"
)
STATUS_ERRORS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_candidate_mining_errors"
)
NEXT_TODO = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory"

TARGET_ROWS = 320
VISIBLE_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "endpoint_pair_visible",
    "geometry_layout_summary_v20",
    "attachment_relation_prompt_v20",
    "coverage_summary_v20",
    "ambiguity_summary_v20",
    "review_question_v20",
    "relation_reliability_state_v20",
    "geometry_support_state_v20",
    "relation_usefulness_state_v20",
    "endpoint_identity_state_v20",
    "coverage_state_v20",
    "primary_reason_v20",
    "uncertainty_reason_v20",
    "review_notes_v20",
]
FORBIDDEN_VISIBLE_PATTERNS = [
    "scan_id",
    "subgraph_id",
    "instance id",
    "object_id",
    "subject_id",
    "rank_band",
    "rank band",
    "source score",
    "semantic score",
    "p_geom",
    "geometry status",
    "machine hint",
    "cell_id",
    "cell id",
    "typed witness",
    "sampling role",
    "selection route",
    "proxy_role",
    "primary_positive_anchor_proxy",
    "primary_hard_negative_proxy",
    "capacity_evidence_tier",
    "quota",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
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


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def validate_capacity(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "expected": EXPECTED_CAPACITY_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_CAPACITY_NEXT:
        errors.append({"error_type": "unexpected_capacity_next", "expected": EXPECTED_CAPACITY_NEXT, "actual": summary.get("next_todo")})
    decision = summary.get("capacity_decision", {})
    if decision.get("capacity_pass") is not True:
        errors.append({"error_type": "capacity_not_passed", "actual": decision.get("capacity_pass")})
    if decision.get("selected_capacity_route") != EXPECTED_SELECTED_ROUTE:
        errors.append({"error_type": "unexpected_capacity_route", "expected": EXPECTED_SELECTED_ROUTE, "actual": decision.get("selected_capacity_route")})
    sample = summary.get("sample_size_feasibility", {}).get("320", {})
    if sample.get("feasible") is not True:
        errors.append({"error_type": "preview_320_not_feasible", "actual": sample.get("feasible")})
    if sample.get("selected_rows") != TARGET_ROWS:
        errors.append({"error_type": "preview_320_row_count_mismatch", "expected": TARGET_ROWS, "actual": sample.get("selected_rows")})
    expected_quotas = {
        "attached to|primary_positive_anchor_proxy": 64,
        "attached to|primary_hard_negative_proxy": 64,
        "hanging on|primary_positive_anchor_proxy": 64,
        "hanging on|primary_hard_negative_proxy": 64,
        "connected to|connected_near_or_overlap_diagnostic": 32,
        "connected to|connected_far_or_functional_ambiguous_diagnostic": 32,
    }
    if sample.get("quota_counts") != expected_quotas:
        errors.append({"error_type": "preview_320_quota_mismatch", "expected": expected_quotas, "actual": sample.get("quota_counts")})
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "capacity_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def relation_family_visible(predicate: str) -> str:
    if predicate == "attached to":
        return "attachment-like relation"
    if predicate == "hanging on":
        return "hanging or mounted relation"
    if predicate == "connected to":
        return "connection-like diagnostic relation"
    return "attachment-family relation"


def geometry_layout_summary(row: dict[str, Any]) -> str:
    near = bool(row.get("near_contact"))
    loose = bool(row.get("loose_near_contact"))
    far = bool(row.get("far_separated"))
    overlap = bool(row.get("projected_overlap_support"))
    distance = "near object-pair layout" if near else "moderately near object-pair layout" if loose else "far-separated object-pair layout" if far else "mixed-distance object-pair layout"
    overlap_text = "projected footprints overlap or nearly overlap" if overlap else "projected footprints show little overlap"
    return f"{distance}; {overlap_text}; review whether this layout supports the directed relation"


def relation_prompt(row: dict[str, Any]) -> str:
    predicate = row["predicate_label"]
    if predicate == "attached to":
        return "Decide whether the visible object labels and layout support a physical attachment, not merely proximity or ordinary support."
    if predicate == "hanging on":
        return "Decide whether the visible object labels and layout support a hanging or mounted relation, not merely support or loose proximity."
    if predicate == "connected to":
        return "Diagnostic only: decide whether the relation appears potentially connected or remains ambiguous without functional evidence."
    return "Review the directed relation using only the visible evidence in this packet."


def ambiguity_summary(row: dict[str, Any]) -> str:
    flags = list(row.get("uncertainty_flags") or [])
    if not flags:
        return "no extra ambiguity flag from the internal geometry summary"
    mapping = {
        "floor_support_confound": "ordinary support may explain the layout",
        "functional_connection_ambiguous_without_visual_or_mesh": "functional connection may need visual or mesh confirmation",
        "hard_surface_pair": "broad structural surfaces may make the directed relation ambiguous",
        "large_obb_overlap_confound": "large boxes can overstate overlap",
        "thin_structure_or_boundary_missing": "thin contact regions may be missing from box-level geometry",
        "typed_witness_ambiguous": "3D cues are mixed or incomplete",
    }
    return "; ".join(mapping.get(flag, "unmapped ambiguity cue") for flag in flags)


def visible_row(row: dict[str, Any], review_card: str) -> dict[str, str]:
    relation = f"{row['subject_label']} {row['predicate_label']} {row['object_label']}"
    return {
        "blind_review_id": "attv20_" + stable_hash(str(row["prediction_id"]))[:12],
        "review_card": review_card,
        "candidate_relation": relation,
        "subject_label": str(row["subject_label"]),
        "predicate_label": str(row["predicate_label"]),
        "object_label": str(row["object_label"]),
        "relation_family_visible": relation_family_visible(str(row["predicate_label"])),
        "endpoint_pair_visible": f"{row['subject_label']} -> {row['object_label']}",
        "geometry_layout_summary_v20": geometry_layout_summary(row),
        "attachment_relation_prompt_v20": relation_prompt(row),
        "coverage_summary_v20": "selected train candidate with pair-level 3D evidence; image or mesh evidence will be checked in a later inventory gate",
        "ambiguity_summary_v20": ambiguity_summary(row),
        "review_question_v20": "Should this directed relation be treated as a reliable scene-graph edge after reviewing the visible evidence?",
        "relation_reliability_state_v20": "",
        "geometry_support_state_v20": "",
        "relation_usefulness_state_v20": "",
        "endpoint_identity_state_v20": "",
        "coverage_state_v20": "",
        "primary_reason_v20": "",
        "uncertainty_reason_v20": "",
        "review_notes_v20": "",
    }


def hidden_row(row: dict[str, Any], visible: dict[str, str]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v20_attachment_candidate_hidden_v1",
        "blind_review_id": visible["blind_review_id"],
        "prediction_id": row.get("prediction_id"),
        "split": "train",
        "source_id": "open3dsg_train_full",
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "directed_pair_id": row.get("directed_pair_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "subject_label": row.get("subject_label"),
        "predicate_family": "attachment_deferred",
        "predicate_label": row.get("predicate_label"),
        "object_label": row.get("object_label"),
        "candidate_role_hidden": "primary_binary_candidate" if row.get("predicate_label") in {"attached to", "hanging on"} else "connected_diagnostic_candidate",
        "proxy_role_hidden": row.get("proxy_role"),
        "capacity_evidence_tier_hidden": row.get("capacity_evidence_tier"),
        "selection_route_level_hidden": row.get("selection_route_level"),
        "cell_id_hidden": row.get("cell_id_hidden"),
        "provisional_status_hidden": row.get("provisional_status_hidden"),
        "anchor_bucket_hidden": row.get("anchor_bucket_hidden"),
        "rank_band_hidden": row.get("rank_band_hidden"),
        "subject_family_hidden": row.get("subject_family"),
        "object_family_hidden": row.get("object_family"),
        "object_family_pair_hidden": row.get("object_family_pair"),
        "visible_endpoint_pair_hidden": row.get("visible_endpoint_pair"),
        "near_contact_hidden": row.get("near_contact"),
        "loose_near_contact_hidden": row.get("loose_near_contact"),
        "far_separated_hidden": row.get("far_separated"),
        "projected_overlap_support_hidden": row.get("projected_overlap_support"),
        "uncertainty_flags_hidden": row.get("uncertainty_flags") or [],
        "reviewer_visible": False,
        "posterior_input_allowed": False,
        "model_input_allowed": False,
        "multi_view_or_mesh_required_before_label_fill": True,
    }


def write_review_card(path: Path, row: dict[str, str]) -> None:
    lines = [
        f"# {row['candidate_relation']}",
        "",
        "## Visible Evidence",
        "",
        f"- Relation family: {row['relation_family_visible']}",
        f"- Endpoint pair: {row['endpoint_pair_visible']}",
        f"- Layout: {row['geometry_layout_summary_v20']}",
        f"- Prompt: {row['attachment_relation_prompt_v20']}",
        f"- Coverage: {row['coverage_summary_v20']}",
        f"- Ambiguity: {row['ambiguity_summary_v20']}",
        "",
        "## Question",
        "",
        row["review_question_v20"],
        "",
        "## Fill Fields",
        "",
        "- relation_reliability_state_v20:",
        "- geometry_support_state_v20:",
        "- relation_usefulness_state_v20:",
        "- endpoint_identity_state_v20:",
        "- coverage_state_v20:",
        "- primary_reason_v20:",
        "- uncertainty_reason_v20:",
        "- review_notes_v20:",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def leakage_hits(visible_rows: list[dict[str, str]], review_card_dir: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in visible_rows:
        for field, value in row.items():
            lower = str(value).lower()
            for pattern in FORBIDDEN_VISIBLE_PATTERNS:
                if pattern in lower:
                    hits.append({"surface": "candidate_sheet", "blind_review_id": row["blind_review_id"], "field": field, "pattern": pattern})
        card_path = review_card_dir / f"{row['blind_review_id']}.md"
        text = card_path.read_text(encoding="utf-8").lower()
        for pattern in FORBIDDEN_VISIBLE_PATTERNS:
            if pattern in text:
                hits.append({"surface": "review_card", "blind_review_id": row["blind_review_id"], "field": str(card_path), "pattern": pattern})
    return hits


def candidate_summary_rows(hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in hidden_rows:
        key = f"{row['predicate_label']}|{row['proxy_role_hidden']}"
        groups.setdefault(key, []).append(row)
    rows = []
    for key, items in sorted(groups.items()):
        rows.append(
            {
                "predicate_proxy_role": key,
                "rows": len(items),
                "unique_scans": len({item["scan_id"] for item in items}),
                "unique_subgraphs": len({item["subgraph_id"] for item in items}),
                "unique_visible_endpoint_pairs": len({item["visible_endpoint_pair_hidden"] for item in items}),
                "top_subject_labels": json.dumps(Counter(item["subject_label"] for item in items).most_common(8), ensure_ascii=False),
                "top_object_labels": json.dumps(Counter(item["object_label"] for item in items).most_common(8), ensure_ascii=False),
                "selection_route_counts": json.dumps(dict(Counter(item["selection_route_level_hidden"] for item in items)), ensure_ascii=False, sort_keys=True),
            }
        )
    return rows


def validate_outputs(
    visible_rows: list[dict[str, str]],
    hidden_rows: list[dict[str, Any]],
    internal_rows: list[dict[str, Any]],
    leaks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(visible_rows) != TARGET_ROWS:
        errors.append({"error_type": "visible_row_count_mismatch", "expected": TARGET_ROWS, "actual": len(visible_rows)})
    if len(hidden_rows) != TARGET_ROWS:
        errors.append({"error_type": "hidden_row_count_mismatch", "expected": TARGET_ROWS, "actual": len(hidden_rows)})
    if len(internal_rows) != TARGET_ROWS:
        errors.append({"error_type": "internal_row_count_mismatch", "expected": TARGET_ROWS, "actual": len(internal_rows)})
    if leaks:
        errors.append({"error_type": "visible_leakage_hits_present", "count": len(leaks)})

    blind_ids = [row["blind_review_id"] for row in visible_rows]
    if len(set(blind_ids)) != len(blind_ids):
        errors.append({"error_type": "duplicate_blind_review_id"})
    prediction_ids = [str(row["prediction_id"]) for row in hidden_rows]
    if len(set(prediction_ids)) != len(prediction_ids):
        errors.append({"error_type": "duplicate_prediction_id"})

    predicate_counts = Counter(row["predicate_label"] for row in hidden_rows)
    expected_predicate_counts = {"attached to": 128, "hanging on": 128, "connected to": 64}
    if dict(predicate_counts) != expected_predicate_counts:
        errors.append({"error_type": "predicate_count_mismatch", "expected": expected_predicate_counts, "actual": dict(predicate_counts)})

    proxy_counts = Counter(f"{row['predicate_label']}|{row['proxy_role_hidden']}" for row in hidden_rows)
    expected_proxy_counts = {
        "attached to|primary_positive_anchor_proxy": 64,
        "attached to|primary_hard_negative_proxy": 64,
        "hanging on|primary_positive_anchor_proxy": 64,
        "hanging on|primary_hard_negative_proxy": 64,
        "connected to|connected_near_or_overlap_diagnostic": 32,
        "connected to|connected_far_or_functional_ambiguous_diagnostic": 32,
    }
    if dict(proxy_counts) != expected_proxy_counts:
        errors.append({"error_type": "proxy_count_mismatch", "expected": expected_proxy_counts, "actual": dict(proxy_counts)})

    connected_primary = sum(1 for row in hidden_rows if row["predicate_label"] == "connected to" and row["candidate_role_hidden"] == "primary_binary_candidate")
    if connected_primary:
        errors.append({"error_type": "connected_to_marked_primary", "actual": connected_primary})
    primary_rows = sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "primary_binary_candidate")
    if primary_rows != 256:
        errors.append({"error_type": "primary_candidate_count_mismatch", "expected": 256, "actual": primary_rows})
    diagnostic_rows = sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "connected_diagnostic_candidate")
    if diagnostic_rows != 64:
        errors.append({"error_type": "diagnostic_candidate_count_mismatch", "expected": 64, "actual": diagnostic_rows})

    for row in hidden_rows:
        if row.get("reviewer_visible") is not False:
            errors.append({"error_type": "hidden_row_marked_visible", "blind_review_id": row.get("blind_review_id")})
        if row.get("model_input_allowed") is not False:
            errors.append({"error_type": "hidden_row_model_input_allowed", "blind_review_id": row.get("blind_review_id")})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V20 Attachment Endpoint-Balanced Candidate Mining",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Result",
        "",
        "```text",
        f"selected_rows = {counts['selected_rows']}",
        f"primary_binary_candidate_rows = {counts['primary_binary_candidate_rows']}",
        f"connected_diagnostic_rows = {counts['connected_diagnostic_rows']}",
        f"attached_to_rows = {counts['attached_to_rows']}",
        f"hanging_on_rows = {counts['hanging_on_rows']}",
        f"connected_to_rows = {counts['connected_to_rows']}",
        f"unique_scans = {counts['unique_scans']}",
        f"unique_subgraphs = {counts['unique_subgraphs']}",
        f"unique_visible_endpoint_pairs = {counts['unique_visible_endpoint_pairs']}",
        f"visible_leakage_hits = {counts['visible_leakage_hits']}",
        "```",
        "",
        "## Boundary",
        "",
        "- Train-only candidate materialization.",
        "- No labels were filled.",
        "- No posterior was trained.",
        "- Hidden proxy roles and witness fields are audit-only and not model inputs.",
        "- Multi-view/mesh assets must be inventoried before label fill.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)
    review_card_dir = output_dir / "review_cards_v20"
    output_dir.mkdir(parents=True, exist_ok=True)

    capacity_summary = read_json(capacity_dir / "summary.json")
    validation_errors = validate_capacity(capacity_summary)
    internal_rows = read_jsonl(capacity_dir / "preview_internal_320.jsonl")

    visible_rows: list[dict[str, str]] = []
    hidden_rows: list[dict[str, Any]] = []
    selected_internal_rows: list[dict[str, Any]] = []
    for row in internal_rows:
        blind_id = "attv20_" + stable_hash(str(row["prediction_id"]))[:12]
        review_card = f"review_cards_v20/{blind_id}.md"
        visible = visible_row(row, review_card)
        hidden = hidden_row(row, visible)
        visible_rows.append(visible)
        hidden_rows.append(hidden)
        selected_internal_rows.append(row)
        write_review_card(review_card_dir / f"{blind_id}.md", visible)

    leaks = leakage_hits(visible_rows, review_card_dir)
    validation_errors.extend(validate_outputs(visible_rows, hidden_rows, selected_internal_rows, leaks))
    status = STATUS_READY if not validation_errors else STATUS_ERRORS

    counts = {
        "selected_rows": len(visible_rows),
        "primary_binary_candidate_rows": sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "primary_binary_candidate"),
        "connected_diagnostic_rows": sum(1 for row in hidden_rows if row["candidate_role_hidden"] == "connected_diagnostic_candidate"),
        "attached_to_rows": sum(1 for row in hidden_rows if row["predicate_label"] == "attached to"),
        "hanging_on_rows": sum(1 for row in hidden_rows if row["predicate_label"] == "hanging on"),
        "connected_to_rows": sum(1 for row in hidden_rows if row["predicate_label"] == "connected to"),
        "unique_scans": len({str(row["scan_id"]) for row in hidden_rows}),
        "unique_subgraphs": len({str(row["subgraph_id"]) for row in hidden_rows}),
        "unique_directed_pairs": len({str(row["directed_pair_id"]) for row in hidden_rows}),
        "unique_visible_endpoint_pairs": len({str(row["visible_endpoint_pair_hidden"]) for row in hidden_rows}),
        "visible_leakage_hits": len(leaks),
        "proxy_counts": dict(Counter(f"{row['predicate_label']}|{row['proxy_role_hidden']}" for row in hidden_rows)),
        "selection_route_counts": dict(Counter(str(row["selection_route_level_hidden"]) for row in hidden_rows)),
    }
    summary_rows = candidate_summary_rows(hidden_rows)
    boundary = {
        "split": "train_only",
        "validation_usage": False,
        "test_usage": False,
        "fills_new_labels": False,
        "ingests_existing_labels": False,
        "candidate_sheet_created": True,
        "source_inventory_required_next": True,
        "hidden_fields_as_model_input": False,
        "uses_source_score_or_rank": False,
        "uses_p_geom_valid": False,
        "uses_geometry_status_or_rank_hint": False,
        "trains_new_posterior": False,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "h001_artifacts_modified": False,
        "rga_redefined_as_lh_only": False,
        "multi_view_as_model_input": False,
        "mesh_as_model_input": False,
        "multi_view_or_mesh_as_audit_or_confirmation_evidence_only": True,
    }
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "candidate_sheet": output_dir / "candidate_sheet_v20.tsv",
        "hidden_audit_manifest": output_dir / "hidden_audit_manifest_v20.jsonl",
        "selected_candidates_internal": output_dir / "selected_candidates_internal_v20.jsonl",
        "candidate_summary": output_dir / "candidate_summary.csv",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "review_cards": review_card_dir,
    }
    summary = {
        "schema_version": "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "capacity_summary": rel_path(capacity_dir / "summary.json"),
            "preview_internal_320": rel_path(capacity_dir / "preview_internal_320.jsonl"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": counts,
        "candidate_summary": summary_rows,
        "boundary": boundary,
        "label_surface_policy": {
            "visible_sheet_hides_construction_fields": True,
            "primary_relation_scope": ["attached to", "hanging on"],
            "diagnostic_relation_scope": ["connected to"],
            "candidate_size": TARGET_ROWS,
            "selected_capacity_route": EXPECTED_SELECTED_ROUTE,
            "multi_view_or_mesh_required_before_label_fill": True,
            "posterior_smoke_allowed": False,
        },
    }

    write_tsv(output_paths["candidate_sheet"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["hidden_audit_manifest"], hidden_rows)
    write_jsonl(output_paths["selected_candidates_internal"], selected_internal_rows)
    write_csv(output_paths["candidate_summary"], summary_rows)
    write_jsonl(output_paths["visible_leakage_hits"], leaks)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(f"status={summary['status']}")
    print(f"selected_rows={counts['selected_rows']}")
    print(f"primary_binary_candidate_rows={counts['primary_binary_candidate_rows']}")
    print(f"connected_diagnostic_rows={counts['connected_diagnostic_rows']}")
    print(f"unique_scans={counts['unique_scans']}")
    print(f"unique_visible_endpoint_pairs={counts['unique_visible_endpoint_pairs']}")
    print(f"visible_leakage_hits={counts['visible_leakage_hits']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
