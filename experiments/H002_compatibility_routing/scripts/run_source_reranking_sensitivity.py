#!/usr/bin/env python3
"""Run H002 source-reranking sensitivity checks.

This stage does not replace the frozen main source-reranking table. It checks two
paper-wording risks found by the experiment-stage gap review:

1. whether the S2 gain is dependent on validation candidate-pool minmax
   normalization;
2. whether the geometry-only ablation should be described as route-aware.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from run_grouped_eval import read_jsonl, stable_hash
from run_official_metric import (
    common_g_features,
    compatibility_features,
    fit_model,
    merge_features,
    safe_float,
    t_features,
)


SCHEMA_VERSION = "h002_source_reranking_sensitivity_v1"
STATUS_READY = "h002_source_reranking_sensitivity_ready"
STATUS_ERROR = "h002_source_reranking_sensitivity_errors"

TRAIN_SPLIT = "internal_train"
PRIMARY_FAMILIES = {"relative_vertical", "size_relative"}
K_GRID = [5, 10, 20, 50, 100]
EXPECTED_TOTAL_ROWS = 762888
CONTROL_SEED = "h002_source_reranking_sensitivity_v1"

SCORE_IDS = [
    "S0_source_score_minmax",
    "S2_minmax_source_x_Ce",
    "S2_rankpct_source_x_Ce",
    "S2_raw_source_x_Ce",
    "A1_minmax_route_G_only",
    "A1_minmax_no_route_G_only",
    "A2_minmax_TG_concat",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--internal-split-dir", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--base-evaluation-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


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


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def ce_feature_fn(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), common_g_features(row), compatibility_features(row))


def route_g_feature_fn(row: dict[str, Any]) -> dict[str, float]:
    return common_g_features(row)


def no_route_g_feature_fn(row: dict[str, Any]) -> dict[str, float]:
    return {key: value for key, value in common_g_features(row).items() if not key.startswith("G.route_family")}


def concat_feature_fn(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), common_g_features(row))


def predict_one(model: Any, prior: float, row: dict[str, Any], feature_fn: Callable[[dict[str, Any]], dict[str, float]]) -> float:
    if model is None:
        return prior
    return float(model.predict_one(feature_fn(row)))


def minmax(value: float, bounds: tuple[float, float] | None) -> float:
    if bounds is None:
        return 0.5
    lo, hi = bounds
    if hi - lo <= 1e-12:
        return 0.5
    return (value - lo) / (hi - lo)


def clip01(value: float, eps: float = 1e-6) -> float:
    return min(max(value, eps), 1.0)


def update_bounds(bounds: dict[Any, list[float]], key: Any, value: float) -> None:
    if key not in bounds:
        bounds[key] = [value, value]
    else:
        bounds[key][0] = min(bounds[key][0], value)
        bounds[key][1] = max(bounds[key][1], value)


def percentile_ranks(records: list[dict[str, Any]], value_key: str, group_key_fn: Callable[[dict[str, Any]], Any]) -> dict[str, float]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[group_key_fn(record)].append(record)
    ranks: dict[str, float] = {}
    for _, rows in grouped.items():
        ordered = sorted(rows, key=lambda row: (float(row[value_key]), str(row["candidate_id"])))
        denom = max(len(ordered) - 1, 1)
        for idx, row in enumerate(ordered):
            ranks[str(row["candidate_id"])] = idx / denom
    return ranks


def read_aligned_rows(materialization_dir: Path) -> Iterable[tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]]:
    paths = {
        "ce": materialization_dir / "model_safe_ce_view.jsonl",
        "geometry": materialization_dir / "model_safe_geometry_only_view.jsonl",
        "rank": materialization_dir / "source_rank_view.jsonl",
        "hidden": materialization_dir / "hidden_metric_manifest.jsonl",
    }
    with (
        paths["ce"].open("r", encoding="utf-8") as ce_handle,
        paths["geometry"].open("r", encoding="utf-8") as geometry_handle,
        paths["rank"].open("r", encoding="utf-8") as rank_handle,
        paths["hidden"].open("r", encoding="utf-8") as hidden_handle,
    ):
        for ce_line, geometry_line, rank_line, hidden_line in zip(ce_handle, geometry_handle, rank_handle, hidden_handle):
            yield json.loads(ce_line), json.loads(geometry_line), json.loads(rank_line), json.loads(hidden_line)


def gt_key(record: dict[str, Any]) -> str:
    return "|".join([str(record["scan_id"]), str(record["subject_id"]), str(record["object_id"]), str(record["predicate_label"])])


def selected_sort_key(score_id: str, record: dict[str, Any]) -> tuple[float, float, str]:
    return (float(record["scores"].get(score_id, 0.0)), float(record.get("source_score", 0.0)), str(record.get("prediction_id", "")))


def empty_accumulator() -> dict[str, Any]:
    return {
        "unit_count": 0,
        "gt_units": 0,
        "gt_total": 0,
        "gt_selected": 0,
        "selected_total": 0,
        "violation_denominator": 0,
        "violation_count": 0,
    }


def add_group_metric(acc: dict[str, Any], denom_gt: set[str], selected_gt: set[str], selected: list[dict[str, Any]]) -> None:
    acc["unit_count"] += 1
    acc["selected_total"] += len(selected)
    if denom_gt:
        acc["gt_units"] += 1
        acc["gt_total"] += len(denom_gt)
        acc["gt_selected"] += len(selected_gt)
    for record in selected:
        if record["violation_checkable"]:
            acc["violation_denominator"] += 1
            if record["violation_status"] == "violated":
                acc["violation_count"] += 1


def finalize(base: dict[str, Any], acc: dict[str, Any]) -> dict[str, Any]:
    return {
        **base,
        "unit_count": acc["unit_count"],
        "gt_units": acc["gt_units"],
        "gt_total": acc["gt_total"],
        "gt_selected": acc["gt_selected"],
        "Recall@K": acc["gt_selected"] / acc["gt_total"] if acc["gt_total"] else None,
        "selected_total": acc["selected_total"],
        "Selected@K_mean": acc["selected_total"] / acc["unit_count"] if acc["unit_count"] else None,
        "violation_denominator": acc["violation_denominator"],
        "violation_count": acc["violation_count"],
        "Violation@K": acc["violation_count"] / acc["violation_denominator"] if acc["violation_denominator"] else None,
    }


def metric_tables(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[(record["source_id"], record["subgraph_id"], record["route_family"])].append(record)

    family_acc: dict[tuple[str, str, str, int], dict[str, Any]] = defaultdict(empty_accumulator)
    for group_key, bucket in groups.items():
        denom_gt = {gt_key(record) for record in bucket if record["gt_exact_match"]}
        for score_id in SCORE_IDS:
            ranked = sorted(bucket, key=lambda record: selected_sort_key(score_id, record), reverse=True)
            for k in K_GRID:
                selected = ranked[: min(k, len(ranked))]
                selected_gt = {gt_key(record) for record in selected if record["gt_exact_match"]}
                add_group_metric(family_acc[(group_key[0], group_key[2], score_id, k)], denom_gt, selected_gt, selected)

    source_family_rows = [
        finalize(
            {
                "level": "source_family",
                "source_id": source_id,
                "route_family": family,
                "score_id": score_id,
                "K": k,
                "primary_success_family": family in PRIMARY_FAMILIES,
            },
            acc,
        )
        for (source_id, family, score_id, k), acc in sorted(family_acc.items())
    ]

    aggregate_rows: list[dict[str, Any]] = []
    rows_by_score_k: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in source_family_rows:
        rows_by_score_k[(str(row["score_id"]), int(row["K"]))].append(row)
    for (score_id, k), rows in sorted(rows_by_score_k.items()):
        for scope, scoped in [
            ("primary_success_weighted", [row for row in rows if row["route_family"] in PRIMARY_FAMILIES]),
            ("all_weighted", rows),
        ]:
            acc = empty_accumulator()
            for row in scoped:
                for key in ["unit_count", "gt_units", "gt_total", "gt_selected", "selected_total", "violation_denominator", "violation_count"]:
                    acc[key] += int(row[key])
            aggregate_rows.append(
                finalize(
                    {
                        "level": scope,
                        "source_id": "ALL",
                        "route_family": "PRIMARY" if scope.startswith("primary") else "ALL",
                        "score_id": score_id,
                        "K": k,
                    },
                    acc,
                )
            )

    comparison_rows: list[dict[str, Any]] = []
    by_key = {(row["level"], row["score_id"], int(row["K"])): row for row in aggregate_rows}
    for k in K_GRID:
        primary = by_key.get(("primary_success_weighted", "S2_minmax_source_x_Ce", k))
        if not primary:
            continue
        for baseline, role in [
            ("S2_rankpct_source_x_Ce", "normalization_sensitivity_rank_percentile"),
            ("S2_raw_source_x_Ce", "normalization_sensitivity_raw_product"),
            ("A1_minmax_route_G_only", "route_aware_geometry_only"),
            ("A1_minmax_no_route_G_only", "no_route_geometry_only"),
            ("A2_minmax_TG_concat", "plain_concat"),
            ("S0_source_score_minmax", "source_baseline"),
        ]:
            other = by_key.get(("primary_success_weighted", baseline, k))
            if not other:
                continue
            comparison_rows.append(
                {
                    "level": "primary_success_weighted",
                    "K": k,
                    "comparison": f"S2_minmax_source_x_Ce_minus_{baseline}",
                    "baseline_role": role,
                    "primary_Recall@K": primary["Recall@K"],
                    "baseline_Recall@K": other["Recall@K"],
                    "delta_Recall@K": None
                    if primary["Recall@K"] is None or other["Recall@K"] is None
                    else primary["Recall@K"] - other["Recall@K"],
                    "primary_Violation@K": primary["Violation@K"],
                    "baseline_Violation@K": other["Violation@K"],
                    "delta_Violation@K": None
                    if primary["Violation@K"] is None or other["Violation@K"] is None
                    else primary["Violation@K"] - other["Violation@K"],
                }
            )
    return source_family_rows, aggregate_rows, comparison_rows


def score_rows(args: argparse.Namespace, train_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    ce_model, ce_prior, ce_fit = fit_model(train_rows, ce_feature_fn, args.epochs, args.lr, args.l2)
    route_g_model, route_g_prior, route_g_fit = fit_model(train_rows, route_g_feature_fn, args.epochs, args.lr, args.l2)
    no_route_g_model, no_route_g_prior, no_route_g_fit = fit_model(train_rows, no_route_g_feature_fn, args.epochs, args.lr, args.l2)
    concat_model, concat_prior, concat_fit = fit_model(train_rows, concat_feature_fn, args.epochs, args.lr, args.l2)

    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    source_bounds_raw: dict[str, list[float]] = {}
    ce_bounds_raw: dict[tuple[str, str], list[float]] = {}
    route_g_bounds_raw: dict[tuple[str, str], list[float]] = {}
    no_route_g_bounds_raw: dict[tuple[str, str], list[float]] = {}
    concat_bounds_raw: dict[tuple[str, str], list[float]] = {}
    source_counts = Counter()
    family_counts = Counter()

    for line_index, (ce_row, geometry_row, rank_row, hidden_row) in enumerate(read_aligned_rows(args.materialization_dir), start=1):
        candidate_id = str(ce_row.get("candidate_id"))
        if (
            candidate_id != geometry_row.get("candidate_id")
            or candidate_id != rank_row.get("candidate_id")
            or candidate_id != hidden_row.get("candidate_id")
        ):
            errors.append({"line": line_index, "error_type": "candidate_id_alignment_mismatch", "candidate_id": candidate_id})
            if len(errors) >= 20:
                break
            continue
        source_id = str(ce_row.get("source_id"))
        family = str(ce_row.get("route_family"))
        source_score = safe_float(rank_row.get("Z_e", {}).get("ranking_score"), 0.0)
        ce_score = predict_one(ce_model, ce_prior, ce_row, ce_feature_fn)
        route_g_score = predict_one(route_g_model, route_g_prior, geometry_row, route_g_feature_fn)
        no_route_g_score = predict_one(no_route_g_model, no_route_g_prior, geometry_row, no_route_g_feature_fn)
        concat_score = predict_one(concat_model, concat_prior, ce_row, concat_feature_fn)
        violation_checkable = bool(hidden_row.get("h2_violation_checkable")) and family != "support_contact"
        record = {
            "candidate_id": candidate_id,
            "source_id": source_id,
            "subgraph_id": str(ce_row.get("subgraph_id")),
            "route_family": family,
            "predicate_label": str(ce_row.get("predicate_label")),
            "prediction_id": str(ce_row.get("prediction_id")),
            "scan_id": str(ce_row.get("scan_id")),
            "subject_id": str(ce_row.get("subject_id")),
            "object_id": str(ce_row.get("object_id")),
            "source_score": source_score,
            "ce_score": ce_score,
            "route_g_score": route_g_score,
            "no_route_g_score": no_route_g_score,
            "concat_score": concat_score,
            "gt_exact_match": bool(hidden_row.get("gt_exact_match")),
            "violation_status": str(hidden_row.get("h2_relation_status")),
            "violation_checkable": violation_checkable,
            "scores": {},
        }
        records.append(record)
        source_counts[source_id] += 1
        family_counts[family] += 1
        update_bounds(source_bounds_raw, source_id, source_score)
        key = (source_id, family)
        update_bounds(ce_bounds_raw, key, ce_score)
        update_bounds(route_g_bounds_raw, key, route_g_score)
        update_bounds(no_route_g_bounds_raw, key, no_route_g_score)
        update_bounds(concat_bounds_raw, key, concat_score)

    if len(records) == EXPECTED_TOTAL_ROWS:
        source_rankpct = percentile_ranks(records, "source_score", lambda row: row["source_id"])
        ce_rankpct = percentile_ranks(records, "ce_score", lambda row: (row["source_id"], row["route_family"]))
    else:
        source_rankpct = {}
        ce_rankpct = {}

    source_bounds = {key: (values[0], values[1]) for key, values in source_bounds_raw.items()}
    ce_bounds = {key: (values[0], values[1]) for key, values in ce_bounds_raw.items()}
    route_g_bounds = {key: (values[0], values[1]) for key, values in route_g_bounds_raw.items()}
    no_route_g_bounds = {key: (values[0], values[1]) for key, values in no_route_g_bounds_raw.items()}
    concat_bounds = {key: (values[0], values[1]) for key, values in concat_bounds_raw.items()}

    for record in records:
        source_id = record["source_id"]
        family = record["route_family"]
        key = (source_id, family)
        source_minmax = clip01(minmax(record["source_score"], source_bounds.get(source_id)))
        ce_minmax = clip01(minmax(record["ce_score"], ce_bounds.get(key)))
        route_g_minmax = clip01(minmax(record["route_g_score"], route_g_bounds.get(key)))
        no_route_g_minmax = clip01(minmax(record["no_route_g_score"], no_route_g_bounds.get(key)))
        concat_minmax = clip01(minmax(record["concat_score"], concat_bounds.get(key)))
        source_rank = clip01(source_rankpct.get(record["candidate_id"], 0.5))
        ce_rank = clip01(ce_rankpct.get(record["candidate_id"], 0.5))
        raw_source = clip01(record["source_score"])
        raw_ce = clip01(record["ce_score"])
        record["scores"] = {
            "S0_source_score_minmax": source_minmax,
            "S2_minmax_source_x_Ce": source_minmax * ce_minmax,
            "S2_rankpct_source_x_Ce": source_rank * ce_rank,
            "S2_raw_source_x_Ce": raw_source * raw_ce,
            "A1_minmax_route_G_only": source_minmax * route_g_minmax,
            "A1_minmax_no_route_G_only": source_minmax * no_route_g_minmax,
            "A2_minmax_TG_concat": source_minmax * concat_minmax,
        }

    summary = {
        "row_count": len(records),
        "source_counts": dict(sorted(source_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "feature_sets": {
            "C_e": ["T_e", "G_e", "compatibility_features"],
            "route_G_only": ["G_e", "G.route_family_one_hot"],
            "no_route_G_only": ["G_e_without_route_family_one_hot"],
            "T_plus_G_concat": ["T_e", "G_e"],
        },
        "fit_summary": {
            "C_e": ce_fit,
            "route_G_only": route_g_fit,
            "no_route_G_only": no_route_g_fit,
            "T_plus_G_concat": concat_fit,
        },
        "normalization_variants": {
            "minmax": "per-source source score and per-source-family model score bounds from eval candidate pool; label-free",
            "rankpct": "per-source source score percentile and per-source-family C_e percentile; label-free rank normalization",
            "raw": "clipped raw source score times clipped raw C_e probability",
        },
    }
    return records, summary, errors


def evaluate_gate(comparison_rows: list[dict[str, Any]], aggregate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    def row_for(comparison: str, k: int) -> dict[str, Any] | None:
        for row in comparison_rows:
            if row["comparison"] == comparison and int(row["K"]) == k:
                return row
        return None

    k_scope = [10, 20, 50]
    checks = []
    for comparison, criterion in [
        ("S2_minmax_source_x_Ce_minus_A1_minmax_no_route_G_only", "no_route_g_only_not_stronger_than_S2"),
        ("S2_minmax_source_x_Ce_minus_A1_minmax_route_G_only", "route_g_only_not_stronger_than_S2"),
        ("S2_minmax_source_x_Ce_minus_A2_minmax_TG_concat", "plain_concat_not_stronger_than_S2"),
    ]:
        values = []
        for k in k_scope:
            row = row_for(comparison, k)
            if not row:
                values.append({"K": k, "passed": False, "reason": "missing_row"})
                continue
            recall_delta = safe_float(row.get("delta_Recall@K"), -999.0)
            violation_delta = safe_float(row.get("delta_Violation@K"), 999.0)
            values.append(
                {
                    "K": k,
                    "delta_Recall@K": recall_delta,
                    "delta_Violation@K": violation_delta,
                    "passed": recall_delta >= -0.01 and violation_delta < 0.0,
                }
            )
        checks.append({"comparison": comparison, "criterion": criterion, "passed_all": all(v["passed"] for v in values), "values": values})

    # Normalization is a robustness check: rank/raw variants need not beat minmax,
    # but they should preserve the core direction versus S0 at mid K.
    by_key = {(row["level"], row["score_id"], int(row["K"])): row for row in aggregate_rows}
    norm_values = []
    for score_id in ["S2_rankpct_source_x_Ce", "S2_raw_source_x_Ce"]:
        for k in k_scope:
            variant = by_key.get(("primary_success_weighted", score_id, k))
            source = by_key.get(("primary_success_weighted", "S0_source_score_minmax", k))
            if not variant or not source:
                norm_values.append({"score_id": score_id, "K": k, "passed": False, "reason": "missing_row"})
                continue
            recall_delta = safe_float(variant.get("Recall@K"), 0.0) - safe_float(source.get("Recall@K"), 0.0)
            violation_delta = safe_float(variant.get("Violation@K"), 1.0) - safe_float(source.get("Violation@K"), 0.0)
            norm_values.append(
                {
                    "score_id": score_id,
                    "K": k,
                    "delta_vs_S0_Recall@K": recall_delta,
                    "delta_vs_S0_Violation@K": violation_delta,
                    "passed": recall_delta >= -0.02 and violation_delta < 0.0,
                }
            )
    checks.append({"comparison": "normalization_variants_vs_S0", "criterion": "direction_preserved", "passed_all": all(v["passed"] for v in norm_values), "values": norm_values})

    return {
        "k_scope": k_scope,
        "checks": checks,
        "sensitivity_pass": all(check["passed_all"] for check in checks),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []

    for path in [
        args.internal_split_dir / "model_safe_split_view.jsonl",
        args.materialization_dir / "model_safe_ce_view.jsonl",
        args.materialization_dir / "model_safe_geometry_only_view.jsonl",
        args.materialization_dir / "source_rank_view.jsonl",
        args.materialization_dir / "hidden_metric_manifest.jsonl",
        args.base_evaluation_dir / "metric_manifest.json",
    ]:
        if not path.exists():
            errors.append({"error_type": "missing_input", "path": str(path)})

    train_rows: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    score_summary: dict[str, Any] = {}
    source_family_rows: list[dict[str, Any]] = []
    aggregate_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []
    gate: dict[str, Any] = {}

    if not errors:
        train_rows = [row for row in read_jsonl(args.internal_split_dir / "model_safe_split_view.jsonl") if row.get("protocol_split") == TRAIN_SPLIT]
        if not train_rows:
            errors.append({"error_type": "empty_internal_train_rows"})

    if not errors:
        records, score_summary, row_errors = score_rows(args, train_rows)
        errors.extend(row_errors)
        if len(records) != EXPECTED_TOTAL_ROWS:
            errors.append({"error_type": "unexpected_row_count", "actual": len(records), "expected": EXPECTED_TOTAL_ROWS})

    if not errors:
        source_family_rows, aggregate_rows, comparison_rows = metric_tables(records)
        gate = evaluate_gate(comparison_rows, aggregate_rows)

    status = STATUS_READY if not errors else STATUS_ERROR
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_artifacts": {
            "internal_split_dir": str(args.internal_split_dir),
            "materialization_dir": str(args.materialization_dir),
            "base_evaluation_dir": str(args.base_evaluation_dir),
        },
        "row_counts": {
            "internal_train": len(train_rows),
            "source_rows_scored": len(records),
            "source_family_metric_rows": len(source_family_rows),
            "aggregate_metric_rows": len(aggregate_rows),
            "comparison_rows": len(comparison_rows),
        },
        "score_ids": SCORE_IDS,
        "score_summary": score_summary,
        "gate": gate,
        "boundary": {
            "paper_table_replacement": False,
            "sensitivity_only": True,
            "official_test_usage": False,
            "label_free_normalization_variants": True,
            "no_route_geometry_ablation_added": True,
        },
        "outputs": {
            "source_family_metrics": str(args.out / "source_family_metrics.csv"),
            "aggregate_metrics": str(args.out / "aggregate_metrics.csv"),
            "comparison_metrics": str(args.out / "comparison_metrics.csv"),
            "score_manifest": str(args.out / "score_manifest.json"),
            "validation_errors": str(args.out / "validation_errors.jsonl"),
        },
        "validation_errors": len(errors),
    }

    write_csv(args.out / "source_family_metrics.csv", source_family_rows)
    write_csv(args.out / "aggregate_metrics.csv", aggregate_rows)
    write_csv(args.out / "comparison_metrics.csv", comparison_rows)
    write_json(args.out / "score_manifest.json", {"schema_version": f"{SCHEMA_VERSION}_score_manifest", **score_summary, "score_ids": SCORE_IDS})
    write_json(args.out / "summary.json", manifest)
    write_jsonl(args.out / "validation_errors.jsonl", errors)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return manifest


def main() -> int:
    args = parse_args()
    manifest = run(args)
    return 0 if manifest["status"] == STATUS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
