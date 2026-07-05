#!/usr/bin/env python3
"""Freeze the next source-reranking ablation expansion for H002."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
H2_ROOT = REPO_ROOT / "hypothesis/CAND-001/H002_factorized-relation-confidence"
EXPERIMENT_ROOT = REPO_ROOT / "experiments/H002_compatibility_routing"
INPUT_SYNC_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_paper_workspace_initial_draft_and_figure_table_sync"
MATERIALIZATION_ROOT = EXPERIMENT_ROOT / "source_reranking_materialization/latest"
EVALUATION_ROOT = EXPERIMENT_ROOT / "source_reranking_evaluation/latest"
CI_ROOT = EXPERIMENT_ROOT / "source_reranking_ci/latest"
OUTPUT_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update"

SCHEMA_VERSION = "h002_source_reranking_ablation_expansion_plan_after_route_goal_update_v1"
STATUS_READY = "h002_source_reranking_ablation_expansion_plan_after_route_goal_update_ready"
STATUS_ERROR = "h002_source_reranking_ablation_expansion_plan_after_route_goal_update_input_errors"
NEXT_TODO = "h002_source_reranking_ablation_expansion_implementation_after_plan"

EXPECTED_PREVIOUS_STATUS = "h002_paper_workspace_initial_draft_and_figure_table_sync_ready"
EXPECTED_PREVIOUS_NEXT_TODO = "h002_source_reranking_ablation_expansion_plan_after_route_goal_update"

REQUIRED_MATERIALIZATION_FILES = [
    "model_safe_ce_view.jsonl",
    "model_safe_geometry_only_view.jsonl",
    "source_rank_view.jsonl",
    "hidden_metric_manifest.jsonl",
]

REQUIRED_EVALUATION_FILES = [
    "score_condition_metrics.csv",
    "control_metrics.csv",
    "source_family_metrics.csv",
]

REQUIRED_EXISTING_SCORE_IDS = {
    "S0_source_score",
    "S1_Ce_only",
    "S2_source_x_Ce",
    "C1_source_x_shuffled_Ce",
    "C2_source_x_wrong_T_Ce",
}

PLANNED_SCORE_IDS = [
    "A1_source_x_G_only",
    "A2_source_x_TG_concat",
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def csv_inventory(path: Path) -> dict:
    rows = 0
    score_ids: set[str] = set()
    levels: set[str] = set()
    ks: set[str] = set()
    route_families: set[str] = set()
    source_ids: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            if row.get("score_id"):
                score_ids.add(row["score_id"])
            if row.get("level"):
                levels.add(row["level"])
            if row.get("K"):
                ks.add(row["K"])
            if row.get("route_family"):
                route_families.add(row["route_family"])
            if row.get("source_id"):
                source_ids.add(row["source_id"])
    return {
        "rows": rows,
        "score_ids": sorted(score_ids),
        "levels": sorted(levels),
        "K": sorted(ks, key=lambda x: int(x) if x.isdigit() else x),
        "route_families": sorted(route_families),
        "source_ids": sorted(source_ids),
    }


def validate() -> tuple[list[dict], dict]:
    errors: list[dict] = []
    inventory: dict = {}

    previous_summary_path = INPUT_SYNC_ROOT / "summary.json"
    if not previous_summary_path.exists():
        errors.append({"error_type": "missing_previous_summary", "path": rel(previous_summary_path)})
    else:
        previous_summary = read_json(previous_summary_path)
        inventory["previous_summary"] = {
            "status": previous_summary.get("status"),
            "validation_errors": previous_summary.get("validation_errors"),
            "next_todo": previous_summary.get("next_todo"),
            "goal": previous_summary.get("goal"),
            "current_main_success_route": previous_summary.get("current_main_success_route"),
        }
        if previous_summary.get("status") != EXPECTED_PREVIOUS_STATUS:
            errors.append(
                {
                    "error_type": "unexpected_previous_status",
                    "expected": EXPECTED_PREVIOUS_STATUS,
                    "actual": previous_summary.get("status"),
                }
            )
        if previous_summary.get("validation_errors") != 0:
            errors.append({"error_type": "previous_validation_errors_nonzero", "actual": previous_summary.get("validation_errors")})
        if previous_summary.get("next_todo") != EXPECTED_PREVIOUS_NEXT_TODO:
            errors.append(
                {
                    "error_type": "unexpected_previous_next_todo",
                    "expected": EXPECTED_PREVIOUS_NEXT_TODO,
                    "actual": previous_summary.get("next_todo"),
                }
            )

    materialization_counts: dict[str, int] = {}
    for filename in REQUIRED_MATERIALIZATION_FILES:
        path = MATERIALIZATION_ROOT / filename
        if not path.exists():
            errors.append({"error_type": "missing_materialization_file", "path": rel(path)})
            continue
        count = count_lines(path)
        materialization_counts[filename] = count
        if count <= 0:
            errors.append({"error_type": "empty_materialization_file", "path": rel(path)})
    inventory["materialization_row_counts"] = materialization_counts
    if materialization_counts:
        unique_counts = sorted(set(materialization_counts.values()))
        if len(unique_counts) != 1:
            errors.append({"error_type": "materialization_row_count_mismatch", "counts": materialization_counts})

    evaluation_inventory: dict[str, dict] = {}
    for filename in REQUIRED_EVALUATION_FILES:
        path = EVALUATION_ROOT / filename
        if not path.exists():
            errors.append({"error_type": "missing_evaluation_file", "path": rel(path)})
            continue
        inv = csv_inventory(path)
        evaluation_inventory[filename] = inv
        if inv["rows"] <= 0:
            errors.append({"error_type": "empty_evaluation_file", "path": rel(path)})
    inventory["evaluation_inventory"] = evaluation_inventory

    score_inv = evaluation_inventory.get("score_condition_metrics.csv", {})
    existing_score_ids = set(score_inv.get("score_ids", []))
    missing_score_ids = sorted(REQUIRED_EXISTING_SCORE_IDS - existing_score_ids)
    if missing_score_ids:
        errors.append({"error_type": "missing_required_existing_score_ids", "score_ids": missing_score_ids})
    inventory["existing_score_ids"] = sorted(existing_score_ids)
    inventory["planned_score_ids"] = PLANNED_SCORE_IDS

    ci_inventory: dict[str, str] = {}
    if CI_ROOT.exists():
        ci_inventory["root"] = rel(CI_ROOT)
        ci_inventory["status"] = "exists"
    else:
        ci_inventory["root"] = rel(CI_ROOT)
        ci_inventory["status"] = "missing_or_not_materialized"
    inventory["ci_inventory"] = ci_inventory

    return errors, inventory


def build_expanded_score_contract() -> list[dict]:
    return [
        {
            "score_id": "S0_source_score",
            "category": "existing_baseline",
            "formula": "normalized_source_score(Z_e)",
            "required_inputs": "source_rank_view.jsonl",
            "status": "already_evaluated",
            "paper_role": "source-only baseline",
            "claim_boundary": "baseline only",
        },
        {
            "score_id": "S1_Ce_only",
            "category": "existing_diagnostic",
            "formula": "C_e(T_e,G_e)",
            "required_inputs": "model_safe_ce_view.jsonl",
            "status": "already_evaluated",
            "paper_role": "compatibility-only diagnostic",
            "claim_boundary": "not deployable source reranking by itself",
        },
        {
            "score_id": "S2_source_x_Ce",
            "category": "existing_primary",
            "formula": "normalized_source_score(Z_e) * C_e(T_e,G_e)",
            "required_inputs": "source_rank_view.jsonl + model_safe_ce_view.jsonl",
            "status": "already_evaluated",
            "paper_role": "current primary reranking score",
            "claim_boundary": "main success currently limited to comparison compatibility route",
        },
        {
            "score_id": "S3_log_source_plus_Ce",
            "category": "existing_sensitivity",
            "formula": "log source utility plus compatibility utility",
            "required_inputs": "source_rank_view.jsonl + model_safe_ce_view.jsonl",
            "status": "already_evaluated",
            "paper_role": "sensitivity score",
            "claim_boundary": "appendix unless promoted after review",
        },
        {
            "score_id": "C1_source_x_shuffled_Ce",
            "category": "existing_control",
            "formula": "normalized_source_score(Z_e) * shuffled C_e",
            "required_inputs": "source_rank_view.jsonl + shuffled model_safe_ce_view.jsonl",
            "status": "already_evaluated",
            "paper_role": "geometry/compatibility provenance control",
            "claim_boundary": "should degrade relative to S2",
        },
        {
            "score_id": "C2_source_x_wrong_T_Ce",
            "category": "existing_control",
            "formula": "normalized_source_score(Z_e) * C_e(wrong T_e,G_e)",
            "required_inputs": "source_rank_view.jsonl + wrong-predicate C_e",
            "status": "already_evaluated",
            "paper_role": "predicate-compatibility control",
            "claim_boundary": "should degrade relative to S2",
        },
        {
            "score_id": "A1_source_x_G_only",
            "category": "planned_required_ablation",
            "formula": "normalized_source_score(Z_e) * G_only_score(G_e)",
            "required_inputs": "source_rank_view.jsonl + model_safe_geometry_only_view.jsonl",
            "status": "must_implement_before_broad_claim",
            "paper_role": "tests whether route gains are just geometry-only reranking",
            "claim_boundary": "required to defend factorized compatibility over geometry-only",
        },
        {
            "score_id": "A2_source_x_TG_concat",
            "category": "planned_required_ablation",
            "formula": "normalized_source_score(Z_e) * C_concat(T_e,G_e)",
            "required_inputs": "source_rank_view.jsonl + model_safe_ce_view.jsonl",
            "status": "must_implement_before_broad_claim",
            "paper_role": "tests whether interaction is needed beyond simple T_e/G_e concatenation",
            "claim_boundary": "required to defend compatibility module over plain fusion",
        },
    ]


def build_table_contract() -> list[dict]:
    return [
        {
            "table_id": "T_main_source_reranking",
            "placement": "main_or_late_main",
            "rows": "K=5,10,20,50,100",
            "required_score_ids": "S0_source_score,S2_source_x_Ce",
            "required_metrics": "Recall@K,Violation@K,Delta(S2-S0),bootstrap_CI",
            "promotion_rule": "primary comparison route only unless route expansion passes",
        },
        {
            "table_id": "T_ablation_absolute",
            "placement": "main_if_space_else_appendix",
            "rows": "score_id x K",
            "required_score_ids": "S0_source_score,S2_source_x_Ce,A1_source_x_G_only,A2_source_x_TG_concat,S3_log_source_plus_Ce",
            "required_metrics": "absolute Recall@K,absolute Violation@K,not_delta_only",
            "promotion_rule": "required before claiming compatibility beats fixed or simpler fusion",
        },
        {
            "table_id": "T_controls_absolute",
            "placement": "appendix_or_control_table",
            "rows": "control_score_id x K",
            "required_score_ids": "S1_Ce_only,C1_source_x_shuffled_Ce,C2_source_x_wrong_T_Ce",
            "required_metrics": "absolute Recall@K,absolute Violation@K,Delta_vs_S2",
            "promotion_rule": "controls must show provenance-sensitive degradation",
        },
        {
            "table_id": "T_family_ci",
            "placement": "appendix_required_for_claim_review",
            "rows": "source_id x route_family x K x score_id",
            "required_score_ids": "S0_source_score,S2_source_x_Ce,A1_source_x_G_only,A2_source_x_TG_concat",
            "required_metrics": "family-wise Recall@K CI,Violation@K CI,Delta CI",
            "promotion_rule": "prevents relative_horizontal or any large family from dominating aggregate claims",
        },
        {
            "table_id": "T_route_readiness",
            "placement": "main_analysis_or_limitations",
            "rows": "route family",
            "required_score_ids": "not_applicable",
            "required_metrics": "paper_status,required_evidence,current_boundary",
            "promotion_rule": "keeps broader framework claim separate from solved-route claim",
        },
    ]


def build_ci_contract() -> list[dict]:
    return [
        {
            "ci_target": "existing_primary_delta",
            "score_comparison": "S2_source_x_Ce - S0_source_score",
            "aggregation": "primary_success_weighted,primary_success_macro",
            "unit": "source/subgraph/family bootstrap",
            "status": "existing_ci_ready_but_should_be_linked_to_table",
        },
        {
            "ci_target": "planned_geometry_only_delta",
            "score_comparison": "S2_source_x_Ce - A1_source_x_G_only",
            "aggregation": "primary_success_weighted,primary_success_macro,source_family",
            "unit": "same bootstrap unit as source reranking CI",
            "status": "must_implement",
        },
        {
            "ci_target": "planned_concat_delta",
            "score_comparison": "S2_source_x_Ce - A2_source_x_TG_concat",
            "aggregation": "primary_success_weighted,primary_success_macro,source_family",
            "unit": "same bootstrap unit as source reranking CI",
            "status": "must_implement",
        },
        {
            "ci_target": "control_degradation",
            "score_comparison": "S2_source_x_Ce - C1/C2 controls",
            "aggregation": "primary_success_weighted,source_family",
            "unit": "same bootstrap unit as source reranking CI",
            "status": "must_extend_or_report_absolute_control_metrics",
        },
    ]


def build_implementation_plan() -> list[dict]:
    return [
        {
            "step": "1",
            "name": "runner_score_extension",
            "action": "extend source-reranking metric runner to emit A1_source_x_G_only and A2_source_x_TG_concat",
            "guardrail": "C_e and concat compatibility inputs must not include Z_e/source score",
        },
        {
            "step": "2",
            "name": "schema_audit_extension",
            "action": "audit that planned ablation features come from model-safe views and hidden labels stay hidden",
            "guardrail": "blocked-field hits must be zero",
        },
        {
            "step": "3",
            "name": "docker_metric_run",
            "action": "run expanded metric inside the H002 Docker workflow",
            "guardrail": "no host-only paper metric promotion",
        },
        {
            "step": "4",
            "name": "absolute_table_export",
            "action": "export absolute metrics for baseline, primary, ablations, and controls",
            "guardrail": "do not use delta-only control reporting",
        },
        {
            "step": "5",
            "name": "familywise_ci",
            "action": "bootstrap CI for family-wise and macro/weighted aggregates",
            "guardrail": "claim cannot depend only on aggregate point estimates",
        },
        {
            "step": "6",
            "name": "result_review",
            "action": "review whether compatibility still beats geometry-only and concat after controls",
            "guardrail": "broader framework wording remains blocked until review passes",
        },
    ]


def build_claim_boundary() -> list[dict]:
    return [
        {
            "claim": "comparison-route source reranking improves validation Recall/Violation over source baseline",
            "status": "currently_allowed_scoped",
            "condition": "use existing S0 vs S2 table with official validation caveat",
        },
        {
            "claim": "factorized compatibility is better than geometry-only reranking",
            "status": "blocked_until_A1_runs",
            "condition": "A1_source_x_G_only absolute metrics and CI must be reviewed",
        },
        {
            "claim": "factorized compatibility is better than simple T/G fusion",
            "status": "blocked_until_A2_runs",
            "condition": "A2_source_x_TG_concat absolute metrics and CI must be reviewed",
        },
        {
            "claim": "route-aware reliable 3D relation framework generalizes across relation families",
            "status": "framework_goal_not_completed_result",
            "condition": "requires family-wise route evidence beyond comparison route",
        },
        {
            "claim": "support/contact is solved",
            "status": "blocked",
            "condition": "support/contact remains hard-route failure taxonomy",
        },
        {
            "claim": "calibrated p_obs/p_rel reliability is solved",
            "status": "blocked",
            "condition": "calibration-upgrade review did not pass quantitative claim gate",
        },
    ]


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    errors, inventory = validate()
    status = STATUS_ERROR if errors else STATUS_READY

    expanded_score_contract = build_expanded_score_contract()
    table_contract = build_table_contract()
    ci_contract = build_ci_contract()
    implementation_plan = build_implementation_plan()
    claim_boundary = build_claim_boundary()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "previous_artifact": rel(INPUT_SYNC_ROOT),
        "materialization_root": rel(MATERIALIZATION_ROOT),
        "evaluation_root": rel(EVALUATION_ROOT),
        "ci_root": rel(CI_ROOT),
        "validation_errors": len(errors),
        "existing_score_ids": inventory.get("existing_score_ids", []),
        "planned_required_score_ids": PLANNED_SCORE_IDS,
        "decision": "freeze_source_reranking_ablation_expansion_before_broad_route_claim",
        "next_todo": NEXT_TODO if not errors else "fix_h002_source_reranking_ablation_expansion_plan_inputs",
        "inventory": inventory,
    }

    write_json(OUTPUT_ROOT / "summary.json", summary)
    write_csv(OUTPUT_ROOT / "expanded_score_contract.csv", expanded_score_contract)
    write_csv(OUTPUT_ROOT / "table_contract.csv", table_contract)
    write_csv(OUTPUT_ROOT / "ci_contract.csv", ci_contract)
    write_csv(OUTPUT_ROOT / "implementation_plan.csv", implementation_plan)
    write_csv(OUTPUT_ROOT / "claim_boundary.csv", claim_boundary)
    (OUTPUT_ROOT / "validation_errors.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in errors),
        encoding="utf-8",
    )

    report_lines = [
        "# H002 Source-Reranking Ablation Expansion Plan",
        "",
        "## Decision",
        "",
        f"- status: `{status}`",
        "- decision: freeze required ablations before broadening the route-aware framework claim",
        "- required new score IDs: `A1_source_x_G_only`, `A2_source_x_TG_concat`",
        "- required table change: report absolute control/ablation metrics, not only deltas",
        "- required uncertainty change: add family-wise CI for source/family/K cells",
        "",
        "## Why This Gate Exists",
        "",
        "The current H002 validation result supports the comparison-compatibility route, but a reviewer can still ask whether the gain is caused by a simpler geometry-only score or a plain concatenation baseline. This gate fixes those missing comparisons before the framework claim is broadened.",
        "",
        "## Next Implementation",
        "",
        f"- next_todo: `{summary['next_todo']}`",
        "- implement expanded metric runner outputs for `A1` and `A2`",
        "- regenerate absolute metric/control tables",
        "- regenerate bootstrap CI with ablation deltas",
        "",
        f"Validation errors: `{len(errors)}`",
    ]
    (OUTPUT_ROOT / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    stage_file = H2_ROOT / "compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update.md"
    stage_file.write_text(
        "\n".join(
            [
                "# compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update",
                "",
                f"status = {status}",
                "artifact_root = hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update/",
                "decision = freeze_source_reranking_ablation_expansion_before_broad_route_claim",
                "required_new_score_ids = A1_source_x_G_only,A2_source_x_TG_concat",
                "required_table_fix = absolute_control_and_ablation_metrics",
                "required_ci_fix = familywise_ci_for_ablation_deltas",
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
