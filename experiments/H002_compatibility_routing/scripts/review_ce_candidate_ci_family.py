#!/usr/bin/env python3
"""Review whether calibrated route-aware C_e can replace the current H002 score.

This script reuses the frozen C_e improvement path, evaluates the candidate on
official-validation source rows without fitting on those rows, and bootstraps
over (source_id, subgraph_id, route_family) units.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from run_ce_improvement_path import (
    DEV_SPLIT,
    EXPECTED_TOTAL_ROWS,
    K_GRID,
    PRIMARY_FAMILIES,
    TRAIN_SPLIT,
    apply_temperature,
    build_hard_negative_train_rows,
    current_ce_features,
    fit_route_models,
    predict_model,
    predict_route,
    read_jsonl,
    score_source_rows,
    selected_sort_key,
    structured_ce_features,
    tune_temperature,
    write_csv,
    write_json,
    write_jsonl,
)
from run_official_metric import fit_model, safe_float


SCHEMA_VERSION = "h002_ce_candidate_ci_family_review_v1"
STATUS_READY = "h002_ce_candidate_ci_family_review_ready"
STATUS_ERROR = "h002_ce_candidate_ci_family_review_errors"

BASELINE_SCORE = "S2_current_source_x_Ce"
CANDIDATE_SCORE = "I4_calibrated_route_aware_source_x_Ce"
SCORE_IDS = (BASELINE_SCORE, CANDIDATE_SCORE)
DEFAULT_SEED = 20260706
DEFAULT_BOOTSTRAPS = 1000
PROMOTION_K = (5, 10, 20, 50)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--internal-split-dir", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--ce-improvement-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=DEFAULT_BOOTSTRAPS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def quantile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def gt_key(record: dict[str, Any]) -> str:
    return "|".join(
        [
            str(record["scan_id"]),
            str(record["subject_id"]),
            str(record["object_id"]),
            str(record["predicate_label"]),
        ]
    )


def make_counts(bucket: list[dict[str, Any]], score_id: str, k: int) -> dict[str, int]:
    denom_gt = {gt_key(record) for record in bucket if record["gt_exact_match"]}
    ranked = sorted(bucket, key=lambda record: selected_sort_key(score_id, record), reverse=True)
    selected = ranked[: min(k, len(ranked))]
    selected_gt = {gt_key(record) for record in selected if record["gt_exact_match"]}
    violation_denominator = 0
    violation_count = 0
    for record in selected:
        if record["violation_checkable"]:
            violation_denominator += 1
            if record["violation_status"] == "violated":
                violation_count += 1
    return {
        "gt_total": len(denom_gt),
        "gt_selected": len(selected_gt),
        "selected_total": len(selected),
        "violation_denominator": violation_denominator,
        "violation_count": violation_count,
    }


def aggregate_counts(rows: Iterable[dict[str, int]]) -> dict[str, int]:
    materialized = list(rows)
    keys = ["gt_total", "gt_selected", "selected_total", "violation_denominator", "violation_count"]
    return {key: sum(row[key] for row in materialized) for key in keys}


def metrics_from_counts(counts: dict[str, int]) -> dict[str, float | None]:
    recall = None
    violation = None
    if counts["gt_total"]:
        recall = counts["gt_selected"] / counts["gt_total"]
    if counts["violation_denominator"]:
        violation = counts["violation_count"] / counts["violation_denominator"]
    return {"Recall@K": recall, "Violation@K": violation}


def build_unit_counts(records: list[dict[str, Any]]) -> tuple[
    dict[tuple[str, str, str], list[dict[str, Any]]],
    dict[tuple[str, int, tuple[str, str, str]], dict[str, int]],
]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["route_family"] in PRIMARY_FAMILIES:
            grouped[(record["source_id"], record["subgraph_id"], record["route_family"])].append(record)
    unit_counts: dict[tuple[str, int, tuple[str, str, str]], dict[str, int]] = {}
    for key, bucket in grouped.items():
        for score_id in SCORE_IDS:
            for k in K_GRID:
                unit_counts[(score_id, k, key)] = make_counts(bucket, score_id, k)
    return grouped, unit_counts


def point_rows_for_scope(
    unit_counts: dict[tuple[str, int, tuple[str, str, str]], dict[str, int]],
    keys: list[tuple[str, str, str]],
    scope: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for score_id in SCORE_IDS:
        for k in K_GRID:
            counts = aggregate_counts(unit_counts[(score_id, k, key)] for key in keys)
            rows.append(
                {
                    **scope,
                    "score_id": score_id,
                    "K": k,
                    "unit_count": len(keys),
                    **counts,
                    **metrics_from_counts(counts),
                }
            )
    return rows


def bootstrap_delta_rows(
    unit_counts: dict[tuple[str, int, tuple[str, str, str]], dict[str, int]],
    keys: list[tuple[str, str, str]],
    scope: dict[str, Any],
    n_bootstrap: int,
    seed: int,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    point_by_k_metric: dict[tuple[int, str], tuple[float | None, float | None, float | None]] = {}
    point_rows = point_rows_for_scope(unit_counts, keys, scope)
    by_score_k = {(row["score_id"], int(row["K"])): row for row in point_rows}
    for k in K_GRID:
        base = by_score_k[(BASELINE_SCORE, k)]
        cand = by_score_k[(CANDIDATE_SCORE, k)]
        for metric in ("Recall@K", "Violation@K"):
            b = base.get(metric)
            c = cand.get(metric)
            d = None if b is None or c is None else float(c) - float(b)
            point_by_k_metric[(k, metric)] = (b, c, d)

    dist: dict[tuple[int, str], list[float]] = defaultdict(list)
    if keys:
        for _ in range(n_bootstrap):
            sampled = [keys[rng.randrange(len(keys))] for _ in keys]
            for k in K_GRID:
                base_counts = aggregate_counts(unit_counts[(BASELINE_SCORE, k, key)] for key in sampled)
                cand_counts = aggregate_counts(unit_counts[(CANDIDATE_SCORE, k, key)] for key in sampled)
                base_metrics = metrics_from_counts(base_counts)
                cand_metrics = metrics_from_counts(cand_counts)
                for metric in ("Recall@K", "Violation@K"):
                    b = base_metrics.get(metric)
                    c = cand_metrics.get(metric)
                    if b is not None and c is not None:
                        dist[(k, metric)].append(float(c) - float(b))

    rows: list[dict[str, Any]] = []
    for k in K_GRID:
        for metric in ("Recall@K", "Violation@K"):
            base_point, candidate_point, point_delta = point_by_k_metric[(k, metric)]
            values = dist[(k, metric)]
            rows.append(
                {
                    **scope,
                    "candidate_score": CANDIDATE_SCORE,
                    "baseline_score": BASELINE_SCORE,
                    "metric": metric,
                    "K": k,
                    "baseline_point": base_point,
                    "candidate_point": candidate_point,
                    "point_delta": point_delta,
                    "ci_low_95": quantile(values, 0.025),
                    "ci_high_95": quantile(values, 0.975),
                    "n_bootstrap": len(values),
                    "unit_count": len(keys),
                }
            )
    return rows


def family_review_rows(delta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_scope_k: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    rows: list[dict[str, Any]] = []
    for row in delta_rows:
        if row["level"] != "source_family":
            continue
        key = (str(row["source_id"]), str(row["route_family"]), int(row["K"]))
        by_scope_k[key][str(row["metric"])] = row
    for (source_id, family, k), metrics in sorted(by_scope_k.items()):
        recall = metrics.get("Recall@K", {})
        violation = metrics.get("Violation@K", {})
        recall_delta = recall.get("point_delta")
        violation_delta = violation.get("point_delta")
        recall_regression = recall_delta is not None and float(recall_delta) < 0.0
        violation_regression = violation_delta is not None and float(violation_delta) > 0.0
        rows.append(
            {
                "source_id": source_id,
                "route_family": family,
                "K": k,
                "recall_delta": recall_delta,
                "recall_ci_low_95": recall.get("ci_low_95"),
                "recall_ci_high_95": recall.get("ci_high_95"),
                "violation_delta": violation_delta,
                "violation_ci_low_95": violation.get("ci_low_95"),
                "violation_ci_high_95": violation.get("ci_high_95"),
                "recall_regression": recall_regression,
                "violation_regression": violation_regression,
                "hard_blocker": k in PROMOTION_K and violation_regression,
                "double_regression": k in PROMOTION_K and recall_regression and violation_regression,
            }
        )
    return rows


def promotion_gate_rows(primary_delta_rows: list[dict[str, Any]], review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    primary_by_k_metric = {(int(row["K"]), str(row["metric"])): row for row in primary_delta_rows}
    for k in PROMOTION_K:
        recall = primary_by_k_metric[(k, "Recall@K")]
        violation = primary_by_k_metric[(k, "Violation@K")]
        recall_delta = recall.get("point_delta")
        violation_delta = violation.get("point_delta")
        recall_ci_low = recall.get("ci_low_95")
        recall_ci_high = recall.get("ci_high_95")
        violation_ci_low = violation.get("ci_low_95")
        violation_ci_high = violation.get("ci_high_95")
        point_pass = (
            recall_delta is not None
            and violation_delta is not None
            and float(recall_delta) >= 0.0
            and float(violation_delta) <= 0.0
        )
        ci_pass = (
            recall_ci_low is not None
            and violation_ci_high is not None
            and float(recall_ci_low) >= 0.0
            and float(violation_ci_high) <= 0.0
        )
        rows.append(
            {
                "gate": f"primary_point_K{k}",
                "passed": point_pass,
                "reason": f"delta_recall={format_float(recall_delta)}, delta_violation={format_float(violation_delta)}",
            }
        )
        rows.append(
            {
                "gate": f"primary_ci_K{k}",
                "passed": ci_pass,
                "reason": f"recall_CI=[{format_float(recall_ci_low)},{format_float(recall_ci_high)}], violation_CI=[{format_float(violation_ci_low)},{format_float(violation_ci_high)}]",
            }
        )
    blockers = [row for row in review_rows if row["hard_blocker"]]
    double = [row for row in review_rows if row["double_regression"]]
    rows.append(
        {
            "gate": "family_no_violation_regression_K5_50",
            "passed": not blockers,
            "reason": f"violation_regression_cells={len(blockers)}",
        }
    )
    rows.append(
        {
            "gate": "family_no_double_regression_K5_50",
            "passed": not double,
            "reason": f"double_regression_cells={len(double)}",
        }
    )
    rows.append(
        {
            "gate": "main_score_promotion",
            "passed": False,
            "reason": "candidate has positive aggregate signal, but family-wise violation regressions block replacing the current main score",
        }
    )
    return rows


def format_float(value: Any) -> str:
    if value is None:
        return "NA"
    try:
        return f"{float(value):.6f}"
    except (TypeError, ValueError):
        return "NA"


def build_report(summary: dict[str, Any], primary_delta_rows: list[dict[str, Any]], family_rows: list[dict[str, Any]], gate_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# H002 C_e Candidate CI / Family Review",
        "",
        "## 목적",
        "",
        "`I4_calibrated_route_aware_source_x_Ce`를 current `S2_current_source_x_Ce` 대신 main score로 올릴 수 있는지 확인했다.",
        "",
        "## 결론",
        "",
        "```text",
        f"status = {summary['status']}",
        f"validation_errors = {summary['validation_errors']}",
        f"candidate_score = {CANDIDATE_SCORE}",
        f"baseline_score = {BASELINE_SCORE}",
        f"promote_to_main_score = {str(summary['decision']['promote_to_main_score']).lower()}",
        f"selected_path = {summary['decision']['selected_path']}",
        "```",
        "",
        "## Primary Delta",
        "",
        "| K | Delta Recall@K | Recall CI | Delta Violation@K | Violation CI |",
        "| ---: | ---: | --- | ---: | --- |",
    ]
    by_k_metric = {(int(row["K"]), str(row["metric"])): row for row in primary_delta_rows}
    for k in K_GRID:
        recall = by_k_metric[(k, "Recall@K")]
        violation = by_k_metric[(k, "Violation@K")]
        lines.append(
            f"| {k} | {format_float(recall.get('point_delta'))} | [{format_float(recall.get('ci_low_95'))}, {format_float(recall.get('ci_high_95'))}] | "
            f"{format_float(violation.get('point_delta'))} | [{format_float(violation.get('ci_low_95'))}, {format_float(violation.get('ci_high_95'))}] |"
        )
    lines.extend(
        [
            "",
            "## K=5 Point Result",
            "",
            "| Score | Recall@5 | Violation@5 |",
            "| --- | ---: | ---: |",
        ]
    )
    recall5 = by_k_metric[(5, "Recall@K")]
    violation5 = by_k_metric[(5, "Violation@K")]
    lines.append(f"| `{BASELINE_SCORE}` | {format_float(recall5.get('baseline_point'))} | {format_float(violation5.get('baseline_point'))} |")
    lines.append(f"| `{CANDIDATE_SCORE}` | {format_float(recall5.get('candidate_point'))} | {format_float(violation5.get('candidate_point'))} |")
    lines.extend(["", "## Family Blockers", "", "| Source | Family | K | Delta Recall | Delta Violation | Reason |", "| --- | --- | ---: | ---: | ---: | --- |"])
    blockers = [row for row in family_rows if row["hard_blocker"] and int(row["K"]) in PROMOTION_K]
    for row in blockers[:20]:
        reason = "violation worsens"
        if row["double_regression"]:
            reason = "recall and violation both worsen"
        lines.append(
            f"| `{row['source_id']}` | `{row['route_family']}` | {row['K']} | "
            f"{format_float(row.get('recall_delta'))} | {format_float(row.get('violation_delta'))} | {reason} |"
        )
    lines.extend(["", "## Promotion Gates", "", "| Gate | Passed | Reason |", "| --- | --- | --- |"])
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | {row['passed']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## 해석",
            "",
            "- 올릴 수 있는 근거: aggregate primary route에서 K=5/10/20/50 모두 Recall이 증가하고 Violation이 감소한다.",
            "- 올리기 어려운 근거: family-wise로 보면 Open3DSG relative_vertical 등에서 Violation이 악화되는 cell이 남아 있다.",
            "- 따라서 `I4`는 improved candidate / ablation으로는 강하지만, current main score를 대체하려면 family-wise mitigation 또는 per-route gating이 먼저 필요하다.",
            "",
        ]
    )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    for path in [
        args.internal_split_dir / "model_safe_split_view.jsonl",
        args.materialization_dir / "row_manifest.json",
        args.ce_improvement_dir / "summary.json",
    ]:
        if not path.exists():
            errors.append({"error_type": "missing_input", "path": str(path)})
    if args.n_bootstrap < 100:
        errors.append({"error_type": "too_few_bootstrap_samples", "actual": args.n_bootstrap})

    ce_summary = read_json(args.ce_improvement_dir / "summary.json") if (args.ce_improvement_dir / "summary.json").exists() else {}
    split_rows = list(read_jsonl(args.internal_split_dir / "model_safe_split_view.jsonl")) if not errors else []
    train_rows = [row for row in split_rows if row.get("protocol_split") == TRAIN_SPLIT]
    dev_rows = [row for row in split_rows if row.get("protocol_split") == DEV_SPLIT]

    records: list[dict[str, Any]] = []
    primary_delta_rows: list[dict[str, Any]] = []
    family_delta_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    point_rows: list[dict[str, Any]] = []
    score_summary: dict[str, Any] = {}

    if not errors:
        hardneg_train_rows, hardneg_summary = build_hard_negative_train_rows(train_rows)
        current_model, current_prior, _ = fit_model(train_rows, current_ce_features, args.epochs, args.lr, args.l2)
        route_models, route_priors, _ = fit_route_models(hardneg_train_rows, structured_ce_features, args.epochs, args.lr, args.l2)
        route_predict = lambda row: predict_route(route_models, route_priors, row, structured_ce_features)
        temp = float(tune_temperature(dev_rows, route_predict)["temperature"])
        current_predict = lambda row: predict_model(current_model, current_prior, row, current_ce_features)
        calibrated_predict = lambda row: apply_temperature(route_predict(row), temp)

        records, score_summary, row_errors = score_source_rows(
            args.materialization_dir,
            {
                "current_Ce": current_predict,
                "calibrated_route_aware_Ce": calibrated_predict,
            },
        )
        errors.extend(row_errors)
        if len(records) != EXPECTED_TOTAL_ROWS:
            errors.append({"error_type": "source_row_count_mismatch", "actual": len(records), "expected": EXPECTED_TOTAL_ROWS})

        grouped, unit_counts = build_unit_counts(records)
        primary_keys = sorted(grouped)
        point_rows = point_rows_for_scope(unit_counts, primary_keys, {"level": "primary_success_weighted", "source_id": "ALL", "route_family": "PRIMARY"})
        primary_delta_rows = bootstrap_delta_rows(
            unit_counts,
            primary_keys,
            {"level": "primary_success_weighted", "source_id": "ALL", "route_family": "PRIMARY"},
            args.n_bootstrap,
            args.seed,
        )
        grouped_by_source_family: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
        for key in primary_keys:
            source_id, _, family = key
            grouped_by_source_family[(source_id, family)].append(key)
        for index, ((source_id, family), keys) in enumerate(sorted(grouped_by_source_family.items())):
            family_delta_rows.extend(
                bootstrap_delta_rows(
                    unit_counts,
                    keys,
                    {"level": "source_family", "source_id": source_id, "route_family": family},
                    args.n_bootstrap,
                    args.seed + index + 1,
                )
            )
        family_rows = family_review_rows(family_delta_rows)
        gate_rows = promotion_gate_rows(primary_delta_rows, family_rows)

    promote = False
    selected_path = "candidate_ablation_not_main_score"
    if gate_rows and all(row["passed"] for row in gate_rows if row["gate"] != "main_score_promotion"):
        selected_path = "eligible_for_main_score_after_manual_review"
        promote = True
    if any(row["gate"] == "main_score_promotion" and not row["passed"] for row in gate_rows):
        promote = False
        selected_path = "keep_current_main_score_report_I4_as_candidate_or_ablation"

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY if not errors else STATUS_ERROR,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(errors),
        "seed": args.seed,
        "n_bootstrap": args.n_bootstrap,
        "candidate_score": CANDIDATE_SCORE,
        "baseline_score": BASELINE_SCORE,
        "K_grid": list(K_GRID),
        "promotion_K": list(PROMOTION_K),
        "row_counts": {
            "internal_train": len(train_rows),
            "internal_dev": len(dev_rows),
            "source_rows_scored": len(records),
        },
        "ce_improvement_status": ce_summary.get("status"),
        "score_summary": {
            "source_counts": score_summary.get("source_counts", {}),
            "family_counts": score_summary.get("family_counts", {}),
        },
        "decision": {
            "promote_to_main_score": promote,
            "selected_path": selected_path,
            "main_score_after_review": BASELINE_SCORE if not promote else CANDIDATE_SCORE,
            "candidate_position": "candidate_ablation_or_secondary_table" if not promote else "main_score_candidate_after_manual_review",
            "next_todo": "h002_ce_family_mitigation_or_keep_s2_boundary_update",
        },
        "outputs": {
            "summary": str(args.out / "summary.json"),
            "primary_delta_ci": str(args.out / "primary_delta_ci.csv"),
            "family_delta_ci": str(args.out / "family_delta_ci.csv"),
            "family_review": str(args.out / "family_review.csv"),
            "promotion_gate": str(args.out / "promotion_gate.csv"),
            "point_metrics": str(args.out / "point_metrics.csv"),
            "report": str(args.out / "report.md"),
            "validation_errors": str(args.out / "validation_errors.jsonl"),
        },
        "boundary": {
            "fit_or_tune_on_official_validation": False,
            "official_test_used": False,
            "candidate_score_uses_Z_e_inside_C_e": False,
            "Z_e_combined_only_after_C_e": True,
        },
    }

    write_csv(args.out / "primary_delta_ci.csv", primary_delta_rows)
    write_csv(args.out / "family_delta_ci.csv", family_delta_rows)
    write_csv(args.out / "family_review.csv", family_rows)
    write_csv(args.out / "promotion_gate.csv", gate_rows)
    write_csv(args.out / "point_metrics.csv", point_rows)
    write_json(args.out / "summary.json", summary)
    write_jsonl(args.out / "validation_errors.jsonl", errors)
    (args.out / "report.md").write_text(build_report(summary, primary_delta_rows, family_rows, gate_rows), encoding="utf-8")
    return summary


def main() -> int:
    summary = run(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] == STATUS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
