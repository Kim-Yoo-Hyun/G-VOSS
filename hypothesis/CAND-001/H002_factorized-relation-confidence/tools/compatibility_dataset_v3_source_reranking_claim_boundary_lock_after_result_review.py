#!/usr/bin/env python3
"""Lock H002 source-reranking claim boundaries after result review."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_metric_result_review_after_runner"
DEFAULT_RUNTIME_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review"

EXPECTED_REVIEW_STATUS = "h002_source_reranking_metric_result_review_after_runner_ready"
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review"
EXPECTED_RUNTIME_STATUS = "h002_source_reranking_metric_runner_ready"

SCHEMA_VERSION = "h002_source_reranking_claim_boundary_lock_after_result_review_v1"
STATUS_READY = "h002_source_reranking_claim_boundary_lock_after_result_review_locked"
STATUS_ERRORS = "h002_source_reranking_claim_boundary_lock_after_result_review_input_errors"
SELECTED_PATH = "source_reranking_claim_boundary_locked_select_validation_table_skeleton"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR)
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


def validate_inputs(
    review_summary: dict[str, Any],
    runtime_manifest: dict[str, Any],
    review_dir: Path,
    recommendation_rows: list[dict[str, str]],
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
    if runtime_manifest.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": runtime_manifest.get("status")})
    if runtime_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_validation_errors", "actual": runtime_manifest.get("validation_errors")})

    decision = review_summary.get("decision", {})
    required_decision = {
        "source_reranking_validation_evidence": "positive",
        "paper_promotion": "not_yet",
        "official_test_usage": False,
        "claim_boundary_lock_required_next": True,
        "weighted_S2_vs_S0_recall_nonnegative_all_K": True,
        "weighted_S2_vs_S0_violation_nonpositive_all_K": True,
        "weighted_S2_vs_shuffled_recall_positive_all_K": True,
        "weighted_S2_vs_wrong_T_recall_positive_all_K": True,
        "weighted_S2_vs_wrong_T_violation_nonpositive_all_K": True,
    }
    for key, expected in required_decision.items():
        if decision.get(key) != expected:
            errors.append({"error_type": "unexpected_review_decision", "key": key, "actual": decision.get(key), "expected": expected})
    if decision.get("negative_recall_cells") != 3:
        errors.append({"error_type": "unexpected_negative_recall_cells", "actual": decision.get("negative_recall_cells"), "expected": 3})
    if decision.get("violation_nonimprove_cells") != 0:
        errors.append({"error_type": "unexpected_violation_nonimprove_cells", "actual": decision.get("violation_nonimprove_cells"), "expected": 0})

    boundary = runtime_manifest.get("boundary", {})
    required_boundary = {
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "paper_metric_promoted": False,
        "source_reranking_metric_produced": True,
        "C_e_excludes_Z_e": True,
        "Z_e_combined_only_after_C_e": True,
        "post_hoc_lambda_tuning": False,
        "p_obs_claim_enabled": False,
        "p_rel_claim_enabled": False,
    }
    for key, expected in required_boundary.items():
        if boundary.get(key) != expected:
            errors.append({"error_type": "unexpected_runtime_boundary", "key": key, "actual": boundary.get(key), "expected": expected})

    recommendation_status = {row.get("claim"): row.get("status") for row in recommendation_rows}
    expected_recommendations = {
        "S2 source-score times C_e improves primary validation recall/violation tradeoff over source-only ranking": "allowed_with_validation_boundary",
        "C_e alone is the deployable ranking score": "blocked",
        "S2 improves every source/family/K cell": "blocked",
        "This is an official test result or final paper promotion": "blocked",
        "support_contact is solved": "blocked",
        "p_obs/p_rel reliability posterior is validated": "blocked",
    }
    for claim, expected in expected_recommendations.items():
        if recommendation_status.get(claim) != expected:
            errors.append({"error_type": "unexpected_recommendation", "claim": claim, "actual": recommendation_status.get(claim), "expected": expected})
    return errors


def locked_table_roles() -> list[dict[str, Any]]:
    return [
        {
            "result_block": "source_reranking_validation_tradeoff",
            "locked_role": "secondary_validation_table_candidate",
            "paper_position": "method_deployability_evidence_after_C_e_mechanism_table",
            "main_text_allowed": "conditional_yes_if_labeled_validation_only",
            "appendix_allowed": "yes",
            "final_test_table_allowed": "no",
            "primary_score": "S2_source_x_Ce",
            "baseline": "S0_source_score",
            "families": "relative_vertical; size_relative",
            "required_caveat": "3/20 source-family-K cells have small Recall@K regressions; violation improves in all reviewed cells",
        },
        {
            "result_block": "controls",
            "locked_role": "supporting_control_rows",
            "paper_position": "same_table_or_adjacent_control_table",
            "main_text_allowed": "yes_as_control_evidence",
            "appendix_allowed": "yes",
            "final_test_table_allowed": "no",
            "primary_score": "S2_source_x_Ce",
            "baseline": "source_x_shuffled_Ce; source_x_wrong_T_Ce",
            "families": "relative_vertical; size_relative",
            "required_caveat": "controls validate compatibility sensitivity, not final relation predictor SOTA",
        },
        {
            "result_block": "C_e_only",
            "locked_role": "diagnostic_negative_control",
            "paper_position": "appendix_or_short_ablation_note",
            "main_text_allowed": "only_to_explain_why_Z_e_and_C_e_are_separated",
            "appendix_allowed": "yes",
            "final_test_table_allowed": "no",
            "primary_score": "S1_Ce_only",
            "baseline": "S0_source_score",
            "families": "relative_vertical; size_relative",
            "required_caveat": "C_e alone is not deployable for low-K source ranking",
        },
    ]


def allowed_claims() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "SRC01_validation_tradeoff",
            "status": "allowed_with_validation_boundary",
            "allowed_wording": "On official validation source candidates, combining source confidence with predicate-geometry compatibility improves the primary recall-violation tradeoff over source-only ranking for clean comparison families.",
            "required_qualifier": "validation-only; primary clean families only; not official test; not uniform across every source-family-K cell",
        },
        {
            "claim_id": "SRC02_factor_separation",
            "status": "allowed",
            "allowed_wording": "C_e is computed from T_e and G_e without source confidence Z_e, and Z_e is combined only at the reranking stage.",
            "required_qualifier": "This supports factor separation; it does not validate p_obs or p_rel.",
        },
        {
            "claim_id": "SRC03_control_sensitivity",
            "status": "allowed",
            "allowed_wording": "Shuffled-C_e and wrong-T controls underperform the correct S2 score, indicating that predicate-geometry compatibility affects source ranking.",
            "required_qualifier": "Control evidence is validation-level and limited to the frozen source-reranking protocol.",
        },
        {
            "claim_id": "SRC04_Ce_only_limitation",
            "status": "allowed_as_negative_ablation",
            "allowed_wording": "C_e alone is insufficient as a deployable source-ranking score at low K, so the deployable hypothesis uses separated source confidence plus compatibility.",
            "required_qualifier": "Do not present C_e-only ranking as the proposed deployment score.",
        },
    ]


def blocked_claims() -> list[dict[str, Any]]:
    return [
        {
            "blocked_claim": "official_test_or_final_result",
            "lock_status": "hard_block",
            "reason": "Only official validation source candidates were evaluated; official test remains unused.",
            "replacement_wording": "Use validation-level source-reranking evidence.",
        },
        {
            "blocked_claim": "uniform_source_family_improvement",
            "lock_status": "hard_block",
            "reason": "3/20 source-family-K cells have small Recall@K regressions.",
            "replacement_wording": "Use primary weighted tradeoff improvement with explicit caveat.",
        },
        {
            "blocked_claim": "C_e_alone_deployable_score",
            "lock_status": "hard_block",
            "reason": "S1_Ce_only has poor low-K recall and is only diagnostic.",
            "replacement_wording": "Use S2_source_x_Ce as the deployable validation score candidate.",
        },
        {
            "blocked_claim": "support_contact_solved",
            "lock_status": "hard_block",
            "reason": "support_contact is excluded from success aggregation and remains diagnostic.",
            "replacement_wording": "Keep support_contact as failure-taxonomy/challenging-route evidence.",
        },
        {
            "blocked_claim": "p_obs_p_rel_validated",
            "lock_status": "hard_block",
            "reason": "This source-reranking metric evaluates C_e-based reranking, not two-head observability/reliability.",
            "replacement_wording": "Discuss p_obs/p_rel as framework design or future evaluation only.",
        },
        {
            "blocked_claim": "SOTA_or_full_3DSSG_improvement",
            "lock_status": "hard_block",
            "reason": "The protocol is a selected-family validation source-reranking study, not a full benchmark or SOTA comparison.",
            "replacement_wording": "Use selected-route source-reranking validation evidence.",
        },
        {
            "blocked_claim": "post_hoc_tuned_reranking",
            "lock_status": "hard_block",
            "reason": "The frozen protocol did not tune lambda or thresholds on official validation.",
            "replacement_wording": "Use the frozen S2_source_x_Ce score contract only.",
        },
    ]


def write_markdown_contract(path: Path, summary: dict[str, Any], table_roles: list[dict[str, Any]], allowed: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> None:
    lines = [
        "# H002 Source Reranking Claim Boundary Lock",
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
        "## Locked Role",
        "",
        "- Source-reranking evidence is locked as validation-level deployability evidence.",
        "- It can be drafted as a secondary validation table candidate or appendix table.",
        "- It is not a final official-test result and not a SOTA/full 3DSSG improvement claim.",
        "- The proposed deployable score is `S2_source_x_Ce`, not `C_e` alone.",
        "",
        "## Table Role Lock",
        "",
        "| Result Block | Locked Role | Main Text | Appendix | Final Test Table | Caveat |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in table_roles:
        lines.append(
            f"| `{row['result_block']}` | `{row['locked_role']}` | {row['main_text_allowed']} | "
            f"{row['appendix_allowed']} | {row['final_test_table_allowed']} | {row['required_caveat']} |"
        )
    lines.extend(["", "## Allowed Wording", ""])
    for row in allowed:
        lines.append(f"- `{row['claim_id']}`: {row['allowed_wording']} Qualifier: {row['required_qualifier']}")
    lines.extend(["", "## Blocked Wording", ""])
    for row in blocked:
        lines.append(f"- `{row['blocked_claim']}`: {row['reason']} Replacement: {row['replacement_wording']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The source-reranking result can be used as bounded validation evidence that separated",
            "`Z_e` and `C_e` improve the recall/violation tradeoff over source-only ranking on clean",
            "comparison families. It must not be promoted as official test evidence, uniform",
            "source-family improvement, or a final paper result before the next table skeleton and",
            "paper-position review.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    review_summary = read_json(args.review_dir / "summary.json")
    runtime_manifest = read_json(args.runtime_dir / "metric_manifest.json")
    recommendation_rows = read_csv(args.review_dir / "claim_boundary_recommendation.csv")
    errors = validate_inputs(review_summary, runtime_manifest, args.review_dir, recommendation_rows)

    status = STATUS_ERRORS if errors else STATUS_READY
    table_roles = locked_table_roles()
    allowed = allowed_claims()
    blocked = blocked_claims()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "source_reranking_claim_boundary_lock_blocked_by_input_errors",
        "validation_errors": len(errors),
        "input_artifacts": {
            "review_summary": rel_path(args.review_dir / "summary.json"),
            "review_recommendation": rel_path(args.review_dir / "claim_boundary_recommendation.csv"),
            "source_family_caveats": rel_path(args.review_dir / "source_family_caveats.json"),
            "runtime_manifest": rel_path(args.runtime_dir / "metric_manifest.json"),
        },
        "decision": {
            "source_reranking_claim_boundary_locked": not errors,
            "source_reranking_table_role": "secondary_validation_table_candidate_or_appendix",
            "main_text_allowed": "conditional_validation_only",
            "appendix_allowed": True,
            "final_paper_result_promotion": "not_yet",
            "official_test_usage": False,
            "primary_score": "S2_source_x_Ce",
            "baseline": "S0_source_score",
            "primary_success_families": ["relative_vertical", "size_relative"],
            "blocked_uniform_improvement": True,
            "negative_recall_cells": review_summary.get("decision", {}).get("negative_recall_cells"),
            "violation_nonimprove_cells": review_summary.get("decision", {}).get("violation_nonimprove_cells"),
        },
        "boundary": {
            "official_validation_only": True,
            "official_test_usage": False,
            "S2_source_x_Ce_claim_enabled": not errors,
            "C_e_alone_deployable_claim_enabled": False,
            "uniform_improvement_claim_enabled": False,
            "support_contact_solved_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "SOTA_or_full_3DSSG_claim_enabled": False,
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "table_role_lock": rel_path(args.output_dir / "table_role_lock.csv"),
            "allowed_claims": rel_path(args.output_dir / "allowed_claims.csv"),
            "blocked_claims_locked": rel_path(args.output_dir / "blocked_claims_locked.csv"),
            "paper_wording_contract": rel_path(args.output_dir / "paper_wording_contract.md"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "next_todo": NEXT_TODO if not errors else EXPECTED_REVIEW_NEXT,
    }

    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "table_role_lock.csv", table_roles)
    write_csv(args.output_dir / "allowed_claims.csv", allowed)
    write_csv(args.output_dir / "blocked_claims_locked.csv", blocked)
    write_markdown_contract(args.output_dir / "paper_wording_contract.md", summary, table_roles, allowed, blocked)
    write_markdown_contract(args.output_dir / "report.md", summary, table_roles, allowed, blocked)

    print(json.dumps({"status": status, "validation_errors": len(errors), "next_todo": summary["next_todo"]}, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
