#!/usr/bin/env python3
"""Decide H002 path after support/contact hard-route metric result review."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner"
)
DEFAULT_OUTPUT_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_support_contact_harder_route_path_decision_after_result_review"
)

EXPECTED_REVIEW_STATUS = "h002_support_contact_harder_route_metric_result_review_after_runner_ready"
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_support_contact_harder_route_path_decision_after_result_review"

SCHEMA_VERSION = "h002_support_contact_harder_route_path_decision_after_result_review_v1"
STATUS_READY = "h002_support_contact_harder_route_path_decision_after_result_review_freeze_diagnostic"
STATUS_ERRORS = "h002_support_contact_harder_route_path_decision_after_result_review_input_errors"
SELECTED_PATH = "freeze_support_contact_harder_route_as_diagnostic_scope_h002_to_clean_routes"
NEXT_TODO = "compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
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
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
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


def row_by_key(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def validate_inputs(review_summary: dict[str, Any], review_dir: Path, gate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
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
    required_decisions = {
        "current_direction_wrong": False,
        "support_contact_harder_route_success": False,
        "support_contact_solved_claim_allowed": False,
        "paper_metric_promoted": False,
        "official_test_usage": False,
        "do_not_posthoc_flip_scores": True,
        "keep_h002_core_routes": True,
        "freeze_support_contact_harder_route_as_diagnostic": True,
        "requires_target_feature_contract_redesign_for_retry": True,
    }
    for key, expected in required_decisions.items():
        if decision.get(key) is not expected:
            errors.append({"error_type": "unexpected_review_decision", "key": key, "actual": decision.get(key), "expected": expected})

    required_failed_gates = [
        "official_M4_beats_geometry_only",
        "wrong_T_control_degrades",
        "paired_group_correct_T_preferred",
        "support_contact_paper_success",
    ]
    for gate in required_failed_gates:
        row = row_by_key(gate_rows, "gate", gate)
        if row.get("status") != "fail":
            errors.append({"error_type": "expected_gate_not_failed", "gate": gate, "actual": row.get("status")})
    return errors


def option_rows(review_summary: dict[str, Any]) -> list[dict[str, Any]]:
    findings = review_summary.get("primary_findings", {})
    m4 = findings.get("official_m4_auroc")
    wrong_t = findings.get("official_wrong_t_auroc")
    paired = findings.get("paired_m4_accuracy")
    paired_wrong = findings.get("paired_wrong_t_accuracy")
    return [
        {
            "option": "A_freeze_support_contact_as_diagnostic",
            "decision": "selected",
            "reason": "Official validation is inverted and support/contact cannot be claimed as solved.",
            "evidence": f"M4 AUROC={m4}; wrong-T AUROC={wrong_t}; paired M4={paired}; paired wrong-T={paired_wrong}",
            "next_action": NEXT_TODO,
        },
        {
            "option": "B_redesign_support_contact_target_feature_contract_now",
            "decision": "defer",
            "reason": "A retry would require a new target and feature contract, not a minor repair.",
            "evidence": "Feature drift and target-semantics mismatch are both high-severity root causes.",
            "next_action": "only_if_user_explicitly_reopens_support_contact_main_claim",
        },
        {
            "option": "C_posthoc_flip_scores",
            "decision": "reject",
            "reason": "AUC inversion is diagnostic evidence of convention mismatch; flipping after seeing validation would be invalid.",
            "evidence": "Wrong-T is the high-performing condition, so the learned direction is not trustworthy.",
            "next_action": "none",
        },
        {
            "option": "D_promote_support_contact_as_success",
            "decision": "reject",
            "reason": "All support/contact success gates failed.",
            "evidence": "M4 below random, below geometry-only, and below wrong-T.",
            "next_action": "none",
        },
        {
            "option": "E_run_source_reranking_or_official_test",
            "decision": "reject_for_now",
            "reason": "Source/test evaluation before path lock would propagate a known failed route.",
            "evidence": "Official validation hard-route result is not stable.",
            "next_action": "defer_until_final_scope_lock",
        },
    ]


def locked_scope_rows() -> list[dict[str, Any]]:
    return [
        {
            "route_family": "relative_vertical",
            "paper_role_after_decision": "main_clean_Ce_evidence",
            "status": "keep",
            "claim": "predicate-conditioned signed vertical-order compatibility",
            "caveat": "does not imply all support/contact or all relation reliability",
        },
        {
            "route_family": "size_relative",
            "paper_role_after_decision": "main_clean_Ce_evidence",
            "status": "keep",
            "claim": "predicate-conditioned signed size-comparison compatibility",
            "caveat": "clean comparison route; avoid overstating as universal reliability",
        },
        {
            "route_family": "relative_horizontal",
            "paper_role_after_decision": "caveated_frame_aware_evidence",
            "status": "keep_with_caveat",
            "claim": "frame-aware horizontal compatibility evidence",
            "caveat": "not frame-invariant and not a solved spatial-reference problem",
        },
        {
            "route_family": "support_contact",
            "paper_role_after_decision": "diagnostic_failure_taxonomy",
            "status": "freeze",
            "claim": "hard contact/pose route exposes current target/feature transfer failure",
            "caveat": "not a solved family and not included as success evidence",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_claim": "support_contact_solved",
            "reason": "official validation M4 is inverted and wrong-T control is stronger",
        },
        {
            "blocked_claim": "posthoc_score_flip",
            "reason": "would use validation failure to redefine the method after the fact",
        },
        {
            "blocked_claim": "all_relation_generalization",
            "reason": "hard route does not transfer and attachment/containment remain unresolved",
        },
        {
            "blocked_claim": "source_reranking_with_support_contact",
            "reason": "source reranking would inherit the failed support/contact route",
        },
        {
            "blocked_claim": "official_test_evaluation",
            "reason": "test must wait until final scope and method are frozen",
        },
        {
            "blocked_claim": "p_obs_p_rel_reliability",
            "reason": "current result only concerns C_e compatibility and has no reliable observability posterior",
        },
    ]


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    review_summary = read_json(args.review_dir / "summary.json")
    gate_rows = read_csv(args.review_dir / "gate_review.csv")
    root_causes = read_csv(args.review_dir / "root_cause_review.csv")
    errors = validate_inputs(review_summary, args.review_dir, gate_rows)

    options = option_rows(review_summary)
    locked_scope = locked_scope_rows()
    blocked_claims = blocked_claim_rows()

    findings = review_summary.get("primary_findings", {})
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "validation_errors": len(errors),
        "selected_path": SELECTED_PATH if not errors else "blocked_fix_path_decision_inputs",
        "next_todo": NEXT_TODO if not errors else "fix_support_contact_harder_route_path_decision_inputs",
        "input_artifacts": {
            "review_summary": rel_path(args.review_dir / "summary.json"),
            "gate_review": rel_path(args.review_dir / "gate_review.csv"),
            "root_cause_review": rel_path(args.review_dir / "root_cause_review.csv"),
        },
        "decision": {
            "selected_option": "freeze_support_contact_as_diagnostic",
            "current_direction_wrong": False,
            "support_contact_harder_route_success": False,
            "support_contact_solved_claim_allowed": False,
            "support_contact_paper_success_role": "none",
            "support_contact_diagnostic_role": "failure_taxonomy_and_future_redesign_motivation",
            "keep_clean_Ce_routes": True,
            "paper_metric_promoted": False,
            "official_test_usage": False,
            "source_reranking_deferred": True,
            "p_obs_p_rel_deferred": True,
        },
        "primary_evidence": {
            "official_m4_auroc": findings.get("official_m4_auroc"),
            "official_wrong_t_auroc": findings.get("official_wrong_t_auroc"),
            "paired_m4_accuracy": findings.get("paired_m4_accuracy"),
            "paired_wrong_t_accuracy": findings.get("paired_wrong_t_accuracy"),
        },
        "reasoning": {
            "why_freeze": (
                "The support/contact hard route fails all official validation success gates and is inverted under wrong-T control."
            ),
            "why_h002_not_rejected": (
                "The failure is route-specific; it shows support/contact needs a different target/feature contract, not that T_e/G_e/C_e factorization is invalid."
            ),
            "next_scope_action": (
                "Lock final H002 scope around clean C_e routes and keep support/contact as diagnostic unless a new support/contact contract is explicitly reopened."
            ),
        },
        "output_artifacts": {
            "summary": rel_path(out_dir / "summary.json"),
            "validation_errors": rel_path(out_dir / "validation_errors.jsonl"),
            "option_decision": rel_path(out_dir / "option_decision.csv"),
            "locked_scope": rel_path(out_dir / "locked_scope.csv"),
            "blocked_claims": rel_path(out_dir / "blocked_claims.csv"),
            "root_cause_snapshot": rel_path(out_dir / "root_cause_snapshot.csv"),
            "next_contract": rel_path(out_dir / "next_contract.json"),
            "report": rel_path(out_dir / "report.md"),
        },
    }

    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_final_h002_scope_lock" if not errors else "blocked",
        "next_todo": summary["next_todo"],
        "next_task": "finalize H002 scope after support/contact freeze",
        "must_include": [
            "clean C_e evidence families",
            "relative_horizontal caveat",
            "support_contact diagnostic/failure taxonomy",
            "blocked source/test/p_obs/p_rel claims",
        ],
        "must_not_do": [
            "posthoc flip support/contact scores",
            "promote support/contact as success",
            "run official test",
            "start source reranking before final scope lock",
        ],
    }

    report_lines = [
        "# Support/Contact Harder Route Path Decision After Result Review",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Purpose",
        "",
        "Decide whether to keep repairing support/contact after the official validation inversion, or freeze it as diagnostic evidence.",
        "",
        "## Result",
        "",
        "Selected path: freeze support/contact hard route as diagnostic/failure taxonomy.",
        "",
        f"- official M4 AUROC: `{findings.get('official_m4_auroc')}`",
        f"- official wrong-T AUROC: `{findings.get('official_wrong_t_auroc')}`",
        f"- paired M4 accuracy: `{findings.get('paired_m4_accuracy')}`",
        f"- paired wrong-T accuracy: `{findings.get('paired_wrong_t_accuracy')}`",
        "",
        "This is not a global rejection of H002. It is a route-specific failure showing that support/contact needs a new target/feature contract.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
    ]

    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "next_contract.json", next_contract)
    write_jsonl(out_dir / "validation_errors.jsonl", errors)
    write_csv(out_dir / "option_decision.csv", options)
    write_csv(out_dir / "locked_scope.csv", locked_scope)
    write_csv(out_dir / "blocked_claims.csv", blocked_claims)
    write_csv(out_dir / "root_cause_snapshot.csv", root_causes)
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return summary


def main() -> int:
    summary = run(parse_args())
    return 1 if summary["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
