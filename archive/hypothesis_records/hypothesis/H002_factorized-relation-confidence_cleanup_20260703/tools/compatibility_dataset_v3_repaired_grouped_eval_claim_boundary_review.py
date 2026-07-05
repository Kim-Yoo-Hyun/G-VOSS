#!/usr/bin/env python3
"""Lock the H002 claim boundary after repaired grouped evaluation."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REPAIR_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis"
DEFAULT_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner"
DEFAULT_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review"

EXPECTED_REPAIR_STATUS = "h002_compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis_ready"
EXPECTED_REVIEW_STATUS = "h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_ready"
EXPECTED_CURRENT_TODO = "compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review_input_errors"
SELECTED_PATH = "claim_boundary_locked_select_official_validation_test_protocol"
NEXT_TODO = "compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-dir", type=Path, default=DEFAULT_REPAIR_DIR)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
                fields.append(key)
                seen.add(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def by_family(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("route_family")): row for row in rows}


def metric(summary: dict[str, Any], view_id: str, key: str) -> float:
    return as_float(summary.get("overall", {}).get("metrics", {}).get(view_id, {}).get(key))


def control(summary: dict[str, Any], comparison: str, key: str) -> float:
    return as_float(summary.get("overall", {}).get("controls", {}).get(comparison, {}).get(key))


def validate(
    *,
    repair_summary: dict[str, Any],
    review_summary: dict[str, Any],
    eval_manifest: dict[str, Any],
    repair_errors: list[dict[str, Any]],
    review_errors: list[dict[str, Any]],
    eval_errors: list[dict[str, Any]],
    predicate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if repair_summary.get("status") != EXPECTED_REPAIR_STATUS:
        errors.append({"error_type": "unexpected_repair_status", "actual": repair_summary.get("status")})
    if repair_summary.get("next_todo") != EXPECTED_CURRENT_TODO:
        errors.append({"error_type": "unexpected_repair_next_todo", "actual": repair_summary.get("next_todo")})
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review_summary.get("status")})
    if review_summary.get("next_todo") != EXPECTED_CURRENT_TODO:
        errors.append({"error_type": "unexpected_review_next_todo", "actual": review_summary.get("next_todo")})

    for name, rows in [("repair", repair_errors), ("review", review_errors), ("eval", eval_errors)]:
        if rows:
            errors.append({"error_type": f"{name}_validation_errors_present", "rows": len(rows)})

    if eval_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "eval_manifest_validation_errors", "actual": eval_manifest.get("validation_errors")})
    boundary = eval_manifest.get("boundary", {})
    for key in ["official_validation_usage", "official_test_usage", "paper_metric_produced", "p_obs_claim_enabled", "p_rel_claim_enabled"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "eval_boundary_not_false", "key": key, "actual": boundary.get(key)})

    families = by_family(review_summary.get("family_decisions", []))
    expected_status = {
        "relative_horizontal": "claim_supporting",
        "relative_vertical": "claim_supporting",
        "size_relative": "claim_supporting",
        "support_contact": "partial",
    }
    for family, status in expected_status.items():
        actual = families.get(family, {}).get("status")
        if actual != status:
            errors.append({"error_type": "unexpected_family_status", "family": family, "expected": status, "actual": actual})

    if metric(review_summary, "M4_TxG_compatibility", "auroc") < 0.95:
        errors.append({"error_type": "overall_m4_auroc_too_low", "actual": metric(review_summary, "M4_TxG_compatibility", "auroc")})
    if control(review_summary, "M4_vs_wrong_T", "delta_auroc") < 0.90:
        errors.append({"error_type": "wrong_t_control_delta_too_low", "actual": control(review_summary, "M4_vs_wrong_T", "delta_auroc")})
    if control(review_summary, "M4_vs_shuffled_G", "delta_auroc") < 0.40:
        errors.append({"error_type": "shuffled_g_control_delta_too_low", "actual": control(review_summary, "M4_vs_shuffled_G", "delta_auroc")})
    if len(predicate_rows) < 10:
        errors.append({"error_type": "predicate_review_incomplete", "rows": len(predicate_rows)})
    return errors


def family_claim_roles(review_summary: dict[str, Any]) -> list[dict[str, Any]]:
    families = by_family(review_summary.get("family_decisions", []))
    specs = [
        {
            "route_family": "relative_horizontal",
            "predicates": "left; right; front; behind",
            "route_type": "predicate_geometry_direction_route",
            "claim_role": "main_internal_compatibility_evidence",
            "allowed_claim": "Frame/direction relations require predicate-conditioned interpretation of horizontal geometry.",
            "paper_wording": "claim-supporting internal grouped-holdout evidence; not official validation/test.",
        },
        {
            "route_family": "relative_vertical",
            "predicates": "higher than; lower than",
            "route_type": "predicate_geometry_axis_order_route",
            "claim_role": "main_internal_compatibility_evidence",
            "allowed_claim": "Vertical order relations require predicate-conditioned interpretation of z-axis geometry.",
            "paper_wording": "claim-supporting internal grouped-holdout evidence after feature-extractor repair.",
        },
        {
            "route_family": "size_relative",
            "predicates": "bigger than; smaller than",
            "route_type": "predicate_geometry_size_route",
            "claim_role": "main_internal_compatibility_evidence",
            "allowed_claim": "Size-comparison relations require predicate-conditioned interpretation of geometry scale evidence.",
            "paper_wording": "claim-supporting internal grouped-holdout evidence; check official split before paper promotion.",
        },
        {
            "route_family": "support_contact",
            "predicates": "standing on; lying on",
            "route_type": "challenging_contact_pose_route",
            "claim_role": "partial_challenging_evidence",
            "allowed_claim": "Contact/pose relations show a weaker but nontrivial interaction signal and require richer local contact/pose evidence before solved-family claims.",
            "paper_wording": "partial/challenging evidence only; do not present as solved.",
        },
    ]
    rows: list[dict[str, Any]] = []
    for spec in specs:
        decision = families.get(spec["route_family"], {})
        rows.append(
            {
                **spec,
                "status": decision.get("status", ""),
                "heldout_rows": decision.get("heldout_rows", ""),
                "heldout_M4_auroc": decision.get("heldout_M4_auroc", ""),
                "heldout_M4_balanced_accuracy": decision.get("heldout_M4_balanced_accuracy", ""),
                "delta_vs_M1": decision.get("delta_vs_M1", ""),
                "delta_vs_M2": decision.get("delta_vs_M2", ""),
                "delta_vs_M3": decision.get("delta_vs_M3", ""),
                "delta_vs_wrong_T": decision.get("delta_vs_wrong_T", ""),
                "delta_vs_shuffled_G": decision.get("delta_vs_shuffled_G", ""),
            }
        )
    return rows


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "C1",
            "status": "allowed_hypothesis_stage_only",
            "claim": "Predicate-geometry compatibility C_e provides stronger internal grouped-holdout discrimination than T_e-only, G_e-only, plain T+G concatenation, wrong-T control, and shuffled-G control.",
            "scope": "H002 internal candidate pool; relative_horizontal, relative_vertical, size_relative as main internal evidence; support_contact partial.",
            "not_yet": "Not an official validation/test result and not a calibrated p_rel/p_obs reliability result.",
        },
        {
            "claim_id": "C2",
            "status": "allowed_hypothesis_stage_only",
            "claim": "Different relation families require different evidence routes instead of one fixed semantic-geometry fusion formula.",
            "scope": "Supported by strong clean comparison routes and partial support/contact behavior.",
            "not_yet": "Does not prove all 3DSSG relation families are covered.",
        },
        {
            "claim_id": "C3",
            "status": "allowed_hypothesis_stage_only",
            "claim": "support_contact is a challenging contact/pose route where interaction is useful but current evidence is insufficient for solved-family wording.",
            "scope": "standing on / lying on in the current internal candidate pool.",
            "not_yet": "No broad support/contact reliability claim; no supported by, attached to, hanging on, connected to claim.",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_claim": "H002 improves official 3DSSG/VL-SAT/Open3DSG validation or test relation prediction metrics.",
            "reason": "The current split is an internal candidate-pool grouped holdout, not official validation/test.",
            "required_before_unblock": "Official validation/test protocol, source adapter, fixed metric table, and leakage/shortcut audit.",
        },
        {
            "blocked_claim": "The method estimates calibrated relation reliability p_rel or selective observability p_obs.",
            "reason": "Current main metric evaluates C_e only; Z_e and Q_e are diagnostic and no calibration/selective-decision protocol has passed.",
            "required_before_unblock": "Separate p_rel/p_obs target, calibration metrics, abstention metrics, and official or independently audited targets.",
        },
        {
            "blocked_claim": "The method solves support/contact relations.",
            "reason": "support_contact M4 AUROC is partial and balanced accuracy remains low.",
            "required_before_unblock": "Richer contact/pose/visual evidence, predicate-level error taxonomy, and stronger heldout performance.",
        },
        {
            "blocked_claim": "The result generalizes to all 3DSSG relation types.",
            "reason": "Only four promoted route families are in the grouped run.",
            "required_before_unblock": "Route map coverage evaluation over remaining relation families or explicit paper scope restriction.",
        },
        {
            "blocked_claim": "Aggregate M4 AUROC alone establishes H002.",
            "reason": "Aggregate can hide family-specific behavior; family-level controls are the valid unit.",
            "required_before_unblock": "Report family-level and predicate-level results with controls.",
        },
    ]


def promotion_gap_rows() -> list[dict[str, Any]]:
    return [
        {
            "gap_id": "G1",
            "next_need": "official_validation_test_protocol",
            "why": "Current evidence is internal candidate-pool heldout only.",
            "deliverable": "Define official split usage, source candidate extraction, metric targets, and no-leakage contract.",
        },
        {
            "gap_id": "G2",
            "next_need": "paper_metric_freeze",
            "why": "Current metrics are hypothesis-stage diagnostics.",
            "deliverable": "Freeze paper-facing families, baselines, controls, K or threshold policy if applicable, and table wording.",
        },
        {
            "gap_id": "G3",
            "next_need": "support_contact_error_taxonomy",
            "why": "support_contact is partial and should explain residual ambiguity.",
            "deliverable": "Predicate-level failure taxonomy for lying on and standing on, with evidence gaps.",
        },
        {
            "gap_id": "G4",
            "next_need": "optional_p_rel_p_obs_protocol",
            "why": "Reliability and observability heads remain conceptual.",
            "deliverable": "Only pursue after C_e official evaluation if calibrated reliability/selective abstention becomes a paper claim.",
        },
    ]


def write_paper_wording(path: Path) -> None:
    text = """# H002 Claim Wording Draft

Recommended wording:

```text
Predicate-geometry compatibility can be learned for selected 3D Scene Graph
relation families when semantic content T_e and predicate-independent geometry
evidence G_e are separated. In internal grouped-holdout evaluation, the
compatibility route outperforms T_e-only, G_e-only, plain concatenation, and
wrong-predicate / shuffled-geometry controls for relative_horizontal,
relative_vertical, and size_relative relations. support_contact remains a
challenging contact/pose route where interaction is useful but current evidence
is not sufficient for solved-family claims.
```

Avoid:

```text
H002 solves relation reliability for all 3DSSG relations.
H002 produces paper-level official validation/test performance.
H002 estimates calibrated p_rel/p_obs.
support_contact is solved.
```
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_report(
    path: Path,
    *,
    summary: dict[str, Any],
    family_rows: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Repaired Grouped-Eval Claim Boundary Review",
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
        "## Decision",
        "",
        "The repaired grouped evaluation supports a hypothesis-stage `T_e x G_e` compatibility claim, but only with family-level boundaries.",
        "",
        "Allowed now:",
        "",
    ]
    for row in claims:
        lines.append(f"- `{row['claim_id']}`: {row['claim']}")
    lines.extend(
        [
            "",
            "Blocked now:",
            "",
        ]
    )
    for row in blocked:
        lines.append(f"- {row['blocked_claim']} Reason: {row['reason']}")
    lines.extend(
        [
            "",
            "## Family Claim Roles",
            "",
            "| Family | Status | Route type | Heldout M4 AUROC | Delta vs M1 | Delta vs M2 | Delta vs M3 | Delta vs wrong-T | Delta vs shuffled-G | Claim role |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in family_rows:
        lines.append(
            "| {route_family} | {status} | {route_type} | {heldout_M4_auroc:.6f} | {delta_vs_M1:.6f} | {delta_vs_M2:.6f} | {delta_vs_M3:.6f} | {delta_vs_wrong_T:.6f} | {delta_vs_shuffled_G:.6f} | {claim_role} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Promotion Gaps",
            "",
        ]
    )
    for row in gaps:
        lines.append(f"- `{row['gap_id']}` {row['next_need']}: {row['why']} Deliverable: {row['deliverable']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- official validation/test 사용 없음.",
            "- paper-level metric 생성 없음.",
            "- `C_e` claim만 hypothesis-stage로 허용.",
            "- `p_rel` / `p_obs` claim은 아직 blocked.",
            "- `Z_e` / `Q_e`는 diagnostic-only.",
            "- H001 artifact 수정 없음.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    repair_summary = read_json(args.repair_dir / "summary.json")
    review_summary = read_json(args.review_dir / "summary.json")
    eval_manifest = read_json(args.eval_dir / "eval_manifest.json")
    repair_errors = read_jsonl(args.repair_dir / "validation_errors.jsonl")
    review_errors = read_jsonl(args.review_dir / "validation_errors.jsonl")
    eval_errors = read_jsonl(args.eval_dir / "validation_errors.jsonl")
    predicate_rows = read_csv(args.review_dir / "predicate_review.csv")

    validation_errors = validate(
        repair_summary=repair_summary,
        review_summary=review_summary,
        eval_manifest=eval_manifest,
        repair_errors=repair_errors,
        review_errors=review_errors,
        eval_errors=eval_errors,
        predicate_rows=predicate_rows,
    )

    family_rows = family_claim_roles(review_summary)
    claims = claim_boundary_rows()
    blocked = blocked_claim_rows()
    gaps = promotion_gap_rows()

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "fix_claim_boundary_review_inputs",
        "next_todo": NEXT_TODO if not validation_errors else "fix_repaired_grouped_eval_claim_boundary_inputs",
        "validation_errors": len(validation_errors),
        "input_artifacts": {
            "repair_summary": rel_path(args.repair_dir / "summary.json"),
            "review_summary": rel_path(args.review_dir / "summary.json"),
            "eval_manifest": rel_path(args.eval_dir / "eval_manifest.json"),
        },
        "boundary": {
            "official_validation_usage": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "c_e_claim_enabled": not bool(validation_errors),
            "c_e_claim_scope": "hypothesis_stage_internal_candidate_pool_only",
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "z_e_q_e_main_model_enabled": False,
            "h001_artifacts_modified": False,
        },
        "overall_heldout": {
            "M1_T_semantic_only_auroc": metric(review_summary, "M1_T_semantic_only", "auroc"),
            "M2_G_geometry_only_auroc": metric(review_summary, "M2_G_geometry_only", "auroc"),
            "M3_T_plus_G_concat_auroc": metric(review_summary, "M3_T_plus_G_concat", "auroc"),
            "M4_TxG_compatibility_auroc": metric(review_summary, "M4_TxG_compatibility", "auroc"),
            "C1_wrong_T_control_auroc": metric(review_summary, "C1_wrong_T_control", "auroc"),
            "C2_shuffled_G_control_auroc": metric(review_summary, "C2_shuffled_G_control", "auroc"),
        },
        "family_claim_roles": family_rows,
        "allowed_claim_count": len(claims),
        "blocked_claim_count": len(blocked),
        "promotion_gap_count": len(gaps),
        "output_artifacts": {
            "claim_boundary": rel_path(args.output_dir / "claim_boundary.csv"),
            "family_claim_roles": rel_path(args.output_dir / "family_claim_roles.csv"),
            "blocked_claims": rel_path(args.output_dir / "blocked_claims.csv"),
            "promotion_gaps": rel_path(args.output_dir / "promotion_gaps.csv"),
            "paper_wording": rel_path(args.output_dir / "paper_wording.md"),
            "report": rel_path(args.output_dir / "report.md"),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "next_contract.json", {"next_todo": summary["next_todo"], "selected_path": summary["selected_path"]})
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "claim_boundary.csv", claims)
    write_csv(args.output_dir / "family_claim_roles.csv", family_rows)
    write_csv(args.output_dir / "blocked_claims.csv", blocked)
    write_csv(args.output_dir / "promotion_gaps.csv", gaps)
    write_paper_wording(args.output_dir / "paper_wording.md")
    write_report(args.output_dir / "report.md", summary=summary, family_rows=family_rows, claims=claims, blocked=blocked, gaps=gaps)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
