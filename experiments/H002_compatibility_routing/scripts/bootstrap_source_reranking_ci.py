#!/usr/bin/env python3
"""Bootstrap CIs for frozen H002 source-reranking metrics.

This script does not fit or tune any score. It reuses the frozen
source-reranking selected predictions and hidden metric manifest, reconstructs
the primary-family top-K metrics, and bootstraps over source/subgraph/family
units.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_source_reranking_bootstrap_ci_v1"
STATUS_READY = "h002_source_reranking_bootstrap_ci_ready"
STATUS_ERROR = "h002_source_reranking_bootstrap_ci_input_errors"

PRIMARY_FAMILIES = {"relative_vertical", "size_relative"}
SCORE_IDS = (
    "S0_source_score",
    "S1_Ce_only",
    "S2_source_x_Ce",
    "C1_source_x_shuffled_Ce",
    "C2_source_x_wrong_T_Ce",
    "A1_source_x_G_only",
    "A2_source_x_TG_concat",
)
DELTA_BASELINE_SCORE_IDS = (
    "S0_source_score",
    "A1_source_x_G_only",
    "A2_source_x_TG_concat",
    "C1_source_x_shuffled_Ce",
    "C2_source_x_wrong_T_Ce",
    "S1_Ce_only",
)
K_GRID = (5, 10, 20, 50, 100)
DEFAULT_SEED = 20260703


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-dir", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
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
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def group_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row["source_id"]), str(row["subgraph_id"]), str(row["route_family"]))


def gt_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row["scan_id"]),
            str(row["subject_id"]),
            str(row["object_id"]),
            str(row["predicate_label"]),
        ]
    )


def quantile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def make_metric(gt_selected: int, gt_total: int, violation_count: int, violation_denominator: int) -> dict[str, float | None]:
    recall = gt_selected / gt_total if gt_total else None
    violation = violation_count / violation_denominator if violation_denominator else None
    return {"Recall@K": recall, "Violation@K": violation}


def load_selected(evaluation_dir: Path) -> tuple[dict[tuple[str, tuple[str, str, str]], list[dict[str, Any]]], set[str], list[dict[str, Any]]]:
    selected_path = evaluation_dir / "selected_predictions.jsonl"
    selected_by_score_group: dict[tuple[str, tuple[str, str, str]], list[dict[str, Any]]] = defaultdict(list)
    selected_candidate_ids: set[str] = set()
    errors: list[dict[str, Any]] = []
    for row in iter_jsonl(selected_path):
        score_id = str(row.get("score_id"))
        family = str(row.get("route_family"))
        if score_id not in SCORE_IDS or family not in PRIMARY_FAMILIES:
            continue
        candidate_id = str(row.get("candidate_id"))
        selected_candidate_ids.add(candidate_id)
        selected_by_score_group[(score_id, group_key(row))].append(row)
    for key, rows in selected_by_score_group.items():
        ranks = [int(row.get("rank", 0)) for row in rows]
        if len(ranks) != len(set(ranks)):
            errors.append({"error_type": "duplicate_rank_within_selected_group", "score_group": repr(key)})
        rows.sort(key=lambda row: (int(row.get("rank", 0)), str(row.get("candidate_id", ""))))
    return selected_by_score_group, selected_candidate_ids, errors


def load_hidden(
    materialization_dir: Path,
    selected_candidate_ids: set[str],
) -> tuple[dict[tuple[str, str, str], set[str]], dict[str, str], dict[str, Any], list[dict[str, Any]]]:
    hidden_path = materialization_dir / "hidden_metric_manifest.jsonl"
    denom_by_group: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    candidate_to_gt: dict[str, str] = {}
    row_count = 0
    primary_row_count = 0
    errors: list[dict[str, Any]] = []
    for row in iter_jsonl(hidden_path):
        row_count += 1
        family = str(row.get("route_family"))
        if family not in PRIMARY_FAMILIES:
            continue
        primary_row_count += 1
        key = group_key(row)
        if bool(row.get("gt_exact_match")):
            gkey = gt_key(row)
            denom_by_group[key].add(gkey)
            candidate_id = str(row.get("candidate_id"))
            if candidate_id in selected_candidate_ids:
                candidate_to_gt[candidate_id] = gkey
    manifest = {
        "hidden_rows_scanned": row_count,
        "primary_rows_scanned": primary_row_count,
        "primary_group_count": len(denom_by_group),
        "selected_candidate_count": len(selected_candidate_ids),
        "selected_gt_key_count": len(candidate_to_gt),
    }
    if row_count == 0:
        errors.append({"error_type": "empty_hidden_manifest"})
    if not denom_by_group:
        errors.append({"error_type": "no_primary_groups_in_hidden_manifest"})
    return denom_by_group, candidate_to_gt, manifest, errors


def group_counts(
    group_key_value: tuple[str, str, str],
    score_id: str,
    k: int,
    denom_by_group: dict[tuple[str, str, str], set[str]],
    candidate_to_gt: dict[str, str],
    selected_by_score_group: dict[tuple[str, tuple[str, str, str]], list[dict[str, Any]]],
) -> dict[str, int]:
    selected = selected_by_score_group.get((score_id, group_key_value), [])[:k]
    selected_gt: set[str] = set()
    violation_denominator = 0
    violation_count = 0
    for row in selected:
        if bool(row.get("gt_exact_match")):
            candidate_id = str(row.get("candidate_id"))
            selected_gt.add(candidate_to_gt.get(candidate_id, candidate_id))
        if bool(row.get("violation_checkable")):
            violation_denominator += 1
            if str(row.get("violation_status")) == "violated":
                violation_count += 1
    return {
        "gt_total": len(denom_by_group.get(group_key_value, set())),
        "gt_selected": len(selected_gt),
        "selected_total": len(selected),
        "violation_denominator": violation_denominator,
        "violation_count": violation_count,
    }


def aggregate_counts(rows: list[dict[str, int]]) -> dict[str, int]:
    keys = ["gt_total", "gt_selected", "selected_total", "violation_denominator", "violation_count"]
    return {key: sum(row[key] for row in rows) for key in keys}


def bootstrap_metric(
    unit_counts: dict[tuple[str, int, tuple[str, str, str]], dict[str, int]],
    group_keys: list[tuple[str, str, str]],
    n_bootstrap: int,
    seed: int,
    scope: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    point_rows: list[dict[str, Any]] = []
    point_by_score_k: dict[tuple[str, int], dict[str, float | None]] = {}
    dist: dict[tuple[str, int, str], list[float]] = defaultdict(list)
    delta_dist: dict[tuple[str, int, str], list[float]] = defaultdict(list)

    for score_id in SCORE_IDS:
        for k in K_GRID:
            counts = aggregate_counts([unit_counts[(score_id, k, key)] for key in group_keys])
            metrics = make_metric(
                counts["gt_selected"],
                counts["gt_total"],
                counts["violation_count"],
                counts["violation_denominator"],
            )
            point_by_score_k[(score_id, k)] = metrics
            point_rows.append(
                {
                    **scope,
                    "score_id": score_id,
                    "K": k,
                    "unit_count": len(group_keys),
                    **counts,
                    **metrics,
                }
            )

    for _ in range(n_bootstrap):
        sampled = [group_keys[rng.randrange(len(group_keys))] for _ in group_keys]
        for score_id in SCORE_IDS:
            for k in K_GRID:
                counts = aggregate_counts([unit_counts[(score_id, k, key)] for key in sampled])
                metrics = make_metric(
                    counts["gt_selected"],
                    counts["gt_total"],
                    counts["violation_count"],
                    counts["violation_denominator"],
                )
                for metric_name, value in metrics.items():
                    if value is not None:
                        dist[(score_id, k, metric_name)].append(float(value))
        for k in K_GRID:
            s2 = {}
            baseline_metrics: dict[str, dict[str, float | None]] = {}
            for score_id, target in [("S2_source_x_Ce", s2)] + [(score_id, {}) for score_id in DELTA_BASELINE_SCORE_IDS]:
                counts = aggregate_counts([unit_counts[(score_id, k, key)] for key in sampled])
                target.update(
                    make_metric(
                        counts["gt_selected"],
                        counts["gt_total"],
                        counts["violation_count"],
                        counts["violation_denominator"],
                    )
                )
                if score_id != "S2_source_x_Ce":
                    baseline_metrics[score_id] = target
            for metric_name in ("Recall@K", "Violation@K"):
                for baseline_id, baseline in baseline_metrics.items():
                    if s2.get(metric_name) is not None and baseline.get(metric_name) is not None:
                        delta_dist[(baseline_id, k, metric_name)].append(float(s2[metric_name]) - float(baseline[metric_name]))

    ci_rows: list[dict[str, Any]] = []
    for point in point_rows:
        score_id = str(point["score_id"])
        k = int(point["K"])
        for metric_name in ("Recall@K", "Violation@K"):
            values = dist.get((score_id, k, metric_name), [])
            ci_rows.append(
                {
                    **scope,
                    "metric": metric_name,
                    "score_id": score_id,
                    "K": k,
                    "point": point.get(metric_name),
                    "ci_low_95": quantile(values, 0.025),
                    "ci_high_95": quantile(values, 0.975),
                    "n_bootstrap": len(values),
                    "unit_count": point["unit_count"],
                }
            )
    delta_rows: list[dict[str, Any]] = []
    for k in K_GRID:
        for metric_name in ("Recall@K", "Violation@K"):
            s2_point = point_by_score_k[("S2_source_x_Ce", k)].get(metric_name)
            for baseline_id in DELTA_BASELINE_SCORE_IDS:
                baseline_point = point_by_score_k[(baseline_id, k)].get(metric_name)
                point_delta = None
                if s2_point is not None and baseline_point is not None:
                    point_delta = float(s2_point) - float(baseline_point)
                values = delta_dist.get((baseline_id, k, metric_name), [])
                delta_rows.append(
                    {
                        **scope,
                        "comparison": f"S2_source_x_Ce_minus_{baseline_id}",
                        "primary_score": "S2_source_x_Ce",
                        "baseline_score": baseline_id,
                        "metric": metric_name,
                        "K": k,
                        "point_delta": point_delta,
                        "ci_low_95": quantile(values, 0.025),
                        "ci_high_95": quantile(values, 0.975),
                        "n_bootstrap": len(values),
                        "unit_count": len(group_keys),
                    }
                )
    return ci_rows, delta_rows


def point_validation(evaluation_dir: Path, ci_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected_path = evaluation_dir / "score_condition_metrics.csv"
    if not expected_path.exists():
        return [{"error_type": "missing_score_condition_metrics"}]
    expected = {}
    for row in read_csv(expected_path):
        if (
            row.get("level") == "primary_success_weighted"
            and row.get("route_family") == "PRIMARY"
            and row.get("score_id") in SCORE_IDS
        ):
            expected[(row["score_id"], int(row["K"]), "Recall@K")] = float(row["Recall@K"])
            expected[(row["score_id"], int(row["K"]), "Violation@K")] = float(row["Violation@K"])
    rows: list[dict[str, Any]] = []
    for row in ci_rows:
        key = (row["score_id"], int(row["K"]), row["metric"])
        expected_value = expected.get(key)
        point = row.get("point")
        diff = None if expected_value is None or point is None else abs(float(point) - expected_value)
        rows.append(
            {
                "score_id": row["score_id"],
                "K": row["K"],
                "metric": row["metric"],
                "reconstructed_point": point,
                "expected_point": expected_value,
                "abs_diff": diff,
                "matches_existing_metric": diff is not None and diff <= 1e-9,
            }
        )
    return rows


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    selected_path = args.evaluation_dir / "selected_predictions.jsonl"
    hidden_path = args.materialization_dir / "hidden_metric_manifest.jsonl"
    metric_path = args.evaluation_dir / "score_condition_metrics.csv"
    for path in [selected_path, hidden_path, metric_path]:
        if not path.exists():
            errors.append({"error_type": "missing_input", "path": str(path)})
    if args.n_bootstrap < 100:
        errors.append({"error_type": "too_few_bootstrap_samples", "actual": args.n_bootstrap})
    if errors:
        summary = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_ERROR,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "validation_errors": len(errors),
        }
        write_json(args.out / "summary.json", summary)
        write_jsonl(args.out / "validation_errors.jsonl", errors)
        return summary

    selected_by_score_group, selected_candidate_ids, selected_errors = load_selected(args.evaluation_dir)
    denom_by_group, candidate_to_gt, manifest, hidden_errors = load_hidden(args.materialization_dir, selected_candidate_ids)
    errors.extend(selected_errors)
    errors.extend(hidden_errors)
    group_keys = sorted(set(denom_by_group) | {key for _, key in selected_by_score_group})
    if not group_keys:
        errors.append({"error_type": "no_bootstrap_groups"})

    unit_counts: dict[tuple[str, int, tuple[str, str, str]], dict[str, int]] = {}
    for score_id in SCORE_IDS:
        for k in K_GRID:
            for key in group_keys:
                unit_counts[(score_id, k, key)] = group_counts(
                    key,
                    score_id,
                    k,
                    denom_by_group,
                    candidate_to_gt,
                    selected_by_score_group,
                )

    ci_rows, delta_rows = bootstrap_metric(
        unit_counts,
        group_keys,
        args.n_bootstrap,
        args.seed,
        {"level": "primary_success_weighted", "source_id": "ALL", "route_family": "PRIMARY"},
    )
    familywise_ci_rows: list[dict[str, Any]] = []
    familywise_delta_rows: list[dict[str, Any]] = []
    group_keys_by_source_family: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
    for key in group_keys:
        source_id, _, route_family = key
        if route_family in PRIMARY_FAMILIES:
            group_keys_by_source_family[(source_id, route_family)].append(key)
    for index, ((source_id, route_family), scoped_keys) in enumerate(sorted(group_keys_by_source_family.items())):
        scoped_ci, scoped_delta = bootstrap_metric(
            unit_counts,
            scoped_keys,
            args.n_bootstrap,
            args.seed + index + 1,
            {"level": "source_family", "source_id": source_id, "route_family": route_family},
        )
        familywise_ci_rows.extend(scoped_ci)
        familywise_delta_rows.extend(scoped_delta)
    validation_rows = point_validation(args.evaluation_dir, ci_rows)
    mismatch_rows = [
        row
        for row in validation_rows
        if row.get("matches_existing_metric") is False and row.get("abs_diff") not in (None, "")
    ]
    if mismatch_rows:
        errors.append({"error_type": "reconstructed_point_metric_mismatch", "count": len(mismatch_rows)})

    write_csv(args.out / "main_reranking_ci.csv", ci_rows)
    write_csv(args.out / "main_reranking_delta_ci.csv", delta_rows)
    write_csv(args.out / "familywise_reranking_ci.csv", familywise_ci_rows)
    write_csv(args.out / "familywise_reranking_delta_ci.csv", familywise_delta_rows)
    write_csv(args.out / "point_validation.csv", validation_rows)

    report = [
        "# H002 Source Reranking Bootstrap CI",
        "",
        "This run bootstraps over `(source_id, subgraph_id, route_family)` units for the frozen primary-family validation source-reranking result.",
        "",
        "## Scope",
        "",
        "- Scores: `S0_source_score`, `S1_Ce_only`, `S2_source_x_Ce`, controls, `A1_source_x_G_only`, `A2_source_x_TG_concat`",
        "- Families: `relative_vertical`, `size_relative`",
        "- Metrics: `Recall@K`, `Violation@K`, `S2-S0`, `S2-A1`, `S2-A2`, and control deltas",
        f"- Bootstrap samples: `{args.n_bootstrap}`",
        f"- Unit count: `{len(group_keys)}`",
        "",
        "## Boundary",
        "",
        "No model fitting, score normalization tuning, threshold tuning, or family selection is performed in this script.",
    ]
    (args.out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY if not errors else STATUS_ERROR,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "n_bootstrap": args.n_bootstrap,
        "primary_families": sorted(PRIMARY_FAMILIES),
        "score_ids": list(SCORE_IDS),
        "delta_baseline_score_ids": list(DELTA_BASELINE_SCORE_IDS),
        "K_grid": list(K_GRID),
        "bootstrap_unit": "source_id/subgraph_id/route_family",
        "unit_count": len(group_keys),
        "familywise_unit_scopes": len(group_keys_by_source_family),
        "manifest": manifest,
        "point_metric_mismatch_count": len(mismatch_rows),
        "validation_errors": len(errors),
        "next_todo": "h002_source_reranking_ablation_expansion_result_review_after_implementation",
    }
    write_json(args.out / "summary.json", summary)
    write_jsonl(args.out / "validation_errors.jsonl", errors)
    return summary


def main() -> None:
    summary = run(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
