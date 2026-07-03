#!/usr/bin/env python3
"""Lock final H002 scope after freezing support/contact as diagnostic."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PATH_DECISION_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_support_contact_harder_route_path_decision_after_result_review"
)
DEFAULT_OFFICIAL_BOUNDARY_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review"
)
DEFAULT_OUTPUT_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze"
)

EXPECTED_PATH_STATUS = "h002_support_contact_harder_route_path_decision_after_result_review_freeze_diagnostic"
EXPECTED_PATH_NEXT = "compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze"
EXPECTED_OFFICIAL_STATUS = "h002_compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review_locked"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze_v1"
STATUS_READY = "h002_compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze_input_errors"
SELECTED_PATH = "final_scope_locked_clean_Ce_routes_support_contact_diagnostic"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
    parser.add_argument("--official-boundary-dir", type=Path, default=DEFAULT_OFFICIAL_BOUNDARY_DIR)
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
        fields = ["empty"]
        rows = [{"empty": ""}]
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


def row_by_key(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def validate_inputs(
    path_summary: dict[str, Any],
    official_summary: dict[str, Any],
    path_dir: Path,
    official_dir: Path,
    path_scope_rows: list[dict[str, str]],
    table_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_summary.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_status", "actual": path_summary.get("status")})
    if path_summary.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_next_todo", "actual": path_summary.get("next_todo")})
    if path_summary.get("validation_errors") != 0:
        errors.append({"error_type": "path_decision_validation_errors", "actual": path_summary.get("validation_errors")})
    if line_count(path_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "path_decision_validation_error_file_not_empty"})

    decision = path_summary.get("decision", {})
    if decision.get("support_contact_solved_claim_allowed") is not False:
        errors.append({"error_type": "support_contact_solved_not_blocked"})
    if decision.get("keep_clean_Ce_routes") is not True:
        errors.append({"error_type": "clean_Ce_routes_not_kept"})
    if decision.get("official_test_usage") is not False:
        errors.append({"error_type": "official_test_unexpectedly_used"})

    support_scope = row_by_key(path_scope_rows, "route_family", "support_contact")
    if support_scope.get("status") != "freeze":
        errors.append({"error_type": "support_contact_not_frozen", "actual": support_scope})

    if official_summary.get("status") != EXPECTED_OFFICIAL_STATUS:
        errors.append({"error_type": "unexpected_official_boundary_status", "actual": official_summary.get("status")})
    if official_summary.get("validation_errors") != 0:
        errors.append({"error_type": "official_boundary_validation_errors", "actual": official_summary.get("validation_errors")})

    boundary = official_summary.get("boundary", {})
    required_false = [
        "official_test_usage",
        "source_reranking_claim_enabled",
        "p_obs_claim_enabled",
        "p_rel_claim_enabled",
        "support_contact_solved_claim_enabled",
        "all_relation_generalization_enabled",
    ]
    for key in required_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_flag_not_false", "key": key, "actual": boundary.get(key)})

    table_support = row_by_key(table_rows, "route_family", "support_contact")
    if table_support.get("locked_table_role") != "diagnostic_failure_taxonomy_row":
        errors.append({"error_type": "official_table_support_contact_not_diagnostic", "actual": table_support})
    return errors


def route_scope_rows() -> list[dict[str, Any]]:
    return [
        {
            "route_family": "relative_vertical",
            "relation_types": "higher than; lower than",
            "final_role": "primary_clean_Ce_mechanism",
            "paper_position": "main mechanism evidence",
            "metric_role": "family-wise AUROC/control primary",
            "claim_boundary": "predicate-conditioned vertical-order compatibility only",
        },
        {
            "route_family": "size_relative",
            "relation_types": "bigger than; smaller than",
            "final_role": "primary_clean_Ce_mechanism",
            "paper_position": "main mechanism evidence",
            "metric_role": "family-wise AUROC/control primary",
            "claim_boundary": "predicate-conditioned size-comparison compatibility only",
        },
        {
            "route_family": "relative_horizontal",
            "relation_types": "left; right; front; behind",
            "final_role": "caveated_frame_aware_Ce_mechanism",
            "paper_position": "caveated mechanism evidence",
            "metric_role": "reported separately or macro with caveat",
            "claim_boundary": "frame-aware compatibility; no frame-invariant spatial-reference claim",
        },
        {
            "route_family": "proximity",
            "relation_types": "close by",
            "final_role": "geometry_only_route_control",
            "paper_position": "control/diagnostic",
            "metric_role": "geometry-only route evidence; not T_e x G_e interaction",
            "claim_boundary": "some relations are geometry-decidable without fixed universal fusion",
        },
        {
            "route_family": "support_contact",
            "relation_types": "standing on; lying on; supported by",
            "final_role": "diagnostic_failure_taxonomy",
            "paper_position": "failure analysis / future redesign motivation",
            "metric_role": "diagnostic only",
            "claim_boundary": "not solved; current target/feature contract does not transfer",
        },
        {
            "route_family": "attachment_observability",
            "relation_types": "attached to; hanging on; connected to",
            "final_role": "future_observability_route",
            "paper_position": "future/deferred",
            "metric_role": "no main metric",
            "claim_boundary": "requires explicit visual/mesh observability labels before p_obs/p_rel claims",
        },
        {
            "route_family": "containment_occlusion_identity_structural",
            "relation_types": "inside; standing in; lying in; hanging in; cover; leaning against; same as; same symmetry as; part of; belonging to",
            "final_role": "future_route_taxonomy",
            "paper_position": "future/deferred",
            "metric_role": "no main metric",
            "claim_boundary": "requires route-specific target definitions, not current unified C_e claim",
        },
    ]


def allowed_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "A01_factorized_evidence_contract",
            "status": "allowed",
            "wording": "H002 separates semantic content T_e, source confidence Z_e, predicate-independent geometry evidence G_e, compatibility C_e, and evidence quality Q_e.",
            "required_qualifier": "current official validation metric evaluates C_e only; Z_e/Q_e/p_obs/p_rel are not promoted",
        },
        {
            "claim_id": "A02_clean_Ce_mechanism",
            "status": "allowed",
            "wording": "For signed comparison routes, C_e = compatibility(T_e, G_e) outperforms semantic-only, geometry-only, and simple concatenation under controls.",
            "required_qualifier": "restricted to relative_vertical and size_relative",
        },
        {
            "claim_id": "A03_horizontal_caveated",
            "status": "allowed_with_caveat",
            "wording": "Relative horizontal relations provide frame-aware compatibility evidence.",
            "required_qualifier": "not a frame-invariant spatial-reference solution",
        },
        {
            "claim_id": "A04_relation_aware_routing",
            "status": "allowed",
            "wording": "Different relation families require different evidence routes: clean compatibility, geometry-only control, observability-aware abstention, or diagnostic/future route.",
            "required_qualifier": "do not claim all relation types are solved",
        },
        {
            "claim_id": "A05_violation_at_k_role",
            "status": "allowed_as_downstream_metric_only",
            "wording": "Violation@K can be reused only after a source-reranking protocol is opened.",
            "required_qualifier": "not the primary metric for current C_e mechanism validation",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_claim": "support_contact_solved",
            "reason": "support/contact hard route is inverted on official validation and frozen as diagnostic",
        },
        {
            "blocked_claim": "all_relation_generalization",
            "reason": "attachment, containment, identity, and semantic/structural routes remain deferred",
        },
        {
            "blocked_claim": "source_reranking_result",
            "reason": "no source-reranking protocol has been run after final scope lock",
        },
        {
            "blocked_claim": "Violation@K_primary_Ce_metric",
            "reason": "Violation@K evaluates downstream top-K graph selection, not C_e mechanism validity",
        },
        {
            "blocked_claim": "p_obs_p_rel_reliability",
            "reason": "independent observability/reliability labels are not locked for current official metric",
        },
        {
            "blocked_claim": "official_test_result",
            "reason": "official test remains unused",
        },
        {
            "blocked_claim": "posthoc_support_contact_flip",
            "reason": "flipping scores after observing validation inversion would invalidate the protocol",
        },
    ]


def metric_role_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric": "family-wise AUROC / macro-family AUROC",
            "role": "primary_current",
            "used_for": "C_e mechanism validation",
            "status": "enabled",
        },
        {
            "metric": "wrong-T / shuffled-G / endpoint-swap / sign-flip controls",
            "role": "primary_current",
            "used_for": "shortcut and compatibility sanity checks",
            "status": "enabled",
        },
        {
            "metric": "balanced accuracy / AUPRC",
            "role": "secondary_current",
            "used_for": "family-level decision support",
            "status": "enabled_if_available",
        },
        {
            "metric": "Recall@K",
            "role": "downstream_future",
            "used_for": "source candidate reranking after final scope lock",
            "status": "deferred",
        },
        {
            "metric": "Violation@K",
            "role": "downstream_future",
            "used_for": "geometry inconsistency of top-K graph selection after reranking",
            "status": "deferred_not_primary_Ce_metric",
        },
        {
            "metric": "risk-coverage / abstain quality",
            "role": "future_p_obs",
            "used_for": "selective decision after independent observability labels",
            "status": "deferred",
        },
    ]


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    path_summary = read_json(args.path_decision_dir / "summary.json")
    official_summary = read_json(args.official_boundary_dir / "summary.json")
    path_scope = read_csv(args.path_decision_dir / "locked_scope.csv")
    table_rows = read_csv(args.official_boundary_dir / "table_role_lock.csv")

    errors = validate_inputs(
        path_summary,
        official_summary,
        args.path_decision_dir,
        args.official_boundary_dir,
        path_scope,
        table_rows,
    )

    route_scope = route_scope_rows()
    allowed_claims = allowed_claim_rows()
    blocked_claims = blocked_claim_rows()
    metric_roles = metric_role_rows()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "validation_errors": len(errors),
        "selected_path": SELECTED_PATH if not errors else "blocked_fix_final_scope_inputs",
        "next_todo": NEXT_TODO if not errors else "fix_final_h002_scope_lock_inputs",
        "input_artifacts": {
            "path_decision_summary": rel_path(args.path_decision_dir / "summary.json"),
            "path_decision_locked_scope": rel_path(args.path_decision_dir / "locked_scope.csv"),
            "path_decision_blocked_claims": rel_path(args.path_decision_dir / "blocked_claims.csv"),
            "official_boundary_summary": rel_path(args.official_boundary_dir / "summary.json"),
            "official_table_role_lock": rel_path(args.official_boundary_dir / "table_role_lock.csv"),
        },
        "decision": {
            "final_scope_locked": not bool(errors),
            "paper_metric_promoted": False,
            "official_validation_only": True,
            "official_test_usage": False,
            "source_reranking_deferred_until_protocol": True,
            "violation_at_k_primary_metric": False,
            "violation_at_k_downstream_metric": True,
            "p_obs_p_rel_deferred": True,
            "support_contact_frozen_diagnostic": True,
        },
        "final_scope": {
            "primary_clean_Ce_families": ["relative_vertical", "size_relative"],
            "caveated_Ce_families": ["relative_horizontal"],
            "geometry_only_control_families": ["proximity"],
            "diagnostic_failure_families": ["support_contact"],
            "future_deferred_families": [
                "attachment_observability",
                "containment_occlusion_identity_structural",
            ],
        },
        "metric_contract": {
            "primary_current": [
                "family-wise AUROC",
                "macro-family AUROC",
                "wrong-T controls",
                "shuffled-G controls",
                "endpoint/sign controls where applicable",
            ],
            "downstream_future": ["Recall@K", "Violation@K"],
            "deferred": ["p_obs/p_rel calibration", "risk-coverage", "official test"],
        },
        "output_artifacts": {
            "summary": rel_path(out_dir / "summary.json"),
            "validation_errors": rel_path(out_dir / "validation_errors.jsonl"),
            "route_scope_lock": rel_path(out_dir / "route_scope_lock.csv"),
            "allowed_claims_final": rel_path(out_dir / "allowed_claims_final.csv"),
            "blocked_claims_final": rel_path(out_dir / "blocked_claims_final.csv"),
            "metric_role_lock": rel_path(out_dir / "metric_role_lock.csv"),
            "next_contract": rel_path(out_dir / "next_contract.json"),
            "report": rel_path(out_dir / "report.md"),
        },
    }

    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_source_reranking_protocol_plan" if not errors else "blocked",
        "next_todo": summary["next_todo"],
        "next_task": "define a source-reranking protocol using only the locked H002 scope",
        "source_reranking_constraints": [
            "do not include support_contact as a solved route",
            "do not use official test before protocol freeze",
            "treat Recall@K and Violation@K as downstream metrics",
            "keep C_e metric evidence separate from source-score Z_e",
            "report family-wise metrics before aggregate metrics",
        ],
    }

    report_lines = [
        "# Final H002 Scope Lock After Support/Contact Freeze",
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
        "## Result",
        "",
        "The final H002 scope is locked as route-specific C_e mechanism evidence.",
        "Support/contact is frozen as diagnostic/failure taxonomy, not a success row.",
        "",
        "Primary current metrics remain family-wise C_e metrics and controls.",
        "Recall@K and Violation@K are deferred to downstream source-reranking evaluation.",
        "",
        "## Final Scope",
        "",
    ]
    for row in route_scope:
        report_lines.append(f"- {row['route_family']}: {row['final_role']} ({row['relation_types']})")
    report_lines.extend(
        [
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
        ]
    )

    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "next_contract.json", next_contract)
    write_jsonl(out_dir / "validation_errors.jsonl", errors)
    write_csv(out_dir / "route_scope_lock.csv", route_scope)
    write_csv(out_dir / "allowed_claims_final.csv", allowed_claims)
    write_csv(out_dir / "blocked_claims_final.csv", blocked_claims)
    write_csv(out_dir / "metric_role_lock.csv", metric_roles)
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return summary


def main() -> None:
    summary = run(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
