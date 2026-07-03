#!/usr/bin/env python3
"""Lock H002 paper-facing claim boundaries after official metric result review."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner"
DEFAULT_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review"

EXPECTED_REVIEW_STATUS = "h002_compatibility_dataset_v3_official_metric_result_review_after_runner_ready_with_boundaries"
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review_locked"
STATUS_ERRORS = "h002_compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review_input_errors"
SELECTED_PATH = "official_claim_boundary_locked_select_paper_table_skeleton"
NEXT_TODO = "compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def row_lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str] | None:
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            return row
    return None


def validate_inputs(
    review_summary: dict[str, Any],
    eval_manifest: dict[str, Any],
    review_dir: Path,
    family_decisions: list[dict[str, str]],
    paper_gate: list[dict[str, str]],
    blocked_claims: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review_summary.get("status")})
    if review_summary.get("next_todo") != EXPECTED_REVIEW_NEXT:
        errors.append({"error_type": "unexpected_review_next_todo", "actual": review_summary.get("next_todo")})
    if review_summary.get("validation_errors") != 0:
        errors.append({"error_type": "review_validation_errors", "actual": review_summary.get("validation_errors")})
    if line_count(review_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "review_validation_errors_file_not_empty"})

    decision = review_summary.get("decision", {})
    if decision.get("paper_level_experiment_execution_gate") != "passed_with_caveats":
        errors.append({"error_type": "unexpected_execution_gate", "actual": decision.get("paper_level_experiment_execution_gate")})
    if decision.get("paper_result_promotion") != "not_yet":
        errors.append({"error_type": "unexpected_paper_result_promotion", "actual": decision.get("paper_result_promotion")})
    if decision.get("next_action") != "claim_boundary_lock":
        errors.append({"error_type": "unexpected_next_action", "actual": decision.get("next_action")})

    boundary = eval_manifest.get("boundary", {})
    required_boundary = {
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "official_validation_metric_produced": True,
        "paper_metric_produced": False,
        "p_obs_claim_enabled": False,
        "p_rel_claim_enabled": False,
        "z_e_excluded_from_main_C_e": True,
        "q_e_excluded_from_main_C_e": True,
        "h001_p_geom_valid_excluded_from_main_G_e": True,
    }
    for key, expected in required_boundary.items():
        if boundary.get(key) is not expected:
            errors.append({"error_type": "unexpected_eval_boundary", "key": key, "actual": boundary.get(key), "expected": expected})

    expected_family_status = {
        "relative_vertical": "paper_candidate_main_evidence",
        "size_relative": "paper_candidate_main_evidence",
        "relative_horizontal": "paper_candidate_with_frame_control_caveat",
        "support_contact": "diagnostic_challenging_only",
    }
    for family, expected_status in expected_family_status.items():
        row = row_lookup(family_decisions, route_family=family)
        if row is None:
            errors.append({"error_type": "missing_family_decision", "route_family": family})
        elif row.get("status") != expected_status:
            errors.append({"error_type": "unexpected_family_status", "route_family": family, "actual": row.get("status"), "expected": expected_status})

    required_gates = {
        "primary_metric_vs_baselines": "pass",
        "wrong_T_and_shuffled_G_controls": "pass",
        "relative_horizontal_frame_control": "caveat",
        "support_contact_claim": "caveat",
        "paper_promotion": "conditional_pass",
    }
    for gate, expected_status in required_gates.items():
        row = row_lookup(paper_gate, gate=gate)
        if row is None:
            errors.append({"error_type": "missing_gate", "gate": gate})
        elif row.get("status") != expected_status:
            errors.append({"error_type": "unexpected_gate_status", "gate": gate, "actual": row.get("status"), "expected": expected_status})

    required_blocked = {
        "all_relation_generalization",
        "solved_support_contact",
        "strong_relative_horizontal_frame_invariance",
        "p_rel_or_p_obs_reliability",
        "source_reranking_recall_tradeoff",
        "official_test_result",
    }
    seen_blocked = {row.get("blocked_claim") for row in blocked_claims}
    for claim in sorted(required_blocked - seen_blocked):
        errors.append({"error_type": "missing_blocked_claim", "blocked_claim": claim})
    return errors


def locked_table_roles(family_decisions: list[dict[str, str]]) -> list[dict[str, Any]]:
    relation_types = {
        "relative_vertical": "higher than; lower than",
        "size_relative": "bigger than; smaller than",
        "relative_horizontal": "left; right; front; behind",
        "support_contact": "standing on; lying on",
    }
    roles = {
        "relative_vertical": {
            "locked_table_role": "main_mechanism_table_primary_row",
            "paper_success_role": "primary",
            "include_in_primary_macro": "yes",
            "must_report_caveat": "no",
            "claim_boundary": "predicate-geometry compatibility is strongly supported for signed vertical-order relations",
        },
        "size_relative": {
            "locked_table_role": "main_mechanism_table_primary_row",
            "paper_success_role": "primary",
            "include_in_primary_macro": "yes",
            "must_report_caveat": "no",
            "claim_boundary": "predicate-geometry compatibility is strongly supported for signed size-comparison relations",
        },
        "relative_horizontal": {
            "locked_table_role": "main_mechanism_table_caveated_row",
            "paper_success_role": "conditional",
            "include_in_primary_macro": "no_report_separately_or_macro_plus_without_claim_overreach",
            "must_report_caveat": "yes_frame_aware_not_frame_invariant",
            "claim_boundary": "frame-aware horizontal compatibility evidence is allowed, but strong frame-invariant wording is blocked",
        },
        "support_contact": {
            "locked_table_role": "diagnostic_failure_taxonomy_row",
            "paper_success_role": "diagnostic",
            "include_in_primary_macro": "no",
            "must_report_caveat": "yes_challenging_not_solved",
            "claim_boundary": "contact/pose route exposes current evidence limitations and is not a solved success case",
        },
    }
    rows: list[dict[str, Any]] = []
    for family in ["relative_vertical", "size_relative", "relative_horizontal", "support_contact"]:
        source = row_lookup(family_decisions, route_family=family) or {}
        rows.append(
            {
                "route_family": family,
                "relation_types": relation_types[family],
                "review_status": source.get("status", ""),
                "locked_table_role": roles[family]["locked_table_role"],
                "paper_success_role": roles[family]["paper_success_role"],
                "include_in_primary_macro": roles[family]["include_in_primary_macro"],
                "must_report_caveat": roles[family]["must_report_caveat"],
                "claim_boundary": roles[family]["claim_boundary"],
                "rows": source.get("rows", ""),
                "positive": source.get("positive", ""),
                "negative": source.get("negative", ""),
                "m4_auroc": source.get("m4_auroc", ""),
                "m4_balanced_accuracy": source.get("m4_balanced_accuracy", ""),
            }
        )
    return rows


def allowed_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "C01_official_validation_Ce_mechanism",
            "status": "allowed",
            "allowed_wording": "On official validation candidates, C_e = compatibility(T_e, G_e) provides paper-candidate evidence for route-specific predicate-geometry compatibility.",
            "required_qualifier": "validation-only; no official test; no source-reranking recall claim",
        },
        {
            "claim_id": "C02_primary_route_evidence",
            "status": "allowed",
            "allowed_wording": "relative_vertical and size_relative are primary mechanism rows because M4 strongly outperforms semantic-only, geometry-only, and concat baselines and collapses under matched controls.",
            "required_qualifier": "restricted to these signed comparison routes",
        },
        {
            "claim_id": "C03_horizontal_caveated_route",
            "status": "allowed_with_caveat",
            "allowed_wording": "relative_horizontal can be reported as frame-aware compatibility evidence.",
            "required_qualifier": "must state that frame-swap control leaves only a modest margin and frame-invariant claims are blocked",
        },
        {
            "claim_id": "C04_support_contact_diagnostic",
            "status": "allowed_as_diagnostic",
            "allowed_wording": "support_contact is useful as a challenging diagnostic route showing where point/contact evidence and class-pair shortcuts still limit the framework.",
            "required_qualifier": "must not describe support_contact as solved or as a primary success route",
        },
        {
            "claim_id": "C05_factor_boundary",
            "status": "allowed",
            "allowed_wording": "The official C_e metric excludes Z_e, Q_e, and H001 p_geom_valid from the compatibility input.",
            "required_qualifier": "Z_e/Q_e/p_rel/p_obs can only be discussed as future or disabled branches in this experiment",
        },
    ]


def locked_blocked_claim_rows(previous_blocked: list[dict[str, str]]) -> list[dict[str, Any]]:
    severity = {
        "all_relation_generalization": "hard_block",
        "solved_support_contact": "hard_block",
        "strong_relative_horizontal_frame_invariance": "hard_block",
        "p_rel_or_p_obs_reliability": "hard_block",
        "source_reranking_recall_tradeoff": "hard_block",
        "official_test_result": "hard_block",
    }
    rows: list[dict[str, Any]] = []
    for row in previous_blocked:
        claim = row.get("blocked_claim", "")
        rows.append(
            {
                "blocked_claim": claim,
                "lock_status": severity.get(claim, "blocked"),
                "reason": row.get("reason", ""),
                "replacement_wording": replacement_wording(claim),
            }
        )
    rows.extend(
        [
            {
                "blocked_claim": "paper_sota_or_full_3dssg_improvement",
                "lock_status": "hard_block",
                "reason": "Current experiment is a C_e mechanism evaluation on selected official validation candidate rows.",
                "replacement_wording": "Use selected-route mechanism evidence, not SOTA or full 3DSSG improvement wording.",
            },
            {
                "blocked_claim": "human_reliability_or_abstention_label_claim",
                "lock_status": "hard_block",
                "reason": "Current official metric uses GT/counterfactual candidate construction, not human-audited accept/reject/abstain targets.",
                "replacement_wording": "Discuss p_obs/abstention only as framework design and future evaluation.",
            },
        ]
    )
    return rows


def replacement_wording(claim: str) -> str:
    replacements = {
        "all_relation_generalization": "Use selected-route generalization over relative_vertical, size_relative, relative_horizontal, and support_contact diagnostics.",
        "solved_support_contact": "Use support_contact as challenging diagnostic/failure taxonomy evidence.",
        "strong_relative_horizontal_frame_invariance": "Use frame-aware horizontal compatibility with a frame-control caveat.",
        "p_rel_or_p_obs_reliability": "Use C_e mechanism evidence only; p_rel/p_obs are disabled in this run.",
        "source_reranking_recall_tradeoff": "Use mechanism-table wording; source reranking requires a separate VL-SAT/Open3DSG experiment.",
        "official_test_result": "Use official validation only; official test remains untouched.",
    }
    return replacements.get(claim, "")


def write_report(path: Path, summary: dict[str, Any], table_roles: list[dict[str, Any]], allowed: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> None:
    primary = [row["route_family"] for row in table_roles if row["paper_success_role"] == "primary"]
    conditional = [row["route_family"] for row in table_roles if row["paper_success_role"] == "conditional"]
    diagnostic = [row["route_family"] for row in table_roles if row["paper_success_role"] == "diagnostic"]
    lines = [
        "# H002 Official Metric Claim Boundary Lock After Result Review",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {summary['output_artifacts']['artifact_root']}",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Locked Paper Role",
        "",
        f"- primary mechanism rows: {', '.join(primary)}",
        f"- caveated mechanism rows: {', '.join(conditional)}",
        f"- diagnostic rows: {', '.join(diagnostic)}",
        "- final paper result promotion: not yet; bounded paper-table draft is allowed.",
        "",
        "## Family Table Role",
        "",
        "| Family | Role | Include In Primary Macro | Caveat | M4 AUROC |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for row in table_roles:
        lines.append(
            "| {route_family} | {locked_table_role} | {include_in_primary_macro} | {must_report_caveat} | {m4_auroc} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Allowed Claims",
            "",
        ]
    )
    for row in allowed:
        lines.append(f"- `{row['claim_id']}`: {row['allowed_wording']} Qualifier: {row['required_qualifier']}")
    lines.extend(["", "## Blocked Claims", ""])
    for row in blocked:
        lines.append(f"- `{row['blocked_claim']}`: {row['reason']} Replacement: {row['replacement_wording']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The official validation C_e result can now be used to draft a bounded mechanism table.",
            "It must not be presented as final paper promotion, official test performance, source reranking,",
            "or all-relation 3DSSG improvement.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    review_dir = args.review_dir
    eval_dir = args.eval_dir
    output_dir = args.output_dir

    review_summary = read_json(review_dir / "summary.json")
    eval_manifest = read_json(eval_dir / "eval_manifest.json")
    family_decisions = read_csv(review_dir / "family_claim_decisions.csv")
    paper_gate = read_csv(review_dir / "paper_level_gate.csv")
    previous_blocked = read_csv(review_dir / "blocked_claims.csv")
    validation_errors = validate_inputs(review_summary, eval_manifest, review_dir, family_decisions, paper_gate, previous_blocked)

    table_roles = locked_table_roles(family_decisions)
    allowed = allowed_claim_rows()
    blocked = locked_blocked_claim_rows(previous_blocked)

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked_fix_inputs_before_claim_lock",
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO if not validation_errors else EXPECTED_REVIEW_NEXT,
        "input_artifacts": {
            "review_summary": rel_path(review_dir / "summary.json"),
            "family_claim_decisions": rel_path(review_dir / "family_claim_decisions.csv"),
            "paper_level_gate": rel_path(review_dir / "paper_level_gate.csv"),
            "blocked_claims": rel_path(review_dir / "blocked_claims.csv"),
            "eval_manifest": rel_path(eval_dir / "eval_manifest.json"),
        },
        "decision": {
            "claim_boundary_locked": not validation_errors,
            "paper_table_draft_allowed": not validation_errors,
            "final_paper_result_promotion": "not_yet",
            "primary_mechanism_families": ["relative_vertical", "size_relative"],
            "caveated_mechanism_families": ["relative_horizontal"],
            "diagnostic_families": ["support_contact"],
            "main_success_macro_policy": "primary_families_only_or_report_macro_plus_caveated_separately",
        },
        "boundary": {
            "official_validation_only": True,
            "official_test_usage": False,
            "source_reranking_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "all_relation_generalization_enabled": False,
            "support_contact_solved_claim_enabled": False,
            "relative_horizontal_frame_invariant_claim_enabled": False,
        },
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "table_role_lock": rel_path(output_dir / "table_role_lock.csv"),
            "allowed_claims": rel_path(output_dir / "allowed_claims.csv"),
            "blocked_claims_locked": rel_path(output_dir / "blocked_claims_locked.csv"),
            "paper_wording_contract": rel_path(output_dir / "paper_wording_contract.md"),
            "report": rel_path(output_dir / "report.md"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(output_dir / "table_role_lock.csv", table_roles)
    write_csv(output_dir / "allowed_claims.csv", allowed)
    write_csv(output_dir / "blocked_claims_locked.csv", blocked)
    write_report(output_dir / "paper_wording_contract.md", summary, table_roles, allowed, blocked)
    write_report(output_dir / "report.md", summary, table_roles, allowed, blocked)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
