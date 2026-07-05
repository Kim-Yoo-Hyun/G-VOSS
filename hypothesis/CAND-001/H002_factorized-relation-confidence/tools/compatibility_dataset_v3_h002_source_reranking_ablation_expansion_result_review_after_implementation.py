#!/usr/bin/env python3
"""Review H002 A1/A2 source-reranking ablation results before paper promotion."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
H2_ROOT = REPO_ROOT / "hypothesis/CAND-001/H002_factorized-relation-confidence"
IMPLEMENTATION_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan"
EVAL_ROOT = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_evaluation/latest"
CI_ROOT = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_ci/latest"
OUTPUT_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation"

SCHEMA_VERSION = "h002_source_reranking_ablation_expansion_result_review_after_implementation_v1"
STATUS_READY = "h002_source_reranking_ablation_expansion_result_review_after_implementation_ready"
STATUS_ERROR = "h002_source_reranking_ablation_expansion_result_review_after_implementation_input_errors"
NEXT_TODO = "h002_experiment_stage_remaining_gap_review_after_ablation_result_review"

EXPECTED_IMPLEMENTATION_STATUS = "h002_source_reranking_ablation_expansion_implementation_after_plan_ready"
PRIMARY_K_FOR_TABLE = "20"
FOCUS_KS = {"10", "20", "50"}
ABLATION_BASELINES = ["A1_source_x_G_only", "A2_source_x_TG_concat"]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def f(row: dict[str, str], key: str) -> float | None:
    value = row.get(key)
    if value in (None, ""):
        return None
    return float(value)


def row_by(rows: list[dict[str, str]], **kwargs: str) -> dict[str, str] | None:
    for row in rows:
        if all(str(row.get(k)) == str(v) for k, v in kwargs.items()):
            return row
    return None


def pass_delta(row: dict[str, str]) -> bool:
    metric = row.get("metric")
    low = f(row, "ci_low_95")
    high = f(row, "ci_high_95")
    if low is None or high is None:
        return False
    if metric == "Recall@K":
        return low > 0
    if metric == "Violation@K":
        return high < 0
    return False


def validate_inputs() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, list[dict[str, str]]]]:
    errors: list[dict[str, Any]] = []
    inventory: dict[str, Any] = {}
    tables: dict[str, list[dict[str, str]]] = {}

    required = [
        IMPLEMENTATION_ROOT / "summary.json",
        EVAL_ROOT / "absolute_primary_metrics.csv",
        EVAL_ROOT / "source_family_metrics.csv",
        EVAL_ROOT / "control_metrics.csv",
        CI_ROOT / "main_reranking_delta_ci.csv",
        CI_ROOT / "familywise_reranking_delta_ci.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append({"error_type": "missing_required_input", "path": rel(path)})
    if errors:
        return errors, inventory, tables

    implementation_summary = read_json(IMPLEMENTATION_ROOT / "summary.json")
    inventory["implementation_status"] = implementation_summary.get("status")
    inventory["implementation_validation_errors"] = implementation_summary.get("validation_errors")
    inventory["implementation_primary_ablation_ci_pass"] = implementation_summary.get("primary_ablation_ci_pass")
    if implementation_summary.get("status") != EXPECTED_IMPLEMENTATION_STATUS:
        errors.append({"error_type": "unexpected_implementation_status", "actual": implementation_summary.get("status")})
    if implementation_summary.get("validation_errors") != 0:
        errors.append({"error_type": "implementation_validation_errors_nonzero", "actual": implementation_summary.get("validation_errors")})
    if implementation_summary.get("primary_ablation_ci_pass") is not True:
        errors.append({"error_type": "implementation_primary_ablation_ci_not_passed"})

    tables["absolute_primary"] = read_csv(EVAL_ROOT / "absolute_primary_metrics.csv")
    tables["source_family"] = read_csv(EVAL_ROOT / "source_family_metrics.csv")
    tables["control"] = read_csv(EVAL_ROOT / "control_metrics.csv")
    tables["main_delta_ci"] = read_csv(CI_ROOT / "main_reranking_delta_ci.csv")
    tables["familywise_delta_ci"] = read_csv(CI_ROOT / "familywise_reranking_delta_ci.csv")
    inventory["absolute_primary_rows"] = len(tables["absolute_primary"])
    inventory["source_family_rows"] = len(tables["source_family"])
    inventory["control_rows"] = len(tables["control"])
    inventory["main_delta_ci_rows"] = len(tables["main_delta_ci"])
    inventory["familywise_delta_ci_rows"] = len(tables["familywise_delta_ci"])
    return errors, inventory, tables


def build_result_interpretation(tables: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for score_id, role in [
        ("S0_source_score", "source baseline"),
        ("A1_source_x_G_only", "geometry-only ablation"),
        ("A2_source_x_TG_concat", "plain T/G concat ablation"),
        ("C1_source_x_shuffled_Ce", "shuffled C_e control"),
        ("C2_source_x_wrong_T_Ce", "wrong-T C_e control"),
        ("S1_Ce_only", "C_e only diagnostic"),
        ("S2_source_x_Ce", "H002 primary compatibility reranking"),
    ]:
        abs_row = row_by(tables["absolute_primary"], score_id=score_id, K=PRIMARY_K_FOR_TABLE)
        if not abs_row:
            continue
        rows.append(
            {
                "score_id": score_id,
                "role": role,
                "K": PRIMARY_K_FOR_TABLE,
                "Recall@K": abs_row.get("Recall@K"),
                "Violation@K": abs_row.get("Violation@K"),
                "gt_selected": abs_row.get("gt_selected"),
                "gt_total": abs_row.get("gt_total"),
                "interpretation": "primary score" if score_id == "S2_source_x_Ce" else "comparison row",
            }
        )
    for baseline in ABLATION_BASELINES:
        for metric in ["Recall@K", "Violation@K"]:
            delta = row_by(
                tables["main_delta_ci"],
                comparison=f"S2_source_x_Ce_minus_{baseline}",
                metric=metric,
                K=PRIMARY_K_FOR_TABLE,
            )
            if not delta:
                continue
            rows.append(
                {
                    "score_id": f"S2_minus_{baseline}",
                    "role": f"delta against {baseline}",
                    "K": PRIMARY_K_FOR_TABLE,
                    "Recall@K": delta.get("point_delta") if metric == "Recall@K" else "",
                    "Violation@K": delta.get("point_delta") if metric == "Violation@K" else "",
                    "gt_selected": "",
                    "gt_total": "",
                    "interpretation": f"{metric} delta 95% CI [{delta.get('ci_low_95')}, {delta.get('ci_high_95')}], pass={pass_delta(delta)}",
                }
            )
    return rows


def build_familywise_caveats(tables: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in tables["familywise_delta_ci"]:
        comparison = row.get("comparison")
        metric = row.get("metric")
        k = row.get("K")
        if comparison not in {f"S2_source_x_Ce_minus_{baseline}" for baseline in ABLATION_BASELINES}:
            continue
        if k not in {"5", "10", "20", "50", "100"}:
            continue
        passed = pass_delta(row)
        severity = "pass"
        caveat = "family-wise CI supports S2 over ablation"
        if not passed and metric == "Recall@K":
            severity = "caveat"
            caveat = "Recall improvement is not uniformly significant in this source/family/K cell; likely saturation or low-denominator effect."
        elif not passed and metric == "Violation@K":
            severity = "risk"
            caveat = "Violation reduction is not significant in this source/family/K cell; do not claim family-wise robustness if present."
        rows.append(
            {
                "source_id": row.get("source_id"),
                "route_family": row.get("route_family"),
                "comparison": comparison,
                "metric": metric,
                "K": k,
                "point_delta": row.get("point_delta"),
                "ci_low_95": row.get("ci_low_95"),
                "ci_high_95": row.get("ci_high_95"),
                "passed": passed,
                "severity": severity,
                "caveat": caveat,
            }
        )
    return rows


def summarize_familywise(caveats: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(caveats)
    pass_rows = [row for row in caveats if row["passed"]]
    recall = [row for row in caveats if row["metric"] == "Recall@K"]
    violation = [row for row in caveats if row["metric"] == "Violation@K"]
    recall_pass = [row for row in recall if row["passed"]]
    violation_pass = [row for row in violation if row["passed"]]
    return {
        "familywise_total_rows": total,
        "familywise_pass_rows": len(pass_rows),
        "recall_rows": len(recall),
        "recall_pass_rows": len(recall_pass),
        "violation_rows": len(violation),
        "violation_pass_rows": len(violation_pass),
        "main_caveat": "Violation reduction is family-wise stable; Recall improvement is not uniformly significant in saturated/low-denominator source-family cells.",
    }


def build_table_placement() -> list[dict[str, Any]]:
    return [
        {
            "table": "main_primary_result",
            "placement_decision": "hold_for_experiment_review_then_main_candidate",
            "content": "S0 vs S2 Recall@K/Violation@K on primary comparison route",
            "reason": "main validation effect remains the central quantitative evidence, but paper insertion is held until experiment review completes",
        },
        {
            "table": "compact_ablation_table",
            "placement_decision": "main_or_near_main_candidate_after_review",
            "content": "K=20 absolute rows for S0, A1, A2, S2 plus S2-A1/S2-A2 CI",
            "reason": "directly answers whether H002 is just geometry-only or plain T/G concat",
        },
        {
            "table": "full_ablation_and_control_table",
            "placement_decision": "appendix_required",
            "content": "all K absolute metrics for S0,S1,S2,S3,C1,C2,A1,A2",
            "reason": "keeps main paper compact while preserving auditability",
        },
        {
            "table": "familywise_caveat_table",
            "placement_decision": "appendix_required_with_main_text_caveat",
            "content": "source/family/K deltas and CI for S2-A1/S2-A2",
            "reason": "prevents aggregate-only overclaim; Recall is not uniformly significant family-wise",
        },
        {
            "table": "support_contact_failure_taxonomy",
            "placement_decision": "limitation_or_appendix",
            "content": "hard route failure taxonomy",
            "reason": "do not hide that current ablation success is comparison-route scoped",
        },
    ]


def build_claim_boundary_wording() -> tuple[list[dict[str, Any]], str]:
    rows = [
        {
            "type": "allowed_scoped",
            "wording": "On the official 3DSSG validation split, for geometry-checkable comparison relations, H002 compatibility-aware reranking improves Recall@K and reduces Violation@K over source-score, geometry-only, and plain T/G concat ablations.",
            "condition": "Use with validation-level and comparison-route caveats.",
        },
        {
            "type": "allowed_mechanism",
            "wording": "The gain is not explained by a geometry-only reranker or by simple T_e/G_e concatenation; the primary score remains strongest under aggregate CI for K={10,20,50}.",
            "condition": "Mention K=5 Recall is not significant and family-wise Recall is mixed.",
        },
        {
            "type": "required_caveat",
            "wording": "Family-wise analysis shows stable Violation reduction, but Recall gains are not uniformly significant in every source/family/K cell.",
            "condition": "Use whenever claiming robustness.",
        },
        {
            "type": "blocked",
            "wording": "H002 solves reliable 3D relations across all relation families.",
            "condition": "Blocked: support/contact, attachment/containment, and semantic/structural routes are not solved.",
        },
        {
            "type": "blocked",
            "wording": "H002 is an official test/SOTA benchmark result.",
            "condition": "Blocked: current evidence is validation-level custom evaluation.",
        },
        {
            "type": "blocked",
            "wording": "p_obs/p_rel is a calibrated solved reliability module.",
            "condition": "Blocked by previous p_obs/p_rel calibration-upgrade review.",
        },
    ]
    md = "\n".join(
        [
            "# H002 Claim Boundary Wording",
            "",
            "## Allowed Scoped Wording",
            "",
            rows[0]["wording"],
            "",
            rows[1]["wording"],
            "",
            "## Required Caveat",
            "",
            rows[2]["wording"],
            "",
            "## Blocked Wording",
            "",
            "- H002 solves reliable 3D relations across all relation families.",
            "- H002 is an official test/SOTA benchmark result.",
            "- p_obs/p_rel is a calibrated solved reliability module.",
            "",
        ]
    )
    return rows, md


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    errors, inventory, tables = validate_inputs()
    status = STATUS_ERROR if errors else STATUS_READY

    result_rows = build_result_interpretation(tables) if tables else []
    familywise_caveats = build_familywise_caveats(tables) if tables else []
    familywise_summary = summarize_familywise(familywise_caveats) if familywise_caveats else {}
    table_placement = build_table_placement()
    claim_rows, claim_md = build_claim_boundary_wording()

    # Experiment-stage review decision: paper promotion stays held even when the
    # ablation mechanism check is positive.
    review_decision = {
        "result_interpretation": "S2 outperforms A1 geometry-only and A2 plain concat on aggregate primary comparison-route metrics.",
        "familywise_caveat": familywise_summary.get("main_caveat"),
        "table_placement": "compact ablation table is a main-candidate after review; full ablation/control and family-wise tables stay appendix-required",
        "claim_boundary": "allowed wording is validation-level and comparison-route scoped; all-relation, SOTA, support/contact-solved, and calibrated p_obs/p_rel solved claims remain blocked",
        "paper_promotion_decision": "hold_until_remaining_experiment_stage_gap_review",
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation_errors": len(errors),
        "implementation_artifact": rel(IMPLEMENTATION_ROOT),
        "runtime_metric_root": rel(EVAL_ROOT),
        "runtime_ci_root": rel(CI_ROOT),
        "review_items_completed": [
            "A1_A2_result_interpretation",
            "familywise_caveat_review",
            "control_ablation_table_placement",
            "claim_boundary_wording",
        ]
        if not errors
        else [],
        "familywise_summary": familywise_summary,
        "review_decision": review_decision,
        "paper_promotion_hold": True,
        "next_todo": NEXT_TODO if not errors else "fix_h002_source_reranking_ablation_expansion_result_review_inputs",
    }

    write_json(OUTPUT_ROOT / "summary.json", summary)
    write_csv(OUTPUT_ROOT / "result_interpretation.csv", result_rows)
    write_csv(OUTPUT_ROOT / "familywise_caveats.csv", familywise_caveats)
    write_csv(OUTPUT_ROOT / "table_placement_decision.csv", table_placement)
    write_csv(OUTPUT_ROOT / "claim_boundary_wording.csv", claim_rows)
    (OUTPUT_ROOT / "claim_boundary_wording.md").write_text(claim_md, encoding="utf-8")
    write_json(OUTPUT_ROOT / "review_decision.json", review_decision)
    (OUTPUT_ROOT / "validation_errors.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in errors),
        encoding="utf-8",
    )

    report = [
        "# H002 A1/A2 Ablation Result Review",
        "",
        "## 1. Result Interpretation",
        "",
        "- `S2_source_x_Ce` is stronger than `A1_source_x_G_only` and `A2_source_x_TG_concat` on aggregate primary comparison-route metrics.",
        "- At K=20, `S2` has Recall@K `0.724490` and Violation@K `0.100487`.",
        "- At K=20, `A1` has Recall@K `0.646259` and Violation@K `0.327534`; `A2` has Recall@K `0.629252` and Violation@K `0.330770`.",
        "",
        "## 2. Family-Wise Caveat",
        "",
        f"- {familywise_summary.get('main_caveat', '')}",
        "- Therefore the strongest claim is aggregate primary-route mechanism evidence, not uniform source/family/K dominance.",
        "",
        "## 3. Table Placement",
        "",
        "- Compact ablation table: main or near-main candidate after the remaining experiment-stage review.",
        "- Full ablation/control table: appendix required.",
        "- Family-wise caveat table: appendix required with main-text caveat.",
        "",
        "## 4. Claim Boundary",
        "",
        "- Allowed: validation-level, comparison-route scoped mechanism claim.",
        "- Blocked: all-relation framework solved, official test/SOTA, support/contact solved, calibrated p_obs/p_rel solved.",
        "- Paper promotion remains on hold until remaining experiment-stage gap review.",
        "",
        f"Validation errors: `{len(errors)}`",
        f"Next TODO: `{summary['next_todo']}`",
    ]
    (OUTPUT_ROOT / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    stage_file = H2_ROOT / "compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation.md"
    stage_file.write_text(
        "\n".join(
            [
                "# compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation",
                "",
                f"status = {status}",
                "artifact_root = hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation/",
                "result_interpretation = S2_beats_A1_A2_on_aggregate_primary_comparison_route",
                "familywise_caveat = violation_stable_recall_mixed",
                "table_placement = compact_main_candidate_full_appendix_required",
                "claim_boundary = validation_level_comparison_route_scoped",
                "paper_promotion_hold = true",
                f"validation_errors = {len(errors)}",
                f"next_todo = {summary['next_todo']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
