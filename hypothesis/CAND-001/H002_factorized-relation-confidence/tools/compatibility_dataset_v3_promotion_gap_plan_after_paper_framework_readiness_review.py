#!/usr/bin/env python3
"""Convert H002 paper/framework readiness gaps into a promotion plan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_READINESS_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review"
)

EXPECTED_READINESS_STATUS = (
    "h002_compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes_ready"
)
EXPECTED_READINESS_NEXT = "compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review_input_errors"
)
SELECTED_PATH = "promotion_gap_plan_ready_select_docker_heldout_protocol_plan"
NEXT_TODO = "compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-dir", type=Path, default=DEFAULT_READINESS_DIR)
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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validation_count(summary: dict[str, Any]) -> int:
    for key in ("validation_errors", "validation_error_count"):
        if key in summary:
            return int(summary.get(key) or 0)
    return 0


def validate_inputs(
    summary: dict[str, Any],
    candidate_rows: list[dict[str, str]],
    diagnostic_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    blocked_rows: list[dict[str, str]],
    readiness_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_READINESS_STATUS:
        errors.append(
            {
                "error_type": "unexpected_readiness_status",
                "expected": EXPECTED_READINESS_STATUS,
                "actual": summary.get("status"),
            }
        )
    if summary.get("next_todo") != EXPECTED_READINESS_NEXT:
        errors.append(
            {
                "error_type": "unexpected_readiness_next_todo",
                "expected": EXPECTED_READINESS_NEXT,
                "actual": summary.get("next_todo"),
            }
        )
    if validation_count(summary) != 0:
        errors.append({"error_type": "readiness_validation_errors", "actual": validation_count(summary)})
    boundary = summary.get("boundary", {})
    if boundary.get("paper_level_ready") is not False:
        errors.append({"error_type": "readiness_already_paper_level_ready"})
    if boundary.get("framework_ready_hypothesis_stage") is not True:
        errors.append({"error_type": "framework_not_ready"})
    if boundary.get("validation_usage") is not False or boundary.get("test_usage") is not False:
        errors.append({"error_type": "validation_or_test_used_in_input"})

    validation_file = readiness_dir / "validation_errors.jsonl"
    if validation_file.exists() and validation_file.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "readiness_validation_error_rows_present"})

    if len(candidate_rows) != 4:
        errors.append({"error_type": "unexpected_candidate_main_rows", "actual": len(candidate_rows)})
    if len(diagnostic_rows) < 4:
        errors.append({"error_type": "too_few_diagnostic_rows", "actual": len(diagnostic_rows)})
    if len(gap_rows) != 5:
        errors.append({"error_type": "unexpected_gap_rows", "actual": len(gap_rows)})
    if len(blocked_rows) < 6:
        errors.append({"error_type": "too_few_blocked_claims", "actual": len(blocked_rows)})

    candidate_families = {row.get("family") for row in candidate_rows}
    required_families = {"relative_vertical", "size_relative", "relative_horizontal", "support_contact"}
    if candidate_families != required_families:
        errors.append(
            {
                "error_type": "candidate_family_set_mismatch",
                "expected": sorted(required_families),
                "actual": sorted(candidate_families),
            }
        )
    return errors


def promotion_roadmap() -> list[dict[str, Any]]:
    return [
        {
            "step": "P0",
            "name": "freeze_current_hypothesis_scope",
            "status": "complete",
            "purpose": "Lock the route-specific framework boundary before promotion.",
            "minimum_artifact": "readiness review summary and route tables",
            "pass_criterion": "candidate/diagnostic/blocked claim tables exist with validation_errors=0",
            "unlocks": "promotion planning only",
        },
        {
            "step": "P1",
            "name": "docker_heldout_protocol_plan",
            "status": "next",
            "purpose": "Define a reproducible Docker protocol and held-out grouped split before running paper experiments.",
            "minimum_artifact": "Docker/compose contract, mounted data paths, grouped split contract, output manifest",
            "pass_criterion": "no experiment root creation or metric claim until protocol is accepted",
            "unlocks": "P2 implementation",
        },
        {
            "step": "P2",
            "name": "route_specific_docker_reproduction",
            "status": "pending",
            "purpose": "Regenerate candidate main route rows and route metrics inside Docker.",
            "minimum_artifact": "container command logs, row manifests, route metric summaries",
            "pass_criterion": "same route definitions reproduced; no host-only dependency",
            "unlocks": "paper-result eligibility for reproduced rows",
        },
        {
            "step": "P3",
            "name": "heldout_grouped_evaluation",
            "status": "pending",
            "purpose": "Test whether route-specific signals survive scan/endpoint-pair grouped splits.",
            "minimum_artifact": "train/dev/test or train/dev protocol, group leakage audit, per-family metrics",
            "pass_criterion": "no scan or endpoint-pair leakage; controls still collapse on held-out groups",
            "unlocks": "scoped generalization claim",
        },
        {
            "step": "P4",
            "name": "calibration_selective_decision",
            "status": "pending",
            "purpose": "Convert C_e mechanism scores into calibrated p_rel and p_obs only if evidence supports it.",
            "minimum_artifact": "ECE, Brier, NLL, selective-risk/coverage, abstention curves",
            "pass_criterion": "calibrated heads improve over uncalibrated route score and maintain controls",
            "unlocks": "calibrated reliability / abstention claim",
        },
        {
            "step": "P5",
            "name": "target_independence_replication",
            "status": "pending",
            "purpose": "Replicate shortcut and construction-leakage audits for promoted rows.",
            "minimum_artifact": "class-pair, source/rank, endpoint, wrong-T, shuffled-G, and hidden-field audits",
            "pass_criterion": "no allowed shortcut solves the target; counterfactual controls behave as expected",
            "unlocks": "reviewer defense against constructed target shortcut",
        },
        {
            "step": "P6",
            "name": "paper_claim_wording_lock",
            "status": "pending",
            "purpose": "Lock exact wording of allowed and blocked claims before manuscript drafting.",
            "minimum_artifact": "claim unlock table, paper table plan, diagnostic boundary table",
            "pass_criterion": "no all-family, full reliability, or R7 learned claim unless corresponding gates pass",
            "unlocks": "paper outline/table drafting",
        },
    ]


def route_gate_matrix(
    candidate_rows: list[dict[str, str]], diagnostic_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    priority = {
        "relative_vertical": "A_minimal",
        "size_relative": "A_minimal",
        "relative_horizontal": "B_reference_frame",
        "support_contact": "B_challenging",
    }
    for row in candidate_rows:
        family = row["family"]
        rows.append(
            {
                "family": family,
                "predicates": row.get("predicates", ""),
                "promotion_role": "candidate_main_mechanism",
                "priority": priority.get(family, "B"),
                "required_gates": "P1,P2,P3,P5,P6",
                "calibration_gate": "P4 required only for p_rel/p_obs claim",
                "minimum_success_definition": (
                    "route interaction beats T-only/G-only/plain-concat and wrong-T/shuffled-G controls collapse "
                    "under grouped held-out evaluation"
                ),
                "paper_claim_if_pass": "scoped route-specific compatibility mechanism evidence",
                "paper_claim_if_fail": "diagnostic route boundary; do not discard taxonomy",
            }
        )
    for row in diagnostic_rows:
        rows.append(
            {
                "family": row.get("family", ""),
                "predicates": row.get("predicates", ""),
                "promotion_role": row.get("diagnostic_role", ""),
                "priority": "diagnostic_or_future",
                "required_gates": "not promoted in current path",
                "calibration_gate": "not applicable until new target exists",
                "minimum_success_definition": row.get("next_if_reopened", ""),
                "paper_claim_if_pass": "future route or appendix diagnostic only",
                "paper_claim_if_fail": "keep as boundary evidence for relation-aware routing",
            }
        )
    return rows


def docker_contract() -> list[dict[str, Any]]:
    return [
        {
            "item": "experiment_root",
            "contract": "Do not create the root in this planning step; proposed root should be under experiments/H002_compatibility_routing/ only after user confirmation.",
            "required": "yes_before_paper_result",
        },
        {
            "item": "container_entrypoint",
            "contract": "One command must regenerate row materialization, shortcut audits, route metrics, and compact result summaries from mounted data.",
            "required": "yes",
        },
        {
            "item": "dependency_record",
            "contract": "Dockerfile or compose plus pinned Python/package record; no host-only package install for promoted metrics.",
            "required": "yes",
        },
        {
            "item": "input_mounts",
            "contract": "Use read-only mounted dataset/source roots; do not copy local_dataset payload into tracked artifacts.",
            "required": "yes",
        },
        {
            "item": "output_manifest",
            "contract": "Each run writes row counts, split counts, route table, metric table, control table, and validation_errors.jsonl.",
            "required": "yes",
        },
        {
            "item": "h001_boundary",
            "contract": "H001 artifacts remain read-only. H002 promotion can reference source outputs only via explicit manifests.",
            "required": "yes",
        },
    ]


def heldout_contract() -> list[dict[str, Any]]:
    return [
        {
            "axis": "split_unit",
            "contract": "Primary grouping by scan_id; secondary guard by endpoint-pair identifier where available.",
            "reason": "Avoid same-scene or same-object-pair leakage across train/dev/test.",
        },
        {
            "axis": "route_balance",
            "contract": "Report per-route positive/negative/abstain counts and drop any paper metric for a route whose held-out target becomes single-class.",
            "reason": "R7 showed that row count alone is not enough.",
        },
        {
            "axis": "construction_fields",
            "contract": "candidate_bucket, geometry_status, label_match_status, proxy bucket, source rank bucket, and hidden construction fields stay out of model-safe inputs.",
            "reason": "Prevent target-construction leakage.",
        },
        {
            "axis": "controls",
            "contract": "For each promoted route, rerun T-only, G-only, plain concat, wrong-T, shuffled-G, and allowed shortcut probes on the same held-out groups.",
            "reason": "Mechanism evidence requires control collapse, not just high primary AUROC.",
        },
        {
            "axis": "reporting",
            "contract": "Report train/dev/test or train/dev protocol explicitly. Do not call train-side smoke a validation/test result.",
            "reason": "Maintain current boundary discipline.",
        },
    ]


def calibration_contract() -> list[dict[str, Any]]:
    return [
        {
            "head": "C_e",
            "role": "compatibility mechanism score",
            "metrics": "AUROC, AUPRC, balanced accuracy, control collapse",
            "paper_claim": "compatibility separates route-specific accept/reject candidates",
        },
        {
            "head": "p_rel",
            "role": "relation reliability when observable",
            "metrics": "ECE, Brier, NLL, AUROC/AUPRC, reliability diagram",
            "paper_claim": "only allowed after calibration gate passes",
        },
        {
            "head": "p_obs",
            "role": "decidability / abstention",
            "metrics": "selective risk, coverage-risk curve, abstain precision/recall, ECE if probabilistic",
            "paper_claim": "only allowed after observability labels and selective-decision protocol pass",
        },
        {
            "head": "Q_e",
            "role": "evidence quality input, not truth label",
            "metrics": "missing-evidence detection, route-specific ablation, Q-shuffle control",
            "paper_claim": "Q_e can govern abstention; it must not directly define relation truth",
        },
    ]


def target_independence_contract() -> list[dict[str, Any]]:
    return [
        {
            "audit": "schema_leakage",
            "required_check": "blocked field names and construction fields absent from model-safe views",
            "pass_condition": "0 blocked-field hits",
        },
        {
            "audit": "class_pair_shortcut",
            "required_check": "subject class, object class, predicate-class-pair, and endpoint-pair probes",
            "pass_condition": "shortcut probe cannot solve target and is reported alongside primary metric",
        },
        {
            "audit": "source_rank_shortcut",
            "required_check": "source id, source score, rank, rank band, and machine hint probes",
            "pass_condition": "Z_e is not used inside C_e; any final reliability use is separately ablated",
        },
        {
            "audit": "counterfactual_controls",
            "required_check": "wrong-T, shuffled-G global, shuffled-G within predicate/family, subject-object swap when meaningful",
            "pass_condition": "primary route signal collapses under invalid counterfactuals",
        },
        {
            "audit": "split_leakage",
            "required_check": "scan and endpoint-pair group disjointness",
            "pass_condition": "0 group overlap between reported splits",
        },
    ]


def claim_unlock_table(blocked_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "claim": "route-specific compatibility mechanism",
            "current_status": "allowed_hypothesis_stage",
            "unlock_gates": "P1,P2,P3,P5,P6",
            "allowed_wording_after_unlock": "Different relation families require different evidence routes, and route-specific C_e separates compatibility beyond T-only/G-only/fixed concat.",
            "still_forbidden": "all 3DSSG relations are solved",
        },
        {
            "claim": "geometry-only route exists",
            "current_status": "allowed_as_control",
            "unlock_gates": "P1,P2,P3,P6",
            "allowed_wording_after_unlock": "Some predicates such as close by are geometry-decidable and should use a simpler route.",
            "still_forbidden": "close by proves predicate-geometry interaction",
        },
        {
            "claim": "support/contact compatibility route",
            "current_status": "allowed_hypothesis_stage_with_caveat",
            "unlock_gates": "P1,P2,P3,P5,P6",
            "allowed_wording_after_unlock": "Support/contact is a challenging route where predicate-contact interaction is necessary but not fully solved.",
            "still_forbidden": "support/contact fully solved",
        },
    ]
    for row in blocked_rows:
        rows.append(
            {
                "claim": row.get("claim", ""),
                "current_status": "blocked",
                "unlock_gates": row.get("required_to_unblock", ""),
                "allowed_wording_after_unlock": "requires new evidence before wording can be fixed",
                "still_forbidden": row.get("blocked_reason", ""),
            }
        )
    return rows


def execution_order() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "todo": NEXT_TODO,
            "action": "write the Docker and held-out split protocol without running promoted metrics",
            "stop_condition": "protocol accepted or explicit user decision to keep H002 hypothesis-only",
        },
        {
            "order": 2,
            "todo": "create_experiment_root_only_after_protocol_acceptance",
            "action": "if accepted, create minimal Docker experiment root and command manifest",
            "stop_condition": "Docker smoke reproduces row counts and route table",
        },
        {
            "order": 3,
            "todo": "run_route_specific_grouped_evaluation",
            "action": "regenerate route metrics and controls under grouped split",
            "stop_condition": "candidate main rows pass/fail promotion gates",
        },
        {
            "order": 4,
            "todo": "calibration_selective_decision_plan_if_needed",
            "action": "only if p_rel/p_obs claim remains desired, run calibration/selective-risk protocol",
            "stop_condition": "calibrated claim passes or stays blocked",
        },
    ]


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# H002 Promotion Gap Plan",
        "",
        "## Verdict",
        "",
        (
            "The promotion path is staged. H002 should not jump directly from train-only route probes "
            "to a paper result. The next concrete step is a Docker + held-out grouped protocol plan."
        ),
        "",
        "## Roadmap",
        "",
        "| Step | Name | Status | Unlocks |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["promotion_roadmap"]:
        lines.append("| {step} | {name} | {status} | {unlocks} |".format(**row))
    lines.extend(
        [
            "",
            "## Route Gate Matrix",
            "",
            "| Family | Role | Priority | Required gates |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in payload["route_gate_matrix"]:
        lines.append(
            "| {family} | {promotion_role} | {priority} | {required_gates} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Next",
            "",
            f"`{NEXT_TODO}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary = read_json(args.readiness_dir / "summary.json")
    candidate_rows = read_csv(args.readiness_dir / "candidate_main_table_rows.csv")
    diagnostic_rows = read_csv(args.readiness_dir / "diagnostic_boundary_table.csv")
    gap_rows = read_csv(args.readiness_dir / "promotion_gap_table.csv")
    blocked_rows = read_csv(args.readiness_dir / "blocked_claims.csv")

    errors = validate_inputs(
        summary, candidate_rows, diagnostic_rows, gap_rows, blocked_rows, args.readiness_dir
    )

    roadmap = promotion_roadmap()
    route_matrix = route_gate_matrix(candidate_rows, diagnostic_rows)
    docker = docker_contract()
    heldout = heldout_contract()
    calibration = calibration_contract()
    independence = target_independence_contract()
    claim_unlock = claim_unlock_table(blocked_rows)
    execution = execution_order()

    if not any(row["step"] == "P1" and row["status"] == "next" for row in roadmap):
        errors.append({"error_type": "missing_p1_next_step"})
    if not any(row["family"] == "support_contact" for row in route_matrix):
        errors.append({"error_type": "missing_support_contact_route_matrix"})
    if not any(row["item"] == "h001_boundary" for row in docker):
        errors.append({"error_type": "missing_h001_boundary_contract"})

    status = STATUS_READY if not errors else STATUS_ERROR
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_input_errors_before_promotion_gap_plan",
        "next_todo": NEXT_TODO if not errors else EXPECTED_READINESS_NEXT,
        "created_at_utc": now,
        "validation_errors": len(errors),
        "boundary": {
            "validation_usage": False,
            "test_usage": False,
            "new_model_or_smoke_run": False,
            "docker_experiment_created": False,
            "h001_artifacts_modified": False,
            "paper_level_ready": False,
            "framework_ready_hypothesis_stage": not errors,
        },
        "input_artifacts": {
            "readiness_review": rel_path(args.readiness_dir),
        },
        "decision_summary": {
            "promotion_strategy": "stage_promotion_before_any_paper_result_claim",
            "next_step": "docker_heldout_protocol_plan",
            "minimal_paper_candidate_routes": [
                "relative_vertical",
                "size_relative",
                "relative_horizontal",
                "support_contact",
            ],
            "diagnostic_routes_not_promoted": [
                "proximity_close_by",
                "support_contact_superordinate_supported_by",
                "attachment_like_R7",
                "future_or_separate_routes",
            ],
            "still_blocked": [
                "paper-level reliability improvement",
                "calibrated p_rel/p_obs",
                "all-family generality",
                "current R7 learned reliability",
                "support/contact fully solved",
                "complete 3DSSG relation coverage",
            ],
        },
        "promotion_roadmap": roadmap,
        "route_gate_matrix": route_matrix,
        "docker_protocol_contract": docker,
        "heldout_split_contract": heldout,
        "calibration_selective_contract": calibration,
        "target_independence_contract": independence,
        "claim_unlock_table": claim_unlock,
        "execution_order": execution,
    }

    write_csv(args.output_dir / "promotion_roadmap.csv", roadmap)
    write_csv(args.output_dir / "route_gate_matrix.csv", route_matrix)
    write_csv(args.output_dir / "docker_protocol_contract.csv", docker)
    write_csv(args.output_dir / "heldout_split_contract.csv", heldout)
    write_csv(args.output_dir / "calibration_selective_contract.csv", calibration)
    write_csv(args.output_dir / "target_independence_contract.csv", independence)
    write_csv(args.output_dir / "claim_unlock_table.csv", claim_unlock)
    write_csv(args.output_dir / "execution_order.csv", execution)
    write_json(
        args.output_dir / "next_contract.json",
        {
            "next_todo": NEXT_TODO,
            "must_do": [
                "write a Docker/held-out grouped protocol plan before creating an experiment root",
                "define exact row/source manifests and split leakage audits",
                "preserve H001 artifacts as read-only inputs if referenced",
            ],
            "must_not_do": [
                "run paper-level H002 metrics from host-only scripts",
                "create a new experiment root before protocol acceptance",
                "claim calibrated p_rel/p_obs before calibration metrics exist",
            ],
        },
    )
    write_json(args.output_dir / "summary.json", payload)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
