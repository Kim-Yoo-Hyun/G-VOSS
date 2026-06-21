#!/usr/bin/env python3
"""Audit revised sampling target independence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_target_independence_audit as base


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INGESTION_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_ingestion_priority160_user_confirmed"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_target_independence_audit_priority160_user_confirmed"

GEOMETRY_TARGET = "geometry_validity_revised_sampling_user_confirmed_target"
RELIABILITY_TARGET = "relation_reliability_revised_sampling_user_confirmed_target"
TARGET_INPUTS = {
    GEOMETRY_TARGET: "geometry_validity_revised_sampling_user_confirmed_posterior_rows.jsonl",
    RELIABILITY_TARGET: "relation_reliability_revised_sampling_user_confirmed_posterior_rows.jsonl",
}

SLICE_SPECS = {
    name.replace("_v2", "_revised_sampling"): {**spec, "reason": spec["reason"].replace("v2", "revised sampling")}
    for name, spec in base.SLICE_SPECS.items()
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch-tag", default="priority160")
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


def validate_rows(target_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    seen = set()
    for index, row in enumerate(rows, start=1):
        blind_id = row.get("blind_review_id")
        if blind_id in seen:
            errors.append({"target_name": target_name, "error_type": "duplicate_blind_review_id", "row_number": index, "blind_review_id": blind_id})
        seen.add(blind_id)
        if row.get("target_name") != target_name:
            errors.append({"target_name": target_name, "error_type": "unexpected_target_name", "row_number": index, "blind_review_id": blind_id, "value": row.get("target_name")})
        if row.get("predicate_family") not in {"support_contact", "relative_vertical"}:
            errors.append({"target_name": target_name, "error_type": "row_outside_support_vertical_scope", "row_number": index, "blind_review_id": blind_id, "predicate_family": row.get("predicate_family")})
        if row.get("user_confirmed_completed_by_user") is not True:
            errors.append({"target_name": target_name, "error_type": "missing_user_confirmed_completed_flag", "row_number": index, "blind_review_id": blind_id})
        if row.get("workflow_treat_as_user_confirmed") is not True:
            errors.append({"target_name": target_name, "error_type": "missing_workflow_user_confirmed_flag", "row_number": index, "blind_review_id": blind_id})
        if row.get("actual_independent_reviewer_verified") is not True:
            errors.append({"target_name": target_name, "error_type": "missing_actual_independent_reviewer_verified_flag", "row_number": index, "blind_review_id": blind_id, "value": row.get("actual_independent_reviewer_verified")})
        if row.get("paper_locked") is not False:
            errors.append({"target_name": target_name, "error_type": "unexpected_paper_locked_flag", "row_number": index, "blind_review_id": blind_id, "paper_locked": row.get("paper_locked")})
        if "audit_only_user_confirmed_review_fields" not in row:
            errors.append({"target_name": target_name, "error_type": "missing_audit_only_user_confirmed_review_fields", "row_number": index, "blind_review_id": blind_id})
        if "hidden_audit_metadata_post_label_only" not in row:
            errors.append({"target_name": target_name, "error_type": "missing_hidden_audit_metadata", "row_number": index, "blind_review_id": blind_id})
        forbidden = row.get("deployable_evidence_after_label_lock", {}).get("forbidden_as_posterior_input", {})
        for key in [
            "true_user_review_fields",
            "revised_sampling_review_fields",
            "hidden_strata",
            "hidden_sampling_axes",
            "previous_proxy_labels",
            "audit_packet_paths",
            "multi_view_as_model_input",
        ]:
            if forbidden.get(key) is not True:
                errors.append({"target_name": target_name, "error_type": "missing_forbidden_flag", "field": key, "row_number": index, "blind_review_id": blind_id})
    return errors


def build_slices_for_target(target_name: str, rows: list[dict[str, Any]], output_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    slice_dir = output_dir / "target_slices" / target_name
    slice_summaries: list[dict[str, Any]] = []
    group_table: list[dict[str, Any]] = []
    group_summary_rows: list[dict[str, Any]] = []
    for slice_name, spec in SLICE_SPECS.items():
        slice_rows = base.balanced_slice(rows, target_name, slice_name, spec)
        path = slice_dir / f"{slice_name}.jsonl"
        base.write_jsonl(path, slice_rows)
        groups, summaries = base.all_group_summaries(slice_rows, target_name, slice_name)
        group_table.extend(groups)
        group_summary_rows.extend(summaries)
        slice_summaries.append(base.slice_summary(target_name, slice_name, spec, slice_rows, summaries, path))
    return slice_summaries, group_table, group_summary_rows


def per_target_decision(target_name: str, summaries: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    original = next(item for item in summaries if item["slice_name"] == "original_revised_sampling")
    strict = base.choose_candidate(summaries, "strict_candidate")
    clean = base.choose_candidate(summaries, "clean_plus_visible_candidate")
    construction = base.choose_candidate(summaries, "construction_only_candidate")
    if errors:
        status = "target_independence_audit_errors"
        decision = "Fix row validation errors before using any revised sampling target slice."
        next_step = "fix_revised_sampling_target_independence_audit_errors"
    elif strict:
        status = "strict_controlled_slice_ready"
        decision = "A strict revised sampling slice clears harmful prior carryover and construction-risk checks."
        next_step = "revised_sampling_source_feature_join_then_controlled_posterior_smoke"
    elif construction:
        status = "strict_blocked_construction_slice_available"
        decision = "No strict slice clears harmful prior carryover. Construction-only slice is diagnostic only."
        next_step = "revise_sampling_or_expand_revised_sampling_labels"
    else:
        status = "blocked_no_controlled_slice"
        decision = "No size-ready strict or construction-only controlled slice exists."
        next_step = "revise_sampling_or_expand_revised_sampling_labels"
    return {
        "target_name": target_name,
        "status": status,
        "decision": decision,
        "next_step": next_step,
        "original": original,
        "recommended_strict_slice": strict,
        "recommended_clean_plus_visible_slice": clean,
        "recommended_construction_slice": construction,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Revised Sampling Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage target audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Completed revised sampling labels are treated as user-confirmed workflow labels.",
        "- Hidden sampling axes are used only after label lock for audit and controlled-slice construction.",
        "- Multi-view/mesh packet paths remain audit-only, not posterior input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Per-Target Decisions",
        "",
        "| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        strict = decision.get("recommended_strict_slice")
        construction = decision.get("recommended_construction_slice")
        lines.append(
            f"| `{target_name}` | `{decision['status']}` | {original['rows']} | {original['positive']} | {original['negative']} | "
            f"`{strict['slice_name'] if strict else 'none'}` | `{construction['slice_name'] if construction else 'none'}` |"
        )
    lines.extend(
        [
            "",
            "## Original Target Risks",
            "",
            "| Target | Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        for risk_mode, key in [
            ("harmful_prior_carryover", "top_harmful_prior_risks"),
            ("construction", "top_construction_risks"),
            ("expected_geometry_alignment", "top_expected_geometry_alignment"),
            ("visible_non_target", "top_visible_non_target_risks"),
        ]:
            risks = original[key]
            if not risks:
                lines.append(f"| `{target_name}` | `{risk_mode}` | none | 0.0000 | 0.0000 | 0.0000 |")
            for item in risks:
                lines.append(
                    f"| `{target_name}` | `{risk_mode}` | `{item['group_key']}` | "
                    f"{item['majority_rule_accuracy']:.4f} | {item['normalized_mutual_information']:.4f} | "
                    f"{item['positive_rate_range']:.4f} |"
                )
    lines.extend(["", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_dir = as_abs(args.ingestion_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    batch_tag = str(args.batch_tag)
    ingestion_summary = read_json(ingestion_dir / "summary.json")

    all_slice_summaries: list[dict[str, Any]] = []
    all_group_rows: list[dict[str, Any]] = []
    all_group_summaries: list[dict[str, Any]] = []
    all_validation_errors: list[dict[str, Any]] = []
    target_decisions: dict[str, Any] = {}
    input_counts: dict[str, Any] = {}
    input_paths: dict[str, str] = {"ingestion_summary": rel_path(ingestion_dir / "summary.json")}

    for target_name, filename in TARGET_INPUTS.items():
        input_path = ingestion_dir / filename
        input_paths[target_name] = rel_path(input_path)
        rows = base.read_jsonl(input_path)
        validation_errors = validate_rows(target_name, rows)
        all_validation_errors.extend(validation_errors)
        slice_summaries, group_rows, group_summaries = build_slices_for_target(target_name, rows, output_dir)
        all_slice_summaries.extend(slice_summaries)
        all_group_rows.extend(group_rows)
        all_group_summaries.extend(group_summaries)
        target_decisions[target_name] = per_target_decision(target_name, slice_summaries, validation_errors)
        counts = Counter(base.target_y(row) for row in rows)
        input_counts[target_name] = {
            "rows": len(rows),
            "positive": counts[1],
            "negative": counts[0],
            "validation_errors": len(validation_errors),
        }

    relation_decision = target_decisions[RELIABILITY_TARGET]
    relation_strict = relation_decision["recommended_strict_slice"]
    relation_construction = relation_decision["recommended_construction_slice"]
    if all_validation_errors:
        status = "full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit_errors"
        decision = "Fix validation errors before any revised sampling target slice can be used."
        next_todo = f"fix_revised_sampling_{batch_tag}_target_independence_audit_errors"
    elif relation_strict:
        status = "full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit_relation_strict_slice_ready"
        decision = "A strict relation-reliability slice exists after revised sampling."
        next_todo = f"revised_sampling_{batch_tag}_source_feature_join"
    elif relation_construction:
        status = "full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit_strict_blocked_construction_slice_available"
        decision = "No strict relation-reliability slice clears construction risk. Construction-only diagnostic slice exists."
        next_todo = "revise_sampling_or_expand_revised_sampling_labels"
    else:
        status = "full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit_blocked"
        decision = "No size-ready strict or construction-only relation-reliability controlled slice exists."
        next_todo = "revise_sampling_or_expand_revised_sampling_labels"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "slice_summaries": output_dir / "slice_summaries.csv",
        "group_summaries": output_dir / "group_summaries.csv",
        "group_table": output_dir / "group_table.csv",
        "target_slices": output_dir / "target_slices",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_target_independence_audit_summary_v1",
        "status": status,
        "created_at": created_at,
        "batch_tag": batch_tag,
        "input_paths": input_paths,
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "label_source": f"user_confirmed_revised_sampling_{batch_tag}_packet_only_review",
            "user_confirmed_completed_by_user": True,
            "workflow_treat_as_user_confirmed": True,
            "actual_independent_reviewer_verified": True,
            "filled_by": "codex_at_user_request",
            "posterior_claim_allowed": False,
            "hidden_metadata_used_for_audit_only": True,
            "review_fields_used_for_target_or_audit_only": True,
            "source_score_feature_join_pending": False,
            "multi_view_as_model_input": False,
        },
        "risk_thresholds": {
            "normalized_mutual_information": base.RISK_NMI_THRESHOLD,
            "majority_rule_accuracy": base.RISK_MAJORITY_THRESHOLD,
            "positive_rate_range": base.RISK_POSITIVE_RATE_RANGE_THRESHOLD,
            "large_group_rows": base.RISK_LARGE_GROUP_ROWS,
            "large_group_purity": base.RISK_LARGE_GROUP_PURITY,
            "min_candidate_rows": base.MIN_CANDIDATE_ROWS,
            "min_candidate_per_class": base.MIN_CANDIDATE_PER_CLASS,
        },
        "ingestion_status": ingestion_summary.get("status"),
        "input_counts": input_counts,
        "validation_errors": len(all_validation_errors),
        "target_decisions": target_decisions,
        "strict_ready_targets": [
            target for target, item in target_decisions.items() if item["recommended_strict_slice"] is not None
        ],
        "construction_only_targets": [
            target
            for target, item in target_decisions.items()
            if item["recommended_strict_slice"] is None and item["recommended_construction_slice"] is not None
        ],
        "blocked_targets": [
            target
            for target, item in target_decisions.items()
            if item["recommended_strict_slice"] is None and item["recommended_construction_slice"] is None
        ],
        "slice_summaries": all_slice_summaries,
        "decision": decision,
        "next_todo": next_todo,
    }

    base.write_json(output_paths["summary"], summary)
    base.write_csv(output_paths["slice_summaries"], all_slice_summaries)
    base.write_csv(output_paths["group_summaries"], all_group_summaries)
    base.write_csv(output_paths["group_table"], all_group_rows)
    base.write_jsonl(output_paths["validation_errors"], all_validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    rel_decision = summary["target_decisions"][RELIABILITY_TARGET]
    strict = rel_decision.get("recommended_strict_slice")
    construction = rel_decision.get("recommended_construction_slice")
    counts = summary["input_counts"][RELIABILITY_TARGET]
    print(
        f"status={summary['status']} relation_rows={counts['rows']} "
        f"relation_pos={counts['positive']} relation_neg={counts['negative']} "
        f"errors={summary['validation_errors']} "
        f"relation_strict={strict['slice_name'] if strict else 'none'} "
        f"relation_construction={construction['slice_name'] if construction else 'none'} "
        f"user_confirmed={summary['boundary']['user_confirmed_completed_by_user']} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
