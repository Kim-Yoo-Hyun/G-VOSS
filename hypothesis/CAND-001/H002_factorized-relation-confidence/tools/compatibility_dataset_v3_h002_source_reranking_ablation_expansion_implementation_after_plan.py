#!/usr/bin/env python3
"""Validate the implemented H002 source-reranking ablation expansion."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
H2_ROOT = REPO_ROOT / "hypothesis/CAND-001/H002_factorized-relation-confidence"
PLAN_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update"
EVAL_ROOT = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_evaluation/latest"
CI_ROOT = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_ci/latest"
OUTPUT_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan"

SCHEMA_VERSION = "h002_source_reranking_ablation_expansion_implementation_after_plan_v1"
STATUS_READY = "h002_source_reranking_ablation_expansion_implementation_after_plan_ready"
STATUS_ERROR = "h002_source_reranking_ablation_expansion_implementation_after_plan_input_errors"
NEXT_TODO = "h002_source_reranking_ablation_expansion_result_review_after_implementation"

EXPECTED_PLAN_STATUS = "h002_source_reranking_ablation_expansion_plan_after_route_goal_update_ready"
EXPECTED_METRIC_STATUS = "h002_source_reranking_metric_runner_ready"
EXPECTED_CI_STATUS = "h002_source_reranking_bootstrap_ci_ready"
REQUIRED_SCORE_IDS = {
    "S0_source_score",
    "S1_Ce_only",
    "S2_source_x_Ce",
    "S3_log_source_plus_Ce",
    "C1_source_x_shuffled_Ce",
    "C2_source_x_wrong_T_Ce",
    "A1_source_x_G_only",
    "A2_source_x_TG_concat",
}
REQUIRED_CI_SCORE_IDS = REQUIRED_SCORE_IDS - {"S3_log_source_plus_Ce"}


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


def collect_score_ids(rows: list[dict[str, str]], key: str = "score_id") -> set[str]:
    return {row[key] for row in rows if row.get(key)}


def row_by(rows: list[dict[str, str]], **kwargs: str) -> dict[str, str] | None:
    for row in rows:
        if all(str(row.get(k)) == str(v) for k, v in kwargs.items()):
            return row
    return None


def validate() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, list[dict[str, str]]]]:
    errors: list[dict[str, Any]] = []
    inventory: dict[str, Any] = {}
    tables: dict[str, list[dict[str, str]]] = {}

    plan_summary_path = PLAN_ROOT / "summary.json"
    metric_manifest_path = EVAL_ROOT / "metric_manifest.json"
    score_manifest_path = EVAL_ROOT / "score_manifest.json"
    ci_summary_path = CI_ROOT / "summary.json"
    required_paths = [
        plan_summary_path,
        metric_manifest_path,
        score_manifest_path,
        ci_summary_path,
        EVAL_ROOT / "absolute_primary_metrics.csv",
        EVAL_ROOT / "control_metrics.csv",
        EVAL_ROOT / "score_condition_metrics.csv",
        EVAL_ROOT / "source_family_metrics.csv",
        CI_ROOT / "main_reranking_ci.csv",
        CI_ROOT / "main_reranking_delta_ci.csv",
        CI_ROOT / "familywise_reranking_ci.csv",
        CI_ROOT / "familywise_reranking_delta_ci.csv",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append({"error_type": "missing_required_output", "path": rel(path)})

    if errors:
        return errors, inventory, tables

    plan_summary = read_json(plan_summary_path)
    metric_manifest = read_json(metric_manifest_path)
    score_manifest = read_json(score_manifest_path)
    ci_summary = read_json(ci_summary_path)
    inventory["plan_summary"] = plan_summary
    inventory["metric_status"] = metric_manifest.get("status")
    inventory["ci_status"] = ci_summary.get("status")
    inventory["metric_row_counts"] = metric_manifest.get("row_counts", {})
    inventory["ci_unit_count"] = ci_summary.get("unit_count")
    inventory["familywise_unit_scopes"] = ci_summary.get("familywise_unit_scopes")

    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_nonzero", "actual": plan_summary.get("validation_errors")})
    if metric_manifest.get("status") != EXPECTED_METRIC_STATUS:
        errors.append({"error_type": "unexpected_metric_status", "actual": metric_manifest.get("status")})
    if metric_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "metric_validation_errors_nonzero", "actual": metric_manifest.get("validation_errors")})
    if ci_summary.get("status") != EXPECTED_CI_STATUS:
        errors.append({"error_type": "unexpected_ci_status", "actual": ci_summary.get("status")})
    if ci_summary.get("validation_errors") != 0:
        errors.append({"error_type": "ci_validation_errors_nonzero", "actual": ci_summary.get("validation_errors")})
    if ci_summary.get("point_metric_mismatch_count") != 0:
        errors.append({"error_type": "ci_point_metric_mismatch", "actual": ci_summary.get("point_metric_mismatch_count")})

    score_ids = set(score_manifest.get("score_ids", []))
    missing_scores = sorted(REQUIRED_SCORE_IDS - score_ids)
    if missing_scores:
        errors.append({"error_type": "missing_required_score_ids_in_score_manifest", "score_ids": missing_scores})
    if set(score_manifest.get("required_ablation_score_ids", [])) != {"A1_source_x_G_only", "A2_source_x_TG_concat"}:
        errors.append(
            {
                "error_type": "required_ablation_score_ids_not_frozen",
                "actual": score_manifest.get("required_ablation_score_ids"),
            }
        )

    boundary = metric_manifest.get("boundary", {})
    for key in ["A1_source_x_G_only_added", "A2_source_x_TG_concat_added", "A1_A2_fit_on_internal_train_only", "A1_A2_use_Z_e_only_at_final_reranking"]:
        if boundary.get(key) is not True:
            errors.append({"error_type": "metric_boundary_flag_not_true", "flag": key, "actual": boundary.get(key)})

    tables["absolute_primary"] = read_csv(EVAL_ROOT / "absolute_primary_metrics.csv")
    tables["control"] = read_csv(EVAL_ROOT / "control_metrics.csv")
    tables["source_family"] = read_csv(EVAL_ROOT / "source_family_metrics.csv")
    tables["main_ci"] = read_csv(CI_ROOT / "main_reranking_ci.csv")
    tables["main_delta_ci"] = read_csv(CI_ROOT / "main_reranking_delta_ci.csv")
    tables["familywise_ci"] = read_csv(CI_ROOT / "familywise_reranking_ci.csv")
    tables["familywise_delta_ci"] = read_csv(CI_ROOT / "familywise_reranking_delta_ci.csv")

    if collect_score_ids(tables["absolute_primary"]) != REQUIRED_SCORE_IDS:
        errors.append({"error_type": "absolute_primary_score_id_set_mismatch", "actual": sorted(collect_score_ids(tables["absolute_primary"]))})
    if collect_score_ids(tables["main_ci"]) != REQUIRED_CI_SCORE_IDS:
        errors.append({"error_type": "main_ci_score_id_set_mismatch", "actual": sorted(collect_score_ids(tables["main_ci"]))})
    for expected_name, expected_count in [
        ("absolute_primary", 40),
        ("control", 30),
        ("source_family", 400),
        ("main_ci", 70),
        ("main_delta_ci", 60),
        ("familywise_ci", 280),
        ("familywise_delta_ci", 240),
    ]:
        actual = len(tables[expected_name])
        inventory[f"{expected_name}_rows"] = actual
        if actual != expected_count:
            errors.append({"error_type": "unexpected_table_row_count", "table": expected_name, "actual": actual, "expected": expected_count})

    return errors, inventory, tables


def build_key_metric_rows(tables: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for score_id in [
        "S0_source_score",
        "S2_source_x_Ce",
        "A1_source_x_G_only",
        "A2_source_x_TG_concat",
        "C1_source_x_shuffled_Ce",
        "C2_source_x_wrong_T_Ce",
        "S1_Ce_only",
    ]:
        for k in ["5", "10", "20", "50", "100"]:
            row = row_by(tables["absolute_primary"], score_id=score_id, K=k)
            if not row:
                continue
            out.append(
                {
                    "score_id": score_id,
                    "K": k,
                    "Recall@K": row.get("Recall@K"),
                    "Violation@K": row.get("Violation@K"),
                    "gt_selected": row.get("gt_selected"),
                    "violation_count": row.get("violation_count"),
                    "violation_denominator": row.get("violation_denominator"),
                }
            )
    return out


def build_delta_snapshot(tables: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    comparisons = {
        "S2_source_x_Ce_minus_S0_source_score",
        "S2_source_x_Ce_minus_A1_source_x_G_only",
        "S2_source_x_Ce_minus_A2_source_x_TG_concat",
        "S2_source_x_Ce_minus_C1_source_x_shuffled_Ce",
        "S2_source_x_Ce_minus_C2_source_x_wrong_T_Ce",
    }
    out: list[dict[str, Any]] = []
    for row in tables["main_delta_ci"]:
        if row.get("comparison") in comparisons and row.get("K") in {"10", "20", "50"}:
            out.append(row)
    return out


def build_familywise_snapshot(tables: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in tables["familywise_delta_ci"]:
        if (
            row.get("comparison") in {"S2_source_x_Ce_minus_A1_source_x_G_only", "S2_source_x_Ce_minus_A2_source_x_TG_concat"}
            and row.get("metric") == "Violation@K"
            and row.get("K") == "20"
        ):
            out.append(row)
    return out


def judge(tables: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for baseline in ["A1_source_x_G_only", "A2_source_x_TG_concat"]:
        for metric in ["Recall@K", "Violation@K"]:
            passed_all = True
            values: list[dict[str, Any]] = []
            for k in ["10", "20", "50"]:
                row = row_by(tables["main_delta_ci"], comparison=f"S2_source_x_Ce_minus_{baseline}", metric=metric, K=k)
                if not row:
                    passed_all = False
                    continue
                low = f(row, "ci_low_95")
                high = f(row, "ci_high_95")
                point = f(row, "point_delta")
                if metric == "Recall@K":
                    passed = low is not None and low > 0
                else:
                    passed = high is not None and high < 0
                passed_all = passed_all and passed
                values.append({"K": k, "point_delta": point, "ci_low_95": low, "ci_high_95": high, "passed": passed})
            checks.append({"baseline": baseline, "metric": metric, "K_scope": "10,20,50", "passed_all": passed_all, "values": values})
    return {
        "primary_ablation_ci_pass": all(check["passed_all"] for check in checks),
        "checks": checks,
        "interpretation": "S2 outperforms geometry-only and plain concat on primary comparison route if all checks pass.",
    }


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    errors, inventory, tables = validate()
    status = STATUS_ERROR if errors else STATUS_READY

    key_rows = build_key_metric_rows(tables) if tables else []
    delta_rows = build_delta_snapshot(tables) if tables else []
    familywise_rows = build_familywise_snapshot(tables) if tables else []
    judgment = judge(tables) if tables else {"primary_ablation_ci_pass": False, "checks": []}

    if tables and not judgment["primary_ablation_ci_pass"]:
        errors.append({"error_type": "primary_ablation_ci_gate_failed", "judgment": judgment})
        status = STATUS_ERROR

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_metric_root": rel(EVAL_ROOT),
        "runtime_ci_root": rel(CI_ROOT),
        "validation_errors": len(errors),
        "implementation_outputs_ready": len(errors) == 0,
        "primary_ablation_ci_pass": judgment.get("primary_ablation_ci_pass"),
        "required_score_ids": sorted(REQUIRED_SCORE_IDS),
        "required_ci_score_ids": sorted(REQUIRED_CI_SCORE_IDS),
        "inventory": inventory,
        "judgment": judgment,
        "next_todo": NEXT_TODO if not errors else "fix_h002_source_reranking_ablation_expansion_implementation",
    }

    write_json(OUTPUT_ROOT / "summary.json", summary)
    write_csv(OUTPUT_ROOT / "key_absolute_primary_metrics.csv", key_rows)
    write_csv(OUTPUT_ROOT / "key_delta_ci.csv", delta_rows)
    write_csv(OUTPUT_ROOT / "familywise_delta_snapshot.csv", familywise_rows)
    write_json(OUTPUT_ROOT / "judgment.json", judgment)
    (OUTPUT_ROOT / "validation_errors.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in errors),
        encoding="utf-8",
    )

    report_lines = [
        "# H002 Source-Reranking Ablation Expansion Implementation",
        "",
        "## Decision",
        "",
        f"- status: `{status}`",
        f"- validation_errors: `{len(errors)}`",
        f"- primary_ablation_ci_pass: `{judgment.get('primary_ablation_ci_pass')}`",
        "- implemented score IDs: `A1_source_x_G_only`, `A2_source_x_TG_concat`",
        "- runtime metric root: `experiments/H002_compatibility_routing/source_reranking_evaluation/latest/`",
        "- runtime CI root: `experiments/H002_compatibility_routing/source_reranking_ci/latest/`",
        "",
        "## Interpretation",
        "",
        "`S2_source_x_Ce` is no longer only compared with the source baseline. It is now also compared with source x geometry-only and source x plain T/G concat ablations under absolute metrics and bootstrap CI.",
        "",
        "This implementation supports a scoped claim that the primary comparison-route gain is not reducible to geometry-only reranking or simple T/G concatenation. Broader all-relation claims still require the next result-review gate.",
        "",
        f"Next TODO: `{summary['next_todo']}`",
    ]
    (OUTPUT_ROOT / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    stage_file = H2_ROOT / "compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan.md"
    stage_file.write_text(
        "\n".join(
            [
                "# compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan",
                "",
                f"status = {status}",
                "artifact_root = hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/",
                "implemented_score_ids = A1_source_x_G_only,A2_source_x_TG_concat",
                "runtime_metric_root = experiments/H002_compatibility_routing/source_reranking_evaluation/latest/",
                "runtime_ci_root = experiments/H002_compatibility_routing/source_reranking_ci/latest/",
                f"primary_ablation_ci_pass = {judgment.get('primary_ablation_ci_pass')}",
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
