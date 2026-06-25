#!/usr/bin/env python3
"""Freeze the H002 v23 hanging-on positive-anchor repair plan."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_after_audit"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v23_hanging_on_positive_anchor_repair_plan"

EXPECTED_PATH_STATUS = (
    "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_"
    "path_decision_select_v23_positive_anchor_repair_plan"
)
EXPECTED_PATH_NEXT = "reliability_target_v23_hanging_on_positive_anchor_repair_plan"
EXPECTED_SELECTED_PATH = "freeze_v22_hanging_on_strict_diagnostic_select_v23_positive_anchor_repair_plan"
EXPECTED_INGESTION_STATUS = (
    "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_"
    "label_ingested_positive_sparse_with_probe_risk"
)

STATUS = "h002_reliability_target_v23_hanging_on_positive_anchor_repair_plan_ready_for_capacity_scan"
NEXT_TODO = "reliability_target_v23_hanging_on_positive_anchor_capacity_scan"


SOFT_HANGING_SUBJECT_LABELS = {
    "bag",
    "backpack",
    "blinds",
    "cloth",
    "clothes",
    "coat",
    "curtain",
    "jacket",
    "towel",
}
ANCHOR_LABELS = {
    "blinds",
    "cabinet",
    "door",
    "doorframe",
    "handle",
    "hook",
    "rack",
    "rail",
    "rod",
    "stand",
    "window",
}
SUPPORT_CONFOUND_ANCHORS = {
    "bed",
    "bench",
    "chair",
    "couch",
    "desk",
    "floor",
    "shelf",
    "sofa",
    "table",
}
GENERIC_LABELS = {"item", "object", "thing"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-dir", type=Path, default=DEFAULT_PATH_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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


def validate_inputs(path_summary: dict[str, Any], ingestion_summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_summary.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_status", "expected": EXPECTED_PATH_STATUS, "actual": path_summary.get("status")})
    if path_summary.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_next_todo", "expected": EXPECTED_PATH_NEXT, "actual": path_summary.get("next_todo")})
    if path_summary.get("selected_path") != EXPECTED_SELECTED_PATH:
        errors.append({"error_type": "unexpected_selected_path", "expected": EXPECTED_SELECTED_PATH, "actual": path_summary.get("selected_path")})
    if path_summary.get("validation_errors") != 0:
        errors.append({"error_type": "path_validation_errors_present", "actual": path_summary.get("validation_errors")})
    if ingestion_summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "expected": EXPECTED_INGESTION_STATUS, "actual": ingestion_summary.get("status")})
    if ingestion_summary.get("validation_errors") != 0:
        errors.append({"error_type": "ingestion_validation_errors_present", "actual": ingestion_summary.get("validation_errors")})
    if ingestion_summary.get("counts", {}).get("rows") != len(rows):
        errors.append({"error_type": "row_count_mismatch", "expected": ingestion_summary.get("counts", {}).get("rows"), "actual": len(rows)})

    counts = Counter(row.get("review_relation_reliability") for row in rows)
    expected_counts = Counter({"accept_reliable": 9, "reject_unreliable": 193, "abstain_uncertain": 38})
    if counts != expected_counts:
        errors.append({"error_type": "unexpected_reliability_counts", "expected": dict(expected_counts), "actual": dict(counts)})
    for source, boundary in [("path_decision", path_summary.get("boundary", {})), ("ingestion", ingestion_summary.get("boundary", {}))]:
        for key in [
            "validation_usage",
            "test_usage",
            "fills_new_labels",
            "trains_new_posterior",
            "posterior_smoke_allowed",
            "paper_evidence_allowed",
            "hidden_fields_as_model_input",
            "multi_view_as_model_input",
            "mesh_as_model_input",
            "h001_artifacts_modified",
        ]:
            if boundary.get(key) is not False:
                errors.append({"error_type": "boundary_violation", "source": source, "key": key, "actual": boundary.get(key)})
    return errors


def family_for_subject(label: str) -> str:
    label = (label or "").lower()
    if label in SOFT_HANGING_SUBJECT_LABELS:
        return "soft_hanging_subject"
    if label in GENERIC_LABELS:
        return "generic_subject"
    return "non_hanging_or_uncertain_subject"


def family_for_anchor(label: str) -> str:
    label = (label or "").lower()
    if label in ANCHOR_LABELS:
        return "hanging_anchor_candidate"
    if label in SUPPORT_CONFOUND_ANCHORS:
        return "support_or_furniture_confound_anchor"
    if label in GENERIC_LABELS:
        return "generic_anchor"
    return "uncertain_anchor"


def annotate_affordance(row: dict[str, Any]) -> dict[str, Any]:
    subject = str(row.get("subject_label", "")).lower()
    obj = str(row.get("object_label", "")).lower()
    subject_family = family_for_subject(subject)
    anchor_family = family_for_anchor(obj)
    if subject_family == "soft_hanging_subject" and anchor_family == "hanging_anchor_candidate":
        cell = "positive_anchor_candidate_cell"
    elif subject_family == "soft_hanging_subject":
        cell = "soft_subject_with_non_anchor_or_uncertain_object"
    elif anchor_family == "hanging_anchor_candidate":
        cell = "anchor_object_with_non_hanging_subject"
    else:
        cell = "non_anchor_generic_or_confound_cell"
    return {
        "subject_affordance_family": subject_family,
        "anchor_affordance_family": anchor_family,
        "positive_anchor_cell": cell,
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = []
    for row in rows:
        item = dict(row)
        item.update(annotate_affordance(row))
        enriched.append(item)

    accept_rows = [row for row in enriched if row.get("review_relation_reliability") == "accept_reliable"]
    reject_rows = [row for row in enriched if row.get("review_relation_reliability") == "reject_unreliable"]
    abstain_rows = [row for row in enriched if row.get("review_relation_reliability") == "abstain_uncertain"]

    def counts_for(field: str, selected: list[dict[str, Any]]) -> dict[str, int]:
        return dict(Counter(str(row.get(field, "missing")) for row in selected))

    def cross_counts(selected: list[dict[str, Any]]) -> dict[str, int]:
        return dict(Counter(f"{row.get('subject_label')}|{row.get('object_label')}" for row in selected))

    by_cell: dict[str, Counter] = defaultdict(Counter)
    for row in enriched:
        by_cell[row["positive_anchor_cell"]][row.get("review_relation_reliability")] += 1

    return {
        "rows": len(rows),
        "reliability_counts": counts_for("review_relation_reliability", enriched),
        "accept_rows": len(accept_rows),
        "reject_rows": len(reject_rows),
        "abstain_rows": len(abstain_rows),
        "accept_subject_counts": counts_for("subject_label", accept_rows),
        "accept_object_counts": counts_for("object_label", accept_rows),
        "accept_subject_object_counts": cross_counts(accept_rows),
        "accept_rank_band_counts": counts_for("rank_band_hidden", accept_rows),
        "accept_geometry_bucket_counts": counts_for("geometry_bucket_hidden", accept_rows),
        "accept_coverage_counts": counts_for("review_coverage", accept_rows),
        "accept_evidence_tier_counts": counts_for("evidence_tier", accept_rows),
        "accept_gt_status_counts": counts_for("gt_label_match_status_hidden", accept_rows),
        "reject_reason_counts": counts_for("primary_reason_v22", reject_rows),
        "abstain_reason_counts": counts_for("primary_reason_v22", abstain_rows),
        "affordance_cell_counts": {cell: dict(counter) for cell, counter in sorted(by_cell.items())},
        "accepted_examples": [
            {
                "candidate_relation": row.get("candidate_relation"),
                "subject_label": row.get("subject_label"),
                "object_label": row.get("object_label"),
                "subject_affordance_family": row.get("subject_affordance_family"),
                "anchor_affordance_family": row.get("anchor_affordance_family"),
                "rank_band_hidden": row.get("rank_band_hidden"),
                "geometry_bucket_hidden": row.get("geometry_bucket_hidden"),
                "review_coverage": row.get("review_coverage"),
                "evidence_tier": row.get("evidence_tier"),
                "gt_label_match_status_hidden": row.get("gt_label_match_status_hidden"),
            }
            for row in accept_rows
        ],
    }


def build_affordance_taxonomy() -> dict[str, Any]:
    return {
        "schema_version": "h002_v23_hanging_on_affordance_taxonomy_v1",
        "purpose": "Define candidate subject-anchor affordance cells for capacity scan; not labels and not model input.",
        "subject_affordance_families": {
            "soft_hanging_subject": sorted(SOFT_HANGING_SUBJECT_LABELS),
            "generic_subject": sorted(GENERIC_LABELS),
            "non_hanging_or_uncertain_subject": "default for all other subject labels",
        },
        "anchor_affordance_families": {
            "hanging_anchor_candidate": sorted(ANCHOR_LABELS),
            "support_or_furniture_confound_anchor": sorted(SUPPORT_CONFOUND_ANCHORS),
            "generic_anchor": sorted(GENERIC_LABELS),
            "uncertain_anchor": "default for all other object labels",
        },
        "positive_anchor_candidate_cell": {
            "definition": "soft_hanging_subject + hanging_anchor_candidate",
            "not_sufficient_for_accept_label": True,
            "requires_matched_hard_negative": True,
        },
    }


def build_capacity_scan_contract(path_summary: dict[str, Any], seed_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_v23_hanging_on_positive_anchor_capacity_scan_contract_v1",
        "name": NEXT_TODO,
        "split": "train_only",
        "posterior_smoke_allowed": False,
        "validation_or_test_allowed": False,
        "fills_new_labels": False,
        "primary_predicate": "hanging on",
        "diagnostic_predicates": ["attached to", "connected to"],
        "input_pool": "full train attachment_deferred pool with v21/v22 raw geometry and source-rank axes",
        "seed_from_v22": {
            "accept_rows": seed_summary["accept_rows"],
            "accept_subject_counts": seed_summary["accept_subject_counts"],
            "accept_object_counts": seed_summary["accept_object_counts"],
            "v22_path_selected": path_summary.get("selected_path"),
        },
        "required_controls": [
            "predicate fixed to hanging on",
            "subject_affordance_family matched or capped",
            "anchor_affordance_family matched or capped",
            "subject_label capped and reported",
            "object_label capped and reported",
            "rank_band matched or balanced",
            "geometry_bucket matched or balanced",
            "coverage_tier matched or balanced",
            "evidence_tier matched or balanced",
            "scan_id capped",
            "visible_endpoint_pair capped",
            "gt_label_match_status audit-only and reported after selection",
        ],
        "proxy_positive_definition_for_capacity_only": (
            "soft_hanging_subject + hanging_anchor_candidate + nonfar geometry bucket + usable coverage/source evidence"
        ),
        "proxy_hard_negative_definition_for_capacity_only": (
            "same or nearby subject-anchor affordance cell but geometry/coverage/context suggests support/proximity/duplicate/generic/non-hanging relation"
        ),
        "pre_label_gates": {
            "positive_anchor_candidate_rows_min": 300,
            "matched_positive_negative_cells_min": 30,
            "balanced_proxy_capacity_min": 160,
            "min_rank_band_coverage": 2,
            "min_geometry_bucket_coverage": 2,
            "max_single_subject_label_share": 0.20,
            "max_single_object_label_share": 0.20,
            "max_single_scan_share": 0.05,
            "max_visible_endpoint_pair_share": 0.04,
        },
        "if_capacity_passes_next": "candidate_mining_with_hidden_field_safe_visible_sheet",
        "if_capacity_fails_next": "attachment_deferred_blocker_synthesis_stop_posterior_route",
        "blocked_until_capacity_passes": [
            "candidate_mining",
            "packet_materialization",
            "label_fill",
            "label_ingestion",
            "target_independence_audit",
            "posterior_smoke",
            "multi_view_as_model_input",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    seed = summary["positive_anchor_seed_summary"]
    lines = [
        "# H002 V23 Hanging-On Positive-Anchor Repair Plan",
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
        "## Why This Plan",
        "",
        "v22 `hanging on` strict target은 `9/193`으로 positive-sparse였고 posterior target으로 부적합했다. "
        "하지만 accept 9개는 특정 subject-anchor affordance cell에 실제 reliable relation 후보가 있음을 보여준다.",
        "",
        "이 단계의 목적은 쉬운 positive를 추가하는 것이 아니라, positive-anchor cell 안에서 matched hard negative가 "
        "충분히 존재하는지를 다음 capacity scan에서 검증할 수 있게 plan을 고정하는 것이다.",
        "",
        "## Seed Summary",
        "",
        "```text",
        f"accept_rows = {seed['accept_rows']}",
        f"reject_rows = {seed['reject_rows']}",
        f"abstain_rows = {seed['abstain_rows']}",
        f"accept_subject_counts = {seed['accept_subject_counts']}",
        f"accept_object_counts = {seed['accept_object_counts']}",
        f"accept_subject_object_counts = {seed['accept_subject_object_counts']}",
        "```",
        "",
        "## Repair Principle",
        "",
        "- Predicate remains fixed to `hanging on`.",
        "- Positive-anchor cell is a sampling hypothesis, not a label.",
        "- Each positive-anchor cell must have matched hard negatives under affordance, rank, geometry, coverage, scan, and endpoint controls.",
        "- If capacity fails, stop this attachment-deferred posterior route rather than weakening controls.",
        "",
        "## Next Contract",
        "",
        "```text",
        f"name = {summary['capacity_scan_contract']['name']}",
        f"positive_anchor_candidate_rows_min = {summary['capacity_scan_contract']['pre_label_gates']['positive_anchor_candidate_rows_min']}",
        f"matched_positive_negative_cells_min = {summary['capacity_scan_contract']['pre_label_gates']['matched_positive_negative_cells_min']}",
        f"balanced_proxy_capacity_min = {summary['capacity_scan_contract']['pre_label_gates']['balanced_proxy_capacity_min']}",
        "```",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis artifact.",
        "- No validation/test rows used.",
        "- No new labels filled.",
        "- No posterior trained or evaluated.",
        "- Multi-view and mesh remain audit/confirmation evidence only.",
        "- H001 and paper artifacts were not modified.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_dir = as_abs(args.path_dir)
    ingestion_dir = as_abs(args.ingestion_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_summary = read_json(path_dir / "summary.json")
    ingestion_summary = read_json(ingestion_dir / "summary.json")
    rows = read_jsonl(ingestion_dir / "ingested_rows.jsonl")

    validation_errors = validate_inputs(path_summary, ingestion_summary, rows)
    seed_summary = summarize_rows(rows)
    taxonomy = build_affordance_taxonomy()
    capacity_contract = build_capacity_scan_contract(path_summary, seed_summary)

    output_paths = {
        "summary": output_dir / "summary.json",
        "repair_plan": output_dir / "repair_plan.json",
        "affordance_taxonomy": output_dir / "affordance_taxonomy.json",
        "positive_anchor_seed_summary": output_dir / "positive_anchor_seed_summary.json",
        "capacity_scan_contract": output_dir / "capacity_scan_contract.json",
        "report": output_dir / "report.md",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    repair_plan = {
        "schema_version": "h002_v23_hanging_on_positive_anchor_repair_plan_v1",
        "selected_route": "positive_anchor_repair_before_any_new_labels",
        "why_v22_is_frozen": {
            "class_counts": path_summary.get("audit_snapshot", {}).get("relation_binary", {}).get("class_counts"),
            "strict_clear_slice_count": path_summary.get("audit_snapshot", {}).get("relation_binary", {}).get("strict_clear_slice_count"),
            "diagnostic_clear_slice_count": path_summary.get("audit_snapshot", {}).get("relation_binary", {}).get("diagnostic_clear_slice_count"),
            "risk_flags": path_summary.get("audit_snapshot", {}).get("counts", {}).get("full_quick_probe_risk_flags"),
        },
        "repair_principle": (
            "Mine positive-anchor cells only if matched hard negatives exist under subject/anchor affordance, "
            "rank, geometry, coverage, scan, and endpoint controls."
        ),
        "affordance_taxonomy": taxonomy,
        "capacity_scan_contract": capacity_contract,
    }

    summary = {
        "schema_version": "h002_v23_hanging_on_positive_anchor_repair_plan_v1",
        "status": STATUS if not validation_errors else STATUS + "_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_artifacts": {
            "path_decision_summary": rel_path(path_dir / "summary.json"),
            "ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "ingested_rows": rel_path(ingestion_dir / "ingested_rows.jsonl"),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "positive_anchor_seed_summary": seed_summary,
        "affordance_taxonomy": taxonomy,
        "capacity_scan_contract": capacity_contract,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "hidden_fields_as_model_input": False,
            "existing_gt_match_axis_as_model_input": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "h001_artifacts_modified": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["repair_plan"], repair_plan)
    write_json(output_paths["affordance_taxonomy"], taxonomy)
    write_json(output_paths["positive_anchor_seed_summary"], seed_summary)
    write_json(output_paths["capacity_scan_contract"], capacity_contract)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    seed = summary["positive_anchor_seed_summary"]
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"accept_rows={seed['accept_rows']}")
    print(f"reject_rows={seed['reject_rows']}")
    print(f"abstain_rows={seed['abstain_rows']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
