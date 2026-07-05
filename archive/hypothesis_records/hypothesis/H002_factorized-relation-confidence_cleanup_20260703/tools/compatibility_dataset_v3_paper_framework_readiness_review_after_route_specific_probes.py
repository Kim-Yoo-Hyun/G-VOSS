#!/usr/bin/env python3
"""Review H002 route-specific probes for paper/framework readiness."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCOPE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze"
)
DEFAULT_SCHEMA_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review"
)
DEFAULT_MANIFEST_AUDIT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes"
)

EXPECTED_SCOPE_STATUS = (
    "h002_compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze_ready"
)
EXPECTED_SCOPE_NEXT = "compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes"
EXPECTED_SCHEMA_STATUS = (
    "h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_ready"
)
EXPECTED_MANIFEST_STATUS = (
    "h002_compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan_ready"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes_input_errors"
)
SELECTED_PATH = "readiness_review_completed_select_promotion_gap_plan"
NEXT_TODO = "compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_DIR)
    parser.add_argument("--manifest-audit-dir", type=Path, default=DEFAULT_MANIFEST_AUDIT_DIR)
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
    scope_summary: dict[str, Any],
    schema_summary: dict[str, Any],
    manifest_summary: dict[str, Any],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {
        "scope": (scope_summary, EXPECTED_SCOPE_STATUS),
        "schema": (schema_summary, EXPECTED_SCHEMA_STATUS),
        "manifest_audit": (manifest_summary, EXPECTED_MANIFEST_STATUS),
    }
    for name, (summary, status) in expected.items():
        if summary.get("status") != status:
            errors.append(
                {
                    "input": name,
                    "error_type": "unexpected_status",
                    "expected": status,
                    "actual": summary.get("status"),
                }
            )
        if validation_count(summary) != 0:
            errors.append(
                {
                    "input": name,
                    "error_type": "validation_errors_present",
                    "actual": validation_count(summary),
                }
            )
        validation_file = roots[name] / "validation_errors.jsonl"
        if validation_file.exists() and validation_file.read_text(encoding="utf-8").strip():
            errors.append({"input": name, "error_type": "validation_error_rows_present"})

    if scope_summary.get("next_todo") != EXPECTED_SCOPE_NEXT:
        errors.append(
            {
                "input": "scope",
                "error_type": "unexpected_next_todo",
                "expected": EXPECTED_SCOPE_NEXT,
                "actual": scope_summary.get("next_todo"),
            }
        )

    required = [
        roots["scope"] / "evidence_table.csv",
        roots["scope"] / "family_route_table.csv",
        roots["scope"] / "final_scope_table.csv",
        roots["scope"] / "risk_register.csv",
        roots["schema"] / "route_taxonomy_freeze.csv",
        roots["schema"] / "paper_claim_boundary.csv",
        roots["schema"] / "promotion_protocol.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append({"input": "artifact_file", "error_type": "missing_required_file", "path": rel_path(path)})
    return errors


def readiness_rows(evidence_rows: list[dict[str, str]], route_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    route_by_family = {row.get("family"): row for row in route_rows}
    family_status = {
        "relative_vertical": (
            "promotable_train_only_mechanism",
            "clean T_e x G_e mechanism anchor; too clean if used alone",
            "Docker reproduction, held-out grouped split, calibration if p_rel is claimed",
        ),
        "size_relative": (
            "promotable_train_only_mechanism",
            "second clean mechanism anchor; deterministic size cue must be framed carefully",
            "Docker reproduction, held-out grouped split, calibration caveat wording",
        ),
        "relative_horizontal": (
            "promotable_train_only_mechanism_with_reference_frame_caveat",
            "frame-aware directional compatibility evidence; excludes complete horizontal ontology",
            "reference-frame definition, held-out grouped split, explicit in-front-of exclusion",
        ),
        "support_contact": (
            "promotable_train_only_challenging_mechanism_with_caveat",
            "interaction necessity evidence; not fully solved and near-threshold internally",
            "failure taxonomy, held-out grouped split, Docker reproduction, Q_e/p_obs calibration later",
        ),
        "proximity": (
            "control_or_generality_only",
            "geometry-only route control; not T_e x G_e interaction proof",
            "keep as route-gating/control row, not main compatibility success",
        ),
        "attachment_like": (
            "diagnostic_future_boundary",
            "observability-heavy relation family; current R7 target is shortcut-prone",
            "evidence-first visual/mesh/topology target before learned smoke",
        ),
    }
    rows: list[dict[str, Any]] = []
    for row in evidence_rows:
        family = row.get("family", "")
        status, reason, needed = family_status.get(
            family,
            ("diagnostic_or_deferred", "not part of current paper-ready mechanism set", "separate route-specific target"),
        )
        route = route_by_family.get(family, {})
        paper_level_ready = "false"
        if status.startswith("control"):
            table_role = "control_table_or_route_taxonomy"
        elif status.startswith("diagnostic"):
            table_role = "diagnostic_boundary_table"
        elif status.startswith("promotable"):
            table_role = "candidate_main_mechanism_table_train_only"
        else:
            table_role = "deferred"
        rows.append(
            {
                "family": family,
                "predicates": row.get("predicates", route.get("predicates", "")),
                "route_type": row.get("route_type", route.get("route", "")),
                "readiness": status,
                "table_role": table_role,
                "paper_level_ready_now": paper_level_ready,
                "why": reason,
                "primary_signal": row.get("primary_signal", ""),
                "semantic_only": row.get("semantic_only", ""),
                "geometry_only": row.get("geometry_only", ""),
                "plain_concat": row.get("plain_concat", ""),
                "wrong_T": row.get("wrong_T", ""),
                "shuffled_G": row.get("shuffled_G", ""),
                "claim_allowed_now": (
                    "hypothesis-stage mechanism/framework claim only"
                    if status.startswith("promotable")
                    else "diagnostic/framework-boundary claim only"
                ),
                "required_before_paper_result": needed,
                "blocked_overclaim": route.get("risk", row.get("caveat", "")),
            }
        )
    return rows


def candidate_main_rows(readiness: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for row in readiness:
        if row["table_role"] == "candidate_main_mechanism_table_train_only":
            selected.append(
                {
                    "candidate_table": "route_specific_mechanism_evidence",
                    "family": row["family"],
                    "predicates": row["predicates"],
                    "route_claim": row["route_type"],
                    "primary_Ce_or_route_signal": row["primary_signal"],
                    "T_only_or_semantic_baseline": row["semantic_only"],
                    "G_only_baseline": row["geometry_only"],
                    "plain_concat_baseline": row["plain_concat"],
                    "wrong_T_control": row["wrong_T"],
                    "shuffled_G_control": row["shuffled_G"],
                    "paper_position_now": "candidate row only; hypothesis-stage train-only",
                    "minimum_promotion_gate": row["required_before_paper_result"],
                }
            )
    return selected


def diagnostic_rows(
    readiness: list[dict[str, Any]], final_scope_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in readiness:
        if row["table_role"] != "candidate_main_mechanism_table_train_only":
            seen.add(row["family"])
            rows.append(
                {
                    "family": row["family"],
                    "predicates": row["predicates"],
                    "diagnostic_role": row["table_role"],
                    "reason": row["why"],
                    "allowed_use": row["claim_allowed_now"],
                    "blocked_use": row["blocked_overclaim"],
                    "next_if_reopened": row["required_before_paper_result"],
                }
            )
    for row in final_scope_rows:
        scope = row.get("scope", "")
        if scope == "superordinate_decomposition" and "support_contact_superordinate" not in seen:
            rows.append(
                {
                    "family": "support_contact_superordinate",
                    "predicates": "supported by",
                    "diagnostic_role": "superordinate_decomposition_diagnostic",
                    "reason": row.get("meaning", ""),
                    "allowed_use": "diagnostic decomposition / relabel / abstain route",
                    "blocked_use": row.get("blocked_overclaim", ""),
                    "next_if_reopened": "subtype-aware support target with relabel and abstain labels",
                }
            )
        if scope == "future_or_separate_routes":
            rows.append(
                {
                    "family": "future_or_separate_routes",
                    "predicates": row.get("families", ""),
                    "diagnostic_role": "deferred_taxonomy_boundary",
                    "reason": row.get("meaning", ""),
                    "allowed_use": "route taxonomy coverage only",
                    "blocked_use": row.get("blocked_overclaim", ""),
                    "next_if_reopened": "new evidence route, target definition, schema audit, and held-out protocol",
                }
            )
    return rows


def promotion_gaps() -> list[dict[str, Any]]:
    return [
        {
            "gate": "G1",
            "gap": "Docker reproduction",
            "why_it_matters": "Current H002 results are hypothesis-stage local artifacts, not promoted experiment results.",
            "minimum_action": "Create Docker/compose entrypoint and regenerate candidate route-specific tables from mounted data.",
            "blocks": "paper-level metric/result claims",
        },
        {
            "gate": "G2",
            "gap": "Held-out grouped evaluation",
            "why_it_matters": "Train-side constructed targets can overstate mechanism separation even when shortcut audits pass.",
            "minimum_action": "Use scan and endpoint-pair grouped splits; report no split leakage and per-family counts.",
            "blocks": "generalization and performance claims",
        },
        {
            "gate": "G3",
            "gap": "Calibration and selective decision",
            "why_it_matters": "High AUROC C_e is not calibrated p_rel or p_obs.",
            "minimum_action": "Run ECE, Brier, NLL, selective-risk/coverage curves for p_rel and p_obs.",
            "blocks": "calibrated reliability posterior and abstention claims",
        },
        {
            "gate": "G4",
            "gap": "Target-independence replication",
            "why_it_matters": "R7 showed that sufficient row counts can still collapse to class-pair shortcuts.",
            "minimum_action": "Repeat schema, shortcut, wrong-T, shuffled-G, class-pair, rank/source, and endpoint leakage audits for promoted routes.",
            "blocks": "reviewer defense against target construction artifacts",
        },
        {
            "gate": "G5",
            "gap": "Failure taxonomy and boundary wording",
            "why_it_matters": "Support/contact and R7 must not be presented as solved; failures are part of route taxonomy evidence.",
            "minimum_action": "Lock claim wording, diagnostic/future rows, and qualitative examples before paper drafting.",
            "blocks": "overbroad all-family claim",
        },
    ]


def blocked_claims(schema_claims: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in schema_claims:
        if row.get("status") == "blocked":
            rows.append(
                {
                    "claim": row.get("claim", ""),
                    "blocked_reason": row.get("wording", ""),
                    "required_to_unblock": row.get("required_artifact", ""),
                    "current_review_verdict": "still_blocked_after_route_specific_probes",
                }
            )
    rows.extend(
        [
            {
                "claim": "current R7 attachment-like learned reliability",
                "blocked_reason": "class-pair repair target is shortcut-prone and p_obs is negative-sparse.",
                "required_to_unblock": "evidence-first visual/mesh/topology target with independent observable accept/reject/abstain labels",
                "current_review_verdict": "blocked",
            },
            {
                "claim": "support/contact fully solved",
                "blocked_reason": "interaction signal is meaningful but aggregate result is near-threshold with standing/lying ambiguity.",
                "required_to_unblock": "stronger evidence, held-out grouped evaluation, and failure analysis showing robust route behavior",
                "current_review_verdict": "blocked",
            },
            {
                "claim": "complete 3DSSG relation coverage",
                "blocked_reason": "containment, cover, leaning, identity/symmetry, and semantic/structural relations remain deferred routes.",
                "required_to_unblock": "route-specific targets and audits for each deferred family",
                "current_review_verdict": "blocked",
            },
        ]
    )
    return rows


def reviewer_risks(existing_risks: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in existing_risks:
        rows.append(
            {
                "risk": row.get("risk", ""),
                "severity": row.get("severity", ""),
                "evidence": row.get("evidence", ""),
                "review_verdict": "still_relevant",
                "mitigation": row.get("mitigation", ""),
            }
        )
    rows.extend(
        [
            {
                "risk": "readiness mistaken for paper result",
                "severity": "high",
                "evidence": "review selects candidate table rows but paper_level_ready_now remains false",
                "review_verdict": "must_separate_framework_ready_from_result_ready",
                "mitigation": "next promotion-gap plan defines Docker/held-out/calibration gates before paper-result promotion",
            },
            {
                "risk": "successful route cherry-picking",
                "severity": "high",
                "evidence": "main rows are four families; R7 and supported-by are diagnostic",
                "review_verdict": "manageable_if_route_taxonomy_is_shown",
                "mitigation": "include diagnostic/boundary table and explain relation-specific target semantics",
            },
            {
                "risk": "fixed fusion baseline ambiguity",
                "severity": "medium",
                "evidence": "close by is geometry-only sufficient while support/contact needs interaction",
                "review_verdict": "turn_into_relation-aware_routing_argument",
                "mitigation": "state that H002 rejects one universal fusion route, not geometry evidence itself",
            },
        ]
    )
    return rows


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# H002 Paper/Framework Readiness Review",
        "",
        "## Verdict",
        "",
        (
            "Current H002 is framework-ready as a hypothesis-stage route-specific mechanism package, "
            "but it is not paper-result ready. The next step is a promotion-gap plan, not another "
            "relation-family mining pass."
        ),
        "",
        "## Candidate Main Mechanism Rows",
        "",
        "| Family | Predicates | Role | Primary signal | Required before paper result |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["candidate_main_table_rows"]:
        lines.append(
            "| {family} | {predicates} | {route_claim} | {primary_Ce_or_route_signal} | {minimum_promotion_gate} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Diagnostic / Boundary Rows",
            "",
            "| Family | Predicates | Role | Reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in payload["diagnostic_boundary_table"]:
        lines.append(
            "| {family} | {predicates} | {diagnostic_role} | {reason} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Promotion Gaps",
            "",
            "| Gate | Gap | Blocks |",
            "| --- | --- | --- |",
        ]
    )
    for row in payload["promotion_gap_table"]:
        lines.append("| {gate} | {gap} | {blocks} |".format(**row))
    lines.extend(
        [
            "",
            "## Blocked Claims",
            "",
            "| Claim | Required to unblock |",
            "| --- | --- |",
        ]
    )
    for row in payload["blocked_claims"]:
        lines.append("| {claim} | {required_to_unblock} |".format(**row))
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

    roots = {
        "scope": args.scope_dir,
        "schema": args.schema_dir,
        "manifest_audit": args.manifest_audit_dir,
    }
    scope_summary = read_json(args.scope_dir / "summary.json")
    schema_summary = read_json(args.schema_dir / "summary.json")
    manifest_summary = read_json(args.manifest_audit_dir / "summary.json")

    errors = validate_inputs(scope_summary, schema_summary, manifest_summary, roots)

    evidence = read_csv(args.scope_dir / "evidence_table.csv")
    routes = read_csv(args.scope_dir / "family_route_table.csv")
    final_scope = read_csv(args.scope_dir / "final_scope_table.csv")
    schema_claims = read_csv(args.schema_dir / "paper_claim_boundary.csv")
    existing_risks = read_csv(args.scope_dir / "risk_register.csv")

    readiness = readiness_rows(evidence, routes)
    main_rows = candidate_main_rows(readiness)
    diagnostic = diagnostic_rows(readiness, final_scope)
    gaps = promotion_gaps()
    blocked = blocked_claims(schema_claims)
    risks = reviewer_risks(existing_risks)

    if len(main_rows) != 4:
        errors.append({"error_type": "unexpected_main_candidate_count", "actual": len(main_rows)})
    if not any(row["family"] == "attachment_like" for row in diagnostic):
        errors.append({"error_type": "missing_attachment_diagnostic_boundary"})
    if not any(row["family"] == "proximity" for row in diagnostic):
        errors.append({"error_type": "missing_proximity_control_boundary"})

    status = STATUS_READY if not errors else STATUS_ERROR
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_input_errors_before_readiness_review",
        "next_todo": NEXT_TODO if not errors else EXPECTED_SCOPE_NEXT,
        "created_at_utc": now,
        "validation_errors": len(errors),
        "boundary": {
            "validation_usage": False,
            "test_usage": False,
            "new_model_or_smoke_run": False,
            "h001_artifacts_modified": False,
            "paper_level_ready": False,
            "framework_ready_hypothesis_stage": not errors,
        },
        "input_artifacts": {
            "scope": rel_path(args.scope_dir),
            "schema": rel_path(args.schema_dir),
            "manifest_audit": rel_path(args.manifest_audit_dir),
        },
        "decision_summary": {
            "paper_framework_readiness": "framework_ready_not_paper_result_ready" if not errors else "blocked",
            "candidate_main_mechanism_families": [
                "relative_vertical",
                "size_relative",
                "relative_horizontal",
                "support_contact",
            ],
            "diagnostic_or_control_families": [
                "proximity_close_by",
                "supported_by",
                "attachment_like_R7",
                "future_or_separate_routes",
            ],
            "next_reason": (
                "The bottleneck is now promotion readiness: Docker reproduction, held-out grouped evaluation, "
                "calibration/selective decision, and claim wording."
            ),
        },
        "candidate_main_table_rows": main_rows,
        "diagnostic_boundary_table": diagnostic,
        "promotion_gap_table": gaps,
        "blocked_claims": blocked,
        "reviewer_risks": risks,
    }

    write_csv(args.output_dir / "readiness_table.csv", readiness)
    write_csv(args.output_dir / "candidate_main_table_rows.csv", main_rows)
    write_csv(args.output_dir / "diagnostic_boundary_table.csv", diagnostic)
    write_csv(args.output_dir / "promotion_gap_table.csv", gaps)
    write_csv(args.output_dir / "blocked_claims.csv", blocked)
    write_csv(args.output_dir / "reviewer_risk_register.csv", risks)
    write_json(
        args.output_dir / "next_contract.json",
        {
            "next_todo": NEXT_TODO,
            "must_do": [
                "convert readiness gaps into a concrete promotion plan",
                "define Docker/held-out/calibration gates per route",
                "lock paper/framework claim wording before new relation mining",
            ],
            "must_not_do": [
                "treat train-only mechanism rows as paper-level results",
                "promote current R7 artifact as learned reliability evidence",
                "claim all 3DSSG relation types are solved",
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
