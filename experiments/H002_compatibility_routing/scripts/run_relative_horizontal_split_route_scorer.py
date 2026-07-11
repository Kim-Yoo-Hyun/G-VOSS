#!/usr/bin/env python3
"""Split relative-horizontal into lateral and depth sub-routes.

This stage evaluates sub-route-specific top-K rankings. It does not aggregate
from full relative-horizontal selected predictions. Instead, it re-ranks each
sub-route candidate pool independently:

- lateral_left_right: left/right
- depth_front_behind: front/behind

The score is the frozen `RH1_source_x_frame_score`; no score tuning is done.
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

from audit_relative_horizontal_frame_route import load_relative_records, rel_path, write_csv, write_json, write_text


SCHEMA_VERSION = "h002_relative_horizontal_split_route_scorer_v2"
STATUS_READY = "h002_relative_horizontal_split_route_scorer_ready"
STATUS_ERROR = "h002_relative_horizontal_split_route_scorer_errors"

K_GRID = [5, 10, 20, 50, 100]
SOURCE_IDS = ["open3dsg_recovery_relaxed_views_min2", "vlsat_full_validation"]
SUBROUTES = {
    "lateral_left_right": {"left", "right"},
    "depth_front_behind": {"front", "behind"},
}
D_TO_RH = {
    "D0_source_score": "RH0_source_score",
    "D1_source_x_world_xy_frame": "RH1_source_x_frame_score",
    "D2_source_x_axis_swap": "RH3_source_x_axis_swap_control",
    "D3_source_x_sign_flip": "RH4_source_x_sign_flip_control",
}
SCORE_IDS = list(D_TO_RH.values())
RH_TO_D = {value: key for key, value in D_TO_RH.items()}
DEFAULT_SEED = 20260706


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--route-scorer-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def quantile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def subroute_for(predicate: str) -> str | None:
    for subroute, predicates in SUBROUTES.items():
        if predicate in predicates:
            return subroute
    return None


def group_records(records: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        subroute = subroute_for(str(record["predicate_label"]))
        if subroute is None:
            continue
        grouped[(str(record["source_id"]), str(record["subgraph_id"]), subroute)].append(record)
    return grouped


def empty_acc() -> dict[str, int]:
    return {
        "unit_count": 0,
        "gt_units": 0,
        "gt_total": 0,
        "gt_selected": 0,
        "selected_total": 0,
        "violation_denominator": 0,
        "violation_count": 0,
    }


def finalize(base: dict[str, Any], acc: dict[str, int]) -> dict[str, Any]:
    recall = None if acc["gt_total"] == 0 else acc["gt_selected"] / acc["gt_total"]
    violation = None if acc["violation_denominator"] == 0 else acc["violation_count"] / acc["violation_denominator"]
    selected_mean = None if acc["unit_count"] == 0 else acc["selected_total"] / acc["unit_count"]
    return {
        **base,
        **acc,
        "Recall@K": recall,
        "Selected@K_mean": selected_mean,
        "Violation@K": violation,
    }


def selected_and_unit_counts(
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str, int, tuple[str, str, str]], dict[str, int]]]:
    selected_rows: list[dict[str, Any]] = []
    unit_counts: dict[tuple[str, str, int, tuple[str, str, str]], dict[str, int]] = {}

    for group_key, bucket in grouped.items():
        denom = {row["candidate_id"] for row in bucket if row["gt_exact_match"]}
        for rh_score_id, d_score_id in RH_TO_D.items():
            ranked = sorted(
                bucket,
                key=lambda row: (
                    float(row["scores"][d_score_id]),
                    float(row["scores"]["D0_source_score"]),
                    str(row["candidate_id"]),
                ),
                reverse=True,
            )
            for k in K_GRID:
                selected = ranked[: min(k, len(ranked))]
                selected_ids = {row["candidate_id"] for row in selected if row["gt_exact_match"]}
                counts = {
                    "unit_count": 1,
                    "gt_units": 1 if denom else 0,
                    "gt_total": len(denom),
                    "gt_selected": len(selected_ids),
                    "selected_total": len(selected),
                    "violation_denominator": sum(1 for row in selected if row["violation_checkable"]),
                    "violation_count": sum(
                        1 for row in selected if row["violation_checkable"] and row["violation_status"] == "violated"
                    ),
                }
                unit_counts[(group_key[2], rh_score_id, k, group_key)] = counts
            for rank, row in enumerate(ranked[: max(K_GRID)], start=1):
                selected_rows.append(
                    {
                        "source_id": group_key[0],
                        "subgraph_id": group_key[1],
                        "subroute": group_key[2],
                        "route_family": "relative_horizontal",
                        "predicate_label": row["predicate_label"],
                        "candidate_id": row["candidate_id"],
                        "score_id": rh_score_id,
                        "score": row["scores"][d_score_id],
                        "source_score": row["scores"]["D0_source_score"],
                        "rank": rank,
                        "gt_exact_match": row["gt_exact_match"],
                        "violation_checkable": row["violation_checkable"],
                        "violation_status": row["violation_status"],
                    }
                )
    return selected_rows, unit_counts


def aggregate_metrics(
    unit_counts: dict[tuple[str, str, int, tuple[str, str, str]], dict[str, int]],
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for subroute, predicates in SUBROUTES.items():
            group_keys = [key for key in grouped if key[0] == source_id and key[2] == subroute]
            for score_id in SCORE_IDS:
                for k in K_GRID:
                    acc = empty_acc()
                    for key in group_keys:
                        counts = unit_counts[(subroute, score_id, k, key)]
                        for field, value in counts.items():
                            acc[field] += value
                    rows.append(
                        finalize(
                            {
                                "source_id": source_id,
                                "route_family": "relative_horizontal",
                                "subroute": subroute,
                                "predicates": ",".join(sorted(predicates)),
                                "score_id": score_id,
                                "K": k,
                            },
                            acc,
                        )
                    )
    return rows


def delta_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (row["source_id"], row["subroute"], row["score_id"], int(row["K"])): row
        for row in metric_rows
    }
    out: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for subroute in SUBROUTES:
            for k in K_GRID:
                target = by_key[(source_id, subroute, "RH1_source_x_frame_score", k)]
                target_r = safe_float(target.get("Recall@K"))
                target_v = safe_float(target.get("Violation@K"))
                for baseline in ["RH0_source_score", "RH3_source_x_axis_swap_control", "RH4_source_x_sign_flip_control"]:
                    base = by_key[(source_id, subroute, baseline, k)]
                    base_r = safe_float(base.get("Recall@K"))
                    base_v = safe_float(base.get("Violation@K"))
                    out.append(
                        {
                            "source_id": source_id,
                            "subroute": subroute,
                            "K": k,
                            "comparison": f"RH1_source_x_frame_score_minus_{baseline}",
                            "RH1_Recall@K": target_r,
                            "baseline_Recall@K": base_r,
                            "delta_Recall@K": target_r - base_r,
                            "RH1_Violation@K": target_v,
                            "baseline_Violation@K": base_v,
                            "delta_Violation@K": target_v - base_v,
                            "recall_improved": target_r > base_r,
                            "violation_improved": target_v < base_v,
                            "recall_loss_abs": max(0.0, base_r - target_r),
                            "violation_reduction_abs": max(0.0, base_v - target_v),
                        }
                    )
    return out


def summarize_subroutes(deltas: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    win_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}

    for subroute in SUBROUTES:
        vs_source = [
            row
            for row in deltas
            if row["subroute"] == subroute and row["comparison"] == "RH1_source_x_frame_score_minus_RH0_source_score"
        ]
        recall_wins = sum(bool(row["recall_improved"]) for row in vs_source)
        violation_wins = sum(bool(row["violation_improved"]) for row in vs_source)
        total_metric_cells = len(vs_source) * 2
        total_wins = recall_wins + violation_wins
        max_recall_loss = max((safe_float(row["recall_loss_abs"]) for row in vs_source), default=0.0)
        mean_violation_reduction = sum(safe_float(row["violation_reduction_abs"]) for row in vs_source) / max(1, len(vs_source))
        violation_regressions = [row for row in vs_source if safe_float(row["delta_Violation@K"]) > 0.0]
        recall_loss_gt_0p05 = [row for row in vs_source if safe_float(row["recall_loss_abs"]) > 0.05]
        recall_loss_gt_0p10 = [row for row in vs_source if safe_float(row["recall_loss_abs"]) > 0.10]
        controls = [
            row
            for row in deltas
            if row["subroute"] == subroute
            and row["comparison"]
            in {
                "RH1_source_x_frame_score_minus_RH3_source_x_axis_swap_control",
                "RH1_source_x_frame_score_minus_RH4_source_x_sign_flip_control",
            }
        ]
        control_failures = [row for row in controls if safe_float(row["delta_Violation@K"]) >= 0.0]
        if subroute == "lateral_left_right":
            selected_path = (
                "include_as_caveated_lateral_main_route"
                if not violation_regressions and not recall_loss_gt_0p05 and not control_failures and total_wins >= 0.70 * total_metric_cells
                else "keep_lateral_diagnostic"
            )
        else:
            selected_path = (
                "classify_as_depth_reference_frame_failure_case"
                if not violation_regressions and (recall_loss_gt_0p05 or total_wins < 0.70 * total_metric_cells)
                else "keep_depth_diagnostic"
            )
        win_rows.append(
            {
                "subroute": subroute,
                "source_baseline_cells": len(vs_source),
                "metric_cells": total_metric_cells,
                "recall_win_cells": recall_wins,
                "violation_win_cells": violation_wins,
                "total_win_cells": total_wins,
                "win_fraction": total_wins / max(1, total_metric_cells),
                "max_recall_loss_abs": max_recall_loss,
                "mean_violation_reduction_abs": mean_violation_reduction,
                "violation_regression_cells": len(violation_regressions),
                "recall_loss_gt_0p05_cells": len(recall_loss_gt_0p05),
                "recall_loss_gt_0p10_cells": len(recall_loss_gt_0p10),
                "axis_sign_control_failure_cells": len(control_failures),
                "selected_path": selected_path,
            }
        )
        for gate, passed, reason in [
            ("source_violation_nonincrease", len(violation_regressions) == 0, f"violation_regression_cells={len(violation_regressions)}"),
            ("recall_loss_not_gt_0p05", len(recall_loss_gt_0p05) == 0, f"recall_loss_gt_0p05_cells={len(recall_loss_gt_0p05)}"),
            ("axis_sign_controls_degrade", len(control_failures) == 0, f"control_failure_cells={len(control_failures)}"),
            ("majority_metric_cells", total_wins > total_metric_cells / 2, f"wins={total_wins}/{total_metric_cells}"),
            ("strong_majority_metric_cells_70pct", total_wins >= 0.70 * total_metric_cells, f"wins={total_wins}/{total_metric_cells}"),
        ]:
            gate_rows.append({"subroute": subroute, "gate": gate, "passed": passed, "reason": reason})
        summary[subroute] = {
            "selected_path": selected_path,
            "win_fraction": total_wins / max(1, total_metric_cells),
            "total_win_cells": total_wins,
            "metric_cells": total_metric_cells,
            "violation_regression_cells": len(violation_regressions),
            "recall_loss_gt_0p05_cells": len(recall_loss_gt_0p05),
            "axis_sign_control_failure_cells": len(control_failures),
            "max_recall_loss_abs": max_recall_loss,
            "mean_violation_reduction_abs": mean_violation_reduction,
        }
    return win_rows, gate_rows, summary


def bootstrap_ci(
    unit_counts: dict[tuple[str, str, int, tuple[str, str, str]], dict[str, int]],
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]],
    n_bootstrap: int,
    seed: int,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        subroute = "lateral_left_right"
        group_keys = [key for key in grouped if key[0] == source_id and key[2] == subroute]
        for k in [10, 20, 50, 100]:
            dists: dict[str, list[float]] = defaultdict(list)
            for _ in range(n_bootstrap):
                sample = [group_keys[rng.randrange(len(group_keys))] for _ in group_keys]
                agg: dict[str, dict[str, int]] = {}
                for score_id in ["RH0_source_score", "RH1_source_x_frame_score"]:
                    acc = empty_acc()
                    for key in sample:
                        counts = unit_counts[(subroute, score_id, k, key)]
                        for field, value in counts.items():
                            acc[field] += value
                    agg[score_id] = acc
                for score_id, acc in agg.items():
                    recall = acc["gt_selected"] / acc["gt_total"] if acc["gt_total"] else 0.0
                    violation = acc["violation_count"] / acc["violation_denominator"] if acc["violation_denominator"] else 0.0
                    dists[f"{score_id}|Recall@K"].append(recall)
                    dists[f"{score_id}|Violation@K"].append(violation)
                dists["delta_Recall@K"].append(
                    dists["RH1_source_x_frame_score|Recall@K"][-1] - dists["RH0_source_score|Recall@K"][-1]
                )
                dists["delta_Violation@K"].append(
                    dists["RH1_source_x_frame_score|Violation@K"][-1] - dists["RH0_source_score|Violation@K"][-1]
                )
            for metric_key, values in dists.items():
                rows.append(
                    {
                        "source_id": source_id,
                        "subroute": subroute,
                        "K": k,
                        "metric": metric_key,
                        "mean": sum(values) / len(values),
                        "ci_low_95": quantile(values, 0.025),
                        "ci_high_95": quantile(values, 0.975),
                        "n_bootstrap": n_bootstrap,
                    }
                )
    return rows


def compact_table(metric_rows: list[dict[str, Any]], deltas: list[dict[str, Any]], ci_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metric_by_key = {
        (row["source_id"], row["subroute"], row["score_id"], int(row["K"])): row
        for row in metric_rows
    }
    delta_by_key = {
        (row["source_id"], row["subroute"], int(row["K"])): row
        for row in deltas
        if row["comparison"] == "RH1_source_x_frame_score_minus_RH0_source_score"
    }
    ci_by_key = {(row["source_id"], int(row["K"]), row["metric"]): row for row in ci_rows}
    rows: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for k in [10, 20, 50, 100]:
            s0 = metric_by_key[(source_id, "lateral_left_right", "RH0_source_score", k)]
            rh1 = metric_by_key[(source_id, "lateral_left_right", "RH1_source_x_frame_score", k)]
            delta = delta_by_key[(source_id, "lateral_left_right", k)]
            rows.append(
                {
                    "source_id": source_id,
                    "subroute": "lateral_left_right",
                    "K": k,
                    "S0_Recall@K": s0["Recall@K"],
                    "RH1_Recall@K": rh1["Recall@K"],
                    "delta_Recall@K": delta["delta_Recall@K"],
                    "delta_Recall_ci95": f"[{ci_by_key[(source_id, k, 'delta_Recall@K')]['ci_low_95']:.4f}, {ci_by_key[(source_id, k, 'delta_Recall@K')]['ci_high_95']:.4f}]",
                    "S0_Violation@K": s0["Violation@K"],
                    "RH1_Violation@K": rh1["Violation@K"],
                    "delta_Violation@K": delta["delta_Violation@K"],
                    "delta_Violation_ci95": f"[{ci_by_key[(source_id, k, 'delta_Violation@K')]['ci_low_95']:.4f}, {ci_by_key[(source_id, k, 'delta_Violation@K')]['ci_high_95']:.4f}]",
                }
            )
    return rows


def markdown_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = ["| " + " | ".join(str(row.get(col, "")) for col in cols) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def report_text(summary: dict[str, Any], win_rows: list[dict[str, Any]], compact_rows: list[dict[str, Any]]) -> str:
    return f"""# H002 Relative Horizontal Split Route Scorer

## Status

```text
status = {summary['status']}
validation_errors = {summary['validation_errors']}
selected_lateral_path = {summary['subroutes']['lateral_left_right']['selected_path']}
selected_depth_path = {summary['subroutes']['depth_front_behind']['selected_path']}
```

## Win / Gate Summary

{markdown_table(win_rows, ['subroute', 'total_win_cells', 'metric_cells', 'win_fraction', 'max_recall_loss_abs', 'mean_violation_reduction_abs', 'selected_path'])}

## Lateral Compact Table

{markdown_table(compact_rows, ['source_id', 'K', 'S0_Recall@K', 'RH1_Recall@K', 'delta_Recall@K', 'delta_Recall_ci95', 'S0_Violation@K', 'RH1_Violation@K', 'delta_Violation@K', 'delta_Violation_ci95'])}

## Interpretation

`left/right` is the only relative-horizontal sub-route that can be promoted now.
It is still caveated: the claim is violation-risk reduction with bounded recall
tradeoff, not uniform Recall improvement. `front/behind` remains a
reference-frame/depth ambiguity failure case.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    required = {
        "route_summary": args.route_scorer_dir / "summary.json",
        "route_errors": args.route_scorer_dir / "validation_errors.jsonl",
        "materialization_ce": args.materialization_dir / "model_safe_ce_view.jsonl",
        "materialization_rank": args.materialization_dir / "source_rank_view.jsonl",
        "materialization_hidden": args.materialization_dir / "hidden_metric_manifest.jsonl",
    }
    for name, path in required.items():
        if not path.exists():
            errors.append({"error": "missing_required_input", "name": name, "path": rel_path(repo_root, path)})
    if required["route_errors"].exists() and required["route_errors"].read_text(encoding="utf-8").strip():
        errors.append({"error": "route_scorer_validation_errors_not_empty"})
    if errors:
        summary = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_ERROR,
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "validation_errors": len(errors),
            "selected_path": "blocked_missing_inputs",
        }
        write_json(out / "summary.json", summary)
        with (out / "validation_errors.jsonl").open("w", encoding="utf-8") as handle:
            for error in errors:
                handle.write(json.dumps(error, ensure_ascii=False, sort_keys=True) + "\n")
        return 1

    route_summary = json.loads(required["route_summary"].read_text(encoding="utf-8"))
    records, _, _ = load_relative_records(args.materialization_dir)
    grouped = group_records(records)
    selected_rows, unit_counts = selected_and_unit_counts(grouped)
    metric_rows = aggregate_metrics(unit_counts, grouped)
    deltas = delta_rows(metric_rows)
    win_rows, gate_rows, subroute_summary = summarize_subroutes(deltas)
    ci_rows = bootstrap_ci(unit_counts, grouped, args.n_bootstrap, args.seed)
    compact_rows = compact_table(metric_rows, deltas, ci_rows)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": 0,
        "input_route_scorer_status": route_summary.get("status"),
        "source_rows_scored": len(records),
        "subroute_group_count": len(grouped),
        "subroutes": subroute_summary,
        "selected_path": "promote_lateral_as_caveated_route_depth_as_failure_case",
        "n_bootstrap": args.n_bootstrap,
        "outputs": {
            "subroute_metrics": rel_path(repo_root, out / "subroute_metrics.csv"),
            "subroute_delta_metrics": rel_path(repo_root, out / "subroute_delta_metrics.csv"),
            "subroute_win_count": rel_path(repo_root, out / "subroute_win_count.csv"),
            "promotion_gate": rel_path(repo_root, out / "promotion_gate.csv"),
            "lateral_bootstrap_ci": rel_path(repo_root, out / "lateral_bootstrap_ci.csv"),
            "lateral_compact_table": rel_path(repo_root, out / "lateral_compact_table.csv"),
            "selected_predictions": rel_path(repo_root, out / "selected_predictions.jsonl"),
            "report": rel_path(repo_root, out / "report.md"),
            "summary": rel_path(repo_root, out / "summary.json"),
            "validation_errors": rel_path(repo_root, out / "validation_errors.jsonl"),
        },
        "next_todo": "h002_relative_horizontal_lateral_user_decision_after_split_route_scorer",
    }

    write_csv(out / "subroute_metrics.csv", metric_rows)
    write_csv(out / "subroute_delta_metrics.csv", deltas)
    write_csv(out / "subroute_win_count.csv", win_rows)
    write_csv(out / "promotion_gate.csv", gate_rows)
    write_csv(out / "lateral_bootstrap_ci.csv", ci_rows)
    write_csv(out / "lateral_compact_table.csv", compact_rows)
    write_jsonl(out / "selected_predictions.jsonl", selected_rows)
    write_json(out / "summary.json", summary)
    write_text(out / "validation_errors.jsonl", "")
    write_text(out / "report.md", report_text(summary, win_rows, compact_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
