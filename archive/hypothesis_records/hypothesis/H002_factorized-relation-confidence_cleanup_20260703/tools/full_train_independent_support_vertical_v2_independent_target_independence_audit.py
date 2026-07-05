#!/usr/bin/env python3
"""Audit independent support/vertical target independence and controlled slices."""

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

DEFAULT_INGESTION_DIR = RGA_ROOT / "independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver"

GEOMETRY_TARGET = "geometry_validity_independent_target"
RELIABILITY_TARGET = "relation_reliability_independent_target"
TARGET_INPUTS = {
    GEOMETRY_TARGET: "geometry_validity_independent_posterior_rows.jsonl",
    RELIABILITY_TARGET: "relation_reliability_independent_posterior_rows.jsonl",
}

LABEL_SOURCE = "codex_independent_support_vertical_visible_only_bootstrap"

SLICE_SPECS = {
    "original_independent": {
        "balanced_keys": [],
        "reason": "full independent binary target",
        "priority": 99,
    },
    "prior_relation_validity_balanced_independent": {
        "balanced_keys": ["relation_validity_label_hidden"],
        "reason": "matched positives/negatives within prior hidden relation-validity label",
        "priority": 10,
    },
    "prior_label_use_balanced_independent": {
        "balanced_keys": ["label_use_hidden"],
        "reason": "matched positives/negatives within prior hidden label-use bucket",
        "priority": 10,
    },
    "prior_target_y_balanced_independent": {
        "balanced_keys": ["posterior_target_y_hidden"],
        "reason": "matched positives/negatives within prior hidden target-y bucket",
        "priority": 10,
    },
    "rank_band_balanced_independent": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "matched positives/negatives within hidden semantic rank band",
        "priority": 1,
    },
    "queue_balanced_independent": {
        "balanced_keys": ["queue_kind_hidden"],
        "reason": "matched positives/negatives within hidden HL/LH queue",
        "priority": 2,
    },
    "role_balanced_independent": {
        "balanced_keys": ["proposed_audit_role_hidden"],
        "reason": "matched positives/negatives within hidden proposed audit role",
        "priority": 3,
    },
    "label_match_balanced_independent": {
        "balanced_keys": ["label_match_status_hidden"],
        "reason": "matched positives/negatives within hidden label-match status",
        "priority": 4,
    },
    "geometry_status_balanced_independent": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "matched positives/negatives within expected hidden geometry status",
        "priority": 5,
    },
    "family_balanced_independent": {
        "balanced_keys": ["predicate_family"],
        "reason": "matched positives/negatives within visible predicate family",
        "priority": 6,
    },
    "predicate_balanced_independent": {
        "balanced_keys": ["predicate_label"],
        "reason": "matched positives/negatives within visible predicate label",
        "priority": 7,
    },
    "rank_family_balanced_independent": {
        "balanced_keys": ["rank_band_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden rank band and visible family",
        "priority": 8,
    },
    "queue_family_balanced_independent": {
        "balanced_keys": ["queue_kind_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden queue and visible family",
        "priority": 9,
    },
    "role_family_balanced_independent": {
        "balanced_keys": ["proposed_audit_role_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden role and visible family",
        "priority": 9,
    },
    "prior_label_rank_balanced_independent": {
        "balanced_keys": ["relation_validity_label_hidden", "rank_band_hidden"],
        "reason": "matched positives/negatives within prior label and rank band",
        "priority": 11,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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
    return base.read_jsonl(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    base.write_json(path, payload)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    base.write_jsonl(path, rows)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    base.write_csv(path, rows)


def validate_rows(target_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    seen = set()
    for index, row in enumerate(rows, start=1):
        blind_id = row.get("blind_review_id")
        if blind_id in seen:
            errors.append({"target_name": target_name, "error_type": "duplicate_blind_review_id", "row_number": index, "blind_review_id": blind_id})
        seen.add(blind_id)
        if row.get("target_name") != target_name:
            errors.append(
                {
                    "target_name": target_name,
                    "error_type": "unexpected_target_name",
                    "row_number": index,
                    "blind_review_id": blind_id,
                    "value": row.get("target_name"),
                }
            )
        if row.get("predicate_family") not in {"support_contact", "relative_vertical"}:
            errors.append(
                {
                    "target_name": target_name,
                    "error_type": "row_outside_support_vertical_scope",
                    "row_number": index,
                    "blind_review_id": blind_id,
                    "predicate_family": row.get("predicate_family"),
                }
            )
        if row.get("human_confirmed") is not False:
            errors.append(
                {
                    "target_name": target_name,
                    "error_type": "unexpected_human_confirmed_flag",
                    "row_number": index,
                    "blind_review_id": blind_id,
                    "human_confirmed": row.get("human_confirmed"),
                }
            )
        if "audit_only_independent_label_fields" not in row:
            errors.append({"target_name": target_name, "error_type": "missing_audit_only_independent_label_fields", "row_number": index, "blind_review_id": blind_id})
        evidence = row.get("deployable_evidence_after_label_lock", {})
        if evidence.get("forbidden_as_posterior_input", {}).get("multi_view_as_model_input") is not True:
            errors.append({"target_name": target_name, "error_type": "missing_multiview_forbidden_flag", "row_number": index, "blind_review_id": blind_id})
    return errors


def build_slices_for_target(
    target_name: str,
    rows: list[dict[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    slice_dir = output_dir / "target_slices" / target_name
    slice_summaries: list[dict[str, Any]] = []
    group_table: list[dict[str, Any]] = []
    group_summary_rows: list[dict[str, Any]] = []
    for slice_name, spec in SLICE_SPECS.items():
        slice_rows = base.balanced_slice(rows, target_name, slice_name, spec)
        path = slice_dir / f"{slice_name}.jsonl"
        write_jsonl(path, slice_rows)
        groups, summaries = base.all_group_summaries(slice_rows, target_name, slice_name)
        group_table.extend(groups)
        group_summary_rows.extend(summaries)
        slice_summaries.append(base.slice_summary(target_name, slice_name, spec, slice_rows, summaries, path))
    return slice_summaries, group_table, group_summary_rows


def per_target_decision(target_name: str, summaries: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    original = next(item for item in summaries if item["slice_name"] == "original_independent")
    strict = base.choose_candidate(summaries, "strict_candidate")
    clean = base.choose_candidate(summaries, "clean_plus_visible_candidate")
    construction = base.choose_candidate(summaries, "construction_only_candidate")
    if errors:
        status = "target_independence_audit_errors"
        decision = "Fix row validation errors before using any independent target slice."
        next_step = "fix_independent_target_independence_audit_errors"
    elif strict:
        status = "strict_controlled_slice_ready"
        decision = (
            "A strict independent controlled slice clears harmful prior-label carryover and "
            "construction-risk checks. Source-score feature join is still required before any posterior smoke."
        )
        next_step = "independent_source_feature_join_then_controlled_posterior_smoke"
    elif construction:
        status = "strict_blocked_construction_slice_available"
        decision = (
            "No strict slice clears harmful prior-label carryover. A construction-only slice exists for "
            "plumbing/error diagnostics, but not method validation."
        )
        next_step = "revise_independent_target_or_collect_human_confirmed_labels"
    else:
        status = "blocked_no_controlled_slice"
        decision = "No size-ready strict or construction-only controlled slice exists."
        next_step = "revise_independent_target_or_collect_human_confirmed_labels"
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
        "# H002 Independent Support/Vertical V2 Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage target audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Hidden metadata is used only after independent label lock for audit and controlled-slice construction.",
        "- Harmful prior carryover is separated from expected geometry alignment.",
        "- Geometry-status alignment is reported but not used as the main harmful-carryover blocker.",
        "- Codex independent labels are not human-confirmed paper evidence.",
        "- Source score/rank and `p_geom_valid` feature join remains pending.",
        "- Multi-view remains audit evidence only, not model input.",
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
    lines.extend(
        [
            "",
            "## Controlled Slices",
            "",
            "| Target | Slice | Rows | Pos | Neg | Harmful Risks | Construction Risks | Geometry Align | Visible Risks | Strict | Construction Only |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in sorted(
        summary["slice_summaries"],
        key=lambda row: (
            row["target_name"],
            not row["strict_candidate"],
            not row["construction_only_candidate"],
            row["priority"],
            -row["rows"],
        ),
    ):
        lines.append(
            f"| `{item['target_name']}` | `{item['slice_name']}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['harmful_prior_risk_count']} | {item['construction_risk_count']} | "
            f"{item['expected_geometry_alignment_risk_count']} | {item['visible_non_target_risk_count']} | "
            f"`{item['strict_candidate']}` | `{item['construction_only_candidate']}` |"
        )
    lines.extend(["", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_dir = as_abs(args.ingestion_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

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
        rows = read_jsonl(input_path)
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

    strict_ready_targets = [
        target for target, decision in target_decisions.items() if decision["recommended_strict_slice"] is not None
    ]
    construction_only_targets = [
        target
        for target, decision in target_decisions.items()
        if decision["recommended_strict_slice"] is None and decision["recommended_construction_slice"] is not None
    ]
    blocked_targets = [
        target
        for target, decision in target_decisions.items()
        if decision["recommended_strict_slice"] is None and decision["recommended_construction_slice"] is None
    ]

    if all_validation_errors:
        status = "full_train_independent_support_vertical_v2_independent_target_independence_audit_errors"
        decision = "Fix validation errors before any independent target slice can be used."
        next_todo = "fix_full_train_independent_support_vertical_v2_independent_target_independence_audit_errors"
    elif RELIABILITY_TARGET in strict_ready_targets:
        status = "full_train_independent_support_vertical_v2_independent_target_independence_audit_relation_strict_slice_ready"
        decision = (
            "A strict independent relation-reliability slice exists. Posterior smoke is still not immediate "
            "because source score/rank and p_geom_valid feature join is pending."
        )
        next_todo = "full_train_independent_support_vertical_v2_independent_source_feature_join"
    elif construction_only_targets:
        status = "full_train_independent_support_vertical_v2_independent_target_independence_audit_strict_blocked_construction_slice_available"
        decision = (
            "No strict relation-reliability slice clears harmful prior-label carryover. Construction-only "
            "diagnostic slices may be used for plumbing/error analysis, but posterior method validation "
            "remains blocked."
        )
        next_todo = "revise_independent_target_or_collect_human_confirmed_support_vertical_labels"
    else:
        status = "full_train_independent_support_vertical_v2_independent_target_independence_audit_blocked"
        decision = "No size-ready strict or construction-only controlled slice exists for independent relation reliability."
        next_todo = "revise_independent_target_or_collect_human_confirmed_support_vertical_labels"

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
        "schema_version": "h002_support_vertical_v2_independent_target_independence_audit_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": input_paths,
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "selected_scope": ["relative_vertical", "support_contact"],
            "label_source": LABEL_SOURCE,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_used_for_audit_only": True,
            "independent_label_fields_used_for_target_or_audit_only": True,
            "v2_audit_axes_used_for_audit_only": True,
            "source_score_feature_join_pending": True,
            "multi_view_as_model_input": False,
            "expected_geometry_alignment_separated_from_harmful_carryover": True,
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
        "harmful_prior_carryover_keys": base.HARMFUL_PRIOR_CARRYOVER_KEYS,
        "construction_keys": base.CONSTRUCTION_KEYS,
        "expected_geometry_alignment_keys": base.EXPECTED_GEOMETRY_ALIGNMENT_KEYS,
        "visible_non_target_keys": base.VISIBLE_NON_TARGET_KEYS,
        "target_decisions": target_decisions,
        "strict_ready_targets": strict_ready_targets,
        "construction_only_targets": construction_only_targets,
        "blocked_targets": blocked_targets,
        "slice_summaries": all_slice_summaries,
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_csv(
        output_paths["slice_summaries"],
        [
            {
                "target_name": item["target_name"],
                "slice_name": item["slice_name"],
                "rows": item["rows"],
                "positive": item["positive"],
                "negative": item["negative"],
                "min_class": item["min_class"],
                "harmful_prior_risk_count": item["harmful_prior_risk_count"],
                "construction_risk_count": item["construction_risk_count"],
                "expected_geometry_alignment_risk_count": item["expected_geometry_alignment_risk_count"],
                "visible_non_target_risk_count": item["visible_non_target_risk_count"],
                "size_ready": item["size_ready"],
                "strict_candidate": item["strict_candidate"],
                "clean_plus_visible_candidate": item["clean_plus_visible_candidate"],
                "construction_only_candidate": item["construction_only_candidate"],
                "balanced_keys": "|".join(item["balanced_keys"]),
                "path": item["path"],
            }
            for item in all_slice_summaries
        ],
    )
    write_csv(output_paths["group_summaries"], all_group_summaries)
    write_csv(output_paths["group_table"], all_group_rows)
    write_jsonl(output_paths["validation_errors"], all_validation_errors)
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
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
