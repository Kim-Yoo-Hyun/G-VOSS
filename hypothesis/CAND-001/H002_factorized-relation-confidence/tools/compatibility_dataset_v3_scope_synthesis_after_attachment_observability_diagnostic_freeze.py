#!/usr/bin/env python3
"""Synthesize H002 scope after freezing R7 attachment-observability diagnostics."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_R7_FREEZE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit"
)
DEFAULT_MULTI_FAMILY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal"
)
DEFAULT_COVERAGE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan"
)
DEFAULT_SCHEMA_FREEZE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze"
)

EXPECTED_R7_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_freeze_diagnostic"
)
EXPECTED_R7_NEXT = "compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze"
EXPECTED_MULTI_FAMILY_STATUS = (
    "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal_ready"
)
EXPECTED_COVERAGE_STATUS = (
    "h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan_ready"
)
EXPECTED_SCHEMA_FREEZE_STATUS = (
    "h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_ready"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze_input_errors"
)
SELECTED_PATH = (
    "scope_sufficient_after_r7_freeze_select_paper_framework_readiness_review"
)
NEXT_TODO = "compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r7-freeze-dir", type=Path, default=DEFAULT_R7_FREEZE_DIR)
    parser.add_argument("--multi-family-dir", type=Path, default=DEFAULT_MULTI_FAMILY_DIR)
    parser.add_argument("--coverage-dir", type=Path, default=DEFAULT_COVERAGE_DIR)
    parser.add_argument("--schema-freeze-dir", type=Path, default=DEFAULT_SCHEMA_FREEZE_DIR)
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


def validate_inputs(
    r7: dict[str, Any],
    multi_family: dict[str, Any],
    coverage: dict[str, Any],
    schema_freeze: dict[str, Any],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {
        "r7_freeze": (r7, EXPECTED_R7_STATUS),
        "multi_family": (multi_family, EXPECTED_MULTI_FAMILY_STATUS),
        "coverage": (coverage, EXPECTED_COVERAGE_STATUS),
        "schema_freeze": (schema_freeze, EXPECTED_SCHEMA_FREEZE_STATUS),
    }
    for name, (summary, status) in expected.items():
        if summary.get("status") != status:
            errors.append({"input": name, "error_type": "unexpected_status", "actual": summary.get("status")})
        if summary.get("validation_errors") != 0:
            errors.append({"input": name, "error_type": "validation_errors_present", "actual": summary.get("validation_errors")})
        boundary = summary.get("boundary", {})
        for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed"]:
            if key in boundary and boundary.get(key) is not False:
                errors.append({"input": name, "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
        validation_file = roots[name] / "validation_errors.jsonl"
        if validation_file.exists() and validation_file.read_text(encoding="utf-8").strip():
            errors.append({"input": name, "error_type": "validation_error_rows_present"})

    if r7.get("next_todo") != EXPECTED_R7_NEXT:
        errors.append({"input": "r7_freeze", "error_type": "unexpected_next_todo", "actual": r7.get("next_todo")})
    if r7.get("decision_summary", {}).get("learned_smoke_allowed") is not False:
        errors.append({"input": "r7_freeze", "error_type": "r7_learned_smoke_not_false"})

    required_files = [
        roots["multi_family"] / "family_route_table.csv",
        roots["multi_family"] / "evidence_table.csv",
        roots["coverage"] / "family_decisions.csv",
        roots["coverage"] / "sufficiency_decision.csv",
        roots["schema_freeze"] / "route_taxonomy_freeze.csv",
        roots["schema_freeze"] / "paper_claim_boundary.csv",
    ]
    for path in required_files:
        if not path.exists():
            errors.append({"input": "artifact_file", "error_type": "missing_required_file", "path": rel_path(path)})
    return errors


def update_family_routes(routes: list[dict[str, str]], r7: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in routes:
        updated: dict[str, Any] = dict(row)
        if row.get("family") == "attachment_like":
            updated.update(
                {
                    "route": "observability-heavy diagnostic/future route",
                    "use_in_claim": "diagnostic_or_future_boundary",
                    "evidence_route": "visual/mesh contact + topology + Q_e required; current source-proxy repair frozen",
                    "p_obs_role": "central but current packet set is negative-sparse",
                    "risk": "current class-pair repair target collapses to object-class prior",
                    "decision": "freeze current R7 artifact as diagnostic; future revisit requires evidence-first target construction",
                    "r7_current_status": r7.get("status"),
                }
            )
        out.append(updated)
    return out


def update_evidence_table(evidence_rows: list[dict[str, str]], r7: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics = r7.get("decision_summary", {}).get("key_diagnostics", {})
    out: list[dict[str, Any]] = []
    for row in evidence_rows:
        updated: dict[str, Any] = dict(row)
        if row.get("family") == "attachment_like":
            updated.update(
                {
                    "route_type": "observability-heavy diagnostic/future route",
                    "primary_signal": "blocked by class-prior shortcut",
                    "semantic_only": "not promoted",
                    "geometry_only": "not promoted",
                    "plain_concat": "not promoted",
                    "wrong_T": "not run",
                    "shuffled_G": "not run",
                    "paper_role": "diagnostic/future boundary",
                    "caveat": (
                        "current R7 class-pair repair frozen: combined p_rel 258/90 but "
                        "predicate-class-pair acc 1.0; hanging-on 86/90 but class-label acc 1.0"
                    ),
                    "r7_allowed_high_risk_blockers": diagnostics.get("allowed_high_risk_blockers"),
                }
            )
        out.append(updated)
    return out


def final_scope_rows() -> list[dict[str, Any]]:
    return [
        {
            "scope": "main_mechanism_evidence",
            "families": "relative_vertical; size_relative; relative_horizontal; support_contact",
            "status": "retain",
            "meaning": "train-only relation-aware T_e x G_e compatibility evidence",
            "blocked_overclaim": "paper-level reliability or all-family solved claim",
        },
        {
            "scope": "geometry_easy_control",
            "families": "proximity / close by",
            "status": "retain_as_control",
            "meaning": "some relations are geometry-decidable and should route differently",
            "blocked_overclaim": "predicate-geometry interaction is needed for close by",
        },
        {
            "scope": "superordinate_decomposition",
            "families": "supported by",
            "status": "retain_as_diagnostic",
            "meaning": "broad support labels need relabel/abstain/decomposition rather than clean binary truth",
            "blocked_overclaim": "supported by is fully solved",
        },
        {
            "scope": "observability_heavy_boundary",
            "families": "attached to; hanging on; connected to",
            "status": "freeze_current_artifact_as_diagnostic",
            "meaning": "visual/mesh/topology observability is required; current proxy labels are not independent",
            "blocked_overclaim": "R7 learned p_rel/p_obs result exists",
        },
        {
            "scope": "future_or_separate_routes",
            "families": "containment; cover; leaning against; identity/symmetry; semantic/structural",
            "status": "defer",
            "meaning": "route taxonomy acknowledges them, but current H002 claim does not depend on solving them",
            "blocked_overclaim": "all relation types have been solved",
        },
    ]


def route_decisions() -> list[dict[str, Any]]:
    return [
        {
            "option": "add another relation family now",
            "decision": "reject_for_now",
            "reason": "R7 freeze confirms the bottleneck is target independence and promotion boundary, not missing another family",
            "next_condition": "reopen only if the claim is widened to all-family generality",
        },
        {
            "option": "repeat R7 class-pair repair",
            "decision": "reject",
            "reason": "same proxy recipe already collapsed to object-class prior after visible labels",
            "next_condition": "requires evidence-first visual/mesh target construction",
        },
        {
            "option": "proceed to paper/framework readiness review",
            "decision": "selected",
            "reason": "current route set is enough for hypothesis-stage framework claim; next blocker is promotion/readiness",
            "next_condition": NEXT_TODO,
        },
        {
            "option": "claim all-family reliability",
            "decision": "reject",
            "reason": "R7, containment, identity/symmetry, semantic/structural routes remain diagnostic/future/boundary",
            "next_condition": "requires new evidence routes, labels, controls, and held-out evaluation",
        },
    ]


def risk_rows() -> list[dict[str, Any]]:
    return [
        {
            "risk": "R7 interpreted as failed method",
            "severity": "medium",
            "evidence": "current R7 target froze as diagnostic-only",
            "mitigation": "state that R7 tests target/evidence route boundary; the failure is target independence, not route nonexistence",
        },
        {
            "risk": "cherry_picking_successful_families",
            "severity": "high",
            "evidence": "some families are main evidence while R7/supported-by/proximity are diagnostic",
            "mitigation": "show full route taxonomy and route-specific decisions, including failures and boundaries",
        },
        {
            "risk": "train-only mechanism overclaim",
            "severity": "high",
            "evidence": "all current H002 evidence remains train-only and many rows are constructed targets",
            "mitigation": "next readiness review must separate hypothesis-stage mechanism claim from paper-level evidence",
        },
        {
            "risk": "calibration claim leakage",
            "severity": "high",
            "evidence": "high AUROC compatibility scores are not calibrated p_rel/p_obs",
            "mitigation": "keep calibrated posterior claim blocked until proper calibration split/protocol exists",
        },
    ]


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Decide whether H002 is ready to move from hypothesis-stage route evidence into paper/framework planning.",
        "required_inputs": [
            "multi-family route/evidence table",
            "route coverage sufficiency decision",
            "schema freeze and promotion protocol",
            "route-specific probe results including R7 diagnostic freeze",
        ],
        "required_outputs": [
            "allowed vs blocked claims",
            "main table candidate rows",
            "which artifacts can be promoted to Docker/paper experiments",
            "which routes stay diagnostic/future",
            "reviewer-risk checklist",
        ],
        "must_not_do": [
            "run learned smoke on current R7 artifact",
            "claim all-family generality",
            "claim calibrated p_rel/p_obs",
            "modify H001 artifacts",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Scope Synthesis After Attachment Observability Diagnostic Freeze",
        "",
        "## Result",
        "",
        "```text",
        f"artifact_root = {summary['artifact_root']}",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Decision",
        "",
        "The current H002 route coverage remains sufficient for a hypothesis-stage",
        "relation-aware evidence routing framework. R7 does not become main learned",
        "evidence; it is frozen as an observability-heavy diagnostic/future boundary.",
        "",
        "Do not add another relation family now. The missing step is readiness review:",
        "which claims, rows, controls, and artifacts can be promoted beyond",
        "hypothesis-stage records.",
        "",
        "## Route Boundary",
        "",
        "- main mechanism: `relative_vertical`, `size_relative`, `relative_horizontal`, `support_contact`",
        "- control/generality: `close by`",
        "- diagnostic decomposition: `supported by`",
        "- diagnostic/future observability: `attached to`, `hanging on`, `connected to`",
        "- future/boundary: containment, cover, leaning, identity/symmetry, semantic/structural relations",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    r7 = read_json(args.r7_freeze_dir / "summary.json")
    multi_family = read_json(args.multi_family_dir / "summary.json")
    coverage = read_json(args.coverage_dir / "summary.json")
    schema_freeze = read_json(args.schema_freeze_dir / "summary.json")
    roots = {
        "r7_freeze": args.r7_freeze_dir,
        "multi_family": args.multi_family_dir,
        "coverage": args.coverage_dir,
        "schema_freeze": args.schema_freeze_dir,
    }
    errors = validate_inputs(r7, multi_family, coverage, schema_freeze, roots)

    family_routes = update_family_routes(read_csv(args.multi_family_dir / "family_route_table.csv"), r7)
    evidence_rows = update_evidence_table(read_csv(args.multi_family_dir / "evidence_table.csv"), r7)
    scope_rows = final_scope_rows()
    decision_rows = route_decisions()
    risks = risk_rows()
    contract = next_contract()

    status = STATUS_ERROR if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_root": rel_path(args.output_dir),
        "status": status,
        "selected_path": "input_errors_stop" if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "boundary": {
            "split": "train_only_scope_synthesis",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "fills_new_labels": False,
            "materializes_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
        },
        "input_paths": {
            "r7_freeze": rel_path(args.r7_freeze_dir / "summary.json"),
            "multi_family": rel_path(args.multi_family_dir / "summary.json"),
            "coverage": rel_path(args.coverage_dir / "summary.json"),
            "schema_freeze": rel_path(args.schema_freeze_dir / "summary.json"),
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "family_route_table": rel_path(args.output_dir / "family_route_table.csv"),
            "evidence_table": rel_path(args.output_dir / "evidence_table.csv"),
            "final_scope_table": rel_path(args.output_dir / "final_scope_table.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "risk_register": rel_path(args.output_dir / "risk_register.csv"),
            "next_contract": rel_path(args.output_dir / "next_contract.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "decision_summary": {
            "selected": "scope_sufficient_after_r7_freeze",
            "next": NEXT_TODO,
            "new_family_mining_now": False,
            "r7_current_artifact_role": "diagnostic_only",
            "main_mechanism_families": [
                "relative_vertical",
                "size_relative",
                "relative_horizontal",
                "support_contact",
            ],
            "control_or_diagnostic_families": [
                "proximity",
                "supported_by",
                "attachment_observability",
                "containment",
                "identity_symmetry",
                "semantic_structural",
            ],
            "blocked_claims": [
                "all-family generality",
                "paper-level performance",
                "held-out/test reliability",
                "calibrated p_rel/p_obs",
                "R7 learned reliability on current artifact",
                "support/contact fully solved",
            ],
        },
        "counts": {
            "family_route_rows": len(family_routes),
            "evidence_rows": len(evidence_rows),
            "final_scope_rows": len(scope_rows),
            "route_decision_rows": len(decision_rows),
            "risk_rows": len(risks),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "family_route_table.csv", family_routes)
    write_csv(args.output_dir / "evidence_table.csv", evidence_rows)
    write_csv(args.output_dir / "final_scope_table.csv", scope_rows)
    write_csv(args.output_dir / "route_decision.csv", decision_rows)
    write_csv(args.output_dir / "risk_register.csv", risks)
    write_json(args.output_dir / "next_contract.json", contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
